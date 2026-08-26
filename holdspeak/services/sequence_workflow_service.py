"""Admitted execution services for Sequence and Workflow definitions."""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from datetime import datetime
from typing import Any

from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal, PrincipalKind
from .errors import ServiceError, ValidationError


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _node_revision(node: Any) -> str:
    """One canonical frozen definition for both workflow payload and projection."""
    return _sha(
        {
            "id": node.id,
            "kind": node.kind,
            "payload": node.payload,
            "failure_policy": node.failure_policy,
            "runs_on": node.runs_on,
        }
    )


class SequenceWorkflowService:
    """Domain-owned linear execution using only trusted, admitted children."""

    def __init__(self, db: Any, broker: Any) -> None:
        self.db, self.broker = db, broker
        from ..kernel.sequence_workflow_projection import register

        register(broker.projection_stager)

    @staticmethod
    def _route_target(route: dict[str, Any], ordinal: int = 1) -> dict[str, str]:
        """Project execution placement only from immutable route evidence."""
        entry = dict(route["entries"][ordinal - 1])
        profile_id = str(entry["profile_id"]).removeprefix("legacy-")
        return {
            "id": profile_id,
            "profile_id": profile_id,
            "engine": "routed",
            "boundary": str(entry["boundary"]),
            "deployment_revision_id": str(entry["deployment_revision_id"]),
        }

    @staticmethod
    def _route_placement(route: dict[str, Any]) -> dict[str, str]:
        """Keep the public summary evidence-derived, never a fresh lookup."""
        target = SequenceWorkflowService._route_target(route)
        return {
            "route_plan_id": str(route["id"]),
            "route_plan_sha256": str(route["sha256"]),
            "source": str(route["source"]["inherited_from"]),
            "effective_target_id": target["profile_id"],
            "deployment_revision_id": target["deployment_revision_id"],
        }

    def _freeze_parent_routes(
        self,
        principal: Principal,
        *,
        command_id: str,
        deadline_at: float,
        routes: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Freeze every future node route together before any model execution."""
        return self.broker.inference_adoption_service.freeze_routes(
            principal,
            command_id=command_id,
            deadline_at=deadline_at,
            routes=routes,
        )

    def _parent_deadline(self, parent: Any) -> float:
        """Reuse the persisted parent fence when a crashed parent is resumed."""
        with self.db._connection() as conn:
            row = conn.execute(
                "SELECT deadline_at FROM kernel_parent_runs WHERE operation_id=?",
                (parent.operation_id,),
            ).fetchone()
        if row is None:
            raise ServiceError(
                "parent_route_missing",
                "The parent run has no durable route fence.",
                context={"status": 409, "parent_operation_id": parent.operation_id},
            )
        return float(row["deadline_at"])

    async def _run_frozen_child(
        self,
        principal: Principal,
        *,
        parent: Any,
        route: dict[str, Any],
        capability_id: str,
        command_id: str,
        operation_id: str,
        payload: dict[str, Any],
        reserved_output_tokens: int,
        publish: Any,
        planned_node: str,
    ) -> dict[str, Any]:
        """Attach mutable material to an already-frozen route, then execute it."""
        admitted = await asyncio.to_thread(
            self.broker.inference_adoption_service.admit_on_frozen_route,
            principal,
            command_id=command_id,
            route_plan_id=str(route["id"]),
            capability_id=capability_id,
            operation_id=operation_id,
            payload=payload,
            reserved_output_tokens=reserved_output_tokens,
            parent_operation_id=parent.operation_id,
        )
        return await asyncio.to_thread(
            self.broker.inference_adoption_service.execute,
            principal,
            execution_id=admitted["execution"]["id"],
            adapter=CanonicalPromptAdapter(),
            publish=publish,
            parent_context=parent.context,
            planned_node=planned_node,
        )

    def _children(self, parent_id: str) -> list[dict[str, Any]]:
        with self.db._connection() as conn:
            rows = conn.execute(
                "SELECT operation_id,native_id FROM kernel_operations "
                "WHERE parent_operation_id=? ORDER BY created_at",
                (parent_id,),
            ).fetchall()
        return [
            {
                "operation_id": str(row["operation_id"]),
                "invocation_id": str(row["native_id"]),
                "outcome": str(
                    (self.broker.store.receipt(str(row["operation_id"])) or {}).get("outcome")
                    or ""
                ),
            }
            for row in rows
        ]

    def _close_or_adopt(
        self, parent: Any, outcome: str, *, principal: Principal, result_ref: str = ""
    ) -> dict[str, Any]:
        """Use this runner's close if live, otherwise report the elected receipt."""
        from ..kernel.model import KernelRefused

        try:
            return dict(
                self.broker.parent_run_controller.close(
                    parent.context, outcome, result_ref, principal=principal
                )
            )
        except KernelRefused as exc:
            receipt = self.broker.store.receipt(parent.operation_id)
            if exc.reason == "parent_context_invalid":
                # The canceler installs CANCELLING before its in-flight child
                # returns; wait briefly for that elected terminal receipt.
                for _ in range(100):
                    if receipt is not None:
                        return dict(receipt)
                    time.sleep(0.01)
                    receipt = self.broker.store.receipt(parent.operation_id)
            raise

    def _terminal_result(
        self, parent: Any, kind: str, definition_id: str, receipt: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "parent_operation_id": parent.operation_id,
            "parent_native_id": parent.native_id,
            "operation": f"{kind}.run",
            f"{kind}_id": definition_id,
            "receipt_id": receipt["receipt_id"],
            "terminal_disposition": receipt.get("outcome"),
            "children": self._children(parent.operation_id),
        }

    def _finish(
        self,
        parent: Any,
        principal: Principal,
        kind: str,
        definition_id: str,
        revision: str,
        output: str,
        sources: list[dict[str, str]],
        steps: list[dict[str, Any]],
        target: dict[str, str] | None,
    ) -> dict[str, Any]:
        aid = "artifact_" + uuid.uuid4().hex[:12]
        stage = self.broker.projection_stager.stage(
            parent.native_id,
            f"{kind}-run-result",
            {
                "kind": kind,
                "parent_operation_id": parent.operation_id,
                "definition_revision": revision,
                "artifact_id": aid,
                "name": definition_id,
                "output": output,
                "sources": sources,
                "steps": steps,
                "created_at": datetime.now().isoformat(),
                "inference_target": target,
            },
        )
        receipt = self._close_or_adopt(
            parent, "succeeded", result_ref=stage.result_ref, principal=principal
        )
        if receipt.get("outcome") != "succeeded":
            return self._terminal_result(parent, kind, definition_id, receipt)
        result = self.broker.projection_stager.finalize(parent.native_id)
        if result is None:
            raise ServiceError(
                "projection_not_published",
                "result is awaiting receipt reconciliation",
                context={"status": 409},
            )
        result.update(
            {
                "parent_operation_id": parent.operation_id,
                "parent_native_id": parent.native_id,
                "operation": f"{kind}.run",
                "children": self._children(parent.operation_id),
                "artifact_id": aid,
                "result_ref": f"artifact:{aid}",
            }
        )
        return result

    def _fail(self, parent: Any, principal: Principal, exc: Exception) -> None:
        # A cross-request cancel invalidates this context, but its receipt is the
        # durable winner and must not turn the original service error into a kernel error.
        try:
            self._close_or_adopt(parent, "failed", principal=principal)
        except Exception:
            pass

    def _replay(self, parent: Any, kind: str, definition_id: str) -> dict[str, Any]:
        result = self.broker.projection_stager.finalize(parent.native_id)
        if result is None:
            raise ServiceError(
                "parent_replay_unavailable",
                "This prior run has no published result.",
                context={"status": 409, "parent_operation_id": parent.operation_id},
            )
        result.update(
            {
                "parent_operation_id": parent.operation_id,
                "parent_native_id": parent.native_id,
                "operation": f"{kind}.run",
                "children": self._children(parent.operation_id),
            }
        )
        result[f"{kind}_id"] = definition_id
        return result

    @staticmethod
    def _reject_retired_selector(body: dict[str, Any]) -> None:
        if str(body.get("inference_target_id") or body.get("requested_placement") or "").strip():
            raise ValidationError(
                "Legacy model selectors are unavailable after assignment migration.",
                code="inference_legacy_selector_retired",
            )

    async def run_sequence(
        self, principal: Principal, chain_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        self._reject_retired_selector(body)
        if principal.kind is PrincipalKind.OWNER:
            self.broker.inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)
        chain = self.db.chains.get(chain_id)
        if chain is None:
            raise ServiceError(
                "not_found", f"Unknown Sequence: {chain_id}", context={"status": 404}
            )
        steps = list(chain.steps or [])
        deadline = time.time() + 60
        parent = self.broker.parent_run_controller.start(
            principal,
            kind="sequence",
            definition_ref=f"sequence:{chain_id}",
            definition_revision=str(chain.last_modified),
            input_snapshot=dict(body),
            deadline_at=deadline,
            # `sequence.step` uses the frozen controller's four-attempt ceiling.
            child_budget=len(steps) * 4,
            idempotency_key=str(body.get("request_id") or "") or None,
        )
        if parent.replayed and self.broker.store.receipt(parent.operation_id) is not None:
            return self._replay(parent, "sequence", chain_id)
        if not steps:
            self.broker.parent_run_controller.close(parent.context, "refused", principal=principal)
            raise ServiceError(
                "empty_sequence",
                "This Sequence has no Agents. Add one before running.",
                context={"status": 409, "parent_operation_id": parent.operation_id},
            )
        recipes = []
        for ordinal, recipe_id in enumerate(steps, 1):
            recipe = self.db.recipes.get(str(recipe_id))
            if recipe is None:
                self._fail(parent, principal, ServiceError("recipe_unavailable", ""))
                raise ServiceError(
                    "recipe_unavailable",
                    f"Agent {recipe_id} is unavailable; the Sequence was not run. Repair the Sequence and run it again.",
                    context={"status": 409},
                )
            recipes.append((ordinal, recipe))
        try:
            routes = await asyncio.to_thread(
                self._freeze_parent_routes,
                principal,
                command_id=f"sequence-routes-{parent.operation_id}",
                deadline_at=self._parent_deadline(parent),
                routes=[
                    {
                        "key": f"step:{ordinal}",
                        "capability_id": "sequence.step",
                        "invocation_id": f"{parent.native_id}:step:{ordinal}",
                        "subject_kind": "recipe",
                        "subject_id": recipe.id,
                    }
                    for ordinal, recipe in recipes
                ],
            )
            from .support import _render_user_prompt

            current, records, sources, last_route = (
                str(body.get("input") or ""),
                [],
                [{"source_type": "chain", "source_ref": chain_id}],
                None,
            )
            for ordinal, recipe in recipes:
                prompt = _render_user_prompt(
                    recipe.user_template,
                    body.get("variables") if isinstance(body.get("variables"), dict) else {},
                    current,
                )
                if not prompt.strip():
                    raise ServiceError(
                        "empty_input",
                        f"Nothing to run for {recipe.name or recipe.id}; input is retained for Retry.",
                        context={"status": 400, "recipe_id": recipe.id},
                    )
                route = routes[f"step:{ordinal}"]
                target = self._route_target(route)
                payload = {
                    "sequence_ref": chain_id,
                    "sequence_revision": str(chain.last_modified),
                    "step_ordinal": ordinal,
                    "recipe_id": recipe.id,
                    "recipe_revision": str(recipe.last_modified),
                    "system_prompt": recipe.system_prompt,
                    "user_prompt": prompt,
                    "temperature": float(body["temperature"])
                    if body.get("temperature") is not None
                    else None,
                    "max_tokens": int(body["max_tokens"])
                    if body.get("max_tokens") is not None
                    else None,
                    "attempt_ordinal": 1,
                }
                operation_id = f"sequence:{parent.operation_id}:step:{ordinal}"

                def projection(
                    value: Any,
                    reservation: dict[str, Any],
                    *,
                    recipe: Any = recipe,
                    ordinal: int = ordinal,
                    prompt: str = prompt,
                    epoch: int = parent.context.epoch,
                    route: dict[str, Any] = route,
                ) -> str:
                    projected = self._route_target(route, int(reservation["route_leg_ordinal"]))
                    return self.broker.projection_stager.stage(
                        str(reservation["child_invocation_id"]),
                        "sequence-step-output",
                        {
                            "parent_operation_id": parent.operation_id,
                            "execution_epoch": epoch,
                            "planned_node": f"step:{ordinal}",
                            "step_ordinal": ordinal,
                            "recipe_id": recipe.id,
                            "recipe_revision": str(recipe.last_modified),
                            "output": str(value.get("output") if isinstance(value, dict) else value),
                            "deployment_revision": projected["deployment_revision_id"],
                            "rendered_input_sha256": _sha(prompt),
                            "provider": str(value.get("provider") if isinstance(value, dict) else ""),
                        },
                        result_sha256=_sha(value),
                        receipt_result_ref=(
                            f"inference-result:{reservation['child_invocation_id']}/{_sha(value)}"
                        ),
                    ).result_ref

                routed = await self._run_frozen_child(
                    principal,
                    parent=parent,
                    route=route,
                    capability_id="sequence.step",
                    command_id=f"{operation_id}:admit",
                    operation_id=operation_id,
                    payload=payload,
                    reserved_output_tokens=int(body.get("max_tokens") or 512),
                    publish=projection,
                    planned_node=f"step:{ordinal}",
                )
                if routed["outcome"] != "succeeded":
                    raise ServiceError(
                        "inference_failed",
                        str(routed.get("error") or routed["outcome"]),
                        context={"status": 502, "recipe_id": recipe.id, "receipt": routed["receipt"]},
                    )
                iid = str(routed["winning_reservation"]["child_invocation_id"])
                checkpoint = self.broker.projection_stager.finalize(iid)
                if checkpoint is None:
                    raise ServiceError(
                        "projection_not_published",
                        "step is awaiting receipt reconciliation",
                        context={"status": 409},
                    )
                if not checkpoint.get("advanced"):
                    raise ServiceError(
                        "parent_child_stale",
                        "The child receipt was retained but cannot advance this Sequence.",
                        context={"status": 409},
                    )
                current = str(checkpoint["output"])
                records.append(
                    {
                        "recipe_id": recipe.id,
                        "output": current,
                        "provider": str(checkpoint.get("provider") or target["engine"]),
                    }
                )
                sources.append({"source_type": "recipe", "source_ref": recipe.id})
                last_route = route
            target = self._route_target(last_route) if last_route else None
            result = self._finish(
                parent,
                principal,
                "sequence",
                chain_id,
                str(chain.last_modified),
                current,
                sources,
                records,
                target,
            )
            if result.get("terminal_disposition"):
                return result
            assert last_route is not None
            result.update(
                {
                    "chain_id": chain_id,
                    "output": current,
                    "provider": records[-1]["provider"],
                    "steps": records,
                    "sources": sources,
                    "inference_target": target,
                    "actual_placement": {
                        "boundary": target["boundary"],
                        "deployment_revision_id": target["deployment_revision_id"],
                    },
                    "placement": self._route_placement(last_route),
                }
            )
            return result
        except Exception as exc:
            self._fail(parent, principal, exc)
            raise

    async def run_workflow(
        self, principal: Principal, workflow_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        self._reject_retired_selector(body)
        workflow = self.db.workflows.get(workflow_id)
        if workflow is None:
            raise ServiceError(
                "not_found", f"Unknown workflow: {workflow_id}", context={"status": 404}
            )
        from .support import (
            _MODEL_KINDS,
            _PASSTHROUGH_KINDS,
            _PURE_TRANSFORM_KINDS,
            _render_user_prompt,
            apply_pure_transform,
            build_node_prompt,
            linearize,
            on_node_error,
            resolved_failure_policy,
        )

        plan = linearize(workflow.graph_json) if workflow.graph_json else None
        executable = [] if plan is None else list(plan.ordered)
        unsupported_reason = plan.reason if plan is not None and not plan.linearizable else ""
        unknown = [
            node
            for node in executable
            if node.kind not in _MODEL_KINDS
            and node.kind not in _PURE_TRANSFORM_KINDS
            and node.kind not in _PASSTHROUGH_KINDS
        ]
        model_nodes = [node for node in executable if node.kind in _MODEL_KINDS]
        if plan is None and str(workflow.prompt or "").strip():
            model_nodes = [
                type(
                    "Prompt",
                    (),
                    {
                        "id": "prompt",
                        "kind": "prompt",
                        "payload": {},
                        "runs_on": "auto",
                        "failure_policy": None,
                    },
                )()
            ]
        deadline = time.time() + 60
        parent = self.broker.parent_run_controller.start(
            principal,
            kind="workflow",
            definition_ref=f"workflow:{workflow_id}",
            definition_revision=str(workflow.last_modified),
            input_snapshot=dict(body),
            deadline_at=deadline,
            child_budget=len(model_nodes) * 4,
            idempotency_key=str(body.get("request_id") or "") or None,
        )
        if parent.replayed and self.broker.store.receipt(parent.operation_id) is not None:
            return self._replay(parent, "workflow", workflow_id)
        if unsupported_reason or unknown:
            self.broker.parent_run_controller.close(parent.context, "refused", principal=principal)
            message = (
                "This Workflow is unavailable on this host: "
                + unsupported_reason
                + ". Open it in a compatible Workbench; it was not lowered to a prompt."
                if unsupported_reason
                else "This Workflow contains unsupported nodes."
            )
            raise ServiceError(
                "unsupported_graph",
                message,
                context={
                    "status": 409,
                    "support": "unsupported_graph",
                    "parent_operation_id": parent.operation_id,
                },
            )
        try:
            routes = await asyncio.to_thread(
                self._freeze_parent_routes,
                principal,
                command_id=f"workflow-routes-{parent.operation_id}",
                deadline_at=self._parent_deadline(parent),
                routes=[
                    {
                        "key": f"node:{node.id}",
                        "capability_id": "workflow.node",
                        "invocation_id": f"{parent.native_id}:node:{node.id}",
                    }
                    for node in model_nodes
                ],
            ) if model_nodes else {}
            current, records, sources, last_route = (
                str(body.get("input") or ""),
                [],
                [{"source_type": "workflow", "source_ref": workflow_id}],
                None,
            )
            if plan is None:
                prompt = _render_user_prompt(
                    str(workflow.prompt or ""),
                    body.get("variables") if isinstance(body.get("variables"), dict) else {},
                    current,
                )
                if not prompt.strip():
                    raise ServiceError(
                        "empty_workflow",
                        "This Workflow has no runnable graph or prompt; its input is retained.",
                        context={"status": 409},
                    )
                executable = model_nodes
            for node in executable:
                if node.kind in _PURE_TRANSFORM_KINDS:
                    current = apply_pure_transform(node, current)
                    records.append(
                        {
                            "node_id": node.id,
                            "kind": node.kind,
                            "output": current,
                            "provider": None,
                            "status": "ok",
                            "runs_on": node.runs_on,
                            "failure_policy": resolved_failure_policy(node),
                        }
                    )
                    continue
                if node.kind in _PASSTHROUGH_KINDS:
                    continue
                prompt = (
                    _render_user_prompt(
                        str(workflow.prompt),
                        body.get("variables") if isinstance(body.get("variables"), dict) else {},
                        current,
                    )
                    if node.kind == "prompt"
                    else build_node_prompt(node, current)
                )
                if not prompt.strip():
                    continue
                route = routes[f"node:{node.id}"]
                revision = _node_revision(node)
                payload = {
                    "workflow_ref": workflow_id,
                    "workflow_revision": str(workflow.last_modified),
                    "node_id": node.id,
                    "node_revision": revision,
                    "rendered_input": current,
                    "system_prompt": "",
                    "user_prompt": prompt,
                    "temperature": float(body["temperature"])
                    if body.get("temperature") is not None
                    else None,
                    "max_tokens": int(body["max_tokens"])
                    if body.get("max_tokens") is not None
                    else None,
                    "attempt_ordinal": 1,
                }
                operation_id = f"workflow:{parent.operation_id}:node:{node.id}"

                def projection(
                    value: Any,
                    reservation: dict[str, Any],
                    *,
                    node: Any = node,
                    prompt: str = prompt,
                    revision: str = revision,
                    epoch: int = parent.context.epoch,
                    route: dict[str, Any] = route,
                ) -> str:
                    projected = self._route_target(route, int(reservation["route_leg_ordinal"]))
                    return self.broker.projection_stager.stage(
                        str(reservation["child_invocation_id"]),
                        "workflow-node-output",
                        {
                            "parent_operation_id": parent.operation_id,
                            "execution_epoch": epoch,
                            "planned_node": f"node:{node.id}",
                            "node_id": node.id,
                            "node_revision": revision,
                            "output": str(value.get("output") if isinstance(value, dict) else value),
                            "deployment_revision": projected["deployment_revision_id"],
                            "rendered_input_sha256": _sha(prompt),
                            "provider": str(value.get("provider") if isinstance(value, dict) else ""),
                        },
                        result_sha256=_sha(value),
                        receipt_result_ref=(
                            f"inference-result:{reservation['child_invocation_id']}/{_sha(value)}"
                        ),
                    ).result_ref

                routed = await self._run_frozen_child(
                    principal,
                    parent=parent,
                    route=route,
                    capability_id="workflow.node",
                    command_id=f"{operation_id}:admit",
                    operation_id=operation_id,
                    payload=payload,
                    reserved_output_tokens=int(body.get("max_tokens") or 512),
                    publish=projection,
                    planned_node=f"node:{node.id}",
                )
                if routed["outcome"] != "succeeded":
                    policy = resolved_failure_policy(node)
                    handled = on_node_error(node, current)
                    if handled is None:
                        # A saved graph may deliberately hold an admitted node
                        # for owner repair. A prompt-only compatibility Workflow
                        # has no such declared policy: its physical provider
                        # failure remains an ordinary transport failure.
                        held = policy == "hold" and plan is not None
                        code = "workflow_failure_policy_hold" if held else "inference_failed"
                        message = (
                            "This Workflow node is held after its admitted model attempt failed."
                            if held
                            else str(routed.get("error") or routed["outcome"])
                        )
                        raise ServiceError(
                            code,
                            message,
                            context={
                                "status": 409 if held else 502,
                                "node_id": node.id,
                                "receipt": routed["receipt"],
                            },
                        )
                    # `carry` and `skip` are local workflow dispositions, not
                    # controller fallback. Their failed attempt receipt remains
                    # linked in the child list; no invented fallback receipt exists.
                    current = handled
                    records.append(
                        {
                            "node_id": node.id,
                            "kind": node.kind,
                            "output": current,
                            "provider": None,
                            "status": policy,
                            "runs_on": node.runs_on,
                            "failure_policy": policy,
                            "error": str(routed["outcome"]),
                        }
                    )
                    last_route = route
                    continue
                iid = str(routed["winning_reservation"]["child_invocation_id"])
                checkpoint = self.broker.projection_stager.finalize(iid)
                if checkpoint is None:
                    raise ServiceError(
                        "projection_not_published",
                        "node is awaiting receipt reconciliation",
                        context={"status": 409},
                    )
                if not checkpoint.get("advanced"):
                    raise ServiceError(
                        "parent_child_stale",
                        "The child receipt was retained but cannot advance this Workflow.",
                        context={"status": 409},
                    )
                current = str(checkpoint["output"])
                records.append(
                    {
                        "node_id": node.id,
                        "kind": node.kind,
                        "output": current,
                        "provider": str(
                            checkpoint.get("provider") or self._route_target(route)["engine"]
                        ),
                        "status": "ok",
                        "runs_on": node.runs_on,
                        "failure_policy": resolved_failure_policy(node),
                    }
                )
                last_route = route
            if not records:
                raise ServiceError(
                    "empty_workflow",
                    "Nothing executable ran; the Workflow input is retained for Retry.",
                    context={"status": 400},
                )
            target = self._route_target(last_route) if last_route else None
            result = self._finish(
                parent,
                principal,
                "workflow",
                workflow_id,
                str(workflow.last_modified),
                current,
                sources,
                records,
                target,
            )
            if result.get("terminal_disposition"):
                return result
            result.update(
                {
                    "workflow_id": workflow_id,
                    "output": current,
                    "provider": next(
                        (item["provider"] for item in reversed(records) if item["provider"]),
                        None,
                    ),
                    "steps": records,
                    "sources": sources,
                    "inference_target": target,
                    "actual_placement": (
                        {
                            "boundary": target["boundary"],
                            "deployment_revision_id": target["deployment_revision_id"],
                        }
                        if target
                        else None
                    ),
                    "placement": self._route_placement(last_route) if last_route else None,
                }
            )
            return result
        except Exception as exc:
            self._fail(parent, principal, exc)
            raise
