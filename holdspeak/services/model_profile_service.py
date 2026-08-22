"""Phase 143's hub-local reusable model-profile authority.

This module intentionally owns only reusable model identity and its local
binding to Phase 142 deployment truth.  It does not resolve capabilities,
assignments, routes, providers, or execution.  Those are subsequent Phase 143
authorities and must consume these immutable records rather than grow a second
registry beside them.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from ..deployment_revisions import DeploymentIdentity, DeploymentRevision
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound, ServiceError, ValidationError


_PROFILE_ID = re.compile(r"^[a-z][a-z0-9_-]{0,95}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_CONTEXT_SUPPORT = frozenset({"exact", "bounded", "unavailable"})
_FORBIDDEN_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "base_url",
        "credential",
        "endpoint",
        "local_locator",
        "locator",
        "model_file",
        "password",
        "path",
        "secret",
        "secret_slot",
        "token",
        "url",
    }
)
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_SECRET_LIKE = re.compile(
    r"(?:\b(?:api[_-]?key|token|secret|authorization)\s*[:=]|\bbearer\s+|^sk-[A-Za-z0-9_-]{8,}$)",
    re.IGNORECASE,
)
_MAX_JSON_BYTES = 16 * 1024
_MAX_JSON_DEPTH = 8
_MAX_JSON_ITEMS = 256
_TOKENIZER_REQUIREMENT_FIELDS = frozenset(
    {
        "tokenizer_id",
        "chat_template",
        "tool_call_template",
        "requires_bos_token",
        "requires_eos_token",
    }
)
_SAFE_PRESENTATION_FIELDS = frozenset({"summary", "badge"})
_LEGACY_RUNTIME_FAMILIES = {
    "legacy_local": frozenset({"configured_local_engine", "llama_cpp_prompt_v1", "mlx_text_v1"}),
    "openai_compatible_v1": frozenset({"openai_compatible", "openai_compatible_v1"}),
    "mesh_relay_v1": frozenset({"mesh_relay", "node_runtime"}),
    "paired_device_v1": frozenset({"paired_runtime", "configured_hub_engine"}),
}

DependencyProvider = Callable[[Any, str], list[dict[str, str]]]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _text(value: Any, *, field: str, limit: int = 500) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string", code="model_profile_invalid")
    text = value.strip()
    if not text or len(text) > limit or any(ord(char) < 32 for char in text):
        raise ValidationError(f"{field} is invalid", code="model_profile_invalid")
    return text


def _safe_text(value: Any, *, field: str, limit: int = 500) -> str:
    text = _text(value, field=field, limit=limit)
    if text.startswith("~") or Path(text).is_absolute() or _WINDOWS_ABSOLUTE.match(text):
        raise ValidationError(
            f"{field} must not contain a local locator", code="model_profile_private_material"
        )
    if "://" in text:
        raise ValidationError(
            f"{field} must not contain an endpoint", code="model_profile_private_material"
        )
    if _SECRET_LIKE.search(text):
        raise ValidationError(
            f"{field} must not contain a credential", code="model_profile_private_material"
        )
    return text


def _require_json(value: Any, *, field: str, kind: type) -> Any:
    if not isinstance(value, kind):
        noun = "object" if kind is dict else "array"
        raise ValidationError(f"{field} must be an {noun}", code="model_profile_invalid")
    return value


def _closed_object(value: Any, *, field: str, allowed: frozenset[str]) -> dict[str, Any]:
    obj = _require_json(value, field=field, kind=dict)
    if set(obj) - allowed:
        raise ValidationError(f"{field} has an invalid shape", code="model_profile_invalid")
    return obj


def _forbid_private_material(value: Any, *, field: str = "profile") -> None:
    """Refuse recursively rather than accidentally admitting a nested secret.

    A model identity can contain a provider/model slug, but no endpoint, local
    locator, credential field, or URL.  The binding resolves those private
    details by following the existing deployment head instead.
    """
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in _FORBIDDEN_KEYS:
                raise ValidationError(
                    f"{field} must not contain {key}", code="model_profile_private_material"
                )
            _forbid_private_material(child, field=field)
    elif isinstance(value, list):
        for child in value:
            _forbid_private_material(child, field=field)
    elif isinstance(value, str):
        if value.startswith("~") or Path(value).is_absolute() or _WINDOWS_ABSOLUTE.match(value):
            raise ValidationError(
                f"{field} must not contain a local locator", code="model_profile_private_material"
            )
        if "://" in value:
            raise ValidationError(
                f"{field} must not contain an endpoint", code="model_profile_private_material"
            )
        if _SECRET_LIKE.search(value):
            raise ValidationError(
                f"{field} must not contain a credential", code="model_profile_private_material"
            )


def _bounded_json(value: Any, *, field: str, depth: int = 0) -> None:
    if depth > _MAX_JSON_DEPTH:
        raise ValidationError(f"{field} is too deeply nested", code="model_profile_invalid")
    if isinstance(value, dict):
        if len(value) > _MAX_JSON_ITEMS:
            raise ValidationError(f"{field} has too many fields", code="model_profile_invalid")
        for child in value.values():
            _bounded_json(child, field=field, depth=depth + 1)
    elif isinstance(value, list):
        if len(value) > _MAX_JSON_ITEMS:
            raise ValidationError(f"{field} has too many entries", code="model_profile_invalid")
        for child in value:
            _bounded_json(child, field=field, depth=depth + 1)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValidationError(f"{field} must contain JSON values", code="model_profile_invalid")
    try:
        encoded = _canonical(value).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must contain JSON values", code="model_profile_invalid") from exc
    if len(encoded) > _MAX_JSON_BYTES:
        raise ValidationError(f"{field} is too large", code="model_profile_invalid")


def _legacy_public_text(value: Any, *, fallback: str, limit: int = 300) -> str:
    """Use historical text only when it cannot be a locator or endpoint."""
    if not isinstance(value, str):
        return fallback
    text = value.strip()
    if (
        not text
        or len(text) > limit
        or any(ord(char) < 32 for char in text)
        or text.startswith("~")
        or Path(text).is_absolute()
        or _WINDOWS_ABSOLUTE.match(text)
        or "://" in text
        or _SECRET_LIKE.search(text)
    ):
        return fallback
    return text


@dataclass(frozen=True)
class ModelProfileRevision:
    """Immutable, locator-free reusable execution intent (ModelProfileRevision@2)."""

    profile_id: str
    revision: int
    sha256: str
    label: str
    provider_family: str
    runtime_family: str
    model_or_artifact_identity: str
    supported_modalities: tuple[str, ...]
    context_support: str
    tokenizer_template_requirements: dict[str, Any]
    capability_manifest: dict[str, Any]
    safe_presentation: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "profile_id": self.profile_id,
            "revision": self.revision,
            "sha256": self.sha256,
            "label": self.label,
            "provider_family": self.provider_family,
            "runtime_family": self.runtime_family,
            "model_or_artifact_identity": self.model_or_artifact_identity,
            "supported_modalities": list(self.supported_modalities),
            "context_support": self.context_support,
            "tokenizer_template_requirements": dict(self.tokenizer_template_requirements),
            "capability_manifest": dict(self.capability_manifest),
            "safe_presentation": dict(self.safe_presentation),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ProfileBinding:
    """The current projection of one revisioned hub-local binding.

    Secret-slot and readiness-observation references remain private storage
    facts.  They deliberately do not appear in this ordinary projection.
    """

    binding_id: str
    revision: int
    profile_id: str
    profile_revision: int
    deployment_head_id: str
    deployment_configuration_revision: int
    deployment_revision_id: str
    enabled: bool
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "binding_id": self.binding_id,
            "revision": self.revision,
            "profile_id": self.profile_id,
            "profile_revision": self.profile_revision,
            "deployment_head_id": self.deployment_head_id,
            "deployment_configuration_revision": self.deployment_configuration_revision,
            "deployment_revision_id": self.deployment_revision_id,
            "enabled": self.enabled,
            "updated_at": self.updated_at,
        }


def adapt_v1_profile(profile: Any) -> dict[str, Any]:
    """Return one deterministic, read-only v1 compatibility view.

    The adapter never writes ``profiles`` or creates a v2 binding.  All public
    fields remain locator-free; it carries no fingerprint of a local path or
    endpoint either.  Phase 143 route adoption can use this narrow view until
    a profile is deliberately recreated as a v2 profile.
    """
    raw = profile.to_dict() if hasattr(profile, "to_dict") else {
        key: getattr(profile, key, "")
        for key in (
            "id", "name", "kind", "model_file", "base_url", "model", "node",
            "context_limit", "requires_key", "created_at", "last_modified", "deleted",
        )
    }

    profile_id = str(raw.get("id") or "").strip()
    if not profile_id:
        raise ValueError("legacy profile id is required")
    kind = str(raw.get("kind") or "onDevice")
    identity = _legacy_public_text(
        raw.get("model"), fallback=f"legacy-profile-{profile_id}"
    )
    label = _legacy_public_text(raw.get("name"), fallback=identity, limit=200)
    provider_family = {
        "onDevice": "local",
        "openAICompatible": "openai_compatible",
        "meshNode": "mesh",
        "desktop": "paired_device",
    }.get(kind, "legacy")
    runtime_family = {
        "onDevice": "legacy_local",
        "openAICompatible": "openai_compatible_v1",
        "meshNode": "mesh_relay_v1",
        "desktop": "paired_device_v1",
    }.get(kind, "legacy_v1")
    manifest = {
        "revision": "legacy-v1",
        "claims": [],
    }
    manifest["sha256"] = _sha256(manifest)
    revision_material = {
        "schema_version": 2,
        "profile_id": f"legacy-{profile_id}",
        "revision": 1,
        "label": label,
        "provider_family": provider_family,
        "runtime_family": runtime_family,
        "model_or_artifact_identity": identity,
        "supported_modalities": ["language"],
        "context_support": "bounded",
        "tokenizer_template_requirements": {},
        "capability_manifest": manifest,
        "safe_presentation": {"source": "legacy-v1"},
    }
    revision_material["sha256"] = _sha256(revision_material)
    return {
        "legacy": True,
        "source_schema_version": 1,
        "source_id": profile_id,
        "profile": revision_material,
        "binding": {
            "legacy": True,
            "binding_id": f"legacy-binding-{profile_id}",
            "revision": 1,
            "profile_id": revision_material["profile_id"],
            "profile_revision": 1,
            # This is explicitly an adapter marker, never a persisted head.
            "deployment_head_id": f"legacy-v1-{profile_id}",
            "deployment_revision_id": None,
            "enabled": True,
        },
    }


@dataclass(frozen=True)
class LegacyV1ExecutionAdapter:
    """Read-only execution bridge for one historical ProfileRecord.

    This intentionally keeps private transport material in the existing v1
    deployment object until its legacy parent migrates.  It does not persist a
    v2 row/binding, change the legacy bytes, or publish those details.
    """

    source_profile_id: str
    source_last_modified: str
    deployment_revision: DeploymentRevision
    receipt: dict[str, Any]


def resolve_v1_profile_execution(profile: Any, *, db: Any = None) -> LegacyV1ExecutionAdapter:
    """Resolve historical v1 bytes through the existing target adapter only."""
    from ..inference_targets import target_from_profile

    target = target_from_profile(profile, db=db)
    if target.deployment is None:
        raise NotFound("legacy deployment", str(getattr(profile, "id", "")))
    revision = DeploymentRevision.from_identity(target.deployment)
    return LegacyV1ExecutionAdapter(
        source_profile_id=str(getattr(profile, "id", "")),
        source_last_modified=str(getattr(profile, "last_modified", "")),
        deployment_revision=revision,
        receipt=target.placement_receipt(),
    )


class ModelProfileService:
    """OWNER-only authority for profile revision and binding truth."""

    def __init__(
        self,
        db: Any,
        *,
        dependency_providers: Mapping[str, DependencyProvider] | None = None,
    ) -> None:
        self._db = db
        # Deletion must name authoritative consumers; it never searches JSON
        # blobs heuristically.  Later assignment/plan stores register exact
        # providers here instead of changing this profile authority's schema.
        self._dependency_providers: dict[str, DependencyProvider] = {
            "binding_heads": self._binding_dependencies,
            "deployment_material": self._deployment_material_dependencies,
            "assignment_store": self._assignment_dependencies,
            "route_plan_store": self._route_plan_dependencies,
        }
        if dependency_providers:
            self._dependency_providers.update(dependency_providers)

    @staticmethod
    def _require_owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "owner_principal_required", "Owner access is required", context={"status": 403}
            )

    def list_profiles(self, principal: Principal, *, include_legacy: bool = True) -> dict[str, Any]:
        self._require_owner(principal)
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT r.* FROM model_profile_revisions r
                     JOIN (SELECT profile_id, MAX(revision) AS revision
                             FROM model_profile_revisions GROUP BY profile_id) latest
                       ON latest.profile_id=r.profile_id AND latest.revision=r.revision
                     LEFT JOIN model_profile_tombstones t ON t.profile_id=r.profile_id
                    WHERE t.profile_id IS NULL ORDER BY r.label COLLATE NOCASE, r.profile_id"""
            ).fetchall()
            profiles = [self._profile_projection(conn, row) for row in rows]
        legacy: list[dict[str, Any]] = []
        if include_legacy:
            legacy = [adapt_v1_profile(row) for row in self._db.profiles.list()]
        return {"schema_version": 2, "profiles": profiles, "legacy_profiles": legacy}

    def get_profile(
        self, principal: Principal, profile_id: str, *, revision: int | None = None
    ) -> dict[str, Any]:
        self._require_owner(principal)
        clean_id = str(profile_id or "").strip()
        if clean_id.startswith("legacy-"):
            legacy = self._db.profiles.get(clean_id.removeprefix("legacy-"))
            if legacy is None:
                raise NotFound("model profile", clean_id)
            return adapt_v1_profile(legacy)
        if not _PROFILE_ID.fullmatch(clean_id):
            raise NotFound("model profile", clean_id)
        with self._db._connection() as conn:
            tombstone = conn.execute(
                "SELECT 1 FROM model_profile_tombstones WHERE profile_id=?", (clean_id,)
            ).fetchone()
            if tombstone is not None:
                raise NotFound("model profile", clean_id)
            if revision is None:
                row = conn.execute(
                    """SELECT * FROM model_profile_revisions WHERE profile_id=?
                         ORDER BY revision DESC LIMIT 1""",
                    (clean_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM model_profile_revisions WHERE profile_id=? AND revision=?",
                    (clean_id, int(revision)),
                ).fetchone()
        if row is None:
            raise NotFound("model profile", clean_id)
        with self._db._connection() as conn:
            return self._profile_projection(conn, row)

    def create_profile(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        """Create the next immutable revision after a narrow profile-head CAS."""
        self._require_owner(principal)
        parsed = self._profile_payload(body)
        profile_id = parsed["profile_id"]
        expected_revision = parsed.pop("expected_revision")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                tombstone = conn.execute(
                    "SELECT 1 FROM model_profile_tombstones WHERE profile_id=?", (profile_id,)
                ).fetchone()
                if tombstone is not None:
                    raise ConflictError(
                        "Deleted model profiles cannot be recreated; add a new profile instead.",
                        code="model_profile_deleted",
                    )
                row = conn.execute(
                    "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                    (profile_id,),
                ).fetchone()
                current = int(row["revision"] or 0)
                if current != expected_revision:
                    raise ConflictError(
                        "Model profile changed. Refresh before saving.",
                        code="model_profile_revision_conflict",
                        context={"expected_revision": expected_revision, "current_revision": current},
                    )
                revision = current + 1
                material = {"schema_version": 2, "profile_id": profile_id, "revision": revision, **parsed}
                digest = _sha256(material)
                created_at = _now()
                conn.execute(
                    """INSERT INTO model_profile_revisions
                       (profile_id,revision,sha256,label,provider_family,runtime_family,
                        model_or_artifact_identity,supported_modalities_json,context_support,
                        tokenizer_template_requirements_json,capability_manifest_json,
                        safe_presentation_json,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        profile_id, revision, digest, parsed["label"], parsed["provider_family"],
                        parsed["runtime_family"], parsed["model_or_artifact_identity"],
                        _canonical(parsed["supported_modalities"]), parsed["context_support"],
                        _canonical(parsed["tokenizer_template_requirements"]),
                        _canonical(parsed["capability_manifest"]), _canonical(parsed["safe_presentation"]),
                        created_at,
                    ),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return self.get_profile(principal, profile_id, revision=revision)

    # The names make the immutable-write law easy for callers to discover.
    create_profile_revision = create_profile
    revise_profile = create_profile

    def probe_profile(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        """Mint one server-observed readiness fact for an exact deployment head.

        Destination observation deliberately happens before the short write
        transaction: endpoint probes can take bounded network time and must not
        hold SQLite's writer lock.  The head is then re-read under
        ``BEGIN IMMEDIATE`` before an observation is persisted, so an observed
        destination can never be attached to a different deployment head.

        The observation uses the canonical destination/readiness authority,
        not artifact state.  A verified file does not prove that its runtime,
        configured local destination, key, endpoint, or paired executor is
        currently usable.
        """
        self._require_owner(principal)
        parsed = self._probe_payload(body)
        snapshot = self._probe_snapshot(parsed)
        state, reason_code = self._observe_destination_readiness(
            principal,
            destination_id=snapshot["destination_id"],
            runtime_id=snapshot["runtime_id"],
            artifact_state=snapshot["artifact_state"],
        )
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if conn.execute(
                    "SELECT 1 FROM model_profile_tombstones WHERE profile_id=?", (parsed["profile_id"],)
                ).fetchone() is not None:
                    raise NotFound("model profile", parsed["profile_id"])
                profile_row = conn.execute(
                    "SELECT * FROM model_profile_revisions WHERE profile_id=? AND revision=?",
                    (parsed["profile_id"], parsed["profile_revision"]),
                ).fetchone()
                if profile_row is None:
                    raise NotFound(
                        "model profile revision", f"{parsed['profile_id']}@{parsed['profile_revision']}"
                    )
                self._revision_from_row(profile_row)
                head = conn.execute(
                    """SELECT d.deployment_id,d.configuration_revision,d.execution_revision_id,
                              d.destination_id,a.state AS artifact_state,r.*
                         FROM inference_deployments d
                         JOIN deployment_revisions r ON r.id=d.execution_revision_id
                         LEFT JOIN inference_model_artifacts a ON a.artifact_id=d.artifact_id
                        WHERE d.deployment_id=?""",
                    (parsed["deployment_head_id"],),
                ).fetchone()
                if head is None:
                    raise NotFound("deployment head", parsed["deployment_head_id"])
                configuration_revision = int(head["configuration_revision"])
                deployment_revision_id = str(head["execution_revision_id"])
                if (
                    configuration_revision != parsed["expected_deployment_configuration_revision"]
                    or deployment_revision_id != parsed["expected_deployment_revision_id"]
                ):
                    raise ConflictError(
                        "Deployment changed. Refresh before checking this model.",
                        code="deployment_head_conflict",
                        context={
                            "current_configuration_revision": configuration_revision,
                            "current_deployment_revision_id": deployment_revision_id,
                        },
                    )
                self._deployment_from_row(head)
                # Local readiness needs both the exact artifact and the
                # captured runtime.  The artifact is a mutable availability
                # fact, so re-check it at the CAS edge after the observation
                # and do not retain a ready claim after an uninstall/corrupt
                # transition.
                if (
                    str(head["destination_id"]) == "this_machine"
                    and str(head["artifact_state"] or "") != "verified"
                ):
                    state, reason_code = "unavailable", "artifact_unavailable"
                observation = {
                    "observation_id": "ready_" + uuid.uuid4().hex,
                    "deployment_head_id": parsed["deployment_head_id"],
                    "deployment_configuration_revision": configuration_revision,
                    "deployment_revision_id": deployment_revision_id,
                    "state": state,
                    "reason_code": reason_code,
                    "observed_at": _now(),
                }
                conn.execute(
                    """INSERT INTO model_profile_readiness_observations
                       (observation_id,deployment_head_id,deployment_configuration_revision,
                        deployment_revision_id,state,reason_code,observed_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        observation["observation_id"], observation["deployment_head_id"],
                        observation["deployment_configuration_revision"],
                        observation["deployment_revision_id"], observation["state"],
                        observation["reason_code"], observation["observed_at"],
                    ),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return observation

    def _probe_snapshot(self, parsed: dict[str, Any]) -> dict[str, str]:
        """Read an exact requested head without holding a transaction for I/O."""
        with self._db._connection() as conn:
            if conn.execute(
                "SELECT 1 FROM model_profile_tombstones WHERE profile_id=?", (parsed["profile_id"],)
            ).fetchone() is not None:
                raise NotFound("model profile", parsed["profile_id"])
            profile_row = conn.execute(
                "SELECT * FROM model_profile_revisions WHERE profile_id=? AND revision=?",
                (parsed["profile_id"], parsed["profile_revision"]),
            ).fetchone()
            if profile_row is None:
                raise NotFound(
                    "model profile revision", f"{parsed['profile_id']}@{parsed['profile_revision']}"
                )
            self._revision_from_row(profile_row)
            head = conn.execute(
                """SELECT d.deployment_id,d.destination_id,d.configuration_revision,
                          d.execution_revision_id,a.state AS artifact_state,r.*
                     FROM inference_deployments d
                     JOIN deployment_revisions r ON r.id=d.execution_revision_id
                     LEFT JOIN inference_model_artifacts a ON a.artifact_id=d.artifact_id
                    WHERE d.deployment_id=?""",
                (parsed["deployment_head_id"],),
            ).fetchone()
        if head is None:
            raise NotFound("deployment head", parsed["deployment_head_id"])
        self._deployment_from_row(head)
        configuration_revision = int(head["configuration_revision"])
        deployment_revision_id = str(head["execution_revision_id"])
        if (
            configuration_revision != parsed["expected_deployment_configuration_revision"]
            or deployment_revision_id != parsed["expected_deployment_revision_id"]
        ):
            raise ConflictError(
                "Deployment changed. Refresh before checking this model.",
                code="deployment_head_conflict",
                context={
                    "current_configuration_revision": configuration_revision,
                    "current_deployment_revision_id": deployment_revision_id,
                },
            )
        return {
            "destination_id": str(head["destination_id"]),
            "runtime_id": str(head["runtime_id"]),
            "artifact_state": str(head["artifact_state"] or ""),
        }

    def _observe_destination_readiness(
        self,
        principal: Principal,
        *,
        destination_id: str,
        runtime_id: str,
        artifact_state: str,
    ) -> tuple[str, str]:
        """Observe canonical live destination readiness without exposing it.

        Only safe state/reason codes leave this service.  The existing target
        resolver owns local/key/paired state; the existing target probe owns
        the bounded endpoint round trip.  This method intentionally receives
        neither a locator nor an endpoint.
        """
        from ..inference_targets import THIS_MACHINE_ID, resolve_inference_target

        if destination_id == THIS_MACHINE_ID:
            if artifact_state != "verified":
                return "unavailable", "artifact_unavailable"
            return self._local_runtime_readiness(runtime_id)

        target = resolve_inference_target(self._db, destination_id)
        if not target.ready:
            return "unavailable", self._destination_reason_code(target.readiness_state)

        profile = self._db.profiles.get(destination_id)
        if profile is not None and str(getattr(profile, "kind", "")) == "openAICompatible":
            # ProfileService is the canonical owner-gated, bounded endpoint
            # probe.  It may inspect private endpoint/key state internally;
            # this projection retains only a generic result code.
            from .profile_service import ProfileService

            result = ProfileService(self._db).probe_inference_target(principal, destination_id)
            if not bool(result.get("reachable")):
                return "unavailable", "endpoint_unreachable"
        return "ready", "ready"

    @staticmethod
    def _destination_reason_code(state: Any) -> str:
        normalized = str(state or "").strip().lower()
        return {
            "needs_key": "credential_unavailable",
            "offline": "destination_offline",
            "stale_manifest": "destination_stale",
            "unsupported": "destination_unsupported",
            "unavailable": "destination_unavailable",
        }.get(normalized, "destination_unavailable")

    @staticmethod
    def _local_runtime_readiness(runtime_id: str) -> tuple[str, str]:
        """Require the captured runtime to be executable, not merely installed."""
        from .inference_setup_service import inspect_runtimes

        apple_silicon = (
            platform.system() == "Darwin"
            and platform.machine().lower() in {"arm64", "aarch64"}
        )
        runtime = next(
            (row for row in inspect_runtimes(apple_silicon=apple_silicon)
             if str(row.get("id") or "") == runtime_id),
            None,
        )
        if runtime is None:
            return "unavailable", "runtime_unavailable"
        availability = dict(runtime.get("availability") or {})
        thought_support = dict(runtime.get("thought_support") or {})
        if (
            availability.get("state") != "available"
            or thought_support.get("state") not in {"supported", "available"}
        ):
            return "unavailable", "runtime_unavailable"
        return "ready", "ready"

    def bind_profile(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        """CAS-bind one profile revision to one already-existing deployment head."""
        self._require_owner(principal)
        parsed = self._binding_payload(body)
        profile_id = parsed["profile_id"]
        binding_id = parsed["binding_id"]
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if conn.execute(
                    "SELECT 1 FROM model_profile_tombstones WHERE profile_id=?", (profile_id,)
                ).fetchone() is not None:
                    raise NotFound("model profile", profile_id)
                profile = conn.execute(
                    """SELECT * FROM model_profile_revisions
                         WHERE profile_id=? AND revision=?""",
                    (profile_id, parsed["profile_revision"]),
                ).fetchone()
                if profile is None:
                    raise NotFound("model profile revision", f"{profile_id}@{parsed['profile_revision']}")
                self._revision_from_row(profile)
                existing = conn.execute(
                    """SELECT h.binding_id,h.revision,b.profile_id FROM model_profile_binding_heads h
                         JOIN model_profile_binding_revisions b
                           ON b.binding_id=h.binding_id AND b.revision=h.revision
                        WHERE h.profile_id=?""",
                    (profile_id,),
                ).fetchone()
                if existing is not None and str(existing["binding_id"]) != binding_id:
                    raise ConflictError(
                        "This profile already has a binding. Update that binding instead.",
                        code="model_profile_binding_exists",
                        context={"binding_id": str(existing["binding_id"])},
                    )
                current = int(existing["revision"]) if existing is not None else 0
                if current != parsed["expected_binding_revision"]:
                    raise ConflictError(
                        "Model binding changed. Refresh before saving.",
                        code="model_profile_binding_conflict",
                        context={
                            "expected_binding_revision": parsed["expected_binding_revision"],
                            "current_revision": current,
                        },
                    )
                head = conn.execute(
                    """SELECT deployment_id,configuration_revision,execution_revision_id
                         FROM inference_deployments WHERE deployment_id=?""",
                    (parsed["deployment_head_id"],),
                ).fetchone()
                if head is None:
                    raise NotFound("deployment head", parsed["deployment_head_id"])
                configuration_revision = int(head["configuration_revision"])
                if configuration_revision != parsed["expected_deployment_configuration_revision"]:
                    raise ConflictError(
                        "Deployment changed. Refresh before binding this model.",
                        code="deployment_head_conflict",
                        context={
                            "expected_configuration_revision": parsed["expected_deployment_configuration_revision"],
                            "current_configuration_revision": configuration_revision,
                        },
                    )
                deployment_revision_id = str(head["execution_revision_id"])
                if deployment_revision_id != parsed["expected_deployment_revision_id"]:
                    raise ConflictError(
                        "Deployment execution revision changed. Refresh before binding this model.",
                        code="deployment_head_conflict",
                        context={
                            "expected_deployment_revision_id": parsed["expected_deployment_revision_id"],
                            "current_deployment_revision_id": deployment_revision_id,
                        },
                    )
                deployment = conn.execute(
                    "SELECT * FROM deployment_revisions WHERE id=?",
                    (deployment_revision_id,),
                ).fetchone()
                if deployment is None:
                    raise ConflictError(
                        "Deployment head has no immutable execution revision.",
                        code="deployment_head_invalid",
                    )
                self._deployment_from_row(deployment)
                self._require_binding_coherence(profile, deployment)
                observation = conn.execute(
                    """SELECT 1 FROM model_profile_readiness_observations
                         WHERE observation_id=? AND deployment_head_id=?
                           AND deployment_configuration_revision=? AND deployment_revision_id=?""",
                    (
                        parsed["readiness_observation_id"], parsed["deployment_head_id"],
                        configuration_revision, deployment_revision_id,
                    ),
                ).fetchone()
                if observation is None:
                    raise ConflictError(
                        "Readiness changed or was not checked for this exact deployment.",
                        code="model_profile_readiness_stale",
                    )
                revision = current + 1
                now = _now()
                conn.execute(
                    """INSERT INTO model_profile_binding_revisions
                       (binding_id,revision,profile_id,profile_revision,deployment_head_id,
                        deployment_configuration_revision,deployment_revision_id,secret_slot,
                        enabled,readiness_observation_id,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        binding_id, revision, profile_id, parsed["profile_revision"],
                        parsed["deployment_head_id"], configuration_revision, deployment_revision_id,
                        str(deployment["secret_slot"] or ""), 1 if parsed["enabled"] else 0,
                        parsed["readiness_observation_id"], now,
                    ),
                )
                conn.execute(
                    """INSERT INTO model_profile_binding_heads(binding_id,profile_id,revision,updated_at)
                       VALUES (?,?,?,?)
                       ON CONFLICT(binding_id) DO UPDATE SET
                         profile_id=excluded.profile_id,revision=excluded.revision,
                         updated_at=excluded.updated_at""",
                    (binding_id, profile_id, revision, now),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return self.get_binding(principal, binding_id)

    def get_binding(self, principal: Principal, binding_id: str) -> dict[str, Any]:
        self._require_owner(principal)
        clean_id = str(binding_id or "").strip()
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT b.*,h.updated_at FROM model_profile_binding_heads h
                     JOIN model_profile_binding_revisions b
                       ON b.binding_id=h.binding_id AND b.revision=h.revision
                    WHERE h.binding_id=?""",
                (clean_id,),
            ).fetchone()
        if row is None:
            raise NotFound("model profile binding", clean_id)
        return self._binding_from_row(row).to_dict()

    def unbind_profile(
        self, principal: Principal, profile_id: str, *, expected_binding_revision: int
    ) -> dict[str, Any]:
        """Remove only the mutable binding head; immutable binding history stays."""
        self._require_owner(principal)
        clean_id = self._profile_id(profile_id)
        if not isinstance(expected_binding_revision, int) or expected_binding_revision < 1:
            raise ValidationError("expected_binding_revision is required", code="model_profile_binding_invalid")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute(
                    "SELECT binding_id,revision FROM model_profile_binding_heads WHERE profile_id=?", (clean_id,)
                ).fetchone()
                if row is None:
                    raise NotFound("model profile binding", clean_id)
                if int(row["revision"]) != expected_binding_revision:
                    raise ConflictError(
                        "Model binding changed. Refresh before removing it.",
                        code="model_profile_binding_conflict",
                        context={"current_revision": int(row["revision"])},
                    )
                conn.execute("DELETE FROM model_profile_binding_heads WHERE profile_id=?", (clean_id,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return {"profile_id": clean_id, "unbound": True}

    def delete_profile(
        self, principal: Principal, profile_id: str, *, expected_revision: int | None = None
    ) -> dict[str, Any]:
        """Tombstone a profile only after naming every live dependent authority."""
        self._require_owner(principal)
        clean_id = self._profile_id(profile_id)
        if not isinstance(expected_revision, int) or expected_revision < 1:
            raise ValidationError(
                "expected_revision is required", code="model_profile_revision_required"
            )
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                exists = conn.execute(
                    "SELECT 1 FROM model_profile_revisions WHERE profile_id=?", (clean_id,)
                ).fetchone()
                if exists is None:
                    raise NotFound("model profile", clean_id)
                current = conn.execute(
                    "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                    (clean_id,),
                ).fetchone()
                if int(current["revision"] or 0) != expected_revision:
                    raise ConflictError(
                        "Model profile changed. Refresh before deleting it.",
                        code="model_profile_revision_conflict",
                        context={"expected_revision": expected_revision, "current_revision": int(current["revision"] or 0)},
                    )
                dependencies = self._dependencies(conn, clean_id)
                assignments = [item["id"] for item in dependencies if item["kind"] == "assignment"]
                if dependencies:
                    raise ConflictError(
                        "Model profile is still in use. Remove its dependent assignments or bindings first.",
                        code="model_profile_referenced",
                        context={"dependencies": dependencies, "dependent_assignments": assignments},
                    )
                conn.execute(
                    "INSERT INTO model_profile_tombstones(profile_id,deleted_at) VALUES (?,?)",
                    (clean_id, _now()),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return {"profile_id": clean_id, "deleted": True}

    @staticmethod
    def _require_binding_coherence(profile: Any, deployment: Any) -> None:
        """Refuse a profile that would describe a different executable thing.

        A binding is not a loose association: the exact immutable execution
        revision must substantiate its model/artifact identity, runtime, and
        (for v2) governed capability evidence.  This is deliberately checked
        inside the same transaction that advances the binding head.
        """
        artifact_id = str(deployment["artifact_id"] or "").strip()
        model = str(deployment["model"] or "").strip()
        actual_identity = artifact_id or model
        profile_identity = str(profile["model_or_artifact_identity"] or "").strip()
        runtime_family = str(profile["runtime_family"] or "").strip()
        runtime_id = str(deployment["runtime_id"] or "").strip()
        runtime_matches = (
            runtime_family == runtime_id
            or runtime_id in _LEGACY_RUNTIME_FAMILIES.get(runtime_family, frozenset())
        )
        if not actual_identity or profile_identity != actual_identity or not runtime_matches:
            raise ConflictError(
                "This deployment does not match the profile's immutable model or runtime.",
                code="model_profile_deployment_mismatch",
            )
        if int(deployment["schema_version"] or 1) >= 2:
            capability_sha256 = str(deployment["capability_sha256"] or "").strip()
            manifest = json.loads(str(profile["capability_manifest_json"]))
            if capability_sha256 and str(manifest.get("sha256") or "") != capability_sha256:
                raise ConflictError(
                    "This deployment does not match the profile's capability evidence.",
                    code="model_profile_deployment_mismatch",
                )

    def _profile_payload(self, body: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "profile_id", "expected_revision", "label", "provider_family", "runtime_family",
            "model_or_artifact_identity", "supported_modalities", "context_support",
            "tokenizer_template_requirements", "capability_manifest", "safe_presentation",
        }
        if not isinstance(body, dict) or set(body) != allowed:
            raise ValidationError(
                "Model profile request has an invalid shape.", code="model_profile_request_invalid"
            )
        _forbid_private_material(body)
        profile_id = self._profile_id(body["profile_id"])
        expected = body["expected_revision"]
        if not isinstance(expected, int) or expected < 0:
            raise ValidationError("expected_revision must be a non-negative integer", code="model_profile_invalid")
        modalities = _require_json(body["supported_modalities"], field="supported_modalities", kind=list)
        if not modalities or len(modalities) > 16:
            raise ValidationError("supported_modalities is invalid", code="model_profile_invalid")
        cleaned_modalities = sorted({_text(value, field="supported_modalities", limit=80) for value in modalities})
        context = _text(body["context_support"], field="context_support", limit=20)
        if context not in _CONTEXT_SUPPORT:
            raise ValidationError("context_support is invalid", code="model_profile_invalid")
        tokenizer = _closed_object(
            body["tokenizer_template_requirements"],
            field="tokenizer_template_requirements",
            allowed=_TOKENIZER_REQUIREMENT_FIELDS,
        )
        manifest = _require_json(body["capability_manifest"], field="capability_manifest", kind=dict)
        if set(manifest) != {"revision", "sha256", "claims"}:
            raise ValidationError("capability_manifest has an invalid shape", code="model_profile_invalid")
        if not isinstance(manifest["revision"], (str, int)) or not _SHA256.fullmatch(str(manifest["sha256"])):
            raise ValidationError("capability_manifest is invalid", code="model_profile_invalid")
        _require_json(manifest["claims"], field="capability_manifest.claims", kind=list)
        presentation = _closed_object(
            body["safe_presentation"],
            field="safe_presentation",
            allowed=_SAFE_PRESENTATION_FIELDS,
        )
        if "summary" not in presentation:
            raise ValidationError("safe_presentation has an invalid shape", code="model_profile_invalid")
        for key in ("tokenizer_id", "chat_template", "tool_call_template"):
            if key in tokenizer:
                tokenizer[key] = _safe_text(tokenizer[key], field=f"tokenizer_template_requirements.{key}")
        for key in ("requires_bos_token", "requires_eos_token"):
            if key in tokenizer and not isinstance(tokenizer[key], bool):
                raise ValidationError(
                    f"tokenizer_template_requirements.{key} must be boolean",
                    code="model_profile_invalid",
                )
        for key in ("summary", "badge"):
            if key in presentation:
                presentation[key] = _safe_text(
                    presentation[key], field=f"safe_presentation.{key}", limit=300
                )
        claims = _require_json(manifest["claims"], field="capability_manifest.claims", kind=list)
        if len(claims) > 128:
            raise ValidationError("capability_manifest.claims is invalid", code="model_profile_invalid")
        manifest["claims"] = [
            _safe_text(value, field="capability_manifest.claims", limit=120)
            for value in claims
        ]
        for value, field in (
            (tokenizer, "tokenizer_template_requirements"),
            (manifest, "capability_manifest"),
            (presentation, "safe_presentation"),
        ):
            _bounded_json(value, field=field)
        manifest_evidence = {"revision": manifest["revision"], "claims": manifest["claims"]}
        if str(manifest["sha256"]) != _sha256(manifest_evidence):
            raise ValidationError(
                "capability_manifest hash does not match its evidence",
                code="model_profile_manifest_hash_invalid",
            )
        return {
            "profile_id": profile_id,
            "expected_revision": expected,
            "label": _safe_text(body["label"], field="label", limit=200),
            "provider_family": _safe_text(body["provider_family"], field="provider_family", limit=100),
            "runtime_family": _safe_text(body["runtime_family"], field="runtime_family", limit=100),
            "model_or_artifact_identity": _safe_text(
                body["model_or_artifact_identity"], field="model_or_artifact_identity", limit=300
            ),
            "supported_modalities": cleaned_modalities,
            "context_support": context,
            "tokenizer_template_requirements": tokenizer,
            "capability_manifest": manifest,
            "safe_presentation": presentation,
        }

    def _binding_payload(self, body: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "binding_id", "profile_id", "profile_revision", "deployment_head_id",
            "expected_binding_revision", "expected_deployment_configuration_revision",
            "expected_deployment_revision_id", "enabled", "readiness_observation_id",
        }
        if not isinstance(body, dict) or set(body) != allowed:
            raise ValidationError(
                "Model binding request has an invalid shape.", code="model_profile_binding_invalid"
            )
        _forbid_private_material(body)
        profile_id = self._profile_id(body["profile_id"])
        binding_id = str(body["binding_id"] or "").strip() or f"binding-{profile_id}"
        if len(binding_id) > 128 or any(ord(char) < 33 for char in binding_id):
            raise ValidationError("binding_id is invalid", code="model_profile_binding_invalid")
        values = {
            "profile_revision": body["profile_revision"],
            "expected_binding_revision": body["expected_binding_revision"],
            "expected_deployment_configuration_revision": body["expected_deployment_configuration_revision"],
        }
        if any(not isinstance(value, int) or value < 0 for value in values.values()):
            raise ValidationError("binding revision fields are invalid", code="model_profile_binding_invalid")
        if values["profile_revision"] < 1:
            raise ValidationError("profile_revision is invalid", code="model_profile_binding_invalid")
        if not isinstance(body["enabled"], bool):
            raise ValidationError("enabled must be boolean", code="model_profile_binding_invalid")
        return {
            "binding_id": binding_id,
            "profile_id": profile_id,
            **values,
            "deployment_head_id": _safe_text(
                body["deployment_head_id"], field="deployment_head_id", limit=160
            ),
            "enabled": body["enabled"],
            "expected_deployment_revision_id": _safe_text(
                body["expected_deployment_revision_id"], field="expected_deployment_revision_id", limit=160
            ),
            "readiness_observation_id": _safe_text(
                body["readiness_observation_id"], field="readiness_observation_id", limit=160
            ),
        }

    def _probe_payload(self, body: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "profile_id", "profile_revision", "deployment_head_id",
            "expected_deployment_configuration_revision", "expected_deployment_revision_id",
        }
        if not isinstance(body, dict) or set(body) != allowed:
            raise ValidationError(
                "Model profile probe request has an invalid shape.", code="model_profile_probe_invalid"
            )
        _forbid_private_material(body)
        profile_revision = body["profile_revision"]
        expected_configuration = body["expected_deployment_configuration_revision"]
        if (
            not isinstance(profile_revision, int) or profile_revision < 1
            or not isinstance(expected_configuration, int) or expected_configuration < 1
        ):
            raise ValidationError("probe revision fields are invalid", code="model_profile_probe_invalid")
        return {
            "profile_id": self._profile_id(body["profile_id"]),
            "profile_revision": profile_revision,
            "deployment_head_id": _safe_text(
                body["deployment_head_id"], field="deployment_head_id", limit=160
            ),
            "expected_deployment_configuration_revision": expected_configuration,
            "expected_deployment_revision_id": _safe_text(
                body["expected_deployment_revision_id"], field="expected_deployment_revision_id", limit=160
            ),
        }

    @staticmethod
    def _profile_id(value: Any) -> str:
        clean = str(value or "").strip()
        if not _PROFILE_ID.fullmatch(clean):
            raise ValidationError(
                "profile_id must be a stable lowercase ASCII slug", code="model_profile_invalid"
            )
        return clean

    @staticmethod
    def _integrity_error(kind: str) -> ConflictError:
        return ConflictError(
            f"Stored {kind} integrity could not be verified.",
            code=f"{kind.replace(' ', '_')}_integrity_invalid",
        )

    def _revision_from_row(self, row: Any) -> ModelProfileRevision:
        """Rebuild immutable profile material and verify its content hash.

        DB rows are persistence, not authority: list/get/bind all call this
        before returning or associating a revision.  The additional private
        material screen protects owner-safe projections even against an actor
        who has tampered with both a row and its digest.
        """
        try:
            revision = ModelProfileRevision(
                profile_id=str(row["profile_id"]),
                revision=int(row["revision"]),
                sha256=str(row["sha256"]),
                label=str(row["label"]),
                provider_family=str(row["provider_family"]),
                runtime_family=str(row["runtime_family"]),
                model_or_artifact_identity=str(row["model_or_artifact_identity"]),
                supported_modalities=tuple(json.loads(str(row["supported_modalities_json"]))),
                context_support=str(row["context_support"]),
                tokenizer_template_requirements=json.loads(str(row["tokenizer_template_requirements_json"])),
                capability_manifest=json.loads(str(row["capability_manifest_json"])),
                safe_presentation=json.loads(str(row["safe_presentation_json"])),
                created_at=str(row["created_at"]),
            )
            material = {
                "schema_version": 2,
                "profile_id": revision.profile_id,
                "revision": revision.revision,
                "label": revision.label,
                "provider_family": revision.provider_family,
                "runtime_family": revision.runtime_family,
                "model_or_artifact_identity": revision.model_or_artifact_identity,
                "supported_modalities": list(revision.supported_modalities),
                "context_support": revision.context_support,
                "tokenizer_template_requirements": revision.tokenizer_template_requirements,
                "capability_manifest": revision.capability_manifest,
                "safe_presentation": revision.safe_presentation,
            }
            if revision.sha256 != _sha256(material):
                raise ValueError("profile content hash mismatch")
            _forbid_private_material(material)
            _bounded_json(revision.tokenizer_template_requirements, field="stored tokenizer requirements")
            _bounded_json(revision.capability_manifest, field="stored capability manifest")
            _bounded_json(revision.safe_presentation, field="stored presentation")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError) as exc:
            raise self._integrity_error("model_profile") from exc
        return revision

    def _deployment_from_row(self, row: Any) -> DeploymentRevision:
        """Reconstruct an execution revision and reject any content-ID drift."""
        try:
            schema_version = int(row["schema_version"])
            values = {
                "destination_id": str(row["destination_id"] or ""),
                "kind": str(row["kind"] or ""),
                "engine": str(row["engine"] or ""),
                "model": str(row["model"] or ""),
                "node": str(row["node"] or ""),
                "boundary": str(row["boundary"] or ""),
                "endpoint": str(row["endpoint"] or ""),
                "model_path": row["model_path"],
                "secret_slot": str(row["secret_slot"] or ""),
                "runtime_id": str(row["runtime_id"] or ""),
                "runtime_revision": str(row["runtime_revision"] or ""),
                "artifact_id": str(row["artifact_id"] or ""),
                "manifest_sha256": str(row["manifest_sha256"] or ""),
                "format": str(row["format"] or ""),
                "architecture": str(row["architecture"] or ""),
                "context_ceiling": int(row["context_ceiling"]),
                "capability_sha256": str(row["capability_sha256"] or ""),
            }
            if schema_version == 1:
                rebuilt = DeploymentRevision.from_identity(DeploymentIdentity(**{
                    key: values[key]
                    for key in ("destination_id", "kind", "engine", "model", "node", "boundary", "model_path", "endpoint", "secret_slot")
                }))
            elif schema_version == 2:
                rebuilt = DeploymentRevision.from_artifact(
                    destination_id=values["destination_id"], engine=values["engine"],
                    model=values["model"], runtime_id=values["runtime_id"],
                    runtime_revision=values["runtime_revision"], artifact_id=values["artifact_id"],
                    manifest_sha256=values["manifest_sha256"], format=values["format"],
                    architecture=values["architecture"], context_ceiling=values["context_ceiling"],
                    capability_sha256=values["capability_sha256"],
                )
            else:
                raise ValueError("unknown deployment schema")
            if str(row["id"]) != rebuilt.id:
                raise ValueError("deployment content id mismatch")
            for key, expected in (("schema_version", rebuilt.schema_version), ("destination_id", rebuilt.destination_id),
                                  ("kind", rebuilt.kind), ("engine", rebuilt.engine), ("model", rebuilt.model),
                                  ("node", rebuilt.node), ("boundary", rebuilt.boundary), ("endpoint", rebuilt.endpoint),
                                  ("model_path", rebuilt.model_path), ("secret_slot", rebuilt.secret_slot),
                                  ("runtime_id", rebuilt.runtime_id), ("runtime_revision", rebuilt.runtime_revision),
                                  ("artifact_id", rebuilt.artifact_id), ("manifest_sha256", rebuilt.manifest_sha256),
                                  ("format", rebuilt.format), ("architecture", rebuilt.architecture),
                                  ("context_ceiling", rebuilt.context_ceiling), ("capability_sha256", rebuilt.capability_sha256)):
                actual = row[key]
                if key in {"schema_version", "context_ceiling"}:
                    if int(actual) != int(expected):
                        raise ValueError(f"deployment field mismatch: {key}")
                elif str(actual or "") != str(expected or ""):
                    raise ValueError(f"deployment field mismatch: {key}")
        except (KeyError, TypeError, ValueError) as exc:
            raise self._integrity_error("deployment_revision") from exc
        return rebuilt

    def _profile_projection(self, conn: Any, row: Any) -> dict[str, Any]:
        profile = self._revision_from_row(row).to_dict()
        binding_row = conn.execute(
            """SELECT b.*,h.updated_at FROM model_profile_binding_heads h
                 JOIN model_profile_binding_revisions b
                   ON b.binding_id=h.binding_id AND b.revision=h.revision
                WHERE h.profile_id=?""",
            (profile["profile_id"],),
        ).fetchone()
        binding = self._binding_from_row(binding_row).to_dict() if binding_row is not None else None
        readiness = None
        if binding is not None:
            observation = conn.execute(
                """SELECT observation_id,deployment_head_id,deployment_configuration_revision,
                          deployment_revision_id,state,reason_code,observed_at
                     FROM model_profile_readiness_observations
                    WHERE deployment_head_id=? AND deployment_configuration_revision=?
                      AND deployment_revision_id=?
                    ORDER BY observed_at DESC,observation_id DESC LIMIT 1""",
                (binding["deployment_head_id"], binding["deployment_configuration_revision"], binding["deployment_revision_id"]),
            ).fetchone()
            if observation is not None:
                readiness = dict(observation)
        return {**profile, "current_binding": binding, "latest_readiness": readiness}

    @staticmethod
    def _binding_from_row(row: Any) -> ProfileBinding:
        return ProfileBinding(
            binding_id=str(row["binding_id"]),
            revision=int(row["revision"]),
            profile_id=str(row["profile_id"]),
            profile_revision=int(row["profile_revision"]),
            deployment_head_id=str(row["deployment_head_id"]),
            deployment_configuration_revision=int(row["deployment_configuration_revision"]),
            deployment_revision_id=str(row["deployment_revision_id"]),
            enabled=bool(row["enabled"]),
            updated_at=str(row["updated_at"]),
        )

    def _dependencies(self, conn: Any, profile_id: str) -> list[dict[str, str]]:
        dependencies: list[dict[str, str]] = []
        for provider_name, provider in self._dependency_providers.items():
            try:
                supplied = provider(conn, profile_id)
                if not isinstance(supplied, list):
                    raise TypeError("provider must return a list")
                for dependency in supplied:
                    if (
                        not isinstance(dependency, dict)
                        or set(dependency) != {"kind", "id"}
                        or not isinstance(dependency["kind"], str)
                        or not isinstance(dependency["id"], str)
                        or not dependency["kind"].strip()
                        or not dependency["id"].strip()
                    ):
                        raise TypeError("provider returned malformed dependency")
                    dependencies.append({"kind": dependency["kind"], "id": dependency["id"]})
            except Exception:
                # An unreadable provider is itself a live dependency.  Deletion
                # must refuse rather than silently declaring a profile unused.
                dependencies.append({"kind": "dependency_provider_error", "id": provider_name})
        unique = sorted({(item["kind"], item["id"]) for item in dependencies})
        return [
            {"kind": kind, "id": identifier}
            for kind, identifier in unique
        ]

    @staticmethod
    def _binding_dependencies(conn: Any, profile_id: str) -> list[dict[str, str]]:
        return [
            {"kind": "binding", "id": str(row["binding_id"])}
            for row in conn.execute(
                "SELECT binding_id FROM model_profile_binding_heads WHERE profile_id=?", (profile_id,)
            ).fetchall()
        ]

    @staticmethod
    def _deployment_material_dependencies(conn: Any, profile_id: str) -> list[dict[str, str]]:
        identities = [
            str(row["model_or_artifact_identity"])
            for row in conn.execute(
                "SELECT model_or_artifact_identity FROM model_profile_revisions WHERE profile_id=?",
                (profile_id,),
            ).fetchall()
        ]
        dependencies: list[dict[str, str]] = []
        for identity in identities:
            for row in conn.execute(
                """SELECT deployment_id FROM inference_deployments
                    WHERE artifact_id=? OR model_identity=?""", (identity, identity)
            ).fetchall():
                dependencies.append({"kind": "deployment", "id": str(row["deployment_id"])})
            for row in conn.execute(
                "SELECT artifact_id FROM inference_model_artifacts WHERE artifact_id=?", (identity,)
            ).fetchall():
                dependencies.append({"kind": "artifact", "id": str(row["artifact_id"])})
            for row in conn.execute(
                "SELECT job_id FROM inference_model_acquisitions WHERE artifact_id=?", (identity,)
            ).fetchall():
                dependencies.append({"kind": "acquisition", "id": str(row["job_id"])})
        return dependencies

    @staticmethod
    def _registered_store_dependencies(conn: Any, profile_id: str, *, table: str, kind: str) -> list[dict[str, str]]:
        present = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if present is None:
            return []
        columns = {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})")}
        if not {"id", "profile_id"}.issubset(columns):
            raise ValueError(f"{table} has no registered exact profile reference")
        return [
            {"kind": kind, "id": str(row["id"])}
            for row in conn.execute(f"SELECT id FROM {table} WHERE profile_id=?", (profile_id,)).fetchall()
        ]

    def _assignment_dependencies(self, conn: Any, profile_id: str) -> list[dict[str, str]]:
        present = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='inference_assignments'"
        ).fetchone()
        if present is None:
            return []
        columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(inference_assignments)")}
        if "assignment_id" in columns:
            return [
                {"kind": "assignment", "id": str(row["assignment_id"])}
                for row in conn.execute(
                    "SELECT DISTINCT assignment_id FROM inference_assignments WHERE profile_id=? ORDER BY assignment_id",
                    (profile_id,),
                ).fetchall()
            ]
        return self._registered_store_dependencies(
            conn, profile_id, table="inference_assignments", kind="assignment"
        )

    def _route_plan_dependencies(self, conn: Any, profile_id: str) -> list[dict[str, str]]:
        return self._registered_store_dependencies(
            conn, profile_id, table="inference_route_plans", kind="route_plan"
        )
