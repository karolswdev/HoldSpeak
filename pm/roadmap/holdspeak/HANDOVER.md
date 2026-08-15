# HANDOVER — Phase 131, HS-131-12 Real-Model Walk

**Date:** 2026-08-15
**Branch:** `phase-131-one-admission-path`
**Phase:** 16/17 stories done
**Last completed story:** HS-131-11 — entry-point contract
**Next story:** HS-131-12 — assembled real-model walk
**Draft PR:** #454 — keep draft until the whole phase is complete

## Start here

HS-131-11 is done. All five public/operator/developer entry points now agree with
the zero-finding fence: one admitted `InferenceRunner` path, one immutable
revision and terminal receipt per physical attempt, honest parent/session
causation, bounded scheduler delegation, and no local-Whisper exemption. The
isolated documentation/API/schema/render matrix is 52 passed.

HS-131-12 is the only story left. Perform the assembled real hub/worker/model
walk, then read the focused, web, and backend output at the owner's functional
bar. Repair ordinary product regressions; do not reopen the meeting MIR decision,
the HS-131-16 hostile protocol-review loop, or a speculative hardening sweep.
Swift remains held; web DeskOS is the spec. Draft PR #454 stays draft until the
walk and phase closure are complete.

## HS-131-11 shipped contract

- Canonical contract:
  [`docs/ARCHITECTURE.md#inference-admission-one-path-one-receipt-per-attempt`](../../../docs/ARCHITECTURE.md#inference-admission-one-path-one-receipt-per-attempt).
  README, backend decomposition, security, and models state the same boundary at
  their own level.
- Ask is `holdspeak.ask@1`; saved Agents are `recipe:<id>` at `last_modified`.
  Every attempt freezes a `DeploymentRevision`; cancellation fences late output,
  fallback/retry gets separate children, and uncertainty remains `indeterminate`.
- Security names scheduler as actor, owner as delegator, exact delegation terms,
  every current refusal code, session parents, shared Whisper/preload children,
  and content-free kernel fields.
- `SYNC_REGISTRY` is Python/web contract authority. Swift is neither authority nor
  work in this phase. Mesh instructions use deliberate node pairing, the node
  bearer, the public offer pin, and hub-only private-key custody.
- Current symbols, operation names, routes, registry kinds, and commands were read
  against production code. No production API/schema changed, so no generated
  snapshot changed.
- Evidence: **52 passed** under a fresh isolated HOME, including API surface,
  primitive/sync contract, doc drift and links, architecture guards, and real
  Mermaid rendering. See
  [`evidence-story-11.md`](./phase-131-one-admission-path/evidence-story-11.md).

## HS-131-10 closed contract

- Final census: 100 sites; gateway 1, witness mints 2, gateway binding 1,
  physical adapters 69, admitted seams 27, findings 0, unregistered 0.
- Every original finding family left by deletion or admission. No command,
  meeting-session product module, or other domain service entered the adapter
  allowlist.
- The literal-spine, exact-context, cardinality, provenance, journal-hygiene,
  cancellation/recovery, late-publication, receipt-immutability, and mutation
  suites pass **143 tests** under a fresh isolated HOME.
- Evidence: [`evidence-story-10.md`](./phase-131-one-admission-path/evidence-story-10.md).
  Final inventory: [`findings-inventory.md`](./phase-131-one-admission-path/assets/hs-131-10/findings-inventory.md).

## HS-131-17 shipped contract

- The dormant session-owned MIR branch is deleted: no private `mir_*` constructor
  inputs, live plugin enumeration, or post-stop `process_meeting_state()` call
  remains. `MeetingConfig.intent_router_enabled`, plugins, persistence, manual
  routing tools, and the separately admitted deferred queue remain.
- `MeetingSession` owns no `MeetingIntel`. It keeps the frozen plan, admitted
  parent, closed fence, and explicit live flag; startup reads frozen readiness and
  constructs no provider.
- Automatic bookmark refinement goes through `_admitted_bookmark_label`; each
  actual model attempt is one exact-revision child with one terminal receipt.
  Deterministic, refused, failed, cancelled, and late cases keep the timestamp
  label.
- Captured focused/integration proof: 166 passed. Full isolated unit lane: 4,676
  passed, with only the three unchanged inherited UI/copy guards.
- Evidence: [`evidence-story-17.md`](./phase-131-one-admission-path/evidence-story-17.md).
  Design ruling: [`DESIGN-HS-131-17.md`](./phase-131-one-admission-path/DESIGN-HS-131-17.md).

## HS-131-16 shipped contract

Production pairing now provisions two distinct things:

- a per-node bearer token for worker HTTP authentication;
- a public Ed25519 offer pin and key ID.

The hub retains the private signing key. A signed offer binds the destination,
credential generation, relay and execution revisions, hub operation and warrant,
attempt ordinal, nonce, payload digest, and bounded deadlines. The worker verifies
and reserves that offer once before revision persistence, runner construction, or
provider work.

Every physical attempt runs through the worker-local `InferenceRunner` under the
node principal and ends in one immutable local receipt. The worker reports a
content-free receipt cohort plus node MAC. The hub independently revalidates and
settles it. Exact transport retry resends the same report and never reruns the
model. Stop, replay, expiry, revocation, wrong-node, wrong-generation, and late
publication paths refuse by name.

## Exact final fingerprint

Base entering the story:

```text
e4193f12de0832892fea5946f3fb6aef4073ec5f
```

Final HS-131-16 source and tests:

| Fact | Value |
|---|---|
| Changed paths | 40 (27 tracked, 13 new) |
| Manifest SHA-256 | `24e25287380abcbad6527d5037f051afccbf155620059b38f11069f8085b1413` |
| Complete diff SHA-256 | `17cb83aaf53082bfccf1e963b942c7304e43fad8f76aca2038fea4e018b14450` |
| Complete diff size | 482,706 bytes / 10,779 lines |
| `git diff --check` | clean |

The rejected forensic reference remains untouched at:

```text
.claude/worktrees/agent-a25f35455ad9f5871
```

Its fingerprint remains 151 paths / 2,034,740 bytes, manifest
`332b62e95a00c996db9af663cb9b12be7b3da32361e4294ee5faa7a3ca76ef32`,
complete diff `62e21a998c76af027f80791e7023f2dd43efa0775b1f9afc6882ae7a627bbb51`.
It is reference material only.

## Verification read by the orchestrator

- Delivery Workbench evidence: **864 passed** in the final 46-file matrix.
- That matrix includes authenticated offer/refusal coverage, production pairing,
  worker admission and receipts, stop/report retry, separate-process hub/worker
  loopback, cardinality, and the zero-finding one-path census.
- Full unit candidate lane: **4,643 passed** with a 30-second per-test bound,
  excluding exactly three inherited guard files.
- The three inherited backend guard failures are unchanged from `e4193f12`:
  old Intelligence left rails, old product-copy vocabulary, and one old
  Follow-Through em dash. Every inspected input is byte-identical to the base.
- Web: tokens, architecture guard, typecheck, and production build pass.
  **785 tests pass** outside two unchanged Speak test files whose stale mocks
  produce 15 inherited failures. No TypeScript source or test changed in 131-16.
- The all-`tests/` isolated-HOME command also reaches browser e2e setup that has no
  Playwright binary in that fresh HOME; that environmental error is not presented
  as green and is not a mesh regression.

The owner explicitly closed the academic review loop. Remaining hostile-signer,
perfect distributed atomicity, microscopic scheduler, future-schema, and protocol
taxonomy observations stay notes unless ordinary product use reproduces damage.

## Why the candidate grew from 37 to 40 paths

The full unit lane exposed three hard-coded schema-v58 assertions after the mesh
worker ledger advanced the database to v59. Only those expected literals changed:

```text
tests/unit/test_decision_commitments.py
tests/unit/test_decision_record_service.py
tests/unit/test_monday_brief_service.py
```

The same lane found `mesh_local_runner.py` seven lines over the existing broker
budget; its module prose was shortened without changing behavior. A scheduler-
sensitive 8 ms test was narrowed to the transport timeout seam it actually claims.
No third repair brief or product-scope expansion was opened.

## Unrelated workspace state

Preserve and do not bundle these pre-existing paths with future story commits:

```text
 D .tmp/BUNDLE-OK.md
?? pm/roadmap/holdspeak/phase-120-the-reckoning/
?? web/test-results/
```

The Phase 120 files are historical roadmap recovery work. The web test result is
local output. Neither belongs to Phase 131 shipping commits.

## Next sequence

1. Read `story-12-the-walk.md`, then start HS-131-12 through Delivery Workbench.
2. Build `scripts/walk_one_admission_path.py` from the existing live-LAN pattern,
   using only isolated database/HOME state and the real model on `.43`.
3. Prove the assembled ordinary paths: Ask/Agent, Sequence/Workflow/Workbench,
   one finite service, bounded schedule success/refusal, speech session children,
   frozen target identity, cancellation, fallback cardinality, and sync/restart.
4. Capture the focused Phase-131 matrix, web suite, and full backend suite. Read
   every output before the final done decision; compare failures to the inherited
   ledger and fix only current ordinary-use regressions.
5. Triage the stale live-bus selector as a bounded harness repair if it still
   blocks CI; do not turn the 66 integration failures into an academic sweep.
6. Keep PR #454 draft until the phase is complete; watch CI, read conclusions,
   classify, and merge as separate actions.

## Rails that still matter

- Constitution Articles V, VI, IX, and XI remain the acceptance floor.
- Every Python verification uses a fresh isolated `HOME`; never migrate the
  owner's real database during tests.
- Read complete output before a done flip.
- Never use `--no-verify`.
- Stage exact story paths only; never `git add -A` in this shared checkout.
- Keep credentials, prompts, completions, claim witnesses, dispatch contexts, and
  verified capabilities out of proof metadata and logs.
- Functional ordinary-use failures are bugs. Theoretical hardening is a ledger
  note unless the shipped product can reproduce damage.
