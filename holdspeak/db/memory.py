"""Relationship-aware long-horizon retrieval over HoldSpeak's local objects.

The lexical candidate pass stays deliberately cheap and deterministic.  A
bounded second pass then follows authoritative one-hop relationships (meeting
provenance, decision lineage, and frozen thread references) and returns the
neighbour's parent object as additional evidence.  This is HoldSpeak's local,
typed adaptation of RAGFlow's zero-LLM compiled-graph expansion and
parent/child retrieval patterns; it does not extract or invent relationships.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Optional

from .base import BaseRepository

_KIND_ORDER = {
    "decision": 0,
    "decision_record": 1,
    "desk_decision": 2,
    "artifact": 3,
    "meeting": 4,
    "note": 5,
    "thread": 6,
    "action": 7,
    "project_item": 8,
    "workbench_item": 9,
    "cadence": 10,
    # What he sent, published, prepared and has on the calendar (inventory C,
    # gap 7). Each is a spec entry over its canonical table; no new index.
    "send": 11,
    "project_update": 12,
    "prep_brief": 13,
    "calendar_event": 14,
}
_VALID_KINDS = frozenset(_KIND_ORDER)


def _not_parked(meeting_column: str) -> str:
    """A parked meeting and what it made (its actions, artifacts, decisions)
    stay out of memory: the lexical passes, the recent read and the
    relationship walk all wear this predicate."""
    return (
        "NOT EXISTS (SELECT 1 FROM meetings pk"
        f" WHERE pk.id={meeting_column} AND pk.parked=1)"
    )

_ECOSYSTEM_SPECS: dict[str, dict[str, str]] = {
    "decision_record": {
        "table": "decision_records",
        "alias": "r",
        "id": "r.id",
        "title": "r.decision_text",
        "body": "COALESCE(r.rationale,'')||' '||COALESCE(r.alternatives,'')||' '||COALESCE(r.owner,'')",
        "time": "r.updated_at",
        "active": "r.deleted=0",
        "project_id": "(SELECT pr.project_id FROM project_resources pr WHERE pr.resource_ref='decision_record:'||r.id AND pr.deleted=0 ORDER BY pr.project_id LIMIT 1)",
        "project": """(EXISTS (SELECT 1 FROM project_resources pr
                             WHERE pr.project_id=?
                               AND pr.resource_ref='decision_record:'||r.id
                               AND pr.deleted=0)
                      OR EXISTS (
                          SELECT 1 FROM decision_record_sources drs
                          WHERE drs.record_id=r.id AND (
                              (drs.source_type IN ('meeting','transcript')
                               AND EXISTS (SELECT 1 FROM meeting_projects mp
                                   WHERE mp.project_id=? AND
                                     drs.source_ref IN (mp.meeting_id,'meeting:'||mp.meeting_id,'transcript:'||mp.meeting_id)))
                              OR (drs.source_type='artifact' AND (
                                  EXISTS (SELECT 1 FROM project_resources apr
                                      WHERE apr.project_id=? AND apr.deleted=0 AND
                                        drs.source_ref IN (substr(apr.resource_ref,10),'artifact:'||substr(apr.resource_ref,10))
                                        AND apr.resource_ref LIKE 'artifact:%')
                                  OR EXISTS (SELECT 1 FROM artifacts a
                                      JOIN meeting_projects mp ON mp.meeting_id=a.meeting_id
                                      WHERE mp.project_id=? AND
                                        drs.source_ref IN (a.id,'artifact:'||a.id))
                              ))
                          )
                      ))""",
    },
    "desk_decision": {
        "table": "desk_decisions",
        "alias": "d",
        "id": "d.id",
        "title": "CASE WHEN d.title='' THEN d.decision_markdown ELSE d.title END",
        "body": "d.context_markdown||' '||d.decision_markdown||' '||d.consequences_markdown||' '||d.alternatives_json",
        "time": "d.updated_at",
        "active": "d.deleted=0",
        # One ref name for a desk decision: `desk_decision:<id>`. Rows the
        # Decide button filed before 2026-10-03 carry `decision:<id>`; the
        # read accepts both, so an old decision stays in its Project.
        "project_id": "(SELECT pr.project_id FROM project_resources pr WHERE pr.resource_ref IN ('desk_decision:'||d.id,'decision:'||d.id) AND pr.deleted=0 ORDER BY pr.project_id LIMIT 1)",
        "project": "EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=? AND pr.resource_ref IN ('desk_decision:'||d.id,'decision:'||d.id) AND pr.deleted=0)",
    },
    "action": {
        "table": "action_items",
        "alias": "a",
        "id": "a.id",
        "title": "a.task",
        "body": "COALESCE(a.owner,'')||' '||COALESCE(a.due,'')||' '||a.status",
        "time": "COALESCE(a.completed_at,a.created_at)",
        "active": _not_parked("a.meeting_id"),
        "project_id": "COALESCE((SELECT mp.project_id FROM meeting_projects mp WHERE mp.meeting_id=a.meeting_id ORDER BY mp.project_id LIMIT 1),(SELECT pr.project_id FROM project_resources pr WHERE pr.resource_ref='action:'||a.id AND pr.deleted=0 ORDER BY pr.project_id LIMIT 1))",
        "project": "(EXISTS (SELECT 1 FROM meeting_projects mp WHERE mp.project_id=? AND mp.meeting_id=a.meeting_id) OR EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=? AND pr.resource_ref='action:'||a.id AND pr.deleted=0))",
    },
    "project_item": {
        "table": "project_items",
        "alias": "p",
        "id": "p.id",
        "title": "p.title",
        "body": "COALESCE(p.summary,'')||' '||COALESCE(p.details_json,'')||' '||p.item_type||' '||p.lifecycle||' '||COALESCE(p.severity,'')",
        "time": "p.updated_at",
        "active": "1=1",
        "project_id": "p.project_id",
        "project": "p.project_id=?",
    },
    "workbench_item": {
        "table": "workbench_items",
        "alias": "w",
        "id": "w.id",
        "title": "w.title",
        "body": "w.body||' '||COALESCE(w.result,'')",
        "time": "w.last_modified",
        "active": "w.status!='dismissed' AND w.parked=0",
        "project_id": "COALESCE((SELECT pr.project_id FROM project_resources pr WHERE pr.resource_ref='workbench_item:'||w.id AND pr.deleted=0 ORDER BY pr.project_id LIMIT 1),(SELECT pr.project_id FROM project_resources pr WHERE pr.resource_ref='workbench:'||w.workbench_id AND pr.deleted=0 ORDER BY pr.project_id LIMIT 1))",
        "project": "EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=? AND pr.deleted=0 AND pr.resource_ref IN ('workbench_item:'||w.id,'workbench:'||w.workbench_id))",
    },
    "cadence": {
        "table": "cadence_loops",
        "alias": "c",
        "id": "c.id",
        "title": "c.title",
        "body": "c.summary||' '||c.status||' '||c.priority||' '||COALESCE(c.owner,'')",
        "time": "c.updated_at",
        "active": "c.status!='killed'",
        "project_id": "COALESCE(c.project,(SELECT pr.project_id FROM project_resources pr WHERE pr.resource_ref='cadence:'||c.id AND pr.deleted=0 ORDER BY pr.project_id LIMIT 1))",
        "project": "(c.project=? OR EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=? AND pr.resource_ref='cadence:'||c.id AND pr.deleted=0))",
    },
    # A send: what, to whom, when, outcome. The frozen payload is NEVER read
    # here: a sent Brief carries People data (custody), and the payload of
    # any document is already found under its own kind. `account_json` is
    # read for the Slack channel label only.
    "send": {
        "table": "channel_sends",
        "alias": "s",
        "id": "s.id",
        "title": "COALESCE(NULLIF(json_extract(s.document_json,'$.title'),''),s.document_ref)",
        "body": (
            "'To '||COALESCE((SELECT cd.name FROM channel_destinations cd"
            " WHERE cd.id=s.destination_id),'')"
            "||' · '||s.channel"
            "||COALESCE(' · '||json_extract(s.target_json,'$.to'),'')"
            "||COALESCE(' · cc '||json_extract(s.target_json,'$.cc'),'')"
            "||COALESCE(' · '||json_extract(s.target_json,'$.repo'),'')"
            "||COALESCE(' · '||json_extract(s.target_json,'$.key'),'')"
            "||COALESCE(' · '||json_extract(s.account_json,'$.channel_label'),'')"
            "||' · '||s.state||COALESCE(' · '||NULLIF(s.reason,''),'')"
        ),
        "time": "COALESCE(s.settled_at,s.dispatch_started_at,s.created_at)",
        # A send he pressed: sent, failed, or unknown. A prepared or
        # discarded row left nothing.
        "active": "s.state IN ('sent','failed','unknown')",
        "project_id": (
            "COALESCE((SELECT u.project_id FROM project_updates u"
            " WHERE s.document_ref='project_update:'||u.id),"
            "(SELECT pr.project_id FROM project_resources pr"
            " WHERE pr.resource_ref=s.document_ref AND pr.deleted=0"
            " ORDER BY pr.project_id LIMIT 1))"
        ),
        "project": (
            "(EXISTS (SELECT 1 FROM project_updates u WHERE u.project_id=?"
            " AND s.document_ref='project_update:'||u.id)"
            " OR EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=?"
            " AND pr.resource_ref=s.document_ref AND pr.deleted=0))"
        ),
    },
    "project_update": {
        "table": "project_updates",
        "alias": "u",
        "id": "u.id",
        "title": (
            "COALESCE((SELECT p.name FROM projects p WHERE p.id=u.project_id),u.project_id)"
            "||' update r'||u.draft_revision"
        ),
        "body": "u.body_md",
        "time": "COALESCE(u.published_at,u.updated_at)",
        # Published only: a draft is not yet what he said.
        "active": "u.lifecycle='published'",
        "project_id": "u.project_id",
        "project": "u.project_id=?",
    },
    "prep_brief": {
        "table": "project_briefs",
        "alias": "b",
        "id": "b.id",
        "title": (
            "COALESCE((SELECT p.name FROM projects p WHERE p.id=b.project_id),b.project_id)"
            "||' prep · '||b.purpose"
        ),
        "body": "b.body_md",
        "time": "COALESCE(b.kept_at,b.updated_at)",
        "active": "b.lifecycle!='discarded'",
        "project_id": "b.project_id",
        "project": "b.project_id=?",
    },
    "calendar_event": {
        "table": "calendar_events",
        "alias": "e",
        "id": "e.id",
        "title": "COALESCE(NULLIF(e.title,''),e.id)",
        "body": (
            "COALESCE(e.location,'')||' '||"
            "CASE WHEN e.attendees_json IN ('','[]') THEN '' ELSE e.attendees_json END"
            "||' '||e.source_label"
        ),
        "time": "e.starts_at",
        "active": "1=1",
        "project_id": (
            "(SELECT cep.project_id FROM calendar_event_projects cep"
            " WHERE cep.calendar_event_id=e.id ORDER BY cep.project_id LIMIT 1)"
        ),
        "project": (
            "EXISTS (SELECT 1 FROM calendar_event_projects cep"
            " WHERE cep.project_id=? AND cep.calendar_event_id=e.id)"
        ),
    },
}

# The meeting's summary and topics as it reads now: the newest intel snapshot
# and the topic rows (inventory C, gap 6). Shared by the lexical summary pass
# and the RECENT read.
_MEETING_SUMMARY = (
    "COALESCE((SELECT i.summary FROM intel_snapshots i WHERE i.meeting_id=m.id"
    " ORDER BY i.timestamp DESC,i.id DESC LIMIT 1),'')"
)
_MEETING_TOPICS = (
    "COALESCE((SELECT group_concat(t.topic,' · ') FROM topics t"
    " WHERE t.meeting_id=m.id),'')"
)

# HS-202-02 (Astra's counsel finding 5 on PR #595) — the RECENT read.
#
# `search()` is lexical: it needs words, and `_match_expression` raises on
# a wordless query. The Desk-memory face opens with NO query, so every
# kind that only has a lexical path read EMPTY on a desk that plainly had
# meetings or notes on it. These specs are the same canonical stores the
# lexical passes join, read by RECENCY instead of by relevance.
_RECENT_SPECS: dict[str, dict[str, str]] = {
    "meeting": {
        "table": "meetings",
        "alias": "m",
        "id": "m.id",
        "title": "COALESCE(NULLIF(m.title,''),m.id)",
        # The summary when the meeting has one; else its first words.
        "body": (
            f"COALESCE(NULLIF(trim({_MEETING_SUMMARY}||' '||{_MEETING_TOPICS}),''),"
            "(SELECT group_concat(s.text,' ') FROM ("
            "SELECT text FROM segments WHERE meeting_id=m.id"
            " ORDER BY start_time LIMIT 4) s),'')"
        ),
        "time": "m.started_at",
        "active": "m.parked=0",
        "project_id": (
            "(SELECT mp.project_id FROM meeting_projects mp"
            " WHERE mp.meeting_id=m.id ORDER BY mp.project_id LIMIT 1)"
        ),
    },
    "note": {
        "table": "notes",
        "alias": "n",
        "id": "n.id",
        "title": "COALESCE(NULLIF(n.title,''),n.id)",
        "body": "COALESCE(n.body_markdown,'')",
        "time": "n.updated_at",
        # The same promotion belt the lexical note pass wears: a note
        # promoted into context is not desk memory.
        "active": (
            "n.deleted=0 AND NOT EXISTS (SELECT 1 FROM context_promotions cp"
            " WHERE cp.target_ref='note:'||n.id)"
        ),
        "project_id": (
            "(SELECT pr.project_id FROM project_resources pr"
            " WHERE pr.resource_ref='note:'||n.id AND pr.deleted=0"
            " ORDER BY pr.project_id LIMIT 1)"
        ),
    },
    "artifact": {
        "table": "artifacts",
        "alias": "a",
        "id": "a.id",
        "title": "COALESCE(NULLIF(a.title,''),a.id)",
        "body": "COALESCE(a.body_markdown,'')",
        "time": "a.updated_at",
        "active": _not_parked("a.meeting_id"),
        "project_id": (
            "(SELECT pr.project_id FROM project_resources pr"
            " WHERE pr.resource_ref='artifact:'||a.id AND pr.deleted=0"
            " ORDER BY pr.project_id LIMIT 1)"
        ),
    },
    # HS-202-02 (Astra round 2, residual 3) — recall asks for `thread`
    # under `also` (`services/recall_service.py:54`), and RECENT had no
    # spec for it: the kind was skipped in silence, so a desk whose only
    # memory is threads read as an empty desk. The custody filters are the
    # lexical pass's own (`_thread_rows`): deleted threads and messages,
    # sensitive parts and drafts never reach memory.
    "thread": {
        "table": "threads",
        "alias": "t",
        "id": "t.id",
        "title": "COALESCE(NULLIF(t.title,''),t.id)",
        "body": (
            "COALESCE((SELECT group_concat(q.text,' ') FROM ("
            "SELECT p.text text FROM thread_message_parts p"
            " JOIN thread_messages m ON m.id=p.message_id"
            " WHERE m.thread_id=t.id AND m.deleted_at IS NULL"
            " AND p.sensitive=0 AND p.draft=0 AND p.kind='text'"
            " AND COALESCE(p.text,'')<>''"
            " ORDER BY m.created_at, p.ordinal LIMIT 4) q),'')"
        ),
        "time": "datetime(t.updated_at,'unixepoch')",
        "active": "t.deleted_at IS NULL",
        "project_id": (
            "(SELECT pr.project_id FROM project_resources pr"
            " WHERE pr.resource_ref='thread:'||t.id AND pr.deleted=0"
            " ORDER BY pr.project_id LIMIT 1)"
        ),
    },
    "decision": {
        "table": "decisions",
        "alias": "d",
        "id": "d.id",
        "title": "d.text",
        "body": "COALESCE(d.text,'')",
        "time": "d.decided_at",
        "active": _not_parked("d.source_meeting_id"),
        "project_id": "d.project_key",
    },
}

_RELATION_SEED_LIMIT = 32
_RELATION_RESULT_LIMIT = 64
_RELATION_NEIGHBOURS_PER_SEED = 2
_QUERY_TERM_LIMIT = 24
# The vector retriever (docs/internal/MEMORY-DESIGN.md §3.2): the top 50
# sources INSIDE the scope.  There is no bound on the walk: a bound spent on
# sources outside the scope would hide the sources inside it.
_VECTOR_RESULT_LIMIT = 50
_MARK = re.compile(r"</?mark>")
_WORD = re.compile(r"\w+", re.UNICODE)
_QUERY_STOPWORDS = frozenset(
    "a an and are about did do does for from how i in is it of on or the to was what when where which who why with we you".split()
)


@dataclass(frozen=True)
class MemoryHit:
    kind: str
    source_ref: str
    title: str
    snippet: str
    occurred_at: str
    project_id: Optional[str]
    bm25: float
    normalized_score: float
    kind_rank: int
    rank: int
    retrieval_origin: str = "lexical"
    related_to: Optional[str] = None
    relationship: Optional[str] = None
    graph_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MemorySearchResult:
    hits: list[MemoryHit]
    total: int
    limit: int
    offset: int
    lexical_total: int = 0
    expanded_total: int = 0
    # Set only when the vector retriever ran and its list was fused in.  With
    # no embedding engine this stays None and the result is the keyword +
    # relation result, unchanged.
    fusion: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        payload = self._to_dict()
        if self.fusion is not None:
            payload["ranking"]["fusion"] = dict(self.fusion)
        return payload

    def _to_dict(self) -> dict[str, Any]:
        return {
            "hits": [hit.to_dict() for hit in self.hits],
            "page": {
                "offset": self.offset,
                "limit": self.limit,
                "count": len(self.hits),
                "total": self.total,
            },
            "ranking": {
                "method": "per_kind_bm25_interleave",
                "normalization": "min_max_within_kind",
                "interleave": "lexical_seed_then_typed_one_hop_neighbours",
                "parent_context": "matching transcript segments and message parts return their parent meeting or thread",
                "relationship_expansion": {
                    "method": "authoritative_typed_one_hop",
                    "lexical_count": self.lexical_total,
                    "expanded_count": self.expanded_total,
                    "max_seeds": _RELATION_SEED_LIMIT,
                    "max_results": _RELATION_RESULT_LIMIT,
                    "max_neighbours_per_seed": _RELATION_NEIGHBOURS_PER_SEED,
                },
            },
        }


#: The keyword tables that hold a COPY of the text: kind -> (table, columns).
_KEYWORD_TABLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "decision": ("decisions_memory_fts", ("text", "rationale")),
    "artifact": ("artifacts_memory_fts", ("title", "body_markdown")),
    "note": ("notes_memory_fts", ("title", "body_markdown")),
}


def _redacted(text: Any) -> str:
    """Memory defense on the way OUT: a title or a snippet never carries a
    secret, whichever retriever found the row and whatever table it came
    from.  A keyword snippet wraps the matched words in ``<mark>``; the marks
    are kept when the text holds no secret and dropped when it does (a mark
    inside ``password=...`` would hide the secret from the pattern)."""
    from ..memory.defense import redact

    value = str(text or "")
    plain = _MARK.sub("", value)
    cleaned = redact(plain)
    return value if cleaned == plain else cleaned


def _match_expression(query: str) -> str:
    """Turn arbitrary user text into a safe, deterministic FTS phrase query."""
    terms = _query_terms(query)
    if not terms:
        raise ValueError("query must contain searchable text")
    # Quoting each lexical term prevents user punctuation/FTS operators from
    # changing the grammar. OR lets a natural-language ask retrieve partial
    # lexical matches; BM25 still rewards sources matching more query terms.
    return " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)


def _query_terms(query: str) -> list[str]:
    raw_terms = _WORD.findall(str(query or "").casefold())
    filtered = [term for term in raw_terms if term not in _QUERY_STOPWORDS] or raw_terms
    # Model prompts can be much larger than search-box queries. Deduplication and
    # a hard term ceiling keep both FTS grammar and canonical-store LIKE passes
    # bounded without allowing repeated prompt words to distort relevance. Keep
    # both ends because the specific question often follows a long pasted body.
    unique = list(dict.fromkeys(filtered))
    if len(unique) <= _QUERY_TERM_LIMIT:
        return unique
    head = _QUERY_TERM_LIMIT // 2
    return unique[:head] + unique[-(_QUERY_TERM_LIMIT - head) :]


def rebuild_memory_index(conn: sqlite3.Connection) -> dict[str, int]:
    """Rebuild all three FTS tables from canonical rows, safely and idempotently.

    Admission is ``memory_admits`` (holdspeak/memory/admission.py): the same
    function the chunk sweep calls, so the keyword index and the chunk index
    can never disagree about what memory may hold.  The text is redacted
    (holdspeak/memory/defense.py), as the triggers store it.
    """
    from ..memory.admission import memory_admits
    from ..memory.defense import redact

    promoted = {
        str(row[0]) for row in conn.execute("SELECT DISTINCT target_ref FROM context_promotions")
    }

    def admitted(kind: str, sql: str) -> list[dict[str, Any]]:
        rows = []
        cursor = conn.execute(sql)
        # The reconcile calls this on a connection with no row factory.
        names = [column[0] for column in cursor.description]
        for raw in cursor:
            row = dict(zip(names, tuple(raw)))
            # HS-200-10 (F0/L1, part 3): a full re-index cannot re-admit what
            # the guarded triggers excluded.  Keyed on the EXISTENCE of a
            # promotion rather than on its disclosure_state.
            row["promoted"] = kind == "note" and f"note:{row['id']}" in promoted
            if memory_admits(kind, row):
                rows.append(row)
        return rows

    conn.execute("DELETE FROM decisions_memory_fts")
    conn.executemany(
        "INSERT INTO decisions_memory_fts(source_id,text,rationale) VALUES (?,?,?)",
        [
            (row["id"], redact(row["text"]), redact(row["rationale"] or ""))
            for row in admitted(
                "decision",
                "SELECT id,text,rationale,deleted,source_state FROM decisions ORDER BY rowid",
            )
        ],
    )
    conn.execute("DELETE FROM artifacts_memory_fts")
    conn.executemany(
        "INSERT INTO artifacts_memory_fts(source_id,title,body_markdown) VALUES (?,?,?)",
        [
            (row["id"], redact(row["title"]), redact(row["body_markdown"]))
            for row in admitted(
                "artifact", "SELECT id,title,body_markdown FROM artifacts ORDER BY rowid"
            )
        ],
    )
    conn.execute("DELETE FROM notes_memory_fts")
    conn.executemany(
        "INSERT INTO notes_memory_fts(source_id,title,body_markdown) VALUES (?,?,?)",
        [
            (row["id"], redact(row["title"]), redact(row["body_markdown"]))
            for row in admitted(
                "note", "SELECT id,title,body_markdown,deleted FROM notes ORDER BY rowid"
            )
        ],
    )
    # A full merge leaves no token of a row that was deleted above.
    for table in _KEYWORD_TABLES.values():
        conn.execute(f"INSERT INTO {table[0]}({table[0]}) VALUES('optimize')")
    counts = {
        "decisions": int(
            conn.execute("SELECT count(*) FROM decisions_memory_fts").fetchone()[0]
        ),
        "artifacts": int(
            conn.execute("SELECT count(*) FROM artifacts_memory_fts").fetchone()[0]
        ),
        "notes": int(
            conn.execute("SELECT count(*) FROM notes_memory_fts").fetchone()[0]
        ),
    }
    counts["total"] = sum(counts.values())
    return counts


class MemoryRepository(BaseRepository):
    """One search contract over independently normalized local FTS corpora."""

    table = "memory"

    def rebuild(self) -> dict[str, int]:
        with self._connection() as conn:
            return rebuild_memory_index(conn)

    def scrub_keyword_rows(self, refs: Iterable[str]) -> int:
        """Redact the keyword-table copy of each named source.

        The triggers copy a row into its keyword table as it is written, in
        the writer's own transaction, so they cannot call the memory defense.
        The sweep calls this for every source whose text holds a secret: the
        copy is replaced by the redacted text, and a merge removes the old
        tokens.  After it, the secret is not a search key and is in no
        keyword table.  Returns the number of rows changed.
        """
        from ..memory.defense import redact

        changed = 0
        touched: set[str] = set()
        with self._connection() as conn:
            for ref in refs:
                kind, _, resource_id = str(ref).partition(":")
                spec = _KEYWORD_TABLES.get(kind)
                if spec is None:
                    continue
                table, columns = spec
                for row in conn.execute(
                    f"SELECT rowid,{','.join(columns)} FROM {table} WHERE source_id=?",
                    (resource_id,),
                ).fetchall():
                    clean = [redact(str(row[column] or "")) for column in columns]
                    if clean == [str(row[column] or "") for column in columns]:
                        continue
                    conn.execute(
                        f"UPDATE {table} SET {','.join(f'{column}=?' for column in columns)}"
                        " WHERE rowid=?",
                        (*clean, row["rowid"]),
                    )
                    changed += 1
                    touched.add(table)
            for table in sorted(touched):
                conn.execute(f"INSERT INTO {table}({table}) VALUES('optimize')")
        return changed

    def set_embedder(self, embedder: Any) -> None:
        """Give recall the engine that embeds a question, or None.

        The memory conductor sets this when ``memory.embed`` has an engine.
        With None, ``search`` is the keyword + relation search and nothing
        else runs.
        """
        self._embedder = embedder

    @property
    def embedder(self) -> Any:
        return getattr(self, "_embedder", None)

    @staticmethod
    def _promoted_refs(conn: sqlite3.Connection) -> set[str]:
        """Every canonical ref carrying a promotion (HS-200-10, F0).

        Keyed on the EXISTENCE of a `context_promotions` row, never on its
        `disclosure_state`: once a record has been minted or appended to by
        promotion it never joins the relevance pool, revoked or not.  This
        errs closed and removes a class of state-dependent bugs.

        Deliberately not exception-guarded.  A missing table here would mean an
        unreconciled database, and swallowing that would fail OPEN -- the one
        direction this fence must never fail.
        """
        return {
            str(row[0])
            for row in conn.execute("SELECT DISTINCT target_ref FROM context_promotions")
            if str(row[0] or "").strip()
        }

    def promoted_refs(self) -> set[str]:
        """The promoted-ref set, for the belt at grounding's relevance call sites."""
        with self._connection() as conn:
            return self._promoted_refs(conn)

    def recent(
        self, *, kinds: Optional[Iterable[str]] = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """The newest rows per kind, with no query.

        HS-202-02 — the wordless read `search()` cannot serve. Same row
        shape the lexical hits carry (kind, source_ref, title, snippet,
        occurred_at, project_id), so the recall face draws them
        identically; `bm25` is absent because nothing was ranked.
        """
        selected = self._normalize_kinds(kinds)
        bounded = max(1, min(int(limit), 500))
        rows: list[dict[str, Any]] = []
        with self._connection() as conn:
            for kind in selected:
                spec = _RECENT_SPECS.get(kind) or _ECOSYSTEM_SPECS.get(kind)
                if spec is None:
                    # A kind with no canonical recency source is reported by
                    # ABSENCE, never by a silent empty list that reads like
                    # "this desk holds none".
                    continue
                try:
                    found = conn.execute(
                        f"""SELECT '{kind}' kind,
                                   '{kind}:'||{spec["id"]} source_ref,
                                   {spec["title"]} title,
                                   substr(COALESCE({spec["body"]},''),1,420) snippet,
                                   {spec["time"]} occurred_at,
                                   {spec["project_id"]} project_id
                            FROM {spec["table"]} {spec["alias"]}
                            WHERE {spec["active"]}
                            ORDER BY occurred_at DESC,{spec["id"]} DESC
                            LIMIT ?""",
                        (bounded,),
                    ).fetchall()
                except sqlite3.Error:  # pragma: no cover - schema drift
                    # A store this database does not carry is simply not a
                    # source of recent memory; it is never a lie about one.
                    continue
                for row in found:
                    item = dict(row)
                    item["title"] = _redacted(item.get("title"))
                    item["snippet"] = _redacted(item.get("snippet"))
                    rows.append(item)
        rows.sort(
            key=lambda row: (str(row.get("occurred_at") or ""), str(row.get("source_ref") or "")),
            reverse=True,
        )
        return rows[:bounded]

    def search(
        self,
        query: str,
        *,
        kinds: Optional[Iterable[str]] = None,
        project_id: Optional[str] = None,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        exclude_refs: Optional[Iterable[str]] = None,
    ) -> MemorySearchResult:
        expression = _match_expression(query)
        terms = _query_terms(query)
        selected = self._normalize_kinds(kinds)
        bounded_limit = max(1, min(int(limit), 500))
        bounded_offset = max(0, int(offset))
        project = str(project_id or "").strip() or None
        start = str(time_from or "").strip() or None
        end = str(time_to or "").strip() or None
        excluded = {
            self._base_ref(str(ref).strip())
            for ref in (exclude_refs or ())
            if str(ref).strip()
        }

        by_kind: dict[str, list[dict[str, Any]]] = {}
        with self._connection() as conn:
            # HS-200-10 (F0/L2): the GRAPH route fence.  A note is reachable by
            # relevance two ways -- lexically through `notes_memory_fts`, and as
            # a one-hop relationship neighbour of a lexical seed, which
            # `_load_related_row` reads straight out of `notes` and never
            # touches the corpus at all.  L1 closes the first and leaves the
            # second wide open while looking green.
            #
            # The union lands HERE, on the shipped `excluded` plumbing, and not
            # at the `MemoryHit` constructor below: `lexical_total`, `total` and
            # the page slice are all computed before that point, so filtering
            # there would over-count, hand back a page shorter than `limit`, and
            # make grounding book withheld sources as mere overflow.
            excluded |= self._promoted_refs(conn)
            if "decision" in selected:
                by_kind["decision"] = self._decision_rows(
                    conn, expression, project, start, end
                )
            if "artifact" in selected:
                by_kind["artifact"] = self._artifact_rows(
                    conn, expression, project, start, end
                )
            if "meeting" in selected:
                by_kind["meeting"] = self._meeting_rows(
                    conn, expression, project, start, end
                )
                # The summary and topics are part of what the meeting said.
                # A meeting the transcript pass already found keeps that hit.
                found = {row["source_ref"] for row in by_kind["meeting"]}
                by_kind["meeting"].extend(
                    row
                    for row in self._meeting_summary_rows(
                        conn, terms, project, start, end
                    )
                    if row["source_ref"] not in found
                )
                by_kind["meeting"].sort(
                    key=lambda row: (float(row["bm25"]), str(row["source_ref"]))
                )
            if "note" in selected:
                by_kind["note"] = self._note_rows(conn, expression, project, start, end)
            if "thread" in selected:
                by_kind["thread"] = self._thread_rows(
                    conn, expression, project, start, end
                )
            for kind in (
                "decision_record",
                "desk_decision",
                "action",
                "project_item",
                "workbench_item",
                "cadence",
                "send",
                "project_update",
                "prep_brief",
                "calendar_event",
            ):
                if kind in selected:
                    by_kind[kind] = self._ecosystem_rows(
                        conn, kind, terms, project, start, end
                    )

        normalized: dict[str, list[dict[str, Any]]] = {}
        for kind, rows in by_kind.items():
            if project:
                for row in rows:
                    row["project_id"] = row.get("project_id") or project
            # FTS5 bm25 values are only comparable inside the same corpus. Normalize
            # each kind independently, rank it independently, then interleave rank
            # tiers; long artifacts can never drown short decisions by raw score.
            scores = [float(row["bm25"]) for row in rows]
            best = min(scores) if scores else 0.0
            worst = max(scores) if scores else 0.0
            span = worst - best
            for index, row in enumerate(rows, start=1):
                row["kind_rank"] = index
                row["normalized_score"] = (
                    1.0 if span == 0 else (worst - float(row["bm25"])) / span
                )
            normalized[kind] = rows

        interleaved = [row for rows in normalized.values() for row in rows]
        if excluded:
            interleaved = [
                row
                for row in interleaved
                if self._base_ref(str(row["source_ref"])) not in excluded
            ]
        interleaved.sort(
            key=lambda row: (
                int(row["kind_rank"]),
                -float(row["normalized_score"]),
                self._recency_key(str(row["occurred_at"])),
                _KIND_ORDER[str(row["kind"])],
                str(row["source_ref"]),
            )
        )
        lexical_total = len(interleaved)
        lexical_rows = list(interleaved)
        with self._connection() as conn:
            expanded = self._expand_related_rows(
                conn,
                interleaved,
                selected=selected,
                project=project,
                start=start,
                end=end,
                excluded=excluded,
            )
        if expanded:
            by_seed: dict[str, list[dict[str, Any]]] = {}
            for row in expanded:
                by_seed.setdefault(str(row["related_to"]), []).append(row)
            for rows in by_seed.values():
                rows.sort(
                    key=lambda row: (
                        -float(row["graph_score"]),
                        _KIND_ORDER[str(row["kind"])],
                        self._recency_key(str(row["occurred_at"])),
                        str(row["source_ref"]),
                    )
                )
            woven: list[dict[str, Any]] = []
            for row in interleaved:
                woven.append(row)
                woven.extend(by_seed.get(self._base_ref(str(row["source_ref"])), ()))
            interleaved = woven

        fusion: Optional[dict[str, Any]] = None
        embedder = self.embedder
        if embedder is not None:
            fused = self._fuse_with_vectors(
                query,
                embedder,
                lexical_rows=lexical_rows,
                woven=interleaved,
                selected=selected,
                project=project,
                start=start,
                end=end,
                excluded=excluded,
            )
            if fused is not None:
                interleaved, fusion = fused

        total = len(interleaved)
        page = interleaved[bounded_offset : bounded_offset + bounded_limit]
        hits = [
            MemoryHit(
                kind=str(row["kind"]),
                source_ref=str(row["source_ref"]),
                title=_redacted(row["title"]),
                snippet=_redacted(row["snippet"]),
                occurred_at=str(row["occurred_at"]),
                project_id=str(row["project_id"]) if row["project_id"] else None,
                bm25=float(row["bm25"]),
                normalized_score=float(row["normalized_score"]),
                kind_rank=int(row["kind_rank"]),
                rank=bounded_offset + index,
                retrieval_origin=str(row.get("retrieval_origin") or "lexical"),
                related_to=(str(row["related_to"]) if row.get("related_to") else None),
                relationship=(
                    str(row["relationship"]) if row.get("relationship") else None
                ),
                graph_score=float(row.get("graph_score") or 0.0),
            )
            for index, row in enumerate(page, start=1)
        ]
        return MemorySearchResult(
            hits,
            total,
            bounded_limit,
            bounded_offset,
            lexical_total=lexical_total,
            expanded_total=(
                max(0, total - lexical_total)
                if fusion is None
                else int(fusion["relation_count"])
            ),
            fusion=fusion,
        )

    # ── the vector retriever and the fusion (MEMORY-DESIGN.md §3.2) ──

    def _fuse_with_vectors(
        self,
        query: str,
        embedder: Any,
        *,
        lexical_rows: list[dict[str, Any]],
        woven: list[dict[str, Any]],
        selected: tuple[str, ...],
        project: Optional[str],
        start: Optional[str],
        end: Optional[str],
        excluded: set[str],
    ) -> Optional[tuple[list[dict[str, Any]], dict[str, Any]]]:
        """Fuse keyword, relation and vector lists by reciprocal rank.

        Returns None when the vector retriever gives nothing (no vectors yet,
        or the engine failed): the caller then keeps the keyword + relation
        result exactly as it is.
        """
        from ..memory.fusion import RRF_K, reciprocal_rank_fusion

        try:
            vector_rows = self._vector_rows(
                query, embedder, selected=selected, project=project,
                start=start, end=end, excluded=excluded,
            )
        except Exception as exc:  # the engine is optional; recall never fails on it
            from ..logging_config import get_logger

            get_logger("db.memory").warning("memory vector retriever skipped: %s", exc)
            return None
        if not vector_rows:
            return None
        relation_rows = [row for row in woven if row.get("related_to")]
        lists = {
            "keyword": [self._base_ref(str(row["source_ref"])) for row in lexical_rows],
            "relation": [self._base_ref(str(row["source_ref"])) for row in relation_rows],
            "vector": [self._base_ref(str(row["source_ref"])) for row in vector_rows],
        }
        first: dict[str, dict[str, Any]] = {}
        for rows in (lexical_rows, relation_rows, vector_rows):
            for row in rows:
                first.setdefault(self._base_ref(str(row["source_ref"])), row)
        fused_rows = [
            first[str(key)] for key, _score, _found in reciprocal_rank_fusion(lists)
        ]
        meta = {
            "method": "reciprocal_rank_fusion",
            "k": RRF_K,
            "retrievers": [name for name, keys in lists.items() if keys],
            "model_id": str(embedder.model_id),
            "keyword_count": len(lexical_rows),
            "relation_count": len(relation_rows),
            "vector_count": len(vector_rows),
        }
        return fused_rows, meta

    def _vector_rows(
        self,
        query: str,
        embedder: Any,
        *,
        selected: tuple[str, ...],
        project: Optional[str],
        start: Optional[str],
        end: Optional[str],
        excluded: set[str],
    ) -> list[dict[str, Any]]:
        """The best chunk per source, nearest first, inside the scope.

        Three rules, each applied to a candidate BEFORE it takes one of the
        50 places:

        1. **Scope.**  Kinds, excluded refs, project and time.  The walk has no
           bound, so sources outside a project can never use up the places of
           the sources inside it.
        2. **Admission now.**  ``current_source`` reads the live row through
           the sweep's own reader and ``memory_admits``.  A source that is
           gone, parked, sensitive, promoted or deleted since the last sweep
           is not a candidate, whatever the index holds.
        3. **The text is the text of now.**  The source is cut again and the
           candidate must be a chunk of that cut, with the hash its vector was
           made from.  The snippet is that fresh, redacted text - never the
           stored chunk - so recall returns nothing the keyword path would
           not return.  A vector made from an older text is dropped.
        """
        import numpy as np

        from ..memory.retain import current_source, prepare_current

        index = self._db.memory_index
        matrix, chunk_ids, source_refs, chunk_shas = index.matrix(str(embedder.model_id))
        if matrix.shape[0] == 0:
            return []
        question = np.asarray(embedder.embed_query(query), dtype=np.float32)
        if question.shape != (matrix.shape[1],):
            return []
        scores = matrix @ question
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        with self._connection() as conn:
            for position in np.argsort(-scores, kind="stable"):
                if len(rows) >= _VECTOR_RESULT_LIMIT:
                    break
                position = int(position)
                ref = source_refs[position]
                if ref in seen:
                    continue  # a nearer chunk of this source was already judged
                seen.add(ref)
                kind, _, resource_id = ref.partition(":")
                if kind not in selected or ref in excluded:
                    continue
                if project and not self._ref_in_project(conn, kind, resource_id, project):
                    continue
                source = current_source(conn, ref)
                if source is None:
                    continue
                occurred_at = str(source.occurred_at or "")
                if not self._in_time(kind, occurred_at, start, end):
                    continue
                _sha, fresh = prepare_current(source)
                chunk = next(
                    (
                        item for item in fresh
                        if item["id"] == chunk_ids[position]
                        and item["content_sha"] == chunk_shas[position]
                    ),
                    None,
                )
                if chunk is None:
                    continue
                source_ref = ref
                if kind == "thread" and str(chunk["anchor"] or ""):
                    # The keyword pass names the matching message; so does this.
                    source_ref = f"{ref}#{chunk['anchor']}"
                score = float(scores[position])
                rows.append(
                    {
                        "kind": kind,
                        "source_ref": source_ref,
                        "title": _redacted(source.title),
                        "snippet": str(chunk["text"])[:420],
                        "occurred_at": occurred_at,
                        "project_id": project or self._project_of(conn, kind, resource_id),
                        "bm25": 0.0,
                        "normalized_score": max(0.0, min(1.0, score)),
                        "kind_rank": len(rows) + 1,
                        "retrieval_origin": "vector",
                    }
                )
        return rows

    @classmethod
    def _ref_in_project(
        cls, conn: sqlite3.Connection, kind: str, resource_id: str, project: str
    ) -> bool:
        """The project rule of the keyword pass, for one ref."""
        spec = _ECOSYSTEM_SPECS.get(kind)
        if spec is None:
            return cls._in_project(conn, kind, resource_id, project)
        clause = spec["project"]
        return (
            conn.execute(
                f"SELECT 1 FROM {spec['table']} {spec['alias']}"
                f" WHERE {spec['id']}=? AND {clause}",
                [resource_id, *([project] * clause.count("?"))],
            ).fetchone()
            is not None
        )

    @staticmethod
    def _project_of(conn: sqlite3.Connection, kind: str, resource_id: str) -> Optional[str]:
        """The project a hit names when the search has no project scope."""
        spec = _ECOSYSTEM_SPECS.get(kind) or (
            _RECENT_SPECS.get(kind) if kind != "thread" else None
        )
        if spec is None:
            return None
        row = conn.execute(
            f"SELECT {spec['project_id']} FROM {spec['table']} {spec['alias']}"
            f" WHERE {spec['id']}=?",
            (resource_id,),
        ).fetchone()
        return str(row[0]) if row is not None and row[0] else None

    @staticmethod
    def _in_time(kind: str, occurred_at: str, start: Optional[str], end: Optional[str]) -> bool:
        if not start and not end:
            return True
        if kind == "thread":
            # A thread time is 'YYYY-MM-DD HH:MM:SS'; compare like with like.
            def norm(value: str) -> str:
                return value.replace("T", " ")[:19]

            value = norm(occurred_at)
            return not ((start and value < norm(start)) or (end and value > norm(end)))
        return not ((start and occurred_at < start) or (end and occurred_at > end))

    @staticmethod
    def _normalize_kinds(kinds: Optional[Iterable[str]]) -> tuple[str, ...]:
        if kinds is None:
            return tuple(_KIND_ORDER)
        if isinstance(kinds, str):
            values = kinds.split(",")
        else:
            values = list(kinds)
        cleaned = tuple(
            dict.fromkeys(
                str(value).strip().lower() for value in values if str(value).strip()
            )
        )
        invalid = set(cleaned) - _VALID_KINDS
        if invalid:
            raise ValueError("unknown memory kind(s): " + ", ".join(sorted(invalid)))
        if not cleaned:
            raise ValueError("at least one memory kind is required")
        return cleaned

    @staticmethod
    def _recency_key(value: str) -> tuple[int, ...]:
        # ISO-8601 timestamps sort lexically within the store's canonical shapes;
        # invert code points so ascending tuple sort is newest-first.
        return tuple(-ord(char) for char in value)

    @staticmethod
    def _decision_rows(conn, match, project, start, end) -> list[dict[str, Any]]:
        clauses = ["decisions_memory_fts MATCH ?", _not_parked("d.source_meeting_id")]
        params: list[Any] = [match]
        if project:
            clauses.append(
                """(d.project_key=?
                     OR EXISTS (SELECT 1 FROM project_resources pr
                                WHERE pr.project_id=?
                                  AND pr.resource_ref='decision:'||d.id
                                  AND pr.deleted=0)
                     OR EXISTS (SELECT 1 FROM meeting_projects mp
                                WHERE mp.project_id=?
                                  AND mp.meeting_id=d.source_meeting_id))"""
            )
            params.extend((project, project, project))
        if start:
            clauses.append("d.decided_at>=?")
            params.append(start)
        if end:
            clauses.append("d.decided_at<=?")
            params.append(end)
        rows = conn.execute(
            f"""SELECT 'decision' kind,'decision:'||d.id source_ref,
                       d.text title,
                       snippet(decisions_memory_fts,-1,'<mark>','</mark>',' … ',24) snippet,
                       d.decided_at occurred_at,d.project_key project_id,
                       bm25(decisions_memory_fts,1.0,0.7,0.5) bm25
                FROM decisions_memory_fts JOIN decisions d ON d.id=decisions_memory_fts.source_id
                WHERE {" AND ".join(clauses)}
                ORDER BY bm25 ASC,d.decided_at DESC,d.id ASC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _artifact_rows(conn, match, project, start, end) -> list[dict[str, Any]]:
        clauses = ["artifacts_memory_fts MATCH ?", _not_parked("a.meeting_id")]
        params: list[Any] = [match]
        if project:
            clauses.append("""(EXISTS (SELECT 1 FROM project_resources pr
                              WHERE pr.project_id=? AND pr.resource_ref='artifact:'||a.id AND pr.deleted=0)
                         OR EXISTS (SELECT 1 FROM meeting_projects mp
                              WHERE mp.project_id=? AND mp.meeting_id=a.meeting_id)
                         OR EXISTS (SELECT 1 FROM project_resources pm
                              WHERE pm.project_id=? AND pm.deleted=0 AND a.meeting_id IS NOT NULL
                                AND pm.resource_ref IN ('meeting:'||a.meeting_id,'transcript:'||a.meeting_id)))""")
            params.extend((project, project, project))
        if start:
            clauses.append("a.updated_at>=?")
            params.append(start)
        if end:
            clauses.append("a.updated_at<=?")
            params.append(end)
        rows = conn.execute(
            f"""SELECT 'artifact' kind,'artifact:'||a.id source_ref,a.title,
                       snippet(artifacts_memory_fts,-1,'<mark>','</mark>',' … ',24) snippet,
                       a.updated_at occurred_at,
                       (SELECT pr.project_id FROM project_resources pr
                        WHERE pr.resource_ref='artifact:'||a.id AND pr.deleted=0
                        ORDER BY pr.project_id LIMIT 1) project_id,
                       bm25(artifacts_memory_fts,1.0,2.0,0.8) bm25
                FROM artifacts_memory_fts JOIN artifacts a ON a.id=artifacts_memory_fts.source_id
                WHERE {" AND ".join(clauses)}
                ORDER BY bm25 ASC,a.updated_at DESC,a.id ASC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _meeting_rows(conn, match, project, start, end) -> list[dict[str, Any]]:
        """Recall child transcript segments and return one parent Meeting hit."""
        clauses = ["segments_fts MATCH ?"]
        params: list[Any] = [match]
        if project:
            clauses.append(
                """(EXISTS (SELECT 1 FROM meeting_projects mp
                              WHERE mp.project_id=? AND mp.meeting_id=m.id)
                     OR EXISTS (SELECT 1 FROM project_resources pr
                              WHERE pr.project_id=? AND pr.deleted=0
                                AND pr.resource_ref IN
                                    ('meeting:'||m.id,'transcript:'||m.id)))"""
            )
            params.extend((project, project))
        if start:
            clauses.append("m.started_at>=?")
            params.append(start)
        if end:
            clauses.append("m.started_at<=?")
            params.append(end)
        rows = conn.execute(
            f"""WITH base AS (
                    SELECT m.id meeting_id,COALESCE(m.title,m.id) title,
                           m.started_at occurred_at,
                           bm25(segments_fts,1.0,0.4) bm25_val,
                           snippet(segments_fts,-1,'<mark>','</mark>',' … ',28) snippet
                    FROM segments_fts
                    JOIN segments s ON s.id=segments_fts.rowid
                    JOIN meetings m ON m.id=s.meeting_id
                    WHERE m.parked = 0 AND {" AND ".join(clauses)}
                ),
                ranked AS (
                    SELECT *,ROW_NUMBER() OVER (
                        PARTITION BY meeting_id ORDER BY bm25_val
                    ) rn FROM base
                )
                SELECT 'meeting' kind,'meeting:'||r.meeting_id source_ref,
                       r.title,r.snippet,r.occurred_at,
                       (SELECT mp.project_id FROM meeting_projects mp
                        WHERE mp.meeting_id=r.meeting_id
                        ORDER BY mp.project_id LIMIT 1) project_id,
                       r.bm25_val bm25
                FROM ranked r WHERE r.rn=1
                ORDER BY bm25 ASC,r.occurred_at DESC,r.meeting_id ASC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _meeting_summary_rows(conn, terms, project, start, end) -> list[dict[str, Any]]:
        """Meetings whose summary or topics hold a query word.

        The transcript has its own FTS corpus (`_meeting_rows`). The summary
        and topics stay canonical (`intel_snapshots`, `topics`) and are read
        with the same bounded LIKE pass the feature stores use.
        """
        haystack = f"lower({_MEETING_SUMMARY}||' '||{_MEETING_TOPICS})"
        patterns = [f"%{term.casefold()}%" for term in terms]
        clauses = [
            "m.parked = 0",
            "(" + " OR ".join(f"{haystack} LIKE ?" for _ in patterns) + ")",
        ]
        params: list[Any] = list(patterns)
        if project:
            clauses.append(
                """(EXISTS (SELECT 1 FROM meeting_projects mp
                              WHERE mp.project_id=? AND mp.meeting_id=m.id)
                     OR EXISTS (SELECT 1 FROM project_resources pr
                              WHERE pr.project_id=? AND pr.deleted=0
                                AND pr.resource_ref IN
                                    ('meeting:'||m.id,'transcript:'||m.id)))"""
            )
            params.extend((project, project))
        if start:
            clauses.append("m.started_at>=?")
            params.append(start)
        if end:
            clauses.append("m.started_at<=?")
            params.append(end)
        score = (
            "-("
            + "+".join(f"CASE WHEN {haystack} LIKE ? THEN 1 ELSE 0 END" for _ in patterns)
            + ")"
        )
        rows = conn.execute(
            f"""SELECT 'meeting' kind,'meeting:'||m.id source_ref,
                       COALESCE(m.title,m.id) title,
                       substr(trim({_MEETING_SUMMARY}||' '||{_MEETING_TOPICS}),1,420) snippet,
                       m.started_at occurred_at,
                       (SELECT mp.project_id FROM meeting_projects mp
                        WHERE mp.meeting_id=m.id
                        ORDER BY mp.project_id LIMIT 1) project_id,
                       {score} bm25
                FROM meetings m
                WHERE {" AND ".join(clauses)}
                ORDER BY bm25 ASC,m.started_at DESC,m.id ASC""",
            [*patterns, *params],
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _note_rows(conn, match, project, start, end) -> list[dict[str, Any]]:
        # HS-200-10 (F0): belt as well as braces.  Corpus exclusion (L1) is the
        # construction; this predicate is the belt that survives a botched
        # trigger refresh on an older database.  Two independent mechanisms,
        # because the retrieval map is a floor and not a ceiling.
        clauses = [
            "notes_memory_fts MATCH ?",
            "NOT EXISTS (SELECT 1 FROM context_promotions cp"
            " WHERE cp.target_ref = 'note:' || n.id)",
        ]
        params: list[Any] = [match]
        if project:
            clauses.append(
                "EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=? AND pr.resource_ref='note:'||n.id AND pr.deleted=0)"
            )
            params.append(project)
        if start:
            clauses.append("n.updated_at>=?")
            params.append(start)
        if end:
            clauses.append("n.updated_at<=?")
            params.append(end)
        rows = conn.execute(
            f"""SELECT 'note' kind,'note:'||n.id source_ref,n.title,
                       snippet(notes_memory_fts,-1,'<mark>','</mark>',' … ',24) snippet,
                       n.updated_at occurred_at,
                       (SELECT pr.project_id FROM project_resources pr
                        WHERE pr.resource_ref='note:'||n.id AND pr.deleted=0
                        ORDER BY pr.project_id LIMIT 1) project_id,
                       bm25(notes_memory_fts,1.0,2.0,0.8) bm25
                FROM notes_memory_fts JOIN notes n ON n.id=notes_memory_fts.source_id
                WHERE {" AND ".join(clauses)}
                ORDER BY bm25 ASC,n.updated_at DESC,n.id ASC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _thread_rows(conn, match, project, start, end) -> list[dict[str, Any]]:
        clauses = ["thread_messages_fts MATCH ?"]
        params: list[Any] = [match]
        if project:
            # A Thread belongs in a Project result only when the thread itself,
            # an explicit Project ref, or one of its frozen source refs belongs
            # to that Project.  A lexical hit elsewhere on the Desk must not
            # leak into a scoped Project search.
            clauses.append(
                """(EXISTS (SELECT 1 FROM project_resources ptr
                              WHERE ptr.project_id=? AND ptr.deleted=0
                                AND ptr.resource_ref='thread:'||t.id)
                     OR EXISTS (SELECT 1 FROM thread_refs tr
                                WHERE tr.thread_id=t.id AND (
                                  (tr.ref_kind='project' AND tr.ref_id=?)
                                  OR EXISTS (SELECT 1 FROM project_resources pr
                                      WHERE pr.project_id=? AND pr.deleted=0
                                        AND pr.resource_ref=tr.ref_kind||':'||tr.ref_id)
                                  OR EXISTS (SELECT 1 FROM meeting_projects mp
                                      WHERE mp.project_id=? AND mp.meeting_id=tr.ref_id
                                        AND tr.ref_kind IN ('meeting','transcript'))
                                )))"""
            )
            params.extend((project, project, project, project))
        if start:
            clauses.append("t.updated_at>=CAST(strftime('%s',?) AS REAL)")
            params.append(start)
        if end:
            clauses.append("t.updated_at<=CAST(strftime('%s',?) AS REAL)")
            params.append(end)
        # FTS auxiliary functions (bm25, snippet) must be computed in the
        # same query level as the MATCH, so pre-compute them in the first
        # CTE and then window-rank over the materialized column.
        rows = conn.execute(
            f"""WITH base AS (
                    SELECT t.id thread_id, t.title, m.id message_id,
                           datetime(t.updated_at,'unixepoch') occurred_at,
                           bm25(thread_messages_fts,1.0) bm25_val,
                           snippet(thread_messages_fts,-1,'<mark>','</mark>',' … ',24) snippet
                    FROM thread_messages_fts
                    JOIN thread_message_parts p ON p.rowid=thread_messages_fts.rowid
                    JOIN thread_messages m ON m.id=p.message_id
                    JOIN threads t ON t.id=m.thread_id
                    WHERE {" AND ".join(clauses)}
                      AND m.deleted_at IS NULL
                      AND t.deleted_at IS NULL
                      AND p.sensitive=0
                      AND p.draft=0
                ),
                ranked AS (
                    SELECT *, ROW_NUMBER() OVER (
                        PARTITION BY thread_id ORDER BY bm25_val
                    ) rn FROM base
                )
                SELECT 'thread' kind,
                       'thread:'||thread_id||'#'||message_id source_ref,
                       title,snippet,occurred_at,NULL project_id,
                       bm25_val bm25
                FROM ranked WHERE rn=1
                ORDER BY bm25 ASC,occurred_at DESC,thread_id ASC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _ecosystem_rows(
        conn: sqlite3.Connection,
        kind: str,
        terms: list[str],
        project: Optional[str],
        start: Optional[str],
        end: Optional[str],
    ) -> list[dict[str, Any]]:
        """Search content-bearing feature stores that do not own an FTS table.

        These stores are deliberately kept canonical rather than copied into a
        second index.  The bounded LIKE pass is the compatibility layer until a
        source grows large enough to justify its own FTS corpus; its score is
        still normalized and interleaved by the same ranking contract.
        """
        specs = _ECOSYSTEM_SPECS
        spec = specs[kind]
        haystack = (
            f"lower(COALESCE({spec['title']},'')||' '||COALESCE({spec['body']},''))"
        )
        patterns = [f"%{term.casefold()}%" for term in terms]
        clauses = [
            spec["active"],
            "(" + " OR ".join(f"{haystack} LIKE ?" for _ in patterns) + ")",
        ]
        where_params: list[Any] = list(patterns)
        if project:
            clauses.append(spec["project"])
            where_params.extend([project] * spec["project"].count("?"))
        if start:
            clauses.append(f"{spec['time']}>=?")
            where_params.append(start)
        if end:
            clauses.append(f"{spec['time']}<=?")
            where_params.append(end)
        score = (
            "-("
            + "+".join(
                f"CASE WHEN {haystack} LIKE ? THEN 1 ELSE 0 END" for _ in patterns
            )
            + ")"
        )
        rows = conn.execute(
            f"""SELECT '{kind}' kind,'{kind}:'||{spec["id"]} source_ref,
                       {spec["title"]} title,substr({spec["body"]},1,420) snippet,
                       {spec["time"]} occurred_at,{spec["project_id"]} project_id,
                       {score} bm25
                FROM {spec["table"]} {spec["alias"]}
                WHERE {" AND ".join(clauses)}
                ORDER BY bm25 ASC,occurred_at DESC,{spec["id"]} ASC""",
            [*patterns, *where_params],
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _base_ref(source_ref: str) -> str:
        """Return the parent object ref for a child-level search hit."""
        ref = str(source_ref or "")
        return ref.split("#", 1)[0] if ref.startswith("thread:") else ref

    @staticmethod
    def _canonical_relation_ref(source_type: str, source_ref: str) -> Optional[str]:
        """Adapt persisted typed-edge shapes to the memory ``kind:id`` contract.

        Older feature stores intentionally keep type and id in separate columns;
        newer stores sometimes persist an already-qualified ref. Accept both,
        but only return kinds that memory can safely hydrate.
        """
        raw_kind = str(source_type or "").strip().lower()
        raw_ref = str(source_ref or "").strip()
        if not raw_ref:
            return None
        qualified_kind, separator, qualified_id = raw_ref.partition(":")
        if separator and qualified_kind in _VALID_KINDS and qualified_id:
            return f"{qualified_kind}:{qualified_id}"
        aliases = {
            "transcript": "meeting",
            "predecessor": "decision_record",
            "successor": "decision_record",
        }
        kind = aliases.get(raw_kind, raw_kind)
        if kind not in _VALID_KINDS:
            return None
        return f"{kind}:{raw_ref}"

    @classmethod
    def _expand_related_rows(
        cls,
        conn: sqlite3.Connection,
        lexical_rows: list[dict[str, Any]],
        *,
        selected: tuple[str, ...],
        project: Optional[str],
        start: Optional[str],
        end: Optional[str],
        excluded: set[str],
    ) -> list[dict[str, Any]]:
        """Follow real one-hop lineage and hydrate bounded neighbour objects.

        RAGFlow's compiled expansion searches seed entities, follows adjacent
        relations, then loads the passages behind the neighbouring entities.
        HoldSpeak can make that stronger and cheaper: its nodes are already
        typed objects and its edges are durable provenance, so this pass never
        calls a model and never manufactures an inferred relation.
        """
        if not lexical_rows:
            return []
        lexical_refs = {cls._base_ref(str(row["source_ref"])) for row in lexical_rows}
        candidates: dict[str, dict[str, Any]] = {}
        for seed in lexical_rows[:_RELATION_SEED_LIMIT]:
            seed_ref = cls._base_ref(str(seed["source_ref"]))
            seed_score = max(0.25, float(seed.get("normalized_score") or 0.0))
            eligible: list[tuple[str, str, float]] = []
            for neighbour_ref, relationship, weight in cls._relation_candidates(
                conn, seed_ref
            ):
                neighbour_ref = cls._base_ref(neighbour_ref)
                kind = neighbour_ref.partition(":")[0]
                if (
                    kind not in selected
                    or neighbour_ref in lexical_refs
                    or neighbour_ref == seed_ref
                    or neighbour_ref in excluded
                ):
                    continue
                eligible.append((neighbour_ref, relationship, weight))
            eligible.sort(key=lambda edge: (-edge[2], edge[0], edge[1]))
            for neighbour_ref, relationship, weight in eligible[
                :_RELATION_NEIGHBOURS_PER_SEED
            ]:
                graph_score = min(1.0, seed_score * weight)
                prior = candidates.get(neighbour_ref)
                if prior is not None and float(prior["graph_score"]) >= graph_score:
                    continue
                candidates[neighbour_ref] = {
                    "related_to": seed_ref,
                    "relationship": relationship,
                    "graph_score": graph_score,
                }

        kind_ranks = {
            kind: max(
                (int(row["kind_rank"]) for row in lexical_rows if row["kind"] == kind),
                default=0,
            )
            for kind in selected
        }
        expanded: list[dict[str, Any]] = []
        ordered = sorted(
            candidates.items(),
            key=lambda item: (-float(item[1]["graph_score"]), item[0]),
        )
        for source_ref, edge in ordered:
            if len(expanded) >= _RELATION_RESULT_LIMIT:
                break
            row = cls._load_related_row(conn, source_ref, project=project)
            if row is None:
                continue
            occurred_at = str(row["occurred_at"] or "")
            if start and occurred_at < start:
                continue
            if end and occurred_at > end:
                continue
            kind = str(row["kind"])
            kind_ranks[kind] = kind_ranks.get(kind, 0) + 1
            row.update(edge)
            row.update(
                {
                    "bm25": 0.0,
                    "normalized_score": float(edge["graph_score"]),
                    "kind_rank": kind_ranks[kind],
                    "retrieval_origin": "relationship",
                }
            )
            expanded.append(row)
        return expanded

    @classmethod
    def _relation_candidates(
        cls, conn: sqlite3.Connection, seed_ref: str
    ) -> list[tuple[str, str, float]]:
        kind, _, resource_id = seed_ref.partition(":")
        if not resource_id:
            return []
        out: list[tuple[str, str, float]] = []
        if kind == "decision":
            row = conn.execute(
                """SELECT source_artifact_id,source_meeting_id,superseded_by
                   FROM decisions WHERE id=? AND deleted=0""",
                (resource_id,),
            ).fetchone()
            if row:
                if row["source_artifact_id"]:
                    out.append(
                        (
                            f"artifact:{row['source_artifact_id']}",
                            "source_artifact",
                            0.95,
                        )
                    )
                if row["source_meeting_id"]:
                    out.append(
                        (f"meeting:{row['source_meeting_id']}", "source_meeting", 0.95)
                    )
                if row["superseded_by"]:
                    out.append(
                        (f"decision:{row['superseded_by']}", "superseded_by", 0.85)
                    )
            out.extend(
                (f"decision:{row[0]}", "supersedes", 0.85)
                for row in conn.execute(
                    "SELECT id FROM decisions WHERE superseded_by=? AND deleted=0",
                    (resource_id,),
                )
            )
        elif kind == "artifact":
            row = conn.execute(
                "SELECT meeting_id FROM artifacts WHERE id=?", (resource_id,)
            ).fetchone()
            if row and row["meeting_id"]:
                out.append((f"meeting:{row['meeting_id']}", "source_meeting", 0.9))
            out.extend(
                (f"decision:{row[0]}", "projects_decision", 0.9)
                for row in conn.execute(
                    "SELECT id FROM decisions WHERE source_artifact_id=? AND deleted=0",
                    (resource_id,),
                )
            )
        elif kind == "meeting":
            out.extend(
                (f"artifact:{row[0]}", "meeting_artifact", 0.8)
                for row in conn.execute(
                    "SELECT id FROM artifacts WHERE meeting_id=? ORDER BY updated_at DESC LIMIT 16",
                    (resource_id,),
                )
            )
            out.extend(
                (f"decision:{row[0]}", "meeting_decision", 0.9)
                for row in conn.execute(
                    """SELECT id FROM decisions
                       WHERE source_meeting_id=? AND deleted=0
                       ORDER BY decided_at DESC LIMIT 16""",
                    (resource_id,),
                )
            )
        elif kind == "thread":
            out.extend(
                (f"{row['ref_kind']}:{row['ref_id']}", "thread_reference", 0.75)
                for row in conn.execute(
                    """SELECT ref_kind,ref_id FROM thread_refs
                       WHERE thread_id=? AND ref_kind IN
                           ('meeting','artifact','decision','note','thread',
                            'decision_record','desk_decision','action','project_item',
                            'workbench_item','cadence')
                       ORDER BY created_at DESC LIMIT 16""",
                    (resource_id,),
                )
            )
        elif kind == "decision_record":
            for row in conn.execute(
                """SELECT source_type,source_ref FROM decision_record_sources
                   WHERE record_id=? ORDER BY created_at,id LIMIT 16""",
                (resource_id,),
            ):
                related = cls._canonical_relation_ref(
                    str(row["source_type"]), str(row["source_ref"])
                )
                if related:
                    out.append((related, "decision_record_source", 0.9))
            for row in conn.execute(
                """SELECT work_type,work_ref FROM decision_record_work
                   WHERE record_id=? ORDER BY created_at,id LIMIT 16""",
                (resource_id,),
            ):
                related = cls._canonical_relation_ref(
                    str(row["work_type"]), str(row["work_ref"])
                )
                if related:
                    out.append((related, "affected_work", 0.75))
        elif kind == "desk_decision":
            out.extend(
                (f"decision_record:{row[0]}", "canonical_record", 0.95)
                for row in conn.execute(
                    "SELECT id FROM decision_records WHERE source_type='desk' AND source_id=? AND deleted=0 LIMIT 4",
                    (resource_id,),
                )
            )
        elif kind == "action":
            row = conn.execute(
                "SELECT meeting_id FROM action_items WHERE id=?", (resource_id,)
            ).fetchone()
            if row and row["meeting_id"]:
                out.append((f"meeting:{row['meeting_id']}", "source_meeting", 0.9))
            out.extend(
                (f"decision:{row[0]}", "decision_commitment", 0.9)
                for row in conn.execute(
                    "SELECT decision_id FROM decision_commitments WHERE action_item_id=? LIMIT 8",
                    (resource_id,),
                )
            )
        elif kind == "workbench_item":
            row = conn.execute(
                "SELECT result_artifact_id,grounding_json FROM workbench_items WHERE id=?",
                (resource_id,),
            ).fetchone()
            if row:
                if row["result_artifact_id"]:
                    out.append(
                        (
                            f"artifact:{row['result_artifact_id']}",
                            "result_artifact",
                            0.9,
                        )
                    )
                try:
                    grounding = json.loads(str(row["grounding_json"] or "{}"))
                except (TypeError, ValueError):
                    grounding = {}
                for ref in (
                    grounding.get("refs", []) if isinstance(grounding, dict) else []
                ):
                    if isinstance(ref, str) and ":" in ref:
                        out.append((ref, "workbench_grounding", 0.75))
        elif kind == "cadence":
            out.extend(
                (f"{row['kind']}:{row['ref_id']}", "cadence_evidence", 0.8)
                for row in conn.execute(
                    "SELECT kind,ref_id FROM cadence_evidence_refs WHERE loop_id=? LIMIT 16",
                    (resource_id,),
                )
            )

        # Decision Record source/work tables store type and raw id separately.
        # Traverse those authoritative edges in reverse as well, so searching a
        # source Meeting or Artifact can recover the durable decision it supports.
        out.extend(
            (f"decision_record:{row[0]}", "supports_decision_record", 0.9)
            for row in conn.execute(
                """SELECT DISTINCT drs.record_id
                   FROM decision_record_sources drs
                   JOIN decision_records dr ON dr.id=drs.record_id
                   WHERE dr.deleted=0 AND drs.source_type=?
                     AND drs.source_ref IN (?,?)
                   ORDER BY dr.updated_at DESC LIMIT 16""",
                (kind, resource_id, seed_ref),
            )
        )
        if kind == "decision_record":
            out.extend(
                (f"decision_record:{row[0]}", "decision_record_lineage", 0.85)
                for row in conn.execute(
                    """SELECT DISTINCT drs.record_id
                       FROM decision_record_sources drs
                       JOIN decision_records dr ON dr.id=drs.record_id
                       WHERE dr.deleted=0
                         AND drs.source_type IN ('predecessor','successor')
                         AND drs.source_ref IN (?,?)
                       ORDER BY dr.updated_at DESC LIMIT 16""",
                    (resource_id, seed_ref),
                )
            )
        out.extend(
            (f"decision_record:{row[0]}", "affected_work_for_record", 0.75)
            for row in conn.execute(
                """SELECT DISTINCT drw.record_id
                   FROM decision_record_work drw
                   JOIN decision_records dr ON dr.id=drw.record_id
                   WHERE dr.deleted=0 AND drw.work_type=?
                     AND drw.work_ref IN (?,?)
                   ORDER BY dr.updated_at DESC LIMIT 16""",
                (kind, resource_id, seed_ref),
            )
        )

        # The reverse edge makes a grounded conversation discoverable from the
        # object it discussed.  import_hash and other internal refs never join.
        out.extend(
            (f"thread:{row[0]}", "referenced_by_thread", 0.65)
            for row in conn.execute(
                """SELECT DISTINCT tr.thread_id FROM thread_refs tr
                   JOIN threads t ON t.id=tr.thread_id
                   WHERE tr.ref_kind=? AND tr.ref_id=? AND t.deleted_at IS NULL
                   ORDER BY t.updated_at DESC LIMIT 16""",
                (kind, resource_id),
            )
        )
        return out

    @classmethod
    def _load_related_row(
        cls,
        conn: sqlite3.Connection,
        source_ref: str,
        *,
        project: Optional[str],
    ) -> Optional[dict[str, Any]]:
        kind, _, resource_id = source_ref.partition(":")
        if not resource_id or not cls._in_project(conn, kind, resource_id, project):
            return None
        if kind == "decision":
            row = conn.execute(
                """SELECT 'decision' kind,'decision:'||id source_ref,text title,
                          substr(text||CASE WHEN rationale IS NULL OR rationale=''
                            THEN '' ELSE ' — '||rationale END,1,420) snippet,
                          decided_at occurred_at,project_key project_id
                   FROM decisions
                   WHERE id=? AND deleted=0 AND source_state='linked'
                     AND """ + _not_parked("decisions.source_meeting_id"),
                (resource_id,),
            ).fetchone()
        elif kind == "artifact":
            row = conn.execute(
                """SELECT 'artifact' kind,'artifact:'||id source_ref,title,
                          substr(body_markdown,1,420) snippet,updated_at occurred_at,
                          (SELECT project_id FROM project_resources
                           WHERE resource_ref='artifact:'||artifacts.id AND deleted=0
                           ORDER BY project_id LIMIT 1) project_id
                   FROM artifacts WHERE id=? AND """ + _not_parked("artifacts.meeting_id"),
                (resource_id,),
            ).fetchone()
        elif kind == "meeting":
            row = conn.execute(
                """SELECT 'meeting' kind,'meeting:'||m.id source_ref,
                          COALESCE(m.title,m.id) title,
                          COALESCE((SELECT substr(group_concat(speaker||': '||text,' '),1,420)
                                    FROM (SELECT speaker,text FROM segments
                                          WHERE meeting_id=m.id ORDER BY start_time LIMIT 6)), '') snippet,
                          m.started_at occurred_at,
                          (SELECT project_id FROM meeting_projects
                           WHERE meeting_id=m.id ORDER BY project_id LIMIT 1) project_id
                   FROM meetings m WHERE m.id=? AND m.parked=0""",
                (resource_id,),
            ).fetchone()
        elif kind == "note":
            row = conn.execute(
                """SELECT 'note' kind,'note:'||id source_ref,title,
                          substr(body_markdown,1,420) snippet,updated_at occurred_at,
                          (SELECT project_id FROM project_resources
                           WHERE resource_ref='note:'||notes.id AND deleted=0
                           ORDER BY project_id LIMIT 1) project_id
                   FROM notes WHERE id=? AND deleted=0""",
                (resource_id,),
            ).fetchone()
        elif kind == "thread":
            row = conn.execute(
                """SELECT 'thread' kind,'thread:'||t.id source_ref,t.title,
                          COALESCE((SELECT substr(group_concat(text,' '),1,420)
                                    FROM (SELECT p.text text
                                          FROM thread_messages m
                                          JOIN thread_message_parts p ON p.message_id=m.id
                                          WHERE m.thread_id=t.id AND m.deleted_at IS NULL
                                            AND p.kind='text' AND p.text IS NOT NULL
                                            AND p.sensitive=0 AND p.draft=0
                                          ORDER BY m.created_at,p.ordinal LIMIT 8)), '') snippet,
                          datetime(t.updated_at,'unixepoch') occurred_at,
                          NULL project_id
                   FROM threads t WHERE t.id=? AND t.deleted_at IS NULL""",
                (resource_id,),
            ).fetchone()
        elif kind == "decision_record":
            row = conn.execute(
                """SELECT 'decision_record' kind,'decision_record:'||r.id source_ref,
                          r.decision_text title,
                          substr(COALESCE(r.rationale,'')||' '||COALESCE(r.alternatives,''),1,420) snippet,
                          r.updated_at occurred_at,
                          (SELECT project_id FROM project_resources WHERE resource_ref='decision_record:'||r.id AND deleted=0 ORDER BY project_id LIMIT 1) project_id
                   FROM decision_records r WHERE r.id=? AND r.deleted=0""",
                (resource_id,),
            ).fetchone()
        elif kind == "desk_decision":
            row = conn.execute(
                """SELECT 'desk_decision' kind,'desk_decision:'||d.id source_ref,
                          CASE WHEN d.title='' THEN d.decision_markdown ELSE d.title END title,
                          substr(d.context_markdown||' '||d.decision_markdown||' '||d.consequences_markdown,1,420) snippet,
                          d.updated_at occurred_at,
                          (SELECT project_id FROM project_resources WHERE resource_ref IN ('desk_decision:'||d.id,'decision:'||d.id) AND deleted=0 ORDER BY project_id LIMIT 1) project_id
                   FROM desk_decisions d WHERE d.id=? AND d.deleted=0""",
                (resource_id,),
            ).fetchone()
        elif kind == "action":
            row = conn.execute(
                """SELECT 'action' kind,'action:'||a.id source_ref,a.task title,
                          substr(a.task||' '||COALESCE(a.owner,'')||' '||COALESCE(a.due,'')||' '||a.status,1,420) snippet,
                          COALESCE(a.completed_at,a.created_at) occurred_at,
                          COALESCE((SELECT project_id FROM meeting_projects WHERE meeting_id=a.meeting_id ORDER BY project_id LIMIT 1),(SELECT project_id FROM project_resources WHERE resource_ref='action:'||a.id AND deleted=0 ORDER BY project_id LIMIT 1)) project_id
                   FROM action_items a WHERE a.id=? AND """ + _not_parked("a.meeting_id"),
                (resource_id,),
            ).fetchone()
        elif kind == "project_item":
            row = conn.execute(
                """SELECT 'project_item' kind,'project_item:'||p.id source_ref,p.title,
                          substr(COALESCE(p.summary,'')||' '||COALESCE(p.details_json,''),1,420) snippet,
                          p.updated_at occurred_at,p.project_id
                   FROM project_items p WHERE p.id=?""",
                (resource_id,),
            ).fetchone()
        elif kind == "workbench_item":
            row = conn.execute(
                """SELECT 'workbench_item' kind,'workbench_item:'||w.id source_ref,w.title,
                          substr(w.body||' '||COALESCE(w.result,''),1,420) snippet,
                          w.last_modified occurred_at,
                          COALESCE((SELECT project_id FROM project_resources WHERE resource_ref='workbench_item:'||w.id AND deleted=0 ORDER BY project_id LIMIT 1),(SELECT project_id FROM project_resources WHERE resource_ref='workbench:'||w.workbench_id AND deleted=0 ORDER BY project_id LIMIT 1)) project_id
                   FROM workbench_items w WHERE w.id=? AND w.status!='dismissed' AND w.parked=0""",
                (resource_id,),
            ).fetchone()
        elif kind == "cadence":
            row = conn.execute(
                """SELECT 'cadence' kind,'cadence:'||c.id source_ref,c.title,
                          substr(c.summary||' '||c.status||' '||c.priority,1,420) snippet,
                          c.updated_at occurred_at,c.project project_id
                   FROM cadence_loops c WHERE c.id=? AND c.status!='killed'""",
                (resource_id,),
            ).fetchone()
        else:
            return None
        if row is None:
            return None
        result = dict(row)
        if project:
            result["project_id"] = project
        return result

    @staticmethod
    def _in_project(
        conn: sqlite3.Connection,
        kind: str,
        resource_id: str,
        project: Optional[str],
    ) -> bool:
        if not project:
            return True
        ref = f"{kind}:{resource_id}"
        if conn.execute(
            """SELECT 1 FROM project_resources
               WHERE project_id=? AND resource_ref=? AND deleted=0""",
            (project, ref),
        ).fetchone():
            return True
        if kind == "desk_decision":
            # The old ref name (`decision:<id>`), still on rows filed before
            # the one-name fix.
            return (
                conn.execute(
                    """SELECT 1 FROM project_resources pr
                       WHERE pr.project_id=? AND pr.deleted=0
                         AND pr.resource_ref='decision:'||?
                         AND EXISTS (SELECT 1 FROM desk_decisions d
                                     WHERE d.id=? AND d.deleted=0)""",
                    (project, resource_id, resource_id),
                ).fetchone()
                is not None
            )
        if kind == "decision":
            return (
                conn.execute(
                    """SELECT 1 FROM decisions d WHERE d.id=? AND d.deleted=0 AND (
                     d.project_key=? OR EXISTS (SELECT 1 FROM meeting_projects mp
                         WHERE mp.project_id=? AND mp.meeting_id=d.source_meeting_id))""",
                    (resource_id, project, project),
                ).fetchone()
                is not None
            )
        if kind == "meeting":
            return (
                conn.execute(
                    "SELECT 1 FROM meeting_projects WHERE project_id=? AND meeting_id=?",
                    (project, resource_id),
                ).fetchone()
                is not None
                or conn.execute(
                    """SELECT 1 FROM project_resources WHERE project_id=? AND deleted=0
                   AND resource_ref='transcript:'||?""",
                    (project, resource_id),
                ).fetchone()
                is not None
            )
        if kind == "artifact":
            return (
                conn.execute(
                    """SELECT 1 FROM artifacts a WHERE a.id=? AND EXISTS (
                     SELECT 1 FROM meeting_projects mp
                     WHERE mp.project_id=? AND mp.meeting_id=a.meeting_id)""",
                    (resource_id, project),
                ).fetchone()
                is not None
            )
        if kind == "thread":
            return (
                conn.execute(
                    """SELECT 1 FROM thread_refs tr WHERE tr.thread_id=? AND (
                     (tr.ref_kind='project' AND tr.ref_id=?)
                     OR EXISTS (SELECT 1 FROM project_resources pr
                         WHERE pr.project_id=? AND pr.deleted=0
                           AND pr.resource_ref=tr.ref_kind||':'||tr.ref_id)
                     OR EXISTS (SELECT 1 FROM meeting_projects mp
                         WHERE mp.project_id=? AND mp.meeting_id=tr.ref_id
                           AND tr.ref_kind IN ('meeting','transcript')))""",
                    (resource_id, project, project, project),
                ).fetchone()
                is not None
            )
        if kind == "project_item":
            return (
                conn.execute(
                    "SELECT 1 FROM project_items WHERE id=? AND project_id=?",
                    (resource_id, project),
                ).fetchone()
                is not None
            )
        if kind == "decision_record":
            return (
                conn.execute(
                    """SELECT 1 FROM decision_record_sources drs
                       WHERE drs.record_id=? AND (
                         (drs.source_type IN ('meeting','transcript') AND EXISTS (
                           SELECT 1 FROM meeting_projects mp
                           WHERE mp.project_id=? AND
                             drs.source_ref IN (mp.meeting_id,'meeting:'||mp.meeting_id,'transcript:'||mp.meeting_id)))
                         OR (drs.source_type='artifact' AND EXISTS (
                           SELECT 1 FROM artifacts a
                           JOIN meeting_projects mp ON mp.meeting_id=a.meeting_id
                           WHERE mp.project_id=? AND
                             drs.source_ref IN (a.id,'artifact:'||a.id)))
                         OR (drs.source_type='artifact' AND EXISTS (
                           SELECT 1 FROM project_resources apr
                           WHERE apr.project_id=? AND apr.deleted=0
                             AND apr.resource_ref LIKE 'artifact:%'
                             AND drs.source_ref IN (
                               substr(apr.resource_ref,10),apr.resource_ref)))
                       )""",
                    (resource_id, project, project, project),
                ).fetchone()
                is not None
            )
        if kind == "action":
            return (
                conn.execute(
                    """SELECT 1 FROM action_items a WHERE a.id=? AND EXISTS (
                       SELECT 1 FROM meeting_projects mp
                       WHERE mp.meeting_id=a.meeting_id AND mp.project_id=?)""",
                    (resource_id, project),
                ).fetchone()
                is not None
            )
        if kind == "cadence":
            return (
                conn.execute(
                    "SELECT 1 FROM cadence_loops WHERE id=? AND project=?",
                    (resource_id, project),
                ).fetchone()
                is not None
            )
        return False


__all__ = [
    "MemoryHit",
    "MemoryRepository",
    "MemorySearchResult",
    "rebuild_memory_index",
]
