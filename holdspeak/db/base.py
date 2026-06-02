"""Shared base for HoldSpeak persistence repositories (Phase 31, HS-31-01)."""
from __future__ import annotations

import json
from typing import Any


class BaseRepository:
    """Base for per-domain repositories.

    Receives the container's connection factory (a zero-arg callable returning a
    context manager yielding a sqlite3.Connection) and the JSON helpers every
    repository shares.
    """

    def __init__(self, connection):
        self._connection = connection

    def _json_dumps(self, value: object, *, fallback: str) -> str:
        try:
            return json.dumps(value, separators=(",", ":"), sort_keys=True)
        except Exception:
            return fallback

    def _json_loads_list(self, raw: object) -> list[Any]:
        if not isinstance(raw, str) or not raw:
            return []
        try:
            parsed = json.loads(raw)
        except Exception:
            return []
        if not isinstance(parsed, list):
            return []
        return parsed

    def _json_loads_dict(self, raw: object) -> dict[str, Any]:
        if not isinstance(raw, str) or not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except Exception:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {str(key): value for key, value in parsed.items()}
