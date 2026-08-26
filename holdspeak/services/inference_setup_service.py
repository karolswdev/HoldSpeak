"""Read-only Capability Truth application projection (HS-142-01)."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..config import Config
from ..deployment_revisions import DeploymentRevision
from ..inference_setup_catalog import (
    applicable_presets,
    packaged_catalog_envelope_json,
    verify_catalog_envelope,
)
from ..inference_targets import InferenceTarget, THIS_MACHINE_ID, resolve_inference_target, this_machine_target_from_model_path
from ..principals import Principal, PrincipalKind
from .errors import ServiceError


SCHEMA_VERSION = 1
_MAX_DETECTED = 200
_MAX_SCAN_DIRECTORIES = 1_000
_MAX_DIRECTORY_ENTRIES = 4_000
_MAX_MLX_CONFIG_BYTES = 64 * 1024
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_ENV_LIKE = re.compile(r"(?:\$\{|\$HOME|(?:API_?KEY|TOKEN|SECRET)\s*=)", re.IGNORECASE)


def _canonical_sha(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _public_text(value: Any, fallback: str, *, limit: int = 200) -> str:
    """Bound a user/config-derived label without ever projecting a local path."""
    text = str(value or "").strip()
    if (
        not text
        or len(text) > limit
        or any(ord(char) < 32 for char in text)
        or Path(text).is_absolute()
        or text.startswith("~")
        or _WINDOWS_ABSOLUTE.match(text)
        or _ENV_LIKE.search(text)
    ):
        return fallback
    return text


def load_config_read_only(path: Path | None = None) -> Config:
    """Load Config without creation, legacy migration, or persistence."""
    if path is None:
        from .. import config as config_facade

        path = config_facade.CONFIG_FILE
    return Config.load(path=path) if path.exists() else Config()


def _memory_total() -> int | None:
    try:
        pages = int(os.sysconf("SC_PHYS_PAGES"))
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        return pages * page_size if pages > 0 and page_size > 0 else None
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def _memory_available() -> int | None:
    try:
        pages = int(os.sysconf("SC_AVPHYS_PAGES"))
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        return pages * page_size if pages >= 0 and page_size > 0 else None
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def inspect_hardware(*, home: Path, now: datetime) -> dict[str, Any]:
    system = platform.system().lower() or "unknown"
    architecture = platform.machine().lower() or "unknown"
    apple_silicon = system == "darwin" and architecture in {"arm64", "aarch64"}
    total = _memory_total()
    capability = {
        "system": system,
        "architecture": architecture,
        "apple_silicon": apple_silicon,
        "total_memory_bytes": total,
        "logical_cpu_count": os.cpu_count(),
        "unified_memory": True if apple_silicon else None,
        "accelerators": ["metal"] if apple_silicon else [],
    }
    capability["sha256"] = _canonical_sha(capability)
    try:
        storage = int(shutil.disk_usage(home if home.exists() else home.parent).free)
    except (OSError, ValueError):
        storage = None
    observation = {
        "available_memory_bytes": _memory_available(),
        "storage_available_bytes": storage,
    }
    observation["sha256"] = _canonical_sha(observation)
    missing = total is None or architecture == "unknown" or system == "unknown"
    return {
        "capability": capability,
        "observation": observation,
        "detection": {
            "state": "partial" if missing else "available",
            "reason": "Some hardware facts are unavailable on this platform." if missing else None,
        },
    }


def _package_available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _package_revision(distribution: str, fallback: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return fallback


def _version_at_least(observed: str, minimum: str) -> bool:
    try:
        return tuple(int(part) for part in observed.split(".")[:3]) >= tuple(
            int(part) for part in minimum.split(".")[:3]
        )
    except (TypeError, ValueError):
        return False


def inspect_runtimes(*, apple_silicon: bool) -> list[dict[str, Any]]:
    llama_revision = _package_revision("llama-cpp-python", "unavailable")
    llama = _package_available("llama_cpp") and _version_at_least(llama_revision, "0.3.34")
    mlx = apple_silicon and _package_available("mlx_lm")
    return [
        {
            "id": "llama_cpp_prompt_v1",
            "revision": llama_revision,
            "formats": ["gguf"],
            "availability": {"state": "available" if llama else "unavailable", "reason": None if llama else "Thoughts require llama-cpp-python 0.3.34 or newer for Qwen 3.5."},
            "thought_support": {"state": "supported" if llama else "unavailable", "reason": "Current GGUF Thought execution." if llama else "Install a Qwen 3.5-capable llama.cpp runtime."},
        },
        {
            "id": "mlx_text_v1",
            "revision": _package_revision("mlx-lm", "unavailable"),
            "formats": ["mlx_safetensors"],
            "availability": {"state": "available" if mlx else "unavailable", "reason": None if mlx else ("MLX text support requires Apple Silicon and mlx-lm." if not apple_silicon else "mlx-lm is not installed.")},
            "thought_support": {"state": "unsupported", "reason": "Detected MLX models are not executable by Thoughts yet."},
        },
        {
            "id": "openai_compatible_v1",
            "revision": "holdspeak-openai-compatible-v1",
            "formats": [],
            "availability": {"state": "available", "reason": None},
            "thought_support": {"state": "supported", "reason": "Configured endpoints use the current v1 adapter."},
        },
    ]


def _this_machine_from_config(config: Config) -> InferenceTarget:
    from ..intel.providers import configured_local_meeting_model_path

    return this_machine_target_from_model_path(
        configured_local_meeting_model_path(meeting=config.meeting)
    )


def _thought_target(db: Any, config: Config) -> tuple[str, str | None, InferenceTarget]:
    pointer = str(config.thoughts.inference_target_id or "").strip() or None
    if pointer in {None, THIS_MACHINE_ID}:
        return ("global" if pointer is None else "config", pointer, _this_machine_from_config(config))
    return "config", pointer, resolve_inference_target(db, pointer)


def _safe_reason(target: InferenceTarget) -> str | None:
    if target.ready:
        return None
    if target.id == THIS_MACHINE_ID:
        return "Configured Thought model is missing."
    if target.readiness_state == "needs_key":
        return f"{_public_text(target.name, 'This AI')} needs its saved key."
    if target.readiness_state == "unavailable":
        return f"{_public_text(target.name, 'This AI')} is unavailable on this hub."
    return f"{_public_text(target.name, 'This AI')} is {_public_text(target.readiness_state, 'unavailable').replace('_', ' ')}."


def _safe_target(target: InferenceTarget) -> dict[str, Any]:
    return {
        "id": _public_text(target.id, "unavailable"),
        "name": _public_text(target.name, "This AI"),
        "kind": target.kind,
        "boundary": target.boundary,
        "engine": _public_text(target.engine, "unavailable"),
        "model": _public_text(target.model, "unavailable"),
        "context_limit": target.context_limit,
    }


def _safe_revision(target: InferenceTarget, db: Any = None) -> dict[str, Any]:
    if target.deployment is None:
        return {
            "schema_version": 1, "id": None, "destination_id": _public_text(target.id, "unavailable"),
            "kind": target.kind, "engine": _public_text(target.engine, "unavailable"), "model": _public_text(target.model, "unavailable"),
            "boundary": target.boundary, "has_local_artifact": False, "requires_secret": False,
        }
    revision = None
    if db is not None:
        from ..deployment_revisions import _artifact_revision_for_identity

        revision = _artifact_revision_for_identity(db, target.deployment)
    revision = revision or DeploymentRevision.from_identity(target.deployment)
    return {
        "schema_version": revision.schema_version,
        "id": revision.id,
        "destination_id": _public_text(revision.destination_id, "unavailable"),
        "kind": revision.kind,
        "engine": _public_text(revision.engine, "unavailable"),
        "model": _public_text(revision.model, "unavailable"),
        "boundary": revision.boundary,
        "has_local_artifact": bool(revision.model_path),
        "requires_secret": bool(revision.secret_slot),
        "artifact_id": revision.artifact_id or None,
        "runtime_id": revision.runtime_id or None,
        "context_ceiling": revision.context_ceiling or target.context_limit,
    }


def _installed_artifacts(db: Any) -> list[dict[str, Any]]:
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT artifact_id,format,source_repository,source_revision,
                      installed_bytes,state,verified_at
                 FROM inference_model_artifacts
                WHERE state='verified'
                  AND source_kind NOT IN ('legacy-rails-observer', 'model_library_provider_material')
                ORDER BY verified_at DESC LIMIT 100"""
        ).fetchall()
    return [
        {
            "id": str(row["artifact_id"]), "format": str(row["format"]),
            "source_repository": str(row["source_repository"]),
            "source_revision": str(row["source_revision"]),
            "installed_bytes": int(row["installed_bytes"]),
            "state": str(row["state"]), "verified_at": str(row["verified_at"]),
        }
        for row in rows
    ]


