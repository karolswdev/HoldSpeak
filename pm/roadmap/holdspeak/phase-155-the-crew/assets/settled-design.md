# Phase 155 settled design — The Crew (DC-05)

Ruled by the orchestrator 2026-08-30 from the holistic counsel
design-beat (Phase 152 `assets/counsel-design-beat.md`: RATIFY; S7,
R5) and RFC §6.9. Builders implement. The charter commit lands on PR
#511 (`feat/deskos-platform-revolution`), the superseding merge vehicle.

## The one sentence

The Thread learns to delegate: a subthread is a real child thread on
the desk — bound to a mode, receipted like everything else, run by the
conductor the desk already trusts — and its report comes back as a tool
message the parent's next pass consumes.

## D1 — the subthread tool (story 01)

- `chat.subthread` MCP tool (effect_proposal): creates a child
  `threads` row via the EXISTING `threads.parent_thread_id`
  (schema.py:3416), bound to a Recipe/mode (153's binding); arguments
  {title, mode, prompt, wait_s?}; S7 validation (mode exists and is
  kind='mode', prompt non-empty, depth cap 1 — a child cannot spawn
  children in this phase). warpdrv auto-approves subthread tools; OURS
  STAYS RECEIPTED: the call is admitted as a kernel child of the parent
  turn's operation through the SAME executor/truth-table path — no new
  admission door.
- The child's palette = its bound mode; `thread_tool_policy` rows may
  pre-allow the mode's list for the child (append-only, receipted).

## D2 — the conductor (story 02)

- The child runs on the EXISTING workbench conductor run-loop
  (`holdspeak/workbench_conductor.py` owns fresh-session runs + bus
  frames today). The parent turn blocks up to 30 s for a fast child
  (S7: the wait is configurable on the tool args, capped), then
  backgrounds; the tool result then reports {child_thread_id,
  state: backgrounded}.

## D3 — notifications (story 03)

- Child → parent messages are `thread.notification` frames + rows; the
  parent's NEXT pass consumes pending notifications as `tool` role
  messages (the 152 exchange format). R5 (recorded): concurrent
  parent/child writes — last writer wins; no locks in this phase.
- The pullout renders the notification row (in-flow, provenance to the
  child, RAW fold) with the 152-05 renderer pattern.

## D4 — the child on the desk (story 04)

- The child thread is a REAL desk object: it opens like any thread
  (read, steer, annotate); its head shows "child of <parent>" with a
  jump link both ways; stopping the child stops its run through the
  conductor. The parent's thread shows a crew row (children with state
  chips).

## D5 — the walk (story 05)

Glass 1440+393 (crew row, child head, notification row); metal on `.43`
(a real delegated read task round-trips; the fence leg proves no
People-egress laundering through a child); docs; close counsel; honest
sweep. The exhibit closes the arc — the port's five rooms shipped.

Recorded: R5 last-writer-wins; depth cap 1; S7 30 s configurable.
