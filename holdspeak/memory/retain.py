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
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Optional

from ..logging_config import get_logger
from .admission import memory_admits
from .chunker import CHUNKER_VERSION, chunk_units, paragraphs
from .defense import redact_parts
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


_PARKED_MEETING = "EXISTS (SELECT 1 FROM meetings pk WHERE pk.id={column} AND pk.parked=1)"

Reader = Callable[[sqlite3.Connection, set[str], Optional[str]], Iterator[MemorySource]]


def _simple(
    kind: str,
    select: str,
    id_column: str,
    build: Callable[[dict[str, Any]], tuple[str, Optional[str], list[tuple[str, str]]]],
) -> Reader:
    """A reader over one table.  ``only_id`` reads one row: the same SQL, the
    same admission and the same text as the sweep, for the read-time check."""

    def read(
        conn: sqlite3.Connection, promoted: set[str], only_id: Optional[str] = None
    ) -> Iterator[MemorySource]:
        if only_id is None:
            rows = conn.execute(f"{select} ORDER BY {id_column}")
        else:
            rows = conn.execute(f"{select} WHERE {id_column}=?", (only_id,))
        for raw in rows:
            row = dict(raw)
            ref = f"{kind}:{row['id']}"
            row["promoted"] = ref in promoted
            if not memory_admits(kind, row):
                continue
            title, occurred_at, units = build(row)
            yield MemorySource(ref, kind, title, occurred_at, units)

    return read


def _spec(kind: str, flags: str = "") -> Reader:
    """A reader made from the keyword search's own spec for the kind (title,
    body and time are the same expressions), so the two cannot drift."""
    from ..db.memory import _ECOSYSTEM_SPECS

    spec = _ECOSYSTEM_SPECS[kind]
    extra = f",{flags}" if flags else ""
    select = (
        f"SELECT {spec['id']} id,{spec['title']} title,{spec['body']} body,"
        f"{spec['time']} occurred_at{extra} FROM {spec['table']} {spec['alias']}"
    )
    return _simple(
        kind,
        select,
        spec["id"],
        lambda row: (
            str(row["title"] or ""),
            row["occurred_at"],
            [("", part) for part in paragraphs(str(row["body"] or ""))],
        ),
    )


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


