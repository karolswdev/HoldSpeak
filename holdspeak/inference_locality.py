"""Where an assignment runs: the one lamp word for a deployment or assignment.

The lamp vocabulary is the egress vocabulary (``intel.providers.
egress_boundary``): ``local``, ``private_network``, ``mesh``, ``cloud``.

A deployment revision stores a boundary word.  An OpenAI-compatible endpoint
on this machine (Ollama, LM Studio, a llama.cpp server on 127.0.0.1) is
stored as ``private_network``, because the endpoint classifier groups
loopback with private ranges.  The lamp reads the endpoint itself through the
one egress classifier, so a loopback endpoint is ``local``: nothing leaves
the machine (Article III).

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
    if endpoint and word in {"private_network", "cloud", ""}:
        from .intel.providers import egress_boundary

        return egress_boundary(cloud=True, base_url=endpoint)
    return word or "unknown"


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


__all__ = ["LAMP_RANK", "assignment_lamp", "deployment_lamp", "head_lamp"]
