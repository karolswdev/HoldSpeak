"""Runtime profiles CRUD (the key never rides the wire).

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.profile_service import ProfileService
from ....services.primitive_service import NotFound, ValidationError
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

    def _svc() -> ProfileService:
        from ....db import get_database

        return ProfileService(get_database())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/profiles")
    async def api_list_profiles(request: Request) -> Any:
        try:
            return JSONResponse(_svc().list_profiles(_principal(request)))
        except Exception as exc:
            return error_500(exc, log, "Failed to list profiles")

    # HS-112-01: `/api/profiles` is a READ-ONLY alias over the same rows.
    # `/api/inference-targets` is the one write path.
    def _profiles_read_only() -> JSONResponse:
        return JSONResponse(
            {
                "error": "/api/profiles is read-only; write via /api/inference-targets",
                "write_path": "/api/inference-targets",
            },
            status_code=405,
        )

    @router.post("/api/profiles")
    async def api_create_profile(request: Request) -> Any:
        return _profiles_read_only()

    @router.get("/api/profiles/{profile_id}")
    async def api_get_profile(profile_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"profile": _svc().get_profile(_principal(request), profile_id)})
        except NotFound:
            return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get profile")

    @router.put("/api/profiles/{profile_id}")
    async def api_update_profile(profile_id: str, request: Request) -> Any:
        return _profiles_read_only()

    @router.delete("/api/profiles/{profile_id}")
    async def api_delete_profile(profile_id: str) -> Any:
        return _profiles_read_only()

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
    async def api_list_inference_targets(request: Request) -> Any:
        try:
            return JSONResponse(_svc().list_inference_targets(_principal(request)))
        except Exception as exc:
            return error_500(exc, log, "Failed to list inference targets")

    @router.post("/api/inference-targets/{target_id}/probe")
    async def api_probe_target(target_id: str) -> Any:
        """Test this destination without persisting a connection result."""
        try:
            from ....db import get_database
            from ....intel.providers import profile_key_env
            from ....setup_runtime import discover_endpoint_models

            db = get_database()
            profile = db.profiles.get(target_id)
            if profile is None:
                return JSONResponse(
                    {"error": f"Unknown destination: {target_id}"}, status_code=404
                )

            if profile.kind == "openAICompatible":
                started = time.perf_counter()
                discovered = discover_endpoint_models(
                    profile.base_url,
                    api_key=os.environ.get(profile_key_env(profile.id)),
                )
                latency_ms = int((time.perf_counter() - started) * 1000)
                reachable = bool(discovered.get("ok"))
                return JSONResponse({
                    "reachable": reachable,
                    "latency_ms": latency_ms,
                    "models": list(discovered.get("models") or []),
                    "error": None if reachable else str(discovered.get("detail") or "Unreachable"),
                })

            if profile.kind == "onDevice":
                model_file = Path(profile.model_file).expanduser()
                reachable = model_file.is_file()
                return JSONResponse({
                    "reachable": reachable,
                    "latency_ms": None,
                    "models": [profile.model] if reachable and profile.model else [],
                    "error": None if reachable else f"Model file not found: {model_file}",
                })

            if profile.kind == "meshNode":
                from datetime import datetime

                from ....intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS

                last_seen = db.mesh_relay.worker_last_seen(profile.node)
                age = None if last_seen is None else (datetime.now() - last_seen).total_seconds()
                reachable = age is not None and age <= DEFAULT_LIVENESS_WINDOW_SECONDS
                error = None if reachable else (
                    f"Mesh node '{profile.node}' has never checked in"
                    if age is None
                    else f"Mesh node '{profile.node}' last checked in {int(age)}s ago"
                )
                return JSONResponse({
                    "reachable": reachable,
                    "latency_ms": None,
                    "models": [],
                    "error": error,
                })

            return JSONResponse({
                "reachable": False,
                "latency_ms": None,
                "models": [],
                "error": f"Destination kind '{profile.kind}' cannot be probed",
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to probe inference target")

    @router.post("/api/inference-targets")
    async def api_create_inference_target(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if rejected := _reject_secret(body):
            return rejected
        try:
            target = _svc().create_profile(_principal(request), body)
            return JSONResponse({"inference_target": target}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
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
        if rejected := _reject_secret(body):
            return rejected
        try:
            target = _svc().update_profile(_principal(request), target_id, body)
            return JSONResponse({"inference_target": target})
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": f"Unknown destination: {target_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update inference target")

    @router.delete("/api/inference-targets/{target_id}")
    async def api_delete_inference_target(target_id: str, request: Request) -> Any:
        try:
            _svc().delete_profile(_principal(request), target_id)
            return JSONResponse({"success": True})
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": f"Unknown destination: {target_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete inference target")

    # ── KBs (knowledge bases) ─────────────────────────────────────────────

    return router
