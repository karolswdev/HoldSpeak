"""HS-S54: one home for the stored "now" shapes, the lenient UTC reader and
the prefixed random id.

Before, each shape had its own copy in 50 modules (``_now``, ``_now_iso``,
``_iso_now``, ``_utc_now``, ``_parse_iso``, ``_parse_ts``, ``_new_id``). Each
module now imports the one function under its old private name, so a test can
still patch ``module._now``. This file holds each shape to the exact text the
old copies made, and each module's name to the one function.
"""
from __future__ import annotations

import importlib
import re
from datetime import datetime, timedelta, timezone

import pytest

from holdspeak import ids, timestamps

# A frozen instant with microseconds, and one on a whole second: the "auto"
# shapes drop the fraction only on the second one.
FRACTION = datetime(2026, 11, 8, 12, 0, 1, 250000, tzinfo=timezone.utc)
WHOLE = datetime(2026, 11, 8, 12, 0, 1, tzinfo=timezone.utc)


class _Frozen(datetime):
    at = FRACTION

    @classmethod
    def now(cls, tz=None):  # noqa: D102 - the frozen clock
        return cls.at if tz is not None else cls.at.replace(tzinfo=None)


@pytest.fixture
def frozen(monkeypatch):
    monkeypatch.setattr(timestamps, "datetime", _Frozen)
    monkeypatch.setattr(_Frozen, "at", FRACTION)
    return _Frozen


# The exact body of the old copies, per shape.
OLD_BODIES = {
    "utc_now_iso": lambda now: now.isoformat(),
    "utc_now_seconds": lambda now: now.isoformat(timespec="seconds"),
    "utc_now_z": lambda now: now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "utc_now_z_micro": lambda now: now.isoformat(timespec="microseconds").replace("+00:00", "Z"),
    "utc_now_iso_z": lambda now: now.isoformat().replace("+00:00", "Z"),
}


def test_the_shapes_stay_apart(frozen) -> None:
    texts = {name: getattr(timestamps, name)() for name in OLD_BODIES}
    assert texts == {
        "utc_now_iso": "2026-11-08T12:00:01.250000+00:00",
        "utc_now_seconds": "2026-11-08T12:00:01+00:00",
        "utc_now_z": "2026-11-08T12:00:01Z",
        "utc_now_z_micro": "2026-11-08T12:00:01.250000Z",
        "utc_now_iso_z": "2026-11-08T12:00:01.250000Z",
    }


# ── semantic 1: None on bad input (parse_utc_iso) ─────────────────────

@pytest.mark.parametrize("value", [None, "", 0, False, "not a time", "2026-13-40", object()])
def test_parse_utc_iso_is_none_on_bad_input(value) -> None:
    assert timestamps.parse_utc_iso(value) is None


def test_parse_utc_iso_reads_z_naive_and_offset() -> None:
    utc = timezone.utc
    assert timestamps.parse_utc_iso("2026-11-08T12:00:00Z") == datetime(2026, 11, 8, 12, tzinfo=utc)
    # A value with no zone is UTC (not hub-local, as parse_stamp reads it).
    naive = timestamps.parse_utc_iso("2026-11-08T12:00:00")
    assert naive == datetime(2026, 11, 8, 12, tzinfo=utc) and naive.tzinfo is utc
    # An offset is kept, not moved to UTC.
    offset = timestamps.parse_utc_iso("2026-11-08T05:00:00-07:00")
    assert offset.utcoffset() == timedelta(hours=-7)
    assert offset == datetime(2026, 11, 8, 12, tzinfo=utc)
    # A datetime reads through its str form; a naive one is UTC.
    assert timestamps.parse_utc_iso(datetime(2026, 11, 8, 12)) == datetime(2026, 11, 8, 12, tzinfo=utc)


# ── semantic 2: the other readers keep their own contracts ────────────

def test_parse_iso_datetime_keeps_a_naive_value_naive() -> None:
    assert timestamps.parse_iso_datetime("2026-11-08T12:00:00").tzinfo is None
    assert timestamps.parse_iso_datetime("garbage") is None


