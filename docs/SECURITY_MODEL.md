# Security model

This page maps runtime controls to source. [Security and privacy](SECURITY.md)
is the user contract.

## Limits

HoldSpeak is local-first, single-user software with cooperating processes. It is
not an OS sandbox. A same-user process can launch code, open sockets, and read
files outside the hub. The main SQLite data and config are plaintext. People
uses a separate encrypted store with native key custody.

## Trust-boundary map

| Boundary | Control |
| --- | --- |
| Caller to edge | Principal derivation and deny-by-default route rights |
| Edge to kernel | Declared operation, hard prerequisites, and policy |
| Kernel to executor | Signed warrant, exact envelope, revocation, deadline, and claim |
| Executor to provider | Frozen destination and operation-family policy |
| Completion to Desk | Durable receipt before publication |

These controls apply only to paths that use the kernel.

## Identity and credentials

`holdspeak/principals.py` defines owner, agent, node, scheduler, service, and
none principals. A request body cannot choose its principal. Agent credentials
are stored as token hashes in memory and a restart clears them. This does not
protect against a memory dump or a compromised user account.

## Kernel controls

Admission binds operation name, version, target, placement, policy version,
authority basis, principal identity, and idempotency. A changed envelope under
the same principal and key is refused.

The journal is append-only and hash chained. Receipts are immutable. The
recursive content filter rejects named audio, PCM, token, and token-stream
fields. It does not classify arbitrary prompt, transcript, or completion
strings.

The executor checks warrant, envelope, revocation, deadline, ancestor liveness,
and claim identity. A late executor cannot turn an `indeterminate` operation
into success.

## Control mode and effect policy

`holdspeak/operation_policy.py` defines `safe`, `neutral`, and `yolo`.
Its hard invariants cover authentication, secret custody, destination and payload binding, pane identity, receipts, configuration integrity, and schema safety. Unknown families are refused.

YOLO reduces repeated confirmation only inside a configured fixed scope. It does
not waive those invariants or the People refusal rules.

## Data handling and egress

The normal database can hold transcripts, meeting intelligence, activity
records, operation metadata, and receipts. Model calls use a frozen deployment
revision and route. A fallback is a new child with a new receipt.

`kernel_parent_runs.input_json` stores caller input snapshots.
The filter excludes named audio, PCM, and token fields, but it does not reject
every prompt or transcript string.

People content has a separate encrypted boundary. See [People security
boundary](PEOPLE_SECURITY.md).

## Failure and recovery

Startup reconciles abandoned parent runs, recovers inference route executions,
reaps expired claims, and recovers projection stages. A lost response becomes a
refusal or `indeterminate`, not an assumed success. Read the Receipt and journal
before retrying an external effect.

## Open limits

- The application does not provide OS isolation for arbitrary plugins.
- Normal SQLite storage is not encrypted by the application.
- A provider can retain data after HoldSpeak sends it.
- Generated boundary inventories are lexical audit leads, not proof of complete
  dynamic coverage.

## Gate preview limit

Gate argument previews redact secrets, then truncate canonical JSON.
The digest is computed from the unredacted canonical JSON. The returned preview
is still sensitive tool content. It can contain prompt or non-secret text that
the redactor does not classify.

## See also

- [Security and privacy](SECURITY.md)
- [Authority model](AUTHORITY_MODEL.md)
- [Gate](GATE.md)
