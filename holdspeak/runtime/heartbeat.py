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
        from ..services.watch_service import WatchService

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

                if should_sweep:
                    ws = WatchService(db, observer=obs)
                    hb_with_ws = HeartbeatService(db, observer=obs, watch_service=ws)
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
