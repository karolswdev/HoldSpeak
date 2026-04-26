# HS-4-06 — DoD sweep + phase exit

- **Project:** holdspeak
- **Phase:** 4
- **Status:** done
- **Depends on:** HS-4-01 through HS-4-05
- **Unblocks:** phase 4 closure
- **Owner:** unassigned

## Problem

Final phase-exit sweep: validate WFS-* + WFS-CFG-* requirements
against on-disk evidence per
`docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` §6.2 + §7.2, generate the
phase evidence bundle at `docs/evidence/phase-wfs-01/<YYYYMMDD-HHMM>/`,
write the phase summary documenting outcome + deferred items, run
the full regression, and flip the phase to `done`. Mirrors HS-1-11 /
HS-2-11 / HS-3-06.

## Scope

- **In:**
  - Generate the spec §7.2 evidence bundle. Original WFS-01 §7.2 lists 17 files; the WFS-CFG-* amendment adds 5 more (one log per CFG story). Final bundle is ~22 files.
  - Run the full-regression command (`uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`) and capture in evidence.
  - Phase tracking docs: flip `current-phase-status.md` story table HS-4-06 to done; check the 6 exit-criteria boxes; bump "Last updated"; project README phase index flips phase 4 to "done"; project README "Last updated" + status updated.
- **Out:**
  - New product code. The phase-4 product surface is complete as of HS-4-05.
  - Test additions beyond what the bundle captures from the existing phase-4 suite.
  - Any deferred items the phase enumerated for follow-up.

## Acceptance criteria

- [x] Evidence bundle exists at `docs/evidence/phase-wfs-01/20260426-1537/` with all listed files non-empty, each leading with command + timestamp + git sha.
- [x] All 6 phase-exit boxes in `current-phase-status.md` are checked with evidence pointers.
- [x] `99_phase_summary.md` enumerates what shipped + remaining deferreds.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS (1072 passed, 13 skipped).
- [x] Project README phase index shows phase 4 as `done` and "Current phase" reverts to "between phases".

## Test plan

- **Spec verification:** the exit-criteria boxes above.
- **Bundle smoke:** `ls docs/evidence/phase-wfs-01/<TS>/ | wc -l` matches the expected count.
- **Regression:** the documented full-suite command.

## Notes / open questions

- Bundle path uses the timestamp at the start of the sweep, not at commit time (HS-2-11 / HS-3-06 convention).
- Mark each WFS-* and WFS-CFG-* requirement against its evidence file in `03_traceability.md` per spec §7.2.
- Bundling note: committed together with HS-4-05 and HS-5-01..03 because the user asked to commit the accumulated significant work from this session. `.tmp/BUNDLE-OK.md` records the intentional bundle.
