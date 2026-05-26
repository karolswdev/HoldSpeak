# Evidence — HS-22-03 Bridge Companion Polling And Display Wiring

Date: 2026-05-24

## Scope Completed

- Added `aipi-lite/bridge/companion_status.py`.
- Wired `CompanionStatusPoller` into the bridge runtime in `aipi-lite/bridge/cli.py`.
- Added `COMPANION_POLL_INTERVAL_S` setting and documented it in `bridge.env.example`.
- Added focused coverage in `aipi-lite/tests/test_companion_status.py`.

## Behavior

- The bridge polls `http://<holdspeak>/api/companion/status`.
- Fresh waiting-agent sessions paint the LCD middle zone with
  `<Agent> waiting: <question>`.
- If the agent stops waiting, the poller clears only the agent text it
  previously painted.
- The poller does not clear unrelated middle-zone content such as transcript
  flashes.
- Device reconnect marks companion state dirty so an active agent question
  repaints after ESPHome LCD services are cached.

## Validation

```text
scripts/aipi_test.sh -q tests/test_companion_status.py tests/test_companion_state.py tests/test_companion_gestures.py tests/test_settings.py
36 passed in 0.19s

scripts/aipi_test.sh -q
194 passed in 7.53s

cd aipi-lite && .venv/bin/ruff check .
All checks passed!

git diff --check
passed
```

## Hardware Preflight

A temporary HoldSpeak web runtime was started on `127.0.0.1:38271`.

```text
HOLDSPEAK_PORT=38271 scripts/aipi_bridge.sh --check
OK: udp + device + holdspeak handshake successful
```

The live bridge was then run against the plugged-in AI PI for seven seconds:

```text
timeout 7 env HOLDSPEAK_PORT=38271 scripts/aipi_bridge.sh
connect.holdspeak.handshake.ok
connect.device.ok host=aipi-green.local
udp.allowlist ips=["192.168.1.19"]
update_link.ok
update_screen.ok msg="Ready"
subscribe.voice_assistant.ok
shutdown.complete
```

`/api/companion/status` also returned the expected v1 shape with
`agent.awaiting_response=false`, `runtime.voice_state="idle"`, and companion
query names `agent_question` / `agent_status`.
