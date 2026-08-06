# HS-119-01 — Click-to-toggle mic

- **Project:** holdspeak
- **Phase:** 119
- **Status:** backlog
- **Depends on:** HS-119-02 (regression sweep lands on a stable baseline first)
- **Unblocks:** HS-119-04 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The browser mic shipped in Phase 118 as hold-to-talk: press and hold a
small button, speak, release. This works for a two-word correction. It
fails for anything longer. The user's hand cramps on mobile, their
attention splits between holding and speaking, and there is no visual
feedback that the system is hearing them — no waveform, no streaming
text, no indication that Whisper is processing.

The desktop hotkey path is press-to-start, press-to-stop. It works
because the hotkey is a toggle. The browser mic deserves the same
interaction model, adapted for a visual surface that can show streaming
feedback.

When this ships, clicking the MicButton starts capture. The button
pulses to show it is listening. A waveform or level meter shows audio
activity. As Whisper processes chunks, partial transcription streams
into the target field — the user sees their words appear as they speak,
with progressive corrections as Whisper refines. Clicking again, or
pressing Enter or Escape, stops capture and finalizes the text. The
hold-to-talk hotkey path (system-level, outside the browser) stays
unchanged.

Every surface that uses MicButton — inlet, AskPanel, note editor,
rework composer, any future input — inherits the toggle behavior
automatically. No surface is special-cased.

**Articles served:** IV (voice as input — every text input can be
spoken into; the quality of the interaction should not depend on
holding a button; one mic authority at a time), VIII (native-grade
craft — streaming feedback is the minimum bar for a voice-first
surface; 60fps interaction budget on the waveform), II (everything
is a primitive — MicButton is a shared OS affordance, not a
per-feature widget; every surface inherits automatically),
VI (honest by construction — the streaming text shows what Whisper
actually heard, corrections arrive visibly, not silently).

## The MicButton state machine

```
          click              click / Enter / Escape
  IDLE ──────────→ LISTENING ──────────────────────→ IDLE
   │                   │
   │                   ├── claimAudioFloor()
   │                   ├── start MediaStream capture
   │                   ├── begin chunked streaming to server
   │                   ├── render pulse + waveform
   │                   └── stream partial text into target field
   │
   └── releaseAudioFloor()
       stop MediaStream
       finalize text
```

The existing `beginHold()` / `endHold()` pattern becomes
`toggleMic()` internally. The floor arbitration contract
(`audioFloor.ts`) is unchanged — `claimAudioFloor()` on start,
`releaseAudioFloor()` on stop. Only one mic owns the floor at
a time.

## Deliverables

1. **MicButton toggle state machine.** Replace the hold-to-talk
   interaction with a click-to-toggle:

   - `onClick`: if idle, transition to listening. If listening,
     transition to idle.
   - `onKeyDown(Enter)` or `onKeyDown(Escape)` while listening:
     transition to idle (finalize).
   - The hold-to-talk gesture (mousedown/mouseup) is removed from
     the browser MicButton. The system-level hotkey path is
     unmodified.

   The state machine lives in a `useMicToggle()` hook (or
   equivalent) that any surface can consume. The MicButton
   component uses this hook.

2. **Visual feedback: pulse + waveform.** While listening:

   - The MicButton icon pulses (CSS animation, compositor-only,
     no layout thrash).
   - A waveform or level meter visualizes audio input. This can
     be a simple bar-graph level meter driven by an
     `AnalyserNode` from the Web Audio API — it does not need
     to be a full waveform. The visualization sits adjacent to
     or inside the MicButton, sized appropriately for the
     surface (inlet, AskPanel, etc.).
   - 60fps budget. The visualization uses `requestAnimationFrame`
     and reads from the `AnalyserNode` — no reflows, no React
     re-renders per frame.

3. **Streaming transcription endpoint.** Extend the server to
   accept chunked audio and return partial transcription results:

   - Option A (WebSocket): a new WebSocket route
     `/ws/dictation/stream` that accepts audio chunks and sends
     back partial transcription events
     (`{type: "partial", text: "..."}`,
      `{type: "final", text: "..."}`).
   - Option B (SSE): `POST /api/dictation/stream` that accepts
     audio as a streaming upload and returns SSE events with
     partial results.

   Choose whichever is simpler given the existing WebSocket
   infrastructure. The endpoint calls Whisper on each chunk and
   returns progressive results. When `pipeline: true` (from
   HS-118-08), the final result passes through the full dictation
   pipeline before the `final` event.

4. **micSession lifecycle.** The streaming capture is a long-running
   session, not a single request/response:

   - `startSession()`: claims the audio floor, begins
     MediaStream capture, opens the streaming connection to the
     server.
   - Audio chunks are sent at a regular interval (e.g. every
     500ms or on voice-activity boundaries).
   - `stopSession()`: sends a finalize signal, waits for the
     final transcription, releases the floor, closes the
     connection.
   - If the WebSocket/SSE connection drops during a session, the
     MicButton transitions to idle and shows an error indicator
     (not a modal — Article VII).

5. **Progressive text insertion.** As partial transcription events
   arrive, the target field is updated:

   - Partial results replace the previous partial in the field.
     The user sees text being refined in place.
   - The final result replaces the last partial and becomes the
     committed text.
   - If the user is typing while the mic is active, the mic text
     is appended at the cursor position, not replacing user-typed
     content.
   - Corrections from the dictation pipeline (when `pipeline:
     true`) arrive in the final event — partials are raw Whisper
     output, the final is pipeline-processed.

6. **Automatic inheritance.** Every surface that renders a
   MicButton inherits the toggle behavior without code changes.
   Verify by testing on: inlet, AskPanel, note editor, rework
   composer. If any surface has a custom MicButton integration
   that bypasses the shared component, unify it.

## What NOT to do

- Do NOT remove the system-level hotkey path. It stays as
  press-to-start, press-to-stop with sounddevice capture.
- Do NOT add a settings toggle between hold-to-talk and
  click-to-toggle for the browser mic. Click-to-toggle is the
  behavior. Users do not choose interaction tiers.
- Do NOT render the waveform as a canvas that repaints the
  entire surface. Use compositor-only animation (transforms,
  opacity) or a small isolated canvas.
- Do NOT block the UI while waiting for the final transcription.
  The mic transitions to idle immediately on click; the final
  text arrives asynchronously and replaces the last partial.

## Test plan

- `npx vitest run` — existing frontend tests pass.
- New test: MicButton click toggles between idle and listening
  states.
- New test: second click (or Enter/Escape) stops capture and
  finalizes.
- New test: `useMicToggle()` hook claims audio floor on start,
  releases on stop.
- New test: floor contention — mic active, second mic attempted,
  second is refused.
- New test: partial transcription events update the target field
  progressively.
- New test: final transcription event replaces the last partial.
- New test: connection drop during session transitions to idle
  with error indicator.
- `uv run pytest -q tests/ -k dictation` — server-side streaming
  endpoint tests:
  - Chunked audio accepted, partial events returned.
  - Final event passes through pipeline when `pipeline=true`.
- Visual at 1440: click mic in inlet, speak a sentence, verify
  streaming text appears, click again, verify finalized text.
- Visual at 393: same flow on mobile viewport — button is
  tappable, waveform is visible, text streams.
- Video: full click-to-toggle cycle with streaming transcription
  visible.
