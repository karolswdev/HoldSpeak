"""Built-in `kb-enricher` stage (DIR-01 §6.2, §8.3).

Pure template substitution against the matched block's `inject`
template. **Never** calls the LLM (DIR-R-004). **Never** types
unresolved `{...}` placeholders into the destination (DIR-F-007) —
when any placeholder is missing context, injection is skipped and
the input text passes through unchanged with a warning.
"""

from __future__ import annotations

import re
import time
from collections.abc import Mapping
from typing import Any

from holdspeak.logging_config import get_logger
from holdspeak.plugins.dictation.blocks import (
    Block,
    InjectMode,
    LoadedBlocks,
)
from holdspeak.plugins.dictation.contracts import (
    IntentTag,
    StageResult,
    Utterance,
)

log = get_logger("dictation.stages.kb_enricher")

_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\}")


class _Unresolved(KeyError):
    pass


def _lookup(context: Mapping[str, Any], path: str) -> str:
    """Resolve a dotted-name path against a mapping context. Raises _Unresolved."""
    parts = path.split(".")
    cursor: Any = context
    for part in parts:
        if isinstance(cursor, Mapping) and part in cursor:
            cursor = cursor[part]
        else:
            raise _Unresolved(path)
    if cursor is None:
        raise _Unresolved(path)
    return str(cursor)


def _resolve_template(template: str, context: Mapping[str, Any]) -> str:
    """Substitute `{a.b.c}` placeholders. Raises `_Unresolved` on miss."""

    def replace(match: re.Match[str]) -> str:
        return _lookup(context, match.group(1))

    return _PLACEHOLDER_RE.sub(replace, template)


def _find_intent(prior: list[StageResult]) -> IntentTag | None:
    for result in reversed(prior):
        if result.intent is not None:
            return result.intent
    return None


def _latest_text(prior: list[StageResult], default: str) -> str:
    if prior:
        return prior[-1].text
    return default


def _build_context(
    utt: Utterance, intent: IntentTag
) -> dict[str, Any]:
    return {
        "raw_text": utt.raw_text,
        "project": utt.project or {},
        "intent": {
            "block_id": intent.block_id,
            "extras": dict(intent.extras),
        },
    }


def _apply_mode(mode: InjectMode, original: str, rendered: str) -> str:
    if mode is InjectMode.REPLACE:
        return rendered
    if mode is InjectMode.PREPEND:
        return f"{rendered}{original}"
    return f"{original}{rendered}"


class KbEnricher:
    """Template-driven enrichment of the matched block's `inject` template."""

    id = "kb-enricher"
    version = "0.1.0"
    requires_llm = False

    def __init__(self, blocks: LoadedBlocks) -> None:
        self._blocks = blocks
        self._by_id: dict[str, Block] = {b.id: b for b in blocks.blocks}

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult:
        start = time.perf_counter()
        text = _latest_text(prior, utt.raw_text)

        intent = _find_intent(prior)

        if intent is None or not intent.matched or intent.block_id is None:
            return self._noop(start, text, "no_match", [])

        block = self._by_id.get(intent.block_id)
        if block is None:
            warning = (
                f"intent block_id {intent.block_id!r} not found in loaded blocks"
            )
            return self._noop(start, text, "unknown_block", [warning])

        threshold = block.match.threshold
        if threshold is None:
            threshold = self._blocks.default_match_confidence
        if intent.confidence < threshold:
            return self._noop(
                start,
                text,
                "below_threshold",
                [],
                metadata_extras={
                    "threshold": threshold,
                    "confidence": intent.confidence,
                },
            )

        context = _build_context(utt, intent)
        try:
            rendered = _resolve_template(block.inject.template, context)
        except _Unresolved as exc:
            elapsed = (time.perf_counter() - start) * 1000.0
            warning = f"unresolved placeholder {{{exc.args[0]}}}; skipping injection"
            log.warning("kb-enricher: %s", warning)
            return StageResult(
                stage_id=self.id,
                text=text,
                intent=None,
                elapsed_ms=elapsed,
                warnings=[warning],
                metadata={"reason": "unresolved_placeholder"},
            )

        final_text = _apply_mode(block.inject.mode, text, rendered)
        elapsed = (time.perf_counter() - start) * 1000.0
        return StageResult(
            stage_id=self.id,
            text=final_text,
            intent=None,
            elapsed_ms=elapsed,
            warnings=[],
            metadata={
                "applied_block": block.id,
                "mode": block.inject.mode.value,
            },
        )

    def _noop(
        self,
        start: float,
        text: str,
        reason: str,
        warnings: list[str],
        *,
        metadata_extras: dict[str, Any] | None = None,
    ) -> StageResult:
        elapsed = (time.perf_counter() - start) * 1000.0
        metadata: dict[str, Any] = {"reason": reason, "applied_block": None}
        if metadata_extras:
            metadata.update(metadata_extras)
        return StageResult(
            stage_id=self.id,
            text=text,
            intent=None,
            elapsed_ms=elapsed,
            warnings=warnings,
            metadata=metadata,
        )
