"""Transport-neutral Recipe operations, admitted through the inference runner."""
from __future__ import annotations
import asyncio
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from ..db.core import Database
from ..deployment_revisions import capture_deployment_revision
from ..kernel.inference_runner import InferenceRunner, InvocationRequest, SavedDefinition
from ..kernel.model import KernelRefused
from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from .inference_outcomes import map_inference_outcome

def _new_id(prefix: str) -> str: return f"{prefix}_{uuid.uuid4().hex[:12]}"
Broadcast = Callable[..., None]

@observe_service
class RecipeService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None, broker: Any = None) -> None:
        if broker is None:
            from ..kernel.runtime import _service
            broker = _service()
        if getattr(broker,"database",db) is not db:
            from ..kernel.runtime import _configure
            broker=_configure(db)
        self._db, self._broker, self._observer = db, broker, observer or NullObserver()
        from ..kernel.recipe_projection import register
        register(broker.projection_stager)
        # Cancellation must reach the SAME runner instance whose in-process
        # registry holds the in-flight invocation, across per-request service
        # constructions: the runner is the broker-owned singleton, and the
        # acting principal rides the kernel `_as_principal` context.
        self._runner = broker.inference_runner

    def _invoke(self, principal: Principal, request: Any, adapter: Any, *, publish: Any):
        from ..kernel.runtime import _as_principal
        with _as_principal(principal):
            return self._runner.invoke(request, adapter, publish=publish)
    def list_recipes(self, principal: Principal) -> list[dict[str, Any]]: return [self._payload(r) for r in self._db.recipes.list()]
    def get_recipe(self, principal: Principal, recipe_id: str) -> dict[str, Any]:
        r=self._db.recipes.get(recipe_id)
        if r is None: raise NotFound("Agent",recipe_id)
        return self._payload(r)
    def create_recipe(self, principal: Principal, *, name: str="", recipe_id: str|None=None, **fields: Any) -> dict[str, Any]:
        if not str(name).strip(): raise ValidationError("Agent name is required")
        fields["name"]=name; return self._payload(self._db.recipes.upsert(recipe_id=str(recipe_id or fields.pop("id",None) or _new_id("recipe")),**self._recipe_fields(fields)))
    def update_recipe(self, principal: Principal, recipe_id: str, **fields: Any) -> dict[str, Any]:
        existing=self._db.recipes.get(recipe_id)
        if existing is None: raise NotFound("Agent",recipe_id)
        return self._payload(self._db.recipes.upsert(recipe_id=recipe_id,**self._recipe_fields(fields,existing)))
    def delete_recipe(self, principal: Principal, recipe_id: str) -> bool:
        if not self._db.recipes.delete(recipe_id): raise NotFound("Agent",recipe_id)
        return True
    async def run(self, principal: Principal, recipe_id: str, *, input: str="", variables: dict[str,Any]|None=None, inference_target_id: str|None=None, requested_placement: str|None=None, max_tokens: Any=None, temperature: Any=None, source_ref: str|None=None, source_type: Any=None, deadline_at: Any=None, broadcast: Broadcast|None=None, **extra: Any) -> dict[str,Any]:
        from .support import _render_user_prompt, canonical_source_type, inject_skills
        recipe=self._recipe(recipe_id); variables=variables if isinstance(variables,dict) else {}
        user=_render_user_prompt(recipe.user_template,variables,str(input or ""))
        if not user.strip(): raise ServiceError("empty_input","nothing to run: provide `input` or a Agent input template")
        target, revision=self._target(recipe,inference_target_id or requested_placement or recipe.profile_id or "this_machine")
        sources=[{"source_type":"recipe","source_ref":recipe_id}]
        if str(source_ref or "").strip(): sources.append({"source_type":canonical_source_type(source_type) if source_type else "input","source_ref":str(source_ref)})
        payload={"system_prompt":inject_skills(self._db,recipe.system_prompt,recipe_id),"user_prompt":user,"variables":variables,"recipe_id":recipe_id,"recipe_revision":str(recipe.last_modified),"deployment_revision":revision.id,"temperature":float(temperature) if temperature is not None else None,"max_tokens":int(max_tokens) if max_tokens is not None else None}
        iid="recipe_run_"+uuid.uuid4().hex; self._broadcast(broadcast,"running",kind="recipe",ref=recipe_id,name=recipe.name or recipe_id)
        try:
            outcome=await asyncio.to_thread(self._invoke,principal,InvocationRequest(revision.id,SavedDefinition(f"recipe:{recipe_id}",str(recipe.last_modified)),float(deadline_at or time.time()+60),payload,iid),CanonicalPromptAdapter(),publish=self._broker.projection_stager.publisher(iid,"recipe-run",lambda result:self._run_projection(result,recipe,target,sources,user)))
        except KernelRefused as exc: raise self._outcome_error(None,exc)
        if outcome.outcome!="succeeded": self._broadcast(broadcast,"error",kind="recipe",ref=recipe_id,name=recipe.name or recipe_id,error=outcome.outcome); raise self._outcome_error(outcome,None,target=target)
        result=self._broker.projection_stager.finalize(iid)
        if result is None: raise ServiceError("projection_not_published","Recipe result is awaiting receipt reconciliation",context={"invocation_id":iid,"operation_id":outcome.operation_id,"status":409})
        self._broadcast(broadcast,"ready",kind="recipe",ref=recipe_id,name=recipe.name or recipe_id); return result
    async def chat(self, principal: Principal, recipe_id: str, *, question: str, history: list[Any]|None=None, grounding: Any=None, inference_target_id: str|None=None, egress_context: Any=None, broadcast: Broadcast|None=None, default_model: str="") -> dict[str,Any]:
        from .support import inject_skills
        question=str(question or "").strip()
        if not question: raise ValidationError("question is required")
        recipe=self._recipe(recipe_id); target,revision=self._target(recipe,inference_target_id or recipe.profile_id or "this_machine")
        from .support import _GROUNDING_EXPANDS, _GROUNDING_MAX_REFS, _hydrate_grounding
        name=recipe.name or recipe_id; blocks=[]; context=[]
        if (recipe.manual_context or "").strip(): context.append(recipe.manual_context)
        if recipe.kb_id: context.append(self._kb_block(recipe.kb_id))
        if context: blocks.append("[CONTEXT]\n"+"\n\n".join(x for x in context if x))
        context_ids=[]; context_titles=[]; grounding_echo=None
        if grounding is not None:
            if not isinstance(grounding,dict): raise ValidationError("grounding must be an object")
            mids=[str(x).strip() for x in grounding.get("meeting_ids",[]) if str(x).strip()] if isinstance(grounding.get("meeting_ids"),list) else []
            aids=[str(x).strip() for x in grounding.get("artifact_ids",[]) if str(x).strip()] if isinstance(grounding.get("artifact_ids"),list) else []
            expand=str(grounding.get("expand") or "summary").strip() or "summary"
            if expand not in _GROUNDING_EXPANDS: raise ValidationError(f"expand {expand!r} is not one of {list(_GROUNDING_EXPANDS)}")
            if len(mids)+len(aids)>_GROUNDING_MAX_REFS: raise ValidationError(f"grounding is capped at {_GROUNDING_MAX_REFS} refs")
            gblocks,gids,gtitles,unknown=_hydrate_grounding(self._db,mids,aids,expand)
            if unknown: raise ServiceError("grounding_not_found","grounding ids not on this hub",context={"unknown_ids":unknown})
            if gblocks: blocks.append("[GROUNDING]\n"+"\n\n".join(gblocks))
            context_ids+=gids; context_titles+=gtitles; grounding_echo={"meeting_ids":mids,"artifact_ids":aids,"expand":expand,"titles":gtitles}
        window=[x for x in (history or []) if isinstance(x,dict)][-12:]
        convo="\n".join(("User: " if str(x.get("role"))=="you" else f"{name}: ")+str(x.get("text") or "") for x in window)
        if convo: blocks.append("[CONVERSATION SO FAR]\n"+convo)
        blocks.append(f"[USER]\n{question[:6000]}\n\nReply as {name}.")
        payload={"system_prompt":inject_skills(self._db,(recipe.system_prompt or "").strip() or f"You are {name}, a helpful assistant.",recipe_id),"user_prompt":"\n\n".join(blocks),"history":window,"recipe_id":recipe_id,"recipe_revision":str(recipe.last_modified),"deployment_revision":revision.id,"context_ids":context_ids,"context_titles":context_titles,"grounding":grounding_echo,"selected_model":default_model or target.model}
        iid="recipe_chat_"+uuid.uuid4().hex; self._broadcast(broadcast,"running",kind="recipe",ref=recipe_id,name=name)
        try:
            outcome=await asyncio.to_thread(self._invoke,principal,InvocationRequest(revision.id,SavedDefinition(f"recipe:{recipe_id}",str(recipe.last_modified)),time.time()+60,payload,iid),CanonicalPromptAdapter(),publish=self._broker.projection_stager.publisher(iid,"recipe-chat-result",lambda result:self._chat_projection(result,recipe,target,payload)))
        except KernelRefused as exc: raise self._outcome_error(None,exc)
        if outcome.outcome!="succeeded": raise self._outcome_error(outcome,None,target=target)
        result=self._broker.projection_stager.finalize(iid)
        if result is None: raise ServiceError("projection_not_published","Recipe chat is awaiting receipt reconciliation",context={"invocation_id":iid,"operation_id":outcome.operation_id,"status":409})
        self._broadcast(broadcast,"ready",kind="recipe",ref=recipe_id,name=name); return result
    def _recipe(self, recipe_id: str):
        r=self._db.recipes.get(recipe_id)
        if r is None: raise NotFound("Agent",recipe_id)
        return r
    def _target(self, recipe: Any, requested: str):
        from ..inference_targets import resolve_inference_target, target_refusal
        target=resolve_inference_target(self._db,requested)
        if not target.ready: raise ServiceError("target_unavailable",target.readiness_reason,context={**target_refusal(target),"status":409})
        return target,capture_deployment_revision(self._db,target)
    _outcome_error = staticmethod(map_inference_outcome)
    @staticmethod
    def _broadcast(broadcast: Broadcast|None,state: str,**frame: Any)->None:
        if broadcast: broadcast(state,**frame)
    def _run_projection(self,result: Any,recipe: Any,target: Any,sources: list[dict[str,str]],user: str)->dict[str,Any]:
        d=dict(result) if isinstance(result,dict) else {"output":str(result)}; output=str(d["output"]); aid="artifact_"+uuid.uuid4().hex[:12]
        return {"recipe_id":recipe.id,"name":f"{recipe.name or recipe.id}: {user}" if user else (recipe.name or recipe.id),"output":output,"provider":str(d.get("provider") or target.engine),"profile_id":target.profile_id,"inference_target":target.to_dict(),"actual_placement":target.placement_receipt(provider=str(d.get("provider") or target.engine),model=str(d.get("model") or target.model)),"sources":sources,"artifact_id":aid,"created_at":datetime.now().isoformat()}
    def _chat_projection(self,result: Any,recipe: Any,target: Any,payload: dict[str,Any])->dict[str,Any]:
        d=dict(result) if isinstance(result,dict) else {"output":str(result)}
        out={"recipe_id":recipe.id,"output":str(d["output"]),"provider":str(d.get("provider") or target.engine),"profile_id":target.profile_id,"inference_target":target.to_dict(),"actual_placement":target.placement_receipt(provider=str(d.get("provider") or target.engine),model=str(d.get("model") or payload["selected_model"])),"egress":{"scope":"local"},"model":str(d.get("model") or payload["selected_model"]),"context_ids":payload["context_ids"],"context_titles":payload["context_titles"]}
        if payload["grounding"] is not None: out["grounding"]=payload["grounding"]
        return out
    def cancel(self, principal: Principal, invocation_id: str) -> dict[str, str]:
        from ..kernel.runtime import _as_principal
        with _as_principal(principal):
            return {"invocation_id": invocation_id, "disposition": self._runner.cancel(invocation_id)}
    def keep(self,principal:Principal,recipe_id:str,*,output:str,input:str="",sources:list[dict[str,str]]|None=None)->dict[str,Any]:
        from .support import _persist_run_artifact
        if not str(output or "").strip(): raise ValidationError("output is required")
        recipe=self._recipe(recipe_id); aid=_persist_run_artifact(db=self._db,kind="recipe",name=recipe.name or recipe_id,user_input=str(input or ""),output=str(output),sources=sources or [{"source_type":"recipe","source_ref":recipe_id}])
        if not aid: raise ServiceError("artifact_persist_failed","keep failed")
        return {"artifact_id":aid}
    def _kb_block(self,kb_id:str)->str:
        from .support import _context_material
        kb=self._db.kbs.get(kb_id)
        if kb is None: return ""
        texts=[]
        for member in list(getattr(kb,"member_ids",None) or [])[:12]:
            bare=member.split(":",1)[1] if ":" in member else member
            for kind in ("note","artifact","meeting"):
                _,text=_context_material(self._db,bare,kind,"")
                if text: texts.append(text[:1200]); break
        return f"[KB: {kb.name or kb_id}]\n"+"\n\n".join(texts) if texts else f"[KB: {kb.name or kb_id} — no hydrated members]"
    def _payload(self,recipe:Any)->dict[str,Any]:
        from .support import capability_descriptor
        from ..inference_targets import resolve_placement
        row=recipe.to_dict(); row["capability"]=capability_descriptor(kind="persona",name=recipe.name or recipe.id,supported_placements=[f"profile:{recipe.profile_id}"] if recipe.profile_id else ["this_machine"],action_label=f"Ask {recipe.name or 'Agent'}"); row["placement"]=resolve_placement(self._db,agent=recipe.profile_id).placement_dict(); return row
    @staticmethod
    def _recipe_fields(body:dict[str,Any],existing:Any=None)->dict[str,Any]:
        p=lambda k,d:body[k] if k in body else d
        return {"name":str(p("name",existing.name if existing else "")),"avatar":str(p("avatar",existing.avatar if existing else "")),"role":str(p("role",existing.role if existing else "")),"system_prompt":str(p("system_prompt",existing.system_prompt if existing else "")),"user_template":str(p("user_template",existing.user_template if existing else "")),"tools":list(p("tools",existing.tools if existing else [])),"kb_id":p("kb_id",existing.kb_id if existing else None) or None,"profile_id":p("profile_id",existing.profile_id if existing else None) or None,"manual_context":str(p("manual_context",existing.manual_context if existing else "")),"use_zone_context":bool(p("use_zone_context",existing.use_zone_context if existing else False))}
