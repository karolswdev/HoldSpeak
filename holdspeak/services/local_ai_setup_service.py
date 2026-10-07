"""Set up local AI: one call gets every local model (owner ruling 2026-10-05).

One owner call downloads, sha-pinned, the three models a fresh install needs:

* the Whisper model for speech (``holdspeak/whisper_models.py``),
* the embedding model for meaning search (``memory/local_model.EMBED_MODEL``),
* the local starter model from the signed setup catalogue
  (``preset_local_qwen35_4b_gguf_q4km``).

The laws:

* **Runtime first.**  The call checks ``llama-cpp-python`` before any request
  leaves this device.  With no runtime, nothing downloads.
* **One egress receipt.**  All the files that are not on this device go in
  ONE ``external.egress`` operation.  Its payload names each file: url, size
  and sha256.
* **Pinned bytes only.**  A file is used only when its size and sha256 are the
  pinned ones.  A file with a different hash is deleted; nothing is adopted.
* **Resumable and idempotent.**  A stopped download continues its part file.
  A second call when every file is on this device downloads nothing.
* **No assignment of "Default for AI work".**  The starter model gets its
  artifact, deployment, profile and a ready binding: the records that show a
  usable local engine.  ``status()["local_engine"]["ready"]`` says so.  The
  rule that assigns it is another part of the product.
* **Only an explicit call starts it.**  Nothing here runs at boot.
"""
from __future__ import annotations

import json
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.request import urlopen

from ..deployment_revisions import DeploymentRevision
from ..inference_setup_catalog import packaged_catalog
from ..logging_config import get_logger
from ..memory.local_model import (
    EMBED_MODEL,
    ModelFetchCancelled,
    ModelFetchError,
    PinnedModel,
    check_destination,
    fetch,
    find_on_device,
    is_pinned_file,
    model_dir,
)
from ..principals import Principal, PrincipalKind
from .errors import ServiceError
from .tool_capability_service import sha256 as _sha

log = get_logger("local_ai_setup")

STARTER_PRESET_ID = "preset_local_qwen35_4b_gguf_q4km"
RUNTIME_ID = "llama_cpp_prompt_v1"
STARTER_PROFILE_ID = "local-ai-starter"
STARTER_BINDING_ID = "binding-" + STARTER_PROFILE_ID
SOURCE_HOST = "huggingface.co"
#: Free space kept after the download, so the disk does not fill completely.
DISK_MARGIN_BYTES = 512 * 1024 * 1024

