"""HS-60-01 — the wake-word engine seam, tested with no engine installed.

The contract: detection at/above the threshold fires once and then the
refractory cooldown holds; pause drains frames without scoring and resume
resets the detector (stale audio can never fire); the loop ends on a closed
source or stop(); the optional engine hides behind lazy imports so this
file (and CI) never needs the `[wakeword]` extra.
"""
from __future__ import annotations

import numpy as np
import pytest

from holdspeak.config import Config, WakeWordConfig
from holdspeak.wake_word import FRAME_SAMPLES, WakeWordListener, wake_word_available


class FakeDetector:
    """Scripted scores + a reset counter."""

    def __init__(self, scores):
        self.scores = list(scores)
        self.resets = 0
        self.predicted = 0

    def predict(self, frame):
        self.predicted += 1
        return self.scores.pop(0) if self.scores else 0.0

    def reset(self):
        self.resets += 1


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _frames(n):
    """A source yielding n silent frames then closing."""
    remaining = {"n": n}

    def source():
        if remaining["n"] <= 0:
            return None
        remaining["n"] -= 1
        return np.zeros(FRAME_SAMPLES, dtype=np.int16)

    return source


def _listener(detector, n_frames, clock=None, **kw):
    hits: list[float] = []
    listener = WakeWordListener(
        detector=detector,
        frames=_frames(n_frames),
        on_detect=hits.append,
        clock=clock or FakeClock(),
        **kw,
    )
    return listener, hits


# ── detection + threshold ────────────────────────────────────────────────────


def test_detection_fires_at_threshold():
    detector = FakeDetector([0.1, 0.5, 0.1])
    listener, hits = _listener(detector, 3, threshold=0.5)
    listener.run()
    assert hits == [0.5]
    assert detector.resets == 1  # state cleared after a hit


def test_below_threshold_never_fires():
    listener, hits = _listener(FakeDetector([0.49, 0.4, 0.3]), 3, threshold=0.5)
    listener.run()
    assert hits == []


# ── the refractory cooldown ──────────────────────────────────────────────────


def test_refractory_blocks_the_double_arm():
    # Scores stay hot after a hit (the openwakeword reality); only one
    # detection may fire inside the cooldown.
    clock = FakeClock()
    detector = FakeDetector([0.9, 0.9, 0.9, 0.9])
    listener, hits = _listener(detector, 4, clock=clock, refractory_seconds=2.0)
    listener.run()
    assert hits == [0.9]


def test_detection_fires_again_after_the_cooldown():
    clock = FakeClock()
    detector = FakeDetector([0.9, 0.9])

    hits: list[float] = []
    frames = _frames(2)

    def ticking_frames():
        frame = frames()
        return frame

    listener = WakeWordListener(
        detector=detector,
        frames=ticking_frames,
        on_detect=lambda s: (hits.append(s), setattr(clock, "now", clock.now + 3.0)),
        threshold=0.5,
        refractory_seconds=2.0,
        clock=clock,
    )
    listener.run()
    assert hits == [0.9, 0.9]


# ── pause / resume ───────────────────────────────────────────────────────────


def test_paused_frames_are_drained_but_never_scored():
    detector = FakeDetector([0.9] * 5)
    listener, hits = _listener(detector, 5)
    listener.pause()
    listener.run()
    assert hits == []
    assert detector.predicted == 0  # drained, not scored


def test_resume_resets_the_detector_and_rearms_the_cooldown():
    clock = FakeClock()
    detector = FakeDetector([0.9, 0.9])
    listener, hits = _listener(detector, 2, clock=clock, refractory_seconds=2.0)
    listener.pause()
    listener.resume()
    assert detector.resets == 1
    # The post-resume cooldown holds: the first hot frame must not fire.
    listener.run()
    assert hits == []


def test_pause_and_resume_are_idempotent():
    detector = FakeDetector([])
    listener, _ = _listener(detector, 0)
    listener.pause()
    listener.pause()
    listener.resume()
    listener.resume()  # a second resume must not reset again
    assert detector.resets == 1
    assert listener.paused is False


# ── lifecycle ────────────────────────────────────────────────────────────────


def test_loop_ends_when_the_source_closes():
    listener, hits = _listener(FakeDetector([0.0]), 1)
    listener.run()  # returns: source yielded one frame then None
    assert hits == []


def test_start_stop_joins_the_thread():
    import threading

    gate = threading.Event()

    def blocking_frames():
        gate.wait(0.05)
        return None  # close promptly so stop() joins fast

    listener = WakeWordListener(
        detector=FakeDetector([]),
        frames=blocking_frames,
        on_detect=lambda s: None,
    )
    listener.start()
    listener.start()  # idempotent
    gate.set()
    listener.stop()
    assert listener._thread is None


def test_exploding_on_detect_never_kills_the_loop():
    detector = FakeDetector([0.9, 0.0, 0.0])
    boom_then_count: list[float] = []

    def on_detect(score):
        boom_then_count.append(score)
        raise RuntimeError("observer boom")

    listener = WakeWordListener(
        detector=detector,
        frames=_frames(3),
        on_detect=on_detect,
        clock=FakeClock(),
    )
    listener.run()  # must not raise
    assert boom_then_count == [0.9]
    assert detector.predicted == 3  # the loop survived


# ── the optional engine stays optional ───────────────────────────────────────


def test_module_imports_without_the_engine():
    # This very file imported holdspeak.wake_word at the top with no
    # openwakeword requirement; the availability probe is bool either way.
    assert wake_word_available() in (True, False)


def test_lazy_imports_only():
    import holdspeak.wake_word as mod

    top_level = [
        l.strip()
        for l in open(mod.__file__)
        if l.startswith(("import ", "from "))
    ]
    for line in top_level:
        assert "openwakeword" not in line, f"engine import must be lazy: {line}"


# ── config ───────────────────────────────────────────────────────────────────


def test_wake_config_defaults_off():
    cfg = WakeWordConfig()
    assert cfg.enabled is False
    assert cfg.action == "preview"
    assert cfg.model == "hey_jarvis"
    assert Config().wake_word.enabled is False


def test_wake_config_normalizes_file_edited_values():
    cfg = WakeWordConfig(threshold="2.5", armed_window_seconds=1, action="TYPE")
    assert cfg.threshold == 1.0  # clamped
    assert cfg.armed_window_seconds == 2.0  # clamped
    assert cfg.action == "type"
    assert WakeWordConfig(action="sideways").action == "preview"


def test_older_config_shape_coerces_forward():
    # A config without the section loads with defaults (the _coerce path).
    assert WakeWordConfig(**{}).enabled is False
