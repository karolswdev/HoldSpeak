# Phase 36 — Meeting Artifact Experience

**Status:** in-progress (opened 2026-06-04; runs after Phase 35).

The plugin system can now *produce* fourteen kinds of meeting artifacts (Phases
16→29) and others can *extend* it (Phase 35). But the **presentation** of those
artifacts in the web history view never got the Phase-30 "Signal" treatment the rest
of the app did — they render as basic chips + flat lists/tables inside a generic
`.segment` card. Direct user feedback (2026-06-04): *"the pills are so basic … the
content often overflows horizontally (e.g., the risk analysis table) … looks very
basic and completely not what I like."*

This phase makes the meeting-intelligence output feel like a first-class, polished
**deliverable** — distinctive Signal-aligned **artifact cards**, a per-artifact
**copy-as-Markdown** affordance, and **overflow-safe** rendering for every wide
artifact (the risk table first). The data and the plugin contract are unchanged; this
is a frontend/UX phase.

## Chosen direction (user, 2026-06-04)

**"Elevated cards."** Each artifact is a distinct elevated card: a type-colored
accent edge, a header row (type icon + title + type chip + copy button + collapse
toggle), and an overflow-safe body. Tables and other wide content scroll within the
card instead of blowing out the modal width.

## Where to look first

- `current-phase-status.md` — goal, scope, exit criteria, story table, risks.
- `web/src/pages/history.astro` — the artifact renderers (~lines 856–1136) + their CSS
  (the `.segment`, `.risk-table`, `.incident-timeline`, `.runbook-list`,
  `.stakeholder-update`, `.announcement-artifact`, … blocks).
- `web/src/scripts/history-app.js` — the Alpine data layer (`openMeeting`, the
  `risksFor`/`hasStructuredRender` helpers).
- `web/src/styles/tokens.css` — the Signal token set (surfaces, accent `#FF6B35`,
  status colors, spacing/type/radius/elevation/motion scales).
- `web/src/components/CommandPreview.astro` — the canonical
  `navigator.clipboard` + `[data-*-copy]` delegator pattern to reuse for copy.
- `../phase-30-ui-ux-overhaul/` — the "Signal" design language this phase applies to
  artifacts.

## Phase boundaries

**Frontend/UX only — no change to the plugin contract, the artifact data shapes
(`structured_json`), or the API.** The artifact CSS **selectors asserted by the
spoken-e2e** (`tests/e2e/test_spoken_meeting_e2e.py`: `.risk-table tbody tr`,
`.incident-timeline li`, `.runbook-list .runbook-change`, `.stakeholder-update`,
`.announcement-artifact .announcement`, …) must keep working — either preserved or
updated in lockstep with the e2e (never silently broken). The web bundle
(`holdspeak/static/_built/`) is rebuilt (`cd web && npm run build`) in the same commit
as any source edit. The `ui-ux-pro-max` design skill (vendored at
`.claude/skills/ui-ux-pro-max`) is the design aid, as in Phase 30.
