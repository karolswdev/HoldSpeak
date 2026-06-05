# HS-39-06 — Documentation

- **Project:** holdspeak
- **Phase:** 39
- **Status:** backlog
- **Depends on:** HS-39-01, HS-39-02, HS-39-03, HS-39-04, HS-39-05
- **Unblocks:** HS-39-07
- **Owner:** unassigned

## Problem

Phase 39 adds five user-facing capabilities to the dictation copilot
(multi-pass rewriting, correction memory, model-assisted target detection,
the suggestion quality gate, depth telemetry), each with new config knobs and
behaviors. Per the project's dedicated-docs-story cadence, these must be
documented in the same phase — before closeout — so no live doc lags the
shipped surface.

## Scope

- In:
  - Update `docs/INTELLIGENT_TYPING_GUIDE.md` with a section per new knob:
    `rewrite_passes` + the refine loop, `corrections_enabled` + how the
    session learns, `target_detect_llm_enabled` / `target_detect_llm_below`,
    the suggestion quality gate (dedup / recurrence / consolidation), and how
    to read the depth telemetry on the readiness surface.
  - Touch `docs/MODELS.md` / `docs/MEETING_MODE_GUIDE.md` only where a new knob
    intersects (e.g. multi-pass latency vs model choice) — minimal, accurate.
  - Reconcile any live doc that implies the copilot is single-pass / stateless
    / heuristic-only.
  - Keep the doc drift-guard + live-doc link-check green.
- Out:
  - New marketing copy / README hero changes (README phase-row update is the
    closeout's job, HS-39-07).
  - Internal `docs/internal/PLAN_*` spec rewrites — DIR-01 stays the canonical
    spec; note the Phase-39 deltas rather than rewriting it.

## Acceptance criteria

- [ ] `docs/INTELLIGENT_TYPING_GUIDE.md` documents every new config knob with
      its default and an example, and explains the opt-in/off-by-default
      posture.
- [ ] No live doc still describes the rewriter as single-pass, the pipeline as
      memoryless, or target detection as heuristic-only where Phase 39 changed
      it.
- [ ] Doc drift-guard test passes (`uv run pytest -q -k doc_drift` or the
      project's guard test).
- [ ] Live-doc link-check passes (the dangling-relative-link test).
- [ ] Every documented knob name matches the actual config field shipped in
      01–05 (no doc/code drift).

## Test plan

- Tests: `uv run pytest -q -k "doc_drift or doc_link or link"` — drift-guard +
  link-check green.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py` (docs-only change;
  suite should be unchanged from HS-39-05's close).
- Manual: re-read the guide against the shipped config dataclasses to confirm
  knob names/defaults match.

## Notes / open questions

- This story lands after the feature surface (01–05) is stable so the docs
  describe what actually shipped, not the plan. If a feature was trimmed
  during implementation, the docs reflect the trim and the phase
  `current-phase-status.md` "Decisions made" records it.
- Honor the project memory `feedback_dedicated_docs_story`: documentation is
  its own story (here), not a closeout footnote.
