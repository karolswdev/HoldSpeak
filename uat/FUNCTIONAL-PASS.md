# Owner functional verification protocol

This is the executable HoldSpeak MVP pass. It is deliberately centered on what
the product feels like and whether its user journeys work. Database drift,
packet-capture/no-telemetry proof, crafted-schema attacks, and token-gate attack
work are not part of this pass by owner decision.

The guided site exposes nine ordered campaigns assembled from the canonical
scenario files. Campaigns 1–5 are the core owner pass. Campaign 6 is the
user-visible connectivity/integration extension. Campaign 7 is conditional on
having the two non-flagship native builds installed. Campaigns 8 and 9 are the
Phase 92 convergence close: the same ten journeys on production Web and the
physical flagship Swift root, with required raw measurements.

This protocol uses implementation target × form factor. Campaign 1 is the
`web_react:desktop` Desk leg. Campaign 5 contains the separately executed
`ios_flagship_swift:ipad` and `ios_flagship_swift:iphone` Desk/native legs.
They are complementary evidence, not the same surface at different widths.
Responsive desktop emulation is never native evidence.

## Start and resume

Desktop-only campaigns:

```bash
cd /Users/karol/dev/tools/HoldSpeak
uv run python -m uat.conductor
```

Native or cross-device campaigns:

```bash
cd /Users/karol/dev/tools/HoldSpeak
UAT_HOST=0.0.0.0 uv run python -m uat.conductor
```

Open the printed URL, start the next numbered campaign, and enable **Device
sitting** for any campaign containing a Swift target or a cross-device leg
(normally campaigns 5–7). Every campaign gets an isolated HOME and product
database. Verdicts persist immediately; reopening the sitting resumes at the
first unanswered target/form-factor slot.

Do not run the nine campaigns as one marathon. End a sitting, review its
findings, and take a real break before the next campaign. The total core pass is
about 8 hours of deliberate human work.

## Campaign map

| # | Campaign | Time | Scenarios / observations | Bootstrap | Primary boundary |
|---|---|---:|---:|---|---|
| 1 | React Web Desk foundation — desktop | 45m | 14 / 39 | 14 automatic | `web_react:desktop`; no `.43` |
| 2 | Voice and dictation loop | 105m | 18 / 60 | 10 automatic, 7 assisted, 1 hands-on | `web_react:desktop`; mic, Whisper, `.43` |
| 3 | Meetings, intelligence, and aftercare | 90m | 8 / 29 | 6 automatic, 2 hands-on | `web_react:desktop`; `.43`, audio fixture, mic/system audio |
| 4 | Agents, steering, and automation | 100m | 12 / 41 | 9 automatic, 2 assisted, 1 hands-on | React desktop; unresolved native legs remain quarantined |
| 5 | Flagship Swift iPhone and iPad, including Desk | 145m | 14 / 85 | assisted/native | `ios_flagship_swift`; physical devices and exact flagship build |
| 6 | Sync, mesh, and integrations | 135m | 18 / 56 | mixed | Explicit React/Swift handoff legs, LAN, second device, disposable targets |
| 7 | Secondary Swift shells | 70m | 6 / 17 | 3 automatic, 3 assisted | Exact companion/classic builds; conditional |
| 8 | Phase 92 ten-journey Web close | 210m | 10 measured journeys | mixed | React desktop + compact; cannot earn Swift evidence |
| 9 | Phase 92 ten-journey flagship close | 300m | 10 measured journeys | assisted/native | Physical flagship iPhone + iPad; exact build attestations |

The site shows each campaign's full preflight before it starts. A campaign's
time is a planning estimate, not a target to race.

`ios_unclassified_swift` and `legacy_unqualified` are quarantine identities,
not owner-pass targets. If either appears in a campaign or resumed snapshot, do
not cast an acceptance verdict; remove that leg from the owner campaign until
its exact implementation root is resolved.

## What “bootstrapped” means

Every scenario is one of three types, shown on the campaign card:

- **Automatic:** the conductor boots the required deck, creates exact product
  state through public HoldSpeak routes, and probes it before showing the first
  instruction. You do no setup.
