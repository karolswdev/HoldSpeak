# HSM-8-02 — PencilKit notebook

- **Project:** holdspeak-mobile
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HSM-8-01
- **Unblocks:** HSM-8-03
- **Owner:** unassigned

## Problem

The iPad's differentiator is handwriting. The charter calls for PencilKit
handwritten notes and a notebook mode — the thing a laptop can't do in a meeting.
Notes have to live alongside the live transcript and persist with the meeting.

## Scope

- **In:** a PencilKit notebook surface in the meeting screen (handwritten notes,
  notebook mode), with the drawing persisted and associated with the meeting via
  the Phase-4 store.
- **Out:** linking a note to a transcript moment (HSM-8-03). Handwriting-to-text
  recognition. Artifact review (HSM-8-04). Any business logic in the view.

## Acceptance criteria

- [ ] A PencilKit canvas captures handwritten notes during/after a meeting in a
      notebook mode.
- [ ] The notebook persists with the meeting and reloads intact (strokes
      preserved).
- [ ] The notebook coexists with the live transcript view without dropping Pencil
      strokes during active transcription (verified on device).
- [ ] Notebook persistence goes through the Runtime-Core/store seam, not direct
      file access from the view.

## Test plan

- Unit: the note view-model persist/reload over a fake store → drawing round-trips.
- Manual / device: take Pencil notes on an iPad during a live recording; confirm
  no dropped strokes and reload-intact.

## Notes / open questions

- Persistence model (PKDrawing blob vs structured) is a phase deferred decision —
  default to the PKDrawing data associated with the meeting.
- Keep stroke capture and transcription off each other's main-thread work so the
  combined screen stays responsive (phase risk).
