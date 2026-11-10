"""Speech service jobs. HTTP owns disconnect watching and serializes (body, status)."""

from __future__ import annotations

import asyncio
import hashlib
import json
from copy import deepcopy
from typing import Any, Optional

from holdspeak.logging_config import get_logger
from .dictation_files import (
    _starter_template,
    _resolve_blocks_target,
    _resolve_project_context,
    _read_blocks_document,
    _unique_block_id,
)
from .dictation_pipeline import _run_dictation_dry_run_text

log = get_logger("services.dictation")


def _reply(
    body: dict[str, Any], *, status_code: int = 200
) -> tuple[dict[str, Any], int]:
    return body, status_code


def session_terminal_of(source: Any) -> dict[str, str]:
    if str(getattr(source, "session_terminal", "") or "") == "indeterminate" or getattr(
        source, "indeterminate", False
    ):
        return {"session_terminal": "indeterminate"}
    return {}


def _log_detached_delivery(task: Any) -> None:
    """Record how a committed send finished after its client disconnected."""
    try:
        if task.cancelled():
            log.error("Remote dictation delivery task was cancelled after disconnect")
            return
        exc = task.exception()
    except Exception:
        return
    if exc is not None:
        log.error(f"Remote dictation delivery failed after disconnect: {exc}")
    else:
        log.info("Remote dictation delivery completed after client disconnect")


def _speech_refusal(exc: Any) -> tuple[dict[str, Any], int]:
    """One named, content-free speech refusal on the wire (HS-131-15).

    The kernel's own safe reason is preserved verbatim rather than being rewritten
    into a generic failure, so the deck can name what happened and the owner can
    act on it. No transcript, prompt, or provider text ever rides along.
    """
    reason = str(getattr(exc, "reason", "") or "speech_session_not_admitted")
    return _reply(
        {
            "error": reason,
            "refusal": reason,
            "failure_category": "speech_session_refused",
            "capability": str(getattr(exc, "capability", "") or ""),
            **session_terminal_of(exc),
        },
        status_code=422,
    )


def _speech_failure(exc: Any) -> tuple[dict[str, Any], int]:
    """One admitted provider attempt's safe failed outcome on the wire."""
    contract = str(getattr(exc, "contract", "") or "speech_provider")
    reason = str(getattr(exc, "reason", "") or "provider_failed")
    return _reply(
        {
            "error": f"{contract}:{reason}",
            "failure_category": "speech_provider_failed",
            "contract": contract,
            "reason": reason,
            **session_terminal_of(exc),
        },
        status_code=502,
    )


PRE_EFFECT_REFUSALS = frozenset(
    {
        "desktop_focus_unresolved",
        "desktop_type_driver_unavailable",
        "desktop_type_claim_refused",
        "desktop_type_refused",
    }
)


def _routed_from_stages(stages: list[Any]) -> tuple[Optional[str], Optional[float]]:
    """The block the run routed to (the newest stage intent with a block_id)."""
    block: Optional[str] = None
    conf: Optional[float] = None
    for stage in stages:
        intent = stage.get("intent") if isinstance(stage, dict) else None
        if isinstance(intent, dict) and intent.get("block_id"):
            block = intent.get("block_id")
            conf = intent.get("confidence")
    return (block, conf)


async def rehearse(
    service: Any,
    principal: Any,
    payload: dict[str, Any],
    *,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
    run_entry: Any,
) -> tuple[dict[str, Any], int]:
    ctx = service._runtime_source
    utterance = payload.get("utterance") if isinstance(payload, dict) else None
    if not isinstance(utterance, str):
        return _reply(
            {
                "error": "utterance must be a string",
                "detail": {"utterance": "required string"},
            },
            status_code=400,
        )
    text = utterance.strip()
    if not text:
        return _reply(
            {
                "error": "utterance must not be empty",
                "detail": {"utterance": "must not be empty"},
            },
            status_code=400,
        )
    project_root_override = (
        payload.get("project_root") if isinstance(payload, dict) else None
    )
    if project_root_override is not None and (
        not isinstance(project_root_override, str)
    ):
        return _reply(
            {
                "error": "project_root must be a string when provided",
                "detail": {"project_root": "optional string path"},
            },
            status_code=400,
        )
    target_hints = payload.get("target") if isinstance(payload, dict) else None
    if target_hints is not None and (not isinstance(target_hints, dict)):
        return _reply(
            {
                "error": "target must be an object when provided",
                "detail": {"target": "optional object of app/window/process hints"},
            },
            status_code=400,
        )

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

    from ..speech_session import (
        AIM_BROWSER_REHEARSE,
        SpeechProviderFailure,
        SpeechSessionRefused,
    )

    try:
        return _reply(await run_entry(AIM_BROWSER_REHEARSE, _work))
    except SpeechSessionRefused as exc:
        return _speech_refusal(exc)
    except SpeechProviderFailure as exc:
        log.error(f"Dictation dry-run provider failed: {exc.contract}:{exc.reason}")
        return _speech_failure(exc)
    except ValueError as exc:
        return _reply({"error": str(exc)}, status_code=400)
    except Exception as exc:
        log.error(f"Dictation dry-run failed: {exc}")
        return _reply({"error": str(exc)}, status_code=500)


