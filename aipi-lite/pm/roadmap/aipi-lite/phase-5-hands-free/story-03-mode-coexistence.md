# AIPI-5-03 — HOLD / WAKE / BOTH Mode Coexistence

- **Project:** aipi-lite
- **Phase:** 5
- **Status:** backlog
- **Depends on:** AIPI-5-01 (wake-word substrate), AIPI-5-02 (VAD end)
- **Unblocks:** —
- **Owner:** karol

## Problem

Different users + different contexts want different session-trigger styles: button-only (for desk use), wake-word-only (for hands-busy use), or both (for flexibility). The mode is currently implicit — wake-word is either on or off in the firmware. This story makes the mode explicit, persistent across reboots, displayed in the LCD `mode_label` slot, and toggleable via a physical gesture.

## Scope

### In

- New ESPHome `globals` field: `mode: enum(HOLD, WAKE, BOTH)`, `restore_value: true`. Default: `HOLD`.
- Mode-aware LCD `mode_label` rendering: `HOLD` / `WAKE` / `BOTH` (4 chars max — `BOTH` fits the existing TOP_LEFT slot width).
- Mode toggle: **right-button triple-tap** cycles through the modes (`HOLD` → `WAKE` → `BOTH` → `HOLD`). LCD flashes the new mode for 1.5 s on toggle.
- **Continuous-mode is retired in this story.** Right-button triple-tap previously toggled the `continuous_mode` global (AIPI-1 era). Continuous-mode was a standalone-bridge-era affordance ("re-arm `voice_assistant` indefinitely") that no longer maps to a HoldSpeak concept now that HoldSpeak owns session arbitration; meeting-mode is the host-driven equivalent for sustained streaming, and WAKE/BOTH partially subsumes the rest of the UX (wake-word → VAD-end → repeat ≈ "always listening" without an explicit toggle). The `continuous_mode` global + its `on_multi_click` handler get deleted from `aipi.yaml` as part of this story; the runbook calls out the removal.
- Mode-aware behavior:
  - `HOLD`: wake-word inference disabled (saves CPU); button-press starts sessions.
  - `WAKE`: button-press disabled (well, ignored — pressing it doesn't start a session); wake-word starts sessions.
  - `BOTH`: button + wake-word both work. Button takes priority if both fire near-simultaneously.
- Update `docs/HOLDSPEAK_BRIDGE.md` with a "Hands-free mode" section: mode meanings, how to toggle, persistence behavior, expected battery impact (wake-word has higher idle draw).

### Out

- Per-mode separate sensitivity tuning (wake-word sensitivity is a global from AIPI-5-01).
- Web/CLI mode toggle — firmware gesture only for v1.
- Time-of-day or location-aware mode switching ("WAKE during day, HOLD at night") — way out of scope.
- Mode-driven LED indication (no LED in current hardware; LCD is the indicator).

## Acceptance criteria

- [ ] `aipi.yaml` defines a mode global with three values + `restore_value: true`. Default `HOLD`.
- [ ] `refresh_mode_label` script (existing from AIPI-2-07) updated to render mode-aware text.
- [ ] Right-button triple-tap cycles `HOLD` → `WAKE` → `BOTH` → `HOLD`; flashes new mode on LCD for 1.5 s.
- [ ] Wake-word inference enabled when mode is `WAKE` or `BOTH`; disabled in `HOLD` (verified by PSRAM/CPU footprint dropping when in HOLD).
- [ ] Button-press behavior: works in `HOLD` or `BOTH`; suppressed (logged + LCD flash `Mode: WAKE`) in `WAKE`.
- [ ] `continuous_mode` global + its `on_multi_click` handler removed from `aipi.yaml`. Runbook documents the removal in a "Removed behaviors" section.
- [ ] Mode persists across reboot: cycle to `BOTH`, power-cycle device, verify on boot the LCD shows `BOTH` and behavior matches.
- [ ] Live verification of all three modes' utterance paths.
- [ ] Runbook section "Hands-free mode" added.

## Test plan

- **Unit:** none (firmware territory; mode-cycling is YAML state).
- **Manual (hardware):**
  1. Boot in default `HOLD`; verify LCD shows `HOLD`, button works, wake-word disabled (PSRAM lower).
  2. Triple-tap right button; verify LCD shows `WAKE`, wake-word works, button suppressed.
  3. Triple-tap; verify `BOTH`; both paths work.
  4. Triple-tap; verify back to `HOLD`.
  5. Power-cycle; verify mode persisted.
  6. Confirm continuous-mode is gone: triple-tap in `HOLD` no longer re-arms voice_assistant after release; pre-AIPI-5-03 firmware (if you have a copy) is the comparison baseline.

## Notes

- **Continuous-mode retirement decided 2026-05-10.** Right-button triple-tap previously toggled the `continuous_mode` global; this story repurposes the gesture for HOLD/WAKE/BOTH and **deletes** the continuous-mode global + handler. Rationale: continuous-mode was a standalone-bridge-era affordance that no longer maps to HoldSpeak's session-arbitration model; meeting-mode covers sustained streaming host-side; WAKE/BOTH covers the per-utterance "no button press" UX. Phase 2's deferred "continuous-mode revisit" item is resolved here as **retire**. Forward-pointer to anyone reading phase 2's deferred list: the revisit landed in AIPI-5-03, decision was retire.
- **Why button-press is suppressed in `WAKE` rather than just no-op:** the user might genuinely want a fast manual override (e.g., they don't want to wait for wake-word in a noisy room). One could argue button-press should always work; that's `BOTH`. Keeping `WAKE` strictly wake-only makes the mode meaningful + documents-without-special-cases.
- **PSRAM footprint check is the cleanest way to verify wake-word disabled:** ESPHome reports PSRAM usage; record numbers in HOLD vs. WAKE/BOTH; if there's no delta the wake-word component isn't actually being conditionally-loaded.
- **Battery impact:** wake-word inference is a continuous load; expect noticeable battery-life delta in WAKE/BOTH vs. HOLD. Document in story notes after measuring.
