from __future__ import annotations

import logging
from typing import Any, Callable

from holdspeak.services.observer import PipelineEvent


_log = logging.getLogger(__name__)

_INSERT_SQL = """
INSERT INTO pipeline_events (
    event_id, timestamp, service, method,
    principal_kind, principal_identity,
    args_summary, result_summary,
    error, error_code, duration_ms,
    correlation_id, is_async
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class SQLiteObserver:
    def __init__(self, connection: Callable[..., Any]) -> None:
        self._connection = connection

    def on_event(self, event: PipelineEvent) -> None:
        try:
            with self._connection() as conn:
                conn.execute(
                    _INSERT_SQL,
                    (
                        event.event_id,
                        event.timestamp,
                        event.service,
                        event.method,
                        event.principal_kind,
                        event.principal_identity,
                        event.args_summary,
                        event.result_summary,
                        event.error,
                        event.error_code,
                        event.duration_ms,
                        event.correlation_id,
                        int(event.is_async),
                    ),
                )
        except Exception:
            _log.warning("Failed to write pipeline event", exc_info=True)
