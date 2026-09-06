"""The task probe (HS-200-04): the smallest REAL request through a live route.

A reachability read proves a socket answered.  It does not prove that the route
this product will actually use can complete a task, and it cannot name the model
that answered.  This module runs one bounded, real request through the frozen
route the assignment resolves to, and records what actually served it: the
deployment's engine and model, the boundary the frozen route named, and the host
the EgressChip shows.

It is not a second planner, runner, or capability.  It borrows an already
registered OWNER capability and runs it through the SAME admit/execute pair the
Ask path uses (`inference_adoption_service.admit` then `.execute`, with the same
closed `_AskAnswerAdapter`), so the route it exercises is the route the product
itself resolves.  The coordinator freezes the plan and the shared fallback
controller owns every physical attempt, so the frozen-route contract holds here
unchanged: no leg outside the frozen plan is ever dispatched, and a failure
returns the receipt that names the route.
"""
from __future__ import annotations

import hashlib
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

from ..principals import Principal
from .errors import ValidationError

# The capability this probe may borrow: registered, OWNER-visible, cheap in
# tokens, and the one the desk asks with.  A closed set of one, so the probe
# names exactly one supported route and claims nothing about the others.
PROBE_CAPABILITIES: tuple[str, ...] = ("ask.answer",)
DEFAULT_PROBE_CAPABILITY = PROBE_CAPABILITIES[0]

# The Concierge group this capability belongs to (inference_capabilities.py).
PROBE_GROUP = "thoughts_notes"

PROBE_SYSTEM_PROMPT = "Reply with one short line and nothing else."
PROBE_USER_PROMPT = "Reply with the single word: ready"
PROBE_MAX_TOKENS = 16

# A cloud leg costs the owner money and sends bytes off the machine.  The
# Concierge law is explicit: no paid probe without his verb.  The pure
# resolution below reads the boundary BEFORE anything is frozen or dispatched.
_OFF_MACHINE = frozenset({"private_network", "mesh", "cloud"})
_PAID = frozenset({"cloud"})


def _authority() -> Principal:
    from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY

    return ROUTE_PLANNING_AUTHORITY


def preview_route(broker: Any, *, capability_id: str = DEFAULT_PROBE_CAPABILITY) -> dict[str, Any]:
    """Pure resolution of the route a probe WOULD use.  No writes, no dispatch.

    Returns the ordered frozen-plan legs with the boundary each names, so a
    caller can refuse a paid probe before any byte leaves the machine.
    """
    if capability_id not in PROBE_CAPABILITIES:
        raise ValidationError(
            "Route probe capability is not probeable.",
            code="route_probe_capability_invalid",
        )
    adoption = broker.inference_adoption_service
    plan = adoption.plans.resolve_route_plan(_authority(), capability_id=capability_id)
    legs = [
        {
            "ordinal": int(entry.get("ordinal") or 0),
            "profileId": str(entry.get("profile_id") or ""),
            "deploymentRevisionId": str(entry.get("deployment_revision_id") or ""),
            "boundary": str(entry.get("boundary") or ""),
        }
        for entry in (plan.get("entries") or ())
    ]
    boundaries = {leg["boundary"] for leg in legs}
    return {
        "capabilityId": capability_id,
        "group": PROBE_GROUP,
        "legs": legs,
        "offMachine": bool(boundaries & _OFF_MACHINE),
        "paid": bool(boundaries & _PAID),
    }


def _deployment_facts(db: Any, deployment_revision_id: str) -> dict[str, str]:
    """Engine, model, endpoint and node of the deployment that actually served."""
    if not deployment_revision_id:
        return {"engine": "", "model": "", "endpoint": "", "node": ""}
    with db._connection() as conn:
        row = conn.execute(
            "SELECT engine,model,endpoint,node FROM deployment_revisions WHERE id=?",
            (deployment_revision_id,),
        ).fetchone()
    if row is None:
        return {"engine": "", "model": "", "endpoint": "", "node": ""}
    return {
        "engine": str(row["engine"] or ""),
        "model": str(row["model"] or ""),
        "endpoint": str(row["endpoint"] or ""),
        "node": str(row["node"] or ""),
    }


def host_for(boundary: str, facts: Mapping[str, str]) -> str:
    """The host the EgressChip names — `THIS DEVICE` when nothing leaves."""
    if boundary == "local":
        return "THIS DEVICE"
    if boundary == "mesh":
        return str(facts.get("node") or "") or "THIS DEVICE"
    endpoint = str(facts.get("endpoint") or "").strip()
    if endpoint:
        return urlparse(endpoint).hostname or endpoint
    return str(facts.get("node") or "")


