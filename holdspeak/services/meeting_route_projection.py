"""The disclosed SERVICE route for deferred Meeting intelligence.

This module is intentionally a read-only projection.  It asks the same route
planner and feature principal that the queue binder uses, then removes planner
identifiers and timestamps from the public selection hash.  Historical jobs
retain their stored route; the Meeting next-run read resolves the current
selection so a repaired assignment can be disclosed and run again.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from ..intel.providers import endpoint_host
from ..meeting_session.deferred_bound import PARENT_KIND, queue_service_principal
from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY, InferenceRoutePlanService


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _boundary(value: str) -> str:
    return {"local": "local", "private_network": "lan", "mesh": "lan", "cloud": "cloud"}.get(
        str(value), str(value)
    )


def _host_from_row(row: Any, boundary: str) -> str:
    if row is None:
        return ""
    node = str(row["node"] or "").strip()
    if node:
        return node
    host = endpoint_host(row["endpoint"])
    if host:
        return host
    # A local deployment has no endpoint host by design.  This is the route's
    # actual bound destination, not a mutable-config fallback.
    return "this machine" if _boundary(str(row["boundary"] or boundary)) == "local" else _boundary(
        str(row["boundary"] or boundary)
    )


def _public_legs(conn: Any, route: Mapping[str, Any]) -> list[dict[str, Any]]:
    legs: list[dict[str, Any]] = []
    for entry in route.get("entries", ()):
        deployment_id = str(entry.get("deployment_revision_id") or "")
        row = conn.execute(
            "SELECT node,endpoint,boundary FROM deployment_revisions WHERE id=?",
            (deployment_id,),
        ).fetchone()
        host = _host_from_row(row, str(entry.get("boundary") or ""))
        if not deployment_id or not host:
            return []
        legs.append(
            {
                "ordinal": int(entry["ordinal"]),
                "host": host,
                "boundary": _boundary(str(entry["boundary"])),
                "profile_id": str(entry["profile_id"]),
                "profile_revision": int(entry["profile_revision"]),
                "deployment_revision_id": deployment_id,
            }
        )
    return legs


def _selection_material(route: Mapping[str, Any], legs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "MeetingDeferredSelection@1",
        "capability": dict(route["capability"]),
        "source": dict(route["source"]),
        "entries": [dict(item) for item in route.get("entries", ())],
        "retry_policy": dict(route["retry_policy"]),
        "operation_policy_revision": str(route["operation_policy_revision"]),
        "legs": legs,
    }


def selection_hash_for_route_plan(db_or_connection: Any, route: Mapping[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    """Hash one resolved or frozen plan using the exact public selection material.

    The queue binder calls this with its claim transaction after freezing the
    route.  That closes the prepare-to-claim race against an assignment change;
    it never reuses a mutable preview hash as proof of the bound plan.
    """
    if hasattr(db_or_connection, "execute"):
        legs = _public_legs(db_or_connection, route)
        return (_hash(_selection_material(route, legs)) if legs else None), legs
    with db_or_connection._connection() as conn:
        legs = _public_legs(conn, route)
    return (_hash(_selection_material(route, legs)) if legs else None), legs


def unavailable(reason: str = "no assignment") -> dict[str, Any]:
    plain = " ".join(str(reason or "route unavailable").replace("_", " ").split())
    return {"status": "unavailable", "reason_code": plain, "selection_hash": None, "legs": []}


def project_route(db: Any, *, invocation_id: str | None = "preview") -> dict[str, Any]:
    """Resolve the Meeting SERVICE route into the settled public shape."""
    try:
        route = InferenceRoutePlanService(db).resolve_route_plan_for_feature(
            ROUTE_PLANNING_AUTHORITY,
            feature_principal=queue_service_principal(),
            parent_kind=PARENT_KIND,
            capability_id="meeting.deferred_analysis",
            invocation_id=invocation_id,
        )
    except Exception as exc:
        reason = getattr(exc, "code", None) or str(exc) or "route unavailable"
        return unavailable(reason)

    _selection_hash, legs = selection_hash_for_route_plan(db, route)
    if not legs:
        return unavailable("route unavailable")
    # The generated route-plan ID and its timestamps are absent. Preserve the
    # full authority material that chooses the route, including policy identity
    # and hashes even when two policies use the same numeric revision.
    return {
        "status": "ready",
        "reason_code": None,
        "selection_hash": _selection_hash,
        "legs": legs,
    }


def summary_route_display(db: Any) -> dict[str, Any]:
    """Add display metadata to the assigned summary route.

    ``project_route`` is the selection authority and its public leg/hash shape
    is intentionally closed.  Trust and Doctor need two safe labels from the
    same immutable revisions, so this adapter enriches a copy for display.
    It does not persist, resolve a second route, or contact a destination.
    """
    route = project_route(db)
    if route.get("status") != "ready":
        return route

    display_legs: list[dict[str, Any]] = []
    with db._connection() as conn:
        for leg in route.get("legs", ()):
            profile = conn.execute(
                "SELECT label FROM model_profile_revisions "
                "WHERE profile_id=? AND revision=?",
                (str(leg.get("profile_id") or ""), int(leg.get("profile_revision") or 0)),
            ).fetchone()
            deployment = conn.execute(
                "SELECT node FROM deployment_revisions WHERE id=?",
                (str(leg.get("deployment_revision_id") or ""),),
            ).fetchone()
            display_legs.append(
                {
                    **leg,
                    "profile_label": "" if profile is None else str(profile["label"] or ""),
                    "node": "" if deployment is None else str(deployment["node"] or ""),
                }
            )
    return {**route, "legs": display_legs}


def route_from_job(job: Any) -> dict[str, Any] | None:
    """Return the immutable route stored on a job, if one exists."""
    value = getattr(job, "planned_route", None)
    if isinstance(value, Mapping):
        return dict(value)
    return None


def require_expected_selection(route: Mapping[str, Any], expected: Any) -> None:
    """Enforce the point-of-decision binding carried by a run gesture."""
    from .errors import ConflictError

    if route.get("status") != "ready":
        raise ConflictError("The summary route is not available.", code="route_unavailable")
    supplied = str(expected or "").strip()
    if not supplied:
        raise ConflictError(
            "Check the summary route, then try again.",
            code="selection_hash_required",
        )
    if supplied != str(route.get("selection_hash") or ""):
        raise ConflictError(
            "The summary route changed. Check it, then try again.",
            code="selection_drift",
        )


__all__ = [
    "project_route", "summary_route_display", "route_from_job", "require_expected_selection",
    "selection_hash_for_route_plan", "unavailable",
]
