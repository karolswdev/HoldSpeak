# Backend basics for HoldSpeak (draft for future `holdspeak/AGENTS.md`)

**Status:** Committee advice — post-merge review pending; no pre-merge gate.
**Drift warning:** anchors were checked on `origin/main` in this worktree on
2026-10-30. Re-check them before copying into a repository instruction file.

This is a compact backend route for the root AGENTS workflow, not a redesign of
the hub, kernel, or persistence model. The Constitution and UX-CANON are higher
authority.

## Routing

- Root `AGENTS.md` owns universal workflow, safety, and focused-test rules.
- `web/AGENTS.md` owns browser-face and route-presentation rules.
- This route applies to `holdspeak/**`, backend tests, contracts, and source
  documents that generate public API/MCP descriptions.
- Read the nearest source and contract before editing. Follow existing seams;
  do not add a parallel service, database, or effect path.

## Enforceable backend basics

1. **Keep HTTP routes thin.** Parse input, use `request.state.principal`, call
   the composed service, and serialize result/error. Keep DB, provider, policy,
   and effect logic out of routes. Canonical shape:
   `holdspeak/web/routes/desk_windows.py:1-16,53-67`. A fallback constructor is
   lawful only for contexts named at `holdspeak/runtime/composition.py:16-30,320-365`.
2. **Keep blocking work off the event loop.** Async handlers wrap DB, probe,
   model, filesystem, and subprocess work with `run_in_threadpool`, as in
   `holdspeak/web/routes/desk_windows.py:20-24,61-67` and
   `holdspeak/web/routes/memory.py:20-54`. Preserve `tests/unit/test_hub_loop_budget.py`;
   do not copy an inline blocking call from an older handler.
3. **Use one live hub authority.** HTTP, MCP, and primitive routes resolve the
   same `RuntimeServices` instances and DB; use
   `holdspeak/runtime/composition.py:14-30,428-450`. Do not create a second
   live root. Browser-visible writes use the composed change bus and one announce
   scope. The exact quiet allow-list is `holdspeak/web/announce.py:20-25,26-89`;
   extend it only with a reason and affected-write test.
4. **Authenticate at the edge; derive identity.** Use the principal supplied by
   hub middleware, never identity, rights, or authority from request JSON. Keep
   route rights and operation authorization aligned with
   `holdspeak/web_server.py:1043-1103` and `holdspeak/operations.py:44-50,84-111,2427-2505`.
   Reject authority fields; payloads must not mint or widen grants.
5. **Put consequential work through the kernel once.** Preserve propose →
   authorize/approve → claim → dispatch → terminal receipt. Approval is not
   dispatch: `holdspeak/kernel/broker.py:242-268` reaches `awaiting_execution`,
   while claim is a separate CAS at `holdspeak/kernel/journal.py:300-322`.
   Keep target, placement, authority, and payload immutable after admission.
6. **Make retries explicit and durable.** Every command has a stable opaque
   operation/domain ID and documented idempotency scope. Replay is scoped by
   `(principal_identity, idempotency_key)` under one write lock; same payload
   replays, different payload refuses (`holdspeak/kernel/journal_atomic.py:59-79`).
   Use DB uniqueness/CAS, not an in-memory “already done” flag.
7. **Treat receipts as outcome records.** Where admitted, domain state,
   terminal state, and kernel receipt commit together via
   `holdspeak/kernel/journal_atomic.py:107-166`. Return safe references, not
   credentials or raw provider responses. Check operation and receipt state;
   never report an approval row as a completed effect.
8. **Keep the model boundary typed and frozen.** Capability definitions say
   what a job requires, not which model runs it
   (`holdspeak/inference_capabilities.py:1-8,19-30`). Validate before provider
   resolution. Physical inference uses typed invoke admission with frozen
   revision, egress, definition origin, and deadline
   (`holdspeak/kernel/inference_invoke.py:65-113`); do not revive `inference.run@1`.
