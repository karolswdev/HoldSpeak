# Phase 177 - The Thread at Work

**Last updated:** 2026-09-05.

## Goal

The desk chat becomes a work tool. Draft / Chase / Plan recipes run
over real Room data: Watch entities, project needs-you items, steward
output, and meeting decisions ground the thread's context. The ask
cites Watch entities by ref. Every effect is admitted through the
kernel with a receipt (Article V, Article XI). The phase is
conditional: a measured week of real use after 170--172 ship decides
whether the Thread and the Workbench earn their place; if they do not,
the phase is cut to adoption support only.

## Status

**PLANNED 0/8.**

**Depends on:** Phase 172 merged (meetings must close their loop --
decisions and commitments must exist -- before the Thread can work
over them).

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Tuesday afternoon. He opens a Chase thread grounded on the governance
Room: "What is Ania waiting on from me?" The thread reads three Watch
entities (two PRs and one Jira issue), cites their refs, and proposes
`people.commitment.transition` for the overdue item. He confirms; the
receipt sits in the thread alongside the answer. Before the Thursday
retro he opens a Plan thread: "What changed in governance since
Monday?" The thread reads the Room's SINCE YOU LOOKED, the steward's
last run, and two meeting decisions. He keeps the answer as a Note for
the retro.

Census facts from THE-TUESDAY-ARC.md section 0 and section 3 that
this phase pays: 10 test threads, none for work; 1 workbench, 0 runs;
"170--172 give them an engine; then a week of use decides whether they
stay."

**CONDITIONAL.** The arc makes this phase evaluative, not guaranteed.
Story 01 is a measured decision: the owner uses the Thread and
Workbench for one measured week after 170--172 ship; the metric and
the kill criterion gate every subsequent story. If the week produces
zero work threads and zero workbench runs, the phase is cut.

## Scope

- In:
  - The measured decision: one week of real use after 170--172; the
    metric (work threads created, workbench runs, Room-grounded
    questions asked); the kill criterion; the owner's GO or CUT.
  - CONDITIONAL on GO: Room grounding for the Thread: project.* tools
    admitted to the thread palette for Chase and Plan modes
    (thread_tools.py:206 today says "MCP-only, in no thread palette");
    Watch entities, needs-you items, steward output available as
    hydrated grounding refs (thread_service.py:23 today resolves desk
    refs only).
  - CONDITIONAL on GO: the grounded ask: the ask resolves Watch
    entities and Room data alongside desk refs; answers cite Watch
    entities by ref.
  - CONDITIONAL on GO: Draft / Chase / Plan over Room data: Chase
    gains project.get, project.get_room, project.get_delta,
    project.watch.inspect, project.list_updates in its palette; Plan
    gains project.get, project.get_room, project.get_steward_run; Draft
    stays pure (no tools).
  - CONDITIONAL on GO: the design on the library before build (canvas
    at 1440 + 393).
  - CONDITIONAL on GO: his walk on his desk: a work thread grounded on
    a Room.
- Out:
  - Workbench overhaul (the Workbench's templates and runner exist; if
    unused after the measured week, that is a signal, not a build
    target).
  - New thread modes beyond the existing five (Desk, Chase, Draft,
    Plan, Project).
  - External MCP client in the Thread (DC-02 candidate).
  - Subthreads (Phase 155 The Crew; DC-05).
  - External effects from the Thread beyond what Chase already admits
    (people.commitment.transition, people.agenda.add,
    people.note.create, follow_through.complete,
    follow_through.commit_decision, door.add_item).

## Exit criteria (evidence required)

- [ ] The measured decision is recorded: one week of real use; the
      metric; the owner's GO or CUT.
- [ ] CONDITIONAL on GO: project.* tools are admitted to the Chase and
      Plan thread palettes; the Thread reads Watch entities, needs-you
      items, and steward output from a Room.
- [ ] CONDITIONAL on GO: the ask resolves Watch entities and Room data;
      the answer cites a Watch entity by ref.
- [ ] CONDITIONAL on GO: Chase moves a Room item (commitment
      transition, agenda add, or door item) with a kernel receipt;
      Plan reflects on Room + steward output; Draft stays pure.
- [ ] CONDITIONAL on GO: the design on the canvas at 1440 + 393 is
      ratified by the owner before the build.
- [ ] CONDITIONAL on GO: his walk on his desk: a work thread grounded
      on a Room; his word.
- [ ] Every effect admitted through the kernel with a receipt (Article
      V, Article XI).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-177-01 | The measured decision (one week of real use; the metric; GO or CUT) | backlog | [story-01-the-measured-decision](./story-01-the-measured-decision.md) | -- |
