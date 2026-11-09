"""PARKED 20261108 (evening, the unreached-routes census): routes no client calls.

Parked from ``holdspeak/web/routes/dictation/pipeline.py``: DELETE /api/dictation/corrections.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Dictation readiness + dry-run routes — HS-34-01 split of `dictation.py`.

`/api/dictation/readiness` and `/api/dictation/dry-run`. The dry-run path writes
detected project-doc suggestions into the shared store owned by
`build_dictation_router`, so it is passed in.
"""


import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ....db import get_observer
from ....logging_config import get_logger
from ....services.dictation_service import DictationService
from ...context import WebContext
from ._helpers import (
    _block_summary,
    _hotkey_custody,
    _open_text_entry,
    diff_text_correction,
    record_correction,
    teach_refusal_reason,
    _resolve_blocks_target,
    _resolve_project_context,
    _run_cancellable_entry,
    _run_dictation_dry_run_text,
    _runtime_readiness,
    session_terminal_of,
)

log = get_logger("web.routes.dictation")


#: HS-176-02 (R12/N1): the order the six target-override ids are offered in.
#: `auto` is NOT a member — it is meaningless as a correction and `_profile`
#: raises `KeyError` on it inside the live typing path.
_TARGET_OVERRIDE_ORDER = (
    "claude_code",
    "codex_cli",
    "terminal_shell",
    "browser",
    "editor",
    "chat",
)


def _target_override_options() -> list[dict[str, str]]:
    """The `target` correction's `[{id, label}]` pick list — six ids, no `auto`.

    The labels come from `_profile`'s own map (`target_profile.py:280-288`), the
    ONE source, so the face prints `Terminal shell` verbatim and no design-owned
    label table can drift from it (C12 note).
    """
    from ....target_profile import TARGET_PROFILE_OVERRIDE_OPTIONS, _profile

    offered = [pid for pid in _TARGET_OVERRIDE_ORDER if pid in TARGET_PROFILE_OVERRIDE_OPTIONS]
    # Anything the option set grows later is still offered (never `auto`).
    offered += sorted(
        TARGET_PROFILE_OVERRIDE_OPTIONS - set(_TARGET_OVERRIDE_ORDER) - {"auto"}
    )
    options: list[dict[str, str]] = []
    for pid in offered:
        try:
            label = _profile(pid, 0.0, "readiness", {}, details={}).label
        except Exception:  # pragma: no cover - the belt N1 pays in target_profile
            label = pid
        options.append({"id": pid, "label": str(label)})
    return options


def _teach(
    store: Any,
    kind: str,
    *,
    key: Optional[str] = None,
    value: Optional[str] = None,
    heard: Optional[str] = None,
    said: Optional[str] = None,
) -> dict[str, Any]:
    """Run the ruled teach for one correction kind. Writes AT MOST one row.

    HS-176-02 (R4). The ONE place both teach routes go through, so the refusal
    vocabulary and the stored-id linkage cannot drift between them. A refusal
    writes nothing and carries a named `reason`; an acceptance carries the
    stored row's `id`, `kind`, `key` and `value`.
    """
    if kind == "text":
        outcome = diff_text_correction(heard or "", said or "")
        rule = outcome["rule"]
        if rule is None:
            # `no_change` (heard == said) and `empty` write NOTHING — no
            # correction row, no `taught_from` flag, no id linkage.
            return {
                "recorded": False,
                "id": None,
                "kind": kind,
                "key": None,
                "value": None,
                "reason": str(outcome["reason"]),
            }
        key = str(rule["key"])
        value = str(rule["value"])

    clean_key = " ".join(str(key or "").split())
    clean_value = str(value or "").strip()
    recorded, correction_id, refusal = record_correction(
        store, kind, clean_key, clean_value
    )
    if not recorded:
        return {
            "recorded": False,
            "id": None,
            "kind": kind,
            "key": None,
            "value": None,
            # The store names its own refusal (`secret` / `one_word` / …); the
            # mirror only covers a store that predates that contract.
            "reason": refusal or teach_refusal_reason(kind, clean_key, clean_value),
        }
    return {
        "recorded": True,
        "id": correction_id,
        "kind": kind,
        "key": clean_key,
        "value": clean_value,
        "reason": None,
    }


