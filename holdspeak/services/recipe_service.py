"""Transport-neutral Recipe operations; each model job goes through the engine door."""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from holdspeak.timestamps import utc_now_iso
from typing import Any

from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from ..db.core import Database
from ..inference_memory_policy import memory_enabled
from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.ids import new_id as _new_id


Broadcast = Callable[..., None]


class _RecipeResultAdapter:
    """Keep the recipe result contract at the physical Runner boundary."""

    connector_id = "inference-provider"

    def __init__(self) -> None:
        self._inner = CanonicalPromptAdapter()

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: Any) -> dict[str, str]:
        result = self._inner.dispatch(engine, payload, cancellation)
        return {
            "output": str(result.get("output") or ""),
            "provider": str(result.get("provider") or ""),
            "model": str(result.get("model") or ""),
        }

    def cancel(self) -> str:
        return self._inner.cancel()


@observe_service
class RecipeService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None, broker: Any = None) -> None:
        if broker is None:
            from ..kernel.runtime import _service
            broker = _service()
        if getattr(broker, "database", db) is not db:
            from ..kernel.runtime import _configure
            broker = _configure(db)
        self._db, self._broker, self._observer = db, broker, observer or NullObserver()
        from ..kernel.recipe_projection import register
        register(broker.projection_stager)

    def list_recipes(self, principal: Principal, *, kind: str | None = None) -> list[dict[str, Any]]:
        if kind is not None:
            return [self._payload(principal, record) for record in self._db.recipes.list_by_kind(kind)]
        return [self._payload(principal, record) for record in self._db.recipes.list()]

    def get_recipe(self, principal: Principal, recipe_id: str) -> dict[str, Any]:
        return self._payload(principal, self._recipe(recipe_id))

    def create_recipe(self, principal: Principal, *, name: str = "", recipe_id: str | None = None, **fields: Any) -> dict[str, Any]:
        if not str(name).strip():
            raise ValidationError("Agent name is required")
        self._refuse_post_marker_profile_pointer(principal, fields)
        fields["name"] = name
        record = self._db.recipes.upsert(
            recipe_id=str(recipe_id or fields.pop("id", None) or _new_id("recipe")),
            **self._recipe_fields(fields),
        )
        return self._payload(principal, record)

    def update_recipe(self, principal: Principal, recipe_id: str, **fields: Any) -> dict[str, Any]:
        existing = self._recipe(recipe_id)
        self._refuse_post_marker_profile_pointer(principal, fields)
        return self._payload(principal, self._db.recipes.upsert(
            recipe_id=recipe_id, **self._recipe_fields(fields, existing)
        ))

    def delete_recipe(self, principal: Principal, recipe_id: str) -> bool:
        if not self._db.recipes.delete(recipe_id):
            raise NotFound("Agent", recipe_id)
        return True

    async def run(self, principal: Principal, recipe_id: str, *, input: str = "", variables: dict[str, Any] | None = None, inference_target_id: str | None = None, requested_placement: str | None = None, workbench_id: str | None = None, max_tokens: Any = None, temperature: Any = None, source_ref: str | None = None, source_type: Any = None, deadline_at: Any = None, broadcast: Broadcast | None = None, **extra: Any) -> dict[str, Any]:
        from .support import (
            _hydrate_grounding_detailed,
            _render_user_prompt,
            canonical_source_type,
            inject_skills,
        )
        self._migrate_subject_pointers(principal)
        self._reject_retired_selector(inference_target_id or requested_placement)
        recipe = self._recipe(recipe_id)
        self._refuse_missing_legacy_profile(recipe)
        variables = variables if isinstance(variables, dict) else {}
        user = _render_user_prompt(recipe.user_template, variables, str(input or ""))
        if not user.strip():
            raise ServiceError("empty_input", "nothing to run: provide `input` or a Agent input template")
        sources = [{"source_type": "recipe", "source_ref": recipe_id}]
        if str(source_ref or "").strip():
            sources.append({"source_type": canonical_source_type(source_type) if source_type else "input", "source_ref": str(source_ref)})
        memory_blocks, memory_ids, memory_titles, memory_hydration = (
            _hydrate_grounding_detailed(
                self._db,
                [],
                [],
                "summary",
                query=user,
                include_memory=memory_enabled("recipe.run"),
            )
        )
        rendered_user = (
            "[MEMORY]\n" + "\n\n".join(memory_blocks) + "\n\n[INPUT]\n" + user
            if memory_blocks
            else user
        )
        payload = {
            "system_prompt": inject_skills(self._db, recipe.system_prompt, recipe_id),
            "user_prompt": rendered_user, "variables": variables, "recipe_id": recipe_id,
            "recipe_revision": str(recipe.last_modified),
            "temperature": float(temperature) if temperature is not None else None,
            "max_tokens": int(max_tokens) if max_tokens is not None else None,
            "workbench_id": str(workbench_id or ""),
            "context_ids": memory_ids,
            "context_titles": memory_titles,
            "grounding": {
                "source_refs": memory_hydration.source_refs,
                "selection": memory_hydration.selection,
                "matched_count": memory_hydration.matched_count,
                "overflow_count": memory_hydration.overflow_count,
            },
        }
        self._broadcast(broadcast, "running", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id)
        try:
            result = await asyncio.to_thread(
                self._through_door, principal, "recipe.run", "recipe-run", recipe, payload,
                lambda value, on: self._run_projection(value, recipe, sources, payload["user_prompt"], on),
            )
        except ServiceError as exc:
            self._broadcast(broadcast, "error", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id,
                            error=str(exc.context.get("outcome") or exc.code))
            raise
        self._broadcast(broadcast, "ready", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id)
        return result

    async def chat(self, principal: Principal, recipe_id: str, *, question: str, history: list[Any] | None = None, grounding: Any = None, inference_target_id: str | None = None, workbench_id: str | None = None, egress_context: Any = None, broadcast: Broadcast | None = None) -> dict[str, Any]:
        from .support import (
            _GROUNDING_EXPANDS,
            _GROUNDING_MAX_REFS,
            _hydrate_grounding_detailed,
            inject_skills,
        )
        self._migrate_subject_pointers(principal)
        self._reject_retired_selector(inference_target_id)
        question = str(question or "").strip()
        if not question:
            raise ValidationError("question is required")
        recipe = self._recipe(recipe_id)
        self._refuse_missing_legacy_profile(recipe)
        name = recipe.name or recipe_id
        blocks, context = [], []
        if (recipe.manual_context or "").strip(): context.append(recipe.manual_context)
        if recipe.kb_id: context.append(self._kb_block(recipe.kb_id))
        if context: blocks.append("[CONTEXT]\n" + "\n\n".join(x for x in context if x))
        context_ids: list[str] = []
        context_titles: list[str] = []
        if grounding is not None and not isinstance(grounding, dict):
            raise ValidationError("grounding must be an object")
        grounding = grounding or {}
        mids = [str(x).strip() for x in grounding.get("meeting_ids", []) if str(x).strip()] if isinstance(grounding.get("meeting_ids"), list) else []
        aids = [str(x).strip() for x in grounding.get("artifact_ids", []) if str(x).strip()] if isinstance(grounding.get("artifact_ids"), list) else []
        refs = [str(x).strip() for x in grounding.get("refs", []) if str(x).strip()] if isinstance(grounding.get("refs"), list) else []
        expand = str(grounding.get("expand") or "summary").strip() or "summary"
        if expand not in _GROUNDING_EXPANDS: raise ValidationError(f"expand {expand!r} is not one of {list(_GROUNDING_EXPANDS)}")
        if len(mids) + len(aids) + len(refs) > _GROUNDING_MAX_REFS: raise ValidationError(f"grounding is capped at {_GROUNDING_MAX_REFS} refs")
        gblocks, gids, gtitles, hydration = _hydrate_grounding_detailed(
            self._db,
            mids,
            aids,
            expand,
            qualified_refs=refs,
            query=question,
            include_memory=memory_enabled("agent.tool_turn"),
        )
        if hydration.unknown: raise ServiceError("grounding_not_found", "grounding ids not on this hub", context={"unknown_ids": hydration.unknown})
        if gblocks: blocks.append("[GROUNDING]\n" + "\n\n".join(gblocks))
        context_ids += gids; context_titles += gtitles
        grounding_echo = {
            "meeting_ids": mids,
            "artifact_ids": aids,
            "refs": refs,
            "expand": expand,
            "titles": gtitles,
            "source_refs": hydration.source_refs,
            "selection": hydration.selection,
            "matched_count": hydration.matched_count,
            "overflow_count": hydration.overflow_count,
        }
        window = [x for x in (history or []) if isinstance(x, dict)][-12:]
        convo = "\n".join(("User: " if str(x.get("role")) == "you" else f"{name}: ") + str(x.get("text") or "") for x in window)
        if convo: blocks.append("[CONVERSATION SO FAR]\n" + convo)
        blocks.append(f"[USER]\n{question[:6000]}\n\nReply as {name}.")
        payload = {"system_prompt": inject_skills(self._db, (recipe.system_prompt or "").strip() or f"You are {name}, a helpful assistant.", recipe_id), "user_prompt": "\n\n".join(blocks), "history": window, "recipe_id": recipe_id, "recipe_revision": str(recipe.last_modified), "context_ids": context_ids, "context_titles": context_titles, "grounding": grounding_echo, "workbench_id": str(workbench_id or "")}
        self._broadcast(broadcast, "running", kind="recipe", ref=recipe_id, name=name)
        result = await asyncio.to_thread(
            self._through_door, principal, "chat.turn", "recipe-chat-result", recipe, payload,
            lambda value, on: self._chat_projection(value, recipe, payload, on),
        )
        self._broadcast(broadcast, "ready", kind="recipe", ref=recipe_id, name=name)
        return result

    def _through_door(self, principal: Principal, job: str, kind: str, recipe: Any, payload: dict[str, Any],
                      project: Callable[[Any, Any], dict[str, Any]]) -> dict[str, Any]:
        """One recipe job through the engine door; its result is staged as
        ``kind`` and published once the receipt says it succeeded."""
        from . import engine_door

        current: list[Any] = []

        def prepare(body: Any, on: Any) -> Any:
            current[:] = [on]
            return body

        try:
            answer = engine_door.run(
                self._broker, principal, job, payload, subject=("recipe", str(recipe.id)),
                adapter=_RecipeResultAdapter(), stage=(kind, lambda value: project(value, current[0])),
                prepare=prepare,
            )
        except engine_door.EngineDoorError as exc:
            raise ServiceError(
                "inference_route_failed", exc.detail or "No assigned model completed this recipe",
                context={"receipt": exc.operation_id, "reason": engine_door.reason(exc), "outcome": exc.outcome or exc.code,
                         "status": 409 if exc.code == "no_engine" else 502},
            ) from exc
        if answer.published is None:
            raise ServiceError("projection_not_published", "Recipe result is awaiting receipt reconciliation",
                               context={"invocation_id": answer.invocation_id, "status": 409})
        return dict(answer.published)

    def _migrate_subject_pointers(self, principal: Principal) -> None:
        self._broker.inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)

    def _refuse_post_marker_profile_pointer(
        self, principal: Principal, fields: dict[str, Any]
    ) -> None:
        """Leave migrated assignments immutable to retired Recipe pointers."""
        if "profile_id" not in fields:
            return
        from .inference_adoption_service import RECIPE_WORKBENCH_MIGRATION_FAMILY
        from .inference_assignment_service import InferenceAssignmentService

        marker = InferenceAssignmentService(self._db).migration_marker(
            principal, family=RECIPE_WORKBENCH_MIGRATION_FAMILY
        )
        if marker is None:
            return
        raise ValidationError(
            "Legacy Recipe profile selectors are unavailable after assignment migration.",
            code="inference_legacy_selector_retired",
            context={"retired_fields": ["profile_id"]},
        )

    def _refuse_missing_legacy_profile(self, recipe: Any) -> None:
        """Fence a post-cutover dangling compatibility selection before routing.

        Exact canonical assignments are the sole route authority.  A saved
        retired pointer without a corresponding legacy or canonical profile is
        not a candidate route, but it remains owner-visible and must block
        inherited/global routing until repaired.
        """
        profile_id = str(getattr(recipe, "profile_id", "") or "").strip()
        if not profile_id:
            return
        with self._db._connection() as conn:
            canonical = conn.execute(
                "SELECT 1 FROM model_profile_revisions WHERE profile_id=? LIMIT 1",
                (profile_id,),
            ).fetchone()
            legacy = conn.execute(
                "SELECT 1 FROM profiles WHERE id=? AND deleted=0", (profile_id,)
            ).fetchone()
        if canonical is not None or legacy is not None:
            return
        from ..inference_targets import InferenceTarget, target_refusal
        unavailable = InferenceTarget(
            id=profile_id,
            name=profile_id,
            kind="unsupported",
            boundary="unknown",
            owner="unknown",
            transport="none",
            profile_id=profile_id,
            engine="unknown",
            model="",
            context_limit=16_384,
            readiness_state="unavailable",
            readiness_reason=f"Destination '{profile_id}' does not exist on this device",
        )
        refusal = target_refusal(unavailable)
        raise ServiceError(
            "target_unavailable",
            str(refusal["error"]),
            context={"status": 409, **refusal},
        )

    @staticmethod
    def _reject_retired_selector(value: Any) -> None:
        if str(value or "").strip():
            raise ValidationError("Legacy model selectors are unavailable after assignment migration.", code="inference_legacy_selector_retired")

    def _recipe(self, recipe_id: str) -> Any:
        record = self._db.recipes.get(recipe_id)
        if record is None: raise NotFound("Agent", recipe_id)
        return record

    @staticmethod
    def _broadcast(broadcast: Broadcast | None, state: str, **frame: Any) -> None:
        if broadcast: broadcast(state, **frame)

    def _route_summary(self, engine: Any) -> dict[str, Any]:
        # Target identity comes from the immutable deployment revision the
        # job ran on, never from the current profile/assignment configuration.
        revision = self._db.deployment_revisions.get(str(engine.revision))
        profile_id = str(engine.profile or getattr(revision, "destination_id", "") or "").removeprefix("legacy-")
        target_id = str(getattr(revision, "destination_id", "") or profile_id)
        return {"id": profile_id, "profile_id": profile_id, "target_id": target_id, "engine": "routed", "boundary": str(getattr(revision, "boundary", "") or ""), "deployment_revision_id": str(engine.revision)}

    def _run_projection(self, result: Any, recipe: Any, sources: list[dict[str, str]], user: str, engine: Any) -> dict[str, Any]:
        value = dict(result) if isinstance(result, dict) else {"output": str(result)}
        target = self._route_summary(engine); output = str(value["output"]); artifact_id = "artifact_" + uuid.uuid4().hex[:12]
        model = str(value.get("model") or target["profile_id"])
        return {"recipe_id": recipe.id, "name": f"{recipe.name or recipe.id}: {user}" if user else (recipe.name or recipe.id), "output": output, "provider": str(value.get("provider") or target["engine"]), "profile_id": target["profile_id"], "inference_target": target, "actual_placement": {"target_id": target["target_id"], "boundary": target["boundary"], "deployment_revision_id": target["deployment_revision_id"], "model": model}, "sources": sources, "artifact_id": artifact_id, "created_at": utc_now_iso(), "placement": {"source": "owner_assignment", "assignment_id": engine.assignment}}

    def _chat_projection(self, result: Any, recipe: Any, payload: dict[str, Any], engine: Any) -> dict[str, Any]:
        value = dict(result) if isinstance(result, dict) else {"output": str(result)}; target = self._route_summary(engine)
        model = str(value.get("model") or target["profile_id"])
        output = {"recipe_id": recipe.id, "output": str(value.get("output") or value.get("summary") or ""), "provider": str(value.get("provider") or target["engine"]), "profile_id": target["profile_id"], "inference_target": target, "actual_placement": {"target_id": target["target_id"], "boundary": target["boundary"], "deployment_revision_id": target["deployment_revision_id"], "model": model}, "egress": {"scope": target["boundary"]}, "model": model, "context_ids": payload["context_ids"], "context_titles": payload["context_titles"], "placement": {"source": "owner_assignment", "assignment_id": engine.assignment}}
        if payload["grounding"] is not None: output["grounding"] = payload["grounding"]
        return output

    def keep(self, principal: Principal, recipe_id: str, *, output: str, input: str = "", sources: list[dict[str, str]] | None = None) -> dict[str, Any]:
        from .support import _persist_run_artifact
        if not str(output or "").strip(): raise ValidationError("output is required")
        recipe = self._recipe(recipe_id)
        artifact_id = _persist_run_artifact(db=self._db, kind="recipe", name=recipe.name or recipe_id, user_input=str(input or ""), output=str(output), sources=sources or [{"source_type": "recipe", "source_ref": recipe_id}])
        if not artifact_id: raise ServiceError("artifact_persist_failed", "keep failed")
        return {"artifact_id": artifact_id}

    def _kb_block(self, kb_id: str) -> str:
        from .support import _context_material
        kb = self._db.kbs.get(kb_id)
        if kb is None: return ""
        texts = []
        for member in list(getattr(kb, "member_ids", None) or [])[:12]:
            bare = member.split(":", 1)[1] if ":" in member else member
            for kind in ("note", "artifact", "meeting"):
                _, text = _context_material(self._db, bare, kind, "")
                if text: texts.append(text[:1200]); break
        return f"[KB: {kb.name or kb_id}]\n" + "\n\n".join(texts) if texts else f"[KB: {kb.name or kb_id} — no hydrated members]"

    def _payload(self, principal: Principal, recipe: Any) -> dict[str, Any]:
        from .support import capability_descriptor
        row = recipe.to_dict()
        row["capability"] = capability_descriptor(kind="persona", name=recipe.name or recipe.id, supported_placements=["assignment:recipe"], action_label=f"Ask {recipe.name or 'Agent'}")
        row["placement"] = {"source": "canonical_assignment", "subject_kind": "recipe", "subject_id": recipe.id}
        return row

    @staticmethod
    def _recipe_fields(body: dict[str, Any], existing: Any = None) -> dict[str, Any]:
        value = lambda key, default: body[key] if key in body else default
        return {"name": str(value("name", existing.name if existing else "")), "avatar": str(value("avatar", existing.avatar if existing else "")), "role": str(value("role", existing.role if existing else "")), "system_prompt": str(value("system_prompt", existing.system_prompt if existing else "")), "user_template": str(value("user_template", existing.user_template if existing else "")), "tools": list(value("tools", existing.tools if existing else [])), "kb_id": value("kb_id", existing.kb_id if existing else None) or None, "profile_id": value("profile_id", existing.profile_id if existing else None) or None, "manual_context": str(value("manual_context", existing.manual_context if existing else "")), "use_zone_context": bool(value("use_zone_context", existing.use_zone_context if existing else False)), "kind": str(value("kind", existing.kind if existing else ""))}
