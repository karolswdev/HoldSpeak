# HoldSpeak user-acceptance charter

This is the governing protocol for a HoldSpeak acceptance sitting. The feature
ledger says what the product claims; scenario YAML says how a claim is tested;
the conductor captures what a person actually observed. Authored coverage is
not execution evidence, and a harness self-test is not a human verdict.

## Protocol v2: target first, form factor second

An execution slot is the tuple `implementation target × form factor`. A result
is valid only for the exact slot named by the scenario:

| Target | Meaning | Allowed form factors |
|---|---|---|
| `cli_python` | the local HoldSpeak Python CLI | `local_shell` |
| `web_react` | the React Web Desk served by the isolated product run | `desktop`, `ipad_browser`, `iphone_browser`, `tablet_viewport` |
| `ios_flagship_swift` | the current production/TestFlight Swift root | `ipad`, `iphone` |
| `ios_companion_swift` | the separately built Swift companion shell | `ipad`, `iphone` |
| `ios_classic_swift` | the Swift classic/demo root, only when intentionally installed | `ipad`, `iphone` |

`local_shell` means the local terminal/CLI implementation. `desktop`,
`ipad_browser`, and `iphone_browser` mean a real browser environment.
`tablet_viewport` means desktop browser emulation and is React-only layout
evidence. `ipad` and `iphone` mean the physical native form factors running the
named Swift binary. Form factor is never implementation identity.

These targets are not interchangeable. Resizing a desktop browser, using
responsive mode, or opening React in Safari on an iPad does not exercise Swift
and cannot fill `ios_*_swift:ipad`. Likewise, a Swift pass says nothing about
React. Code compiled into an Xcode target but unreachable from its installed
root is not an exposed capability. Unresolved native roots remain diagnostic
and quarantined; they cannot produce acceptance evidence.

The former “web/iPad/iPhone—three surfaces, one script” doctrine is superseded.
Parity is now a join across independently executed target-specific legs. A
React Desk pass and a Swift Desk pass may be compared only after each has its
own direct verdict and provenance.

## Roles

- The human tester owns verdicts and physical-device facts.
- The conductor owns isolation, staging, transitions, isolated Python-product
  logs, timestamps, and immutable protocol evidence. Native-client logs are not
  automatically collected; the debrief says so instead of implying otherwise.
- The reviewing agent correlates findings and logs, proposes hypotheses, and
  helps convert triaged `fix` findings into roadmap backlog entries.
- Product code is not fixed during the sitting. Reproduce and triage first;
  implementation follows through the normal product workflow.

## Entry gate

Before the first verdict:

1. Record the exact git commit and execution target. The conductor
   snapshots the commit, ledger, scenarios, recipes, decks, and content hashes.
2. Use an isolated run. Never point a UAT native client at the owner's live hub.
3. For a native sitting, start with `UAT_HOST=0.0.0.0`, select **Device sitting**,
   pair the named Swift app to the displayed LAN URL/token, and prove a
   deterministic seed reads back.
4. Register a native device attestation for each target/form-factor pair. It
   records target, form factor, device name, OS, bundle ID, build number,
   installation source, and the human confirmation that pairing was verified.
   A native verdict remains locked without an exact matching attestation.
5. Record orientation/size class, permissions, audio route, inference
   mode/model, and any required second device/Pencil/connector in the scenario
   evidence.
6. A recipe probe or manual preflight must be complete before its first beat.
   A failed state transition blocks the next beat; it is never waved through.

## Verdicts

| Verdict | Meaning |
|---|---|
| `pass` | the stated expectation was met on this exact target/form-factor slot |
| `fail` | the expectation was not met or a trust/safety promise broke |
| `partial` | useful behavior worked, but a material part of the bar did not |
| `observe` | the bar passed, but a bug-hunt/UX/performance observation needs triage; a note is required |
| `skip` | no answer was obtained; this never earns executed coverage |

Verdicts are cast only from direct observation of the named slot. A person
looking at React in an iPad-sized Mac browser must not fill a Swift iPad slot;
a person holding an iPad must still distinguish `web_react:ipad_browser` from
`ios_flagship_swift:ipad`. A fail, partial, or observe should carry a concise
note; attach a screenshot when it materially reduces ambiguity.
Non-deterministic output is judged structurally on the promised decision,
owner, risk, source, type, and provenance—not exact prose.

## Sitting rules

- Stage, then walk. A state change between control and treatment is a durable
  server transition and must verify before the treatment is judged.
- Every LLM claim gets a genuine control and treatment that differ by one named
  input. If the UI cannot produce the alleged OFF state, the protocol is wrong.
- Every pack closes with an honest failure/control. Refusal must be fast and name
  the unavailable endpoint, node, permission, or policy.
- Mutating CRUD protocols need a fresh state per execution slot unless cross-device
  propagation is itself the claim. Shared-state results must say so.
- A scenario contains one implementation target. If a journey crosses React
  and Swift, author target-specific legs and state the handoff; do not reuse one
  generic instruction as if the controls were identical.
- `unknown` in the ledger is a research obligation, not a denominator escape.
  On-glass exploratory scenarios may resolve it; `n/a` means genuinely absent.

## Exit and acceptance

A sitting can be recorded only when every applicable slot has a verdict and all
required state transitions completed. The debrief reports:

- `passed`: no fail, partial, or skip;
- `passed-with-observations`: acceptance passed but observations require triage;
- `inconclusive`: at least one partial or skip;
- `failed`: at least one fail.

Release acceptance additionally requires the exact release target/build, all
release-critical target/form-factor slots, matching native attestations, no
untriaged findings, no unresolved severity-1/2 defects, and retained debrief +
artifacts. Planned/authored coverage is shown separately from executed coverage.
“Desk parity” is never inferred from one leg: React Desk and Swift Desk must
both have independent accepted evidence before their results are joined.

## Findings lifecycle

Fail, partial, and observe verdicts become one stable finding per scenario step,
wearing all applicable slot outcomes within its target. Triage each to `fix`,
`wont-fix`, `by-design`, or `duplicate`, with a disposition. Corrected verdicts
remove stale findings so an old defect cannot leak into a later backlog block.

## Current release blockers

The protocol preserves the gaps found in the 2026-07-09 audit:

- several iPad claims belonged to the companion or unreachable classic Swift
  root rather than the installed flagship;
- the old corpus treated web/iPad/iPhone as interchangeable “surfaces” and
  therefore could not distinguish responsive React from Swift;
- protocol v2 now records a structured, pairing-verified native device
  attestation and binds every native verdict to it, but that attestation is a
  human assertion—not cryptographic device identity;
- native-client diagnostics are not yet collected automatically; attach them
  to a finding when a Swift-only failure needs more than a screenshot and note;
- manual preflight is persisted as a scenario confirmation, but not as one
  evidence row per checklist item;
- legacy scenario-level feature citations still need migration to step-level
  `verifies` attribution before all coverage is fine-grained traceability;
- mutable CRUD is still one shared run across form factors unless the protocol
  explicitly restages.

Until those are closed, use the rig for disciplined dogfooding and defect
discovery; do not call the whole product release-accepted.
