# Evidence — HS-36-01: Elevated artifact-card shell + overflow-safe layout

**Shipped:** 2026-06-04. **Story:** [story-01-artifact-card-shell.md](./story-01-artifact-card-shell.md).

## What shipped

The generic flat `.segment` artifact container is replaced by a Signal **elevated
artifact card**. Each meeting artifact now renders as a distinct card with:

- a **type-colored accent edge** (a 3px left bar driven by `artifactAccent()` →
  `--artifact-accent`: incident→danger, risk/runbook→warn, comms/decisions→accent,
  requirements/adr/milestone/dependency/scope/diagram→info, action-items/signals→ok);
- a **header** — a type **icon** (`artifactIcon()`: 🔥 incident, ⚠️ risk, 🧯 runbook,
  📣 stakeholder, 📢 announcement, 🎯 decisions, ✅ actions, 🧩 requirements, 🏛️ adr,
  🗓️ milestones, 🔗 dependencies, 🔎 scope, 💬 signals, 🗺️ diagram), a bold
  display-font **title**, a colored **type chip** + confidence/date/source pills, and a
  **collapse toggle** (defaults open);
- an **overflow-safe body** — wide content scrolls within the card.

Cards stack full-width (`.artifact-stack`) for readability instead of the old 280px
auto-fill grid.

**Risk-table overflow fixed:** the `.risk-table` is wrapped in `.table-scroll`
(`overflow-x: auto`) and given `min-width: 540px` + `td { overflow-wrap: anywhere }`, so
it scrolls within its card instead of blowing out the modal width.

## Files

- `web/src/pages/history.astro` — artifact loop restructured from `<div class="segment">`
  to the `.artifact-card` shell (header + `x-data="{open:true}"` collapsible
  `.artifact-card__body`); `.grid` → `.artifact-stack`; risk table wrapped in
  `.table-scroll`; ~120 lines of Signal CSS for `.artifact-card*` / `.artifact-stack` /
  `.table-scroll` + the risk-table overflow rules. Inner per-type markup (and every
  asserted selector) is unchanged — it just moved into the card body.
- `web/src/scripts/history-app.js` — `artifactIcon()` / `artifactAccent()` /
  `artifactTypeLabel()` helpers.
- `holdspeak/static/_built/**` — rebuilt locally (`cd web && npm run build`) so the
  served app / e2e reflect the source. **Not committed** — it's a gitignored build
  product (`.gitignore:55`), built from `web/src/**` at install (`scripts/install.sh`)
  or bundled into the wheel at package time (`pyproject` `holdspeak/static/_built/**`).
  The committed change is the **source**.
- `tests/e2e/test_spoken_meeting_e2e.py` — lockstep: the two dynamic-test card-count
  *prints* now count `.detail-side .artifact-card` (the artifact card is no longer
  `.segment`). Assertions unchanged.

## Verification

- **`cd web && npm run build`** → ✓ 8 pages built; the rebuilt (gitignored) bundle's
  `history/index.html` contains `artifact-card` + `table-scroll` and the built JS
  contains `artifactAccent` — i.e. the source change reaches the served output.
- **Selectors preserved (the key risk).** Re-ran the incident-retro spoken-e2e on real
  `.43` — all asserted inner selectors still resolve inside the new card body:

  ```
  $ HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s \
      tests/e2e/test_spoken_meeting_e2e.py::test_spoken_incident_retro_end_to_end
  [e2e:incident] artifacts: ['decision_announcement', 'incident_timeline',
  'risk_register', 'runbook_delta', 'stakeholder_update']
  1 passed in 22.85s
  ```

  (`.risk-table tbody tr`, `.incident-timeline li`, `.runbook-list .runbook-change`,
  `.stakeholder-update`, `.announcement-artifact .announcement` all matched, now wrapped
  in `.artifact-card__body` / `.table-scroll`.)
- **Full suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2020 passed,
  15 skipped**.
- **Visual:** [`evidence/artifact_cards_new_look.png`](./evidence/artifact_cards_new_look.png)
  — the incident-retro artifacts in the new elevated cards (accent edges, icons, type
  chips, collapse toggles; the risk heatmap contained in its scroll wrapper).

## Acceptance criteria — re-checked

- [x] Every artifact renders in the `.artifact-card` shell (accent edge + header +
      contained body); the generic `.segment` artifact chrome is gone (transcript/action
      cards still use `.segment`, untouched).
- [x] Asserted inner selectors still resolve — incident e2e green.
- [x] `.risk-table` contained via `.table-scroll` (+ min-width + cell wrap) — no longer
      overflows the modal.
- [x] `npm run build` succeeds; the source change reaches the rebuilt bundle (which is
      a gitignored build product — not committed; built at install/package time).
- [x] Full suite green.

## Deviations from plan

The copy-button **slot** (HS-36-02) is reserved by the `.artifact-card__actions` row
(currently just the collapse toggle); the button itself lands in HS-36-02. The
committed `dynamic_meeting_after.png` (HS-36-05) still shows the *old flat* cards — it
predates this story; HS-36-06 re-captures the before/after in the new cards.
