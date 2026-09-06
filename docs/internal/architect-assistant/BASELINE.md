# Baseline and implementation disposition

Assessment date: 2026-09-05. Main inspected baseline: `f8e2739d`. A second development checkout was observed at `dbeb8576` during analysis and `0f80bde6` during specification preparation. These are observation points, not deployment attestations. Running processes predated those observations; their loaded revisions were not established.

The assessment ran nine existing Python test modules: **99 passed in 29.31 seconds**. The modules covered decision records, memory retrieval, Cadence, a Sequence restart seam, Steward conductor behavior, due Watches, coder factory behavior, graph support/refusal, and Thread tool execution. Temporary paths and databases isolated the run. No claim is made about live model quality, physical capture, current UI usability, the full suite, or the newer checkout.

Read-only installation inspection found capture and some project activity, with several decision, intelligence, automation, and attention paths unused or disabled. A large stored brief motivated a relevance requirement. Private installation counts and configuration details remain in the local assessment rather than this shareable specification. Non-use is evidence of an activation gap, not proof of a particular defect or user preference.

## Capability disposition

| Capability | Source | Disposition for this package |
|---|---|---|
| Desk and Project Room | [ProjectService](../../../holdspeak/services/project_service.py), [Desk guide](../../WEB_DESK.md) | Reuse identity, room projections, relationships, and window grammar. |
| Capture, Notes, Thoughts | [README](../../../README.md), [refinement service](../../../holdspeak/services/refinement_thought_service.py) | Reuse custody and explicit context selection; prove first value and recovery. |
| Project interview | [ProjectSetupService](../../../holdspeak/services/project_setup_service.py), [Project MCP family](../../../holdspeak/mcp/families/project.py) | Reuse durable stages, source-proposal testing, and atomic finalization. Setup sessions expire after 24 hours. Start/resume/answer/suggest/finalize are exposed; proposal select/deselect/test and repository clarification need MCP parity for a complete conversational setup path at this baseline. |
| Decisions and follow-through | [decision records](../../../holdspeak/services/decision_record_service.py), [decision lifecycle](../../../holdspeak/services/decision_lifecycle_service.py), [follow-through](../../../holdspeak/services/follow_through_service.py) | Reuse canonical owners; add architect-specific links only where absent. |
| Memory | [MemoryService](../../../holdspeak/services/memory_service.py), [FTS implementation](../../../holdspeak/db/memory.py) | Reuse source-cited local search. Complete organization-wide semantic coverage is not established. |
| Watches and Steward | [WatchService](../../../holdspeak/services/watch_service.py), [Steward](../../../holdspeak/services/project_steward_service.py) | Reuse observations, watermarks, internal effects, limits, and scheduling seams. |
| Briefs and attention | [brief service](../../../holdspeak/services/monday_brief_service.py), [Cadence](../../../holdspeak/cadence/scheduler.py) | Prove activation and prioritization; reconcile newer heartbeat work first. |
| Project updates | [update service](../../../holdspeak/services/project_update_service.py) | Deterministic and model drafting code exist. Test actual placement, claims, and output; do not rebuild from the obsolete “identity stub” description. |
| Manual workers | [factory launch](../../../holdspeak/delivery/factory_launch.py), [steering](../../../holdspeak/coder_steering.py), [capability ledger](../../../holdspeak/agent_capabilities.py) | Reuse launch/worktree/session/receipt contracts, respecting adapter differences. |
| Model authority | [router architecture](../ARCHITECTURE_INTELLIGENCE_ROUTER.md), [kernel runtime](../../../holdspeak/kernel/runtime.py) | Reuse admission, frozen deployment revisions, child accounting, and terminal receipts. |
| Thread tools | [ThreadService](../../../holdspeak/services/thread_service.py), [modes](../../../holdspeak/services/thread_modes.py) | Ten-pass bounded tool loop exists; project/provider tools are excluded from ordinary thread palettes at baseline. |
| Interview tool composition | [Thread schema conversion/executor](../../../holdspeak/services/thread_tools.py), [MCP registry](../../../holdspeak/mcp/tools.py) | Schema conversion already exists. Add scoped admission, reviewed domain metadata, durable interview control, and complete business-path coverage; a prompt alone cannot grant the absent palette. |
| Workflow execution | [support](../../../holdspeak/services/support.py), [service](../../../holdspeak/services/sequence_workflow_service.py) | Desktop hub supports linear chains. Branches, loops, forks, and joins cannot be presumed executable. |
| Child agents | [Phase 155](../../../pm/roadmap/holdspeak/phase-155-the-crew/current-phase-status.md) | Backlog at baseline. Reconcile that charter before introducing a second child-work design. |
| MCP | [sidecar](../../MCP_SIDECAR.md), [project composition](../../../holdspeak/mcp/families/project.py) | Local stdio owner process; selected live coder callbacks absent. The old watch-fetcher composition gap is already fixed in code. |
| Organization boundary | [security](../../SECURITY.md), [People security](../../PEOPLE_SECURITY.md) | Single owner, local normal data plane, separately protected People domain. No enterprise multi-user claim. |

