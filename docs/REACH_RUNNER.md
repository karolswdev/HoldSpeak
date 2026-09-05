# Reach Runner

A dependency-light Python 3 MCP client that connects to a HoldSpeak
hub's Streamable HTTP endpoint, triggers the sweep and the steward's
drafter for each active Room, and disconnects.

Runs on any machine with `python3` (stdlib only -- no pip install).
Designed for the `.43` box on the tailnet.

## Install

Copy the script:

```
scp scripts/reach_runner.py user@192.168.1.43:~/reach_runner.py
```

## Credential

Issue a scoped credential in Settings > System > REMOTE ACCESS >
Issue credential.  Copy the token into a file on the .43 box:

```
echo 'YOUR_TOKEN_HERE' > ~/.holdspeak-token
chmod 600 ~/.holdspeak-token
```

The token is shown once at issue time.  If the hub restarts, the
in-memory credential store is wiped -- re-issue.

## Run

```
python3 ~/reach_runner.py \
  --hub http://100.64.0.2:8765 \
  --token-file ~/.holdspeak-token \
  --rooms all \
  --poll 5 \
  --timeout 900
```

Arguments:

| Flag | Default | Description |
|------|---------|-------------|
| `--hub` | required | Hub URL (tailnet address + port) |
| `--token-file` | required | Path to a file containing the bearer token |
| `--rooms` | `all` | Comma-separated project IDs, or `all` |
| `--poll` | `5` | Steward run poll interval (seconds) |
| `--timeout` | `900` | Steward run timeout (seconds) |

## Schedule (cron)

```cron
0 22 * * * python3 /home/user/reach_runner.py --hub http://100.64.0.2:8765 --token-file /home/user/.holdspeak-token >> /home/user/reach.log 2>&1
```

Or with a systemd timer:

```ini
# ~/.config/systemd/user/reach-runner.timer
[Unit]
Description=HoldSpeak overnight sweep

[Timer]
OnCalendar=*-*-* 22:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# ~/.config/systemd/user/reach-runner.service
[Unit]
Description=HoldSpeak reach runner

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/user/reach_runner.py --hub http://100.64.0.2:8765 --token-file /home/user/.holdspeak-token
```

```
systemctl --user enable --now reach-runner.timer
```

## Prerequisites

The hub must be awake when the runner connects.  macOS puts the machine
to sleep when the lid closes.  Two options:

1. System Settings > Energy Saver > "Prevent automatic sleeping when
   the display is off" (requires AC power).
2. `caffeinate -s` in a terminal before closing the lid (keeps the
   system awake on AC power until killed).

If the Mac is asleep, the runner prints `HUB ASLEEP OR OFF` and exits
with code 2.  It does not retry.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All calls succeeded |
| 1 | One or more tool calls failed or a steward run timed out |
| 2 | Connection refused (hub asleep or off) |
| 3 | Credential refused (401/403 or missing token file) |
| 4 | Palette refused (MCP-005) |

## Transcript

The runner prints one line per step with UTC timestamps:

```
[2026-09-05 22:15:01] CONNECT hub=http://100.64.0.2:8765 protocol=2025-03-26 identity=holdspeak-mcp
[2026-09-05 22:15:02] CALL cadence_run_now
[2026-09-05 22:15:14] OK sweep completed
[2026-09-05 22:15:15] CALL project_run_steward project=gov
[2026-09-05 22:17:42] OK steward_run completed run_id=abc123 project=gov
[2026-09-05 22:17:43] DISCONNECT
```

The token never appears in stdout or stderr.

## Receipts on the desk

Every remote call lands a kernel receipt with `origin: remote` and the
caller's IP.  The receipt rows in the shade and the Room's observer
carry the `REMOTE` badge:

```
SWEEP -- 32 ENTITIES -- REMOTE -- 192.168.1.43 -- 22:15
STEWARD RUN -- draft -- REMOTE -- 192.168.1.43 -- 22:17
```
