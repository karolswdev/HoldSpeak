"""CadenceMixin (CAD-1-04) — the in-runtime cadence tick.

Mirrors PluginQueueMixin: a daemon thread on `runtime_stop_event`, started by
WebRuntime.run() ONLY when `config.cadence.enabled` is True. When disabled the
thread never starts and the runtime is byte-identical to a build without cadence.
The loop performs no external side effect — it projects + scores loops and computes
which are due (delivery is Phase 2+).
"""
from __future__ import annotations

from typing import Optional

from ..logging_config import get_logger

log = get_logger("runtime.cadence")


class CadenceMixin:
    def _cadence_enabled(self) -> bool:
        return bool(getattr(getattr(self.config, "cadence", None), "enabled", False))

    def _cadence_service(self):
        """Lazily build a CadenceService bound to the shared DB + config."""
        if getattr(self, "_cadence_service_obj", None) is None:
            from ..cadence.service import CadenceService
            from ..db import get_database

            self._cadence_service_obj = CadenceService(get_database(), self.config.cadence)
        return self._cadence_service_obj

    def _cadence_tick_once(self) -> None:
        try:
            result = self._cadence_service().tick()
            if result.due:
                log.info(
                    "cadence tick: %d projected, %d open, %d due",
                    result.projected, result.open_loops, result.due_count,
                )
        except Exception as exc:  # never let the tick crash the runtime
            log.error("cadence tick failed: %s", exc)

    def _cadence_loop(self) -> None:
        interval = max(30, int(getattr(self.config.cadence, "tick_interval_seconds", 300)))
        # An initial settle so startup isn't contended; then tick on the interval.
        while not self.runtime_stop_event.wait(interval):
            self._cadence_tick_once()
