# Phase 5 — Hands-free (Wake-word + On-device VAD)

**Last updated:** 2026-05-10 (phase opened).

## Goal

Voice typing without a button press. Wake-word triggers a session; on-device VAD ends it on silence; user can choose `HOLD` (button) / `WAKE` (wake-word) / `BOTH` mode and the choice persists across reboots. Hands-busy scenarios (cooking, ad-hoc thinking, driving-context) become viable.

This phase **succeeds phase 4** logically (active-device feedback substrate makes wake-word UX legible — the LCD shows you when it's listening) but is independent of phase 3 (cross-network) and phase 4 (active device); it can ship at any time once phase 2's bridge spine is in place.

## Scope

### In

- ESPHome `micro_wake_word` integration on the AIPI-Lite (ESP32-S3 + octal PSRAM has the headroom).
- Wake-word fires `voice_assistant.start` → bridge already maps to `StartFrame` (no bridge change for the trigger path).
- VAD-driven session end via ESPHome `voice_assistant`'s `silence_detection` (or equivalent); fires `voice_assistant.on_end` → bridge already maps to `StopFrame`.
- Maximum session duration cap (default 30 s) to prevent runaway sessions.
- LCD feedback: `Wake  >>` flash on wake; `Saving  ...` flash on VAD-end (both reuse existing activity-symbol map).
- New mode global (`HOLD` / `WAKE` / `BOTH`), persisted via `globals` + `restore_value: true`.
- Mode toggle: triple-tap right button cycles modes; LCD flashes new mode for 1.5 s.
- Mode-aware `mode_label` rendering in TOP_LEFT slot.

### Out

- Custom-trained wake-word model. Use ESPHome's bundled set; document the chosen model. Custom training is its own story if no bundled model fits.
- Wake-word during meetings — meeting-mode keeps streaming continuously; wake-word is a session-trigger UX, not a meeting-control UX.
- Per-mode separate sensitivity tuning — wake-word sensitivity is a single global from story 01.
- Web/CLI mode toggle — firmware gesture only for v1.
- Multi-language wake-word.

## Exit criteria (evidence required)

- [ ] AIPI-5-01: wake-word triggers an end-to-end session (wake → speak → transcript types into focused host app); 30-min ambient false-positive rate measured + recorded.
- [ ] AIPI-5-02: VAD ends session within ~1.5 s of silence; max-duration cap enforced; both verified live on hardware.
- [ ] AIPI-5-03: HOLD / WAKE / BOTH modes cycle via triple-tap; persist across reboot; `mode_label` reflects current; per-mode behavior verified (button works in HOLD/BOTH; wake works in WAKE/BOTH).
- [ ] PSRAM + idle CPU footprint of wake-word inference documented in story notes.
- [ ] Runbook section "Hands-free mode" added to `docs/HOLDSPEAK_BRIDGE.md`.
- [ ] Compatibility verified: wake-word + meeting-mode coexist without false-trigger spam during a meeting.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| AIPI-5-01 | ESPHome `micro_wake_word` integration | backlog | [story-01-wake-word.md](./story-01-wake-word.md) | — |
| AIPI-5-02 | VAD-driven session end | backlog | [story-02-vad-session-end.md](./story-02-vad-session-end.md) | — |
| AIPI-5-03 | HOLD / WAKE / BOTH mode coexistence | backlog | [story-03-mode-coexistence.md](./story-03-mode-coexistence.md) | — |

(Status values: `backlog`, `ready`, `in-progress`, `blocked`, `done`, `cancelled`.)

## Where we are

Phase opened 2026-05-10. Pickup order: **AIPI-5-01** (wake-word substrate) → **AIPI-5-02** (VAD end, piggybacks on the wake-triggered session shape) → **AIPI-5-03** (mode UX closes the loop). Live-hardware testing required throughout — false-positive rate is not measurable in unit tests; ambient acoustic environment is the test.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Bundled `micro_wake_word` models don't reliably pick up the user's voice | medium | Story-01 tests multiple bundled models; document chosen + sensitivity setting | If best model has > 5 % miss rate at normal speech volume after tuning, escalate to a custom-model story (out of phase scope) |
| Wake-word inference burns enough CPU/PSRAM to destabilize aioesphomeapi | low | Story-01 measures footprint; if API flaps, deprioritize wake-listen during established sessions | If aioesphomeapi disconnects > 1×/hour during wake-listen, story-01 stops + redesign |
| Triple-tap mode-cycle conflicts with existing continuous-mode triple-tap on right button | medium | Phase 2 noted continuous-mode is *orthogonal* to HOLD/WAKE/BOTH; story-03 must verify independence | If triple-tap unexpectedly toggles continuous-mode while in WAKE, redesign gesture (e.g., left-button triple-tap, but conflicts with AIPI-1-05) |
| VAD silence threshold tuning is environment-specific (cafe vs. office vs. home) | medium | Default tuned for typical home/office; expose as config | If users report frequent premature session ends, surface threshold via `bridge.env` or ESPHome global |
| Wake-word false-positive during a meeting causes spurious `StartFrame` (HoldSpeak ignores attached-device starts, but bridge-side noise) | low | Bridge logs at INFO not WARNING when start is server-no-op; meeting-mode sticky activity prevents LCD double-paint | If log pollution becomes meaningful, gate wake-word emission on "not in meeting" sticky check |

## Decisions made

- 2026-05-10 — **Use ESPHome's bundled wake-word models**, not custom-trained. Custom training is its own story when no bundled option works.
- 2026-05-10 — **Default mode is `HOLD`** (preserves existing UX). Users opt-in to wake-word via the mode toggle.
- 2026-05-10 — **Mode global is orthogonal to continuous-mode global**: HOLD/WAKE/BOTH controls *how a session is started*; continuous-mode controls *whether `voice_assistant.start` re-arms after each utterance*. Both can be `true`/`false` independently.

## Decisions deferred

- Continuous-mode reinterpretation under HoldSpeak (right-button triple-tap currently re-arms voice_assistant indefinitely; phase 2 deferred this; phase 5's mode global may absorb it cleanly — revisit at story-03 close).
- Per-app wake-words / multi-utterance command grammar ("Hey HoldSpeak record" vs. "Hey HoldSpeak summarize") — phase 6+ idea, gated on phase-5 field experience.
- Wake-word pre-roll (preserve the ~250 ms before wake-detected to capture the first syllable of the actual utterance) — ESPHome's `voice_assistant` likely already does this; verify in story-01 and document, raise its own story if absent.
