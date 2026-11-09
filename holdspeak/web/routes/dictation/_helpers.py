"""Shared, ctx-free helpers for the dictation route sub-package (HS-34-01).

These are the private helpers that several dictation route groups share —
project-context resolution, blocks-document IO, the dry-run executor, the starter
templates, and the project-doc-suggestion plumbing. They were inline closures in
the original 1,607-line `dictation.py`; the split moves them here verbatim, with
two signature tweaks so the shared in-memory suggestion store is passed
explicitly (it used to be a closure variable):
`_store_project_doc_suggestion(..., suggestions)` and
`_run_dictation_dry_run_text(..., suggestions)`.

Imports gained one relative dot — these modules sit one package deeper than the
old `web/routes/dictation.py`.
"""

from __future__ import annotations

import os
from holdspeak.timestamps import utc_now
from pathlib import Path
from typing import Any, Optional


from ....services.dictation_files import (  # noqa: F401 (re-exported; moved 2026-11-09)
    _resolve_project_context,
    _resolve_blocks_target,
    _project_hs_payload,
    _write_project_hs_files,
    _read_blocks_document,
    _STARTER_BLOCK_TEMPLATES,
    _STARTER_PROJECT_KB,
    _starter_template,
    _unique_block_id,
    _block_summary,
    TEACH_NO_CHANGE,
    TEACH_EMPTY,
    TEACH_SECRET,
    TEACH_ONE_WORD,
    TEACH_REFUSED,
    diff_text_correction,
    teach_refusal_reason,
    record_correction,
)

# ── project-doc-suggestion helpers (operate on a caller-owned store) ──────


def _project_suggestion_key(project: dict[str, Any]) -> str:
    return str(Path(project["root"]).resolve())


def _extract_project_doc_suggestion(stages: list[dict[str, Any]]) -> dict[str, str] | None:
    from ....project_doc_suggestions import validate_project_doc_suggestion_payload

    for stage in stages:
        metadata = stage.get("metadata") if isinstance(stage, dict) else None
        raw = metadata.get("project_doc_suggestion") if isinstance(metadata, dict) else None
        if not isinstance(raw, dict):
            continue
        try:
            return validate_project_doc_suggestion_payload(
                target_path=str(raw.get("target_path") or ""),
                rationale=str(raw.get("rationale") or ""),
                content=str(raw.get("content") or ""),
            ).to_dict()
        except ValueError:
            continue
    return None


def _store_project_doc_suggestion(
    project: dict[str, Any] | None,
    stages: list[dict[str, Any]],
    suggestions: dict[str, dict[str, str]],
    *,
    dismissed_signatures: set[str] | None = None,
) -> str:
    """Store the dry-run's suggestion (or suppress it). Returns the outcome.

    HS-39-04: a suggestion whose signature was previously dismissed in this
    session is suppressed (``"dismissed"``) so it doesn't recur.
    """
    if not project:
        return "no_project"
    key = _project_suggestion_key(project)
    suggestion = _extract_project_doc_suggestion(stages)
    if suggestion is None:
        suggestions.pop(key, None)
        return "no_suggestion"
    if dismissed_signatures is not None:
        from ....project_doc_suggestions import suggestion_signature

        sig = suggestion_signature(
            str(suggestion.get("target_path") or ""), str(suggestion.get("content") or "")
        )
        if sig in dismissed_signatures:
            suggestions.pop(key, None)
            return "dismissed"
    suggestions[key] = suggestion
    return "stored"


def _validate_project_doc_suggestion_body(payload: dict[str, Any]) -> Any:
    from ....project_doc_suggestions import validate_project_doc_suggestion_payload

    raw = payload.get("suggestion") if isinstance(payload.get("suggestion"), dict) else payload
    if not isinstance(raw, dict):
        raise ValueError("request body must include a suggestion object")
    return validate_project_doc_suggestion_payload(
        target_path=str(raw.get("target_path") or ""),
        rationale=str(raw.get("rationale") or ""),
        content=str(raw.get("content") or ""),
    )


def _write_project_doc_suggestion(root: Path, suggestion: Any) -> Path:
    target = (root / suggestion.target_path).resolve()
    resolved_root = root.resolve()
    if resolved_root not in target.parents:
        raise ValueError("target_path must stay inside the project root")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(suggestion.content, encoding="utf-8")
    os.replace(tmp, target)
    return target


