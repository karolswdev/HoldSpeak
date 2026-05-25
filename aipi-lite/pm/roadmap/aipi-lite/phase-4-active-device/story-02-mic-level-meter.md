# AIPI-4-02 — Mic-Level Meter on LCD Activity Slot

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** backlog
- **Depends on:** AIPI-2-07 (LCD activity-slot substrate)
- **Unblocks:** —
- **Owner:** karol

## Problem

During an active session the LCD shows `Listening...  >>` but gives the user no signal that audio is *actually flowing*. A mic-level RMS bar in the activity slot makes the device feel responsive — the user sees their voice, immediately, on the device they're holding. This is the kind of detail that makes the device feel *alive* rather than instrumented.

The open question is whether the ESPHome `update_screen` API can sustain ~8 Hz updates without jacking up roundtrip latency or destabilizing the aioesphomeapi connection. Story starts with a measurement spike; if the cost is too high, the story closes with documented "infeasible at scale."

## Scope

### In

- **Spike (story-internal, before any feature path):** push 8 Hz `update_screen` calls for 30 s on live hardware; measure roundtrip latency p50/p95/p99; record in story notes.
- **Tier the implementation by spike result:**
  - p95 < 50 ms → ship at 8 Hz update rate.
  - p95 50–100 ms → ship at 4 Hz.
  - p95 > 100 ms → close story as "infeasible at scale" with notes; bridge code reverts.
- New module `bridge/audio_meter.py`: RMS computation over 120 ms (8 Hz) or 250 ms (4 Hz) windows of UDP audio bytes; dB-FS conversion; ASCII bar formatter (8 chars).
- Active only during a session — sticky activity matches `Listening*` or `Recording*` (NOT during meetings — see Out).
- Throttle: skip pushes when the rendered bar is identical to the previous frame (silence stretches don't generate API noise).
- Render format: `<sticky-text>  ▇▆▅▄▃▂` if Montserrat 10 has block glyphs; ASCII fallback `[####    ]` otherwise.
- Tests: `tests/test_audio_meter.py` — RMS computation across silence/loud fixtures, dB-FS mapping, bar formatting, throttle dedup.

### Out

- **Mic-meter during meetings.** Meetings stream continuously; the cost of 8 Hz pushes for an hour is meaningfully different from a 5-second voice-typing session. Revisit if metrics permit.
- Per-channel meters (the device is mono).
- Showing the meter on HoldSpeak's web UI (server doesn't know about it).
- Adaptive update-rate (could in principle slow to 1 Hz in long-silent stretches; not worth the complexity for v1).

## Acceptance criteria

- [ ] **Spike phase 1:** 30 s of 8 Hz `update_screen` pushes against live device; p50/p95/p99 latency recorded in story notes.
- [ ] **Implementation tier picked** per the spike result (8 Hz / 4 Hz / abort); decision recorded in story notes with the latency table.
- [ ] If implementing: `bridge/audio_meter.py` exists; computes RMS over 120 ms (8 Hz) or 250 ms (4 Hz) windows; converts to dB-FS; maps to 0..7 bar levels.
- [ ] Bar string rendered into the activity slot via `update_screen`; format reuses sticky-text + bar (`Listening  ▇▆▅▄▃▂`).
- [ ] Active only when sticky activity matches `Listening*` or `Recording*`; **silenced during meetings** even if sticky says `Recording`.
- [ ] Throttle: identical-bar dedup verified (silence stretches don't fire API calls).
- [ ] On session end, revert handled by existing `_paint_activity` revert mechanic (no new code path).
- [ ] Tests passing; lint clean.

## Test plan

- **Spike (manual, hardware):** `--audio-loopback` with the meter feature flag enabled; capture aioesphomeapi roundtrip latency for 30 s; produce table.
- **Unit:** RMS computation (silence → 0; full-scale sine → max bar); dB-FS mapping linearity at quantization boundaries; bar string equality dedup.
- **Integration:** mock `update_screen` recorder; feed simulated UDP datagrams via the audio queue; assert pushed-bar count + content.
- **Manual:** speak into the device during a voice-typing session; verify the bar moves with voice; verify silence shows minimum bar; verify session-end leaves sticky text intact.

## Notes

- **Why a spike instead of just shipping:** ESPHome's `update_screen` is an API service call, which goes through the aioesphomeapi reactor + a TCP roundtrip. We don't know empirically what the latency budget is on this hardware build (depends on WiFi RSSI, ESPHome's API thread scheduling, LVGL redraw budget). Better to measure than guess.
- **ASCII fallback:** if Montserrat 10 doesn't have ▁▃▅▇ block glyphs, use ASCII `[####    ]` (8 columns, fill chars + space chars). AIPI-4-04 (LVGL symbols) may resolve glyph-coverage uncertainty before this story; coordinate.
- **Meeting suppression rationale:** mic-meter during meeting = ~28,800 update_screen calls/hour at 8 Hz. Even if each call is cheap, that's a sustained API load that competes with `update_link` heartbeats and any future API traffic. Voice-typing sessions are seconds-long; the cost there is bounded.
- **Cooperation with AIPI-4-04:** if LVGL builtin block-character glyphs render, the bar can use those; otherwise ASCII. This story doesn't block on AIPI-4-04 (ASCII works either way).
