# Evidence — HS-47-04: Discovery nudge (find it where it helps)

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-47-project-kb-legibility`.

## What shipped

An ambient, dismissible, focus-safe hint that surfaces project knowledge to a user
who would otherwise never click into the tabs, and routes them into the guided
flow. No new detection path, no nagging.

### The nudge (`#kn-nudge`)

A calm accent bar on `/dictation`, placed above the tab nav so it is seen from any
tab (static markup toggled by JS so its scoped CSS applies). Copy: "Teach the
copilot about this project. <name> has none yet. HoldSpeak can use this repo's
facts and context to sharpen your dictation." Actions:

- **Set it up** routes into the guided flow: it marks the project dismissed (acting
  on it counts), activates the Context tab, and opens the HS-47-03 guided panel
  once detection completes (a `pendingOpen` flag handled at the end of
  `loadHSContext`, since the section load is async).
- **Not now** dismisses for this project.
- **Stop suggesting** is the global off switch.

It is `role="note"`, never a modal, and the dictation bundle still calls zero
`.focus()` (the focus-safe guard passes).

### Show / suppress logic

`maybeShowKnNudge()` runs on load and on every project-root change
(`refreshProjectScopedView`). It fetches the existing readiness endpoint and shows
the nudge only when: the global switch is on, a project is detected, it has no
facts (`project_kb.exists` false) and no context (`project_context.exists` false),
and it is not dismissed for that root. It re-evaluates cleanly (hides first, then
decides), so switching to a configured project hides a stale nudge.

### Durable dismissal

- Per-project: a localStorage map `holdspeak.knNudgeDismissed` keyed by project
  root. Survives reloads; only that project is suppressed.
- Global: `holdspeak.knNudgeDisabled = "1"`. Local-first, matching the ambient
  posture; no server round-trip.

### Backend: one additive signal

The readiness payload gained `project_context: {path, exists}` (the `.hs/`
existence) so the nudge can tell "no knowledge yet" without a new detection path.
Additive; nothing else changed.

## Tests run

- New: `test_dictation_has_focus_safe_discovery_nudge` (cockpit page-content +
  bundle: markup, role, the three controls, the show/suppress + dismissal logic,
  and the zero-`.focus()` guard); `test_readiness_exposes_project_context_existence_for_the_nudge`
  (the additive signal flips false → true when `.hs/` appears).
- Targeted: `uv run pytest -q -k "dictation or readiness or doc_drift or link"`
  → **373 passed, 5 skipped**.
- Full-suite gate: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → **2372 passed, 17 skipped** (exit 0).
- Build: `(cd web && npm run build)` clean; **0** `_built/` tracked.
- Screenshot-verified: the nudge renders as a calm accent bar above the tabs; a
  Playwright check confirmed "Set it up" activates the Context tab and opens the
  guided panel (the async `pendingOpen` path works).

## Acceptance criteria

- [x] Surfaces when a detected project lacks knowledge and routes into the guided
      flow; suppressed when knowledge exists.
- [x] Focus-safe; dismissible; durable per-project dismissal; global off switch.
- [x] Never naggy; `role="note"`, not a modal.
- [x] Behavior-preserving; tests + build green; 0 `_built/`.
