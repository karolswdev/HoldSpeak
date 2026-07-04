# Evidence — HS-82-05 — The approval leg and the joint proof

**Status:** done (2026-07-04).

## The approval leg

The belt steers through the native lifecycle, nothing invented: a
story chip click opens the flip row, the chosen verb `POST`s to
`/api/missioncontrol/story/propose` (fields validated against the
LIVE feed — unknown repo/project/story, bad status, and unknown
verbs all 400 before a proposal exists), the proposal lands in
`db.actuators` (desk origin, idempotent on the payload hash), and
the decision route runs the shared `decide_proposal` with a
Delivery Workbench execute leg: a gated connector
(`build_dw_story_connector`) admitting exactly the two `dw story`
argv shapes, argv built from the STORED payload at egress, the
repo path-allow-listed against the operator's project map at
execution time. A dw refusal lands the proposal `failed` with the
banner verbatim in its error field and renders first-class on the
belt.

Unit proof (`uv run --extra test pytest
tests/unit/test_web_routes_missioncontrol.py` — **16 passed**):
propose-validation table, approve→executed with the allow-listed
argv asserted, the crown-case banner riding back verbatim, reject
never touching the CLI, and a tampered payload naming an off-map
repo failing the path-allow-list. Full unit tier: **2425 passed**;
the two `test_doctor_command` project-context failures reproduce
on this desk's `main` checkout too (environment-dependent,
pre-existing, not this phase's doing).

## The joint proof — run live on this desk, 2026-07-04

Server: `uv run holdspeak web --no-open` from this branch's
worktree, against the real `~/.holdspeak/delivery_workbench.json`
project map and the real delivery-workbench checkout (dw 1.9.0).

- **(a) Feed → conveyor:** `/api/missioncontrol/state` relayed the
  live feed — phase 13 at 5/6, next `WLA-13-05` (the counterpart
  story this proof unblocks). The belt renders it:
  [`screenshots/conveyor-live.png`](./screenshots/conveyor-live.png)
  — phases 0–13 as segments, 13 boxed current, stories 01–06 with
  evidence marks, WLA-13-05 in the accent as next actionable, the
  sessions row, and the event ticker narrating this very proof's
  flips.
- **(b) Correlation live:** the real registry relayed — three
  codex sessions `on_story WSH-1-02` (the phase-13-03 fixture
  repo), the claude sessions honest in `off_rails`, awaiting and
  stale flags carried. (Honest note: the delivery-workbench repo
  itself correlates `off_rails` because its roadmap lives under
  `pmo-roadmap/pm/roadmap`, not `pm/roadmap` — the correlator's §2
  rule working as pinned; a compatibility note for their side, not
  a bug in either.)
- **(c) Steering live:** proposal `65da4cfc…` (flip WLA-13-05
  backlog→in-progress), approved as `karol-at-the-desk` → status
  `executed`, argv
  `[…/.githooks/dw, story, status, work-log-automation, 13,
  WLA-13-05, in-progress]` — and `dw context` in that repo showed
  the story in-progress. Restored the same way (a second approved
  proposal back to backlog); both flips appear in their event log
  and on the ticker in the screenshot.
- **(d) The crown case, with a UI:** proposal `d23c02e4…` (flip
  WLA-13-05 to done — no evidence exists), approved anyway →
  status `failed`, error verbatim: `dw exited 1: dw: refusing to
  mark story done without evidence; pass --evidence-body or
  --evidence-from-file`. Driven through the REAL UI with a
  headless browser (chip click → done → the card), the refusal
  renders first-class on the belt:
  [`screenshots/crown-refusal-on-the-desk.png`](./screenshots/crown-refusal-on-the-desk.png).
  An approved proposal refused by the dw gate is the stack
  working — now visible on the Desk that proposed it.

The counterpart's WLA-13-05 cites this evidence for its exit exam.
