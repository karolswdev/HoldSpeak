# HS-T23-02 · Correct only the text path-coverage classifier

**Status:** fully specified conditional task. Requires accepted G23, completed [HS-T00](HS-T00-baseline.md)/[HS-T23-01](HS-T23-01-contract.md), and a scoped implementation assignment in the authorized repository lane. Planning permission alone does not unlock it. Parent: [HS-S23](../stories/HS-S23-path-bound-guard.md). Next: [HS-T23-03](HS-T23-03-verification.md).

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [contract](../stories/HS-S23-path-bound-guard.md#proposed-contract-and-g23-decision), [matrix](../stories/HS-S23-path-bound-guard.md#acceptance-matrix), [required behavior](../stories/HS-S23-path-bound-guard.md#required-observed-behavior-after-an-authorized-implementation) and [source map](../stories/HS-S23-path-bound-guard.md#exact-existing-context-and-editable-ownership); [V23](../VALIDATION.md#v23-first-slice-verification); invariants [I16/I18/I19/I20](../INVARIANTS.md); actual predecessor reports. No hidden conversation context is required.

## Owned files

**Existing, editable:**
- `holdspeak/services/program_text.py`: `within` branch of `_lowers_head` and a cohesive private coverage helper beside it.
- `tests/unit/test_program_text.py`
- `tests/unit/test_program_agent_bar.py`
- `tests/unit/test_program_shaper.py`

No new production module, schema, route, public API or dependency. Helper/test names are **proposed**, not existing contracts. All other story paths, fixtures, night/canon consumers and public docs are read-only. If correctness requires another file, stop for an explicit owned-path amendment.

## Implementation and proof sequence

1. Recheck SHA/status and accepted G23. Confirm the baseline failure/nonfailure report before editing.
2. Add C01–C15 regression cases using existing parsed/printed text and real rig state. Proposed test labels should say coverage expansion, narrowing, equivalence or mixed replacement; do not report them as preexisting. Preserve a stable `program.within` diff row even when coverage is equivalent but representation differs.
3. Split `test_removing_a_within_path_lowers_the_bar`: retain the whole-list-removal owner gate; change the partial-removal expectation only according to G23. Add additive/mixed expansion cases. Record the expected red result against the old classifier, distinguishing it from unrelated fixture failures.
4. Implement the minimal Boolean comparison: does the new union admit any path absent from the old union? Keep empty-universal semantics, slash boundaries and the accepted lexical edge handling. Do not canonicalize persisted/printed lists, resolve symlinks, expand globs, inspect path existence or import stateful planner modules.
5. Exercise service behavior, not only the helper: owner preview/no writes; owner expansion held then explicit row approval; creator-agent expansion refused; non-owner `allow_lower` refused; unrelated-agent actual write refused; stale-base conflict. Check returned rows/allowed text plus stored `within`, revision and existing relevant checkpoint/event assertions.
6. Extend existing shape tests using their injected response seam: generated expansion at YOLO is retained for a separate owner action, including owner-invoked shaping; a mixed answer applies only its independent allowed row and retains the lower-bar against the refreshed base. Do not change mixed-row partial-write policy.
7. Run the exact V23 focused budget after the final edit. Night/canon remain unchanged. Inspect the final diff for unrelated lower-bar fields, storage/wire changes, direct-update behavior or expanded ownership.

## Acceptance

All story cases and authority/YOLO behaviors are observable in existing test suites. Expected red is explained; final named tests pass in isolation, or the task is reported incomplete with precise blockers. Parser, direct update, manual plan and diff behavior are unchanged. No new filesystem enforcement claim appears in code/comments/report. Only owned files differ, unless an explicit amendment is recorded.

## Rollback and stops

Rollback is a reviewed reverse patch to this helper/branch and accompanying expectations, preserving other lane changes. No data migration or stored Program rewrite is needed. Restoring old code restores its additive-expansion limitation; state that. Never reset, restore, clean, force a ref or weaken tests. Stop for unresolved normalization, changed authority, required consumer/API/schema changes or a missing proving boundary. Hold for independent verification and SHIP; do not stage, commit, push or deploy. Return [completion evidence](../COMPLETION_REPORT_TEMPLATE.md).
