# Phase 2 — Bridge Protocol Translator (HoldSpeak Satellite)

**Last updated:** 2026-05-10. **Phase closed** — see [`final-summary.md`](./final-summary.md). This file is now frozen per `~/dev/HoldSpeak/pm/roadmap/roadmap-builder.md` §3 (no further edits after phase close). Live-hardware smoke for AIPI-2-07 / 08 / select acceptance items in 01–06 was deferred at close (user not co-located with hardware on 2026-05-10); those deferrals are enumerated in [`final-summary.md`](./final-summary.md) "Stories cut or deferred".

## Goal

Make AIPI-Lite a first-class HoldSpeak satellite **end-to-end**:

- **Voice typing:** press the right button on the device, speak,
  release — the transcribed text lands in whatever app is focused on
  the HoldSpeak host machine. Same UX as HoldSpeak's local hotkey,
  driven by the device.
- **Meeting recording:** when HoldSpeak starts a meeting with the
  device attached, audio streams continuously, transcripts come back
  per-segment with the device's label, and the existing meeting
  intelligence (topics / action items / summary) just works because
  it doesn't care where the audio came from.

The mechanism: gut `bridge.py`'s self-contained STT + LLM + TTS loop
and replace it with a **thin, async, stateless WebSocket forwarder**
that translates between aioesphomeapi (the AIPI-Lite device) and
HoldSpeak's `/api/devices/audio` route. The bridge becomes ~150-250
lines of Python whose only job is moving bytes and translating events.

## Why this shape

Surveyed HoldSpeak's `pm/roadmap/holdspeak/phase-14-aipi-lite-devices/`
on 2026-05-07: **all 8 stories shipped** (HS-14-07 status pushback +
HS-14-08 DoD/protocol-doc both landed late on the same day after the
initial survey). The device-side WebSocket substrate
(`holdspeak/device_audio_ws.py` + `holdspeak/device_audio.py`), PSK
auth, handshake schema (`DeviceHandshake` Pydantic model), audio
frame format (16 kHz mono int16-LE PCM), session arbitration
(`holdspeak/voice_typing.py:VoiceTypingSession`), meeting attach
(`MeetingSession.attach_device` + `POST /api/meeting/start` with
`devices: list[str]`), inbound `status` frames
(`{"type":"status","text":...,"ttl_ms":...}`), and inbound `event`
frames (`{"type":"event","name":"long_press","at":...}` →
`MeetingSession.add_bookmark`) are all live. The canonical wire
contract is now `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md`; this phase
**references that doc** rather than duplicating field schemas.
AIPI-2 was *explicitly* designed to land on this substrate. We don't
reinvent the protocol; we land on it.

Two paths considered and rejected during the survey:

- **MQTT** — duplicates HoldSpeak's WS substrate; HoldSpeak has no
  MQTT surface today; adding one is contrary to HS-14's design.
- **HoldSpeak speaks aioesphomeapi directly** — couples HoldSpeak to
  ESPHome internals and reinvents the bridge. The
  `/api/devices/audio` boundary is the right abstraction.

## Scope

### In

- A rewritten `bridge.py` that is a stateless async forwarder with
  three loops:
  1. **Device loop** — aioesphomeapi connection to the AIPI-Lite,
     subscribes to button events + voice_assistant audio events.
  2. **HoldSpeak loop** — WebSocket to `ws://<host>:<port>/api/devices/audio`,
     handshake with PSK, heartbeat, control + binary frames.
  3. **Translator** — maps device events → control frames, audio frames
     → WS binary, and (placeholder for AIPI-3 / HS-14-07) inbound
     `status` frames → ESPHome `update_screen` service.
- A `bridge.env` config (or `secrets.yaml` additions — story-04
  decides) with `HOLDSPEAK_HOST`, `HOLDSPEAK_PORT`, `HOLDSPEAK_PSK`,
  `DEVICE_ID`, `DEVICE_LABEL`.
- Type-safe message handling: every WS frame goes through a Pydantic
  model that mirrors HoldSpeak's `DeviceHandshake` /
  control-frame schema. No raw dict slinging.
