# PHILO-12-04 - Destinations on the Floor and the drop

- **Project:** holdspeak-philo
- **Phase:** 12
- **Status:** backlog
- **Depends on:** PHILO-12-02 ratified (canvases F, G, I); PHILO-12-01 and PHILO-12-03 merged
- **Unblocks:** PHILO-12-05, PHILO-12-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-12/grounding/faces.md` F4, F5, F6, F7, F8, F11; `backend.md` findings 2, 4
- **Design:** `design/floor-send.md` sections 1, 5, 6
- **Canvas:** F, G, I, as ratified in story 02

## Problem

No destination is on the Floor, and the Floor's world and scene accept primitives only (`web/src/desk/world.ts:11`; `web/src/desk/gl/sceneModel.ts:123`). The drop matrix is kind × kind (`web/src/desk/dropMatrix.ts:17-48`) and cannot refuse per object. The brief is not on the Floor. No deep link opens the Room at the Update posture with one update (faces §5, unknown).

## Scope

- **In:** the destinations layer (design §1): active rows only, the right-edge column, positions under `destination:<id>` in the existing map, one pixel-art sprite family per channel (rest, `_sel`, `_stale`), the menu `Open` → Settings → Destinations at that row, not drawn at compact width (`world.ts:172`), nothing drawn with no destinations, refresh on the destination-change hook. The brief icon (design §5): the latest stored brief, key `intelligence:brief`, open → Intelligence → BRIEF, no brief → no icon. The send rule (design §6): the `Preview for <destination>` tag, the refusals on the tag, release opens the dragged document's window at the drop point with the destination picked (decision, meeting with Summary and the picker, project at the Update posture with its latest published update, brief, artifact), the icon goes home, preview only. The Room deep link if it does not exist (its shape in this story's first commit, checked by Astra).
- **Out:** destination icons at compact width; a drop from the phone; Park or Remove on the Floor; prepare on drop.

## Acceptance criteria

- [ ] One icon per active destination; a parked one gone after the next read; a moved icon keeps its place after a reload; `Open` lands on that row in Settings; none at compact width; none with no destinations.
- [ ] For each sendable kind at 1440: the tag reads `Preview for <destination>` and never contains `Send`; release opens the dragged document's window with the destination picked and the preview loaded; the icon goes back; zero `channel_sends` rows and zero kernel operations before Send; after Send, the face equals the hub's send row (its `document_ref` per design §2) and receipt.
- [ ] Each refusal (no summary, no published update, parked) shows on the tag; release does nothing.
- [ ] The brief icon opens Intelligence → BRIEF; a drop sends the id the view shows; a refresh does not switch an open preview; no brief → no icon.
- [ ] No new `PrimitiveKind`, pullout or descriptor row for a destination or the brief.
- [ ] Every board of F, G and I built as ratified at both widths; the web baseline has zero branch-new failures.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days.

## Test plan

- **Glass:** Playwright fences through the real hub on an isolated HOME; the drop at 1440, the absence of icons at 393.
- **Web unit:** the scene model's destination layer and hit test; the send rule in the drop matrix.

## Notes

- 2026-09-30 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
