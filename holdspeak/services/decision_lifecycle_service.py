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
        from ..kernel.runtime import _service
        from ..inference_targets import resolve_inference_target, target_refusal
        from .support import RunLifecycle
        broker=self._kernel or _service(); invocation_id="invocation_"+uuid.uuid4().hex; requested=str(payload.get("inference_target_id") or "this_machine").strip()
        handle=broker.submit({"request_schema":1,"request_id":str(uuid.uuid4()),"idempotency_key":invocation_id,"operation":{"name":"inference.run","version":1},"target":{},"arguments":{"invocation_id":invocation_id,"definition_ref":"program:decision-promotion-v1","definition_revision":"1","grounding_refs":[{"ref":f"decision:{decision.id}","revision":decision.updated_at},{"ref":f"meeting:{decision.source_meeting_id}","revision":decision.decided_at}],"requested_target_id":requested,"deadline_at":time.time()+300.0,"input_snapshot":{"decision_id":decision.id,"artifact_type":str(artifact_type).strip().lower()}}},principal)
        if handle.get("state")=="refused": raise ConflictError("inference_admission_refused", code="inference_admission_refused", context={**handle,"status":409})
        try: handle=broker.decide(handle["operation_id"],"approve",handle["revision"],principal)
        except Exception as exc: raise ConflictError(str(exc), code=getattr(exc,"reason","inference_admission_failed")) from exc
        lifecycle=RunLifecycle(self._db,invocation_id,"program:decision-promotion-v1",operation_id=handle["operation_id"],broker=broker); target=resolve_inference_target(self._db,requested)
        try:
            lifecycle.start_attempt(destination=target.id,target=target)
            if not target.ready:
                invocation=lifecycle.fail(target.readiness_reason,state="unavailable"); raise ServiceError("target_unavailable",target.readiness_reason,context={**target_refusal(target),"invocation":invocation,"status":409})
            prompt=f"Artifact type: {str(artifact_type).strip().lower()}\nDecision: {decision.text}\nRationale: {decision.rationale or 'Not recorded'}\nDecided at: {decision.decided_at}\nMeeting: {decision.source_meeting_id}"
            if self._model_generator is not None:
                output, intel = await self._model_generator(self._db, target, prompt)
            else:
                from ..inference_targets import build_intel_for_target
                intel=build_intel_for_target(target,self._db)
                output=await asyncio.to_thread(intel.run_prompt,system_prompt="Draft one concise artifact from the accepted decision. Preserve the decision's meaning. Return Markdown only and do not invent approval.",user_prompt=prompt,max_tokens=1200)
            output=str(output or "").strip()
            if not output:
                invocation=lifecycle.fail("model_returned_empty_output",state="empty"); raise ConflictError("model_returned_empty_output",code="model_returned_empty_output",context={"invocation":invocation})
            receipt=self._db.decisions.promote(decision.id,artifact_type,actor=principal.identity,body_markdown=output,review_status="draft",model_assisted=True)
            invocation=lifecycle.succeed(receipt.artifact_id,provider=getattr(intel,"active_provider",None),model=target.model)
            return {**self._promotion_payload(decision_id,receipt),"operation_id":handle["operation_id"],"invocation_id":invocation_id,"invocation":invocation,"inference_target":target.to_dict()}
        except ServiceError: raise
        except (NotFound,ConflictError): raise
        except Exception as exc:
            try: lifecycle.fail(str(exc))
            except Exception: pass
            raise ServiceError("decision_promotion_generation_failed",str(exc),context={"status":500}) from exc
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
