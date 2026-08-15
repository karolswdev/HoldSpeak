"""The deterministic worker execution revision (HS-131-16, design §3).

The relay revision describes the hub-to-node DESTINATION. Feeding it back through
target resolution would recurse into the mesh, and reading a mutable profile row
at dispatch time would let configuration retarget a run the hub already froze. So
one pure function derives the worker's own execution revision from the signed,
content-addressed relay revision and nothing else.

Both nodes run this function and recompute the same content address, which is what
makes the derived revision part of the signed offer rather than a worker claim.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from ..deployment_revisions import DeploymentRevision
from ..inference_targets import DeploymentIdentity, _private_endpoint
from .refusals import (
    EXECUTION_TARGET_RECURSIVE,
    EXECUTION_TARGET_UNUSABLE,
    MeshAuthorityRefused,
)

#: The relay kind a worker may never execute: it would relay to itself.
MESH_KIND = "mesh_node"


def _usable_endpoint(endpoint: str) -> bool:
    """A parseable absolute http(s) URL with a host — anything else refuses.

    Sol's round-four ruling 2: malformed endpoint parsing is always the fixed
    named refusal, never a silently different destination.
    """
    value = str(endpoint or "").strip()
    if not value:
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def derive_worker_execution_revision(relay_revision: Any) -> DeploymentRevision:
    """The one derivation, pure and total: a revision or a named refusal.

    Destination id, model, endpoint, model path, node, and secret slot come ONLY
    from the signed relay revision; the engine/kind/boundary triple is decided
    here by the artifact the relay revision actually names.
    """
    model_path = str(getattr(relay_revision, "model_path", "") or "").strip()
    endpoint = str(getattr(relay_revision, "endpoint", "") or "").strip()
    if model_path:
        kind, engine, boundary = "this_device", "local", "same_device"
    elif _usable_endpoint(endpoint):
        private = _private_endpoint(endpoint)
        kind = "private_endpoint" if private else "external_service"
        engine = "openai_compatible"
        boundary = "private_network" if private else "external_service"
    else:
        raise MeshAuthorityRefused(EXECUTION_TARGET_UNUSABLE)

    identity = DeploymentIdentity(
        destination_id=str(getattr(relay_revision, "destination_id", "") or ""),
        kind=kind,
        engine=engine,
        model=str(getattr(relay_revision, "model", "") or ""),
        node=str(getattr(relay_revision, "node", "") or ""),
        boundary=boundary,
        model_path=model_path or None,
        endpoint="" if model_path else endpoint,
        secret_slot=str(getattr(relay_revision, "secret_slot", "") or ""),
    )
    if identity.kind == MESH_KIND or not identity.destination_id:
        # Structural, not advisory: a derived mesh kind would send the job back
        # out of this node under authority that was issued for local execution.
        raise MeshAuthorityRefused(EXECUTION_TARGET_RECURSIVE)
    return DeploymentRevision.from_identity(identity)


__all__ = ["MESH_KIND", "derive_worker_execution_revision"]
