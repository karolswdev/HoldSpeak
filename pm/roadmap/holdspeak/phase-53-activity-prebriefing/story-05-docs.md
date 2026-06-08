# HS-53-05 — Docs: the pre-briefing guide

- **Project:** holdspeak
- **Phase:** 53
- **Status:** not started
- **Depends on:** HS-53-04
- **Unblocks:** HS-53-06
- **Owner:** unassigned

## Problem
Pre-briefing nudges read your local activity and surface it. That is exactly the kind of
feature a user wants to understand and trust before they rely on it, so it needs an
honest guide, in product-tense, that obeys the Phase-51 roadmap-vocabulary guard.

## Scope
- **In:**
  - A short user guide (e.g. `docs/ACTIVITY_PREBRIEFING.md`, or a section in an existing
    activity/dictation guide): what pre-briefing nudges are, that they are computed
    locally from activity HoldSpeak already records, that every nudge is source-cited and
    dismissible and never acts on its own, how the "dictate with this as context" action
    works, and that the existing activity privacy toggle gates them (off means no nudges).
  - Link it into the docs index (`docs/README.md`) under the right journey; keep the index
    a map.
  - Product-tense, no roadmap vocabulary (the Phase-51 guard will fail otherwise). Run the
    `humanizer` skill over the new doc.
- **Out:** new feature work.

## Acceptance criteria
- [ ] The guide exists: what the nudges are, the local + source-cited + dismissible +
      never-acts model stated honestly, the dictate-with-context action, the activity
      toggle gate; every claim grounded in the shipped engine + UI.
- [ ] Linked in `docs/README.md`; the index stays a map.
- [ ] Passes the Phase-51 roadmap-vocabulary guard and the link/image guards
      (`uv run pytest -q -k "doc_drift or doc_guard or doc"`); `humanizer` run, no em/en
      dashes.
- [ ] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- `uv run pytest -q -k "doc_drift or doc_guard or doc"`; manual read as a user deciding
  whether this is for them.

## Notes / open questions
- This is the dedicated docs story. Be honest about the citation coarseness and the
  browser-only scope; do not imply it watches more than it does.
