"""The hub's background work: what the lifespan starts, and what it stops.

``start_background(hub, host)`` runs the lifespan's startup body: it reads
the same switches in the same order and starts the same threads (thread names
unchanged; the SIGUSR1 dump and the tests name them). ``Stopper.stop()`` is
the lifespan's shutdown. ``web_server`` keeps the lifespan as these two calls.

One way only: this module imports services and runtime, never ``web_server``.
``host`` is the running web server, read by its attributes (``port``,
``broadcast``, ``voice_session``, the conductor callbacks and the two loop
hooks), so the server's own asyncio loops stay with the server.

The switches, in the order startup reads them: ``HOLDSPEAK_LOOP_WATCH`` (off
by default), ``HOLDSPEAK_CALLS``, ``HOLDSPEAK_PHONE``, ``HOLDSPEAK_TELEGRAM``,
``HOLDSPEAK_RECORDINGS``, ``HOLDSPEAK_RESTART_CHECK``, ``HOLDSPEAK_PROGRAMS``
(inside the workbench conductor), ``HOLDSPEAK_MACOS_CALENDAR`` (inside the
calendar conductor), ``HOLDSPEAK_EVENT_RETENTION_DAYS``. The keystore warm and
the workbench and scheduled-recording conductor threads have no switch (the
calendar conductor refreshes once at boot and starts no thread); the intel
queue, memory, retention and defaults work runs only in the process that owns
the database.
"""
from __future__ import annotations

import asyncio
import importlib
import os
import threading
from typing import Any

from ..logging_config import get_logger

log = get_logger("web_server")

#: The hub's worker-thread budget for ``run_in_threadpool`` (PERF-HUB).
HUB_THREAD_TOKENS = 64

#: Betterment AG0: ``HOLDSPEAK_RESTART_CHECK=off`` asks tmux nothing about
#: the launches (a rig hub on the shared tmux socket, with seeded launches
#: that never had a session). Default: on.
RESTART_CHECK_ENV = "HOLDSPEAK_RESTART_CHECK"


def record_restart_stops() -> None:
    """Betterment AG0: a launch whose tmux session is gone reads "Stopped by
    restart" (hub start, then about each minute). A failure is logged and
    never stops the hub's timer."""
    if os.environ.get(RESTART_CHECK_ENV, "").strip().lower() in {"0", "off", "false", "no"}:
        return
    try:
        from ..services.launch_lane import record_restart_stops as _record

        _record()
    except Exception as exc:
        log.warning(f"restart stop check failed: {exc}")


# HS-200-03: EVERY conductor the lifespan started is stopped at shutdown.
# Only the calendar one was, so the workbench and scheduled-recording
# conductors outlived the app that started them: on an in-process restart they
# kept ticking against a database nobody owned any more, and in a test process
# they survived every subsequent app and called `get_database()` on a
# 60-second timer for the rest of the run. That is the thread whose tick
# produced the CI-only web-activity failures.
_CONDUCTOR_STOPS = (
    ("calendar ingest", "calendar_ingest_conductor.stop_calendar_ingest_conductor"),
    ("workbench", "workbench_conductor.stop_conductor"),
    ("scheduled recording", "scheduled_recording_conductor.stop_scheduled_recording_conductor"),
    ("intel queue", "intel_queue_conductor.stop_intel_queue_conductor"),
    ("memory", "memory_conductor.stop_memory_conductor"),
    ("defaults", "defaults_conductor.stop_defaults_conductor"),
)


