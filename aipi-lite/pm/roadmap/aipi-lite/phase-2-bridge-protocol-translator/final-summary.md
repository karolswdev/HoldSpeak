# Phase 2 — Final Summary

- **Phase opened:** 2026-05-07 (`476e4a9 aipi-lite roadmap: open AIPI-2 (bridge protocol translator) phase`)
- **Phase closed:** 2026-05-10
- **Chunks shipped:** 8 (AIPI-2-01..08)

## Goal — was it met?

> Make AIPI-Lite a first-class HoldSpeak satellite **end-to-end**:
> voice typing — press the right button, speak, release, transcript types into the focused host app; meeting recording — HoldSpeak attaches the device, audio streams continuously, transcripts come back per-segment with the device's label.
> Mechanism: gut `bridge.py`'s self-contained STT + LLM + TTS loop and replace it with a thin async stateless WebSocket forwarder.

**Yes — partial live evidence.**

Voice typing + meeting attach were live-verified end-to-end on 2026-05-08 against the running HoldSpeak instance, alongside the UDP fix that landed in `9ff88a6`. See [`evidence-story-02.md`](./evidence-story-02.md) for the trace: button press → speak → release → text typed in ~2 s; `POST /api/meeting/start {"devices":["aipi-1"]}` produces per-segment transcripts tagged with the device's `DEVICE_LABEL`; per-source attribution `[Karol]` / `[Me]` / `[Remote]` resolved correctly.

Two follow-on stories landed on disk on 2026-05-10 *after* that live trace and were not re-smoked: AIPI-2-07 (LCD pushback) and AIPI-2-08 (package split + hardening + deepened `--check`). Both have full unit-test + fake-server integration-test coverage; live LCD paint timing + the deepened `--check` paths are deferred (see "Stories cut or deferred" below). At phase close (2026-05-10) the user is not co-located with hardware (Barnes & Noble); hardware smoke is waived for the close-out and tracked as the highest-priority phase-2 follow-on.

## Exit criteria — final state

