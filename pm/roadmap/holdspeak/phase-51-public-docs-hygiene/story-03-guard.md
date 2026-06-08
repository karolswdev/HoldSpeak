# HS-51-03 — Lock it: roadmap-vocabulary doc-drift guard

- **Project:** holdspeak
- **Phase:** 51
- **Status:** done
- **Depends on:** HS-51-02
- **Unblocks:** HS-51-04, HS-51-05
- **Owner:** unassigned

## Problem
A one-time scrub rots the moment the next phase writes a doc and pastes "see Phase
52 ..." into a user guide. The clean state needs a guard, the same way the
plugin-count and dangling-link guards keep their invariants. Without it, this phase
is a snapshot, not a contract.

## Scope
- **In:**
  - A new test in `tests/unit/test_doc_drift_guard.py` that fails when a
    **user/operator-facing** doc contains roadmap/process vocabulary: `Phase <N>`,
    `HS-<NN>-<NN>`, `PMO`, and the process words chosen in HS-51-01 (e.g.
    "closeout", "the current roadmap").
  - **Scope the scan to user-facing docs only.** Do NOT reuse the existing
    `_live_docs()` helper as-is: it returns `docs/**/*.md` minus `docs/evidence/`,
    which still includes `docs/internal/` (its own sanity test asserts
    `PLAN_ARCHITECT_PLUGIN_SYSTEM.md` is in the set). The vocabulary guard must scan
    the root `README.md` + `docs/*.md` top-level (or an explicit curated list) and
    **exclude `docs/internal/**` and `docs/evidence/**`** and the PMO corpus.
  - A non-vacuous sanity test (the guard sees real files, e.g. it scans
    `CONNECTOR_DEVELOPMENT.md`) so a green result is not empty-set-vacuous.
  - Patterns narrow enough that they never match the kept spec names `MIR-01` /
    `DIR-01` or product nouns.
- **Out:** the scrub itself (HS-51-02, must already be green); scanning or editing
  the internal corpus; new product behavior.

## Acceptance criteria
- [x] A guard test fails on a user-facing doc containing `Phase <N>` / `HS-NN-NN` /
      `PMO` / the chosen process words, and passes on the post-scrub tree.
      (`test_no_user_facing_doc_leaks_roadmap_vocabulary`; proven red on a planted
      lowercase "phase 99" in `USER_GUIDE.md`, green after revert)
- [x] The scan scope excludes `docs/internal/**`, `docs/evidence/**`,
      `docs/assets/**`, and `pm/roadmap/**`; a sanity test proves the guard scans
      real user-facing files. (`_user_facing_docs()` = README + non-recursive
      `docs/*.md`; `test_roadmap_vocab_guard_scans_real_user_facing_docs`)
- [x] The patterns do not match `MIR-01` / `DIR-01` or product nouns (verified by a
      kept-term not tripping the guard).
      (`test_roadmap_vocab_pattern_is_narrow_enough_to_keep_spec_names`)
- [x] Case-insensitive (the lowercase leaks HS-51-02 caught proved this is required).
- [x] `uv run pytest -q tests/unit/test_doc_drift_guard.py` -> 8 passed.
- [x] `npm run build` n/a (no UI bundle touched); 0 `_built/` tracked.

## Test plan
- `uv run pytest -q -k "doc_drift or doc_guard"`.
- Manual: temporarily plant `Phase 99` in a user-facing doc, confirm red; remove,
  confirm green (this is also the HS-51-05 dogfood).

## Notes / open questions
- Keep the guard cheap: regex over a file list, like the sibling guards in the same
  file.
- If a user-facing doc has a genuine, unavoidable reason to name a phase, prefer
  rewording over an allowlist exception; if an exception is truly needed, make it an
  explicit, commented constant so it is visible.
