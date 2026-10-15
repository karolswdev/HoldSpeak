"""The task probe (HS-200-04): the smallest REAL request through a live route.

A reachability read proves a socket answered.  It does not prove that the route
this product will actually use can complete a task, and it cannot name the model
that answered.  This module runs one bounded, real request through the frozen
route the assignment resolves to, and records what actually served it: the
deployment's engine and model, the boundary the frozen route named, and the host
the EgressChip shows.

It borrows an already registered OWNER capability and runs a fixed public
sample through its existing admit/execute pair and closed result adapter.
The coordinator freezes the plan and the shared fallback
controller owns every physical attempt, so the frozen-route contract holds here
unchanged: no leg outside the frozen plan is ever dispatched, and a failure
returns the receipt that names the route.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse

from ..principals import Principal
from .errors import ValidationError

# Fixed, public material only. These capabilities already have an adopted
# execution stage; no domain materializer, saved recipe or tool is invoked.
_SAMPLES = {
    "ask.answer": {
        "group": "thoughts_notes", "task": "Answers",
        "system": "Answer the question in one short line.",
        "input": "What is 2 + 2?",
    },
    "speech.rewrite": {
        "group": "writing_dictation", "task": "Dictation clean-up",
        "system": "Correct capitalization and punctuation. Return only the corrected text.",
        "input": "we will meet at ten tomorrow",
    },
    "meeting.deferred_analysis": {
        "group": "meetings", "task": "Meeting summary",
        "system": (
            "Summarize this transcript. Return JSON only, with topics (a list of strings), "
            "summary (a string), action_items (a list of objects with task, owner, and due), "
            "and decisions (a list of objects with decision and rationale). "
            "Use null for an unknown owner, due, or rationale. Do not add other keys."
        ),
        "input": "Alex: We will ship the settings fix on Tuesday.\nSam: I will check the change before then.",
    },
    "recipe.run": {
        "group": "agents_tools", "task": "Recipe",
        "system": "Follow the instruction in one short line.",
        "input": "Write a task title for checking a settings fix.",
    },
    "background.rails_summary": {
        "group": "background", "task": "Background summary",
        "system": "Summarize this software delivery event in one short line.",
        "input": "The settings fix passed review and is ready to ship.",
    },
}
PROBE_CAPABILITIES: tuple[str, ...] = tuple(_SAMPLES)
DEFAULT_PROBE_CAPABILITY = PROBE_CAPABILITIES[0]

# The Concierge group this capability belongs to (inference_capabilities.py).
PROBE_GROUP = "thoughts_notes"

PROBE_MAX_TOKENS = 512

# A cloud leg costs the owner money and sends bytes off the machine.  The
# Concierge law is explicit: no paid probe without his verb.  The pure
# resolution below reads the boundary BEFORE anything is frozen or dispatched.
_OFF_MACHINE = frozenset({"private_network", "mesh", "cloud"})
_PAID = frozenset({"cloud"})


def _authority() -> Principal:
    from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY

    return ROUTE_PLANNING_AUTHORITY


def _sample_facts(capability_id: str) -> dict[str, Any]:
    sample = _SAMPLES[capability_id]
    return {
        "group": sample["group"], "testedTask": sample["task"],
        "sampleInput": sample["input"], "sampleOutput": "", "emptyOutput": False,
    }


def _sample_adapter(capability_id: str) -> Any:
    from ..kernel.prompt_adapter import CanonicalPromptAdapter
    from ..kernel.provider_signals import InferenceInvalidTypedOutput
    from .ask_service import _AskAnswerAdapter
    from .inference_semantic_adapters import adapter_for

    prompt = CanonicalPromptAdapter()
    if capability_id == "ask.answer":
        return _AskAnswerAdapter(prompt)
    if capability_id == "background.rails_summary":
        return adapter_for(capability_id, prompt.dispatch)
    if capability_id == "meeting.deferred_analysis":
        def meeting_sample(engine: Any, payload: Mapping[str, Any], cancellation: Any) -> Any:
            raw = prompt.dispatch(engine, dict(payload), cancellation)
            try:
                return json.loads(raw["output"])
            except (KeyError, TypeError, ValueError):
                raise InferenceInvalidTypedOutput() from None

        return adapter_for(capability_id, meeting_sample)
    return prompt


def preview_route(broker: Any, *, capability_id: str = DEFAULT_PROBE_CAPABILITY, db: Any = None) -> dict[str, Any]:
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
    # Endpoint profiles store loopback under private_network. Use the same
    # classifier as the desk lamp without changing the frozen leg facts.
    from ..inference_locality import deployment_lamp

    boundaries = {
        deployment_lamp(leg["boundary"], _deployment_facts(db, leg["deploymentRevisionId"])["endpoint"])
        if db is not None else leg["boundary"]
        for leg in legs
    }
    return {
        "capabilityId": capability_id,
        "group": _SAMPLES[capability_id]["group"],
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
        **_sample_facts(capability_id),
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
    expected_profile_ids: Sequence[str] | None = None,
    nonce: str = "",
) -> dict[str, Any]:
    """Run one real request through the assigned route and record what served it.

    The result names the actual model and the actual boundary.  A failure names
    the route: its plan id and every frozen leg the controller considered.  It
    never names a provider that was not in the frozen plan, because it never
    dispatches one — the reservation fence in the kernel runner refuses that.
    """
    try:
        preview = preview_route(broker, capability_id=capability_id, db=db)
    except ValidationError as exc:
        if getattr(exc, "code", "") == "route_probe_capability_invalid":
            raise
        return _unresolved(capability_id, exc)
    except Exception as exc:
        return _unresolved(capability_id, exc)
    if expected_profile_ids is not None and any(
        leg["profileId"] not in expected_profile_ids for leg in preview["legs"]
    ):
        return {
            "state": "REFUSED", "ok": False, "outcome": "refused",
            "capabilityId": capability_id, **_sample_facts(capability_id),
            "reasonCode": "route_probe_assignment_changed", "legs": preview["legs"],
        }
    if preview["offMachine"] and not allow_off_machine:
        # Nothing has been frozen and nothing has been sent.
        return {
            "state": "REFUSED",
            "ok": False,
            "capabilityId": capability_id,
            **_sample_facts(capability_id),
            "reasonCode": "route_probe_off_machine_not_confirmed",
            "paid": preview["paid"],
            "legs": preview["legs"],
        }

    adoption = broker.inference_adoption_service
    identity = f"{capability_id}:{nonce or time.time_ns()}"
    digest = hashlib.sha256(identity.encode()).hexdigest()
    invocation_id = "routeprobe" + digest[:24]
    sample = _SAMPLES[capability_id]

    payload = {
        "schema_version": 2,
        "system_prompt": sample["system"],
        "user_prompt": sample["input"],
        "lens": "Probe",
        "context_ids": [],
        "context_titles": [],
        "grounding": None,
        "source_text": "",
        "temperature": None,
        "max_tokens": PROBE_MAX_TOKENS,
    }
    if capability_id == "meeting.deferred_analysis":
        payload["response_format"] = {"type": "json_object"}

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
            **_sample_facts(capability_id),
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
        adapter=_sample_adapter(capability_id),
    )
    latency_ms = int((time.monotonic() - started) * 1000)

    receipt = dict(routed.get("receipt") or {})
    outcome = str(receipt.get("outcome") or routed.get("outcome") or "indeterminate")
    winning = dict(routed.get("winning_reservation") or {})
    deployment_id = str(
        receipt.get("winning_deployment_revision_id")
        or winning.get("deployment_revision_id")
        or ""
    )
    facts = _deployment_facts(db, deployment_id)
    boundary = str(receipt.get("winning_boundary") or winning.get("boundary") or "")
    result = routed.get("result") if isinstance(routed.get("result"), Mapping) else {}
    output_field = "summary" if capability_id in {"meeting.deferred_analysis", "background.rails_summary"} else "output"
    output = str((result or {}).get(output_field) or "")
    # The runner has already validated the frozen result schema and the
    # controller has settled its receipt. Preserve that terminal truth even
    # when a valid text result is empty; expose that separate fact to the face.
    ok = outcome == "succeeded"

    return {
        "state": "READY" if ok else "UNREACHABLE",
        "ok": ok,
        "capabilityId": capability_id,
        **_sample_facts(capability_id),
        "sampleOutput": output,
        "emptyOutput": ok and not output.strip(),
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
