# HS-167-02 - The debts a user hits: functional, before beauty

- **Project:** holdspeak
- **Phase:** 167
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-167-05, HS-167-06
- **Owner:** unassigned

## Problem

Five ledgered debts bite inside a week of real use. The beauty pass
comes after the functional pass (the standing directive), so these
land first and change no face composition.

## Scope

- **In:** (1) **Population toggles persisted** — the Jira type/
  status/scope toggles held in useSetupController.ts:642 and written
  only by updateJiraScope (:862) ride the setup session's persisted
  answers (project_setup_answer's shape) so leaving and resuming
  setup (project_setup_resume) restores them; the controller reads
  them back from the wire, never from React memory. (2) **Enrichment
  receipted** — the `calls` count jira_provider.py:1405-1421 already
  computes lands on the steward run record (the OBSERVE checkpoint's
  receipt) and is decoded by steward/model.ts so 05 can render it
  (a count on a Receipt, no prose). (3) **The acli lock across
  processes** — jira_provider.py:90's RLock becomes a file lock
  under the data dir shared by the web server and the MCP sidecar,
  with a bounded wait that raises a typed PROV-009-class error
  (never a hang); the switch-and-verify read-back stays. (4) **The
  cadence write wire** — `evaluation_cadence_minutes` joins
  savePolicy (useStewardController.ts:288) and the route it calls,
  and the MCP `project.watch.set_rules` twin (holdspeak/mcp/
  families/project.py), range-fenced to what the conductor tick
  can honor; the steward face's read-only decode (steward/model.ts:
  210) becomes an edit-in-world in 05. (5) **The trigger route** —
  one route + one MCP tool that asks the conductor to evaluate_due /
  run_due now (workbench_conductor.py:598/:619) through the
  set_scheduler_services seam (unwired = honest typed refusal),
  reusing the 163 same-watermark contract — never a second act
  path.
- **Out:** face changes (05); the door-title choice (ledgered); a
  second Jira account.

## Acceptance criteria

- [ ] Each of the five has a unit test that fails on the old code and passes on the new; the file lock has a two-process test (subprocess) proving exclusion and the typed timeout.
- [ ] api-surface + MCP tool census regenerated honestly; the effect census unchanged or its diff explained.
- [ ] Scoped suites green: tests/unit/test_hs166_*, tests/unit/test_hs163_*, tests/unit/test_hs164_*, the setup controller vitest.

## Test plan

- **Unit:** new tests beside the changed modules (tests/unit/test_hs167_debts.py; web/src/features/project-room/setup/__tests__, steward/__tests__).
- **Live (real HOME):** a one-shot live script proving the receipt count equals the acli calls made against project KAN.