async def remote_delivery(
    service: Any,
    principal: Any,
    payload: dict[str, Any],
    *,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
    open_entry: Any,
) -> tuple[dict[str, Any], int]:
    """HSM-13-01 — accept a dictated answer from a companion client (iPhone/iPad),"""
    ctx = service._runtime_source
    text = payload.get("text") if isinstance(payload, dict) else None
    if not isinstance(text, str) or not text.strip():
        return _reply({"error": "text must be a non-empty string"}, status_code=400)
    text = text.strip()
    target_hints = payload.get("target") if isinstance(payload, dict) else None
    if target_hints is not None and (not isinstance(target_hints, dict)):
        return _reply(
            {"error": "target must be an object when provided"}, status_code=400
        )
    target_mode = payload.get("target_mode") if isinstance(payload, dict) else None
    if target_mode is None:
        target_mode = "agent"
    if target_mode not in ("agent", "focused"):
        return _reply(
            {"error": 'target_mode must be one of "agent" or "focused"'},
            status_code=400,
        )
    require_agent = (
        bool(payload.get("require_agent")) if isinstance(payload, dict) else False
    )
    delivery_id_value = (
        payload.get("delivery_id") if isinstance(payload, dict) else None
    )
    delivery_id = ""
    if delivery_id_value is None:
        return _reply(
            {
                "error": "delivery_id is required for committed remote delivery",
                "error_code": "delivery_id_required",
                "failure_category": "delivery_conflict",
            },
            status_code=400,
        )
    if not isinstance(delivery_id_value, str) or not delivery_id_value.strip():
        return _reply(
            {"error": "delivery_id must be a non-empty identifier"}, status_code=400
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
        json.dumps(request_shape, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()
    try:
        claim = await asyncio.to_thread(
            lambda: service.claim_delivery(
                principal, delivery_id, request_hash=request_hash
            )
        )
    except ValueError as exc:
        return _reply(
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
        return _reply(cached, status_code=int(claim.get("response_status") or 200))
    if claim_state == "pending":
        return _reply(
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
    ) -> tuple[dict[str, Any], int]:
        response_body = dict(body)
        if delivery_id:
            response_body["delivery_id"] = delivery_id
            response_body["deduplicated"] = False
            try:
                if 200 <= status_code < 300:
                    service.complete_delivery(
                        principal,
                        delivery_id,
                        response_status=status_code,
                        response=response_body,
                    )
                else:
                    service.fail_delivery(
                        principal,
                        delivery_id,
                        response_status=status_code,
                        response=response_body,
                        error=str(response_body.get("error") or "delivery failed"),
                    )
            except Exception as exc:
                log.error(f"Remote dictation receipt persistence failed: {exc}")
                return _reply(
                    {
                        "error": "Delivery outcome could not be recorded. The draft remains on the sending device. Send again to retry.",
                        "error_code": "delivery_pending",
                        "failure_category": "delivery_conflict",
                        "delivery_id": delivery_id,
                    },
                    status_code=425,
                )
        return _reply(response_body, status_code=status_code)

    def uncertain_delivery(
        body: dict[str, Any], *, legacy_status: int = 502
    ) -> tuple[dict[str, Any], int]:
        """Refuse to replay an effect whose hook outcome is ambiguous."""
        if not delivery_id:
            return _reply(body, status_code=legacy_status)
        pending = dict(body)
        pending.update(
            {
                "error_code": "delivery_pending",
                "failure_category": "delivery_conflict",
                "delivery_id": delivery_id,
                "deduplicated": False,
            }
        )
        return _reply(pending, status_code=425)

    def refusal_response(
        reason: str, *, final_text: str = "", session: Any = None
    ) -> tuple[dict[str, Any], int]:
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
    ) -> tuple[bool, dict[str, Any] | None, tuple[dict[str, Any], int] | None]:
        """Run the ONE delivery hook. Returns (delivered, receipt, refusal).

        HS-112-02: the two call sites (raw + processed) share this so the
        room and the companion cannot drift apart on how a refusal reads.
        When a provider-backed remote entry is supplied, settle its honest
        terminal outcome before constructing the response and before the
        caller releases the speech/effect handoff election.
        """
        from ..desktop_typing import DesktopTypeRefused

        if ctx.on_remote_dictation is None:
            if terminal_entry is not None:
                terminal_entry.close("succeeded")
            return (False, None, None)
        try:
            if target_mode == "agent":
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
                        str(exc.reason), final_text=body_text, session=terminal_entry
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
                    }
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
                    }
                ),
            )
        receipt = dict(outcome) if isinstance(outcome, dict) else None
        if terminal_entry is not None:
            terminal_entry.close("succeeded")
        return (True, receipt, None)

    async def _committed_send() -> tuple[dict[str, Any], int]:
        if require_agent and target_mode == "agent":
            from ..agent_context import get_recent_awaiting_agent_session
            from ..agent_context.models import DEFAULT_RECENT_MAX_AGE_SECONDS

            try:
                awaiting = await asyncio.to_thread(
                    get_recent_awaiting_agent_session,
                    max_age_seconds=DEFAULT_RECENT_MAX_AGE_SECONDS,
                )
            except Exception as exc:
                log.warning(f"Awaiting-agent probe failed: {exc}")
                awaiting = None
            if awaiting is None:
                return await asyncio.to_thread(refusal_response, "no_awaiting_agent")
        if bool(payload.get("raw")):
            delivered, receipt, refused = await asyncio.to_thread(deliver, text)
            if refused is not None:
                return refused
            body: dict[str, Any] = {
                "success": True,
                "final_text": text,
                "delivered": delivered,
            }
            if receipt is not None:
                body["delivery"] = receipt
            return await asyncio.to_thread(terminal_response, body)
        from ..config import Config
        from ..dictation_runner import dispatch_voice_command

        def _remote_type(t: str) -> None:
            if ctx.on_remote_dictation is None:
                raise RuntimeError("voice_macro_direct_gesture_required")
            ctx.on_remote_dictation(t, target="focused")

        config_snapshot = await asyncio.to_thread(Config.load)
        try:
            fired = await asyncio.to_thread(
                dispatch_voice_command,
                text,
                config=config_snapshot,
                type_writer=_remote_type,
            )
        except Exception as exc:
            log.error(f"Remote voice-command dispatch failed: {exc}")
            fired = None
        if fired is not None and fired.handled:
            return await asyncio.to_thread(
                terminal_response,
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
                },
            )
        activity_context = None
        try:
            from ..activity_context import build_activity_context
            from ..dictation_selection import consume_selected_record

            selected_record_id = await asyncio.to_thread(consume_selected_record)
            if selected_record_id is not None:
                activity_context = (
                    await asyncio.to_thread(
                        build_activity_context,
                        limit=20,
                        refresh=False,
                        selected_record_id=selected_record_id,
                    )
                ).to_dict()
        except Exception as exc:
            log.warning(f"Remote dictation activity grounding unavailable: {exc}")
        from ..speech_session import (
            AIM_REMOTE_DELIVERY,
            SpeechProviderFailure,
            SpeechSessionRefused,
            pipeline_provider_capabilities,
        )

        entry = None
        final_text = text
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
                    journal_source="dictation",
                )

            if not pipeline_provider_capabilities(config_snapshot):
                processed = await asyncio.to_thread(_run_text, None)
                final_text = (
                    processed.get("final_text", text)
                    if isinstance(processed, dict)
                    else text
                )
                delivered, receipt, refused = await asyncio.to_thread(
                    deliver, final_text
                )
            else:
                config_snapshot, entry = await asyncio.to_thread(
                    open_entry, AIM_REMOTE_DELIVERY, config_snapshot=config_snapshot
                )
                with entry:
                    processed = await asyncio.to_thread(_run_text, entry)
                    final_text = (
                        processed.get("final_text", text)
                        if isinstance(processed, dict)
                        else text
                    )
                    cleared, delivery = await asyncio.to_thread(
                        entry.fence.publish,
                        "remote pre-delivery handoff",
                        lambda: deliver(final_text, terminal_entry=entry),
                    )
                    if not cleared:
                        raise SpeechSessionRefused(
                            entry.fence.reason() or "speech_session_not_live"
                        )
                    assert delivery is not None
                    delivered, receipt, refused = delivery
        except SpeechSessionRefused as exc:
            reason = str(getattr(exc, "reason", "") or "speech_session_not_admitted")
            log.error(f"Remote dictation refused: {reason}")
            return await asyncio.to_thread(
                refusal_response, reason, final_text=final_text, session=entry
            )
        except SpeechProviderFailure as exc:
            log.error(f"Remote dictation provider failed: {exc.contract}:{exc.reason}")
            return await asyncio.to_thread(
                terminal_response,
                {
                    "error": f"{exc.contract}:{exc.reason}",
                    "delivered": False,
                    **session_terminal_of(entry),
                },
                status_code=502,
            )
        except Exception as exc:
            log.error(f"Remote dictation pipeline failed: {exc}")
            return await asyncio.to_thread(
                terminal_response,
                {"error": str(exc), **session_terminal_of(entry)},
                status_code=500,
            )
        if refused is not None:
            return refused
        body = {"success": True, "final_text": final_text, "delivered": delivered}
        if isinstance(processed, dict):
            body["raw_text"] = processed.get("raw_text", text)
            body["corrections_applied"] = [
                int(x) for x in processed.get("corrections_applied") or []
            ]
            body["journal_id"] = processed.get("journal_id")
        if receipt is not None:
            body["delivery"] = receipt
        if entry is not None and entry.indeterminate:
            body["session_terminal"] = "indeterminate"
        return await asyncio.to_thread(terminal_response, body)

    task = asyncio.ensure_future(_committed_send())
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        task.add_done_callback(_log_detached_delivery)
        raise


