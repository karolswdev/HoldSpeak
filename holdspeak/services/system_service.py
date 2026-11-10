"""Hub-local callbacks behind the declared system operations.

The composition root binds the running hub's context, never a second runtime.
Reads keep the old fail-soft state and status envelopes. Queue processing is
the owner's press and uses the runtime's existing queue callback.
"""
from __future__ import annotations

from typing import Any

from ..logging_config import get_logger
from .errors import ServiceError, ValidationError

log = get_logger("system_service")


class SystemService:
    def __init__(self, context: Any) -> None:
        self._context = context

    def state(self, principal: Any) -> dict[str, Any]:
        try:
            return self._context.get_state() or {}
        except Exception as exc:
            log.error("get_state failed: %s", exc)
            return {}

    def devices_health(self, principal: Any) -> dict[str, Any]:
        from ..meeting_session import _device_descriptor_to_dict

        return {"devices": [_device_descriptor_to_dict(row) for row in self._context.device_registry.active()]}

    def runtime_status(self, principal: Any) -> dict[str, Any]:
        from ..web.routes.system._shared import _normalize_runtime_status_payload

        state = self.state(principal)
        callback = self._context.on_get_status
        if callback is not None:
            try:
                payload = callback()
            except Exception as exc:
                log.error("on_get_status failed: %s", exc)
                raise ServiceError("runtime_status_failed", str(exc), context={"status": 500}) from exc
            if not isinstance(payload, dict):
                return {"status": "ok", "runtime_status": payload}
        else:
            payload = {}
        return _normalize_runtime_status_payload(payload, state)

    def identity(self, principal: Any) -> dict[str, Any]:
        from ..runtime_identity import identity_report

        return identity_report(detailed=True)

    def process_plugin_jobs(self, principal: Any, *, max_jobs: int | None = None,
                            mode: str = "respect_backoff") -> dict[str, Any]:
        callback = self._context.on_process_plugin_jobs
        if callback is None:
            raise ServiceError("plugin_queue_unavailable", "Deferred plugin queue processing not supported",
                               context={"status": 501})
        if max_jobs is not None and (isinstance(max_jobs, bool) or not isinstance(max_jobs, int) or max_jobs <= 0):
            raise ValidationError("max_jobs must be greater than 0")
        mode = str(mode or "respect_backoff").strip().lower()
        if mode not in {"respect_backoff", "retry_now"}:
            raise ValidationError("mode must be respect_backoff or retry_now")
        data = callback(max_jobs=max_jobs, include_scheduled=mode == "retry_now")
        result = dict(data) if isinstance(data, dict) else {"processed": int(data)}
        result.update(mode=mode, success=True)
        self._context.broadcast("plugin_jobs_processed", result)
        return result