def _receipt_legs(receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every frozen leg the controller considered, with what became of it."""
    return [
        {
            "ordinal": int(item.get("route_leg_ordinal") or 0),
            "profileId": str(item.get("profile_id") or ""),
            "deploymentRevisionId": str(item.get("deployment_revision_id") or ""),
            "boundary": str(item.get("boundary") or ""),
            "status": str(item.get("status") or ""),
            "disposition": str(item.get("disposition") or ""),
        }
        for item in (receipt.get("considerations") or ())
    ]


def _unresolved(capability_id: str, exc: Exception) -> dict[str, Any]:
    """No assignment can be resolved, so no route exists to test.

    The probe says which, and invents nothing: no model, no boundary, no host.
    """
    return {
        "state": "UNREACHABLE",
        "ok": False,
        "capabilityId": capability_id,
        "group": PROBE_GROUP,
        "outcome": "refused",
        "reasonCode": str(getattr(exc, "code", "") or type(exc).__name__),
        "routePlanId": "",
        "executionId": "",
        "legs": [],
        "allModelsFailed": False,
    }


def task_probe(
    broker: Any,
    principal: Principal,
    *,
    db: Any,
    capability_id: str = DEFAULT_PROBE_CAPABILITY,
    allow_off_machine: bool = False,
    nonce: str = "",
) -> dict[str, Any]:
    """Run one real request through the assigned route and record what served it.

    The result names the actual model and the actual boundary.  A failure names
    the route: its plan id and every frozen leg the controller considered.  It
    never names a provider that was not in the frozen plan, because it never
    dispatches one — the reservation fence in the kernel runner refuses that.
    """
    try:
        preview = preview_route(broker, capability_id=capability_id)
    except ValidationError as exc:
        if getattr(exc, "code", "") == "route_probe_capability_invalid":
            raise
        return _unresolved(capability_id, exc)
    except Exception as exc:
        return _unresolved(capability_id, exc)
    if preview["offMachine"] and not allow_off_machine:
        # Nothing has been frozen and nothing has been sent.
        return {
            "state": "REFUSED",
            "ok": False,
            "capabilityId": capability_id,
            "group": PROBE_GROUP,
            "reasonCode": "route_probe_off_machine_not_confirmed",
            "paid": preview["paid"],
            "legs": preview["legs"],
        }

    from ..kernel.prompt_adapter import CanonicalPromptAdapter
    from .ask_service import _AskAnswerAdapter

    adoption = broker.inference_adoption_service
    identity = f"{capability_id}:{nonce or time.time_ns()}"
    digest = hashlib.sha256(identity.encode()).hexdigest()
    invocation_id = "routeprobe" + digest[:24]

    payload = {
        "schema_version": 2,
        "system_prompt": PROBE_SYSTEM_PROMPT,
        "user_prompt": PROBE_USER_PROMPT,
        "lens": "Probe",
        "context_ids": [],
        "context_titles": [],
        "grounding": None,
        "source_text": "",
        "temperature": None,
        "max_tokens": PROBE_MAX_TOKENS,
    }

    started = time.monotonic()
    try:
        admitted = adoption.admit(
            principal,
            command_id=f"admit-{invocation_id}",
            capability_id=capability_id,
            operation_id=invocation_id,
            payload=payload,
            invocation_id=invocation_id,
            reserved_output_tokens=PROBE_MAX_TOKENS,
        )
    except Exception as exc:
        # A missing or incompatible assignment cannot create a route, and this
        # probe does not invent one.  It names why, and the planned legs.
        return {
            "state": "UNREACHABLE",
            "ok": False,
            "capabilityId": capability_id,
            "group": PROBE_GROUP,
            "outcome": "refused",
            "reasonCode": str(getattr(exc, "code", "") or type(exc).__name__),
            "routePlanId": "",
            "executionId": "",
            "legs": preview["legs"],
            "allModelsFailed": False,
        }
    routed = adoption.execute(
        principal,
        execution_id=str(admitted["execution"]["id"]),
        adapter=_AskAnswerAdapter(CanonicalPromptAdapter()),
    )
    latency_ms = int((time.monotonic() - started) * 1000)

    outcome = str(routed.get("outcome") or "indeterminate")
    receipt = dict(routed.get("receipt") or {})
    winning = dict(routed.get("winning_reservation") or {})
    deployment_id = str(
        receipt.get("winning_deployment_revision_id")
        or winning.get("deployment_revision_id")
        or ""
    )
    facts = _deployment_facts(db, deployment_id)
    boundary = str(receipt.get("winning_boundary") or winning.get("boundary") or "")
    result = routed.get("result") if isinstance(routed.get("result"), Mapping) else {}
    answered = bool(str((result or {}).get("output") or "").strip())
    ok = outcome == "succeeded" and answered

    return {
        "state": "READY" if ok else "UNREACHABLE",
        "ok": ok,
        "capabilityId": capability_id,
        "group": PROBE_GROUP,
        "outcome": outcome,
        "reasonCode": "" if ok else ("inference_" + outcome),
        # What actually served this request — never an advertised model.
        "engine": facts["engine"],
        "model": facts["model"],
        "boundary": boundary,
        "host": host_for(boundary, facts) if boundary else "",
        "latencyMs": latency_ms,
        # The route, named. A failure carries the same identity as a success.
        "routePlanId": str(
            receipt.get("route_plan_id") or admitted["route_plan"]["id"] or ""
        ),
        # The route execution's durable identity. The controller's receipt has
        # no separate id of its own; this is the row every attempt hangs off.
        "executionId": str(
            receipt.get("execution_id") or admitted["execution"]["id"] or ""
        ),
        "operationId": invocation_id,
        "legs": _receipt_legs(receipt) or preview["legs"],
        "allModelsFailed": bool(receipt.get("all_models_physically_failed")),
    }


__all__ = [
    "DEFAULT_PROBE_CAPABILITY",
    "PROBE_CAPABILITIES",
    "PROBE_GROUP",
    "host_for",
    "preview_route",
    "task_probe",
]
