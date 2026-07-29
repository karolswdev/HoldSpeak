# HS-109-05 - The Project Memory window

- **Project:** holdspeak
- **Phase:** 109
- **Status:** backlog
- **Depends on:** HS-109-01, HS-109-03, HS-109-04
- **Unblocks:** HS-109-08
- **Owner:** unassigned

## The thesis (the bar)

The project APIs are stronger than their surface: meetings, action
items, artifacts, summary, and qualified relationships all exist
server-side, while on the desk a Project is a row in the Meetings
window's plumbing drawer with no open action
(`HistoryCore.tsx:953-1034`), and `project` is not even a primitive
kind (`web/src/lib/primitives.ts:27-39`).

The bar: **the Project becomes a touchable desk object, and opening
it opens its memory.** One window in the one grammar: the timeline
of meetings and decisions, the decision list with lifecycle worn
honestly, memory search scoped to the project, and ask-this-project
— each answer wearing its citations and its egress badge. Filed
objects stay openable; the transcript moment is one jump away.

## Problem

Everything 01-04 built is invisible. Memory that is not touchable on
the desk does not exist for the owner (Article I: everything is seen
and done through the Desk).

## Recipe

1. **The primitive.** `project` joins the desk primitive contract —
   icon per the icon discipline (1:1 pixel cell, real states, the
   documented Pixellab recipe if a new sprite is needed), Info
   derived from the one contract, verbs on the registry
   (Open / Get Info / Ask this project). No ad-hoc card.
2. **The window.** A memory core in `SurfaceWindows` (the same seam
   every core uses): a timeline face (meetings + decisions + promoted
   artifacts, newest down, each row openable to its object), a
   decisions wing (lifecycle chips — recorded / accepted /
   superseded→successor / rejected — with the transcript-moment jump
   from 02), and a search well scoped to the project (04's index)
   whose hits open in place.
3. **Ask this project.** The existing Ask composer grammar
   (`desk-chat-well`) embedded with grounding pre-pinned to the
   project; the answer renders through `Material` with its citation
   refs as openable chips and the egress badge at the point of
   decision. The overflow count from 04 renders plainly ("grounded on
   12 of 47 matches").
4. **Since last meeting, project-qualified.** The aftercare rollup
   scoped to THIS project's meetings (fixing the global
   `_previous_meeting` scan for this surface —
   `meeting_aftercare.py:157-181`), and the window names WHICH
   meeting it compared against (Article VI).
5. **Promotion in-world.** Accept / supersede / promote verbs on a
   decision row (03's routes), edit-in-place where text is editable,
   voice mic on the search and ask inputs (the standing input rule),
   zero modals.
6. **Both densities.** 1440 and 393 walks against the real hub with
   real archive data; the phone leads with the list; no body
   overflow.

## Out of scope

- New chart/visualization work — the timeline is rows, not a canvas.
- Cross-project search UI (the route supports it; the global surface
  is a future notch).
- Any change to Ask's egress/consent semantics.
- Drawer drag-reorder and the other Workbench remainders (BACKLOG AA).

## Acceptance

- A Project opens from the desk as a real window that restores with
  the desk's arrangement memory; `project` Info derives from the
  contract; verbs ghost with reasons, never hide.
- The timeline renders real archive data; every row opens its object
  in-world; a decision's moment jumps to the transcript segment.
- Search-in-project returns 04's ranked hits; empty is an honest
  zero state, not blank.
- Ask-this-project produces a cited answer against `.43`; citations
  open; the badge and the grounded-on count are visible at 1440 and
  393.
- Supersede from the window propagates (03) and the row's face
  updates without reload.
- Screenshot walk at both densities on the real hub, live-caught
  defects fixed and re-walked; web suite + build + token gates green.
- Full suite green; spine byte-unchanged.

## Test plan

- **Unit (web):** timeline composition; lifecycle chips; citation
  chip rendering; empty/overflow states.
- **Integration:** project-scoped aftercare; window restore; verb
  registry rows.
- **Live (evidence):** the screenshot walk (1440+393) with real
  archive data; the cited `.43` ask from the window; the supersession
  walked on-screen.

## Chef's notes

- This is the story the owner will judge the phase by. The Desk
  Grammar (`docs/internal/DESK_GRAMMAR.md`) is law: one panel system,
  windows coexist, badges reported never inferred.
- The icon needs the dual-state discipline from Phase 105 — check
  whether an existing sprite family member fits before generating.
- "Grounded on 12 of 47" is the honesty feature of the whole phase —
  fight for that count's plumbing if 04's shape makes it awkward.
- Reuse `SurfaceLibrary`/`SurfaceRows` composition; a bespoke list
  component here would be a Phase-102-style refit waiting to happen.
