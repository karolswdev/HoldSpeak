"""Shared, server-agnostic helpers for the web layer (HS-26-06).

These three pieces are used by both `web_server` (the assembler / runtime) and the
extracted route modules. Homing them here lets the `routes/` package depend on a
neutral module instead of importing back into `web_server` (the monolith the
Phase 26 decomposition is dismantling).

- `UnknownDeviceError` — raised by the meeting-start callback when a requested
  device id is not registered; the meeting routes map it to a 404.
- `meeting_callback_payload` — normalize a lifecycle-callback result (an object
  with `to_dict()`, a dict, or neither) into a JSON-able payload or `None`.
- `parse_iso_datetime` — lenient ISO-8601 parse used by duration formatting and
  the activity meeting-candidate routes.

The names keep their historical leading underscore via module-level aliases so
existing call sites (`_UnknownDeviceError`, `_meeting_callback_payload`,
`_parse_iso_datetime`) read unchanged after switching their import line.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi.responses import JSONResponse


class UnknownDeviceError(LookupError):
    """Raised by ``on_start`` when a requested device id is not registered.

    The route maps this to a 404 with the offending ``device_id``
    surfaced in the JSON body so the caller can correct its
    request without polling the registry.
    """

    def __init__(self, device_id: str) -> None:
        super().__init__(f"Unknown device id: {device_id!r}")
        self.device_id = device_id


def meeting_callback_payload(result: Any) -> Any:
    if hasattr(result, "to_dict"):
        try:
            return result.to_dict()
        except Exception:
            return None
    if isinstance(result, dict):
        return result
    return None


def parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def error_500(exc: Exception, logger: logging.Logger, detail: str) -> JSONResponse:
    """The one place the web routes' generic 500 response is shaped (HS-32-05).

    Replaces the ~48 duplicated ``log.error(f"<detail>: {e}"); return
    JSONResponse({"error": str(e)}, status_code=500)`` blocks across the route
    modules. Behavior-preserving: same log line, same response body + status.
    ``detail`` is the already-formatted message (the caller keeps any f-string
    interpolation), so this reproduces the original ``log.error`` exactly.
    """
    logger.error(f"{detail}: {exc}")
    return JSONResponse({"error": str(exc)}, status_code=500)


# Backwards-friendly aliases so call sites keep their underscore-prefixed names.
_UnknownDeviceError = UnknownDeviceError
_meeting_callback_payload = meeting_callback_payload
_parse_iso_datetime = parse_iso_datetime
_error_500 = error_500