- [x] `bridge.py` rewritten as stateless async forwarder; legacy STT/LLM/TTS deleted — see [`evidence-story-01.md`](./evidence-story-01.md) + [`evidence-story-04.md`](./evidence-story-04.md). Final shape is a `bridge/` package, not a single file (AIPI-2-08 split).
- [x] `bridge.env.example` documents every config field; missing-field exit 1 with clear errors — see [`evidence-story-04.md`](./evidence-story-04.md).
- [x] WebSocket handshake against real HoldSpeak succeeds (no 4001/4003/4009) — verified live 2026-05-08; see [`evidence-story-02.md`](./evidence-story-02.md) (audio doesn't flow without handshake).
- [x] End-to-end voice typing — verified live 2026-05-08; see [`evidence-story-02.md`](./evidence-story-02.md) and [`evidence-story-03.md`](./evidence-story-03.md).
- [x] End-to-end meeting attach with per-device-labeled transcripts — verified live 2026-05-08; see [`evidence-story-05.md`](./evidence-story-05.md).
- [~] Reconnect resilience (`pkill -f holdspeak`, device unplug/replug) — `tests/test_holdspeak_leg.py` covers clean + abrupt-close paths against a fake `websockets.serve` server; `aioesphomeapi.ReconnectLogic` handles the device leg. **Live `pkill` + USB-replug smoke deferred** — hardware not co-located at phase close.
- [x] `docs/HOLDSPEAK_BRIDGE.md` exists; fresh-user-walkthrough verification deferred — see [`evidence-story-06.md`](./evidence-story-06.md).
- [x] Unit tests cover Pydantic models + reconnect-with-jitter scheduler — `tests/test_models.py` (17 cases) + `tests/test_reconnect.py` (9 cases) at story-01; full suite is now 98 cases. `pytest -q` exits 0.
- [x] All AIPI-2-01..08 stories show `Status: done` with paired `evidence-story-{n}.md` files — landed in this commit.
- [x] `final-summary.md` records what shipped + surprises + handoff — this file.
- [x] `pm/roadmap/aipi-lite/README.md` reflects phase 2 done + current-phase pointer to phase 3 — landed in this commit.

## Stories shipped

| ID | Title | Commit | Date |
|---|---|---|---|
| AIPI-2-01 | Bridge skeleton — async forwarder + Pydantic models | `f71947a` | 2026-05-07 |
| AIPI-2-02 | Audio forwarding — mic frames → WS binary; UDP fix | `bd7a107` + `9ff88a6` | 2026-05-07 / 2026-05-08 |
| AIPI-2-03 | Control mapping — button → WS, session_busy → LCD | `2de1c18` | 2026-05-07 |
| AIPI-2-04 | Configuration migration — `Settings(BaseSettings)` + dep prune | `67bc2f3` | 2026-05-07 |
| AIPI-2-05 | Meeting-mode integration verification (bridge-side no-op) | `9ff88a6` (verified) | 2026-05-08 |
| AIPI-2-06 | Phase exit + DoD + HoldSpeak Bridge runbook | `105bb1a` (partial) + close-out | 2026-05-07 / 2026-05-10 |
| AIPI-2-07 | HoldSpeak → LCD pushback (status frames + link indicator) | close-out commit | 2026-05-10 |
| AIPI-2-08 | Hardening, package split, test infrastructure | close-out commit | 2026-05-10 |

## Stories cut or deferred

| Item | Status | Re-targeted to |
|---|---|---|
| Live `pkill -f holdspeak` reconnect smoke | deferred at phase close | First post-phase-2 hardware session |
| Live device unplug/replug reconnect smoke | deferred at phase close | First post-phase-2 hardware session |
| Live LCD paint during a real meeting (AIPI-2-07) | deferred at phase close | First post-phase-2 hardware session — highest priority because activity-slot paint timing is the part most likely to surface UX issues that a fake-server test doesn't catch |
| Live `[--]→[OK]` link flip on real HoldSpeak restart | deferred at phase close | First post-phase-2 hardware session |
| Live deepened `--check` (UDP bind, firmware service availability, ack `device_id` echo) | deferred at phase close | First post-phase-2 hardware session |
| Fresh-user runbook walkthrough simulation | deferred at phase close | First post-phase-2 hardware session |
| Intel-pipeline observation for device-driven meeting (topics / action items / summary) | not explicitly captured 2026-05-08 | Low priority; runs deferred-cloud or local depending on HoldSpeak config |
| Continuous-mode redesign (right-button triple-tap meaning under HoldSpeak) | deferred — kept as local affordance | Revisit in field after usage |
| PSK reload-on-change (HUP / file-watch) | deferred | Open if rotation frequency demands |
| macOS launchd plist | deferred | Phase 3 or later (systemd is v1 supervised path) |
| Outbound `event` frames (bookmark gesture device → server) | deferred — server hook dormant | Phase-3 or AIPI-2 follow-up; left-button quick-tap during meeting is the candidate gesture |
| Mic-level meter on LCD activity slot | deferred | Needs API-roundtrip cost measurement before commit |
| LVGL builtin symbols on LCD | deferred | After Montserrat 10 glyph coverage verified on hardware |
| mypy adoption | deferred | Follow-up story candidate |
| Coverage threshold gate in CI | deferred | After legs decompose further |
| `pyproject.toml` + publishable distribution | deferred | When usage warrants |

## Surprises and lessons

- **ESPHome `voice_assistant` is UDP-first.** Returning `None` from `handle_va_start` (intending "use API audio") silently broke the audio path: bridge logged `subscribe.voice_assistant.ok` and `device.voice_assistant.start` on press but zero `audio.bytes_forwarded`. Fix: return a UDP port; bridge listens on `0.0.0.0:UDP_AUDIO_PORT`. Lesson saved to `~/.claude/projects/-home-karol-dev-esp32-AIPI-Lite-Voice-Bridge/memory/feedback-esphome-voice-assistant-udp.md`. **Phase-3 takeaway:** when wrapping in TLS / a tunnel, the tunnel must carry UDP, not just TCP — Tailscale and WireGuard handle this transparently; Cloudflare Tunnel does not (TCP-only).
- **UDP source-IP allowlist closed a real attack.** Without it, anyone on the LAN could push PCM to UDP 50000 and have it forwarded as the user's voice — non-theoretical for hotspot / "follow me out of the home LAN" scenarios. Phase-3 cross-network transport will need the same discipline at the tunnel layer (route UDP only from the device's tunnel-assigned IP).
- **`gather` vs `wait(FIRST_COMPLETED)` matters for tear-down.** Plain `gather` hung on server-close until the next 15s heartbeat fired. Visible symptom: bridge logs looked clean but reconnect was 15s-laggy. AIPI-2-08 fixed it; phase-3 retains the pattern.
- **`ConnectionClosedOK` vs `ConnectionClosedError` matters for backoff.** Treating every close as clean caused tight retry loops on flapping HoldSpeak. Clean close → reset backoff; abrupt → engage exponential. Phase-3's TLS-wrapped transport will see a third class (TLS-handshake failures); pre-classify before the backoff branch.
- **Empty `HOLDSPEAK_PSK` silently passed Pydantic-required.** `SecretStr("")` is truthy at the Pydantic-required level; the bridge only failed at handshake time. Reject empty strings explicitly at config load.
- **LCD pushback was supposed to be out-of-scope.** The original phase plan punted it to phase 3. After the substrate landed, the surface collapsed into a contained shape (~30 LOC sticky/flash state machine + new `update_link` API service + `link_label` widget). Promoted to AIPI-2-07 rather than slipping. Lesson: a feature carved out for "scope discipline" reasons can sometimes be cheaper than the no-op stub it leaves behind — re-evaluate when its blockers clear.
- **`bridge.py` ballooned from ~430 LOC at AIPI-2-01 to ~1500 LOC.** Hardening + LCD pushback added density, not features. The package split (AIPI-2-08) buys focused per-module reasoning + per-module test surface; re-exports preserve `from bridge import X` for tests + external callers. Phase-3 should aim to add code in the existing modules (e.g., a new `bridge/transport.py` for the TLS / tunnel wrapper) rather than re-bloating any one module.
- **`_handle_va_audio` was kept "as a backup" and turned out to be dead code.** Stock ESPHome firmware doesn't fire it; the UDP path is the only live path. AIPI-2-08 deleted it. Lesson: a code path with "fallback" written on it deserves an explicit test or a death sentence — not both.
- **`--check` evolved from a fast-fail health check into a mini-smoke test.** AIPI-2-08 deepened it to also bind UDP, list firmware services + warn on missing ones (catches outdated firmware), and validate the ack `device_id` echo (catches a bridge pointing at the wrong HoldSpeak). Pre-commit hook material if this repo ever grows one.
- **The cross-repo protocol-sync test is worth its weight.** `tests/test_protocol_sync.py` skips cleanly when `~/dev/HoldSpeak/` isn't checked out, but when it is, a HoldSpeak schema change that drifts from `holdspeak_proto.py` fails the suite loudly. Phase-3 should keep this discipline as the wire surface grows (TLS handshake additions, tunnel-aware fields, etc.).

