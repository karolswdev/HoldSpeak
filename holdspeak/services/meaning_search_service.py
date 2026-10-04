"""Meaning search: one step to turn it on (MEMORY-DESIGN.md §4).

``turn_on`` gets the embedding model (a copy on this device with the pinned
sha256, or a download after the owner's press), makes its model profile with
the ``embedding`` claim, assigns that profile to ``memory.embed`` and wakes
the memory conductor.  ``turn_off`` clears the assignment; keyword search
continues.

* **A download is egress.**  It starts only in ``turn_on`` and only when no
  copy with the pinned hash is on this device.  Each download request is one
  ``external.egress`` operation with a receipt, for the owner who pressed.
* **No signature claim.**  The pinned sha256 is the integrity check.  The
  signed packaged catalogue is not used and not changed.
* **The download state is in this process.**  The partial file stays on the
  disk, so the next press continues it.  After a hub restart the state is
  OFF; nothing downloads again without a press.
"""
from __future__ import annotations

import importlib.metadata
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.request import urlopen

from ..deployment_revisions import DeploymentRevision
from ..logging_config import get_logger
from ..memory.embedder import MEMORY_EMBED_DIM, model_id_for
from ..memory.engine import MEMORY_EMBED_CAPABILITY, assigned_revision
from ..memory.local_model import (
    EMBED_MODEL,
    ModelFetchCancelled,
    ModelFetchError,
    PinnedModel,
    fetch,
    find_on_device,
    check_destination,
    model_dir,
)
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, ServiceError
from .tool_capability_service import sha256 as _sha

log = get_logger("meaning_search")

EMBEDDING_CLAIM = "embedding"
RUNTIME_ID = "llama_cpp_prompt_v1"
PROFILE_ID = "meaning-search-embed"
_ASSIGNMENT_KEY = f"capability:{MEMORY_EMBED_CAPABILITY}"
_SCOPE = {"kind": "capability", "capability_id": MEMORY_EMBED_CAPABILITY}

