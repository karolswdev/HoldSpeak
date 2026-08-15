# HANDOVER — Phase 131, HS-131-10 Zero-Finding Close

**Date:** 2026-08-14
**Branch:** `phase-131-one-admission-path`
**Phase:** 14/17 stories done
**Last completed story:** HS-131-17 — meeting residual admission
**Next story:** HS-131-10 — close the one-path fence at zero findings
**Draft PR:** #454 — keep draft until the whole phase is complete

## Start here

HS-131-17 is done. The five-story amendment wave has removed every blocking
family: the executable one-path census now reports 100 sites, zero findings,
zero blocking families, and zero unregistered execution. Do not reopen the
meeting MIR decision or the HS-131-16 hostile protocol-review loop.

Next, return to the already-shipped blocked checkpoint HS-131-10 and close it
against the now-green zero-finding fence. Then do HS-131-11 entry-point docs and
HS-131-12's real hub/worker model walk. Swift remains held; web DeskOS is the
spec. Draft PR #454 stays draft until all three are complete.

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

1. Read `story-10-one-path-fence.md`, its existing evidence, and the current
   phase status.
2. Move HS-131-10 from `blocked` to `in-progress` through Delivery Workbench.
3. Rerun the executable census and focused cardinality/provenance proof under a
   fresh isolated HOME; the blocking ledger must remain empty.
4. Update HS-131-10's checkpoint claims from blocked to closed and ship it alone
   through the stamped contract.
5. Complete HS-131-11 entry-point docs, then HS-131-12 on the real mesh model.
6. Triage current CI only at the ordinary-use functional bar; the stale live-bus
   selector is a bounded harness repair, not a new architecture review.
7. Keep PR #454 draft until the phase is complete; watch CI, read conclusions,
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
