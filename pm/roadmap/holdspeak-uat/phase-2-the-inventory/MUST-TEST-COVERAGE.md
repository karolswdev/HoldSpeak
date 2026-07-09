# UAT Must-Test Coverage — Round 2 (2026-07-09)

> A 6-agent flotilla authored a protocol for every one of the 66 uncovered
> must-do capabilities (auto-staged where a recipe exists, hand-staged with
> manual_setup where not). **Independently verified: 115/115 must-tests cited,
> 0 validation errors, 105 scenarios across 9 packs.** 26 of the new scenarios
> are hand-staged (device/live-capture/connectors) — authored and walkable, their
> proof deferred to a human sitting.

# UAT Must-Test Coverage — Authoring Round 2

## 1. Per-pack results

| Pack | Scenarios | Must-keys covered | Manual-staged | Validated |
|---|---|---|---|---|
| `pack-f-mobile` | 11 (`01-airgapped-notetaker` … `11-workbench-graph-author`) | 19 | 7 | clean |
| `pack-desk` | 13 (`09-coders-on-the-desk` … `21-qlippy-decision-cards`) | 13 | 4 | clean |
| `pack-g-connectors` | 6 (`01-governance-gate` … `06-named-key-allowlist`) | 9 | 2 | clean |
| `pack-b-steering` | 8 (`06-arm-and-keys` … `13-fire-while-dictating`) | 9 | 3 | clean |
| `pack-c-dictation-grounding` | 7 (`09-hold-to-talk` … `15-byo-backends`) | 8 | 5 | clean |
| `pack-a-aftercare` | 6 (`08-import-audio-recording` … `13-belt-approval-leg`) | 8 | 5 | clean |
| **Total** | **51 scenarios** | **66** | **26** | **all clean** |

## 2. Unique must-keys covered this round

**66 of 66** previously-uncovered keys, deduped. The six packs' key lists sum to 66 with **zero overlap** — each pack owns a disjoint slice of the must-test surface, so the union equals the sum. This round closes the entire 66-key uncovered backlog.

## 3. Keys still uncovered

**None.** Every pack reported `uncovered_remaining: []`. All 66 assigned keys are grep-confirmed cited by ≥1 scenario, and each pack validates CLEAN (0 errors) against the contract/ledger/recipe/deck registries. New staging assets were built only where the ledger pointed at non-existent recipes — notably `pack-g-connectors` added `uat/recipes/pack-g-actuators-armed.yaml`, `pack-g-slack-armed.yaml` + two decks; `pack-b-steering` added `uat/recipes/pack-b-pane-steered.yaml`; `pack-c` added three recipes + two seeds. `pack-f-mobile`, `pack-desk`, and `pack-a-aftercare` added no new recipes (reused existing registry recipes + `manual_setup`).

## 4. Honest coverage line

With **49 must-do capabilities already covered before this round + 66 closed now, the protocol reaches all 115** — every must-test capability is authored, validated CLEAN, and cited. The honest caveat: authored ≠ walked. 26 of the 51 new scenarios are `manual_setup` (live mic, paired devices, on-device inference, credentialed connectors, from-the-future stores, live tmux coder panes) and cannot be recipe-induced, so their proof is deferred to a human sitting; the LLM-backed features carry ordered control-vs-treatment pairs judged structurally on `.43`, but the coverage claim is that the protocol *exercises* all 115, not that all 115 have yet been green-walked on real metal.