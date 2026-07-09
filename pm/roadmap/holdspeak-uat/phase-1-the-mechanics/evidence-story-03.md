# Evidence - HSU-1-03

- **Story:** HSU-1-03 - The scenario contract + the feature ledger
- **Status:** done
- **Date:** 2026-07-09

## What shipped

`uat/conductor/contract/` + `uat/features.yaml` + `uat/scenarios/smoke/` +
`uat/tools/build_ledger.py`:

- **The feature ledger** (`uat/features.yaml`, 255 keys): every capability with
  per-surface applicability (`yes|no|unknown`), the holdspeak phases that shipped
  it, needed recipes, and priority. A `phase_map` pins **every** holdspeak phase
  0–87 to its covering keys or an explicit `internal/no-uat-surface` marker (20
  internal/refactor phases carry the marker) — no phase silently absent. Seeded
  from the Phase-2 directory's 255 rows by `build_ledger.py`, which *proposes*;
  the committed YAML is canon, freshness-checked by `test_build_ledger.py`.
- **The scenario contract** (`scenarios.py`): loads/validates scenarios with
  named `ERROR <path>: <issue>` errors; enforces the three-surface axis (default
  all-yes, opt out only with `{n/a: <reason>}`); resolves per-(step, surface)
  applicability; validates cited ledger keys, recipes, decks, and mid-run actions.
- **Coverage math** (`coverage.py` + `ledger.py`): exact per surface and overall
  — retired excluded, `unknown` counted distinctly, uncovered enumerated.
- **The smoke pack** (`uat/scenarios/smoke/`, 7 scenarios): both golden decks'
  postures (`seeded-desk`/`fresh-desk` + `meeting-just-ended-open-actions`), both
  bad decks (`intel-endpoint-dead`, `first-run-no-model`), a three-surface desk
  walk, an honest per-surface `n/a` with reason, and a mid-run mesh kill. Loads
  clean, cites real keys + recipes.
- Conductor API: `GET /api/features`, `GET /api/packs`, `GET /api/packs/{pack}`
  (scenarios + coverage + validation errors).

Coverage the smoke pack reports (honest — a thin smoke pack, Phase 3 authors the
rest): overall 14/254, web 13/220, ipad 6/142, iphone 0/25, 36 expected verdicts.

## Proof

### Captured run — 2026-07-09T07:29:48Z

- **Command:** `uv run pytest -q tests/uat/ --ignore=tests/uat/test_induction_integration_43.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ab94ed9ae3ee71f24f13ca165182769d8531d0d

```text
.................................................................        [100%]
65 passed in 13.92s
```
