# Control modes, decisions, and grants

Use Control mode to choose how future operations ask for authority. The default
is **YOLO**. YOLO lets an eligible effect run inside its configured scope without
another HoldSpeak approval prompt.

HoldSpeak records three things apart:

| State | Question |
| --- | --- |
| `ReviewDecision` | Is the proposed content accepted or dismissed? |
| `AuthorizationState` | May this effect occur? |
| `ExecutionState` | Did execution start, complete, fail, or become unavailable? |

An accepted proposal does not prove that its effect ran. Check the execution
state and the Receipt before you report completion. The commitment label on an
operation names the intended effect, for example **Approve and send to Slack**.

## Set the Control mode

The modes are **Secure**, **Normal**, and **YOLO**. They apply to operations
created after the change. The saved values are `safe`, `neutral`, and `yolo`.

Change the mode in Web **Settings**, in native Settings on a paired device, or
with the CLI:

```console
holdspeak control-mode
holdspeak control-mode secure
holdspeak control-mode normal
holdspeak control-mode yolo --json
```

Without an argument, the command shows the current mode.

## What each mode does

| Family | Secure | Normal | YOLO |
|---|---|---|---|
| Dictation commit | Preview before typing | Follow the preview setting | Commit directly |
| Coder steering | Exact pane grant, up to 5 minutes | Exact pane grant, up to 15 minutes | Direct text and allowed-key delivery to the registered pane. No arm prompt. |
| Slack, webhook, or GitHub write | Per-action authorization or an exact short grant | Per-action authorization or an exact short grant | Direct run for a configured fixed destination. No HoldSpeak approval prompt. |
| Cadence | Explicit `run-now`. No background loop. | A configured cadence can run | A configured cadence can run |

The resolver applies this order every time:

1. Hard invariants.
2. Revocation.
3. An exact scoped grant.
4. Control mode.
5. The feature default.

An unsupported operation family is refused. It never inherits a permissive YOLO
default.

A mode change revokes active reusable grants and in-memory Coder pane grants. A
change to a configured Slack, webhook, or GitHub destination revokes the reusable
grants for the old configuration.

### Coder steering

A session name is not enough to identify a destination. The pane snapshot gives
the expected tmux `%N`. Every delivery resolves the current registry target again
and sends only to that pane. A missing, gone, or changed pane is refused before
any key is sent.

Secure and Normal use the bounded in-memory pane grant. YOLO uses the central
policy decision for a registered session or an exact `pane:%N`. The key
allow-list, payload, pane identity, audit, and source-linked Receipt always apply.
Killing a session keeps its own grant and confirmation.

## Grants

A reusable grant binds these fields:

- the actor
- the operation family and effect
- the normalized fixed destination
- the data classes
- the project or resource scope
- the expiry
- the maximum use count

A grant holds no payload and no credentials. Each use writes an append-only use
receipt. Revocation takes effect at once. A mismatch in payload, destination,
identity, expiry, count, or configuration is refused before any egress.

A grant can come only from an existing fixed-destination proposal. The API does not
accept a newly found destination as grant input.

## Limits that no mode weakens

Authentication, secret custody, destination binding, payload binding, pane
identity, audit receipts, configuration integrity, and schema safety apply in all
three modes. YOLO removes repeat confirmation only inside authority that you
already bounded. It is not a bypass.

## Troubleshooting

| Problem | Action |
| --- | --- |
| An approval did not give the expected result | Read the execution state and the terminal Receipt. Fix the executor failure it names. |
| A reusable grant stopped working | Check the expiry, use count, destination changes, revocation, and mode changes. |
| A Coder delivery is refused | Check the current pane identity and the grant or mode. |
| YOLO does not admit an operation | Read the refusal. Unsupported families and hard invariants still apply. |

## See also

- [Authority model](AUTHORITY_MODEL.md): how the runtime enforces this.
- [Automation](AUTOMATION.md): triggers and execution paths.
- [Threads](USER_GUIDE.md#the-thread-has-hands): per-tool policy and Thread admission.
- [Security and privacy](SECURITY.md): credentials and data boundaries.
