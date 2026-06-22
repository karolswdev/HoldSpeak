# HSM-14-11 — The live capture canvas (transcription bubbles + tack-to-board)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress (built + on the iPad + Simulator-proven; live-mic drag/pin verification on device is the remaining item)
- **Depends on:** HSM-8-01 (capture + live transcript), HSM-8-03 (marked moments), HSM-14-01 (Tactile Sheets)
- **Owner:** unassigned

## Vision (owner)

> "For taking notes during an active meeting — why can't we see some of those transcription
> bubbles pop here and there and maybe stick, and let us grab one with the magic pencil and
> tap it down somewhere? This was supposed to be a serious app."

The live transcript was a wall of text plumbed into a box. That is not an experience. The
meeting should feel **alive and hand-driven**: words arrive as objects you can touch, and the
Apple Pencil is the instrument that captures what matters.

## What shipped

The old `transcriptCard` (a `Text` in a `ScrollView`) is **replaced** by `LiveCaptureCanvas`:

- **Bubbles stream.** Each finished utterance (sentence) floats up as a tappable, draggable
  bubble with a grab-handle. `CaptureModel.ingest(_:)` splits the running transcript into
  finished sentences (one bubble each, capped to the last 5 so it stays glanceable) + the
  trailing fragment.
- **A live caption breathes.** The words still being transcribed pulse beneath the bubbles
  (`LiveCaption`, animated equalizer bars) — the "it's listening right now" signal.
- **Grab + tack.** Press a bubble (finger or Pencil) → it lifts (shadow + scale + haptic).
  Drag it below the fold onto the **pin board** and release → it tacks down with a brass
  pushpin at a slight tilt and a landing bounce (`PinnedNoteView`). Release high → it snaps
  back.
- **Pinning MEANS something.** A tacked bubble is also a **marked moment** (HSM-8-03):
  `pin(...)` calls `linker.markMoment(at:label:)`, so the on-device intelligence (InkEmphasis /
  MIR) **weights what you cared about** at generation time. The tactile gesture and the
  intelligence are one flow, not two features.
- **Pinned notes are live objects** — drag to reposition (clamped to the board), tap the
  pushpin to unpin.
- **Transcript → note canvas.** Press-and-hold any bubble OR a tacked moment → a context menu
  ("Add to notes" / "Copy" / "Unpin") — choosing **Add to notes** pulls the snippet onto the
  actual PencilKit note canvas as a quoted, draggable `NoteCard` (above the ink, so you ink
  around it), and the UI jumps to the Notes pane so you land where it arrived. Cards persist
  per meeting (`NotebookModel.cards`, JSON in the container) and drag/remove freely. This is
  the owner's ask: "pull it into the actual note-taking canvas, or provide it as an option if
  you hold-press that specific part of the transcript."

## Live dynamism + the floating recorder (2026-06-21, owner steer)

Owner: transcription felt slow/static, and the meeting was "contained to big-ass pages" — it
should feel "nearly like an operating system."

- **Root-caused the slow transcription:** `WhisperKitTranscriber.transcribe()` constructed a
  **fresh `WhisperKit(...)` on every tick**, reloading the CoreML model from disk (seconds)
  each time — so the live transcript compounded into a frozen feel. Now the model is **cached**
  (lock-guarded static; WhisperKit isn't Sendable so it's created+used within the nonisolated
  method, never crossing isolation) and the tick cadence dropped 3s → **1.2s**.
- **Audio-reactive control plane:** `MeetingCapture` now exposes a smoothed `inputLevel` (RMS of
  each captured buffer, ~12×/s); `CaptureModel` polls it at 20 Hz; `MicWaveform` renders bars
  that **react to the mic the instant sound arrives** — no transcription round-trip. The canvas
  empty state and the recorder both use it.
- **The floating recorder (OS-like):** while recording, the big Record button + segmented bar
  **collapse into one compact, frosted, DRAGGABLE capsule** (`FloatingRecorder`): stop · live
  elapsed timer · the audio-reactive waveform · mark-this-moment · transcript/notes toggle. Drag
  it anywhere; the canvas goes **full-bleed**. The chrome floats and moves out of the way.

## One free-form desktop (not two big boxes)