def _acquisitions(db: Any) -> list[dict[str, Any]]:
    from .inference_acquisition_service import InferenceAcquisitionApplicationService

    with db._connection() as conn:
        rows = conn.execute(
            """SELECT * FROM inference_model_acquisitions
                ORDER BY created_at DESC LIMIT 20"""
        ).fetchall()
    return [InferenceAcquisitionApplicationService._public(row) for row in rows]


def _valid_gguf(path: Path) -> bool:
    try:
        if path.is_symlink() or not path.is_file():
            return False
        with path.open("rb") as handle:
            return handle.read(4) == b"GGUF"
    except OSError:
        return False


def _valid_mlx(path: Path) -> bool:
    try:
        config_path = path / "config.json"
        if path.is_symlink() or not config_path.is_file() or config_path.is_symlink():
            return False
        if config_path.stat().st_size > _MAX_MLX_CONFIG_BYTES:
            return False
        config = json.loads(config_path.read_bytes().decode("utf-8"))
        if not isinstance(config, dict):
            return False
        weights = False
        with os.scandir(path) as iterator:
            for ordinal, child in enumerate(iterator):
                if ordinal >= _MAX_DIRECTORY_ENTRIES:
                    break
                if child.name.endswith(".safetensors") and child.is_file(follow_symlinks=False):
                    weights = True
                    break
        index = path / "model.safetensors.index.json"
        return weights or (index.is_file() and not index.is_symlink())
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False