9. **Change schema through the canonical source.** Edit `SCHEMA_SQL` and the
   additive reconciler; never drop a table/column or delete rows to migrate
   (`holdspeak/db/reconcile.py:1-8`, `holdspeak/db/schema.py:1-8`). The stamp is
   informational, not a version gate. Shape changes update the canonical fixture
   and focused policy tests (`tests/unit/test_db.py:1733-1761`,
   `tests/unit/test_db_schema_policy.py`).
10. **Use aware time everywhere.** Stored/wire stamps use `utc_now()` or
    `utc_now_iso()`; local wall-clock decisions use aware `local_now()`
    (`holdspeak/timestamps.py:1-16`). Do not add naive time; the AST census is
    `tests/unit/test_aware_time_census.py:1-20,182-194`.
11. **Keep effects injected, gated, and secret-safe.** Use a connector and
    permission manifest; routes/services must not open sockets or shell out.
    `holdspeak/plugins/gated_connector.py:1-29,68-92,137-151` binds scope and
    payload digest and reads credentials only at dispatch. Secrets never belong
    in IDs, logs, errors, fixtures, arguments, or receipts.
12. **Update contracts and evidence together.** Operation descriptors are the
    transport-neutral source (`holdspeak/operations.py:192-210`); regenerate
    public docs/MCP rosters with the repository script when source changes. Add
    the narrow contract/DB/loop/receipt/secret test for the seam. Use isolated
    HOME and affected tests only; never a real desk/provider.

## Design requirements versus current guarantees

- The Constitution requires a receipt for every admitted consequential effect.
  `ActuatorExecutor` accepts an optional broker: with one it closes a kernel
  receipt, without one it does not (`docs/ACTUATOR_DEVELOPMENT.md:98-115`). Do
  not document universal receipt coverage without proving caller wiring.
- Actuator config is not a universal off switch: Desk and Mission Control pass
  `allow_actuators=True` and no ID allow-list; config is status-only there
  (`docs/ACTUATOR_DEVELOPMENT.md:127-137`). Do not claim those toggles narrow
  execution until wiring and tests change.
- `Admission.enforced` is a descriptor declaration, not execution enforcement
  (`holdspeak/operations.py:84-111`). Verify the broker/executor path before
  calling a guarantee enforced.

## Committee advice — post-merge review pending (no pre-merge gate)

**VERDICT: RATIFY-WITH-CONDITIONS.** The integrated guide is accurate and useful.

**FINDINGS:** The kernel wording at `holdspeak/AGENTS.md:36-43` is a sound new-work
requirement and its legacy-gap caveat at `:56-63` is present. For zero ambiguity,
future edits should say “where an existing kernel contract applies”; the registry
can intentionally bypass the kernel for exempt or unenforced descriptors
(`holdspeak/operations.py:2581-2592`). The adapter rule is not a blanket shell or
provider ban: injected/gated process and provider seams remain allowed
(`holdspeak/plugins/gated_connector.py:220-251,268-292`). Inference explicitly
keeps specialist speech separate (`holdspeak/AGENTS.md:67-72`; `holdspeak/speech_session/child.py:1-13`).
Authority, model seam, DB reconcile, and generator instructions match the live
edges (`holdspeak/web_server.py:1049-1103`; `holdspeak/kernel/runtime.py:196-214`;
`holdspeak/db/reconcile.py:1-8`; `scripts/gen_docs.sh:1-34`).

**CONDITIONS:** Treat the kernel clarification as a post-merge documentation
follow-up, not a shipping gate. Preserve the explicit actuator receipt/toggle
gaps and the no-premerge-gate fast-cycle ruling.

**MISSED:** None material. **TUESDAY:** The guide directs an implementer to one
hub, one authority, one effect seam, and a focused proof. **UNKNOWN:** No tests or
live provider/device runs were performed, per brief.
