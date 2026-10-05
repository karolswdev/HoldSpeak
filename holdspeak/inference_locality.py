"""Where an assignment runs: the one lamp word for a deployment or assignment.

The lamp vocabulary is the egress vocabulary (``intel.providers.
egress_boundary``): ``local``, ``private_network``, ``mesh``, ``cloud``.

A deployment revision stores a boundary word.  An OpenAI-compatible endpoint
on this machine (Ollama, LM Studio, a llama.cpp server on 127.0.0.1) is
stored as ``private_network``, because the endpoint classifier groups
loopback with private ranges.  The lamp reads the endpoint itself through
``loopback_http.endpoint_lamp``: ``local`` only for a loopback IP literal or
the word ``localhost`` (pinned to 127.0.0.1 at every connect); any other name
is at best ``private_network`` (Article III).

This module reads SQLite rows only.  Any layer can import it.
"""
from __future__ import annotations

from typing import Any

#: Lamp words, from the most private to the least.
LAMP_RANK = {"local": 0, "mesh": 1, "private_network": 2, "cloud": 3}

_BOUNDARY_LAMP = {
    "same_device": "local",
    "local": "local",
    "private_network": "private_network",
    "lan": "private_network",
    "private_mesh": "mesh",
    "mesh": "mesh",
    "paired": "mesh",
    "paired_device": "mesh",
    "cloud": "cloud",
    "external_service": "cloud",
}


def deployment_lamp(boundary: Any, endpoint: Any = "") -> str:
    """The lamp word for one deployment: local, private_network, mesh, cloud.

    A deployment with an endpoint is read through the one egress classifier,
    so a loopback endpoint is ``local``.  ``unknown`` when nothing is known.
    """
    word = _BOUNDARY_LAMP.get(str(boundary or "").strip(), "")
    endpoint = str(endpoint or "").strip()
    if endpoint and word != "mesh":
        # The endpoint decides, through the ONE classifier
        # (intel.providers.egress_boundary via loopback_http.endpoint_lamp):
        # LOCAL only where every connect pins loopback (#855).
        from .loopback_http import endpoint_lamp

        return endpoint_lamp(endpoint)
    return word or "unknown"


#: Send phases at which the request bytes may have left for the engine.
_SENT_PHASES = frozenset({
    "dispatch_intent", "provider_no_generation", "provider_returned",
    "physical_outcome_unknown",
})


def _attempt_route(conn: Any, attempt: dict) -> dict[str, str]:
    """The lamp, host and model of the deployment one attempt was sent to."""
    row = conn.execute(
        "SELECT model,endpoint,node FROM deployment_revisions WHERE id=?",
        (str(attempt.get("deployment_revision_id") or ""),),
    ).fetchone()
    endpoint = str(row["endpoint"] or "") if row else ""
    node = str(row["node"] or "") if row else ""
    lamp = deployment_lamp(attempt.get("boundary"), endpoint)
    if lamp not in LAMP_RANK:
        # Bytes went to a destination this hub cannot name: the least
        # private lamp, never a quieter one.
        lamp = "cloud"
    if lamp == "local":
        host = ""
    elif lamp == "mesh":
        host = node
    else:
        from urllib.parse import urlparse

        host = (urlparse(endpoint).hostname or "") if endpoint else node
    return {"lamp": lamp, "host": host, "model": str(row["model"] or "") if row else ""}


def served_route(conn: Any, receipt: Any) -> dict[str, Any] | None:
    """Where one routed run's bytes went, read from its execution receipt.

    The route is the LEAST PRIVATE attempt that was sent (any send phase past
    dispatch), so a cloud attempt is never hidden behind a local fallback; on
    a tie, the winner.  ``fallback`` is True when the winner is another
    attempt.  ``receipt`` is this receipt's execution id: the token belongs to
    the route shown.  ``lamp`` is "" when no attempt was sent (no model call:
    no lamp).  ``None`` when ``receipt`` is not a route execution receipt (no
    ``attempts``).  Lamps come from ``deployment_lamp`` (the one classifier).
    """
    if not isinstance(receipt, dict) or not isinstance(receipt.get("attempts"), list):
        return None
    execution = str(receipt.get("execution_id") or receipt.get("id") or "")
    winner = str(receipt.get("winning_attempt_id") or "")
    best: tuple[tuple[int, int, int], dict[str, Any]] | None = None
    for index, attempt in enumerate(receipt["attempts"]):
        if not isinstance(attempt, dict) or str(attempt.get("send_phase") or "") not in _SENT_PHASES:
            continue
        route = _attempt_route(conn, attempt)
        won = bool(winner) and str(attempt.get("attempt_id") or "") == winner
        key = (LAMP_RANK[route["lamp"]], int(won), index)
        if best is None or key > best[0]:
            best = (key, {**route, "fallback": bool(winner) and not won})
    if best is None:
        return {"lamp": "", "host": "", "model": "", "receipt": execution, "fallback": False}
    return {**best[1], "receipt": execution}


