"""Held items outside Programs as briefing packages (PG-DIRECTION DIR10, 2026-11-01).

DIRECTION-2026-10-31.md §3 "The held item" (the desk's holds outside
Programs) and §10 "Then every other held item". Each source names its items
by the Needs you ref, reads whether the item still waits, composes the
package body in his words (the same keys a Program item's body has: head,
note, question, choices with their consequences), and answers a choice
through the item's OWN verb — the one the desk's Needs you row presses — so
the record is the same whatever the channel:

- ``decision:<id>``: a Desk decision to review (``proposed``): **Confirm**
  (``PrimitiveService.update_decision_status`` → ``accepted``, the Needs you
  row's verb) or **Later**.
- ``phone-call:<id>``: a call an agent asks to place (``held``): **Call now**
  (``PhoneService.ring_held``) or **Let it wait** (``PhoneService.decline``).

Not here: a meeting's proposals and a project's review proposals (their
approve runs an effect; the page must show its preview first), an agent's
question (his answer is text), a prepared send and a gate hold (the page
only, by the owner's authority rule): their sources come next.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("services.briefing_sources")


class Source:
    """One kind of held item outside Programs."""

    prefix = ""
    kind = ""
    kind_words = ""

    def __init__(self, db: Any) -> None:
        self.db = db

    def ident(self, ref: str) -> str:
        return str(ref)[len(self.prefix):]

    def held(self, ref: str) -> Optional[dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError

    def body(self, ref: str, item: Mapping[str, Any]) -> dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError

    def decide(self, ref: str, item: Mapping[str, Any], choice: str, *, via: str) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def _base(self, ref: str, *, head: str, question: str, note: list[str], since: str,
              choices: list[tuple[str, str, str]]) -> dict[str, Any]:
        """The package body (the keys the page and Telegram read)."""
        return {
            "ref": ref, "kind": self.kind, "kind_words": self.kind_words, "source": self.prefix.rstrip(":"),
            "program_id": None, "program_title": "", "step_id": "", "step_ordinal": None, "step_title": "",
            "head": head, "goal": note[0] if note else "", "doing": note[1] if len(note) > 1 else "",
            "happened": note[2] if len(note) > 2 else "", "note": note, "question": question,
            "place": "", "track": [], "blocked": [], "blocked_words": "", "level": "", "since": since or "",
            "changed": [], "evidence": [], "error": "",
            "choices": [{"id": choice, "label": label, "consequence": said, "primary": index == 0}
                        for index, (choice, label, said) in enumerate(choices)],
        }


def _sentence(text: Any, limit: int = 240) -> str:
    words = " ".join(str(text or "").split())[:limit].rstrip()
    return words if not words or words[-1] in ".?!" else words + "."


class DecisionSource(Source):
    """A Desk decision that waits for his review (``proposed``)."""

    prefix, kind, kind_words = "decision:", "decision", "Decision to review"

    def _service(self) -> Any:
        from ..runtime import composition
        from .primitive_service import PrimitiveService

        return composition.service("primitive_service", lambda: PrimitiveService(self.db))

    def held(self, ref: str) -> Optional[dict[str, Any]]:
        try:
            row = self.db.desk_decisions.get(self.ident(ref))
        except Exception as exc:
            log.debug(f"decision {ref} not read: {exc}")
            return None
        if row is None:
            return None
        record = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        return record if str(record.get("status") or "") == "proposed" else None

    def body(self, ref: str, item: Mapping[str, Any]) -> dict[str, Any]:
        title = " ".join(str(item.get("title") or item.get("decision_markdown") or "A decision").split())
        why = _sentence(item.get("decision_markdown") or item.get("context_markdown") or "")
        note = [_sentence(f"The decision: {title}")]
        if why:
            note.append(why)
        return self._base(ref, head="A decision to review", question="Confirm this decision?", note=note,
                          since=str(item.get("created_at") or ""),
                          choices=[("confirm", "Confirm", "The decision is accepted. It leaves your review list.")])

    def decide(self, ref: str, item: Mapping[str, Any], choice: str, *, via: str) -> dict[str, Any]:
        from ..principals import Principal, PrincipalKind

        if choice != "confirm":
            raise ValueError(choice)
        principal = Principal(PrincipalKind.OWNER, f"briefing-{via}")
        return self._service().update_decision_status(principal, self.ident(ref), "accepted")


class PhoneCallSource(Source):
    """A call an agent asks to place, held for his press."""

    prefix, kind, kind_words = "phone-call:", "held_call", "Call request"

    def _service(self) -> Any:
        from ..phone.service import default_phone_service

        return default_phone_service(self.db)

    def held(self, ref: str) -> Optional[dict[str, Any]]:
        try:
            row = self._service().store.get_call(self.ident(ref))
        except Exception as exc:
            log.debug(f"call {ref} not read: {exc}")
            return None
        return dict(row) if row and str(row.get("state") or "") == "held" else None

    def body(self, ref: str, item: Mapping[str, Any]) -> dict[str, Any]:
        reason = " ".join(str(item.get("reason") or "something that waits on you").split()).rstrip(".?")
        about = reason[0].lower() + reason[1:] if len(reason) > 1 and reason[0].isupper() and reason[1].islower() else reason
        return self._base(ref, head="An agent asks to call you", question=f"Call you about {about}?",
                          note=[_sentence(f"An agent asks to call you about {about}")],
                          since=str(item.get("created_at") or ""),
                          choices=[("call_now", "Call now", "Your phone rings now."),
                                   ("let_wait", "Let it wait", "No call. It stays on your desk.")])

    def decide(self, ref: str, item: Mapping[str, Any], choice: str, *, via: str) -> dict[str, Any]:
        from ..principals import Principal, PrincipalKind

        if choice == "call_now":
            return self._service().ring_held(Principal(PrincipalKind.OWNER, f"briefing-{via}"), self.ident(ref))
        if choice == "let_wait":
            return self._service().decline(self.ident(ref))
        raise ValueError(choice)


SOURCES = (DecisionSource, PhoneCallSource)


def source_for(db: Any, ref: Any) -> Optional[Source]:
    """The source of a ref that is not a Program's, else ``None``."""
    text = str(ref or "")
    for kind in SOURCES:
        if text.startswith(kind.prefix):
            return kind(db)
    return None


__all__ = ["DecisionSource", "PhoneCallSource", "SOURCES", "Source", "source_for"]
