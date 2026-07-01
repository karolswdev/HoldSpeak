# Evidence — HS-70-08: Naming + positioning coherence (the docs story)

**Date:** 2026-06-30
**Verdict:** done. The new front door is locked into canon and the entry-point
docs reflect it: POSITIONING records the web IA and adds "Studio" (plus "Home"
and "Meetings") as canonical names; the docs index and Getting Started describe
landing on Home with the two modes and the Studio tier.

## What shipped (docs-only, zero behavior change)

- **`docs/internal/POSITIONING.md`**:
  - A new **"The web surface (information architecture)"** section: the four
    primary destinations (Home · Dictation · Meetings · Studio · Settings) as the
    surface expression of "one copilot, two modes"; Studio is the advanced tier
    **below** the two modes, not a third pillar; first-run arrival is the single
    `/welcome` surface; the standing rule that a new capability joins a mode or
    Studio, not a new top-level door.
  - Three canonical-name rows: **Home** (not "the dashboard" / "the runtime
    page"), **Meetings** (the mode + nav label; not "History"), **Studio** (the
    advanced tier; not "the advanced panel" / "power tools").
- **`docs/GETTING_STARTED.md`**: the surface map updated to the new IA (the old
  "`/` Runtime dashboard" / "`/history` Meeting history" rows replaced with Home
  / Dictation mode / Meetings mode / Studio / Settings, plus `/welcome` as the
  single arrival and `/setup` as "Setup and health"); the returning-user line now
  says they land on **Home**.
- **`docs/README.md`** (docs index): a front-door paragraph — the app opens on
  Home with the two modes as the front door and a Studio tier for advanced
  tools, "four destinations, not a flat list of pages".

## Naming is already canonical on-screen

The nav labels (Home / Dictation / Meetings / Studio), the Meetings page title
(HS-70-05), and the Activity ledger retitle (HS-70-04) already use the canonical
names from the feature stories, so this story records them rather than renames
anything further. A sweep of `docs/*.md` + README found **no** stale surface
language ("Runtime dashboard", "History tab", "Activity tab").

## Proof

- **Voice guard green:** `tests/unit/test_doc_drift_guard.py` **15 passed**
  (includes `test_no_user_facing_doc_uses_dashes_in_prose` + the roadmap-vocab +
  canonical-name checks over README + `docs/*.md`). My new prose is dash-free
  (verified by grep); POSITIONING lives in `docs/internal/` (internal corpus).
- Full suite **3045 passed, 37 skipped** (docs-only; no code path touched).