## Work already underway

The newer checkout includes the Great Pass/Concierge, Heartbeat, and Loop Closes work, tracked by Phase 170, Phase 171, and Phase 172. Implemented paths include model setup, needs-you aggregation, recurring briefs, scheduling, notifications, meeting proposals, and People grounding. Story rows and aggregate status prose are not fully synchronized. The specification requires evidence from the selected integration revision and runtime, not inference from a heading.

The original [Tuesday Arc](../../../pm/roadmap/holdspeak/THE-TUESDAY-ARC.md) is motivation. Its phase names and individual capability claims have drifted. Delivery packets must inspect existing work and record one disposition per requirement: reuse and prove, integrate, fix a demonstrated gap, implement a missing capability, or defer. “Feature mentioned in roadmap” is not an implementation disposition.

## Product direction supplied during specification

The owner requested repeatable, section-specific interviews covering Projects, recurring work, concerns, related People, Decisions, and Goals, with powerful LLM suggestions and MCP-driven setup. This is direct product intent, not a finding inferred from installation usage. [INTERVIEW](INTERVIEW.md) translates it into a proposed controller, extension contract, tool-coverage work, and acceptance scenarios. Current code supports reuse of domain setup machinery; it does not establish that a universal interview or every required MCP operation already exists.

## Assumptions and unresolved product choices

| ID | Working assumption | How to resolve without blocking independent work |
|---|---|---|
| AS-01 | One Senior Software Architect is the initial operator. | Confirm participant and decision-owner records during the first project setup; do not invent an org chart. |
| AS-02 | One transformation stream and one connected repository are sufficient for the pilot. | Select actual records at R0; contract fixtures can be synthetic meanwhile. |
| AS-03 | GitHub and Jira are the first supported work sources. | Select an additional connector only when a pilot recipe cannot complete without it. |
| AS-04 | Approved architecture records remain in an existing Git/document destination. | Choose the exact authority and record locator before external reconciliation is enabled; local draft work proceeds. |
| AS-05 | Web is the primary surface. | Prove 1440px and 393px browser layouts; record native device work separately. |
| AS-06 | Existing control posture remains in force. | Runtime reports applicable policy and authority at action time; no package-level default change. |
| AS-07 | Proposed time and quality thresholds are initial acceptance targets. | Baseline real tasks, then record any target adjustment with rationale before scoring the pilot. |
| AS-08 | Overnight work can initially use one available owner-controlled hub. | If that hub sleeps, mark missed coverage; an always-on node is an explicit later deployment decision. |

Assumptions about employer source access, organizational authority, retention, or model destinations cannot be resolved by public search. Unsupported access remains visible in coverage; synthetic data verifies mechanics only.
