# Effortless HoldSpeak — remediation baseline

**Captured:** 2026-07-11<br>
**Repository:** `main` at `1e6a28f3`<br>
**Nature of evidence:** source inspection, roadmap state, focused automated
checks, and the UAT closeout report. No physical-device or stopwatch result is
invented here.

## 1. Why remediation exists

The adoption/adoptability/usability assignment produced a complete Phase-92
plan and was followed by six large implementation commits. The work is real:

- 293 files changed from the Phase-91 merge base;
- approximately 17,800 additions and 1,500 deletions;
- new contracts for product language, inference destinations, authority,
  invocation attempts, relationships, capture recovery, and Desk projections;
- Python, React, and Swift automated checks for those contracts.

The user outcome is not yet established:

- Phase 92 is formally 0/10 stories done;
- 27 of 72 story acceptance boxes are checked;
- the phase folder contains no evidence files, screenshots, or final summary;
- the Phase-92 closeout reports missing Phase-91 closure and missing Web/native
  campaign debriefs;
- the UAT database has no physical-device attestation;
- there is no observed before/after time-to-value or comprehension result.

Phase 93 is not a rejection of the substrate. It is the delivery boundary for
the experience the substrate was meant to enable.

## 2. Preserved substrate

| Substrate | Current value | Phase-93 rule |
|---|---|---|
| `docs/product-language.json` and client adapters | one compatibility-aware vocabulary source | use it to delete visible drift; do not add a second registry |
| InferenceTarget and Runs-on picker | named destination classes and placement receipts | present it only when a run needs placement; never reteach provider architecture |
| OperationDescriptor, PolicyDecision, Grants | central authority semantics and hard invariants | surface the consequence and mode context at the action point |
| capability Invocation/Attempt/Artifact refs | retained run input, attempts, placement, and result lineage | make retry and return-to-subject effortless |
| QualifiedRefs and relationship stores | Zone, Knowledge, and Project axes no longer collide | make them understandable without three setup lessons |
| capture journals and provisional Meetings | durable identity and bounded-loss recovery substrate | prove it under real duration, interruption, disk, and sync faults |
| Desk attention/receipt projections | one non-sensitive read model over authoritative records | attach it to subjects; do not become another global product |
| React single surface and Swift Desk roots | viable primary clients | simplify actual navigation and journeys rather than replace either client |

## 3. Visible complexity baseline

| Surface | Reproduced baseline | Remediation direction |
|---|---|---|
| Web primary navigation | nine visible destinations: Desk, Dictation, Meetings, Studio, Activity, Commands, Cadence, Workbench, Settings | no more than five global destinations; advanced tools remain first-class on the Desk through tool, selection, search, inspector, and workroom affordances; Studio is authoring/configuration only |
| Desk creation chrome | five simultaneous nouns: Note, Knowledge, Persona, Zone, Workflow | one clear Create action with humane progressive disclosure; Dictate and Record remain immediate |
| Web world objects | Meeting, Note, Knowledge, Persona, Artifact, Sequence, Workflow, Coder; Project and Integration absent | Project/Integration become contextual Desk presences without permanent extra chrome |
| Native live-session language | `Agent Desk` / `Your live agents` | Coder sessions; Persona remains saved behavior |
| Native paired dictation badge | `ON-DEVICE · LOCAL MESH` | named paired-device boundary; never same-device local |
| Consequential verbs | bare or weakly qualified Approve, Apply, Open, and Run remain in Qlippy, History, Mission Control, companion/native review, and workrooms | zero ambiguous commitment verbs in the primary journeys |
| First-value measurement | Web submits fixed `steps: 1`, `decisions: 0`; no physical timing baseline | record actual observed steps, decisions, recovery, and elapsed time without phrase content |
| Workroom orientation | direct routes work, but subject context and return behavior vary | every focused room behaves like a Desk window/workspace: it receives an origin/subject and returns to it or its retained result |
| Control mode | available mainly through Settings/CLI | current effect of the mode is explained where a consequential action is proposed |
| Product copy | mixed operational copy, positioning prose, mascot voice, narrative empty states, and implementation explanations | professional, concise, task-first copy under one controlled contract; visual character remains |

