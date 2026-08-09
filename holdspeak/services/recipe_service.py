"""Transport-neutral recipe (persona) operations (HS-122-03)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import asyncio
import uuid
from collections.abc import Callable
from typing import Any

from ..db.core import Database
from ..principals import Principal
from holdspeak.services.errors import NotFound, ServiceError, ValidationError


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


Broadcast = Callable[..., None]


@observe_service
class RecipeService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def list_recipes(self, principal: Principal) -> list[dict[str, Any]]:
        return [self._payload(recipe) for recipe in self._db.recipes.list()]

    def get_recipe(self, principal: Principal, recipe_id: str) -> dict[str, Any]:
        recipe = self._db.recipes.get(recipe_id)
        if recipe is None:
            raise NotFound("Agent", recipe_id)
        return self._payload(recipe)

    def create_recipe(
        self, principal: Principal, *, name: str = "", recipe_id: str | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        if not str(name or "").strip():
            raise ValidationError("Agent name is required")
        fields["name"] = name
        recipe = self._db.recipes.upsert(
            recipe_id=str(recipe_id or fields.pop("id", None) or _new_id("recipe")),
            **self._recipe_fields(fields),
        )
        return self._payload(recipe)

    def update_recipe(
        self, principal: Principal, recipe_id: str, **fields: Any
    ) -> dict[str, Any]:
        existing = self._db.recipes.get(recipe_id)
        if existing is None:
            raise NotFound("Agent", recipe_id)
        recipe = self._db.recipes.upsert(
            recipe_id=recipe_id, **self._recipe_fields(fields, existing)
        )
        return self._payload(recipe)

    def delete_recipe(self, principal: Principal, recipe_id: str) -> bool:
        if not self._db.recipes.delete(recipe_id):
            raise NotFound("Agent", recipe_id)
        return True

    async def run(
        self,
        principal: Principal,
        recipe_id: str,
        *,
        input: str = "",
        variables: dict[str, Any] | None = None,
        inference_target_id: str | None = None,
        requested_placement: str | None = None,
        max_tokens: Any = None,
        temperature: Any = None,
        source_ref: str | None = None,
        source_type: Any = None,
        grounding_refs: Any = None,
        grounding_revisions: Any = None,
        source_revision: Any = None,
        deadline_at: Any = None,
        initiator: Any = None,
        broadcast: Broadcast | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        from .support import RunLifecycle, _persist_run_artifact, _render_user_prompt, canonical_source_type, inject_skills

        recipe = self._db.recipes.get(recipe_id)
        if recipe is None:
            raise NotFound("Agent", recipe_id)
        valid_variables = variables if isinstance(variables, dict) else {}
        body: dict[str, Any] = {
            "input": input,
            "variables": valid_variables,
            "inference_target_id": inference_target_id,
            "requested_placement": requested_placement,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "source_ref": source_ref,
            "source_type": source_type,
            "grounding_refs": grounding_refs or [],
            "grounding_revisions": grounding_revisions,
            "source_revision": source_revision,
            "deadline_at": deadline_at,
            "initiator": initiator,
            **extra,
        }
        lifecycle: RunLifecycle | None = None
        try:
            lifecycle = RunLifecycle.begin(
                self._db,
                definition_ref=f"persona:{recipe_id}",
                body=body,
                default_placement=f"profile:{recipe.profile_id}" if recipe.profile_id else "this_machine",
                principal=principal,
                definition_revision=recipe.last_modified or recipe.created_at or "unversioned",
            )
            user_input = str(input or "")
            user_prompt = _render_user_prompt(recipe.user_template, valid_variables, user_input)
            if not user_prompt.strip():
                invocation = lifecycle.fail(
                    "nothing to run: provide `input` or a Agent input template", state="empty"
                )
                raise ServiceError("empty_input", "nothing to run: provide `input` or a Agent input template", context={"invocation": invocation, "invocation_id": lifecycle.invocation_id})

            from ..inference_targets import (
                build_intel_for_target, resolve_inference_target, target_refusal, target_runtime_error,
            )
            from ..intel.models import MeetingIntelError

            requested_target_id = str(
                inference_target_id or requested_placement or recipe.profile_id or "this_machine"
            ).strip()
            target = resolve_inference_target(self._db, requested_target_id)
            ran_profile_id = target.profile_id
            lifecycle.start_attempt(destination=target.id, target=target)
            if not target.ready:
                invocation = lifecycle.fail(target.readiness_reason, state="unavailable")
                raise ServiceError("target_unavailable", target.readiness_reason, context={**target_refusal(target), "recipe_id": recipe_id, "invocation": invocation, "invocation_id": lifecycle.invocation_id})
            intel = build_intel_for_target(target, self._db)
            self._broadcast(broadcast, "running", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id)
            try:
                output = await asyncio.to_thread(
                    intel.run_prompt,
                    system_prompt=inject_skills(self._db, recipe.system_prompt, recipe_id),
                    user_prompt=user_prompt,
                    temperature=float(temperature) if temperature is not None else None,
                    max_tokens=int(max_tokens) if max_tokens is not None else None,
                )
            except MeetingIntelError as exc:
                error = target_runtime_error(target, exc)
                self._broadcast(broadcast, "error", kind="recipe", ref=recipe_id,
                                name=recipe.name or recipe_id, error=error)
                invocation = lifecycle.fail(error, provider=getattr(intel, "active_provider", None))
                raise ServiceError("inference_failed", error, context={"recipe_id": recipe_id, "invocation": invocation, "invocation_id": lifecycle.invocation_id}) from exc
            cancelled = lifecycle.cancelled()
            if cancelled is not None:
                self._broadcast(broadcast, "error", kind="recipe", ref=recipe_id,
                                name=recipe.name or recipe_id, error="cancelled")
                raise ServiceError("cancelled", "cancelled", context={"recipe_id": recipe_id, "invocation": cancelled, "invocation_id": lifecycle.invocation_id, "operation_id": lifecycle.operation_id})
            if not str(output or "").strip():
                error = "Agent returned no output; your input is retained for Retry."
                self._broadcast(broadcast, "error", kind="recipe", ref=recipe_id,
                                name=recipe.name or recipe_id, error=error)
                invocation = lifecycle.fail(error, state="empty", provider=getattr(intel, "active_provider", None))
                raise ServiceError("empty_output", error, context={"recipe_id": recipe_id, "invocation": invocation, "invocation_id": lifecycle.invocation_id})
            self._broadcast(broadcast, "ready", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id)

            sources: list[dict[str, str]] = [{"source_type": "recipe", "source_ref": recipe_id}]
            provided_ref = str(source_ref or "").strip()
            if provided_ref:
                input_type = canonical_source_type(source_type) if source_type else "input"
                sources.append({"source_type": input_type, "source_ref": provided_ref})
            sources.extend(lifecycle.lineage())
            artifact_id = _persist_run_artifact(
                db=self._db, kind="recipe", name=recipe.name or recipe_id, user_input=user_input,
                output=output, sources=sources,
            )
            if not artifact_id:
                invocation = lifecycle.fail("The result could not be kept as an Artifact.")
                raise ServiceError("artifact_persist_failed", invocation["error"], context={"recipe_id": recipe_id, "invocation": invocation, "invocation_id": lifecycle.invocation_id})
            invocation = lifecycle.succeed(
                artifact_id, provider=getattr(intel, "active_provider", None), model=target.model,
            )
            return {
                "recipe_id": recipe_id, "output": output, "provider": intel.active_provider,
                "profile_id": ran_profile_id, "inference_target": target.to_dict(),
                "actual_placement": invocation["attempts"][-1]["actual_placement"],
                "sources": sources, "artifact_id": artifact_id, "result_ref": f"artifact:{artifact_id}",
                "invocation_id": lifecycle.invocation_id, "operation_id": lifecycle.operation_id,
                "correlation_id": lifecycle.invocation_id, "invocation": invocation,
            }
        except ServiceError:
            raise
        except Exception as exc:
            if lifecycle is not None:
                try:
                    lifecycle.fail(str(exc))
                except Exception:
                    pass
            raise

    async def chat(
        self, principal: Principal, recipe_id: str, *, question: str,
        history: list[Any] | None = None, grounding: Any = None,
        inference_target_id: str | None = None, egress_context: Any = None,
        broadcast: Broadcast | None = None, default_model: str = "",
    ) -> dict[str, Any]:
        question = str(question or "").strip()
        if not question:
            raise ValidationError("question is required")
        recipe = self._db.recipes.get(recipe_id)
        if recipe is None:
            raise NotFound("Agent", recipe_id)
        from ..inference_targets import (
            build_intel_for_target, resolve_inference_target, target_refusal, target_runtime_error,
        )
        from ..intel.models import MeetingIntelError
        from .support import _GROUNDING_EXPANDS, _GROUNDING_MAX_REFS, _hydrate_grounding, _run_egress, inject_skills

        name = recipe.name or recipe_id
        blocks: list[str] = []
        ctx_parts: list[str] = []
        if (recipe.manual_context or "").strip():
            ctx_parts.append(recipe.manual_context)
        if recipe.kb_id:
            kb_text = self._kb_block(recipe.kb_id)
            if kb_text:
                ctx_parts.append(kb_text)
        if ctx_parts:
            blocks.append("[CONTEXT]\n" + "\n\n".join(ctx_parts))

        context_ids: list[str] = []
        context_titles: list[str] = []
        grounding_echo = None
        if grounding is not None:
            if not isinstance(grounding, dict):
                raise ValidationError("grounding must be an object")
            raw_m, raw_a = grounding.get("meeting_ids"), grounding.get("artifact_ids")
            meeting_ids = [str(x).strip() for x in raw_m if str(x).strip()] if isinstance(raw_m, list) else []
            artifact_ids = [str(x).strip() for x in raw_a if str(x).strip()] if isinstance(raw_a, list) else []
            expand = str(grounding.get("expand") or "summary").strip() or "summary"
            if expand not in _GROUNDING_EXPANDS:
                raise ValidationError(f"expand {expand!r} is not one of {list(_GROUNDING_EXPANDS)}")
            if len(meeting_ids) + len(artifact_ids) > _GROUNDING_MAX_REFS:
                raise ValidationError(f"grounding is capped at {_GROUNDING_MAX_REFS} refs")
            g_blocks, g_ids, g_titles, unknown = _hydrate_grounding(
                self._db, meeting_ids, artifact_ids, expand
            )
            if unknown:
                raise ServiceError("grounding_not_found", "grounding ids not on this hub", context={"unknown_ids": unknown})
            if g_blocks:
                blocks.append("[GROUNDING]\n" + "\n\n".join(g_blocks))
            context_ids += g_ids
            context_titles += g_titles
            grounding_echo = {"meeting_ids": meeting_ids, "artifact_ids": artifact_ids,
                              "expand": expand, "titles": g_titles}

        window = [item for item in (history or []) if isinstance(item, dict)][-12:]
        if window:
            convo = "\n".join(
                ("User: " if str(item.get("role")) == "you" else f"{name}: ")
                + str(item.get("text") or "") for item in window
            )
            blocks.append("[CONVERSATION SO FAR]\n" + convo)
        blocks.append("[USER]\n" + question[:6000] + f"\n\nReply as {name}.")

        target = resolve_inference_target(
            self._db, inference_target_id or recipe.profile_id or "this_machine"
        )
        if not target.ready:
            raise ServiceError("target_unavailable", target.readiness_reason, context=target_refusal(target))
        ran_profile_id = target.profile_id
        profile = self._db.profiles.get(ran_profile_id) if ran_profile_id else None
        intel = build_intel_for_target(target, self._db)
        raw_system = (recipe.system_prompt or "").strip() or f"You are {name}, a helpful assistant."
        system_prompt = inject_skills(self._db, raw_system, recipe_id)
        self._broadcast(broadcast, "running", kind="recipe", ref=recipe_id, name=name)
        try:
            output = await asyncio.to_thread(
                intel.run_prompt, system_prompt=system_prompt, user_prompt="\n\n".join(blocks)
            )
        except MeetingIntelError as exc:
            error = target_runtime_error(target, exc)
            self._broadcast(broadcast, "error", kind="recipe", ref=recipe_id, name=name, error=error)
            raise ServiceError("inference_failed", error, context={"recipe_id": recipe_id, "inference_target": target.to_dict(), "alternate_target_id": "this_machine"}) from exc
        self._broadcast(broadcast, "ready", kind="recipe", ref=recipe_id, name=name)
        egress, model = _run_egress(profile, intel, default_model=default_model)
        payload: dict[str, Any] = {
            "recipe_id": recipe_id, "output": output, "provider": intel.active_provider,
            "profile_id": ran_profile_id, "inference_target": target.to_dict(),
            "actual_placement": target.placement_receipt(provider=intel.active_provider, model=model),
            "egress": egress, "model": model, "context_ids": context_ids,
            "context_titles": context_titles,
        }
        if grounding_echo is not None:
            payload["grounding"] = grounding_echo
        return payload

    def keep(
        self, principal: Principal, recipe_id: str, *, output: str,
        input: str = "", sources: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        from .support import _persist_run_artifact

        if not str(output or "").strip():
            raise ValidationError("output is required")
        recipe = self._db.recipes.get(recipe_id)
        if recipe is None:
            raise NotFound("Agent", recipe_id)
        artifact_id = _persist_run_artifact(
            db=self._db, kind="recipe", name=recipe.name or recipe_id, user_input=str(input or ""),
            output=str(output), sources=sources or [{"source_type": "recipe", "source_ref": recipe_id}],
        )
        if not artifact_id:
            raise ServiceError("artifact_persist_failed", "keep failed")
        return {"artifact_id": artifact_id}

    @staticmethod
    def _broadcast(broadcast: Broadcast | None, state: str, **frame: Any) -> None:
        if broadcast is not None:
            broadcast(state, **frame)

    def _payload(self, recipe: Any) -> dict[str, Any]:
        from .support import capability_descriptor
        from ..inference_targets import resolve_placement

        row = recipe.to_dict()
        row["capability"] = capability_descriptor(
            kind="persona", name=recipe.name or recipe.id,
            supported_placements=[f"profile:{recipe.profile_id}"] if recipe.profile_id else ["this_machine"],
            action_label=f"Ask {recipe.name or 'Agent'}",
        )
        # HS-130-01: every placement API response carries {effective_target_id,
        # source}. A bare recipe resolves through the Agent default → global;
        # an unset recipe reports the source it inherited from, never a bare
        # target with no provenance.
        row["placement"] = resolve_placement(
            self._db, agent=recipe.profile_id
        ).placement_dict()
        return row

    @staticmethod
    def _recipe_fields(body: dict[str, Any], existing: Any = None) -> dict[str, Any]:
        def pick(key: str, default: Any) -> Any:
            return body[key] if key in body else default
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "avatar": str(pick("avatar", existing.avatar if existing else "")),
            "role": str(pick("role", existing.role if existing else "")),
            "system_prompt": str(pick("system_prompt", existing.system_prompt if existing else "")),
            "user_template": str(pick("user_template", existing.user_template if existing else "")),
            "tools": list(pick("tools", existing.tools if existing else [])),
            "kb_id": (pick("kb_id", existing.kb_id if existing else None) or None),
            "profile_id": (pick("profile_id", existing.profile_id if existing else None) or None),
            "manual_context": str(pick("manual_context", existing.manual_context if existing else "")),
            "use_zone_context": bool(pick("use_zone_context", existing.use_zone_context if existing else False)),
        }

    def _kb_block(self, kb_id: str) -> str:
        from .support import _context_material
        kb = self._db.kbs.get(kb_id)
        if kb is None:
            return ""
        name = kb.name or kb_id
        texts: list[str] = []
        for member_id in list(getattr(kb, "member_ids", None) or [])[:12]:
            bare = member_id.split(":", 1)[1] if ":" in member_id else member_id
            for kind in ("note", "artifact", "meeting"):
                _, text = _context_material(self._db, bare, kind, "")
                if text:
                    texts.append(text[:1200])
                    break
        if texts:
            return f"[KB: {name}]\n" + "\n\n".join(texts)
        return f"[KB: {name} — no hydrated members]"
