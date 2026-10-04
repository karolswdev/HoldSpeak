"""The memory index tables: ledger, chunks, vectors (MEMORY-DESIGN.md §2).

Every row here is derived.  A write replaces one source's chunks and stamps
its ledger row in ONE transaction, so a reader never sees half a source.
Vectors are plain float32 BLOBs; search is a numpy scan over one matrix per
model, built lazily and rebuilt when the vector rows change.
"""
from __future__ import annotations

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
        # Every write through this repository moves the generation, so a
        # cached matrix is never served after the rows under it changed.
        self._generation = 0
        # model_id -> (stamp, matrix, chunk ids, source refs)
        self._matrices: dict[str, tuple[tuple[int, ...], np.ndarray, list[str], list[str]]] = {}

    def _touch(self) -> None:
        with self._matrix_lock:
            self._generation += 1

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
        self._touch()

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
            conn.execute("DELETE FROM memory_chunks WHERE source_ref=?", (source_ref,))
            conn.execute(
                "UPDATE memory_sources SET state='gone',updated_at=? WHERE source_ref=?",
                (_now(), source_ref),
            )
        self._touch()

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
        self._touch()
        return written

    def matrix(self, model_id: str) -> tuple[np.ndarray, list[str], list[str]]:
        """``(vectors, chunk ids, source refs)`` for the current chunk vectors
        of one model.  Cached; rebuilt when the vector rows change."""
        with self._connection() as conn:
            stamp_row = conn.execute(
                "SELECT count(*),COALESCE(max(rowid),0) FROM memory_embeddings"
                " WHERE model_id=?",
                (model_id,),
            ).fetchone()
            chunk_row = conn.execute(
                "SELECT count(*),COALESCE(max(rowid),0) FROM memory_chunks"
            ).fetchone()
            with self._matrix_lock:
                generation = self._generation
            stamp = (
                generation,
                int(stamp_row[0]), int(stamp_row[1]),
                int(chunk_row[0]), int(chunk_row[1]),
            )
            with self._matrix_lock:
                cached = self._matrices.get(model_id)
                if cached is not None and cached[0] == stamp:
                    return cached[1], cached[2], cached[3]
            rows = conn.execute(
                """SELECT c.id,c.source_ref,e.vector,e.dim
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
            vectors = np.frombuffer(
                b"".join(bytes(row["vector"]) for row in rows if int(row["dim"]) == dim),
                dtype=np.float32,
            ).reshape(-1, dim)
            kept = [row for row in rows if int(row["dim"]) == dim]
        else:
            vectors = np.zeros((0, 0), dtype=np.float32)
            kept = []
        chunk_ids = [str(row["id"]) for row in kept]
        source_refs = [str(row["source_ref"]) for row in kept]
        with self._matrix_lock:
            self._matrices[model_id] = (stamp, vectors, chunk_ids, source_refs)
        return vectors, chunk_ids, source_refs

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
        self._touch()
        return removed

    # ── maintenance ──────────────────────────────────────────────────

    def clear(self) -> None:
        """Drop every derived memory row.  The sweep builds them again."""
        with self._connection() as conn:
            conn.execute("DELETE FROM memory_embeddings")
            conn.execute("DELETE FROM memory_chunks")
            conn.execute("DELETE FROM memory_sources")
        with self._matrix_lock:
            self._generation += 1
            self._matrices.clear()

    def stats(self) -> dict[str, int]:
        with self._connection() as conn:
            return {
                "sources": int(conn.execute("SELECT count(*) FROM memory_sources WHERE state='live'").fetchone()[0]),
                "gone": int(conn.execute("SELECT count(*) FROM memory_sources WHERE state='gone'").fetchone()[0]),
                "chunks": int(conn.execute("SELECT count(*) FROM memory_chunks").fetchone()[0]),
                "vectors": int(conn.execute("SELECT count(*) FROM memory_embeddings").fetchone()[0]),
            }


__all__ = ["CHUNK_ITEM_KIND", "MemoryIndexRepository"]
