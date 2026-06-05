# Evidence — HS-39-04 — Project-doc suggestion quality gate

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-39/hs-39-01-multi-pass-rewriting`
- **Owner:** unassigned

## Files touched

- `holdspeak/project_doc_suggestions.py` — `suggestion_signature`,
  `suggestion_already_covered` (dedup, 0.85 Jaccard), `consolidate_suggestions`.
- `holdspeak/plugins/dictation/builtin/project_rewriter.py` — `_existing_doc_text`
  + dedup in `_suggestion_for` (status `already_covered`).
- `holdspeak/web/routes/dictation/__init__.py` — a session
  `dismissed_suggestion_signatures` set, threaded into the project-docs +
  pipeline routers.
- `holdspeak/web/routes/dictation/project_docs.py` — the dismiss route records
  the dismissed suggestion's signature.
- `holdspeak/web/routes/dictation/pipeline.py` — passes the dismissed set into
  the dry-run.
- `holdspeak/web/routes/dictation/_helpers.py` — `_store_project_doc_suggestion`
  suppresses a dismissed signature and returns a status; the dry-run surfaces
  `suggestion_status`.
- Tests: `tests/unit/test_dictation_suggestion_gate.py` (**new**, 8) + 2 dedup
  cases in `tests/unit/test_dictation_project_rewriter.py`.

## Verification artifacts

- Targeted: `uv run pytest -q tests/unit/test_dictation_suggestion_gate.py tests/unit/test_dictation_project_rewriter.py tests/unit/test_dictation_routes_split.py`
  → `27 passed`.
- Ruff (touched files) → `All checks passed!`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → `2177 passed, 16 skipped` (was 2167/16 at HS-39-09; +10).

## Acceptance criteria — re-checked

- [x] Already-covered suggestion suppressed (`already_covered`) —
      `test_project_rewriter_dedup_suppresses_already_covered`,
      `test_already_covered_true_when_doc_has_the_tokens`.
- [x] Dismissed suggestion doesn't recur (session signature set) —
      `test_store_keeps_then_suppresses_dismissed`.
- [x] Consolidation folds N → one (pure helper) —
      `test_consolidate_merges_several`.
- [x] Suppression reason visible — `already_covered` on the stage status;
      `dismissed`/`stored`/`no_suggestion` as the dry-run `suggestion_status`.
- [x] Validation unchanged; novel suggestion still surfaces —
      `test_project_rewriter_surfaces_novel_suggestion`,
      `test_already_covered_false_for_novel_content`.
- [x] No DB schema change; no auto-write.

## Deviations from plan

- **Consolidation is a tested pure helper, not yet wired into a cross-utterance
  UI** (the live store holds one suggestion per project; accumulate-then-fold
  needs a list-shaped store + a control). Recorded in the story Notes; the
  helper is ready for the follow-up.
- Reasons surfaced are `already_covered` + `dismissed` (the two implemented
  suppressions); there is no separate "below-quality" reason.

## Follow-ups

- Wire `consolidate_suggestions` into the web surface (accumulate recent
  suggestions per project, offer a "fold into one" action).
- HS-39-05 telemetry can report suppression counts (already-covered / dismissed).
