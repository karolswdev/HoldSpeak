"""AIPI-4-14 — meeting-stats view formatter + cycle tests."""

from __future__ import annotations

from holdspeak.device_meeting_stats import (
    CYCLE_ORDER,
    VIEW_INTEL,
    VIEW_NUMBERS,
    VIEW_SPEAKERS,
    format_intel_view,
    format_numbers_view,
    format_speakers_view,
    pick_next_view,
    render_view_for_state,
)


class _Segment:
    def __init__(self, speaker: str | None = None) -> None:
        self.speaker = speaker


class _Action:
    def __init__(self, task: str = "", owner: str = "") -> None:
        self.task = task
        self.owner = owner


class _Intel:
    def __init__(
        self,
        topics: list[str] | None = None,
        action_items: list | None = None,
    ) -> None:
        self.topics = topics or []
        self.action_items = action_items or []


class _State:
    def __init__(
        self,
        *,
        duration: float = 0.0,
        segments: list | None = None,
        bookmarks: list | None = None,
        intel=None,
    ) -> None:
        self.duration = duration
        self.segments = segments or []
        self.bookmarks = bookmarks or []
        self.intel = intel


# ---------- format_numbers_view ----------


def test_numbers_view_zero_state():
    out = format_numbers_view(_State())
    assert "Stats:" in out
    assert "Recording: 00:00" in out
    assert "Segments: 0" in out
    assert "Bookmarks: 0" in out


def test_numbers_view_mid_meeting():
    state = _State(
        duration=125.0,
        segments=[_Segment("Karol")] * 7,
        bookmarks=[object(), object()],
    )

    out = format_numbers_view(state)

    assert "Recording: 02:05" in out
    assert "Segments: 7" in out
    assert "Bookmarks: 2" in out


def test_numbers_view_hour_plus():
    state = _State(duration=3725.0)
    out = format_numbers_view(state)
    assert "Recording: 01:02:05" in out


# ---------- format_speakers_view ----------


def test_speakers_view_empty_falls_back():
    out = format_speakers_view(_State())
    assert "Speakers:" in out
    assert "None yet" in out


def test_speakers_view_top_three_counted():
    segments = (
        [_Segment("Karol")] * 5
        + [_Segment("Remote")] * 3
        + [_Segment("Me")] * 2
        + [_Segment("Other")] * 1
    )
    state = _State(segments=segments)

    out = format_speakers_view(state)

    assert "- Karol: 5" in out
    assert "- Remote: 3" in out
    assert "- Me: 2" in out
    # Beyond top 3.
    assert "Other" not in out


def test_speakers_view_handles_missing_speaker():
    state = _State(segments=[_Segment(None), _Segment("Karol")])
    out = format_speakers_view(state)
    # ? bucket for unspecified speakers.
    assert "- ?: 1" in out


# ---------- format_intel_view ----------


def test_intel_view_no_intel():
    out = format_intel_view(_State())
    assert "Intel:" in out
    assert "Not yet ready" in out


def test_intel_view_topics_and_action():
    intel = _Intel(
        topics=["Auth refactor", "Q4 planning", "Latency"],
        action_items=[_Action(task="schema doc", owner="Karol")],
    )
    state = _State(intel=intel)

    out = format_intel_view(state)

    assert "Intel:" in out
    assert "Topics: Auth refactor, Q4 planning, Latency" in out
    assert "Next: Karol: schema doc" in out


def test_intel_view_topics_only():
    intel = _Intel(topics=["x"])
    out = format_intel_view(_State(intel=intel))
    assert "Topics: x" in out
    assert "Next:" not in out


def test_intel_view_action_dict_shape():
    intel = _Intel(action_items=[{"task": "ship", "owner": "Karol"}])
    out = format_intel_view(_State(intel=intel))
    assert "Karol: ship" in out


def test_intel_view_empty_intel_object():
    intel = _Intel()
    out = format_intel_view(_State(intel=intel))
    assert "No content yet" in out


# ---------- pick_next_view (cycle) ----------


def test_cycle_advances_in_order():
    next_index, view_id, _ = pick_next_view(-1)
    assert next_index == 0
    assert view_id == VIEW_NUMBERS

    next_index, view_id, _ = pick_next_view(0)
    assert next_index == 1
    assert view_id == VIEW_SPEAKERS

    next_index, view_id, _ = pick_next_view(1)
    assert next_index == 2
    assert view_id == VIEW_INTEL

    next_index, view_id, _ = pick_next_view(2)
    assert next_index == 0
    assert view_id == VIEW_NUMBERS


def test_cycle_order_constant():
    assert CYCLE_ORDER == (VIEW_NUMBERS, VIEW_SPEAKERS, VIEW_INTEL)


# ---------- render_view_for_state dispatch ----------


def test_render_dispatches_by_view_id():
    state = _State(duration=60.0)
    assert "Recording: 01:00" in render_view_for_state(VIEW_NUMBERS, state)
    assert "Speakers:" in render_view_for_state(VIEW_SPEAKERS, state)
    assert "Intel:" in render_view_for_state(VIEW_INTEL, state)


def test_render_unknown_view_id():
    out = render_view_for_state("not_a_view", _State())
    assert "Unknown view" in out
