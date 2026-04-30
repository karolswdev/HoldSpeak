# HS-12-04 evidence — Designer handoff refresh + phase 12 exit

## Files refreshed

- `designer-handoff/style-handoff.md` — full rewrite. Documents
  the Workbench-evoking voice as it actually shipped:
  - The four anchors (blue / white / black / orange) plus the
    supporting palette (blue / orange families, grey ramp,
    distinct status hues).
  - Three-font stack (Sora body, VT323 display, JetBrains Mono
    code) with the explicit *Workbench moments* policy
    restricting VT323 to the TopNav, page h1, and panel
    titles.
  - Geometry: radius 0 across the board, hard 1 px borders,
    panel-as-window grammar, notebook tabs, disabled hatch,
    Workbench inverse-bar selection.
  - Resolved style questions: dark theme replaced by the
    Workbench light-on-blue-desktop, unified nav, local-only
    grammar, command preview look, candidate-state pill tones.
  - Deferred: a second theme, per-route hero illustrations,
    page-level transitions.
  - Explicit "what was *intentionally* not taken from
    Workbench" section: stripe title bars, full inset/outset
    bevels, pixel cursor, clamped 4-colour rendering. Brief
    was *evoke not emulate*.
- `designer-handoff/ux-inventory.md` — "What's left after phase
  12" and "What was closed in phase 12" replace the phase-10
  references.
- `designer-handoff/screenshots/{dashboard,activity,activity-mobile,history,dictation}-desktop.png`
  — recaptured against the running app at the cumulative
  HS-12-02 voice (committed in `2ba97f0`).

## Phase DoD checklist

- [x] **All HS-12-01..03 stories `done` with evidence files.**
  - HS-12-01 / `evidence-story-01.md` — token map + VT323.
  - HS-12-02 / `evidence-story-02.md` — six review-driven
    slices.
  - HS-12-03 / `evidence-story-03.md` — dashboard polish
    closed.
- [x] **`current-phase-status.md` story table fully updated.**
  All four rows now `done` with evidence-file links.
- [x] **`pm/roadmap/holdspeak/README.md` "Last updated" bumped,
  phase 12 flipped to `done`.** Done in this commit.
- [x] **`npm run build` clean.** Verified.
- [x] **`uv run pytest -q --ignore=tests/e2e/test_metal.py` green.**
  1269 passed, 13 skipped.

## Phase shape — what shipped

Phase 12 took the phase-10 design system from "competent SaaS"
to *Workbench-evoking*. The component layer is largely
unchanged — phase 12 was a values + voice replatform:

- **HS-12-01** rebuilt `tokens.css` on the canonical four-
  colour Workbench palette and added the supporting palette;
  introduced `--font-display: VT323` with `--font-ui: Sora`;
  collapsed every radius and elevation to 0/none.
- **HS-12-02** propagated the voice across every component +
  every page surface in six review-driven slices. Each user
  callout ("font is too greedy", "4 colours is regarded",
  "gray-on-gray is illegible") drove the next slice.
- **HS-12-03** closed four phase-10 polish items folded into
  the slices (oversized hero wordmark, redundant idle copy,
  duplicate toasts, "No tags yet" placeholder).
- **HS-12-04** (this story) refreshed the designer-handoff
  package — the artifact a designer judges first — so future
  contributors get a Workbench-voiced reference, not a stale
  phase-10 snapshot.

## Phase exit

Phase 12 is **done**. The design system has a real,
distinctive voice anchored in the Amiga Workbench reference
the project's name implies. The next phase to resume is
**phase 11** (Local Connector Ecosystem), paused at HS-11-01
while phase 12 ran.