- **Assisted:** the product state is automatic, but a real-world fact cannot be
  manufactured—microphone permission, a physical build, airplane mode, a live
  audio route, or a disposable connector. The site lists only those human facts.
- **Hands-on:** the behavior itself begins outside the harness, such as recording
  live audio or focusing a foreign Mac text field. The checklist is the test
  precondition, not busywork.

If staging fails, do not judge the step. Save the displayed error/log, retry
once, then mark the scenario blocked in the sitting notes and triage the staging
failure. A probe is a precondition check, never a human pass verdict.

### Exact worlds used by the pass

| World | What the conductor guarantees | Used for |
|---|---|---|
| `desk-primitives` | Known BLUEBIRD/Pylon/Questline notes, two KBs, a filed zone, recipe, chain, workflow, and profile | Desk read/open/file/create/lasso tests |
| `functional-aftercare-review` | `Owner functional review (UAT seed)` with one known pending action and one known accepted action, both owned by Karol | Consent, action review, mobile file-issue |
| `functional-proposal-review` | The accepted action above plus one real, unexecuted GitHub proposal for `acme/holdspeak-owner-uat` | Proposal queue and decision lifecycle |
| `functional-qlippy-queue` | Two real, unexecuted proposal events created only after the quiet control | Qlippy card and `+1` queue behavior |
| Pylon / Ledgerline / Questline transcript fixtures | Stable, repo-specific decisions, owners, risks, tags, and source moments | Live model intelligence and control/treatment comparisons |
| UAT tmux sessions | A named waiting coder owned and torn down by the isolated run | Peek, arm, keys, answer, kill, relay |
| `first-run-no-model` | A truly fresh, not-ready arrival | Welcome and recovery usability |

Deterministic fixtures are used for interface mechanics. Real `.43` inference is
retained where generated intelligence, grounding, routing, or degradation is the
capability being judged. This keeps wording nondeterminism out of CRUD tests
without faking the model tests.

## The per-scenario loop

Use the same loop for every scenario:

1. **Read the purpose before acting.** Identify the user goal, not just the
   control to click.
2. **Verify the staged world.** Automatic probes must be green. Complete any
   listed human preflight and record device/build/audio facts in the first note.
3. **Run the control exactly.** Do not improve the state, add context, or retry
   into a pass unless the instruction explicitly asks for it.
4. **Run the treatment exactly.** For voice/model tests, use the same words and
   change only the named input or setting.
5. **Judge the exact displayed slot.** Verify both implementation target and
   form factor before acting. Never fill a Swift iPad/iPhone verdict from React,
   a desktop viewport, or a different Swift app root.
6. **Capture usability, not merely correctness.** A technically successful but
   confusing, undiscoverable, slow, or mistrust-inducing result is `observe` or
   `partial`, not an automatic pass.
7. **Attach evidence at the moment of failure.** One screenshot and a short note
   are more useful than a retrospective essay.

For timing-sensitive flows, record an approximate wait in the note. Use this
note shape when something is not a clean pass:

```text
Goal: what I was trying to accomplish
Observed: what the product did, including visible wording/state
Expected: the smallest material difference
Recovery: whether I could recover without restarting or outside knowledge
Time: approximate delay, if relevant
```

## Usability bar

At every step, ask all six questions:

1. **Discoverable:** Could the owner find the next action without knowing the
   implementation or reading this repository?
2. **Comprehensible:** Did the UI explain the current state, target, and result
   in ordinary language?
3. **Responsive:** Did input produce immediate feedback, and did long work show
   honest progress?
4. **Recoverable:** Did cancel, retry, back, reconnect, and empty/error states
   preserve the user's work and suggest a next move?
5. **Persistent:** After refresh, reopen, or cold launch, was the completed work
   still there exactly once?
6. **Consistent:** Within the target, did the same object/action mean the same
   thing across Desk, meetings, mobile, and agent workflows? Cross-target
   consistency is judged only after both independent legs have evidence.

`pass` means the functional expectation and these usability basics held.
`observe` means the task succeeded but a usability defect deserves triage.
`partial` means the task was materially impaired. `fail` means the promised
outcome did not happen. `skip` means no answer was obtained and earns no
coverage.

