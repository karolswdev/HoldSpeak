"""Transport-neutral decision lifecycle operations (HS-123-04)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
import asyncio
import time
import uuid
from typing import Any
from ..db.core import Database
from ..principals import Principal, PrincipalKind, PrincipalRight
from .errors import ConflictError, NotFound, ServiceError, ValidationError

@observe_service
class DecisionLifecycleService:
    def __init__(self, db: Database, kernel: Any | None = None, model_generator: Any | None = None, *, observer: PipelineObserver | None = None) -> None:
        self._db, self._kernel, self._model_generator = db, kernel, model_generator
        self._observer = observer or NullObserver()
    def list_decisions(self, principal: Principal, *, project_id: str | None = None, project_key: str | None = None, meeting_id: str | None = None, lifecycle: str | None = None, limit: int = 200, offset: int = 0) -> dict[str, Any]:
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
        self._require(principal, PrincipalRight.OWNER); payload=payload or {}
        from ..db.decisions import derive_promoted_artifact_id
        try: decision=self._db.decisions.assert_promotable(decision_id); derive_promoted_artifact_id(decision_id,artifact_type)
        except Exception as exc: raise self._promotion_error(exc, decision_id) from exc
        from ..deployment_revisions import capture_deployment_revision
        from ..inference_targets import resolve_placement, target_refusal
        from ..kernel.inference_runner import InvocationRequest, ServiceContract
        from ..kernel.prompt_adapter import CanonicalPromptAdapter
        from ..kernel.runtime import _as_principal, _service
        broker=self._kernel or _service(); requested=str(payload.get("inference_target_id") or "this_machine").strip(); target=resolve_placement(self._db, invocation=requested).target
        if not target.ready: raise ServiceError("target_unavailable",target.readiness_reason,context={**target_refusal(target),"status":409})
        revision=capture_deployment_revision(self._db,target); normalized=str(artifact_type).strip().lower()
        prompt=f"Artifact type: {normalized}\nDecision: {decision.text}\nRationale: {decision.rationale or 'Not recorded'}\nDecided at: {decision.decided_at}\nMeeting: {decision.source_meeting_id}"
        parent=broker.parent_run_controller.start(principal,kind="decision.promotion-draft",definition_ref=f"decision:{decision.id}",definition_revision=str(decision.updated_at),input_snapshot={"decision_id":decision.id,"meeting_revision":decision.decided_at,"artifact_type":normalized},deadline_at=time.time()+300,child_budget=1)
        invocation_id="decision_draft_"+uuid.uuid4().hex
        material={"system_prompt":"Draft one concise artifact from the accepted decision. Preserve the decision's meaning. Return Markdown only and do not invent approval.","user_prompt":prompt,"max_tokens":1200,"temperature":None,"decision_revision":decision.updated_at,"meeting_revision":decision.decided_at,"artifact_type":normalized}
        request=InvocationRequest(revision.id,ServiceContract.for_payload("holdspeak.decision-promotion-draft","1",material),time.time()+300,material,invocation_id,parent.operation_id)
        def projection_payload(value: Any) -> dict[str, Any]:
            return {"output":str(dict(value).get("output") or ""),"decision_id":decision.id,"artifact_type":normalized,"actor":principal.identity}
        with _as_principal(principal): outcome=await asyncio.to_thread(broker.inference_runner.invoke,request,CanonicalPromptAdapter(),publish=broker.projection_stager.publisher(invocation_id,"decision-promotion-draft",projection_payload),parent_context=parent.context)
        if outcome.outcome != "succeeded":
            if broker.store.receipt(parent.operation_id) is None:
                broker.parent_run_controller.close(parent.context,outcome.outcome,principal=principal)
            raise ConflictError(f"inference_{outcome.outcome}",code=f"inference_{outcome.outcome}")
        projection=broker.projection_stager.finalize(invocation_id)
        if projection is None:
            if broker.store.receipt(parent.operation_id) is None:
                broker.parent_run_controller.close(parent.context,"cancelled",principal=principal)
            raise ConflictError("decision_promotion_cancelled",code="decision_promotion_cancelled")
        output=str(projection.get("output") or "").strip(); artifact_id=str(projection.get("artifact_id") or "")
        if not output or not artifact_id:
            broker.parent_run_controller.close(parent.context,"failed",principal=principal); raise ConflictError("model_returned_empty_output",code="model_returned_empty_output")
        parent_receipt=broker.parent_run_controller.close(parent.context,"succeeded",artifact_id,principal=principal)
        artifact=self._db.plugins.get_artifact(artifact_id); current=self._db.decisions.get(decision_id)
        receipt={"actor":principal.identity,"operation":"decision.promote","subject":f"decision:{decision_id}","outcome":"applied","artifact_id":artifact_id,"artifact_type":normalized,"review_status":"draft"}
        return {"decision":current.to_dict() if current else None,"artifact":artifact.to_dict() if artifact else None,"receipt":receipt,"operation_id":parent.operation_id,"invocation_id":invocation_id,"invocation":{"operation_id":outcome.operation_id,"deployment_revision":revision.id,"outcome":outcome.outcome,"receipt":dict(outcome.receipt)},"parent_receipt":dict(parent_receipt),"inference_target":target.to_dict()}
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
