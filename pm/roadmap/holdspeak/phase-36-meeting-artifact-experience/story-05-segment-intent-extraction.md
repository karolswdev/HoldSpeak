# HS-36-05 — Segment-aware intent extraction (fish out intent per segment)

- **Project:** holdspeak
- **Phase:** 36
- **Status:** not-started
- **Depends on:** HS-36-04 (the messy-meeting e2e is the repro/proof)
- **Unblocks:** HS-36-06
- **Owner:** unassigned

## Problem

A long, digression-heavy meeting can **silently lose a real intent**. The MIR-01
pipeline scores **fixed 90s rolling windows** (`intent_timeline.build_intent_windows`)
with **lexical keyword matching** (`plugins/signals.extract_intent_signals`:
`score = min(1.0, 0.22*keyword_hits + 0.2*tag_boost)`) and activates an intent only when
its window score clears the **0.6 threshold** (`plugins/router.select_active_intents`).

So a brief-but-clear signal — e.g. a risk raised in a 20s aside buried in 70s of
unrelated chatter — is **diluted across its 90s window below 0.6**: the intent never
activates, the incident/risk plugins never run, and the signal vanishes from the output.
Keyword-only scoring compounds it (anything paraphrased outside the ~8 hardcoded
keywords per intent scores nothing). Hysteresis only *sustains* an already-active
intent; it can't revive a diluted spike. This is the weakness the messy-meeting e2e
(HS-36-04) is built to expose.

The fix the user asked for: **divide the meeting into segments and probe each segment
for the intent(s) it exhibits** — "fish out" intent per segment — so a clearly-incident
segment activates the incident chain regardless of the noise around it.

## Scope

- **In:**
  - **Per-segment intent probing.** Add a segment-aware intent extractor: segment the
    meeting into topic-coherent chunks and determine the intent(s) each segment exhibits,
    **LLM-assisted** (one pass over the transcript returning topic segments + their
    intents, via the same configured endpoint the plugins use —
    `build_configured_meeting_intel`-style, JSON-only prompt, parse/validate). Catches
    brief + paraphrased intents that keyword/threshold scoring misses.
  - **Deterministic fallback preserved.** When the `llm` capability is unavailable (or
    the probe fails/parses empty), fall back to the existing fixed-window + lexical path
    so behavior degrades gracefully and stays testable offline. Gate the LLM path on the
    `llm` capability + a config knob.
  - **Aggregate (union) so nothing is diluted away.** An intent that any segment clearly
    exhibits activates its plugin chain for the meeting; map each activated plugin to the
    **relevant segment(s)** so it dispatches with tight local context (not the whole
    meeting blob, not a diluted 90s window).
  - **Wire into the pipeline** (`plugins/pipeline.process_meeting_state` /
    `meeting_session` finalization), behind the gate; persist per-segment routing so
    telemetry/readiness can show why a plugin ran.
  - **Tests** updated in lockstep: a deterministic regression test proving a brief
    signal that the old path dropped now activates its chain; the existing
    `test_intent_router` / `test_intent_dispatch` / `test_multi_intent_routing` updated
    (not silenced); the messy-meeting e2e (HS-36-04) proves it on real `.43`.
  - New config knob(s) as needed (e.g. `intent_segment_probe_enabled`), defaulting
    consistently with the current conservative MIR defaults.
  - **Capture the AFTER screenshot.** Re-run the HS-36-04 messy meeting (same script)
    through the *new* segment-probe routing and save `evidence/dynamic_meeting_after.png`
    — the dense/varied artifact set the genuinely-present intents now produce. Record the
    produced intents/artifacts so the before→after delta is quantifiable (e.g. "before: 1
    type; after: N types"). This pairs with `evidence/dynamic_meeting_before.png` from
    HS-36-04 as the phase's headline comparison.
- **Out:**
  - Changing any plugin's **output `structured_json` shape** — this changes *which*
    plugins run and *what segment* they see, not what they emit.
  - Realtime/streaming re-segmentation — the probe runs at meeting finalization (where
    MIR already runs), not live.
  - Re-tuning the lexical keyword lists as the primary fix (kept only as fallback).

## Acceptance criteria

- [ ] A segment-aware intent extractor exists: the meeting is segmented and each segment
      probed for intent (LLM-assisted), aggregated to an active-intent set + per-segment
      plugin context.
- [ ] A regression test proves a brief, signal-dense segment amid noise — one the old
      fixed-window/keyword path diluted below threshold — now activates its chain and
      yields its artifact.
- [ ] The deterministic lexical fallback path still works with the `llm` capability off
      (unit-tested); the LLM path is gated + degrades gracefully on failure.
- [ ] `test_intent_router` / `test_intent_dispatch` / `test_multi_intent_routing`
      updated in lockstep (not `-k`-silenced); full suite green.
- [ ] The messy-meeting e2e (HS-36-04) on real `.43` shows the richer extraction (more
      of the genuinely-present intents surface than the old path would).

## Test plan

- Unit: a new `test_segment_intent_*` (deterministic parts — segmentation aggregation,
  fallback selection, per-segment context mapping); update `test_intent_router` /
  `test_intent_dispatch` / `test_intent_scoring` for the new selection path.
- Integration: `tests/integration/test_multi_intent_routing.py` — extend for a
  digression-amid-noise arc; assert the diluted-intent regression.
- e2e (opt-in, real `.43`): the HS-36-04 dynamic meeting surfaces ≥ the intents the old
  path would, including at least one that fixed-window scoring would have dropped.

## Notes / open questions

- Design spike first: confirm one-LLM-pass (segments + intents together) vs finer
  windows + a per-window LLM intent probe. Default to the one-pass approach; keep the
  deterministic fixed-window path as the fallback implementation.
- Read the real selection/dispatch path before editing: `holdspeak/intent_timeline.py`,
  `holdspeak/plugins/signals.py`, `holdspeak/plugins/router.py`,
  `holdspeak/plugins/dispatch.py`, `holdspeak/plugins/pipeline.py`,
  `holdspeak/meeting_session.py`. Keep the change additive + gated.
- If the messy meeting still drops a genuinely-present intent after this, that's a
  tuning follow-up, not a silent failure — surface it (telemetry / a logged reason).
- Egress: the probe sends transcript to the configured endpoint exactly as the plugins
  already do — honor the Phase-25 provider gate; off when the `llm` capability is off.