# ── dry-run executor + its serialization helpers ─────────────────────────


def _serialize_intent(intent: Any) -> Optional[dict[str, Any]]:
    if intent is None:
        return None
    return {
        "matched": bool(getattr(intent, "matched", False)),
        "block_id": getattr(intent, "block_id", None),
        "confidence": float(getattr(intent, "confidence", 0.0)),
        "raw_label": getattr(intent, "raw_label", None),
        "extras": dict(getattr(intent, "extras", {}) or {}),
    }


def _serialize_stage_result(result: Any) -> dict[str, Any]:
    from ....dictation_telemetry import summarize_stage

    payload = {
        "stage_id": str(getattr(result, "stage_id", "")),
        "elapsed_ms": float(getattr(result, "elapsed_ms", 0.0)),
        "intent": _serialize_intent(getattr(result, "intent", None)),
        "warnings": list(getattr(result, "warnings", []) or []),
        "metadata": dict(getattr(result, "metadata", {}) or {}),
        "text": str(getattr(result, "text", "")),
    }
    payload["telemetry"] = summarize_stage(payload)
    return payload


def _open_text_entry(
    request: Any, insertion_aim: str, *, config_snapshot: Any = None
) -> tuple[Any, Any]:
    """ONE fresh, credential-authenticated text-entry session for this request.

    HS-131-15. Three properties this seam exists to guarantee:

    * **Authority comes only from the credential middleware.** The principal is
      ``request.state.principal`` and nothing else — never a payload field, never
      the request's network location, never a synthesized owner. A request that
      arrived without a principal refuses by name inside ``admit_*``.
    * **The session is always fresh.** Four different routes share the pipeline
      helper; each opens its own short parent and never joins the browser open-mic
      interval, whose authority belongs to a visible microphone the caller is not
      holding.
    * **One snapshot.** The ``Config`` returned here is the SAME object the plan
      was frozen from and the same one assembly builds from, so mutation after
      admission cannot retarget construction, dispatch, egress, or publication.

    Returns ``(config_snapshot, entry)``; the caller owns the entry's terminal
    outcome.
    """
    from ....config import Config
    from ....db import get_database
    from ....speech_session import SpeechEntry, admit_text_entry_session

    config_snapshot = Config.load() if config_snapshot is None else config_snapshot
    session = admit_text_entry_session(
        principal=getattr(getattr(request, "state", None), "principal", None),
        insertion_aim=insertion_aim,
        config_snapshot=config_snapshot,
        registry_snapshot=get_database(),
    )
    return config_snapshot, SpeechEntry(session)


#: How often a cancellable preview asks whether its client is still there.
_DISCONNECT_POLL_SECONDS = 0.25


async def _watch_disconnect(request: Any, entry: Any) -> None:
    """Cancel ``entry`` as soon as this request's client goes away.

    The ASGI server does NOT reliably cancel a handler when the socket closes —
    it depends on the server, the protocol, and whether the handler is awaiting
    something cancellable at that moment. A preview that relied on handler
    cancellation therefore kept a real classify/rewrite running with a live
    session behind it, and its publication could still land minutes after the
    person had closed the tab. So the disconnect is OBSERVED, not assumed:
    ``request.is_disconnected()`` is polled, and the first observation cancels
    the session. The worker thread keeps running (a native model call is not
    interruptible), but the fence is now closed, so it loses the publication
    election and nothing it produced is written or returned.
    """
    import asyncio

    probe = getattr(request, "is_disconnected", None)
    if not callable(probe):
        return
    while True:
        # Probe BEFORE the first sleep. A lexical or already-warm preview can
        # publish in less than one polling interval, and ASGI servers such as
        # Uvicorn report connection_lost without cancelling the application task.
        try:
            gone = bool(await probe())
        except Exception:  # noqa: BLE001 - an unreadable socket is not a cancel
            return
        if gone:
            try:
                # Terminal cancellation performs SQLite transactions and may wait
                # behind a publication election. Keep that blocking work off the
                # ASGI loop; the worker still contends on the same lock, so exactly
                # one of cancellation or publication wins.
                await asyncio.to_thread(entry.cancel)
            except Exception as exc:  # noqa: BLE001 - best-effort teardown
                from ....logging_config import get_logger

                get_logger("web.routes.dictation").error(
                    f"Preview cancellation after disconnect failed: {exc}"
                )
            return
        await asyncio.sleep(_DISCONNECT_POLL_SECONDS)


