# Operations

Use this runbook to check HoldSpeak health, protect the Desk database, and
recover an uncertain run. For one failure, read
[Troubleshooting](TROUBLESHOOTING.md).

## Check health

Run the doctor after install, after upgrade, and when a runtime fails:

```sh
holdspeak doctor
holdspeak doctor --strict
holdspeak doctor --connectors
```

`--strict` treats warnings as failures. `--connectors` lists connector packs
and skips unrelated checks. The checks cover runtime, configuration, database, web authentication, models, inference targets, mesh, dictation, and connectors.
They also cover People custody, agent hooks, tmux, MCP, and the running hub.

Some checks contact configured endpoints. Doctor reports current observations;
it does not prove that a future provider call will succeed.

The generated [doctor check reference](generated/doctor-checks.json) lists
conditions and repair text. Regenerate it with
`python scripts/philo_doctor_reference.py` when its source changes.

## Check the running hub

The running hub keeps the code and web bundle loaded at startup. In **Settings
> System**, inspect the version, revision, bundle, schema version, process
start, and RAW database path.

| Token | Meaning | Action |
| --- | --- | --- |
| `STALE BUNDLE` | The process bundle differs from disk. | Restart the hub or rebuild the web bundle. |
| `TWO RUNTIMES` | Another hub owns the database. | Stop the other hub. |
| `SCHEMA AHEAD` | The database is newer than this build. | Use the newer build or restore a backup. |
| `SCHEMA BEHIND` | The database is older than this build expects. | Use the matching build or restore a backup. |

## One hub owns the database

Only one `holdspeak web` can own a database. The owner lock is beside the file:
`holdspeak.db.owner.lock`. A second hub refuses to start, because two
schedulers could run the same work twice.

The local MCP sidecar is not a second hub. It reads the owner lock, sends each
JSON-RPC message to the hub's loopback `/api/mcp`, and never opens or writes
the database. The retired standalone sidecar mode is ignored.

For diagnosis only, `HOLDSPEAK_ALLOW_UNOWNED_DB=1` starts with scheduled work
off and shows `TWO RUNTIMES`. Do not use it for normal operation.

## Back up and restore the database

```sh
holdspeak backup
holdspeak restore
holdspeak restore <backup-file>
holdspeak restore <backup-file> --yes
```

1. Run `holdspeak backup` and save the printed path.
2. Run `holdspeak restore` with no file to list backups.
3. Stop the hub and every process that holds the database.
4. Restore the validated backup. Add `--yes` to skip confirmation.
5. Start the hub and run `holdspeak doctor`.
6. Inspect records and Receipts before continuing work.

Restore validates the backup, saves a safety copy of the current database,
replaces the file, and removes stale `-wal` and `-shm` files. If validation
fails, it stops without changing the database.

The main backup does not include the encrypted People store, operating-system
keychain credentials, config files, or audio files. Back up or reconnect those
separately. See [Security and privacy](SECURITY.md).

## Restart behavior

At startup the hub repairs database shape, recovers parent work, checks
liveness, and repairs projections in that order. A result that cannot be
proved becomes `indeterminate` or refused. Read its Receipt before retrying an
external effect.

## Coding-agent operations

For a launched Claude Code, Codex, or pi task, check the launch record,
worktree, hooks, tmux, and brief delivery state. The `agents.working_at_once`
setting defaults to 6. A queued hand is expected when all working slots are
full. Do not delete a worktree or a launch record to clear a stale card; use
the supported resume, stop, clear-stale, or park operation.

For an inference CLI engine, check the executable, preset, model, and provider
egress. CLI engines are not coding-agent launches. `HOLDSPEAK_CLI_ENGINES=off`
disables their discovery and execution.

## Run a mesh node

A mesh node serves this machine's model to the hub:

```sh
holdspeak mesh serve [--hub URL] [--node NAME] [--token-env ENV] [--once]
```

The default hub is `http://127.0.0.1:8765`. The default token environment is
`HOLDSPEAK_NODE_TOKEN`. An owner token is not a node token. A node cannot use
owner decision rights.

## Control mode

```sh
holdspeak control-mode
holdspeak control-mode secure|normal|yolo
```

The command reads or sets the mode for future operations. A mode change can
revoke active grants. See [Control mode](SECURITY.md#control-mode).

## Record facts for an incident

Record:

- the build branch or commit;
- doctor output and exit code;
- database and backup paths with timestamps;
- operation id, state, Receipt id, and outcome;
- principal kind: owner, agent, node, or scheduler;
- egress destination and refusal code.

Do not record prompts, transcripts, audio, credentials, or tokens in an
incident handoff.