async def replay_journal(
    service: Any,
    principal: Any,
    entry_id: int,
    *,
    project_doc_suggestions: dict[str, dict[str, str]],
    dismissed_signatures: set[str] | None = None,
    run_entry: Any,
) -> tuple[dict[str, Any], int]:
    """HS-45-04: re-run a stored utterance through the *current* pipeline."""
    ctx = service._runtime_source
    repo = service._edits_of()
    if repo is None:
        return _reply({"error": "journal unavailable"}, status_code=404)
    entry = await asyncio.to_thread(repo.get, entry_id)
    if entry is None:
        return _reply({"error": "entry not found"}, status_code=404)

    def _work(config_snapshot: Any, admitted: Any) -> dict[str, Any]:
        return _run_dictation_dry_run_text(
            entry.transcript,
            entry.project_root,
            None,
            suggestions=project_doc_suggestions,
            config_snapshot=config_snapshot,
            admission=None if admitted is None else admitted.provider,
            fence=None if admitted is None else admitted.fence,
            terminal_entry=admitted,
            corrections=ctx.corrections,
            dismissed_signatures=dismissed_signatures,
            telemetry=None,
            journal=None,
        )

    from ..speech_session import (
        AIM_JOURNAL_REPLAY,
        SpeechProviderFailure,
        SpeechSessionRefused,
    )

    try:
        after = await run_entry(AIM_JOURNAL_REPLAY, _work)
    except SpeechSessionRefused as exc:
        return _speech_refusal(exc)
    except SpeechProviderFailure as exc:
        log.error(f"Journal replay provider failed: {exc.contract}:{exc.reason}")
        return _speech_failure(exc)
    except ValueError as exc:
        return _reply({"error": str(exc)}, status_code=400)
    except Exception as exc:
        log.error(f"Journal replay failed: {exc}")
        return _reply({"error": str(exc)}, status_code=500)
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
        or (before["target_profile"] or None)
        != (after_summary["target_profile"] or None)
        or (before["final_text"] or "") != (after_summary["final_text"] or "")
    )
    return _reply(
        {
            "entry_id": entry_id,
            "before": before,
            "after": after_summary,
            "detail": after,
            "changed": changed,
        }
    )


