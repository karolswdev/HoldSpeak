from __future__ import annotations

from holdspeak.activity_tracker import RuntimeActivityTracker, desktop_window_policy, normalize_activity_state


def test_desktop_window_policy_is_transient() -> None:
    assert desktop_window_policy("idle") == {
        "mode": "hidden",
        "visible": False,
        "linger_ms": 0,
    }

    recording = desktop_window_policy("recording")
    assert recording["mode"] == "active"
    assert recording["visible"] is True
    assert recording["linger_ms"] == 0

    meeting_live = desktop_window_policy("meeting_live")
    assert meeting_live["mode"] == "linger"
    assert meeting_live["visible"] is True
    assert meeting_live["linger_ms"] > 0

    typing = desktop_window_policy("typing")
    assert typing["mode"] == "active"
    assert typing["visible"] is True
    assert typing["linger_ms"] == 0

    typed = desktop_window_policy("complete")
    assert typed["mode"] == "linger"
    assert typed["visible"] is True
    assert typed["linger_ms"] > 0


def test_activity_tracker_tracker_updates_snapshot_and_window_policy() -> None:
    stamps = iter(
        [
            "2026-06-05T10:00:00",
            "2026-06-05T10:00:01",
            "2026-06-05T10:00:02",
        ]
    )
    tracker = RuntimeActivityTracker(clock=lambda: next(stamps))

    recording = tracker.update(
        "recording",
        source="hotkey",
        detail="HoldSpeak is listening.",
        last_event="dictation_recording_started",
    )
    assert recording["state"] == "recording"
    assert recording["source"] == "hotkey"
    assert recording["label"] == "Recording"
    assert recording["started_at"] == "2026-06-05T10:00:01"
    assert recording["updated_at"] == "2026-06-05T10:00:01"
    assert recording["window"]["mode"] == "active"

    still_recording = tracker.update("recording", source="hotkey", detail="Still listening.")
    assert still_recording["started_at"] == "2026-06-05T10:00:01"
    assert still_recording["updated_at"] == "2026-06-05T10:00:02"


def test_unknown_activity_state_normalizes_to_idle() -> None:
    assert normalize_activity_state("surprised") == "idle"
    assert desktop_window_policy("surprised")["mode"] == "hidden"
