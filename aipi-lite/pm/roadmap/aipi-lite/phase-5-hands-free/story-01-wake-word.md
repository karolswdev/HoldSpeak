# AIPI-5-01 — ESPHome `micro_wake_word` Integration

- **Project:** aipi-lite
- **Phase:** 5
- **Status:** backlog
- **Depends on:** AIPI-2 (full phase); AIPI-1 hardware verification (mic capture path needs to be solid)
- **Unblocks:** AIPI-5-02, AIPI-5-03
- **Owner:** karol

## Problem

Voice typing today requires a button press. For seated/desk use this is fine, but for hands-busy scenarios (cooking, ad-hoc thinking, driving-context, kid-on-lap) a wake-word is the right UX. ESPHome's `micro_wake_word` integration ships TF-Lite Micro-based detection; the AIPI-Lite (ESP32-S3 + octal PSRAM) has the headroom for it.

## Scope

### In

- Add a `micro_wake_word` block to `aipi.yaml`. Pick a wake-word model from ESPHome's bundled set (e.g., `okay_nabu`, `hey_jarvis`, `alexa`) — the one with best on-this-hardware miss-rate at normal speech volume.
- On wake → trigger `voice_assistant.start` (existing handler chain — no bridge code change for the trigger path).
- LCD: 1 s flash `Wake  >>` (reuses `Listening` symbol from AIPI-2-07 map) on wake-detected, before the actual `Listening...` sticky lands.
- Configurable wake-word sensitivity via ESPHome `globals` (default: medium). The setting is an integer 0–10 mapped to model probability threshold.
- Hardware metrics captured in story notes: PSRAM usage delta with wake-word enabled vs. disabled; idle CPU%; aioesphomeapi connection stability over a 1-hour wake-listen window.
- Pre-roll verification: confirm ESPHome's `voice_assistant` captures the ~250 ms before wake-detection (so the first syllable of the actual utterance isn't clipped). If absent, document and raise a follow-up story.
- 30-min ambient false-positive test in story notes: with the device in normal conversation/background-noise environment, count spurious wakes; tune sensitivity.

### Out

- **Custom-trained wake-word model.** Use ESPHome's bundled set; document the chosen model. Custom training (espressif's tooling) is its own story when no bundled option works at acceptable miss-rate.
- Wake-word ↔ button coexistence — AIPI-5-03 owns this.
- VAD-driven session end — AIPI-5-02 owns this.
- Multi-language wake-word.
- Wake-word during meetings — meeting-mode keeps streaming continuously; wake-word is a session-trigger UX, not a meeting-control UX. Confirm story-level: wake-word should NOT trigger during a meeting (would emit a no-op `StartFrame` against an already-active recorder).

## Acceptance criteria

- [ ] `aipi.yaml` includes a `micro_wake_word` block; chosen model documented in YAML comments + story notes.
- [ ] Wake-word triggers `voice_assistant.start` (existing chain → bridge `StartFrame` → HoldSpeak session-claim).
- [ ] LCD flashes `Wake  >>` for 1 s on wake-detected.
- [ ] Wake-word sensitivity exposed as an ESPHome `global` (default mid-range).
- [ ] Compile + flash succeed; `aipi.local` boots normally; aioesphomeapi connection stable.
- [ ] Live verification: say wake-word → device captures audio → bridge forwards to HoldSpeak → transcript types into focused app on host. End-to-end latency comparable to button-press path (~2 s post-end-of-utterance).
- [ ] False-positive rate measured: 30-min ambient test results recorded in story notes.
- [ ] Memory + CPU footprint documented in story notes (PSRAM delta, idle CPU% over 1-hour window).
- [ ] Wake-word does NOT fire during a meeting (verified by sticky-activity gating, either firmware-side or bridge-side — story decides).

## Test plan

- **Unit:** none (firmware + integration territory).
- **Manual (hardware):**
  1. Flash with wake-word disabled; baseline PSRAM + CPU.
  2. Flash with wake-word enabled; record PSRAM + CPU delta.
  3. 30-min ambient false-positive test: device in normal environment; count spurious wakes.
  4. Wake-and-speak utterance test: 10 utterances; verify all are captured + typed; record miss rate.
  5. 1-hour aioesphomeapi stability test: device idle, wake-word listening; ensure no API disconnects.

## Notes

- **Bundled-model choice rationale:** ESPHome ships `okay_nabu`, `hey_jarvis`, `alexa`, etc. We don't have a "Hey HoldSpeak" model. Pick the one with the lowest miss rate + the lowest false-positive rate on this hardware in this user's voice. Document and live with it; users who want "Hey HoldSpeak" specifically can train one (out of phase scope).
- **TF-Lite Micro vs. ESP-SR:** ESPHome's `micro_wake_word` uses TF-Lite Micro per upstream; ESP-SR is the alternative path. TF-Lite Micro is the ESPHome default + the one with the biggest community model library. Stick with it unless story-01 finds a blocker.
- **Pre-roll matters.** If wake-detection fires *after* the user has already started saying "Hey nabu, what is the…", the first 200ms of the actual command can be clipped. ESPHome's voice_assistant should pre-roll; verify in story-01 — if it doesn't, raise a separate story.
- **Memory pressure on octal PSRAM:** AIPI-Lite's octal PSRAM was specced for the previous-life STT/LLM pipeline; wake-word inference uses well below that. But the device runs LVGL + WiFi + ESPHome API + voice_assistant + now wake-word concurrently. Verify steady-state under wake-listen.