def _create_template_block(
    service: Any, payload: dict[str, Any], scope: str, project_root: Optional[str]
) -> tuple[dict[str, Any], int]:
    ctx = service._runtime_source
    from ..plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

    template_id = payload.get("template_id") if isinstance(payload, dict) else None
    if not isinstance(template_id, str) or not template_id.strip():
        return _reply(
            {"error": "request body must include template_id"}, status_code=400
        )
    template = _starter_template(template_id.strip())
    if template is None:
        return _reply(
            {"error": f"unknown starter template {template_id!r}"}, status_code=404
        )
    run_dry_run = bool(payload.get("dry_run", False))
    if "dry_run" in payload and (not isinstance(payload.get("dry_run"), bool)):
        return _reply(
            {"error": "dry_run must be a boolean when provided"}, status_code=400
        )
    try:
        path, project = _resolve_blocks_target(scope, project_root)
    except ValueError as exc:
        status = 404 if "no project detected" in str(exc) else 400
        return _reply({"error": str(exc)}, status_code=status)
    if run_dry_run and project_root:
        try:
            _resolve_project_context(project_root)
        except ValueError as exc:
            return _reply({"error": str(exc)}, status_code=400)
    requested_block_id = payload.get("block_id") if isinstance(payload, dict) else None
    if requested_block_id is not None and (not isinstance(requested_block_id, str)):
        return _reply(
            {"error": "block_id must be a string when provided"}, status_code=400
        )
    try:
        document, _exists = _read_blocks_document(path)
    except Exception as exc:
        log.error(f"Failed to read blocks document: {exc}")
        return _reply({"error": str(exc)}, status_code=500)
    block = deepcopy(template["block"])
    base_id = (requested_block_id or block["id"]).strip()
    if not base_id:
        return _reply({"error": "block_id cannot be empty"}, status_code=400)
    block["id"] = _unique_block_id(base_id, document)
    document["blocks"].append(block)
    try:
        save_blocks_yaml(path, document)
    except BlockConfigError as exc:
        return _reply({"error": str(exc)}, status_code=422)
    if ctx.on_dictation_config_changed is not None:
        try:
            ctx.on_dictation_config_changed()
        except Exception as exc:
            log.error(f"on_dictation_config_changed failed: {exc}")
    response_payload = {
        "scope": scope,
        "path": str(path),
        "project": project,
        "template": {
            "id": template["id"],
            "title": template["title"],
            "sample_utterance": template["sample_utterance"],
        },
        "block": block,
        "document": document,
    }
    return _reply(response_payload, status_code=201)


