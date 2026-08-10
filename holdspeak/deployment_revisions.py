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


def capture_deployment_revision(
    db: Any, target: InferenceTarget | DeploymentIdentity, *, conn: Any | None = None,
) -> DeploymentRevision:
    """Persist and return the exact deployment admission is about to name."""
    identity = target.deployment if isinstance(target, InferenceTarget) else target
    if identity is None:
        raise ValueError("resolved target has no deployment identity")
    revision = DeploymentRevision.from_identity(identity)
    if conn is None:
        db.deployment_revisions.upsert(revision)
    else:
        conn.execute(
            """INSERT OR IGNORE INTO deployment_revisions
               (id, destination_id, kind, engine, model, node, boundary, endpoint, model_path, secret_slot)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (revision.id, revision.destination_id, revision.kind, revision.engine, revision.model,
             revision.node, revision.boundary, revision.endpoint, revision.model_path, revision.secret_slot),
        )
    return revision


def resolve_workbench_deployment_revision(conn: Any, workbench_id: str) -> DeploymentRevision | None:
    """Rebuild a Workbench's live effective deployment from one SQLite snapshot."""
    from .db.models import ProfileRecord
    from .inference_targets import GLOBAL_DEFAULT_TARGET_ID, resolve_inference_target, target_from_profile

    workbench = conn.execute("SELECT profile_id,recipe_id FROM workbenches WHERE id=? AND deleted=0", (workbench_id,)).fetchone()
    if workbench is None:
        return None
    recipe = conn.execute("SELECT profile_id FROM recipes WHERE id=? AND deleted=0", (str(workbench["recipe_id"] or ""),)).fetchone()
    recipe_profile = str(recipe["profile_id"] or "") if recipe is not None else ""
    profile_id = str(workbench["profile_id"] or "") or recipe_profile
    if not profile_id:
        target = resolve_inference_target(None, GLOBAL_DEFAULT_TARGET_ID)
    else:
        row = conn.execute("SELECT * FROM profiles WHERE id=? AND deleted=0", (profile_id,)).fetchone()
        if row is None:
            return None
        profile = ProfileRecord(id=str(row["id"]), name=str(row["name"] or ""), kind=str(row["kind"] or ""), model_file=str(row["model_file"] or ""), base_url=str(row["base_url"] or ""), model=str(row["model"] or ""), node=str(row["node"] or ""), context_limit=int(row["context_limit"] or 16384), requires_key=bool(row["requires_key"]), created_at=str(row["created_at"] or ""), last_modified=str(row["last_modified"] or ""), deleted=bool(row["deleted"]))
        target = target_from_profile(profile)
    return DeploymentRevision.from_identity(target.deployment) if target.deployment is not None else None


def resolve_deployment_revision(db: Any, revision_id: str) -> DeploymentRevision | None:
    """Resolve an admitted revision without consulting mutable profile state."""
    return db.deployment_revisions.get(revision_id)