#: code -> the plain words a face shows.  Short sentences; each one says
#: what to do.
_ERRORS = {
    "runtime": "llama-cpp-python 0.3.34 or newer is not installed. Install it. Then try again.",
    "disk": "There is not enough free disk space. Free some space. Then try again.",
    "network": "The download stopped. Try again to continue.",
    "integrity": "A file was not correct. HoldSpeak deleted it. Try again.",
    "refused": "The hub did not permit the download. Try again.",
    "unsafe": "The model folder holds a link. Remove the link. Then try again.",
    "setup": "The models are on this device, but setup did not finish. Try again.",
    "speech_not_covered": "Set up local AI cannot get the selected Whisper model. Select the base model, or add the model yourself.",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def starter_preset(catalog: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """The signed catalogue row of the local starter model."""
    entries = (catalog or packaged_catalog(now=datetime.now(timezone.utc)))["entries"]
    row = next((item for item in entries if item["id"] == STARTER_PRESET_ID), None)
    if row is None:
        raise ServiceError("local_ai_starter_missing", "The starter model is not in the catalogue.", context={"status": 409})
    return row


def starter_artifact_id(preset: dict[str, Any]) -> str:
    """The same artifact id a Models-library download of this preset gets."""
    return "artifact_" + str(preset["source"]["manifest_sha256"]).removeprefix("sha256:")


def starter_model(preset: dict[str, Any]) -> PinnedModel:
    source = preset["source"]
    return PinnedModel(
        name=str(source["filename"]).removesuffix(".gguf"),
        label=str(preset["label"]),
        repository=str(source["repository"]),
        revision=str(source["revision"]),
        filename=str(source["filename"]),
        sha256=str(source["file_sha256"]).removeprefix("sha256:"),
        size=int(source["download_bytes"]),
        license=str(source["license"]),
        architecture="gguf",
        context_ceiling=int(preset["context"]["recommended_tokens"]),
    )


def starter_model_path(home: Path, preset: Optional[dict[str, Any]] = None) -> Path:
    """Where the starter file is on this device: the Models-library place."""
    row = preset or starter_preset()
    return (
        home / ".local" / "share" / "holdspeak" / "models" / "artifacts"
        / starter_artifact_id(row) / str(row["source"]["filename"])
    )


def starter_claims() -> list[str]:
    """The honest capability claims of the starter on llama.cpp.

    * ``language``: a chat model (the same base claim the Models library
      gives a connected provider).
    * ``result_schema:<meeting intel schema>``: meeting analysis
      (``meeting.deferred_analysis`` and ``meeting.live_analysis``; one claim
      each since PHILO-15 08 gave the summary its decisions).
      The same-device engine (``inference_targets._local_pinned_engine`` ->
      ``MeetingIntel(provider="local")``) sends that schema to llama.cpp as a
      JSON-schema grammar, so the output is constrained to it.

    Not claimed, because no executor on this path enforces their schema:
    the meeting plugins (``meeting_plugin`` class + their own schemas),
    ``thought.interview``, ``chat.compact``/``chat.guardrail``,
    ``agent.plan``/``agent.tool_turn``, ``calendar.snapshot_extract`` (image)
    and the speech classifiers.  No profile in the product claims those today.
    """
    from ..inference_capabilities import meeting_analysis_claims

    # PHILO-15 08: the deferred summary and the live window now have two
    # result shapes; the one executor serves both.
    return ["language", *meeting_analysis_claims()]


def file_ref(model: PinnedModel) -> str:
    """The kernel ref that names one downloaded file on the egress receipt."""
    return f"model-file:{model.repository}/{model.filename}:sha256:{model.sha256}:{model.size}"


class LocalAISetupService:
    """Owner-only: download the local models, verify them, make them ready."""

    def __init__(
        self,
        db: Any,
        *,
        meaning_search: Any,
        profile_service: Any = None,
        broker_provider: Optional[Callable[[], Any]] = None,
        home_provider: Callable[[], Path] = Path.home,
        config_provider: Optional[Callable[[], Any]] = None,
        catalog_provider: Optional[Callable[[], dict[str, Any]]] = None,
        runtime_probe: Optional[Callable[[], dict[str, Any]]] = None,
        opener: Callable[..., Any] = urlopen,
        url_for: Optional[Callable[[PinnedModel], str]] = None,
        allowed_host: Optional[Callable[[str], bool]] = None,
    ) -> None:
        from .model_profile_service import ModelProfileService

        self._db = db
        self._meaning = meaning_search
        self._profiles = profile_service or ModelProfileService(db)
        self._broker_provider = broker_provider or self._default_broker
        self._home = home_provider
        self._config_provider = config_provider or self._default_config
        self._catalog_provider = catalog_provider or (lambda: packaged_catalog(now=datetime.now(timezone.utc)))
        self._runtime_probe = runtime_probe or self._installed_runtime
        self._opener = opener
        self._url_for = url_for or (lambda model: model.url)
        self._allowed_host = allowed_host
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._cancel = threading.Event()
        self._bytes = 0
        self._bytes_total = 0
        self._error = ""

    # ── seams ────────────────────────────────────────────────────────

    @staticmethod
    def _default_broker() -> Any:
        from ..kernel.runtime import _service

        return _service()

    @staticmethod
    def _default_config() -> Any:
        from ..config import Config

        return Config.load()

    @staticmethod
    def _installed_runtime() -> dict[str, Any]:
        # The ONE runtime rule (shared with the Meaning search press).
        from .inference_setup_service import local_llama_runtime

        return local_llama_runtime()

    @staticmethod
    def _require_owner(principal: Optional[Principal]) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("local_ai_owner_required", "Owner access is required.", context={"status": 403})

    # ── the plan ─────────────────────────────────────────────────────

    def _runtime(self) -> dict[str, Any]:
        return dict(self._runtime_probe())

    def _whisper(self) -> tuple[str, str]:
        from ..transcribe import resolve_backend_or_raw

        model = getattr(self._config_provider(), "model", None)
        name = str(getattr(model, "name", "") or "base")
        backend = resolve_backend_or_raw(str(getattr(model, "backend", "") or "auto"))
        return name, backend

    def _plan(self) -> list[dict[str, Any]]:
        """Every file this call is responsible for, with its place on disk."""
        from ..whisper_models import pinned_file_on_device, pinned_whisper, pinned_whisper_dir

        home = self._home()
        items: list[dict[str, Any]] = []
        name, backend = self._whisper()
        for model in pinned_whisper(name, backend):
            # Size + sha256 for every pinned file, the cache copy included: a
            # truncated or changed file is downloaded again inside the call.
            items.append({
                "key": "whisper", "model": model,
                "destination": pinned_whisper_dir(model.repository, home) / model.filename,
                "on_device": pinned_file_on_device(model, home=home),
            })
        embed = getattr(self._meaning, "_model", EMBED_MODEL)
        embed_path = find_on_device(embed, home)
        items.append({
            "key": "embed", "model": embed,
            "destination": embed_path or model_dir(home) / embed.filename,
            "on_device": embed_path is not None,
        })
        preset = starter_preset(self._catalog_provider())
        starter = starter_model(preset)
        starter_path = starter_model_path(home, preset)
        items.append({
            "key": "starter", "model": starter, "destination": starter_path,
            "on_device": is_pinned_file(starter, starter_path), "preset": preset,
        })
        return items

    def _speech(self, plan: list[dict[str, Any]]) -> dict[str, Any]:
        """Is the CONFIGURED Whisper model covered?  Never silently dropped."""
        from ..whisper_models import whisper_on_disk

        name, backend = self._whisper()
        pinned = [item for item in plan if item["key"] == "whisper"]
        if pinned:
            state = "on_device" if all(item["on_device"] for item in pinned) else "will_download"
        elif whisper_on_disk(name, backend, home=self._home()):
            state = "on_device_unpinned"  # the owner's own copy; no pin to check
        else:
            state = "not_covered"  # no pinned files for this model: setup cannot get it
        return {"model": name, "backend": backend, "state": state}

    def _file_row(self, item: dict[str, Any]) -> dict[str, Any]:
        model: PinnedModel = item["model"]
        return {
            "key": item["key"],
            "label": model.label,
            "filename": model.filename,
            "url": self._url_for(model),
            "size_bytes": model.size,
            "sha256": model.sha256,
            "on_device": bool(item["on_device"]),
        }

    # ── reads ────────────────────────────────────────────────────────

    def _downloading(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def local_engine(self) -> dict[str, Any]:
        """The "local engine ready" signal: a ready binding for the starter.

        Read from the binding head and its readiness observation, so it is
        true only after a profile probe said ``ready``.
        """
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT b.profile_id,b.profile_revision,b.deployment_head_id,b.enabled,o.state
                     FROM model_profile_binding_heads h
                     JOIN model_profile_binding_revisions b
                       ON b.binding_id=h.binding_id AND b.revision=h.revision
                     LEFT JOIN model_profile_readiness_observations o
                       ON o.observation_id=b.readiness_observation_id
                    WHERE h.binding_id=?""",
                (STARTER_BINDING_ID,),
            ).fetchone()
        if row is None:
            return {"ready": False, "profile_id": None, "profile_revision": None, "deployment_id": None}
        return {
            "ready": bool(row["enabled"]) and str(row["state"] or "") == "ready",
            "profile_id": str(row["profile_id"]),
            "profile_revision": int(row["profile_revision"]),
            "deployment_id": str(row["deployment_head_id"]),
        }

    def status(self, principal: Optional[Principal] = None) -> dict[str, Any]:
        self._require_owner(principal)
        runtime = self._runtime()
        plan = self._plan()
        files = [self._file_row(item) for item in plan]
        missing = [row for row in files if not row["on_device"]]
        engine = self.local_engine()
        speech = self._speech(plan)
        meaning = str((self._meaning.status(principal) or {}).get("state") or "off")
        error = self._error
        if self._downloading():
            state = "downloading"
        elif not runtime["ready"]:
            state = "needs_runtime"
        elif error:
            state = "failed"
        elif not missing and engine["ready"] and meaning in {"on", "indexing"}:
            # Ready means speech too: a model setup cannot get is not ready.
            if speech["state"] == "not_covered":
                state, error = "incomplete", "speech_not_covered"
            else:
                state = "ready"
        else:
            state = "not_started"
        total = self._bytes_total if state == "downloading" else sum(row["size_bytes"] for row in missing)
        return {
            "state": state,
            "runtime": runtime,
            "files": files,
            "bytes_total": total,
            "bytes_done": self._bytes if state == "downloading" else 0,
            "percent": min(99, int(self._bytes * 100 / total)) if state == "downloading" and total else (100 if state == "ready" else 0),
            # What the next call sends out of this device: nothing when every
            # file is here, one model-file request operation when not.
            "egress": (
                {"destination": SOURCE_HOST, "what": "model file request", "files": len(missing),
                 "bytes": sum(row["size_bytes"] for row in missing)}
                if missing and state != "downloading" else None
            ),
            "local_engine": engine,
            "speech": speech,
            "meaning_search": meaning,
            "error": _ERRORS.get(error, ""),
            "error_code": error,
        }

    # ── commands ─────────────────────────────────────────────────────

    def start(self, principal: Principal) -> dict[str, Any]:
        """The owner's call.  Check the runtime, then download, then set up."""
        self._require_owner(principal)
        with self._lock:
            if self._downloading():
                return self.status(principal)
            self._error = ""
            # Runtime FIRST: no request leaves this device without it.
            if not self._runtime()["ready"]:
                self._error = "runtime"
                raise ServiceError(
                    "local_ai_runtime_unavailable", _ERRORS["runtime"],
                    context={"status": 409, "runtime": self._runtime()},
                )
            plan = self._plan()
            missing = [item for item in plan if not item["on_device"]]
            if missing:
                need = sum(item["model"].size for item in missing)
                root = self._home()
                probe = next((path for path in (root / ".local" / "share", root) if path.exists()), root)
                if shutil.disk_usage(probe).free < need + DISK_MARGIN_BYTES:
                    self._error = "disk"
                    raise ServiceError("local_ai_disk", _ERRORS["disk"], context={"status": 409})
                self._cancel.clear()
                self._bytes = 0
                self._bytes_total = need
                self._thread = threading.Thread(
                    target=self._download_then_set_up, args=(principal, plan, missing),
                    name="local-ai-setup", daemon=True,
                )
                self._thread.start()
                return self.status(principal)
        # Every file is on this device: no download, only the setup records.
        self._set_up(principal, plan)
        return self.status(principal)

    def cancel(self, principal: Principal) -> dict[str, Any]:
        self._require_owner(principal)
        self._cancel.set()
        self.wait(10)
        return self.status(principal)

    def wait(self, timeout: float = 60.0) -> None:
        """Wait for a download in progress (tests)."""
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    # ── the download (one egress operation) ──────────────────────────

    def _fetch_all(self, missing: list[dict[str, Any]]) -> list[str]:
        done_before = 0
        written: list[str] = []
        for item in missing:
            model: PinnedModel = item["model"]
            destination: Path = item["destination"]
            check_destination(destination)

            def progress(done: int, base: int = done_before) -> None:
                self._bytes = base + done

            kwargs: dict[str, Any] = {
                "url": self._url_for(model), "opener": self._opener,
                "on_progress": progress, "cancelled": self._cancel.is_set,
            }
            if self._allowed_host is not None:
                kwargs["allowed_host"] = self._allowed_host
            try:
                fetch(model, destination, **kwargs)
            except ModelFetchError as exc:
                if exc.code == "integrity":
                    # Keep nothing that failed the pin.
                    invalid = destination.parent / (destination.name + ".invalid")
                    try:
                        invalid.unlink()
                    except FileNotFoundError:
                        pass
                raise
            written.append(str(destination))
            done_before += model.size
        return written

    def _download_then_set_up(
        self, principal: Principal, plan: list[dict[str, Any]], missing: list[dict[str, Any]],
    ) -> None:
        from ..kernel.external_egress import EgressOperationRefused, run_external_egress

        material = {
            "purpose": "set_up_local_ai",
            "files": [
                {"key": item["key"], "url": self._url_for(item["model"]), "filename": item["model"].filename,
                 "size": item["model"].size, "sha256": item["model"].sha256}
                for item in missing
            ],
        }
        try:
            for item in missing:  # before any request leaves
                check_destination(item["destination"])
            run_external_egress(
                connector_id="model-download",
                destination=SOURCE_HOST,
                data_classes=("model_file_request",),
                payload_material=material,
                sender=self._fetch_all,
                args=(missing,),
                allowed_destinations=(SOURCE_HOST,),
                principal=principal,
                broker=self._broker_provider(),
                # The receipt names every file: repository/file, sha256, size.
                # The payload digest binds each url as well.
                subject_refs=("setup:local-ai", *(file_ref(item["model"]) for item in missing)),
            )
        except ModelFetchCancelled:
            return
        except ModelFetchError as exc:
            self._error = exc.code if exc.code in _ERRORS else "network"
            return
        except EgressOperationRefused as exc:
            log.warning("local AI download refused: %s", exc.reason)
            self._error = "refused"
            return
        except Exception as exc:
            log.warning("local AI download failed: %s", exc)
            self._error = "network"
            return
        if self._cancel.is_set():
            return
        self._set_up(principal, plan)

    # ── setup records ────────────────────────────────────────────────

    def _set_up(self, principal: Principal, plan: list[dict[str, Any]]) -> None:
        try:
            starter = next(item for item in plan if item["key"] == "starter")
            if not self.local_engine()["ready"]:
                self._register_starter(principal, starter)
            # Meaning search adopts its file from this device: no download.
            meaning = self._meaning.turn_on(principal) or {}
            if meaning.get("error_code") == "runtime":
                self._error = "runtime"
            elif meaning.get("error_code") in {"setup", "unsafe", "integrity"}:
                self._error = "setup"
        except ServiceError as exc:
            log.warning("local AI setup failed: %s (%s)", exc.detail, exc.code)
            self._error = "runtime" if exc.code == "local_ai_runtime_unavailable" else "setup"
        except Exception as exc:
            log.warning("local AI setup failed: %s", exc)
            self._error = "setup"

    def _register_starter(self, principal: Principal, item: dict[str, Any]) -> None:
        model: PinnedModel = item["model"]
        preset = item["preset"]
        path: Path = item["destination"]
        runtime = self._runtime()
        runtime_revision = str(runtime.get("revision") or "")
        if not runtime.get("ready"):
            raise ServiceError("local_ai_runtime_unavailable", _ERRORS["runtime"])
        source = preset["source"]
        artifact_id = starter_artifact_id(preset)
        artifact_manifest = {"files": [{"path": model.filename, "sha256": source["file_sha256"], "size": model.size}]}
        claims = {"revision": "local-ai-starter-v2", "claims": starter_claims()}
        capability_manifest = {**claims, "sha256": _sha(claims)}
        revision = DeploymentRevision.from_artifact(
            destination_id="this_machine", engine="configured_local_engine",
            model=model.label, runtime_id=RUNTIME_ID, runtime_revision=runtime_revision,
            artifact_id=artifact_id, manifest_sha256=str(source["manifest_sha256"]), format="gguf",
            architecture="gguf", context_ceiling=model.context_ceiling,
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
                    artifact_id, "gguf", "huggingface_file", model.repository, model.revision,
                    _canonical(artifact_manifest), source["manifest_sha256"], model.size, str(path), now, now,
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
                    model.label, model.context_ceiling, model.context_ceiling,
                    _canonical({"format": "gguf", "context_ceiling": model.context_ceiling}),
                    str(capability_manifest["sha256"]), revision.id, now, now,
                ),
            )
            configuration_revision = int(conn.execute(
                "SELECT configuration_revision FROM inference_deployments WHERE deployment_id=?",
                (deployment_id,),
            ).fetchone()[0])
            conn.commit()
        profile_revision = self._ensure_profile(principal, artifact_id, capability_manifest, model)
        observation = self._profiles.probe_profile(
            principal,
            {
                "profile_id": STARTER_PROFILE_ID,
                "profile_revision": profile_revision,
                "deployment_head_id": deployment_id,
                "expected_deployment_configuration_revision": configuration_revision,
                "expected_deployment_revision_id": revision.id,
            },
        )
        if str(observation.get("state")) != "ready":
            raise ServiceError("local_ai_runtime_unavailable", _ERRORS["runtime"])
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM model_profile_binding_heads WHERE binding_id=?", (STARTER_BINDING_ID,)
            ).fetchone()
        self._profiles.bind_profile(
            principal,
            {
                "binding_id": STARTER_BINDING_ID,
                "profile_id": STARTER_PROFILE_ID,
                "profile_revision": profile_revision,
                "deployment_head_id": deployment_id,
                "expected_binding_revision": int(row["revision"]) if row is not None else 0,
                "expected_deployment_configuration_revision": configuration_revision,
                "expected_deployment_revision_id": revision.id,
                "enabled": True,
                "readiness_observation_id": observation["observation_id"],
            },
        )

    def _ensure_profile(
        self, principal: Principal, artifact_id: str, capability_manifest: dict[str, Any], model: PinnedModel,
    ) -> int:
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT revision,model_or_artifact_identity,capability_manifest_json
                     FROM model_profile_revisions WHERE profile_id=?
                    ORDER BY revision DESC LIMIT 1""",
                (STARTER_PROFILE_ID,),
            ).fetchone()
            deleted = conn.execute(
                "SELECT 1 FROM model_profile_tombstones WHERE profile_id=?", (STARTER_PROFILE_ID,)
            ).fetchone() is not None
        if deleted:
            raise ServiceError("local_ai_profile_deleted", "The owner deleted the starter model profile.", context={"status": 409})
        current = int(row["revision"]) if row is not None else 0
        if (
            row is not None
            and str(row["model_or_artifact_identity"]) == artifact_id
            and json.loads(str(row["capability_manifest_json"])).get("sha256") == capability_manifest["sha256"]
        ):
            return current
        self._profiles.create_profile(
            principal,
            {
                "profile_id": STARTER_PROFILE_ID,
                "expected_revision": current,
                "label": f"{model.label} (this device)",
                "provider_family": "local",
                "runtime_family": RUNTIME_ID,
                "model_or_artifact_identity": artifact_id,
                "supported_modalities": ["text", "language"],
                "context_support": "bounded",
                "tokenizer_template_requirements": {},
                "capability_manifest": capability_manifest,
                "safe_presentation": {"summary": "Local starter model. It runs on this device."},
            },
        )
        return current + 1


__all__ = [
    "LocalAISetupService",
    "file_ref",
    "STARTER_BINDING_ID",
    "STARTER_PRESET_ID",
    "STARTER_PROFILE_ID",
    "starter_artifact_id",
    "starter_model",
    "starter_model_path",
    "starter_preset",
]
