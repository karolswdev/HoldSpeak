# HoldSpeak Markdown project plan

Version 0.15.16, publication edition · 4 November 2026 · documentation-only draft PR authorized, implementation not assigned

## Start here

1. **Owner review:** [proposed order and first owner choice](EXECUTION_INDEX.md#3-detailed-slices-and-proposed-order). The recommendation is S11 creation context: explicit project before creation versus an unbound Draft with a broader lifecycle design. Neither priority nor behavior is accepted yet.
2. **Detailed slices:** choose one outcome in the [ordered hierarchy](EXECUTION_INDEX.md#2-proposed-workstream-hierarchy), then its story and task. Thirteen detailed slices have local decisions, exact implementation ownership and verification. The separate [spending-contract task](epics/HS-E20-program-contracts.md#hs-s24-spending-contract-gate) resolves what the amount promises before any enforcement plan; it is not a prerequisite for creation/context work.
3. **Agent handoff:** provide the preserved Markdown folder plus one [assignment/decision/predecessor handoff](AGENT_START.md#one-portable-handoff-bounded-reading). Read only the assigned task's exact mandatory context; the full S11 chain uses nine package files, not the whole evidence library. Source checkout and actual repository onboarding remain separate prerequisites.

The two product jobs are building/delivering repository-backed projects and directing technical work across projects and people. The target is surgical improvement of the existing system. No parallel platform, generic workflow engine, arbitrary line cap or broad storage merger is proposed.

## What is ready

- The initial epic/story hierarchy and dependency order are written in the project plan.
- Thirteen detailed slices have bounded contracts, exact source ownership, focused producer/consumer proof, rollback and stop conditions. A separate spending-contract task brings the total to forty-seven briefs, including the shared baseline. It is ready for contract resolution, not implementation.
- HS-S11’s first-slice handoff and the [conditional creation-to-Room join](VALIDATION.md#creation-to-room-integration-gate) now name exact producer/consumer proof. Stored creation, notification, successful Room read and detail reveal are separate boundaries. Both local choices and the joint assignment remain pending; no runtime success is implied.
- The [conditional review-to-delivery join](VALIDATION.md#review-to-delivery-integration-gate) specifies the missing joint proof between human-reviewed step completion and final delivery recovery without merging their authority or adding tasks. Both design gates and the joint assignment remain pending.
- Other stories are explicitly decision-gated or need more evidence. Their inclusion is not an accepted design or permission to implement them.
- Commands are source-verified or labeled proposed. No HoldSpeak application, product test, provider call or Git operation was run to prepare this plan.

The owner requested detailed planning after the earlier supervisory pause. That authorizes this expansion, not repository mutation, test execution in an unassigned environment, shipping, PR approval or deployment. See [current direction](DECISIONS.md#detailed-planning-direction-3-november-2026).

## Documentation-only draft PR

On 4 November 2026, the owner authorized publication of this complete package as one documentation-only draft PR in `karolswdev/HoldSpeak`. Its location is `docs/internal/holdspeak-execution-plan/`. Keep the folder hierarchy intact; do not present a standalone overview as the complete plan. The [publication checklist](PACKAGE_VALIDATION.md#documentation-publication-readiness) names the package contents, review requirements and historical analysis artifacts that are **not bundled**. Publication does not accept proposed behavior, assign implementation, approve or merge the PR, or authorize deployment.

## Evidence library, not mandatory onboarding

[Product vision](PRODUCT-VISION-AND-JOURNEYS.md), [target design](NEXTGEN-TARGET-PROPOSAL.md), [review synthesis](REVIEW-BRIEF.md), [decision ledger](DECISIONS.md), [journey evidence](NEXTGEN-JOURNEYS-AND-NAVIGATION.md), [structural evidence](STRUCTURAL-REVIEW.md), [source register](EVIDENCE.md), [dead-code ledger](DEAD-CODE-REVIEW.md), [Python v1](PYTHON-STATIC-ANALYSIS.md) and [Python v2](PYTHON-STATIC-ANALYSIS-V2.md) preserve the supporting research. Read only the concern linked from your task.

[Validation](VALIDATION.md), [invariants](INVARIANTS.md) and [completion report](COMPLETION_REPORT_TEMPLATE.md) are shared execution references. [Package validation](PACKAGE_VALIDATION.md) records document checks, not passing product tests; the [changelog](CHANGELOG.md) preserves earlier checkpoints.

The old `E00/E01/E02/E03/E04/E90/E99`, `S00/S10/S20/S21/S30/S40/S90/S99` outlines and [four-seam target](TARGET_DESIGN.md) are historical inputs. The **HS-** identifiers in the current plan are authoritative for this new planning hierarchy; old reserved task IDs must not be executed as its backlog. No historical file is silently deleted or promoted into accepted work.

Source baseline: `80b641fa41c7352280cfa52e933acf6dbe8d3857`, rechecked as GitHub main at 19:34 UTC on 3 November. Each execution checkout must revalidate drift and current instructions.
