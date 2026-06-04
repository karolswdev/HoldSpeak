# Phase 36 — Meeting Artifact Experience

**Status:** in-progress (opened 2026-06-04). 0/4 stories shipped.

**Last updated:** 2026-06-04 (phase opened off Phase 35's close, on direct user
feedback that the artifact rendering looks basic, has no copy affordance, and overflows
horizontally. Direction chosen: "Elevated cards". HS-36-01 first).

## Goal

Make the meeting-intelligence output a polished, first-class **deliverable** in the web
history view. Today the fourteen artifact types render as basic chips + flat
lists/tables inside a generic card, missed by the Phase-30 "Signal" pass; wide content
(the risk table) overflows horizontally; and there is no way to lift an artifact's
content out as Markdown. This phase fixes all three — distinctive Signal **artifact
cards**, **copy-as-Markdown** per artifact, and **overflow-safe** rendering — without
touching the plugin contract or artifact data.

## Scope

### In

- **Elevated artifact-card shell + overflow-safe layout (HS-36-01).** Replace the
  generic `.segment` artifact container with a Signal "artifact card": a type-colored
  accent edge, a header row (type icon + title + type chip + collapse toggle), and a
  body region that contains overflow. Fix the **risk-table horizontal overflow** (and
  any other wide artifact) via an overflow-safe scroll container + sensible cell
  wrapping. Card chrome is shared across all artifact types.
- **Copy-as-Markdown per artifact (HS-36-02).** A per-artifact "Copy" button that
  serializes that artifact's `structured_json` to clean Markdown (headings, tables,
  lists per type) and writes it to the clipboard, reusing the `CommandPreview`
  clipboard pattern (copied-state feedback, graceful fallback). Plus a "copy all
  artifacts" affordance for the meeting.
- **Per-artifact-type body polish (HS-36-03).** Apply the Signal treatment to each
  renderer's *body* (timeline, runbook delta, risk register, stakeholder update,
  decision announcement, decisions/open-questions, requirements, ADR, milestone plan,
  dependency map, scope review, customer signals, action items, mermaid) — typed
  status colors, iconography, spacing, density — so each reads as a designed block,
  not a flat dump.
- **Closeout (HS-36-04).** Rebuild the bundle; verify/update the spoken-e2e selectors
  in lockstep; capture before/after screenshots (incl. the incident-retro meeting);
  `final-summary.md`.

### Out

- **Any change to the plugin contract, artifact `structured_json` shapes, synthesis,
  or the API.** This is presentation only.
- **New artifact types or new renderers** for types that don't exist yet.
- **Export-to-file / download** beyond clipboard Markdown (a later idea; clipboard is
  the asked-for facility).
- **A non-dark / light theme** for artifacts — Signal is dark-first.

## Exit criteria (evidence required)

- [ ] Artifacts render as elevated Signal cards (accent edge + header + contained
      body); the generic `.segment` chrome is gone for artifacts. (HS-36-01)
- [ ] The risk table (and every wide artifact) no longer overflows the modal — content
      scrolls within its card; verified at a narrow viewport. (HS-36-01)
- [ ] Each artifact has a working "Copy as Markdown" button (clipboard write +
      copied-state); the produced Markdown is well-formed per type. (HS-36-02)
- [ ] Every artifact type's body got the Signal polish pass. (HS-36-03)
- [ ] `cd web && npm run build` succeeds and the rebuilt bundle is committed with each
      source change; `tests/e2e/test_spoken_meeting_e2e.py` selectors pass (preserved
      or updated in lockstep). (all)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout; the
      incident-retro spoken-e2e re-run for real shows the new look (screenshot). (HS-36-04)

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-36-01 | Elevated artifact-card shell + overflow-safe layout | not-started | [story-01-artifact-card-shell.md](./story-01-artifact-card-shell.md) | — |
| HS-36-02 | Copy-as-Markdown per artifact | not-started | [story-02-copy-as-markdown.md](./story-02-copy-as-markdown.md) | — |
| HS-36-03 | Per-artifact-type body polish | not-started | [story-03-per-type-body-polish.md](./story-03-per-type-body-polish.md) | — |
| HS-36-04 | Phase closeout + final-summary | not-started | [story-04-closeout.md](./story-04-closeout.md) | — |

## Where we are

Opened 2026-06-04 immediately after Phase 35 closed (merged via PR #11; the config
hardening follow-up is PR #12). Phase 35 made the plugin system extensible; this phase
makes its *output* look the part. The recon is done: artifacts render in
`web/src/pages/history.astro` (~856–1136) via Astro + Alpine, the Signal tokens live in
`web/src/styles/tokens.css`, a reusable clipboard pattern exists in
`CommandPreview.astro`, the risk-table overflow is a missing `overflow-x` container +
unbounded cells, and the spoken-e2e pins several artifact selectors. Direction chosen
by the user: **Elevated cards**. Numbering: this took the Phase 36 slot; **Actuators
moved to Phase 37**. HS-36-01 (card shell + overflow fix) first — the most visible win.

## Pickup order

1. HS-36-01 — elevated card shell + overflow-safe layout. **◀ first** (the structural
   foundation + the most-complained-about overflow; highest visible impact).
2. HS-36-02 — copy-as-Markdown (builds on the card header for the button slot).
3. HS-36-03 — per-type body polish (fills in each artifact body within the new shell).
4. HS-36-04 — closeout + final-summary.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Renaming artifact CSS classes breaks the spoken-e2e selectors | High (if careless) | Preserve the asserted class names (`.risk-table tbody tr`, `.incident-timeline li`, …) or update the e2e in the same commit; keep them as inner elements within the new card | An e2e `wait_for_selector` times out |
| Forgetting to rebuild the bundle → source edits don't show | Medium | `cd web && npm run build` + commit `holdspeak/static/_built/` in the same commit as any source edit (phase rule) | The served app looks unchanged after an edit |
| Collapsible cards hide content from the e2e / from copy | Medium | Default artifact cards to expanded; copy reads from data, not the DOM | e2e can't see a collapsed body |
| Scope creep into export-to-file / new artifact types | Medium | Clipboard Markdown only; presentation only — no data/plugin changes | A PR touching `plugins/` or `synthesis.py` shapes |

## Decisions made (this phase)

- 2026-06-04 — **Direction = "Elevated cards"** (vs tabbed workspace / notebook feed) —
  user pick from previewed options.
- 2026-06-04 — **Numbering: UI overhaul = Phase 36, Actuators → Phase 37** — user pick;
  the "teed-up Phase 36 — Actuators" references in HANDOVER/README updated accordingly.
- 2026-06-04 — **Presentation only** — no change to the plugin contract, artifact data
  shapes, or API; the 14 built-ins' output is unchanged (agent scope guard).

## Decisions deferred

- Whether to add export-to-file (download .md / .json) in addition to clipboard —
  trigger: HS-36-02 — default: clipboard only this phase (the asked-for facility).
- Whether artifact cards should be collapsible by default vs always-expanded —
  trigger: HS-36-01 — default: always-expanded (keeps e2e + copy simple), add a
  collapse toggle that defaults open.
