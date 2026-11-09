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

import re
from typing import Any, Optional

from fastapi import APIRouter, Request, Response
from starlette.concurrency import run_in_threadpool

from ...principals import UNAUTHENTICATED
from ..context import WebContext
from . import delivery_declared

_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


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


def build_delivery_dossiers_router(ctx: WebContext) -> APIRouter:
    """The dossier routes, produced from the ``delivery.story_dossier``,
    ``delivery.phase_dossier`` and ``delivery.evidence_asset`` rows. The
    dossier service and its test seams live on ``ctx.delivery_service``.
    The asset route answers a file, so it is written here; it still calls
    the declared verb."""
    registry = delivery_declared.registry_for(ctx)

    def asset_handler(descriptor: Any) -> Any:
        async def api_evidence_asset(bundle_id: str, asset_id: str, request: Request) -> Any:
            """Manifest-bound bytes. Content-Type comes from the manifest,
            ETag is the member sha256, and single Range requests answer
            206 (dw's member cap bounds the buffered body)."""
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            args = {"bundle_id": bundle_id, "asset_id": asset_id}
            try:
                data, member = await run_in_threadpool(
                    lambda: registry().invoke(principal, descriptor.name, args, shape="web")
                )
            except Exception as exc:
                return delivery_declared.refused(descriptor.name, exc)

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

        return api_evidence_asset

    return delivery_declared.router(
        ctx, ("delivery.story_dossier", "delivery.phase_dossier", "delivery.evidence_asset"),
        module=__name__, hand_written={"delivery.evidence_asset": asset_handler},
    )