def _artifact_size(path: Path) -> int:
    try:
        if path.is_file():
            return int(path.stat().st_size)
        total = 0
        with os.scandir(path) as iterator:
            for ordinal, child in enumerate(iterator):
                if ordinal >= _MAX_DIRECTORY_ENTRIES:
                    break
                if child.is_file(follow_symlinks=False):
                    total += int(child.stat(follow_symlinks=False).st_size)
        return total
    except OSError:
        return 0


def _detected_artifact_id(format_id: str, path: Path, _ordinal: int) -> str:
    """Return a public, path-independent scan identity (never a locator).

    The ordinal is deliberately ignored: adding another model must not make an
    already-rendered choice resolve to a different file.  A bounded content
    prefix makes the ID independent of the owner's home path and filesystem
    timestamps; activation still performs full content verification before
    registering anything executable.
    """
    try:
        size = _artifact_size(path)
        if path.is_file():
            with path.open("rb") as handle:
                prefix = handle.read(_MAX_MLX_CONFIG_BYTES)
        else:
            config = path / "config.json"
            with config.open("rb") as handle:
                prefix = handle.read(_MAX_MLX_CONFIG_BYTES)
        scan_facts = str(size).encode("ascii") + b"\0" + prefix
    except OSError:
        scan_facts = b"unavailable"
    digest = hashlib.sha256()
    digest.update((format_id + "\0" + path.name + "\0").encode("utf-8"))
    digest.update(scan_facts)
    return "detected_" + digest.hexdigest()[:20]


