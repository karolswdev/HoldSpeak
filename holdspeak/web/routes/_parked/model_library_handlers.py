"""Parked 2026-11-08 (Lane I): the six Model Library HTTP handlers no web or
iOS face called (the read, catalog download, add a detected model, connect a
hosted model, connect a paired device, use a model file). The service and its
MCP family (holdspeak/mcp/families/model_library.py) keep every one of these
commands. Kept as text, not mounted; they lived inside
``build_model_library_router`` in holdspeak/web/routes/model_library.py.
"""

PARKED_HANDLERS = r'''
    @router.get("/api/inference/model-library")
    def get_model_library(request: Request) -> Any:
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
            result = service.add_to_library(request.state.principal, await _json(request))
            _engine_changed("add_to_library")
            return JSONResponse(result, status_code=202)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add detected model")

    @router.post("/api/inference/model-library/connect-hosted-model")
    async def connect_hosted_model(request: Request) -> Any:
        try:
            draft, secret = await _provider_body(request)
            result = await run_in_threadpool(service.connect_hosted_model, request.state.principal, draft, secret)
            _engine_changed("connect_hosted_model")
            return JSONResponse(result, status_code=200)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception:
            return _provider_error_500("Failed to connect hosted model")

    @router.post("/api/inference/model-library/connect-paired-device")
    async def connect_paired_device(request: Request) -> Any:
        try:
            draft, secret = await _provider_body(request)
            if secret is not None:
                raise ServiceError("model_library_secret_invalid", "Paired device has no credential body.", context={"status": 400})
            result = service.connect_paired_device(request.state.principal, draft)
            _engine_changed("connect_paired_device")
            return JSONResponse(result, status_code=200)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception:
            return _provider_error_500("Failed to connect paired device")

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
            _engine_changed("use_model_file")
            return JSONResponse(result, status_code=202)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add model file")
        finally:
            if staging_path is not None:
                staging_path.unlink(missing_ok=True)

'''
