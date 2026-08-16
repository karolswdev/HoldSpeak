"""Principal-aware cadence query and lifecycle boundary."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from ..intel.providers import endpoint_egress
from ..principals import Principal
from .errors import ConflictError, NotFound, ValidationError

_LOCAL_EGRESS = endpoint_egress(cloud=False, label="Local only")
#: One loop detail is a foreground read; its drafted action never outlives it.
_DRAFT_DEADLINE_SECONDS = 120.0
#: The canonical payload contract this service admits its one child under.
_DRAFT_CONTRACT = "holdspeak.cadence-next-action"
#: The kernel projection kind the drafted output is staged as.
_DRAFT_PROJECTION = "cadence-next-action"


@observe_service
class CadenceService:
    def __init__(self, db: Any, config: Any, kernel: Any | None = None, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._config = config
        self._kernel = kernel
        self._observer = observer or NullObserver()

    def _loop_dict(self, loop: Any, *, with_next_action: bool = True) -> dict[str, Any]:
        from ..cadence.next_action import generate_next_action
        out = {"id": loop.id, "title": loop.title, "summary": loop.summary,
               "project": loop.project, "source_type": loop.source_type,
               "status": loop.status, "priority": loop.priority,
               "needs_review": loop.needs_review, "owner": loop.owner,
               "due_at": loop.due_at, "snoozed_until": loop.snoozed_until,
               "stale_score": loop.stale_score, "nudge_count": loop.nudge_count,
               "evidence": [{"kind": e.kind, "ref_id": e.ref_id, "label": e.label,
                             "timestamp": e.timestamp, "deep_link": e.deep_link} for e in loop.evidence],
               "egress": _LOCAL_EGRESS}
        if with_next_action:
            action = generate_next_action(loop)
            out["next_action"] = {"kind": action.kind, "title": action.title,
                                  "body_markdown": action.body_markdown, "reversible": action.reversible,
                                  "confidence": action.confidence}
        return out

    def status(self, principal: Principal) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for loop in self._db.cadence.list_loops(include_terminal=True):
            counts[loop.status] = counts.get(loop.status, 0) + 1
        c = self._config
        return {"enabled": c.enabled, "pressure": c.pressure,
                "tick_interval_seconds": c.tick_interval_seconds,
                "quiet_hours": {"start": c.quiet_hours_start, "end": c.quiet_hours_end},
                "max_nudges_per_day": c.max_nudges_per_day,
                "policies": len(self._db.cadence.list_policies()), "counts": counts,
                "egress": _LOCAL_EGRESS}

    def list_loops(self, principal: Principal, *, include_terminal: bool = False) -> dict[str, Any]:
        return {"loops": [self._loop_dict(loop) for loop in self._db.cadence.list_loops(include_terminal=include_terminal)], "egress": _LOCAL_EGRESS}

    def brief(self, principal: Principal) -> dict[str, Any]:
        from ..cadence.brief import build_brief
        brief = build_brief(self._db)
        return {"date": brief.date, "headline": brief.headline, "open_count": brief.open_count,
                "generated_by": brief.generated_by,
                "items": [{"loop": self._loop_dict(item.loop, with_next_action=False),
                           "next_action": {"kind": item.next_action.kind, "title": item.next_action.title,
                                           "body_markdown": item.next_action.body_markdown}} for item in brief.items],
                "egress": _LOCAL_EGRESS}

    def closeout(self, principal: Principal) -> dict[str, Any]:
        from ..cadence.closeout import build_closeout
        closeout = build_closeout(self._db, now=datetime.now())
        return {"date": closeout.date, "open_count": closeout.open_count, "summary": closeout.summary,
                "recs": [{"loop": self._loop_dict(rec.loop), "severity": rec.severity,
                          "action": rec.action, "reason": rec.reason} for rec in closeout.recs],
                "egress": _LOCAL_EGRESS}

    def apply_closeout(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
        from ..cadence.closeout import apply_decision
        applied = skipped = 0
        for decision in payload.get("decisions") or []:
            if apply_decision(self._db, str(decision.get("loop_id", "")), str(decision.get("action", ""))): applied += 1
            else: skipped += 1
        return {"applied": applied, "skipped": skipped, "egress": _LOCAL_EGRESS}

    def history(self, principal: Principal, *, limit: int = 50) -> dict[str, Any]:
        return {"nudges": self._db.cadence.list_nudges(limit=limit), "egress": _LOCAL_EGRESS}

    def _required_loop(self, loop_id: str) -> Any:
        loop = self._db.cadence.get_loop(loop_id)
        if loop is None:
            raise NotFound("loop", loop_id)
        return loop

    def snooze(self, principal: Principal, loop_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._required_loop(loop_id)
        until = payload.get("until")
        if not until:
            until = (datetime.now() + timedelta(hours=float(payload.get("hours", 24)))).isoformat()
        self._db.cadence.snooze(loop_id, until)
        return self._loop_dict(self._required_loop(loop_id))

    def set_status(self, principal: Principal, loop_id: str, status: str) -> dict[str, Any]:
        self._required_loop(loop_id)
        self._db.cadence.set_status(loop_id, status)
        return self._loop_dict(self._required_loop(loop_id))

    def reply(self, principal: Principal, loop_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Deliver the owner's typed answer into a waiting agent's pane, then close.

        Never autonomous (CAD-3-03, kept through the Phase-123 service move): the
        text is the owner's, given here and now. The loop must be an
        ``agent_question``, and its session must still resolve to a live pane —
        otherwise nothing is delivered and the loop stays open. The side effect
        rides the one owner-gesture ``process.input`` path and lives HERE, never in
        the side-effect-free ``holdspeak.cadence`` package.
        """
        loop = self._required_loop(loop_id)
        if loop.source_type != "agent_question":
            raise ValidationError("not an agent loop", code="cadence_reply_not_agent_loop")
        text = str(payload.get("text") or "").strip()
        if not text:
            raise ValidationError("reply text is required", code="cadence_reply_empty")
        session = self._awaiting_agent_session(str(loop.source_id or ""))
        pane = str(getattr(session, "tmux_pane", "") or "").strip()
        if not pane:
            raise ConflictError("no terminal pane for this agent session",
                                code="cadence_reply_no_pane")
        from ..delivery.direct_gesture_input import (
            ProcessInputRefused,
            submit_process_input_from_owner_gesture,
        )
        try:
            result = submit_process_input_from_owner_gesture(
                pane=pane,
                text=text,
                session_key=str(getattr(session, "session_id", "") or f"pane:{pane}"),
                agent=str(getattr(session, "agent", "") or ""),
                principal=principal,
            )
        except ProcessInputRefused as exc:
            raise ConflictError(f"delivery refused: {exc.reason}",
                                code="cadence_reply_refused") from exc
        # The answer handles the question; the loop closes and the send is counted.
        self._db.cadence.set_status(loop_id, "closed")
        self._db.cadence.bump_nudge(loop_id)
        return {"delivered": True, "pane": pane,
                "operation_id": result.get("operation_id"),
                "command_id": result.get("command_id"),
                "egress": _LOCAL_EGRESS}

    @staticmethod
    def _awaiting_agent_session(session_id: str) -> Any:
        """The still-awaiting capture for one session id, or ``None``."""
        from .. import agent_context
        try:
            sessions = agent_context.list_recent_awaiting_agent_sessions()
        except Exception:
            return None
        return next((s for s in sessions if getattr(s, "session_id", None) == session_id), None)

    def run_now(self, principal: Principal) -> dict[str, Any]:
        from ..cadence.service import CadenceService as TickService
        result = TickService(self._db, self._config).tick(datetime.now())
        return {"at": result.at, "projected": result.projected, "open_loops": result.open_loops,
                "due": [self._loop_dict(loop) for loop in result.due], "egress": _LOCAL_EGRESS}

    def audit(self, principal: Principal) -> dict[str, Any]:
        from ..cadence.audit import export_audit
        return export_audit(self._db)

    async def get_loop(self, principal: Principal, loop_id: str) -> dict[str, Any]:
        loop = self._db.cadence.get_loop(loop_id)
        if loop is None: raise NotFound("loop", loop_id)
        result = self._loop_dict(loop, with_next_action=False)
        action = await self._next_action(principal, loop)
        result["next_action"] = {"kind": action.kind, "title": action.title,
                                 "body_markdown": action.body_markdown, "reversible": action.reversible,
                                 "confidence": action.confidence, "generated_by": action.generated_by}
        return result

    async def _next_action(self, principal: Principal, loop: Any) -> Any:
        """The drafted action when one was really admitted; otherwise the deterministic one.

        CAD-7 has always been fail-closed, and HS-131-13 keeps that shape while
        moving the model work onto the one admission path: a refused, cancelled,
        failed, or off-contract draft is not an error the caller sees — it is a
        `generated_by="deterministic"` action, and the kernel already holds the
        receipt that says what happened.
        """
        from ..cadence.next_action import generate_next_action
        if getattr(self._config, "use_llm", False):
            try:
                drafted = await self._drafted_next_action(principal, loop)
            except Exception:
                drafted = None
            if drafted is not None:
                return drafted
        return await asyncio.to_thread(generate_next_action, loop)

    async def _drafted_next_action(self, principal: Principal, loop: Any) -> Any:
        """ONE admitted Cadence child, or ``None``. Never a manufactured principal.

        Request-time cadence intelligence is not scheduler authority (HS-131-06):
        the parent starts as the caller the transport authenticated, so an
        unauthenticated read is refused at admission rather than quietly borrowing
        the owner's rights. Placement comes from the one placement authority and is
        frozen into a deployment revision BEFORE the child is admitted, so the run
        can never drift onto whatever the config says when the provider answers.
        """
        from ..deployment_revisions import capture_deployment_revision
        from ..inference_targets import resolve_placement
        from ..kernel.runtime import _service

        broker = self._kernel or _service()
        target = resolve_placement(self._db).target
        if not target.ready:
            return None
        revision = capture_deployment_revision(self._db, target)
        loop_revision = str(loop.updated_at or loop.created_at or "unversioned")
        parent = broker.parent_run_controller.start(
            principal, kind="cadence.next-action-draft", definition_ref=f"cadence-loop:{loop.id}",
            definition_revision=loop_revision,
            input_snapshot={"loop_id": loop.id, "source_type": loop.source_type, "loop_revision": loop_revision},
            deadline_at=time.time() + _DRAFT_DEADLINE_SECONDS, child_budget=1)
        try:
            return await self._draft_child(broker, parent, principal, loop, revision, loop_revision)
        except asyncio.CancelledError:
            # The REQUEST went away (client disconnect, shutdown, timeout) while the
            # provider still runs in its worker thread — cancelling this coroutine
            # stops nothing downstream. Closing the parent `failed` here would be
            # both dishonest and unsafe: `failed` is not one of the states the
            # projection stager fences on, so the surviving thread's output would
            # publish through the next recovery pass. Elect a DURABLE cancellation
            # instead: the controller signals the live child and leaves the parent
            # CANCELLED, which is what makes the stage discard rather than publish.
            self._cancel_parent(broker, parent, principal)
            raise
        except BaseException:
            # Article XI.2: an unexpected failure still ends in a terminal receipt,
            # here and now rather than whenever the lease reaper next runs. A
            # closure problem never masks the error that actually happened.
            try:
                self._close_parent(broker, parent, principal, "failed")
            except Exception:
                pass
            raise

    async def _draft_child(self, broker: Any, parent: Any, principal: Principal, loop: Any,
                           revision: Any, loop_revision: str) -> Any:
        """The ONE admitted invocation child under an already-open Cadence parent."""
        from ..cadence.llm_action import next_action_from_output, next_action_prompt
        from ..kernel.inference_runner import InvocationRequest, ServiceContract
        from ..kernel.prompt_adapter import CanonicalPromptAdapter
        from ..kernel.runtime import _as_principal

        system_prompt, user_prompt = next_action_prompt(loop)
        material = {"system_prompt": system_prompt, "user_prompt": user_prompt, "max_tokens": 900,
                    "temperature": None, "loop_id": loop.id, "loop_revision": loop_revision}
        invocation_id = "cadence_next_action_" + uuid.uuid4().hex
        request = InvocationRequest(revision.id, ServiceContract.for_payload(_DRAFT_CONTRACT, "1", material),
                                    time.time() + _DRAFT_DEADLINE_SECONDS, material, invocation_id,
                                    parent.operation_id)
        def projection_payload(value: Any) -> dict[str, Any]:
            return {"output": str(dict(value).get("output") or ""), "loop_id": loop.id,
                    "actor": principal.identity}
        with _as_principal(principal):
            outcome = await asyncio.to_thread(
                broker.inference_runner.invoke, request, CanonicalPromptAdapter(),
                publish=broker.projection_stager.publisher(invocation_id, _DRAFT_PROJECTION, projection_payload),
                parent_context=parent.context)
        if outcome.outcome != "succeeded":
            self._close_parent(broker, parent, principal, outcome.outcome)
            return None
        # Staged, never applied directly: a cancelled parent (or a receipt that never
        # became durable) discards the stage, and this read returns nothing to publish.
        projection = broker.projection_stager.finalize(invocation_id)
        if projection is None:
            self._close_parent(broker, parent, principal, "cancelled")
            return None
        # The CHILD's receipt records what the provider did; the PARENT records
        # whether a usable draft came out of it. An off-contract answer is a failed
        # draft, not a success the caller never sees.
        action = next_action_from_output(loop, str(projection.get("output") or ""))
        drafted = action.generated_by == "llm"
        self._close_parent(broker, parent, principal, "succeeded" if drafted else "failed")
        return action if drafted else None

    @staticmethod
    def _close_parent(broker: Any, parent: Any, principal: Principal, outcome: str) -> None:
        if broker.store.receipt(parent.operation_id) is None:
            broker.parent_run_controller.close(parent.context, outcome, principal=principal)

    @staticmethod
    def _cancel_parent(broker: Any, parent: Any, principal: Principal) -> None:
        """Durably elect cancellation, and never let it raise over the cancellation.

        ``cancel_by_operation_id`` is the controller's own route-side path: it
        checks the durable owner, moves the parent to CANCELLING, signals the live
        invocation child, and closes the parent ``cancelled``. If it cannot (the
        parent already terminalized, the row is gone), the fallback is still a
        terminal receipt rather than an OPEN parent left for the lease reaper.
        """
        try:
            broker.parent_run_controller.cancel_by_operation_id(principal, parent.operation_id)
        except Exception:
            try:
                CadenceService._close_parent(broker, parent, principal, "cancelled")
            except Exception:
                pass
