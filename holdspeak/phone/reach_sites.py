"""PH12: the other reach kinds of design §6, at the places that write their Needs you rows.

- **heartbeat_security**: after a heartbeat sweep built Needs you, each row
  about security or data loss (a row tagged so, or a Program finding whose
  words the Programs rules call security or data loss).
- **aftercare**: after a recorded meeting's aftercare is ready, its asks (the
  open items and the proposals to review).
- **agent_question**: a HoldSpeak-launched agent's question the desk could not
  draft (the responder's REAL path, and every question at Secure).

Each one goes through :meth:`PhoneService.reach` (the rules decide message,
call or nothing by level and quiet hours; a ``phone.reach`` kernel operation
each), once per thing (``origin_ref``). A reach never breaks its caller.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("phone.reach_sites")

SECURITY = "security"
DATA_LOSS = "data loss"


def _phone(db: Any) -> Any:
    from . import service as phone_service

    try:
        # The hub's one Phone service (its sweeper runs); a second handle
        # on the same database must not replace it.
        return phone_service.default_phone_service()
    except Exception:
        return phone_service.default_phone_service(db)


def reach_once(
    kind: str, text: str, *, origin_ref: str, db: Any = None, level: Any = None, reason: Optional[str] = None,
    context: Optional[str] = None, facts: Optional[Mapping[str, Any]] = None,
    still_open: Optional[tuple[str, Callable[[str], bool]]] = None,
) -> Optional[dict[str, Any]]:
    """One reach of ``kind`` about ``origin_ref``, unless one was made in the
    last day (the phone's own sweep asks again later). ``level`` None: the
    desk's Control level. None when the phone is off, nothing is paired and no
    number is set, it was reached already, or it failed."""
    try:
        from . import phone_on

        if not phone_on():
            return None
        from . import service as phone_service

        phone = _phone(db)
        if still_open is not None:
            phone.open_check(*still_open)
        if not phone.paired() and not phone.number.number():
            # Nothing reaches him: no paired phone and no number. A message
            # here would only be a second Needs you row about the first one.
            return None
        if phone._reaches(origin_ref):
            return None
        return phone.reach(kind, level=phone_service._desk_level() if level is None else level, text=text,
                           reason=reason, context=context, origin_ref=origin_ref, facts=facts)
    except Exception as exc:
        log.warning(f"the desk did not reach the phone ({kind}): {exc}")
        return None


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" + ("" if count == 1 else "s")


# ── heartbeat_security ───────────────────────────────────────────────


def safety_of(item: Mapping[str, Any]) -> str:
    """``security``, ``data loss`` or ``""`` for one Needs you row: its tags,
    or a Program finding's words read by the Programs rules (``is_core``)."""
    from ..services.program_rules import is_core

    tags = [str(tag) for tag in item.get("tags") or []]
    program = item.get("program") if isinstance(item.get("program"), Mapping) else {}
    text = str(item.get("title") or "") if program.get("kind") == "finding" else ""
    if not tags and not text:
        return ""
    reason = is_core({"finding_tags": tags, "finding_text": text})
    if reason == "a finding is about security":
        return SECURITY
    if reason == "a finding is about data loss":
        return DATA_LOSS
    return ""


def reach_safety_findings(db: Any, items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The heartbeat's pass: each row about security or data loss reaches him once."""
    done: list[dict[str, Any]] = []
    for item in items:
        what = safety_of(item)
        ident = str(item.get("id") or item.get("ref") or "")
        if not what or not ident:
            continue
        title = str(item.get("title") or "").strip()
        reason = f"A {what} finding needs you: {title}"
        result = reach_once(
            "heartbeat_security", f"{reason}. Open Needs you on your desk to decide.",
            origin_ref=f"heartbeat:{ident}", db=db, reason=reason,
            context=f"Tell him: {reason}. Ask him to look at it on the desk. Do not decide for him.",
        )
        if result is not None:
            done.append(result)
    return done


# ── aftercare ────────────────────────────────────────────────────────


def reach_aftercare(db: Any, event: Optional[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """A recorded meeting's asks (``build_aftercare_ready_event``): the open
    items and the proposals to review. Decisions alone ask nothing."""
    if not event or not event.get("meeting_id"):
        return None
    open_total = int(event.get("open_total") or 0)
    proposals = int(event.get("proposal_total") or 0)
    if open_total + proposals <= 0:
        return None
    asks = " and ".join(part for part in (
        _plural(open_total, "open item") if open_total else "",
        _plural(proposals, "proposal") + " to review" if proposals else "",
    ) if part)
    title = str(event.get("title") or "The meeting").strip() or "The meeting"
    verb = "waits" if open_total + proposals == 1 else "wait"
    text = f"{title}: {asks} {verb} for you on the desk."
    return reach_once("aftercare", text, origin_ref=f"meeting:{event['meeting_id']}:aftercare", db=db,
                      reason=f"{title} left {asks}")


# ── agent_question ───────────────────────────────────────────────────


def agent_origin(key: str, wait_id: str) -> str:
    return f"agent:{key}:{wait_id}"


def reach_agent_question(
    db: Any, *, key: str, wait_id: str, agent: str, question: str, level: Any,
    still_open: Optional[Callable[[str], bool]] = None,
) -> Optional[dict[str, Any]]:
    """An agent's question the desk could not draft. "Away" (no desk for 30
    minutes) is one of the facts :meth:`PhoneService.reach` reads;
    ``still_open`` tells the phone's sweep the wait still waits on him."""
    words = " ".join(str(question or "").split())
    if not words:
        return None
    who = (agent or "An agent").strip().capitalize()
    cut = words if len(words) <= 300 else words[:299].rstrip() + "…"
    text = f"{who} asks: {cut}"
    return reach_once("agent_question", text, origin_ref=agent_origin(key, wait_id), db=db, level=level,
                      reason=f"{who} has a question for you", context=f"{text}\nDo not answer for him.",
                      still_open=("agent:", still_open) if still_open is not None else None)


__all__ = ["DATA_LOSS", "SECURITY", "agent_origin", "reach_aftercare", "reach_agent_question", "reach_once",
           "reach_safety_findings", "safety_of"]
