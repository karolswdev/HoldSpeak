"""HS-36-05 — segment-aware intent probe + probe-augmented scoring.

The deterministic lexical scorer misses brief/paraphrased intents (an incident
described as "it fell over and we rolled it back" matches no `incident` keyword). These
tests cover the probe parser, the injected-chat probe, and the key regression: a window
whose lexical incident score is ~0 becomes active once the probe flags it — while the
no-probe path stays byte-identical to lexical-only scoring.
"""

from __future__ import annotations

from holdspeak.plugins.contracts import IntentWindow
from holdspeak.plugins.router import select_active_intents
from holdspeak.plugins.scoring import score_window
from holdspeak.plugins.segment_probe import (
    build_segment_probe,
    parse_probe_scores,
    probe_intents,
)


def _window(transcript: str) -> IntentWindow:
    return IntentWindow(
        window_id="m:w0",
        meeting_id="m",
        start_seconds=0.0,
        end_seconds=90.0,
        transcript=transcript,
    )


# An incident described in plain English — matches none of the incident keywords
# (incident/outage/sev/rollback/...). The lexical scorer scores it ~0.
_NATURAL_INCIDENT = (
    "So checkout fell over on Tuesday afternoon and was down for half an hour. "
    "We ended up rolling it back. Turned out a bad deploy ate the connection pool."
)


class TestParseProbeScores:
    def test_fenced_json(self):
        raw = 'here:\n```json\n{"incident": 0.9, "comms": 0.7}\n```\n'
        assert parse_probe_scores(raw) == {"incident": 0.9, "comms": 0.7}

    def test_bare_json_object(self):
        assert parse_probe_scores('{"product": 0.8}') == {"product": 0.8}

    def test_unknown_keys_dropped_and_clamped(self):
        raw = '{"incident": 1.4, "delivery": -0.2, "bogus": 0.9, "product": "nope"}'
        # 1.4 -> 1.0, -0.2 -> 0.0, unknown dropped, non-numeric dropped.
        assert parse_probe_scores(raw) == {"incident": 1.0, "delivery": 0.0}

    def test_garbage_returns_empty(self):
        assert parse_probe_scores("not json at all") == {}
        assert parse_probe_scores("") == {}


class TestProbeIntents:
    def test_injected_chat_fn(self):
        def fake(messages, **kw):
            assert messages[-1]["content"]  # the transcript is passed through
            return '```json\n{"incident": 0.92}\n```'

        assert probe_intents(_NATURAL_INCIDENT, chat_fn=fake) == {"incident": 0.92}

    def test_empty_transcript_skips_call(self):
        called = {"n": 0}

        def fake(messages, **kw):
            called["n"] += 1
            return "{}"

        assert probe_intents("   ", chat_fn=fake) == {}
        assert called["n"] == 0  # no LLM call for empty text

    def test_chat_failure_degrades_to_empty(self):
        def boom(messages, **kw):
            raise RuntimeError("endpoint down")

        assert probe_intents(_NATURAL_INCIDENT, chat_fn=boom) == {}

    def test_build_segment_probe_over_fake_intel(self):
        class FakeIntel:
            def _chat_completion_text(self, messages, *, temperature, max_tokens):
                return '{"comms": 0.8}'

        probe = build_segment_probe(FakeIntel())
        assert probe(_NATURAL_INCIDENT) == {"comms": 0.8}


class TestProbeAugmentedScoring:
    def test_no_probe_is_lexical_identical(self):
        win = _window(_NATURAL_INCIDENT)
        assert score_window(win).scores == score_window(win, probe=None).scores

    def test_lexical_only_misses_natural_incident(self):
        # Regression baseline: without the probe, the natural-language incident does
        # NOT activate the incident intent (the weakness HS-36-04 captured).
        score = score_window(_window(_NATURAL_INCIDENT))
        assert score.scores["incident"] < score.threshold
        assert "incident" not in select_active_intents(score.scores, threshold=score.threshold)

    def test_probe_fishes_out_the_dropped_intent(self):
        # With the probe flagging incident, the same window now activates it.
        probe = lambda _t: {"incident": 0.9}  # noqa: E731 - tiny test stub
        score = score_window(_window(_NATURAL_INCIDENT), probe=probe)
        assert score.scores["incident"] >= 0.9
        assert "incident" in select_active_intents(score.scores, threshold=score.threshold)

    def test_probe_only_raises_never_suppresses(self):
        # A window with a strong lexical signal isn't lowered by a small probe value.
        strong = _window("We need to discuss the API schema and the service latency design.")
        lexical = score_window(strong).scores["architecture"]
        assert lexical > 0.0
        probed = score_window(strong, probe=lambda _t: {"architecture": 0.0}).scores["architecture"]
        assert probed == lexical  # max(lexical, 0.0) == lexical

    def test_probe_exception_falls_back_to_lexical(self):
        def boom(_t):
            raise RuntimeError("probe blew up")

        win = _window(_NATURAL_INCIDENT)
        assert score_window(win, probe=boom).scores == score_window(win).scores
