# HS-32-03 — Converge audio ownership

- **Status:** done (2026-06-02). Evidence: [evidence-story-03.md](./evidence-story-03.md).

## Goal

Collapse the three inconsistent audio-ownership models — hotkey, device, and
meeting — onto the single `VoiceTypingSession` owner contract. Today hotkey and
device go through `VoiceTypingSession`'s single-owner lock but `MeetingSession`
constructs its own recorder and bypasses it entirely, so "two things grabbed the
mic" is possible and untested.

## Scope

- First, understand *why* the meeting path bypasses `VoiceTypingSession` today
  (it likely needs concurrent system+mic capture) — understanding the constraint,
  not preserving the bypass. Greenfield: if the cleanest single model means
  meeting capture behaves slightly differently, that's acceptable, as long as the
  real capture paths still work.
- Route all three through one ownership arbiter with a single, testable owner
  model and defined precedence.

## Test plan

- Concurrency test: hotkey acquire while a meeting owns the device (and vice
  versa) resolves through the single owner model deterministically.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- The real-audio paths remain covered by the existing `metal` tests (run locally
  when hardware is available — note in evidence whether that was possible).

## Done when

- [x] One ownership model arbitrates hotkey / device / meeting capture.
- [x] A concurrency test demonstrates mutual exclusion / defined precedence.
- [x] No working capture path regresses; full suite green; ruff clean.

## Evidence

[evidence-story-03.md](./evidence-story-03.md). `VoiceTypingSession` gained
source-less `acquire`/`release`; the meeting holds the shared floor (rejecting
hotkey/device `begin()` and being rejected while they record); redundant hotkey
meeting-guards removed — the arbiter is the single decision point. New
`TestAudioFloorArbitration` (7 tests incl. a concurrency mutual-exclusion test).
Suite green **1946/14**. Real-audio paths stay `metal`-gated (not runnable
remotely).
