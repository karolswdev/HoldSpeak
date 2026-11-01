"""PG-IMPORT IMP3: when the owner was last at his desk, and what happened since.

BroCrew (``components/SinceYouWereLastHere.vue``) keeps a block of what
finished while the person was away, with two honest lines when the read was
not whole: "Part of the record couldn't be read, so some lines may be
missing." and "Only the newest N were read; older ones may be missing."

The desk reports its front window once a minute while he looks at it
(``POST /api/desk/presence``, :mod:`holdspeak.desk_presence`, memory only).
This module keeps the edge of his visits on disk (the ``desk_presence`` row of
the cadence policies, the store Reach keeps its digest day in): ``last_seen``
is the newest report (written at most once a minute), and a report after a gap
of :data:`AWAY_SECONDS` moves the old ``last_seen`` to ``previous``: the time
he was last here. A hub restart keeps both.

:func:`since_last_here` reads the Programs ledger (merged, parked and Done
moves the engine saw; Decided for you; the night's digest; a message to him
that did not arrive) and the Reach packages sent to him, after ``previous``:
one line per Program, the newest first, at most :data:`MAX_LINES`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from ..logging_config import get_logger
from ..timestamps import utc_now_iso

log = get_logger("last_here")

POLICY = "desk_presence"
#: A gap this long between two reports is a new visit (Phone's "away").
AWAY_SECONDS = 30 * 60
#: ``last_seen`` is written at most this often.
WRITE_SECONDS = 60
#: The ledger rows read at most (the honest "Only the newest 40 were read").
READ_LIMIT = 40
#: The lines Today shows at most.
MAX_LINES = 4

PARTIAL_WORDS = "Part of the record could not be read, so some lines may be missing."


def capped_words(limit: int = READ_LIMIT) -> str:
    return f"Only the newest {limit} were read; older ones may be missing."


def _parse(stamp: Any) -> Optional[datetime]:
    try:
        value = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _config(db: Any) -> dict[str, Any]:
    policy = db.cadence.get_policy(POLICY)
    return dict(getattr(policy, "config", None) or {}) if policy else {}


def touch(db: Any, now: Optional[str] = None) -> dict[str, Any]:
    """A desk report: keep ``last_seen``; after a gap, the old one becomes
    ``previous`` (he was last here then). Returns the stored config."""
    from ..cadence.models import CadencePolicy

    stamp = now or utc_now_iso()
    at = _parse(stamp)
    config = _config(db)
    last = _parse(config.get("last_seen"))
    changed = False
    if last is not None and at is not None and (at - last).total_seconds() > AWAY_SECONDS:
        config["previous"] = config["last_seen"]
        changed = True
    if last is None or at is None or changed or (at - last).total_seconds() >= WRITE_SECONDS:
        config["last_seen"] = stamp
        changed = True
    if changed:
        db.cadence.upsert_policy(CadencePolicy(name=POLICY, config=config))
    return config


def last_here(db: Any) -> Optional[str]:
    """When he was last at the desk before this visit, or ``None``."""
    try:
        return _config(db).get("previous") or None
    except Exception as exc:
        log.debug(f"last here not read: {exc}")
        return None


def _plural(n: int, one: str, many: str) -> str:
    return one.format(n=n) if n == 1 else many.format(n=n)


def since_last_here(db: Any, programs: Any, since: Optional[str], *, limit: int = READ_LIMIT) -> Optional[dict[str, Any]]:
    """``{since, lines: [{program_id, title, line, at}], partial, capped,
    partial_words?, capped_words?}``; ``None`` when there is no ``since`` or
    nothing happened (no zero section)."""
    if not since or _parse(since) is None:
        return None
    partial = False
    capped = False
    rows: list[dict[str, Any]] = []
    try:
        with db._connection() as conn:
            found = conn.execute(
                "SELECT id, step_id, program_id, at, by_kind, line, kind, rule, undo_json FROM program_checkpoints "
                "WHERE at > ? AND by_kind = 'engine' ORDER BY at DESC, id DESC LIMIT ?", (since, limit + 1)).fetchall()
        capped = len(found) > limit
        import json

        for row in found[:limit]:
            try:
                undo = json.loads(row["undo_json"] or "{}") or {}
            except ValueError:
                undo, partial = {}, True
            rows.append({**dict(row), "undo": undo})
    except Exception as exc:
        log.info(f"since last here: the ledger was not read: {exc}")
        partial = True
    sent: dict[str, int] = {}
    try:
        from ..db.briefing import BriefingStore

        for package in BriefingStore(db).sent_since(since):
            for ref in package.get("refs") or []:
                parts = str(ref).split(":")
                if len(parts) >= 2 and parts[0] == "program":
                    sent[parts[1]] = sent.get(parts[1], 0) + 1
    except Exception as exc:
        log.info(f"since last here: Reach was not read: {exc}")
        partial = True
    by_program: dict[str, dict[str, Any]] = {}
    seen_steps: dict[str, set[str]] = {}
    for row in rows:
        pid = str(row["program_id"])
        entry = by_program.setdefault(pid, {"merged": 0, "parked": 0, "decided": 0, "lost": 0, "night": "",
                                            "at": row["at"]})
        undo = row["undo"]
        state = (undo.get("seen") or {}).get("state") if isinstance(undo.get("seen"), dict) else None
        step = str(row["step_id"] or "")
        key = f"{state}:{step}"
        if row["kind"] == "night_digest" and not entry["night"]:
            entry["night"] = str((undo.get("lines") or [row["line"]])[0])
        elif row["kind"] == "notice_lost":
            entry["lost"] += 1
        elif row["rule"]:
            entry["decided"] += 1
        elif step and state in ("merged", "parked") and key not in seen_steps.setdefault(pid, set()):
            seen_steps[pid].add(key)
            entry["merged" if state == "merged" else "parked"] += 1
    for pid, count in sent.items():
        by_program.setdefault(pid, {"merged": 0, "parked": 0, "decided": 0, "lost": 0, "night": "", "at": since})
        by_program[pid]["sent"] = count
    lines: list[dict[str, Any]] = []
    for pid, entry in sorted(by_program.items(), key=lambda item: str(item[1]["at"]), reverse=True):
        try:
            program = programs.store.get_program(pid)
        except Exception:
            program, partial = None, True
        if program is None:
            continue
        if entry["night"]:
            words = entry["night"]
        else:
            parts = [
                _plural(entry["merged"], "{n} step merged", "{n} steps merged") if entry["merged"] else "",
                f"{entry['parked']} parked" if entry["parked"] else "",
                f"{entry['decided']} decided for you" if entry["decided"] else "",
                _plural(entry.get("sent", 0), "{n} message to you", "{n} messages to you") if entry.get("sent") else "",
                _plural(entry["lost"], "{n} message did not arrive", "{n} messages did not arrive") if entry["lost"] else "",
            ]
            words = ", ".join(part for part in parts if part)
        if not words:
            continue
        lines.append({"program_id": pid, "title": str(program.get("title") or "Program"),
                      "line": words[:1].upper() + words[1:], "at": entry["at"]})
        if len(lines) >= MAX_LINES:
            break
    if not lines and not partial:
        return None
    out: dict[str, Any] = {"since": since, "lines": lines, "partial": partial, "capped": capped}
    if partial:
        out["partial_words"] = PARTIAL_WORDS
    if capped:
        out["capped_words"] = capped_words(limit)
    return out


__all__ = ["AWAY_SECONDS", "MAX_LINES", "PARTIAL_WORDS", "READ_LIMIT", "capped_words", "last_here",
           "since_last_here", "touch"]
