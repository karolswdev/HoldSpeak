# Evidence — HS-36-06: Phase 36 closeout

**Date:** 2026-06-04. **Branch:** `phase-36/hs-36-01-artifact-card-shell`.

## The headline — before/after, re-captured in the new cards on real `.43`

Both spoken-e2e screenshots of the **same** messy meeting were re-run on real `.43`
(Qwen3.5-9B-Q6) **after** the experience track (HS-36-01/02/03) landed, so the
before/after now shows the new elevated, polished cards — not the old flat chrome.

```
[e2e:dynamic]       windows=5  active_intents=['architecture', 'product']
[e2e:dynamic]       BEFORE artifact_types=[action_items, adr, customer_signals,
                                           decisions, diagram, requirements, scope_review] (count=7)
[e2e:dynamic]       rendered artifact cards (BEFORE) = 23

[e2e:dynamic:after] active_intents=['architecture','comms','delivery','incident','product']
[e2e:dynamic:after] AFTER artifact_types=[action_items, adr, customer_signals,
                                          decision_announcement, decisions, dependency_map,
                                          diagram, incident_timeline, milestone_plan,
                                          requirements, runbook_delta, scope_review,
                                          stakeholder_update] (count=13)
[e2e:dynamic:after] intent-gated types fished out = [decision_announcement,
                                          incident_timeline, runbook_delta, stakeholder_update]
[e2e:dynamic:after] rendered artifact cards (AFTER) = 51
```

| | intents active | artifact types | rendered cards |
|---|---|---|---|
| **BEFORE** (old fixed-window/keyword routing) | 2 (`architecture`, `product`) | **7** | 23 |
| **AFTER** (segment-probe routing) | 5 (`+comms`, `+delivery`, `+incident`) | **13** | 51 |

The meeting's clearly-stated incident ("Prod fell over… checkout was down… we rolled it
back… a bad deploy that ate the connection pool") and comms ("I'll send a note to the
wider team announcing the onboarding changes") — diluted below the 0.6 lexical threshold
in the BEFORE — are now fished out per segment, and their plugin chains fire. The diff is
the phase's money shot.

- `evidence/dynamic_meeting_before.png` — old routing, sparse, in the new cards.
- `evidence/dynamic_meeting_after.png` — segment-probe routing, dense, in the new cards.

## Spoken-e2e re-run (real `.43`) — selectors green in the new cards

`HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s` (LAN, `dangerouslyDisableSandbox`):

```
tests/e2e/test_spoken_meeting_e2e.py::test_spoken_dynamic_meeting_end_to_end             PASSED
tests/e2e/test_spoken_meeting_e2e.py::test_spoken_dynamic_meeting_after_probe_end_to_end PASSED
tests/e2e/test_spoken_meeting_e2e.py::test_spoken_incident_retro_end_to_end              PASSED
3 passed, 25 warnings in 245.99s (0:04:05)
```

The incident-retro produced all five comms/incident artifacts
(`decision_announcement`, `incident_timeline`, `risk_register`, `runbook_delta`,
`stakeholder_update`) and every asserted inner selector resolved inside the new
`.artifact-card` body (`.incident-timeline li`, `.risk-table tbody tr`,
`.runbook-list .runbook-change`, `.stakeholder-update`, `.announcement-artifact
.announcement`, …) — i.e. the card shell (HS-36-01) + body polish (HS-36-03) preserved
all of them. `phase-35-plugin-frontier/evidence/spoken_incident_artifacts.png` refreshed.

## Bundle + suite

```
$ cd web && npm run build          # ✓ 8 pages built
$ git ls-files holdspeak/static/_built/ | wc -l   # 0 — gitignored build product, not committed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2020 passed, 15 skipped in 59.35s
```

## Exit criteria (phase)

- [x] Artifacts render as elevated Signal cards; generic `.segment` chrome gone. (HS-36-01)
- [x] Risk table (and wide artifacts) no longer overflow; scroll within the card. (HS-36-01)
- [x] Each artifact has a working "Copy as Markdown" button + "Copy all". (HS-36-02)
- [x] Every artifact type's body got the Signal polish pass. (HS-36-03)
- [x] A third opt-in dynamic/messy spoken-e2e exists, verified on `.43`, structural
      assertions. (HS-36-04)
- [x] Segment-aware intent extraction surfaces a brief-but-clear intent the old path
      diluted away — regression test + the messy-meeting e2e on `.43`; lexical fallback
      intact with `llm` off. (HS-36-05)
- [x] Bundle rebuilt from source (gitignored `_built` not committed); spoken-e2e
      selectors pass. (all)
- [x] Before/after captured (same meeting), quantified delta (7 → 13 types). (HS-36-04/05/06)
- [x] Full suite green; routing tests updated in lockstep, not silenced. (HS-36-06)
