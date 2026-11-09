"""First-run setup routes (HS-42-01), produced from ``holdspeak/setup_operations.py``.

Every ``/api/setup`` route (and the model download read, the inference
targets list) is ``OperationRegistry.invoke`` over its declared row. Each
answers in the envelope its hand-written handler had: the Setup window's
admitted presses (found, use, people, the LAN look) with the kernel receipt;
the first-value rows with ``{success: false, error}``; the local-AI rows with
``{code, message, recovery}``.

Kept hand-written: ``POST /api/setup/discover-models``. It reads a typed key,
a profile key or the environment's OpenAI key and decides per address which
one may leave the machine; that key custody moves to a service in its own
change, not as a side effect of this one.
"""
from __future__ import annotations

import os
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...services.errors import NotFound, ServiceError, ValidationError
from ...db import get_database, get_observer
from ...setup_operations import SETUP_OPERATIONS, Unavailable
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router
from ._room_kernel import kernel_refusal, refusal_fields, service_refusal

log = get_logger("web.routes.setup")

#: The Setup window's admitted presses and reads: the kernel receipt rides the answer.
_KERNEL = frozenset({"setup.found", "setup.use", "setup.people.add", "setup.lan.scan"})
#: The local-AI rows and the download read: ``{code, message, recovery}``.
_INFERENCE = frozenset({"setup.local_ai.status", "setup.local_ai.start", "setup.local_ai.cancel",
                        "inference.acquisition.get"})


def _refused(exc: OperationRefused) -> JSONResponse:
    status = 403 if exc.code == "owner_required" else 400
    return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code,
                         "message": exc.detail, **refusal_fields(exc)}, status_code=status)


async def _kernel_answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return _refused(exc)
    except ServiceError as exc:
        if (refused := kernel_refusal(exc)) is not None:
            return refused
        return service_refusal(exc)
    except Exception as exc:
        return error_500(exc, log, "Setup failed")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return _refused(exc)
    except NotFound as exc:
        return JSONResponse({"success": False, "error": repr(exc.id)}, status_code=404)
    except ValidationError as exc:
        return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
    except ServiceError as exc:
        if exc.code == "owner_required" or exc.context.get("status") == 403:
            return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=403)
        return JSONResponse({"success": False, "error": exc.detail, "code": exc.code},
                            status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        return error_500(exc, log, "Setup failed")


async def _inference_answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return _refused(exc)
    except ServiceError as exc:
        body: dict[str, Any] = {"code": exc.code, "message": exc.detail, "recovery": exc.context.get("recovery")}
        if "current" in exc.context:
            body["current"] = exc.context["current"]
        return JSONResponse(body, status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        return error_500(exc, log, "Local AI failed")


def build_setup_router(ctx: WebContext) -> APIRouter:
    if ctx.setup_service is None:
        raise RuntimeError("SetupService must be supplied at application composition")
    router = APIRouter()

    def ops() -> Any:
        from ...services.profile_service import ProfileService

        return operations.for_context(ctx, local_ai_setup_service=Unavailable,
                                      inference_acquisition_service=Unavailable,
                                      profile_service=lambda: ProfileService(get_database(), observer=get_observer()))

    mount_router(router, operation_router(
        [d for d in SETUP_OPERATIONS if d.name in _KERNEL], ops, _kernel_answer, module=__name__, receipted=True))
    mount_router(router, operation_router(
        [d for d in SETUP_OPERATIONS if d.name in _INFERENCE], ops, _inference_answer, module=__name__))
    mount_router(router, operation_router(
        [d for d in SETUP_OPERATIONS if d.name not in _KERNEL | _INFERENCE], ops, _answer, module=__name__))

    @router.post("/api/setup/discover-models")
    async def api_discover_models(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = None
        if not isinstance(body, dict):
            return JSONResponse({"ok": False, "models": [], "detail": "Expected a JSON object."}, status_code=400)
        try:
            from ...intel.providers import profile_key_env
            from ...profile_key_store import ProfileKeyStoreError, resolve_profile_key
            from ...setup_runtime import KEY_NOT_HEADER_SAFE, discover_endpoint_models, key_is_header_safe
            profile_id = str(body.get("profile_id") or "").strip()
            try:
                key = resolve_profile_key(profile_key_env(profile_id)) if profile_id else ""
            except ProfileKeyStoreError:
                key = ""
            # The environment key goes only to OpenAI itself (https,
            # api.openai.com). Any other address gets no key unless one was
            # typed or a profile was named: a caller-supplied address must
            # never receive the owner's OpenAI key.
            from urllib.parse import urlparse as _key_urlparse

            _target = _key_urlparse(str(body.get("base_url") or "").strip())
            fallback_key = (
                os.environ.get("OPENAI_API_KEY") or None
                if _target.scheme == "https" and _target.netloc.lower() in {"api.openai.com", "api.openai.com:443"}
                else None
            )
            # PHILO-15 02: the Concierge's optional Key field. A key typed on
            # the face is the one Check uses; it is used for this one call
            # and never stored or echoed (the saved key goes through the
            # Model Library's secret store on Use this for summaries).
            typed = body.get("api_key")
            typed_key = typed.strip() if isinstance(typed, str) else ""
            if typed_key and not key_is_header_safe(typed_key):
                # Refused at the boundary, before any header exists; never echoed.
                return JSONResponse(
                    {"ok": False, "models": [], "detail": KEY_NOT_HEADER_SAFE, "reason": "key_invalid"},
                    status_code=400,
                )
            if typed_key:
                api_key: str | None = typed_key
            elif profile_id:
                api_key = key
            else:
                api_key = fallback_key
            result = await run_in_threadpool(
                discover_endpoint_models,
                str(body.get("base_url") or ""),
                api_key=api_key,
            )
            # PHILO-15 10 (B05): the Check asks the server once whether it
            # takes tool calls. Only the face's Check asks (`check_tools`).
            if result.get("ok") and result.get("models") and body.get("check_tools") is True:
                from urllib.parse import urlparse as _urlparse

                import ipaddress as _ip

                from ...setup_runtime import endpoint_tool_support

                base_url = str(body.get("base_url") or "")
                # Astra r1, finding 4: the 1-token request goes only where it
                # cannot be billed: no key, and a private or loopback address
                # LITERAL (a name or a suffix can point anywhere) -- or the
                # owner said "this is my server" (MY SERVER on the row).
                try:
                    _addr = _ip.ip_address((_urlparse(base_url).hostname or "").strip("[]"))
                    private = _addr.is_private or _addr.is_loopback
                except ValueError:
                    private = False
                own_server = body.get("my_server") is True
                result["tools"] = await run_in_threadpool(
                    endpoint_tool_support,
                    base_url,
                    model=str(result["models"][0]),
                    api_key=api_key,
                    lan=own_server or (private and not api_key),
                    tools_claimed=bool(result.get("toolsClaimed")),
                )
            return JSONResponse(result, status_code=200 if result.get("ok") else 422)
        except Exception as exc:
            return error_500(exc, log, "Failed to discover endpoint models")

    return router
