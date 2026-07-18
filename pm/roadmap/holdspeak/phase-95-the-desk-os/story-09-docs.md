# HS-95-09 — Docs: the Desk OS is the documented product

- **Project:** holdspeak
- **Phase:** 95
- **Status:** backlog
- **Depends on:** HS-95-08
- **Unblocks:** HS-95-10

## Problem

After HS-95-08 the product's shape changes fundamentally: there are no
pages, there is an OS. Every doc that teaches "go to the Dictation page" or
screenshots the flat shell is now wrong, and the architecture docs still
describe a two-shell frontend. Worse, the model that makes the system
legible — services surfaced through OS primitives, never through their own
screens — exists only in this phase's files. Docs stories must touch entry
points (standing rule), and this one lands the model where users and
contributors actually enter.

## Scope

- In:
  - `README.md` (public surface): the desk-first story updated — what you
    see on arrival, how windows/dock work, how deep links behave;
  - `docs/ARCHITECTURE.md` + diagrams: the frontend section redrawn — one
    shell, the WebGL stage, the window system, the route-demotion table;
    the render guard stays green;
  - `docs/internal/POSITIONING.md` amended under the Constitution: the
    Phase 70 page-based information architecture section (four
    destinations, Desk in the Studio tier) is rewritten to Article I —
    the Desk is the operating surface; services (dictation, meetings,
    steering, delivery, configuration) are system primitives; windows,
    desk objects, and the dock are the OS primitives they surface
    through; feature UIs never own navigation;
  - every touched doc checked against
    `docs/internal/CONSTITUTION.md`; any remaining drift is named in the
    story's evidence rather than papered over (Article X);
  - USER_GUIDE: every "page" walkthrough rewritten as a window/desk
    walkthrough with fresh screenshots from the shipped build;
  - `web/README.md`: the contributor path — how to add a surface (core +
    window registration + route-table row), the no-exit guard, the style
    seam;
  - the voice guard passes on everything touched (no AI vocabulary, dash
    rules, no privacy prose — the badge carries trust).
- Out:
  - HSM/native docs (the Swift belt documents its own catch-up);
  - marketing/site work beyond the README surface;
  - roadmap archaeology (final-summary belongs to HS-95-10).

## Acceptance criteria

- [ ] No shipped doc instructs navigating to a flat product page; every
      walkthrough moves through desk windows (sweep-verified over docs/
      and README.md for the demoted route paths).
- [ ] ARCHITECTURE frontend section and its Mermaid diagrams match the
      shipped code (one shell, stage, windows, demotion table); the render
      guard passes.
- [ ] POSITIONING carries the Desk OS canon paragraph: system primitives
      surfaced through OS primitives, with the named services listed.
- [ ] USER_GUIDE screenshots are from the shipped build at real viewports
      (1440 desktop, 393 phone) — no stale flat-shell captures anywhere in
      docs assets.
- [ ] `web/README.md` documents the add-a-surface path including the
      HS-95-04 core pattern and the HS-95-08 guard.
- [ ] Voice guard and doc lints pass on the full touched set.

## Test plan

- `uv run pytest -q tests/ -k doctor` plus the docs/voice/render guards.
- The demoted-route sweep over docs (grep list from HS-95-08's table).
- Manual read-through of the USER_GUIDE desk walkthrough against the live
  product (the doc IS the walkthrough script).

## Implementation direction

- Screenshots come from the HS-95-10 walk tooling where possible — one
  capture pipeline, two consumers.
- Write the POSITIONING canon tight: one section, the frame, the named
  primitives, the rule. It governs future phases; it is not an essay.
- Entry points first: README and USER_GUIDE arrival flow before internals.

## Evidence required

- captured guard/lint runs;
- the docs sweep output (zero demoted-route instructions);
- the diff summary showing entry-point files touched;
- one before/after doc screenshot pair.
