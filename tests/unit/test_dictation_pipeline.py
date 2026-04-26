"""Unit tests for the DIR-01 dictation pipeline executor (HS-1-03)."""

from __future__ import annotations

from datetime import datetime, timezone

from holdspeak.plugins.dictation.contracts import (
    IntentTag,
    StageResult,
    Utterance,
)
from holdspeak.plugins.dictation.pipeline import DictationPipeline, PipelineRun


def _utt(text: str = "hello world") -> Utterance:
    return Utterance(
        raw_text=text,
        audio_duration_s=1.0,
        transcribed_at=datetime(2026, 4, 25, tzinfo=timezone.utc),
    )


class _Stage:
    """Minimal Transducer-conforming test stage."""

    def __init__(
        self,
        sid: str,
        *,
        transform=None,
        intent: IntentTag | None = None,
        requires_llm: bool = False,
        warnings: list[str] | None = None,
        raises: type[BaseException] | None = None,
        record_prior: list[list[str]] | None = None,
    ) -> None:
        self.id = sid
        self.version = "0.1.0"
        self.requires_llm = requires_llm
        self._transform = transform or (lambda t: t)
        self._intent = intent
        self._warnings = warnings or []
        self._raises = raises
        self._record_prior = record_prior

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult:
        if self._record_prior is not None:
            self._record_prior.append([r.stage_id for r in prior])
        if self._raises is not None:
            raise self._raises(f"boom from {self.id}")
        text = self._transform(prior[-1].text if prior else utt.raw_text)
        return StageResult(
            stage_id=self.id,
            text=text,
            intent=self._intent,
            elapsed_ms=0.0,
            warnings=list(self._warnings),
        )


def _fake_clock():
    """Deterministic clock: 1ms per tick."""
    state = {"t": 0.0}

    def now() -> float:
        state["t"] += 0.001
        return state["t"]

    return now


# DIR-F-002
def test_disabled_pipeline_is_noop():
    seen: list[PipelineRun] = []
    s = _Stage("a", transform=lambda t: t.upper())
    p = DictationPipeline([s], enabled=False, on_run=seen.append)

    run = p.run(_utt("hello"))

    assert run.final_text == "hello"
    assert run.stage_results == []
    assert run.intent is None
    assert run.warnings == []
    assert run.short_circuited is True
    assert seen == []  # on_run not invoked when disabled
    assert p.recent_runs() == []  # disabled runs are not buffered


# DIR-F-001
def test_stages_execute_in_declared_order_and_see_prior_results():
    priors: list[list[str]] = []
    s1 = _Stage("first", record_prior=priors)
    s2 = _Stage("second", record_prior=priors)
    s3 = _Stage("third", record_prior=priors)
    p = DictationPipeline([s1, s2, s3])

    p.run(_utt())

    assert priors == [[], ["first"], ["first", "second"]]


def test_text_threads_through_stages():
    s1 = _Stage("up", transform=str.upper)
    s2 = _Stage("excl", transform=lambda t: t + "!")
    p = DictationPipeline([s1, s2])

    run = p.run(_utt("hi"))

    assert run.final_text == "HI!"
    assert [r.stage_id for r in run.stage_results] == ["up", "excl"]
    assert run.short_circuited is False


# DIR-F-003
def test_stage_exception_short_circuits_to_input_text():
    s1 = _Stage("good", transform=str.upper)
    s2 = _Stage("bad", raises=RuntimeError)
    s3 = _Stage("never", transform=lambda t: t + "?")
    p = DictationPipeline([s1, s2, s3])

    run = p.run(_utt("hello"))

    assert run.final_text == "hello"
    assert run.short_circuited is True
    assert [r.stage_id for r in run.stage_results] == ["good", "bad"]
    assert run.stage_results[-1].metadata.get("failed") is True
    # Third stage never ran.
    assert all(r.stage_id != "never" for r in run.stage_results)


def test_stage_exception_warning_is_structured():
    s1 = _Stage("bad", raises=ValueError)
    p = DictationPipeline([s1])

    run = p.run(_utt())

    assert any(
        w.startswith("bad: ValueError:") for w in run.warnings
    ), run.warnings


# DIR-F-011
def test_llm_disabled_skips_requires_llm_stages():
    s1 = _Stage("router", transform=str.upper, requires_llm=True)
    s2 = _Stage("enricher", transform=lambda t: t + "!")
    p = DictationPipeline([s1, s2], llm_enabled=False)

    run = p.run(_utt("hi"))

    assert [r.stage_id for r in run.stage_results] == ["enricher"]
    # enricher runs against the original raw_text since router was skipped.
    assert run.final_text == "hi!"
    assert any("router: skipped" in w for w in run.warnings)
    assert run.short_circuited is False


def test_intent_propagates_to_pipeline_run():
    tag = IntentTag(
        matched=True,
        block_id="ai_prompt",
        confidence=0.9,
        raw_label="ai_prompt",
    )
    s1 = _Stage("router", intent=tag)
    s2 = _Stage("enricher", transform=str.upper)
    p = DictationPipeline([s1, s2])

    run = p.run(_utt("x"))

    assert run.intent is tag


# DIR-F-009
def test_recent_runs_ring_buffer_caps_at_n():
    p = DictationPipeline([_Stage("noop")], ring_buffer_size=3)

    for i in range(5):
        p.run(_utt(f"t{i}"))

    runs = p.recent_runs()
    assert len(runs) == 3
    # Newest last.
    assert runs[-1].final_text == "t4"
    assert runs[0].final_text == "t2"


def test_on_run_callback_invoked_after_buffer_append():
    observations: list[tuple[int, str]] = []
    p_holder: dict = {}

    def hook(run: PipelineRun) -> None:
        # When the hook fires, the buffer must already contain this run.
        buf = p_holder["p"].recent_runs()
        observations.append((len(buf), buf[-1].final_text))

    s = _Stage("noop")
    p = DictationPipeline([s], on_run=hook)
    p_holder["p"] = p

    p.run(_utt("a"))
    p.run(_utt("b"))

    assert observations == [(1, "a"), (2, "b")]


def test_on_run_exception_does_not_propagate():
    def hook(run: PipelineRun) -> None:
        raise RuntimeError("hook explode")

    p = DictationPipeline([_Stage("noop")], on_run=hook)

    run = p.run(_utt())  # must not raise

    assert any("on_run: RuntimeError:" in w for w in run.warnings)
    # The buffered entry reflects the hook warning too.
    assert p.recent_runs()[-1].warnings == run.warnings


def test_clock_injection_makes_timings_deterministic():
    p = DictationPipeline([_Stage("a"), _Stage("b")], clock=_fake_clock())

    run = p.run(_utt())

    # Fake clock advances 1ms per call: 1 (run start) + 2*2 (stage start +
    # body for two stages) + 1 (run end) = 6 ticks; total spans ticks
    # 1..6 → ~5ms.
    assert run.total_elapsed_ms > 0.0
    assert run.short_circuited is False
