"""DIR-01 dictation pipeline executor (HS-1-03).

Spec: `docs/internal/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §6.1, §6.2, §9.1,
§9.7. Single in-process, synchronous, ordered execution of
`Transducer` stages between `TextProcessor.process` and
`TextTyper.type_text`. Failures short-circuit to the original
post-`TextProcessor` text. The executor is I/O-free; the controller
(HS-1-07) supplies the structured-log emitter via `on_run`.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from holdspeak.plugins.dictation.contracts import (
    IntentTag,
    StageResult,
    Transducer,
    Utterance,
)


def _fatal_speech_signal(exc: BaseException) -> bool:
    """True when ``exc`` is a speech CONTROL signal, not an ordinary stage failure.

    HS-131-15 (Sol Amendment 3). DIR-F-003 says a stage that blows up degrades to
    the original post-`TextProcessor` text. That is right for a bad block, a
    malformed model answer, or a plugin bug — and exactly wrong for a session
    refusal, a provider failure, an exact-revision mismatch, an expiry or
    revocation, or a child-budget refusal. Degrading THOSE produced the quiet
    raw-text path this story closes: the refusal was caught here, `current_text`
    reset to the utterance, and a successful-looking response and journal row
    landed for work that was never authorized.

    Imported lazily and only on the failure path, so the hot loop pays nothing.
    """
    try:
        from holdspeak.speech_session.child import fatal_speech_signal
    except Exception:  # noqa: BLE001 - never let the guard itself break a run
        return False
    return bool(fatal_speech_signal(exc))


@dataclass(frozen=True)
class PipelineRun:
    """One full pipeline run's record (kept in the ring buffer)."""

    final_text: str
    stage_results: list[StageResult]
    intent: IntentTag | None
    warnings: list[str]
    total_elapsed_ms: float
    short_circuited: bool


class DictationPipeline:
    """Ordered, error-isolating executor of `Transducer` stages."""

    def __init__(
        self,
        stages: Sequence[Transducer],
        *,
        enabled: bool = True,
        llm_enabled: bool = True,
        ring_buffer_size: int = 20,
        on_run: Callable[[PipelineRun], None] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._stages: list[Transducer] = list(stages)
        self._enabled = enabled
        self._llm_enabled = llm_enabled
        self._on_run = on_run
        self._clock = clock if clock is not None else time.perf_counter
        self._recent: deque[PipelineRun] = deque(maxlen=ring_buffer_size)

    def recent_runs(self) -> list[PipelineRun]:
        """Return recorded runs newest-last (a copy; deque is internal)."""
        return list(self._recent)

    def run(self, utt: Utterance) -> PipelineRun:
        if not self._enabled:
            return PipelineRun(
                final_text=utt.raw_text,
                stage_results=[],
                intent=None,
                warnings=[],
                total_elapsed_ms=0.0,
                short_circuited=True,
            )

        run_start = self._clock()
        results: list[StageResult] = []
        warnings: list[str] = []
        intent: IntentTag | None = None
        current_text = utt.raw_text
        short_circuited = False

        for stage in self._stages:
            if stage.requires_llm and not self._llm_enabled:
                warnings.append(f"{stage.id}: skipped (llm disabled)")
                continue

            stage_start = self._clock()
            try:
                result = stage.run(utt, list(results))
            except Exception as exc:  # DIR-F-003
                if _fatal_speech_signal(exc):
                    # Propagate UNCHANGED so the entry owner sees the kernel's own
                    # safe reason, closes its parent honestly, and publishes
                    # nothing. Never rewritten, never degraded to raw text.
                    raise
                elapsed = (self._clock() - stage_start) * 1000.0
                warnings.append(
                    f"{stage.id}: {type(exc).__name__}: {exc}"
                )
                results.append(
                    StageResult(
                        stage_id=stage.id,
                        text=current_text,
                        intent=None,
                        elapsed_ms=elapsed,
                        warnings=[f"{type(exc).__name__}: {exc}"],
                        metadata={"failed": True},
                    )
                )
                short_circuited = True
                current_text = utt.raw_text
                break

            results.append(result)
            current_text = result.text
            if result.intent is not None:
                intent = result.intent
            if result.warnings:
                warnings.extend(f"{stage.id}: {w}" for w in result.warnings)

        total_elapsed_ms = (self._clock() - run_start) * 1000.0

        run_record = PipelineRun(
            final_text=current_text,
            stage_results=results,
            intent=intent,
            warnings=warnings,
            total_elapsed_ms=total_elapsed_ms,
            short_circuited=short_circuited,
        )
        self._recent.append(run_record)

        if self._on_run is not None:
            try:
                self._on_run(run_record)
            except Exception as exc:
                # The hook must never break the pipeline. Record and move on.
                # We can't mutate a frozen dataclass, so replace the buffer
                # entry with an updated copy that carries the hook warning.
                hook_warning = f"on_run: {type(exc).__name__}: {exc}"
                updated = PipelineRun(
                    final_text=run_record.final_text,
                    stage_results=run_record.stage_results,
                    intent=run_record.intent,
                    warnings=[*run_record.warnings, hook_warning],
                    total_elapsed_ms=run_record.total_elapsed_ms,
                    short_circuited=run_record.short_circuited,
                )
                self._recent[-1] = updated
                run_record = updated

        return run_record
