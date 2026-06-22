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
- [ ] **Live-mic verification on device** — record a real meeting, watch bubbles pop, tack one
      with the Pencil, confirm the marked moment shifts the generated artifacts. (App is on the
      iPad Air M4; owner verification pending.)

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