_ERRORS = {
    "network": "The download stopped. Press Turn on to continue.",
    "integrity": "The downloaded file is not the correct file. Press Turn on to download it again.",
    "refused": "The download was not permitted.",
    "unsafe": "The model folder on this hub holds a link. Remove the link, then press Turn on.",
    "runtime": "The local model runtime (llama-cpp-python) is not installed on this hub.",
    "setup": "Meaning search did not start. Press Turn on to try again.",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class MeaningSearchService:
    def __init__(
        self,
        db: Any,
        *,
        assignment_service: Any,
        profile_service: Any = None,
        broker_provider: Optional[Callable[[], Any]] = None,
        model: PinnedModel = EMBED_MODEL,
        home_provider: Callable[[], Path] = Path.home,
        opener: Callable[..., Any] = urlopen,
        source_url: Optional[str] = None,
        allowed_host: Optional[Callable[[str], bool]] = None,
        wake: Optional[Callable[[], None]] = None,
    ) -> None:
        from .model_profile_service import ModelProfileService

        self._db = db
        self._assignments = assignment_service
        self._profiles = profile_service or ModelProfileService(db)
        self._broker_provider = broker_provider or self._default_broker
        self._model = model
        self._home = home_provider
        self._opener = opener
        self._source_url = source_url
        self._allowed_host = allowed_host
        self._wake = wake or self._default_wake
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._cancel = threading.Event()
        self._bytes = 0
        self._error = ""

    # ── seams ────────────────────────────────────────────────────────

    @staticmethod
    def _default_broker() -> Any:
        from ..kernel.runtime import _service

        return _service()

    @staticmethod
    def _default_wake() -> None:
        from .. import memory_conductor

        memory_conductor.wake()

    @staticmethod
    def _require_owner(principal: Optional[Principal]) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("meaning_search_owner_required", "Owner access is required.", context={"status": 403})

    # ── reads ────────────────────────────────────────────────────────

    def _head(self) -> tuple[int, bool]:
        """(revision, assigned) of the ``memory.embed`` assignment head."""
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT revision,cleared FROM inference_assignment_heads WHERE assignment_key=?",
                (_ASSIGNMENT_KEY,),
            ).fetchone()
        if row is None:
            return 0, False
        return int(row["revision"]), not bool(row["cleared"])

    def _downloading(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def status(self, principal: Optional[Principal] = None) -> dict[str, Any]:
        """OFF / DOWNLOADING n% / INDEXING n of m / ON, from the real stores."""
        model = self._model
        # The same verified decision the press uses (the hash is checked
        # once and kept by path, size and time): "on this device" is never
        # said for a file the press would not adopt.
        on_device = find_on_device(model, self._home()) is not None
        payload: dict[str, Any] = {
            "state": "off",
            "percent": 0,
            "bytes_done": 0,
            "bytes_total": model.size,
            "indexed": 0,
            "total": 0,
            "error": self._error,
            "model": {
                "label": model.label,
                "size_bytes": model.size,
                "on_device": on_device,
                "source": model.host,
                "boundary": "local",
            },
            # What the next Turn on press sends out of this device: nothing
            # when the file is here, one file request when it is not.
            "egress": None if on_device else {"destination": model.host, "what": "model file request"},
        }
        _revision, assigned = self._head()
        if assigned:
            done, total = self._index_progress()
            payload.update(
                # ON only when the conductor gave the engine to recall and
                # every chunk has its vector.
                state="on" if self._db.memory.embedder is not None and done >= total else "indexing",
                indexed=done, total=total, error=self._conductor_error(), egress=None,
            )
            return payload
        if self._downloading():
            payload.update(
                state="downloading",
                bytes_done=self._bytes,
                percent=min(99, int(self._bytes * 100 / model.size)) if model.size else 0,
                error="",
            )
        return payload

    def _index_progress(self) -> tuple[int, int]:
        model_name = ""
        try:
            revision = assigned_revision(self._broker_provider())
            model_name = str((revision or {}).get("model") or (revision or {}).get("revision_id") or "")
        except Exception as exc:  # a status read never fails on the route
            log.warning("meaning search status could not resolve the engine: %s", exc)
        total = int(self._db.memory_index.stats()["chunks"])
        if not model_name:
            return 0, total
        pending = self._db.memory_index.pending_count(model_id_for(model_name, MEMORY_EMBED_DIM))
        return total - pending, total

    @staticmethod
    def _conductor_error() -> str:
        from .. import memory_conductor

        report = memory_conductor.last_report()
        return "The index stopped. It continues automatically." if report.get("error") else ""

    # ── commands ─────────────────────────────────────────────────────

    def turn_on(self, principal: Principal) -> dict[str, Any]:
        self._require_owner(principal)
        with self._lock:
            _revision, assigned = self._head()
            if assigned or self._downloading():
                return self.status(principal)
            self._error = ""
            path = find_on_device(self._model, self._home())
            if path is not None:
                self._activate_safely(principal, path)
                return self.status(principal)
            self._cancel.clear()
            self._bytes = 0
            self._thread = threading.Thread(
                target=self._download_then_activate, args=(principal,),
                name="meaning-search-download", daemon=True,
            )
            self._thread.start()
        return self.status(principal)

    def turn_off(self, principal: Principal) -> dict[str, Any]:
        self._require_owner(principal)
        self._cancel.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(10)
        with self._lock:
            self._error = ""
            revision, assigned = self._head()
            if assigned:
                self._assignments.clear_assignment(
                    principal,
                    {
                        "command_id": f"meaning-search-off-{uuid.uuid4().hex}",
                        "expected_revision": revision,
                        "scope": dict(_SCOPE),
                        "capability_id": MEMORY_EMBED_CAPABILITY,
                    },
                )
        self._wake()
        return self.status(principal)

    def wait(self, timeout: float = 60.0) -> None:
        """Wait for a download in progress (tests)."""
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    # ── the download (egress) ────────────────────────────────────────

    def _download_then_activate(self, principal: Principal) -> None:
        from ..kernel.external_egress import EgressOperationRefused, run_external_egress

        model = self._model
        destination = model_dir(self._home()) / model.filename
        url = self._source_url or model.url

        def progress(done: int) -> None:
            self._bytes = done

        kwargs: dict[str, Any] = {
            "url": url, "opener": self._opener,
            "on_progress": progress, "cancelled": self._cancel.is_set,
        }
        if self._allowed_host is not None:
            kwargs["allowed_host"] = self._allowed_host
        try:
            check_destination(destination)  # before any request leaves
            path = run_external_egress(
                connector_id="model-download",
                destination=model.host,
                data_classes=("model_file_request",),
                payload_material={"url": url, "sha256": model.sha256},
                sender=fetch,
                args=(model, destination),
                kwargs=kwargs,
                allowed_destinations=(model.host,),
                principal=principal,
                broker=self._broker_provider(),
                subject_refs=(f"capability:{MEMORY_EMBED_CAPABILITY}",),
            )
        except ModelFetchCancelled:
            return
        except ModelFetchError as exc:
            self._error = _ERRORS.get(exc.code, _ERRORS["network"])
            return
        except EgressOperationRefused as exc:
            log.warning("meaning search download refused: %s", exc.reason)
            self._error = _ERRORS["refused"]
            return
        except Exception as exc:
            log.warning("meaning search download failed: %s", exc)
            self._error = _ERRORS["network"]
            return
        if self._cancel.is_set():
            return
        with self._lock:
            self._activate_safely(principal, path)

    # ── profile, binding, assignment ─────────────────────────────────

    def _activate_safely(self, principal: Principal, path: Path) -> None:
        try:
            self._activate(principal, path)
        except ServiceError as exc:
            log.warning("meaning search setup failed: %s (%s)", exc.detail, exc.code)
            self._error = _ERRORS["runtime" if exc.code == "meaning_search_runtime_unavailable" else "setup"]
            return
        except Exception as exc:
            log.warning("meaning search setup failed: %s", exc)
            self._error = _ERRORS["setup"]
            return
        self._wake()

    def _activate(self, principal: Principal, path: Path) -> None:
        model = self._model
        try:
            runtime_revision = importlib.metadata.version("llama-cpp-python")
        except importlib.metadata.PackageNotFoundError as exc:
            raise ServiceError("meaning_search_runtime_unavailable", _ERRORS["runtime"]) from exc
        file_sha = "sha256:" + model.sha256
        artifact_manifest = {"files": [{"path": model.filename, "sha256": file_sha, "size": model.size}]}
        manifest_sha = _sha(artifact_manifest)
        artifact_id = "artifact_" + manifest_sha.removeprefix("sha256:")
        claims = {"revision": "memory-embed-v1", "claims": [EMBEDDING_CLAIM]}
        capability_manifest = {**claims, "sha256": _sha(claims)}
        revision = DeploymentRevision.from_artifact(
            destination_id="this_machine", engine="configured_local_engine",
            model=model.name, runtime_id=RUNTIME_ID, runtime_revision=runtime_revision,
            artifact_id=artifact_id, manifest_sha256=manifest_sha, format="gguf",
            architecture=model.architecture, context_ceiling=model.context_ceiling,
            capability_sha256=str(capability_manifest["sha256"]),
        )
        deployment_id = "deployment_" + artifact_id.removeprefix("artifact_")[:24]
        self._db.deployment_revisions.upsert(revision)
        now = _now()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """INSERT INTO inference_model_artifacts
                   (artifact_id,format,source_kind,source_repository,source_revision,
                    manifest_json,manifest_sha256,installed_bytes,state,local_locator,
                    created_at,verified_at)
                   VALUES (?,?,?,?,?,?,?,?,'verified',?,?,?)
                   ON CONFLICT(artifact_id) DO UPDATE SET
                    state='verified',local_locator=excluded.local_locator,
                    verified_at=excluded.verified_at""",
                (
                    artifact_id, "gguf", "pinned_local_file", model.repository, model.revision,
                    _canonical(artifact_manifest), manifest_sha, model.size, str(path), now, now,
                ),
            )
            conn.execute(
                """INSERT INTO inference_deployments
                   (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,
                    model_identity,context_ceiling,recommended_context,capability_json,
                    capability_sha256,execution_revision_id,configuration_revision,active,
                    created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,1,0,?,?)
                   ON CONFLICT(deployment_id) DO UPDATE SET
                    configuration_revision=configuration_revision
                      + (execution_revision_id<>excluded.execution_revision_id),
                    runtime_revision=excluded.runtime_revision,
                    capability_json=excluded.capability_json,
                    capability_sha256=excluded.capability_sha256,
                    execution_revision_id=excluded.execution_revision_id,
                    updated_at=excluded.updated_at""",
                (
                    deployment_id, "this_machine", RUNTIME_ID, runtime_revision, artifact_id,
                    model.name, model.context_ceiling, model.context_ceiling,
                    _canonical({EMBEDDING_CLAIM: True, "format": "gguf", "context_ceiling": model.context_ceiling}),
                    str(capability_manifest["sha256"]), revision.id, now, now,
                ),
            )
            configuration_revision = int(conn.execute(
                "SELECT configuration_revision FROM inference_deployments WHERE deployment_id=?",
                (deployment_id,),
            ).fetchone()[0])
            conn.commit()
        profile_id, profile_revision = self._ensure_profile(principal, artifact_id, capability_manifest)
        observation = self._profiles.probe_profile(
            principal,
            {
                "profile_id": profile_id,
                "profile_revision": profile_revision,
                "deployment_head_id": deployment_id,
                "expected_deployment_configuration_revision": configuration_revision,
                "expected_deployment_revision_id": revision.id,
            },
        )
        if str(observation.get("state")) != "ready":
            raise ServiceError("meaning_search_runtime_unavailable", _ERRORS["runtime"])
        binding_id = f"binding-{profile_id}"
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM model_profile_binding_heads WHERE binding_id=?", (binding_id,)
            ).fetchone()
        self._profiles.bind_profile(
            principal,
            {
                "binding_id": binding_id,
                "profile_id": profile_id,
                "profile_revision": profile_revision,
                "deployment_head_id": deployment_id,
                "expected_binding_revision": int(row["revision"]) if row is not None else 0,
                "expected_deployment_configuration_revision": configuration_revision,
                "expected_deployment_revision_id": revision.id,
                "enabled": True,
                "readiness_observation_id": observation["observation_id"],
            },
        )
        head_revision, assigned = self._head()
        if not assigned:
            self._assignments.set_assignment(
                principal,
                {
                    "command_id": f"meaning-search-on-{uuid.uuid4().hex}",
                    "expected_revision": head_revision,
                    "scope": dict(_SCOPE),
                    "entries": [{"profile_id": profile_id, "profile_revision": profile_revision}],
                },
            )

    def _ensure_profile(
        self, principal: Principal, artifact_id: str, capability_manifest: dict[str, Any]
    ) -> tuple[str, int]:
        """The embedding profile for this artifact: (profile_id, revision)."""
        for suffix in ("", "-2", "-3", "-4"):
            profile_id = PROFILE_ID + suffix
            with self._db._connection() as conn:
                row = conn.execute(
                    """SELECT revision,model_or_artifact_identity,capability_manifest_json
                         FROM model_profile_revisions WHERE profile_id=?
                        ORDER BY revision DESC LIMIT 1""",
                    (profile_id,),
                ).fetchone()
                deleted = conn.execute(
                    "SELECT 1 FROM model_profile_tombstones WHERE profile_id=?", (profile_id,)
                ).fetchone() is not None
            if deleted:
                continue  # the owner deleted that profile; it is not made again
            current = int(row["revision"]) if row is not None else 0
            if (
                row is not None
                and str(row["model_or_artifact_identity"]) == artifact_id
                and json.loads(str(row["capability_manifest_json"])).get("sha256") == capability_manifest["sha256"]
            ):
                return profile_id, current
            self._profiles.create_profile(
                principal,
                {
                    "profile_id": profile_id,
                    "expected_revision": current,
                    "label": f"Meaning search ({self._model.label})",
                    "provider_family": "local",
                    "runtime_family": RUNTIME_ID,
                    "model_or_artifact_identity": artifact_id,
                    "supported_modalities": ["text"],
                    "context_support": "bounded",
                    "tokenizer_template_requirements": {},
                    "capability_manifest": capability_manifest,
                    "safe_presentation": {"summary": "Local embedding model. Used only for meaning search."},
                },
            )
            return profile_id, current + 1
        raise ConflictError("The meaning search profile was deleted.", code="meaning_search_profile_deleted")


__all__ = ["EMBEDDING_CLAIM", "MeaningSearchService", "PROFILE_ID"]
