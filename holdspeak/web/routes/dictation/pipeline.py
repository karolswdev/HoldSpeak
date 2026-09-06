"""Dictation readiness + dry-run routes — HS-34-01 split of `dictation.py`.

`/api/dictation/readiness` and `/api/dictation/dry-run`. The dry-run path writes
detected project-doc suggestions into the shared store owned by
`build_dictation_router`, so it is passed in.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....db import get_observer
from ....logging_config import get_logger
from ....services.dictation_service import DictationService
from ...context import WebContext
from ._helpers import (
    _block_summary,
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


def build_pipeline_router(
    ctx: WebContext,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
) -> APIRouter:
    router = APIRouter()
    dictation_service = (
        ctx.dictation_service
        if isinstance(ctx.dictation_service, DictationService)
        else DictationService(
            journal_repository=getattr(ctx.journal, "repository", None),
            journal_available=ctx.journal is not None,
            delivery_repository=ctx.dictation_deliveries,
            observer=get_observer(),
        )
    )

    @router.get("/api/dictation/readiness")
    async def api_dictation_readiness(project_root: Optional[str] = None) -> Any:
        """Return one browser-facing readiness snapshot for dictation setup."""
        from ....agent_context import get_recent_agent_session
        from ....config import Config
        from ....plugins.dictation.project_kb import ProjectKBError, kb_path_for, read_project_kb
        from ....target_profile import detect_active_target_profile, detect_target_profile_with_override

        config_snapshot = Config.load()
        cfg = config_snapshot.dictation
        warnings: list[dict[str, Any]] = []

        project: Optional[dict[str, Any]]
        project_error: Optional[str] = None
        try:
            project = _resolve_project_context(project_root)
        except ValueError as exc:
            if project_root:
                return JSONResponse({"error": str(exc)}, status_code=400)
            project = None
            project_error = str(exc)

        global_path, _ = _resolve_blocks_target("global")
        global_blocks = _block_summary(global_path)

        project_blocks: Optional[dict[str, Any]] = None
        project_root_path: Optional[Path] = None
        if project is not None:
            project_root_path = Path(project["root"])
            project_blocks = _block_summary(project_root_path / ".holdspeak" / "blocks.yaml")

        resolved_blocks = (
            project_blocks
            if project_blocks is not None and project_blocks["exists"]
            else global_blocks
        )
        resolved_scope = (
            "project"
            if project_blocks is not None and project_blocks["exists"]
            else "global"
        )

        kb_payload: dict[str, Any] = {
            "path": None,
            "exists": False,
            "valid": True,
            "keys": [],
            "error": None,
        }
        if project_root_path is not None:
            kb_path = kb_path_for(project_root_path)
            kb_payload["path"] = str(kb_path)
            kb_payload["exists"] = kb_path.exists()
            try:
                kb = read_project_kb(project_root_path)
                kb_payload["keys"] = sorted((kb or {}).keys())
            except ProjectKBError as exc:
                kb_payload["valid"] = False
                kb_payload["error"] = str(exc)

        # HS-47-04: the `.hs/` context existence, so the discovery nudge can tell
        # "this project has no knowledge yet" (no KB and no context) without a new
        # detection path.
        hs_context_payload: dict[str, Any] = {"path": None, "exists": False}
        if project_root_path is not None:
            hs_dir = project_root_path / ".hs"
            hs_context_payload["path"] = str(hs_dir)
            hs_context_payload["exists"] = hs_dir.is_dir()

        runtime_payload = _runtime_readiness(cfg)
        from ....db import get_database
        from ....speech_session import configured_pipeline_egress_boundary

        egress_boundary = configured_pipeline_egress_boundary(
            config_snapshot, get_database()
        )
        try:
            target_payload = detect_active_target_profile(
                cfg.pipeline.target_profile_override
            ).to_dict()
        except Exception:
            target_payload = detect_target_profile_with_override(
                {},
                cfg.pipeline.target_profile_override,
            ).to_dict()
        # HS-176-02 (R12/N1): the label source for a `target` correction. The
        # face renders labels; the wire carries ids. SIX ids —
        # `TARGET_PROFILE_OVERRIDE_OPTIONS` minus `auto`, which is meaningless
        # as a correction and raises `KeyError` inside `_profile` on the live
        # typing path. The labels are read from `_profile`'s own map, so there
        # is no second, drifting label table (C12 note).
        target_payload["overrides"] = _target_override_options()
        agent_hooks_payload: dict[str, Any] = {}
        for agent in ("claude", "codex"):
            latest = get_recent_agent_session(agent=agent, max_age_seconds=7 * 24 * 60 * 60)
            agent_hooks_payload[agent] = {
                "fresh": latest is not None,
                "latest_session": latest.to_dict() if latest else None,
            }

        if not cfg.pipeline.enabled:
            warnings.append({
                "code": "pipeline_disabled",
                "message": "Dictation pipeline is disabled.",
                "action": "Enable the dictation pipeline from Runtime.",
                "section": "runtime",
                "runtime_action": "enable_pipeline",
            })
        if project is None:
            warnings.append({
                "code": "no_project",
                "message": project_error or "No project root detected.",
                "action": "Set a project root override or launch holdspeak from a project directory.",
                "section": "readiness",
            })
        if not resolved_blocks["exists"] or int(resolved_blocks["count"]) == 0:
            warnings.append({
                "code": "no_blocks",
                "message": "No dictation blocks are loaded for the selected project.",
                "action": "Create the Action item starter and run its sample.",
                "section": "blocks",
                "template_id": "action_item",
                "template_action": "create_dry_run",
                "template_scope": "project" if project is not None else "global",
            })
        if not global_blocks["valid"] or (project_blocks is not None and not project_blocks["valid"]):
            warnings.append({
                "code": "invalid_blocks",
                "message": "A blocks.yaml file is invalid.",
                "action": "Open Blocks and fix the validation error.",
                "section": "blocks",
            })
        if project is not None and not kb_payload["exists"]:
            warnings.append({
                "code": "missing_project_kb",
                "message": "Project KB file is missing.",
                "action": "Create a starter Project KB file.",
                "section": "kb",
                "kb_action": "create_starter",
            })
        if not kb_payload["valid"]:
            warnings.append({
                "code": "invalid_project_kb",
                "message": "Project KB file is invalid.",
                "action": "Open Project KB and fix the validation error.",
                "section": "kb",
            })
        if runtime_payload["status"] == "unavailable":
            warnings.append({
                "code": "runtime_unavailable",
                "message": runtime_payload["detail"],
                "action": "Install the selected runtime extra or change backend.",
                "section": "runtime",
                "guidance": runtime_payload.get("guidance"),
            })
        elif runtime_payload["status"] == "missing_model":
            warnings.append({
                "code": "runtime_model_missing",
                "message": runtime_payload["detail"],
                "action": "Download the model or update the runtime model path.",
                "section": "runtime",
                "guidance": runtime_payload.get("guidance"),
            })

        ready = (
            cfg.pipeline.enabled
            and project is not None
            and bool(resolved_blocks["valid"])
            and int(resolved_blocks["count"]) > 0
            and bool(kb_payload["valid"])
            and runtime_payload["status"] == "available"
        )

        # HS-39-05: depth telemetry — per-stage latency quantiles + budget
        # guidance + multi-pass timings + correction-store state.
        from ....dictation_telemetry import build_depth_readiness

        telemetry_store = ctx.telemetry
        corrections_store = ctx.corrections
        depth_payload = build_depth_readiness(
            stage_quantiles=telemetry_store.stage_quantiles() if telemetry_store is not None else {},
            rewrite_pass_ms=telemetry_store.latest_rewrite_pass_ms() if telemetry_store is not None else [],
            run_count=len(telemetry_store) if telemetry_store is not None else 0,
            budget_ms=cfg.pipeline.max_total_latency_ms,
            corrections_enabled=bool(getattr(cfg.pipeline, "corrections_enabled", False)),
            corrections_size=len(corrections_store) if corrections_store is not None else 0,
            corrections_recent=(
                [c.key for c in corrections_store.recent(limit=5)]
                if corrections_store is not None
                else []
            ),
        )

        return JSONResponse(
            {
                "ready": ready,
                "project": project,
                "egress_boundary": egress_boundary,
                "config": {
                    "pipeline_enabled": cfg.pipeline.enabled,
                    "max_total_latency_ms": cfg.pipeline.max_total_latency_ms,
                    "backend": cfg.runtime.backend,
                },
                "blocks": {
                    "global": global_blocks,
                    "project": project_blocks,
                    "resolved_scope": resolved_scope,
                    "resolved": resolved_blocks,
                },
                "project_kb": kb_payload,
                "project_context": hs_context_payload,
                "runtime": runtime_payload,
                "telemetry": runtime_payload.get("telemetry"),
                "depth": depth_payload,
                "target": target_payload,
                "agent_hooks": agent_hooks_payload,
                "warnings": warnings,
            }
        )

    @router.post("/api/dictation/dry-run")
    async def api_dictation_dry_run(request: Request, payload: dict[str, Any]) -> Any:
        utterance = payload.get("utterance") if isinstance(payload, dict) else None
        if not isinstance(utterance, str):
            return JSONResponse(
                {
                    "error": "utterance must be a string",
                    "detail": {"utterance": "required string"},
                },
                status_code=400,
            )
        text = utterance.strip()
        if not text:
            return JSONResponse(
                {
                    "error": "utterance must not be empty",
                    "detail": {"utterance": "must not be empty"},
                },
                status_code=400,
            )
        project_root_override = payload.get("project_root") if isinstance(payload, dict) else None
        if project_root_override is not None and not isinstance(project_root_override, str):
            return JSONResponse(
                {
                    "error": "project_root must be a string when provided",
                    "detail": {"project_root": "optional string path"},
                },
                status_code=400,
            )
        target_hints = payload.get("target") if isinstance(payload, dict) else None
        if target_hints is not None and not isinstance(target_hints, dict):
            return JSONResponse(
                {
                    "error": "target must be an object when provided",
                    "detail": {"target": "optional object of app/window/process hints"},
                },
                status_code=400,
            )

        # HS-131-15: the rehearsal runs the FULL configured pipeline, so it opens
        # ONE fresh `dictation.session` derived from the middleware principal —
        # never the payload, never the open-mic interval — before any runtime is
        # constructed. Off the event loop: a mesh-routed rewrite WAITS on the
        # relay queue, and THIS loop must serve the worker's claim polls.
        def _work(config_snapshot: Any, entry: Any) -> dict[str, Any]:
            return _run_dictation_dry_run_text(
                text,
                project_root_override,
                target_hints,
                suggestions=project_doc_suggestions,
                config_snapshot=config_snapshot,
                admission=None if entry is None else entry.provider,
                fence=None if entry is None else entry.fence,
                terminal_entry=entry,
                corrections=ctx.corrections,
                dismissed_signatures=dismissed_signatures,
                telemetry=ctx.telemetry,
                journal=ctx.journal,
            )

        from ....speech_session import (
            AIM_BROWSER_REHEARSE,
            SpeechProviderFailure,
            SpeechSessionRefused,
        )

        try:
            return JSONResponse(
                await _run_cancellable_entry(request, AIM_BROWSER_REHEARSE, _work)
            )
        except SpeechSessionRefused as exc:
            return _speech_refusal(exc)
        except SpeechProviderFailure as exc:
            log.error(f"Dictation dry-run provider failed: {exc.contract}:{exc.reason}")
            return _speech_failure(exc)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            log.error(f"Dictation dry-run failed: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

    @router.post("/api/dictation/remote")
    async def api_dictation_remote(request: Request, payload: dict[str, Any]) -> Any:
        """HSM-13-01 — accept a dictated answer from a companion client (iPhone/iPad),
        run it through the rich dictation pipeline (corrections/blocks/plugins), and
        deliver it into the desktop's dictation target / AI PI path.

        Auth: gated by the runtime's web-auth middleware (``Authorization: Bearer``)
        exactly like every other route when bound off-loopback — the companion client
        mirrors the server's ``web_auth_token`` on every request. Delivery is
        deliver-on-command (the client user pressed send); there is no autonomous path.

        HS-112-02 — this is ALSO the Speak room's wire. The room named Speak holds
        TALK, releases, and posts the transcript here: one delivery contract, one
        pipeline, one journal, one idempotency claim, whoever is holding the key.
        Two things the room needs and the companion never asked for:

        * ``require_agent`` — an aimed AGENT delivery refuses honestly when nothing
          is awaiting rather than silently free-typing into whatever happens to be
          focused. Absent/false keeps the companion's fallback byte-identical.
        * a deterministic kernel refusal (``desktop_focus_unresolved`` and friends)
          comes back as a NAMED terminal refusal the deck renders in-flow, instead
          of an ambiguous "pending" the owner cannot act on.
        """
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str) or not text.strip():
            return JSONResponse({"error": "text must be a non-empty string"}, status_code=400)
        text = text.strip()
        target_hints = payload.get("target") if isinstance(payload, dict) else None
        if target_hints is not None and not isinstance(target_hints, dict):
            return JSONResponse(
                {"error": "target must be an object when provided"}, status_code=400
            )
        # HSM-15-01a: the delivery target mode. "agent" (default) answers the
        # waiting coder exactly as before (byte-identical); "focused" free-types
        # the processed text into whatever Mac app is focused, with no awaiting
        # coder session required.
        target_mode = payload.get("target_mode") if isinstance(payload, dict) else None
        if target_mode is None:
            target_mode = "agent"
        if target_mode not in ("agent", "focused"):
            return JSONResponse(
                {"error": 'target_mode must be one of "agent" or "focused"'},
                status_code=400,
            )
        # HS-112-02: an AIMED agent delivery. The Speak room's AGENT aim means
        # "the awaiting agent, or nothing" — the desktop fallback is a companion
        # convenience, not an aim.
        require_agent = bool(payload.get("require_agent")) if isinstance(payload, dict) else False

        # HS-93-05: new companion clients choose a stable id before sending.
        # Claim it before pipeline/macro/delivery work so reconnect retries can
        # read the original terminal response without repeating the effect.
        delivery_id_value = payload.get("delivery_id") if isinstance(payload, dict) else None
        delivery_id = ""
        delivery_service = dictation_service
        principal = getattr(request.state, "principal", None)
        if delivery_id_value is None:
            # A remote send becomes committed work: it may outlive this HTTP
            # connection. Without a client-stable claim there is no honest retry
            # answer and a reconnect can type the same effect twice.
            return JSONResponse(
                {
                    "error": "delivery_id is required for committed remote delivery",
                    "error_code": "delivery_id_required",
                    "failure_category": "delivery_conflict",
                },
                status_code=400,
            )
        if not isinstance(delivery_id_value, str) or not delivery_id_value.strip():
            return JSONResponse(
                {"error": "delivery_id must be a non-empty identifier"},
                status_code=400,
            )
        delivery_id = delivery_id_value.strip()
        request_shape = {
            "text": text,
            "target": target_hints,
            "target_mode": target_mode,
            "raw": bool(payload.get("raw")),
            "require_agent": require_agent,
        }
        request_hash = hashlib.sha256(
            json.dumps(
                request_shape, separators=(",", ":"), sort_keys=True
            ).encode("utf-8")
        ).hexdigest()
        try:
            claim = delivery_service.claim_delivery(
                principal, delivery_id, request_hash=request_hash
            )
        except ValueError as exc:
            return JSONResponse(
                {
                    "error": str(exc),
                    "failure_category": "delivery_conflict",
                    "delivery_id": delivery_id,
                },
                status_code=409,
            )
        claim_state = claim.get("claim_state")
        if claim_state in {"succeeded", "failed"}:
            cached = dict(claim.get("response") or {})
            cached["delivery_id"] = delivery_id
            cached["deduplicated"] = True
            return JSONResponse(
                cached,
                status_code=int(claim.get("response_status") or 200),
            )
        if claim_state == "pending":
            return JSONResponse(
                {
                    "error": "Delivery is still pending. The draft remains on the sending device; retry this delivery id.",
                    "error_code": "delivery_pending",
                    "failure_category": "delivery_conflict",
                    "delivery_id": delivery_id,
                },
                status_code=425,
            )

        def terminal_response(
            body: dict[str, Any], *, status_code: int = 200
        ) -> JSONResponse:
            response_body = dict(body)
            if delivery_id:
                response_body["delivery_id"] = delivery_id
                response_body["deduplicated"] = False
                try:
                    if 200 <= status_code < 300:
                        delivery_service.complete_delivery(
                            principal,
                            delivery_id,
                            response_status=status_code,
                            response=response_body,
                        )
                    else:
                        delivery_service.fail_delivery(
                            principal,
                            delivery_id,
                            response_status=status_code,
                            response=response_body,
                            error=str(response_body.get("error") or "delivery failed"),
                        )
                except Exception as exc:  # pragma: no cover - defensive persistence fault
                    log.error(f"Remote dictation receipt persistence failed: {exc}")
                    return JSONResponse(
                        {
                            "error": "Delivery outcome could not be recorded. The draft remains on the sending device. Send again to retry.",
                            "error_code": "delivery_pending",
                            "failure_category": "delivery_conflict",
                            "delivery_id": delivery_id,
                        },
                        status_code=425,
                    )
            return JSONResponse(response_body, status_code=status_code)

        def uncertain_delivery(
            body: dict[str, Any], *, legacy_status: int = 502
        ) -> JSONResponse:
            """Refuse to replay an effect whose hook outcome is ambiguous."""
            if not delivery_id:
                return JSONResponse(body, status_code=legacy_status)
            pending = dict(body)
            pending.update(
                {
                    "error_code": "delivery_pending",
                    "failure_category": "delivery_conflict",
                    "delivery_id": delivery_id,
                    "deduplicated": False,
                }
            )
            # Deliberately leave the pre-effect claim in `pending`. A retry of
            # this id reads that state and never invokes the hook again.
            return JSONResponse(pending, status_code=425)

        def refusal_response(
            reason: str, *, final_text: str = "", session: Any = None
        ) -> JSONResponse:
            """A named, terminal refusal — nothing was typed, say so plainly.

            ``session`` carries the speech entry (or the exception that came from
            it) so a refusal whose parent close ALSO could not be recorded reports
            both facts rather than the first one only.
            """
            return terminal_response(
                {
                    "error": reason,
                    "refusal": reason,
                    "failure_category": "delivery_refused",
                    "delivered": False,
                    "final_text": final_text,
                    **session_terminal_of(session),
                },
                status_code=422,
            )

        def deliver(
            body_text: str, *, terminal_entry: Any = None
        ) -> tuple[bool, dict[str, Any] | None, JSONResponse | None]:
            """Run the ONE delivery hook. Returns (delivered, receipt, refusal).

            HS-112-02: the two call sites (raw + processed) share this so the
            room and the companion cannot drift apart on how a refusal reads.
            When a provider-backed remote entry is supplied, settle its honest
            terminal outcome before constructing the response and before the
            caller releases the speech/effect handoff election.
            """
            from ....desktop_typing import DesktopTypeRefused

            if ctx.on_remote_dictation is None:
                if terminal_entry is not None:
                    terminal_entry.close("succeeded")
                return False, None, None
            try:
                if target_mode == "agent":
                    # Byte-identical to the pre-15 call (a plain str hook): the
                    # default path never threads the new keyword.
                    outcome = ctx.on_remote_dictation(body_text)
                else:
                    outcome = ctx.on_remote_dictation(body_text, target=target_mode)
            except DesktopTypeRefused as exc:
                if str(exc.reason) in PRE_EFFECT_REFUSALS:
                    if terminal_entry is not None:
                        terminal_entry.close("refused")
                    return (
                        False,
                        None,
                        refusal_response(
                            str(exc.reason),
                            final_text=body_text,
                            session=terminal_entry,
                        ),
                    )
                log.error(f"Remote dictation delivery refused mid-effect: {exc}")
                if terminal_entry is not None:
                    terminal_entry.close("failed")
                return (
                    False,
                    None,
                    uncertain_delivery(
                        {
                            "error": f"delivery failed: {exc}",
                            "final_text": body_text,
                            "delivered": False,
                            **session_terminal_of(terminal_entry),
                        },
                    ),
                )
            except Exception as exc:
                log.error(f"Remote dictation delivery failed: {exc}")
                if terminal_entry is not None:
                    terminal_entry.close("failed")
                return (
                    False,
                    None,
                    uncertain_delivery(
                        {
                            "error": f"delivery failed: {exc}",
                            "final_text": body_text,
                            "delivered": False,
                            **session_terminal_of(terminal_entry),
                        },
                    ),
                )
            receipt = dict(outcome) if isinstance(outcome, dict) else None
            if terminal_entry is not None:
                terminal_entry.close("succeeded")
            return True, receipt, None

        # ── everything below is COMMITTED work (HS-131-15) ───────────────────
        # The idempotency claim above was ACCEPTED: the user pressed send and the
        # hub took responsibility for it. A phone that walks out of Wi-Fi is not a
        # revocation of that decision, so the remainder runs in a shielded task
        # and continues to a terminal delivery claim even if this HTTP request is
        # cancelled. (Explicit session expiry or revocation before the delivery
        # gate still refuses — see the pre-delivery election below.)
        async def _committed_send() -> JSONResponse:
            # HS-112-02 — the aimed-agent refusal, decided BEFORE any pipeline or
            # effect work: no awaiting agent means no delivery, named in one word.
            if require_agent and target_mode == "agent":
                from ....agent_context import get_recent_awaiting_agent_session

                try:
                    awaiting = get_recent_awaiting_agent_session(max_age_seconds=120)
                except Exception as exc:  # pragma: no cover - defensive probe
                    log.warning(f"Awaiting-agent probe failed: {exc}")
                    awaiting = None
                if awaiting is None:
                    return refusal_response("no_awaiting_agent")

            # HSM-18-01 — verbatim delivery for a client holding a dry-run receipt.
            # A previewed `final_text` has already been through the pipeline; running
            # it again would make the receipt a lie (the rewrite is not idempotent).
            # `raw: true` types EXACTLY the given text: no pipeline, no macro
            # dispatch. Absent/false -> the paths below run byte-identical.
            if bool(payload.get("raw")):
                delivered, receipt, refused = deliver(text)
                if refused is not None:
                    return refused
                body: dict[str, Any] = {
                    "success": True,
                    "final_text": text,
                    "delivered": delivered,
                }
                if receipt is not None:
                    body["delivery"] = receipt
                return terminal_response(body)

            # HSM-18-02 — voice command macros must fire on the remote relay too, exactly
            # as they do on the local dictation path (dictation_capture._maybe_dispatch_
            # voice_command). A configured, enabled macro keyword is NOT dictated as prose;
            # it fires through the same bounded, guarded connector and returns a "fired"
            # result the companion renders as the macro-object chip (the Phase-18 signature
            # moment). Off by default: macros disabled -> dispatch returns None -> the
            # normal dictation path below runs, byte-identical to before this fix.
            from ....config import Config
            from ....dictation_runner import dispatch_voice_command

            def _remote_type(t: str) -> None:
                # a `type_text` macro free-types into the focused Mac app via the proven
                # focused-delivery relay; if nothing can deliver, the macro still fires its
                # action, it just cannot type.
                if ctx.on_remote_dictation is None:
                    raise RuntimeError("voice_macro_direct_gesture_required")
                ctx.on_remote_dictation(t, target="focused")

            config_snapshot = Config.load()
            try:
                fired = dispatch_voice_command(
                    text, config=config_snapshot, type_writer=_remote_type
                )
            except Exception as exc:  # a macro failure must never block plain dictation
                log.error(f"Remote voice-command dispatch failed: {exc}")
                fired = None
            if fired is not None and fired.handled:
                return terminal_response(
                    {
                        "success": True,
                        "fired": {
                            "keyword": fired.keyword,
                            "kind": fired.kind,
                            "preview": fired.preview,
                            "ok": fired.ok,
                            "error": fired.error,
                        },
                        "delivered": fired.ok,
                        "final_text": "",
                    }
                )

            # HSM-18-05 — the pre-briefing loop closes on the REMOTE lane too, exactly
            # as it does in the local runner (HS-53-07): a "Dictate with this" tap
            # parked a record id; consume it (one-shot, recency-bounded) and fold the
            # activity context in so the rewrite grounds in the selected record. This
            # was the third silent relay hole of the audit's pattern: the pin existed,
            # the local path consumed it, and the remote path never did. No pending
            # pin -> activity_context is None -> byte-identical to before this fix.
            activity_context = None
            try:
                from ....activity_context import build_activity_context
                from ....dictation_selection import consume_selected_record

                selected_record_id = consume_selected_record()
                if selected_record_id is not None:
                    activity_context = build_activity_context(
                        limit=20, refresh=False, selected_record_id=selected_record_id
                    ).to_dict()
            except Exception as exc:
                log.warning(f"Remote dictation activity grounding unavailable: {exc}")

            # Reuse the exact rich-pipeline path the browser dry-run uses, so the same
            # corrections/blocks/plugins apply — the answer is as smart as one spoken at
            # the desk, not raw transcript.
            #
            # HS-131-15: the processing is real classify/rewrite work, so it runs
            # under its OWN fresh `dictation.session` derived from the SAME
            # middleware principal that took the delivery claim. It never borrows
            # the browser's open-mic authority, and it encloses the provider work
            # right through the final pre-delivery gate.
            from ....speech_session import (
                AIM_REMOTE_DELIVERY,
                SpeechProviderFailure,
                SpeechSessionRefused,
                pipeline_provider_capabilities,
            )

            # `None` until admission succeeds, so the failure paths below can tell
            # "never admitted" from "admitted, then could not record its end".
            entry = None
            final_text = text
            # HS-176 counsel C1: the run's own facts, kept so the terminal body
            # can carry the SAME three keys the dry-run reply carries
            # (`raw_text`, `corrections_applied`, `journal_id`). The deck reads
            # all three off one `result` object (`useSpeakDeck.ts:161,166,443`),
            # so a delivery that omitted them left the APPLIED chip blank, the
            # TEXT teach well pre-filled from the LANDED text, and `teach()` on
            # the corrections fallback instead of the journal route.
            processed: Any = None
            try:
                def _run_text(owned: Any) -> Any:
                    return _run_dictation_dry_run_text(
                        text,
                        None,
                        target_hints,
                        suggestions=project_doc_suggestions,
                        config_snapshot=config_snapshot,
                        admission=None if owned is None else owned.provider,
                        fence=None if owned is None else owned.fence,
                        corrections=ctx.corrections,
                        dismissed_signatures=dismissed_signatures,
                        telemetry=ctx.telemetry,
                        journal=ctx.journal,
                        activity_context=activity_context,
                        # HS-112-02: a delivery is a dictation, not a rehearsal. The
                        # journal now shows the room's and the companion's utterances
                        # beside the hotkey's, same schema; `dry_run` is reserved for
                        # the explicit REHEARSE preview.
                        journal_source="dictation",
                    )

                if not pipeline_provider_capabilities(config_snapshot):
                    processed = await asyncio.to_thread(_run_text, None)
                    final_text = (
                        processed.get("final_text", text)
                        if isinstance(processed, dict)
                        else text
                    )
                    delivered, receipt, refused = deliver(final_text)
                else:
                    # Inside the try on purpose: admission itself can refuse (no
                    # principal, no plan, a capability this configuration needs and
                    # the registry cannot resolve), and a refusal owes the sender a
                    # NAMED terminal response — never an unhandled 500 that leaves the
                    # accepted claim without an outcome.
                    config_snapshot, entry = _open_text_entry(
                        request,
                        AIM_REMOTE_DELIVERY,
                        config_snapshot=config_snapshot,
                    )
                    with entry:
                        processed = await asyncio.to_thread(_run_text, entry)
                        final_text = (
                            processed.get("final_text", text)
                            if isinstance(processed, dict)
                            else text
                        )
                        # The last gate before the effect. An explicit expiry or
                        # revocation that landed while the model was working still
                        # refuses here; past it, the existing delivery operation and
                        # its receipt own the typing effect, and this fence never
                        # becomes a second delivery record.
                        cleared, delivery = entry.fence.publish(
                            "remote pre-delivery handoff",
                            lambda: deliver(final_text, terminal_entry=entry),
                        )
                        if not cleared:
                            # Escape the context manager so the parent records the
                            # same named refusal returned to the sender. Returning
                            # normally here would falsely close it ``succeeded``.
                            raise SpeechSessionRefused(
                                entry.fence.reason() or "speech_session_not_live"
                            )
                        assert delivery is not None
                        delivered, receipt, refused = delivery
            except SpeechSessionRefused as exc:
                reason = str(getattr(exc, "reason", "") or "speech_session_not_admitted")
                log.error(f"Remote dictation refused: {reason}")
                return refusal_response(reason, final_text=final_text, session=entry)
            except SpeechProviderFailure as exc:
                log.error(f"Remote dictation provider failed: {exc.contract}:{exc.reason}")
                return terminal_response(
                    {
                        "error": f"{exc.contract}:{exc.reason}",
                        "delivered": False,
                        **session_terminal_of(entry),
                    },
                    status_code=502,
                )
            except Exception as exc:
                log.error(f"Remote dictation pipeline failed: {exc}")
                return terminal_response(
                    {"error": str(exc), **session_terminal_of(entry)},
                    status_code=500,
                )

            if refused is not None:
                return refused
            body = {"success": True, "final_text": final_text, "delivered": delivered}
            # C1: the loop's three facts, from the run that already computed
            # them — never recomputed, never a read-time guess. Absent when the
            # run produced no dict (a `raw: true` verbatim send returns above
            # and never reaches here).
            if isinstance(processed, dict):
                body["raw_text"] = processed.get("raw_text", text)
                body["corrections_applied"] = [
                    int(x) for x in (processed.get("corrections_applied") or [])
                ]
                body["journal_id"] = processed.get("journal_id")
            if receipt is not None:
                body["delivery"] = receipt
            if entry is not None and entry.indeterminate:
                # The typing effect either happened or it did not, and the
                # delivery receipt above is the record of THAT. An unknown
                # terminal state on the speech parent is a separate, lesser fact,
                # so it is reported beside the delivery instead of demoting a
                # known-typed effect into a pre-effect failure.
                body["session_terminal"] = "indeterminate"
            return terminal_response(body)

        task = asyncio.ensure_future(_committed_send())
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # The client is gone; the send is not. Let the task finish writing its
            # terminal delivery claim so a retry of this id reads the real outcome
            # instead of replaying an effect that already happened.
            task.add_done_callback(_log_detached_delivery)
            raise

    @router.get("/api/dictation/corrections")
    async def api_dictation_corrections_list() -> Any:
        from ....config import Config
        from ....plugins.dictation.corrections import CORRECTION_KINDS

        store = ctx.corrections
        cfg = Config.load().dictation
        items = store.list_for_display() if store is not None else []
        # HS-176-02 (R3): `applied` is a REAL count — the number of retained
        # journal rows whose stored `corrections_applied` names this rule, i.e.
        # the times it actually fired. It replaces HS-48-02's `similar`
        # (`reach_for_gist`), which counted *similar transcripts* — including
        # the teaching utterance itself, so a brand-new correction read
        # `1 APPLIED` meaning zero applications. `reach_for_gist` stays in the
        # learning digest and appears on no face.
        #
        # C3 note: this counts the RETAINED journal, so it can go DOWN as rows
        # age out (the recorder prunes to `journal_retention`, default 500).
        counts = _applied_counts()
        for item in items:
            try:
                correction_id = int(item.get("id"))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                item["applied"] = 0
                continue
            item["applied"] = int(counts.get(correction_id, 0))
        return JSONResponse(
            {
                "enabled": bool(getattr(cfg.pipeline, "corrections_enabled", False)),
                "kinds": list(CORRECTION_KINDS),
                "size": len(store) if store is not None else 0,
                "items": items,
            }
        )

    @router.get("/api/dictation/learning-digest")
    async def api_dictation_learning_digest(window: str = "week") -> Any:
        """HS-48-01: a read-only "What HoldSpeak learned" aggregation.

        Reads the correction memory + the journal and returns honest, windowed
        counts: corrections made, dictations corrected, the by-kind / by-block /
        by-target breakdown, and a real "learned from N similar" per correction.
        The "N similar" is the same Jaccard matcher that nudges routing, so the
        reported reach is exactly what the live pipeline would nudge. No writes.
        """
        from ....config import Config
        from ....dictation_learning import build_learning_digest

        cfg = Config.load().dictation
        store = ctx.corrections
        corrections = store.list_for_display() if store is not None else []
        repo = _journal_repo()
        journal_rows = (
            [
                {
                    "transcript": r.transcript,
                    "created_at": r.created_at,
                    "corrected": r.corrected,
                }
                for r in repo.recent()
            ]
            if repo is not None
            else []
        )
        digest = build_learning_digest(
            corrections=corrections,
            journal_rows=journal_rows,
            window=window,
            enabled=bool(getattr(cfg.pipeline, "corrections_enabled", False)),
        )
        return JSONResponse(digest)

    @router.post("/api/dictation/corrections")
    async def api_dictation_corrections_record(payload: dict[str, Any]) -> Any:
        """Teach one correction (the fallback route — no journal row to attach).

        Request:
        - routing kinds (`intent` / `target`): ``{"kind", "text", "value"}`` —
          `text` is the gist the rule applies to, `value` the block id / target
          profile id. Unchanged since HS-39-02.
        - the `text` kind (HS-176-02): ``{"kind": "text", "heard", "said"}`` —
          what the mic heard and what he said. `text` is accepted as an alias
          for `heard` and `value` for `said`, so the existing shape still works.
          The server runs the word-level diff (`diff_text_correction`) and
          stores the rule the diff yields; the face sends no key/value.

        Response: ``{"recorded", "size"}`` always, plus the stored
        ``{"id", "kind", "key", "value"}`` when something was written, or a
        named ``"reason"`` when nothing was (R4: `recorded` is the ONE key the
        face reads on both teach routes).
        """
        from ....plugins.dictation.corrections import CORRECTION_KINDS

        store = ctx.corrections
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        kind = payload.get("kind") if isinstance(payload, dict) else None
        text = payload.get("text") if isinstance(payload, dict) else None
        value = payload.get("value") if isinstance(payload, dict) else None
        heard = payload.get("heard") if isinstance(payload, dict) else None
        said = payload.get("said") if isinstance(payload, dict) else None
        if kind not in CORRECTION_KINDS:
            return JSONResponse(
                {"error": f"kind must be one of {list(CORRECTION_KINDS)}"}, status_code=400
            )
        if kind == "text":
            heard = heard if isinstance(heard, str) else text
            said = said if isinstance(said, str) else value
            if not isinstance(heard, str) or not heard.strip():
                return JSONResponse(
                    {"error": "heard must be a non-empty string"}, status_code=400
                )
            if not isinstance(said, str) or not said.strip():
                return JSONResponse(
                    {"error": "said must be a non-empty string"}, status_code=400
                )
            return _teach_response(store, "text", heard=heard, said=said)
        if not isinstance(text, str) or not text.strip():
            return JSONResponse({"error": "text must be a non-empty string"}, status_code=400)
        if not isinstance(value, str) or not value.strip():
            return JSONResponse({"error": "value must be a non-empty string"}, status_code=400)
        return _teach_response(store, kind, key=text, value=value)

    @router.delete("/api/dictation/corrections/{correction_id}")
    async def api_dictation_corrections_delete(correction_id: int) -> Any:
        """HS-40-04: remove one persistent correction by id (curate the memory)."""
        store = ctx.corrections
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        if store.remove(correction_id):
            return JSONResponse({"removed": True, "size": len(store)})
        return JSONResponse({"removed": False, "error": "correction not found"}, status_code=404)

    @router.delete("/api/dictation/corrections")
    async def api_dictation_corrections_clear() -> Any:
        """HS-40-04: forget everything the copilot has learned (ring + durable)."""
        store = ctx.corrections
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        store.clear()
        return JSONResponse({"cleared": True, "size": len(store)})

    # ── HS-45-02: the dictation journal (review + curate) ─────────────────
    def _journal_repo():
        """The durable journal repository behind the recorder, or None."""
        recorder = ctx.journal
        return getattr(recorder, "repository", None) if recorder is not None else None

    def _journal_transcripts() -> list[str]:
        """Every journal transcript (for reach counts), or [] on a bare server."""
        repo = _journal_repo()
        return [r.transcript for r in repo.recent()] if repo is not None else []

    def _applied_counts() -> dict[int, int]:
        """How many RETAINED journal rows each correction actually fired on.

        HS-176-02 (R3). ONE pass over the retained journal, computed once for the
        whole corrections list — cheaper than a per-correction query and honest
        about what it counts: rows whose stored `corrections_applied` names the
        id. The teaching utterance is never one of them (it was never re-run).
        A bare server, or a repository that predates the column, yields {}.
        """
        repo = _journal_repo()
        if repo is None:
            return {}
        counts: dict[int, int] = {}
        try:
            for record in repo.recent():
                for raw_id in getattr(record, "corrections_applied", None) or []:
                    try:
                        correction_id = int(raw_id)
                    except (TypeError, ValueError):
                        continue
                    counts[correction_id] = counts.get(correction_id, 0) + 1
        except Exception:  # pragma: no cover - a read must never fail the list
            return {}
        return counts

    def _dictation_service() -> DictationService:
        return dictation_service

    @router.get("/api/dictation/journal")
    async def api_dictation_journal_list(
        request: Request,
        limit: int = 200,
        source: Optional[str] = None,
        before: Optional[int] = None,
    ) -> Any:
        """List journal entries newest-first (HS-45-02).

        Reports the toggle + retention from config so the UI can show the
        local-only trust statement. With no durable repo (a bare server) the
        list is empty — never an error.

        HS-176-03: `source` accepts every source the recorder writes
        (`VALID_SOURCES` — `dictation` / `dry_run` / `browser` / `hotkey`); the
        old clamp silently dropped `browser` and `hotkey` into "no filter".
        `before=<id>` is the scroll-to-load cursor: entries older than that id.

        R2: the row no longer carries `learning` / `best_correction_signal` — a
        read-time "would match" computed over the whole journal, which painted
        rows recorded BEFORE the correction existed. What fired on a row is a
        stored per-run fact (`corrections_applied`), served by the serializer.
        """
        from ....config import Config
        from ....plugins.dictation.journal import VALID_SOURCES

        cfg = Config.load().dictation
        journal = _dictation_service().list_journal(
            getattr(request.state, "principal", None),
            limit=limit,
            source=source if source in VALID_SOURCES else None,
            cursor=before,
        )
        return JSONResponse(
            {
                "enabled": bool(getattr(cfg.pipeline, "journal_enabled", True)),
                "retention": int(getattr(cfg.pipeline, "journal_retention", 500)),
                "count": journal["count"],
                # C4: the footer's token counts TODAY, so the route serves
                # today. `count` (all-time retained) is untouched.
                "today": journal.get("today", 0),
                "items": journal["items"],
            }
        )

    @router.put("/api/dictation/journal/{entry_id}")
    async def api_dictation_journal_update(
        entry_id: int, payload: dict[str, Any]
    ) -> Any:
        """HS-101 B3 — edit the transcript record in place.

        The smallest possible write: one entry's transcript text.
        Corrections stay the separate taught act (`/correct`); an empty
        transcript refuses rather than blanking the record.
        """
        repo = _journal_repo()
        if repo is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        transcript = str(payload.get("transcript") or "").strip()
        if not transcript:
            return JSONResponse(
                {"error": "transcript required"}, status_code=422
            )
        if repo.update_transcript(entry_id, transcript):
            return JSONResponse({"updated": True, "transcript": transcript})
        return JSONResponse(
            {"updated": False, "error": "entry not found"}, status_code=404
        )

    @router.delete("/api/dictation/journal/{entry_id}")
    async def api_dictation_journal_delete(entry_id: int) -> Any:
        """Delete one journal entry by id (HS-45-02)."""
        repo = _journal_repo()
        if repo is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        if repo.delete(entry_id):
            return JSONResponse({"removed": True, "count": repo.count()})
        return JSONResponse({"removed": False, "error": "entry not found"}, status_code=404)

    @router.delete("/api/dictation/journal")
    async def api_dictation_journal_clear(request: Request) -> Any:
        """Wipe the whole journal (HS-45-02 — the one-click local wipe)."""
        if _journal_repo() is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        return JSONResponse(_dictation_service().clear_journal(getattr(request.state, "principal", None)))

    @router.post("/api/dictation/journal/{entry_id}/correct")
    async def api_dictation_journal_correct(entry_id: int, payload: dict[str, Any]) -> Any:
        """HS-45-03: correct a journaled run in the moment — and teach.

        Records a correction (reusing the Phase-40 `CorrectionStore`, so future
        routing is nudged), then flips the journal entry's `corrected` flag and
        links the correction. The store secret-filters every teach.

        Request:
        - routing kinds (`intent` / `target`): ``{"kind", "value"}`` — the rule
          is keyed on the entry's own transcript, `value` is the block id /
          target profile id. Unchanged since HS-45-03.
        - the `text` kind (HS-176-02): ``{"kind": "text", "heard", "said"}`` —
          `heard` defaults to the entry's stored transcript, and `value` is
          accepted as an alias for `said`. The server runs the word-level diff.

        HS-176-02 (R4), four wire fixes:
        1. `recorded` is the key BOTH teach routes answer with (`taught` stays
           as its long-standing mirror on this route only).
        2. `mark_corrected` moved INSIDE `if recorded` — a refused teach no
           longer flips `corrected` on the row.
        3. the linked `correction_id` is the id `record()` returned, not the
           newest correction in the store (which, on a refusal, was somebody
           else's rule entirely).
        4. a refusal carries a named `reason` (`secret` / `one_word` /
           `no_change` / …) so the face can say `REFUSED · SECRET` truthfully.
        """
        from ....plugins.dictation.corrections import CORRECTION_KINDS

        repo = _journal_repo()
        store = ctx.corrections
        if repo is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        if store is None:
            return JSONResponse({"error": "correction store unavailable"}, status_code=503)
        kind = payload.get("kind") if isinstance(payload, dict) else None
        value = payload.get("value") if isinstance(payload, dict) else None
        heard = payload.get("heard") if isinstance(payload, dict) else None
        said = payload.get("said") if isinstance(payload, dict) else None
        if kind not in CORRECTION_KINDS:
            return JSONResponse(
                {"error": f"kind must be one of {list(CORRECTION_KINDS)}"}, status_code=400
            )
        if kind == "text":
            said = said if isinstance(said, str) else value
            if not isinstance(said, str) or not said.strip():
                return JSONResponse(
                    {"error": "said must be a non-empty string"}, status_code=400
                )
        elif not isinstance(value, str) or not value.strip():
            return JSONResponse({"error": "value must be a non-empty string"}, status_code=400)
        entry = repo.get(entry_id)
        if entry is None:
            return JSONResponse({"error": "entry not found"}, status_code=404)
        if kind == "text":
            result = _teach(
                store,
                "text",
                heard=(heard if isinstance(heard, str) and heard.strip() else entry.transcript),
                said=said,
            )
        else:
            result = _teach(store, kind, key=entry.transcript, value=value)
        recorded = bool(result["recorded"])
        correction_id = result["id"]
        if recorded:
            repo.mark_corrected(entry_id, correction_id=correction_id)
        # HS-48-02: the honest coverage a ROUTING teach now has — how many
        # journal utterances the correction reaches (the same Jaccard count the
        # digest uses). A `text` rule is exact-phrase and has no Jaccard reach,
        # so its `similar` is 0 rather than a borrowed number (R3/R7).
        from ....config import Config
        from ....dictation_learning import reach_for_gist

        similar = (
            reach_for_gist(entry.transcript, _journal_transcripts())
            if recorded and kind != "text"
            else 0
        )
        cfg = Config.load().dictation
        corrections_enabled = bool(getattr(cfg.pipeline, "corrections_enabled", False))
        # HS-56-04: reflect the learning loop on the presence surface — but only
        # honestly. The broadcast fires only when something was actually taught
        # AND has real reach (similar > 0); a no-op teach or a reach of zero
        # stays silent, so Qlippy never claims learning that did not happen.
        if recorded and similar > 0:
            gist = (entry.transcript or "").strip()
            ctx.broadcast(
                "learning_event",
                {
                    "kind": kind,
                    "gist": gist[:120] + ("…" if len(gist) > 120 else ""),
                    "value": str(result["value"] or "").strip(),
                    "similar": int(similar),
                    "enabled": corrections_enabled,
                },
            )
        body: dict[str, Any] = {
            # `corrected` now says what actually happened to the ROW: a refused
            # teach flips nothing, so it cannot claim True (R4).
            "corrected": recorded,
            "recorded": recorded,
            "taught": recorded,  # the long-standing mirror; `recorded` is canon
            "correction_id": correction_id,
            "size": len(store),
            "similar": similar,
            "enabled": corrections_enabled,
        }
        if recorded:
            body.update(
                {"id": correction_id, "kind": result["kind"], "key": result["key"], "value": result["value"]}
            )
        else:
            body["reason"] = result["reason"]
        return JSONResponse(body)

    @router.post("/api/dictation/journal/{entry_id}/replay")
    async def api_dictation_journal_replay(request: Request, entry_id: int) -> Any:
        """HS-45-04: re-run a stored utterance through the *current* pipeline.

        Replays the entry's stored **transcript** (not audio) through the dry-run
        pipeline — no typing, no new journal row — using the entry's original
        project root so routing context matches, and returns a before → after
        diff. This makes "it learned" tangible: correct an utterance, replay it,
        and watch the routing change. The original journal row is never mutated.
        """
        repo = _journal_repo()
        if repo is None:
            return JSONResponse({"error": "journal unavailable"}, status_code=404)
        entry = repo.get(entry_id)
        if entry is None:
            return JSONResponse({"error": "entry not found"}, status_code=404)
        # HS-131-15: a replay re-runs classify/rewrite, so it is admitted like any
        # other provider-bearing entry — its own fresh session, never an open-mic
        # parent — and it runs OFF the event loop so a mesh-routed rewrite cannot
        # deadlock against the relay poller this loop is serving.
        def _work(config_snapshot: Any, admitted: Any) -> dict[str, Any]:
            return _run_dictation_dry_run_text(
                entry.transcript,
                entry.project_root,  # original context
                None,
                suggestions=project_doc_suggestions,
                config_snapshot=config_snapshot,
                admission=None if admitted is None else admitted.provider,
                fence=None if admitted is None else admitted.fence,
                terminal_entry=admitted,
                corrections=ctx.corrections,
                dismissed_signatures=dismissed_signatures,
                telemetry=None,  # a preview — don't pollute readiness telemetry
                journal=None,  # replay never journals (it's not a new dictation)
            )

        from ....speech_session import (
            AIM_JOURNAL_REPLAY,
            SpeechProviderFailure,
            SpeechSessionRefused,
        )

        try:
            after = await _run_cancellable_entry(request, AIM_JOURNAL_REPLAY, _work)
        except SpeechSessionRefused as exc:
            return _speech_refusal(exc)
        except SpeechProviderFailure as exc:
            log.error(f"Journal replay provider failed: {exc.contract}:{exc.reason}")
            return _speech_failure(exc)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:  # pragma: no cover - mirrors the dry-run route
            log.error(f"Journal replay failed: {exc}")
            return JSONResponse({"error": str(exc)}, status_code=500)

        after_block, after_conf = _routed_from_stages(after.get("stages") or [])
        after_summary = {
            "block_id": after_block,
            "confidence": after_conf,
            "target_profile": (after.get("target") or {}).get("id"),
            "final_text": after.get("final_text") or "",
            "runtime_status": after.get("runtime_status"),
        }
        before = {
            "block_id": entry.block_id,
            "confidence": entry.confidence,
            "target_profile": entry.target_profile,
            "final_text": entry.final_text,
        }
        changed = (
            (before["block_id"] or None) != (after_summary["block_id"] or None)
            or (before["target_profile"] or None) != (after_summary["target_profile"] or None)
            or (before["final_text"] or "") != (after_summary["final_text"] or "")
        )
        return JSONResponse(
            {
                "entry_id": entry_id,
                "before": before,
                "after": after_summary,
                "detail": after,
                "changed": changed,
            }
        )

    return router


def _routed_from_stages(stages: list[Any]) -> tuple[Optional[str], Optional[float]]:
    """The block the run routed to (the newest stage intent with a block_id)."""
    block: Optional[str] = None
    conf: Optional[float] = None
    for stage in stages:
        intent = stage.get("intent") if isinstance(stage, dict) else None
        if isinstance(intent, dict) and intent.get("block_id"):
            block = intent.get("block_id")
            conf = intent.get("confidence")
    return block, conf


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
