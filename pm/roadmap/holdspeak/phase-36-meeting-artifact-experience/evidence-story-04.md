# Evidence — HS-36-04: Dynamic, digression-heavy multi-topic spoken-e2e (BEFORE)

**Shipped:** 2026-06-04. **Story:** [story-04-dynamic-meeting-e2e.md](./story-04-dynamic-meeting-e2e.md).

## What shipped

`test_spoken_dynamic_meeting_end_to_end` in `tests/e2e/test_spoken_meeting_e2e.py` — a
third opt-in spoken-e2e scenario: a long, messy, human-sounding meeting (small talk,
tangents, an interruption, "anyway where were we" resets, callbacks) that drifts across
many topics, with real substance buried in the noise:

- a **product** decision (onboarding scope → ship welcome screen + sample project, punt
  the template gallery),
- an **architecture** aside (a slow onboarding endpoint: 2s latency, a needless schema
  join),
- a **prod incident** ("checkout was down for half an hour Tuesday… we rolled it back…
  bad deploy ate the connection pool"),
- **action items** dropped in passing ("I'll write the spec", "can you own the sample
  content", "ping infra about that endpoint"),
- a **risk** raised offhand ("my one worry is the holiday traffic… could get ugly"),
- a **comms** plan ("I'll send a note to the wider team announcing the changes").

Unlike the two existing scenarios (which execute a hardcoded chain over the whole
transcript), this one **drives the real MIR routing path** — `say` → Whisper →
`MeetingState` → `process_meeting_state` (`build_intent_windows` → `score_window` →
`select_active_intents` → `dispatch_window` per window → `synthesize_and_persist`) →
temp SQLite → `MeetingWebServer` → Playwright. Only the real routing exhibits the
dilution weakness Phase 36 targets, so this is what makes the before/after meaningful.
`defer_heavy=False` runs the deferred LLM plugins inline so one call yields persisted
runs + artifacts. Assertions are intentionally **loose** (windows built, no fatal
pipeline error, ≥1 artifact) — the job here is to *expose* what the old routing drops,
not to assert richness (HS-36-05's bar). Opt-in (`HOLDSPEAK_SPOKEN_E2E=1`), module-skips
otherwise.

## Verification — run for real against `.43` (Qwen3.5-9B-Q6)

```
$ HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s \
    tests/e2e/test_spoken_meeting_e2e.py::test_spoken_dynamic_meeting_end_to_end
[e2e:dynamic] meeting spans 132s across 10 segments
[e2e:dynamic] transcript: Morning everyone. ... Did you all see Prod fell over on
Tuesday afternoon? Check out was down for like half an hour. We rolled it back. It was
a bad deploy that ate the connection pool. ... My one worry, honestly, is the holiday
traffic in two weeks ... I'll send a note to the wider team announcing the onboarding
changes ...
[e2e:dynamic] windows=5 active_intents=['architecture', 'product']
[e2e:dynamic] plugins_ran=['action_owner_enforcer', 'adr_drafter',
'customer_signal_extractor', 'decision_capture', 'mermaid_architecture',
'requirements_extractor', 'scope_guard']
[e2e:dynamic] BEFORE artifact_types=['action_items', 'adr', 'customer_signals',
'decisions', 'diagram', 'requirements', 'scope_review'] (count=7)
[e2e:dynamic] rendered artifact cards (BEFORE) = 23
[e2e:dynamic] BEFORE screenshot saved: .../evidence/dynamic_meeting_before.png
1 passed in 82.18s
```

Reproduced across two runs (same 7 artifact types, same `['architecture', 'product']`
active intents) — a deterministic baseline.

**Screenshot:** [`evidence/dynamic_meeting_before.png`](./evidence/dynamic_meeting_before.png)
— the meeting modal on the current routing + current (flat) artifact styling.

## The weakness, captured live (the BEFORE half of the headline)

The real routing activated **only `architecture` and `product`** across all 5 windows.
**`incident` and `comms` never cleared the 0.6 threshold** — so the meeting's prod
incident, its holiday-traffic risk, and its comms/announcement plan produced **no**
`incident_timeline`, `risk_register`, `runbook_delta`, `stakeholder_update`, or
`decision_announcement` artifacts. They were **silently lost.**

Two mechanisms, both as predicted in the recon:

1. **Keyword brittleness.** The `incident` keywords (`incident`, `outage`, `sev`,
   `rollback`, `mitigation`, …) don't match the meeting's natural phrasing — "rolled it
   back" (not "rollback"), "fell over", "bad deploy", "connection pool". The incident
   was described clearly in English but scored ≈0 lexically.
2. **Dilution.** `comms` got a single hit (`announce` in "announcing") inside a 90s
   window full of unrelated chatter → ≈0.22, well under 0.6.

`architecture` and `product` fired because their keywords (`latency`, `schema`, `api`,
`endpoint`; `customer`, `feedback`, `persona`, `scope`, `value`) were dense and
repeated.

This is exactly the failure HS-36-05 (segment-aware per-segment intent probing) will
fix; HS-36-05 captures the AFTER on this same script, and HS-36-06 presents the
before/after with the quantified delta.

## Acceptance criteria — re-checked

- [x] New opt-in scenario with a long, digression-heavy, multi-topic, multi-speaker
      script — proven by the run above.
- [x] Routes via the **real** `process_meeting_state` MIR path (windows=5, real
      scoring/selection/dispatch) — not a hardcoded chain.
- [x] Loose/noise-tolerant assertions (windows built, no fatal error, ≥1 artifact) — 7
      artifact types produced; pass in 82s.
- [x] BEFORE screenshot + produced intents/artifacts captured for the before/after.
- [x] Opt-in/module-skip matches the existing scenarios; default suite green without
      the opt-in — `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2007 passed,
      15 skipped**.
- [x] Verified once for real against `.43`.

## Deviations from plan

None. (Bonus finding: the BEFORE is not merely "sparse" — it's *selectively* missing the
incident/risk/comms intents while keeping architecture/product, which makes the
before/after sharper than anticipated.)
