# PHILO-12-03 - Send to, the artifact window and the decision sprite

- **Project:** holdspeak-philo
- **Phase:** 12
- **Status:** backlog
- **Depends on:** PHILO-12-02 ratified (canvases H, J1, F4, G7–G9); PHILO-12-01 merged
- **Unblocks:** PHILO-12-04, PHILO-12-05
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-12/grounding/faces.md` F1, F2, F3, F8, F9, F10; `checks/charter-astra-r1.md` findings 1–6
- **Design:** `design/floor-send.md` sections 2 (the reads), 3, 5 (the handoff and the list row), 6 (the push seams), 7, 8
- **Canvas:** H1–H7, J1, F4, G7–G9, as ratified in story 02

## Problem

No object menu offers Send (`web/src/desk/verbRegistry.ts:399-591`). The menu bar builds its entries apart from `objectMenuEntries` (`web/src/desk/components/DeskMenuBar.tsx:78-82`; the compact `Go` menu `:101-108`). On the phone the list has no drag, so the menu is the only path (F1), and the list row exposes `onContextMenu` only (`web/src/desk/components/DeskSortableTable.tsx:247`). The Floor does not know a meeting's summary or a project's published update (`web/src/lib/primitives.ts:213`; `holdspeak/services/meeting_service.py:868`). The Room opener carries only a project (`web/src/desk/store/compositorSlice.ts:158-168`); the brief navigation carries no id (`web/src/desk/intelligenceNavigation.ts:5`; `web/src/desk/pullouts/views/BriefView.tsx:174`). The pick and the meeting form are private and read once (`web/src/desk/surface/send/SendWell.tsx:63-64`, `:459`; `web/src/meetings/MeetingSendWell.tsx:28`, `:34`). The artifact window has no SEND well and three raw `<button>`s (`web/src/desk/pullouts/ArtifactPullout.tsx:38`, `:57`, `:64`). The decision wears the note sprite (`web/src/desk/sprites.ts:28`).

## Scope

- **In:**
  - **One shared composition** of an object's menu entries, `Send to ▸` included, and all three entry points: the spatial Floor, the list, the menu bar (its Object menu and, at compact width, the `Go` menu). `Send to ▸` rows from the active destinations; `Add destination` when there are none; withheld per object through story 01's binding; the registry comment (`verbRegistry.ts:8-12`) amended for A.11.
  - **The two reads** in one shared module for the menu and story 04's drop: summary presence (`GET /api/meetings/{meeting_id}`, `holdspeak/web/routes/meetings/crud.py:100`) and the latest published update (`GET /api/projects/{project_id}/updates`, `holdspeak/web/routes/project_updates.py:61`), each as `Fact<T>`; a pick on `pending` waits; a known absence refuses on the row; a failed read shows `CAN'T CHECK` and still opens the document's window.
  - **The open paths:** the Room link `{ projectId, updateId, destinationId }`, opening that update at the Update posture when the data is ready, also when the Room is already open (its code shape in this story's first commit, checked by Astra); the brief's exact-id handoff `{ view: "brief", briefId, destinationId }` over story 01's by-id read; the brief as a list row.
  - **The push seams** (design §6): one per well, named in `web/src/desk/surface/contract.md`; an open well reacts in place; the destination kept across Summary → Digest → Follow-up.
  - **A touch long-press on a list row** opens the row menu (or the platform already does, proven).
  - The SEND well in `ArtifactPullout` on `artifact:<id>`; its three raw buttons as library Buttons. The decision sprite family (rest, `_sel`, `_stale`) and its pool entry.
- **Out:** destination icons, the brief icon on the spatial Floor, the drop, J2, the Settings row focus (04).

## Acceptance criteria

- [ ] `Send to ▸` on each sendable kind (the brief as a list row) on the spatial Floor, the list and the menu bar (Object menu; `Go` at compact width), from one composition, at both widths; withheld on a note, a persona, knowledge, a meeting with a known absent summary, a project with a known absent published update.
- [ ] At 393 the fence opens the list row menu by a **touch** long-press; the submenu replaces the panel with a back row. A mouse right-click is not the proof.
- [ ] A pick on an object whose read is loading opens the right window when the read lands; a failed read shows `CAN'T CHECK` and the pick still opens the document's window. No `Send to ▸` is withheld while a read is not `known`.
- [ ] With no destinations, one `Add destination` row opens Settings → Destinations at the form.
- [ ] A pick opens the right window with the destination picked and the preview loaded; zero `channel_sends` rows and zero kernel operations before Send; after Send, the face equals the hub's send row (its `document_ref` per design §2) and receipt.
- [ ] Rendered-transition fences at both widths, each ending with Send and its receipt: a second pick on an already-open window changes the pick in place; Summary → Digest → Follow-up keeps the destination; the Room already open on another update switches to the linked update; Intelligence → BRIEF keeps the handed brief id when `latest` is another.
- [ ] The artifact window sends `artifact:<id>`; no raw `<button>` in `ArtifactPullout` (red on main).
- [ ] The decision has its own sprite at rest, `_sel` and `_stale` (red on main).
- [ ] Every board of H1–H7, J1, F4 and G7–G9 built as ratified at both widths; the web baseline has zero branch-new failures.

## Effort (not a promise)

PROVISIONAL: 2.5–3.5 engineering days.

## Test plan

- **Glass:** Playwright fences through the real hub on an isolated HOME at both widths; touch emulation for the 393 list menu.
- **Web unit:** the shared composition per kind and per refusal; the reads' `Fact` states; the push seams.

## Notes

- 2026-09-30 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`): the Room link, the reads, the open paths and the push seams moved here; the menu bar and the touch list menu added; J2 moved to 04.
- 2026-09-30 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
