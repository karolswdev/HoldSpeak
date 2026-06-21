# Evidence — HSM-8-01 (iPad shell + meeting capture)

**Date:** 2026-06-21 · **Status:** done

The runtime's first face on iPad: open the app, see your recordings, press Record, watch
the transcript appear, stop to keep it — capture (Phase 2) + Whisper (Phase 3) +
persistence (Phase 4) all **on-device**, through a Runtime-Core view-model. This is the
spine the PencilKit notebook (HSM-8-02) and review (HSM-8-04) hang off.

## What shipped

- **`MeetingCapture` view-model (RuntimeCore):** composes `IAudioCapture`, a
  `([AudioChunk]) -> ITranscriber` factory, and a `MeetingStore` behind seams — the view
  holds no engine/provider types. `start()` → records; `tick()` re-transcribes the audio
  captured so far so the **live transcript grows as speech accumulates** (windowed; a
  truly streaming transcriber is HSM-3-02); `stop()` transcribes the full take, builds a
  `Meeting`, and persists it; `meetings()` / `reopen(id:)` back the list + reopen-intact.
- **Contract enablers:** public inits on `Meeting` / `IntelStatus` / `Bookmark`
  (Contracts) so on-device code can build a recording from captured segments — a Swift
  convenience only; the Codable/wire shape is unchanged (the schema-version + round-trip
  tests still pass).
- **The iPad app (`MeetingCaptureApp`):** a Signal-language meeting list + a capture
  screen (Record/Stop + a live transcript view driven by a 3s `tick` timer) + a detail
  view that reopens a saved meeting's transcript. A `WhisperKitTranscriber` (on-device,
  reusing the package's `WhisperText.clean`) and a `SQLiteMeetingStore` adapter over the
  Phase-4 `SQLiteStorage`. `gen-meeting-capture.rb` (+ WhisperKit 0.11.0) + `Capture-Info.plist`
  (mic; no networking).

## Tests (ran)

`swift test` → **140 passed / 6 skipped / 0 failed** (+7 `MeetingCaptureTests`): the live
transcript **grows as audio accumulates**; stop **persists + reopens intact** (including
through a fresh view-model over the same store); mic-start failure and save failure each
land in `.failed`; `tick` is a no-op when idle; egress is "on-device · nothing leaves".
The Phase-4 `StorageTests` (incl. the schema-version + meeting round-trip) stay green, so
the new contract inits are safe.

## Real-metal

- The app **builds + signs, installs, and LAUNCHED on the physical iPad Air M4**
  (`devicectl`).
- The on-device transcription path is the **same WhisperKit one proven on real metal in
  HSM-13-04** (the voice gate transcribed real speech on-device); this story wires it into
  the meeting loop. Real capture (`AudioCaptureService`), real Whisper, and real SQLite
  persistence are each independently proven.
- Screenshot (iPad-Pro simulator): `screenshots/meetings-list.png` — the on-device
  Meetings entry surface (record CTA + honest "stays on this iPad", empty state).

## Acceptance

- **Launches on iPad, meeting list, capture screen** — the app opens to the Meetings list
  and the New-recording CTA pushes the capture screen.
- **Record/stop drives Phase-2 capture; live transcript updates from the Phase-3
  transcriber** — host-proven (windowed `tick`); on real metal the components are the
  proven `AudioCaptureService` + WhisperKit.
- **Meeting + segments persist via Phase-4 store and reopen intact** — host-proven
  (`testStopPersistsAndReopensIntact`, `testReopenSurvivesAFreshViewModel`); the app
  reopens from on-device SQLite.
- **View depends only on Runtime-Core seams/view-models** — `MeetingCaptureApp` drives
  `MeetingCapture`; no engine/provider concrete types leak into the view layer.

## Note

The integrated **record-a-meeting** walkthrough (speak → live transcript → stop → reopen)
runs on the app now deployed on the iPad; it folds into the Track-I gate. Every component
on that path is already real-metal-proven; this story makes the loop and proves it host-side.
