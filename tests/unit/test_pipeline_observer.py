from __future__ import annotations

import enum
import json
import re
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from holdspeak.redaction import REDACTED, redact_bounded
from holdspeak.services.observer import NullObserver, PipelineEvent, PipelineObserver


def make_event() -> PipelineEvent:
    return PipelineEvent(
        event_id="event-123",
        timestamp=123.456,
        service="PrimitiveService",
        method="create_note",
        principal_kind="user",
        principal_identity="user-123",
        args_summary='{"title":"Note"}',
        result_summary='{"id":"note-123"}',
        error=None,
        error_code=None,
        duration_ms=12.5,
        correlation_id="correlation-123",
        is_async=False,
    )


def test_an_in_transaction_method_is_not_observed() -> None:
    """It runs inside the caller's write transaction, so its event could only
    wait out the busy timeout and be dropped (decide accept took 5 s)."""
    from holdspeak.services.observer import observe_service
    from holdspeak.services.project_service import ProjectService

    @observe_service
    class Probe:
        def write(self) -> str:
            return "w"

        def write_in_transaction(self, conn: object) -> str:
            return "t"

    assert getattr(Probe.write, "__wrapped__", None) is not None
    assert getattr(Probe.write_in_transaction, "__wrapped__", None) is None
    assert getattr(ProjectService.create_item_in_transaction, "__wrapped__", None) is None
    assert getattr(ProjectService.create_item, "__wrapped__", None) is not None


# The summarizer as it was before #1936 (cbb0f06bb), kept here as the
# reference: the runtime must store this text, byte for byte, for every value
# (Codex on #1936). It is a copy on purpose: it must not follow the runtime.
_OLD_CREDENTIAL_KEY = re.compile(
    r"(?i)[A-Za-z0-9_-]*(?:token|password|passwd|secret|api[_-]?key|apikey|credential|authorization)"
)


def _old_redact_tree(value: Any) -> Any:
    if isinstance(value, str):
        return redact_bounded(value)
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            if (isinstance(key, str) and _OLD_CREDENTIAL_KEY.fullmatch(key)
                    and isinstance(item, (str, int, float)) and not isinstance(item, bool)
                    and str(item).strip() and not str(item).isdigit()):
                out[key] = REDACTED
            else:
                out[key] = _old_redact_tree(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_old_redact_tree(item) for item in value]
    return value


def _old_summary(value: Any, limit: int = 2048) -> str:
    try:
        value = _old_redact_tree(value)
    except Exception:
        pass
    try:
        summary = json.dumps(value, default=str, separators=(",", ":"))
    except Exception:
        try:
            summary = repr(value)
        except Exception:
            summary = "<unserializable>"
    summary = redact_bounded(summary)
    if len(summary) > limit:
        return summary[: limit - 1] + "…"
    return summary


def _wrapped(inner: Any, depth: int) -> Any:
    for _ in range(depth):
        inner = {"": inner}
    return inner


def _stored_result_summaries(tmp_path: Path, values: list[Any]) -> list[str]:
    """Each value returned by a real observed method; the result summaries as
    the SQLiteObserver stored them in ``pipeline_events``."""
    from holdspeak.db.core import Database, reset_database
    from holdspeak.services.observer import observed
    from holdspeak.services.sqlite_observer import SQLiteObserver

    reset_database()
    try:
        db = Database(tmp_path / "holdspeak.db")

        class Source:
            def __init__(self) -> None:
                self._observer = SQLiteObserver(db._connection)

            @observed
            def read(self, index: int) -> Any:
                return values[index]

        source = Source()
        for index in range(len(values)):
            source.read(index)
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT result_summary FROM pipeline_events WHERE method = 'read' ORDER BY rowid"
            ).fetchall()
        return [row[0] for row in rows]
    finally:
        reset_database()


def test_a_deeply_nested_result_stores_the_old_summary(tmp_path: Path) -> None:
    """Codex on #1936, findings 1 and 3: a head read closed the nested
    containers, so the stored text was not the old text (220 wrappers: it
    differed at character 1904; a 1933-character result at 2026)."""
    deep = _wrapped([0] * 1000, 220)
    short_raw = _wrapped([{"token": "a"}] * 28 + [0] * 520, 100)
    values = [deep, short_raw, deep, short_raw]  # twice: the kept answers too
    stored = _stored_result_summaries(tmp_path, values)
    assert stored == [_old_summary(value) for value in values]
    assert len(stored[0]) == 2048 and stored[0].endswith("…")


def test_a_result_over_the_guard_stores_only_the_marker(tmp_path: Path) -> None:
    """Codex on #1936, finding 2: past the 1 MB guard the old summary held no
    source text, only the marker; the head read stored 2048 characters of
    it. The stored text is the old text again."""
    over = [{"text": "private-source-sentinel-" + str(i)} for i in range(40000)]
    stored = _stored_result_summaries(tmp_path, [over, over])
    assert stored == [_old_summary(over)] * 2
    assert stored[0].startswith(" [cut: ") and stored[0].endswith(" characters in all]")
    assert "private-source-sentinel" not in stored[0]


def test_a_summary_is_the_old_summary_at_every_size() -> None:
    """The same text as the whole read before #1936, secrets redacted, at
    every size, read twice (the second read is a kept answer)."""
    from holdspeak.services.observer import _truncate

    class Kind(str, enum.Enum):
        SECRET = "Bearer sk-live-0123456789abcdefghijklmnop"

    class Shown(str):
        def __str__(self) -> str:
            return "token=abcdef0123456789zz"

    secret = "Bearer sk-live-0123456789abcdefghijklmnop"
    row = {"title": "Review the cutover", "owner": "Priya", "api_key": "sk-0123456789abcdef0123",
           "detail": f"Authorization: {secret}", "n": 3, "due": None, "tags": ("a", "b")}
    big = {"items": [dict(row, id=f"row-{i}") for i in range(2000)], "count": 2000}
    secret_head = {"items": [{"note": f"Authorization: {secret} " * 40} for _ in range(400)]}
    one_long_string = {"text": "x" * 70000, "after": [1, 2, 3]}
    # A str subclass is never read from a kept plain-text answer.
    lookalikes = [{"k": Kind.SECRET.value}, {"k": Kind.SECRET}, {"k": "token=abcdef0123456789zz"},
                  {"k": Shown("token=abcdef0123456789zz")}, {Shown("password"): "hunter2hunter2"}]
    values = [big, secret_head, one_long_string, row, [row] * 3, "short", list(range(5000)), *lookalikes]
    for _ in range(2):
        for value in values:
            assert _truncate(value) == _old_summary(value)
    assert "sk-live" not in _truncate(big)
