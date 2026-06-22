# HSM-14-13 — The spatial workspace (OS-like capture surface)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — **deliverables 1–4 built + host-proven + Simulator-shown** (2026-06-22):
  dockable/minimizable recorder, free-place vs tack, resizable cards, one-tap tidy with undo. The
  stretch deliverables 5–6 (minimap, windowed panes) and the device hardware-feel pass remain. See
  "Evidence" below.
- **Depends on:** HSM-14-11 (free-form desktop + draggable floating recorder)
- **Unblocks:** the "nearly like an operating system" capture experience the owner is after
- **Owner:** unassigned

## Vision (owner)

> "Why must we be contained to those big-ass pages? Why can't we minimize the recording button to
> something smaller, move things around? This is nearly like an operating system. iOS. Incredible."

HSM-14-11 took the first steps: the canvas became one free-form dot-grid **desktop**, the recorder
became a **draggable floating capsule**, and bubbles can be **flung anywhere to tack**. This story
makes it a real **spatial workspace** — elements you arrange, dock, resize, and that remember where
you put them — without losing the one-handed, glanceable feel.

## Design principles

- **Spatial, not modal.** Fewer hard mode switches (the Transcript/Notes segmented toggle); more
  one surface where things coexist and you arrange them.
- **Everything has a place and remembers it.** Positions/sizes persist per meeting.
- **Direct manipulation + haptics.** Drag, snap, resize, dock — all gesture-first with feedback.
- **Never trap the user.** Anything moved/minimized is one gesture from restored; an "organize"
  affordance re-tidies the surface.

## Deliverables (ordered; later ones are stretch)

1. **Dockable floating recorder.** The `FloatingRecorder` can **dock** to an edge (bottom / top /
   side) or float free; magnetic **snap zones** with a haptic; **minimize** to a compact "rec
   orb" (timer dot + waveform tick) and re-expand on tap. Position/dock state persists per session.
2. **Free-place vs tack.** Dragging a streaming bubble can drop it as a **loose card** anywhere on
   the desktop (just placed) **or** tack it as a **marked moment** (feeds MIR, HSM-8-03) — a clear,
   discoverable distinction (e.g. a drop onto the "pin" gutter / a long-press-then-drag = tack;
   a plain drag = loose place). Loose cards persist; tacked cards also mark the moment.
3. **Resizable cards.** Corner-drag (and/or pinch) to resize `NoteCard` / pinned cards; text reflows;
   min/max bounds; size persists.
4. **Organize / tidy.** A one-tap "tidy" that re-flows loose cards into a readable layout (so the
   freedom never becomes a mess), with an undo.
5. **Minimap / overview.** On a surface larger than the viewport, a small overview thumbnail of
   where cards live; tap a region to pan/jump. (Stretch.)
6. **Panes as windows.** Replace the Transcript/Notes segmented toggle with **movable panels**
   (transcript, notes, and — post-meeting — intelligence) that can sit side by side, overlap, or
   minimize — a windowed workspace. (Stretch / likely its own follow-up story.)

## Architecture

- A small **layout model** persisted per meeting (extend the existing `notecards-<id>.json` pattern,
  or a sibling `workspace-<id>.json`): card id → `{x, y, w, h, kind: loose|tacked}`, plus recorder
  dock state. Reuses `CaptureModel` / `NotebookModel` ownership; no new store seam needed.
- **Snap/dock** is a pure function (drop point + viewport → nearest dock/snap target) — host-testable.
- **Coordinate spaces:** keep the named `"canvas"` space from HSM-14-11; the recorder uses the
  screen space. Resizing uses the card's local space.
- Build on the existing `LiveCaptureCanvas`, `PinnedNoteView`, `NoteCardView`, `FloatingRecorder`,
  `DesktopGrid` — extend, don't rewrite.

## Scope

- **In:** deliverables 1–4 (dock/minimize recorder, free-place vs tack, resizable cards, tidy),
  with per-meeting spatial persistence; the snap/dock/tidy math host-tested; Simulator-proven +
  device-verified for hardware feel (drag latency, haptics).
- **Stretch (in this story if time, else split to 14-14):** minimap (5), windowed panes (6).
- **Out:** multi-meeting/global workspace, external-display/Stage-Manager multi-window, collaboration.

## Acceptance criteria

- [ ] **Recorder docks + minimizes** — drag the floating recorder to an edge → it snaps/docks with
      a haptic; minimize → a compact rec orb; re-expand on tap; state persists across a pane switch
      and re-entry. Simulator-proven + device feel verified.
- [ ] **Free-place vs tack is clear** — a bubble can be dropped as a loose card OR tacked as a
      marked moment, with a discoverable distinction; tacking still calls `markMoment` (MIR weight).
      Both persist per meeting.
- [ ] **Cards resize** — corner-drag resizes a note/pinned card within bounds; text reflows; size
      persists across re-entry.
- [ ] **Tidy works + is reversible** — one tap re-flows loose cards into a readable layout; undo
      restores the prior arrangement.
