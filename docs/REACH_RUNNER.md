# Reach Runner

Use Reach Runner to request a Heartbeat sweep and Steward runs from another machine.
The script uses the HoldSpeak remote MCP endpoint and Python's standard library.

## Before you start

- Install Python 3 on the runner machine.
- Keep the HoldSpeak hub running and reachable.
- Enable Reach and issue a scoped credential for the required tools.
- Configure the Projects and Steward policies that the run will use.

The script does not wake an unavailable hub or configure its model assignments.
An external scheduler is required when you want the script to repeat.
See [Reach](USER_GUIDE.md#reach) for remote access setup.

## Install the script

Copy [reach_runner.py](../scripts/reach_runner.py) to the runner machine.
For example, replace `RUNNER_HOST` with your SSH host:

```sh
scp scripts/reach_runner.py user@RUNNER_HOST:~/reach_runner.py
```

No additional Python packages are required by the script.

## Store the scoped credential

1. Open **Settings > System** on the hub.
2. Use **REMOTE ACCESS > Issue credential** with the required scope.
3. Save the displayed token in a private file on the runner machine.
4. Restrict the file permissions.

   ```sh
   chmod 600 ~/.holdspeak-token
   ```

The command examples below pass the file path, not the token value.
The token appears only once when issued.
The hub stores Reach credentials in memory. A hub restart requires a new credential.

## Run once

Replace `HUB_ADDRESS` and `PORT` with your reachable hub address and port.
Replace `PROJECT_ID` with the Project you intend to run.

```sh
python3 ~/reach_runner.py --hub http://HUB_ADDRESS:PORT --token-file ~/.holdspeak-token --rooms PROJECT_ID --poll 5 --timeout 900
```

Use HTTPS when your configured deployment terminates TLS.
The access boundary is the one configured for Reach.
See [Security & Privacy](SECURITY.md) for remote transport requirements.

| Argument | Default | Meaning |
| --- | --- | --- |
| `--hub` | Required | Reachable hub base URL |
| `--token-file` | Required | File containing the scoped credential |
| `--rooms` | `all` | Comma-separated Project IDs, or all Projects returned to the caller |
| `--poll` | `5` | Seconds between Steward status reads |
| `--timeout` | `900` | Maximum wait for each Steward run, in seconds |

The runner first calls `heartbeat.run_now` for a Heartbeat sweep.
Its console label for that call is `cadence_run_now`.
That label does not mean it invoked the separate Cadence system.
It then requests the applicable Steward runs and polls their results.
Each service still applies its own policy and permissions.

## Inspect the result

The script prints timestamped steps and the terminal outcome.
Its exit code identifies the broad failure class:

| Code | Meaning |
| --- | --- |
| `0` | All requested calls completed successfully |
| `1` | A tool call failed or a Steward run exceeded the timeout |
| `2` | The connection or initialization failed, including an unavailable hub |
| `3` | The credential was missing or refused |
| `4` | The tool palette was refused |

Inspect the terminal output for the specific reason.
Use the hub's run and Receipt records to inspect the underlying work.
A remote call carries its remote origin in the execution record.

## Schedule repeated runs

After a successful manual trial, configure your operating system's scheduler.
The schedule uses the runner machine's time zone unless you configure a different one.
The hub must remain available at the scheduled time.

Example cron entry for 22:00 each day:

```cron
0 22 * * * python3 /home/user/reach_runner.py --hub http://HUB_ADDRESS:PORT --token-file /home/user/.holdspeak-token --rooms PROJECT_ID >> /home/user/reach.log 2>&1
```

Replace the paths, address, port, and Project ID before installing the entry.
Remove or disable that scheduler entry to stop future starts.
Disabling the scheduler does not cancel a run that already started.
Use the relevant run control on the hub for that operation.

## Troubleshooting

| Problem | Action |
| --- | --- |
| The hub cannot be reached | Check the process, network path, listener, and machine sleep state. |
| The credential fails after restart | Issue a new scoped credential and replace the private token file. |
| The palette is refused | Check that the credential permits the required tools. |
| A Steward run is refused | Inspect the Project policy and the named service refusal. |
| A timed-out run has an uncertain outcome | Inspect the run record before you repeat it. |

## See also

- [Automation](AUTOMATION.md): manual and recurring execution paths.
- [Reach](USER_GUIDE.md#reach): transport and credential setup.
- [MCP sidecar](MCP_SIDECAR.md): tool names and permission boundaries.
- [Control modes](AUTHORITY.md): operation authority.
