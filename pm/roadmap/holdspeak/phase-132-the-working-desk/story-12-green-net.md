# HS-132-12 — The regression net comes back green

- **Project:** holdspeak
- **Phase:** 132
- **Status:** done
- **Depends on:** HS-132-01, HS-132-02, HS-132-11 (their fixes green ~13 of the red names)
- **Unblocks:** HS-132-14
- **Owner:** unassigned

## Problem

CI "Tests" has been red on main for 8+ consecutive merges. The full-suite
audit (30:03, isolated HOME) counted 5542 passed / 71 failed / 17 errors —
88 red names, 87 byte-identical to the pre-Phase-130 inherited ledger
(Backlog Candidate Z). Every route-level defect this phase fixes was already
covered by a named red test nobody could see. Root-cause clusters:

- **~28 stale source-greps:** tests assert literals in monolith `.tsx` files
  emptied by the Phase 117 decomposition (e.g.
  `test_web_dictation_journal.py:137` greps `DictationCore.tsx` for markup
  now in `dictation/Journal.tsx:214`; same for history/settings/live).
- **~21 monkeypatch-era route tests:** patch `holdspeak.db.get_database`
  after services captured the handle at composition
  (`web_server.py:631-648`), so live routes answer 404/empty (MIR history,
  speakers, intel queue, global action items, rails journal, companion
  slack fixture ordering).
- **17 environment errors:** 14 workbench-walk tests error on
  ERR_CONNECTION_REFUSED with no hub; 3 Playwright tests fail only because
  isolated HOME hides the browser cache (green with
  `PLAYWRIGHT_BROWSERS_PATH` exported).
- **Stale Phase-131 guards:** `test_decision_records.py:440,491` patch a
  deliberately removed seam; :241 pins schema version 32 against 59.
- **Canon guards, real violations:** left rails in
  `intelligence.css:205,245`; retired noun in `KbEditor.tsx:131`; fact-free
  error copy in `voice.py:187`; em-dash prose in `FollowThroughView.tsx:162`.
- **Egress vocabulary drift (held owner question #1):** yolo receipts say
  `per_action_decision`/`authorization_required` where companion tests
  contract `control_posture`/`refused` (`operation_policy.py:271-338`).
- **Slack actuator seam:** six tests where the executor cannot find a
  proposal the API just created — harness artifact or real composition
  split, to be determined and fixed accordingly.

## Scope

### In

- Re-point the ~28 source-grep tests at the decomposed modules (or delete
  any whose invariant no longer exists, named in evidence).
- Rebuild the ~21 monkeypatch-era tests against composed services (fix the
  composition seam or the fixtures — whichever restores real coverage).
- Convert environment-dependent tests to named skips on unmet preconditions;
  document `PLAYWRIGHT_BROWSERS_PATH` for isolated-HOME runs in CLAUDE.md's
  test commands.
- Repair the stale Phase-131 decision guards so the admission invariant is
  guarded again.
- Fix the four canon-violation sites in shipped source.
- Settle the egress vocabulary per the owner ruling and fix the losing side.
- Diagnose and fix the slack propose/execute seam.
- Exit: the CI "Tests" workflow green on main.

### Out

- Metal-only and `.43`-dependent tests beyond honest skips; suite
  performance work beyond what exists.

## Acceptance criteria

- [ ] `HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run pytest -q --ignore=tests/e2e/test_metal.py` reports 0 failed / 0 errors (skips named and justified).
- [ ] CI "Tests" is green on the PR and on main after merge.
- [ ] No test was deleted without its invariant either re-homed or named in
  the evidence as intentionally retired.
- [ ] The egress ruling is recorded and the receipts/tests agree.

## Test plan

The story IS the test plan: full suite under the quiet-tree rule (no worker
editing during the run), output read from file before any flip, per the
standing read-output-before-flip rule.
