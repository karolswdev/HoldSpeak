# HS-82-05 — The approval leg and the joint proof

- **Project:** holdspeak
- **Phase:** 82
- **Status:** backlog
- **Depends on:** HS-82-03, HS-82-04 (the belt and its live layer).
- **Unblocks:** phase close; unblocks the counterpart's WLA-13-05
  (their joint exit exam runs against this).

*Re-pinned by HS-82-01 (2026-07-04): implement against [docs/internal/MISSION_CONTROL_DESK.md](../../../../docs/internal/MISSION_CONTROL_DESK.md) §4+§5.*

## Problem

Mission control that can only watch is a dashboard. The write path
already exists with two consent layers in front of it — the
actuator pack proposes, a human approves, the gated connector
executes exactly two `dw story` argv shapes, and the dw gate still
refuses anything dishonest. The Desk needs to drive that path from
the belt, and the whole two-repo stack needs one continuous
demonstration.

## The design

A story item on the belt offers the two rails verbs as proposals:
the Desk builds a `dw_action` fields payload (never argv), the
proposal renders with the actuator pack's own preview, approval is
an explicit act in the Desk UI, and execution goes through the
`dw_story_writer` connector. A dw refusal renders as the stack
working: the banner verbatim, pinned to the story that refused,
and the same refusal arrives as a `gate_refusal`/failed-flip in
the event layer. Then the joint proof, evidence-captured on this
desk against the real delivery-workbench checkout: (a) live phase
state on the belt; (b) a real agent session correlated to its
story with its blocked state; (c) an approved flip moving the
conveyor; (d) the crown case — an approved, evidence-less done
flip refused by the dw gate, refusal rendered first-class. Those
four legs are exactly their WLA-13-05's acceptance list; this
story's evidence (screenshots + captured outputs) is what that
story cites.

## Test plan

- Unit: `dw_action` payload construction from a belt item;
  refusal rendering from a connector error fixture.
- Integration: the proposal→approval→connector flow against a
  fixture rails repo (the connector's own test seam), including
  the refused done-flip.
- Manual on this desk: the four joint-proof legs above, every leg
  captured into evidence; screenshots under `screenshots/`.
