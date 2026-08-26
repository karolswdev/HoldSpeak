"""Narrow owner-only HTTP transport for ModelLibraryProjection@1."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse

from ...services.errors import ServiceError
from ..context import WebContext
from ..runtime_support import error_500
from ...logging_config import get_logger

log = get_logger("web.routes.model_library")


def _safe_error(exc: ServiceError) -> JSONResponse:
    """Map domain failures without serializing private context or request bodies."""
    status = int(exc.context.get("status") or 400)
    if status not in {400, 403, 404, 409, 413, 503}:
        status = 400
    return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=status)


def build_model_library_router(ctx: WebContext) -> APIRouter:
    service = ctx.model_library_service
    if service is None:
        raise RuntimeError("ModelLibraryApplicationService must be supplied at application composition")
    router = APIRouter()

    def _owner(request: Request) -> None:
        # Deliberately before request.json()/form(): unauthorized callers never
        # get their potentially sensitive body parsed or retained by this seam.
        service.require_owner(getattr(request.state, "principal", None))

    async def _json(request: Request) -> dict[str, Any]:
        _owner(request)
        try:
            body = await request.json()
        except Exception as exc:
            raise ServiceError("model_library_request_invalid", "Expected a JSON object.", context={"status": 400}) from exc
        if not isinstance(body, dict):
            raise ServiceError("model_library_request_invalid", "Expected a JSON object.", context={"status": 400})
        return body

    async def _provider_body(request: Request) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Parse the nonsecret draft and dedicated write-only secret body.

        This seam intentionally has no request logging. Owner authority is
        checked before JSON parsing so an unauthorized caller's credential body
        cannot become request state here.
        """
        body = await _json(request)
        if set(body) != {"draft", "secret"} or not isinstance(body.get("draft"), dict):
            raise ServiceError("model_library_provider_invalid", "Provider request is invalid.", context={"status": 400})
        secret = body.get("secret")
        if secret is not None and not isinstance(secret, dict):
            raise ServiceError("model_library_secret_invalid", "Provider credential is invalid.", context={"status": 400})
        return body["draft"], secret

    @router.get("/api/inference/model-library")
    async def get_model_library(request: Request) -> Any:
        try:
            _owner(request)
            return service.get_library(request.state.principal)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read Model Library")

    @router.post("/api/inference/model-library/download")
    async def download_model(request: Request) -> Any:
        try:
            return JSONResponse(service.download(request.state.principal, await _json(request)), status_code=202)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add catalog model")

    @router.post("/api/inference/model-library/add-to-library")
    async def add_detected_model(request: Request) -> Any:
        try:
            return JSONResponse(service.add_to_library(request.state.principal, await _json(request)), status_code=202)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add detected model")

    @router.post("/api/inference/model-library/connect-hosted-model")
    async def connect_hosted_model(request: Request) -> Any:
        try:
            draft, secret = await _provider_body(request)
            return JSONResponse(
                service.connect_hosted_model(request.state.principal, draft, secret), status_code=200,
            )
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            # Never include a parsed request/secret in this safe error or log.
            return error_500(exc, log, "Failed to connect hosted model")

    @router.post("/api/inference/model-library/define-endpoint")
    async def define_endpoint(request: Request) -> Any:
        try:
            draft, secret = await _provider_body(request)
            return JSONResponse(
                service.define_endpoint(request.state.principal, draft, secret), status_code=200,
            )
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            # Never include a parsed request/secret in this safe error or log.
            return error_500(exc, log, "Failed to define provider endpoint")

    @router.post("/api/inference/model-library/connect-paired-device")
    async def connect_paired_device(request: Request) -> Any:
        try:
            draft, secret = await _provider_body(request)
            if secret is not None:
                raise ServiceError("model_library_secret_invalid", "Paired device has no credential body.", context={"status": 400})
            return JSONResponse(service.connect_paired_device(request.state.principal, draft), status_code=200)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to connect paired device")

    @router.post("/api/inference/model-library/use-model-file")
    async def use_model_file(request: Request) -> Any:
        staging_path: Path | None = None
        try:
            _owner(request)
            form = await request.form()
            # Do not accept paths, JSON-shaped upload plans, or extra transport
            # fields.  The hub receives bytes and owns all staging/verification.
            if set(form.keys()) != {"request_id", "file"}:
                raise ServiceError("model_library_upload_invalid", "Use model file has an invalid request shape.", context={"status": 400})
            request_id = form.get("request_id")
            upload = form.get("file")
            # ``Request.form`` yields Starlette's upload implementation; accept
            # that wire boundary structurally rather than treating it as a
            # browser-provided path/string.
            if not isinstance(upload, UploadFile) and not (hasattr(upload, "file") and hasattr(upload, "filename")):
                raise ServiceError("model_library_upload_invalid", "Upload one model file.", context={"status": 400})
            suffix = Path(upload.filename or "").suffix.lower() or ".upload"
            with tempfile.NamedTemporaryFile(prefix="holdspeak-model-library-", suffix=suffix, delete=False) as staged:
                staging_path = Path(staged.name)
                shutil.copyfileobj(upload.file, staged)
            if staging_path.stat().st_size == 0:
                raise ServiceError("model_library_upload_invalid", "The uploaded file is empty.", context={"status": 400})
            result = service.use_model_file(
                request.state.principal, request_id=request_id, filename=upload.filename or "", staging_path=staging_path,
            )
            return JSONResponse(result, status_code=202)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add model file")
        finally:
            if staging_path is not None:
                staging_path.unlink(missing_ok=True)

    return router


__all__ = ["build_model_library_router"]
