# HS-177-05 — Draft / Chase / Plan over Room data

- **Project:** holdspeak
- **Phase:** 177
- **Status:** backlog
- **Depends on:** HS-177-03, HS-177-04
- **Unblocks:** HS-177-06
- **Owner:** unassigned

**CONDITIONAL: this story proceeds only if HS-177-01 produces a GO
verdict. If the measured decision is CUT, this story is cancelled.**

## Problem

The Thread modes exist (thread_modes.py:113-147) but their tool
palettes are desk-scoped. Chase has people/follow-through effects +
candidate_builder tools; Plan has thought/decision_record reads +
door.get + memory.search. Neither can read Watch entities, project
deltas, or the steward's output. The arc says: "Draft / Chase / Plan
recipes over real Room data." With Room grounding (HS-177-03) and the
grounded ask (HS-177-04) in place, this story widens the palettes and
verifies each mode works over Room data.

## Scope

- In:
  - Chase palette widened: add project.get, project.get_room,
    project.get_delta, project.watch.inspect, project.list_updates to
    _CHASE_TOOLS (thread_modes.py:59-67). Chase can now read Room
    state and move work forward using its existing people/follow-through
    effects.
  - Plan palette widened: add project.get, project.get_room,
    project.get_steward_run, project.get_delta to _PLAN_TOOLS
    (thread_modes.py:73-78). Plan can now reflect on Room state +
    steward output alongside thoughts/decisions/memory.
  - Draft stays pure: _DRAFT_TOOLS remains frozenset() (line 70). No
    tools, no context lookups, just composition.
  - Project mode stays as-is: MCP-only, identifies project-agent
    threads (line 143). No palette change.
  - System prompts for Chase and Plan updated to mention Room context
    availability (the mode recipe's system field).
  - Verified: a Chase thread grounded on a Room can read a Watch entity
    and propose a people.commitment.transition; a Plan thread can
    read the steward's last run and the Room's delta.
- Out:
  - project.* effect_proposal tools in any thread palette (archive,
    configure_steward, run_steward stay MCP-only).
  - New modes or mode creation UI.
  - Guardrail changes (the existing egress guardrail on Chase applies
    to the new project tools; the fail-closed gate is unchanged).

## Acceptance criteria

- [ ] _CHASE_TOOLS includes project.get, project.get_room,
      project.get_delta, project.watch.inspect, project.list_updates
      (verified by a unit test reading the frozenset).
- [ ] _PLAN_TOOLS includes project.get, project.get_room,
      project.get_steward_run, project.get_delta.
- [ ] _DRAFT_TOOLS remains frozenset() (no tools).
- [ ] A Chase thread grounded on a Room reads a Watch entity and
      proposes a people.commitment.transition; the kernel receipt
      exists (Article XI).
- [ ] A Plan thread grounded on a Room reads the steward's last run
      and the Room's delta; no effects fired (Plan is read-only).
- [ ] The fail-closed gate blocks project tools not in the palette;
      verified by test.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k modes_room_data`
  - Chase palette contains the expected project tools.
  - Plan palette contains the expected project tools.
  - Draft palette is empty.
  - A project tool NOT in Chase is denied by the gate.
- Integration: a Chase thread reads a Watch entity via
  project.watch.inspect; a Plan thread reads project.get_steward_run.
- Manual: the owner uses Chase to move a commitment from a Room-
  grounded thread; the receipt shows in the thread.

## Notes / open questions

- The existing Chase guardrails (thread_modes.py:104) include an
  egress guardrail. The new project.* evidence_read tools are reads
  (no egress); the guardrail should not fire on them. Verify during
  build.
