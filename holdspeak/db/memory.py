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
}
_VALID_KINDS = frozenset(_KIND_ORDER)
_RELATION_SEED_LIMIT = 32
_RELATION_RESULT_LIMIT = 64
_RELATION_NEIGHBOURS_PER_SEED = 2
_QUERY_TERM_LIMIT = 24
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

    def to_dict(self) -> dict[str, Any]:
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
    """Rebuild all three FTS tables from canonical rows, safely and idempotently."""
    conn.execute("DELETE FROM decisions_memory_fts")
    conn.execute(
        """INSERT INTO decisions_memory_fts(source_id,text,rationale)
           SELECT id,text,COALESCE(rationale,'') FROM decisions
           WHERE deleted=0 AND source_state='linked'"""
    )
    conn.execute("DELETE FROM artifacts_memory_fts")
    conn.execute(
        """INSERT INTO artifacts_memory_fts(source_id,title,body_markdown)
           SELECT id,title,body_markdown FROM artifacts"""
    )
    conn.execute("DELETE FROM notes_memory_fts")
    conn.execute(
        """INSERT INTO notes_memory_fts(source_id,title,body_markdown)
           SELECT id,title,body_markdown FROM notes WHERE deleted=0"""
    )
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

        total = len(interleaved)
        page = interleaved[bounded_offset : bounded_offset + bounded_limit]
        hits = [
            MemoryHit(
                kind=str(row["kind"]),
                source_ref=str(row["source_ref"]),
                title=str(row["title"]),
                snippet=str(row["snippet"]),
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
            expanded_total=max(0, total - lexical_total),
        )

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
        clauses = ["decisions_memory_fts MATCH ?"]
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
        clauses = ["artifacts_memory_fts MATCH ?"]
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
                    WHERE {" AND ".join(clauses)}
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
    def _note_rows(conn, match, project, start, end) -> list[dict[str, Any]]:
        clauses = ["notes_memory_fts MATCH ?"]
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
        specs: dict[str, dict[str, str]] = {
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
                "project_id": "(SELECT pr.project_id FROM project_resources pr WHERE pr.resource_ref='desk_decision:'||d.id AND pr.deleted=0 ORDER BY pr.project_id LIMIT 1)",
                "project": "EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=? AND pr.resource_ref='desk_decision:'||d.id AND pr.deleted=0)",
            },
            "action": {
                "table": "action_items",
                "alias": "a",
                "id": "a.id",
                "title": "a.task",
                "body": "COALESCE(a.owner,'')||' '||COALESCE(a.due,'')||' '||a.status",
                "time": "COALESCE(a.completed_at,a.created_at)",
                "active": "1=1",
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
                "active": "w.status!='dismissed'",
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
        }
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
                   WHERE id=? AND deleted=0 AND source_state='linked'""",
                (resource_id,),
            ).fetchone()
        elif kind == "artifact":
            row = conn.execute(
                """SELECT 'artifact' kind,'artifact:'||id source_ref,title,
                          substr(body_markdown,1,420) snippet,updated_at occurred_at,
                          (SELECT project_id FROM project_resources
                           WHERE resource_ref='artifact:'||artifacts.id AND deleted=0
                           ORDER BY project_id LIMIT 1) project_id
                   FROM artifacts WHERE id=?""",
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
                   FROM meetings m WHERE m.id=?""",
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
                          (SELECT project_id FROM project_resources WHERE resource_ref='desk_decision:'||d.id AND deleted=0 ORDER BY project_id LIMIT 1) project_id
                   FROM desk_decisions d WHERE d.id=? AND d.deleted=0""",
                (resource_id,),
            ).fetchone()
        elif kind == "action":
            row = conn.execute(
                """SELECT 'action' kind,'action:'||a.id source_ref,a.task title,
                          substr(a.task||' '||COALESCE(a.owner,'')||' '||COALESCE(a.due,'')||' '||a.status,1,420) snippet,
                          COALESCE(a.completed_at,a.created_at) occurred_at,
                          COALESCE((SELECT project_id FROM meeting_projects WHERE meeting_id=a.meeting_id ORDER BY project_id LIMIT 1),(SELECT project_id FROM project_resources WHERE resource_ref='action:'||a.id AND deleted=0 ORDER BY project_id LIMIT 1)) project_id
                   FROM action_items a WHERE a.id=?""",
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
                   FROM workbench_items w WHERE w.id=? AND w.status!='dismissed'""",
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
