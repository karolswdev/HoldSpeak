# HS-167-02 - The debts a user hits: functional, before beauty

- **Project:** holdspeak
- **Phase:** 167
- **Status:** done
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

- [x] Each of the five has a unit test that fails on the old code and passes on the new; the file lock has a two-process test (subprocess) proving exclusion and the typed timeout.
- [x] api-surface + MCP tool census regenerated honestly; the effect census unchanged or its diff explained.
- [x] Scoped suites green: tests/unit/test_hs166_*, tests/unit/test_hs163_*, tests/unit/test_hs164_*, the setup controller vitest.

## Landed (2026-09-03)

(1) The Jira scope rides the setup answers as `jira_scope` (the same
`{original, normalized}` shape; resume restores it; python round-trip
tests). (2) `calls` lands on `watch_evaluations.metadata_json` (one
additive column in the ONE schema) via a thread-local carried from the
snapshot adapter to evaluate_core (a hidden coupling — ledgered N),
then on the OBSERVE checkpoint's receipt_json; the step decoder reads
`calls`. (3) `_CrossProcessLock`: fcntl.flock on `<data dir>/.acli.lock`
+ the in-process RLock semantics, bounded wait (HOLDSPEAK_ACLI_LOCK_
TIMEOUT, default 10s) → typed `lock_timeout` (503); a two-process test.
(4) `evaluation_cadence_minutes` on the policy PUT (fenced 1..10080,
applied to the project's watches), the MCP `project.watch.set_rules`
twin, the controller draft. (5) `POST /api/steward/trigger` + MCP
`project.steward.trigger` through a new `get_scheduler_services()`
accessor on the conductor seam; unwired → typed 503 refusal; the 163
same-watermark law proven (two run_once at one watermark both create).

ORCHESTRATOR CATCHES (three, paid in-round): the scope submit ran
INSIDE a React state updater (StrictMode double-fires; updaters must
stay pure) → moved out behind a ref; the trigger route took a
project_id it never used (evaluate_due/run_due are desk-wide and
principal-scoped) → the route and tool are honestly desk-wide; both
wrapped a thrown scheduler error as `success: true` → surfaced (the
methods never raise by contract; an exception is a fault). Debt: the
controller round-trip for (1) has python coverage only (no vitest was
written — ledgered). Gates read: 72 python (debts + 166 walk fixes +
api-surface + MCP surface + one-path census) and 320 vitest passed.

## Test plan

- **Unit:** new tests beside the changed modules (tests/unit/test_hs167_debts.py; web/src/features/project-room/setup/__tests__, steward/__tests__).
- **Live (real HOME):** a one-shot live script proving the receipt count equals the acli calls made against project KAN.
