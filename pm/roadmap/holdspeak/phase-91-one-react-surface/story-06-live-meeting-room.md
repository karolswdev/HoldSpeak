# HS-91-06 — The live meeting room in React

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** HS-91-01, HS-91-02
- **Unblocks:** HS-91-09
- **Owner:** unassigned

## Problem

The live room combines recording state, transcript, waveform, bookmarks,
intent routing, plugin jobs, queue state and WebSocket events in a large Alpine
page. React must make those concurrent states understandable without changing
the meeting runtime contract.

## Scope

- In: React `/live`; recording lifecycle, transcript and waveform, bookmarks,
  metadata, routing controls/timeline, plugin queue, meeting intelligence,
  connection and trust states; one runtime-bus subscription model.
- Out: recorder/backend pipeline redesign; new meeting intelligence features.

## Acceptance criteria

- [x] Recording/start/stop/finalize, bookmark, metadata, routing and queue verbs
      match the parity ledger and existing APIs.
- [x] WebSocket ownership is singular; reconnect/stale/offline states are typed
      and visible; component unmount removes listeners.
- [x] Transcript updates preserve reading/focus position and do not rerender the
      whole room unnecessarily; performance evidence covers a long transcript.
- [x] Trust and egress badges remain hub-reported, never inferred client-side.
- [x] Existing live/intent/plugin integration suites pass and old page scripts
      for this cohort are removed.

## Test plan

- Unit: live state reducer, frame normalization and reconnect tests.
- Integration: browser fake-frame rig plus existing meeting/intent pytest.
- Manual / device: real microphone meeting from start through archive, including
  a bookmark and an honest model-unavailable path.

## Notes / open questions

The Presence HUD can consume the same typed frame normalizers but migrates with
the support surfaces in HS-91-08.
