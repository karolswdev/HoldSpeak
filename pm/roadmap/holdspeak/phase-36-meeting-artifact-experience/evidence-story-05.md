# Evidence — HS-36-05: Segment-aware intent extraction (the AFTER)

**Shipped:** 2026-06-04. **Story:** [story-05-segment-intent-extraction.md](./story-05-segment-intent-extraction.md).

## What shipped

An LLM-assisted **per-segment intent probe** that fixes the routing weakness HS-36-04
captured: a brief/paraphrased intent diluted below the lexical threshold and silently
dropped. It is **additive and gated** — with the probe off, routing is byte-identical to
before.

- **`holdspeak/plugins/segment_probe.py`** — `probe_intents(transcript, *, chat_fn)`
  reads a transcript segment with the configured LLM (a JSON-only prompt that judges
  intents *by meaning, not keywords*) and returns a confidence per intent;
  `build_segment_probe(intel=None)` wraps `build_configured_meeting_intel()`'s
  `_chat_completion_text` (same seam + egress posture as the built-in plugins). Any
  failure / unparseable response returns `{}` → graceful fallback to lexical scoring.
- **`scoring.score_window(..., probe=None)`** — when a probe is supplied, its
  confidences are merged **element-wise max** over the lexical scores (the probe can only
  *raise* an intent, never suppress one). `probe=None` is byte-identical to the old path.
- **`pipeline.process_meeting_state(..., segment_probe=None)`** — threads the probe into
  per-window scoring; default `None` keeps the pipeline unchanged.
- **`MeetingConfig.intent_segment_probe_enabled: bool = False`** — opt-in knob (like the
  rest of MIR). `MeetingSession` gained `mir_segment_probe`; `WebRuntime` builds the
  probe (defensively — any construction failure → `None` + lexical fallback) only when
  the knob is on and passes it through.

## Verification — unit (deterministic) + e2e (real `.43`)

### Unit — `tests/unit/test_segment_probe.py` (13 tests)

```
$ uv run pytest -q tests/unit/test_segment_probe.py
13 passed
```

Covers the parser (fenced/bare JSON, unknown-key drop, clamping, garbage→{}), the
injected-chat probe (success, empty-transcript-skips-call, failure→{}), and the
probe-augmented scoring — including the **core regression**: a window whose transcript
describes an incident in plain English ("checkout fell over… we rolled it back… a bad
deploy ate the connection pool") scores `incident` **below** threshold lexically (not
active), but **activates** once the probe flags it; plus probe-only-raises-never-suppresses
and probe-exception-falls-back-to-lexical.

The existing routing tests are **unchanged and green** (the default `probe=None` path is
byte-identical):

```
$ uv run pytest -q tests/unit/test_intent_router.py tests/unit/test_intent_dispatch.py \
    tests/unit/test_intent_scoring.py
21 passed
```

Full suite: **2020 passed, 15 skipped** (+13 new).

### e2e — the same messy meeting, BEFORE vs AFTER, on real `.43`

```
$ HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s \
    tests/e2e/test_spoken_meeting_e2e.py::test_spoken_dynamic_meeting_after_probe_end_to_end
[e2e:dynamic:after] active_intents=['architecture', 'comms', 'delivery', 'incident', 'product']
[e2e:dynamic:after] AFTER artifact_types=['action_items', 'adr', 'customer_signals',
'decision_announcement', 'decisions', 'dependency_map', 'diagram', 'incident_timeline',
'milestone_plan', 'requirements', 'runbook_delta', 'scope_review', 'stakeholder_update']
(count=13)
[e2e:dynamic:after] intent-gated types fished out = ['decision_announcement',
'incident_timeline', 'runbook_delta', 'stakeholder_update']
[e2e:dynamic:after] rendered artifact cards (AFTER) = 51
1 passed in 146.41s
```

## The before/after (the phase's headline)

| | BEFORE (HS-36-04, lexical) | AFTER (HS-36-05, segment probe) |
|---|---|---|
| active intents | `architecture, product` | `architecture, comms, delivery, incident, product` |
| artifact types | **7** | **13** |
| rendered cards | 23 | 51 |
| incident / comms | **dropped** | `incident_timeline`, `runbook_delta`, `stakeholder_update`, `decision_announcement` |

Screenshots: [`evidence/dynamic_meeting_before.png`](./evidence/dynamic_meeting_before.png)
vs [`evidence/dynamic_meeting_after.png`](./evidence/dynamic_meeting_after.png) — the
same meeting, same real routing path; the only change is the per-window LLM probe. The
prod incident, the comms/announcement plan, and the delivery planning that the lexical
scorer silently lost are now fished out and rendered.

Note: `risk_register` (risk_heatmap) is in the **incident *profile* base chain**, not the
incident *intent* chain (`_INTENT_PLUGIN_CHAIN["incident"] = [incident_timeline,
runbook_delta]`), so it doesn't appear under the `balanced` profile regardless of the
probe — a pre-existing routing-config detail, not a probe gap. The probe surfaced 4 of
the meeting's genuinely-present intents that the lexical path missed.

## Acceptance criteria — re-checked

- [x] Segment-aware extractor: meeting segmented (per-window) + each probed; aggregated
      to the active-intent set; per-window local context to plugins.
- [x] Regression proving a brief signal the old path diluted now activates its chain —
      `test_segment_probe.py::TestProbeAugmentedScoring` + the e2e (incident/comms
      surfaced).
- [x] Deterministic lexical fallback works with the probe off / on failure
      (unit-tested); LLM path gated by `intent_segment_probe_enabled` + built defensively.
- [x] `test_intent_router` / `test_intent_dispatch` / `test_intent_scoring` unchanged
      and green (default path byte-identical) — **not** `-k`-silenced.
- [x] The messy-meeting e2e on real `.43` shows materially richer extraction (7 → 13
      types); AFTER screenshot captured.

## Deviations from plan

Implemented as a **per-window** LLM probe merged into scoring (rather than a separate
whole-meeting segmentation pass) — simpler, fits the existing per-window dispatch
exactly, keeps the default path byte-identical, and an LLM reading a 90s window is not
fooled by the dilution that defeats keyword-counting. The deferred "one-pass
segmentation vs finer windows" design question is thus resolved in favor of
per-window probing.
