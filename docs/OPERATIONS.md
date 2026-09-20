# Operations

This runbook is based on source inspected at snapshot
`675401a857b85336d4acaa8c65383dfc9636e4c8` (2026-09-19). It describes
operator-visible paths and their evidence. It does not claim that a local
machine has been configured or healthy. The focused tests named here were
inspected but not run in this documentation lane.

## Startup and normal health

The database is reconciled when the runtime opens it. The kernel startup path
then performs parent recovery, liveness recovery and projection repair in that
order (`holdspeak/kernel/runtime.py:138-175`). A restart can therefore emit
refusal or `indeterminate` terminal evidence for work whose execution outcome
cannot be proved. Read the receipt before retrying an external effect.

The CLI exposes:

```console
holdspeak doctor
holdspeak doctor --strict
holdspeak doctor --connectors
```

The parser defines those options in `holdspeak/main.py:348-365`. A normal
doctor exits non-zero for failures; `--strict` also treats warnings as
failures, while `--connectors` lists connector packs and skips other checks
(`holdspeak/commands/doctor.py:1454-1485`).

The local doctor checks runtime, config, database, microphone and
transcription, web runtime/auth, meeting intelligence and egress, endpoint
health, trust destinations, profiles and inference targets, mesh edges,
dictation, MIR telemetry, hotkeys/text injection/clipboard, ffmpeg/pactl/audio
capture, connector discovery, People key custody, agent capability ledger and
the tool-call gate (`holdspeak/commands/doctor.py:1267-1310`). Some checks may
inspect configured or remote endpoints. Network preflight can be skipped by
the code-level `skip_network` path; this page does not prescribe a shell flag
that the current parser does not define.

Doctor is diagnostic. It does not run a full migration test, prove all tables
are current, or prove a provider will complete a future request. Its database
check confirms readability and table presence, while reconciliation occurs on
normal database open (`holdspeak/commands/doctor.py:58-110`).

## Complete check-function inventory

The [doctor branch reference](generated/doctor-checks.json) records each check's
condition source, success/warning/failure result expressions and repair text.
It is generated without executing checks or contacting configured endpoints.
Use the condition source for exact platform branches; a function name alone
does not establish applicability. `holdspeak/commands/doctor.py` owns the local
CLI checks; `holdspeak/doctor.py` owns the remote/runtime diagnostic helpers.

