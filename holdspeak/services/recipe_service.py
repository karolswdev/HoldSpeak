"""Transport-neutral Recipe operations on the routed inference waist."""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service
from ..db.core import Database
from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from .inference_outcomes import map_inference_outcome


Broadcast = Callable[..., None]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


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
        self._runner = broker.inference_runner

    def list_recipes(self, principal: Principal) -> list[dict[str, Any]]:
        return [self._payload(principal, record) for record in self._db.recipes.list()]

    def get_recipe(self, principal: Principal, recipe_id: str) -> dict[str, Any]:
        return self._payload(principal, self._recipe(recipe_id))

    def create_recipe(self, principal: Principal, *, name: str = "", recipe_id: str | None = None, **fields: Any) -> dict[str, Any]:
        if not str(name).strip():
            raise ValidationError("Agent name is required")
        fields["name"] = name
        record = self._db.recipes.upsert(
            recipe_id=str(recipe_id or fields.pop("id", None) or _new_id("recipe")),
            **self._recipe_fields(fields),
        )
        if "profile_id" in fields:
            self._write_legacy_profile_compatibility(principal, record.id, fields["profile_id"])
        return self._payload(principal, record)

    def update_recipe(self, principal: Principal, recipe_id: str, **fields: Any) -> dict[str, Any]:
        existing = self._recipe(recipe_id)
        if "profile_id" in fields:
            self._write_legacy_profile_compatibility(principal, recipe_id, fields["profile_id"])
        return self._payload(principal, self._db.recipes.upsert(
            recipe_id=recipe_id, **self._recipe_fields(fields, existing)
        ))

    def delete_recipe(self, principal: Principal, recipe_id: str) -> bool:
        if not self._db.recipes.delete(recipe_id):
            raise NotFound("Agent", recipe_id)
        return True

    async def run(self, principal: Principal, recipe_id: str, *, input: str = "", variables: dict[str, Any] | None = None, inference_target_id: str | None = None, requested_placement: str | None = None, workbench_id: str | None = None, max_tokens: Any = None, temperature: Any = None, source_ref: str | None = None, source_type: Any = None, deadline_at: Any = None, broadcast: Broadcast | None = None, **extra: Any) -> dict[str, Any]:
        from .support import _render_user_prompt, canonical_source_type, inject_skills
        self._migrate_subject_pointers(principal)
        self._reject_retired_selector(inference_target_id or requested_placement)
        recipe = self._recipe(recipe_id)
        variables = variables if isinstance(variables, dict) else {}
        user = _render_user_prompt(recipe.user_template, variables, str(input or ""))
        if not user.strip():
            raise ServiceError("empty_input", "nothing to run: provide `input` or a Agent input template")
        sources = [{"source_type": "recipe", "source_ref": recipe_id}]
        if str(source_ref or "").strip():
            sources.append({"source_type": canonical_source_type(source_type) if source_type else "input", "source_ref": str(source_ref)})
        payload = {
            "system_prompt": inject_skills(self._db, recipe.system_prompt, recipe_id),
            "user_prompt": user, "variables": variables, "recipe_id": recipe_id,
            "recipe_revision": str(recipe.last_modified),
            "temperature": float(temperature) if temperature is not None else None,
            "max_tokens": int(max_tokens) if max_tokens is not None else None,
            "workbench_id": str(workbench_id or ""),
        }
        invocation_id = "recipe_run_" + uuid.uuid4().hex
        self._broadcast(broadcast, "running", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id)
        admitted = await asyncio.to_thread(
            self._broker.inference_adoption_service.admit, principal,
            command_id=f"admit-{invocation_id}", capability_id="recipe.run",
            operation_id=invocation_id, payload=payload, subject_kind="recipe", subject_id=recipe_id,
            reserved_output_tokens=int(max_tokens) if max_tokens is not None else 512,
        )
        routed = await asyncio.to_thread(
            self._broker.inference_adoption_service.execute, principal,
            execution_id=admitted["execution"]["id"], adapter=_RecipeResultAdapter(),
            publish=self._publisher("recipe-run", recipe, payload, sources, admitted["route_plan"]),
        )
        if routed["outcome"] != "succeeded":
            self._broadcast(broadcast, "error", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id, error=routed["outcome"])
            raise ServiceError("inference_route_failed", "No assigned model completed this recipe", context={"receipt": routed["receipt"], "status": 409})
        winner = str(routed["winning_reservation"]["child_invocation_id"])
        result = self._broker.projection_stager.finalize(winner)
        if result is None:
            raise ServiceError("projection_not_published", "Recipe result is awaiting receipt reconciliation", context={"invocation_id": winner, "status": 409})
        result = dict(result)
        result["route_execution_receipt"] = routed["receipt"]
        self._broadcast(broadcast, "ready", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id)
        return result

    async def chat(self, principal: Principal, recipe_id: str, *, question: str, history: list[Any] | None = None, grounding: Any = None, inference_target_id: str | None = None, workbench_id: str | None = None, egress_context: Any = None, broadcast: Broadcast | None = None) -> dict[str, Any]:
        from .support import _GROUNDING_EXPANDS, _GROUNDING_MAX_REFS, _hydrate_grounding, inject_skills
        self._migrate_subject_pointers(principal)
        self._reject_retired_selector(inference_target_id)
        question = str(question or "").strip()
        if not question:
            raise ValidationError("question is required")
        recipe = self._recipe(recipe_id)
        name = recipe.name or recipe_id
        blocks, context = [], []
        if (recipe.manual_context or "").strip(): context.append(recipe.manual_context)
        if recipe.kb_id: context.append(self._kb_block(recipe.kb_id))
        if context: blocks.append("[CONTEXT]\n" + "\n\n".join(x for x in context if x))
        context_ids: list[str] = []
        context_titles: list[str] = []
        grounding_echo = None
        if grounding is not None:
            if not isinstance(grounding, dict): raise ValidationError("grounding must be an object")
            mids = [str(x).strip() for x in grounding.get("meeting_ids", []) if str(x).strip()] if isinstance(grounding.get("meeting_ids"), list) else []
            aids = [str(x).strip() for x in grounding.get("artifact_ids", []) if str(x).strip()] if isinstance(grounding.get("artifact_ids"), list) else []
            expand = str(grounding.get("expand") or "summary").strip() or "summary"
            if expand not in _GROUNDING_EXPANDS: raise ValidationError(f"expand {expand!r} is not one of {list(_GROUNDING_EXPANDS)}")
            if len(mids) + len(aids) > _GROUNDING_MAX_REFS: raise ValidationError(f"grounding is capped at {_GROUNDING_MAX_REFS} refs")
            gblocks, gids, gtitles, unknown = _hydrate_grounding(self._db, mids, aids, expand)
            if unknown: raise ServiceError("grounding_not_found", "grounding ids not on this hub", context={"unknown_ids": unknown})
            if gblocks: blocks.append("[GROUNDING]\n" + "\n\n".join(gblocks))
            context_ids += gids; context_titles += gtitles
            grounding_echo = {"meeting_ids": mids, "artifact_ids": aids, "expand": expand, "titles": gtitles}
        window = [x for x in (history or []) if isinstance(x, dict)][-12:]
        convo = "\n".join(("User: " if str(x.get("role")) == "you" else f"{name}: ") + str(x.get("text") or "") for x in window)
        if convo: blocks.append("[CONVERSATION SO FAR]\n" + convo)
        blocks.append(f"[USER]\n{question[:6000]}\n\nReply as {name}.")
        payload = {"system_prompt": inject_skills(self._db, (recipe.system_prompt or "").strip() or f"You are {name}, a helpful assistant.", recipe_id), "user_prompt": "\n\n".join(blocks), "history": window, "recipe_id": recipe_id, "recipe_revision": str(recipe.last_modified), "context_ids": context_ids, "context_titles": context_titles, "grounding": grounding_echo, "workbench_id": str(workbench_id or "")}
        invocation_id = "recipe_chat_" + uuid.uuid4().hex
        self._broadcast(broadcast, "running", kind="recipe", ref=recipe_id, name=name)
        # Qualification is a zero-write probe of the *agent.tool_turn* route.
        # A Recipe's persisted `tools` list is intentionally never consulted.
        qualified = await asyncio.to_thread(
            self._broker.inference_adoption_service.next_run_summary,
            principal, capability_id="agent.tool_turn", subject_kind="recipe", subject_id=recipe_id,
        )
        if qualified["status"] == "ready":
            from .agent_turn_service import AgentTurnService
            agent = AgentTurnService.compose(self._broker)
            turn = await asyncio.to_thread(
                agent.run_recipe,
                principal, command_id=f"agent-turn-{invocation_id}", turn_id=f"turn-{invocation_id}",
                recipe_id=recipe_id,
                messages=[{"role": "system", "content": payload["system_prompt"]}, {"role": "user", "content": payload["user_prompt"]}],
                deadline_at=time.time() + 20,
                publish=lambda route: self._publisher("recipe-chat-result", recipe, payload, [], route),
            )
            routed = {
                "outcome": turn["outcome"], "receipt": turn["receipt"],
                "winning_reservation": turn["winning_reservation"],
            }
        else:
            admitted = await asyncio.to_thread(self._broker.inference_adoption_service.admit, principal, command_id=f"admit-{invocation_id}", capability_id="recipe.chat", operation_id=invocation_id, payload=payload, subject_kind="recipe", subject_id=recipe_id, reserved_output_tokens=512)
            routed = await asyncio.to_thread(self._broker.inference_adoption_service.execute, principal, execution_id=admitted["execution"]["id"], adapter=_RecipeResultAdapter(), publish=self._publisher("recipe-chat-result", recipe, payload, [], admitted["route_plan"]))
        if routed["outcome"] != "succeeded":
            raise ServiceError("inference_route_failed", "No assigned model completed this recipe", context={"receipt": routed["receipt"], "status": 409})
        winner = str(routed["winning_reservation"]["child_invocation_id"])
        result = self._broker.projection_stager.finalize(winner)
        if result is None: raise ServiceError("projection_not_published", "Recipe chat is awaiting receipt reconciliation", context={"invocation_id": winner, "status": 409})
        result = dict(result); result["route_execution_receipt"] = routed["receipt"]
        self._broadcast(broadcast, "ready", kind="recipe", ref=recipe_id, name=name)
        return result

    def _publisher(self, kind: str, recipe: Any, payload: dict[str, Any], sources: list[dict[str, str]], route: dict[str, Any]) -> Callable[[Any, dict[str, Any]], str]:
        def publish(output: Any, reservation: dict[str, Any]) -> str:
            ordinal = int(reservation["route_leg_ordinal"])
            projection = self._run_projection(output, recipe, sources, payload["user_prompt"], route, ordinal) if kind == "recipe-run" else self._chat_projection(output, recipe, payload, route, ordinal)
            digest = "sha256:" + hashlib.sha256(json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
            return self._broker.projection_stager.stage(str(reservation["child_invocation_id"]), kind, projection, result_sha256=digest, receipt_result_ref=f"inference-result:{reservation['child_invocation_id']}/{digest}").result_ref
        return publish

    def _migrate_subject_pointers(self, principal: Principal) -> None:
        self._broker.inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)

    def _write_legacy_profile_compatibility(self, principal: Principal, recipe_id: str, value: Any) -> None:
        from .inference_adoption_service import RECIPE_WORKBENCH_MIGRATION_FAMILY
        from .inference_assignment_service import InferenceAssignmentService
        assignments = InferenceAssignmentService(self._db)
        if assignments.migration_marker(principal, family=RECIPE_WORKBENCH_MIGRATION_FAMILY) is None:
            return
        profile_id = str(value or "").strip()
        for capability_id in ("recipe.run", "recipe.chat"):
            scope = {"kind": "subject", "subject_kind": "recipe", "subject_id": recipe_id, "capability_id": capability_id}
            try:
                current = assignments.get_assignment(principal, scope)
            except NotFound:
                current = None
            if not profile_id:
                if current is not None:
                    assignments.clear_assignment(principal, {"command_id": f"recipe-profile-clear-{recipe_id}-{capability_id}", "expected_revision": current["revision"], "scope": scope, "capability_id": capability_id, "subject_kind": "recipe", "subject_id": recipe_id})
                continue
            entry_profile = profile_id
            with self._db._connection() as conn:
                revision = conn.execute("SELECT MAX(revision) FROM model_profile_revisions WHERE profile_id=?", (profile_id,)).fetchone()[0]
                legacy = conn.execute("SELECT 1 FROM profiles WHERE id=? AND deleted=0", (profile_id,)).fetchone()
            if not revision and legacy is not None:
                entry_profile = f"legacy-{profile_id}"
            assignments.set_assignment(principal, {"command_id": f"recipe-profile-write-{recipe_id}-{capability_id}", "expected_revision": 0 if current is None else current["revision"], "scope": scope, "entries": [{"profile_id": entry_profile}]})

    @staticmethod
    def _reject_retired_selector(value: Any) -> None:
        if str(value or "").strip():
            raise ValidationError("Legacy model selectors are unavailable after assignment migration.", code="inference_legacy_selector_retired")

    def _recipe(self, recipe_id: str) -> Any:
        record = self._db.recipes.get(recipe_id)
        if record is None: raise NotFound("Agent", recipe_id)
        return record

    _outcome_error = staticmethod(map_inference_outcome)

    @staticmethod
    def _broadcast(broadcast: Broadcast | None, state: str, **frame: Any) -> None:
        if broadcast: broadcast(state, **frame)

    @staticmethod
    def _route_summary(route: dict[str, Any], ordinal: int) -> dict[str, Any]:
        entry = dict(route["entries"][ordinal - 1])
        profile_id = str(entry["profile_id"]).removeprefix("legacy-")
        return {"id": profile_id, "profile_id": profile_id, "engine": "routed", "boundary": entry["boundary"], "deployment_revision_id": entry["deployment_revision_id"]}

    def _run_projection(self, result: Any, recipe: Any, sources: list[dict[str, str]], user: str, route: dict[str, Any], ordinal: int) -> dict[str, Any]:
        value = dict(result) if isinstance(result, dict) else {"output": str(result)}
        target = self._route_summary(route, ordinal); output = str(value["output"]); artifact_id = "artifact_" + uuid.uuid4().hex[:12]
        return {"recipe_id": recipe.id, "name": f"{recipe.name or recipe.id}: {user}" if user else (recipe.name or recipe.id), "output": output, "provider": str(value.get("provider") or target["engine"]), "profile_id": target["profile_id"], "inference_target": target, "actual_placement": {"boundary": target["boundary"], "deployment_revision_id": target["deployment_revision_id"]}, "sources": sources, "artifact_id": artifact_id, "created_at": datetime.now().isoformat(), "placement": {"route_plan_id": route["id"], "route_plan_sha256": route["sha256"]}}

    def _chat_projection(self, result: Any, recipe: Any, payload: dict[str, Any], route: dict[str, Any], ordinal: int) -> dict[str, Any]:
        value = dict(result) if isinstance(result, dict) else {"output": str(result)}; target = self._route_summary(route, ordinal)
        output = {"recipe_id": recipe.id, "output": str(value.get("output") or value.get("summary") or ""), "provider": str(value.get("provider") or target["engine"]), "profile_id": target["profile_id"], "inference_target": target, "actual_placement": {"boundary": target["boundary"], "deployment_revision_id": target["deployment_revision_id"]}, "egress": {"scope": target["boundary"]}, "model": str(value.get("model") or target["profile_id"]), "context_ids": payload["context_ids"], "context_titles": payload["context_titles"], "placement": {"route_plan_id": route["id"], "route_plan_sha256": route["sha256"]}}
        if payload["grounding"] is not None: output["grounding"] = payload["grounding"]
        return output

    def cancel(self, principal: Principal, invocation_id: str) -> dict[str, str]:
        from ..kernel.runtime import _as_principal
        with _as_principal(principal): return {"invocation_id": invocation_id, "disposition": self._runner.cancel(invocation_id)}

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
        return {"name": str(value("name", existing.name if existing else "")), "avatar": str(value("avatar", existing.avatar if existing else "")), "role": str(value("role", existing.role if existing else "")), "system_prompt": str(value("system_prompt", existing.system_prompt if existing else "")), "user_template": str(value("user_template", existing.user_template if existing else "")), "tools": list(value("tools", existing.tools if existing else [])), "kb_id": value("kb_id", existing.kb_id if existing else None) or None, "profile_id": value("profile_id", existing.profile_id if existing else None) or None, "manual_context": str(value("manual_context", existing.manual_context if existing else "")), "use_zone_context": bool(value("use_zone_context", existing.use_zone_context if existing else False))}
