"""Runtime profiles CRUD (the key never rides the wire).

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _new_id

log = get_logger("web.routes.primitives")


def build_profiles_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _reject_secret(body: dict[str, Any]) -> Optional[JSONResponse]:
        forbidden = sorted(
            key for key in body
            if key.lower().replace("-", "_") in {"api_key", "apikey", "secret", "token"}
        )
        if forbidden:
            return JSONResponse(
                {"error": "InferenceTarget never accepts secret material", "forbidden_fields": forbidden},
                status_code=400,
            )
        return None

    def _profile_fields(body: dict[str, Any], existing=None) -> dict[str, Any]:
        def pick(key: str, default: Any) -> Any:
            return body[key] if key in body else default
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "kind": str(pick("kind", existing.kind if existing else "onDevice")),
            "model_file": str(pick("model_file", existing.model_file if existing else "")),
            "base_url": str(pick("base_url", existing.base_url if existing else "")),
            "model": str(pick("model", existing.model if existing else "")),
            "node": str(pick("node", existing.node if existing else "")),
            "context_limit": int(pick("context_limit", existing.context_limit if existing else 16384)),
            "requires_key": bool(pick("requires_key", existing.requires_key if existing else False)),
        }

    @router.get("/api/profiles")
    async def api_list_profiles() -> Any:
        try:
            from ....db import get_database
            db = get_database()
            profiles = db.profiles.list()
            # HS-85-04: mesh liveness rides the ENVELOPE, never the profile
            # shape (the synced primitive stays pure; the shape guard pins it).
            liveness: dict[str, Any] = {}
            nodes = {str(getattr(p, "node", "") or "") for p in profiles if p.kind == "meshNode"}
            if nodes - {""}:
                from datetime import datetime as _dt

                from ....intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS

                now = _dt.now()
                for node in sorted(nodes - {""}):
                    last = db.mesh_relay.worker_last_seen(node)
                    age = None if last is None else (now - last).total_seconds()
                    liveness[node] = {
                        "live": age is not None and age <= DEFAULT_LIVENESS_WINDOW_SECONDS,
                        "last_seen_seconds": None if age is None else int(age),
                    }
            return JSONResponse({
                "profiles": [p.to_dict() for p in profiles],
                "mesh_liveness": liveness,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to list profiles")

    @router.post("/api/profiles")
    async def api_create_profile(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        # Legacy Profile clients historically sent key-shaped extras. Keep the
        # alias tolerant and drop them through _profile_fields; the canonical
        # InferenceTarget endpoint below refuses secret material explicitly.
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "profile name is required"}, status_code=400)
        try:
            from ....db import get_database
            profile = get_database().profiles.upsert(
                profile_id=str(body.get("id") or _new_id("profile")),
                **_profile_fields(body),
            )
            return JSONResponse({"profile": profile.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create profile")

    @router.get("/api/profiles/{profile_id}")
    async def api_get_profile(profile_id: str) -> Any:
        try:
            from ....db import get_database
            profile = get_database().profiles.get(profile_id)
            if profile is None:
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            return JSONResponse({"profile": profile.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get profile")

    @router.put("/api/profiles/{profile_id}")
    async def api_update_profile(profile_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.profiles.get(profile_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            profile = db.profiles.upsert(profile_id=profile_id, **_profile_fields(body, existing))
            return JSONResponse({"profile": profile.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update profile")

    @router.delete("/api/profiles/{profile_id}")
    async def api_delete_profile(profile_id: str) -> Any:
        try:
            from ....db import get_database
            if not get_database().profiles.delete(profile_id):
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete profile")

    # HS-92-07: InferenceTarget is an additive API/view over the version-1
    # ProfileRecord.  The old endpoints and sync primitive stay byte-compatible;
    # both names read and write the same rows, so old and new clients converge.
    def _target_fields(body: dict[str, Any], existing=None) -> dict[str, Any]:
        kind_aliases = {
            "this_device": "onDevice",
            "paired_device": "desktop",
            "private_endpoint": "openAICompatible",
            "external_service": "openAICompatible",
            "mesh_node": "meshNode",
            # Profile-kind values are tolerated during the alias window.
            "onDevice": "onDevice",
            "desktop": "desktop",
            "openAICompatible": "openAICompatible",
            "meshNode": "meshNode",
        }
        raw_kind = str(body.get("kind", existing.kind if existing else "this_device"))
        adapted = dict(body)
        adapted["kind"] = kind_aliases.get(raw_kind, raw_kind)
        if "endpoint" in body and "base_url" not in body:
            adapted["base_url"] = body["endpoint"]
        if "contextLimit" in body and "context_limit" not in body:
            adapted["context_limit"] = body["contextLimit"]
        if "requiresKey" in body and "requires_key" not in body:
            adapted["requires_key"] = body["requiresKey"]
        if isinstance(body.get("engine"), dict) and "model" not in body:
            adapted["model"] = body["engine"].get("model", "")
        return _profile_fields(adapted, existing)

    @router.get("/api/inference-targets")
    async def api_list_inference_targets() -> Any:
        try:
            from ....db import get_database
            from ....inference_targets import (
                PROFILE_ALIAS_VERSION,
                TARGET_CONTRACT_VERSION,
                list_inference_targets,
            )

            db = get_database()
            return JSONResponse({
                "version": TARGET_CONTRACT_VERSION,
                "targets": [target.to_dict() for target in list_inference_targets(db)],
                "profile_alias": {
                    "version": PROFILE_ALIAS_VERSION,
                    "status": "supported",
                    "removal": "not_before_inference_target_v3",
                },
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to list inference targets")

    @router.post("/api/inference-targets")
    async def api_create_inference_target(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if rejected := _reject_secret(body):
            return rejected
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "destination name is required"}, status_code=400)
        try:
            from ....db import get_database
            from ....inference_targets import target_from_profile

            db = get_database()
            profile = db.profiles.upsert(
                profile_id=str(body.get("id") or _new_id("target")),
                **_target_fields(body),
            )
            return JSONResponse(
                {"inference_target": target_from_profile(profile, db).to_dict()},
                status_code=201,
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create inference target")

    @router.get("/api/inference-targets/{target_id}")
    async def api_get_inference_target(target_id: str) -> Any:
        try:
            from ....db import get_database
            from ....inference_targets import resolve_inference_target

            target = resolve_inference_target(get_database(), target_id)
            if target.readiness_state == "unavailable":
                return JSONResponse({"error": target.readiness_reason}, status_code=404)
            return JSONResponse({"inference_target": target.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get inference target")

    @router.put("/api/inference-targets/{target_id}")
    async def api_update_inference_target(target_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if target_id == "this_machine":
            return JSONResponse({"error": "This device is a built-in destination"}, status_code=400)
        if rejected := _reject_secret(body):
            return rejected
        try:
            from ....db import get_database
            from ....inference_targets import target_from_profile

            db = get_database()
            existing = db.profiles.get(target_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown destination: {target_id}"}, status_code=404)
            profile = db.profiles.upsert(
                profile_id=target_id, **_target_fields(body, existing)
            )
            return JSONResponse({"inference_target": target_from_profile(profile, db).to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update inference target")

    @router.delete("/api/inference-targets/{target_id}")
    async def api_delete_inference_target(target_id: str) -> Any:
        if target_id == "this_machine":
            return JSONResponse({"error": "This device is a built-in destination"}, status_code=400)
        try:
            from ....db import get_database
            if not get_database().profiles.delete(target_id):
                return JSONResponse({"error": f"Unknown destination: {target_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete inference target")

    # ── KBs (knowledge bases) ─────────────────────────────────────────────

    return router
