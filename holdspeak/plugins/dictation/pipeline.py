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
from typing import Any
from dataclasses import dataclass, field, replace

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
    # HS-176-02 (ruling R2): the durable ids of the corrections that ACTUALLY
    # fired on this run — the `text` rules applied at the transcript seam below,
    # plus the routing nudge's rule when the router marked the intent corrected.
    # It carries a DEFAULT on purpose: `journal.passthrough_run`
    # (`plugins/dictation/journal.py:32-49`) fakes a run with a
    # `SimpleNamespace`, and the recorder reads this field with `getattr(...)`,
    # so the pipeline-off path can never raise on it.
    corrections_applied: tuple[int, ...] = ()


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
        corrections: Sequence[Any] | None = None,
    ) -> None:
        self._stages: list[Transducer] = list(stages)
        self._enabled = enabled
        self._llm_enabled = llm_enabled
        self._on_run = on_run
        # HS-176-02: the same correction snapshot the intent-router stage gets
        # (`assembly.build_pipeline` hands both the one gated list). The `text`
        # subset is applied here, at the transcript seam; the routing subset is
        # the router's business and is only read back to name the rule that
        # fired.
        self._corrections: list[Any] = list(corrections or [])
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

        # ── HS-176-02: the `text` correction seam (ruling R1) ──────────────
        # The one funnel every dictation source passes through. The stored
        # `text` rules rewrite the raw transcript BEFORE the stage loop, and a
        # corrected `Utterance` (frozen — `dataclasses.replace`) is what every
        # stage receives, so the rewrite pass and the router both see the words
        # he actually said. It is NOT a stage: no StageResult, no `stage_ms`
        # entry, no `requires_llm`, nothing added to `self._stages`.
        utt, applied_ids = self._apply_text_corrections(utt)

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

        # The routing nudge's own rule, when one fired (R2). The router marks
        # `extras["corrected"]` (builtin/intent_router.py:225, :233) but carries
        # no id, so the fired rule is re-resolved here through the SAME
        # function, list and text the router used — a deterministic lookup, not
        # a guess.
        nudge_id = self._intent_correction_id(intent, utt.raw_text)
        if nudge_id is not None and nudge_id not in applied_ids:
            applied_ids = (*applied_ids, nudge_id)

        run_record = PipelineRun(
            final_text=current_text,
            stage_results=results,
            intent=intent,
            warnings=warnings,
            total_elapsed_ms=total_elapsed_ms,
            short_circuited=short_circuited,
            corrections_applied=applied_ids,
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
                    corrections_applied=run_record.corrections_applied,
                )
                self._recent[-1] = updated
                run_record = updated

        return run_record

    # ── HS-176-02 helpers ─────────────────────────────────────────────────

    def _apply_text_corrections(self, utt: Utterance) -> tuple[Utterance, tuple[int, ...]]:
        """Rewrite `utt.raw_text` through the stored `text` rules.

        Returns the utterance the stages will see (the SAME object when nothing
        fired, so a pipeline with no corrections is byte-identical) and the ids
        of the rules that changed the text.
        """
        if not self._corrections:
            return utt, ()
        try:
            from holdspeak.plugins.dictation.corrections import apply_text_corrections

            corrected, applied = apply_text_corrections(utt.raw_text, self._corrections)
        except Exception:  # pragma: no cover - a correction must never break typing
            return utt, ()
        if corrected == utt.raw_text:
            return utt, applied
        return replace(utt, raw_text=corrected), applied

    def _intent_correction_id(self, intent: IntentTag | None, text: str) -> int | None:
        """The durable id of the `intent` correction the router nudged with."""
        if intent is None or not self._corrections:
            return None
        extras = getattr(intent, "extras", None) or {}
        if not extras.get("corrected"):
            return None
        try:
            from holdspeak.plugins.dictation.builtin.intent_router import (
                _NUDGE_SIMILARITY,
            )
            from holdspeak.plugins.dictation.corrections import best_match_in

            match = best_match_in(
                self._corrections, "intent", text, min_similarity=_NUDGE_SIMILARITY
            )
        except Exception:  # pragma: no cover - defensive; never break a run
            return None
        if match is None or match.value != getattr(intent, "block_id", None):
            return None
        rule_id = getattr(match, "correction_id", None)
        return int(rule_id) if rule_id is not None else None
