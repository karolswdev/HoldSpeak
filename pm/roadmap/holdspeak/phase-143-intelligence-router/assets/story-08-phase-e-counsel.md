# Counsel record — Phase E capped implementation pass (HS-143-08)

Sol counsel, 2026-08-24, post-commit pass on Phase E at `abe4bb63`
(slice 1 `dd1ef120` + slices 2-4 `abe4bb63`), audited against the
ratified design + E1-E3. Focused verification: the eight named proof
files, 129 passed; production-object probes through real broker,
routes, controller, and receipts. Verdict: **ONE FIX ROUND REQUIRED —
four ordinary-path findings; then RATIFY-WITH-NOTES and ship.**

The bar, the full per-finding evidence (exact seams, reproductions,
required proofs), and the checks that held are recorded verbatim in
the session ledger; the four findings:

## E-F1 — The migrated Rails sentinel is permanently non-executable

The E1 migration recovers the exact historical local path
(inference_adoption_service.py:2197-2205, deployment at 2269-2282)
but then persists the private artifact as `state="removed"` with an
empty `local_locator` (2301-2307) and binds a hard
`unavailable/unobserved_legacy_local` readiness observation
(2328-2342); route_plan_service.py:1356-1368 allows unavailable
first-use only for the speech exception. Reproduced: migration says
`migrated`, yet every frozen Rails route is
`known_preflight_unavailable`, terminalizes `failed`, 0 attempts,
0 children — the batch is ALWAYS event-only. The committed test
proves rows exist, not that the migrated route can execute. Required
proof: blank sentinel + nameable saved local deployment preserves the
locator; first frozen route executes without a migration-time probe;
one physical leaf entry, one child receipt, one summarized journal;
unmappable variant = event-only + one refusal receipt + zero partial
rows.

## E-F2 — Refusal identity aliases the valid routed request

record_pre_route_refusal (inference_parent_route_bundle_service.py:
155-175) uses the executable bundle's command_id as the refusal
parent's idempotency key and returns any existing receipt unverified.
Reproduced on BOTH product surfaces: stale override → clean retry
fails `inference_route_execution_parent_sealed` (no provider call, no
artifact; valid bundle attached to the refused zero-budget parent);
missing-assignment refusal → assignment created → retry still sealed;
success → stale override returns the OLD `succeeded` artifact receipt
as its "refusal"; delivery HTTP: 200→409-with-succeeded-receipt and
409→500. Required: DISTINCT deterministic, content-free, reason-bound
refusal identities that cannot collide with executable bundle
identities; five-sequence proof through both product surfaces (see
verbatim record); no mocking of run_owner_draft/bundle
start/planning/controller/receipts.

## E-F3 — Rails egress truth disappears before the journal is persisted

rails_observer.py:133-139 puts the frozen boundary in the transient
batch; 142-155 builds the persisted journal body IGNORING
batch["egress"]; web_server.py:1158-1168 discards the transient
batch. Reproduced: a successful routed batch froze `local`, the
persisted note had NO egress field. On a cloud assignment rail events
would egress with the durable journal silently losing that fact — a
HARD-boundary badge violation. Required proof: local AND
cloud/private routed batches through the real broker + journal
materializer — persisted/opened journal carries exactly one visible
egress badge equal to the widest frozen boundary, receipt and journal
agree, replay preserves one note/badge/call.

## E-F4 — Known route failure is relabeled as indeterminate

rails_observer.py:414-423 and inference_owner_draft.py:173-195 map
every non-success/non-refusal outcome — including known `failed`
(preflight_unavailable, 0 attempts, no dispatch) — to parent
`indeterminate`. Reproduced: route outcome `failed`, parent receipt
`indeterminate`. A normal-path receipt lie on Phase E's sole
degradation surface. Required proof: known-unavailable route → zero
child/attempt, route AND parent terminalize known `failed`, adopter
degrades only after those receipts exist; separate proof that only
genuine dispatch uncertainty stays `indeterminate`.

## Checks that held (Sol)

Fresh missing-assignment refusals = one terminal receipt, zero
bundle/route/child; attempt-time KernelRefused keeps real receipts;
Cadence stays OWNER with no SERVICE escalation; post-freeze
assignment edits never retarget; only elected {draft} materializes;
delivery stays non-posting with one-child diff replay; Rails replay
across a DB reopen = one attempt/child/note/call; rails-observer@1 is
capability-only; the parent-kind reconcile heals with row survival;
trusted-child retains the sealed Rails basis.

## Orchestrator dispositions (2026-08-24)

- **E-F1–E-F4 ALL ACCEPTED** — each is a normal-action receipt/
  execution-truth defect squarely inside the yolo bar. No dissent.
- ONE Terra fix round dispatched with Sol's exact seams and proof
  specs. After it lands with the orchestrator's sweep clean, Phase E
  is RATIFIED-WITH-NOTES per the cap — no further counsel round.

## Fix round landed — PHASE E RATIFIED-WITH-NOTES (2026-08-24)

All four findings fixed per Sol's proof specs, plus one orchestrator
sweep catch on the E-F1 fix itself:

- E-F1: the migrated Rails artifact keeps its exact private locator as
  a usable declaration; a narrow first-use route exception exists only
  for the exact migrated Rails runtime revision; readiness persists
  `ready/loaded_under_rails_observer` only after the first successful
  admitted child. Sweep catch: the migrated deployment leaked into the
  generic reverse lookup (deployment_revisions.py locator match) and
  became the CURRENT THOUGHT DEPLOYMENT in a fresh rig — and the
  migration fired on a default-constructed blank config with the
  observer DISABLED. Fixed: the migration gates on an ENABLED
  observer (default blank+disabled mints nothing); the Rails
  deployment is capability-owned (`active=0`, matching the speech
  precedent) and excluded from the generic setup projection; an
  existing marker replay repairs any pre-fix active footprint.
  Proofs: thought execution_revision identical before/after
  migration; Rails artifact absent from generic installed models;
  disabled-default creates zero rows; both acquisition glass e2es
  serial-green.
- E-F2: refusal identities live in their own namespace —
  `pre-route-refusal:` + sha256 of
  {schema InferencePreRouteRefusalIdentity@1, command_id, reason} —
  reason-bound, content-free, collision-free with executable bundles;
  the seam never returns a non-refusal receipt as a refusal. All five
  counsel sequences proven through the decision service and the
  delivery HTTP route (override→retry succeeds; success→stale
  override gets a distinct refused receipt; assignment
  restore→retry succeeds; valid replay = one call/artifact; overrides
  create nothing).
- E-F3: the persisted Rails journal carries exactly one badge
  `[egress: <boundary>]` = the widest frozen member boundary, proven
  for local and cloud routes with receipt/journal agreement and
  replay-safe cardinality.
- E-F4: known terminal route outcomes keep their true parent outcome
  (failed stays failed; cancelled/refused preserved); only genuine
  dispatch uncertainty (ProviderIndeterminate) stays indeterminate —
  proven for Rails and the shared owner adapter.

Orchestrator verified independently (focused 233 + 101 passed;
confirming sweep **6470 passed / 51 failed / ZERO branch-new** — 48
inherited + delivery-campaign ×2 and refinement-recovers-owner xdist
flakes, each serial-green ×2). Per the cap there is no further
counsel round: **Phase E is RATIFIED-WITH-NOTES.** Ledger carried:
none new beyond the design's (remote adopters' future SERVICE
capabilities stay separately chartered).