async def _run_cancellable_entry(request: Any, insertion_aim: str, work: Any) -> Any:
    """Run ``work(config_snapshot, entry)`` off the loop under a fresh entry.

    A provider-free snapshot takes the lexical branch: ``entry`` is ``None`` and
    no parent/watcher/terminal I/O exists. For provider-bearing work, three things
    happen here that a bare ``await asyncio.to_thread(...)`` did not:

    * **Off the event loop, always.** A mesh-routed rewrite WAITS on the relay
      queue, and this loop is what serves the worker's claim polls. Journal replay
      and template preview used to call the helper inline and could deadlock a
      mesh-backed pipeline against its own poller.
    * **Disconnect actively cancels.** These entries are cancellable PREVIEWS, not
      committed effects, and a watcher polls ``request.is_disconnected()`` rather
      than trusting the server to cancel this coroutine. Either route to
      cancellation — the watcher or a real ``CancelledError`` — closes the fence
      before the worker can publish.
    * **The terminal outcome is reported, not swallowed** — on BOTH exits. If the
      parent's close could not be persisted, the success payload says so, and so
      does the refusal or failure that propagates instead of one. A run that
      refused AND could not record its own terminal state is two facts, and the
      caller is owed both; reporting only the first is the same swallow the
      success path already fixed.
    """
    import asyncio

    from ....config import Config
    from ....speech_session import pipeline_provider_capabilities

    config_snapshot = Config.load()
    if not pipeline_provider_capabilities(config_snapshot):
        # Intentionally lexical: no provider runtime, parent, child, disconnect
        # watcher, or terminal receipt exists. This is the same contract as CLI
        # dry-run; only the caller's text and lexical stages run off-loop.
        return await asyncio.to_thread(work, config_snapshot, None)

    config_snapshot, entry = _open_text_entry(
        request, insertion_aim, config_snapshot=config_snapshot
    )
    watcher = asyncio.ensure_future(_watch_disconnect(request, entry))
    try:
        try:
            with entry:
                payload = await asyncio.to_thread(work, config_snapshot, entry)
        except BaseException as exc:
            # `with entry` has already run its terminal close by the time this
            # handler sees the exception, so `indeterminate` is settled. Ride the
            # marker on the exception (a fixed string, never content) so the
            # route's named-refusal response can carry it too.
            mark_session_terminal(exc, entry)
            raise
    finally:
        watcher.cancel()
    if entry.indeterminate and isinstance(payload, dict):
        payload["session_terminal"] = "indeterminate"
    return payload


def mark_session_terminal(exc: BaseException, entry: Any) -> None:
    """Stamp an unknown parent terminal state onto a propagating safe exception."""
    if entry is not None and getattr(entry, "indeterminate", False):
        try:
            exc.session_terminal = "indeterminate"  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - a slotted exception is not worth failing over
            pass


def session_terminal_of(source: Any) -> dict[str, str]:
    """``{"session_terminal": "indeterminate"}`` when known, else ``{}``.

    A merge-in fragment so every response shape can carry the marker without each
    call site re-deriving it. Content-free by construction: the only value it ever
    produces is the fixed string.
    """
    if str(getattr(source, "session_terminal", "") or "") == "indeterminate":
        return {"session_terminal": "indeterminate"}
    if getattr(source, "indeterminate", False):
        return {"session_terminal": "indeterminate"}
    return {}