class Stopper:
    """The lifespan's shutdown for the work ``start_background`` started."""

    def __init__(self, refinement_coordinator: Any) -> None:
        self._refinement_coordinator = refinement_coordinator

    async def stop(self) -> None:
        try:
            from ..calls.service import CALLS

            await CALLS.stop_listening()
        except Exception as e:
            log.error(f"calls listener stop failed: {e}")
        try:
            from ..recordings.service import RECORDINGS

            RECORDINGS.shutdown()
        except Exception as e:
            log.error(f"recordings stop failed: {e}")
        try:
            from ..phone import service as phone_service

            if phone_service._DEFAULT is not None:
                phone_service._DEFAULT.stop()
        except Exception as e:
            log.error(f"phone stop failed: {e}")
        try:
            from ..services import reach_service

            if reach_service._DEFAULT is not None:
                reach_service._DEFAULT.stop()
        except Exception as e:
            log.error(f"reach stop failed: {e}")
        for name, stop in _CONDUCTOR_STOPS:
            module_name, _, attribute = stop.partition(".")
            try:
                module = importlib.import_module(f"holdspeak.{module_name}")
                getattr(module, attribute)()
            except Exception as e:
                log.error(f"{name} conductor shutdown failed: {e}")
        from ..mcp import aio as _mcp_aio

        _mcp_aio.set_hub_loop(None)
        await self._refinement_coordinator.shutdown()


async def _start_reach_and_recordings(host: Any) -> None:
    # Calls: with calls on and enabled, the hub waits for a call.
    try:
        from ..calls.service import CALLS

        CALLS.bind_loop()
        CALLS.ensure_listening()
    except Exception as e:
        log.error(f"calls listener startup failed: {e}")
    # Phone: the follow-up sweep (a call after an unanswered message).
    try:
        from ..phone import phone_on

        if phone_on():
            from ..phone.service import default_phone_service

            await asyncio.to_thread(lambda: default_phone_service().start())
    except Exception as e:
        log.error(f"phone startup failed: {e}")
    # PG-DIRECTION DIR4/DIR5: the reach thread (Later's returns, the
    # ladder, Telegram's long poll when a chat is paired). The bot
    # token moves from the config file into the keystore once.
    # HOLDSPEAK_TELEGRAM=off (every rig) polls and sends nothing.
    try:
        from ..services import telegram_reach
        from ..services.reach_service import default_reach_service

        telegram_reach.remember_port(host.port)
        if telegram_reach.telegram_on():
            await asyncio.to_thread(telegram_reach.repair_token)
            await asyncio.to_thread(lambda: default_reach_service().start())
    except Exception as e:
        log.error(f"reach startup failed: {e}")
    # Recordings: park old ones, finish a cut encode, watch for stale.
    try:
        from ..recordings.service import RECORDINGS

        await asyncio.to_thread(RECORDINGS.startup)
    except Exception as e:
        log.error(f"recordings startup failed: {e}")


def _recover_interrupted_work(web_ctx: Any, kernel_service: Any) -> None:
    # HS-104-02 restart honesty: revalidate-or-expire, never resume.
    try:
        from ..web.routes.system.gate_routes import invalidate_held_on_startup

        invalidate_held_on_startup(web_ctx.gate_service)
    except Exception as e:
        log.error(f"gate startup invalidation failed: {e}")
    try:
        from ..web.routes.primitives.invocations import recover_inference_on_startup

        recover_inference_on_startup()
    except Exception as e:
        log.error(f"inference startup recovery failed: {e}")
    # Betterment P1: an engine pass's thread dies with the process; a
    # job still running ends failed ("the hub restarted"), never polled forever.
    try:
        if web_ctx.project_update_service is not None:
            recovered_passes = web_ctx.project_update_service.recover_engine_passes()
            if recovered_passes:
                log.info(f"updates: {recovered_passes} interrupted engine pass(es) ended failed")
    except Exception as e:
        log.error(f"update engine pass startup recovery failed: {e}")
    # PHILO-15-03: no import worker survives a restart; a row still
    # importing/active ends import_failed + failed (import it again).
    try:
        if web_ctx.meeting_service is not None:
            recovered_imports = web_ctx.meeting_service.recover_interrupted_imports()
            if recovered_imports:
                log.info(f"meetings: {recovered_imports} interrupted import(s) ended failed")
    except Exception as e:
        log.error(f"meeting import startup recovery failed: {e}")
    # PHILO-7-02 (T6): a desk write left admitting/awaiting_decision by a
    # dead process ends indeterminate with its receipt (never resumed).
    try:
        from ..kernel.desk_broker import recover_on_startup as recover_desk_on_startup

        recovered_desk = recover_desk_on_startup(kernel_service())
        if recovered_desk:
            log.info(f"desk: {recovered_desk} interrupted desk write(s) ended indeterminate")
    except Exception as e:
        log.error(f"desk startup recovery failed: {e}")


