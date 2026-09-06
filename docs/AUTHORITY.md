# Control modes, decisions, and grants

Use Control mode to choose how future operations request authority.
The default is **YOLO**, which permits eligible effects within configured scope without another HoldSpeak approval prompt.

HoldSpeak records content review, authorization, and execution separately:

| State | Question |
| --- | --- |
| `ReviewDecision` | Is the proposed content accepted or dismissed? |
| `AuthorizationState` | May this effect occur? |
| `ExecutionState` | Did execution start, complete, fail, or become unavailable? |

An accepted proposal does not prove that its effect ran.
Inspect the execution state and Receipt before you report completion.
The operation's commitment label describes the intended effect, such as **Approve and send to Slack**.

## Control mode

Secure, Normal, and YOLO are presets for future operations. The persisted wire
values remain `safe`, `neutral`, and `yolo`. Change the mode in Web Settings,
native Settings on a paired device, or the CLI:

```console
holdspeak control-mode
holdspeak control-mode secure
holdspeak control-mode normal
holdspeak control-mode yolo --json
```

The resolver always applies the same precedence:

1. hard invariants;
2. revocation;
3. an exact scoped grant;
4. Control mode;
5. the feature default.

Unsupported operation families refuse. They never inherit a permissive YOLO
default.

| Family | Secure | Normal | YOLO |
|---|---|---|---|
| Dictation commit | Preview before typing | Follow the configured preview setting | Commit directly |
| Coder steering | Exact pane grant, up to 5 min | Exact pane grant, up to 15 min | Direct text/allowed-key delivery to the registered pane; no arm prompt |
| Slack/webhook/GitHub write | Per-action authorization or exact short grant | Per-action authorization or exact short grant | Direct execution for a configured fixed destination; no HoldSpeak approval prompt |
| Cadence | Explicit `run-now`; no background loop | Configured cadence may run | Configured cadence may run |

Changing modes affects operations created afterward. Changing a configured
Slack, webhook, or GitHub destination revokes reusable grants bound to the old
configuration. Changing modes revokes active reusable grants and in-memory
Coder pane grants; a Coder attempt resolved afterward uses the new posture.

Coder steering never treats a session name as sufficient destination identity.
The read-side pane snapshot supplies the expected tmux `%N`; every delivery
re-resolves the current registry target and sends only to that canonical pane.
A missing, gone, or changed pane refuses before a keystroke. Secure and Normal
use the existing bounded in-memory grant. YOLO uses the central posture decision
for a registered session or exact `pane:%N`, while the key allow-list, payload,
pane identity, audit, and source-linked Receipt remain mandatory. Destructive
session factory operations retain their separate grant/confirmation path until
that operation family receives its own policy treatment.

## Grants

A reusable grant binds the actor, operation family and effect, normalized fixed
destination, data classes, project/resource scope, expiry, and maximum use
count. It contains neither payload nor credentials. Each consumption is an
append-only use receipt, and revocation is immediate. A payload, destination,
identity, expiry, count, or configuration mismatch refuses before egress.

Grants can only be issued from an existing fixed-destination proposal. The API
does not accept an arbitrary newly discovered destination as grant input.

## Invariants that modes cannot weaken

Authentication, secret custody, destination binding, payload binding, pane
identity, audit receipts, configuration integrity, and schema safety run in all
three modes. YOLO reduces repeated confirmation only inside authority the owner
already bounded; it is not a bypass.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Approval did not produce the expected result | Inspect execution state and the terminal Receipt. Resolve the named executor failure. |
| A reusable grant stopped working | Check expiry, use count, destination changes, revocation, and Control mode changes. |
| A Coder delivery is refused | Check the current pane identity and the applicable grant or mode. |
| YOLO does not admit an operation | Read the refusal. Unsupported families and hard invariants still apply. |

## See also

- [Automation](AUTOMATION.md): triggers and execution paths.
- [Threads](USER_GUIDE.md#the-thread-has-hands): per-tool policy and Thread admission.
- [Security & Privacy](SECURITY.md): credentials and data boundaries.
