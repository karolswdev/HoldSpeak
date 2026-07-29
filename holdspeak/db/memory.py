"""Ranked long-horizon retrieval over decisions, artifacts, and notes."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Optional

from .base import BaseRepository

_KIND_ORDER = {"decision": 0, "artifact": 1, "note": 2}
_VALID_KINDS = frozenset(_KIND_ORDER)
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MemorySearchResult:
    hits: list[MemoryHit]
    total: int
    limit: int
    offset: int

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
                "interleave": "kind_rank_tiers_then_normalized_score_recency_kind",
            },
        }


def _match_expression(query: str) -> str:
    """Turn arbitrary user text into a safe, deterministic FTS phrase query."""
    raw_terms = _WORD.findall(str(query or "").casefold())
    terms = [term for term in raw_terms if term not in _QUERY_STOPWORDS] or raw_terms
    if not terms:
        raise ValueError("query must contain searchable text")
    # Quoting each lexical term prevents user punctuation/FTS operators from
    # changing the grammar. OR lets a natural-language ask retrieve partial
    # lexical matches; BM25 still rewards sources matching more query terms.
    return " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)


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
        "decisions": int(conn.execute("SELECT count(*) FROM decisions_memory_fts").fetchone()[0]),
        "artifacts": int(conn.execute("SELECT count(*) FROM artifacts_memory_fts").fetchone()[0]),
        "notes": int(conn.execute("SELECT count(*) FROM notes_memory_fts").fetchone()[0]),
    }
    counts["total"] = sum(counts.values())
    return counts


class MemoryRepository(BaseRepository):
    """One search contract over three independently normalized FTS corpora."""

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
    ) -> MemorySearchResult:
        expression = _match_expression(query)
        selected = self._normalize_kinds(kinds)
        bounded_limit = max(1, min(int(limit), 500))
        bounded_offset = max(0, int(offset))
        project = str(project_id or "").strip() or None
        start = str(time_from or "").strip() or None
        end = str(time_to or "").strip() or None

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
            if "note" in selected:
                by_kind["note"] = self._note_rows(
                    conn, expression, project, start, end
                )

        normalized: dict[str, list[dict[str, Any]]] = {}
        for kind, rows in by_kind.items():
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
        interleaved.sort(
            key=lambda row: (
                int(row["kind_rank"]),
                -float(row["normalized_score"]),
                self._recency_key(str(row["occurred_at"])),
                _KIND_ORDER[str(row["kind"])],
                str(row["source_ref"]),
            )
        )
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
            )
            for index, row in enumerate(page, start=1)
        ]
        return MemorySearchResult(hits, total, bounded_limit, bounded_offset)

    @staticmethod
    def _normalize_kinds(kinds: Optional[Iterable[str]]) -> tuple[str, ...]:
        if kinds is None:
            return tuple(_KIND_ORDER)
        if isinstance(kinds, str):
            values = kinds.split(",")
        else:
            values = list(kinds)
        cleaned = tuple(dict.fromkeys(str(value).strip().lower() for value in values if str(value).strip()))
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
            clauses.append("(d.project_key=? OR EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=? AND pr.resource_ref='decision:'||d.id AND pr.deleted=0))")
            params.extend((project, project))
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
                WHERE {' AND '.join(clauses)}
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
                WHERE {' AND '.join(clauses)}
                ORDER BY bm25 ASC,a.updated_at DESC,a.id ASC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _note_rows(conn, match, project, start, end) -> list[dict[str, Any]]:
        clauses = ["notes_memory_fts MATCH ?"]
        params: list[Any] = [match]
        if project:
            clauses.append("EXISTS (SELECT 1 FROM project_resources pr WHERE pr.project_id=? AND pr.resource_ref='note:'||n.id AND pr.deleted=0)")
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
                WHERE {' AND '.join(clauses)}
                ORDER BY bm25 ASC,n.updated_at DESC,n.id ASC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]


__all__ = [
    "MemoryHit",
    "MemoryRepository",
    "MemorySearchResult",
    "rebuild_memory_index",
]
