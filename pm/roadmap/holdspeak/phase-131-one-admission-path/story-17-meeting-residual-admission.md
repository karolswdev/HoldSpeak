# HS-131-17 — Meetings lose the parallel engine

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
- **Depends on:** HS-131-02, HS-131-08
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

Meeting session start still constructs a mutable config-time `MeetingIntel`
alongside the frozen admitted plan. Bookmark auto-label runs that engine in a
background thread instead of the existing admitted bookmark seam, and dormant
MIR would route model work outside the meeting child if enabled. These parallel
paths can silently retarget and publish without the child receipts required by
Constitution Articles VI.2 and XI.1–3.

## Scope

### In

- Begin with a Sol-ruled design beat that chooses delete versus admit for dormant
  MIR and proves the meeting object no longer needs a parallel live engine.
- Replace config-time `MeetingIntel` construction with the frozen
  `MeetingIntelPlan`, explicit capability/liveness flags, and engine construction
  only inside a claimed invocation child's exact dispatch context.
- Route bookmark auto-label through `_admitted_bookmark_label` under the live
  meeting session parent. Preserve one child and terminal receipt per actual
  label attempt; deterministic labels mint no model child.
- If MIR remains, freeze its capability revisions in the session plan and admit
  each physical routing/model attempt as a child that rechecks session
  liveness, authority, revocation, and attempt budget. If it is deleted, remove
  its flags, branches, and latent provider reachability completely.
- Preserve HS-131-08's live/deferred distinction, displaced-work queue,
  cancellation ordering, all-settled readiness, and no-principal recording
  behavior. A meeting allowed to record without intelligence may not construct
  an engine.
- Remove `dormant-mir`, `legacy-live-meeting-engine`, and
  `bookmark-auto-label` from `NAMED_FINDINGS` only after the AST and runtime
  proofs agree.

### Out

- Meeting UI, recording behavior, plugin output changes, or new MIR features.
- Retaining the parallel engine as a liveness probe or compatibility fallback.
- Treating the session parent as the receipt for bookmark or MIR model calls.
- Enabling dormant MIR without explicit owner-visible product work.

## Acceptance criteria

- [x] A Sol-ruled design records the delete-versus-admit MIR decision and proves
  every retained model-bearing transition under the frozen meeting plan.
- [x] Session start constructs no `MeetingIntel` or provider engine outside a
  claimed invocation dispatch context.
- [x] Bookmark auto-label reaches `_admitted_bookmark_label`; each model attempt
  has the meeting session as causal parent, the exact revision, and one immutable
  terminal receipt.
- [x] MIR is unreachable and deleted, or every physical attempt is an admitted
  session child with liveness, revocation, budget, cancellation, and late-output
  fencing.
- [x] Recording without an intelligence principal continues honestly with zero
  engine construction and zero inference children.
- [x] The one-path census removes all three meeting findings with zero meeting
  scopes in `ADAPTER_ALLOWLIST` and zero unregistered execution.

## Test plan

- Design: state-machine review for start, live analysis, bookmark, MIR,
  stop/cancel, displaced work, deferred retry, and no-principal recording.
- Unit: engine-construction sentinel at session start; admitted/deterministic
  bookmark cases; MIR delete or child-cardinality matrix; revocation,
  cancellation, restart, and late-publication races; one-path census.
- Mutation: restore background `generate_bookmark_label` and config-time
  `MeetingIntel`; prove both exact named fence failures before restoring green.
- Integration: live and deferred meeting sessions, including recording-only
  mode, with parent/child/revision/receipt inspection.
- Manual / device: HS-131-12 exercises bookmark labeling and any retained MIR
  behavior against the real model.

## Notes / open questions

[DESIGN-HS-131-17](./DESIGN-HS-131-17.md) rules: delete the dormant
session-owned MIR branch while preserving the separately admitted deferred routing
product; delete the parallel live engine; route automatic bookmark refinement
through the existing admitted child seam. Liveness is a capability fact, not an
engine object constructed outside admission.