async def create_template_block(
    service: Any,
    principal: Any,
    payload: dict[str, Any],
    *,
    project_doc_suggestions: dict[str, dict[str, str]],
    scope: str = "global",
    project_root: Optional[str] = None,
    dismissed_signatures: set[str] | None = None,
    run_entry: Any,
) -> tuple[dict[str, Any], int]:
    response_payload, status = await asyncio.to_thread(
        _create_template_block, service, payload, scope, project_root
    )
    if status != 201 or not payload.get("dry_run"):
        return response_payload, status
    template = response_payload["template"]
    block = response_payload["block"]

    def _work(config_snapshot: Any, admitted: Any) -> dict[str, Any]:
        return _run_dictation_dry_run_text(
            str(template["sample_utterance"]),
            project_root,
            suggestions=project_doc_suggestions,
            config_snapshot=config_snapshot,
            admission=None if admitted is None else admitted.provider,
            fence=None if admitted is None else admitted.fence,
            terminal_entry=admitted,
        )

    from ..speech_session import AIM_TEMPLATE_PREVIEW, SpeechSessionRefused

    try:
        dry_run = await run_entry(AIM_TEMPLATE_PREVIEW, _work)
    except SpeechSessionRefused as exc:
        response_payload["dry_run"] = None
        response_payload["dry_run_error"] = {
            "created": True,
            "created_block_id": block["id"],
            "failure_category": "template_preview_refused",
            "refusal": str(getattr(exc, "reason", "") or "speech_session_refused"),
            **session_terminal_of(exc),
        }
        return _reply(response_payload, status_code=201)
    except Exception as exc:
        log.error(f"Template dry-run failed: {exc}")
        response_payload["dry_run"] = None
        response_payload["dry_run_error"] = {
            "created": True,
            "created_block_id": block["id"],
            "failure_category": "template_preview_failed",
            "error": str(exc),
            **session_terminal_of(exc),
        }
        return _reply(response_payload, status_code=201)
    dry_run["created_block_id"] = block["id"]
    dry_run["template_id"] = template["id"]
    dry_run["template_title"] = template["title"]
    dry_run["sample_utterance"] = template["sample_utterance"]
    response_payload["dry_run"] = dry_run
    return _reply(response_payload, status_code=201)
