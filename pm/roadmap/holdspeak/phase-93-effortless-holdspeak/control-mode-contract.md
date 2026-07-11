# Control posture product contract

**Decision date:** 2026-07-11<br>
**Status:** Phase-93 target contract; not a claim about current implementation.

## Product intent

Control posture answers one question: **how much should HoldSpeak interrupt me
before it acts?** It is an automation posture, not an inference profile and not
a switch that disables correctness.

The product labels are:

- **Secure** — cautious and deliberately interruptible;
- **Normal** — useful defaults with confirmation at genuinely consequential
  boundaries;
- **YOLO** — zero HoldSpeak approval prompts for eligible configured actions;
  things happen and leave receipts.

The existing wire values remain compatible during migration:

| Product label | Current wire value | Migration rule |
|---|---|---|
| Secure | `safe` | clients render Secure; APIs continue accepting/returning `safe` until a versioned wire change is justified |
| Normal | `neutral` | clients render Normal; this remains the default posture |
| YOLO | `yolo` | label and wire already align |

Do not create another generic Profile. The architecture noun remains
`ControlMode` or `ControlPosture`.

## What zero approvals means

In YOLO, HoldSpeak itself does not ask for a per-action confirmation, reusable
grant, arm gesture, or second human decision before an eligible operation runs.
The selected posture is the authority basis.

Zero approvals does **not** mean:

- bypassing macOS/iOS microphone, filesystem, notification, or accessibility
  permission owned by the operating system;
- inventing credentials, pairing, endpoints, repositories, panes, or connector
  configuration that does not exist;
- allowing an LLM or remote payload to introduce an arbitrary destination or
  executable capability outside the owner's configured/registered set;
- weakening authentication, secret custody, destination or payload integrity,
  pane identity, configuration integrity, audit/receipts, or schema safety;
- hiding what happened.

These are prerequisites and correctness invariants, not approval UX. A missing
prerequisite refuses with a named recovery action in every posture.

## Intended policy matrix

The detailed operation registry remains typed. This table defines the default
human-interruption posture; a direct gesture, existing scoped grant, or explicit
feature setting may reduce interruption in Secure/Normal only when its authority
is equally clear.

| Operation family | Secure | Normal | YOLO |
|---|---|---|---|
| Basic same-device dictation | preview before commit | commit directly unless preview preference is on | commit directly |
| Dictation to paired device/app | show destination and confirm delivery | direct hold/release gesture authorizes delivery | deliver directly |
| Same-device read/organize/edit | execute direct user gestures; preview bulk/destructive work | execute | execute |
| Local or explicitly selected inference run | show scope/target for new or unusually broad data; direct Run authorizes ordinary use | direct Run authorizes | run automatically when invoked/scheduled |
| Paired/private/external inference | confirm new boundary or changed scope; grants remain short | direct Run on a visible selected target authorizes | run without prompt on configured target |
| Slack/GitHub/webhook/other external write | per-action approval unless an exact short grant exists | approval for new destination/scope; configured scoped grant may automate | execute without HoldSpeak approval on configured registered destination |
| Coder steering and key/shell effects | explicit short arm/grant; destructive operations remain individually visible | direct session arm or scoped grant; bounded automation | no arm/approval prompt for registered session/capability; pane identity and receipts remain mandatory |
| Sync and cadence/background work | manual start or explicit narrow schedule | configured cadence runs | configured work runs; eligible agent-initiated work may run |
| Destructive local mutation | explicit confirmation unless undo/transaction makes consequence safely reversible | confirm irreversible operations; reversible direct gestures execute | execute registered operation without prompt, with receipt and recovery/undo where possible |

## Shared policy and client expression

The hub owns one versioned operation description and policy decision. React and
Swift must not maintain private mode matrices.

Both clients:

- show Secure, Normal, or YOLO on the Desk as system posture, not only in
  Settings;
- explain the practical effect near an imminent consequential action;
- allow changing posture from a Desk trust/system inspector and a focused
  Settings workspace;
- show when the change takes effect and never retroactively widen an existing
  proposal or attempt;
- snapshot posture, policy version, authority basis, destination, effect, and
  outcome on every consequential Receipt;
- render the same refusal reason when a hard prerequisite or invariant fails;
- preserve platform-native controls, warnings, sheets, motion, and haptics.

## Coverage rule

`current_behavior` is not an acceptable Phase-93 outcome for a consequential
operation that appears in a primary journey. The operation registry and policy
matrix must cover dictation, meeting/capture side effects, inference, workflow
runs, Integrations, Coder steering/factory operations, sync, cadence/background
work, and destructive Desk mutations.

Unsupported third-party/plugin operations fail closed and explain that their
control posture is not declared. YOLO never turns an unknown operation into an
allowed one.