def _run_dictation_dry_run_text(
    text: str,
    project_root_override: Optional[str],
    target_hints: Optional[dict[str, Any]] = None,
    *,
    suggestions: dict[str, dict[str, str]],
    config_snapshot: Any,
    admission: Any,
    fence: Any,
    terminal_entry: Any = None,
    corrections: Any = None,
    dismissed_signatures: set[str] | None = None,
    telemetry: Any = None,
    journal: Any = None,
    activity_context: Optional[dict[str, Any]] = None,
    journal_source: str = "dry_run",
) -> dict[str, Any]:
    """Execute the browser dry-run path for already-validated text.

    ``activity_context`` (HSM-18-05): a pre-built activity dict (the runner's
    ``build_activity_context(...).to_dict()`` shape) folded into the utterance so
    the rewrite can ground in a selected record — the remote relay passes it when
    a "Dictate with this" pin is pending. ``None`` keeps the historical
    target-only activity dict byte-identical.

    ``journal_source`` (HS-112-02): which lane the run belongs to. The rich
    pipeline is shared by the REHEARSE preview (``dry_run``) and by a real
    delivery (``dictation``) — one helper, one journal schema, an honest row.
    Only an explicit rehearsal writes a ``dry_run`` entry.

    HS-131-15 — ``config_snapshot`` is caller-owned; ``admission`` and ``fence``
    are REQUIRED exactly when that frozen snapshot selects a provider capability,
    and MUST be absent when it is intentionally lexical. This helper mints no
    session and reads no ambient one; it takes no principal, parent id, warrant,
    placement, client profile, or revision, so a payload cannot choose authority
    or where the model runs. A provider path proves its handed admission is a
    live, fresh text-entry admission before construction, and every model-derived
    publication — returned body, stored suggestion, journal row — goes through
    that session's election. A lexical path constructs no runtime and mints no
    parent or child.

    A cancellable preview also passes its ``terminal_entry``. Its final publication
    and successful parent close then happen inside ONE election: publication-first
    cannot be overwritten by a disconnect watcher. Committed remote delivery omits
    it because that session must remain live through the later pre-delivery gate.
    """
    from ....dictation_telemetry import summarize_dry_run
    from ....plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH, build_pipeline
    from ....plugins.dictation.contracts import Utterance
    from ....speech_session import (
        ENTRY_SESSION_REQUIRED,
        SpeechSessionRefused,
        pipeline_provider_capabilities,
        require_entry_admission,
    )
    from ....target_profile import (
        apply_model_assisted_target,
        apply_target_correction,
        collect_active_target_hints,
        detect_target_profile_with_override,
    )

    capabilities = pipeline_provider_capabilities(config_snapshot)
    lexical = not capabilities
    # Before construction: provider work needs OUR live, fresh entry admission.
    # An intentionally provider-free configuration is the opposite contract: it
    # mints no parent and constructs no runtime.
    if lexical:
        if admission is not None or fence is not None or terminal_entry is not None:
            raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)
        egress_boundary = "local"
    else:
        require_entry_admission(admission, fence)
        # Execution proof comes only from the same frozen route members every
        # child dispatches under.  A text entry has no transcription route, so
        # the ProviderAdmission accessor must still see its provider members.
        egress_boundary = str(admission.egress_boundary)
        if terminal_entry is not None and (
            getattr(terminal_entry, "provider", None) is not admission
            or getattr(terminal_entry, "fence", None) is not fence
        ):
            raise SpeechSessionRefused(ENTRY_SESSION_REQUIRED)

    def _elect_publication(stage: str, publication: Any) -> tuple[bool, Any]:
        """Publish, then settle a cancellable entry before releasing its election."""

        def _publish_and_settle() -> Any:
            payload = publication()
            if terminal_entry is not None:
                terminal_entry.close("succeeded")
            return payload

        if lexical:
            return True, _publish_and_settle()
        return fence.publish(stage, _publish_and_settle)

    def _lost(stage: str) -> SpeechSessionRefused:
        from ....speech_session import SESSION_NOT_LIVE

        return SpeechSessionRefused(fence.reason() or SESSION_NOT_LIVE, stage)

    cfg = config_snapshot.dictation
    # HS-39-02: only consult corrections when the feature is on; a None snapshot
    # keeps routing + target detection byte-identical.
    correction_snapshot = (
        corrections.snapshot()
        if corrections is not None and getattr(cfg.pipeline, "corrections_enabled", False)
        else None
    )
    try:
        project = _resolve_project_context(project_root_override)
    except ValueError:
        if project_root_override:
            raise
        project = None
    project_root = Path(project["root"]) if project else None

    if not cfg.pipeline.enabled:
        warnings = ["dictation pipeline disabled"]

        def _publish_disabled() -> dict[str, Any]:
            # F-07: the journal follows `journal_enabled`, not the pipeline gate —
            # a pipeline-off dry-run records a passthrough row so the review
            # surface reflects real activity. Best-effort like every journal write.
            journal_id = None
            if journal is not None:
                from ....plugins.dictation.journal import passthrough_run

                recorded = journal.record(
                    passthrough_run(text),
                    source=journal_source,
                    transcript=text,
                    enabled=bool(getattr(cfg.pipeline, "journal_enabled", True)),
                    retention=int(getattr(cfg.pipeline, "journal_retention", 500)),
                )
                journal_id = getattr(recorded, "id", None)
            return {
                "project": dict(project) if project else None,
                "egress_boundary": egress_boundary,
                "runtime_status": "disabled",
                "runtime_detail": "dictation pipeline disabled (opt-in)",
                "blocks_count": 0,
                "stages": [],
                "final_text": text,
                # HS-176-02 (N2): the transcript AS HEARD, before any rewrite.
                # The TEXT teach well pre-fills from this, and the word-level
                # diff runs heard(raw) vs said(his edit) — a key harvested from
                # `final_text` would be matched against a string it never equals.
                # Pipeline off: nothing rewrote and no rule fired.
                "raw_text": text,
                "corrections_applied": [],
                "total_elapsed_ms": 0.0,
                "warnings": warnings,
                "journal_id": journal_id,
                "learning": None,
                "telemetry": summarize_dry_run(
                    runtime_status="disabled",
                    runtime_detail="dictation pipeline disabled (opt-in)",
                    stages=[],
                    warnings=warnings,
                    total_elapsed_ms=0.0,
                    max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
                ),
            }

        # A disabled pipeline is not an exemption from the election: a cancelled
        # session still writes no journal row and returns no body.
        won, payload = _elect_publication(
            "dictation entry (pipeline disabled)", _publish_disabled
        )
        if not won:
            raise _lost("dictation entry (pipeline disabled)")
        return payload

    # Runtime construction and cancellation elect one winner. A preceding
    # liveness check was only a snapshot: the worker could then build a runtime
    # after the disconnect watcher had cancelled this entry. Construction itself
    # is bounded by the fence; no model attempt occurs here (admitted construction
    # forces warm_on_start=False), and each later physical attempt still mints its
    # own child.
    construction = lambda: build_pipeline(
        cfg,
        project_root=project_root,
        global_blocks_path=DEFAULT_GLOBAL_BLOCKS_PATH,
        corrections=correction_snapshot,
        on_run=(telemetry.record_run if telemetry is not None else None),
        admission=admission,
        lexical=lexical,
    )

    if lexical:
        result = construction()
    else:
        constructed, result = fence.publish(
            "dictation entry construction", construction
        )
        if not constructed:
            raise _lost("dictation entry construction")
        assert result is not None
    resolved_hints = target_hints or collect_active_target_hints()
    target_profile = detect_target_profile_with_override(
        resolved_hints,
        cfg.pipeline.target_profile_override,
    )
    target_profile = apply_target_correction(
        target_profile, text=text, corrections=correction_snapshot
    )
    target_profile = apply_model_assisted_target(
        target_profile,
        runtime=result.runtime,
        hints=resolved_hints,
        text=text,
        enabled=bool(getattr(cfg.pipeline, "target_detect_llm_enabled", False)),
        below_confidence=float(getattr(cfg.pipeline, "target_detect_llm_below", 0.8)),
    )
    # Model-assisted target detection is a provider-bearing continuation; check
    # the fence again before the pipeline's own provider work begins.
    if not lexical and fence.discarded("dictation entry pipeline"):
        raise _lost("dictation entry pipeline")
    activity = dict(activity_context) if activity_context else {}
    activity["target"] = target_profile.to_dict()
    run = result.pipeline.run(
        Utterance(
            raw_text=text,
            audio_duration_s=0.0,
            transcribed_at=utc_now(),
            project=project,
            activity=activity,
        )
    )
    # HS-45-01: journal the dry-run as a side-channel (best-effort; never alters
    # the returned result). Tagged `source='dry_run'` so the no-mic path is
    # first-class. A recorder with no repository (bare server) is a no-op.
    # HS-45-03: the returned record's id flows back so the result panel can
    # offer an in-the-moment "fix it here" that attaches to this entry.
    # HS-48-02: the inline "learned from N similar" signal for this utterance.
    # Computed from the same snapshot routing used (None when corrections are
    # off -> no signal), over the journal as it stood *before* this run, so the
    # count reflects past utterances rather than counting this one. Quiet when
    # nothing matches.
    learning_signal = None
    if correction_snapshot:
        from ....dictation_learning import best_correction_signal, reach_by_gist_map

        repo = getattr(journal, "repository", None) if journal is not None else None
        past_transcripts = (
            [r.transcript for r in repo.recent()] if repo is not None else []
        )
        reach_map = reach_by_gist_map(correction_snapshot, past_transcripts)
        learning_signal = best_correction_signal(text, correction_snapshot, reach_map)

    def _publish() -> dict[str, Any]:
        """Every model-derived output of this run, under one election.

        The journal row, the stored project-doc suggestion, and the returned body
        are ONE publication. Splitting them would let a cancellation land between
        a written journal row and a suppressed response — a persisted claim about
        work whose result the caller never receives.
        """
        journal_id = None
        if journal is not None:
            recorded = journal.record(
                run,
                source=journal_source,
                transcript=text,
                target_profile=target_profile,
                project_root=project_root,
                enabled=bool(getattr(cfg.pipeline, "journal_enabled", True)),
                retention=int(getattr(cfg.pipeline, "journal_retention", 500)),
            )
            journal_id = getattr(recorded, "id", None)
        stages = [_serialize_stage_result(sr) for sr in run.stage_results]
        suggestion_status = _store_project_doc_suggestion(
            project, stages, suggestions, dismissed_signatures=dismissed_signatures
        )
        warnings = list(run.warnings)
        return {
            "project": dict(project) if project else None,
            "egress_boundary": egress_boundary,
            "target": target_profile.to_dict(),
            "suggestion_status": suggestion_status,
            "journal_id": journal_id,
            "learning": learning_signal,
            "runtime_status": result.runtime_status,
            "runtime_detail": result.runtime_detail,
            "blocks_count": len(result.blocks.blocks),
            "stages": stages,
            "final_text": run.final_text,
            # HS-176-02 (N2): the transcript AS HEARD — the exact string the
            # `text` rules are applied to at the head of `Pipeline.run` — beside
            # the landed text, plus the ids of the rules that actually fired on
            # this run (R2: the APPLIED chip renders from this stored fact, never
            # from a read-time "would match"). `getattr` because `PipelineRun`'s
            # field is additive and the passthrough fakes a run (C5 note).
            "raw_text": text,
            "corrections_applied": _correction_ids(
                getattr(run, "corrections_applied", None)
            ),
            "total_elapsed_ms": float(run.total_elapsed_ms),
            "warnings": warnings,
            "telemetry": summarize_dry_run(
                runtime_status=result.runtime_status,
                runtime_detail=result.runtime_detail,
                stages=stages,
                warnings=warnings,
                total_elapsed_ms=float(run.total_elapsed_ms),
                max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
            ),
        }

    won, payload = _elect_publication("dictation entry publication", _publish)
    if not won:
        raise _lost("dictation entry publication")
    return payload