### Current control-mode mismatch

The current wire and UI expose Safe, Neutral, and YOLO, but the implemented
matrix is deliberately narrow:

- YOLO still requires a Coder steering grant;
- external writes still require per-action authorization unless an exact
  fixed-destination grant already exists;
- operation families outside dictation commit, Coder steering, external write,
  and sync/cadence retain `current_behavior`;
- mode is primarily configured in Settings rather than experienced as Desk
  system posture.

The owner target is Secure/Normal/YOLO, with existing `safe`/`neutral` wire
compatibility. YOLO means zero HoldSpeak approval prompts for eligible
configured and registered actions; hard prerequisites, invariant validation,
and receipts remain. See [control-mode-contract.md](./control-mode-contract.md).

### Copy baseline

The repository has no controlled measurement of promotional, narrative,
anthropomorphic, or redundant UI copy. Source inspection reproduces the class of
problem, but Phase 93 must establish the exact rendered-string baseline before
claiming reduction. The target contract is
[copy-contract.md](./copy-contract.md); no count is invented during scaffolding.

## 4. Robustness baseline

Automated improvements exist, but the following lived proofs are absent or
incomplete:

- physical Web/iPhone/iPad microphone and exactly-once dictation delivery;
- 60-minute native and 120-minute desktop capture memory traces;
- disk-full, permission revocation, route change, lock/suspension, process kill,
  and relaunch recovery;
- airplane-mode meeting capture and exactly-once Web return;
- owner-visible conflict recovery for Meeting and relationship changes;
- five actual destination classes with killed-target control/treatment runs;
- Web keyboard-only and native screen-curtain VoiceOver completion;
- next-day return against real accumulated work;
- a deterministic canonical test command: the current all-tests command can
  enter real-metal audio and UAT product-boot waits without a bounded result.

## 5. Measures Phase 93 must establish honestly

Unknown values remain unknown until a real run records them.

| Measure | Known baseline | Exit direction |
|---|---|---|
| Primary Web navigation destinations | 9 | no more than 5 |
| Simultaneous Desk create-type controls | 5 | 1 Create entry; type choice progressively disclosed |
| Primary daily starts visible on a fresh Desk | mixed between links, orb, and create chips | Dictate, Record, Create are identifiable without opening Settings or Studio |
| Ambiguous consequential verbs | multiple reproduced examples | 0 in the controlled primary-journey census |
| Paired work described as same-device local | reproduced in flagship Swift | 0 |
| Primary journeys with Desk entry and retained return | not directly measured | 10/10 |
| Lost speech/text/capture under the forced-failure matrix | not physically measured | 0 |
| Physical-device accessibility completion | not measured | all primary actions complete on iPhone and iPad with direct evidence |
| First-dictation elapsed time and decisions | not measured | capture baseline first; improvement must be observed, not hardcoded |
| Sustained owner use | no Phase-92 debrief | five working days with every blocking finding fixed or explicitly open |
| Consequential operation families covered by the shared posture resolver | 4 initial families; unsupported families keep old behavior | every family in the ten primary journeys; no consequential `current_behavior` escape |
| YOLO HoldSpeak approval prompts for eligible configured operations | grants/per-action authority still required in several families | 0 |
| Promotional/narrative/filler copy in operational primary journeys | not yet counted; reproduced examples exist | 0 outside enumerated marketing/visual-brand exceptions |
| Actionable failures missing retained-work or next-action facts | not yet counted | 0 in the forced-failure matrix |

## 6. Stop signals

Stop and re-scope if:

- a story adds a permanent top-level route, dashboard, queue, or noun;
- the visible control count falls only because actions became hidden or
  unlabeled;
- an advanced capability becomes discoverable only by leaving the Desk for
  Studio, Settings, documentation, or a memorized URL;
- professional copy is interpreted as sterile visual design or as permission to
  remove necessary state, consequence, destination, or recovery facts;
- a fixture or simulator is being credited as owner/device comprehension;
- compatibility cleanup expands into a database or universal-graph rewrite;
- a happy path is polished while its failure path can discard work;
- the phase cannot name a before/after owner observation for a UI-facing story.
