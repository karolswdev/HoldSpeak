# PHILO-12-02 - The canvases F–J

- **Project:** holdspeak-philo
- **Phase:** 12
- **Status:** in-progress
- **Depends on:** the owner's ratification; design `floor-send.md` (the wire the harness shim serves). May start before Phase 11 closes.
- **Unblocks:** PHILO-12-03, PHILO-12-04
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-12/grounding/faces.md` §3, F1–F10
- **Design:** `design/floor-send.md`
- **Canvas:** five, before any build (UX-CANON §A.2): F destinations on the Floor, G the drop, H `Send to ▸`, I the brief icon, J artifacts

## Problem

Nothing is drawn. The Floor has no destination, no brief and no send gesture (faces shots `01-floor-1440.png`, `02-decision-menu-1440.png`). The decision wears the note sprite (F2).

## Scope

- **In:** the boards of faces.md §3, each at 1440 × 900 and 393 × 852, on the real product with a harness shim (the Phase 10/11 pattern, `../phase-10-the-channels/assets/story-04-send-canvas/README.md`), with the ratification defaults applied: F1–F4 (the column at the right edge, parked ones absent, 393 the list with no destination icons and the brief row; the icon's menu `Open` only, which supersedes grounding board F2 (`Open`, `Park`; Astra r1 finding 6), and `Open` landing on the destination's row in Settings; no destinations, nothing drawn; the decision sprite beside a note, rest / `_sel` / `_stale`); the six channel sprites; G1–G6 at 1440 (the `Preview for <destination>` tag; release, the window with the destination picked and the preview open, the egress chip in the well; sent; the refusal tags; a meeting with Summary and the picker; a project at the Update posture with its latest published update), 393 showing the same end state reached by the menu; H1–H5 (`Send to ▸` at 1440, at 393 in the list with the back row, `Add destination` with no destinations, withheld on a note, the menu bar Object menu and the compact `Go` menu); H6 the brief row in the 393 list with `Send to ▸`; H7 a row whose read is loading, and `CAN'T CHECK` on a failed read; G7 a second pick on an already-open window, the pick changed in place; G8 Summary → Digest with the destination kept; G9 the Room already open on another update, switched to the linked update; I1–I4 (the brief icon `BRIEF <day>`, opened, dropped, no brief → no icon); J1–J2 (the artifact window with its SEND well and library Buttons; an artifact dropped on a folder). Astra's check; then the owner's word, recorded verbatim.
- **Out:** the build (03, 04).

## Acceptance criteria

- [ ] Every board drawn at both widths; G at 1440 with its 393 end state by the menu.
- [ ] No tag says `Send`; the egress chip only in the well; no brand logo; no counter of zero.
- [ ] Every verb the library Button; no modal; no prose.
- [ ] Astra's check recorded; the owner's ratification recorded verbatim before story 03 or 04 commits a face change.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Glass:** the harness boards through the real hub on an isolated HOME at both widths; shots under `assets/story-02-canvas/`.

## Notes

- 2026-10-01 — round two drawn on Astra canvas r1 RATIFY-WITH-CONDITIONS (`checks/canvas-astra-r1.md`, verbatim); paid in `assets/story-02-canvas/README.md` ("Round two").
- 2026-09-30 — round one drawn: `assets/story-02-canvas/` (README, `index.html`, `harness/`, `shots/`). For Astra's check and the owner's ratification.
- 2026-09-30 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-30 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
