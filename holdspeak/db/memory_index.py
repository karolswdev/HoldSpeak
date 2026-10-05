"""The memory index tables: ledger, chunks, vectors (MEMORY-DESIGN.md §2).

Every row here is derived.  A write replaces one source's chunks and stamps
its ledger row in ONE transaction, so a reader never sees half a source.
Vectors are plain float32 BLOBs; search is a numpy scan over one matrix per
model, built lazily and rebuilt when the vector rows change.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Iterable, Optional, Sequence

import numpy as np

from .base import BaseRepository

CHUNK_ITEM_KIND = "chunk"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class MemoryIndexRepository(BaseRepository):
    table = "memory_index"

    def __init__(self, connection, container=None):
        super().__init__(connection, container)
        self._matrix_lock = threading.Lock()
        # model_id -> (generation, matrix, chunk ids, source refs, chunk shas)
        self._matrices: dict[str, tuple[int, np.ndarray, list[str], list[str], list[str]]] = {}

    @staticmethod
    def _bump(conn: sqlite3.Connection) -> None:
        """Move the index generation.  Called INSIDE each write transaction,
        so the generation and the rows change together or not at all, and a
        reader on any handle or in any process sees the change."""
        conn.execute(
            "INSERT INTO memory_index_state(key,value) VALUES ('generation',1)"
            " ON CONFLICT(key) DO UPDATE SET value=value+1"
        )

    def generation(self) -> int:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT value FROM memory_index_state WHERE key='generation'"
            ).fetchone()
        return int(row[0]) if row else 0

    # ── ledger ───────────────────────────────────────────────────────

    def ledger(self, kinds: Optional[Iterable[str]] = None) -> dict[str, dict[str, Any]]:
        clause, params = "", []
        if kinds is not None:
            wanted = list(kinds)
            clause = " WHERE kind IN (%s)" % ",".join("?" for _ in wanted)
            params = wanted
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT source_ref,kind,content_sha,chunker_version,state"
                " FROM memory_sources" + clause,
                params,
            ).fetchall()
        return {str(row["source_ref"]): dict(row) for row in rows}

    def ledger_for(self, refs: Sequence[str]) -> dict[str, dict[str, Any]]:
        """The ledger rows of the named sources only."""
        found: dict[str, dict[str, Any]] = {}
        with self._connection() as conn:
            for ref in refs:
                row = conn.execute(
                    "SELECT source_ref,kind,content_sha,chunker_version,state"
                    " FROM memory_sources WHERE source_ref=?",
                    (str(ref),),
                ).fetchone()
                if row is not None:
                    found[str(row["source_ref"])] = dict(row)
        return found

    def replace_source(
        self,
        *,
        source_ref: str,
        kind: str,
        title: str,
        occurred_at: Optional[str],
        content_sha: str,
        chunker_version: int,
        chunks: Sequence[dict[str, Any]],
    ) -> None:
        """Replace one source's chunks and stamp its ledger row, atomically.

        A chunk that keeps its id and its text keeps its vector.  A vector
        whose chunk is gone is removed here; a vector whose chunk changed
        stays until the embed step replaces it, and recall ignores it
        (the ``content_sha`` join in ``matrix``).
        """
        with self._connection() as conn:
            keep = [str(chunk["id"]) for chunk in chunks]
            old = [
                str(row[0])
                for row in conn.execute(
                    "SELECT id FROM memory_chunks WHERE source_ref=?", (source_ref,)
                )
            ]
            gone = [chunk_id for chunk_id in old if chunk_id not in set(keep)]
            self._delete_vectors(conn, gone)
            self._delete_keyword_rows(conn, source_ref)
            conn.execute("DELETE FROM memory_chunks WHERE source_ref=?", (source_ref,))
            conn.executemany(
                "INSERT INTO memory_chunks"
                "(id,source_ref,ordinal,anchor,text,occurred_at,content_sha)"
                " VALUES (?,?,?,?,?,?,?)",
                [
                    (
                        str(chunk["id"]),
                        source_ref,
                        int(chunk["ordinal"]),
                        str(chunk.get("anchor") or ""),
                        str(chunk["text"]),
                        occurred_at,
                        str(chunk["content_sha"]),
                    )
                    for chunk in chunks
                ],
            )
            # The keyword rows, in the same transaction as the chunks.
            conn.execute(
                "INSERT INTO memory_chunks_fts(rowid,text,chunk_id,source_ref)"
                " SELECT rowid,text,id,source_ref FROM memory_chunks WHERE source_ref=?",
                (source_ref,),
            )
            conn.execute(
                "INSERT INTO memory_sources"
                "(source_ref,kind,title,occurred_at,content_sha,chunker_version,state,updated_at)"
                " VALUES (?,?,?,?,?,?,'live',?)"
                " ON CONFLICT(source_ref) DO UPDATE SET kind=excluded.kind,"
                " title=excluded.title,occurred_at=excluded.occurred_at,"
                " content_sha=excluded.content_sha,"
                " chunker_version=excluded.chunker_version,state='live',"
                " updated_at=excluded.updated_at",
                (source_ref, kind, title, occurred_at, content_sha, int(chunker_version), _now()),
            )
            self._bump(conn)

    def mark_gone(self, source_ref: str) -> None:
        """The source was deleted, parked or made sensitive: remove what was
        derived from it and keep the ledger row as ``gone``."""
        with self._connection() as conn:
            ids = [
                str(row[0])
                for row in conn.execute(
                    "SELECT id FROM memory_chunks WHERE source_ref=?", (source_ref,)
                )
            ]
            self._delete_vectors(conn, ids)
            self._delete_keyword_rows(conn, source_ref)
            conn.execute("DELETE FROM memory_chunks WHERE source_ref=?", (source_ref,))
            # Its facts go too, kept ones included, and an entity that only
            # this source named (custody: a source made sensitive or parked
            # leaves no name behind).
            self._delete_facts(conn, source_ref)
            conn.execute(
                "UPDATE memory_sources SET state='gone',extracted_sha=NULL,"
                "extractor_version=NULL,updated_at=? WHERE source_ref=?",
                (_now(), source_ref),
            )
            self._bump(conn)

    @staticmethod
    def _delete_keyword_rows(conn: sqlite3.Connection, source_ref: str) -> None:
        """Remove the source's ``memory_chunks_fts`` rows (by the chunks'
        rowids, read through the source index).  Call BEFORE the chunks go."""
        conn.execute(
            "DELETE FROM memory_chunks_fts WHERE rowid IN"
            " (SELECT rowid FROM memory_chunks WHERE source_ref=?)",
            (source_ref,),
        )

    @staticmethod
    def _delete_facts(conn: sqlite3.Connection, source_ref: str) -> None:
        from ..memory.entities import recount

        ids = [
            str(row[0])
            for row in conn.execute("SELECT id FROM memory_facts WHERE source_ref=?", (source_ref,))
        ]
        touched = MemoryIndexRepository._entities_of(conn, ids)
        conn.executemany("DELETE FROM memory_fact_entities WHERE fact_id=?", [(i,) for i in ids])
        conn.execute("DELETE FROM memory_facts WHERE source_ref=?", (source_ref,))
        conn.execute("DELETE FROM memory_extract_parts WHERE source_ref=?", (source_ref,))
        recount(conn, touched)

    @staticmethod
    def _entities_of(conn: sqlite3.Connection, fact_ids: Sequence[str]) -> set[str]:
        found: set[str] = set()
        for fact in fact_ids:
            found.update(
                str(row[0])
                for row in conn.execute(
                    "SELECT entity_id FROM memory_fact_entities WHERE fact_id=?", (fact,)
                )
            )
        return found

    @staticmethod
    def _delete_vectors(conn: sqlite3.Connection, chunk_ids: Sequence[str]) -> None:
        conn.executemany(
            "DELETE FROM memory_embeddings WHERE item_kind=? AND item_id=?",
            [(CHUNK_ITEM_KIND, chunk_id) for chunk_id in chunk_ids],
        )

    # ── vectors ──────────────────────────────────────────────────────

    def pending_chunks(self, model_id: str, limit: int = 64) -> list[dict[str, Any]]:
        """Chunks with no current vector for ``model_id``, oldest source last."""
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT c.id,c.text,c.content_sha FROM memory_chunks c
                   LEFT JOIN memory_embeddings e
                     ON e.item_kind=? AND e.item_id=c.id AND e.model_id=?
                    AND e.content_sha=c.content_sha
                   WHERE e.item_id IS NULL
                   ORDER BY COALESCE(c.occurred_at,'') DESC,c.id
                   LIMIT ?""",
                (CHUNK_ITEM_KIND, model_id, max(1, int(limit))),
            ).fetchall()
        return [dict(row) for row in rows]

    def pending_count(self, model_id: str) -> int:
        """How many chunks have no current vector for ``model_id``."""
        with self._connection() as conn:
            return int(conn.execute(
                """SELECT count(*) FROM memory_chunks c
                   LEFT JOIN memory_embeddings e
                     ON e.item_kind=? AND e.item_id=c.id AND e.model_id=?
                    AND e.content_sha=c.content_sha
                   WHERE e.item_id IS NULL""",
                (CHUNK_ITEM_KIND, model_id),
            ).fetchone()[0])

    def store_vectors(
        self,
        model_id: str,
        dim: int,
        rows: Sequence[tuple[str, str, np.ndarray]],
    ) -> int:
        """Write one batch ``(chunk id, content sha, vector)`` in one
        transaction.  A vector for a chunk that changed or left while the
        engine ran is dropped, never written."""
        with self._connection() as conn:
            written = 0
            for chunk_id, content_sha, vector in rows:
                live = conn.execute(
                    "SELECT 1 FROM memory_chunks WHERE id=? AND content_sha=?",
                    (chunk_id, content_sha),
                ).fetchone()
                if live is None:
                    continue
                data = np.asarray(vector, dtype=np.float32)
                if data.shape != (int(dim),):
                    raise ValueError("vector has the wrong size")
                conn.execute(
                    "INSERT OR REPLACE INTO memory_embeddings"
                    "(item_kind,item_id,model_id,dim,vector,content_sha)"
                    " VALUES (?,?,?,?,?,?)",
                    (CHUNK_ITEM_KIND, chunk_id, model_id, int(dim), data.tobytes(), content_sha),
                )
                written += 1
            if written:
                self._bump(conn)
        return written

    def matrix(self, model_id: str) -> tuple[np.ndarray, list[str], list[str], list[str]]:
        """``(vectors, chunk ids, source refs, chunk shas)`` for the current
        chunk vectors of one model.

        Cached per generation.  The generation is read BEFORE the rows, so a
        cached matrix is never labelled newer than the rows it holds; a write
        that lands between the two reads only causes one more rebuild.
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT value FROM memory_index_state WHERE key='generation'"
            ).fetchone()
            generation = int(row[0]) if row else 0
            with self._matrix_lock:
                cached = self._matrices.get(model_id)
                if cached is not None and cached[0] == generation:
                    return cached[1], cached[2], cached[3], cached[4]
            rows = conn.execute(
                """SELECT c.id,c.source_ref,c.content_sha,e.vector,e.dim
                   FROM memory_embeddings e
                   JOIN memory_chunks c ON c.id=e.item_id
                    AND c.content_sha=e.content_sha
                   JOIN memory_sources s ON s.source_ref=c.source_ref AND s.state='live'
                   WHERE e.item_kind=? AND e.model_id=?
                   ORDER BY c.id""",
                (CHUNK_ITEM_KIND, model_id),
            ).fetchall()
        if rows:
            dim = int(rows[0]["dim"])
            kept = [row for row in rows if int(row["dim"]) == dim]
            vectors = np.frombuffer(
                b"".join(bytes(row["vector"]) for row in kept), dtype=np.float32
            ).reshape(-1, dim)
        else:
            vectors = np.zeros((0, 0), dtype=np.float32)
            kept = []
        chunk_ids = [str(row["id"]) for row in kept]
        source_refs = [str(row["source_ref"]) for row in kept]
        shas = [str(row["content_sha"]) for row in kept]
        with self._matrix_lock:
            self._matrices[model_id] = (generation, vectors, chunk_ids, source_refs, shas)
        return vectors, chunk_ids, source_refs, shas

    def chunk(self, chunk_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id,source_ref,ordinal,anchor,text,occurred_at FROM memory_chunks WHERE id=?",
                (chunk_id,),
            ).fetchone()
        return dict(row) if row else None

    def drop_other_models(self, model_id: str) -> int:
        """Remove vectors of other models once this model's set is complete."""
        if self.pending_chunks(model_id, limit=1):
            return 0
        with self._connection() as conn:
            removed = conn.execute(
                "DELETE FROM memory_embeddings WHERE model_id<>?", (model_id,)
            ).rowcount
            if removed:
                self._bump(conn)
        return removed

    # ── facts and entities (MEMORY-DESIGN.md §3.1 steps 5-6) ────────

    def pending_extraction(
        self, kinds: Iterable[str], version: int, *, now: Optional[str] = None
    ) -> list[tuple[str, str]]:
        """``(source ref, content sha)`` of the live sources of ``kinds``
        whose facts are not from their text of now and this extractor
        version, newest source first (a backlog runs oldest-last).  A source
        whose job failed six times on this text, or waits for its retry
        time, is left out."""
        wanted = sorted(set(kinds))
        if not wanted:
            return []
        stamp = now or _now()
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT s.source_ref,s.content_sha FROM memory_sources s
                    WHERE s.state='live' AND s.kind IN (SELECT value FROM json_each(?))
                      AND (s.extracted_sha IS NULL OR s.extracted_sha<>s.content_sha
                           OR COALESCE(s.extractor_version,0)<>?)
                      AND NOT EXISTS (
                        SELECT 1 FROM memory_jobs j
                         WHERE j.kind='extract' AND j.target=s.source_ref
                           AND j.input_sha=s.content_sha AND j.version=?
                           AND (j.status='failed' OR COALESCE(j.next_attempt_at,'')>?))
                    ORDER BY COALESCE(s.occurred_at,'') DESC,s.source_ref""",
                (json.dumps(wanted), int(version), int(version), stamp),
            ).fetchall()
        return [(str(row[0]), str(row[1])) for row in rows]

    def extraction_backlog(self, kinds: Iterable[str], version: int) -> int:
        return len(self.pending_extraction(kinds, version))

    def write_facts(
        self,
        *,
        source_ref: str,
        content_sha: str,
        extractor_version: int,
        mentioned_at: Optional[str],
        facts: Sequence[dict[str, Any]],
        still_current: Optional[Any] = None,
    ) -> bool:
        """ONE transaction: write the source's new facts, resolve their
        entities, retire its old facts and stamp the ledger.

        A fact read again from changed text, or a retired fact that comes
        back, waits for consolidation again (``consolidated_at`` cleared).

        The old facts serve recall until this commits.  An old fact that no
        later step has used (no ``consolidated_at``) is removed; a used one
        is kept as ``retired``.  Returns False, and writes nothing, when the
        source left or changed since the engine read it: the ledger says so,
        or ``still_current(conn)`` (the source's LIVE text, read inside this
        transaction after the write lock is taken) does.  An edit made while
        the engine ran is never stamped with the old text's facts.
        """
        from ..memory.entities import fold, is_name, recount, resolve

        with self._connection() as conn:
            if not conn.in_transaction:
                conn.execute("BEGIN IMMEDIATE")
            known = conn.execute(
                "SELECT state,content_sha FROM memory_sources WHERE source_ref=?", (source_ref,)
            ).fetchone()
            if known is None or known["state"] != "live" or str(known["content_sha"]) != content_sha:
                return False
            if still_current is not None and not still_current(conn):
                return False
            old = [
                str(row[0])
                for row in conn.execute(
                    "SELECT id FROM memory_facts WHERE source_ref=? AND state='live'", (source_ref,)
                )
            ]
            touched = self._entities_of(conn, old)
            new_ids = {str(fact["id"]) for fact in facts}
            for fact in facts:
                names = [entity["name"] for entity in fact["entities"]]
                links: dict[str, str] = {}
                for entity in fact["entities"]:
                    found = resolve(
                        conn,
                        name=entity["name"],
                        kind=entity["kind"],
                        neighbours=[name for name in names if name != entity["name"]],
                        seen=fact.get("occurred_start") or mentioned_at,
                    )
                    links[fold(entity["name"])] = found
                subject = links.get(fold(fact["subject"])) if is_name(fact["subject"]) else None
                obj = links.get(fold(fact["object"])) if is_name(fact["object"]) else None
                conn.execute(
                    """INSERT INTO memory_facts(id,source_ref,chunk_id,kind,text,subject_entity_id,
                         predicate,object_entity_id,object_text,occurred_start,occurred_end,
                         mentioned_at,confidence,extractor_version,state,chunk_sha,anchor)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,'live',?,?)
                       ON CONFLICT(id) DO UPDATE SET chunk_id=excluded.chunk_id,
                         chunk_sha=excluded.chunk_sha,anchor=excluded.anchor,
                         kind=excluded.kind,text=excluded.text,
                         subject_entity_id=excluded.subject_entity_id,
                         predicate=excluded.predicate,object_entity_id=excluded.object_entity_id,
                         object_text=excluded.object_text,occurred_start=excluded.occurred_start,
                         occurred_end=excluded.occurred_end,mentioned_at=excluded.mentioned_at,
                         confidence=excluded.confidence,
                         extractor_version=excluded.extractor_version,state='live',
                         consolidated_at=CASE WHEN memory_facts.state='live'
                           AND memory_facts.chunk_sha=excluded.chunk_sha
                           AND memory_facts.anchor=excluded.anchor
                           THEN memory_facts.consolidated_at ELSE NULL END""",
                    (
                        str(fact["id"]), source_ref, str(fact["chunk_id"]), fact["kind"],
                        fact["text"], subject, fact["predicate"], obj, fact["object"],
                        fact.get("occurred_start"), fact.get("occurred_end"), mentioned_at,
                        float(fact["confidence"]), int(extractor_version),
                        str(fact.get("chunk_sha") or ""), str(fact.get("anchor") or ""),
                    ),
                )
                touched |= self._entities_of(conn, [str(fact["id"])])
                conn.execute("DELETE FROM memory_fact_entities WHERE fact_id=?", (str(fact["id"]),))
                rows: set[tuple[str, str, str]] = set()
                for key, entity in links.items():
                    role = "subject" if entity == subject else "object" if entity == obj else "mention"
                    rows.add((str(fact["id"]), entity, role))
                conn.executemany(
                    "INSERT OR IGNORE INTO memory_fact_entities(fact_id,entity_id,role) VALUES (?,?,?)",
                    sorted(rows),
                )
                touched |= set(links.values())
            gone = [fact for fact in old if fact not in new_ids]
            for fact in gone:
                used = conn.execute(
                    "SELECT consolidated_at FROM memory_facts WHERE id=?", (fact,)
                ).fetchone()
                if used is not None and used[0]:
                    conn.execute("UPDATE memory_facts SET state='retired' WHERE id=?", (fact,))
                else:
                    conn.execute("DELETE FROM memory_fact_entities WHERE fact_id=?", (fact,))
                    conn.execute("DELETE FROM memory_facts WHERE id=?", (fact,))
            recount(conn, touched)
            conn.execute(
                "UPDATE memory_sources SET extracted_sha=?,extractor_version=? WHERE source_ref=?",
                (content_sha, int(extractor_version), source_ref),
            )
            conn.execute(
                "DELETE FROM memory_jobs WHERE kind='extract' AND target=?", (source_ref,)
            )
            conn.execute("DELETE FROM memory_extract_parts WHERE source_ref=?", (source_ref,))
            self._bump(conn)
        return True

    def extract_parts(self, source_ref: str, version: int) -> dict[tuple[str, str], list[dict[str, Any]]]:
        """The checked answers already read for a source's chunks, keyed by
        ``(chunk id, chunk sha)``: a job that stopped goes on from here."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT chunk_id,chunk_sha,facts_json FROM memory_extract_parts"
                " WHERE source_ref=? AND version=?",
                (source_ref, int(version)),
            ).fetchall()
        return {(str(r[0]), str(r[1])): json.loads(r[2]) for r in rows}

    def store_extract_part(
        self, source_ref: str, chunk_id: str, chunk_sha: str, version: int, facts: Sequence[dict[str, Any]]
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memory_extract_parts"
                "(source_ref,chunk_id,chunk_sha,version,facts_json) VALUES (?,?,?,?,?)",
                (source_ref, chunk_id, chunk_sha, int(version), json.dumps(list(facts), ensure_ascii=False)),
            )

    def record_job_failure(
        self,
        *,
        kind: str,
        target: str,
        input_sha: str,
        version: int,
        error: str,
        boundary: str,
        max_attempts: int,
        delay: Any,
    ) -> dict[str, Any]:
        """One failed attempt of a job on its input: back off, and stop after
        ``max_attempts`` (status ``failed``) until the input or the version
        changes."""
        from datetime import timedelta

        with self._connection() as conn:
            row = conn.execute(
                "SELECT attempts FROM memory_jobs WHERE kind=? AND target=? AND input_sha=? AND version=?",
                (kind, target, input_sha, int(version)),
            ).fetchone()
            attempts = (int(row[0]) if row is not None else 0) + 1
            status = "failed" if attempts >= int(max_attempts) else "queued"
            next_at = (
                datetime.now(timezone.utc) + timedelta(seconds=int(delay(attempts)))
            ).isoformat(timespec="seconds")
            conn.execute(
                """INSERT INTO memory_jobs(kind,target,input_sha,version,status,attempts,
                     next_attempt_at,last_error,boundary)
                   VALUES (?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(kind,target,input_sha,version) DO UPDATE SET
                     status=excluded.status,attempts=excluded.attempts,
                     next_attempt_at=excluded.next_attempt_at,last_error=excluded.last_error,
                     boundary=excluded.boundary""",
                (kind, target, input_sha, int(version), status, attempts, next_at, error, boundary),
            )
        return {"attempts": attempts, "status": status, "next_attempt_at": next_at}

    def entities(self) -> tuple[int, list[dict[str, Any]]]:
        """``(generation, every entity)`` for the entity walk, cached per
        index generation (each fact write moves it)."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT value FROM memory_index_state WHERE key='generation'"
            ).fetchone()
            generation = int(row[0]) if row else 0
            with self._matrix_lock:
                cached = getattr(self, "_entity_cache", None)
                if cached is not None and cached[0] == generation:
                    return cached
            rows = [
                dict(item)
                for item in conn.execute(
                    "SELECT id,kind,name,name_key,aliases_json FROM memory_entities ORDER BY id"
                )
            ]
        with self._matrix_lock:
            self._entity_cache = (generation, rows)
        return generation, rows

    def has_live_facts(self) -> bool:
        with self._connection() as conn:
            return conn.execute(
                "SELECT 1 FROM memory_facts WHERE state='live' LIMIT 1"
            ).fetchone() is not None

    def facts_for_entities(self, entity_ids: Sequence[str]) -> list[dict[str, Any]]:
        """The live facts that name any of ``entity_ids``, with the entity."""
        wanted = list(dict.fromkeys(entity_ids))
        if not wanted:
            return []
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT f.id,f.source_ref,f.chunk_id,f.chunk_sha,f.anchor,f.text,f.confidence,
                          f.mentioned_at,f.occurred_start,fe.entity_id
                   FROM memory_fact_entities fe
                   JOIN memory_facts f ON f.id=fe.fact_id AND f.state='live'
                   WHERE fe.entity_id IN (SELECT value FROM json_each(?))
                   ORDER BY f.id""",
                (json.dumps(wanted),),
            ).fetchall()
        return [dict(row) for row in rows]

    # ── observations (MEMORY-DESIGN.md §3.3, slice 4) ───────────────

    def has_observations(self) -> bool:
        with self._connection() as conn:
            return conn.execute(
                "SELECT 1 FROM memory_observations WHERE state<>'retired' LIMIT 1"
            ).fetchone() is not None

    @staticmethod
    def _history(
        conn: sqlite3.Connection,
        observation_id: str,
        at: str,
        reason: str,
        fact_ids: Sequence[str],
        *,
        prior_text: str,
        prior_state: str,
        prior_version: Optional[int],
    ) -> None:
        """Append one history row: the text and state before a change, the
        version that text is, and the facts of the change.  Append only."""
        conn.execute(
            "INSERT INTO memory_observation_history"
            "(observation_id,at,prior_text,prior_state,reason,fact_ids_json,prior_version)"
            " VALUES (?,?,?,?,?,?,?)",
            (observation_id, at, prior_text, prior_state, reason, json.dumps(sorted(fact_ids)), prior_version),
        )

    @staticmethod
    def _back(
        conn: sqlite3.Connection, observation_id: str, version: int, facts: Sequence[dict[str, Any]], kind: str
    ) -> None:
        """One backing group for one version: these facts, all of them."""
        count = conn.execute(
            "SELECT count(DISTINCT grp) FROM memory_observation_backing WHERE observation_id=? AND version=?",
            (observation_id, int(version)),
        ).fetchone()[0]
        group = f"{kind}{int(count) + 1}"
        # Append only: a trigger refuses a second row with the same key, so
        # a fact named twice in one entry is written once.
        conn.executemany(
            "INSERT INTO memory_observation_backing(observation_id,version,grp,fact_id)"
            " VALUES (?,?,?,?)",
            [(observation_id, int(version), group, fact) for fact in dict.fromkeys(str(f["id"]) for f in facts)],
        )

    @staticmethod
    def _version(conn: sqlite3.Connection, observation_id: str, text: str, at: str) -> int:
        """Append the next text version; returns its number."""
        last = conn.execute(
            "SELECT COALESCE(MAX(version),0) FROM memory_observation_versions WHERE observation_id=?",
            (observation_id,),
        ).fetchone()[0]
        number = int(last) + 1
        conn.execute(
            "INSERT INTO memory_observation_versions(observation_id,version,text,at) VALUES (?,?,?,?)",
            (observation_id, number, text, at),
        )
        return number

    @staticmethod
    def _add_evidence(
        conn: sqlite3.Connection, observation_id: str, facts: Sequence[dict[str, Any]], stance: str, at: str
    ) -> None:
        """Link each fact to the observation, with the chunk it was read
        from.  The same fact again (read from new text by a later job) takes
        the new chunk: only a job that read that text adds it."""
        conn.executemany(
            """INSERT INTO memory_observation_evidence
                 (observation_id,fact_id,stance,added_at,source_ref,chunk_id,chunk_sha,anchor)
               VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(observation_id,fact_id) DO UPDATE SET stance=excluded.stance,
                 added_at=excluded.added_at,source_ref=excluded.source_ref,
                 chunk_id=excluded.chunk_id,chunk_sha=excluded.chunk_sha,anchor=excluded.anchor""",
            [
                (
                    observation_id, str(f["id"]), stance, at, str(f["source_ref"]),
                    str(f["chunk_id"]), str(f["chunk_sha"]), str(f.get("anchor") or ""),
                )
                for f in facts
            ],
        )

    @staticmethod
    def _recount_proof(conn: sqlite3.Connection, observation_ids: Iterable[str]) -> None:
        for observation in set(observation_ids):
            conn.execute(
                "UPDATE memory_observations SET proof_count=(SELECT count(*) FROM"
                " memory_observation_evidence WHERE observation_id=? AND stance='supports')"
                " WHERE id=?",
                (observation, observation),
            )

    def write_observations(
        self,
        *,
        scope: tuple[str, str],
        facts: Sequence[dict[str, Any]],
        observations: Sequence[dict[str, Any]],
        answer: dict[str, list[dict[str, Any]]],
        boundary: str,
        version: int,
        still_live: Optional[Any] = None,
        input_sha: Optional[str] = None,
    ) -> bool:
        """ONE transaction: apply a checked consolidate answer and mark every
        input fact read.

        ``answer`` is ``consolidate.validate_output``'s result (positions
        into ``facts`` and ``observations``).  Effects (§3.3):

        * create: a new ``current`` observation with its facts as evidence.
        * supports: add evidence.
        * refines: the prior text to history; the new text; add evidence.
        * supersedes: a new ``current`` observation; the old one to history,
          ``superseded``, ``superseded_by`` the new one.  It stays readable.
        * contradicts: a new observation with the facts; both ``disputed``;
          the facts are ``contradicts`` evidence on the old one.

        Takes the write lock first, then ``still_live(conn)`` checks every
        input again.  Returns False, and writes nothing, when an input moved
        while the engine ran.
        """
        from ..memory.consolidate import observation_id

        scope_kind, scope_id = scope
        with self._connection() as conn:
            if not conn.in_transaction:
                conn.execute("BEGIN IMMEDIATE")
            if still_live is not None and not still_live(conn):
                return False
            at = _now()
            touched: set[str] = set()

            def seen(chosen: Sequence[dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
                days = sorted(
                    str(f.get("occurred_start") or f.get("mentioned_at") or "")
                    for f in chosen if f.get("occurred_start") or f.get("mentioned_at")
                )
                return (days[0], days[-1]) if days else (None, None)

            def create(text: str, chosen: list[dict[str, Any]], state: str) -> str:
                keys = [f"{f['id']}@{f['chunk_sha']}" for f in chosen]
                new_id = observation_id(scope, text, keys)
                exists = conn.execute(
                    "SELECT state FROM memory_observations WHERE id=?", (new_id,)
                ).fetchone()
                # A retired observation never comes back: the same belief read
                # again from live text is a new observation.
                generation = 0
                while exists is not None and exists["state"] == "retired":
                    generation += 1
                    new_id = observation_id(scope, text, [*keys, f"#{generation}"])
                    exists = conn.execute(
                        "SELECT state FROM memory_observations WHERE id=?", (new_id,)
                    ).fetchone()
                first, last = seen(chosen)
                if exists is None:
                    conn.execute(
                        """INSERT INTO memory_observations(id,scope_kind,scope_id,text,state,
                             proof_count,first_seen,last_seen,boundary,consolidator_version,updated_at)
                           VALUES (?,?,?,?,?,0,?,?,?,?,?)""",
                        (new_id, scope_kind, scope_id, text, state, first, last, boundary,
                         int(version), at),
                    )
                    number = self._version(conn, new_id, text, at)
                else:
                    number = int(conn.execute(
                        "SELECT MAX(version) FROM memory_observation_versions WHERE observation_id=?",
                        (new_id,),
                    ).fetchone()[0] or self._version(conn, new_id, text, at))
                self._back(conn, new_id, number, chosen, "i")
                self._add_evidence(conn, new_id, chosen, "supports", at)
                touched.add(new_id)
                return new_id

            def widen(observation: str, chosen: list[dict[str, Any]]) -> None:
                first, last = seen(chosen)
                if first is None:
                    return
                conn.execute(
                    "UPDATE memory_observations SET"
                    " first_seen=CASE WHEN first_seen IS NULL OR first_seen>? THEN ? ELSE first_seen END,"
                    " last_seen=CASE WHEN last_seen IS NULL OR last_seen<? THEN ? ELSE last_seen END"
                    " WHERE id=?",
                    (first, first, last, last, observation),
                )

            for item in answer["creates"]:
                create(item["text"], [facts[i] for i in item["facts"]], "current")
            for item in answer["updates"]:
                shown = observations[item["observation"]]
                old = str(shown["id"])
                # The version the engine was shown (``scope_observations``):
                # a supports backs it; a change records it as the prior text.
                prior = {"prior_text": str(shown["text"]), "prior_state": str(shown["state"]),
                         "prior_version": int(shown["version"])}
                chosen = [facts[i] for i in item["facts"]]
                ids = [str(f["id"]) for f in chosen]
                relation = item["relation"]
                if relation == "supports":
                    self._back(conn, old, int(shown["version"]), chosen, "s")
                    self._add_evidence(conn, old, chosen, "supports", at)
                    widen(old, chosen)
                    conn.execute(
                        "UPDATE memory_observations SET updated_at=?,boundary=? WHERE id=?",
                        (at, boundary, old),
                    )
                elif relation == "refines":
                    self._history(conn, old, at, f"refines: {item['reason']}", ids, **prior)
                    number = self._version(conn, old, item["text"], at)
                    self._back(conn, old, number, chosen, "i")
                    conn.execute(
                        "UPDATE memory_observations SET text=?,updated_at=?,boundary=?,"
                        "consolidator_version=? WHERE id=?",
                        (item["text"], at, boundary, int(version), old),
                    )
                    self._add_evidence(conn, old, chosen, "supports", at)
                    widen(old, chosen)
                elif relation == "supersedes":
                    new_id = create(item["text"], chosen, "current")
                    self._history(conn, old, at, f"superseded by {new_id}: {item['reason']}", ids, **prior)
                    conn.execute(
                        "UPDATE memory_observations SET state='superseded',superseded_by=?,"
                        "updated_at=? WHERE id=?",
                        (new_id, at, old),
                    )
                else:  # contradicts, with no clear winner: both disputed
                    new_id = create(item["text"], chosen, "disputed")
                    self._history(conn, old, at, f"disputed by {new_id}: {item['reason']}", ids, **prior)
                    conn.execute(
                        "UPDATE memory_observations SET state='disputed',updated_at=? WHERE id=?",
                        (at, old),
                    )
                    self._add_evidence(conn, old, chosen, "contradicts", at)
                touched.add(old)
            self._recount_proof(conn, touched)
            conn.executemany(
                "UPDATE memory_facts SET consolidated_at=? WHERE id=?",
                [(at, str(f["id"])) for f in facts],
            )
            # Only this batch's back-off row: a batch of the scope that failed
            # for good stays failed (passed over), never tried again here.
            conn.execute(
                "DELETE FROM memory_jobs WHERE kind='consolidate' AND target=? AND input_sha=?",
                (f"project:{scope_id}" if scope_kind == "project" else "desk", str(input_sha or "")),
            )
            self._bump(conn)
        return True

    def refresh_observations(self) -> dict[str, int]:
        """Retire each observation no version of which is backed by live
        evidence now (``consolidate.served``; a history row first) and set
        every other one's ``proof_count`` to the live facts that back its
        served version.  ONE transaction.  One row read when
        memory holds no observation that is not retired."""
        from ..memory.consolidate import LiveText, ScopeReader, served

        out = {"retired": 0, "checked": 0}
        with self._connection() as conn:
            if conn.execute(
                "SELECT 1 FROM memory_observations WHERE state<>'retired' LIMIT 1"
            ).fetchone() is None:
                return out
            if not conn.in_transaction:
                conn.execute("BEGIN IMMEDIATE")
            rows = [
                dict(r) for r in conn.execute(
                    "SELECT id,scope_kind,scope_id,state,proof_count FROM memory_observations"
                    " WHERE state<>'retired' ORDER BY id"
                )
            ]
            views = served(conn, rows, live=LiveText(conn), scopes=ScopeReader(conn))
            at = _now()
            changed = False
            for row in rows:
                out["checked"] += 1
                view = views[str(row["id"])]
                held = view["facts"] if view else set()
                if not held:
                    # No text: a retire row carries none (the versions hold it).
                    self._history(conn, str(row["id"]), at, "retired: no live evidence", [],
                                  prior_text="", prior_state=str(row["state"]), prior_version=None)
                    conn.execute(
                        "UPDATE memory_observations SET state='retired',proof_count=0,updated_at=?"
                        " WHERE id=?",
                        (at, str(row["id"])),
                    )
                    out["retired"] += 1
                    changed = True
                elif len(held) != int(row["proof_count"]):
                    conn.execute(
                        "UPDATE memory_observations SET proof_count=? WHERE id=?",
                        (len(held), str(row["id"])),
                    )
                    changed = True
            if changed:
                self._bump(conn)
        return out

    def observation_rows(
        self,
        *,
        scope: Optional[tuple[str, str]] = None,
        states: Sequence[str] = ("current", "disputed", "superseded"),
    ) -> list[dict[str, Any]]:
        """The stored observations of ``states`` (one scope, or every scope),
        newest first.  The CALLER checks liveness before it serves one."""
        with self._connection() as conn:
            return [
                dict(r) for r in conn.execute(
                    "SELECT id,scope_kind,scope_id,text,state,superseded_by,proof_count,first_seen,"
                    "last_seen,boundary,consolidator_version,updated_at FROM memory_observations"
                    " WHERE state IN (SELECT value FROM json_each(?))"
                    " AND (? IS NULL OR (scope_kind=? AND scope_id=?))"
                    " ORDER BY COALESCE(last_seen,'') DESC,id",
                    (
                        json.dumps(list(states)),
                        None if scope is None else 1,
                        scope[0] if scope else "",
                        scope[1] if scope else "",
                    ),
                )
            ]

    # ── pages (MEMORY-DESIGN.md §3.4, slice 5) ──────────────────────

    def write_page(
        self,
        *,
        page_id: str,
        scope: tuple[str, str],
        slug: str,
        question: str,
        answer_md: str,
        sources: Sequence[str],
        sentences: Sequence[dict[str, Any]],
        seen: str,
        seen_keys: Sequence[str] = (),
        boundary: str = "",
        model: str = "",
        version: int = 1,
        still_live: Optional[Any] = None,
        job_target: str = "",
        input_sha: str = "",
    ) -> bool:
        """ONE transaction: the old page to history (append only), then the
        new page, and this job's back-off row cleared.

        Takes the write lock first, then ``still_live(conn)`` checks every
        input (and that the page is the one the job replaces).  Returns
        False, and writes nothing, when one moved while the engine ran.
        """
        with self._connection() as conn:
            if not conn.in_transaction:
                conn.execute("BEGIN IMMEDIATE")
            if still_live is not None and not still_live(conn):
                return False
            old = conn.execute("SELECT * FROM memory_pages WHERE id=?", (page_id,)).fetchone()
            if old is not None:
                conn.execute(
                    "INSERT INTO memory_page_history(page_id,built_at,answer_md,sources_json,"
                    "sentences_json,boundary,model,writer_version) VALUES (?,?,?,?,?,?,?,?)",
                    (page_id, old["built_at"], old["answer_md"], old["sources_json"], old["sentences_json"],
                     old["boundary"], old["model"], old["writer_version"]),
                )
            conn.execute(
                """INSERT INTO memory_pages(id,scope_kind,scope_id,slug,question,answer_md,sources_json,
                     sentences_json,built_at,last_memory_seen_at,seen_keys_json,boundary,model,
                     writer_version)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET question=excluded.question,answer_md=excluded.answer_md,
                     sources_json=excluded.sources_json,sentences_json=excluded.sentences_json,
                     built_at=excluded.built_at,last_memory_seen_at=excluded.last_memory_seen_at,
                     seen_keys_json=excluded.seen_keys_json,boundary=excluded.boundary,model=excluded.model,writer_version=excluded.writer_version""",
                (page_id, scope[0], scope[1], slug, question, answer_md,
                 json.dumps(list(sources), ensure_ascii=False),
                 json.dumps(list(sentences), ensure_ascii=False, sort_keys=True),
                 _now(), seen, json.dumps(sorted(seen_keys)), boundary, model, int(version)),
            )
            conn.execute(
                "DELETE FROM memory_jobs WHERE kind='page' AND target=? AND input_sha=?",
                (job_target, input_sha),
            )
        return True

    # ── maintenance ──────────────────────────────────────────────────

    def clear(self) -> None:
        """Drop every derived memory row.  The sweep builds them again."""
        with self._connection() as conn:
            conn.execute("DELETE FROM memory_embeddings")
            conn.execute("DELETE FROM memory_chunks_fts")
            conn.execute("DELETE FROM memory_chunks")
            conn.execute("DELETE FROM memory_fact_entities")
            conn.execute("DELETE FROM memory_facts")
            conn.execute("DELETE FROM memory_entities")
            conn.execute("DELETE FROM memory_jobs")
            conn.execute("DELETE FROM memory_extract_parts")
            conn.execute("DELETE FROM memory_sources")
            self._bump(conn)
        with self._matrix_lock:
            self._matrices.clear()

    def stats(self) -> dict[str, int]:
        with self._connection() as conn:
            return {
                "sources": int(conn.execute("SELECT count(*) FROM memory_sources WHERE state='live'").fetchone()[0]),
                "gone": int(conn.execute("SELECT count(*) FROM memory_sources WHERE state='gone'").fetchone()[0]),
                "chunks": int(conn.execute("SELECT count(*) FROM memory_chunks").fetchone()[0]),
                "keyword_rows": int(conn.execute("SELECT count(*) FROM memory_chunks_fts").fetchone()[0]),
                "vectors": int(conn.execute("SELECT count(*) FROM memory_embeddings").fetchone()[0]),
                "facts": int(conn.execute("SELECT count(*) FROM memory_facts WHERE state='live'").fetchone()[0]),
                "entities": int(conn.execute("SELECT count(*) FROM memory_entities").fetchone()[0]),
                "observations": int(conn.execute(
                    "SELECT count(*) FROM memory_observations WHERE state<>'retired'").fetchone()[0]),
            }


__all__ = ["CHUNK_ITEM_KIND", "MemoryIndexRepository"]
