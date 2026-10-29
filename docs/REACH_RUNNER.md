# Reach Runner

Reach Runner is a standard-library Python client for a remote HoldSpeak hub.
It calls the Streamable HTTP MCP endpoint, requests one Heartbeat sweep, then
starts the configured Steward run for each selected Project Room. It does not
run a second hub, own a Desk database, or install a scheduler.

## Before you start

- Run Python 3 on the runner machine.
- Keep the hub running and reachable at its MCP address.
- Enable the remote Streamable HTTP listener on the hub.
- Issue a scoped agent credential with the palette required by the runner.
- Configure the Project Watches and Steward policy on the hub.

The runner cannot wake a stopped hub, configure assignments, or widen its
palette. Use HTTPS when the deployment terminates TLS.

## Install the script

Copy [reach_runner.py](../scripts/reach_runner.py) to the runner machine. It
uses only Python's standard library:

```sh
scp scripts/reach_runner.py user@RUNNER_HOST:~/reach_runner.py
```

## Store the scoped credential

1. Open **Settings > This Mac** on the hub. Switch the hub row to `REMOTE ON`.
2. In the `CREDENTIALS` section, select **Issue credential**. Pick the **Palette** that the runner needs, then select **Issue**.
3. Save the displayed token in a private file on the runner machine.
4. Restrict the file permissions.

   ```sh
   chmod 600 ~/.holdspeak-token
   ```

The hub stores only the token hash. Live credentials are reloaded from the
credential ledger after a hub restart; revoke the credential or issue a new
one when its scope or lifetime must change.

## Run once

Replace `HUB_ADDRESS`, `PORT`, and `PROJECT_ID`:

```sh
python3 ~/reach_runner.py \
  --hub https://HUB_ADDRESS:PORT \
  --token-file ~/.holdspeak-token \
  --rooms PROJECT_ID \
  --poll 5 \
  --timeout 900
```

Use `--rooms all` to list active, non-archived Projects through the caller's
palette. The runner sends the credential only as
`Authorization: Bearer <token>`. It refuses a token in the URL.

| Argument | Default | Meaning |
| --- | --- | --- |
| `--hub` | Required | Hub base URL |
| `--token-file` | Required | File containing the scoped credential |
| `--rooms` | `all` | Comma-separated Project IDs, or all active Projects |
| `--poll` | `5` | Seconds between Steward status reads |
| `--timeout` | `900` | Maximum wait for one Steward run |

The console label `cadence_run_now` refers to the Heartbeat tool call used by
the script. It does not invoke the separate Cadence engine. The hub still
applies the Heartbeat, Project, Steward, and operation policies.

## Inspect the result

The script prints a timestamped transcript. The terminal outcome is also in
the hub's run and Receipt records. The exit codes are:

| Code | Meaning |
| --- | --- |
| `0` | All requested calls completed, or a configured Steward was disabled or in cooldown |
| `1` | A tool failed, or a Steward run failed or timed out |
| `2` | Connection or MCP initialization failed |
| `3` | Credential was missing or refused |
| `4` | The credential palette refused a required tool |

An exit code does not prove an external effect. Read the operation and
destination record before repeating an uncertain run.

## Schedule repeated runs

Run one manual trial first. Then configure cron, a system timer, or another
scheduler on the runner machine. The runner machine's time zone controls the
schedule unless your scheduler says otherwise.

```cron
0 22 * * * python3 /home/user/reach_runner.py --hub https://HUB_ADDRESS:PORT --token-file /home/user/.holdspeak-token --rooms PROJECT_ID >> /home/user/reach.log 2>&1
```

Disable that scheduler entry to stop future starts. It does not cancel a run
already admitted on the hub. Use the hub's run control for that run.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Hub cannot be reached | Check the hub process, listener, network path, TLS, and machine sleep state. |
| Credential fails after restart | Issue a new credential and replace the token file. |
| Palette is refused | Issue a credential with the required palette, or remove the unsupported call from the job. |
| Steward run is refused | Read the Project policy and the typed refusal. |
| Polling reaches the timeout | Read `project.get_steward_run` and the Receipt before retrying. |
| Scheduled runs stop | Check the external scheduler and whether the hub was running at the scheduled time. |

## See also

- [Automation](AUTOMATION.md): manual and recurring execution paths.
- [MCP sidecar](MCP_SIDECAR.md): transport, tools, and palette rules.
- [Control mode](SECURITY.md#control-mode): authority and grants.
- [Operations](OPERATIONS.md): hub health and recovery.
