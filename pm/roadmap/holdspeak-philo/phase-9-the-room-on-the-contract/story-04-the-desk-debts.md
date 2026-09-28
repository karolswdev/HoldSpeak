# PHILO-9-04 - The desk debts: the selection and the list face (canvas first)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter; the list canvas ratified before the list face is built (the selection token needs no canvas)
- **Unblocks:** PHILO-9-05
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** the owner's D2 (2026-09-27); Phase 8 THE LEDGER rows 1, 2, 6 (`../phase-8-the-honest-floor/final-summary.md`); BACKLOG "PHILO-8-03 follow-ups" row 1, "PHILO-8-01 follow-ups" row 1, "PHILO-8-02 follow-ups" row 1; measured again on main `b37dc2fb`, `docs/internal/philo/phase-9/grounding/README.md` "The D2 debts"
- **Canvas:** the list face at 1440 and 393 from the library species, ratified by the owner before build (UX-CANON §A.2)

## Problem

Measured on main `b37dc2fb` (grounding `d2/`):

- The desk-wide `::selection` is `--accent-soft` (`web/src/styles/global.css:68-71`): `rgba(168,110,74,.12)` over the field's `rgb(21,23,29)` is **1.13:1** at both widths, so a selected name looks unselected.
- The list's census and status lines are 10 px (`web/src/desk/components/list-view.css:61`, `:76`); 51 (1440) and 33 (393) visible text nodes are under 12 px.
- The status reads "27 SHOWNS OF 27" (`web/src/desk/components/DeskListView.tsx:331`).
- At 393 the Kind, Zone and Attention columns are wholly off the right edge (cells end at 685, 764 and 842 px on a 393 px viewport): only NAME shows.
- The four sort headers are raw `<button>`s (`web/src/desk/components/DeskSortableTable.tsx:96`; UX-CANON §A.1).
- At 393 the row menu's Delete is cut 15 px at the bottom (top 839, bottom 867, viewport 852; the menu opens `anchor="below"`, `DeskListView.tsx:376-385`). At 1440 it is in view.

## Scope

- **In:** a selection token with a visible contrast, desk-wide (the library's token, not a per-face override); the list face as the canvas draws it: product text at 12 px or more, the "SHOWN" plural, every column readable at 393, the sort headers as the library Button, the row menu kept inside the viewport at 393 (the menu species, not a list-only patch).
- **Out:** the 11/10 px rules outside the list (Phase 7 ledger row 11); the Floor's rename field (BACKLOG "PHILO-8-01 follow-ups").

## Acceptance criteria

- [ ] The selected zone name on the list reaches at least 3:1 against the field at 1440 and 393 (measured, as the grounding probe measures it); the palette search field too (red on main: 1.13:1).
- [ ] The list shows no product text under 12 px at 1440 and 393 (red on main: 51 and 33 nodes).
- [ ] The status says "SHOWN" for any count (red on main: "SHOWNS").
- [ ] At 393 every column the canvas keeps is inside the viewport (red on main: three columns off screen); at 1440 preservation green.
- [ ] The sort headers are the library Button (a structural fence; a mutation re-adding a raw `<button>` turns it red).
- [ ] At 393 the row menu's last entry is inside the viewport when opened on a row near the bottom edge (red on main: cut 15 px); at 1440 preservation green (in view on main).
- [ ] The face matches the owner-ratified canvas at both widths; the web baseline has zero branch-new.

## Effort (not a promise)

PROVISIONAL: 1–1.5 engineering days, the canvas included.

## Test plan

- **Fences and atlas cases ship with this story** (story 05 only assembles and reruns).
- **Glass:** executable failing assertions through the real hub on an isolated HOME at 1440 and 393. The grounding probes (`docs/internal/philo/phase-9/grounding/probes/d2_probe.py.txt`, `menu_probe.py.txt`) are diagnostic measurements, not fences: they record numbers and exit 0.
- **Web unit:** `uv run python scripts/check_web_baseline.py --run`; `docs/generated/boundary-candidates.json` regenerated if `web/src` changes (handover XXIX law 3).
- **Manual / device:** the owner's review of the canvas and the shots.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. The 393 Zone column is worse than the Phase 8 record ("`1 ITEM` shows as `1 ITE`"): on this main the whole column is off screen.
- 2026-09-27 — round two (Codex Astra r1 F7, F8 paid): preservation green at the unaffected width; the sort headers a structural fence; fences ship with the story.