def _hotkey_custody(ctx: Any, config_snapshot: Any) -> dict[str, Any]:
    """HS-200-05: the physical hotkey's custody, for `/api/dictation/readiness`.

    Two facts, joined: whether the global listener actually installed (the
    runtime's own `global_hotkey_available` / `global_hotkey_error`, which
    until now nothing read), and the honestly-read state of the three macOS
    grants the dictation path needs. Reading a grant NEVER prompts.

    When the app has no runtime to ask — a bare test server, a dry run —
    availability is `None`, which the face must render UNKNOWN. It is never
    smoothed into "the hotkey works".
    """
    from ....desktop_permissions import hotkey_custody

    available: Optional[bool] = None
    error = ""
    getter = getattr(ctx, "on_get_status", None)
    if callable(getter):
        try:
            status = getter() or {}
        except Exception as exc:  # pragma: no cover - defensive
            status = {}
            error = f"{type(exc).__name__}: {exc}"
        raw = status.get("global_hotkey_available") if isinstance(status, dict) else None
        if isinstance(raw, bool):
            available = raw
        if isinstance(status, dict) and not error:
            error = str(status.get("global_hotkey_error") or "")

    hotkey_cfg = getattr(config_snapshot, "hotkey", None)
    return hotkey_custody(
        listener_available=available,
        listener_error=error,
        key=str(getattr(hotkey_cfg, "key", "") or ""),
        display=str(getattr(hotkey_cfg, "display", "") or ""),
    )


