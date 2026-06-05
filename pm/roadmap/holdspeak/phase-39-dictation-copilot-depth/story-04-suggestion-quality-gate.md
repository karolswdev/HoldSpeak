# HS-39-04 — Project-doc suggestion quality gate

- **Project:** holdspeak
- **Phase:** 39
- **Status:** done
- **Depends on:** none
- **Unblocks:** none
- **Owner:** unassigned

## Problem

`suggest_project_doc_update()` (`holdspeak/project_doc_suggestions.py`) proposes
a narrow `.hs/.../*.md` update per qualifying rewrite, validated for path +
length + secrets. But it has **no awareness of what's already written**: it can
re-propose content the doc already contains, and a dismissed suggestion can
recur on the next similar utterance. Phase 19 explicitly left "suggestion
quality thresholds under long, noisy coding sessions" experimental. This story
adds the quality gate.

## Scope

- In:
  - **Dedup against the existing doc:** before surfacing a suggestion, compare
    it to the current contents of the target `.hs/*.md`; suppress (no-op +
    trace note) when it is ~already covered.
  - **Recurrence suppression:** track dismissed suggestions in the session so a
    near-duplicate does not re-surface after the user dismissed it (reuses /
    extends the in-memory `project_doc_suggestions` store on `WebRuntime`).
  - **Optional consolidation:** a mode to fold suggestions from the last N
    utterances into a single proposed update instead of N separate nudges.
  - Surfacing: the dry-run / suggestion API reports *why* a suggestion was
    suppressed (already-covered | dismissed | below-quality).
- Out:
  - Auto-applying suggestions — explicit apply/dismiss stays (Phase 19 safety
    posture unchanged).
  - Semantic embedding similarity — use a conservative lexical/structural
    overlap check this phase (an embedding index is out).
  - Cross-session memory of dismissals (session-scoped, mirrors HS-39-02).

## Acceptance criteria

- [x] A suggestion whose content is ~already present in the target `.hs/*.md`
      is suppressed with status `already_covered` (not silently dropped) —
      `project_rewriter._existing_doc_text` + `suggestion_already_covered`;
      `test_project_rewriter_dedup_suppresses_already_covered`.
- [x] A dismissed suggestion does not recur for a near-duplicate utterance in
      the same session — a session `dismissed_suggestion_signatures` set
      (router-scoped); the dismiss route records the signature and
      `_store_project_doc_suggestion` suppresses it (status `dismissed`);
      `test_store_keeps_then_suppresses_dismissed`.
- [x] Consolidation folds N suggestions into one with combined rationale +
      de-duplicated content — `consolidate_suggestions`;
      `test_consolidate_merges_several`. (Pure helper, tested; cross-utterance
      UI accumulation is a follow-up — see Notes.)
- [x] The suppression reason is visible: `already_covered` on the rewriter
      stage's `project_doc_suggestion_status`; `dismissed` / `stored` /
      `no_suggestion` as the dry-run's top-level `suggestion_status`.
- [x] Existing path/length/secret validation unchanged; a genuinely new
      suggestion still surfaces — `test_project_rewriter_surfaces_novel_suggestion`,
      `test_already_covered_false_for_novel_content`.
- [x] No DB schema change; no auto-write of any `.hs` file (apply stays
      explicit).

## Test plan

- Unit: `tests/unit/test_project_doc_suggestions.py` — dedup suppresses a
  near-duplicate, novel content passes, dismissal suppresses recurrence,
  consolidation folds N → 1, suppression-reason surfaced.
- Integration: `tests/integration/test_web_dictation_*api.py` (project-doc
  suggestion routes) — dismiss then re-dry-run does not re-surface.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Manual / device: n/a (dry-run integration covers it).

## Notes / open questions

- Similarity check: keep it explainable (normalized line/section overlap,
  shared headings) so a suppression can be justified in the trace. Tune
  conservatively — prefer a false *surface* over a false *suppress* (a
  dropped useful suggestion is the worse failure; see the risk table).
- Consolidation interacts with HS-39-02's correction store conceptually but is
  independent code; keep them decoupled.
- **Consolidation wiring deferred (recorded at ship):** `consolidate_suggestions`
  is a pure, tested helper. The live suggestion store holds one suggestion per
  project, so cross-utterance "accumulate N then fold" needs a list-shaped store
  + a UI control — left as a follow-up (the helper is ready). The dedup +
  recurrence suppressions are the high-value, fully-wired pieces.
- The `already_covered` similarity threshold is conservative (0.85 Jaccard) to
  prefer a false *surface* over a false *suppress* — dropping a genuinely new
  note is the worse failure.
- Canon: the suggestion target allow-list (`.hs/{memory,decisions,handoffs,
  workflows,issues}/slug.md`) and the no-silent-write rule are unchanged —
  this story only *filters* what gets proposed.
