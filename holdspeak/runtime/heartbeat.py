"""HS-171-02: HeartbeatMixin -- the heartbeat conductor loop.

A daemon thread beside the plugin-queue and cadence threads in WebRuntime.
Independent failure boundary: an exception in the heartbeat loop never
kills another loop, and vice versa.

Conductor loops in the runtime (documented):
  1. HoldSpeakMirPluginQueue  -- PluginQueueMixin (web_runtime.py)
  2. HoldSpeakCadenceEngine   -- CadenceMixin (runtime/cadence.py), conditional
  3. HoldSpeakHeartbeat       -- HeartbeatMixin (this file), always-on
  4. RecordingTicker           -- per-meeting lifecycle (device_recording_tick.py)
  5. Transcriber warm          -- one-shot at startup (runtime/transcriber_state.py)
"""
from __future__ import annotations

from ..logging_config import get_logger

log = get_logger("runtime.heartbeat")


def _sweep_watch_service(db, obs):
    """Return the WatchService the sweep must evaluate through (HS-200-43 R1).

    The heartbeat is now the ONLY scheduler for graduated watches, so it must
    run the SAME fully-wired instance the app serves.

    A bare ``WatchService(db)`` does NOT fail outright -- `_fetch` falls
    through to `watch_sources.fetch_watch_snapshot`, so a GitHub watch still
    reads (HS-200-43 F4 corrected an earlier claim here that it would fail).
    What the bare instance loses is the COMPOSITION: the app wires
    `default_snapshot_fetcher(github_runner=..., jira_adapter=JiraProviderAdapter(
    db, runner=self._acli_runner))` (`web_server.py:341-353`), so the wired
    instance carries the Jira adapter composed with the real acli runner and
    the hub's gh runner. The fallback path builds a lazy db-only adapter
    instead, so a Jira watch evaluated through it would not reach acli.

    The bare instance survives only as an explicitly-logged fallback for a
    process that never called `set_scheduler_services` (a CLI or a test
    harness).
    """
    from ..services.watch_service import WatchService

    try:
        from ..workbench_conductor import get_scheduler_services

        wired, _steward = get_scheduler_services()
    except Exception as exc:  # pragma: no cover - import guard only
        wired = None
        log.warning("heartbeat: scheduler-services read failed (%s)", exc)
    if wired is not None:
        return wired
    log.warning(
        "heartbeat: no app-wired WatchService (set_scheduler_services was "
        "never called); falling back to a bare WatchService whose Jira "
        "adapter is not composed with the acli runner",
    )
    return WatchService(db, observer=obs)


class HeartbeatMixin:
    """The heartbeat conductor loop -- evaluates due watches on a cadence."""

    def _start_heartbeat_thread(self) -> None:
        """Construct and start the heartbeat daemon thread.

        Called from WebRuntime.run() beside the plugin-queue and cadence
        thread starts.  Always-on (no feature gate).
        """
        import threading

        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="HoldSpeakHeartbeat",
            daemon=True,
        )
        self.heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        """Tick every 60 seconds; on each tick, check if a sweep is due."""
        import time

        from ..db import get_database, get_observer
        from ..principals import Principal, PrincipalKind
        from ..services.heartbeat_service import HeartbeatService

        TICK_SECONDS = 60  # check every minute whether a sweep is due

        # Initial settle
        self.runtime_stop_event.wait(10)

        while not self.runtime_stop_event.is_set():
            try:
                db = get_database()
                obs = get_observer()
                hb = HeartbeatService(db, observer=obs)
                settings = hb.get_settings()
                sweep_interval = settings["sweep_every_minutes"] * 60

                # Decide if a sweep is due
                last_sweep = settings.get("last_sweep_at")
                should_sweep = False
                if last_sweep is None:
                    should_sweep = True
                else:
                    try:
                        from datetime import datetime, timezone
                        last_dt = datetime.fromisoformat(last_sweep)
                        if last_dt.tzinfo is None:
                            last_dt = last_dt.replace(tzinfo=timezone.utc)
                        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
                        should_sweep = elapsed >= sweep_interval
                    except (ValueError, TypeError):
                        should_sweep = True

                # HS-174-08: check runs_on -- if a remote host is selected,
                # the local loop holds and records a quiet receipt instead.
                runs_on = settings.get("runs_on", "local")
                if should_sweep and runs_on != "local":
                    hb.record_held_remote(runs_on)
                    log.info(
                        "heartbeat sweep held: runs_on=%s (remote)",
                        runs_on,
                    )
                    should_sweep = False

                if should_sweep:
                    ws = _sweep_watch_service(db, obs)
                    # HS-175-02: the calendar refresh rides the heartbeat sweep;
                    # the standalone conductor thread is retired.
                    from ..calendar_ingest_conductor import _conductor as _cal_conductor
                    hb_with_ws = HeartbeatService(
                        db, observer=obs, watch_service=ws,
                        calendar_conductor=_cal_conductor,
                    )
                    principal = Principal(PrincipalKind.OWNER, "heartbeat-conductor")
                    receipt = hb_with_ws.run_sweep(principal)
                    log.info(
                        "heartbeat sweep: watches=%d rooms=%d held=%s duration=%.0fms",
                        receipt.get("watches", 0),
                        receipt.get("rooms", 0),
                        receipt.get("held", False),
                        receipt.get("duration_ms", 0),
                    )
            except Exception as exc:
                # Independent failure boundary: log and continue.
                log.error("heartbeat loop error: %s", exc)

            # Sleep until next tick (or until stop is signaled)
            self.runtime_stop_event.wait(TICK_SECONDS)
