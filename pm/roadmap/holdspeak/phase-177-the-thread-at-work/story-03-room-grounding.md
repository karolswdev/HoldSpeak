# HS-177-03 — Room grounding for the Thread

- **Project:** holdspeak
- **Phase:** 177
- **Status:** backlog
- **Depends on:** HS-177-02
- **Unblocks:** HS-177-04, HS-177-05
- **Owner:** unassigned

**CONDITIONAL: this story proceeds only if HS-177-01 produces a GO
verdict. If the measured decision is CUT, this story is cancelled.**

## Problem

The Thread's grounding today resolves desk-level refs only: notes,
meetings, decisions, thoughts (thread_service.py:23,
hydrate_refs_detailed). project.* tools are classified "MCP-only, in
no thread palette" (thread_tools.py:206). The Thread cannot read Watch
entities, project needs-you items, or the steward's output. The arc
says: "Draft / Chase / Plan recipes over real Room data." This story
wires the Room into the Thread's grounding vocabulary and admits
project.* evidence_read tools to the thread palette.

## Scope

- In:
  - New grounding ref types: `project://room/{id}`,
    `watch://entity/{id}`, `project://steward-run/{id}` added to
    hydrate_refs_detailed (thread_service.py:23); the hydrator resolves
    them to Room data, Watch entity snapshots, and steward run
    summaries via project_service and watch_sources.
  - project.* evidence_read tools admitted to the thread palette
    (thread_tools.py:206): project.get, project.get_room,
    project.get_delta, project.list, project.list_updates,
    project.get_steward_run, project.watch.inspect. Classified as
    evidence_read (no palette change for effect_proposal tools).
  - Thread creation with a Room ref: "Continue in thread" from a Room
    opens a thread with the Room as the grounding context; the Room's
    Watch entities and needs-you items are available to the model.
  - The fail-closed gate (thread_tools.py) remains fail-closed: new
    tools are explicitly classified, never admitted by default.
- Out:
  - project.* effect_proposal tools in the thread palette (archive,
    configure_steward, accept_review, etc. stay MCP-only).
  - New Watch source types (the existing GitHub, Jira, and meeting
    sources from 172/175 are sufficient).
  - Workbench Room grounding (deferred to the measured decision's
    outcome for the Workbench).

## Acceptance criteria

- [ ] hydrate_refs_detailed resolves project://room/{id},
      watch://entity/{id}, and project://steward-run/{id} to their
      data (Article IX.1).
- [ ] project.get, project.get_room, project.get_delta, project.list,
      project.list_updates, project.get_steward_run,
      project.watch.inspect are classified as evidence_read in
      thread_tools.py and appear in the Chase and Plan palettes.
- [ ] A thread created from a Room carries the Room's Watch entities
      and needs-you items as grounding context.
- [ ] The fail-closed gate blocks unclassified project.* tools;
      verified by a test that adds a fake project tool and asserts
      denial.
- [ ] Zero egress (Article III); the grounding data stays local.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k room_grounding`
  - hydrate_refs_detailed resolves the three new ref types.
  - project.* evidence_read tools are in Chase and Plan palettes.
  - Unclassified project tools are denied by the gate.
- Integration: a thread created from a Room resolves Watch entity refs
  and project.get_room returns data.
- Manual: the owner opens a Chase thread from a Room; the model cites
  Watch entities in its response.

## Notes / open questions

- The ref format (project://room/{id} vs watch://entity/{id}) is a
  proposal; the owner may prefer a different grammar at design time.
- The existing grounding refs use desk-qualified URIs
  (desk://note/{id}, meeting://{id}). The Room refs follow the same
  pattern.