## Campaign gates

### 1. React Web Desk foundation

Finish only if you can arrive, understand the four-door information
architecture, create/open/file objects, use project facts and profiles, and
recognize an unavailable runtime without help in `web_react:desktop`. A welcome
loop, dead navigation, lost primitive, or misleading readiness state is a
stop-and-triage result. This gate accepts React Desk only; it neither exercises
nor accepts Swift Desk.

### 2. Voice and dictation

Use a fixed canary phrase for persistence checks and repeat the exact same
utterance for control/treatment. Finish only if speech can be previewed,
committed, corrected, learned, and found again without duplicate typing or lost
intent. Stop on unintended text injection, a broken correction loop, or a wake
flow that types before consent.

### 3. Meetings and aftercare

Keep fixture-based UI checks separate from live-intelligence checks. Finish only
if transcript/audio/live capture becomes reviewable source-grounded work, and
the owner can understand what remains open and export it. Stop on fabricated
artifacts, permanently stuck processing, missing owners/sources, or lost audio.

### 4. Agents and automation

Read the target session before every input. Finish only if the owner can see what
needs attention, deliberately intervene, and verify the result/audit. Stop on
wrong-pane input, an unclear arm state, silent execution, or a result whose
origin cannot be understood.

### 5. Flagship native

Run on physical glass and record bundle/build, device, iOS, orientation, audio
route, inference mode, and permissions. Finish only if pairing, capture
persistence, native Desk arrival/CRUD/spatial behavior, offline use,
profiles/models, and steering work in the installed flagship root. Register and
pair-verify an exact device attestation before the first native verdict. Do not
substitute the companion/classic app, React in a device browser, or responsive
desktop emulation.

### 6. Connectivity and integrations

Use throwaway repositories/endpoints only. Finish only if sync and remote work
are understandable from the initiating surface and every proposed action can be
reviewed before it touches the disposable destination. This is a functional
workflow pass; do not expand it into network or storage hardening.
Each handoff leg retains its own target identity. A React result and a Swift
result are joined as cross-target evidence only after both legs were executed.

### 7. Secondary native shells

Run only when both exact non-flagship builds are intentionally installed. Their
results remain labeled companion/classic and never count as flagship evidence.

### 8–9. Phase 92 convergence close

Run campaign 8 on production React and campaign 9 on physical flagship iPhone
and iPad. Every prompted measurement is required for a substantive verdict and
is exported as raw debrief data. Neither campaign can borrow verdicts from the
other. Do not generate Phase 92 story evidence or a final summary until both
debriefs pass, all findings are triaged, Phase 91 is closed, and the Delivery
Workbench close gates are genuinely satisfied.

## Stop, triage, and resume

Stop the current campaign after a severity-1 event (data loss, input sent to the
wrong external target, unintended external action, or unrecoverable crash). For
ordinary defects, finish the current scenario, capture the evidence, then decide
whether later scenarios would be contaminated by the same defect.

At campaign end:

1. Finish the sitting so the debrief is generated.
2. Triage every `fail`, `partial`, and `observe`; never bulk-convert them to pass.
3. Merge duplicates by user-visible cause, not by route or stack trace.
4. Rank fixes by frequency × task blockage × daily-owner pain.
5. Resume with the next campaign only when the current findings are understood.

The MVP functional pass is complete when campaigns 1–5 have no untriaged result
and every core user journey has a direct owner verdict. Campaign 6 is the
extended connected-product pass. Campaign 7 is explicitly conditional.
Phase 92 is not closed by that MVP bar: campaigns 8 and 9 must independently
pass with raw measurements and the Delivery Workbench close conditions above.

## Explicitly outside this pass

The following remain available as reference/diagnostic scenarios but are not in
the numbered functional campaign: crafted newer-schema/backup attacks,
no-telemetry observation, off-loopback token attack, profile-secret reflection,
named-key allow-list attacks, relay payload secrecy, and duplicate smoke/honest-
failure scenarios already covered by a functional journey.

Do not block the MVP usability pass on those items and do not silently add them
back to a numbered campaign. They require a fresh owner priority decision.
