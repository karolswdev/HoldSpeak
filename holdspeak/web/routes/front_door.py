"""Front Door routes (HS-156-01 recommendation, HS-156-02 apply).

GET  /api/front-door/recommendation  -- pack recommendations
POST /api/front-door/apply           -- apply a recommended pack
GET  /api/front-door/apply           -- read the current apply plan
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...principals import UNAUTHENTICATED, PrincipalKind
from ...services.errors import ServiceError
from ..context import WebContext


def _error(exc: ServiceError) -> JSONResponse:
    ctx = exc.context or {}
    status = int(ctx.get("status", 400))
    return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=status)


def build_front_door_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/front-door", tags=["front-door"])

    @router.get("/recommendation")
    async def get_recommendation(request: Request) -> Any:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            return _error(ServiceError(
                "front_door_owner_required",
                "Owner access is required.",
                context={"status": 403},
            ))

        try:
            from ...services.front_door_service import recommend
            from ...services.inference_setup_service import (
                InferenceSetupApplicationService,
                inspect_hardware,
                inspect_runtimes,
                load_config_read_only,
            )
            from ...inference_setup_catalog import (
                applicable_presets,
                packaged_catalog_envelope_json,
                verify_catalog_envelope,
            )
            from ...inference_targets import (
                list_inference_targets,
                THIS_MACHINE_ID,
            )
            from ...config import Config
            from datetime import datetime, timezone
            from pathlib import Path

            # Gather inputs
            setup_svc = ctx.inference_setup_service
            db = None
            home = Path.home()
            now = datetime.now(timezone.utc)

            if setup_svc is not None:
                db = setup_svc._db
                home = setup_svc._home_provider()

            config = load_config_read_only()
            hardware = inspect_hardware(home=home, now=now)
            capability = hardware.get("capability", {})
            apple_silicon = bool(capability.get("apple_silicon"))
            runtimes = inspect_runtimes(apple_silicon=apple_silicon)

            # Catalog entries
            envelope_json = packaged_catalog_envelope_json()
            catalog = verify_catalog_envelope(envelope_json, now=now)
            runtime_ids = {
                row["id"] for row in runtimes
                if row["availability"]["state"] == "available"
            }
            platform_id = f'{capability["system"]}_{capability["architecture"]}'
            entries = applicable_presets(
                platform_id=platform_id,
                runtime_ids=runtime_ids,
                entries=catalog["entries"],
            )

            # Known endpoints: profiles with base_url (openAICompatible kind)
            known_endpoints: list[dict[str, Any]] = []
            if db is not None:
                for profile in db.profiles.list():
                    if profile.kind == "openAICompatible" and profile.base_url:
                        known_endpoints.append({
                            "id": profile.id,
                            "name": profile.name,
                            "base_url": profile.base_url,
                            "model": profile.model,
                        })

            # Legacy GGUF from config
            from ...intel.providers import configured_local_meeting_model_path
            legacy_path_raw = configured_local_meeting_model_path(meeting=config.meeting)
            legacy_gguf_path = legacy_path_raw if legacy_path_raw else None
            legacy_gguf_label = None
            if legacy_gguf_path:
                from pathlib import PurePosixPath
                legacy_gguf_label = PurePosixPath(legacy_gguf_path).name

            # Runtime availability
            has_llama_cpp = any(
                row["id"] == "llama_cpp_prompt_v1"
                and row["availability"]["state"] == "available"
                for row in runtimes
            )
            has_mlx = any(
                row["id"] == "mlx_text_v1"
                and row["availability"]["state"] == "available"
                for row in runtimes
            )

            # Cloud credential: check if any hosted profile has a key
            has_cloud_credential = False
            if db is not None:
                from ...inference_targets import _profile_key_present
                for profile in db.profiles.list():
                    if profile.kind == "openAICompatible" and profile.requires_key:
                        if _profile_key_present(profile.id):
                            has_cloud_credential = True
                            break

            result = recommend(
                hardware=hardware,
                catalog_entries=entries,
                known_endpoints=known_endpoints,
                legacy_gguf_path=legacy_gguf_path,
                legacy_gguf_label=legacy_gguf_label,
                has_llama_cpp=has_llama_cpp,
                has_mlx=has_mlx,
                has_cloud_credential=has_cloud_credential,
            )
            return JSONResponse(result)

        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return JSONResponse(
                {"code": "front_door_internal_error", "message": str(exc)},
                status_code=500,
            )

    @router.post("/apply")
    async def post_apply(request: Request) -> Any:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            return _error(ServiceError(
                "front_door_owner_required",
                "Owner access is required.",
                context={"status": 403},
            ))

        try:
            body = await request.json()
            pack_id = body.get("pack_id") if isinstance(body, dict) else None
            if not pack_id or not isinstance(pack_id, str):
                return _error(ServiceError(
                    "front_door_apply_invalid",
                    "pack_id is required.",
                    context={"status": 400},
                ))

            from ...services.front_door_service import apply_pack, recommend
            from ...services.inference_setup_service import (
                inspect_hardware,
                inspect_runtimes,
                load_config_read_only,
            )
            from ...inference_setup_catalog import (
                applicable_presets,
                packaged_catalog_envelope_json,
                verify_catalog_envelope,
            )
            from datetime import datetime, timezone
            from pathlib import Path

            setup_svc = ctx.inference_setup_service
            db = None
            home = Path.home()
            now = datetime.now(timezone.utc)

            if setup_svc is not None:
                db = setup_svc._db
                home = setup_svc._home_provider()

            if db is None:
                return _error(ServiceError(
                    "front_door_apply_unavailable",
                    "Database is not available.",
                    context={"status": 503},
                ))

            # Reconstruct the recommendation to find the requested pack
            config = load_config_read_only()
            hardware = inspect_hardware(home=home, now=now)
            capability = hardware.get("capability", {})
            apple_silicon = bool(capability.get("apple_silicon"))
            runtimes = inspect_runtimes(apple_silicon=apple_silicon)

            envelope_json = packaged_catalog_envelope_json()
            catalog = verify_catalog_envelope(envelope_json, now=now)
            catalog_revision = catalog["catalog_revision"]
            runtime_ids = {
                row["id"] for row in runtimes
                if row["availability"]["state"] == "available"
            }
            platform_id = f'{capability["system"]}_{capability["architecture"]}'
            entries = applicable_presets(
                platform_id=platform_id,
                runtime_ids=runtime_ids,
                entries=catalog["entries"],
            )

            known_endpoints: list[dict[str, Any]] = []
            for profile in db.profiles.list():
                if profile.kind == "openAICompatible" and profile.base_url:
                    known_endpoints.append({
                        "id": profile.id,
                        "name": profile.name,
                        "base_url": profile.base_url,
                        "model": profile.model,
                    })

            from ...intel.providers import configured_local_meeting_model_path
            legacy_path_raw = configured_local_meeting_model_path(meeting=config.meeting)
            legacy_gguf_path = legacy_path_raw if legacy_path_raw else None
            legacy_gguf_label = None
            if legacy_gguf_path:
                from pathlib import PurePosixPath
                legacy_gguf_label = PurePosixPath(legacy_gguf_path).name

            has_llama_cpp = any(
                row["id"] == "llama_cpp_prompt_v1"
                and row["availability"]["state"] == "available"
                for row in runtimes
            )
            has_mlx = any(
                row["id"] == "mlx_text_v1"
                and row["availability"]["state"] == "available"
                for row in runtimes
            )
            has_cloud_credential = False
            from ...inference_targets import _profile_key_present
            for profile in db.profiles.list():
                if profile.kind == "openAICompatible" and profile.requires_key:
                    if _profile_key_present(profile.id):
                        has_cloud_credential = True
                        break

            recommendation = recommend(
                hardware=hardware,
                catalog_entries=entries,
                known_endpoints=known_endpoints,
                legacy_gguf_path=legacy_gguf_path,
                legacy_gguf_label=legacy_gguf_label,
                has_llama_cpp=has_llama_cpp,
                has_mlx=has_mlx,
                has_cloud_credential=has_cloud_credential,
            )

            target_pack = None
            for pack in recommendation["packs"]:
                if pack["id"] == pack_id:
                    target_pack = pack
                    break

            if target_pack is None:
                return _error(ServiceError(
                    "front_door_pack_not_found",
                    f"Pack '{pack_id}' was not recommended for this hardware.",
                    context={"status": 404},
                ))

            model_library_svc = ctx.model_library_service
            assignment_svc = ctx.inference_assignment_service

            if model_library_svc is None or assignment_svc is None:
                return _error(ServiceError(
                    "front_door_apply_unavailable",
                    "Required services are not available.",
                    context={"status": 503},
                ))

            result = apply_pack(
                pack=target_pack,
                db=db,
                model_library_service=model_library_svc,
                assignment_service=assignment_svc,
                principal=principal,
                catalog_revision=catalog_revision,
            )
            return JSONResponse(result)

        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return JSONResponse(
                {"code": "front_door_apply_error", "message": str(exc)},
                status_code=500,
            )

    @router.get("/apply")
    async def get_apply(request: Request) -> Any:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            return _error(ServiceError(
                "front_door_owner_required",
                "Owner access is required.",
                context={"status": 403},
            ))

        try:
            setup_svc = ctx.inference_setup_service
            if setup_svc is None:
                return _error(ServiceError(
                    "front_door_apply_unavailable",
                    "Database is not available.",
                    context={"status": 503},
                ))
            db = setup_svc._db
            plan = db.front_door.get_latest_plan()
            if plan is None:
                return JSONResponse({"plan": None})
            return JSONResponse({"plan": plan})

        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return JSONResponse(
                {"code": "front_door_apply_error", "message": str(exc)},
                status_code=500,
            )

    return router
