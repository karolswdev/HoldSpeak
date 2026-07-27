"""HTTP transports for the kernel's four caller and three executor calls."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from .... import kernel
from ....kernel.model import KernelRefused
from ....kernel.runtime import _as_principal


def _refused(exc: KernelRefused) -> JSONResponse:
    status = 403 if "principal" in exc.reason else 409
    return JSONResponse(
        {"error": exc.reason, "operation_id": exc.operation_id or None}, status_code=status
    )


def build_kernel_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/kernel/read")
    async def api_kernel_read(
        request: Request, refs: list[str] = Query(default=[]),
        view: str = "state", consistency: str = "committed",
    ) -> Any:
        try:
            with _as_principal(request.state.principal):
                return JSONResponse(kernel.read(refs, view, consistency))
        except KernelRefused as exc:
            return _refused(exc)

    @router.post("/api/kernel/submit")
    async def api_kernel_submit(request: Request) -> Any:
        body = await request.json()
        try:
            with _as_principal(request.state.principal):
                return JSONResponse(kernel.submit(body), status_code=202)
        except KernelRefused as exc:
            return _refused(exc)

    @router.post("/api/kernel/operations/{operation_id}/decide")
    async def api_kernel_decide(operation_id: str, request: Request) -> Any:
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "decision_body_malformed"}, status_code=400)
        mutation = {"payload", "arguments", "target", "placement"}.intersection(body)
        if mutation:
            return JSONResponse(
                {"error": "admitted_envelope_immutable", "fields": sorted(mutation)},
                status_code=409,
            )
        unknown = set(body) - {"decision", "expected_revision"}
        if unknown:
            return JSONResponse(
                {"error": "decision_field_not_allowed", "fields": sorted(unknown)},
                status_code=400,
            )
        try:
            revision = int(body.get("expected_revision"))
            with _as_principal(request.state.principal):
                return JSONResponse(
                    kernel.decide(operation_id, str(body.get("decision") or ""), revision)
                )
        except KernelRefused as exc:
            return _refused(exc)
        except (TypeError, ValueError):
            return JSONResponse({"error": "expected_revision_required"}, status_code=400)

    @router.get("/api/kernel/events")
    async def api_kernel_events(
        request: Request, after_cursor: int = 0, operation_id: str = "",
        event_type: str = "", privacy_class: str = "", stream: str = "",
    ) -> Any:
        filters = {
            key: value for key, value in {
                "operation_id": operation_id, "event_type": event_type,
                "privacy_class": privacy_class, "stream": stream,
            }.items() if value
        }
        try:
            with _as_principal(request.state.principal):
                return JSONResponse(kernel.events(after_cursor, filters))
        except KernelRefused as exc:
            return _refused(exc)

    @router.post("/api/kernel/executor/claim")
    async def api_kernel_claim(request: Request) -> Any:
        try:
            with _as_principal(request.state.principal):
                return JSONResponse(kernel.claim())
        except KernelRefused as exc:
            return _refused(exc)

    @router.post("/api/kernel/executor/operations/{operation_id}/receipt")
    async def api_kernel_receipt(operation_id: str, request: Request) -> Any:
        body = await request.json()
        if not isinstance(body, dict) or set(body) - {"outcome", "result_ref"}:
            return JSONResponse({"error": "receipt_body_invalid"}, status_code=400)
        try:
            with _as_principal(request.state.principal):
                return JSONResponse(
                    kernel.receipt(
                        operation_id, str(body.get("outcome") or ""),
                        str(body.get("result_ref") or ""),
                    )
                )
        except KernelRefused as exc:
            return _refused(exc)

    @router.get("/api/kernel/executor/operations/{operation_id}/reconcile")
    async def api_kernel_reconcile(operation_id: str, request: Request) -> Any:
        try:
            with _as_principal(request.state.principal):
                return JSONResponse(kernel.reconcile(operation_id))
        except KernelRefused as exc:
            return _refused(exc)

    return router