Owner: "why must we be contained to those big-ass pages… move things around… like an operating
system." The canvas was a top "stream column" + a bottom dashed "board." It's now **one
continuous spatial desktop**: a subtle dot-grid surface (`DesktopGrid`), utterances stream from
the top strip, and you **fling any bubble anywhere on the whole surface to tack it** (drop below
a small `pinFloor`, not into a tray). Pinned notes live wherever you drop them and drag freely; a
small frosted "N tacked" chip replaces the big board label. Combined with the draggable
`FloatingRecorder`, the meeting reads as an arrangeable workspace, not stacked pages.

## Promote a note → a real artifact

A note card on the canvas now **offers** an action: a visible **Promote** pill (smart-guesses
the type from the text) + a long-press submenu for an explicit type. Promoting writes a
`needs_review` artifact (`pluginId = holdspeak.mobile.note`, confidence 1.0) into the meeting's
store, so the hand-note **joins the model's artifacts in the intelligence pane** — the loop
closes both ways. Cards always render now (the page-0 gate that could hide them on reopen was
removed).

## Craft assets (Pixellab)

Three bespoke pixel-art assets were generated and **bundled offline** (no network at runtime),
each with an SF-Symbol fallback so the build never depends on them (`pixelAsset(_:size:fallback:)`):

- `qlippy.png` — the paperclip mascot (Clippy homage), the "listening" presence in the empty state.
- `pushpin.png` — the brass pushpin that holds each tacked moment.
- `waveorb.png` — a concentric amber waveform orb (recording heartbeat).

## Acceptance criteria

- [x] **Bubbles replace the box** — finished utterances stream as draggable bubbles; the live
      fragment pulses as a caption. Built + Simulator-proven (committed screenshot).
- [x] **Tack-to-board** — a bubble drags onto the board and pins with a pushpin + tilt + bounce;
      pinned notes reposition and unpin. Simulator-proven.
- [x] **Pinning feeds the intelligence** — `pin(...)` marks the moment (HSM-8-03 link), so MIR
      weights it. Wired through `CaptureModel`.
- [x] **Bespoke assets, bundled offline** — Qlippy + pushpin + waveform orb, with symbol fallbacks.
- [x] **Transcript → note canvas** — long-press a bubble/tacked moment → "Add to notes" pulls
      it onto the PencilKit canvas as a draggable quoted card (above the ink), jumping to the
      Notes pane. Cards persist per meeting + drag/remove. Built + Simulator-proven (committed
      screenshot `transcript-to-notes.png`).
- [x] **Promote a note → artifact** — a card's "Promote" pill (or long-press type menu) writes a
      `needs_review` artifact into the meeting; it appears in the intelligence pane. Built + on iPad.
- [x] **Live dynamism** — WhisperKit model cached (no per-tick reload) + 1.2s cadence; mic-reactive
      `MicWaveform` from `MeetingCapture.inputLevel`; the recording controls collapse into a
      draggable `FloatingRecorder` with the canvas full-bleed. Built + Simulator-proven.
- [ ] **Live-mic verification on device** — record a real meeting, watch bubbles pop, tack one
      with the Pencil, pull a moment into the notes canvas, confirm the marked moment shifts the
      generated artifacts. (App is on the iPad Air M4; owner verification pending.)

## Evidence

`apple/App/MeetingCaptureApp.swift` (`LiveCaptureCanvas`, `LiveBubbleView`, `LiveCaption`,
`PinnedNoteView`, `CaptureModel.ingest/pin/unpin/movePin`) + `apple/App/{qlippy,pushpin,waveorb}.png`
bundled via `apple/scripts/gen-meeting-capture.rb`. Simulator screenshot: the canvas in flight
(three live bubbles + live caption + two tacked moments under pushpins). Device build installed
+ launched on the iPad Air M4.

## Notes

- Sentence-count diffing is resilient to WhisperKit's windowed state (which mostly appends);
  a rare revision that shrinks the count just leaves prior bubbles in place — never re-bubbles.
- The Simulator seed (`seedDemo`, `HS_DEMO=1`) is `#if targetEnvironment(simulator)` only — it
  stages demo bubbles/notes for design screenshots and is never compiled into the device build.
