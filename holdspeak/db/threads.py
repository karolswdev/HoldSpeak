"""Thread ledger persistence (HS-150-01).

CRUD + tree operations for persistent desk conversations: threads, messages
(with parent_id tree), typed parts, frozen refs, and FTS search.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from .base import BaseRepository


# ---------------------------------------------------------------------------
# Frozen dataclass models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Thread:
    id: str
    title: str
    recipe_id: str
    profile_override: str
    directory_id: str
    parent_thread_id: str
    status_line: str
    token_in: int
    token_out: int
    created_at: float
    updated_at: float
    last_turn_at: Optional[float]
    deleted_at: Optional[float]


@dataclass(frozen=True)
class ThreadMessage:
    id: str
    thread_id: str
    parent_id: Optional[str]
    role: str
    streaming: bool
    operation_id: str
    receipt_id: str
    invocation_id: str
    egress_scope: str
    egress_host: str
    model_id: str
    route_plan_id: str
    stats_json: str
    error_json: str
    created_at: float
    updated_at: float
    completed_at: Optional[float]
    aborted_at: Optional[float]
    deleted_at: Optional[float]


@dataclass(frozen=True)
class ThreadMessagePart:
    id: str
    message_id: str
    ordinal: int
    kind: str
    text: Optional[str]
    tool_call_id: str
    attachment_ref: str
    meta_json: str
    sensitive: bool


@dataclass(frozen=True)
class ThreadRef:
    id: str
    thread_id: str
    message_id: Optional[str]
    ref_kind: str
    ref_id: str
    version: str
    frozen_json: str
    created_at: float


# ---------------------------------------------------------------------------
# Row converters
# ---------------------------------------------------------------------------

def _row_to_thread(row: Any) -> Thread:
    return Thread(
        id=str(row["id"]),
        title=str(row["title"] or ""),
        recipe_id=str(row["recipe_id"] or ""),
        profile_override=str(row["profile_override"] or ""),
        directory_id=str(row["directory_id"] or ""),
        parent_thread_id=str(row["parent_thread_id"] or ""),
        status_line=str(row["status_line"] or ""),
        token_in=int(row["token_in"]),
        token_out=int(row["token_out"]),
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
        last_turn_at=float(row["last_turn_at"]) if row["last_turn_at"] is not None else None,
        deleted_at=float(row["deleted_at"]) if row["deleted_at"] is not None else None,
    )


def _row_to_message(row: Any) -> ThreadMessage:
    return ThreadMessage(
        id=str(row["id"]),
        thread_id=str(row["thread_id"]),
        parent_id=str(row["parent_id"]) if row["parent_id"] else None,
        role=str(row["role"]),
        streaming=bool(row["streaming"]),
        operation_id=str(row["operation_id"] or ""),
        receipt_id=str(row["receipt_id"] or ""),
        invocation_id=str(row["invocation_id"] or ""),
        egress_scope=str(row["egress_scope"] or ""),
        egress_host=str(row["egress_host"] or ""),
        model_id=str(row["model_id"] or ""),
        route_plan_id=str(row["route_plan_id"] or ""),
        stats_json=str(row["stats_json"] or ""),
        error_json=str(row["error_json"] or ""),
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
        completed_at=float(row["completed_at"]) if row["completed_at"] is not None else None,
        aborted_at=float(row["aborted_at"]) if row["aborted_at"] is not None else None,
        deleted_at=float(row["deleted_at"]) if row["deleted_at"] is not None else None,
    )


def _row_to_part(row: Any) -> ThreadMessagePart:
    return ThreadMessagePart(
        id=str(row["id"]),
        message_id=str(row["message_id"]),
        ordinal=int(row["ordinal"]),
        kind=str(row["kind"]),
        text=str(row["text"]) if row["text"] is not None else None,
        tool_call_id=str(row["tool_call_id"] or ""),
        attachment_ref=str(row["attachment_ref"] or ""),
        meta_json=str(row["meta_json"] or ""),
        sensitive=bool(row["sensitive"]),
    )


def _row_to_ref(row: Any) -> ThreadRef:
    return ThreadRef(
        id=str(row["id"]),
        thread_id=str(row["thread_id"]),
        message_id=str(row["message_id"]) if row["message_id"] else None,
        ref_kind=str(row["ref_kind"] or ""),
        ref_id=str(row["ref_id"] or ""),
        version=str(row["version"] or ""),
        frozen_json=str(row["frozen_json"] or ""),
        created_at=float(row["created_at"]),
    )


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class ThreadRepository(BaseRepository):
    """Persistence layer for threads, messages, parts, refs, and FTS search."""

    table = "threads"

    # ── Thread CRUD ─────────────────────────────────────────────────

    def create_thread(
        self,
        *,
        title: str = "",
        recipe_id: str = "",
        profile_override: str = "",
        directory_id: str = "",
        parent_thread_id: str = "",
        status_line: str = "",
    ) -> Thread:
        thread_id = _new_id("th")
        now = time.time()
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO threads
                   (id, title, recipe_id, profile_override, directory_id,
                    parent_thread_id, status_line, token_in, token_out,
                    created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,0,0,?,?)""",
                (thread_id, title, recipe_id, profile_override, directory_id,
                 parent_thread_id, status_line, now, now),
            )
            row = conn.execute(
                "SELECT * FROM threads WHERE id=?", (thread_id,)
            ).fetchone()
        return _row_to_thread(row)

    def get(self, thread_id: str) -> Optional[Thread]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM threads WHERE id=?", (str(thread_id),)
            ).fetchone()
        return _row_to_thread(row) if row else None

    def list(self, *, limit: int = 100, ref_id: str = "") -> list[Thread]:
        """Return newest-first, excluding soft-deleted threads.

        When *ref_id* is non-empty, only threads whose ``thread_refs``
        contain at least one row with that ``ref_id`` are returned.
        """
        with self._connection() as conn:
            if ref_id:
                rows = conn.execute(
                    "SELECT DISTINCT t.* FROM threads t "
                    "JOIN thread_refs r ON r.thread_id = t.id "
                    "WHERE t.deleted_at IS NULL AND r.ref_id = ? "
                    "ORDER BY t.updated_at DESC LIMIT ?",
                    (ref_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM threads WHERE deleted_at IS NULL "
                    "ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [_row_to_thread(r) for r in rows]

    def patch(
        self,
        thread_id: str,
        *,
        title: Optional[str] = None,
        profile_override: Optional[str] = None,
        status_line: Optional[str] = None,
    ) -> Optional[Thread]:
        sets: list[str] = []
        params: list[Any] = []
        if title is not None:
            sets.append("title=?")
            params.append(title)
        if profile_override is not None:
            sets.append("profile_override=?")
            params.append(profile_override)
        if status_line is not None:
            sets.append("status_line=?")
            params.append(status_line)
        if not sets:
            return self.get(thread_id)
        sets.append("updated_at=?")
        params.append(time.time())
        params.append(str(thread_id))
        with self._connection() as conn:
            conn.execute(
                f"UPDATE threads SET {','.join(sets)} WHERE id=?",
                params,
            )
            row = conn.execute(
                "SELECT * FROM threads WHERE id=?", (str(thread_id),)
            ).fetchone()
        return _row_to_thread(row) if row else None

    def soft_delete(self, thread_id: str) -> bool:
        """Soft-delete a thread (sets deleted_at). Returns True if a row was updated."""
        now = time.time()
        with self._connection() as conn:
            cursor = conn.execute(
                "UPDATE threads SET deleted_at=?, updated_at=? "
                "WHERE id=? AND deleted_at IS NULL",
                (now, now, str(thread_id)),
            )
            # Also soft-delete all messages in this thread so FTS triggers fire.
            if cursor.rowcount:
                conn.execute(
                    "UPDATE thread_messages SET deleted_at=?, updated_at=? "
                    "WHERE thread_id=? AND deleted_at IS NULL",
                    (now, now, str(thread_id)),
                )
        return bool(cursor.rowcount)

    # ── Messages ────────────────────────────────────────────────────

    def append_message(
        self,
        thread_id: str,
        *,
        role: str,
        parent_id: Optional[str] = None,
        operation_id: str = "",
        receipt_id: str = "",
        invocation_id: str = "",
        egress_scope: str = "",
        egress_host: str = "",
        model_id: str = "",
        route_plan_id: str = "",
    ) -> ThreadMessage:
        msg_id = _new_id("tm")
        now = time.time()
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO thread_messages
                   (id, thread_id, parent_id, role, streaming,
                    operation_id, receipt_id, invocation_id,
                    egress_scope, egress_host, model_id, route_plan_id,
                    stats_json, error_json, created_at, updated_at)
                   VALUES (?,?,?,?,0,?,?,?,?,?,?,?,?,?,?,?)""",
                (msg_id, str(thread_id), parent_id, role,
                 operation_id, receipt_id, invocation_id,
                 egress_scope, egress_host, model_id, route_plan_id,
                 "", "", now, now),
            )
            # Touch thread's updated_at and last_turn_at.
            conn.execute(
                "UPDATE threads SET updated_at=?, last_turn_at=? WHERE id=?",
                (now, now, str(thread_id)),
            )
            row = conn.execute(
                "SELECT * FROM thread_messages WHERE id=?", (msg_id,)
            ).fetchone()
        return _row_to_message(row)

    def get_message(self, message_id: str) -> Optional[ThreadMessage]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM thread_messages WHERE id=?", (str(message_id),)
            ).fetchone()
        return _row_to_message(row) if row else None

    # ── Parts ───────────────────────────────────────────────────────

    def append_part(
        self,
        message_id: str,
        *,
        kind: str,
        text: Optional[str] = None,
        ordinal: Optional[int] = None,
        tool_call_id: str = "",
        attachment_ref: str = "",
        meta_json: str = "",
        sensitive: bool = False,
    ) -> ThreadMessagePart:
        part_id = _new_id("tp")
        with self._connection() as conn:
            if ordinal is None:
                row = conn.execute(
                    "SELECT COALESCE(MAX(ordinal), -1) + 1 AS next_ord "
                    "FROM thread_message_parts WHERE message_id=?",
                    (str(message_id),),
                ).fetchone()
                ordinal = int(row["next_ord"])
            conn.execute(
                """INSERT INTO thread_message_parts
                   (id, message_id, ordinal, kind, text,
                    tool_call_id, attachment_ref, meta_json, sensitive)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (part_id, str(message_id), ordinal, kind, text,
                 tool_call_id, attachment_ref, meta_json, int(bool(sensitive))),
            )
            # Touch message updated_at.
            now = time.time()
            conn.execute(
                "UPDATE thread_messages SET updated_at=? WHERE id=?",
                (now, str(message_id)),
            )
            row = conn.execute(
                "SELECT * FROM thread_message_parts WHERE id=?", (part_id,)
            ).fetchone()
        return _row_to_part(row)

    def extend_part_text(self, part_id: str, chunk: str) -> None:
        """Append-only text extension (one UPDATE, cheap).

        Uses COALESCE so the first call on a NULL text column works.
        """
        with self._connection() as conn:
            conn.execute(
                "UPDATE thread_message_parts "
                "SET text = COALESCE(text, '') || ? WHERE id=?",
                (chunk, str(part_id)),
            )
            # Touch the parent message's updated_at for streaming cadence.
            conn.execute(
                """UPDATE thread_messages SET updated_at=?
                   WHERE id = (SELECT message_id FROM thread_message_parts WHERE id=?)""",
                (time.time(), str(part_id)),
            )

    def get_parts(self, message_id: str) -> list[ThreadMessagePart]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM thread_message_parts "
                "WHERE message_id=? ORDER BY ordinal",
                (str(message_id),),
            ).fetchall()
        return [_row_to_part(r) for r in rows]

    # ── Streaming lifecycle ─────────────────────────────────────────

    def mark_streaming(self, message_id: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE thread_messages SET streaming=1, updated_at=? WHERE id=?",
                (time.time(), str(message_id)),
            )

    def complete_message(
        self,
        message_id: str,
        *,
        receipt_id: str = "",
        stats_json: str = "",
        error_json: str = "",
    ) -> Optional[ThreadMessage]:
        now = time.time()
        with self._connection() as conn:
            conn.execute(
                "UPDATE thread_messages "
                "SET streaming=0, completed_at=?, updated_at=?, receipt_id=?, "
                "stats_json=?, error_json=? "
                "WHERE id=?",
                (now, now, receipt_id, stats_json, error_json, str(message_id)),
            )
            row = conn.execute(
                "SELECT * FROM thread_messages WHERE id=?", (str(message_id),)
            ).fetchone()
        return _row_to_message(row) if row else None

    def abort_message(self, message_id: str) -> Optional[ThreadMessage]:
        now = time.time()
        with self._connection() as conn:
            conn.execute(
                "UPDATE thread_messages "
                "SET streaming=0, aborted_at=?, updated_at=? WHERE id=?",
                (now, now, str(message_id)),
            )
            row = conn.execute(
                "SELECT * FROM thread_messages WHERE id=?", (str(message_id),)
            ).fetchone()
        return _row_to_message(row) if row else None

    # ── Tree operations ─────────────────────────────────────────────

    def list_path(self, thread_id: str) -> list[ThreadMessage]:
        """Return the messages on the newest leaf path (root to leaf).

        The leaf is the newest non-deleted message with no children. The path
        walks parent_id pointers back to the root, then reverses.
        """
        with self._connection() as conn:
            # All non-deleted messages for this thread.
            rows = conn.execute(
                "SELECT * FROM thread_messages "
                "WHERE thread_id=? AND deleted_at IS NULL "
                "ORDER BY created_at",
                (str(thread_id),),
            ).fetchall()

        if not rows:
            return []

        messages = [_row_to_message(r) for r in rows]
        by_id = {m.id: m for m in messages}
        # Messages that are parents of other messages.
        parent_ids = {m.parent_id for m in messages if m.parent_id}
        # Leaves = messages with no children.
        leaves = [m for m in messages if m.id not in parent_ids]
        if not leaves:
            # Shouldn't happen in a well-formed tree; fall back to newest.
            leaves = messages

        # Pick the newest leaf.
        leaf = max(leaves, key=lambda m: m.created_at)

        # Walk from leaf to root.
        path: list[ThreadMessage] = []
        current: Optional[ThreadMessage] = leaf
        visited: set[str] = set()
        while current is not None and current.id not in visited:
            visited.add(current.id)
            path.append(current)
            current = by_id.get(current.parent_id) if current.parent_id else None

        path.reverse()
        return path

    def siblings(self, message_id: str) -> tuple[int, int]:
        """Return (n, m) where this message is the nth of m siblings.

        Siblings share the same parent_id, ordered by created_at. A root
        message (parent_id IS NULL) counts siblings among other roots in the
        same thread.
        """
        with self._connection() as conn:
            msg_row = conn.execute(
                "SELECT thread_id, parent_id, created_at FROM thread_messages WHERE id=?",
                (str(message_id),),
            ).fetchone()
            if not msg_row:
                return (1, 1)

            thread_id = msg_row["thread_id"]
            parent_id = msg_row["parent_id"]

            if parent_id:
                sibling_rows = conn.execute(
                    "SELECT id FROM thread_messages "
                    "WHERE thread_id=? AND parent_id=? AND deleted_at IS NULL "
                    "ORDER BY created_at",
                    (thread_id, parent_id),
                ).fetchall()
            else:
                sibling_rows = conn.execute(
                    "SELECT id FROM thread_messages "
                    "WHERE thread_id=? AND parent_id IS NULL AND deleted_at IS NULL "
                    "ORDER BY created_at",
                    (thread_id,),
                ).fetchall()

        ids = [str(r["id"]) for r in sibling_rows]
        m = len(ids)
        try:
            n = ids.index(str(message_id)) + 1
        except ValueError:
            n = 1
        return (n, m)

    # ── Refs ────────────────────────────────────────────────────────

    def freeze_refs(
        self,
        thread_id: str,
        message_id: Optional[str],
        refs: list[dict[str, Any]],
    ) -> list[ThreadRef]:
        """Persist a batch of frozen ref leaves for a thread/message."""
        now = time.time()
        result: list[ThreadRef] = []
        with self._connection() as conn:
            for ref in refs:
                ref_row_id = _new_id("tr")
                frozen = ref.get("frozen_json", "")
                if isinstance(frozen, dict):
                    frozen = json.dumps(frozen, separators=(",", ":"), sort_keys=True)
                conn.execute(
                    """INSERT INTO thread_refs
                       (id, thread_id, message_id, ref_kind, ref_id,
                        version, frozen_json, created_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (ref_row_id, str(thread_id), message_id,
                     str(ref.get("ref_kind", "")),
                     str(ref.get("ref_id", "")),
                     str(ref.get("version", "")),
                     str(frozen),
                     now),
                )
                row = conn.execute(
                    "SELECT * FROM thread_refs WHERE id=?", (ref_row_id,)
                ).fetchone()
                result.append(_row_to_ref(row))
        return result

    def get_refs(self, thread_id: str) -> list[ThreadRef]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM thread_refs WHERE thread_id=? ORDER BY created_at",
                (str(thread_id),),
            ).fetchall()
        return [_row_to_ref(r) for r in rows]

    # ── Search (FTS) ────────────────────────────────────────────────

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """BM25 search over thread message text. Returns dicts with
        thread_id, message_id, part_id, snippet. Never returns deleted content.
        """
        if not query or not query.strip():
            return []
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT p.id AS part_id, p.message_id, m.thread_id,
                          snippet(thread_messages_fts, 0, '<mark>', '</mark>', '...', 32) AS snippet
                   FROM thread_messages_fts
                   JOIN thread_message_parts p ON p.rowid = thread_messages_fts.rowid
                   JOIN thread_messages m ON m.id = p.message_id
                   JOIN threads t ON t.id = m.thread_id
                   WHERE thread_messages_fts MATCH ?
                     AND m.deleted_at IS NULL
                     AND t.deleted_at IS NULL
                   ORDER BY thread_messages_fts.rank
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Token totals ────────────────────────────────────────────────

    def add_token_totals(
        self,
        thread_id: str,
        *,
        token_in: int = 0,
        token_out: int = 0,
    ) -> None:
        """Increment the thread's cumulative token counters (counsel S3, R4)."""
        with self._connection() as conn:
            conn.execute(
                "UPDATE threads SET token_in = token_in + ?, token_out = token_out + ?, "
                "updated_at = ? WHERE id=?",
                (max(0, token_in), max(0, token_out), time.time(), str(thread_id)),
            )

    # ── Import (D7 dedup) ──────────────────────────────────────────

    def import_threads(self, payload: list[dict[str, Any]]) -> dict[str, str]:
        """Import threads from the old localStorage payload.

        Dedup key = sha256(recipe_id + first user text + created_ts), stored
        as a thread_refs row with ref_kind='import_hash' (counsel S2).

        Returns a mapping of import_hash -> thread_id for every item in the
        payload (whether newly created or already existing).
        """
        result: dict[str, str] = {}
        for item in payload:
            recipe_id = str(item.get("recipe_id", ""))
            messages = item.get("messages", [])
            first_user_text = ""
            for msg in messages:
                if msg.get("role") == "user":
                    parts = msg.get("parts", [])
                    if parts:
                        first_user_text = str(parts[0].get("text", ""))
                    elif msg.get("text"):
                        first_user_text = str(msg["text"])
                    break
            created_ts = str(item.get("created_at", item.get("created_ts", "")))
            import_hash = hashlib.sha256(
                f"{recipe_id}{first_user_text}{created_ts}".encode()
            ).hexdigest()

            # Check for existing import.
            with self._connection() as conn:
                existing = conn.execute(
                    "SELECT thread_id FROM thread_refs "
                    "WHERE ref_kind='import_hash' AND ref_id=?",
                    (import_hash,),
                ).fetchone()

            if existing:
                result[import_hash] = str(existing["thread_id"])
                continue

            # Create the thread.
            thread = self.create_thread(
                title=str(item.get("title", "")),
                recipe_id=recipe_id,
            )

            # Create messages.
            parent_msg_id: Optional[str] = None
            for msg in messages:
                role = str(msg.get("role", "user"))
                tm = self.append_message(
                    thread.id,
                    role=role,
                    parent_id=parent_msg_id,
                )
                parts = msg.get("parts", [])
                if parts:
                    for i, part in enumerate(parts):
                        self.append_part(
                            tm.id,
                            kind=str(part.get("kind", "text")),
                            text=part.get("text"),
                            ordinal=i,
                        )
                elif msg.get("text"):
                    self.append_part(
                        tm.id,
                        kind="text",
                        text=str(msg["text"]),
                        ordinal=0,
                    )
                parent_msg_id = tm.id

            # Store the import_hash ref.
            self.freeze_refs(thread.id, None, [
                {"ref_kind": "import_hash", "ref_id": import_hash},
            ])

            result[import_hash] = thread.id

        return result
