"""The startup assignment migration: the owner's old Config, once, into assignment rows.

This is the one place the assignment store is written at startup
(``kernel/runtime.py``). Each family reads its old Config selector once and
writes its marker; a family with a marker never reads Config again. The engine
door reads the rows it wrote (``InferenceAssignmentService.chain``). Moved
here from the parked routed-inference waist (2026-11-09).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from ..deployment_revisions import DeploymentRevision
from ..inference_capabilities import (
    InferenceCapabilityRegistry,
    process_inference_capability_registry,
)
from ..principals import Principal
from .errors import ValidationError
from .inference_assignment_service import (
    RECIPE_WORKBENCH_MIGRATION_FAMILY,
    InferenceAssignmentService,
)
from .model_profile_service import ModelProfileService
from holdspeak.timestamps import utc_now_z_micro as _now

MIGRATION_FAMILY = "thoughts-writing-route-assignments"
MEETING_MIGRATION_FAMILY = "meeting-route-assignments"
MEETING_DEFERRED_MIGRATION_FAMILY = "meeting-deferred-route-assignments"
SPEECH_RECOGNITION_MIGRATION_FAMILY = "speech-recognition-route-assignments"
RAILS_OBSERVER_MIGRATION_FAMILY = "rails-observer-route-assignments"
MEETING_ASSIGNMENT_CAPABILITIES = (
    "meeting.live_analysis",
    "meeting.bookmark_label",
    "meeting.auto_title",
)

# The legacy selector has no general repository/path authority.  This closed
# map is the complete set of historically shipped local Whisper selectors that
# can become v2 Model Library authority without guessing or egress.
_LOCAL_WHISPER_ARTIFACTS = {
    (backend, model): f"builtin-whisper-{backend}-{model}"
    for backend in ("mlx", "faster-whisper")
    for model in ("tiny", "base", "small", "medium", "large")
}


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Inference material must be canonical JSON.",
            code="inference_adoption_material_invalid",
        ) from exc


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


class AssignmentMigration:
    """Each old Config selector becomes assignment rows once, or one repair issue."""

    def __init__(self, db: Any, *, registry: InferenceCapabilityRegistry | None = None) -> None:
        self._db = db
        self._registry = registry or process_inference_capability_registry()

    def migrate_meeting_route_assignments(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """Copy the one saved Meeting profile pointer or return a repair issue.

        The legacy Meeting configuration has one persisted profile pointer, not a
        model artifact or endpoint.  A blank pointer therefore cannot lawfully be
        expanded into a local default or an auto/cloud chain.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(
            principal, family=MEETING_MIGRATION_FAMILY
        )
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}
        meeting = getattr(config, "meeting", None)
        profile_id = str(getattr(meeting, "intel_profile_id", "") or "").strip()
        provider = str(getattr(meeting, "intel_provider", "") or "").strip()
        source = {"intel_profile_id": profile_id, "intel_provider": provider}
        source_sha256 = _sha256(source)
        if not profile_id:
            return self._migration_issue(
                MEETING_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_meeting_model_profile",
                source_sha256,
            )
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                (profile_id,),
            ).fetchone()
        revision = int(row["revision"] or 0) if row is not None else 0
        if revision < 1:
            return self._migration_issue(
                MEETING_MIGRATION_FAMILY,
                "legacy_profile_requires_upgrade",
                "upgrade_model_profile",
                source_sha256,
            )
        try:
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=MEETING_MIGRATION_FAMILY,
                source_sha256=source_sha256,
                capability_entries={
                    capability_id: {
                        "profile_id": profile_id,
                        "profile_revision": revision,
                    }
                    for capability_id in MEETING_ASSIGNMENT_CAPABILITIES
                },
            )
        except ValidationError as exc:
            if exc.code != "inference_assignment_incompatible":
                raise
            return self._migration_issue(
                MEETING_MIGRATION_FAMILY,
                "legacy_profile_incompatible",
                "choose_compatible_meeting_model_profile",
                source_sha256,
            )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    def migrate_meeting_deferred_route_assignments(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """Copy the saved Meeting profile into the deferred queue's exact scope.

        This intentionally remains a separate marker family: databases that
        already completed the live Meeting migration must acquire this newly
        adopted deferred capability without re-reading or rewriting that family.
        It follows the same no-guess/refusal law as the live family.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(
            principal, family=MEETING_DEFERRED_MIGRATION_FAMILY
        )
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}
        meeting = getattr(config, "meeting", None)
        profile_id = str(getattr(meeting, "intel_profile_id", "") or "").strip()
        provider = str(getattr(meeting, "intel_provider", "") or "").strip()
        source = {"intel_profile_id": profile_id, "intel_provider": provider}
        source_sha256 = _sha256(source)
        if not profile_id:
            return self._migration_issue(
                MEETING_DEFERRED_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_meeting_model_profile",
                source_sha256,
            )
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                (profile_id,),
            ).fetchone()
        revision = int(row["revision"] or 0) if row is not None else 0
        if revision < 1:
            return self._migration_issue(
                MEETING_DEFERRED_MIGRATION_FAMILY,
                "legacy_profile_requires_upgrade",
                "upgrade_model_profile",
                source_sha256,
            )
        try:
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=MEETING_DEFERRED_MIGRATION_FAMILY,
                source_sha256=source_sha256,
                capability_entries={
                    "meeting.deferred_analysis": {
                        "profile_id": profile_id,
                        "profile_revision": revision,
                    }
                },
            )
        except ValidationError as exc:
            if exc.code != "inference_assignment_incompatible":
                raise
            return self._migration_issue(
                MEETING_DEFERRED_MIGRATION_FAMILY,
                "legacy_profile_incompatible",
                "choose_compatible_meeting_model_profile",
                source_sha256,
            )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    def migrate_speech_recognition_route_assignments(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """Convert one exact, built-in local Whisper selector or refuse it.

        This is intentionally a tiny closed migration: it resolves ``auto`` by
        the runtime's importability-only rule, never loads/downloads a model, and
        refuses repositories, paths, and every remote-shaped selector. The profile,
        unavailable local deployment,
        binding, assignment, and family marker share the assignment service's one
        transaction.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(
            principal, family=SPEECH_RECOGNITION_MIGRATION_FAMILY
        )
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}
        model = getattr(config, "model", None)
        name = str(getattr(model, "name", "") or "").strip().lower()
        saved_backend = str(getattr(model, "backend", "") or "").strip().lower()
        language = str(getattr(model, "language", "") or "").strip().lower()
        backend = saved_backend
        if backend == "auto":
            # Design note §Orchestrator amendment (2026-08-22): `auto` is the
            # owner's historically effective primary. Reuse Transcriber's
            # importability-only resolution; it loads no model and touches no network.
            try:
                from ..transcribe import _resolve_backend

                backend = _resolve_backend("auto")
            except Exception:
                backend = ""
        source_sha256 = _sha256(
            {
                "model_name": name,
                "backend": saved_backend,
                "resolved_backend": backend,
                "language": language,
            }
        )
        artifact_identity = _LOCAL_WHISPER_ARTIFACTS.get((backend, name))
        if not name or artifact_identity is None:
            return self._migration_issue(
                SPEECH_RECOGNITION_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_audio_model_profile",
                source_sha256,
            )
        # The existing language vocabulary treats ``auto`` as the one valid
        # unpinned value.  It is authority about the owned local operation, not
        # an endpoint, secret, or any cloud consent.
        if language and not (language == "auto" or language.isalpha() and len(language) <= 12):
            return self._migration_issue(
                SPEECH_RECOGNITION_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_audio_model_profile",
                source_sha256,
            )
        profile_id = "speech-migrated-" + source_sha256.removeprefix("sha256:")[:24]
        artifact_id = "artifact-" + profile_id
        deployment_id = "deployment-" + profile_id
        binding_id = "binding-" + profile_id
        manifest_evidence = {
            "revision": "legacy-whisper-v1",
            "claims": [
                "audio",
                "speech_language:" + (language or "auto"),
                "result_schema:" + self._registry.require("speech.transcribe").output_schema_sha256,
            ],
        }
        manifest = {**manifest_evidence, "sha256": _sha256(manifest_evidence)}
        profile_payload = ModelProfileService(self._db)._profile_payload({
            "profile_id": profile_id,
            "expected_revision": 0,
            "label": f"Whisper {backend} {name}",
            "provider_family": "local",
            "runtime_family": backend,
            "model_or_artifact_identity": artifact_id,
            "supported_modalities": ["audio"],
            "context_support": "bounded",
            "tokenizer_template_requirements": {},
            "capability_manifest": manifest,
            "safe_presentation": {
                "summary": "Migrated local Whisper selection",
                "badge": "legacy-model-config",
            },
        })
        capability_sha = str(manifest["sha256"])
        artifact_manifest = {"schema": "LegacyWhisperArtifact@1", "identity": artifact_identity}
        artifact_manifest_sha = _sha256(artifact_manifest)
        revision = DeploymentRevision.from_artifact(
            destination_id="local_whisper",
            engine=backend,
            model=artifact_identity,
            runtime_id=backend,
            runtime_revision="legacy-model-config-v1",
            artifact_id=artifact_id,
            manifest_sha256=artifact_manifest_sha,
            format="mlx_safetensors",
            architecture="whisper",
            # Speech emits no prompt tokens, but its frozen lifecycle and
            # transcription children reserve bounded controller output capacity.
            context_ceiling=1024,
            capability_sha256=capability_sha,
        )

        def prelude(conn: Any) -> None:
            now = _now()
            profile_material = {
                "schema_version": 2,
                "profile_id": profile_id,
                "revision": 1,
                **{key: value for key, value in profile_payload.items() if key != "expected_revision"},
            }
            conn.execute(
                """INSERT INTO model_profile_revisions
                   (profile_id,revision,sha256,label,provider_family,runtime_family,
                    model_or_artifact_identity,supported_modalities_json,context_support,
                    tokenizer_template_requirements_json,capability_manifest_json,
                    safe_presentation_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    profile_id, 1, _sha256(profile_material), profile_payload["label"],
                    profile_payload["provider_family"], profile_payload["runtime_family"], artifact_id,
                    _canonical(profile_payload["supported_modalities"]), profile_payload["context_support"],
                    _canonical(profile_payload["tokenizer_template_requirements"]),
                    _canonical(manifest), _canonical(profile_payload["safe_presentation"]), now,
                ),
            )
            conn.execute(
                """INSERT INTO inference_model_artifacts
                   (artifact_id,format,source_kind,source_repository,source_revision,
                    manifest_json,manifest_sha256,installed_bytes,state,local_locator,created_at,verified_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    artifact_id, "mlx_safetensors", "legacy-model-config", artifact_identity,
                    "legacy-model-config-v1", _canonical(artifact_manifest), artifact_manifest_sha,
                    1, "removed", "", now, now,
                ),
            )
            conn.execute(
                """INSERT INTO deployment_revisions
                   (id,schema_version,destination_id,kind,engine,model,node,boundary,
                    endpoint,model_path,secret_slot,runtime_id,runtime_revision,artifact_id,
                    manifest_sha256,format,architecture,context_ceiling,capability_sha256)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    revision.id, revision.schema_version, revision.destination_id, revision.kind,
                    revision.engine, revision.model, revision.node, revision.boundary,
                    revision.endpoint, None, revision.secret_slot, revision.runtime_id,
                    revision.runtime_revision, revision.artifact_id, revision.manifest_sha256,
                    revision.format, revision.architecture, revision.context_ceiling,
                    revision.capability_sha256,
                ),
            )
            conn.execute(
                """INSERT INTO inference_deployments
                   (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,
                    model_identity,context_ceiling,recommended_context,capability_json,
                    capability_sha256,execution_revision_id,configuration_revision,active,
                    created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    deployment_id, "local_whisper", backend, revision.runtime_revision, artifact_id,
                    artifact_identity, 1024, 1024, _canonical(manifest), capability_sha, revision.id,
                    1, 0, now, now,
                ),
            )
            observation_id = "ready-" + profile_id
            conn.execute(
                """INSERT INTO model_profile_readiness_observations
                   (observation_id,deployment_head_id,deployment_configuration_revision,
                    deployment_revision_id,state,reason_code,observed_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (observation_id, deployment_id, 1, revision.id, "unavailable", "artifact_unobserved", now),
            )
            conn.execute(
                """INSERT INTO model_profile_binding_revisions
                   (binding_id,revision,profile_id,profile_revision,deployment_head_id,
                    deployment_configuration_revision,deployment_revision_id,secret_slot,
                    enabled,readiness_observation_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (binding_id, 1, profile_id, 1, deployment_id, 1, revision.id, "", 1, observation_id, now),
            )
            conn.execute(
                "INSERT INTO model_profile_binding_heads(binding_id,profile_id,revision,updated_at) VALUES (?,?,?,?)",
                (binding_id, profile_id, 1, now),
            )

        try:
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=SPEECH_RECOGNITION_MIGRATION_FAMILY,
                source_sha256=source_sha256,
                capability_entries={
                    "speech.transcribe": {"profile_id": profile_id, "profile_revision": 1}
                },
                _prelude=prelude,
            )
        except ValidationError as exc:
            if exc.code != "inference_assignment_incompatible":
                raise
            return self._migration_issue(
                SPEECH_RECOGNITION_MIGRATION_FAMILY,
                "builtin_profile_required",
                "choose_audio_model_profile",
                source_sha256,
            )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    @staticmethod
    def _migration_issue(
        family: str, reason_code: str, repair: str, source_sha256: str
    ) -> dict[str, Any]:
        return {
            "schema": "InferenceAssignmentMigrationIssue@1",
            "family": family,
            "status": "needs_attention",
            "reason_code": reason_code,
            "repair": repair,
            "source_sha256": source_sha256,
        }

    def migrate_rails_observer_route_assignments(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """Convert Rails' one historical local selector without guessing.

        A blank selector is the documented ``this_machine`` deployment.  The
        migration records a minimum local v2 profile/binding from that exact
        saved deployment identity in the same assignment/marker transaction;
        it never tests the path, loads a model, or discovers another target.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(principal, family=RAILS_OBSERVER_MIGRATION_FAMILY)
        if existing is not None:
            # A pre-fix marker may have materialized this Rails-only artifact as
            # active. Repair that older footprint without re-reading Config or
            # re-running migration selection: Rails execution is assignment-led,
            # so it must never participate in the generic local-artifact lookup.
            with self._db._connection() as conn:
                try:
                    conn.execute(
                        """UPDATE inference_deployments SET active=0
                           WHERE active=1 AND artifact_id IN (
                               SELECT artifact_id FROM inference_model_artifacts
                               WHERE source_kind='legacy-rails-observer'
                           )"""
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
            return {**existing, "status": "migrated", "legacy_config_read": False}
        rails = getattr(config, "rails_observer", None)
        # Rails is off by default.  A default-constructed blank selector is not
        # saved observer intent, so it must not mint an otherwise generic local
        # deployment merely because the meeting default happens to name a path.
        # The historic ``this_machine`` sentinel is meaningful only for an
        # enabled observer: that is the installed feature which would have read
        # the saved selector.
        if not bool(getattr(rails, "enabled", False)):
            return {
                "family": RAILS_OBSERVER_MIGRATION_FAMILY,
                "status": "not_applicable",
                "reason_code": "rails_observer_disabled",
                "legacy_config_read": True,
            }
        configured = str(getattr(rails, "profile_id", "") or "").strip()
        source_selector = configured or "this_machine"
        source: dict[str, Any] = {"profile_id": source_selector}
        profile_id = configured
        profile_revision = 0
        local_path = ""
        if configured:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                    (configured,),
                ).fetchone()
            profile_revision = int(row["revision"] or 0) if row is not None else 0
            if profile_revision < 1:
                legacy = self._db.profiles.get(configured)
                if legacy is None or str(getattr(legacy, "kind", "")) != "onDevice":
                    return self._migration_issue(
                        RAILS_OBSERVER_MIGRATION_FAMILY,
                        "legacy_profile_requires_upgrade",
                        "choose_rails_observer_model_profile",
                        _sha256(source),
                    )
                local_path = str(getattr(legacy, "model_file", "") or "").strip()
        else:
            # This function reads the loaded configuration object rather than
            # Config again.  It does no filesystem readiness probe.
            meeting = getattr(config, "meeting", None)
            local_path = str(getattr(meeting, "intel_realtime_model", "") or "").strip()
            if not local_path:
                from ..intel.providers import DEFAULT_INTEL_MODEL_PATH
                local_path = str(DEFAULT_INTEL_MODEL_PATH or "").strip()
        source["same_device_deployment_sha256"] = _sha256({"model_path": local_path})
        source_sha256 = _sha256(source)
        if profile_revision >= 1:
            try:
                marker = assignments.migrate_capability_assignments_atomically(
                    principal,
                    family=RAILS_OBSERVER_MIGRATION_FAMILY,
                    source_sha256=source_sha256,
                    capability_entries={
                        "background.rails_summary": {
                            "profile_id": profile_id,
                            "profile_revision": profile_revision,
                        }
                    },
                )
            except ValidationError as exc:
                if exc.code != "inference_assignment_incompatible":
                    raise
                return self._migration_issue(
                    RAILS_OBSERVER_MIGRATION_FAMILY,
                    "legacy_profile_incompatible",
                    "choose_rails_observer_model_profile",
                    source_sha256,
                )
            return {**marker, "status": "migrated", "legacy_config_read": True}
        if not local_path:
            return self._migration_issue(
                RAILS_OBSERVER_MIGRATION_FAMILY,
                "same_device_deployment_unnamed",
                "choose_rails_observer_model_profile",
                source_sha256,
            )

        # The stored id is a stable public handle; the exact local locator stays
        # only in the private deployment revision, as it did for the legacy path.
        suffix = source_sha256.removeprefix("sha256:")[:24]
        profile_id = "rails-observer-local-" + suffix
        artifact_id = "artifact-" + profile_id
        deployment_id = "deployment-" + profile_id
        binding_id = "binding-" + profile_id
        model = Path(local_path).expanduser().stem
        if not model:
            return self._migration_issue(
                RAILS_OBSERVER_MIGRATION_FAMILY,
                "same_device_deployment_unnamed",
                "choose_rails_observer_model_profile",
                source_sha256,
            )
        self._registry.require("background.rails_summary")
        manifest_evidence = {"revision": "rails-observer-this-machine-v1", "claims": ["language"]}
        manifest = {**manifest_evidence, "sha256": _sha256(manifest_evidence)}
        profile_payload = ModelProfileService(self._db)._profile_payload({
            "profile_id": profile_id,
            "expected_revision": 0,
            "label": f"Rails observer local {model}",
            "provider_family": "local",
            "runtime_family": "configured_local_engine",
            "model_or_artifact_identity": artifact_id,
            "supported_modalities": ["language"],
            "context_support": "bounded",
            "tokenizer_template_requirements": {},
            "capability_manifest": manifest,
            "safe_presentation": {"summary": "Migrated Rails observer local deployment", "badge": "rails-observer"},
        })
        deployment = DeploymentRevision.from_artifact(
            destination_id="this_machine",
            engine="configured_local_engine",
            model=model,
            runtime_id="configured_local_engine",
            runtime_revision="rails-observer-this-machine-v1",
            artifact_id=artifact_id,
            manifest_sha256=_sha256({"same_device_deployment_sha256": source["same_device_deployment_sha256"]}),
            format="gguf",
            architecture="unknown",
            context_ceiling=16384,
            capability_sha256=str(manifest["sha256"]),
            resolved_model_path=local_path,
        )

        def prelude(conn: Any) -> None:
            now = _now()
            profile_material = {"schema_version": 2, "profile_id": profile_id, "revision": 1,
                                **{key: value for key, value in profile_payload.items() if key != "expected_revision"}}
            conn.execute(
                """INSERT INTO model_profile_revisions
                   (profile_id,revision,sha256,label,provider_family,runtime_family,model_or_artifact_identity,
                    supported_modalities_json,context_support,tokenizer_template_requirements_json,
                    capability_manifest_json,safe_presentation_json,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (profile_id, 1, _sha256(profile_material), profile_payload["label"],
                 profile_payload["provider_family"], profile_payload["runtime_family"], artifact_id,
                 _canonical(profile_payload["supported_modalities"]), profile_payload["context_support"],
                 _canonical(profile_payload["tokenizer_template_requirements"]), _canonical(manifest),
                 _canonical(profile_payload["safe_presentation"]), now),
            )
            conn.execute(
                """INSERT INTO inference_model_artifacts
                   (artifact_id,format,source_kind,source_repository,source_revision,manifest_json,
                    manifest_sha256,installed_bytes,state,local_locator,created_at,verified_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                # The saved selector is the exact historical local locator.  It
                # is a truthful private artifact declaration, not a migration
                # probe: readiness remains unavailable until first execution
                # successfully loads this frozen deployment.
                (artifact_id, "gguf", "legacy-rails-observer", "this_machine",
                 "rails-observer-this-machine-v1", _canonical({"same_device_deployment_sha256": source["same_device_deployment_sha256"]}),
                 deployment.manifest_sha256, 1, "verified", local_path, now, now),
            )
            conn.execute(
                """INSERT INTO deployment_revisions
                   (id,schema_version,destination_id,kind,engine,model,node,boundary,endpoint,model_path,
                    secret_slot,runtime_id,runtime_revision,artifact_id,manifest_sha256,format,architecture,
                    context_ceiling,capability_sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (deployment.id, deployment.schema_version, deployment.destination_id, deployment.kind,
                 deployment.engine, deployment.model, deployment.node, deployment.boundary, deployment.endpoint,
                 None, deployment.secret_slot, deployment.runtime_id, deployment.runtime_revision,
                 deployment.artifact_id, deployment.manifest_sha256, deployment.format, deployment.architecture,
                 deployment.context_ceiling, deployment.capability_sha256),
            )
            conn.execute(
                """INSERT INTO inference_deployments
                   (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,model_identity,
                    context_ceiling,recommended_context,capability_json,capability_sha256,execution_revision_id,
                    configuration_revision,active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                # This is capability-owned route material, not the owner's
                # generic current Thought deployment.  Keep it inactive so
                # locator-based Thought resolution cannot adopt the Rails
                # artifact; the explicit background.rails_summary assignment
                # below is its only execution authority.
                (deployment_id, "this_machine", deployment.runtime_id, deployment.runtime_revision, artifact_id,
                 model, 16384, 16384, _canonical(manifest), str(manifest["sha256"]), deployment.id, 1, 0, now, now),
            )
            observation_id = "ready-" + profile_id
            # No probe occurred.  This is deliberately unavailable until the
            # actual frozen execution observes readiness.
            conn.execute(
                """INSERT INTO model_profile_readiness_observations
                   (observation_id,deployment_head_id,deployment_configuration_revision,deployment_revision_id,
                    state,reason_code,observed_at) VALUES (?,?,?,?,?,?,?)""",
                (observation_id, deployment_id, 1, deployment.id, "unavailable", "unobserved_legacy_local", now),
            )
            conn.execute(
                """INSERT INTO model_profile_binding_revisions
                   (binding_id,revision,profile_id,profile_revision,deployment_head_id,
                    deployment_configuration_revision,deployment_revision_id,secret_slot,enabled,
                    readiness_observation_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (binding_id, 1, profile_id, 1, deployment_id, 1, deployment.id, "", 1, observation_id, now),
            )
            conn.execute(
                "INSERT INTO model_profile_binding_heads(binding_id,profile_id,revision,updated_at) VALUES (?,?,?,?)",
                (binding_id, profile_id, 1, now),
            )

        try:
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=RAILS_OBSERVER_MIGRATION_FAMILY,
                source_sha256=source_sha256,
                capability_entries={"background.rails_summary": {"profile_id": profile_id, "profile_revision": 1}},
                _prelude=prelude,
            )
        except ValidationError as exc:
            if exc.code != "inference_assignment_incompatible":
                raise
            return self._migration_issue(
                RAILS_OBSERVER_MIGRATION_FAMILY,
                "same_device_deployment_incompatible",
                "choose_rails_observer_model_profile",
                source_sha256,
            )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    def migrate_recipe_workbench_subject_assignments(
        self, principal: Principal
    ) -> dict[str, Any]:
        """Consume Recipe/Workbench pointers once into exact subject assignments.

        The durable primitive id is the assignment subject.  The old profile id
        is only the one transaction's input and is retained in the marker's
        source-record map for audit; neither blank nor stale pointers become a
        post-marker execution selector.
        """
        family = RECIPE_WORKBENCH_MIGRATION_FAMILY
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(principal, family=family)
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}

        def entry_for(profile_id: str) -> dict[str, Any]:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                    (profile_id,),
                ).fetchone()
                revision = int(row["revision"] or 0) if row is not None else 0
                legacy = conn.execute(
                    "SELECT 1 FROM profiles WHERE id=? AND deleted=0", (profile_id,)
                ).fetchone()
            if revision >= 1:
                return {"profile_id": profile_id, "profile_revision": revision}
            if legacy is not None:
                return {"profile_id": f"legacy-{profile_id}", "profile_revision": 1}
            # Deliberately fail the whole transaction: making a marker around a
            # dangling pointer would hide the repair and make its old intent
            # execution-dead without an explicit refusal.
            raise ValidationError(
                "Legacy subject pointer names a missing model profile.",
                code="inference_assignment_profile_missing",
            )

        subject_entries: list[dict[str, Any]] = []
        source_records: list[dict[str, Any]] = []
        for recipe in self._db.recipes.list():
            value = str(getattr(recipe, "profile_id", "") or "").strip()
            source_records.append({
                "record_kind": "recipe", "record_id": str(recipe.id), "field": "profile_id",
                "legacy_value": value, "legacy_read": bool(value),
            })
            if value:
                profile = entry_for(value)
                for capability_id in ("recipe.run", "chat.turn"):  # HS-151-02: recipe.chat → chat.turn; sequence.step parked 2026-11-08
                    subject_entries.append({
                        "subject_kind": "recipe", "subject_id": str(recipe.id),
                        "capability_id": capability_id, "entry": profile,
                    })
        for workbench in self._db.workbenches.list():
            for field, capability_id in (
                ("profile_id", "workbench.item"),
                ("resolver_profile_id", "voice.reference_resolve"),
            ):
                value = str(getattr(workbench, field, "") or "").strip()
                source_records.append({
                    "record_kind": "workbench", "record_id": str(workbench.id), "field": field,
                    "legacy_value": value, "legacy_read": bool(value),
                })
                if value:
                    subject_entries.append({
                        "subject_kind": "workbench", "subject_id": str(workbench.id),
                        "capability_id": capability_id, "entry": entry_for(value),
                    })
        source_sha256 = _sha256({"records": sorted(source_records, key=lambda item: (item["record_kind"], item["record_id"], item["field"]))})
        marker = assignments.migrate_subject_assignments_atomically(
            principal, family=family, source_sha256=source_sha256,
            subject_entries=subject_entries, source_records=source_records,
        )
        return {**marker, "status": "migrated", "legacy_config_read": True}

    def migrate_startup_legacy_assignments(
        self, principal: Principal, config_loader: Callable[[], Any]
    ) -> dict[str, dict[str, Any]]:
        """Run each startup-owned family once without reading Config after markers."""
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        markers = {
            family: assignments.migration_marker(principal, family=family)
            for family in (
                MIGRATION_FAMILY,
                MEETING_MIGRATION_FAMILY,
                MEETING_DEFERRED_MIGRATION_FAMILY,
                SPEECH_RECOGNITION_MIGRATION_FAMILY,
                RAILS_OBSERVER_MIGRATION_FAMILY,
                RECIPE_WORKBENCH_MIGRATION_FAMILY,
            )
        }
        if all(markers.values()):
            return {
                family: {**marker, "status": "migrated", "legacy_config_read": False}
                for family, marker in markers.items()
                if marker is not None
            }
        config = config_loader()
        return {
            MIGRATION_FAMILY: self.migrate_legacy_config(principal, config),
            MEETING_MIGRATION_FAMILY: self.migrate_meeting_route_assignments(
                principal, config
            ),
            MEETING_DEFERRED_MIGRATION_FAMILY: self.migrate_meeting_deferred_route_assignments(
                principal, config
            ),
            SPEECH_RECOGNITION_MIGRATION_FAMILY: self.migrate_speech_recognition_route_assignments(
                principal, config
            ),
            RAILS_OBSERVER_MIGRATION_FAMILY: self.migrate_rails_observer_route_assignments(
                principal, config
            ),
            RECIPE_WORKBENCH_MIGRATION_FAMILY: self.migrate_recipe_workbench_subject_assignments(
                principal
            ),
        }

    def migrate_legacy_config(
        self, principal: Principal, config: Any
    ) -> dict[str, Any]:
        """One-way Config-pointer adapter; never a post-marker selector.

        A configured v2 profile is copied into capability assignments exactly
        once.  The implicit ``this_machine`` sentinel cannot truthfully name a
        reusable v2 profile, so it returns one explicit repair instead of
        inventing a model identity from mutable Config.
        """
        assignments = InferenceAssignmentService(self._db, registry=self._registry)
        existing = assignments.migration_marker(principal, family=MIGRATION_FAMILY)
        if existing is not None:
            return {**existing, "status": "migrated", "legacy_config_read": False}

        # An owner may have selected all four routes in the assignment surface
        # before the family marker was written.  That selection is already the
        # authority: migrate its effective entries and do not infer a local
        # target from Config.  Incompatible selections remain in place so the
        # owner can repair them from the same surface.
        assigned_routes: dict[str, dict[str, Any]] = {}
        for capability_id in (
            "thought.interview", "ask.answer", "speech.intent_classify", "speech.rewrite",
        ):
            resolved = assignments.resolve_effective(
                principal, capability_id=capability_id,
            )
            if resolved.get("status") not in {"assigned", "no_compatible_assignment"}:
                assigned_routes = {}
                break
            entries = ((resolved.get("assignment") or {}).get("entries") or [])
            if not entries:
                assigned_routes = {}
                break
            assigned_routes[capability_id] = {
                "entries": [
                    {
                        "profile_id": str(entry.get("profile_id") or ""),
                        "profile_revision": int(entry.get("profile_revision") or 0),
                    }
                    for entry in entries
                ],
                "status": str(resolved.get("status") or ""),
            }
        if len(assigned_routes) == 4 and all(
            item["entries"] and all(
                entry["profile_id"] and entry["profile_revision"] > 0
                for entry in item["entries"]
            )
            for item in assigned_routes.values()
        ):
            marker = assignments.migrate_capability_assignments_atomically(
                principal,
                family=MIGRATION_FAMILY,
                source_sha256=_sha256({"assignments": assigned_routes}),
                capability_entries={
                    capability_id: item["entries"]
                    for capability_id, item in assigned_routes.items()
                },
            )
            return {**marker, "status": "migrated", "legacy_config_read": False}

        thoughts = str(
            getattr(getattr(config, "thoughts", None), "inference_target_id", "") or ""
        ).strip()
        writing = str(
            getattr(
                getattr(getattr(config, "dictation", None), "runtime", None),
                "profile_id",
                "",
            )
            or ""
        ).strip()
        source = {"thoughts": thoughts or "this_machine", "writing": writing or "this_machine"}
        source_sha = _sha256(source)
        if not thoughts or not writing or thoughts == "this_machine" or writing == "this_machine":
            return {
                "schema": "InferenceAssignmentMigrationIssue@1",
                "family": MIGRATION_FAMILY,
                "status": "needs_attention",
                "reason_code": "builtin_profile_required",
                "repair": "choose_model_profile",
                "source_sha256": source_sha,
            }

        def exact_profile(profile_id: str) -> dict[str, Any] | None:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                    (profile_id,),
                ).fetchone()
            revision = int(row["revision"] or 0) if row is not None else 0
            return None if revision < 1 else {"profile_id": profile_id, "profile_revision": revision}

        thought_profile, writing_profile = exact_profile(thoughts), exact_profile(writing)
        if thought_profile is None or writing_profile is None:
            return {
                "schema": "InferenceAssignmentMigrationIssue@1",
                "family": MIGRATION_FAMILY,
                "status": "needs_attention",
                "reason_code": "legacy_profile_requires_upgrade",
                "repair": "upgrade_model_profile",
                "source_sha256": source_sha,
            }
        profiles = {
            "thought.interview": thought_profile,
            "ask.answer": thought_profile,
            "speech.intent_classify": writing_profile,
            "speech.rewrite": writing_profile,
        }
        marker = assignments.migrate_capability_assignments_atomically(
            principal,
            family=MIGRATION_FAMILY,
            source_sha256=source_sha,
            capability_entries=profiles,
        )
        return {**marker, "status": "migrated", "legacy_config_read": True}


def migrate_startup(
    db: Any, principal: Principal, config_loader: Callable[[], Any], *,
    registry: InferenceCapabilityRegistry | None = None,
) -> dict[str, dict[str, Any]]:
    """The kernel startup's one call: every family, once."""
    return AssignmentMigration(db, registry=registry).migrate_startup_legacy_assignments(
        principal, config_loader
    )


__all__ = [
    "MIGRATION_FAMILY",
    "MEETING_MIGRATION_FAMILY",
    "MEETING_DEFERRED_MIGRATION_FAMILY",
    "SPEECH_RECOGNITION_MIGRATION_FAMILY",
    "RAILS_OBSERVER_MIGRATION_FAMILY",
    "RECIPE_WORKBENCH_MIGRATION_FAMILY",
    "AssignmentMigration",
    "migrate_startup",
]