def test_the_delta_cursor_reader_defaults_to_the_earliest_time() -> None:
    # Semantic 3: a default, never None or an error (the cursor compare).
    from holdspeak.services.project_delta_service import _parse_utc

    earliest = datetime.min.replace(tzinfo=timezone.utc)
    assert _parse_utc("") == earliest
    assert _parse_utc("garbage") == earliest
    assert _parse_utc("2026-11-08T05:00:00-07:00") == datetime(2026, 11, 8, 12, tzinfo=timezone.utc)


# ── the prefixed random id ────────────────────────────────────────────

def test_new_id_is_prefix_and_twelve_fresh_hex() -> None:
    first, second = ids.new_id("note"), ids.new_id("note")
    assert re.fullmatch(r"note_[0-9a-f]{12}", first)
    assert first != second
    assert re.fullmatch(r"automation-with_[0-9a-f]{12}", ids.new_id("automation-with"))


# ── each module's old name is the one function ────────────────────────

ONE_HOME = {
    ids.new_id: [
        "holdspeak.db.threads._new_id", "holdspeak.services.primitive_service._new_id",
        "holdspeak.services.recipe_service._new_id", "holdspeak.services.support._new_id",
        "holdspeak.services.workbench_service._new_id", "holdspeak.skills_library._new_id",
        "holdspeak.web.routes.primitives._shared._new_id",
    ],
    timestamps.parse_utc_iso: [
        "holdspeak.delivery.attempts._parse_ts", "holdspeak.delivery.commands._parse_iso",
        "holdspeak.delivery.factory_launch._parse_ts", "holdspeak.delivery.follow_through._parse",
        "holdspeak.services.preparation_brief_service._parse_iso",
        "holdspeak.services.agent_flights._stamp",
        "holdspeak.services.door_service.DoorService._parse_iso",
    ],
    timestamps.utc_now_iso: [
        "holdspeak.net_bounds._now_iso", "holdspeak.services.agent_hand_service._iso_now",
        "holdspeak.services.agent_review._now", "holdspeak.services.inference_default_service._now",
        "holdspeak.services.project_door_service._iso_now", "holdspeak.services.project_repository._now",
    ],
    timestamps.utc_now_seconds: [
        "holdspeak.db.memory_index._now", "holdspeak.memory.consolidate._now", "holdspeak.people.store._now",
        "holdspeak.services.heartbeat_service._now_iso", "holdspeak.services.project_delta_service._now_iso",
        "holdspeak.services.project_evidence_collector._now_iso",
        "holdspeak.services.project_steward_service._now_iso",
    ],
    timestamps.utc_now_z: [
        "holdspeak.db.primitives._now_iso", "holdspeak.db.refinement_thoughts._now",
        "holdspeak.db.workbenches._now_iso", "holdspeak.scheduled_recording_conductor._now_iso",
        "holdspeak.services.people_service._now", "holdspeak.delivery.collector._utc_now",
        "holdspeak.delivery.first_message._iso_now", "holdspeak.delivery.pr_receipts._utc_now",
        "holdspeak.services.launch_rebrief._now",
    ],
    timestamps.utc_now_z_micro: [
        "holdspeak.db.front_door._now", "holdspeak.db.task_resume._now",
        "holdspeak.services.assignment_migration._now",
        "holdspeak.services.inference_assignment_service._now",
        "holdspeak.services.model_library_service._now", "holdspeak.services.model_profile_service._now",
    ],
    timestamps.utc_now_iso_z: [
        "holdspeak.services.agent_hand_queue._now", "holdspeak.services.inference_acquisition_service._now",
        "holdspeak.services.local_ai_setup_service._now", "holdspeak.services.meaning_search_service._now",
    ],
    timestamps.utc_now: [
        "holdspeak.delivery.commands._utc_now", "holdspeak.delivery.follow_through._now",
        "holdspeak.services.channel_service._now",
    ],
}


def _resolve(dotted: str):
    parts = dotted.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        try:
            value = importlib.import_module(".".join(parts[:cut]))
        except ModuleNotFoundError:
            continue
        for attr in parts[cut:]:
            value = getattr(value, attr)
        return value
    raise ImportError(dotted)


