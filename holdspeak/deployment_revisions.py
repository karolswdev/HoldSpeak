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
    schema_version: int = 1
    runtime_id: str = ""
    runtime_revision: str = ""
    artifact_id: str = ""
    manifest_sha256: str = ""
    format: str = ""
    architecture: str = ""
    context_ceiling: int = 0
    capability_sha256: str = ""

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
        value = asdict(self)
        if self.schema_version == 1:
            # Phase 131 v1 is an immutable public/sync contract. New v2 fields
            # must not alter its serialized bytes or content identity.
            for key in (
                "schema_version", "runtime_id", "runtime_revision", "artifact_id",
                "manifest_sha256", "format", "architecture", "context_ceiling",
                "capability_sha256",
            ):
                value.pop(key, None)
        else:
            # V2 is locator-free by construction. Resolution may attach a
            # private path in memory for the physical leaf; it never serializes.
            value.pop("model_path", None)
        return value

    @classmethod
    def from_artifact(
        cls,
        *,
        destination_id: str,
        engine: str,
        model: str,
        runtime_id: str,
        runtime_revision: str,
        artifact_id: str,
        manifest_sha256: str,
        format: str,
        architecture: str,
        context_ceiling: int,
        capability_sha256: str,
        resolved_model_path: str | None = None,
    ) -> "DeploymentRevision":
        identity = {
            "schema_version": 2,
            "destination_id": destination_id,
            "kind": "this_device",
            "engine": engine,
            "model": model,
            "node": "",
            "boundary": "same_device",
            "endpoint": "",
            "secret_slot": "",
            "runtime_id": runtime_id,
            "runtime_revision": runtime_revision,
            "artifact_id": artifact_id,
            "manifest_sha256": manifest_sha256,
            "format": format,
            "architecture": architecture,
            "context_ceiling": int(context_ceiling),
            "capability_sha256": capability_sha256,
        }
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return cls(
            id="dep2_" + hashlib.sha256(encoded.encode()).hexdigest(),
            model_path=resolved_model_path,
            **identity,
        )

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
    revision = _artifact_revision_for_identity(db, identity, conn=conn)
    if revision is None:
        revision = DeploymentRevision.from_identity(identity)
    if conn is None:
        db.deployment_revisions.upsert(revision)
    else:
        conn.execute(
            """INSERT OR IGNORE INTO deployment_revisions
               (id, schema_version, destination_id, kind, engine, model, node,
                boundary, endpoint, model_path, secret_slot, runtime_id,
                runtime_revision, artifact_id, manifest_sha256, format,
               architecture, context_ceiling, capability_sha256)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                revision.id, revision.schema_version, revision.destination_id,
                revision.kind, revision.engine, revision.model, revision.node,
                revision.boundary, revision.endpoint,
                revision.model_path if revision.schema_version == 1 else None,
                revision.secret_slot, revision.runtime_id,
                revision.runtime_revision, revision.artifact_id,
                revision.manifest_sha256, revision.format,
                revision.architecture, revision.context_ceiling,
                revision.capability_sha256,
            ),
        )
    return revision


def _artifact_revision_for_identity(
    db: Any, identity: DeploymentIdentity, *, conn: Any | None = None,
) -> DeploymentRevision | None:
    """Return the active locator-free v2 revision for an owned artifact path."""
    locator = str(identity.model_path or "").strip()
    if not locator:
        return None
    owns_connection = conn is None
    if owns_connection:
        context = db._connection()
        conn = context.__enter__()
    try:
        row = conn.execute(
            """SELECT d.*, a.local_locator, a.manifest_sha256, a.format
                 FROM inference_deployments d
                 JOIN inference_model_artifacts a ON a.artifact_id=d.artifact_id
                WHERE d.active=1 AND a.state='verified' AND a.local_locator=?
                ORDER BY d.configuration_revision DESC LIMIT 1""",
            (locator,),
        ).fetchone()
        if row is None:
            return None
        return DeploymentRevision.from_artifact(
            destination_id=str(row["destination_id"]),
            engine="configured_local_engine",
            model=str(row["model_identity"]),
            runtime_id=str(row["runtime_id"]),
            runtime_revision=str(row["runtime_revision"]),
            artifact_id=str(row["artifact_id"]),
            manifest_sha256=str(row["manifest_sha256"]),
            format=str(row["format"]),
            architecture="qwen3.5",
            context_ceiling=int(row["context_ceiling"]),
            capability_sha256=str(row["capability_sha256"]),
            resolved_model_path=locator,
        )
    finally:
        if owns_connection:
            context.__exit__(None, None, None)


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
    revision = db.deployment_revisions.get(revision_id)
    if revision is None or revision.schema_version == 1:
        return revision
    with db._connection() as conn:
        row = conn.execute(
            """SELECT local_locator, manifest_sha256, format, state
                 FROM inference_model_artifacts WHERE artifact_id=?""",
            (revision.artifact_id,),
        ).fetchone()
    if (
        row is None
        or str(row["state"]) != "verified"
        or str(row["manifest_sha256"]) != revision.manifest_sha256
        or str(row["format"]) != revision.format
    ):
        return None
    return DeploymentRevision(
        **{
            **asdict(revision),
            "model_path": str(row["local_locator"]),
        }
    )
