"""The held item's own verbs on a phone message (PG-JOURNEYS J6, JRN6).

A message the desk wrote about a Program step (``origin_ref
program_step:<step>:<reach kind>``) carries the verbs of the item that
waits on that step now (``actions``: the briefing package's choices, with
their labels and consequences; never a waive, which needs a typed line). A
press on his paired phone (``POST /api/phone/messages/{id}/decide``, the
device's token) is his press: the item's own verb through
``BriefingService.decide_item`` with ``via="phone"``, the ledger line "…
decided on your phone". A second press, or a press after the item was
answered elsewhere, is refused in the page's and Telegram's words
("Answered at 06:41 from the desk").
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("phone.actions")

PREFIX = "program_step:"


def step_of(row: Mapping[str, Any]) -> str:
    ref = str(row.get("origin_ref") or "")
    if row.get("direction") != "to_phone" or not ref.startswith(PREFIX):
        return ""
    return ref[len(PREFIX):].split(":", 1)[0]


def _briefing(db: Any) -> Any:
    from ..services.briefing_service import BriefingService

    return BriefingService(db)


def held_ref(db: Any, step_id: str, programs: Any = None, *, items: Optional[list[Mapping[str, Any]]] = None) -> Optional[str]:
    """The Needs you ref of the briefable item that waits on the step now
    (``items``: the Programs' your-turn items, read once by the caller)."""
    from ..services.briefing_service import BRIEFABLE, TEXT_KINDS

    if items is None:
        if programs is None:
            from ..services.program_service import default_program_service

            programs = default_program_service(db)
        items = programs.needs_you_items()
    for item in items:
        if item.get("step_id") == step_id and item.get("kind") in BRIEFABLE and item.get("kind") not in TEXT_KINDS:
            return f"program:{item['program_id']}:{item['id']}"
    return None


def actions_for(db: Any, row: Mapping[str, Any], *, briefing: Any = None,
                items: Optional[list[Mapping[str, Any]]] = None) -> Optional[dict[str, Any]]:
    """``{ref, kind, question, choices[{id, label, consequence}]}`` of the item
    a desk message is about, while it waits; else ``None``."""
    step_id = step_of(row)
    if not step_id:
        return None
    try:
        briefing = briefing or _briefing(db)
        ref = held_ref(db, step_id, briefing.programs(), items=items)
        body = briefing.compose(ref) if ref else None
    except Exception as exc:
        log.debug(f"phone actions not read: {exc}")
        return None
    if not body or not body.get("choices"):
        return None
    return {"ref": ref, "kind": body.get("kind"), "question": body.get("question"),
            "choices": [{key: choice.get(key) for key in ("id", "label", "consequence")}
                        for choice in body["choices"]]}


def decide(db: Any, row: Mapping[str, Any], choice: Any, *, briefing: Any = None) -> dict[str, Any]:
    """His press on the phone: the item's own verb, as his press."""
    from ..principals import Principal, PrincipalKind
    from ..services.briefing_service import BriefingRefused, NOT_USABLE, not_pending

    briefing = briefing or _briefing(db)
    step_id = step_of(row)
    if not step_id:
        raise BriefingRefused("not_an_item", "This message asks nothing.", status=409)
    if not str(choice or "").strip():
        raise BriefingRefused("not_usable", NOT_USABLE, status=400, refusal="not_usable", words=NOT_USABLE)
    ref = held_ref(db, step_id, briefing.programs())
    if ref is None:
        raise not_pending(*_answered_where(briefing, step_id))
    answer = briefing.decide_item(Principal(PrincipalKind.OWNER, "phone-press"), ref, str(choice), via="phone")
    return {"decided": True, "ref": ref, "choice": str(choice), "answer": answer}


def _answered_where(briefing: Any, step_id: str) -> tuple[Any, Any]:
    """The step's newest owner line: when and on which channel."""
    try:
        programs = briefing.programs()
        step = programs.store.get_step(step_id)
        rows = programs.store.list_checkpoints(str(step["program_id"])) if step else []
    except Exception:
        rows = []
    line = next((r for r in rows if r.get("by") == "owner" and r.get("step_id") == step_id), None)
    return ((line or {}).get("at"), (line or {}).get("via") or "desk")
