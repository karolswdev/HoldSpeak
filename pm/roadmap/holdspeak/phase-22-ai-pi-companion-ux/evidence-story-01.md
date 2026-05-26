# Evidence — HS-22-01 Companion State Model And LCD Priority Contract

Date: 2026-05-24

## Scope Completed

- Added bridge-side pure companion state contract in `aipi-lite/bridge/companion_state.py`.
- Added focused tests in `aipi-lite/tests/test_companion_state.py`.
- Documented LCD zones, state ownership, priority rules, and stale-agent clearing in `companion-state-model.md`.
- Re-exported the state model from `bridge.__init__` for follow-up bridge stories.

## Contract Highlights

- Top-right link is independent and always reflects HoldSpeak connectivity.
- Bottom sticky baseline priority is reply capture, transcribing, meeting recording, then ready.
- Middle attention priority is error/busy, reply target, stale clear, fresh agent waiting, transcript flash, then clear.
- Agent questions use the existing 120-second freshness window; stale questions flash `Agent stale; cleared` instead of remaining actionable.

## Validation

```text
scripts/aipi_test.sh -q tests/test_companion_state.py tests/test_lcd_helpers.py
24 passed in 0.18s

scripts/aipi_test.sh -q
174 passed in 7.53s

cd aipi-lite && .venv/bin/ruff check .
All checks passed!

git diff --check
passed
```

## Hardware Check

The old bridge process from the pre-import sibling checkout was stopped before
validation. The unified bridge check then passed against the connected AI PI
when pointed at a temporary `holdspeak web --no-open` runtime:

```text
HOLDSPEAK_PORT=32879 scripts/aipi_bridge.sh --check
OK: udp + device + holdspeak handshake successful
```

The device advertised the expected ESPHome services:
`simulate_left_press`, `simulate_voice_typing`, `update_link`, `update_middle`,
and `update_screen`.
