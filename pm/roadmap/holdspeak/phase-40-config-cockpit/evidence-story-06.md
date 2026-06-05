# Evidence — HS-40-06 — Closeout

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-40/hs-40-01-settings-api-knobs`
- **Owner:** unassigned

## Dogfood — UI-only setup that survives a restart

`scripts/dogfood_cockpit.py` (**new**) drives the full loop over two server
instances sharing one config file + DB:

1. **Session 1** — configured the copilot **entirely in the web UI** (no file
   editing): `/dictation → Runtime → Copilot depth` → pipeline on · rewrite
   passes **3** · corrections on · infer-target on → **Save**; then recorded a
   correction in `/dictation → Memory` ("ship the ledger reconciliation fix →
   `agent_task_buildout`").
2. **Session 2 (simulated restart)** — a fresh `MeetingWebServer` over the same
   config + DB.

Transcript:

```
session 1: configured via UI — pipeline on, 3 passes, corrections on, infer-target on
session 1: recorded a correction in the Memory tab — 1 card(s) shown
session 2 (restart): durable store has 1 correction(s): intent:ship the ledger reconciliation fix→agent_task_buildout
session 2 (restart): config persisted — enabled=True passes=3 corrections=True infer_target=True
session 2 (restart): Memory tab shows 1 persisted correction card(s)

DOGFOOD PASSED — correction + config survived the restart
```

Capture: [`evidence/dogfood_post_restart.png`](./evidence/dogfood_post_restart.png)
— the Memory tab after the restart: banner `learning: on · remembered: 1`, the
corrections toggle on, and the persisted correction card present. (Depth
telemetry shows its empty state — it's in-memory + session-scoped by design, as
labelled.)

Earlier per-story captures: `evidence/cockpit_depth_group.png` +
`evidence/cockpit_depth.png` (HS-40-03), `evidence/memory_panel.png` (HS-40-04).

## Invariant re-verification

- **Off-by-default byte-identity** — `test_intent_dispatch` / `test_intent_router`
  + the no-repo `CorrectionStore` path → `25 passed`. Routing is unchanged;
  persistence is additive and `corrections_enabled` still gates the nudge.
- **Schema** — `test_fresh_schema_matches_canonical_snapshot` green (the one new
  table + index are in the committed canonical snapshot).
- **Bundle** — `cd web && npm run build` succeeds; `git ls-files
  holdspeak/static/_built` is **empty** (nothing tracked); `git status` shows no
  `_built/` staged.

## Final suite

> `uv run` is broken on this machine; run via `.venv/bin/python -m pytest`.

- `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`
  → **2221 passed, 16 skipped** (2186/16 at phase open; +35).

## Acceptance criteria — re-checked

- [x] End-to-end UI-only setup captured (configure → use → correct → restart →
      correction persisted) — the dogfood transcript + screenshot above.
- [x] Demo screenshots committed (cockpit / memory / telemetry / post-restart).
- [x] Full suite green at close (2221/16); off-by-default byte-identity
      re-asserted; no `_built/` tracked.
- [x] `final-summary.md` exists (goal-met, exit criteria, stories, metrics,
      lessons, Phase-41 handoff).
- [x] `current-phase-status.md` frozen; README phase row → done + pointer
      advanced; PR opened (merge when CI green).

## Deviations from plan

- None. `HANDOVER.md`'s "Most recent" pointer + the roadmap README "Last
  updated" / "Current phase" lines were both refreshed to Phase 40 CLOSED.
