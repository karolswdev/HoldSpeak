# Phase 200 delivery sequence

**Status:** planning.
The [status table](current-phase-status.md#story-status) owns live story state.
This document owns the intended sequence and milestone criteria.

## Release gates

| Gate | Stories | Exit proof | Available outcome |
|---|---|---|---|
| **G0: Known and recoverable installation** | 01–05 | Runtime identity, isolated checks, cold first value, physical voice, and restore are proven. | An attested installation can create, recover, and reopen actual work. |
| **G1: Trustworthy daily Project work** | 06–16 | Claim support, coverage, real-model evaluation, daily flows, and the two-day owner sequence pass. | The R1 owner pilot starts. Assignments are not a prerequisite. |
| **G2: Configurable working practice** | 17–23 | Three recipes, replay-safe setup, revisit, one actual scheduled brief, and the R1 pilot pass. | Useful daily work and its supported recurrence are demonstrated. |
| **G3: Supervised assignments** | 24–30 | One adapter, immutable work contracts, verification, intervention, recovery, and five useful tasks pass. | Delegated results can be judged against their frozen outcome. |
| **G4: Bounded unattended execution** | 31–36 | Host and credential recovery, durable triggers, bounded retry, two recipes, and real occurrences pass. | The selected deployment earns its documented unattended claim. |
| **G5: Adopted release** | 37–40 | Outcome review, packaged candidate, recovery guides, cold rehearsal, and final evidence pass. | The owner can approve a release whose claims match its proof. |

Gate completion is cumulative.
A later gate cannot erase an unresolved earlier requirement.
Intermediate builds can ship within the authority and repository process already in force.
They must describe only the outcomes their evidence supports.

G1 corresponds to daily R1 readiness.
G2 establishes configurable R1 usefulness.
G3 corresponds to R2, and G4 corresponds to R3.
G5 is the product release decision.
The broader R4 transformation portfolio remains a follow-on.

## Dependency order

Story headers are the authoritative dependency graph.
The table below is its reading view.
A dependency means its relevant contract or proof must exist before the dependent story completes.

| Story | Gate | Depends on | Outcome |
|---|---|---|---|
| 01 | G0 | none | [Establish the integration baseline and obligation map](story-01-baseline-and-obligation-map.md) |
| 02 | G0 | 01 | [Expose loaded runtime identity and prove restore](story-02-runtime-identity-and-restore.md) |
| 03 | G0 | 01 | [Make release checks isolated and actionable](story-03-ci-isolation-and-release-contract.md) |
| 04 | G0 | 02, 03 | [Make first value and model readiness work cold](story-04-first-value-and-model-readiness.md) |
| 05 | G0 | 02, 03, 04 | [Prove physical voice capture, correction, and custody](story-05-physical-voice-and-custody.md) |
| 06 | G1 | 01, 03 | [Separate citation, factual support, and acceptance](story-06-claim-support-semantics.md) |
| 07 | G1 | 01, 03 | [Make incomplete attention coverage explicit](story-07-coverage-and-partial-results.md) |
| 08 | G1 | 01, 03, 06 | [Establish repeatable live-model quality evaluation](story-08-semantic-evaluation-harness.md) |
| 09 | G1 | 01 | [Design the daily Project workflow on existing surfaces](story-09-daily-workflow-design.md) |
| 10 | G1 | 06, 09 | [Promote reusable working context into canonical records](story-10-scoped-working-context.md) |
| 11 | G1 | 04, 06, 07, 09, 10 | [Produce a useful Project preparation brief](story-11-project-preparation.md) |
| 12 | G1 | 04, 05, 06, 09 | [Connect a real meeting to reviewed outcomes](story-12-meeting-to-reviewed-outcomes.md) |
| 13 | G1 | 10, 11, 12 | [Carry decisions and commitments into the next day](story-13-decision-and-commitment-continuity.md) |
| 14 | G1 | 07, 12, 13 | [Make permitted People preparation useful](story-14-people-preparation-boundary.md) |
| 15 | G1 | 07, 09, 13 | [Present actionable attention with controlled notifications](story-15-relevant-attention.md) |
| 16 | G1 | 05, 08, 11, 12, 13, 14, 15 | [Prove the daily loop and open the owner pilot](story-16-two-day-daily-loop.md) |
| 17 | G2 | 06, 10, 11, 13 | [Define three executable recipe contracts](story-17-recipe-catalog-and-compiler.md) |
| 18 | G2 | 08, 09, 17 | [Turn Interview intent into a reviewable setup plan](story-18-interview-prepared-configuration.md) |
| 19 | G2 | 17, 18 | [Apply and recover multi-service recipe setup](story-19-setup-apply-and-reconciliation.md) |
| 20 | G2 | 08, 10, 18, 19 | [Make Interview revisits fast and reliable](story-20-interview-revisit-and-quality.md) |
| 21 | G2 | 15, 17, 19, 20 | [Run a configured brief through an existing cadence](story-21-repeatable-brief-on-existing-cadence.md) |
| 22 | G2 | 01, 09, 11, 21 | [Integrate the calendar work required by daily recipes](story-22-calendar-dependency-integration.md) |
| 23 | G2 | 16, 20, 21, 22 | [Complete the ten-workday daily-practice pilot](story-23-daily-practice-pilot.md) |
| 24 | G3 | 01, 06, 17 | [Review the Assignment boundary and first adapter](story-24-assignment-design-and-adapter-decision.md) |
| 25 | G3 | 24 | [Persist immutable assignments and canonical run links](story-25-assignment-definitions-and-run-links.md) |
| 26 | G3 | 24, 25 | [Launch one bounded supervised worker](story-26-supervised-worker-adapter.md) |
| 27 | G3 | 06, 25, 26 | [Verify results against the frozen acceptance contract](story-27-result-verification-and-review.md) |
| 28 | G3 | 09, 25, 26, 27 | [Make assignment progress and intervention usable](story-28-assignment-desk-controls.md) |
| 29 | G3 | 25, 26, 27, 28 | [Prove assignment recovery, cancellation, and scope change](story-29-assignment-recovery-and-cancellation.md) |
| 30 | G3 | 23, 27, 28, 29 | [Prove five supervised assignments on useful tasks](story-30-supervised-assignment-pilot.md) |
| 31 | G4 | 02, 21, 24 | [Choose and prove the durable execution host](story-31-durable-hub-deployment.md) |
| 32 | G4 | 24, 31 | [Implement a scoped credential lifecycle for recurring work](story-32-durable-credential-lifecycle.md) |
| 33 | G4 | 17, 21, 25, 31, 32 | [Bind triggers to versioned recipes and assignments](story-33-durable-trigger-bindings.md) |
| 34 | G4 | 29, 33 | [Enforce leases, bounded retry, and missed-run policy](story-34-leases-retries-and-missed-runs.md) |
| 35 | G4 | 23, 30, 32, 33, 34 | [Enable bounded unattended preparation and analysis](story-35-bounded-unattended-recipes.md) |
| 36 | G4 | 31, 32, 34, 35 | [Prove unattended operation through real occurrences and restart](story-36-unattended-restart-proof.md) |
| 37 | G5 | 23, 30, 36 | [Review net value and decide the next investment](story-37-outcome-review-and-expansion-decision.md) |
| 38 | G5 | 23, 30, 36 | [Package the verified product and recovery procedures](story-38-release-package-and-operator-guides.md) |
| 39 | G5 | 37, 38 | [Rehearse the release without implementation guidance](story-39-cold-release-rehearsal.md) |
| 40 | G5 | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39 | [Close Phase 200 on outcomes and release evidence](story-40-release-and-phase-close.md) |

## Start sequence

1. Complete 01 and establish current runtime, integration, source, and debt facts.
2. Complete 02–05 for an installation that can create and recover real work.
3. Develop 06–08 and 09–15 along their explicit dependencies.
4. Complete 16 on two working days and begin the daily-use log.
5. Deliver 17–22 while collecting that log, then evaluate it in 23.
6. Design 24 when its evidence is available. Build 25–29 against the reviewed contract.
7. Prove useful supervised work in 30.
8. Prepare deployment 31–34 while supervised proof develops.
9. Enable 35 only after daily value and supervised acceptance pass.
10. Complete 36–40 on the actual candidate and deployment.

A pilot is a period of observed work, not a period during which development must stop.
Record build changes and segment comparisons when repairs affect the measured behavior.
Do not defer useful R1 observation until every Assignment feature exists.

## Review and delivery units

One story is one scoped PR under the repository contract.
A design story ends with a reviewable decision and evidence.
An implementation story ends with behavior and its relevant proof.
A live-proof story cannot finish from source inspection alone.
The phase never waits for one forty-story merge.

Before a story starts, identify its concrete gap on current main.
If the behavior exists, reuse it and prove the required path.
If its diff would contain several independent architectural changes, split the story visibly before implementation.
Keep existing IDs stable and add new IDs at the end of the phase.
Update the dependency graph and status table in the same change.

Only one integration owner serializes changes to shared contracts.
Potentially independent work includes evidence semantics, daily UI design, and deployment research after their prerequisites.
This does not authorize parallel agents or select a model.
Any delegated work follows the applicable session authorization and repository model rules.
Roadmap authorship remains with the primary planning agent.

## Capacity and planning horizon

This is a substantial delivery program with forty reviewable units.
No calendar completion date is promised before G0.
At G0, estimate each remaining story using observed repair scope and actual capacity.
Publish the estimate range and the critical dependency path in the status record.

Default allocation while the pilot runs:

| Capacity | Use |
|---|---|
| About 60% | Current milestone's complete user workflow |
| About 25% | Reliability, evaluation, and recovery needed by that workflow |
| About 15% | Owner observation, documentation, integration, and scope decisions |

These are planning allocations, not time accounting rules.
Pilot correction and maintenance effort must still appear in the outcome measures.
A missed estimate changes sequencing or capacity openly. It does not lower an acceptance threshold.

## Scope admission

A new request enters the current milestone when it repairs a required scenario or resolves a measured pilot obstacle.
Otherwise record the problem, evidence, and revisit trigger for HS-200-37.
Existing work on another branch is reviewed for reuse before new implementation begins.
Do not abandon or rewrite that branch as a side effect of this plan.

The core contracts and acceptance gates remain mandatory.
A proposed reduction changes the scope explicitly and retains the original requirement in the decision history.
An unmet core gate cannot be relabeled optional at closeout.

## Evidence and closeout

Each story's actual evidence includes build, environment, commands, results, limitations, and relevant user observations.
Follow the repository evidence pairing and stamped commit process.
Use synthetic or redacted public fixtures.
Keep private owner evidence in an explicitly chosen local destination and link a shareable observation summary.

The next review checkpoint is HS-200-01's current-state map.
The first product checkpoint is HS-200-16's two-day Project sequence.
The final checkpoint is a release whose daily, supervised, and unattended claims all match demonstrated evidence.
