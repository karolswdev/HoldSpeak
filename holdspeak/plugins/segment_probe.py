"""LLM-assisted per-segment intent probe (HS-36-05).

The deterministic lexical scorer (`signals.extract_intent_signals`) misses intents that
are **brief or paraphrased**: a prod incident described as *"it fell over and we rolled
it back"* matches none of the `incident` keywords, and a single *"announcing…"* is
diluted below the activation threshold across a 90s window of chatter. The messy-meeting
e2e (HS-36-04) proved this — the routing silently dropped a clear incident, risk, and
comms.

This probe reads a transcript segment with the configured LLM and returns a confidence
per intent, judged by **meaning, not keywords**, so a genuinely-present intent activates
its chain regardless of keyword coverage or surrounding noise — i.e. it "fishes out" the
intent per segment.

It is **additive and gated**:

- Routing *without* a probe is byte-identical to before — `scoring.score_window(...,
  probe=None)` is unchanged, so the existing router/dispatch/pipeline tests don't move.
- When a probe is supplied, its confidences are merged (element-wise **max**) with the
  lexical scores, so the probe can only *raise* an intent's score, never suppress one.
- Any probe failure / parse-miss degrades gracefully to the lexical path (returns `{}`).

HS-131-14 closed the probe's own side door. It used to build the configured engine
itself (`build_configured_meeting_intel()`), which re-read mutable configuration and
put a model call outside any admitted child. A probe now EXISTS only where an
admitted dispatch handle does: `build_segment_probe(dispatch)` returns ``None``
without one, and the caller keeps the lexical path it already falls back to on any
probe failure. There is no unadmitted construction to degrade from.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ..logging_config import get_logger
from .signals import SUPPORTED_INTENTS

log = get_logger("plugins.segment_probe")

# The admitted chat seam: messages -> text, with the handle's
# `chat(messages, *, temperature, max_tokens)` keyword signature.
IntelChat = Callable[..., str]
SegmentProbe = Callable[[str], dict[str, float]]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.DOTALL | re.IGNORECASE)

_INTENT_DEFINITIONS = (
    "architecture: technical/system design — APIs, schemas, latency, services, "
    "interfaces, design decisions.\n"
    "delivery: planning & execution — scope, milestones, deadlines, owners, estimates, "
    "dependencies, roadmap.\n"
    "product: product/customer — customer needs, personas, features, feedback, value, "
    "product scope.\n"
    "incident: a production failure/outage — something broke or went down, a rollback, "
    "root cause, postmortem — HOWEVER it is phrased (e.g. 'prod fell over', 'we rolled "
    "it back', 'a bad deploy ate the connection pool').\n"
    "comms: communicating outward — announcing changes or sending an update / note / "
    "email / recap to stakeholders or the wider team."
)


def _system_prompt() -> str:
    return (
        "You classify which meeting INTENTS are genuinely discussed in a transcript "
        "segment.\n\nIntents and what each means:\n"
        + _INTENT_DEFINITIONS
        + "\n\nJudge by MEANING, not keywords — natural, paraphrased language counts. "
        "Be precise: only include an intent that is actually discussed, but don't miss "
        "one just because the exact term wasn't used.\n\n"
        "Output strictly a single fenced ```json block containing an object that maps "
        "each genuinely-discussed intent to a confidence between 0.0 and 1.0. Omit "
        "intents that are not discussed. No prose.\n"
        'Example: {"incident": 0.9, "comms": 0.7}'
    )


def _extract_json_object(text: str) -> Optional[dict]:
    """Pull a JSON object out of a model response (fenced block, else first {...})."""
    if not text:
        return None
    candidate: Optional[str] = None
    fence = _JSON_FENCE_RE.search(text)
    if fence is not None:
        candidate = fence.group(1).strip()
    if not candidate:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
    if not candidate:
        return None
    try:
        obj = json.loads(candidate)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def parse_probe_scores(
    raw: str,
    *,
    supported_intents: tuple[str, ...] = SUPPORTED_INTENTS,
) -> dict[str, float]:
    """Parse a probe response into clamped per-intent confidences (unknown keys dropped)."""
    obj = _extract_json_object(raw)
    if not obj:
        return {}
    out: dict[str, float] = {}
    for key, value in obj.items():
        intent = str(key or "").strip().lower()
        if intent not in supported_intents:
            continue
        try:
            conf = float(value)
        except Exception:
            continue
        out[intent] = min(1.0, max(0.0, conf))
    return out


def probe_intents(
    transcript: str | None,
    *,
    chat_fn: IntelChat,
    supported_intents: tuple[str, ...] = SUPPORTED_INTENTS,
    temperature: float = 0.0,
    max_tokens: int = 256,
) -> dict[str, float]:
    """Probe one transcript segment for the intents it exhibits.

    Returns a confidence per genuinely-discussed intent. Any failure (endpoint error,
    unparseable response) returns ``{}`` so the caller falls back to lexical scoring.
    """
    text = (transcript or "").strip()
    if not text:
        return {}
    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": text},
    ]
    from ..kernel.provider_signals import CONTROL_SIGNALS

    try:
        raw = chat_fn(messages, temperature=temperature, max_tokens=max_tokens)
    except CONTROL_SIGNALS:
        # HS-131-14: a dialect retry is the RUNNER's second admitted child, and an
        # indeterminate attempt is a real outcome. Degrading either to lexical
        # would hide a physical attempt that already happened. Ordered ahead of the
        # catch-all, exactly like every other sanitizing seam.
        raise
    except Exception as exc:  # endpoint down, bad kwargs, etc. — degrade to lexical
        log.warning("segment intent probe failed: %s", exc)
        return {}
    return parse_probe_scores(raw, supported_intents=supported_intents)


def build_segment_probe(dispatch: Any = None) -> Optional[SegmentProbe]:
    """Build a `(transcript) -> {intent: confidence}` probe over an ADMITTED handle.

    ``dispatch`` is the :class:`~holdspeak.plugins.intelligence.PluginDispatch` issued
    for the child that authorized this routing pass. Without one there is no probe:
    this returns ``None`` and the caller scores lexically — the same degradation a
    probe failure already produces, and the only honest one, because a probe with no
    admitted child would be an unrecorded model call (Article XI.2).

    The returned callable never raises for a PROBE failure — a dead endpoint or
    an unparseable answer yields ``{}`` and the caller scores lexically. A
    REVOKED handle (released, cancelled, or rebound to another child) is not a
    probe failure but withdrawn authority, and propagates.
    """
    if dispatch is None:
        return None
    from .intelligence import require_plugin_dispatch

    handle = require_plugin_dispatch(dispatch, plugin_id="segment_probe")
    chat_fn = handle.chat

    def _probe(transcript: str) -> dict[str, float]:
        return probe_intents(transcript, chat_fn=chat_fn)

    return _probe
