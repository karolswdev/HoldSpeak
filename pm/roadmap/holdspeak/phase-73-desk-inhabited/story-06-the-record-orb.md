# HS-73-06 — The Record orb (the live verb)

- **Status:** done
- **Priority:** HIGH (the desk's center of gravity; without it the world is a museum)
- **Depends on:** HS-73-02 (coordinates with HS-72-08; does not block on it)

## Goal

The product's primary verb lives on the front door. A warm Record orb sits
bottom-center in the world (iPad parity: the `DioAmbientRecorder` entry,
`DeskDioramaStage.swift:~1915`); tapping it starts the **hub's** recorder;
while live, the orb pulses with the runtime; on stop, the finished meeting
**materializes as an object** in front of the user.

## Scope

- **In:** the `RecordOrb` component; start/stop against the existing hub
  routes; live state from the existing event stream; the materialize beat;
  external-state honesty; the live meeting's pull-out content (minimal).
- **Out:** browser-microphone capture (decided: the orb drives the hub
  recorder — no new plumbing, no new egress; any `getUserMedia` in a diff
  is a stop signal); a full live-transcript canvas on the desk (the live
  meeting's pull-out shows status + a `live` chip whose "Open full" goes
  to `/live`); intent controls/bookmarks (stay on `/live`).

## Tasks

- [ ] `RecordOrb`: bottom-center, warm accent, idle glow; recording =
      `motion` pulse + elapsed time; the same orb is the stop control.
      Reduced-motion: static ring.
- [ ] Start/stop: reuse `/live`'s calls **verbatim** —
      `POST /api/meeting/start`, `POST /api/meeting/stop`
      (`holdspeak/web/routes/core.py`). Read `dashboard-app.js`'s payloads
      and copy them exactly; do not invent parameters.
- [ ] State honesty: initial state from `GET /api/state`; live updates via
      the `useRuntimeBus` hook (the `hs-*` DOM events `runtime-bus.js`
      already dispatches — stable across HS-72-08). If a meeting is
      already live (started from `/live`, the CLI, or the iPad), the orb
      shows recording with a `live elsewhere` whisper and its tap becomes
      stop — **never a second start**.
- [ ] The shell `Waveform` widget (fed by `audio_level` frames) renders
      above the stage while recording — verify z-index and that it doesn't
      fight the orb visually.
- [ ] On stop: refresh meetings, identify the new id, materialize the
      object near the orb with the NEW beat; its pull-out (HS-73-04) shows
      the meeting with whatever intel status the normal queue reports — no
      invented states.
- [ ] Egress: recording is hub-local; the badge does not change; no copy
      narrates this.

## Proof required

A capture: idle → tap → pulsing + elapsed (a real-metal run on the Mac's
mic is the preferred evidence per the standing rule) → stop → the meeting
object materializes → its pull-out opens. The external-state case proven:
start from `/live` in another tab; the desk orb reflects it and cannot
double-start. Route pre-flight + full suite + `npm run build` green.

## Done

Shipped. The orb sits bottom-center driving the HUB's recorder with
/live's exact calls (never a browser mic); state is honest by construction
— seeded and kept live by the ONE runtime bus, so a meeting started
anywhere flips the orb with the `live elsewhere` whisper and its tap can
only stop (a second start is structurally unreachable). Stop materializes
the finished meeting with the NEW beat in front of you. Proofs: real
server broadcasts drove the external-truth case and the settle; the
materialize beat asserted with the fresh meeting wearing is-new; two
screenshots; zero page errors; manifest + pre-flight + live-bus 10
passed (one socket per page holds); full suite 3066 passed, 37 skipped. The mic-in-hand
lifecycle is the owner's real-metal leg of the closeout walk, per the
story's own preference. See
[evidence-story-06.md](./evidence-story-06.md).
