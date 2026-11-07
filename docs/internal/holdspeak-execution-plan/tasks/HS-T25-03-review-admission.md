# HS-T25-03 · Admit merges from current local review evidence

**Conditional implementation brief; execution not authorized.** Depends on [HS-T25-02](HS-T25-02-review-observations.md), its proof, and accepted G25-A. Parent: [HS-S25](../stories/HS-S25-current-person-review.md).

## Mandatory context

[Safety](../AGENT_START.md#authority-and-checkout-safety); story [Program gate](../stories/HS-S25-current-person-review.md#program-owns-effective-eligibility), [visible state](../stories/HS-S25-current-person-review.md#visible-state-stays-truthful), [matrix](../stories/HS-S25-current-person-review.md#acceptance-matrix), [rollback](../stories/HS-S25-current-person-review.md#rollback-and-stops); [V25](../VALIDATION.md#v25-current-person-review-verification); [I16/I18/I19/I21/I22](../INVARIANTS.md); current scoped guides.

## Ownership and procedure

Production edits only existing `holdspeak/services/program_runner.py`, `program_service.py`, `brief_words.py`. Editable integration/word suites, bounded shared-rig amendment and the current `docs/programs.md` person-review paragraph are listed in V25. No new module, state, route, frontend structure, lock or final-delivery mechanism.

1. Implement a small runner-owned read-only evaluator of current Program/step/person and latest launch observation. Verify exact launch/source/PR URL+number and accepted observed-head conditions. Empty/unreadable person matching, legacy bool-only data or unavailable/incomplete/mismatched observation blocks. Do not call provider or effectful `_pr` from this evaluator.
2. Keep `person_approved` historical; add the bounded present-state projection in existing facts. Reconcile while waiting even after prior approval. Matching changes always block, independently of whether timestamp-based feedback dedup permits another round. Preserve reviewer words, same branch/PR and current dedup limits. Record attempt/failure/skip truth without claiming delivery or automatically resending.
3. Update owner admission to reread Program and step under its current `_LOCK`. At actual runner merge entry, independently reread current Program, step and launch and recompute the gate for person-gated GitHub steps, so direct/engine calls cannot skip it. Bind gh merge to the validated canonical URL. Preserve the other gates applicable to each existing caller; do not unify owner/engine CI policy. Local/non-person behavior stays unchanged.
4. Within person-gated GitHub admission only, if an outstanding request marker is already durable, do not dispatch or duplicate a success checkpoint. Render waiting for actual receipt, not a cancellable Merge/Not yet prompt. Do not broaden locking; document that simultaneous pre-marker and command-before-save windows remain unsolved. Accepted requests/actual terminal receipts are not retroactively cancelled by newer review data.
5. Ensure all facts writes incorporate reconciled state and latest saved marker rather than restoring stale copied facts. Preserve unrelated facts/requirements/rounds/history. A new semantic eligibility/target/feedback change must reach existing Program change notifications even when state does not change; timestamp-only reads should not cause notification churn.
6. Update wait/report/Your turn words using present evidence, while historical bool/checkpoints can explain prior approval. Unknown read is not never-reviewed or revoked. Remove stale Merge readiness; unavailable does not automatically prepare Ask/Send. Use existing states/surface fields only, and prove the response contract remains renderable.
7. Extend the real-producer integration chain with the bounded rig option in V25. Existing fabricated sweep remains for unrelated tests; it is not the only proof of this feature. Record requested versus actually observed merged state separately.

## Acceptance and rollback

Prove C25-04 through C25-13 plus composed producer continuity. Return [completion report](../COMPLETION_REPORT_TEMPLATE.md) with command counts/targets, current/historical facts, notification evidence and limitations. Stop for stronger concurrency/commit/poll semantics, unsafe fake-provider fallback, required new UI/API or scope conflict. Reverting code must not run old historical-latch admission over unfinished review holds; preserve outstanding/actual merges and request an authorized hold/compatibility plan if safe downgrade is unavailable.
