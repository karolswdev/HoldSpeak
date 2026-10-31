"""The briefing packages store (PG-DIRECTION DIR1, 2026-10-31): one table, static SQL only.

``briefing_packages`` (``holdspeak/db/schema.py``): a held item frozen for a
channel, with the SHA-256 of its page token (the token itself is never
stored), its expiry, its revocation and the one answer per ref. The rules
live in ``services/briefing_service.py``; this module only reads and writes.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Optional

_COLUMNS = ("id, kind, refs_json, body_json, token_hash, created_at, expires_at, revoked_at, sent_json, "
            "answers_json")


def _loads(raw: Any, default: Any) -> Any:
    try:
        value = json.loads(raw or "null")
    except ValueError:
        return default
    return value if isinstance(value, type(default)) else default


def _row(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"], "kind": row["kind"], "refs": _loads(row["refs_json"], []),
        "body": _loads(row["body_json"], {}), "token_hash": row["token_hash"],
        "created_at": row["created_at"], "expires_at": row["expires_at"], "revoked_at": row["revoked_at"],
        "sent": _loads(row["sent_json"], []), "answers": _loads(row["answers_json"], {}),
    }


class BriefingStore:
    def __init__(self, db: Any) -> None:
        self._db = db

    def add(self, *, package_id: str, kind: str, refs: list[str], body: Mapping[str, Any], token_hash: str,
            created_at: str, expires_at: str) -> None:
        with self._db._connection() as conn:
            conn.execute(
                "INSERT INTO briefing_packages (id, kind, refs_json, body_json, token_hash, created_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (package_id, kind, json.dumps(list(refs)), json.dumps(dict(body), ensure_ascii=False), token_hash,
                 created_at, expires_at),
            )

    def by_hash(self, token_hash: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute(f"SELECT {_COLUMNS} FROM briefing_packages WHERE token_hash=?",
                               (token_hash,)).fetchone()
        return _row(row) if row is not None else None

    def get(self, package_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute(f"SELECT {_COLUMNS} FROM briefing_packages WHERE id=?", (package_id,)).fetchone()
        return _row(row) if row is not None else None

    def open_like(self, ref_prefix: str, now: str) -> list[dict[str, Any]]:
        """The packages not revoked and not expired whose refs start with
        ``ref_prefix`` (a Program's ``program:<id>:``), newest first."""
        like = ref_prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self._db._connection() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM briefing_packages WHERE revoked_at IS NULL AND expires_at > ? "
                "AND refs_json LIKE ? ESCAPE '\\' ORDER BY created_at DESC",
                (now, f'%"{like}%'),
            ).fetchall()
        return [_row(row) for row in rows]

    def open_pages(self, ref_prefix: str, now: str) -> dict[str, dict[str, Any]]:
        """``{ref: {package_id, expires_at}}`` for each open, unanswered ref
        under ``ref_prefix`` (the newest package wins)."""
        pages: dict[str, dict[str, Any]] = {}
        for package in self.open_like(ref_prefix, now):
            answers = package["answers"]
            for ref in package["refs"]:
                answer = answers.get(ref) if isinstance(answers, dict) else None
                if ref in pages or not str(ref).startswith(ref_prefix):
                    continue
                if isinstance(answer, dict) and answer.get("choice") != "later":
                    continue
                pages[ref] = {"package_id": package["id"], "expires_at": package["expires_at"]}
                # PG-DIRECTION DIR5: where the package went last ({via, at}).
                sent = [row for row in package["sent"] if isinstance(row, dict) and row.get("via")]
                if sent:
                    pages[ref]["sent"] = {"via": sent[-1]["via"], "at": sent[-1].get("at")}
        return pages

    def answer(self, package_id: str, answers: Mapping[str, Any]) -> None:
        with self._db._connection() as conn:
            conn.execute("UPDATE briefing_packages SET answers_json=? WHERE id=?",
                         (json.dumps(dict(answers), ensure_ascii=False), package_id))

    def revoke(self, package_id: str, at: str) -> None:
        with self._db._connection() as conn:
            conn.execute("UPDATE briefing_packages SET revoked_at=? WHERE id=? AND revoked_at IS NULL",
                         (at, package_id))

    def set_sent(self, package_id: str, sent: list[Mapping[str, Any]]) -> None:
        """DIR5: where the package went (``[{via, at, message_id?, chat?}]``)."""
        with self._db._connection() as conn:
            conn.execute("UPDATE briefing_packages SET sent_json=? WHERE id=?",
                         (json.dumps([dict(row) for row in sent], ensure_ascii=False), package_id))

    def sent_since(self, since: str) -> list[dict[str, Any]]:
        """The packages made after ``since`` that went to a channel, newest first."""
        with self._db._connection() as conn:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM briefing_packages WHERE created_at > ? AND sent_json != '[]' "
                "ORDER BY created_at DESC", (since,),
            ).fetchall()
        return [_row(row) for row in rows]


class HeldLaterStore:
    """``held_later`` (PG-DIRECTION DIR4): one row per deferred held item."""

    def __init__(self, db: Any) -> None:
        self._db = db

    def put(self, *, ref: str, until: str, via: str, at: str, package_id: Optional[str] = None) -> None:
        with self._db._connection() as conn:
            conn.execute(
                "INSERT INTO held_later (ref, until, via, at, package_id) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(ref) DO UPDATE SET until=excluded.until, via=excluded.via, at=excluded.at, "
                "package_id=excluded.package_id",
                (ref, until, via, at, package_id),
            )

    def get(self, ref: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT ref, until, via, at, package_id FROM held_later WHERE ref=?",
                               (ref,)).fetchone()
        return dict(row) if row is not None else None

    def like(self, ref_prefix: str) -> dict[str, dict[str, Any]]:
        """``{ref: row}`` for the rows whose ref starts with ``ref_prefix``."""
        like = ref_prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self._db._connection() as conn:
            rows = conn.execute("SELECT ref, until, via, at, package_id FROM held_later WHERE ref LIKE ? ESCAPE '\\'",
                                (f"{like}%",)).fetchall()
        return {str(row["ref"]): dict(row) for row in rows}

    def due(self, now: str) -> list[dict[str, Any]]:
        """The rows whose next touch has come."""
        with self._db._connection() as conn:
            rows = conn.execute("SELECT ref, until, via, at, package_id FROM held_later WHERE until <= ? "
                                "ORDER BY until", (now,)).fetchall()
        return [dict(row) for row in rows]

    def drop(self, ref: str) -> None:
        with self._db._connection() as conn:
            conn.execute("DELETE FROM held_later WHERE ref=?", (ref,))

    def drop_like(self, ref_prefix: str) -> None:
        like = ref_prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self._db._connection() as conn:
            conn.execute("DELETE FROM held_later WHERE ref LIKE ? ESCAPE '\\'", (f"{like}%",))


__all__ = ["BriefingStore", "HeldLaterStore"]
