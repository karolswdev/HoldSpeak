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

- ``meeting-proposal:<id>``: a meeting's proposed action (aftercare). The
  body carries ``preview`` (its destination and the lines it would send or
  write), shown before the choice. **Do it** (``MeetingAftercareService
  .decide_proposal`` approved) or **Not this** (rejected).
- ``project-proposal:<id>``: a project review's proposal. Its ``preview``
  says what Accept adds. **Accept** or **Dismiss**
  (``ProjectDeltaService.decide_proposal``, the review's own verbs).

A Program step's agent question is the Program's item (``program:…:answer``,
answered with text on the page).

- ``send:<id>``: a prepared send (``channel_sends`` ``prepared``). The page
  only (``page_only``): its preview names the destination and the lines it
  sends (UX-CANON A.9); **Send** runs ``channel.send`` and **Discard**
  ``channel.discard`` through the kernel's operation path; never a Telegram tap.
- ``coder:<agent>:<session>``: a desk agent's question outside a Program
  (a HoldSpeak-launched agent's lane), answered with his text. The answer is
  typed into the agent's own pane through the steering path
  (``AgentResponder._deliver``, the path the desk's own answers take).
  A permission prompt is authority and stays on the desk (IMP5).

Not here: a gate hold (IMP5, #1711: a permission never travels, which
supersedes DIRECTION §3's "the page only").
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
    #: DIRECTION §3: decided on the page only, never by a Telegram tap.
    page_only = False

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

    def answer_text(self, ref: str, item: Mapping[str, Any], text: str, *, via: str,
                    expected_wait_id: Optional[str] = None) -> dict[str, Any]:
        """His text answer (a question source only)."""
        raise ValueError("answer")

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


def _preview_lines(text: Any, limit: int = 8) -> list[str]:
    lines = [" ".join(line.split())[:200] for line in str(text or "").splitlines() if line.strip()]
    return lines[:limit]


class MeetingProposalSource(Source):
    """A meeting's proposed action (aftercare), with its preview."""

    prefix, kind, kind_words = "meeting-proposal:", "meeting_proposal", "Meeting proposal"

    def _service(self) -> Any:
        from ..runtime import composition
        from .meeting_aftercare_service import MeetingAftercareService

        return composition.service("meeting_aftercare_service", lambda: MeetingAftercareService(self.db))

    def held(self, ref: str) -> Optional[dict[str, Any]]:
        try:
            row = self.db.actuators.get_proposal(self.ident(ref))
        except Exception as exc:
            log.debug(f"meeting proposal {ref} not read: {exc}")
            return None
        if row is None or getattr(row, "origin", "") != "meeting" or getattr(row, "status", "") != "proposed":
            return None
        return {"id": row.id, "meeting_id": row.meeting_id, "target": row.target, "action": row.action,
                "preview": row.preview, "reversible": bool(row.reversible),
                "created_at": str(getattr(row, "created_at", "") or "")}

    def body(self, ref: str, item: Mapping[str, Any]) -> dict[str, Any]:
        destination = str(item.get("target") or "its destination")
        action = " ".join(str(item.get("action") or "the action").replace("_", " ").split())
        title = ""
        try:
            meeting = self.db.meetings.get_meeting(str(item.get("meeting_id") or ""))
            title = str(getattr(meeting, "title", "") or "")
        except Exception:
            title = ""
        body = self._base(ref, head=f"{title} · after the meeting" if title else "After a meeting",
                          question=f"Do it: {action} to {destination}?",
                          note=[_sentence(f"The meeting asks for one action: {action} to {destination}")],
                          since=str(item.get("created_at") or ""),
                          choices=[("approve", "Do it", f"HoldSpeak does it now: {action} to {destination}."),
                                   ("reject", "Not this", "Nothing is done or sent.")])
        # DIR10: what the action sends or writes, shown before the choice.
        body["preview"] = {"destination": destination, "lines": _preview_lines(item.get("preview")),
                           "reversible": bool(item.get("reversible"))}
        return body

    def decide(self, ref: str, item: Mapping[str, Any], choice: str, *, via: str) -> dict[str, Any]:
        from ..principals import Principal, PrincipalKind

        decision = {"approve": "approved", "reject": "rejected"}.get(choice)
        if decision is None:
            raise ValueError(choice)
        return self._service().decide_proposal(Principal(PrincipalKind.OWNER, f"briefing-{via}"),
                                               str(item.get("meeting_id") or ""), self.ident(ref),
                                               {"decision": decision, "decided_by": f"briefing-{via}"})


class ProjectProposalSource(Source):
    """A project review's open proposal, with what Accept adds."""

    prefix, kind, kind_words = "project-proposal:", "project_proposal", "Project review"

    def _service(self) -> Any:
        from ..runtime import composition

        def build() -> Any:
            from .project_delta_service import ProjectDeltaService
            from .project_evidence_collector import ProjectEvidenceCollector
            from .project_service import ProjectService

            delta = ProjectDeltaService(self.db, collector=ProjectEvidenceCollector(self.db))
            delta.attach_project_service(ProjectService(self.db, delta_service=delta))
            return delta

        return composition.service("project_delta_service", build)

    def held(self, ref: str) -> Optional[dict[str, Any]]:
        try:
            row = self.db.project_observations.get_proposal(self.ident(ref))
        except Exception as exc:
            log.debug(f"project proposal {ref} not read: {exc}")
            return None
        return dict(row) if row and str(row.get("lifecycle") or "") == "open" else None

    def body(self, ref: str, item: Mapping[str, Any]) -> dict[str, Any]:
        import json as _json

        project = ""
        try:
            found = self.db.projects.get_project(str(item.get("project_id") or ""))
            project = str(getattr(found, "name", "") or (found or {}).get("name", "") if found else "")
        except Exception:
            project = ""
        title = " ".join(str(item.get("title") or "A proposal").split())
        kind = str(item.get("proposal_kind") or "")
        adds = {"risk_attention": "a risk item", "action_attention": "an action item"}.get(kind, "")
        try:
            patch = _json.loads(item.get("patch_json") or "{}")
        except ValueError:
            patch = {}
        lines = [f"Accept adds {adds}: {title}" if adds else f"Accept records: {title}"]
        lines += [f"{key.replace('_', ' ').capitalize()}: {value}"[:200] for key, value in
                  (patch.items() if isinstance(patch, Mapping) else []) if isinstance(value, (str, int, float))][:5]
        body = self._base(ref, head=f"{project} · the project review" if project else "The project review",
                          question=f"Accept: {title}?",
                          note=[_sentence(title), _sentence(item.get("rationale") or "")],
                          since=str(item.get("created_at") or ""),
                          choices=[("accept", "Accept", lines[0] + "."), ("dismiss", "Dismiss", "Nothing is added.")])
        body["note"] = [line for line in body["note"] if line]
        body["preview"] = {"destination": f"the project {project}" if project else "the project", "lines": lines,
                           "reversible": True}
        return body

    def decide(self, ref: str, item: Mapping[str, Any], choice: str, *, via: str) -> dict[str, Any]:
        from ..principals import Principal, PrincipalKind

        if choice not in ("accept", "dismiss"):
            raise ValueError(choice)
        return self._service().decide_proposal(
            Principal(PrincipalKind.OWNER, f"briefing-{via}"), str(item.get("project_id") or ""), self.ident(ref),
            choice, review_id=str(item.get("review_window_key") or "") or None)


class SendSource(Source):
    """A prepared send that waits for his Send (the page only)."""

    prefix, kind, kind_words = "send:", "send", "Ready to send"
    page_only = True

    def _registry(self) -> Any:
        from .. import operations
        from ..runtime.composition import notify_desk_changed
        from .channel_service import ChannelService

        return operations.for_runtime(channel_service=lambda: ChannelService(self.db, on_changed=notify_desk_changed))

    def held(self, ref: str) -> Optional[dict[str, Any]]:
        try:
            row = self.db.channel_sends.get(self.ident(ref))
        except Exception as exc:
            log.debug(f"send {ref} not read: {exc}")
            return None
        return dict(row) if row and str(row.get("state") or "") == "prepared" else None

    def body(self, ref: str, item: Mapping[str, Any]) -> dict[str, Any]:
        import json as _json

        document = item.get("document_json")
        if isinstance(document, str):
            try:
                document = _json.loads(document or "{}")
            except ValueError:
                document = {}
        document = document if isinstance(document, Mapping) else {}
        title = " ".join(str(document.get("title") or item.get("document_ref") or "A document").split())
        name = item.get("destination_name")
        if not name:
            try:
                name = (self.db.channel_destinations.get(str(item.get("destination_id") or "")) or {}).get("name")
            except Exception:
                name = None
        destination = " ".join(str(name or "its destination").split())
        body = self._base(ref, head=f"{title} · to {destination}", question=f"Send it to {destination}?",
                          note=[_sentence(f"{title} is ready to send to {destination}")],
                          since=str(item.get("created_at") or ""),
                          choices=[("send", "Send", f"HoldSpeak sends it to {destination} now."),
                                   ("discard", "Discard", "Nothing is sent. The prepared send is dropped.")])
        # UX-CANON A.9: egress is disclosed at the act, on the page that sends it.
        payload = item.get("payload")
        if isinstance(payload, (bytes, bytearray, memoryview)):
            payload = bytes(payload).decode("utf-8", "replace")
        # The frozen bytes the Send dispatches: what it sends, word for word.
        body["preview"] = {"destination": destination, "lines": _preview_lines(payload or ""), "reversible": False}
        body["page_only"] = True
        return body

    def decide(self, ref: str, item: Mapping[str, Any], choice: str, *, via: str) -> dict[str, Any]:
        from ..principals import Principal, PrincipalKind

        if via == "telegram":
            raise ValueError(choice)  # the page only (DIRECTION §3)
        name = {"send": "channel.send", "discard": "channel.discard"}.get(choice)
        if name is None:
            raise ValueError(choice)
        result, _kernel = self._registry().invoke_receipted(Principal(PrincipalKind.OWNER, f"briefing-{via}"), name,
                                                            {"send_id": self.ident(ref)})
        return dict(result or {})


class CoderQuestionSource(Source):
    """A desk agent's question outside a Program, answered with his text."""

    prefix, kind, kind_words = "coder:", "answer", "An agent asks"

    def _responder(self) -> Any:
        from .agent_responder import default_agent_responder

        return default_agent_responder(self.db)

    def held(self, ref: str) -> Optional[dict[str, Any]]:
        from ..agent_context.models import is_blocked, wait_kind

        key = self.ident(ref)
        try:
            responder = self._responder()
            session = next((row for row in responder._sessions() if responder._key(row) == key), None)
            launch = responder._launch_for(key)
        except Exception as exc:
            log.debug(f"agent question {ref} not read: {exc}")
            return None
        if session is None or launch is None or not is_blocked(session):
            return None
        if wait_kind(session) == "approve":
            return None  # a permission prompt stays on the desk (IMP5)
        question = str(getattr(session, "question", "") or "").strip()
        if not question:
            return None
        from ..coder_steering import wait_episode

        return {"key": key, "agent": str(getattr(session, "agent", "") or ""), "question": question,
                # Astra post-merge 2026-11-01: the wait he answers; a changed
                # wait (a permission prompt now) refuses the answer.
                "wait_id": wait_episode(session),
                "launch": dict(launch), "since": str(getattr(session, "wait_started_at", "")
                                                     or getattr(session, "updated_at", "") or "")}

    def body(self, ref: str, item: Mapping[str, Any]) -> dict[str, Any]:
        launch = item.get("launch") or {}
        who = {"claude": "Claude Code", "codex": "Codex", "pi": "pi"}.get(str(item.get("agent") or ""),
                                                                            "An agent")
        title = " ".join(str(launch.get("title") or launch.get("story_title") or "").split())
        body = self._base(ref, head=f"{who} · {title}" if title else who,
                          question=_sentence(item.get("question"), 400),
                          note=[_sentence(f"{who} asks you a question")], since=str(item.get("since") or ""),
                          choices=[])
        from .briefing_service import ANSWER_MAX_CHARS

        body["text"] = {"id": "answer", "label": "Your answer", "max": ANSWER_MAX_CHARS,
                        "consequence": f"HoldSpeak types your answer to {who}."}
        body["wait_id"] = str(item.get("wait_id") or "")
        return body

    def decide(self, ref: str, item: Mapping[str, Any], choice: str, *, via: str) -> dict[str, Any]:
        raise ValueError(choice)  # answered with text only

    def answer_text(self, ref: str, item: Mapping[str, Any], text: str, *, via: str,
                    expected_wait_id: Optional[str] = None) -> dict[str, Any]:
        """His text to the agent, bound to the wait he answered: when the
        agent's wait changed (it now asks a permission, or another question),
        nothing is typed and he gets the late-answer words."""
        from .briefing_service import WAIT_CHANGED
        from .errors import ServiceError

        said = " ".join(str(text or "").split())
        expected = str(expected_wait_id if expected_wait_id is not None else item.get("wait_id") or "")
        if not expected or expected != str(item.get("wait_id") or ""):
            raise ServiceError("wait_changed", WAIT_CHANGED, context={"status": 409})
        sent = self._responder()._deliver(item.get("launch") or {}, str(item.get("key") or ""),
                                          str(item.get("agent") or ""), said, expected_wait_id=expected)
        if str((sent or {}).get("status") or "") == "wait_not_current":
            raise ServiceError("wait_changed", WAIT_CHANGED, context={"status": 409})
        if str((sent or {}).get("status") or "") != "delivered":
            raise ServiceError("not_kept", "Your answer did not reach the agent. Nothing was typed. Try again.",
                               context={"status": 409})
        return {"answered": True, "key": item.get("key")}


SOURCES = (DecisionSource, PhoneCallSource, MeetingProposalSource, ProjectProposalSource, SendSource,
           CoderQuestionSource)


def source_for(db: Any, ref: Any) -> Optional[Source]:
    """The source of a ref that is not a Program's, else ``None``."""
    text = str(ref or "")
    for kind in SOURCES:
        if text.startswith(kind.prefix):
            return kind(db)
    return None


__all__ = ["CoderQuestionSource", "DecisionSource", "MeetingProposalSource", "PhoneCallSource", "ProjectProposalSource",
           "SOURCES", "SendSource", "Source", "source_for"]
