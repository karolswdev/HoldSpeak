# PHILO-12-03 - Send to, the artifact window and the decision sprite

- **Project:** holdspeak-philo
- **Phase:** 12
- **Status:** backlog
- **Depends on:** PHILO-12-02 ratified (canvases H, J, F4); PHILO-12-01 merged
- **Unblocks:** PHILO-12-04, PHILO-12-05
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-12/grounding/faces.md` F1, F2, F3, F9, F10
- **Design:** `design/floor-send.md` sections 3, 6 (the pre-pick setters), 7, 8
- **Canvas:** H, J, F4, as ratified in story 02

## Problem

No object menu offers Send (`web/src/desk/verbRegistry.ts:399-591`). On the phone the list has no drag, so the menu is the only path (F1). The pick and the meeting form are private maps; nothing outside the well can pre-pick (`web/src/desk/surface/send/SendWell.tsx:63-64`; `web/src/meetings/MeetingSendWell.tsx:28`). The artifact window has no SEND well and three raw `<button>`s (`web/src/desk/pullouts/ArtifactPullout.tsx:38`, `:57`, `:64`). The decision wears the note sprite (`web/src/desk/sprites.ts:28`).

## Scope

- **In:** one `sub` entry `Send to ▸` in `objectMenuEntries` (`web/src/desk/floorMenu.ts:59-71`), reaching the spatial Floor, the list and the menu bar; its rows from the active destinations; `Add destination` when there are none; withheld per object through story 01's binding; one line in the registry comment (`verbRegistry.ts:8-12`) for the withhold exception. The two exported pre-pick setters and their line in `web/src/desk/surface/contract.md`. A pick opens the document's window with the destination picked and the preview loaded. The SEND well in `ArtifactPullout` on `artifact:<id>`; its three raw buttons as library Buttons. The decision sprite family (rest, `_sel`, `_stale`) and its pool entry.
- **Out:** destination icons, the brief icon, the drop (04).

## Acceptance criteria

- [ ] `Send to ▸` on each sendable kind on the spatial Floor, the list and the menu bar Object menu, at both widths (the list at 393, the submenu replacing the panel with a back row); withheld on a note, a persona, knowledge, a meeting with no summary, a project with no published update.
- [ ] With no destinations, one `Add destination` row opens Settings → Destinations at the form.
- [ ] A pick opens the right window with the destination picked and the preview loaded; zero `channel_sends` rows and zero kernel operations before Send; after Send, the face's outcome equals the hub's send row (its `document_ref` per design §2) and receipt in the same fence.
- [ ] The artifact window sends `artifact:<id>`; no raw `<button>` in `ArtifactPullout` (red on main).
- [ ] The decision has its own sprite at rest, `_sel` and `_stale` (red on main).
- [ ] Every board of H, J and F4 built as ratified at both widths; the web baseline has zero branch-new failures.

## Effort (not a promise)

PROVISIONAL: 1.5–2 engineering days.

## Test plan

- **Glass:** Playwright fences through the real hub on an isolated HOME at both widths.
- **Web unit:** the menu entry per kind and per refusal; the setters.

## Notes

- 2026-09-30 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
