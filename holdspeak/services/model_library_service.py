"""Owner-facing Model Library availability authority (HS-143-12).

This service composes catalog/local availability with the canonical profile and
binding authorities.  It is deliberately not an assignment editor: every
library command snapshots assignment heads on both sides and never calls
``InferenceAssignmentService.set_assignment``.

Provider drafts are command-shaped.  Their endpoint/key material is retained
only in the private target/deployment/key-custody authorities; a profile
revision, public library projection, persisted command receipt, and error
never contain it.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..deployment_revisions import DeploymentRevision
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound, ServiceError, ValidationError
from .model_profile_service import ModelProfileService
from .profile_key_service import ProfileKeyService
from .profile_service import ProfileService

MODEL_LIBRARY_SCHEMA = "ModelLibraryProjection@1"
_SUCCESS_COPY = "Added to the Model Library. Assignments are unchanged."
_ACTIONS = frozenset({
    "Download", "Add to library", "Connect", "Add model", "Ready", "Checking", "Try again",
})
# The aggregate owns the header truth too: the browser must not infer that an
# empty library is ready merely because there are no repairs to count.
_SUMMARY_STATES = frozenset({"empty", "ready", "attention"})
_PROVIDER_FAMILIES = frozenset({
    "openrouter", "anthropic", "openai_compatible", "private_endpoint", "paired_device", "future_backend",
})
_PROFILE_ID = re.compile(r"^[a-z][a-z0-9_-]{0,95}$")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _text(value: Any, fallback: str = "Model") -> str:
    """Return a small presentation label; never project a locator or secret."""
    text = str(value or "").strip()
    if not text or len(text) > 200 or "/" in text or "\\" in text or "secret" in text.lower():
        return fallback
    return text


class ModelLibraryApplicationService:
    """The one owner-only aggregate and availability command boundary."""

    def __init__(
        self,
        db: Any,
        *,
        setup_service: Any,
        acquisition_service: Any,
        profile_service: ModelProfileService | None = None,
        target_profile_service: ProfileService | None = None,
        profile_key_service: ProfileKeyService | None = None,
    ) -> None:
        self._db = db
        self._setup = setup_service
        self._acquisition = acquisition_service
        self._profiles = profile_service or ModelProfileService(db)
        # These are private execution/custody adapters.  The library aggregate
        # is their sole ordinary owner-facing writer; they are never projected.
        self._target_profiles = target_profile_service or ProfileService(db)
        self._keys = profile_key_service or ProfileKeyService(db)

    @staticmethod
    def require_owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "model_library_owner_required", "Owner access is required.", context={"status": 403}
            )

    def get_library(self, principal: Principal) -> dict[str, Any]:
        self.require_owner(principal)
        setup = self._setup.get_model_library_facts(principal)
        profiles = self._profiles.list_profiles(principal)
        rows = self._rows(setup, profiles)
        return {
            "schema": MODEL_LIBRARY_SCHEMA,
            "catalog_revision": int(setup["preset_catalog"]["catalog_revision"]),
            "artifact_detection": {"state": str(setup["artifact_detection"]["state"])},
            "summary": self._summary(rows),
            "rows": rows,
        }

    # Alias makes the projection's intent obvious to transport callers.
    projection = get_library

    def download(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        """Start a catalog-pinned library download without any assignment write."""
        self.require_owner(principal)
        if not isinstance(body, dict) or set(body) != {"request_id", "catalog_id", "catalog_revision"}:
            raise ServiceError("model_library_download_invalid", "Download has an invalid request shape.", context={"status": 400})
        request = {
            "request_id": self._request_id(body.get("request_id")),
            "catalog_id": self._identifier(body.get("catalog_id"), "catalog_id"),
            "catalog_revision": self._revision(body.get("catalog_revision")),
        }
        before = self.assignment_heads(principal)
        result = self._acquisition.download(
            principal,
            {
                "request_id": request["request_id"],
                "catalog_id": request["catalog_id"],
                "catalog_revision": request["catalog_revision"],
            },
        )
        return self._receipt(before, self.assignment_heads(principal), result)

    def add_to_library(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        """Adopt one freshly re-resolved server-detected artifact."""
        self.require_owner(principal)
        if not isinstance(body, dict) or set(body) != {"request_id", "detected_artifact_id"}:
            raise ServiceError("model_library_add_invalid", "Add to library has an invalid request shape.", context={"status": 400})
        request = {
            "request_id": self._request_id(body.get("request_id")),
            "detected_artifact_id": self._identifier(body.get("detected_artifact_id"), "detected_artifact_id"),
        }
        before = self.assignment_heads(principal)
        result = self._acquisition.add_to_library(principal, request)
        return self._receipt(before, self.assignment_heads(principal), result)

    def use_model_file(
        self, principal: Principal, *, request_id: Any, filename: Any, staging_path: Path,
    ) -> dict[str, Any]:
        """Ingest a hub-staged upload.  ``staging_path`` never enters a DTO."""
        self.require_owner(principal)
        clean_request_id = self._request_id(request_id)
        clean_name = Path(str(filename or "")).name
        if not clean_name or clean_name != str(filename or "") or len(clean_name) > 180:
            raise ServiceError("model_library_upload_invalid", "Model file name is invalid.", context={"status": 400})
        before = self.assignment_heads(principal)
        result = self._acquisition.adopt_uploaded(
            principal, request_id=clean_request_id, filename=clean_name, staging_path=staging_path,
        )
        return self._receipt(before, self.assignment_heads(principal), result)

    def connect_hosted_model(
        self, principal: Principal, draft: dict[str, Any], secret: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Connect OpenRouter or Anthropic through one explicit provider draft.

        ``secret`` is intentionally separate from the canonical draft.  It is
        consumed directly by ``ProfileKeyService`` and is never included in the
        durable replay hash or any result.
        """
        return self._connect_provider(principal, draft, secret, hosted=True)

    def define_endpoint(
        self, principal: Principal, draft: dict[str, Any], secret: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Define one explicit OpenAI-compatible/private endpoint draft."""
        return self._connect_provider(principal, draft, secret, hosted=False)

    def connect_paired_device(self, principal: Principal, draft: dict[str, Any]) -> dict[str, Any]:
        """Add an existing paired/mesh destination without creating a target."""
        return self._connect_provider(principal, draft, None, hosted=False, paired=True)

    def _connect_provider(
        self,
        principal: Principal,
        raw_draft: dict[str, Any],
        secret: dict[str, Any] | None,
        *,
        hosted: bool,
        paired: bool = False,
    ) -> dict[str, Any]:
        self.require_owner(principal)
        draft = self._provider_draft(raw_draft, hosted=hosted, paired=paired)
        # Validate the write-only body before reserving a command.  This retains
        # the value only on the stack, never in a ServiceError/context/receipt.
        key_value = self._secret_value(secret, required=draft["requires_key"])
        request_hash = _digest({"kind": draft["command_kind"], "draft": draft["hash_material"]})
        before = self.assignment_heads(principal)
        replay = self._provider_command(draft["request_id"], draft["command_kind"], request_hash, draft["profile_id"])
        if replay is not None:
            response = replay
            self._assert_assignment_unchanged(principal, before, response)
            return response

        # A custody failure leaves this reservation pending.  Replaying the
        # exact nonsecret draft is therefore safe after a delayed/unavailable
        # key store, while a changed draft with the same request id is refused.
        profile = self._ensure_profile(principal, draft)
        target_id = self._ensure_private_target(principal, draft)
        if draft["requires_key"] and key_value is not None:
            # Existing ProfileKeyService is the only durable key writer.
            self._keys.set(principal, target_id, {"value": key_value})
        deployment_id, deployment_revision_id = self._ensure_provider_deployment(draft, profile, target_id)
        observation_id = self._ensure_provider_readiness(
            principal, draft, profile, deployment_id, deployment_revision_id,
        )
        binding = self._ensure_binding(
            principal, profile, deployment_id, deployment_revision_id, observation_id,
        )
        after = self.assignment_heads(principal)
        receipt = self._provider_receipt(
            principal, before, after, profile, binding, draft, target_id,
        )
        self._complete_provider_command(draft["request_id"], request_hash, receipt)
        return receipt

    def assignment_heads(self, principal: Principal) -> dict[str, Any]:
        """Read the canonical assignment heads; never instantiate a write path."""
        self.require_owner(principal)
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT assignment_key,assignment_id,revision,cleared
                     FROM inference_assignment_heads ORDER BY assignment_key"""
            ).fetchall()
        heads = [
            {"assignment_key": str(row["assignment_key"]), "assignment_id": str(row["assignment_id"]),
             "revision": int(row["revision"]), "cleared": bool(row["cleared"])}
            for row in rows
        ]
        return {"heads": heads, "sha256": _digest(heads)}

    def _receipt(self, before: dict[str, Any], after: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        self._assert_assignment_heads(before, after)
        # Acquisition data is already public/safe; keeping it nested makes this
        # route a closed transport instead of leaking its persistence plan.
        acquisition = result.get("acquisition") if isinstance(result, dict) else None
        return {
            "receipt": {
                "kind": "model_library_add",
                "message": _SUCCESS_COPY,
                "assignments_unchanged": True,
                "assignments_before": before,
                "assignments_after": after,
            },
            "acquisition": acquisition,
        }

    @staticmethod
    def _assert_assignment_heads(before: dict[str, Any], after: dict[str, Any]) -> None:
        if before != after:
            raise ServiceError(
                "model_library_assignment_changed", "Model Library cannot change assignments.", context={"status": 409}
            )

    def _assert_assignment_unchanged(self, principal: Principal, before: dict[str, Any], response: dict[str, Any]) -> None:
        receipt = response.get("receipt") if isinstance(response, dict) else None
        if not isinstance(receipt, dict) or receipt.get("assignments_before") != before:
            raise ServiceError("model_library_assignment_changed", "Model Library cannot change assignments.", context={"status": 409})
        self._assert_assignment_heads(before, self.assignment_heads_dummy(receipt))
        self._assert_assignment_heads(before, self.assignment_heads(principal))

    @staticmethod
    def assignment_heads_dummy(receipt: dict[str, Any]) -> dict[str, Any]:
        after = receipt.get("assignments_after")
        if not isinstance(after, dict):
            raise ServiceError("model_library_provider_receipt_invalid", "Provider command receipt is invalid.", context={"status": 409})
        return after

    def _provider_draft(self, body: dict[str, Any], *, hosted: bool, paired: bool) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise ServiceError("model_library_provider_invalid", "Provider draft is invalid.", context={"status": 400})
        if paired:
            allowed = {
                "request_id", "profile_id", "expected_profile_revision", "label", "model",
                "paired_target_id", "provider_family",
            }
        elif hosted:
            allowed = {
                "request_id", "profile_id", "expected_profile_revision", "label", "provider_family",
                "model", "requires_key",
            }
        else:
            allowed = {
                "request_id", "profile_id", "expected_profile_revision", "label", "provider_family",
                "model", "endpoint", "requires_key",
            }
        if set(body) != allowed:
            raise ServiceError("model_library_provider_invalid", "Provider draft is invalid.", context={"status": 400})
        family = self._clean_provider_family(body.get("provider_family"))
        if hosted and family not in {"openrouter", "anthropic"}:
            raise ServiceError("model_library_provider_invalid", "Hosted provider is invalid.", context={"status": 400})
        if not hosted and not paired and family not in {"openai_compatible", "private_endpoint", "future_backend"}:
            raise ServiceError("model_library_provider_invalid", "Endpoint provider is invalid.", context={"status": 400})
        if paired and family != "paired_device":
            raise ServiceError("model_library_provider_invalid", "Paired provider is invalid.", context={"status": 400})
        profile_id = self._profile_id(body.get("profile_id"))
        expected = body.get("expected_profile_revision")
        if type(expected) is not int or expected < 0:
            raise ServiceError("model_library_provider_invalid", "Provider revision is invalid.", context={"status": 400})
        label = self._safe_field(body.get("label"), "Provider model")
        model = self._safe_field(body.get("model"), "model", allow_slash=True)
        requires_key = bool(body.get("requires_key", False))
        if not paired and type(body.get("requires_key")) is not bool:
            raise ServiceError("model_library_provider_invalid", "Provider key requirement is invalid.", context={"status": 400})
        endpoint = ""
        paired_target_id = ""
        if hosted:
            endpoint = "https://openrouter.ai/api/v1" if family == "openrouter" else "https://api.anthropic.com/v1"
            requires_key = True
        elif paired:
            paired_target_id = self._identifier(body.get("paired_target_id"), "paired_target_id")
        else:
            endpoint = self._endpoint(body.get("endpoint"))
        command_kind = "connect_hosted" if hosted else ("connect_paired" if paired else "define_endpoint")
        hash_material = {
            "profile_id": profile_id,
            "expected_profile_revision": expected,
            "label": label,
            "provider_family": family,
            "model": model,
            "requires_key": requires_key,
            # Only a SHA reaches durable replay material, not the locator itself.
            "endpoint_sha256": _digest(endpoint) if endpoint else "",
            "paired_target_id": paired_target_id,
        }
        return {
            "request_id": self._request_id(body.get("request_id")),
            "command_kind": command_kind,
            "profile_id": profile_id,
            "expected_profile_revision": expected,
            "label": label,
            "provider_family": family,
            "model": model,
            "requires_key": requires_key,
            "endpoint": endpoint,
            "paired_target_id": paired_target_id,
            "hash_material": hash_material,
        }

    def _ensure_profile(self, principal: Principal, draft: dict[str, Any]) -> dict[str, Any]:
        desired = self._profile_body(draft)
        try:
            current = self._profiles.get_profile(principal, draft["profile_id"])
        except NotFound:
            current = None
        if current is not None:
            if self._profile_matches(current, desired):
                # Pending custody retries resume their already-created immutable revision.
                return current
            if int(current["revision"]) != draft["expected_profile_revision"]:
                raise ConflictError(
                    "Model profile changed. Refresh before saving.", code="model_profile_revision_conflict",
                    context={"status": 409},
                )
        return self._profiles.create_profile(principal, desired)

    @staticmethod
    def _profile_matches(current: dict[str, Any], desired: dict[str, Any]) -> bool:
        return all(current.get(key) == desired.get(key) for key in (
            "profile_id", "label", "provider_family", "runtime_family", "model_or_artifact_identity",
            "supported_modalities", "context_support", "tokenizer_template_requirements",
            "capability_manifest", "safe_presentation",
        ))

    @staticmethod
    def _profile_body(draft: dict[str, Any]) -> dict[str, Any]:
        claims = ["language"]
        evidence = {"revision": "model-library-provider-v1", "claims": claims}
        manifest = {**evidence, "sha256": _digest(evidence)}
        runtime = {
            "openrouter": "openai_compatible_v1",
            # Custody may understand Anthropic before execution does. It still
            # uses the existing endpoint deployment grammar; projection below
            # is what enforces the no-false-Ready runtime truth.
            "anthropic": "openai_compatible_v1",
            "openai_compatible": "openai_compatible_v1",
            "private_endpoint": "openai_compatible_v1",
            "paired_device": "paired_device_v1",
            "future_backend": "future_backend_v1",
        }[draft["provider_family"]]
        return {
            "profile_id": draft["profile_id"],
            "expected_revision": draft["expected_profile_revision"],
            "label": draft["label"],
            "provider_family": draft["provider_family"],
            "runtime_family": runtime,
            "model_or_artifact_identity": draft["model"],
            "supported_modalities": claims,
            "context_support": "bounded",
            "tokenizer_template_requirements": {},
            "capability_manifest": manifest,
            "safe_presentation": {"summary": "Connected provider"},
        }

    def _ensure_private_target(self, principal: Principal, draft: dict[str, Any]) -> str:
        if draft["paired_target_id"]:
            target = self._db.profiles.get(draft["paired_target_id"])
            if target is None or str(getattr(target, "kind", "")) not in {"desktop", "meshNode"}:
                raise ServiceError("model_library_paired_target_invalid", "Paired device is unavailable.", context={"status": 400})
            return str(getattr(target, "id"))
        target_id = f"library_provider_{draft['profile_id']}"
        kind = "openAICompatible"
        fields = {
            "id": target_id,
            "name": draft["label"],
            "kind": kind,
            "base_url": draft["endpoint"],
            "model": draft["model"],
            "requires_key": draft["requires_key"],
        }
        existing = self._db.profiles.get(target_id)
        if existing is None:
            self._target_profiles.create_profile(principal, fields)
        elif not self._target_matches(existing, fields):
            # This is an explicit library command, never an ordinary Models
            # screen autosave. The legacy target remains private adaptation data.
            self._target_profiles.update_profile(principal, target_id, fields)
        return target_id

    @staticmethod
    def _target_matches(target: Any, fields: dict[str, Any]) -> bool:
        return (
            str(getattr(target, "name", "")) == str(fields["name"])
            and str(getattr(target, "kind", "")) == str(fields["kind"])
            and str(getattr(target, "base_url", "")) == str(fields["base_url"])
            and str(getattr(target, "model", "")) == str(fields["model"])
            and bool(getattr(target, "requires_key", False)) == bool(fields["requires_key"])
        )

    def _ensure_provider_deployment(
        self, draft: dict[str, Any], profile: dict[str, Any], target_id: str,
    ) -> tuple[str, str]:
        profile_revision = int(profile["revision"])
        deployment_id = f"library-provider-{draft['profile_id']}-r{profile_revision}"
        with self._db._connection() as conn:
            existing = conn.execute(
                "SELECT execution_revision_id FROM inference_deployments WHERE deployment_id=?", (deployment_id,)
            ).fetchone()
        if existing is not None:
            return deployment_id, str(existing["execution_revision_id"])
        target = self._db.profiles.get(target_id)
        if target is None:
            raise ServiceError("model_library_provider_invalid", "Provider destination is unavailable.", context={"status": 409})
        from ..inference_targets import target_from_profile

        identity = target_from_profile(target, self._db).deployment
        if identity is None:
            raise ServiceError("model_library_provider_invalid", "Provider destination is unavailable.", context={"status": 409})
        revision = DeploymentRevision.from_identity(identity)
        artifact_id = f"provider-material-{draft['profile_id']}-r{profile_revision}"
        material = {
            "schema": "ModelLibraryProviderMaterial@1",
            "profile_id": draft["profile_id"],
            "profile_revision": profile_revision,
            "provider_family": draft["provider_family"],
            "model": draft["model"],
        }
        now = _now()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO inference_model_artifacts
                       (artifact_id,format,source_kind,source_repository,source_revision,
                        manifest_json,manifest_sha256,installed_bytes,state,local_locator,
                        created_at,verified_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        artifact_id, "gguf", "model_library_provider_material", draft["provider_family"],
                        str(profile_revision), _canonical(material), _digest(material), 1, "verified", "", now, now,
                    ),
                )
                conn.execute(
                    """INSERT OR IGNORE INTO deployment_revisions
                       (id,schema_version,destination_id,kind,engine,model,node,boundary,
                        endpoint,model_path,secret_slot,runtime_id,runtime_revision,artifact_id,
                        manifest_sha256,format,architecture,context_ceiling,capability_sha256)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        revision.id, revision.schema_version, revision.destination_id, revision.kind,
                        revision.engine, revision.model, revision.node, revision.boundary,
                        revision.endpoint, revision.model_path, revision.secret_slot, revision.runtime_id,
                        revision.runtime_revision, revision.artifact_id, revision.manifest_sha256,
                        revision.format, revision.architecture, revision.context_ceiling, revision.capability_sha256,
                    ),
                )
                conn.execute(
                    """INSERT INTO inference_deployments
                       (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,
                        model_identity,context_ceiling,recommended_context,capability_json,
                        capability_sha256,execution_revision_id,configuration_revision,active,
                        created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        deployment_id, target_id, "", "", artifact_id, draft["model"], 16_384, 16_384,
                        "{}", "", revision.id, 1, 0, now, now,
                    ),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return deployment_id, revision.id

    def _ensure_provider_readiness(
        self,
        principal: Principal,
        draft: dict[str, Any],
        profile: dict[str, Any],
        deployment_id: str,
        deployment_revision_id: str,
    ) -> str:
        profile_revision = int(profile["revision"])
        with self._db._connection() as conn:
            existing = conn.execute(
                """SELECT observation_id FROM model_profile_readiness_observations
                     WHERE deployment_head_id=? AND deployment_configuration_revision=1
                       AND deployment_revision_id=? ORDER BY observed_at DESC LIMIT 1""",
                (deployment_id, deployment_revision_id),
            ).fetchone()
        if existing is not None:
            return str(existing["observation_id"])
        if draft["provider_family"] == "anthropic":
            # There is no Anthropic execution adapter in this product yet. A
            # key may be durably held, but it never turns this row into Ready.
            return self._record_readiness(deployment_id, deployment_revision_id, "unavailable", "anthropic_runtime_missing")
        if draft["provider_family"] == "future_backend":
            return self._record_readiness(deployment_id, deployment_revision_id, "unavailable", "runtime_unavailable")
        observation = self._profiles.probe_profile(principal, {
            "profile_id": draft["profile_id"],
            "profile_revision": profile_revision,
            "deployment_head_id": deployment_id,
            "expected_deployment_configuration_revision": 1,
            "expected_deployment_revision_id": deployment_revision_id,
        })
        return str(observation["observation_id"])

    def _record_readiness(self, deployment_id: str, revision_id: str, state: str, reason_code: str) -> str:
        observation_id = "ready_" + uuid.uuid4().hex
        with self._db._connection() as conn:
            conn.execute(
                """INSERT INTO model_profile_readiness_observations
                   (observation_id,deployment_head_id,deployment_configuration_revision,
                    deployment_revision_id,state,reason_code,observed_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (observation_id, deployment_id, 1, revision_id, state, reason_code, _now()),
            )
        return observation_id

    def _ensure_binding(
        self,
        principal: Principal,
        profile: dict[str, Any],
        deployment_id: str,
        deployment_revision_id: str,
        observation_id: str,
    ) -> dict[str, Any]:
        profile_id = str(profile["profile_id"])
        binding_id = f"binding-{profile_id}"
        try:
            existing = self._profiles.get_binding(principal, binding_id)
        except NotFound:
            existing = None
        if existing is not None and (
            int(existing["profile_revision"]) == int(profile["revision"])
            and str(existing["deployment_head_id"]) == deployment_id
            and str(existing["deployment_revision_id"]) == deployment_revision_id
        ):
            return existing
        return self._profiles.bind_profile(principal, {
            "binding_id": binding_id,
            "profile_id": profile_id,
            "profile_revision": int(profile["revision"]),
            "deployment_head_id": deployment_id,
            "expected_binding_revision": int(existing["revision"]) if existing is not None else 0,
            "expected_deployment_configuration_revision": 1,
            "expected_deployment_revision_id": deployment_revision_id,
            "enabled": True,
            "readiness_observation_id": observation_id,
        })

    def _provider_receipt(
        self,
        principal: Principal,
        before: dict[str, Any],
        after: dict[str, Any],
        profile: dict[str, Any],
        binding: dict[str, Any],
        draft: dict[str, Any],
        target_id: str,
    ) -> dict[str, Any]:
        self._assert_assignment_heads(before, after)
        target = self._db.profiles.get(target_id)
        secret_presence = {"required": bool(draft["requires_key"]), "present": False}
        if target is not None and str(getattr(target, "kind", "")) == "openAICompatible":
            # Query the same injected custody authority that confirmed the
            # write. No key value crosses this return boundary.
            secret_presence = self._keys.presence(principal, target_id)
        return {
            "receipt": {
                "kind": "model_library_provider",
                "message": _SUCCESS_COPY,
                "assignments_unchanged": True,
                "assignments_before": before,
                "assignments_after": after,
            },
            "provider": {
                "profile_id": str(profile["profile_id"]),
                "profile_revision": int(profile["revision"]),
                "binding_id": str(binding["binding_id"]),
                "binding_revision": int(binding["revision"]),
                "provider_family": draft["provider_family"],
                "secret": secret_presence,
            },
        }

    def _provider_command(self, request_id: str, kind: str, request_hash: str, profile_id: str) -> dict[str, Any] | None:
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute(
                    """SELECT command_kind,request_sha256,state,response_json
                         FROM model_library_provider_commands WHERE request_id=?""", (request_id,)
                ).fetchone()
                if row is not None:
                    if str(row["command_kind"]) != kind or str(row["request_sha256"]) != request_hash:
                        raise ConflictError(
                            "Provider request was already used with different details.",
                            code="model_library_provider_request_mismatch", context={"status": 409},
                        )
                    if str(row["state"]) == "completed":
                        raw = str(row["response_json"] or "")
                        try:
                            response = json.loads(raw)
                        except json.JSONDecodeError as exc:
                            raise ServiceError("model_library_provider_receipt_invalid", "Provider command receipt is invalid.", context={"status": 409}) from exc
                        conn.commit()
                        return response if isinstance(response, dict) else None
                    conn.commit()
                    return None
                conn.execute(
                    """INSERT INTO model_library_provider_commands
                       (request_id,command_kind,request_sha256,profile_id,state,response_json,response_sha256,created_at,updated_at)
                       VALUES (?,?,?,?, 'pending', NULL, NULL, ?, ?)""",
                    (request_id, kind, request_hash, profile_id, _now(), _now()),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return None

    def _complete_provider_command(self, request_id: str, request_hash: str, receipt: dict[str, Any]) -> None:
        encoded = _canonical(receipt)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute(
                    "SELECT request_sha256,state FROM model_library_provider_commands WHERE request_id=?", (request_id,)
                ).fetchone()
                if row is None or str(row["request_sha256"]) != request_hash:
                    raise ConflictError("Provider command changed. Retry the original draft.", code="model_library_provider_request_mismatch", context={"status": 409})
                if str(row["state"]) == "completed":
                    conn.commit()
                    return
                conn.execute(
                    """UPDATE model_library_provider_commands
                          SET state='completed',response_json=?,response_sha256=?,updated_at=?
                        WHERE request_id=?""",
                    (encoded, _digest(receipt), _now(), request_id),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def _secret_value(body: dict[str, Any] | None, *, required: bool) -> str | None:
        if body is None:
            return None
        if not isinstance(body, dict) or set(body) != {"value"}:
            raise ServiceError("model_library_secret_invalid", "Provider credential is invalid.", context={"status": 400})
        value = body.get("value")
        if not isinstance(value, str):
            raise ServiceError("model_library_secret_invalid", "Provider credential is invalid.", context={"status": 400})
        # Keep exact key-store validation without ever including the supplied
        # material in a message, structured context, or replay payload.
        value = value.strip()
        if not value or len(value) > ProfileKeyService.MAX_VALUE_LENGTH or any(char in value for char in ("\x00", "\r", "\n")):
            raise ServiceError("model_library_secret_invalid", "Provider credential is invalid.", context={"status": 400})
        return value

    @staticmethod
    def _request_id(value: Any) -> str:
        value = str(value or "").strip()
        if not value or len(value) > 128:
            raise ServiceError("model_library_request_id_invalid", "A stable request id is required.", context={"status": 400})
        return value

    @staticmethod
    def _identifier(value: Any, field: str) -> str:
        value = str(value or "").strip()
        if not value or len(value) > 160:
            raise ServiceError("model_library_request_invalid", f"{field} is invalid.", context={"status": 400})
        return value

    @staticmethod
    def _profile_id(value: Any) -> str:
        clean = str(value or "").strip()
        if not _PROFILE_ID.fullmatch(clean):
            raise ServiceError("model_library_provider_invalid", "Provider profile id is invalid.", context={"status": 400})
        return clean

    @staticmethod
    def _safe_field(value: Any, fallback: str, *, allow_slash: bool = False) -> str:
        text = str(value or "").strip()
        if (
            not text or len(text) > 200 or any(ord(char) < 32 for char in text)
            or "\\" in text or (not allow_slash and "/" in text)
            or (allow_slash and text.startswith("/"))
        ):
            raise ServiceError("model_library_provider_invalid", "Provider draft is invalid.", context={"status": 400})
        return text

    @staticmethod
    def _clean_provider_family(value: Any) -> str:
        family = str(value or "").strip()
        if family not in _PROVIDER_FAMILIES:
            raise ServiceError("model_library_provider_invalid", "Provider family is invalid.", context={"status": 400})
        return family

    @staticmethod
    def _endpoint(value: Any) -> str:
        from urllib.parse import urlparse

        endpoint = str(value or "").strip()
        parsed = urlparse(endpoint)
        if (
            not endpoint or len(endpoint) > 1024 or parsed.scheme not in {"http", "https"}
            or not parsed.netloc or parsed.username or parsed.password or any(ord(char) < 32 for char in endpoint)
        ):
            raise ServiceError("model_library_provider_invalid", "Provider endpoint is invalid.", context={"status": 400})
        return endpoint.rstrip("/")

    @staticmethod
    def _revision(value: Any) -> int:
        if type(value) is not int or value < 1:
            raise ServiceError("model_library_request_invalid", "catalog_revision is invalid.", context={"status": 400})
        return value

    @staticmethod
    def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Project the closed header state from the same facts as the rows."""
        ready_count = sum(row["status"] == "ready" for row in rows)
        attention_count = sum(row["repair"] is not None for row in rows)
        if not rows:
            state, label = "empty", "Add model"
        elif attention_count:
            state, label = "attention", "Needs attention"
        else:
            state, label = "ready", "Ready"
        if state not in _SUMMARY_STATES:
            raise AssertionError("model library summary is not closed")
        return {
            "state": state,
            "label": label,
            "ready_count": ready_count,
            "attention_count": attention_count,
        }

    def _rows(self, setup: dict[str, Any], profiles: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in setup.get("presets", []):
            kind = str(item.get("kind") or "")
            source = "catalog"
            if kind == "local_artifact_preset" and item.get("activation") == "download":
                status, action, repair = "available", "Download", None
            elif kind in {"hosted_preset", "hosted_provider", "hosted_profile_preset"}:
                status, action, repair = "available", "Connect", None
            else:
                status, action, repair = "available", "Add model", None
            rows.append(self._row(
                row_id="catalog:" + _text(item.get("id"), "unknown"), source=source,
                label=_text(item.get("label")), status=status, action=action, repair=repair,
                detail={"format": _text(item.get("format"), "unknown"), "catalog_revision": int(setup["preset_catalog"]["catalog_revision"])},
            ))
        for item in setup.get("detected_local_artifacts", []):
            format_id = str(item.get("format") or "unknown")
            if format_id == "gguf":
                status, action, repair = "detected", "Add to library", None
            else:
                status, action, repair = "unavailable", "Add model", self._repair("runtime_unavailable", "MLX runtime is not installed")
            rows.append(self._row(
                row_id="detected:" + _text(item.get("id"), "unknown"), source="detected",
                label=_text(item.get("label"), "Local model"), status=status, action=action, repair=repair,
                detail={"format": format_id, "size_bytes": int(item.get("size_bytes") or 0)},
            ))
        for item in setup.get("installed_model_artifacts", []):
            format_id = _text(item.get("format"), "unknown")
            if format_id == "mlx_safetensors":
                status, action, repair = "broken", "Add model", self._repair("mlx_runtime_unavailable", "MLX runtime is not installed")
            else:
                status, action, repair = "ready", "Ready", None
            rows.append(self._row(
                row_id="installed:" + _text(item.get("id"), "unknown"), source="installed",
                label=_text(item.get("id"), "Installed model"), status=status, action=action, repair=repair,
                detail={"format": format_id, "installed_bytes": int(item.get("installed_bytes") or 0), "source_revision": _text(item.get("source_revision"), "unknown")},
            ))
        for item in setup.get("acquisitions", []):
            state = str(item.get("state") or "indeterminate")
            if state in {"requested", "resolving_source", "downloading", "verifying", "installing"}:
                status, action, repair = "acquiring", "Checking", None
            elif state == "ready" and str(item.get("activation_state")) == "not_requested":
                status, action, repair = "ready", "Ready", None
            else:
                error = dict(item.get("error") or {})
                status, action, repair = "broken", "Try again", self._repair(_text(error.get("code"), "acquisition_failed"), _text(error.get("message"), "Try again"))
            rows.append(self._row(
                row_id="acquisition:" + _text(item.get("id"), "unknown"), source="acquiring",
                label=_text(item.get("preset_id"), "Model download"), status=status, action=action, repair=repair,
                detail={"state": state, "verified_bytes": int(item.get("verified_bytes") or 0), "bytes_total": int(item.get("bytes_total") or 0)},
            ))
        for item in profiles.get("profiles", []):
            rows.append(self._profile_row(item))
        for item in profiles.get("legacy_profiles", []):
            legacy_profile = dict(item.get("profile") or {})
            rows.append(self._row(
                row_id="legacy:" + _text(item.get("source_id"), "unknown"), source="legacy",
                label=_text(legacy_profile.get("label")), status="configured", action="Add model",
                repair=self._repair("legacy_adapter", "Add this legacy model to the library"),
                detail={"provider_family": _text(legacy_profile.get("provider_family"), "legacy")},
            ))
        return rows

    def _profile_row(self, item: dict[str, Any]) -> dict[str, Any]:
        binding = item.get("current_binding") or None
        readiness = item.get("latest_readiness") or None
        family = _text(item.get("provider_family"), "unknown")
        if binding is None:
            status, action, repair = "configured", "Add model", self._repair("binding_missing", "Model needs a deployment binding")
        elif family == "anthropic":
            # Exact orchestrator ruling: stored custody is not an executable adapter.
            status, repair = "broken", self._repair("anthropic_runtime_missing", "Anthropic runtime is not installed")
            action = repair["label"]
        elif readiness and readiness.get("state") == "ready":
            status, action, repair = "ready", "Ready", None
        else:
            code = _text((readiness or {}).get("reason_code"), "readiness_unknown")
            repair = self._provider_repair(code, family)
            status, action = "broken", repair["label"]
        return self._row(
            row_id="profile:" + _text(item.get("profile_id"), "unknown"), source="provider" if family in _PROVIDER_FAMILIES else "profile",
            label=_text(item.get("label")), status=status, action=action, repair=repair,
            detail={"provider_family": family, "runtime_family": _text(item.get("runtime_family"), "unknown"), "profile_revision": int(item.get("revision") or 0)},
        )

    @staticmethod
    def _provider_repair(code: str, family: str) -> dict[str, str]:
        labels = {
            "credential_unavailable": "Provider key is missing",
            "endpoint_unreachable": "Endpoint is unavailable",
            "destination_offline": "Paired device is offline",
            "destination_stale": "Paired device model is unavailable",
            "destination_unsupported": "Endpoint is invalid",
            "destination_unavailable": "Provider is unavailable",
            "runtime_unavailable": "Provider runtime is not installed",
            "artifact_unavailable": "Provider material is unavailable",
        }
        return {"code": code, "label": labels.get(code, "Check this model")}

    @staticmethod
    def _repair(code: str, label: str) -> dict[str, str]:
        return {"code": code, "label": label}

    @staticmethod
    def _row(*, row_id: str, source: str, label: str, status: str, action: str, repair: dict[str, str] | None, detail: dict[str, Any]) -> dict[str, Any]:
        if action not in _ACTIONS and (repair is None or action != repair["label"]):
            raise AssertionError("model library action is not closed")
        return {"id": row_id, "source": source, "label": label, "status": status, "detail": detail, "repair": repair, "selected_action": action}


__all__ = ["MODEL_LIBRARY_SCHEMA", "ModelLibraryApplicationService"]
