"""The disclosed engine chain for deferred Meeting intelligence.

A read of the owner's live assignment for ``meeting.deferred_analysis``
through the engine door (``engine_door.chain``): the engines the next run
will use, in his order. Nothing is planned or frozen. The selection hash
covers the assignment id and the legs, so a run gesture that carries it
is refused when the owner changes the assignment in between.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from ..intel.providers import endpoint_host

SUMMARY_JOB = "meeting.deferred_analysis"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _boundary(value: str) -> str:
    """The public boundary word of a deployment boundary (the assignment
    aliases, then local / lan / cloud)."""
    from .inference_assignment_service import _BOUNDARY_ALIASES

    plain = _BOUNDARY_ALIASES.get(str(value), str(value))
    return {"local": "local", "private_network": "lan", "mesh": "lan", "cloud": "cloud"}.get(plain, plain)


def _host_from_row(row: Any, boundary: str) -> str:
    if row is None:
        return ""
    node = str(row["node"] or "").strip()
    if node:
        return node
    host = endpoint_host(row["endpoint"])
    if host:
        return host
    # A local deployment has no endpoint host by design: its raw boundary word
    # (``same_device``) is the host the faces have always read.
    raw = str(row["boundary"] or boundary)
    plain = {"local": "local", "private_network": "lan", "mesh": "lan", "cloud": "cloud"}.get(raw, raw)
    return "this machine" if plain == "local" else plain


def chain_legs(db: Any, job: str = SUMMARY_JOB) -> tuple[str, list[dict[str, Any]]]:
    """The owner's assignment for ``job`` (``<id>@<revision>``) and its engines as public
    legs: ``{ordinal, host, boundary, profile_id, profile_revision,
    deployment_revision_id}``. ``("", [])`` when nothing is assigned, the
    assigned model cannot do the job, or an engine is not read."""
    from . import engine_door
    from .inference_assignment_service import InferenceAssignmentService

    service = InferenceAssignmentService(db)
    with db._connection() as conn:
        status = service._resolve(conn, service._registry.require(job))["status"]
    if status != "assigned":
        # Nothing assigned, or the assigned model cannot do this job.
        return "", []
    assignment, engines = engine_door.chain(db, job)
    legs: list[dict[str, Any]] = []
    with db._connection() as conn:
        head = conn.execute(
            "SELECT MAX(revision) AS revision FROM inference_assignment_heads WHERE assignment_id=?",
            (assignment,),
        ).fetchone()
        # The assignment's revision: a re-save of the same chain is a new selection.
        assignment = f"{assignment}@{int((head['revision'] if head else 0) or 0)}" if assignment else ""
        for ordinal, engine in enumerate(engines, 1):
            row = conn.execute(
                "SELECT node,endpoint,boundary FROM deployment_revisions WHERE id=?",
                (engine.revision,),
            ).fetchone()
            profile = conn.execute(
                "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                (engine.profile,),
            ).fetchone()
            host = _host_from_row(row, "")
            if not host:
                return "", []
            legs.append({
                "ordinal": ordinal,
                "host": host,
                "boundary": _boundary(str(row["boundary"] or "")),
                "profile_id": engine.profile,
                "profile_revision": int((profile["revision"] if profile else 0) or 0),
                "deployment_revision_id": engine.revision,
            })
    return assignment, legs


def selection_hash(assignment: str, legs: list[dict[str, Any]]) -> str | None:
    """The hash a run gesture carries: the assignment and its legs."""
    if not assignment or not legs:
        return None
    return _hash({"schema": "MeetingDeferredSelection@2", "assignment": assignment, "legs": legs})


#: The route reason when the owner turned summaries OFF (PHILO-15 01 ruling).
SUMMARIES_OFF_REASON = "summaries off"


def route_is_off(route: Mapping[str, Any] | None) -> bool:
    """True when a projected route says the owner turned summaries OFF."""
    return bool(route) and str(route.get("reason_code") or "") == SUMMARIES_OFF_REASON


def summaries_off(db: Any) -> bool:
    """True when the owner turned summaries OFF (the explicit OFF record)."""
    from .inference_assignment_service import InferenceAssignmentService

    try:
        with db._connection() as conn:
            return InferenceAssignmentService.capability_off(conn, "meeting.deferred_analysis")
    except Exception:  # pragma: no cover - a read never blocks the caller
        return False


def unavailable(reason: str = "no assignment") -> dict[str, Any]:
    plain = " ".join(str(reason or "route unavailable").replace("_", " ").split())
    return {"status": "unavailable", "reason_code": plain, "selection_hash": None, "legs": []}


def project_route(db: Any, *, invocation_id: str | None = "preview") -> dict[str, Any]:
    """The summary's engine chain in the settled public shape
    ``{status, reason_code, selection_hash, legs}``. ``invocation_id`` is
    kept for callers; the chain does not depend on it."""
    del invocation_id
    if summaries_off(db):
        # PHILO-15 01: the owner turned summaries OFF; not "no engine".
        return unavailable("summaries_off")
    try:
        assignment, legs = chain_legs(db)
    except Exception as exc:
        return unavailable(getattr(exc, "code", None) or str(exc) or "route unavailable")
    if not legs:
        return unavailable("no assignment")
    return {
        "status": "ready",
        "reason_code": None,
        "selection_hash": selection_hash(assignment, legs),
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
    "chain_legs", "selection_hash", "unavailable", "SUMMARIES_OFF_REASON",
    "route_is_off", "summaries_off",
]


def summary_engine_fact(db: Any) -> dict[str, Any]:
    """PHILO-15 B33: the one "does the summary have an engine" fact for every face.

    The faces that said "no model" (the Settings headline and rows, Settings ›
    Meetings, the Connections Models row, doctor's hub check) read THIS, the
    route the queue would take (``project_route``: exact capability, group and
    global default, OFF first), never an exact-assignment check or the legacy
    ``meeting.intel_profile_id`` config pointer.

    ``engine_set``: True when the route is ready, False when it is not, None
    when the route could not be read.  ``off``: the owner turned summaries
    OFF.  ``host``: where the first leg runs (a LAN host, a node, ``local``).
    """
    try:
        route = summary_route_display(db)
    except Exception:  # pragma: no cover - a read never blocks a face
        return {"engine_set": None, "off": False, "host": None, "profile": None}
    if route.get("status") != "ready" or not route.get("legs"):
        return {"engine_set": False, "off": route_is_off(route), "host": None, "profile": None}
    leg = route["legs"][0]
    host = str(leg.get("node") or "").strip() or str(leg.get("host") or "").strip()
    if host == "this machine" or str(leg.get("boundary") or "") == "local":
        host = host if leg.get("node") else "local"
    return {
        "engine_set": True,
        "off": False,
        "host": host or None,
        "profile": str(leg.get("profile_label") or leg.get("profile_id") or "") or None,
    }
