# PHILO-12-04 - Destinations on the Floor and the drop

- **Project:** holdspeak-philo
- **Phase:** 12
- **Status:** backlog
- **Depends on:** PHILO-12-02 ratified (canvases F, G1–G6, I, J2); PHILO-12-01 and PHILO-12-03 merged
- **Unblocks:** PHILO-12-05, PHILO-12-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-12/grounding/faces.md` F4, F5, F6, F7, F11; `backend.md` findings 2, 4; `checks/charter-astra-r1.md` findings 6, 7
- **Design:** `design/floor-send.md` sections 1, 5, 6
- **Canvas:** F, G1–G6, I, J2, as ratified in story 02

## Problem

No destination is on the Floor, and the Floor's world and scene accept primitives only (`web/src/desk/world.ts:11`; `web/src/desk/gl/sceneModel.ts:123`). The drop matrix is kind × kind (`web/src/desk/dropMatrix.ts:17-48`) and cannot refuse per object. The brief is not on the spatial Floor. The Destinations arrival opens the add form, not a named row (`web/src/pages/cores/connections/Destinations.tsx:360-366`).

## Scope

- **In:** the destinations layer (design §1): active rows only, the right-edge column, positions under `destination:<id>` in the existing map, one pixel-art sprite family per channel (rest, `_sel`, `_stale`), the menu `Open` only (superseding board F2) → Settings → Destinations **focused on that destination's row** (the arrival extended to carry a destination id), not drawn at compact width (`world.ts:172`) or in the list, nothing drawn with no destinations, refresh on the destination-change hook. The brief icon on the spatial Floor (design §5): the latest stored brief, key `intelligence:brief`, open → Intelligence → BRIEF on its exact id, no brief → no icon. The send rule (design §6): the `Preview for <destination>` tag, the refusals on the tag (known absence only; `pending` stays a target), release opens the dragged document's window at the drop point with the destination picked, through story 03's reads, open paths and push seams; the icon goes home; preview only. Board J2 (an artifact dropped on a folder).
- **Out:** destination icons at compact width or in the list; a drop from the phone; Park or Remove on the Floor; prepare on drop; the reads, the Room link and the brief handoff (03).

## Acceptance criteria

- [ ] One icon per active destination; a parked one gone after the next read; a moved icon keeps its place after a reload; `Open` lands on that destination's row in Settings (not the add form); none at compact width or in the list; none with no destinations.
- [ ] For each sendable kind at 1440: the tag reads `Preview for <destination>` and never contains `Send`; release opens the dragged document's window with the destination picked and the preview loaded; the icon goes back; zero `channel_sends` rows and zero kernel operations before Send; after Send, the face equals the hub's send row (its `document_ref` per design §2) and receipt.
- [ ] Each known refusal (no summary, no published update, parked) shows on the tag; release does nothing. A drop on an object whose read is still loading opens the window when the read lands.
- [ ] A drop on a document whose window is already open changes that window's pick in place (story 03's seam), ending with Send and its receipt.
- [ ] The brief icon opens Intelligence → BRIEF; a drop sends the id the icon holds; a refresh does not switch an open preview; no brief → no icon.
- [ ] No new `PrimitiveKind`, pullout or descriptor row for a destination or the brief.
- [ ] Every board of F, G1–G6, I and J2 built as ratified at both widths; the web baseline has zero branch-new failures.

## Effort (not a promise)

PROVISIONAL: 1.5–2 engineering days.

## Test plan

- **Glass:** Playwright fences through the real hub on an isolated HOME; the drop at 1440, the absence of icons at 393.
- **Web unit:** the scene model's destination layer and hit test; the send rule in the drop matrix.

## Notes

- 2026-09-30 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`): the Room link moved to 03; the Settings row focus and J2 added here.
- 2026-09-30 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