def _meetings(
    conn: sqlite3.Connection, promoted: set[str], only_id: Optional[str] = None
) -> Iterator[MemorySource]:
    sql = "SELECT id,title,started_at,parked FROM meetings"
    meetings = [
        dict(row)
        for row in (
            conn.execute(sql + " ORDER BY id")
            if only_id is None
            else conn.execute(sql + " WHERE id=?", (only_id,))
        )
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
        # The summary and the topics as the meeting reads now (the keyword
        # search finds a word that is only there; so does the vector search).
        summary = conn.execute(
            "SELECT summary FROM intel_snapshots WHERE meeting_id=?"
            " ORDER BY timestamp DESC,id DESC LIMIT 1",
            (meeting["id"],),
        ).fetchone()
        if summary is not None and str(summary[0] or "").strip():
            units.append(("summary", "Summary: " + str(summary[0])))
        topics = [
            str(row[0])
            for row in conn.execute(
                "SELECT topic FROM topics WHERE meeting_id=? ORDER BY id", (meeting["id"],)
            )
            if str(row[0] or "").strip()
        ]
        if topics:
            units.append(("topics", "Topics: " + " · ".join(topics)))
        if not units:
            continue
        yield MemorySource(
            ref, "meeting", str(meeting["title"] or meeting["id"]), meeting["started_at"], units
        )


def _threads(
    conn: sqlite3.Connection, promoted: set[str], only_id: Optional[str] = None
) -> Iterator[MemorySource]:
    sql = (
        "SELECT id,title,deleted_at,datetime(updated_at,'unixepoch') occurred_at"
        " FROM threads"
    )
    threads = [
        dict(row)
        for row in (
            conn.execute(sql + " ORDER BY id")
            if only_id is None
            else conn.execute(sql + " WHERE id=?", (only_id,))
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


def _readers() -> dict[str, Reader]:
    return {
        "decision": _simple(
            "decision",
            "SELECT id,text,rationale,decided_at,deleted,source_state,"
            + _PARKED_MEETING.format(column="decisions.source_meeting_id")
            + " parked FROM decisions",
            "id",
            lambda row: (str(row["text"]), row["decided_at"], [("", str(row["rationale"] or ""))]),
        ),
        "decision_record": _simple(
            "decision_record",
            "SELECT id,decision_text,rationale,alternatives,owner,updated_at,deleted"
            " FROM decision_records",
            "id",
            lambda row: (
                str(row["decision_text"]),
                row["updated_at"],
                [("", _text(row["rationale"], row["alternatives"], row["owner"]))],
            ),
        ),
        "desk_decision": _simple(
            "desk_decision",
            "SELECT id,title,context_markdown,decision_markdown,consequences_markdown,"
            "alternatives_json,updated_at,deleted FROM desk_decisions",
            "id",
            _desk_decision,
        ),
        "artifact": _simple(
            "artifact",
            "SELECT id,title,body_markdown,updated_at,"
            + _PARKED_MEETING.format(column="artifacts.meeting_id")
            + " parked FROM artifacts",
            "id",
            lambda row: (
                str(row["title"] or ""),
                row["updated_at"],
                [("", part) for part in paragraphs(row["body_markdown"])],
            ),
        ),
        "meeting": _meetings,
        "note": _simple(
            "note",
            "SELECT id,title,body_markdown,updated_at,deleted FROM notes",
            "id",
            lambda row: (
                str(row["title"] or ""),
                row["updated_at"],
                [("", part) for part in paragraphs(row["body_markdown"])],
            ),
        ),
        "thread": _threads,
        "action": _simple(
            "action",
            "SELECT id,task,owner,due,status,COALESCE(completed_at,created_at) occurred_at,"
            + _PARKED_MEETING.format(column="action_items.meeting_id")
            + " parked FROM action_items",
            "id",
            lambda row: (
                str(row["task"]),
                row["occurred_at"],
                [("", _text(row["owner"], row["due"], row["status"]))],
            ),
        ),
        "project_item": _simple(
            "project_item",
            "SELECT id,title,summary,details_json,item_type,updated_at FROM project_items",
            "id",
            lambda row: (
                str(row["title"] or ""),
                row["updated_at"],
                [("", _text(row["summary"], row["details_json"]))],
            ),
        ),
        "workbench_item": _simple(
            "workbench_item",
            "SELECT id,title,body,result,status,parked,last_modified FROM workbench_items",
            "id",
            lambda row: (
                str(row["title"] or ""),
                row["last_modified"],
                [("", part) for part in paragraphs(_text(row["body"]))]
                + [("result", str(row["result"] or ""))],
            ),
        ),
        "cadence": _simple(
            "cadence",
            "SELECT id,title,summary,status,priority,owner,updated_at FROM cadence_loops",
            "id",
            lambda row: (
                str(row["title"]), row["updated_at"], [("", _text(row["summary"], row["owner"]))]
            ),
        ),
        # What he sent, published, prepared and has on the calendar.
        "send": _spec("send", "s.state state"),
        "project_update": _spec("project_update", "u.lifecycle lifecycle"),
        "prep_brief": _spec("prep_brief", "b.lifecycle lifecycle"),
        "calendar_event": _spec("calendar_event"),
    }


class _Readers(dict):
    """One reader per kind memory holds.  Built on first use (the spec
    readers read ``holdspeak.db.memory``, which imports this package)."""

    def _load(self) -> None:
        if not dict.__len__(self):
            dict.update(self, _readers())

    def __getitem__(self, key):
        self._load()
        return dict.__getitem__(self, key)

    def __iter__(self):
        self._load()
        return dict.__iter__(self)

    def __contains__(self, key):
        self._load()
        return dict.__contains__(self, key)

    def __len__(self):
        self._load()
        return dict.__len__(self)

    def get(self, key, default=None):
        self._load()
        return dict.get(self, key, default)


#: The order is the sweep order.
SOURCE_READERS: dict[str, Reader] = _Readers()


def current_source(conn: sqlite3.Connection, source_ref: str) -> Optional[MemorySource]:
    """The source as it is NOW, or None when memory may not hold it.

    Recall calls this for every vector candidate, so the decision to return a
    source is made against the live row with ``memory_admits`` - the same
    reader and the same admission as the sweep - never against what the index
    held when it was built.
    """
    kind, _, resource_id = str(source_ref or "").partition(":")
    reader = SOURCE_READERS.get(kind)
    if reader is None or not resource_id:
        return None
    promoted = (
        conn.execute(
            "SELECT 1 FROM context_promotions WHERE target_ref=? LIMIT 1", (source_ref,)
        ).fetchone()
        is not None
    )
    try:
        return next(iter(reader(conn, {source_ref} if promoted else set(), resource_id)), None)
    except sqlite3.Error:
        return None


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def redact_source(source: MemorySource) -> tuple[str, list[tuple[str, str]], bool]:
    """The COMPLETE admitted text of one source, redacted as one text.

    Returns ``(title, units, held_secret)``.  The title and every unit are
    read together, so a secret that runs across units (a key read aloud over
    many transcript turns) is one secret.  Every chunk and every snippet is
    cut from this, never from the raw text.
    """
    raw = [(anchor, str(text)) for anchor, text in source.units if str(text or "").strip()]
    parts, changed = redact_parts([str(source.title or "")] + [text for _anchor, text in raw])
    units = [(anchor, text) for (anchor, _raw), text in zip(raw, parts[1:])]
    return parts[0], units, changed


def _redacted(source: MemorySource) -> tuple[str, list[tuple[str, str]], str]:
    """Redact one admitted source and hash it.

    The hash is over the REDACTED text, so a secret is never in a hash input
    that is stored.
    """
    title, units, _changed = redact_source(source)
    return title, units, _sha([title, source.occurred_at, units, source.pack])


def _holds_secret(source: MemorySource, title: str, units: list[tuple[str, str]]) -> bool:
    raw = [(anchor, str(text)) for anchor, text in source.units if str(text or "").strip()]
    return title != str(source.title or "") or units != raw


def _chunks(source: MemorySource, title: str, units: list[tuple[str, str]]) -> list[dict[str, Any]]:
    if source.pack:
        cut = chunk_units(title, units)
    else:
        cut = []
        for anchor, text in units:
            for chunk in chunk_units(title, [(anchor, text)]):
                cut.append(type(chunk)(ordinal=len(cut), anchor=anchor, text=chunk.text))
    return [
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


def prepare(source: MemorySource) -> tuple[str, list[dict[str, Any]]]:
    """Redact, hash and chunk one admitted source: ``(content_sha, chunks)``."""
    title, units, content_sha = _redacted(source)
    return content_sha, _chunks(source, title, units)


_PREPARED_LOCK = threading.Lock()
_PREPARED: "OrderedDict[str, tuple[str, list[dict[str, Any]]]]" = OrderedDict()
_PREPARED_MAX = 256


def prepare_current(source: MemorySource) -> tuple[str, list[dict[str, Any]]]:
    """``prepare`` for the read path, with a small cache.

    The key is a hash of the RAW live source (title, time, every unit), so a
    source that changed in any way is cut again; only an unchanged source
    reuses its cut.  Recall checks each vector candidate against this.
    """
    key = _sha([source.ref, source.title, source.occurred_at, source.units, source.pack])
    with _PREPARED_LOCK:
        held = _PREPARED.get(key)
        if held is not None:
            _PREPARED.move_to_end(key)
            return held
    prepared = prepare(source)
    with _PREPARED_LOCK:
        _PREPARED[key] = prepared
        while len(_PREPARED) > _PREPARED_MAX:
            _PREPARED.popitem(last=False)
    return prepared


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
    secret_refs: list[str] = []
    for kind in selected:
        with db._connection() as conn:
            try:
                sources = list(SOURCE_READERS[kind](conn, _promoted(conn), None))
            except sqlite3.Error as exc:  # a store this database does not carry
                log.warning("memory sweep could not read %s: %s", kind, exc)
                continue
        seen: set[str] = set()
        for source in sources:
            title, units, content_sha = _redacted(source)
            if _holds_secret(source, title, units):
                # Checked on EVERY sweep, changed or not: a trigger writes the
                # raw text into the keyword table again on any source update.
                secret_refs.append(source.ref)
            known = ledger.get(source.ref)
            if (
                known is not None
                and known["state"] == "live"
                and known["content_sha"] == content_sha
                and int(known["chunker_version"]) == CHUNKER_VERSION
            ):
                # Same hash as the ledger: stop.  No chunk work for this source.
                seen.add(source.ref)
                stats["seen"] += 1
                stats["unchanged"] += 1
                continue
            chunks = _chunks(source, title, units)
            if not chunks:
                continue
            seen.add(source.ref)
            stats["seen"] += 1
            if max_sources is not None and stats["written"] >= max_sources:
                db.memory.scrub_keyword_rows(secret_refs)
                return {**stats, "complete": 0}
            index.replace_source(
                source_ref=source.ref,
                kind=source.kind,
                title=title,
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
    stats["scrubbed"] = db.memory.scrub_keyword_rows(secret_refs)
    return {**stats, "complete": 1}


#: A ``desk_changed`` kind that names more than one memory kind.
_CHANGE_KINDS: dict[str, tuple[str, ...]] = {
    "decision": ("decision", "decision_record", "desk_decision"),
    "workbench": ("workbench_item",),
    "update": ("project_update",),
    "brief": ("prep_brief",),
    "event": ("calendar_event",),
}


def refs_for_change(kind: str, resource_id: str) -> list[str]:
    """The memory source refs one ``desk_changed`` change can name.

    A kind memory does not hold gives no ref: the slow full sweep sees it.
    """
    kind, resource_id = str(kind or "").strip(), str(resource_id or "").strip()
    if not kind or not resource_id:
        return []
    kinds = _CHANGE_KINDS.get(kind) or ((kind,) if kind in SOURCE_READERS else ())
    return [f"{name}:{resource_id}" for name in kinds if name in SOURCE_READERS]


def sweep_refs(db: Any, refs: Iterable[str]) -> dict[str, int]:
    """The sweep for named sources only: the work is one read per ref.

    The same reader, admission, redaction and hash as ``sweep``.  A ref whose
    source is gone, parked or not admitted is marked ``gone`` when the index
    holds it.
    """
    index = db.memory_index
    wanted = list(dict.fromkeys(str(ref) for ref in refs))
    stats = {"seen": 0, "written": 0, "unchanged": 0, "gone": 0}
    if not wanted:
        return stats
    ledger = index.ledger_for(wanted)
    secret_refs: list[str] = []
    for ref in wanted:
        with db._connection() as conn:
            source = current_source(conn, ref)
        known = ledger.get(ref)
        chunks: list[dict[str, Any]] = []
        if source is not None:
            title, units, content_sha = _redacted(source)
            if _holds_secret(source, title, units):
                secret_refs.append(source.ref)
            stats["seen"] += 1
            if (
                known is not None
                and known["state"] == "live"
                and known["content_sha"] == content_sha
                and int(known["chunker_version"]) == CHUNKER_VERSION
            ):
                stats["unchanged"] += 1
                continue
            chunks = _chunks(source, title, units)
        if source is None or not chunks:
            if known is not None and known["state"] == "live":
                index.mark_gone(ref)
                stats["gone"] += 1
            continue
        index.replace_source(
            source_ref=source.ref,
            kind=source.kind,
            title=title,
            occurred_at=source.occurred_at,
            content_sha=content_sha,
            chunker_version=CHUNKER_VERSION,
            chunks=chunks,
        )
        stats["written"] += 1
    stats["scrubbed"] = db.memory.scrub_keyword_rows(secret_refs)
    return stats


def embed_pending(
    db: Any,
    embedder: MemoryEmbedder,
    *,
    batch_size: int = EMBED_BATCH,
    max_batches: Optional[int] = None,
    should_stop: Optional[Callable[[], bool]] = None,
    pause_seconds: float = 0.0,
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
        if should_stop is not None and should_stop():
            break
        if batches and pause_seconds > 0:
            # Leave room between two batches for a live model call.
            time.sleep(pause_seconds)
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
    "refs_for_change",
    "sweep_refs",
    "current_source",
    "embed_pending",
    "prepare",
    "prepare_current",
    "rebuild",
    "redact_source",
    "sweep",
]
