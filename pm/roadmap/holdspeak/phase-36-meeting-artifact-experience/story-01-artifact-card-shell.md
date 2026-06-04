# HS-36-01 — Elevated artifact-card shell + overflow-safe layout

- **Project:** holdspeak
- **Phase:** 36
- **Status:** not-started
- **Depends on:** none
- **Unblocks:** HS-36-02, HS-36-03
- **Owner:** unassigned

## Problem

Artifacts render inside a generic `.segment` card (`web/src/pages/history.astro`
~927–1132) with a basic title + `status-pill` + metadata pills. It reads as flat and
undesigned, and wide content overflows: `.risk-table` (5 columns, unbounded `Risk` /
`Mitigation` cells) has no `overflow-x` container and no cell wrapping, so it blows out
the modal horizontally. This is the most-complained-about part of the meeting view.

## Scope

- **In:**
  - A shared **artifact card** shell (new classes, e.g. `.artifact-card`,
    `.artifact-card__header`, `.artifact-card__body`, `.artifact-card__accent`) applied
    to every artifact in the detail modal, replacing the generic `.segment` chrome for
    artifacts. Header = type icon + title + type chip + (slot for the copy button from
    HS-36-02) + a collapse toggle (defaults open).
  - A **type-colored accent edge** driven by artifact type (map each type → a Signal
    status/accent color; e.g. incident/risk → danger/warn, decision/announcement →
    accent, requirements/scope → info).
  - **Overflow-safe body:** the card body (and especially tables) contain horizontal
    overflow — a scroll container around wide tables + sensible `word-break`/min-column
    behavior so `.risk-table` and friends never push the modal wider.
  - Signal tokens only (`tokens.css`): surfaces, `--elev-*`, `--radius-*`, `--space-*`,
    status colors, motion.
  - Rebuild the bundle (`cd web && npm run build`) and commit `holdspeak/static/_built/`.
- **Out:**
  - The copy button's *behavior* (HS-36-02) — leave a header slot for it.
  - Deep per-type body restyling (HS-36-03) — this story is the shell + overflow fix;
    bodies keep their current inner markup (and asserted selectors) inside the new card.

## Acceptance criteria

- [ ] Every artifact in the detail modal renders inside the new `.artifact-card` shell
      (accent edge + header + contained body); the generic `.segment` artifact chrome
      is gone.
- [ ] The asserted inner selectors still resolve inside the card:
      `.risk-table tbody tr`, `.incident-timeline li`, `.runbook-list .runbook-change`,
      `.stakeholder-update`, `.announcement-artifact .announcement`,
      `.action-item-list .action-item`, `.decisions-artifact .decision-list li`,
      `.requirement-list .requirement-item`, `.adr-artifact .adr-record`,
      `.milestone-artifact .milestone-record`, `.dependency-list li`,
      `.scope-list .scope-finding`, `.signal-list .signal-item`,
      `.mermaid-artifact` — preserved, or the e2e updated in lockstep.
- [ ] `.risk-table` no longer overflows the modal at a 1280-wide (and a narrow ~700)
      viewport — it scrolls within its card. Verified by inspection / screenshot.
- [ ] `cd web && npm run build` succeeds; the rebuilt `holdspeak/static/_built/` is
      committed in the same commit.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Test plan

- Unit/suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green (no Python
  behavior changed; this is frontend).
- Manual/visual: rebuild + open `/history` for the incident-retro meeting; confirm the
  card shell + the risk table contained at 1280 and at a narrow width. Screenshot.
- e2e (opt-in, closeout): `HOLDSPEAK_SPOKEN_E2E=1 … test_spoken_incident_retro_end_to_end`
  still finds every selector (full re-run lands in HS-36-04).

## Notes / open questions

- Collapse toggle defaults **open** so the e2e and copy see the body.
- Keep the accent-color → type mapping in one place (a small JS/CSS map) so HS-36-03
  can reuse it.