def _scan_local_artifact_candidates(
    *, home: Path, current_target: InferenceTarget,
) -> tuple[list[tuple[str, Path]], dict[str, Any]]:
    """Boundedly inspect local model roots while retaining locators in-process."""
    configured_raw = str(getattr(current_target.deployment, "model_path", "") or "").strip()
    configured = Path(configured_raw).expanduser() if configured_raw else None
    found: list[tuple[str, Path]] = []
    gguf_root = home / "Models" / "gguf"
    mlx_root = home / "Models" / "mlx"
    scanned = 0
    failures = 0
    traversal_capped = False
    if configured is not None and _valid_gguf(configured):
        found.append(("gguf", configured))
    try:
        if gguf_root.is_dir():
            visited = 0
            stack = [gguf_root]
            while stack and len(found) <= _MAX_DETECTED:
                directory = stack.pop()
                visited += 1
                if visited > _MAX_SCAN_DIRECTORIES:
                    traversal_capped = True
                    break
                with os.scandir(directory) as iterator:
                    for ordinal, entry in enumerate(iterator):
                        if ordinal >= _MAX_DIRECTORY_ENTRIES:
                            traversal_capped = True
                            break
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        elif entry.name.lower().endswith(".gguf"):
                            path = Path(entry.path)
                            if configured is not None and path.absolute() == configured.absolute():
                                continue
                            if _valid_gguf(path):
                                found.append(("gguf", path))
                            if len(found) > _MAX_DETECTED:
                                traversal_capped = True
                                break
        scanned += 1
    except OSError:
        failures += 1
    try:
        if mlx_root.is_dir():
            with os.scandir(mlx_root) as iterator:
                for ordinal, entry in enumerate(iterator):
                    if ordinal >= _MAX_DIRECTORY_ENTRIES:
                        traversal_capped = True
                        break
                    path = Path(entry.path)
                    if entry.is_dir(follow_symlinks=False) and _valid_mlx(path):
                        found.append(("mlx_safetensors", path))
                    if len(found) > _MAX_DETECTED:
                        traversal_capped = True
                        break
        scanned += 1
    except OSError:
        failures += 1
    unique: dict[str, tuple[str, Path]] = {}
    for format_id, path in found:
        key = str(path.absolute())
        unique[key] = (format_id, path)
    configured_row = unique.pop(str(configured.absolute()), None) if configured is not None else None
    ordered = ([configured_row] if configured_row is not None else []) + sorted(
        unique.values(), key=lambda item: (item[1].name.casefold(), str(item[1]))
    )
    ordered = ordered[0:_MAX_DETECTED]
    capped = len(unique) > _MAX_DETECTED or traversal_capped
    if scanned == 0:
        detection = {"state": "unavailable", "reason": "Local model folders could not be inspected."}
    elif failures or capped:
        detection = {"state": "partial", "reason": "Some local model facts could not be inspected." if failures else f"Only the first {_MAX_DETECTED} local models are shown."}
    else:
        detection = {"state": "complete", "reason": None}
    return ordered, detection


