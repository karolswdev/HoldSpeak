"""Evidence dossier + safe asset routes (HS-94-05).

The §10 hub API's evidence surface:

- ``GET /api/delivery/stories/{project}/{story}/dossier`` — the story
  dossier: sanitized story/evidence Markdown served as text, parsed
  captured runs (pass/fail explicit), path-free asset metadata, phase
  and final-summary references;
- ``GET /api/delivery/phases/{project}/{phase}/dossier`` — the
  phase's story dossiers grouped, metadata only (no asset reads on
  this route — laziness is proven by subprocess count in tests);
- ``GET /api/delivery/evidence/{bundle_id}/{asset_id}`` — bytes via
  the counterpart's ``dw evidence asset`` chokepoint, Content-Type
  from the manifest, single-range requests honored (dw streams whole
  bounded members — MAX_ASSET_BYTES-capped — so the hub slices the
  captured bytes; multi-range answers 200 full).

Typed refusal mapping (dossiers.REFUSAL_HTTP): not_in_manifest /
outside_root / symlink / absent → 404, oversize → 413,
bundle_changed / hash_mismatch → 409 (cached manifest metadata rides
the body — §13: preserve, request a new bundle), source offline /
dw dead → 503 ``unavailable`` (the manifest stays visible on the
dossier routes). Raw filesystem paths never cross the wire in either
direction.

This router supersedes the legacy ``/api/missioncontrol/evidence``
read; that route stays working alongside (§10 compatibility rule).
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.delivery_dossiers")

_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def _classified_500(exc: Exception, detail: str) -> JSONResponse:
    """§12.3: the exception (which may carry paths) goes to the log,
    never the wire."""
    log.error(f"{detail}: {exc}")
    return JSONResponse({"error": detail}, status_code=500)


def _refusal_response(refusal: Any) -> JSONResponse:
    body: dict[str, Any] = {
        "refusal": refusal.code,
        "detail": refusal.detail,
    }
    if refusal.manifest is not None:
        body["manifest"] = refusal.manifest
    return JSONResponse(body, status_code=refusal.http_status)


def parse_range(header: Optional[str], size: int) -> Optional[tuple[int, int]]:
    """One satisfiable single range as ``(start, end)`` inclusive.
    ``None`` means serve the full body (absent/malformed/multi-range —
    documented 200 fallback). An unsatisfiable start raises
    ``ValueError`` for a 416."""
    if not header:
        return None
    match = _RANGE_RE.match(header.strip())
    if not match:
        return None
    start_text, end_text = match.groups()
    if not start_text and not end_text:
        return None
    if not start_text:
        # suffix range: last N bytes
        length = int(end_text)
        if length <= 0:
            raise ValueError("unsatisfiable range")
        start = max(0, size - length)
        return (start, size - 1)
    start = int(start_text)
    if start >= size:
        raise ValueError("unsatisfiable range")
    end = int(end_text) if end_text else size - 1
    return (start, min(end, size - 1))


def build_delivery_dossiers_router(
    ctx: WebContext,
    *,
    service: Any = None,
    registry_path: Optional[Path] = None,
    map_path: Optional[Path] = None,
    runner: Any = None,
    dw_argv_factory: Any = None,
    max_age_seconds: float = 15.0,
) -> APIRouter:
    """Every keyword is a test seam (the delivery-router precedent);
    production uses the defaults. The service builds lazily so app
    assembly has no side effects."""
    _ = ctx
    router = APIRouter()
    holder: dict[str, Any] = {"service": service}

    def _service() -> Any:
        if holder["service"] is None:
            from ...delivery import DeliveryRegistry
            from ...delivery.dossiers import DossierService

            registry = DeliveryRegistry(registry_path, map_path=map_path)
            holder["service"] = DossierService(
                registry,
                runner=runner,
                dw_argv_factory=dw_argv_factory,
                max_age_seconds=max_age_seconds,
            )
        return holder["service"]

    @router.get("/api/delivery/stories/{project}/{story}/dossier")
    async def api_story_dossier(
        project: str, story: str, source: str = ""
    ) -> Any:
        """The story dossier. ``?source=src_...`` pins one source;
        omitted, every registered source is tried (a story an offline
        source may hold answers 503, never a silent 404)."""
        from ...delivery.dossiers import DossierRefusal

        try:
            def _load() -> Any:
                svc = _service()
                if source:
                    return svc.story_dossier(source, project, story)
                return svc.story_dossier_any(project, story)

            return await asyncio.to_thread(_load)
        except DossierRefusal as refusal:
            return _refusal_response(refusal)
        except Exception as exc:
            return _classified_500(exc, "story dossier failed")

    @router.get("/api/delivery/phases/{project}/{phase}/dossier")
    async def api_phase_dossier(
        project: str, phase: int, source: str = ""
    ) -> Any:
        """The phase dossier: grouped story dossiers + the final
        summary REFERENCE — metadata only, no asset bytes load here."""
        from ...delivery.dossiers import DossierRefusal

        try:
            def _load() -> Any:
                svc = _service()
                if source:
                    return svc.phase_dossier(source, project, phase)
                last: Any = None
                for source_id in svc.source_ids():
                    try:
                        return svc.phase_dossier(source_id, project, phase)
                    except DossierRefusal as refusal:
                        if refusal.code != "not_found":
                            last = refusal
                raise last or DossierRefusal(
                    "not_found", f"phase {phase} not found in any source"
                )

            return await asyncio.to_thread(_load)
        except DossierRefusal as refusal:
            return _refusal_response(refusal)
        except Exception as exc:
            return _classified_500(exc, "phase dossier failed")

    @router.get("/api/delivery/evidence/{bundle_id}/{asset_id}")
    async def api_evidence_asset(
        bundle_id: str, asset_id: str, request: Request
    ) -> Any:
        """Manifest-bound bytes. Content-Type comes from the manifest,
        ETag is the member sha256, and single Range requests answer
        206 (dw's member cap bounds the buffered body)."""
        from ...delivery.dossiers import DossierRefusal

        try:
            data, member = await asyncio.to_thread(
                lambda: _service().open_asset(bundle_id, asset_id)
            )
        except DossierRefusal as refusal:
            return _refusal_response(refusal)
        except Exception as exc:
            return _classified_500(exc, "evidence asset failed")

        etag = str(member.get("sha256") or "")
        media_type = str(member.get("media_type") or "application/octet-stream")
        headers = {"Accept-Ranges": "bytes", "ETag": etag}
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers=headers)
        try:
            window = parse_range(request.headers.get("range"), len(data))
        except ValueError:
            return Response(
                status_code=416,
                headers={**headers, "Content-Range": f"bytes */{len(data)}"},
            )
        if window is None:
            return Response(content=data, media_type=media_type, headers=headers)
        start, end = window
        return Response(
            content=data[start : end + 1],
            status_code=206,
            media_type=media_type,
            headers={
                **headers,
                "Content-Range": f"bytes {start}-{end}/{len(data)}",
            },
        )

    return router
