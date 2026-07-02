"""The deferred plugin-run queue (HS-63-04).

The flush, the drain passes, the background loop, and the on-demand
processor — verbatim moves out of WebRuntime.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from ..logging_config import get_logger
from ..plugins.queue import drain_plugin_run_queue, process_next_plugin_run_job

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"



log = get_logger("web_runtime")


class PluginQueueMixin:
    def _flush_deferred_plugin_runs_to_db(self) -> dict[str, object]:
        """Persist host-deferred heavy plugin jobs into DB queue storage."""
        queued_jobs = 0
        flush_error: Optional[str] = None
        try:
            from ..db import get_database

            db = get_database()
            while True:
                queued_run = self.plugin_host.pop_next_deferred_run()
                if queued_run is None:
                    break
                db.plugins.enqueue_plugin_run_job(
                    meeting_id=queued_run.meeting_id,
                    window_id=queued_run.window_id,
                    plugin_id=queued_run.plugin_id,
                    plugin_version=queued_run.plugin_version,
                    transcript_hash=queued_run.transcript_hash,
                    idempotency_key=queued_run.idempotency_key,
                    context=queued_run.context,
                )
                queued_jobs += 1
        except Exception as exc:
            flush_error = str(exc)
            log.error(f"Failed to persist deferred plugin queue: {exc}")

        return {"queued_jobs": queued_jobs, "error": flush_error}

    def _broadcast_runtime_queue(self) -> None:
        """HS-77-02: the queue changed — broadcast the real truth."""
        if self.server is None:
            return
        try:
            from ..db import get_database
            from ..intel_queue import build_runtime_queue_frame

            self.server.broadcast(
                "runtime_queue", build_runtime_queue_frame(get_database())
            )
        except Exception as exc:
            log.debug(f"runtime_queue frame dropped: {exc}")

    def _process_deferred_plugin_queue_once(self, *, include_scheduled: bool = False) -> bool:
        """Run one deferred MIR queue job if available."""
        if self._active_meeting_session() is not None:
            return False
        try:
            from ..db import get_database

            db = get_database()
            processed = process_next_plugin_run_job(
                host=self.plugin_host,
                db=db,
                include_scheduled=include_scheduled,
            )
            if processed:
                self._broadcast_runtime_queue()
            return processed
        except Exception as exc:
            log.error(f"Deferred MIR queue processing failed: {exc}")
            return False

    def _process_deferred_plugin_queue(
        self,
        *,
        max_jobs: Optional[int] = None,
        include_scheduled: bool = False,
    ) -> dict[str, object]:
        """Drain deferred MIR queue through runtime-owned plugin host."""
        if self._active_meeting_session() is not None:
            return {"processed": 0, "skipped_active_meeting": True}
        try:
            from ..db import get_database

            db = get_database()
            processed = drain_plugin_run_queue(
                host=self.plugin_host,
                db=db,
                max_jobs=max_jobs,
                include_scheduled=include_scheduled,
            )
            return {"processed": int(processed), "skipped_active_meeting": False}
        except Exception as exc:
            log.error(f"Deferred MIR queue drain failed: {exc}")
            return {
                "processed": 0,
                "skipped_active_meeting": False,
                "error": str(exc),
            }

    def _deferred_plugin_queue_loop(self) -> None:
        while not self.runtime_stop_event.is_set():
            processed = self._process_deferred_plugin_queue_once()
            if processed:
                continue
            self.runtime_stop_event.wait(0.6)

    def _on_process_plugin_jobs(
        self,
        *,
        max_jobs: Optional[int],
        include_scheduled: bool,
    ) -> dict[str, object]:
        queue_flush = self._flush_deferred_plugin_runs_to_db()
        queue_result = self._process_deferred_plugin_queue(
            max_jobs=max_jobs,
            include_scheduled=include_scheduled,
        )
        self._broadcast_runtime_queue()
        return {
            "processed": int(queue_result.get("processed") or 0),
            "skipped_active_meeting": bool(queue_result.get("skipped_active_meeting")),
            "deferred_queue_jobs": int(queue_flush.get("queued_jobs") or 0),
            "deferred_queue_error": queue_flush.get("error"),
            "error": queue_result.get("error"),
        }