- Resilient reconnect logic on both legs — exponential backoff with
  jitter, max retries logged structurally, no silent infinite loops.
- Structured logging (Python `logging` with JSON formatter or `loguru`
  — story-01 picks).
- A systemd unit example (`scripts/aipi-bridge.service` or similar)
  + a Docker option in the runbook so the bridge can be daemonized.
- A runbook (`docs/HOLDSPEAK_BRIDGE.md`) covering install, configure,
  run, troubleshoot.
- An end-to-end smoke test scenario documented in story-06: HoldSpeak
  + bridge + AIPI device → press right button → speak → text appears
  in a known target app on the host.
- Updated top-level `README.md` describing the new architecture
  (bridge is forwarder; HoldSpeak is brain).
- Meeting-recording verification end-to-end (story-05): start a
  meeting from HoldSpeak with `devices:["aipi-1"]`, talk into the
  device, confirm transcripts come back with `device_id` + label.

### Out

- ~~**LCD status pushback** (server → device, rendering
  `Recording 12:34` / `Saving meeting...` on the device's LCD).~~
  **Promoted in 2026-05-10:** the followup turned out to be small
  enough (~30 LOC of state-machine + a new `update_link` API
  service) that pulling it into phase 2 was cheaper than carrying
  the no-op stub into AIPI-3. Shipped as **AIPI-2-07**. See story
  for the three-zone LCD layout, sticky/flash ttl semantics, and
  ASCII symbol map.
- **Inbound `event` frames from device → server (e.g.,
  bookmark-on-tap during meetings).** HS-14-07 wired
  `{"type":"event","name":"long_press"}` →
  `MeetingSession.add_bookmark` server-side. *Available*, but no
  device gesture in phase 2 maps to it (right button = voice
  typing; left button = AP-mode entry / factory reset; triple-tap
  = local continuous-mode toggle). The bridge does **not** emit
  event frames in this phase — server-side bookmark hook stays
  dormant. Wiring a gesture (e.g., left-button quick-tap or a
  combo) is a follow-up after we have field experience.
- **Cross-network operation** — Tailscale / Cloudflare Tunnel /
  WireGuard. AIPI-3, paired with HS-14-15.
- **Multi-device support** — one bridge process per device for now.
  Multiplexing is a non-goal until the use case shows up.
- **Wake-word / on-device VAD** — AIPI-4+.
- **Re-purposing the existing `triple-tap = always-listening` toggle.**
  Decision deferred (see Decisions deferred); for v1 the device-side
  toggle stays a local affordance with no HoldSpeak meaning, and
  meeting mode is host-driven.
- **Replacing the legacy STT/LLM/TTS loop with a feature flag** so
  users can choose. AIPI-2 commits to the HoldSpeak shape; the legacy
  code is removed. Anyone who wants the old behaviour pins the
  pre-AIPI-2 commit.

## Exit criteria (evidence required)

- [ ] `bridge.py` rewritten as a stateless async forwarder; the
  legacy STT (faster-whisper) + LLM (Qwen/DeepSeek) + TTS (gTTS) code
  paths are deleted. Lines: target ≤ 250 (reference: ~415 lines today).
- [ ] `bridge.env.example` (or `secrets.yaml.example` updates per
  story-04) documents every config field; `bridge.py` exits with a
  clear error if any required field is missing.
- [ ] WebSocket handshake against a real HoldSpeak instance succeeds:
  bridge logs `hello-ack` from server, no 4001/4003/4009 close codes.
- [ ] End-to-end voice typing: press the device's right button on
  hardware, speak, release → text appears in a known target app on
  the HoldSpeak host within ~2 s of release. Recorded in
  `evidence-story-06.md` with terminal output / video.
- [ ] End-to-end meeting attach: from HoldSpeak's web UI or CLI, start
  a meeting with `devices:["aipi-1"]`, speak into the device, confirm
  meeting transcript pages show segments with the device's label.
  Recorded in `evidence-story-05.md`.
- [ ] Reconnect resilience: kill HoldSpeak (`pkill -f holdspeak`),
  bridge logs the disconnect, reconnects with backoff when HoldSpeak
  comes back, voice typing continues to work without restarting the
  bridge. Same for the device leg (unplug + replug USB).
- [ ] `docs/HOLDSPEAK_BRIDGE.md` exists and a fresh user can stand
  the bridge up from clone → working voice typing in under 10
  minutes.
- [ ] Unit tests cover the Pydantic models (round-trip vs. fixtures
  derived from `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md`) and the
  WS reconnect-with-jitter scheduler. `pytest -q` exits 0.
- [ ] All AIPI-2-01..06 stories show `Status: done` with paired
  `evidence-story-{n}.md` files.
- [ ] `final-summary.md` records what shipped + what surprised us +
  handoff notes for AIPI-3 (cross-network) and the LCD-pushback +
  bookmark-gesture follow-ups.
- [ ] `pm/roadmap/aipi-lite/README.md` reflects phase 2 done +
  phase 3 not-started.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| AIPI-2-01 | Bridge skeleton: ESPHome + HoldSpeak connections, handshake, heartbeat, reconnect | done | [story-01-bridge-skeleton.md](./story-01-bridge-skeleton.md) | [evidence-story-01](./evidence-story-01.md) |
| AIPI-2-02 | Audio forwarding: mic events → WS binary frames | done | [story-02-audio-forwarding.md](./story-02-audio-forwarding.md) | [evidence-story-02](./evidence-story-02.md) |
| AIPI-2-03 | Control mapping: button events → WS start/stop, session_busy handling | done | [story-03-control-mapping.md](./story-03-control-mapping.md) | [evidence-story-03](./evidence-story-03.md) |
| AIPI-2-04 | Configuration migration: env/secrets schema; legacy LLM vars removed | done | [story-04-config-migration.md](./story-04-config-migration.md) | [evidence-story-04](./evidence-story-04.md) |
| AIPI-2-05 | Meeting-mode integration verification | done | [story-05-meeting-mode.md](./story-05-meeting-mode.md) | [evidence-story-05](./evidence-story-05.md) |
| AIPI-2-06 | DoD: HOLDSPEAK_BRIDGE.md runbook + final-summary + phase exit | done | [story-06-dod.md](./story-06-dod.md) | [evidence-story-06](./evidence-story-06.md) |
| AIPI-2-07 | LCD pushback: `status` frames + link indicator (was a phase-2 "Out") | done | [story-07-lcd-feedback.md](./story-07-lcd-feedback.md) | [evidence-story-07](./evidence-story-07.md) |
| AIPI-2-08 | Hardening, package split, test infra (ruff + CI + protocol-sync) | done | [story-08-hardening-and-package.md](./story-08-hardening-and-package.md) | [evidence-story-08](./evidence-story-08.md) |

(Status values: `backlog`, `in-progress`, `paused`, `done`, `cancelled`.)

## Where we are (frozen 2026-05-10)

**Phase 2 closed.** See [`final-summary.md`](./final-summary.md) for the close-out narrative, deferred-item list, and handoff to phase 3.

The history below is preserved for archaeological context only — it was the live "Where we are" log during phase 2 and stops updating at phase close.

## Where we are (historical log)

AIPI-2-01 (bridge skeleton) implemented 2026-05-07. New files:
`bridge.py` (rewritten — async forwarder spine, ~430 lines),
`holdspeak_proto.py` (Pydantic models, `extra="forbid"` mirroring
`DeviceHandshake`), `tests/test_models.py` (17 cases),
`tests/test_reconnect.py` (9 cases), `pytest.ini`. Updated
`requirements.txt` adds `pydantic`, `structlog`, `websockets`,
`pytest`, `pytest-asyncio`; legacy STT/LLM/TTS deps stay flagged
for removal in story 04. `pytest tests/ -q` passes 26/26.
`python3 bridge.py --check` against the live `aipi.local`
device confirms the device leg; the HoldSpeak leg fails cleanly
with `ConnectionRefusedError` and a decoded message when no
server is running. JSON-structured logs via `structlog`.

The legacy `bridge.py` (faster-whisper + Qwen LLM + gTTS round-trip
loop) is gone — story 01 chose to delete the old code paths in
the same rewrite rather than leave a transitional half-rewrite.
Story 04 still owns formalising the env schema (`bridge.env` +
`pydantic-settings`) and pruning legacy deps from
`requirements.txt`.

AIPI-2-02 (audio forwarding) shipped 2026-05-07. New helpers
`synth_sine_pcm` + `read_wav_pcm` (16k mono int16 strict
validation). `DeviceLeg` subscribes to `voice_assistant` on
connect and pushes chunks to a bounded `asyncio.Queue` (cap 500
chunks; drop-newest with throttled overflow logging).
`HoldSpeakLeg.session()` now gathers four tasks: heartbeat
sender, frame receiver, audio sender (drains the queue → WS
binary), and a 1 s metrics ticker that emits
`audio.bytes_forwarded` with `bytes_forwarded` +
`frames_forwarded` fields when frames moved during the window.
Two new CLI modes — `--send-test-audio <wav>` (one-shot WAV
streaming with real-time pacing) and `--audio-loopback`
(continuous 440 Hz sine) — bypass the device leg for
HoldSpeak-side smoke tests. `tests/test_audio.py` adds 9
cases; 35/35 total pass.

AIPI-2-03 (control mapping) shipped 2026-05-07. New
`control_queue` (cap 100) carries serialised control frames
from `DeviceLeg` to `HoldSpeakLeg`. `_handle_va_start`
enqueues `StartFrame`; `_handle_va_stop` enqueues `StopFrame`
plus fires `VoiceAssistantEventType.VOICE_ASSISTANT_RUN_END`
so the firmware's `voice_assistant.on_end` trigger fires
(continuous-mode re-arm). New `_control_sender(ws)` task
drains the queue → WS text frames; gathered alongside the
heartbeat/receiver/audio/metrics tasks (5 concurrent now).
Inbound `error: session_busy` fires the `on_session_busy`
callback (wired in `_run` to `device.update_screen("Busy")`)
as a fire-and-forget task so the receive loop doesn't block.
DeviceLeg now exposes `update_screen(msg)`, calling the
firmware's existing `update_screen` API service.

AIPI-2-04 (config migration) shipped 2026-05-07. `Settings`
became a `pydantic-settings.BaseSettings` subclass that reads
env + an optional `bridge.env` file (gitignored). `HOLDSPEAK_PSK`
is `SecretStr` so `repr()` and any log line that captures the
model auto-redact to `**********`; plaintext access requires the
explicit `.get_secret_value()` call. `bridge.env.example`
documents every field with comments + defaults + the
`holdspeak device-psk show` cue. Legacy STT/LLM/TTS deps
(`faster-whisper`, `gtts`, `pydub`, `requests`,
`webrtcvad-wheels`) are gone from `requirements.txt`;
`pydantic-settings>=2` added.

The bridge is now feature-complete on the runtime side. The
top-level `README.md` rewrite is intentionally deferred to story
06 (DoD), where it lands alongside the `docs/HOLDSPEAK_BRIDGE.md`
runbook so the new architecture story is told once, in one place.

AIPI-2-06 partial close shipped 2026-05-07.
`docs/HOLDSPEAK_BRIDGE.md` (TL;DR-shaped 8-section runbook
covering architecture, prerequisites, first-time setup, voice
typing, meeting recording, daemonising, PSK rotation, and an
extensive troubleshooting cheatsheet) plus
`scripts/aipi-bridge.service` (systemd unit with both
system-wide and rootless install paths, `--check` as
`ExecStartPre` for fast-fail).

AIPI-2-05 (meeting verification) is in-progress: bridge code
change is zero (audio channel is identical for voice typing
and meetings), and the documentation deliverable is folded
into the runbook §5. Live HoldSpeak verification of attach +
per-device-labeled transcripts is the only remaining acceptance
work — pairs with the rest of phase 2's verification queue.

**2026-05-09: README rewritten** as part of AIPI-2-06 close-out
prep. The legacy STT/LLM/TTS narrative is gone; the new shape
(thin forwarder onto HoldSpeak, three-zone LCD, `python -m bridge`)
is documented with a quick-start, repo-layout table, project-status
section, and pointers to the canonical runbook. Acknowledgements
section preserved.

**2026-05-10: AIPI-2-07 (LCD pushback) shipped on disk.** The
followup that was originally carved out of phase 2 ("LCD status
pushback ... out of scope") got pulled in once the surface
proved containable. New ESPHome `update_link` API service +
`link_label` widget at TOP_RIGHT; sticky/flash/revert state
machine in `bridge.holdspeak.HoldSpeakLeg`; ASCII activity-symbol
map (Listening → `>>`, Recording → ` *`, Bookmark → `\!//`,
Saving → `...`, Busy → `[?]`, Ready → `─`, error → `/!\`);
`[..]→[OK]→[--]` link transitions painted across the WS
lifecycle; `docs/HOLDSPEAK_BRIDGE.md` §5 rewritten. 25 new
tests (`tests/test_dispatch.py` + `tests/test_lcd_helpers.py`
+ four in `tests/test_holdspeak_leg.py`).

**2026-05-10: AIPI-2-08 (hardening + package + infra) shipped.**
Long pass through the remaining critique findings + a structural
cleanup. Highlights:

- **Correctness:** UDP source-IP allowlist (drops alien LAN
  senders), UDP listener wrapped in `reconnect_with_backoff` +
  SO_REUSEADDR, loud `EADDRINUSE`/`EACCES` errors with
  remediation hints, `subscribe_voice_assistant` failure now
  fatal (was silent), `gather` → `wait(FIRST_COMPLETED)` so
  server-close tears the session down promptly,
  `ConnectionClosedOK` vs `ConnectionClosedError` split (clean
  reset / abrupt backoff), empty PSK rejected at config load,
  `update_screen`/`update_link` handles cached on connect.
- **Deeper `--check`:** also binds the UDP audio port, lists
  firmware services + warns on outdated firmware, validates
  HoldSpeak's `hello-ack` echoes the configured `device_id`.
- **Structural:** `bridge.py` (1500 LOC) → `bridge/` package
  (settings / audio / lcd / reconnect / device / holdspeak /
  cli + `__main__`). Re-exports preserve the
  `from bridge import X` import surface so tests didn't churn.
  Systemd unit + runbook updated for `python -m bridge` + `%h`
  rootless paths.
- **Test + lint:** 35 → 98 tests across 8 test files; ruff
  0.15.12 with a conservative ruleset (`E F I B C4 UP ISC`);
  62 % coverage (100 % on `holdspeak_proto`); cross-repo
  protocol-sync test (skips when sibling not present); GitHub
  Actions CI on push/PR (3.10/3.11/3.12 matrix).
- **Cleanup:** `docs/DEVICE_AUDIO_OUTPUT.md` recovery doc for
  the deliberately-removed device speaker stack
  (octal PSRAM rationale, EMI dance, ES8311 deep-mute,
  paste-back YAML); `pm/probes/` directory removed
  (probe served its purpose 2026-05-07); `debug_mic.wav`
  artefact deleted; `requirements.txt` pinned with
  `requirements-dev.txt` separation.

The phase is **implementation-complete** with full runtime,
runbook, LCD pushback, hardening, lint, CI, and test infra on
disk. Everything left is hardware verification + the close-out
commit. Hardware verification now also covers the
AIPI-2-07/08 acceptance criteria (LCD paints during a real
meeting; `[--]→[OK]` transitions across a real HoldSpeak
restart; deeper `--check` against live device + HoldSpeak).

The phase is now 100 % implementation-complete with full
runtime + runbook on disk. Everything left is **hardware
verification + a single close-out commit** that:

1. Authors `evidence-story-01..05.md` from the inline evidence
   already in story files.
2. Flips stories 01..06 to `done`.
3. Authors `final-summary.md` (handoff to AIPI-3 + the two
   followups: LCD pushback wiring, bookmark gesture).
4. Rewrites the top-level `README.md` for the new architecture.
5. Freezes `current-phase-status.md`.
6. Bumps `pm/roadmap/aipi-lite/README.md`: phase 2 → done,
   `Current phase` → phase 3.

Pickup when HoldSpeak is running: walk through the runbook §3 +
§4 + §5 with the live device, capture terminal output for the
evidence files, then make the close-out commit.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| HoldSpeak's `DeviceHandshake` schema or the WS protocol shifts before we land (HS-14-07/08 are still in motion) | medium | Pin a `holdspeak` revision in the bridge's runbook and re-pin when we close phase 2. Mirror HoldSpeak's Pydantic model with `extra="forbid"` so version drift fails loudly, not silently. | If HoldSpeak makes a breaking schema change mid-phase, pause AIPI-2-01..03 until HS-14-08's `docs/DEVICE_PROTOCOL.md` lands and locks the contract. |
| ESPHome's `voice_assistant` audio-event API on aioesphomeapi is poorly documented; we may have to capture mic frames via a different mechanism (e.g., a custom `media_player` or raw I2S read) | medium | Story-02 starts with a 1-day spike: confirm the aioesphomeapi event shape against the device. If voice_assistant doesn't expose raw frames, fall back to triggering `media_player.start_recording` or a custom service. | If neither path works, descope to a narrower mic-capture mechanism (bridge sends synthesized fixed-tone audio so the rest of the path is verifiable) and open an upstream-clarification ticket. |
| Latency: WS round-trip + HoldSpeak transcription might feel slower than the current bridge.py loop | low | Measure end-to-end latency in story-06 (button release → text typed). The current loop already round-trips through faster-whisper; HoldSpeak does the same on the host side, so total latency should be similar. | If latency exceeds 3 s end-to-end on a typical utterance, profile + open a story to optimise (likely on HoldSpeak side, since the bridge is just bytes). |
| PSK-rotation UX: when the user rotates the PSK on HoldSpeak, the bridge has no live feedback channel to update | low | Document the rotation procedure in the runbook (rotate PSK → update `bridge.env` → restart bridge). The bridge logs handshake failures clearly. | If users hit this in practice, consider adding a `holdspeak device-psk show` CLI dependency in the runbook and/or watching the file for changes (HUP-style reload). |
| The legacy `bridge.py` deletion removes someone's working flow if they didn't follow the roadmap | low | Phase explicitly accepts this trade-off (see Decisions made). The runbook calls out: pin the pre-AIPI-2 commit if you want the legacy STT+LLM+TTS path. | n/a — this is a documented spec drift, not a stop signal. |

## Decisions revised (this phase)

- 2026-05-10 — **LCD pushback (HS-14-07) is now IN scope.**
  Originally carved out as an AIPI-2-followup so phase 2's spine
  could ship cleanly. After the substrate landed, the LCD UX
  decisions deferred (ttl handling, conflict with the existing
  mode label, mode/link/activity zones) collapsed into a small,
  contained shape — a new `link_label` widget + a new
  `update_link` API service + a ~30 LOC sticky/flash state
  machine. Promoted to **AIPI-2-07** rather than slipping to
  AIPI-3.
- 2026-05-10 — **`bridge.py` becomes a package.** The single-file
  bridge ballooned from ~430 LOC at AIPI-2-01 to ~1500 LOC after
  the hardening + LCD pushback work. Splitting into focused
  modules (`settings`, `audio`, `lcd`, `reconnect`, `device`,
  `holdspeak`, `cli`) buys cleaner reasoning + per-module test
  surface; re-exports preserve `from bridge import X` so the test
  suite + external callers don't churn. Entry point flipped from
  `bridge.py` to `python -m bridge`; systemd unit + docs updated.

## Decisions made (this phase)

- 2026-05-07 — **Land on HoldSpeak HS-14's WebSocket substrate, not a
  custom protocol.** Six of eight HS-14 stories already shipped; the
  abstraction is exactly what AIPI-2 needs. Reinventing it would be
  pure cost.
- 2026-05-07 — **Bridge stays Python, async, single-process.**
  HoldSpeak is Python; aioesphomeapi is Python; the bridge already
  has both deps. Switching language for the rewrite would be cost
  without payoff.
- 2026-05-07 — **One bridge process per device.** Multi-device
  multiplexing is a non-goal for v1. If the user runs two AIPI-Lites,
  they run two bridge processes (e.g., two systemd unit instances).
- 2026-05-07 — **Pydantic models on the wire, mirrored from HoldSpeak.**
  Type-safe message handling is non-negotiable for the "kicks ass"
  bar. `extra="forbid"` so schema drift fails loudly.
- 2026-05-07 — **Delete legacy STT/LLM/TTS code paths from
  `bridge.py`.** Don't keep them behind a feature flag — that's
  exactly the "feature flags + backwards-compat shim" pattern the
  project's coding guidelines call out as the wrong default. Anyone
  who wants the legacy behaviour pins the pre-AIPI-2 commit.
- 2026-05-07 — **LCD status pushback (server → device) is OUT
  even though HS-14-07 shipped.** The substrate is available, but
  pulling it into phase 2 expands the surface (LCD UX decisions:
  ttl handling, conflict with the existing mode label, behaviour
  during a meeting vs. voice typing). Phase 2 ships the bridge as
  a one-way (device → host) audio path; LCD gets richer state in a
  dedicated follow-up. Story-01's skeleton leaves a no-op inbound
  `status` handler so the follow-up is small.
- 2026-05-07 — **No `event` frames emitted from bridge → server in
  this phase.** HS-14-07 wired the server-side bookmark hook
  (`MeetingSession.add_bookmark`), but no device gesture in phase
  2 maps to it. Wiring a gesture (e.g., a left-button quick-tap
  during a meeting) is a follow-up after we have field experience
  with the meeting flow.
- 2026-05-07 — **WebSocket health is enforced via ping/pong, not
  frame-receive timeouts.** A healthy idle HoldSpeak connection
  produces zero unsolicited server frames; checking "no frame in
  N seconds" would tear down healthy connections. The `websockets`
  library's `ping_interval=15, ping_timeout=30` is the right
  primitive.
- 2026-05-07 — **Device-leg reconnect delegates to
  `aioesphomeapi.ReconnectLogic`.** That class already implements
  the reconnect pattern we want; writing a parallel
  exponential-backoff loop on the device leg would fight with the
  internal logic. Only the HoldSpeak (WS) leg needs a custom
  `reconnect_with_backoff(coro_factory, name)` helper.
- 2026-05-07 — **Meeting recording is a host-driven mode, no new
  device gesture.** HoldSpeak's web UI / CLI starts the meeting with
  `devices:["aipi-1"]`; the device just keeps streaming audio. No
  new physical button mapping in this phase. (Continuous mode toggle
  via triple-tap of the right button stays a local affordance; its
  long-term role is deferred — see below.)

## Decisions deferred

- **Continuous mode (right-button triple-tap) — keep, repurpose, or
  retire?** Today it toggles `voice_assistant.start` indefinitely.
  Once HoldSpeak owns sessions, this could mean "I'm in a meeting,
  keep streaming," but HoldSpeak's meeting mode does that already
  from the host side. Kept as a local affordance for v1; revisit
  once we have field experience.
- **PSK reload-on-change** vs. restart-to-reload. Restart is simpler
  and ships in v1. File-watch reload is a nice-to-have if rotations
  become frequent.
- **Bridge as systemd unit vs. user-space supervisor.** The runbook
  ships a systemd unit example as the recommended path. macOS users
  get `launchd` instructions in a follow-up; for now they `tmux` it
  or use `pm2`-style runners.
- **Telemetry / metrics export.** Out of scope until we have a
  reason. Structured logs are enough for debugging in v1.
