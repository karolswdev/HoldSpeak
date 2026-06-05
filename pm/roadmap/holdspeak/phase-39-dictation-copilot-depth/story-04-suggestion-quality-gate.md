# HS-39-04 — Project-doc suggestion quality gate

- **Project:** holdspeak
- **Phase:** 39
- **Status:** backlog
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

- [ ] A suggestion whose content is ~already present in the target `.hs/*.md`
      is suppressed and the reason is recorded (not silently dropped).
- [ ] A dismissed suggestion does not recur for a near-duplicate utterance in
      the same session.
- [ ] Consolidation mode folds N qualifying utterances into one suggested
      update with combined rationale.
- [ ] The suppression reason (already-covered | dismissed | below-quality) is
      visible in the dry-run / suggestion response.
- [ ] Existing path/length/secret validation is unchanged; a genuinely new
      suggestion still surfaces (no false suppression on novel content).
- [ ] No DB schema change; no auto-write of any `.hs` file.

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
- Canon: the suggestion target allow-list (`.hs/{memory,decisions,handoffs,
  workflows,issues}/slug.md`) and the no-silent-write rule are unchanged —
  this story only *filters* what gets proposed.
