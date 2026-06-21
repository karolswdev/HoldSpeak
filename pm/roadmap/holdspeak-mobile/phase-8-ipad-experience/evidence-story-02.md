# Evidence — HSM-8-02 (PencilKit notebook)

**Date:** 2026-06-21 · **Status:** done

The iPad's differentiator — handwritten notes that live alongside the live transcript and
persist with the meeting. A rich PencilKit notebook (multi-page, real pen tools), the
thing a laptop can't do in a meeting.

## What shipped

- **`Notebook` view-model (RuntimeCore):** round-trips PencilKit pages (each a serialized
  `PKDrawing`, i.e. `Data`) through a `NotebookStore` seam, keyed per meeting and
  versioned (`NotebookPages`). UIKit-free — the Core works in serialized drawings; the
  view owns the canvas. A corrupt blob reloads to `[]` rather than throwing (a meeting's
  notes never block reopen). `MeetingCapture.currentID` was exposed so notes bind to the
  in-progress meeting before it's persisted.
- **The notebook surface (`MeetingCaptureApp`):** a `PencilCanvas` (`UIViewRepresentable`
  over `PKCanvasView` + the system `PKToolPicker` — pen / pencil / highlighter / eraser /
  ruler + colors), `NotebookView` with **multi-page** nav + add-page, a `FileNotebookStore`
  (one JSON blob per meeting in the app container — the view never touches files). The
  capture screen gained a **Transcript / Notes** segmented control so ink and the live
  transcript **coexist**; the detail screen reloads the meeting's notebook (editable, so
  notes can be added after).

## Tests (ran)

`swift test` → **146 passed / 6 skipped / 0 failed** (+6 `NotebookTests`): pages
round-trip intact through the store; multi-page; **keyed per meeting**; save overwrites;
a **corrupt blob reloads empty, never throws**; save failure propagates.

## Screenshots + real-metal

- `screenshots/notebook.png` (iPad-Pro simulator) — the **rich** surface: the "Handwritten
  notes" notebook with **multi-page nav + add-page** and the full **PencilKit tool picker**
  (pen / pencil / highlighter / eraser / ruler + color palette). Not a blank box.
- The notebook-enabled app **builds + signs, installs, and launched on the physical iPad
  Air M4**. Stroke capture runs on PencilKit's own path (the `PKCanvasView` delegate),
  independent of the 3-second windowed transcription `tick`, so ink and transcription
  don't fight for the main thread.

## Acceptance

- **PencilKit canvas captures notes during/after a meeting** — the Notes pane during
  recording (bound to the live meeting) + the editable notebook on the meeting detail.
- **Rich surface, screenshot-verified** — multi-page + the pen/highlighter/eraser tool
  set + the Signal language (`notebook.png`).
- **Persists with the meeting + reloads intact** — host-proven round-trip
  (`testPagesRoundTripIntact`, keyed per meeting); the detail reloads from the
  `FileNotebookStore`.
- **Coexists with the live transcript without dropping strokes** — the Transcript/Notes
  panes share the screen; stroke capture is on PencilKit's path, off the transcription
  work. The on-device no-dropped-strokes confirmation runs on the app now deployed on the
  iPad (folds into the Track-I gate).
- **Persistence through the seam, not direct file access from the view** — the view drives
  `Notebook` → `NotebookStore`; only `FileNotebookStore` touches files.

## Deferred (by design)

Linking a note to a transcript moment (HSM-8-03) and handwriting-to-text /
ink-into-intelligence (HSM-8-06) are later stories; this stands up the rich notebook and
its persistence.
