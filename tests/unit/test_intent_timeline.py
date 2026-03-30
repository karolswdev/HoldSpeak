from __future__ import annotations

from holdspeak.intent_timeline import build_intent_windows, detect_intent_transitions


def test_build_intent_windows_creates_overlapping_windows() -> None:
    segments = [
        {"start_time": 0.0, "end_time": 10.0, "text": "Architecture overview", "speaker": "Me"},
        {"start_time": 14.0, "end_time": 24.0, "text": "Delivery timeline and owners", "speaker": "Remote"},
        {"start_time": 33.0, "end_time": 44.0, "text": "Incident mitigation follow-up", "speaker": "Me"},
    ]

    windows = build_intent_windows(
        segments,
        meeting_id="meeting-123",
        window_seconds=20.0,
        step_seconds=10.0,
    )

    assert len(windows) == 5
    assert windows[0].window_id == "meeting-123:w0000"
    assert windows[0].transcript == "Architecture overview Delivery timeline and owners"
    assert windows[1].transcript == "Delivery timeline and owners"
    assert windows[2].transcript == "Delivery timeline and owners Incident mitigation follow-up"
    assert windows[3].transcript == "Incident mitigation follow-up"
    assert windows[4].transcript == "Incident mitigation follow-up"


def test_build_intent_windows_sorts_and_filters_invalid_segments() -> None:
    windows = build_intent_windows(
        [
            {"start_time": 20.0, "end_time": 30.0, "text": "Second"},
            {"start_time": 0.0, "end_time": 5.0, "text": "First"},
            {"start_time": 5.0, "end_time": 6.0, "text": " "},
        ],
        meeting_id="m-1",
        window_seconds=15.0,
        step_seconds=15.0,
    )
    assert [w.window_id for w in windows] == ["m-1:w0000", "m-1:w0001"]
    assert windows[0].transcript == "First"
    assert windows[1].transcript == "Second"


def test_detect_intent_transitions_reports_added_and_removed_intents() -> None:
    transitions = detect_intent_transitions(
        [
            ("w0", ["architecture"]),
            ("w1", ["architecture", "delivery"]),
            ("w2", ["delivery"]),
            ("w3", ["delivery"]),
        ]
    )

    assert len(transitions) == 3
    assert transitions[0]["window_id"] == "w0"
    assert transitions[0]["added"] == ["architecture"]
    assert transitions[1]["added"] == ["delivery"]
    assert transitions[2]["removed"] == ["architecture"]
