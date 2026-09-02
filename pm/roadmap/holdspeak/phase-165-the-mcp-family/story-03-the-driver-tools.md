# HS-165-03 - The driver tools: steward, setup, providers, the watch graduation

- **Project:** holdspeak
- **Phase:** 165
- **Status:** done
- **Depends on:** HS-165-02
- **Unblocks:** HS-165-04
- **Owner:** unassigned

## Problem

§11.0's missing autonomous lifecycle: MCP must start/poll the
application-owned steward run (MCP-003), drive the durable setup
interview, discover providers, and graduate the legacy watch tools
to WatchSpec@1 — extend, never replace.

## Scope

- **In:** project.configure_steward (policy read/write incl.
  unattended_enabled) / run_steward (insert_run on the call, run_id
  returned PROMPTLY, execution handed off exactly as the 164 route
  does — never hold the tool call open; MCP-003) / stop_steward /
  get_steward_run (run + steps + receipts, the STW-011 substrate).
  project.setup.start/resume/answer/suggest/finalize over the 159
  durable interview service. provider.* (connections, capabilities,
  bounded discovery through the existing adapters). project.watch.*:
  propose/test/activate/inspect/evaluate/pause/retire over the
  GRADUATED WatchSpec@1 machinery (161/164) — evaluation/effect
  inspection included; the legacy reactions-family tools
  (reactions.py:21-35) stay untouched and OWN the legacy rows (the
  164 boundary rule's MCP twin: record which family owns which watch
  family, in the story trace).
- **Out:** palette (04), the walk (05).

## Acceptance criteria

- [ ] MCP-003 proven: run_steward returns run_id before phase work (slow-phase fixture); polling reaches terminal state with receipts.
- [ ] The setup interview resumes across tool calls (durable session); finalize activates atomically — the same seams as Web.
- [ ] The watch boundary recorded and tested: graduated tools refuse legacy rows typed, and vice versa; nothing replaced.

## Test plan

- **Unit:** tests/unit/test_project_mcp_driver.py (+ watch-graduation coverage beside the 164 suites).

## Trace record (orchestrator round, 2026-09-02)

- The boundary rule, as shipped: graduated tools guard with
  _require_graduated_watch (state in active/tested/paused/retired;
  refusal code legacy_watch_boundary); the reactions family is
  untouched and owns state='' rows. Both directions under test.
- ORCHESTRATOR FIXES in-round: (1) the three copied steward
  serializers now DELEGATE to the route's own (the resources.py
  precedent — one source of truth; copies drift); (2) the command
  insert guard narrowed from a bare except-pass to
  sqlite3.IntegrityError only — a disk or schema failure must
  surface, only the replay conflict is silent.
- Copied-glue register additions: _NATIVE_PROVIDERS (providers.py
  31-43 mirrored). The serializer copies were struck from the
  register by delegation.
- The charter's "propose" watch verb does not exist as a WatchService
  seam — proposing lives in the setup interview; the tools mirror
  the actual route surface (recorded, not invented).
- command_id posture mirrors each route exactly; routes without
  idempotency did not have one invented (registered per tool in the
  build report).
