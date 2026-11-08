"""Transport-neutral decision lifecycle operations (HS-123-04)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
import asyncio
import uuid
from typing import Any
from ..db.core import Database
from ..principals import Principal, PrincipalKind, PrincipalRight
from .errors import ConflictError, NotFound, ServiceError, ValidationError

@observe_service
class DecisionLifecycleService:
    def __init__(self, db: Database, kernel: Any | None = None, *, observer: PipelineObserver | None = None) -> None:
        self._db, self._kernel = db, kernel
        self._observer = observer or NullObserver()
    def list_decisions(self, principal: Principal, *, project_id: str | None = None, project_key: str | None = None, meeting_id: str | None = None, lifecycle: str | None = None, limit: int = 200, offset: int = 0, scope: str | None = None, decision_id: str | None = None, q: str | None = None, current: bool = False) -> dict[str, Any]:
        # PHILO-17: `scope="all"` is every decision on the desk (meeting and
        # Desk decisions), with its date, its meeting and its record; one
        # page and the total. `decision_id` reads one row; `q` searches.
        if scope == "all":
            self._require(principal, PrincipalRight.READ)
            return self._db.decisions.ledger(meeting_id=meeting_id, decision_id=decision_id, query=q, current=current, limit=limit, offset=offset)
        if project_id and project_key and project_id != project_key: raise ValidationError("project_id and project_key must name the same project")
        if not any((project_id, project_key, meeting_id, lifecycle)): return {"decisions":[r.to_dict() for r in self._db.desk_decisions.list(limit=limit)]}
        self._require(principal, PrincipalRight.READ)
        rows=self._db.decisions.list(project_key=project_key or project_id, meeting_id=meeting_id, lifecycle=lifecycle, limit=limit, offset=offset)
        return {"decisions":[r.to_dict() for r in rows], "page":{"offset":max(0,int(offset)),"limit":max(1,min(int(limit),500)),"count":len(rows)}}
    def get_decision(self, principal: Principal, decision_id: str) -> dict[str, Any]:
        desk=self._db.desk_decisions.get(decision_id)
        if desk is not None: return {"decision":desk.to_dict()}
        self._require(principal, PrincipalRight.READ)
        result=self._db.decisions.get_with_lineage(decision_id)
        if result is None: raise NotFound("decision", decision_id)
        return result
    def get_moment(self, principal: Principal, decision_id: str) -> dict[str, Any]:
        self._require(principal, PrincipalRight.READ)
        decision=self._db.decisions.get(decision_id)
        if decision is None: raise NotFound("decision", decision_id)
        moment=self._db.decisions.resolve_decision_moment(decision_id)
        if moment is None: raise NotFound("decision_moment", decision_id)
        return {"decision_id":decision.id,"provenance_label":decision.provenance_label,"moment":moment.to_dict()}
    def transition(self, principal: Principal, decision_id: str, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require(principal, PrincipalRight.OWNER)
        from ..db.decisions import DecisionTransitionRefused
        try:
            if action == "accept": receipt=self._db.decisions.accept(decision_id, actor=principal.identity)
            elif action == "reject": receipt=self._db.decisions.reject(decision_id, actor=principal.identity)
            elif action == "supersede": receipt=self._db.decisions.supersede(decision_id, str((payload or {}).get("superseded_by") or "").strip(), actor=principal.identity)
            else: raise ValidationError(f"unknown decision transition: {action}")
        except KeyError as exc: raise NotFound("decision",decision_id) from exc
        except DecisionTransitionRefused as exc: raise ConflictError(str(exc), code=exc.code, context={"current_lifecycle":exc.current,"action":exc.action}) from exc
        record=self._db.decisions.get(decision_id)
        return {"decision":record.to_dict() if record else None,"receipt":receipt.to_dict()}
    def supersede(self, principal: Principal, decision_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        desk=self._db.desk_decisions.get(decision_id)
        if desk is not None:
            successor=self._db.desk_decisions.supersede(decision_id,"decision_"+uuid.uuid4().hex[:12])
            if successor is None: raise NotFound("decision",decision_id)
            return {"decision":successor.to_dict(),"_status":201}
        return self.transition(principal,decision_id,"supersede",payload)
    def promote(self, principal: Principal, decision_id: str, artifact_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require(principal, PrincipalRight.OWNER)
        try: receipt=self._db.decisions.promote(decision_id,artifact_type,actor=principal.identity)
        except Exception as exc: raise self._promotion_error(exc, decision_id) from exc
        return self._promotion_payload(decision_id, receipt)
    async def draft_promoted_with_model(self, principal: Principal, decision_id: str, artifact_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Draft an accepted decision through its exact frozen OWNER assignment."""
        self._require(principal, PrincipalRight.OWNER)
        payload = payload or {}
        from ..db.decisions import derive_promoted_artifact_id
        try:
            decision = self._db.decisions.assert_promotable(decision_id)
            derive_promoted_artifact_id(decision_id, artifact_type)
        except Exception as exc:
            raise self._promotion_error(exc, decision_id) from exc
        from ..kernel.runtime import _service
        from . import engine_door

        normalized = str(artifact_type).strip().lower()
        broker = self._kernel or _service()
        # E3: the v1 per-request engine override is retired; the assignment names the engine.
        if str(payload.get("inference_target_id") or "").strip():
            raise ConflictError(
                "inference_request_target_override_retired",
                code="inference_request_target_override_retired",
            )
        try:
            engine = engine_door.engine_for(broker, "decision.promotion_draft")
        except engine_door.EngineDoorError as exc:
            raise ConflictError(
                "decision_promotion_draft_refused",
                code="decision_promotion_draft_refused",
                context={"reason": "inference_no_engine", "operation_id": ""},
            ) from exc
        prompt = (
            f"Artifact type: {normalized}\nDecision: {decision.text}\n"
            f"Rationale: {decision.rationale or 'Not recorded'}\n"
            f"Decided at: {decision.decided_at}\nMeeting: {decision.source_meeting_id}"
        )
        prompt_payload = engine_door.with_memory(
            broker, engine,
            {
                "system_prompt": "Draft one concise artifact from the accepted decision. Preserve the decision's meaning. Return Markdown only and do not invent approval.",
                "user_prompt": prompt,
                "max_tokens": 1200,
                "temperature": None,
                "decision_revision": decision.updated_at,
                "meeting_revision": decision.decided_at,
                "artifact_type": normalized,
            },
            lambda: self._decision_memory(decision),
            reserved_output_tokens=1200,
        )

        def projection(value: Any) -> dict[str, Any]:
            text = value.get("output") if isinstance(value, dict) else value
            return {
                "output": str(text or ""),
                "decision_id": decision.id,
                "artifact_type": normalized,
                "actor": principal.identity,
            }

        try:
            answer = await asyncio.to_thread(
                engine_door.run, broker, principal, "decision.promotion_draft", prompt_payload,
                engine=engine, deadline=180, stage=("decision-promotion-draft", projection),
            )
        except engine_door.EngineDoorError as exc:
            code = "decision_promotion_cancelled" if exc.outcome == "cancelled" else "decision_promotion_draft_refused"
            raise ConflictError(
                code,
                code=code,
                context={"reason": "inference_" + (exc.outcome or exc.code), "operation_id": exc.operation_id},
            ) from exc
        published = answer.published if isinstance(answer.published, dict) else {}
        artifact_id = str(published.get("artifact_id") or "")
        output = str(published.get("output") or "").strip()
        if not artifact_id or not output:
            raise ConflictError("model_returned_empty_output", code="model_returned_empty_output")
        artifact = self._db.plugins.get_artifact(artifact_id)
        current = self._db.decisions.get(decision_id)
        receipt = {
            "actor": principal.identity,
            "operation": "decision.promote",
            "subject": f"decision:{decision_id}",
            "outcome": "applied",
            "artifact_id": artifact_id,
            "artifact_type": normalized,
            "review_status": "draft",
        }
        return {
            "decision": current.to_dict() if current else None,
            "artifact": artifact.to_dict() if artifact else None,
            "receipt": receipt,
            # The runner's kernel operation is the one receipt for the draft.
            "operation_id": answer.operation_id,
            "invocation_id": answer.invocation_id,
            "invocation": {"operation_id": answer.operation_id, "outcome": "succeeded"},
            "placement": {"source": "owner_assignment", "egress": {"scope": engine_door.egress_of(broker, engine)}},
        }
    def _decision_memory(self, decision: Any) -> Any:
        """Earlier decisions and notes on the same subject.

        The decision is left out under every name: its ref, its meeting, and
        any other source that repeats its words (a decision record minted
        from it).  Those are already in the prompt.
        """
        from .memory_grounding import memory_for

        return memory_for(
            "decision.promotion_draft",
            self._db,
            query=f"{decision.text} {decision.rationale or ''}",
            exclude_refs=[f"decision:{decision.id}"]
            + ([f"meeting:{decision.source_meeting_id}"] if decision.source_meeting_id else []),
            exclude_texts=[decision.text],
        )

    def _require(self, principal: Principal, right: PrincipalRight) -> None:
        if not principal.permits(right):
            status=401 if principal.kind is PrincipalKind.NONE else 403
            from ..principals import refusal
            raise ServiceError("forbidden","authority refused",context={**refusal(principal,right),"status":status})
    def _promotion_error(self, exc: Exception, decision_id: str) -> ServiceError:
        from ..db.decisions import DecisionPromotionRefused
        if isinstance(exc,KeyError): return NotFound("decision",decision_id)
        if isinstance(exc,DecisionPromotionRefused): return ConflictError(exc.detail,code=exc.code,context={"decision_id":exc.decision_id})
        return ValidationError(str(exc))
    def _promotion_payload(self, decision_id: str, receipt: Any) -> dict[str, Any]:
        artifact=self._db.plugins.get_artifact(receipt.artifact_id); decision=self._db.decisions.get(decision_id)
        return {"decision":decision.to_dict() if decision else None,"artifact":artifact.to_dict() if artifact else None,"receipt":receipt.to_dict()}
