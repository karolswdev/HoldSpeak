# HoldSpeak product vision and core journeys

**Status: user-confirmed purpose; provisional feature-set mapping.** This is a design proposal, not a completed product validation or an implementation assignment. The latest [decision record](DECISIONS.md) governs: surgical next-generation evolution across frontend and backend, not a replacement system for its own sake.

## Confirmed purpose

HoldSpeak should be the central hub in which a technical person manages their technical life. It must work both for someone building and orchestrating projects in their own repositories and for a technical leader/director coordinating work across an engineering organization. Existing capabilities should form coherent feature sets that support those jobs with less fragmentation.

Architecture serves those jobs. Cleaner folders are useful only when they make behavior easier to understand, capabilities easier to combine, feature changes more local, and agent onboarding more bounded. Preserve useful existing behavior; remove or simplify incidental machinery only when its purpose and consumers have been established and a change is authorized.

## Journey 1 Take a project through its repository and delivery lifecycle

**Confirmed job:** Orchestrate a project, its repositories and the lifecycle of work, rather than switch among disconnected tools/concepts.

**Existing capabilities evidenced in the pinned repository:** capture notes and meeting context; ask with sources; connect records to a Project Room; prepare tasks/agent briefs; hand coding work to an agent/worktree; use Programs to coordinate steps/checks/review/PR/merge; inspect results, decisions and handover records.

**Proposed experience to validate:** Keep the project and its intent recognizable across capture, clarification, preparation, execution and review. A task/Program/agent session should be a clearly related part of the job, not a competing project identity. Preserve sources, authority, status and outcome as work moves between those surfaces.

**Lifecycle prerequisite now made explicit:** connecting a GitHub source or registering a Project repository does not by itself supply the local source that Program creation resolves. The existing ordinary agent hand-off has a separate first-clone path; Program creation does not call it. Conversely, a filed/local source can resolve without that remote-registration record. Existing Terminal folder registration and Project-resource binding are useful setup capabilities; their presence does not establish a seamless global Program onboarding path. A registration or `cloned` label is not a universal readiness or selected-target guarantee. The [project lifecycle acceptance map](EXECUTION_INDEX.md#repository-readiness-in-the-project-journey) distinguishes those states from saved Program and launch/worktree identity.

**Proposed first acceptance scope:** exercise the local-repository journey through acknowledged creation, execution, review and independent delivery, while naming remote-only onboarding as uncovered unless separately designed and proven. Do not launch work just to obtain a clone or silently add cloning to Create. A remote-first preparation experience is a separate product/authority choice, not part of the current S11 UI fix.

**Not yet established:** Which current transitions are genuinely redundant, which screens can be consolidated, which identifiers/records must remain distinct, and what the minimal shared context should be. No screen or store merger is approved by this proposal.

## Journey 2 Lead an engineering organization from connected work

**Confirmed job:** Manage the technical-leadership view across projects and people, not only an individual coding task.

**Existing capabilities evidenced in the pinned repository:** Project Rooms and source-backed updates; meetings and reviewed outputs; People/1:1 context and commitments; decisions, risks and open work; briefings and repeat work through Automations; reviewed sends to configured destinations. Confidential People material has separate protection.

**Proposed experience to validate:** Move from a cross-project concern to the relevant evidence, decision, person/commitment and next action without rebuilding context. Project status and people/meeting context should support leadership decisions while preserving their distinct privacy and authority rules.

**Director-to-delivery continuity:** a confirmed meeting decision need not create work. Action-kind confirmation and the separate deliberate commitment of an accepted source decision already provide ordinary action identities that can connect to project work. Authored Desk decisions, canonical records and private People promises are different branches, not interchangeable IDs. The [integrated acceptance map](EXECUTION_INDEX.md#director-decisions-through-project-delivery) now names the path into Program fulfillment and its separate delivery outcome; actual UI continuity and the selected acceptance branch remain unproven and pending.

**Not yet established:** The right overview/navigation, ownership of cross-project summaries, or whether current surfaces should merge. A coherent feature set must not expose private 1:1 material to broader project updates or turn a draft into an authorized send.

## Provisional feature-set consolidation map

These are **candidate groupings of existing capabilities**, not new features, final navigation labels or approved code packages.

| Candidate feature set | Existing capabilities it could connect | Intended coherence | Pending decision |
| --- | --- | --- | --- |
| Project work and delivery | Project Rooms, repositories, tasks/briefs, agents, Programs, review/results | One project context from intent through delivery | Which task/Program/agent concepts stay distinct, and where one entry can replace redundant entry points |
| Leadership and relationships | People/1:1, commitments, meetings, project concerns, decisions and updates | Connected leadership preparation, decisions and follow-through | Appropriate cross-project view and strict private-source boundaries |
| Capture and working knowledge | Notes, meetings, sources, memory and Ask | Capture once, find/inspect evidence, reuse context in both journeys | Which capture/read surfaces can share context without flattening distinct source/canonical records |
| Assistance and repeat work | Ask/Threads, Calls, Automations, briefings, prepared sends | Assistance embedded in the job instead of another competing workflow | Interactive versus scheduled lifecycles, distinct approval/late-answer behavior and which user-visible concepts should remain |

Cross-cutting connections in this table do not imply merging their databases, state machines or authorization models. For example, extracted decisions and accepted canonical decisions mean different things; Calls can finish permitted work after hangup; unknown send outcomes cannot be blindly retried.

## Evidence and limits

The existing-capability map is grounded in the pinned [repository README](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/README.md), source-backed [structural review](STRUCTURAL-REVIEW.md), and [evidence register](EVIDENCE.md). The user supplied the product purpose and fragmentation concern. The candidate grouping and journey continuity are design hypotheses, not claims of observed end-to-end usability.

No live journey walkthrough, owner acceptance test, navigation experiment or feature-merger validation has been performed for this document. Whole-product capability coverage, including remote-first repository preparation and composed lifecycle recovery, remains incomplete. The existing Python static analyses inform dependency ownership; they do not validate the product vision.

## Next review questions

- Does each proposed grouping preserve the jobs already useful to the owner?
- Where does a journey currently lose context or repeat an action/concept, with concrete examples?
- Which distinctions carry real domain/authority meaning and must stay visible?
- Which frontend/backend mechanisms exist only because of incidental architecture rather than a supported job?

Asynchronous registration is a priority example of the last question. First trace the actual registration, lazy-loading and lifecycle paths and their purposes. Do not remove behavior merely because its mechanism is asynchronous or its need is not yet documented.

## What follows

Use validated journey problems to select responsibility boundaries and narrowly justified structural changes. The now-authorized [HS plan](EXECUTION_INDEX.md) supplies reviewed epic/story/task briefs with exact local context and proof. Do not create a parallel new system, generic migration platform or broad cutover ceremony unless a specific approved change makes one necessary. Detailed planning is authorized; unresolved target choices and any implementation assignment remain separate.
