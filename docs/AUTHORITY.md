# Control modes, decisions, and grants

Control mode describes how a concrete operation obtains authority. It does not
decide whether a model answer is correct. The default is **YOLO**.

HoldSpeak records three states apart:

| State | Question |
| --- | --- |
| `ReviewDecision` | Is the proposed content accepted or dismissed? |
| `AuthorizationState` | May this exact effect occur? |
| `ExecutionState` | Did execution start, finish, fail, or become uncertain? |

An accepted proposal does not prove that an effect ran. Read the operation state
and terminal Receipt.

## Set the Control mode

The modes are **Secure**, **Normal**, and **YOLO**. The stored values are
`safe`, `neutral`, and `yolo`.

Use Settings or the CLI:

```console
holdspeak control-mode
holdspeak control-mode secure
holdspeak control-mode normal
holdspeak control-mode yolo --json
```

## What each mode does

| Family | Secure | Normal | YOLO |
| --- | --- | --- | --- |
| Dictation commit | Preview can be required | Uses preview setting | Eligible commit can run directly |
| Coder steering | Exact pane grant | Exact pane grant or configured rule | Registered fixed pane can run directly |
| External write | Per-action authorization or exact grant | Per-action authorization or exact grant | Fixed configured destination can run directly |
| Cadence | Explicit run-now | Configured cadence | Configured cadence |

The resolver applies hard invariants, revocation, exact grants, control mode, and
feature defaults in that order. Unknown operation families are refused.

### Coder steering

A session name does not identify a destination by itself. The relay resolves the
current pane and checks its identity before it sends text or an allowed key.
An owner press on **Answer**, **Allow**, or **Deny** authorizes the current wait
only. A stale wait or pane is refused in every mode.

## Grants

A reusable grant binds the actor, operation family, effect class, normalized
destination, data classes, project or resource scope, expiry, and use count. It
does not hold credentials or an arbitrary payload. Each use has a receipt.

The grant API issues a grant only for a fixed-destination proposal. Revocation
and mode changes invalidate affected reusable grants.

## Limits that no mode weakens

Authentication, secret custody, destination binding, payload binding, pane
identity, audit receipts, configuration integrity, and schema safety apply in
all three modes. YOLO removes repeated confirmation only inside authority that
is already scoped.

## Calls, Phone, and Programs

**Calls** and **Phone** are optional reach surfaces. Pair a device or configure
the line in **Settings ▸ Calls ▸ Phone** before a call can leave the hub. A
message or call is a `phone.reach` operation with a reason, destination, and
receipt; no transport means a named refusal. The owner's word for each kind
(`Message`, `Call`, or `Nothing`), quiet hours, repeat suppression, and an
active-call check still apply.

**Programs** cut a goal into steps. A program or step can set `may_call`, but an
agent call without the owner's press is allowed only when that flag is set and
the Program control is not Secure. Otherwise the call waits in **Needs you** for
the owner. Silence is never consent. A Phone message has its own rate limit for
an agent step and remains separate from a call.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A review did not produce an effect | Read the execution state and terminal Receipt. |
| A grant stopped working | Check expiry, use count, destination, revocation, and mode. |
| Coder delivery is refused | Check the current pane and current agent wait. |
| YOLO does not admit an operation | Read the refusal. Hard invariants still apply. |

## See also

- [Authority model](AUTHORITY_MODEL.md): how the runtime enforces this.
- [Automation](AUTOMATION.md): triggers and execution paths.
- [The Thread has hands](USER_GUIDE.md#the-thread-has-hands): per-tool policy and Thread admission.
- [Security and privacy](SECURITY.md): credentials and data boundaries.
