# Hub and backend development

Follow the [root guide](../AGENTS.md), the [Constitution](../docs/internal/CONSTITUTION.md)
and the [backend architecture](../docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md).
Read the actual caller, service, persistence and execution path before changing
behavior. A descriptor or configuration field does not prove runtime enforcement.

## One hub, one behavior

- Keep HTTP and MCP adapters thin: parse/validate, obtain the authenticated
  principal, call the composed service, serialize its result or named error.
  Business rules belong in the service, persistence in the DB layer.
- HTTP, MCP and primitive routes must use the same live services and DB from
  `runtime/composition.py`. Do not improvise a second live composition root
  or a bare service that loses the hub's callbacks and policy wiring.
  Bare fallbacks are only for the contexts documented by that module.
- Keep DB, filesystem, synchronous model/probe and subprocess work off the
  async event loop. Use `run_in_threadpool` or the existing async boundary;
  do not wrap an already asynchronous operation in a blocking substitute.
  Read routes must not stall the desk behind a live machine/provider probe.
- The hub owns durable domain state and shared windows. Browser views consume
  it; they do not become competing authorities. Preserve revision guards,
  transactions and named conflicts. Commit state before announcing its change.
  Use the composed announce/change bus, scoped to the changed entity; avoid
  duplicate frames or full-desk refreshes for a local write.

Examples: `web/routes/desk_windows.py` for the thin/threadpool route,
`services/desk_window_service.py` for shared state and revisions,
`runtime/composition.py` and `web/announce.py` for live wiring and announces.

## Authority, effects and recovery

- Identity and authority come from authenticated context and bounded delegation,
  never client JSON or model text. Keep route rights, operation rights and
  actual service checks aligned. Read access does not grant effect authority.
- Route consequential work through kernel admission and execution. Reuse an
  existing operation contract where one applies; a new effect needs an explicit
  contract, not a bypass. Preserve frozen payload, target and authority, a
  single execution claim and a terminal outcome. Pure reads need no new
  approval ceremony.
  The owner's gesture or valid prior delegation is consent; do not add a
  second confirmation for the same authorized act.
- Admission, approval, dispatch and completion are different states. Check the
  actual executor and stored outcome before reporting that something was sent,
  typed, launched or finished. A successful HTTP response is insufficient.
- Give retriable commands stable IDs and a defined idempotency scope. Reuse
  the existing DB uniqueness/CAS or journal claim; an in-memory flag cannot
  prevent duplicate effects after restart. For the kernel, replay is scoped
  by principal and key; a changed payload must not silently reuse the result.
- Preserve durable cancellation, deadlines and one terminal winner. An unknown
  external outcome stays uncertain; do not blindly retry it. Closing a browser
  window is not proof that its server-side work stopped.
- Use injected connector/process/provider adapters for external effects. Keep
  credential custody in the established secret store/environment boundary;
  never leak secret values into logs, fixtures, IDs, receipts, errors or normal
  read responses. Do not turn a provider failure into a quiet success.

Read `kernel/admission.py`, `kernel/broker.py`, `kernel/journal_atomic.py`,
`operations.py` and the domain executor for the operation you change.
These are requirements for new work, not a claim that every legacy path
already satisfies them. In particular, check optional actuator broker wiring
before claiming kernel receipts. The stored actuator toggles are not enforced
by current Desk/Mission Control construction; a proposal decision alone does
not dispatch an actuator. Track such gaps in `pm/STATUS.md`; do not describe
a declaration such as `Admission.enforced` as execution proof.

## Inference, storage and contracts

- Use the existing capability/assignment and typed inference path for core
  model jobs. Share the composed runner and frozen route; preserve invocation
  admission, egress, fallback rules, deadlines, cancellation and receipts.
  Do not call a provider directly from a route or invent another resolver.
  Specialist runtimes, such as the Line speech process, have a separate
  explicit contract; do not claim the core runner already covers them.
- Canonical schema lives in `db/schema.py`; upgrades use `db/reconcile.py`.
  Preserve data and follow its shape-based policy. Do not add a separate
  version migration chain, wipe rows to make an upgrade pass or rely on a
  schema-stamp bump alone. Test fresh and existing DB shapes for an upgrade.
- Stored and wire instants use aware UTC via `timestamps.utc_now()` /
  `utc_now_iso()`. Local quiet hours/display use aware `local_now()` and the
  existing parsing helpers. Do not introduce naive stored times or another
  clock policy.
- Keep transport-neutral operation definitions, codecs, events and real
  producers aligned with their HTTP/MCP consumers. Update the relevant
  operation/tool schema and realtime frame registration with implementation.
  Generate references with the matching scripts; do not edit generated
  inventories by hand. `scripts/gen_docs.sh` is the complete generator entry.

## Prove the changed seam

Use the root guide's lock, isolated HOME and focused test budget. Test the
real service/route and stored state. Add refusal, stale revision, retry/replay,
cancellation, restart or migration cases when the changed behavior needs them.
Use recorded provider/connector adapters for deterministic tests; live-device
or provider proof needs a separately authorized, isolated run.

Relevant existing guards include `test_hub_handlers_off_loop.py`,
`test_hub_loop_budget.py`, `test_db_schema_policy.py`,
`test_static_sql_matches_schema.py`, `test_aware_time_census.py` and
`test_kernel_effect_fence.py` under `tests/unit/`. Run the files that cover
your change and the required quick check, not the full tape as another gate.
Report the boundary actually exercised and any missing caller wiring.
