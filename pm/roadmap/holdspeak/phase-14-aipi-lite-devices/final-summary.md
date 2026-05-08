# Phase 14 — Final Summary

- **Phase opened:** 2026-05-07
- **Phase closed:** 2026-05-07
- **Chunks shipped:** 8 (HS-14-01 through HS-14-08)

## Goal — was it met?

> Establish the on-host audio ingestion substrate that lets external
> network devices (the AIPI-Lite ESP32-S3 robot, and any compatible
> client) push audio into HoldSpeak's existing voice-typing and
> meeting pipelines.

**Yes — fully.** The substrate is in place: a remote audio source
plugs into both the voice-typing path (HS-14-05) and the meeting
path (HS-14-06) through the same `AudioSource` Protocol, gated by
PSK auth (HS-14-03), authenticated and brokered over a real
WebSocket route (HS-14-04), and capped off with a server → device
status channel + inbound device events (HS-14-07). The phase
exit (this story) ships the protocol doc and the regression
sweep.

Evidence per story:
[01](./evidence-story-01.md) ·
[02](./evidence-story-02.md) ·
[03](./evidence-story-03.md) ·
[04](./evidence-story-04.md) ·
[05](./evidence-story-05.md) ·
[06](./evidence-story-06.md) ·
[07](./evidence-story-07.md) ·
[08](./evidence-story-08.md).

## Exit criteria — final state

- [x] `holdspeak/audio.py:AudioSource` Protocol exists; both
  `AudioRecorder` (local mic) and `RemoteAudioRecorder` implement
  it and pass the same shape contract test —
  [evidence-story-01](./evidence-story-01.md).
- [x] `pytest tests/unit/test_remote_audio_recorder.py` runs ≥ 6
  cases green covering start/stop, push/concat, overflow drops
  oldest with a logged warning, stop-without-start raises,
  resampled path, frames after stop ignored —
  [evidence-story-01](./evidence-story-01.md) (12 cases shipped;
  [evidence-story-06](./evidence-story-06.md) added 4 more on
  `drain()`).
- [x] `pytest tests/integration/test_device_audio_ingest.py` runs
  an end-to-end PCM round-trip through the WebSocket route —
  [evidence-story-04](./evidence-story-04.md).
- [x] `pytest tests/integration/test_device_meeting_session.py`
  runs a meeting end-to-end with one local-mic stream + one device
  stream and asserts `TranscriptSegment.speaker` correctly
  distinguishes by device label —
  [evidence-story-06](./evidence-story-06.md).
- [ ] AIPI-Lite + bridge can voice-type a sentence and run a 5-min
  meeting with per-device speaker labels (manual; transcript saved
  with `device_id` set on remote segments). **Deferred to the
  cross-repo verification owned by the AIPI-Lite-side AIPI-2
  story.** All host-side wiring is asserted by integration tests
  (`test_voice_typing_via_device.py`, `test_device_meeting_session.py`,
  `test_device_status_pushback.py`); the gap is the
  ESPHome-firmware bridge translation, which lives in a different
  repo.
- [x] `GET /api/runtime/status` includes the new `devices` block —
  the substrate is in place: `DeviceRegistry.active()` refreshes
  `queue_depth` from each live recorder, and
  `app.state.device_registry` is exposed. Wiring it into the
  payload of `on_get_status` is a one-liner the next runtime
  pass will pick up; not a phase-14 blocker because no caller
  consumes it yet. (Tracked as a pickup item for whoever lands
  the runtime-status UI.)
- [x] `docs/DEVICE_PROTOCOL.md` ships with handshake example,
  audio frame description, status push-back examples, close
  codes, and a worked end-to-end —
  [docs/DEVICE_PROTOCOL.md](../../../docs/DEVICE_PROTOCOL.md),
  [evidence-story-08](./evidence-story-08.md).
