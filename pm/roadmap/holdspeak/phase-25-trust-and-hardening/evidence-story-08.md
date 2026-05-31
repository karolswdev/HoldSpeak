# Evidence — HS-25-08 — Web Egress-Posture Badge

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

The runtime dashboard now renders the meeting-intel egress posture (from HS-25-01's
`intel_egress` API field) as a glanceable "Privacy" badge — so a user watching
only the browser can see whether transcripts can leave the machine.

## Files touched

- `web/src/scripts/dashboard-app.js` — `intelEgress` data field; captured in
  `fetchRuntimeStatus`; `egressLabel()` helper (`🔒 Local only` / `🔒 Intel off`
  vs `☁︎ Cloud` / `☁︎ Auto → cloud`).
- `web/src/pages/index.astro` — a "Privacy" stat bound to `egressLabel()`, full
  sentence in the `title` tooltip.
- `holdspeak/static/_built/**` — regenerated via `npm run build` (large
  generated diff, expected).
- `tests/integration/test_web_server.py` — `test_dashboard_includes_egress_posture_badge`.

## Verification artifacts

```
$ (cd web && npm run build)
[build] 8 page(s) built — Complete!

$ grep -c "egressLabel\|Privacy" holdspeak/static/_built/index.html   # badge present
1

$ uv run pytest -q tests/integration/test_web_server.py::TestDashboardEndpoint::test_dashboard_includes_egress_posture_badge
1 passed

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
3 failed, 1871 passed, 13 skipped
```

## Pre-existing failures: 9 → 3 (and a correction)

The rebuild cleared **6** failures — every stale-`_built` page-content test
(`device_health_surface`, `companion`, and the 4 dictation-page tests). They were
asserting markup that current `web/src` already had but the committed bundle
lacked.

**Correction to the record:** earlier evidence files (01–06) inherited an
exploration-agent claim that the other 3 failures were a "missing Safari
fixture." That is **wrong** — `tests/unit/test_activity_history.py` self-creates
its fixture via `_create_safari_history`. The real cause: the fixture uses a
**fixed** `visit_time` (`799_203_600.0` macOS epoch ≈ 2026-04-29). The importer
prunes records older than the 30-day retention default at import time; with
today = 2026-05-31 that record is ~32 days old and pruned immediately, so
`imported_count == 1` but `list_activity_records()` returns `[]`. A **time-bomb in
test data**, pre-existing on `main`, unrelated to Phase 25.

## Acceptance criteria — re-checked

- [x] Dashboard shows egress posture from `intel_egress` (no logs).
- [x] Visually distinct when transcripts can leave (🔒 vs ☁︎ + tooltip).
- [x] `_built/` rebuilt + committed; badge page-content test passes.

## Deviations from plan

None for the badge. The rebuild incidentally (and intentionally) fixed 6
unrelated stale-`_built` reds.

## Follow-ups

- **Fix the time-bomb activity-history tests** (3 reds on `main`): make the
  fixture `visit_time` recent/relative, or freeze the clock. Trivial, but its own
  change (out of Phase 25 scope). Recommend a small dedicated story/commit.