| Check | Source | Result branches |
| --- | --- | ---: |
| `_check_runtime` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L58) | 1 |
| `_check_database` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L71) | 4 |
| `_check_config` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L126) | 3 |
| `_check_microphone` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L157) | 3 |
| `_check_transcription_backend` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L183) | 2 |
| `_check_hotkey` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L207) | 3 |
| `_check_text_injection` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L232) | 3 |
| `_check_clipboard_tools` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L257) | 5 |
| `_check_web_runtime` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L294) | 2 |
| `_check_ffmpeg` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L313) | 2 |
| `_check_pactl` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L328) | 3 |
| `_check_system_audio_capture` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L350) | 3 |
| `_check_meeting_intel_runtime` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L378) | 3 |
| `_check_meeting_intel_egress` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L463) | 3 |
| `_check_trust_destinations` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L511) | 2 |
| `_check_web_auth` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L531) | 1 |
| `_check_meeting_intel_cloud_preflight` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L553) | 14 |
| `_check_dictation_project_context` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L705) | 4 |
| `_check_runtime_profiles` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L755) | 3 |
| `_check_inference_targets` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L834) | 2 |
| `_check_mesh_edges` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L873) | 3 |
| `_check_dictation_runtime` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L910) | 6 |
| `_check_dictation_constraint_compile` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1000) | 5 |
| `_check_dictation_runtime_counters` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1072) | 3 |
| `_check_mir_routing` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1114) | 4 |
| `_check_mir_telemetry` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1171) | 2 |
| `_check_connector_packs` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1204) | 2 |
| `_check_endpoint_health` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1243) | 2 |
| `_check_people_keystore` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1313) | 2 |
| `_check_agent_capabilities` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1351) | 2 |
| `_check_tool_call_gate` | [`holdspeak/commands/doctor.py`](../holdspeak/commands/doctor.py#L1379) | 3 |
| `_check_hub_health` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L85) | 3 |
| `_check_runtime_status` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L95) | 3 |
| `_check_runtime_preflight` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L109) | 4 |
| `_check_websocket` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L123) | 5 |
| `_check_desk_bootstrap` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L152) | 3 |
| `_check_auth` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L162) | 4 |
| `_check_mcp_server` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L174) | 4 |
| `_check_inference` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L229) | 5 |
| `_check_database` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L245) | 2 |
| `check_observer` | [`holdspeak/doctor.py`](../holdspeak/doctor.py#L257) | 3 |

A zero branch count means the function delegates result construction; it does
not mean the check cannot fail. Inspect the included source and called helper.
Regenerate with `python scripts/philo_doctor_reference.py`; `--check` detects
changes to these conditions and result messages.

## Database backup and restore

Use the built-in commands:

```console
holdspeak backup
holdspeak restore
holdspeak restore <backup-file>
holdspeak restore <backup-file> --yes
```

`holdspeak backup` writes a timestamped sibling and prints its path;
`holdspeak restore` with no file lists siblings; restore confirmation can be
skipped with `--yes` (`holdspeak/commands/backup.py:15-80`). The database
primitive uses SQLite's backup API, validates a restore candidate, refuses a
live owner or unsafe target, makes a safety backup, replaces the file and
removes stale WAL/SHM sidecars (`holdspeak/db/core.py:72-202`).

Before restore:

1. Stop the hub and any process that owns the database.
2. Keep the printed safety-backup path.
3. Choose the candidate by its timestamp and inspect the printed source.
4. Restore, start the hub, and run `holdspeak doctor`.
5. Check the application records and kernel receipts before resuming work.

The database snapshot does not automatically include config, audio, browser
history copies, browser local storage or the encrypted People sidecar. See
[STORAGE_AND_MIGRATIONS.md](STORAGE_AND_MIGRATIONS.md) and
[SECURITY.md](SECURITY.md) for those boundaries.

## Runtime and executor procedures

The kernel HTTP surface has separate routes for read, submit, decision, event
cursor, executor claim, executor receipt and reconcile
(`holdspeak/web/routes/system/kernel_routes.py:21-121`). Keep these roles
separate:

- an owner or permitted agent submits a declared operation;
- the owner decides when policy requires review;
- a node/executor claims only with a valid warrant;
- the executor writes one native and kernel receipt;
- the reconciler resolves liveness and staged publication after restart.

Do not post a result by impersonating an owner route, pass authority fields in
the submit envelope, or treat an HTTP provider response as success before the
receipt exists. The [authority model](AUTHORITY_MODEL.md) and
[kernel contract](KERNEL.md) give the state and refusal details.

For mesh serving, the CLI requires a node token environment variable or
imported pairing custody; the owner token is not a mesh fallback. The parser
supports:

```console
holdspeak mesh serve [--hub URL] [--node NAME] [--token-env ENV] [--once]
```

(`holdspeak/main.py:376-413`). `--once` claims at most one job and exits. A
mesh node is a `node` principal and cannot use owner decision rights.

## Authority and secret custody checks

Control mode can be inspected or changed through the CLI using `secure`,
`normal`, `yolo` and their persisted `safe`/`neutral` aliases
(`holdspeak/main.py:312-335`). Mode changes revoke applicable active grants
and affect future operations. Use [AUTHORITY.md](AUTHORITY.md) for the
operator-facing matrix and [AUTHORITY_MODEL.md](AUTHORITY_MODEL.md) for the
runtime gates.

The doctor deliberately surfaces key custody. A development People file
keystore is a warning, not production custody; the check calls out when both
development and native sidecars exist (`holdspeak/commands/doctor.py:1313-1348`).
The tool-call gate is healthy when off by default, healthy and fail-closed
when fully armed, and a warning when only half opted in
(`holdspeak/commands/doctor.py:1379-1408`).

## Operator evidence

Record these facts when diagnosing or handing off an incident:

| Evidence | Why it matters |
| --- | --- |
| Source snapshot or branch SHA | Runtime contracts can drift; this lane documents `675401a…` |
| Doctor output and exit mode | Distinguishes warnings, failures and connector-only checks |
| Database path, backup path and timestamps | Makes restore scope auditable |
| Operation id, parent id, state, receipt id and outcome | Binds runtime claims to durable evidence |
| Principal kind and target | Shows whether the caller was owner, agent, node or scheduler |
| Egress destination/revision and refusal code | Shows where data could leave and why work stopped |

Do not record prompt, transcript, audio, completion, credentials or token
streams in the generic kernel handoff. The kernel's prohibited journal keys
are declared in `holdspeak/kernel/model.py:9-13`.

## Routine failure handling

| Symptom | First action | Escalation boundary |
| --- | --- | --- |
| Hub will not answer | Run local doctor, then the remote hub checks against `/health` | Do not retry an unreceipted external effect blindly |
| Doctor reports database warning | Preserve the file, take a copy if readable, let normal reconcile report shape | Restore only from a validated backup with the hub stopped |
| Work is `indeterminate` | Read the terminal receipt and journal event | Treat as unknown completion; inspect destination before any compensating action |
| Agent receives 403 | Check principal derivation, credential expiry/revocation and route right | Agent cannot self-upgrade to owner/decider |
| Node cannot claim | Check node token, exact target, warrant, deadline and ancestor liveness | Re-admit a new operation only after resolving the old receipt |
| People doctor warning | Unset development file keystore for real use and verify native key custody | Do not copy the People sidecar into normal DB storage |

For state-specific recovery, use [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Verification limits

No doctor command, backup, restore or live hub was run for this documentation
lane. The source and focused assertions were inspected only. In particular,
the exact output on a user's machine depends on its OS, configured providers,
database path, credentials and network. Report those as observed facts only
after collecting the relevant output.
