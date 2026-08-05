"""Constitutional context: the owner's always-on briefing for every agent run.

A single markdown document, revisioned and hashed, injected as the first system
tier in every agent prompt. Immutable for the duration of a run — edits mid-session
take effect on the next run, never the current one.

HS-116-13: migrated from file to DB. Single row in constitutional_context table,
last 10 revisions in constitutional_context_history.

Articles served: II (a primitive), III (honest egress — the context itself never
leaves the machine unless a run carries it), VII (no prose — the editor IS the
surface).
"""
from __future__ import annotations

import hashlib
from typing import Optional

from .logging_config import get_logger

log = get_logger("constitutional_context")

CHAR_LIMIT = 32_768


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _db():
    from .db import get_database
    return get_database()


def get_constitutional_context() -> dict:
    """Return the current constitutional context: content, revision, hash."""
    try:
        db = _db()
        conn = db._conn
        row = conn.execute(
            "SELECT content, revision, content_hash, updated_at FROM constitutional_context WHERE id = 1"
        ).fetchone()
        if row:
            return {
                "content": row[0],
                "revision": row[1],
                "content_hash": row[2],
                "updated_at": row[3],
            }
    except Exception:
        pass
    return {"content": "", "revision": 0, "content_hash": _sha256("")}


def update_constitutional_context(content: str) -> dict:
    """Update the constitutional context. Auto-increments revision, recomputes hash.

    Raises ValueError if content exceeds the character limit.
    """
    new_content = content.strip()
    if len(new_content) > CHAR_LIMIT:
        raise ValueError(
            f"Constitutional context exceeds {CHAR_LIMIT:,} character limit "
            f"(got {len(new_content):,})"
        )

    current = get_constitutional_context()
    new_revision = current.get("revision", 0) + 1
    new_hash = _sha256(new_content)

    try:
        db = _db()
        conn = db._conn
        conn.execute(
            """INSERT INTO constitutional_context (id, content, revision, content_hash, updated_at)
               VALUES (1, ?, ?, ?, datetime('now'))
               ON CONFLICT(id) DO UPDATE SET
                 content = excluded.content,
                 revision = excluded.revision,
                 content_hash = excluded.content_hash,
                 updated_at = excluded.updated_at""",
            (new_content, new_revision, new_hash),
        )
        conn.execute(
            """INSERT INTO constitutional_context_history (content, revision, content_hash)
               VALUES (?, ?, ?)""",
            (new_content, new_revision, new_hash),
        )
        # Keep only last 10 revisions
        conn.execute(
            """DELETE FROM constitutional_context_history
               WHERE id NOT IN (
                 SELECT id FROM constitutional_context_history ORDER BY id DESC LIMIT 10
               )"""
        )
        conn.commit()
    except Exception as exc:
        log.error(f"Failed to update constitutional context: {exc}")
        raise

    return {
        "content": new_content,
        "revision": new_revision,
        "content_hash": new_hash,
    }


def get_constitutional_history() -> list[dict]:
    """Return the last 10 revisions, newest first."""
    try:
        db = _db()
        conn = db._conn
        rows = conn.execute(
            """SELECT content, revision, content_hash, created_at
               FROM constitutional_context_history
               ORDER BY id DESC LIMIT 10"""
        ).fetchall()
        return [
            {"content": r[0], "revision": r[1], "content_hash": r[2], "created_at": r[3]}
            for r in rows
        ]
    except Exception:
        return []


def constitutional_system_message() -> Optional[str]:
    """Return the constitutional context as a system message string, or None if empty."""
    ctx = get_constitutional_context()
    content = ctx.get("content", "").strip()
    if not content:
        return None
    return content


def constitutional_receipt() -> dict:
    """Return the revision + hash for stamping into run receipts."""
    ctx = get_constitutional_context()
    return {
        "revision": ctx.get("revision", 0),
        "content_hash": ctx.get("content_hash", ""),
    }