## Handoff to phase 3 (cross-network transport)

### What's now available

- A working stateless async forwarder (`bridge/` package): aioesphomeapi on the device leg, `websockets` on the HoldSpeak leg, UDP listener for audio.
- Type-safe wire layer: `holdspeak_proto.py` Pydantic models with `extra="forbid"` mirroring HoldSpeak's `DeviceHandshake`. Cross-repo drift test in `tests/test_protocol_sync.py`.
- Resilient reconnect on both legs: ESPHome via `aioesphomeapi.ReconnectLogic`; HoldSpeak via custom `reconnect_with_backoff` (1s, 2s, 4s, 8s, 16s, 30s ±25% jitter).
- Three-zone LCD with one owner per zone (firmware: `mode_label` TOP_LEFT; bridge: `link_label` TOP_RIGHT + `ai_response_label` BOTTOM). New `update_link` API service.
- Activity state machine with sticky / flash / revert semantics + ASCII activity-symbol map.
- 98 tests, 62% coverage (100% on `holdspeak_proto`), `ruff` clean, GitHub Actions CI matrix on 3.10/3.11/3.12.
- Documentation: `docs/HOLDSPEAK_BRIDGE.md` (8-section runbook), `docs/DEVICE_AUDIO_OUTPUT.md` (recovery doc for the deliberately-removed speaker stack), top-level `README.md` rewritten for the new architecture.
- Operational hygiene: systemd unit (`scripts/aipi-bridge.service`) with rootless-install support; `bridge.env.example` documenting every field with `holdspeak device-psk show` cue.