def _start_conductors(web_ctx: Any, host: Any) -> None:
    try:
        from ..skills_library import seed_skills_if_empty
        seeded = seed_skills_if_empty()
        if seeded:
            log.info(f"Seeded {seeded} built-in skills")
    except Exception as e:
        log.debug(f"skill seeding skipped: {e}")
    # HS-163-02 STW-009 + PHILO-9-02 (the steward beat, section 3):
    # settle abandoned steward work on the hub's COMPOSED service,
    # before the conductor starts: every Room operation left
    # non-terminal ends indeterminate with its receipt (children
    # first) and its run row interrupted in the same transaction; a
    # legacy run with no operation is interrupted as before.
    try:
        recovered = web_ctx.project_steward_service.recover_admitted_on_startup()
        if any(recovered.values()):
            log.info(f"Steward recovery: {recovered}")
    except Exception as e:
        log.error(f"steward startup recovery failed: {e}")
    try:
        from ..workbench_conductor import (
            start_conductor,
            set_broadcast,
            set_scheduler_services,
        )
        set_broadcast(lambda t, d: host.broadcast(t, d))
        set_scheduler_services(
            web_ctx.watch_service,
            web_ctx.project_steward_service,
        )
        start_conductor()
    except Exception as e:
        log.error(f"workbench conductor startup failed: {e}")
    try:
        from ..scheduled_recording_conductor import (
            start_scheduled_recording_conductor,
            set_broadcast as sr_set_broadcast,
        )
        sr_set_broadcast(lambda t, d: host.broadcast(t, d))
        # HS-151-06: the conductor speaks the SAME contract the routes do:
        # `on_start(principal=...)` with the pending-title/calendar seam set
        # on the bound method's owner (the runtime), and `on_meeting_stop()`
        # which IS the fallback-free stop (meeting_glue.py). Capture C7:
        # `voice_session` is ALWAYS an attribute (None on a server with no
        # runtime); no arbiter = no holder.
        start_scheduled_recording_conductor(
            voice_floor_fn=lambda: getattr(host.voice_session, "active_owner", None),
            start_meeting_fn=host._conductor_start_meeting,
            stop_meeting_fn=host._conductor_stop_meeting,
        )
    except Exception as e:
        log.error(f"scheduled recording conductor startup failed: {e}")
    try:
        from ..calendar_ingest_conductor import start_calendar_ingest_conductor

        start_calendar_ingest_conductor()
    except Exception as e:
        log.error(f"calendar ingest conductor startup failed: {e}")
    # HS-200-42: the fourth conductor drains `intel_jobs`. It refuses to
    # start when this process does not own the database, so the
    # HOLDSPEAK_ALLOW_UNOWNED_DB hub keeps its "scheduled work OFF" promise.
    try:
        from ..intel_queue_conductor import start_intel_queue_conductor

        start_intel_queue_conductor(
            broadcast=lambda t, d: host.broadcast(t, d)
        )
    except Exception as e:
        log.error(f"intel queue conductor startup failed: {e}")
    # The memory conductor (MEMORY-DESIGN.md §3): sweeps the source
    # tables into the chunk index and embeds through memory.embed.
    try:
        from ..memory_conductor import set_live_check, start_memory_conductor

        # Extraction yields to a live meeting (MEMORY-DESIGN.md §9).
        set_live_check(host._memory_live_check)
        start_memory_conductor()
    except Exception as e:
        log.error(f"memory conductor startup failed: {e}")
    # PERF-HUB 2026-10-28: old READ receipts leave pipeline_events
    # (a daemon thread, after the hub is up, then daily). Owner-only,
    # like every other scheduled work.
    try:
        from ..db import get_database
        from ..db.pipeline_events_retention import start_retention
        from ..intel_queue_conductor import owns_database

        if owns_database():
            start_retention(get_database()._connection)
    except Exception as e:
        log.error(f"pipeline event retention startup failed: {e}")
    # Owner ruling 2026-10-05 ("strong defaults, batteries included"):
    # a LOCAL engine becomes "Default for AI work" by itself; network
    # and cloud engines become proposals. Background thread: the
    # loopback scan never delays the listener. Only the hub that owns
    # the database writes a default.
    try:
        from ..intel_queue_conductor import owns_database

        if web_ctx.inference_default_service is not None and owns_database():
            web_ctx.inference_default_service.kick("boot")
    except Exception as e:
        log.error(f"batteries default startup failed: {e}")
    # The defaults watcher: an engine started after boot is found by a
    # light loopback re-scan, and the meetings saved before any
    # engine existed are summarised once one does. Owner-only.
    try:
        from ..defaults_conductor import start_defaults_conductor

        start_defaults_conductor(
            defaults_service=web_ctx.inference_default_service,
        )
    except Exception as e:
        log.error(f"defaults watcher startup failed: {e}")


