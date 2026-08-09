"""Immutable deployment revisions captured before model dispatch (HS-131-01)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .inference_targets import DeploymentIdentity, InferenceTarget


@dataclass(frozen=True)
class DeploymentRevision:
    """Content-addressed execution specification with no credential material."""

    id: str
    destination_id: str
    kind: str
    engine: str
    model: str
    node: str
    boundary: str
    endpoint: str
    model_path: str | None
    secret_slot: str

    @classmethod
    def from_identity(cls, identity: DeploymentIdentity) -> "DeploymentRevision":
        fields = {
            "destination_id": identity.destination_id,
            "kind": identity.kind,
            "engine": identity.engine,
            "model": identity.model,
            "node": identity.node,
            "boundary": identity.boundary,
            "endpoint": identity.endpoint,
            "model_path": identity.model_path,
            "secret_slot": identity.secret_slot,
        }
        encoded = json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return cls(id="dep_" + hashlib.sha256(encoded.encode()).hexdigest(), **fields)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def identity(self) -> DeploymentIdentity:
        return DeploymentIdentity(
            destination_id=self.destination_id,
            kind=self.kind,
            engine=self.engine,
            model=self.model,
            node=self.node,
            boundary=self.boundary,
            model_path=self.model_path,
            endpoint=self.endpoint,
            secret_slot=self.secret_slot,
        )


def capture_deployment_revision(db: Any, target: InferenceTarget | DeploymentIdentity) -> DeploymentRevision:
    """Persist and return the exact deployment admission is about to name."""
    identity = target.deployment if isinstance(target, InferenceTarget) else target
    if identity is None:
        raise ValueError("resolved target has no deployment identity")
    revision = DeploymentRevision.from_identity(identity)
    db.deployment_revisions.upsert(revision)
    return revision


def resolve_deployment_revision(db: Any, revision_id: str) -> DeploymentRevision | None:
    """Resolve an admitted revision without consulting mutable profile state."""
    return db.deployment_revisions.get(revision_id)