### What changed in the contract / canon

- Wire contract is locked to HS-14-08's `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md` — the canonical source, not duplicated in the runbook.
- `device_id` echo in `hello-ack` is now validated by `--check` (was a silent assumption).
- Empty `HOLDSPEAK_PSK` rejected at config load (was a silent failure at handshake).
- `update_screen` and `update_link` API services are both required by the bridge; `--check` warns if firmware is missing either.
- UDP source-IP allowlist on the device-side audio listener — phase-3's tunnel layer must preserve a similar trust boundary.
- Re-exports in `bridge/__init__.py` preserve `from bridge import X` for backwards-compatible imports; new code can import directly from sub-modules.

### What phase 3 should read first

1. [`current-phase-status.md`](./current-phase-status.md) — this phase's frozen state, including risks + decisions + deferred items.
2. [`docs/HOLDSPEAK_BRIDGE.md`](../../../../docs/HOLDSPEAK_BRIDGE.md) — runbook, troubleshooting, operational shape.
3. `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md` — canonical wire contract.
4. [`evidence-story-02.md`](./evidence-story-02.md) — the live UDP-fix trace; the lessons there about audio transport will inform how to wrap audio in TLS / a tunnel.
5. `pm/roadmap/aipi-lite/phase-3-cross-network-transport/` — phase-3's scaffolding (already opened in `4e51684`).

## Final asset / test posture

- **Tests:** 98 cases across 10 files (`test_audio.py`, `test_models.py`, `test_reconnect.py`, `test_holdspeak_leg.py`, `test_device_leg.py`, `test_device_methods.py`, `test_dispatch.py`, `test_lcd_helpers.py`, `test_settings.py`, `test_protocol_sync.py`).
- **Coverage:** 62% overall, 100% on `holdspeak_proto`, 59% on `bridge.*`. Gap is CLI entrypoints (`_run` / `_check` / `_send_test_audio` / `_audio_loopback`); deliberately not chased to 100% because the alternative is "fake everything" mocks with poor return on maintenance cost.
- **Lint:** `ruff` 0.15.12 with rule set `E F I B C4 UP ISC`; clean.
- **CI:** GitHub Actions on push + PR; Python 3.10/3.11/3.12 matrix; concurrency cancellation. First run pending the close-out push.
- **LOC:** `bridge/` package totals 1802 LOC across 10 modules (largest: `cli.py` at 466, `device.py` at 436, `holdspeak.py` at 427); was a 1500 LOC monolith before AIPI-2-08.
- **Documentation:** runbook at `docs/HOLDSPEAK_BRIDGE.md` (8 sections); recovery doc at `docs/DEVICE_AUDIO_OUTPUT.md`; top-level `README.md` aligned with the new architecture.
- **Memory entries created this phase:** `aipi-holdspeak-integration.md` (integration shape), `feedback-esphome-voice-assistant-udp.md` (UDP-first lesson).

---

This summary is immutable per `~/dev/HoldSpeak/pm/roadmap/roadmap-builder.md` §2.5. If phase 2 needs to be re-opened (e.g., a hardware-smoke regression that needs structural fix rather than a follow-up story), open a new phase 2.5 rather than editing this file.
