"""Shared helpers for the primitives routers (moved verbatim, HS-79-03)."""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.primitives")

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ── Run-response provenance: the canonical `source_type` vocabulary ──────────
#
# Every primitive `run` endpoint here returns a `sources` lineage list whose
# entries are `{"source_type": <canonical>, "source_ref": <id>}`. The hub is the
# canonical authority for this vocabulary. The pinned set (and what each means):
#
#   "agent"    — a saved Agent persona that produced/contributed to the output
#   "input"    — the run's input record (e.g. a meeting_id passed as source_ref)
#   "chain"    — the Chain (crew) a run executed
#   "workflow" — the Workflow a run executed
#
# A future change to any of these literals is a wire contract break for every
# surface that attaches lineage; `test_run_response_source_type_vocab_is_pinned`
# guards them.
#
# Aliases (tolerated, non-breaking): the iPad authoring port historically emits
# "card" for an input source (its canvas card == an input record). We accept that
# synonym and fold it to the canonical "input" via `canonical_source_type` so
# lineage from either surface lands on one stored vocabulary; nothing is rejected.
CANONICAL_SOURCE_TYPES: frozenset[str] = frozenset(
    {"recipe", "input", "chain", "workflow"}
)

# iPad / authoring-port synonyms → the canonical hub value (additive, tolerant).
# "agent" is the pre-rename word for a recipe (the v8 Recipe rename): older
# clients that still emit it fold to the canonical value, nothing rejected.
_SOURCE_TYPE_ALIASES: dict[str, str] = {"card": "input", "agent": "recipe"}


def canonical_source_type(raw: Any) -> str:
    """Fold a raw `source_type` to the canonical hub vocabulary.

    Canonical values pass through unchanged; known aliases (the iPad "card")
    map to their canonical form. Anything else is returned lowercased + stripped
    untouched (non-breaking: we never reject an unknown lineage tag, we just
    don't claim it is canonical).
    """
    val = str(raw or "").strip().lower()
    return _SOURCE_TYPE_ALIASES.get(val, val)


async def _json_body(request: Request) -> Optional[dict[str, Any]]:
    try:
        body = await request.json()
    except Exception:
        return None
    return body if isinstance(body, dict) else None


def _render_user_prompt(template: str, variables: dict[str, Any], user_input: str) -> str:
    """Render an agent's user_template.

    `{input}` is the primary slot for the runtime input; any `{name}` matching a
    provided variable is substituted. Unknown braces are left intact (a missing
    key never raises) so a persona authored elsewhere can't crash the hub.
    """
    if not template:
        return user_input
    mapping = dict(variables or {})
    mapping.setdefault("input", user_input)

    class _Safe(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    try:
        return template.format_map(_Safe(mapping))
    except Exception:
        # A malformed template (e.g. stray brace) → fall back to template + input.
        return f"{template}\n\n{user_input}".strip()


def _run_frame(
    ctx: "WebContext",
    state: str,
    *,
    kind: str,
    ref: str,
    name: str,
    error: str | None = None,
) -> None:
    """Broadcast one honest run frame (HS-74-02).

    Runs ride the SAME `intel_status` vocabulary the theater and the Queue
    HUD already consume (`running` reveals, `ready`/`error` settle), tagged
    `scope: "run"` so meeting-scoped consumers (the /live intel panel) can
    ignore them. The engine call is synchronous — there are no token frames
    to fake.
    """
    if ctx.broadcast is None:
        return
    try:
        frame: dict[str, Any] = {
            "state": state,
            "scope": "run",
            "capability": {"kind": kind, "id": ref, "name": name},
        }
        if error:
            frame["error"] = error
        ctx.broadcast("intel_status", frame)
    except Exception as exc:
        log.debug(f"run frame dropped: {exc}")


def _persist_run_artifact(
    *,
    kind: str,
    name: str,
    user_input: str,
    output: str,
    sources: list[dict[str, str]],
) -> Optional[str]:
    """Persist a run's output as a run-born artifact (v6, Phase 74).

    The result enters the ONE artifact store — it syncs, lands on the desk,
    and shows in the iPad's artifact review — instead of evaporating with
    the HTTP response. A persistence failure never eats a successful run:
    log and return None.
    """
    try:
        from ....db import get_database

        artifact_id = _new_id("artifact")
        head = " ".join(user_input.split())[:48]
        title = f"{name}: {head}" if head else f"{name} run"
        get_database().plugins.record_artifact(
            artifact_id=artifact_id,
            meeting_id="",
            artifact_type="run_output",
            title=title,
            body_markdown=str(output or ""),
            status="draft",
            plugin_id=f"{kind}_run",
            plugin_version="1",
            sources=sources,
        )
        return artifact_id
    except Exception as exc:
        log.error(f"Failed to persist run artifact: {exc}")
        return None


