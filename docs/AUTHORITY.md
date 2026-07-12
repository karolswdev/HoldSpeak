# Control modes, decisions, and grants

HoldSpeak separates three questions that used to hide behind one proposal
status:

- `ReviewDecision`: is the content accepted or dismissed?
- `AuthorizationState`: may the described effect happen?
- `ExecutionState`: has an executor started, succeeded, failed, or become unavailable?

Approving an effect does not claim that it ran. Every proposed action API returns
all three axes, its typed operation, the policy snapshot used for the decision,
and a commitment label such as **Approve and send to Slack**.

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
