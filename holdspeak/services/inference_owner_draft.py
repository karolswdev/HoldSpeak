"""One-member OWNER draft bundles for Phase-143 request-time adopters.

This is deliberately a narrow composition seam, not a second planner or runner.
It starts the durable parent and its exact assigned route together, stages private
prompt material only after that freeze, and lets the shared fallback controller
own every physical attempt.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal, PrincipalKind
from .errors import ValidationError
from .inference_parent_route_bundle_service import InferenceParentRouteBundleService
from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
from .inference_semantic_adapters import adapter_for_frozen_definition

# A deterministic request identity must replay the same frozen route rather than
# conflict merely because a foreground request arrived a few milliseconds later.
# The controller terminalizes each execution; this is an identity fence, not a
# standing provider lease.
_REPLAY_DEADLINE_AT = 4_102_444_800.0  # 2100-01-01 UTC
_BOUNDARY_RANK = {"local": 0, "mesh": 1, "private_network": 2, "cloud": 3}


def frozen_route_egress(route: Mapping[str, Any]) -> dict[str, str]:
    """Return the widest actual boundary named by a frozen route, or refuse."""
    boundaries = [str(item.get("boundary") or "") for item in route.get("entries", ())]
    if not boundaries or any(boundary not in _BOUNDARY_RANK for boundary in boundaries):
        raise ValidationError(
            "Frozen route has no valid egress boundary.",
            code="inference_frozen_route_boundary_invalid",
        )
    return {"scope": max(boundaries, key=lambda boundary: _BOUNDARY_RANK[boundary])}


def run_owner_draft(
    broker: Any,
    principal: Principal,
    *,
    command_id: str,
    parent_kind: str,
    definition_ref: str,
    definition_revision: str,
    input_snapshot: Mapping[str, Any],
    capability_id: str,
    route_key: str,
    operation_id: str,
    reserved_output_tokens: int,
    payload_factory: Callable[[], Mapping[str, Any]],
    projection_kind: str,
    projection_factory: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    result_is_usable: Callable[[Mapping[str, Any]], bool] | None = None,
    parent_result_ref: Callable[[Mapping[str, Any]], str] | None = None,
    parent_started: Callable[[Any], None] | None = None,
) -> dict[str, Any]:
    """Execute exactly one OWNER capability through its frozen bundle member.

    A missing/incompatible assignment cannot create a route.  It instead uses the
    E2 parent-refusal seam and returns its receipt to the adopter so that each
    surface can apply its own honest degradation.  Once a route exists, all
    attempt outcomes stay controller-owned and retain their real child receipts.
    """
    if principal.kind is not PrincipalKind.OWNER:
        raise ValidationError(
            "Owner draft routing requires an authenticated owner.",
            code="inference_owner_draft_owner_required",
        )
    adoption = broker.inference_adoption_service
    bundles = InferenceParentRouteBundleService(broker, adoption)
    try:
        started = bundles.start(
            principal,
            command_id=command_id,
            parent_kind=parent_kind,
            definition_ref=definition_ref,
            definition_revision=definition_revision,
            input_snapshot=dict(input_snapshot),
            deadline_at=_REPLAY_DEADLINE_AT,
            routes=({
                "key": route_key,
                "capability_id": capability_id,
                "invocation_id": command_id,
            },),
        )
    except ValidationError as exc:
        refusal = bundles.record_pre_route_refusal(
            principal,
            command_id=command_id,
            parent_kind=parent_kind,
            definition_ref=definition_ref,
            definition_revision=definition_revision,
            input_snapshot=dict(input_snapshot),
            deadline_at=_REPLAY_DEADLINE_AT,
            reason=exc.code,
        )
        return {
            "outcome": "refused",
            "reason": exc.code,
            "parent": refusal["parent"],
            "parent_receipt": refusal["receipt"],
            "pre_route_refusal": True,
        }

    parent = started["parent"]
    if parent_started is not None:
        parent_started(parent)
    member = next(
        (item for item in started["bundle"]["members"] if item.get("key") == route_key),
        None,
    )
    if not isinstance(member, Mapping) or not str(member.get("route_plan_id") or ""):
        parent_receipt = _close_parent(
            broker, parent, principal, "refused", f"{route_key}:frozen-member-missing"
        )
        return {
            "outcome": "refused",
            "reason": "inference_frozen_route_member_missing",
            "parent": parent,
            "parent_receipt": parent_receipt,
        }

    route_plan_id = str(member["route_plan_id"])
    try:
        # Prompt/diff/decision text is intentionally created only below this line:
        # bundle start above is the atomic public freeze.
        admitted = adoption.admit_on_frozen_route(
            principal,
            command_id="admit:" + command_id,
            route_plan_id=route_plan_id,
            capability_id=capability_id,
            operation_id=operation_id,
            payload=dict(payload_factory()),
            reserved_output_tokens=reserved_output_tokens,
            parent_operation_id=parent.operation_id,
        )
        route = adoption.plans.get_route_plan(ROUTE_PLANNING_AUTHORITY, route_plan_id)
        egress = frozen_route_egress(route)
        definition = adoption._frozen_capability_definition(route_plan_id)

        def publish(value: Any, winning: Mapping[str, Any]) -> str:
            from .inference_adoption_service import _sha256

            invocation_id = str(winning["child_invocation_id"])
            stage = broker.projection_stager.stage(
                invocation_id,
                projection_kind,
                dict(projection_factory(dict(value))),
                result_sha256=_sha256(value),
                receipt_result_ref=str(winning["result_ref"]),
            )
            return stage.result_ref

        routed = adoption.execute(
            principal,
            execution_id=str(admitted["execution"]["id"]),
            adapter=adapter_for_frozen_definition(
                definition, CanonicalPromptAdapter().dispatch
            ),
            publish=publish,
            parent_context=parent.context,
        )
    except Exception:
        # This is after an actual parent/bundle exists but before a controller
        # result can be returned.  Do not manufacture/erase a child receipt.
        parent_receipt = _close_parent(
            broker, parent, principal, "failed", f"{route_key}:admission-failed"
        )
        raise

    outcome = str(routed.get("outcome") or "indeterminate")
    published: Mapping[str, Any] | None = None
    winning = routed.get("winning_reservation") or {}
    invocation_id = str(winning.get("child_invocation_id") or "")
    if outcome == "succeeded" and invocation_id:
        value = broker.projection_stager.finalize(invocation_id)
        published = dict(value) if isinstance(value, Mapping) else None
    usable = (
        outcome == "succeeded"
        and published is not None
        and (result_is_usable is None or result_is_usable(published))
    )
    parent_outcome = "succeeded" if usable else (
        "refused" if outcome == "refused" else "failed" if outcome == "succeeded" else "indeterminate"
    )
    result_ref = f"{route_key}:" + str(
        (routed.get("receipt") or {}).get("receipt_id") or outcome
    )
    if usable and parent_result_ref is not None and published is not None:
        result_ref = str(parent_result_ref(published))
    parent_receipt = _close_parent(
        broker, parent, principal, parent_outcome, result_ref
    )
    return {
        "outcome": outcome,
        "reason": "" if outcome == "succeeded" else "inference_" + outcome,
        "parent": parent,
        "parent_receipt": parent_receipt,
        "routed": routed,
        "published": published,
        "egress": egress,
        "route_plan_id": route_plan_id,
    }


def _close_parent(
    broker: Any,
    parent: Any,
    principal: Principal,
    outcome: str,
    result_ref: str,
) -> Mapping[str, Any]:
    existing = broker.store.receipt(parent.operation_id)
    if existing is not None:
        return dict(existing)
    return dict(
        broker.parent_run_controller.close(
            parent.context, outcome, result_ref, principal=principal
        )
    )


__all__ = ["frozen_route_egress", "run_owner_draft"]