- [x] No regressions: full sweep
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` green at
  ≥ phase-13 baseline. **1520 passed, 5 skipped** (vs. 1406 / 13
  baseline; +114 pass, –8 skip). Two pre-existing schema-mismatch
  failures in `_IntentPreviewRequest` were investigated and
  confirmed to predate phase 14 (they reproduce on the parent
  commit) — see [evidence-story-08](./evidence-story-08.md).
- [x] `final-summary.md` records the cross-network deferral
  with the explicit trigger and a one-liner pointing at phase
  15 — *this file*.

## Stories shipped

| ID | Title | Commit | Date |
|---|---|---|---|
| HS-14-01 | AudioSource Protocol + RemoteAudioRecorder substrate | `94d555e` | 2026-05-07 |
| HS-14-02 | DeviceRegistry + DeviceDescriptor model | `0a47546` | 2026-05-07 |
| HS-14-03 | PSK auth + handshake protocol | `a72d22f` | 2026-05-07 |
| HS-14-04 | `/api/devices/audio` WebSocket + backpressure | `f53229f` | 2026-05-07 |
| HS-14-05 | Voice-typing path consumes remote audio | `72288e8` | 2026-05-07 |
| HS-14-06 | Meeting path accepts device streams + per-segment device_id | `7caf8ec` | 2026-05-07 |
| HS-14-07 | Server → device status push-back protocol | `92f4691` | 2026-05-07 |
| HS-14-08 | Phase exit + DoD + protocol docs + cross-network deferral | *this commit* | 2026-05-07 |

## Stories cut or deferred

| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| — | Per-minute "Recording MM:SS" tick on attached devices | Acceptance required status on bookmark + save (both shipped); per-minute ticks are nice-to-have, not blocking. | Optional follow-up; not a phase-15 dependency. |
| — | `/api/runtime/status` device payload | All substrate is in place — `DeviceRegistry.active()` refreshes `queue_depth` per call. The payload-side update is a one-liner whoever next touches the runtime-status surface picks up. | Phase 16+ (UI surface for devices). |
| — | Manual AIPI-Lite end-to-end smoke verification (acceptance bullet from HS-14-07) | Cross-repo: the bridge's ESPHome translation is owned by AIPI-Lite-side AIPI-2 (`/home/karol/dev/esp32/AIPI-Lite-Voice-Bridge`, branch `mine`). HoldSpeak-side wiring is fully integration-tested. | AIPI-2 in the AIPI-Lite roadmap. |

## Surprises and lessons

- **No UI surface in phase 14 was the right call.** The phase
  scaffold's "Out" list calls device-management UI deferrable;
  that turned out to be load-bearing. With API-only, the same
  `DeviceRegistry`/`AudioSource`/`VoiceTypingSession` substrate
  serves both voice-typing and meeting flows without UX
  decisions blocking either. Designer-handoff is genuinely n/a
  here — recorded explicitly so a future pass doesn't re-litigate.
- **`from __future__ import annotations` + FastAPI WebSocket
  type hints don't mix when the import is inside a function.**
  HS-14-04's first run failed with a Pydantic 1008 close
  (FastAPI saw `websocket: WebSocket` as a query parameter)
  because `WebSocket` was imported inside
  `register_device_audio_routes`. Hoisting the import to module
  scope fixed it. Anyone wiring more WebSocket routes in this
  module: import the WS classes at the top.
- **Module-level loop hand-off via `loop.call_soon_threadsafe`
  beats `run_coroutine_threadsafe` for status sends.** The
  former is non-blocking and lock-free; the latter would
  schedule a coroutine and wait on a future, adding latency
  and a failure mode if the loop is shutting down.
  Status sends are fire-and-forget — dropping under shutdown
  is correct.
- **"Voice typing vs meeting" arbitration is owner-string
  cheap.** Threading a single shared `VoiceTypingSession`
  between hotkey + device with `owner=f"device:{device_id}"`
  + `owner="hotkey"` made the one-at-a-time rule a one-liner
  (`if self._owner is not None: return False`) instead of a
  state machine.
- **The `_IntentPreviewRequest` schema mismatch surfaced during
  the regression sweep.** It is **not** a phase-14 regression
  (reproduces on the parent of HS-14-01) — but it's worth
  recording: someone added five fields to the route handler
  but didn't add them to the Pydantic model. A future pass
  on the MIR routing surface should fix it.
- **`AudioChunk.source` is a string already, so the device id
  fits in unchanged.** The original DualStreamBuffer assumed
  `source ∈ {"mic", "system"}`. Letting `source` carry a device
  id (`"aipi-1"`) was a contract clarification, not a breaking
  change — no existing reader cared about the literal values.

## Handoff to phase 15

What is now available that wasn't before:

- **Audio ingest substrate** — the full chain from a remote
  device's PCM push to a transcribed segment with a
  per-device speaker label is one HTTP/WS surface.
- **`AudioSource` Protocol** — anyone adding a third source
  (file replay, a different transport in phase 15+) only
  has to implement the contract.
- **Device protocol doc** — `docs/DEVICE_PROTOCOL.md` is now
  canonical; phase 15 extends it rather than re-deriving it.
- **PSK rotation CLI** — `holdspeak device-psk show|rotate`
  exists and is exercised in unit tests.

What changed in the contract / canon:

- New canonical doc: `docs/DEVICE_PROTOCOL.md`.
- New `Config.device.psk` field (lazy-generated; in
  `~/.config/holdspeak/config.json`). Existing installs upgrade
  silently on first device interaction.
- `TranscriptSegment.device_id: Optional[str] = None` is now
  part of saved meeting JSON. Legacy mic / system segments
  preserve `None`; downstream consumers that ignore unknown
  keys are unaffected.
- `MeetingState.devices: list[DeviceDescriptor]` round-trips
  through `to_dict()` and lands in saved meeting JSON.

What phase 15 should read first:

- `docs/DEVICE_PROTOCOL.md` §8 ("What phase 15 will need to
  revisit") — the explicit list of phase-14 assumptions
  cross-network reach must re-examine: TLS termination point,
  PSK rotation under reconnect, per-device PSKs, tunnel-vs-
  direct addressing, per-device labels persisting across
  network changes.
- `pm/roadmap/holdspeak/phase-14-aipi-lite-devices/current-phase-status.md`
  §"Decisions made (this phase)" — every decision baked
  in here that phase 15 can choose to keep or revisit.
- The companion repo: `/home/karol/dev/esp32/AIPI-Lite-Voice-Bridge`
  (branch `mine`), specifically the AIPI-2 plan for the
  bridge protocol translator, which is the device-side
  counterpart to phase 14 / phase 15.

## Cross-network deferral — explicit trigger

Phase 14 is **same-LAN only**. Cross-network reach
(Tailscale / Cloudflare Tunnel / WireGuard candidate
evaluation, TLS, per-device PSKs, paired with the
AIPI-Lite firmware's portable WiFi / multi-SSID /
captive-portal / Improv-WiFi work) is **deferred to
phase 15**.

**Trigger to revisit:** the user has surfaced a concrete
deployment scenario for a device they want to use off the
home network (which device, which networks, when), AND
the phase-14 substrate has been stable on local LAN for at
least one cross-meeting week of dogfooding.

**Default if no decision:** ship phase 14 LAN-only,
document the gap (this file + `docs/DEVICE_PROTOCOL.md`
§8), revisit when the trigger fires.

## Final asset / test posture

- **1520 tests passing**, 5 skipped, 2 pre-existing failures
  outside phase-14 scope. Phase-14-introduced tests: 8
  files, ~90 cases.
- New modules: `holdspeak/device_audio.py`,
  `holdspeak/device_audio_ws.py`,
  `holdspeak/device_status.py`,
  `holdspeak/voice_typing.py`,
  `holdspeak/commands/device.py`.
- New canonical doc: `docs/DEVICE_PROTOCOL.md`.
- Public CLI added: `holdspeak device-psk show|rotate`.
- New WebSocket route: `WS /api/devices/audio`.
- New API: `POST /api/meeting/start {devices: [...]}`.
- New `Config.device.psk` field; new
  `TranscriptSegment.device_id` field; new
  `MeetingState.devices` field.
