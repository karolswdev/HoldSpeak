"""Transport-neutral profile and inference-target operations (HS-122-05)."""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import time
from typing import Any

from ..db.core import Database
from ..principals import Principal
from holdspeak.services.errors import NotFound, ServiceError, ValidationError


class ProfileService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def list_profiles(self, principal: Principal) -> dict[str, Any]:
        from ..intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS

        profiles = self._db.profiles.list()
        liveness: dict[str, Any] = {}
        nodes = {str(getattr(profile, "node", "") or "") for profile in profiles if profile.kind == "meshNode"}
        now = datetime.now()
        for node in sorted(nodes - {""}):
            last = self._db.mesh_relay.worker_last_seen(node)
            age = None if last is None else (now - last).total_seconds()
            liveness[node] = {
                "live": age is not None and age <= DEFAULT_LIVENESS_WINDOW_SECONDS,
                "last_seen_seconds": None if age is None else int(age),
            }
        return {"profiles": [profile.to_dict() for profile in profiles], "mesh_liveness": liveness}

    def get_profile(self, principal: Principal, profile_id: str) -> dict[str, Any]:
        profile = self._db.profiles.get(profile_id)
        if profile is None:
            raise NotFound("profile", profile_id)
        return profile.to_dict()

    def create_profile(self, principal: Principal, fields: dict[str, Any]) -> dict[str, Any]:
        self._reject_secret(fields)
        if not str(fields.get("name") or "").strip():
            raise ValidationError("destination name is required")
        profile = self._db.profiles.upsert(
            profile_id=str(fields.get("id") or self._new_id()),
            **self._target_fields(fields),
        )
        return self._target(profile)

    def update_profile(
        self, principal: Principal, profile_id: str, patch: dict[str, Any]
    ) -> dict[str, Any]:
        if profile_id == "this_machine":
            raise ValidationError("This device is a built-in destination")
        self._reject_secret(patch)
        existing = self._db.profiles.get(profile_id)
        if existing is None:
            raise NotFound("destination", profile_id)
        profile = self._db.profiles.upsert(
            profile_id=profile_id, **self._target_fields(patch, existing)
        )
        return self._target(profile)

    def delete_profile(self, principal: Principal, profile_id: str) -> bool:
        if profile_id == "this_machine":
            raise ValidationError("This device is a built-in destination")
        if not self._db.profiles.delete(profile_id):
            raise NotFound("destination", profile_id)
        return True

    def list_inference_targets(self, principal: Principal) -> dict[str, Any]:
        from ..inference_targets import PROFILE_ALIAS_VERSION, TARGET_CONTRACT_VERSION, list_inference_targets

        return {
            "version": TARGET_CONTRACT_VERSION,
            "targets": [target.to_dict() for target in list_inference_targets(self._db)],
            "profile_alias": {
                "version": PROFILE_ALIAS_VERSION,
                "status": "supported",
                "removal": "not_before_inference_target_v3",
            },
        }

    def probe_inference_target(
        self, principal: Principal, target_id: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        from ..intel.providers import profile_key_env
        from ..setup_runtime import discover_endpoint_models

        profile = self._db.profiles.get(target_id)
        if profile is None:
            raise NotFound("destination", target_id)
        if profile.kind == "openAICompatible":
            started = time.perf_counter()
            discovered = discover_endpoint_models(profile.base_url, api_key=os.environ.get(profile_key_env(profile.id)))
            reachable = bool(discovered.get("ok"))
            return {"reachable": reachable, "latency_ms": int((time.perf_counter() - started) * 1000), "models": list(discovered.get("models") or []), "error": None if reachable else str(discovered.get("detail") or "Unreachable")}
        if profile.kind == "onDevice":
            model_file = Path(profile.model_file).expanduser()
            reachable = model_file.is_file()
            return {"reachable": reachable, "latency_ms": None, "models": [profile.model] if reachable and profile.model else [], "error": None if reachable else f"Model file not found: {model_file}"}
        if profile.kind == "meshNode":
            from ..intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS
            last_seen = self._db.mesh_relay.worker_last_seen(profile.node)
            age = None if last_seen is None else (datetime.now() - last_seen).total_seconds()
            reachable = age is not None and age <= DEFAULT_LIVENESS_WINDOW_SECONDS
            error = None if reachable else (f"Mesh node '{profile.node}' has never checked in" if age is None else f"Mesh node '{profile.node}' last checked in {int(age)}s ago")
            return {"reachable": reachable, "latency_ms": None, "models": [], "error": error}
        return {"reachable": False, "latency_ms": None, "models": [], "error": f"Destination kind '{profile.kind}' cannot be probed"}

    def get_inference_target(self, principal: Principal, target_id: str) -> dict[str, Any]:
        from ..inference_targets import resolve_inference_target
        target = resolve_inference_target(self._db, target_id)
        if target.readiness_state == "unavailable":
            raise ServiceError("target_unavailable", target.readiness_reason, context={"status": 404})
        return {"inference_target": target.to_dict()}

    @staticmethod
    def _new_id() -> str:
        import uuid
        return f"target_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _reject_secret(body: dict[str, Any]) -> None:
        forbidden = sorted(
            key for key in body
            if key.lower().replace("-", "_") in {"api_key", "apikey", "secret", "token"}
        )
        if forbidden:
            raise ValidationError(
                "InferenceTarget never accepts secret material: " + ", ".join(forbidden)
            )

    @staticmethod
    def _target_fields(body: dict[str, Any], existing: Any = None) -> dict[str, Any]:
        aliases = {
            "this_device": "onDevice", "paired_device": "desktop",
            "private_endpoint": "openAICompatible", "external_service": "openAICompatible",
            "mesh_node": "meshNode", "onDevice": "onDevice", "desktop": "desktop",
            "openAICompatible": "openAICompatible", "meshNode": "meshNode",
        }
        adapted = dict(body)
        def pick(key: str, default: Any) -> Any:
            return adapted[key] if key in adapted else default
        if "endpoint" in adapted and "base_url" not in adapted:
            adapted["base_url"] = adapted["endpoint"]
        if "contextLimit" in adapted and "context_limit" not in adapted:
            adapted["context_limit"] = adapted["contextLimit"]
        if "requiresKey" in adapted and "requires_key" not in adapted:
            adapted["requires_key"] = adapted["requiresKey"]
        if isinstance(adapted.get("engine"), dict) and "model" not in adapted:
            adapted["model"] = adapted["engine"].get("model", "")
        kind = str(adapted.get("kind", existing.kind if existing else "this_device"))
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "kind": aliases.get(kind, kind),
            "model_file": str(pick("model_file", existing.model_file if existing else "")),
            "base_url": str(pick("base_url", existing.base_url if existing else "")),
            "model": str(pick("model", existing.model if existing else "")),
            "node": str(pick("node", existing.node if existing else "")),
            "context_limit": int(pick("context_limit", existing.context_limit if existing else 16384)),
            "requires_key": bool(pick("requires_key", existing.requires_key if existing else False)),
        }

    def _target(self, profile: Any) -> dict[str, Any]:
        from ..inference_targets import target_from_profile
        return target_from_profile(profile, self._db).to_dict()