- [ ] **Spatial persistence** — positions/sizes/dock state reload intact when the meeting is
      reopened (host-tested for the layout model; device-verified end to end).
- [ ] **Snap/dock/tidy math host-tested** — pure functions for nearest-dock, snap target, and tidy
      layout have unit tests.
- [ ] **No trap** — every minimized/moved element is one gesture from restored (UI-verified).

## Test plan

- Host tests for the pure layout math (`dock(for:in:)`, `snap`, `tidy`) and the layout
  model's encode/decode round-trip → `swift test`.
- Simulator screenshots (committed) for each deliverable's states (docked / minimized / loose
  card / resized / tidied), via the existing `HS_DEMO` sim seeds.
- Device: hardware feel — drag latency, snap haptics, Pencil vs finger — on the iPad Air M4.

## Evidence (deliverables 1–4 built 2026-06-22; stretch 5–6 + device feel remain)

**Deliverable 1 — dockable + minimizable recorder.** The `FloatingRecorder` **docks** to the
top/bottom edge on drag-release (magnetic snap + medium haptic) or **floats** clamped on-screen
(light haptic), and **minimizes** to a compact breathing **rec orb** (tap to re-expand every
control — the "never trap" rule). Dock/float/minimized state persists on `CaptureModel`
(`recorderLayout`) across pane switches + re-entry. The snap/dock decision is the pure
`RecorderSnap` (RuntimeCore), 9 `RecorderLayoutTests` (edge decisions, the margin boundary, edge
homes, the floating fallback, on-screen clamp, Codable round-trip).

**Deliverable 2 — free-place vs tack.** A plain drop below the stream places a bubble as a **loose
card** (no marked moment); a drop on the **tack target** (a dashed pill that appears only mid-drag
and lights up when the drag is over it) **tacks** it — a pushpin + tilt that calls `markMoment`
(HSM-8-03) so the on-device intelligence weights it. A loose card promotes later via "Tack as
moment" (`tackExisting`). The drop decision is the pure `BubblePlacement` (RuntimeCore), 5 tests.

**Deliverable 3 — resizable cards.** A corner-drag grip on each workspace card (`PinnedNote`, loose
or tacked) resizes its width; the text reflows within it; the width is clamped to a readable range
by the pure `CardSize.clampWidth` (RuntimeCore) and persists on the model. `CaptureModel.resizePin`.

**Deliverable 4 — one-tap tidy + undo.** A "Tidy" control re-flows the **loose** cards into a
centered grid below the streaming strip (tacked moments stay put — placed deliberately), with a
single **Undo** that restores the prior arrangement. The grid is the pure `WorkspaceTidy.layout`
(RuntimeCore); `CaptureModel.tidyLoose` saves the pre-tidy centers, `undoTidy` restores them.

- **Tests:** `swift test` **233/6/0** (+9 `RecorderLayoutTests`, +5 `BubblePlacementTests`, +5
  `CardLayoutTests` — clamp range, empty tidy, all-below-stream + on-screen, row wrap, row centering).
- **Built + shown:** app `xcodebuild … BUILD SUCCEEDED`; committed Simulator shots:
  [docked](./screenshots/recorder-docked-top.png) · [rec orb](./screenshots/recorder-minimized-orb.png) ·
  [free-place vs tack](./screenshots/recorder-freeplace-vs-tack.png) (footer "1 tacked · 1 placed") ·
  [lit tack target](./screenshots/recorder-tack-target.png) ·
  [resized card](./screenshots/recorder-resizable-card.png) (text reflowed + corner grip) ·
  [tidied grid](./screenshots/recorder-tidy-grid.png) (5 loose cards re-flowed, Undo·Tidy control).
- **Files:** `Sources/RuntimeCore/Capture/{RecorderLayout,BubblePlacement,CardLayout}.swift` + their
  tests; `App/MeetingCaptureApp.swift` (`FloatingRecorder`, `LiveBubbleView`, `PinnedNoteView` + resize
  grip, the canvas `tackTarget`/`tackZone`/`tidyControl`, `CaptureModel` layout/drop/resize/tidy).
- **Remaining:** stretch deliverables 5 (minimap) + 6 (windowed panes) — candidate HSM-14-14; and
  the device hardware-feel pass (drag latency, snap/tack/resize haptics, Pencil vs finger).

## Notes

- Sequencing: land **1 (dock/minimize)** and **2 (free-place vs tack)** first — they deliver the
  most "OS-like" feel for the least surface area. **6 (windowed panes)** is the biggest lever but
  also the biggest change; if it grows, split it into **HSM-14-14 (windowed panes + minimap)** so
  this story stays shippable.
- Keep it one-handed and glanceable — spatial freedom must not cost the press-record-and-go speed.
- Honors the standing UX bar ([[feedback_high_ui_standards]], [[feedback_deliver_mobile_craft_not_plumbing]]):
  shown via Simulator screenshots, hardware feel on the device.