| HS-177-02 | The design (CONDITIONAL on 01 GO; the Thread at Work faces on the canvas) | backlog | [story-02-the-design](./story-02-the-design.md) | -- |
| HS-177-03 | Room grounding for the Thread (CONDITIONAL on 01 GO; project.* tools in the palette; Watch refs as grounding) | backlog | [story-03-room-grounding](./story-03-room-grounding.md) | -- |
| HS-177-04 | The grounded ask (CONDITIONAL on 01 GO; the ask resolves Watch entities and Room data) | backlog | [story-04-the-grounded-ask](./story-04-the-grounded-ask.md) | -- |
| HS-177-05 | Draft / Chase / Plan over Room data (CONDITIONAL on 01 GO; palettes widened; Draft stays pure) | backlog | [story-05-modes-over-room-data](./story-05-modes-over-room-data.md) | -- |
| HS-177-06 | The walk (CONDITIONAL on 01 GO; his desk: a work thread grounded on a Room) | backlog | [story-06-the-walk](./story-06-the-walk.md) | -- |
| HS-177-07 | The docs (CONDITIONAL on 01 GO; the Thread at Work in the guide; Room grounding in the architecture) | backlog | [story-07-the-docs](./story-07-the-docs.md) | -- |
| HS-177-08 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | backlog | [story-08-the-close](./story-08-the-close.md) | -- |

## Where we are

PLANNED. Waiting for Phase 172 to merge (the loop must close before
the Thread can work over its output). The phase is conditional on the
measured decision in story 01.

The recon is complete:

**Thread today:** the Thread primitive exists with five modes (Desk,
Chase, Draft, Plan, Project; thread_modes.py:113-147), a 715-line
fail-closed tool gate (thread_tools.py), full kernel admission
(thread_service.py:458), grounding via hydrated desk refs
(thread_service.py:23), mode-bound guardrails, voice annotations,
branch/regenerate, and a 1,750-line pullout (ThreadPullout.tsx). But
the modes' tool palettes are desk-scoped: notes, thoughts, decisions,
memory. project.* tools are classified "MCP-only, in no thread
palette" (thread_tools.py:206). The Thread cannot read Watch entities,
Room data, needs-you items, or the steward's output.

**Grounding today:** `ask.resolve_grounding` (mcp/families/ask.py:109)
and the thread's own `hydrate_refs_detailed` resolve desk-level refs
(notes, meetings, decisions). No Watch entity, project entity, or
Room ref type exists in the grounding vocabulary. The gap: "the ask
grounded on Watches and the Room" from the arc is not implemented.

**Workbench today:** full service layer (workbench_service.py,
workbench_runner.py, workbench_conductor.py, workbench_memory.py,
workbench_templates.py) with templates (TODO, Triage, Meeting Prep,
Delivery). Census: 1 workbench on the owner's desk, 0 runs.

**The arc's conditionality:** "a week of use decides whether they
stay." This is not a suggestion; it is the charter's gating condition.
Story 01 is a measured decision. If the owner creates zero work
threads and zero workbench runs in one measured week after 170--172
ship, the phase is cut to adoption support only.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| The measured week produces zero use | Medium | 170--172 give the Thread an engine (decisions, commitments, Room data); the measured week starts only after those phases land; the kill criterion is honest | Zero work threads AND zero workbench runs in the measured week; the phase is CUT |
| project.* tool palette scope creep | Low | Only evidence_read project tools enter Chase and Plan; effect_proposal project tools (archive, configure_steward) stay out; the fail-closed gate blocks unclassified tools | A project effect lands without a kernel receipt |
| Grounding vocabulary explosion | Low | Room refs and Watch entity refs are added to hydrate_refs_detailed alongside existing desk refs; the ref grammar stays qualified (project://room/{id}, watch://entity/{id}); no wildcard resolution | Grounding resolves > 50 entities for one ref (unbounded fanout) |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- Whether the Workbench gets Room grounding alongside the Thread (if
  the measured week shows workbench use, the same grounding pattern
  applies; if not, the Workbench stays as-is) -- decided by the
  measured decision.
- Which project.* effect_proposal tools (if any) enter the Chase
  palette beyond evidence_read -- decided at design time after the
  measured decision, gated by the arc's principle: every effect
  admitted with a receipt.
- The exact Watch entity ref format in grounding (project://room/{id}
  vs watch://entity/{id}) -- decided at design time.
