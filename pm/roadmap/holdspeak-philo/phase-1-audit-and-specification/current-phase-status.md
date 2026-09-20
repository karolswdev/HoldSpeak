# Phase 1 — Philo audit and specification

**Last updated:** 2026-09-19.

## Goal

Deliver both preserved research briefs as one source-backed documentation and Desk specification package.
The Tuesday result is a short system explanation and a traceable meeting-to-summary path.

## Authority

The owner explicitly instructed: “In this instance - no relying on Muad'Dib. It's you and your Luna XHigh sub-agents.”
Astra owns scope, design, verification and the final deliverable. This overrides the other-brain dependency for Philo only.
Earlier Muad'Dib reviews remain historical planning evidence. No further Claude invocation is authorized for this task.

## Scope

- In: source reconstruction, maintained registries/reference generation, documented contracts, SRS, annotated artboards, repository skills, validation and executive report.
- Out: unrequested production rewrites, owner-machine state changes and claims of observed usability without observation.
- Desktop: specify the host boundary; preserve prototype requests and evaluate them as isolated research if feasible, never as shipped support.

## Exit criteria

- [ ] The preserved request has a requirement disposition matrix.
- [ ] All requested subsystem areas have evidence-backed documentation.
- [ ] Registry/schema/generation/coverage tools pass positive and negative checks.
- [ ] Desk SRS and wide/compact visual artifacts distinguish current from proposed.
- [ ] Repository skills validate and link to real sources and tests.
- [ ] Full required verification is recorded, with failures classified.
- [ ] Final hostile audit and executive report name remaining unknowns.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| PHILO-1-01 | Reconcile the request and sources | done | [story-01-reconcile.md](story-01-reconcile.md) | [evidence-story-01](./evidence-story-01.md) |
| PHILO-1-02 | Kernel, authority, storage and operations | done | [story-02-runtime.md](story-02-runtime.md) | [evidence-story-02](./evidence-story-02.md) |
| PHILO-1-03 | Dictation, meetings and model execution | done | [story-03-voice.md](story-03-voice.md) | [evidence-story-03](./evidence-story-03.md) |
| PHILO-1-04 | Agents, integrations, companions and knowledge | in-progress | [story-04-integrations.md](story-04-integrations.md) | - |
| PHILO-1-05 | Desk design specification and SRS | in-progress | [story-05-desk.md](story-05-desk.md) | - |
| PHILO-1-06 | Registries, validation and repository skills | in-progress | [story-06-maintenance.md](story-06-maintenance.md) | - |
| PHILO-1-07 | Integrated audit and final verification | in-progress | [story-07-verification.md](story-07-verification.md) | - |

## Lanes

| Lane | Stories | Owner | Workers | Working directory |
| --- | --- | --- | --- | --- |
| Runtime | 02 | Astra | Luna xhigh | HoldSpeak-Philo |
| Voice | 03 | Astra | Luna xhigh | HoldSpeak-Philo |
| Desk | 05 | Astra | Luna xhigh | HoldSpeak-Philo |
| Integration and maintenance | 04, 06 | Astra | Later Luna xhigh waves | HoldSpeak-Philo |
| Reconciliation and verification | 01, 07 | Astra | Independent Luna review | HoldSpeak-Philo |

## Where we are

Implementation authorized. Initial source-only audits exist under docs/internal/philo/checks.
Use docs/internal/philo/data/README.md as the shared metadata contract.
Workers own disjoint files. Astra is the only commit lane.

## Decisions made

- Preserve existing domain registries; add cross-domain documentation metadata only.
- Put portable reference outputs under docs/generated and curated inputs under docs/internal/philo/data.
- Keep the owner's first-use Phase 201 independent.
- Check each lane through source inspection and relevant tests; no stable classification from metadata alone.

## Active risks

| Risk | Mitigation |
| --- | --- |
| Census breadth obscures the user job | Lead with the short guide and meeting path |
| Source changes on main | Pin snapshot and report drift before merge |
| Existing docs conflict | Record authority and execution separately |
| Hardware or owner observations unavailable | Label limits; never fabricate evidence |

## Open dissents

None. The Philo-specific owner override is recorded above.
