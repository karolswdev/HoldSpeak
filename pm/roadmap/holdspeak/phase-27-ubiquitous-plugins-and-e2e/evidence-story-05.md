# HS-27-05 Evidence — RFC reality-check refresh + phase exit

**Date:** 2026-06-01.
**Story:** [story-05-phase-exit.md](./story-05-phase-exit.md).

## What shipped

**RFC reality-status table** (`docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`): heading
updated to "phase 27 close"; count corrected to **fourteen** plugin IDs with
**four real** (`mermaid_architecture`, `action_owner_enforcer`,
`decision_capture`, `requirements_extractor`). The three phase-27 plugins flipped
⚠️ → ✅ (with the shipping story IDs); `decision_capture` added as a net-new row;
the remaining ten stay ⚠️. The follow-on paragraph now records the spoken e2e and
hands the remaining ten stubs to a later phase.

**`final-summary.md`** written per `roadmap-builder.md` §2.5: dates, 5/5 chunks,
goal-met assessment, exit-criteria re-run against evidence, stories table,
cut/deferred (none), live `.43` Q6 parse-quality handoff note, surprises/lessons
(the configured-provider wiring gap, the structured-render rule, the
net-new-vs-already-routed routing-ripple distinction), asset/test posture, and the
handoff to the next plugin-rollout phase.

**`current-phase-status.md`** frozen with a closing line; phase marked done.

**`README.md`**: phase-27 row → done; "Last updated" + "Current phase" repointed.

## Regression sweep

```bash
uv run pytest -q --ignore=tests/e2e/test_metal.py
# 1939 passed, 14 skipped   (phase-16 close was 1902 passed, 13 skipped)
```

The spoken e2e remains opt-in (its own `spoken_e2e` marker, module-skipped without
`HOLDSPEAK_SPOKEN_E2E=1`) and is excluded from the default sweep. It was run green
this phase (`HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s` → 1 passed),
producing `evidence/spoken_meeting_artifacts.png`.

## Exit criteria

- [x] RFC reality-status table reflects what actually shipped this phase.
- [x] `final-summary.md` exists, conforms to §2.5, references the e2e evidence.
- [x] `current-phase-status.md` frozen; README phase-27 row → done + Current phase repointed.
- [x] Every Phase-27 exit-criterion checked (see `final-summary.md`).
- [x] Full sweep green; the spoken e2e remains opt-in/excluded.

## Result

Phase 27 closed, 5/5. Four real ubiquitous plugins flow end-to-end (transcript →
LLM → artifact → structured web render), proven by a real spoken-meeting e2e on
live endpoints. The remaining ten stubs are handed to a later plugin-rollout phase
with a fully trodden pattern.
