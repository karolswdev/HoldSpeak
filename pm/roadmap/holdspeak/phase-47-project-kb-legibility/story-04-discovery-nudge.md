# HS-47-04 — Discovery nudge (find it where it helps)

- **Project:** holdspeak
- **Phase:** 47
- **Status:** done
- **Depends on:** HS-47-01
- **Unblocks:** HS-47-06
- **Owner:** unassigned

## Problem
Project knowledge is invisible unless you already click an opaque tab. A user
dictating into a detected project that has **no** project knowledge gets no hint
that the capability exists or that it would sharpen their output — so the feature
is never discovered.

## Scope
- **In:**
  - An **ambient, dismissible discovery hint** surfaced where a user would benefit:
    when a project root is detected but has no `.hs/` and no `project.yaml` KB,
    offer a calm, one-line "teach the copilot about this project?" affordance that
    opens the guided flow (HS-47-03). Candidate homes: the `/dictation` readiness
    panel, the dashboard, or a dictation-result hint — pick the least intrusive.
  - **Dismissal that sticks** (per-project, durable) so it never re-nags; respects a
    global off switch.
- **Out:** the setup flow itself (HS-47-03); the surface explainers (HS-47-02). This
  story is *discovery + entry*, not the destination.

## Acceptance criteria
- [x] When a detected project lacks knowledge (no facts and no `.hs/`), an ambient
      `#kn-nudge` bar surfaces on `/dictation` (above the tabs, seen from any tab)
      and "Set it up" routes into the guided flow (HS-47-03); when knowledge
      exists, the readiness `project_context.exists` / `project_kb.exists` signals
      suppress it.
- [x] Focus-safe (the dictation bundle still calls zero `.focus()`); dismissible
      ("Not now"); dismissal is durable per-project (localStorage map keyed by
      root); a global off switch ("Stop suggesting") persists too.
- [x] Never naggy: `role="note"`, not a modal; suppressed once dismissed for that
      project or globally; re-evaluated cleanly on project-root change.
- [x] Behavior-preserving (the readiness `project_context` field is additive);
      tests + `npm run build` green; 0 `_built/` tracked.

## Test plan
- Unit: the hint's show/suppress logic (detected-project ∧ no-knowledge ∧
  not-dismissed); dismissal persistence; `uv run pytest -q -k "dictation or readiness"`.
- Manual: a project with knowledge → no hint; without → one calm hint that opens the
  flow and stays gone after dismissal.

## Notes / open questions
- Mirror the Phase-42 TrustChip / first-run-nudge posture (ambient, never naggy).
- Reuse readiness/project-detection signals already on `/dictation`; don't add a new
  detection path.