def _teach_response(store: Any, kind: str, **kwargs: Any) -> Any:
    """`_teach` as the fallback route's body: `recorded` + `size` + the facts."""
    result = _teach(store, kind, **kwargs)
    body: dict[str, Any] = {"recorded": bool(result["recorded"]), "size": len(store)}
    if result["recorded"]:
        body.update(
            {
                "id": result["id"],
                "kind": result["kind"],
                "key": result["key"],
                "value": result["value"],
            }
        )
    else:
        body["reason"] = result["reason"]
    return JSONResponse(body)


def _log_detached_delivery(task: Any) -> None:
    """Record how a committed send finished after its client disconnected."""
    try:
        if task.cancelled():
            log.error("Remote dictation delivery task was cancelled after disconnect")
            return
        exc = task.exception()
    except Exception:  # pragma: no cover - defensive
        return
    if exc is not None:
        log.error(f"Remote dictation delivery failed after disconnect: {exc}")
    else:
        log.info("Remote dictation delivery completed after client disconnect")


def _speech_refusal(exc: Any) -> JSONResponse:
    """One named, content-free speech refusal on the wire (HS-131-15).

    The kernel's own safe reason is preserved verbatim rather than being rewritten
    into a generic failure, so the deck can name what happened and the owner can
    act on it. No transcript, prompt, or provider text ever rides along.
    """
    reason = str(getattr(exc, "reason", "") or "speech_session_not_admitted")
    return JSONResponse(
        {
            "error": reason,
            "refusal": reason,
            "failure_category": "speech_session_refused",
            "capability": str(getattr(exc, "capability", "") or ""),
            # A run that refused AND could not record its own terminal state is
            # two facts. The marker rides the exception from the entry owner.
            **session_terminal_of(exc),
        },
        status_code=422,
    )


def _speech_failure(exc: Any) -> JSONResponse:
    """One admitted provider attempt's safe failed outcome on the wire."""

    contract = str(getattr(exc, "contract", "") or "speech_provider")
    reason = str(getattr(exc, "reason", "") or "provider_failed")
    return JSONResponse(
        {
            "error": f"{contract}:{reason}",
            "failure_category": "speech_provider_failed",
            "contract": contract,
            "reason": reason,
            **session_terminal_of(exc),
        },
        status_code=502,
    )


# HS-112-02 — the kernel refusals that are known to have happened BEFORE any
# keystroke left the machine. They are deterministic and safe to make terminal:
# the room can name them ("no focus resolved") and the owner can simply speak
# again. Anything else (a driver that raised mid-type) stays ambiguous and is
# parked `pending` — an effect we cannot prove never replays itself.
PRE_EFFECT_REFUSALS = frozenset(
    {
        "desktop_focus_unresolved",
        "desktop_type_driver_unavailable",
        "desktop_type_claim_refused",
        "desktop_type_refused",
    }
)




def parked_build_pipeline_router(
    ctx: WebContext,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.delete("/api/dictation/corrections")
    def api_dictation_corrections_clear() -> Any:
        """HS-40-04: forget everything the copilot has learned (ring + durable)."""
        store = ctx.corrections
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        store.clear()
        return JSONResponse({"cleared": True, "size": len(store)})

    return router


def _journal_to_dict(record: Any) -> dict[str, Any]:
    """Serialize a `DictationJournalRecord` for the Journal UI (HS-45-02)."""
    return {
        "id": record.id,
        "created_at": record.created_at,
        "source": record.source,
        "transcript": record.transcript,
        "final_text": record.final_text,
        "project_root": record.project_root,
        "intent": record.intent,
        "block_id": record.block_id,
        "target_profile": record.target_profile,
        "stage_ms": record.stage_ms,
        "total_ms": record.total_ms,
        "rewrite_pass_ms": record.rewrite_pass_ms,
        "confidence": record.confidence,
        "warnings": record.warnings,
        "corrected": record.corrected,
        "correction_id": record.correction_id,
        # HS-176-02 (R5): the two stored facts, split and both named.
        # `taught_from` is the existing `corrected` column under its true
        # meaning — "he taught FROM this row"; `corrections_applied` is the new
        # per-run fact — "these stored rules fired ON this row".
        "taught_from": bool(record.corrected),
        "corrections_applied": [
            int(x) for x in (getattr(record, "corrections_applied", None) or [])
        ],
    }
