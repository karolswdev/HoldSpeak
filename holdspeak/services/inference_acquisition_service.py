"""Durable GGUF acquisition and activation (HS-142-02).

The owner command is one saga: intent is durable before network, bytes are
verified before adoption, and activation is a later narrow route mutation.
Filesystem and SQLite work are deliberately ordered rather than called atomic.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from ..config import Config
from ..deployment_revisions import DeploymentRevision
from ..inference_setup_catalog import packaged_catalog
from ..principals import Principal, PrincipalKind
from .errors import ServiceError
from .settings_service import settings_revision


_CHUNK_BYTES = 1024 * 1024
_ALLOWED_STATES = {
    "requested", "resolving_source", "downloading", "verifying",
    "installing", "ready", "cancelled", "failed", "indeterminate",
}
_CANCELLABLE = {"requested", "resolving_source", "downloading"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _route_revision(config: Config) -> str:
    return _sha({
        "thoughts_target_id": config.thoughts.inference_target_id,
        "local_model": config.meeting.intel_realtime_model,
    })


def _safe_error(code: str) -> tuple[str, str]:
    messages = {
        "model_download_network": (
            "Download stopped.",
            "HoldSpeak could not reach Hugging Face. The file will restart safely.",
        ),
        "model_download_integrity": (
            "The downloaded model did not match its published checksum.",
            "The bytes were quarantined and will not be used.",
        ),
        "model_download_disk": (
            "There is not enough free space to download and install this model safely.",
            "Choose a smaller model or free some space.",
        ),
        "model_activation_conflict": (
            "The model is downloaded and verified, but Thoughts changed AI while it downloaded.",
            "Choose Use for Thoughts when you are ready.",
        ),
        "model_existing_invalid": (
            "That local model changed or could not be verified.",
            "Check the file, then refresh Models and try again.",
        ),
    }
    return messages.get(code, ("Model setup stopped.", "Try again or choose another model."))


class _Cancelled(Exception):
    pass


class InferenceAcquisitionApplicationService:
    """Owner-only acquisition authority with a durable pollable ledger."""

    def __init__(
        self,
        db: Any,
        *,
        setup_service: Any,
        model_root: Path | None = None,
        config_provider: Callable[[], Config] = Config.load,
        config_saver: Callable[[Config], None] | None = None,
        opener: Callable[..., Any] = urlopen,
        catalog_provider: Callable[[], dict[str, Any]] | None = None,
        source_url_builder: Callable[[dict[str, Any]], str] | None = None,
        allowed_download_host: Callable[[str], bool] | None = None,
        home_provider: Callable[[], Path] = Path.home,
        auto_recover: bool = True,
    ) -> None:
        self._db = db
        self._setup = setup_service
        self._root = model_root or (Path.home() / ".local" / "share" / "holdspeak" / "models")
        self._config_provider = config_provider
        self._config_saver = config_saver or (lambda config: config.save())
        self._opener = opener
        self._catalog_provider = catalog_provider or (
            lambda: packaged_catalog(now=datetime.now(timezone.utc))
        )
        self._source_url_builder = source_url_builder or self._huggingface_url
        self._allowed_download_host = allowed_download_host or (
            lambda host: host == "huggingface.co"
            or host.endswith(".hf.co")
            or host.endswith(".huggingface.co")
        )
        self._home_provider = home_provider
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="holdspeak-model")
        self._submitted: set[str] = set()
        self._submitted_lock = threading.Lock()
        if auto_recover:
            self.recover()

    @staticmethod
    def _require_owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "inference_setup_owner_required", "Owner access is required.",
                context={"status": 403},
            )

    @staticmethod
    def route_revision(config: Config) -> str:
        return _route_revision(config)

    def recover(self) -> None:
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT job_id FROM inference_model_acquisitions
                    WHERE state IN ('requested','resolving_source','downloading','verifying','installing')"""
            ).fetchall()
        for row in rows:
            self._submit(str(row["job_id"]))

    def _submit(self, job_id: str) -> None:
        with self._submitted_lock:
            if job_id in self._submitted:
                return
            self._submitted.add(job_id)
        future = self._executor.submit(self._run, job_id)
        future.add_done_callback(lambda _future: self._forget(job_id))

    def _forget(self, job_id: str) -> None:
        with self._submitted_lock:
            self._submitted.discard(job_id)

    def download_and_use(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        self._require_owner(principal)
        allowed = {
            "request_id", "preset_id", "catalog_revision", "context_choice",
            "expected_route_revision",
        }
        if not isinstance(body, dict) or set(body) != allowed:
            raise ServiceError(
                "inference_acquisition_request_invalid",
                "Download & use has an invalid request shape.", context={"status": 400},
            )
        request_id = str(body["request_id"] or "").strip()
        if not request_id or len(request_id) > 128:
            raise ServiceError("inference_request_id_invalid", "A stable request id is required.", context={"status": 400})
        if (
            not isinstance(body["preset_id"], str)
            or not body["preset_id"]
            or type(body["catalog_revision"]) is not int
            or type(body["context_choice"]) is not int
            or not isinstance(body["expected_route_revision"], str)
        ):
            raise ServiceError("inference_acquisition_request_invalid", "Download & use has invalid field types.", context={"status": 400})
        expected_route = body["expected_route_revision"]
        payload = {
            "request_id": request_id,
            "preset_id": body["preset_id"],
            "catalog_revision": body["catalog_revision"],
            "context_choice": body["context_choice"],
            "expected_route_revision": expected_route,
        }
        request_sha = _sha(payload)
        with self._db._connection() as conn:
            replay = conn.execute(
                """SELECT job_id,request_sha256 FROM inference_model_acquisitions
                    WHERE request_id=?""",
                (request_id,),
            ).fetchone()
        if replay is not None:
            if str(replay["request_sha256"]) != request_sha:
                raise ServiceError("request_payload_mismatch", "That request id was already used for different model setup.", context={"status": 409})
            acquisition = self._get(str(replay["job_id"]))
            return {"acquisition": acquisition, "receipt": self._receipt(acquisition), "setup": self._setup.get_inference_setup(principal)}
        catalog = self._catalog_provider()
        if body["catalog_revision"] != catalog["catalog_revision"]:
            raise ServiceError("inference_catalog_stale", "The model catalog changed. Check again.", context={"status": 409})
        preset = next((row for row in catalog["entries"] if row["id"] == body["preset_id"]), None)
        if preset is None or preset["kind"] != "local_artifact_preset":
            raise ServiceError("inference_preset_unknown", "That local model is not in this catalog.", context={"status": 404})
        if preset["format"] != "gguf" or preset["runtime_id"] != "llama_cpp_prompt_v1":
            raise ServiceError("inference_runtime_unsupported", "This model cannot run in Thoughts yet.", context={"status": 409})
        if body["context_choice"] != preset["context"]["recommended_tokens"]:
            raise ServiceError("inference_context_choice_invalid", "That context size is not qualified for this preset.", context={"status": 409})
        current_config = self._config_provider()
        if expected_route != _route_revision(current_config):
            raise ServiceError("inference_route_stale", "Thoughts changed AI. Check the current route and try again.", context={"status": 409})
        source = dict(preset["source"])
        signed_manifest = {
            "files": [{
                "path": source["filename"],
                "sha256": source["file_sha256"],
                "size": source["download_bytes"],
            }],
        }
        if _sha(signed_manifest) != source["manifest_sha256"]:
            raise ServiceError("inference_catalog_integrity", "The signed model manifest is inconsistent.", context={"status": 409})
        if shutil.disk_usage(self._root.parent if self._root.parent.exists() else Path.home()).free < source["peak_free_bytes"]:
            raise ServiceError("model_download_disk", _safe_error("model_download_disk")[0], context={"status": 409})
        plan = {
            "kind": "huggingface_file",
            "repository": source["repository"],
            "revision": source["revision"],
            "filename": source["filename"],
            "sha256": source["file_sha256"],
            "size": source["download_bytes"],
            "manifest_sha256": source["manifest_sha256"],
            "license": source["license"],
            "runtime_id": preset["runtime_id"],
            "runtime_min_revision": preset["runtime_min_revision"],
            "format": preset["format"],
            "model_identity": preset["label"],
            "context_ceiling": int(body["context_choice"]),
        }
        plan_sha = _sha(plan)
        source_claim_sha = _sha({
            key: plan[key]
            for key in (
                "kind", "repository", "revision", "filename", "sha256",
                "size", "manifest_sha256", "format",
            )
        })
        job_id = "acq_" + hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:32]
        created = _now()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            replay = conn.execute(
                "SELECT request_sha256 FROM inference_model_acquisitions WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if replay is not None:
                if str(replay["request_sha256"]) != request_sha:
                    conn.rollback()
                    raise ServiceError("request_payload_mismatch", "That request id was already used for different model setup.", context={"status": 409})
                conn.commit()
                acquisition = self._get(job_id)
                return {"acquisition": acquisition, "receipt": self._receipt(acquisition), "setup": self._setup.get_inference_setup(principal)}
            active = conn.execute(
                """SELECT job_id FROM inference_model_acquisitions
                    WHERE source_claim_sha256=?
                      AND state IN ('requested','resolving_source','downloading','verifying','installing')
                    ORDER BY created_at ASC LIMIT 1""",
                (source_claim_sha,),
            ).fetchone()
            if active is not None:
                conn.commit()
                acquisition = self._get(str(active["job_id"]))
                return {"acquisition": acquisition, "receipt": self._receipt(acquisition), "setup": self._setup.get_inference_setup(principal)}
            conn.execute(
                """INSERT INTO inference_model_acquisitions
                   (job_id,request_id,request_sha256,preset_id,catalog_revision,
                    source_plan_json,source_plan_sha256,source_claim_sha256,state,bytes_total,
                    expected_route_revision,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,'requested',?,?,?,?)""",
                (
                    job_id, request_id, request_sha, preset["id"],
                    catalog["catalog_revision"], _canonical(plan), plan_sha, source_claim_sha,
                    source["download_bytes"], expected_route, created, created,
                ),
            )
            conn.commit()
        self._adopt_resumable_prefix(job_id, source_claim_sha, int(plan["size"]), str(plan["filename"]))
        self._submit(job_id)
        acquisition = self._get(job_id)
        return {"acquisition": acquisition, "receipt": self._receipt(acquisition), "setup": self._setup.get_inference_setup(principal)}

    def use_existing(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        """Verify and activate one freshly re-resolved detected GGUF."""
        self._require_owner(principal)
        allowed = {
            "request_id", "detected_artifact_id", "context_choice",
            "expected_route_revision",
        }
        if not isinstance(body, dict) or set(body) != allowed:
            raise ServiceError(
                "inference_existing_request_invalid",
                "Use existing model has an invalid request shape.",
                context={"status": 400},
            )
        request_id = str(body["request_id"] or "").strip()
        detected_id = str(body["detected_artifact_id"] or "").strip()
        expected_route = str(body["expected_route_revision"] or "")
        if (
            not request_id or len(request_id) > 128
            or not detected_id.startswith("detected_")
            or len(detected_id) > 96
            or type(body["context_choice"]) is not int
            or body["context_choice"] != 8192
            or not expected_route
        ):
            raise ServiceError(
                "inference_existing_request_invalid",
                "Use existing model has invalid fields.", context={"status": 400},
            )
        payload = {
            "request_id": request_id,
            "detected_artifact_id": detected_id,
            "context_choice": body["context_choice"],
            "expected_route_revision": expected_route,
        }
        request_sha = _sha(payload)
        with self._db._connection() as conn:
            replay = conn.execute(
                "SELECT job_id,request_sha256 FROM inference_model_acquisitions WHERE request_id=?",
                (request_id,),
            ).fetchone()
        if replay is not None:
            if str(replay["request_sha256"]) != request_sha:
                raise ServiceError(
                    "request_payload_mismatch",
                    "That request id was already used for different model setup.",
                    context={"status": 409},
                )
            acquisition = self._get(str(replay["job_id"]))
            return {
                "acquisition": acquisition,
                "receipt": self._receipt(acquisition),
                "setup": self._setup.get_inference_setup(principal),
            }
        config = self._config_provider()
        if expected_route != _route_revision(config):
            raise ServiceError(
                "inference_route_stale",
                "Thoughts changed AI. Check the current route and try again.",
                context={"status": 409},
            )
        from .inference_setup_service import (
            _this_machine_from_config,
            resolve_detected_local_artifact,
        )

        candidate = resolve_detected_local_artifact(
            home=self._home_provider(),
            current_target=_this_machine_from_config(config),
            artifact_id=detected_id,
        )
        if candidate is None:
            raise ServiceError(
                "inference_detected_artifact_stale",
                "That detected model is no longer available. Refresh Models.",
                context={"status": 409},
            )
        if candidate["format"] != "gguf":
            raise ServiceError(
                "inference_runtime_unsupported",
                "MLX Thought execution is not installed yet.",
                context={"status": 409},
            )
        path = Path(candidate["path"])
        try:
            stat = path.stat()
        except OSError as exc:
            raise ServiceError(
                "inference_detected_artifact_stale",
                "That detected model is no longer available. Refresh Models.",
                context={"status": 409},
            ) from exc
        plan = {
            "kind": "existing_local_file",
            "filename": path.name,
            "local_locator": str(path),
            "size": int(stat.st_size),
            "mtime_ns": int(stat.st_mtime_ns),
            "runtime_id": "llama_cpp_prompt_v1",
            # Existing GGUF activation uses the long-established pinned local
            # engine seam; it does not require the newer acquisition-only
            # runtime features used by packaged downloads.
            "runtime_min_revision": "0.3.16",
            "format": "gguf",
            "architecture": "gguf",
            "model_identity": str(candidate["label"]).removesuffix(".gguf"),
            "context_ceiling": 8192,
        }
        plan_sha = _sha(plan)
        source_claim_sha = _sha({
            "kind": plan["kind"], "locator": plan["local_locator"],
            "size": plan["size"], "mtime_ns": plan["mtime_ns"],
        })
        job_id = "acq_" + hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:32]
        created = _now()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            replay = conn.execute(
                "SELECT job_id,request_sha256 FROM inference_model_acquisitions WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if replay is not None:
                if str(replay["request_sha256"]) != request_sha:
                    conn.rollback()
                    raise ServiceError(
                        "request_payload_mismatch",
                        "That request id was already used for different model setup.",
                        context={"status": 409},
                    )
                conn.commit()
                acquisition = self._get(str(replay["job_id"]))
                return {
                    "acquisition": acquisition,
                    "receipt": self._receipt(acquisition),
                    "setup": self._setup.get_inference_setup(principal),
                }
            active = conn.execute(
                """SELECT job_id FROM inference_model_acquisitions
                    WHERE source_claim_sha256=?
                      AND state IN ('requested','resolving_source','downloading','verifying','installing')
                    ORDER BY created_at ASC LIMIT 1""",
                (source_claim_sha,),
            ).fetchone()
            if active is not None:
                conn.commit()
                acquisition = self._get(str(active["job_id"]))
                return {
                    "acquisition": acquisition,
                    "receipt": self._receipt(acquisition),
                    "setup": self._setup.get_inference_setup(principal),
                }
            conn.execute(
                """INSERT INTO inference_model_acquisitions
                   (job_id,request_id,request_sha256,preset_id,catalog_revision,
                    source_plan_json,source_plan_sha256,source_claim_sha256,state,
                    bytes_total,expected_route_revision,created_at,updated_at)
                   VALUES (?,?,?,?,0,?,?,?,'requested',?,?,?,?)""",
                (
                    job_id, request_id, request_sha, detected_id,
                    _canonical(plan), plan_sha, source_claim_sha, plan["size"],
                    expected_route, created, created,
                ),
            )
            conn.commit()
        self._submit(job_id)
        acquisition = self._get(job_id)
        return {
            "acquisition": acquisition,
            "receipt": self._receipt(acquisition),
            "setup": self._setup.get_inference_setup(principal),
        }

    def get_acquisition(self, principal: Principal, job_id: str) -> dict[str, Any]:
        self._require_owner(principal)
        acquisition = self._get(job_id)
        return {"acquisition": acquisition}

    def cancel(self, principal: Principal, job_id: str, body: dict[str, Any]) -> dict[str, Any]:
        self._require_owner(principal)
        if not isinstance(body, dict) or set(body) != {"request_id", "expected_revision"}:
            raise ServiceError("inference_cancel_invalid", "Cancel has an invalid request shape.", context={"status": 400})
        request_id = str(body["request_id"] or "").strip()
        if not request_id or len(request_id) > 128:
            raise ServiceError("inference_request_id_invalid", "A stable request id is required.", context={"status": 400})
        request_sha = _sha({
            "request_id": request_id,
            "job_id": job_id,
            "expected_revision": int(body["expected_revision"]),
        })
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM inference_model_acquisitions WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                conn.rollback()
                raise ServiceError("inference_acquisition_unknown", "That download does not exist.", context={"status": 404})
            if row["cancel_request_id"] == request_id:
                if row["cancel_request_sha256"] != request_sha:
                    conn.rollback()
                    raise ServiceError("request_payload_mismatch", "That request id was already used for a different cancellation.", context={"status": 409})
                conn.commit()
                acquisition = self._get(job_id)
                return {"acquisition": acquisition, "receipt": self._receipt(acquisition), "setup": self._setup.get_inference_setup(principal)}
            if int(row["revision"]) != int(body["expected_revision"]):
                conn.rollback()
                raise ServiceError("inference_acquisition_stale", "The download changed. Check its current state.", context={"status": 409})
            if str(row["state"]) not in _CANCELLABLE:
                conn.rollback()
                raise ServiceError("cancellation_too_late", "Verification has begun; this model can no longer be cancelled.", context={"status": 409, "current": self._public(row)})
            conn.execute(
                """UPDATE inference_model_acquisitions
                      SET cancel_requested=1, cancel_request_id=?,
                          cancel_request_sha256=?, revision=revision+1, updated_at=?
                    WHERE job_id=?""",
                (request_id, request_sha, _now(), job_id),
            )
            conn.commit()
        acquisition = self._get(job_id)
        return {"acquisition": acquisition, "receipt": self._receipt(acquisition), "setup": self._setup.get_inference_setup(principal)}

    def list_active(self) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM inference_model_acquisitions
                    WHERE state NOT IN ('cancelled','failed')
                    ORDER BY created_at DESC LIMIT 20"""
            ).fetchall()
        return [self._public(row) for row in rows]

    def _get(self, job_id: str) -> dict[str, Any]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM inference_model_acquisitions WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise ServiceError("inference_acquisition_unknown", "That download does not exist.", context={"status": 404})
        return self._public(row)

    @staticmethod
    def _public(row: Any) -> dict[str, Any]:
        state = str(row["state"])
        return {
            "id": str(row["job_id"]),
            "preset_id": str(row["preset_id"]),
            "state": state if state in _ALLOWED_STATES else "indeterminate",
            "verified_bytes": int(row["verified_bytes"]),
            "transport_bytes": int(row["transport_bytes"]),
            "bytes_total": int(row["bytes_total"]),
            "artifact_id": row["artifact_id"],
            "activation_state": str(row["activation_state"]),
            "error": None if not row["error_code"] else {
                "code": str(row["error_code"]),
                "message": str(row["error_message"] or "Model setup stopped."),
            },
            "resumable": bool(row["resumable"]),
            "can_cancel": state in _CANCELLABLE,
            "revision": int(row["revision"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    @staticmethod
    def _receipt(acquisition: dict[str, Any]) -> dict[str, Any]:
        return {
            "kind": "model_acquisition",
            "acquisition_id": acquisition["id"],
            "artifact_id": acquisition["artifact_id"],
            "state": acquisition["state"],
            "activation_state": acquisition["activation_state"],
        }

    def _transition(self, job_id: str, state: str, **fields: Any) -> None:
        assignments = ["state=?", "revision=revision+1", "updated_at=?"]
        values: list[Any] = [state, _now()]
        for key, value in fields.items():
            if key not in {"verified_bytes", "transport_bytes", "artifact_id", "activation_state", "receipt_json", "error_code", "error_message", "resumable"}:
                raise ValueError(f"invalid acquisition field: {key}")
            assignments.append(f"{key}=?")
            values.append(value)
        values.append(job_id)
        with self._db._connection() as conn:
            conn.execute(f"UPDATE inference_model_acquisitions SET {', '.join(assignments)} WHERE job_id=?", values)

    def _cancelled(self, job_id: str) -> bool:
        with self._db._connection() as conn:
            row = conn.execute("SELECT cancel_requested,state FROM inference_model_acquisitions WHERE job_id=?", (job_id,)).fetchone()
        return bool(row and row["cancel_requested"] and str(row["state"]) in _CANCELLABLE)

    def _run(self, job_id: str) -> None:
        plan: dict[str, Any] = {}
        try:
            with self._db._connection() as conn:
                row = conn.execute("SELECT * FROM inference_model_acquisitions WHERE job_id=?", (job_id,)).fetchone()
            if row is None or str(row["state"]) in {"ready", "cancelled", "failed"}:
                return
            plan = json.loads(str(row["source_plan_json"]))
            if _sha(plan) != str(row["source_plan_sha256"]):
                self._transition(job_id, "indeterminate", error_code="source_plan_integrity", error_message="The saved download plan is damaged.")
                return
            if plan.get("kind") == "existing_local_file":
                self._run_existing(job_id, plan)
                return
            self._transition(job_id, "resolving_source")
            if self._cancelled(job_id):
                raise _Cancelled
            staging = self._root / "staging" / job_id
            staging.mkdir(parents=True, exist_ok=True)
            part = staging / (str(plan["filename"]) + ".part")
            self._transition(job_id, "downloading")
            self._download(job_id, plan, part)
            if self._cancelled(job_id):
                raise _Cancelled
            self._transition(job_id, "verifying")
            digest = self._hash_file(part)
            if digest != str(plan["sha256"]).removeprefix("sha256:") or part.stat().st_size != int(plan["size"]):
                quarantine = self._root / "quarantine"
                quarantine.mkdir(parents=True, exist_ok=True)
                os.replace(part, quarantine / f"{job_id}.invalid")
                self._fail(job_id, "model_download_integrity")
                return
            with part.open("rb") as handle:
                if handle.read(4) != b"GGUF":
                    self._fail(job_id, "model_download_integrity")
                    return
            self._transition(job_id, "installing", verified_bytes=int(plan["size"]))
            artifact_id = "artifact_" + str(plan["manifest_sha256"]).removeprefix("sha256:")
            artifact_dir = self._root / "artifacts" / artifact_id
            artifact_dir.parent.mkdir(parents=True, exist_ok=True)
            final_file = artifact_dir / str(plan["filename"])
            if not artifact_dir.exists():
                marker = staging / "holdspeak-artifact.json"
                marker.write_text(_canonical({"artifact_id": artifact_id, "plan": plan}), encoding="utf-8")
                os.replace(part, staging / str(plan["filename"]))
                os.replace(staging, artifact_dir)
            elif not final_file.is_file() or self._hash_file(final_file) != digest:
                self._fail(job_id, "model_download_integrity")
                return
            else:
                shutil.rmtree(staging, ignore_errors=True)
            now = _now()
            with self._db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    """INSERT OR IGNORE INTO inference_model_artifacts
                       (artifact_id,format,source_kind,source_repository,
                        source_revision,manifest_json,manifest_sha256,
                        installed_bytes,state,local_locator,created_at,verified_at)
                       VALUES (?,?,?,?,?,?,?,?, 'verified',?,?,?)""",
                    (
                        artifact_id, plan["format"], plan["kind"],
                        plan["repository"], plan["revision"],
                        _canonical({"files": [{"path": plan["filename"], "sha256": plan["sha256"], "size": plan["size"]}]}),
                        plan["manifest_sha256"], plan["size"], str(final_file),
                        now, now,
                    ),
                )
                conn.commit()
            self._activate(job_id, artifact_id, final_file, plan)
        except _Cancelled:
            staging = self._root / "staging" / job_id
            if staging.is_dir():
                shutil.rmtree(staging, ignore_errors=True)
            self._transition(job_id, "cancelled")
        except OSError as exc:
            if plan.get("kind") == "existing_local_file":
                self._fail(job_id, "model_existing_invalid")
                return
            code = "model_download_disk" if getattr(exc, "errno", None) == 28 else "model_download_network"
            part = self._partial_file(job_id)
            resumable = bool(
                code == "model_download_network"
                and part is not None
                and 0 < part.stat().st_size < int(plan.get("size", 0))
            )
            self._fail(job_id, code, resumable=resumable)
        except Exception:
            self._fail(
                job_id,
                "model_existing_invalid"
                if plan.get("kind") == "existing_local_file"
                else "model_download_network",
            )

    def _run_existing(self, job_id: str, plan: dict[str, Any]) -> None:
        self._transition(job_id, "resolving_source")
        if self._cancelled(job_id):
            raise _Cancelled
        path = Path(str(plan["local_locator"]))
        if path.is_symlink() or not path.is_file():
            raise OSError("detected model is no longer a regular file")
        stat = path.stat()
        if (
            int(stat.st_size) != int(plan["size"])
            or int(stat.st_mtime_ns) != int(plan["mtime_ns"])
        ):
            raise OSError("detected model changed before verification")
        self._transition(job_id, "verifying")
        digest = self._hash_file(path)
        with path.open("rb") as handle:
            if handle.read(4) != b"GGUF":
                raise OSError("detected model is not GGUF")
        post = path.stat()
        if (
            int(post.st_size) != int(plan["size"])
            or int(post.st_mtime_ns) != int(plan["mtime_ns"])
        ):
            raise OSError("detected model changed during verification")
        sha = "sha256:" + digest
        manifest = {
            "files": [{"path": plan["filename"], "sha256": sha, "size": plan["size"]}],
        }
        manifest_sha = _sha(manifest)
        execution_plan = {
            **plan,
            "sha256": sha,
            "manifest_sha256": manifest_sha,
            "repository": "Existing local model",
            "revision": sha,
        }
        self._transition(job_id, "installing", verified_bytes=int(plan["size"]))
        artifact_id = "artifact_" + manifest_sha.removeprefix("sha256:")
        now = _now()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """INSERT OR IGNORE INTO inference_model_artifacts
                   (artifact_id,format,source_kind,source_repository,
                    source_revision,manifest_json,manifest_sha256,
                    installed_bytes,state,local_locator,created_at,verified_at)
                   VALUES (?,?,?,?,?,?,?,?, 'verified',?,?,?)""",
                (
                    artifact_id, "gguf", "existing_local_file",
                    "Existing local model", sha, _canonical(manifest),
                    manifest_sha, plan["size"], str(path), now, now,
                ),
            )
            conn.commit()
        self._activate(job_id, artifact_id, path, execution_plan)

    def _download(self, job_id: str, plan: dict[str, Any], part: Path) -> None:
        url = self._source_url_builder(plan)
        offset = part.stat().st_size if part.is_file() else 0
        headers = {"User-Agent": "HoldSpeak/HS-142-02"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        request = Request(url, headers=headers)
        with self._opener(request, timeout=60) as response:
            final = urlparse(str(response.geturl()))
            host = (final.hostname or "").lower()
            if final.scheme not in {"https", "http"} or not self._allowed_download_host(host):
                raise OSError("download redirect left the approved source boundary")
            status = getattr(response, "status", None)
            if status is None and hasattr(response, "getcode"):
                status = response.getcode()
            response_headers = getattr(response, "headers", {})
            content_range = response_headers.get("Content-Range", "") if hasattr(response_headers, "get") else ""
            append = bool(offset and status == 206 and str(content_range).startswith(f"bytes {offset}-"))
            if offset and not append:
                offset = 0
                self._transition(job_id, "downloading", transport_bytes=0, resumable=0)
            total = offset
            with part.open("ab" if append else "wb") as output:
                while True:
                    if self._cancelled(job_id):
                        raise _Cancelled
                    chunk = response.read(_CHUNK_BYTES)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > int(plan["size"]):
                        raise OSError("download exceeded signed size")
                    output.write(chunk)
                    self._transition(job_id, "downloading", transport_bytes=total, resumable=1 if append else 0)
            if total != int(plan["size"]):
                raise OSError("download ended before signed size")

    @staticmethod
    def _huggingface_url(plan: dict[str, Any]) -> str:
        return (
            "https://huggingface.co/" + quote(str(plan["repository"]), safe="/")
            + "/resolve/" + quote(str(plan["revision"]), safe="")
            + "/" + quote(str(plan["filename"]), safe="") + "?download=true"
        )

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(_CHUNK_BYTES):
                digest.update(chunk)
        return digest.hexdigest()

    def _activate(self, job_id: str, artifact_id: str, final_file: Path, plan: dict[str, Any]) -> None:
        config = self._config_provider()
        with self._db._connection() as conn:
            row = conn.execute("SELECT expected_route_revision FROM inference_model_acquisitions WHERE job_id=?", (job_id,)).fetchone()
        if row is None or _route_revision(config) != str(row["expected_route_revision"]):
            self._transition(job_id, "ready", artifact_id=artifact_id, activation_state="failed", error_code="model_activation_conflict", error_message=_safe_error("model_activation_conflict")[0])
            return
        try:
            runtime_revision = importlib.metadata.version("llama-cpp-python")
        except importlib.metadata.PackageNotFoundError:
            self._transition(
                job_id,
                "ready",
                artifact_id=artifact_id,
                activation_state="failed",
                error_code="inference_runtime_unavailable",
                error_message="The model is verified, but llama.cpp support is not installed.",
            )
            return
        from .inference_setup_service import _version_at_least
        if not _version_at_least(runtime_revision, str(plan["runtime_min_revision"])):
            self._transition(
                job_id,
                "ready",
                artifact_id=artifact_id,
                activation_state="failed",
                error_code="inference_runtime_unavailable",
                error_message=f"The model is verified, but llama-cpp-python {plan['runtime_min_revision']} or newer is required.",
            )
            return
        capability = {"structured_output": True, "format": "gguf", "context_ceiling": int(plan["context_ceiling"])}
        capability_sha = _sha(capability)
        revision = DeploymentRevision.from_artifact(
            destination_id="this_machine", engine="configured_local_engine",
            model=str(plan["model_identity"]), runtime_id=str(plan["runtime_id"]),
            runtime_revision=runtime_revision, artifact_id=artifact_id,
            manifest_sha256=str(plan["manifest_sha256"]), format="gguf",
            architecture=str(plan.get("architecture") or "gguf"),
            context_ceiling=int(plan["context_ceiling"]),
            capability_sha256=capability_sha,
        )
        config.meeting.intel_realtime_model = str(final_file)
        config.thoughts.inference_target_id = None
        self._config_saver(config)
        now = _now()
        deployment_id = "deployment_" + artifact_id.removeprefix("artifact_")[:24]
        receipt = {
            "kind": (
                "use_existing_model"
                if plan.get("kind") == "existing_local_file"
                else "download_and_use"
            ),
            "artifact_id": artifact_id,
            "deployment_id": deployment_id, "deployment_revision_id": revision.id,
            "route": "thoughts", "activated_at": now,
        }
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._insert_revision(conn, revision)
            conn.execute("UPDATE inference_deployments SET active=0 WHERE destination_id='this_machine'")
            conn.execute(
                """INSERT INTO inference_deployments
                   (deployment_id,destination_id,runtime_id,runtime_revision,
                    artifact_id,model_identity,context_ceiling,
                    recommended_context,capability_json,capability_sha256,
                    execution_revision_id,configuration_revision,active,
                    created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,1,1,?,?)
                   ON CONFLICT(deployment_id) DO UPDATE SET
                    active=1, configuration_revision=configuration_revision+1,
                    updated_at=excluded.updated_at""",
                (
                    deployment_id, "this_machine", plan["runtime_id"],
                    runtime_revision, artifact_id, plan["model_identity"],
                    plan["context_ceiling"], plan["context_ceiling"],
                    _canonical(capability), capability_sha, revision.id, now, now,
                ),
            )
            conn.execute(
                """UPDATE inference_model_acquisitions
                      SET state='ready', artifact_id=?, activation_state='in_use',
                          receipt_json=?, error_code=NULL,error_message=NULL,
                          revision=revision+1,updated_at=? WHERE job_id=?""",
                (artifact_id, _canonical(receipt), now, job_id),
            )
            conn.commit()

    @staticmethod
    def _insert_revision(conn: Any, revision: DeploymentRevision) -> None:
        conn.execute(
            """INSERT OR IGNORE INTO deployment_revisions
               (id,schema_version,destination_id,kind,engine,model,node,boundary,
                endpoint,model_path,secret_slot,runtime_id,runtime_revision,
                artifact_id,manifest_sha256,format,architecture,context_ceiling,
                capability_sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                revision.id, revision.schema_version, revision.destination_id,
                revision.kind, revision.engine, revision.model, revision.node,
                revision.boundary, revision.endpoint, None, revision.secret_slot,
                revision.runtime_id, revision.runtime_revision,
                revision.artifact_id, revision.manifest_sha256, revision.format,
                revision.architecture, revision.context_ceiling,
                revision.capability_sha256,
            ),
        )

    def _partial_file(self, job_id: str) -> Path | None:
        staging = self._root / "staging" / job_id
        if not staging.is_dir():
            return None
        try:
            return next(path for path in staging.iterdir() if path.name.endswith(".part") and path.is_file())
        except (OSError, StopIteration):
            return None

    def _adopt_resumable_prefix(
        self, job_id: str, source_claim_sha: str, total: int, filename: str,
    ) -> None:
        with self._db._connection() as conn:
            prior = conn.execute(
                """SELECT job_id FROM inference_model_acquisitions
                    WHERE source_claim_sha256=? AND state='failed' AND resumable=1
                      AND job_id<>? ORDER BY updated_at DESC LIMIT 1""",
                (source_claim_sha, job_id),
            ).fetchone()
        if prior is None:
            return
        source = self._partial_file(str(prior["job_id"]))
        if source is None:
            return
        try:
            size = source.stat().st_size
            if not 0 < size < total:
                return
            destination_dir = self._root / "staging" / job_id
            destination_dir.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination_dir / f"{filename}.part")
            self._transition(job_id, "requested", transport_bytes=size, resumable=1)
        except OSError:
            return

    def _fail(self, job_id: str, code: str, *, resumable: bool = False) -> None:
        title, detail = _safe_error(code)
        if code == "model_download_network" and resumable:
            detail = "Your resumable partial download is kept; the complete file will still be checksum-verified before use."
        self._transition(
            job_id, "failed", error_code=code,
            error_message=f"{title} {detail}", resumable=1 if resumable else 0,
        )


__all__ = ["InferenceAcquisitionApplicationService"]