def _runtime_readiness(cfg: Any) -> dict[str, Any]:
    from ....dictation_telemetry import summarize_readiness_telemetry
    from ....plugins.dictation import runtime as runtime_module
    from ....plugins.dictation.runtime_counters import get_counters, get_session_status

    if not cfg.pipeline.enabled:
        payload = {
            "status": "disabled",
            "requested_backend": cfg.runtime.backend,
            "resolved_backend": None,
            "detail": "dictation pipeline disabled",
            "model_path": None,
            "model_exists": False,
            "counters": get_counters(),
            "session": get_session_status(),
        }
        payload["telemetry"] = summarize_readiness_telemetry(
            runtime_payload=payload,
            max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
        )
        return payload

    try:
        resolved_backend, reason = runtime_module.resolve_backend(
            cfg.runtime.backend, mlx_model_set=bool(str(cfg.runtime.mlx_model or "").strip())
        )
    except runtime_module.RuntimeUnavailableError as exc:
        from ....plugins.dictation.guidance import runtime_guidance

        payload = {
            "status": "unavailable",
            "requested_backend": cfg.runtime.backend,
            "resolved_backend": None,
            "detail": str(exc),
            "model_path": None,
            "model_exists": False,
            "guidance": runtime_guidance(
                kind="unavailable",
                requested_backend=cfg.runtime.backend,
            ),
            "counters": get_counters(),
            "session": get_session_status(),
        }
        payload["telemetry"] = summarize_readiness_telemetry(
            runtime_payload=payload,
            max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
        )
        return payload

    if resolved_backend == "openai_compatible":
        from ....intel.providers import effective_dictation_llm
        from ....plugins.dictation.guidance import runtime_guidance

        effective = effective_dictation_llm(cfg.runtime)
        payload = {
            "status": "available",
            "requested_backend": cfg.runtime.backend,
            "resolved_backend": resolved_backend,
            "detail": (
                f"endpoint={effective.base_url or 'unset'}; "
                f"model={effective.model or 'unset'}"
            ),
            "model_path": None,
            "model_exists": True,
            "guidance": runtime_guidance(
                kind="endpoint_config",
                requested_backend=cfg.runtime.backend,
                resolved_backend=resolved_backend,
            ),
            "counters": get_counters(),
            "session": get_session_status(),
        }
        payload["telemetry"] = summarize_readiness_telemetry(
            runtime_payload=payload,
            max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
        )
        return payload

    raw_model_path = str(
        cfg.runtime.mlx_model
        if resolved_backend == "mlx"
        else cfg.runtime.llama_cpp_model_path
    ).strip()
    model_path = Path(raw_model_path).expanduser()
    # A blank path is "not set", never Path("") == "." (which exists).
    model_exists = bool(raw_model_path) and model_path.exists()
    guidance = None
    if not model_exists:
        from ....plugins.dictation.guidance import runtime_guidance

        guidance = runtime_guidance(
            kind="missing_model",
            requested_backend=cfg.runtime.backend,
            resolved_backend=resolved_backend,
            model_path=model_path,
        )
    payload = {
        "status": "available" if model_exists else "missing_model",
        "requested_backend": cfg.runtime.backend,
        "resolved_backend": resolved_backend,
        "detail": reason if model_exists else f"model file missing at {model_path}",
        "model_path": str(model_path),
        "model_exists": model_exists,
        "guidance": guidance,
        "counters": get_counters(),
        "session": get_session_status(),
    }
    payload["telemetry"] = summarize_readiness_telemetry(
        runtime_payload=payload,
        max_total_latency_ms=cfg.pipeline.max_total_latency_ms,
    )
    return payload


def _correction_ids(value: Any) -> list[int]:
    """A clean ``list[int]`` of correction ids from whatever the run carries."""
    ids: list[int] = []
    for item in (value or []):
        try:
            ids.append(int(item))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            continue
    return ids
