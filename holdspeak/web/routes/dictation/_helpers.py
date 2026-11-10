"""Request-owned speech session lifetime and compatibility imports.

Pure pipeline, readiness, file and suggestion functions live beside the
DictationService. This module keeps the HTTP disconnect watcher and the
fresh session derived from authenticated request state.
"""
from __future__ import annotations

from typing import Any


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


from ....services.dictation_jobs import session_terminal_of  # noqa: F401


from ....services.dictation_readiness import _hotkey_custody, _runtime_readiness  # noqa: F401


from ....services.dictation_pipeline import (  # noqa: F401 (one implementation)
    _project_suggestion_key, _extract_project_doc_suggestion, _store_project_doc_suggestion,
    _validate_project_doc_suggestion_body, _write_project_doc_suggestion,
    _serialize_intent, _serialize_stage_result, _run_dictation_dry_run_text, _correction_ids,
)
