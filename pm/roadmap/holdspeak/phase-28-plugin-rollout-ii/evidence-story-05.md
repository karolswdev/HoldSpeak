# HS-28-05 Evidence — RFC reality-check refresh + phase exit

**Date:** 2026-06-01.
**Story:** [story-05-phase-exit.md](./story-05-phase-exit.md).

## What shipped

**RFC reality-status table** (`docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`): heading →
"phase 28 close"; counts corrected to **fourteen** IDs with **seven real**. The
three phase-28 plugins flipped ⚠️ → ✅ (`adr_drafter` HS-28-02, `milestone_planner`
HS-28-03, `risk_heatmap` HS-28-04) with their artifact types; the remaining seven
stay ⚠️. The follow-on paragraph now records the renderer registry and hands the
seven remaining stubs to a later phase.

**`final-summary.md`** written per `roadmap-builder.md` §2.5: dates, 5/5 chunks,
goal-met, exit-criteria re-run against evidence, stories table, cut/deferred
(none), per-plugin `.43` Q6 parse-quality, surprises/lessons (registry-pays-for-
itself, already-routed-stubs-don't-ripple, e2e non-determinism, fixed-modal
screenshot fix), final asset/test posture, and the handoff.

**`current-phase-status.md`** frozen with a closing line; phase marked done.

**`README.md`**: phase-28 row → done; "Last updated" + "Current phase" repointed.

## Regression sweep

```bash
uv run pytest -q --ignore=tests/e2e/test_metal.py
# 1978 passed, 14 skipped   (phase-27 close was 1939 passed, 14 skipped)
```

The spoken e2e remains opt-in (`spoken_e2e` marker, module-skipped without
`HOLDSPEAK_SPOKEN_E2E=1`) and excluded from the default sweep. It was run green
this phase exercising all seven real plugins, producing
`evidence/spoken_meeting_artifacts.png`.

## Exit criteria

- [x] RFC reality-status table reflects what actually shipped this phase.
- [x] `final-summary.md` exists, conforms to §2.5, references the e2e evidence.
- [x] `current-phase-status.md` frozen; README phase-28 row → done + Current phase repointed.
- [x] Every Phase-28 exit-criterion checked (see `final-summary.md`).
- [x] Full sweep green; the spoken e2e remains opt-in/excluded.

## Result

Phase 28 closed, 5/5. Seven real plugins now cover the architecture / delivery /
risk / requirements / decisions / action-items / diagram meeting outputs, all
end-to-end (transcript → LLM → artifact → structured web render) and proven by the
spoken-meeting e2e. The remaining seven stubs are handed to a later phase with a
fully mechanized pattern.