def inspect_local_artifacts(
    *,
    home: Path,
    current_target: InferenceTarget,
    gguf_executable: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered, detection = _scan_local_artifact_candidates(
        home=home, current_target=current_target,
    )
    configured_raw = str(getattr(current_target.deployment, "model_path", "") or "").strip()
    configured = Path(configured_raw).expanduser() if configured_raw else None
    rows: list[dict[str, Any]] = []
    for ordinal, (format_id, path) in enumerate(ordered[0:_MAX_DETECTED]):
        is_configured = configured is not None and path.absolute() == configured.absolute()
        if format_id == "mlx_safetensors":
            support = {"state": "unsupported", "reason": "MLX is not executable by Thoughts yet."}
            activation = {
                "state": "unsupported", "action": "none", "context_tokens": None,
                "reason": "MLX Thought execution is not installed yet.",
            }
        elif is_configured and current_target.ready:
            support = {"state": "current_v1", "reason": "This is the configured v1 Thought model."}
            activation = {
                "state": "current", "action": "none",
                "context_tokens": min(max(int(current_target.context_limit or 8192), 1), 32768),
                "reason": "Thoughts already use this model.",
            }
        elif gguf_executable:
            support = {"state": "candidate", "reason": "Detected locally and ready to verify for Thoughts."}
            activation = {
                "state": "available", "action": "use_existing", "context_tokens": 8192,
                "reason": "HoldSpeak will verify this file before using it.",
            }
        else:
            support = {"state": "candidate", "reason": "Detected locally, but llama.cpp support is unavailable."}
            activation = {
                "state": "unavailable", "action": "none", "context_tokens": None,
                "reason": "Install llama.cpp support before using this GGUF.",
            }
        rows.append({
            "id": _detected_artifact_id(format_id, path, ordinal),
            "label": _public_text(path.name, "Local model"),
            "format": format_id,
            "size_bytes": _artifact_size(path),
            "configured_for_thoughts": is_configured,
            "thought_support": support,
            "activation": activation,
        })
    return rows, detection


def resolve_detected_local_artifact(
    *, home: Path, current_target: InferenceTarget, artifact_id: str,
) -> dict[str, Any] | None:
    """Resolve one projected scan id to a private locator after fresh inspection."""
    ordered, _detection = _scan_local_artifact_candidates(
        home=home, current_target=current_target,
    )
    for ordinal, (format_id, path) in enumerate(ordered):
        if _detected_artifact_id(format_id, path, ordinal) != artifact_id:
            continue
        try:
            return {
                "id": artifact_id,
                "format": format_id,
                "label": _public_text(path.name, "Local model"),
                "path": path,
                "size_bytes": _artifact_size(path),
            }
        except OSError:
            return None
    return None


def _execution_support(
    target: InferenceTarget, artifacts: list[dict[str, Any]], runtimes: list[dict[str, Any]]
) -> dict[str, Any]:
    if not target.ready:
        return {"state": "unavailable", "executable": False, "reason": _safe_reason(target)}
    deployment = target.deployment
    if target.kind == "paired_device":
        return {
            "state": "unsupported", "executable": False,
            "reason": "Paired-device Thought execution is not available on this hub.",
        }
    is_local_artifact = target.boundary == "same_device" or bool(
        getattr(deployment, "model_path", None)
    )
    if not is_local_artifact:
        if target.kind in {"external_service", "private_endpoint", "mesh_node"}:
            return {"state": "executable", "executable": True, "reason": None}
        return {
            "state": "unsupported", "executable": False,
            "reason": "This deployment kind is not executable by Thoughts.",
        }
    llama_ready = any(
        row["id"] == "llama_cpp_prompt_v1"
        and row["availability"]["state"] == "available"
        and row["thought_support"]["state"] == "supported"
        for row in runtimes
    )
    model_path = Path(str(getattr(deployment, "model_path", "") or "")).expanduser()
    configured_valid = _valid_gguf(model_path)
    if not configured_valid:
        return {
            "state": "unavailable",
            "executable": False,
            "reason": "Configured local model is not a valid GGUF artifact.",
        }
    if not llama_ready:
        return {
            "state": "unsupported",
            "executable": False,
            "reason": "Thoughts cannot load GGUF without llama.cpp support.",
        }
    return {"state": "executable", "executable": True, "reason": None}


class InferenceSetupApplicationService:
    """One transport-neutral, owner-only, read-only setup projection."""

    def __init__(
        self,
        db: Any,
        *,
        config_provider: Callable[[], Config] = load_config_read_only,
        home_provider: Callable[[], Path] = Path.home,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._db = db
        self._config_provider = config_provider
        self._home_provider = home_provider
        self._clock = clock
        self._catalog_envelope_json = packaged_catalog_envelope_json()
        verify_catalog_envelope(self._catalog_envelope_json, now=clock())

    @staticmethod
    def _require_owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("inference_setup_owner_required", "Owner access is required.", context={"status": 403})

    def get_model_library_facts(self, principal: Principal) -> dict[str, Any]:
        """Return availability facts for the Model Library without reading routes.

        The older setup projection includes a legacy current-route diagnostic.
        Model Library is deliberately a separate job: it receives catalog,
        runtime, detected, installed, and acquisition facts only and never
        observes an assignment pointer to decide what a model should do.
        """
        self._require_owner(principal)
        now = self._clock()
        catalog = verify_catalog_envelope(self._catalog_envelope_json, now=now)
        config = self._config_provider()
        home = self._home_provider()
        hardware = inspect_hardware(home=home, now=now)
        runtimes = inspect_runtimes(apple_silicon=hardware["capability"]["apple_silicon"])
        target = _this_machine_from_config(config)
        llama_ready = any(
            row["id"] == "llama_cpp_prompt_v1"
            and row["availability"]["state"] == "available"
            and row["thought_support"]["state"] == "supported"
            for row in runtimes
        )
        artifacts, artifact_detection = inspect_local_artifacts(
            home=home, current_target=target, gguf_executable=llama_ready,
        )
        runtime_ids = {row["id"] for row in runtimes if row["availability"]["state"] == "available"}
        platform_id = f'{hardware["capability"]["system"]}_{hardware["capability"]["architecture"]}'
        return {
            "schema_version": SCHEMA_VERSION,
            "runtimes": runtimes,
            "artifact_detection": artifact_detection,
            "detected_local_artifacts": artifacts,
            "installed_model_artifacts": _installed_artifacts(self._db),
            "acquisitions": _acquisitions(self._db),
            "preset_catalog": {key: catalog[key] for key in ("schema_version", "catalog_revision", "generated_at", "expires_at", "signing_key_id", "sha256")},
            "presets": applicable_presets(platform_id=platform_id, runtime_ids=runtime_ids, entries=catalog["entries"]),
        }

    def get_inference_setup(self, principal: Principal) -> dict[str, Any]:
        self._require_owner(principal)
        from .inference_acquisition_service import InferenceAcquisitionApplicationService

        now = self._clock()
        catalog = verify_catalog_envelope(self._catalog_envelope_json, now=now)
        config = self._config_provider()
        home = self._home_provider()
        hardware = inspect_hardware(home=home, now=now)
        runtimes = inspect_runtimes(apple_silicon=hardware["capability"]["apple_silicon"])
        source, configured_target_id, target = _thought_target(self._db, config)
        llama_ready = any(
            row["id"] == "llama_cpp_prompt_v1"
            and row["availability"]["state"] == "available"
            and row["thought_support"]["state"] == "supported"
            for row in runtimes
        )
        artifacts, artifact_detection = inspect_local_artifacts(
            home=home, current_target=target, gguf_executable=llama_ready,
        )
        execution_support = _execution_support(target, artifacts, runtimes)
        runtime_ids = {row["id"] for row in runtimes if row["availability"]["state"] == "available"}
        platform_id = f'{hardware["capability"]["system"]}_{hardware["capability"]["architecture"]}'
        limitations: list[dict[str, Any]] = []
        if not target.ready:
            limitations.append({"code": "current_thought_deployment_unavailable", "title": "Current AI is unavailable", "detail": _safe_reason(target), "repair": {"action": "open_models", "label": "Choose AI"}})
        if any(row["format"] == "mlx_safetensors" for row in artifacts):
            limitations.append({"code": "mlx_thought_execution_unsupported", "title": "MLX is not available for Thoughts yet", "detail": "Detected MLX models remain available to existing writing and dictation paths only.", "repair": {"action": "none", "label": "No action available"}})
        with self._db._connection() as conn:
            routed = conn.execute(
                "SELECT 1 FROM inference_assignment_migrations WHERE family='thoughts-writing-route-assignments'"
            ).fetchone() is not None
        current_routes = (
            {
                "authority": "inference_assignments",
                "thoughts": {"capability_id": "thought.interview"},
                "dictation": {"capability_ids": ["speech.intent_classify", "speech.rewrite"]},
                "meetings": {"target_id": config.meeting.intel_profile_id, "provider": config.meeting.intel_provider},
            }
            if routed else {
                "authority": "config",
                "thoughts": {
                    "target_id": config.thoughts.inference_target_id,
                    "inherits_this_device": config.thoughts.inference_target_id is None,
                    "revision": InferenceAcquisitionApplicationService.route_revision(config),
                },
                "dictation": {"target_id": config.dictation.runtime.profile_id, "backend": config.dictation.runtime.backend},
                "meetings": {"target_id": config.meeting.intel_profile_id, "provider": config.meeting.intel_provider},
            }
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "observed_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "hardware": hardware,
            "runtimes": runtimes,
            "current_routes": current_routes,
            "current_thought_deployment": {
                "source": source,
                "configured_target_id": configured_target_id,
                "target": _safe_target(target),
                "readiness": {"state": target.readiness_state, "available": target.ready, "reason": _safe_reason(target)},
                "execution_support": execution_support,
                "execution_revision": _safe_revision(target, self._db),
            },
            "artifact_detection": artifact_detection,
            "detected_local_artifacts": artifacts,
            "installed_model_artifacts": _installed_artifacts(self._db),
            "acquisitions": _acquisitions(self._db),
            "preset_catalog": {
                key: catalog[key]
                for key in (
                    "schema_version", "catalog_revision", "generated_at",
                    "expires_at", "signing_key_id", "sha256",
                )
            },
            "presets": applicable_presets(
                platform_id=platform_id,
                runtime_ids=runtime_ids,
                entries=catalog["entries"],
            ),
            "limitations": limitations,
        }
