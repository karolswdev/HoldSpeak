"""Owner-facing Model Library availability authority (HS-143-12).

This service intentionally composes the catalog, local acquisition saga, and
canonical profile/binding authority.  It is not an assignment editor: library
commands snapshot assignment heads on both sides of the operation and never
call ``InferenceAssignmentService.set_assignment``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..principals import Principal, PrincipalKind
from .errors import ServiceError
from .model_profile_service import ModelProfileService

MODEL_LIBRARY_SCHEMA = "ModelLibraryProjection@1"
_SUCCESS_COPY = "Added to the Model Library. Assignments are unchanged."
_ACTIONS = frozenset({
    "Download", "Add to library", "Connect", "Add model", "Ready", "Checking", "Try again",
})


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


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
    ) -> None:
        self._db = db
        self._setup = setup_service
        self._acquisition = acquisition_service
        self._profiles = profile_service or ModelProfileService(db)

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
        if before != after:
            raise ServiceError(
                "model_library_assignment_changed", "Model Library cannot change assignments.", context={"status": 409}
            )
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
    def _revision(value: Any) -> int:
        if type(value) is not int or value < 1:
            raise ServiceError("model_library_request_invalid", "catalog_revision is invalid.", context={"status": 400})
        return value

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
            binding = item.get("current_binding") or None
            readiness = item.get("latest_readiness") or None
            if binding is None:
                status, action, repair = "configured", "Add model", self._repair("binding_missing", "Model needs a deployment binding")
            elif readiness and readiness.get("state") == "ready":
                status, action, repair = "ready", "Ready", None
            else:
                code = _text((readiness or {}).get("reason_code"), "readiness_unknown")
                status, action, repair = "broken", "Checking", self._repair(code, "Check this model")
            rows.append(self._row(
                row_id="profile:" + _text(item.get("profile_id"), "unknown"), source="profile",
                label=_text(item.get("label")), status=status, action=action, repair=repair,
                detail={"provider_family": _text(item.get("provider_family"), "unknown"), "runtime_family": _text(item.get("runtime_family"), "unknown"), "profile_revision": int(item.get("revision") or 0)},
            ))
        for item in profiles.get("legacy_profiles", []):
            legacy_profile = dict(item.get("profile") or {})
            rows.append(self._row(
                row_id="legacy:" + _text(item.get("source_id"), "unknown"), source="legacy",
                label=_text(legacy_profile.get("label")), status="configured", action="Add model",
                repair=self._repair("legacy_adapter", "Add this legacy model to the library"),
                detail={"provider_family": _text(legacy_profile.get("provider_family"), "legacy")},
            ))
        return rows

    @staticmethod
    def _repair(code: str, label: str) -> dict[str, str]:
        return {"code": code, "label": label}

    @staticmethod
    def _row(*, row_id: str, source: str, label: str, status: str, action: str, repair: dict[str, str] | None, detail: dict[str, Any]) -> dict[str, Any]:
        if action not in _ACTIONS:
            raise AssertionError("model library action is not closed")
        return {"id": row_id, "source": source, "label": label, "status": status, "detail": detail, "repair": repair, "selected_action": action}


__all__ = ["MODEL_LIBRARY_SCHEMA", "ModelLibraryApplicationService"]
