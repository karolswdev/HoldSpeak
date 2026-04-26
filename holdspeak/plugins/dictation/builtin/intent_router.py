"""Built-in `intent-router` stage (DIR-01 §6.2, §7).

Calls the constrained-decoded LLM runtime to classify the utterance
against the loaded `BlockSet`. Returns an `IntentTag`. Never raises
out of `run()` — the stage's contract is "always return a
`StageResult`"; the pipeline's error isolation is a fallback.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from holdspeak.logging_config import get_logger
from holdspeak.plugins.dictation.blocks import LoadedBlocks
from holdspeak.plugins.dictation.contracts import (
    IntentTag,
    StageResult,
    Utterance,
)
from holdspeak.plugins.dictation.grammars import (
    StructuredOutputSchema,
)
from holdspeak.plugins.dictation.runtime import LLMRuntime

log = get_logger("dictation.stages.intent_router")


def _default_prompt_builder(blocks: LoadedBlocks, utt: Utterance) -> str:
    lines: list[str] = [
        "You are an utterance classifier for a voice-typing tool.",
        "Choose the single best matching block id for the user's utterance,",
        "or set matched=false with confidence=0.0 if none fit.",
        "",
        "Available blocks:",
    ]
    for b in blocks.blocks:
        lines.append(f"- {b.id}: {b.description}")
        for ex in b.match.examples:
            lines.append(f"    + example: {ex}")
        for neg in b.match.negative_examples:
            lines.append(f"    - counter-example: {neg}")
        if b.match.extras_schema:
            for key, values in b.match.extras_schema.items():
                lines.append(f"    extras.{key} ∈ {{{', '.join(values)}}}")
    lines.append("")
    lines.append(f'Utterance: "{utt.raw_text}"')
    lines.append("")
    lines.append(
        "Respond with a single JSON object: "
        '{"matched": <bool>, "block_id": <id|null>, "confidence": <0.0-1.0>, '
        '"extras": {<key>: <value>}}.'
    )
    return "\n".join(lines)


def _coerce_intent(
    raw: dict[str, Any],
    valid_block_ids: tuple[str, ...],
) -> IntentTag:
    """Normalize a runtime classify() dict into an IntentTag, or raise."""
    if not isinstance(raw, dict):
        raise ValueError(f"classify() did not return a dict: {type(raw).__name__}")
    matched = bool(raw.get("matched", False))
    block_id_raw = raw.get("block_id")
    block_id = block_id_raw if isinstance(block_id_raw, str) else None
    if matched and (block_id is None or block_id not in valid_block_ids):
        raise ValueError(
            f"matched=true but block_id {block_id!r} not in taxonomy {valid_block_ids}"
        )
    confidence_raw = raw.get("confidence", 0.0)
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"confidence not numeric: {confidence_raw!r}") from exc
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"confidence {confidence} out of [0.0, 1.0]")
    extras = raw.get("extras", {}) or {}
    if not isinstance(extras, dict):
        raise ValueError(f"extras must be a dict, got {type(extras).__name__}")
    return IntentTag(
        matched=matched,
        block_id=block_id if matched else None,
        confidence=confidence if matched else 0.0,
        raw_label=block_id_raw if isinstance(block_id_raw, str) else None,
        extras=dict(extras),
    )


def _no_match() -> IntentTag:
    return IntentTag(
        matched=False,
        block_id=None,
        confidence=0.0,
        raw_label=None,
        extras={},
    )


class IntentRouter:
    """LLM-driven intent classifier."""

    id = "intent-router"
    version = "0.1.0"
    requires_llm = True

    def __init__(
        self,
        runtime: LLMRuntime,
        blocks: LoadedBlocks,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
        prompt_builder: Callable[[LoadedBlocks, Utterance], str] | None = None,
    ) -> None:
        self._runtime = runtime
        self._blocks = blocks
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._prompt_builder = prompt_builder or _default_prompt_builder

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult:
        start = time.perf_counter()

        if not self._blocks.blocks:
            elapsed = (time.perf_counter() - start) * 1000.0
            return StageResult(
                stage_id=self.id,
                text=utt.raw_text,
                intent=_no_match(),
                elapsed_ms=elapsed,
                warnings=[],
                metadata={"reason": "empty_blockset"},
            )

        block_set = self._blocks.to_block_set()
        schema = StructuredOutputSchema.from_block_set(block_set)
        prompt = self._prompt_builder(self._blocks, utt)
        valid_ids = schema.block_ids

        warnings: list[str] = []
        intent: IntentTag | None = None
        for attempt in (1, 2):
            try:
                raw = self._runtime.classify(
                    prompt,
                    schema,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                )
                intent = _coerce_intent(raw, valid_ids)
                break
            except Exception as exc:
                warnings.append(
                    f"classify attempt {attempt} failed: "
                    f"{type(exc).__name__}: {exc}"
                )
                log.warning(
                    "intent-router classify attempt %d failed: %s", attempt, exc
                )

        if intent is None:
            intent = _no_match()
            warnings.append("classify retries exhausted; returning no-match")

        elapsed = (time.perf_counter() - start) * 1000.0
        return StageResult(
            stage_id=self.id,
            text=utt.raw_text,
            intent=intent,
            elapsed_ms=elapsed,
            warnings=warnings,
            metadata={"taxonomy_size": len(valid_ids)},
        )
