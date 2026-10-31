"""Shaping a Program by voice on a call (PG-LANG LANG5, 2026-10-31).

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §4.2, §10.
On a call (and on the Line) "change the overnight program: add a check that
the window fits at 393 to every step" is ``program.shape`` held for his
spoken yes (``CALL_HELD_PROGRAM``):

1. The held call asks nothing yet: :func:`prepare` shapes the sentence (a
   preview; one engine call, nothing written) and builds the read back, one
   sentence for each row ("In the program The hub stops stalling: A new
   requirement on every step: The People window fits at 393. Apply?").
2. His yes applies the allowed rows through ``text_apply`` (one checkpoint,
   one frame). A row that lowers the bar or is a core question never applies
   from a call: it is read as "waits for you on the desk" and lands in that
   Program's change well, where his own press applies it.
3. "Later" applies nothing and puts every row in the well on the desk.
   "No" applies nothing and keeps nothing.
4. A sentence the engine asks back about, or one with no row that can apply,
   asks no yes: the tool answers what the engine said (``spoken``) and the
   call says it.

The rows that wait on the desk live in this hub process (``_DESK``), one
set per Program, until Apply or Not this in the Program window. A hub
restart drops them; the call's Note keeps what he said.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Mapping, Optional

#: A read back he did not answer is dropped after this long.
KEEP_SECONDS = 600.0
#: At most this many rows are read aloud; the rest are counted.
READ_ROWS = 4

_LOCK = threading.Lock()
#: (program id, sentence) → the read back of a held call (state asked | yes | later | spoken).
_HELD: dict[tuple[str, str], dict[str, Any]] = {}
#: program id → the rows that wait in the change well on the desk.
_DESK: dict[str, dict[str, Any]] = {}

_COUNT = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five"}


def _key(program_id: Any, sentence: Any) -> tuple[str, str]:
    return str(program_id or ""), " ".join(str(sentence or "").split()).casefold()


def _count(n: int) -> str:
    return _COUNT.get(n, str(n))


def _says(rows: list[Mapping[str, Any]]) -> list[str]:
    return [str(row.get("say") or "").strip().rstrip(".") for row in rows if str(row.get("say") or "").strip()]


def _sentence(args: Mapping[str, Any]) -> str:
    return " ".join(str(args.get("sentence") or "").split())


def _forget_old() -> None:
    now = time.time()
    for key in [key for key, row in _HELD.items() if now - float(row.get("at") or 0) > KEEP_SECONDS]:
        _HELD.pop(key, None)


def read_back(title: str, rows: list[Mapping[str, Any]]) -> tuple[str, str]:
    """``(question, spoken)``: the yes question when a row can apply, else
    the one line the call says instead."""
    allowed = [row for row in rows if row.get("verdict") == "allowed"]
    lowers = [row for row in rows if row.get("verdict") == "lowers"]
    refused = [row for row in rows if row.get("verdict") in ("refused", "conflict")]
    parts: list[str] = []
    if allowed:
        said = _says(allowed)
        shown = said[:READ_ROWS]
        more = len(said) - len(shown)
        parts.append(f"In the program {title}: " + ". ".join(shown) + "."
                     + (f" And {_count(more).lower()} more {'change' if more == 1 else 'changes'}." if more > 0 else ""))
    if lowers:
        said = _says(lowers)
        if len(lowers) == 1:
            parts.append("One change lowers the bar and waits for you on the desk"
                         + (f": {said[0]}." if said else "."))
        else:
            parts.append(f"{_count(len(lowers))} changes lower the bar and wait for you on the desk.")
    if refused:
        reason = str(refused[0].get("reason") or "").strip()
        parts.append(f"{_count(len(refused))} {'change' if len(refused) == 1 else 'changes'} cannot be made"
                     + (f": {reason}" if reason else ".") + ("" if not reason or reason.endswith(".") else "."))
    if allowed:
        return " ".join(parts) + " Apply?", ""
    if not rows:
        return "", f"Nothing in the program {title} changes."
    return "", " ".join(parts) + " Nothing changed on the call."


def prepare(service: Any, principal: Any, args: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """Shape the sentence of a held ``program.shape`` (a preview) and keep
    the read back. None when no Program has that name (the tool then says
    so)."""
    from .errors import ServiceError

    sentence = _sentence(args)
    try:
        found = service.find(principal, program_id=args.get("program_id"), name=args.get("name"))
    except ServiceError:
        return None
    try:
        answer = service.shape(principal, found["id"], sentence)
    except ServiceError as exc:
        words = str(getattr(exc, "detail", "") or getattr(exc, "message", "") or exc)
        held = {"program_id": found["id"], "title": found["title"], "sentence": sentence, "answer": None,
                "question": "", "spoken": words, "state": "spoken", "at": time.time()}
    else:
        if answer.get("question") and not answer.get("changes"):
            question, spoken = "", f"The engine asks: {answer['question']}"
        else:
            question, spoken = read_back(str(found["title"]), list(answer.get("changes") or []))
        held = {"program_id": found["id"], "title": found["title"], "sentence": sentence, "answer": answer,
                "question": question, "spoken": spoken, "state": "asked" if question else "spoken",
                "at": time.time()}
    with _LOCK:
        _forget_old()
        _HELD[_key(found["id"], sentence)] = held
    return held


def answered(program_id: Any, sentence: Any, decision: str) -> None:
    """His answer to the read back: ``approve`` (yes), ``later`` or ``deny``."""
    with _LOCK:
        held = _HELD.get(_key(program_id, sentence))
        if held is None:
            return
        if decision == "deny":
            _HELD.pop(_key(program_id, sentence), None)
        elif decision in ("approve", "later") and held["state"] == "asked":
            held["state"] = "yes" if decision == "approve" else "later"


def take(program_id: Any, sentence: Any) -> Optional[dict[str, Any]]:
    """The read back he answered (yes, later, or nothing to ask), once."""
    with _LOCK:
        key = _key(program_id, sentence)
        held = _HELD.get(key)
        if held is None or held["state"] == "asked":
            return None
        return _HELD.pop(key)


def run(service: Any, principal: Any, held: Mapping[str, Any]) -> dict[str, Any]:
    """The tool's answer after his yes, his "later", or a read back with
    nothing to ask."""
    from .program_shaper import apply_allowed

    title, pid = str(held["title"]), str(held["program_id"])
    answer = held.get("answer") or None
    if held["state"] == "spoken" or answer is None:
        waiting = [row for row in (answer or {}).get("changes") or [] if row.get("verdict") == "lowers"]
        if waiting and answer is not None:
            put_on_desk(service, pid, answer, held["sentence"])
        return {"program_id": pid, "applied": False, "spoken": held["spoken"]}
    if held["state"] == "later":
        put_on_desk(service, pid, answer, held["sentence"])
        n = len(answer.get("changes") or [])
        return {"program_id": pid, "applied": False, "on_desk": n,
                "spoken": f"Nothing changed yet. The {'change waits' if n == 1 else f'{_count(n).lower()} changes wait'} "
                          f"for you in the program {title} on the desk."}
    landed = apply_allowed(service, principal, pid, str(answer["base"]), str(answer["proposed_text"]))
    if not landed["applied"]:
        return {"program_id": pid, "applied": False,
                "spoken": f"The program {title} changed since I read it. Nothing changed. Say it again."}
    out: dict[str, Any] = {"program_id": pid, "applied": True, "changes": len(landed["applied_rows"])}
    words = f"Done: the program {title} has {_count(len(landed['applied_rows'])).lower()} " \
            f"{'change' if len(landed['applied_rows']) == 1 else 'changes'}."
    if landed.get("waiting"):
        put_on_desk(service, pid, {**answer, **landed["waiting"]}, held["sentence"])
        n = len(landed["waiting"]["changes"])
        out["on_desk"] = n
        words += f" {_count(n)} {'waits' if n == 1 else 'wait'} for you on the desk."
    out["spoken"] = words
    return out


# ── the rows that wait on the desk ───────────────────────────────────

def put_on_desk(service: Any, program_id: str, answer: Mapping[str, Any], sentence: str) -> None:
    """The rows land in the Program's change well (the window re-reads on
    the frame)."""
    keep = {key: answer.get(key) for key in (
        "changes", "patch", "allowed_text", "text", "revision", "version", "refused", "lowers", "say", "engine",
        "seconds", "base", "proposed_text", "question")}
    keep.update(program_id=program_id, sentence=sentence, applied=False, applied_rows=[], decision=None,
                source="call", at=time.time())
    with _LOCK:
        _DESK[str(program_id)] = keep
    try:
        service._broadcast("program_changed", {"program_id": program_id, "held_shape": True})
    except Exception:
        pass


def on_desk(program_id: Any) -> Optional[dict[str, Any]]:
    with _LOCK:
        found = _DESK.get(str(program_id or ""))
        return dict(found) if found else None


def drop(program_id: Any) -> bool:
    """Not this, or Apply: the call's rows leave the well."""
    with _LOCK:
        return _DESK.pop(str(program_id or ""), None) is not None


def reset() -> None:
    """A test's fresh hub."""
    with _LOCK:
        _HELD.clear()
        _DESK.clear()


__all__ = ["answered", "drop", "on_desk", "prepare", "put_on_desk", "read_back", "reset", "run", "take"]
