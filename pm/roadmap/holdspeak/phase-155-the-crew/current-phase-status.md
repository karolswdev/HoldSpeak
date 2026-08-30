# Phase 155 - The Desk Chat — The Crew (DC-05)

**Last updated:** 2026-08-30.

## Goal

The Thread learns to delegate: chat.subthread children on the desk,
run by the existing conductor, reporting back as tool messages —
receipted end to end, never a side door (settled design D1–D5; counsel
RATIFY; S7, R5).

## Scope

- **In:** the five stories below; the charter lands on PR #511
  (`feat/deskos-platform-revolution`), the superseding merge vehicle.
- **Out:** depth > 1, crew templates, cross-desk crews.

## Exit criteria (evidence required)

- [ ] All five stories done with evidence; glass 1440+393; metal on `.43` incl. the fence leg; close counsel zero open must-fix; the arc exhibit published; sweep name-diff clean vs main.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-155-01 | chat.subthread (receipted, S7 validation, depth cap) | backlog | [story-01-subthread-tool](./story-01-subthread-tool.md) | - |
| HS-155-02 | The conductor runs the child (30 s then background) | backlog | [story-02-conductor](./story-02-conductor.md) | - |
| HS-155-03 | thread.notification (frames, tool-role consumption, R5) | backlog | [story-03-notifications](./story-03-notifications.md) | - |
| HS-155-04 | The child on the desk (crew row, steer, stop) | backlog | [story-04-child-on-desk](./story-04-child-on-desk.md) | - |
| HS-155-05 | The walk and the close — the arc closes | backlog | [story-05-walk-and-close](./story-05-walk-and-close.md) | - |

## Where we are

Chartered 2026-08-30 from the settled design (assets/settled-design.md)
on the superseding merge vehicle (PR #511). Builds after Phase 154.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Subthreads as a People-egress laundering path | medium | the 155-03 fence leg; sensitive flags ride notifications | a cloud payload carrying child-sourced People text |
| Conductor contention with workbench runs | low | one run-loop, bounded waits (S7) | a workbench run starved by crew children |

## Decisions made (this phase)

- 2026-08-30 - Subthread calls stay receipted (no warpdrv auto-approve) - the Constitution: every effect admitted - counsel D1.
- 2026-08-30 - Depth cap 1 in this phase - bounded delegation - orchestrator.
- 2026-08-30 - The charter lands on PR #511, not #507 - vehicle superseded - owner ruling.

## Decisions deferred

- Depth > 1 and crew templates - trigger: real Tuesday use asks for it - default no.