async def start_background(hub: Any, host: Any) -> Stopper:
    """Start the hub's background work, in the lifespan's order."""
    import anyio.to_thread

    # 2026-11-07: `kill -USR1 <hub pid>` writes every thread's Python
    # stack to stderr (the hub log). A stalled route names itself
    # without root (py-spy needs sudo on macOS).
    try:
        import faulthandler
        import signal

        faulthandler.register(signal.SIGUSR1, all_threads=True, chain=False)
    except Exception as exc:  # pragma: no cover - platform without SIGUSR1
        log.info(f"thread dump signal not registered: {exc}")

    anyio.to_thread.current_default_thread_limiter().total_tokens = HUB_THREAD_TOKENS
    # 2026-11-08: the one keystore opens its master key once (bounded,
    # off the loop) and moves the old per-secret Keychain items.
    from .. import keystore

    threading.Thread(target=keystore.warm, name="keystore-warm", daemon=True).start()
    # PERF-HUB 2026-10-28: HOLDSPEAK_LOOP_WATCH=1 names any handler
    # that holds the event loop longer than 100 ms. Off by default.
    from ..web import loop_watch

    if loop_watch.enabled():
        loop_watch.start(asyncio.get_running_loop())
    await _start_reach_and_recordings(host)

    from ..kernel.runtime import _service as kernel_service

    web_ctx = hub.web_ctx
    _recover_interrupted_work(web_ctx, kernel_service)
    # The server's own asyncio loops (duration, coder frames, rails, the
    # agent spool, the PR poll) and the MCP hub loop.
    host.start_loop_tasks(web_ctx)
    # Betterment AG0: agents a restart took read "Stopped by restart".
    await asyncio.to_thread(record_restart_stops)
    await asyncio.to_thread(kernel_service().reap_and_recover_projections)
    try:
        await hub.refinement_coordinator.start()
    except Exception as e:
        log.error(f"refinement coordinator startup recovery failed: {e}")
    # HS-200-41: settle asks whose dispatching process is gone. After
    # the coordinator starts, so that a lease a live refinement_hosts
    # row still backs reads as work in flight and never as
    # abandonment. Reconcile from proof only — this dispatches nothing.
    try:
        lost = await asyncio.to_thread(hub.project_service.recover_ask_tasks_on_startup)
        if lost:
            log.info(f"Settled {len(lost)} unfinished ask(s) whose host was lost")
    except Exception as e:
        log.error(f"ask task startup recovery failed: {e}")
    host.start_liveness_task()
    _start_conductors(web_ctx, host)
    return Stopper(hub.refinement_coordinator)


__all__ = [
    "HUB_THREAD_TOKENS",
    "RESTART_CHECK_ENV",
    "Stopper",
    "record_restart_stops",
    "start_background",
]
