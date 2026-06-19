# Phase 8 — iPad Experience

**Status:** planning (scaffolded 2026-06-18). Track I of the Council
Implementation Charter. The first Platform Host (Layer 4): the iPad app that
turns the runtime into the charter's flagship experience — record a meeting, take
PencilKit notes, link them to the transcript, and review the artifacts, all on an
iPad Air/Pro M4.

**Last updated:** 2026-06-18 (scaffolded — stories HSM-8-01..04 stubbed from
charter Track I; no work started).

## Goal

Build the iPad SwiftUI host over the Runtime Core: a meeting-capture screen
(record → live transcript), a PencilKit notebook for handwritten notes,
transcript linking (a note bound to the transcript moment it was written at), and
an artifact-review surface. The phase passes when the full meeting-notebook
workflow is complete on an iPad — the Track I gate. The host is thin: it presents
the Runtime Core, it does not own business logic.

## Scope

- **In:** the iPad app shell + meeting-capture screen over the Runtime Core
  (HSM-8-01); PencilKit handwritten notes + notebook mode (HSM-8-02); transcript
  linking — note ↔ `Segment`/timestamp (HSM-8-03); artifact review + the
  notebook-workflow gate closeout (HSM-8-04).
- **Out:** the iPhone experience (Phase 9). Sync across devices (Phase 10). The
  audio/transcription/inference/intelligence engines themselves (Phases 2–7 — this
  host consumes them). Any business logic in the view layer (it stays in the
  core). Hardening scenarios (Phase 11).

## Exit criteria (evidence required)

- [ ] The iPad app records a meeting and shows the live transcript, driving the
      Runtime Core through provider/seam interfaces only (no business logic in the
      views) (HSM-8-01).
- [ ] PencilKit handwritten notes work in a notebook mode and persist with the
      meeting (HSM-8-02).
- [ ] A handwritten note links to the transcript moment it was taken at, and
      tapping the link navigates to that `Segment` (HSM-8-03).
- [ ] **Track I gate — the meeting-notebook workflow is complete:** record →
      transcript → notebook notes → linked moments → artifact review, end to end
      on a real iPad, evidenced by a device walkthrough (HSM-8-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-8-01 | iPad shell + meeting capture | backlog | [story-01](./story-01-ipad-shell-meeting-capture.md) | — |
| HSM-8-02 | PencilKit notebook | backlog | [story-02](./story-02-pencilkit-notebook.md) | — |
| HSM-8-03 | Transcript linking | backlog | [story-03](./story-03-transcript-linking.md) | — |
| HSM-8-04 | Artifact review + notebook closeout | backlog | [story-04](./story-04-artifact-review-closeout.md) | — |

## Where we are

Just scaffolded. This is the first real product surface and it sits on top of the
whole stack: it needs Phase 2 (audio), Phase 3 (transcript), and — for the review
to show real artifacts — Phases 5–7. The four stories follow Track I's feature
list (capture, PencilKit notebook, transcript linking, artifact review) and end
on the notebook-workflow gate. Next: HSM-8-01 once Phases 2–3 give a recordable,
transcribing runtime; the artifact-review depth (HSM-8-04) wants Phase 6.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Business logic leaks into SwiftUI views, breaking the charter's layer rule | high | Views call Runtime-Core seams / view-models only; no engine code in the view layer; keep the host thin | A view imports an engine/provider concrete type or holds business state — pull it into the core |
| Transcript linking has no stable anchor (segment ids shift) to bind a note to | medium | Bind notes to the Phase-0 `Segment` identity/timing, not to rendered text offsets | A note's link breaks when the transcript re-renders — anchor on the contract `Segment`, not the view |
| Artifact review needs Phase 6 artifacts that aren't ready when Phase 8 starts | medium | Build capture + notebook + linking first; gate the review depth (HSM-8-04) on Phase 6; stub artifacts visibly until then | HSM-8-04 can't show real artifacts because Phase 6 isn't done — sequence it after Phase 6, don't fake parity |
| PencilKit + live transcript on one screen fights for layout/performance on smaller iPads | low | Target iPad Air/Pro M4 (Tier-1) first; verify the combined screen on device, not just canvas | The notebook drops Pencil strokes while transcribing live — separate the workloads or stage them |

## Decisions made (this phase)

- 2026-06-18 — The iPad host is a thin SwiftUI Platform Host (Layer 4) over the
  Runtime Core; all business logic stays in the core, per the charter's
  architecture principle — charter Architecture §Principle + §Layers.

## Decisions deferred

- Notebook persistence model (PencilKit `PKDrawing` blob vs. a structured note
  entity) — trigger: HSM-8-02 — default: store the `PKDrawing` data associated
  with the meeting, with link anchors as structured metadata.
- Whether artifact review is read-only in v1 or includes approve actions (the
  Propose→Approve half) — trigger: HSM-8-04 — default: review + approve of
  proposals on-device, never autonomous execution (charter non-goal).
- Multitasking / Stage Manager support — trigger: post-gate polish — default:
  single-window first; multitasking parked.
