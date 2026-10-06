# Operations

Use this runbook to check that HoldSpeak is healthy, to back up and restore
the database, and to run a mesh node. For a specific failure, read
[Troubleshooting](TROUBLESHOOTING.md).

## Check health

Run the doctor after you install, after you upgrade, and when something fails.

```console
holdspeak doctor
holdspeak doctor --strict
holdspeak doctor --connectors
```

- `holdspeak doctor` exits with a non-zero code when a check fails.
- `--strict` also treats warnings as failures.
- `--connectors` lists the connector packs and skips all other checks.

The doctor checks these areas:

- runtime, config, database
- microphone, transcription, hotkey, text injection, clipboard
- `ffmpeg`, `pactl`, system audio capture
- web runtime and web authentication
- meeting intelligence and its egress
- endpoint health, trust destinations, profiles, inference targets, mesh edges
- dictation and MIR telemetry
- connector packs
- People key custody, agent capabilities, the tool-call gate

Some checks contact configured endpoints. The doctor reports what it finds.
It does not prove that a provider will complete a future request.

The [doctor check reference](generated/doctor-checks.json) lists each check,
its condition and its repair text. Regenerate it with
`python scripts/philo_doctor_reference.py`. The local checks are in
`holdspeak/commands/doctor.py`. The checks for a running hub are in
`holdspeak/doctor.py`.

### Check the running hub

A new checkout does not change a running hub. The hub keeps the code and web
bundle it loaded at start. Open **Settings**, then **System**, to see what the
hub loaded: version, revision, bundle, schema version and process start. The
**RAW** fold shows the database path and the process id.

The block shows a token when something does not match:

| Token | Meaning | Action |
| --- | --- | --- |
| `STALE BUNDLE` | The bundle on disk differs from the bundle the process loaded, or no bundle exists. | Restart the hub. Or run `npm --prefix web run build`. |
| `TWO RUNTIMES` | Another hub owns this database. | Stop the other hub. |
| `SCHEMA AHEAD` | The database is newer than this build. | Run a newer build, or restore a backup. |
| `SCHEMA BEHIND` | The database is older than this build expects. | Run the matching build, or restore a backup. |

### One hub owns the database

A second `holdspeak web` on the same database refuses to start. The message
names the process that holds the database, its port and its start time. Two
hubs would run the scheduled work twice.

The owner lock is a file next to the database, `holdspeak.db.owner.lock`. The
operating system releases it when the process exits. A crashed hub leaves
nothing to clean up.

For diagnosis only, set `HOLDSPEAK_ALLOW_UNOWNED_DB=1`. The hub then starts
with scheduled work off and shows `TWO RUNTIMES`.

## Back up and restore the database

```console
holdspeak backup
holdspeak restore
holdspeak restore <backup-file>
holdspeak restore <backup-file> --yes
```

1. Run `holdspeak backup`. It writes a timestamped file next to the database
   and prints the path.
2. Run `holdspeak restore` with no file to list the backups.
3. Stop the hub and every tool that holds the database. Restore refuses
   while another process has it open.
4. Run `holdspeak restore <backup-file>`. Add `--yes` to skip the
   confirmation.
5. Start the hub and run `holdspeak doctor`.
6. Check your records and receipts before you continue work.

Restore validates the file first. It saves a safety copy of the current
database, then replaces the file. It removes the stale `-wal` and `-shm`
files. If the file is missing, truncated or not a HoldSpeak database, restore
stops and changes nothing. Keep the printed safety-copy path.

The backup holds the main database only. These items are outside it:

- The People store, `people.v1.sqlite3`. It has its own keys. Back it up
  separately.
- Credentials in the operating system keychain. Reconnect the accounts after
  a restore.
- Config and audio files.

See [Storage and migrations](STORAGE_AND_MIGRATIONS.md) and
[Security](SECURITY.md) for these limits.

## Restart behavior

When the hub starts, it opens the database and repairs its shape. Then it
recovers parent work, checks liveness and repairs projections, in that order.

After a restart, work whose result cannot be proved ends as `indeterminate`
or refused. Read the receipt before you retry any external effect. The state
table in [Troubleshooting](TROUBLESHOOTING.md) lists each case.

## Run a mesh node

A mesh node serves this machine's model to the hub.

```console
holdspeak mesh serve [--hub URL] [--node NAME] [--token-env ENV] [--once]
```

- `--hub` sets the hub URL. The default is `http://127.0.0.1:8765`.
- `--node` sets the node name. The default is the device mesh name.
- `--token-env` names the environment variable that holds the node token.
  The default is `HOLDSPEAK_NODE_TOKEN`. If it is unset, the command uses the
  imported pairing token.
- `--once` claims at most one job and exits.

The owner token does not work as a node token. A node cannot use owner
decision rights.

## Control mode

```console
holdspeak control-mode
holdspeak control-mode secure|normal|yolo
```

The command shows or sets the mode for future operations. A mode change
revokes the active grants that it affects. See [Authority](AUTHORITY.md) for
the rules and [Authority model](AUTHORITY_MODEL.md) for the runtime gates.

## Record facts for an incident

Collect these facts when you diagnose a problem or hand it to someone:

- the branch or commit of the build
- the doctor output and its exit code
- the database path, backup path and timestamps
- the operation id, state, receipt id and outcome
- the principal kind: owner, agent, node or scheduler
- the egress destination and the refusal code

Do not record prompts, transcripts, audio, credentials or tokens in a handoff.
