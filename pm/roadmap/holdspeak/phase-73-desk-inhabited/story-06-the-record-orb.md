# HS-73-06 — The Record orb (the live verb)

- **Status:** todo
- **Priority:** HIGH (the desk's center of gravity; without it the world is a museum)
- **Depends on:** HS-73-01 (coordinates with HS-72-08, does not block on it)

## Goal

The product's primary verb lives in the world. A warm Record orb sits
bottom-center on the web desk (iPad parity: the `DioAmbientRecorder` entry,
`DeskDioramaStage.swift:~1915`); tapping it starts the **hub's** recorder;
while live, the orb pulses with the runtime; on stop, the finished meeting
**materializes as an object on the stage** in front of the user. Today the
web desk can do nothing live — recording is on `/live`, a different door.

## Scope

- **In:** the orb; start/stop against the existing hub routes; live state
  from the existing event stream; the materialize beat; external-state
  honesty.
- **Out:** browser-microphone capture (phase decision: the orb drives the
  hub recorder via the `/live` pattern — no new plumbing, no new egress);
  in-world live transcript rendering (the pull-out of the LIVE meeting may
  show a "live" chip linking `/live` as its Open-full; a full live canvas
  on the desk is future work); intent controls/bookmarks (stay on `/live`).

## Tasks

- [ ] `web/src/scripts/desk/recorder.js` + `components/desk/DeskOrb.astro`
      (factory-rendered, `is:global`): the orb bottom-center, warm accent,
      idle glow; recording state = pulse + elapsed time, stop affordance on
      the same orb. Reduced-motion: static ring instead of pulse.
- [ ] Start/stop: reuse `/live`'s calls **verbatim** —
      `POST /api/meeting/start`, `POST /api/meeting/stop`
      (`holdspeak/web/routes/core.py`). Do not invent parameters; read
      `dashboard-app.js`'s payloads and copy them.
- [ ] State honesty: on load, derive orb state from `GET /api/state`; while
      mounted, subscribe to the `hs-*` DOM events `runtime-bus.js` already
      dispatches on every page (this keeps the story independent of
      HS-72-08 — if the bus refactor lands first, the events are
      unchanged). If a meeting is already live (started from `/live`, the
      CLI, or the iPad), the orb shows recording with a `live elsewhere`
      whisper and its tap becomes stop — never a second start (the
      double-start stop signal in the phase risks table).
- [ ] The waveform: the shell `Waveform` widget (Phase 69, fed by
      `audio_level` frames) is already mounted by AppLayout — verify it
      renders above the desk stage while recording (z-index vs
      `.desk-stage`) and does not fight the orb visually.
- [ ] On stop: refresh meetings (`loadMeetings`, `desk-app.js:488`), find
      the new id, `markNew(id)` + `hs-materialize` — the meeting lands as
      an object near the orb, NEW beat playing. Its pull-out (HS-73-03)
      opens on tap; intel arrives later via the normal queue (the object's
      card shows the existing intel status it already gets from the
      meetings payload — no new states invented).
- [ ] Egress: recording is hub-local — the egress badge does not change;
      assert no new copy narrates this (the badge IS the answer).

## Proof required

A capture: idle orb → tap → pulsing + elapsed (a real or seeded hub
recording; a real-metal run on the Mac's mic is the preferred evidence per
the real-metal rule) → stop → the meeting object materializes with the NEW
beat → its pull-out opens. The external-state case proven: start from
`/live` in another tab, the desk orb reflects it and cannot double-start.
Route pre-flight + full suite + `npm run build` green.
