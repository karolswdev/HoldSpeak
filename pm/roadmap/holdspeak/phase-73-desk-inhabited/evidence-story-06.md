# Evidence — HS-73-06 — The Record orb (the live verb)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **The product's primary verb lives on the front door.** `RecordOrb`
  sits bottom-center (the `DioAmbientRecorder` position): warm idle glow;
  recording = pulse + tabular elapsed + the core squares into a stop
  glyph; reduced-motion swaps the pulse for a static ring.
- **It drives the HUB's recorder** with `/live`'s exact calls
  (`POST /api/meeting/start` / `stop`, `accept: application/json`,
  no invented parameters) — **never a browser microphone** (`getUserMedia`
  absent from the tree by the phase's standing stop signal).
- **State is honest by construction**: seeded via the one runtime bus's
  `seedState()` and kept live by subscribing to `runtime_activity`
  frames (the island imports `runtime-bus.js` directly — the same
  singleton the shell widgets ride, one socket per page preserved). A
  meeting started ANYWHERE (the `/live` page, the CLI, the iPad) flips
  the orb to recording with the `live elsewhere` whisper, and its tap is
  a STOP — a second start is structurally unreachable (the click handler
  only starts from `idle`).
- **The finished meeting materializes**: stop → refresh → the meeting id
  that wasn't there before wears the NEW beat in front of you; its
  pull-out (HS-73-04) opens on tap. No invented intel states — the object
  shows whatever the normal queue reports.
- Egress unchanged: recording is hub-local; no copy narrates it (the
  badge is the answer).

## Verification artifacts (Playwright + real server broadcasts)

- Arrival: the orb idles bottom-center.
- **The external-truth case** (the story's stop signal): a real
  `server.broadcast("runtime_activity", {state: "meeting_live"})` flipped
  the orb to recording with the whisper (`06-orb-live-elsewhere.png`);
  an idle frame settled it back.
- **The materialize beat**: live frame + a new meeting row + tapping the
  orb (the stop path) → "Just recorded" appeared wearing `is-new`
  (`06-meeting-materialized.png`). The full mic-in-hand lifecycle is the
  owner's real-metal pass (the story's preferred evidence), recorded as
  part of the closeout walk.
- Zero page errors. Honest note: the shell Waveform's live reaction
  could not be meaningfully asserted headless (it needs real
  `audio_level` frames from a recording runtime); its mount on `/` is by
  AppLayout's immersive path and its behavior is unchanged from Phase 69.
- Build 18 pages; manifest + pre-flight + the live-bus proofs **10
  passed** (one socket per page HOLDS with the island subscribing — the
  bus singleton shared, as designed); full suite **3066 passed, 37
  skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] The orb bottom-center; pulse + elapsed; stop on the same orb;
      reduced-motion safe.
- [x] `/live`'s calls verbatim; no `getUserMedia` anywhere.
- [x] External state honestly reflected; double-start structurally
      unreachable.
- [x] The finished meeting materializes with the beat.

## Deviations from plan

- The recording-lifecycle proof simulates the runtime (a live frame + a
  new meeting row) because the test harness has no microphone runtime;
  the orb's two API calls are byte-copies of `/live`'s, and the
  mic-in-hand run is explicitly the owner's real-metal leg of the
  closeout walk.

## Follow-ups

- HS-73-07 (the rail) is the last verb before the cutover.
