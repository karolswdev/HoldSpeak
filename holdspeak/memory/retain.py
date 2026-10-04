"""RETAIN, slice 1: the sweep, the chunk step and the embed step
(MEMORY-DESIGN.md §3.1).

The sweep reads each source kind, asks ``memory_admits``, redacts secrets,
and compares a content hash with the ledger.  A new or changed source gets
new chunks; a source that left (deleted, parked, made sensitive, promoted)
loses its chunks and vectors.  Each source is one transaction, so a sweep
that stops half way leaves every finished source whole and every other
source as it was.  Run it again and it completes.

The embed step gives each chunk without a current vector to the engine, in
batches.  One batch is one transaction.

No hook in a producer is needed for correctness: a missed wake can never
lose a memory, because the next sweep sees the source.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Optional

from ..logging_config import get_logger
from .admission import memory_admits
from .chunker import CHUNKER_VERSION, chunk_units, paragraphs
from .defense import redact
from .embedder import EMBED_BATCH, MemoryEmbedder

log = get_logger("memory.retain")


@dataclass
class MemorySource:
    ref: str
    kind: str
    title: str
    occurred_at: Optional[str]
    units: list[tuple[str, str]] = field(default_factory=list)
    #: False: each unit is its own chunk (a thread message).
    pack: bool = True


def _promoted(conn: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in conn.execute("SELECT DISTINCT target_ref FROM context_promotions")
        if str(row[0] or "").strip()
    }


def _text(*parts: Any) -> str:
    return " ".join(str(part).strip() for part in parts if str(part or "").strip())


def _simple(
    kind: str,
    sql: str,
    build: Callable[[dict[str, Any]], tuple[str, Optional[str], list[tuple[str, str]]]],
) -> Callable[[sqlite3.Connection, set[str]], Iterator[MemorySource]]:
    def read(conn: sqlite3.Connection, promoted: set[str]) -> Iterator[MemorySource]:
        for raw in conn.execute(sql):
            row = dict(raw)
            ref = f"{kind}:{row['id']}"
            row["promoted"] = ref in promoted
            if not memory_admits(kind, row):
                continue
            title, occurred_at, units = build(row)
            yield MemorySource(ref, kind, title, occurred_at, units)

    return read


def _desk_decision(row: dict[str, Any]) -> tuple[str, Optional[str], list[tuple[str, str]]]:
    title = str(row["title"] or "") or str(row["decision_markdown"] or "")[:160]
    units = [
        ("context", str(row["context_markdown"] or "")),
        ("decision", str(row["decision_markdown"] or "")),
        ("consequences", str(row["consequences_markdown"] or "")),
    ]
    alternatives = str(row["alternatives_json"] or "")
    if alternatives not in ("", "[]"):
        units.append(("alternatives", alternatives))
    return title, row["updated_at"], units


def _meetings(conn: sqlite3.Connection, promoted: set[str]) -> Iterator[MemorySource]:
    meetings = [
        dict(row)
        for row in conn.execute("SELECT id,title,started_at,parked FROM meetings ORDER BY id")
    ]
    for meeting in meetings:
        ref = f"meeting:{meeting['id']}"
        meeting["promoted"] = ref in promoted
        if not memory_admits("meeting", meeting):
            continue
        units = [
            (str(row["id"]), f"{row['speaker']}: {row['text']}")
            for row in conn.execute(
                "SELECT id,speaker,text FROM segments WHERE meeting_id=?"
                " ORDER BY start_time,id",
                (meeting["id"],),
            )
        ]
        if not units:
            continue
        yield MemorySource(
            ref, "meeting", str(meeting["title"] or meeting["id"]), meeting["started_at"], units
        )


def _threads(conn: sqlite3.Connection, promoted: set[str]) -> Iterator[MemorySource]:
    threads = [
        dict(row)
        for row in conn.execute(
            "SELECT id,title,deleted_at,datetime(updated_at,'unixepoch') occurred_at"
            " FROM threads ORDER BY id"
        )
    ]
    for thread in threads:
        ref = f"thread:{thread['id']}"
        thread["promoted"] = ref in promoted
        if not memory_admits("thread", thread):
            continue
        by_message: dict[str, list[str]] = {}
        for raw in conn.execute(
            """SELECT m.id message_id,m.deleted_at message_deleted_at,p.text,
                      p.kind part_kind,p.sensitive,p.draft
               FROM thread_messages m
               JOIN thread_message_parts p ON p.message_id=m.id
               WHERE m.thread_id=? ORDER BY m.created_at,m.id,p.ordinal""",
            (thread["id"],),
        ):
            part = dict(raw)
            if not memory_admits("thread_part", part):
                continue
            if str(part["text"] or "").strip():
                by_message.setdefault(str(part["message_id"]), []).append(str(part["text"]))
        units = [(message_id, "\n".join(texts)) for message_id, texts in by_message.items()]
        if not units:
            continue
        yield MemorySource(
            ref, "thread", str(thread["title"] or ""), thread["occurred_at"], units, pack=False
        )


#: One reader per kind memory holds today.  The order is the sweep order.
SOURCE_READERS: dict[str, Callable[[sqlite3.Connection, set[str]], Iterator[MemorySource]]] = {
    "decision": _simple(
        "decision",
        "SELECT id,text,rationale,decided_at,deleted,source_state FROM decisions ORDER BY id",
        lambda row: (str(row["text"]), row["decided_at"], [("", str(row["rationale"] or ""))]),
    ),
    "decision_record": _simple(
        "decision_record",
        "SELECT id,decision_text,rationale,alternatives,owner,updated_at,deleted"
        " FROM decision_records ORDER BY id",
        lambda row: (
            str(row["decision_text"]),
            row["updated_at"],
            [("", _text(row["rationale"], row["alternatives"], row["owner"]))],
        ),
    ),
    "desk_decision": _simple(
        "desk_decision",
        "SELECT id,title,context_markdown,decision_markdown,consequences_markdown,"
        "alternatives_json,updated_at,deleted FROM desk_decisions ORDER BY id",
        _desk_decision,
    ),
    "artifact": _simple(
        "artifact",
        "SELECT id,title,body_markdown,updated_at FROM artifacts ORDER BY id",
        lambda row: (
            str(row["title"] or ""),
            row["updated_at"],
            [("", part) for part in paragraphs(row["body_markdown"])],
        ),
    ),
    "meeting": _meetings,
    "note": _simple(
        "note",
        "SELECT id,title,body_markdown,updated_at,deleted FROM notes ORDER BY id",
        lambda row: (
            str(row["title"] or ""),
            row["updated_at"],
            [("", part) for part in paragraphs(row["body_markdown"])],
        ),
    ),
    "thread": _threads,
    "action": _simple(
        "action",
        "SELECT id,task,owner,due,status,COALESCE(completed_at,created_at) occurred_at"
        " FROM action_items ORDER BY id",
        lambda row: (
            str(row["task"]),
            row["occurred_at"],
            [("", _text(row["owner"], row["due"], row["status"]))],
        ),
    ),
    "project_item": _simple(
        "project_item",
        "SELECT id,title,summary,details_json,item_type,updated_at FROM project_items ORDER BY id",
        lambda row: (
            str(row["title"] or ""),
            row["updated_at"],
            [("", _text(row["summary"], row["details_json"]))],
        ),
    ),
    "workbench_item": _simple(
        "workbench_item",
        "SELECT id,title,body,result,status,last_modified FROM workbench_items ORDER BY id",
        lambda row: (
            str(row["title"] or ""),
            row["last_modified"],
            [("", part) for part in paragraphs(_text(row["body"]))]
            + [("result", str(row["result"] or ""))],
        ),
    ),
    "cadence": _simple(
        "cadence",
        "SELECT id,title,summary,status,priority,owner,updated_at FROM cadence_loops ORDER BY id",
        lambda row: (str(row["title"]), row["updated_at"], [("", _text(row["summary"], row["owner"]))]),
    ),
}


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def prepare(source: MemorySource) -> tuple[str, list[dict[str, Any]]]:
    """Redact, hash and chunk one admitted source.

    Returns ``(content_sha, chunks)``.  The hash is over the REDACTED text, so
    a secret is never in a hash input that is stored.
    """
    title = redact(source.title)
    units = [(anchor, redact(text)) for anchor, text in source.units if str(text or "").strip()]
    content_sha = _sha([title, source.occurred_at, units, source.pack])
    if source.pack:
        cut = chunk_units(title, units)
    else:
        cut = []
        for anchor, text in units:
            for chunk in chunk_units(title, [(anchor, text)]):
                cut.append(type(chunk)(ordinal=len(cut), anchor=anchor, text=chunk.text))
    chunks = [
        {
            "id": f"{source.ref}#{chunk.ordinal}",
            "ordinal": chunk.ordinal,
            "anchor": chunk.anchor,
            "text": chunk.text,
            "content_sha": _sha(chunk.text),
        }
        for chunk in cut
        if chunk.text.strip()
    ]
    return content_sha, chunks


def sweep(
    db: Any,
    *,
    kinds: Optional[Iterable[str]] = None,
    max_sources: Optional[int] = None,
) -> dict[str, int]:
    """Make the chunk index equal to the admitted source rows.

    ``max_sources`` stops the sweep after that many writes (a test uses it to
    stand in for a crash).  A sweep that stopped early never marks a source
    ``gone``: only a kind that was read to its end can say what left.
    """
    selected = [kind for kind in SOURCE_READERS if kinds is None or kind in set(kinds)]
    index = db.memory_index
    ledger = index.ledger(selected)
    stats = {"seen": 0, "written": 0, "unchanged": 0, "gone": 0}
    for kind in selected:
        with db._connection() as conn:
            try:
                sources = list(SOURCE_READERS[kind](conn, _promoted(conn)))
            except sqlite3.Error as exc:  # a store this database does not carry
                log.warning("memory sweep could not read %s: %s", kind, exc)
                continue
        seen: set[str] = set()
        for source in sources:
            content_sha, chunks = prepare(source)
            if not chunks:
                continue
            seen.add(source.ref)
            stats["seen"] += 1
            known = ledger.get(source.ref)
            if (
                known is not None
                and known["state"] == "live"
                and known["content_sha"] == content_sha
                and int(known["chunker_version"]) == CHUNKER_VERSION
            ):
                stats["unchanged"] += 1
                continue
            if max_sources is not None and stats["written"] >= max_sources:
                return {**stats, "complete": 0}
            index.replace_source(
                source_ref=source.ref,
                kind=source.kind,
                title=redact(source.title),
                occurred_at=source.occurred_at,
                content_sha=content_sha,
                chunker_version=CHUNKER_VERSION,
                chunks=chunks,
            )
            stats["written"] += 1
        for ref, known in ledger.items():
            if known["kind"] == kind and known["state"] == "live" and ref not in seen:
                index.mark_gone(ref)
                stats["gone"] += 1
    return {**stats, "complete": 1}


def embed_pending(
    db: Any,
    embedder: MemoryEmbedder,
    *,
    batch_size: int = EMBED_BATCH,
    max_batches: Optional[int] = None,
) -> int:
    """Give every chunk without a current vector to the engine.

    One batch is one engine call and one transaction.  An engine error stops
    the step; the batches already written stay, the failed batch writes
    nothing.  Returns the number of vectors written.
    """
    index = db.memory_index
    written = 0
    batches = 0
    while max_batches is None or batches < max_batches:
        pending = index.pending_chunks(embedder.model_id, limit=batch_size)
        if not pending:
            break
        vectors = embedder.embed_documents([str(row["text"]) for row in pending])
        if len(vectors) != len(pending):
            raise RuntimeError("the embedding engine gave the wrong number of vectors")
        stored = index.store_vectors(
            embedder.model_id,
            embedder.dim,
            [
                (str(row["id"]), str(row["content_sha"]), vectors[position])
                for position, row in enumerate(pending)
            ],
        )
        written += stored
        batches += 1
        if stored == 0:
            # Every chunk of the batch changed while the engine ran.  The next
            # sweep and embed pass take them; do not spin here.
            break
    return written


def rebuild(db: Any, embedder: Optional[MemoryEmbedder] = None) -> dict[str, int]:
    """Drop every derived memory row and build the index again from the
    source tables: the keyword tables, the chunks and, with an engine, the
    vectors."""
    keyword = db.memory.rebuild()
    db.memory_index.clear()
    swept = sweep(db)
    vectors = embed_pending(db, embedder) if embedder is not None else 0
    stats = db.memory_index.stats()
    return {
        "keyword_rows": int(keyword.get("total", 0)),
        "sources": stats["sources"],
        "chunks": stats["chunks"],
        "vectors": stats["vectors"],
        "written": swept["written"],
        "embedded": vectors,
    }


__all__ = [
    "MemorySource",
    "SOURCE_READERS",
    "embed_pending",
    "prepare",
    "rebuild",
    "sweep",
]