def least_private(routes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Of several passes' routes, the least private one that sent bytes (on a
    tie, the later pass); None when no pass sent any."""
    sent = [(LAMP_RANK[r["lamp"]], i, r) for i, r in enumerate(routes) if r and r.get("lamp")]
    return max(sent, key=lambda item: item[:2])[2] if sent else None


def _entry_lamp(conn: Any, row: Any) -> str:
    profile_id = str(row["profile_id"])
    if int(row["profile_schema_version"] or 2) == 1:
        legacy = conn.execute(
            "SELECT kind,base_url FROM profiles WHERE id=? AND deleted=0",
            (profile_id.removeprefix("legacy-"),),
        ).fetchone()
        if legacy is None:
            return "unknown"
        kind = str(legacy["kind"] or "")
        if kind == "onDevice":
            return "local"
        if kind in {"meshNode", "desktop"}:
            return "mesh"
        if kind == "openAICompatible":
            return deployment_lamp("private_network", legacy["base_url"])
        return "unknown"
    binding = conn.execute(
        """SELECT b.deployment_revision_id FROM model_profile_binding_heads h
             JOIN model_profile_binding_revisions b
               ON b.binding_id=h.binding_id AND b.revision=h.revision
            WHERE h.profile_id=? AND b.profile_revision=?""",
        (profile_id, int(row["profile_revision"])),
    ).fetchone()
    if binding is None:
        return "unknown"
    deployment = conn.execute(
        "SELECT boundary,endpoint FROM deployment_revisions WHERE id=?",
        (binding["deployment_revision_id"],),
    ).fetchone()
    if deployment is None:
        return "unknown"
    return deployment_lamp(deployment["boundary"], deployment["endpoint"])


def assignment_lamp(conn: Any, assignment_id: str, revision: int) -> str:
    """The least private lamp of every model in one assignment revision.

    ``unknown`` when an entry does not resolve; a caller that needs
    ``local`` treats ``unknown`` as not local.
    """
    rows = conn.execute(
        """SELECT profile_id,profile_revision,profile_schema_version
             FROM inference_assignments
            WHERE assignment_id=? AND assignment_revision=? ORDER BY ordinal""",
        (str(assignment_id), int(revision)),
    ).fetchall()
    if not rows:
        return "unknown"
    lamps = [_entry_lamp(conn, row) for row in rows]
    if any(lamp not in LAMP_RANK for lamp in lamps):
        return "unknown"
    return max(lamps, key=lambda lamp: LAMP_RANK[lamp])


#: The kernel operation the batteries-included default writes as evidence
#: (services/inference_default_service.py).
AUTO_ASSIGNED_OPERATION = "inference.default_assigned"


def made_by_holdspeak(conn: Any, assignment_id: str, revision: int) -> bool:
    """True when this exact assignment revision was the product's own write.

    The source of truth is the revision's ``made_by`` column, written in the
    same transaction as the revision.  The receipt is evidence only: a lost
    receipt never turns the product's default into an owner press.
    """
    row = conn.execute(
        "SELECT made_by FROM inference_assignment_revisions WHERE assignment_id=? AND revision=?",
        (str(assignment_id), int(revision)),
    ).fetchone()
    return row is not None and str(row["made_by"]) == "holdspeak_default"


def head_lamp(conn: Any, assignment_key: str) -> str | None:
    """The lamp of the live head at ``assignment_key``; None when there is none."""
    row = conn.execute(
        "SELECT assignment_id,revision FROM inference_assignment_heads"
        " WHERE assignment_key=? AND cleared=0",
        (assignment_key,),
    ).fetchone()
    if row is None:
        return None
    return assignment_lamp(conn, str(row["assignment_id"]), int(row["revision"]))


__all__ = [
    "AUTO_ASSIGNED_OPERATION", "LAMP_RANK", "assignment_lamp", "deployment_lamp", "least_private", "served_route",
    "head_lamp", "made_by_holdspeak",
]
