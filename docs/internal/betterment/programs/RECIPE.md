# Programs: the recipe

The slices that make `PROGRAMS-DESIGN-2026-10-28.md` real. The owner asked
for one holistic PR (2026-10-28), so PG1 to PG11 ship in one PR from the
program branch `lane/programs-20261028`, built by three lanes (PG-HUB,
PG-FACES, PG-DOCS; design §12). The slices after PG11 are left for later
PRs in the fast cycle (`CLAUDE.md`). Short paths: `desk/` is `web/src/desk/`,
`hs/` is `holdspeak/`. Tests follow the test diet: T1 a hub test, T2 vitest
(one file per app: `desk/programs/__tests__/programs.app.test.tsx`), T3 the
desk sweep, T4 a real browser only for keys, drag or touch.

**The rig for every slice.** `tests/integration/program_rig.py` runs a
Program against fake agents: a fake launch that commits on its branch, the
fake gate `tests/fixtures/fake_program_check.sh` (writes a green or red
log in the quick check's shape), a fake reviewer verdict and a fake
follow-through merge. `scripts/record_program_fixtures.py` records the
hub's real answers from that rig into `desk/programs/__fixtures__/` for the
T2 doubles. Never start his real `claude`, `codex` or `pi` in a test; every
rig hub sets `HOLDSPEAK_PROGRAMS=off` unless the test drives the runner.

State: **Shipped** means in this PR. **Left** means a later slice.

---

## PG1. The record: Programs, Steps, Checkpoints (Shipped)

- **Goal**: a Program, its steps and its checkpoint lines are stored, with
  the state machine of design §4.
- **Files**: `hs/db/schema.py` (+ `tests/fixtures/db_schema_canonical.txt`),
  `hs/db/programs.py`, `hs/services/program_service.py`,
  `hs/program_templates.py`.
- **Changes**: three tables and one index (`programs`, `program_steps`,
  `program_checkpoints`; the extra columns are in the design's "Built"
  section); create, plan (replace or append; `size: auto` triage by rule),
  update, start, park, resume, close; the transition table; the five
  templates (Fast cycle, Build and review, Race, From the desk, Overnight on
  the home box).
- **Done when**: every state has its moves and a refused move raises; a
  plan with `size: auto` sets each step's effort by rule.
- **Tests**: T1 `tests/unit/test_program_service.py`
  (`test_the_transition_table_covers_every_state_and_its_moves`,
  `test_a_refused_move_raises`, `test_triage_by_rule`,
  `test_plan_size_auto_sets_effort`,
  `test_the_overnight_template_runs_pi_on_the_home_engine_at_yolo`).
- **Not in this slice**: the tick.

## PG2. The control ladder and core questions (Shipped)

- **Goal**: the engine decides by rule at the Program's level (Secure,
  Normal, YOLO); a core question goes to him at every level.
- **Files**: `hs/services/program_rules.py`.
- **Changes**: one function `decide(level, kind, facts)` that returns a
  `Decision` (choice, rule, overturnable) or a `CoreQuestion`; `is_core`
  for the core list of design §6 (goal, shape, egress, money, authority or
  config, safety, no rule). Rounds: 2 at Secure and Normal, 3 at YOLO.
- **Done when**: each row of the §6 table has a test at each level.
- **Tests**: T1 `tests/unit/test_program_rules.py`.
- **Not in this slice**: a second classifier for agent questions (the
  desk's `AgentResponder` stays the only one).

## PG3. The gate: a verified log (Shipped)

- **Goal**: a step is green only when its check log says so, never on an
  exit code.
- **Files**: `hs/services/program_verifier.py`, `scripts/quick_check.sh`
  (a `build ok` line; `HOME_REAL` kept when the caller isolated HOME).
- **Changes**: the check runs in the step's worktree, through
  `scripts/test_lock.py` when the repository has it, with an isolated HOME,
  to `<worktree>/.tmp/program-check/<step>/<ts>.log`; the verifier checks
  the commit line, a clean tree at start, every section's result line, no
  red, no section twice, the final verdict line. No log path: not green.
- **Done when**: a green log is green; each of the four rules turns a
  log red.
- **Tests**: T1 `tests/unit/test_program_verifier.py`.
- **Not in this slice**: per-repository check shapes beyond the quick
  check's sections (a repository names its command in
  `.holdspeak/program.json`).

## PG4. The tick, the hand kind and the brief (Shipped)

- **Goal**: ready steps are handed to agents in their own worktrees, up to
  the desk's working slots, and followed to a commit.
- **Files**: `hs/services/program_runner.py`, `hs/services/program_brief.py`,
  `hs/agent_operations.py`, `hs/services/agent_hand_service.py`,
  `hs/services/agent_brief.py`, `hs/workbench_conductor.py`,
  `hs/delivery/factory_launch.py`, `hs/delivery/pi_launch.py`.
- **Changes**: the hand kind `program_step` (worktree `hs-program-<step>`,
  branch `program/<slug>/<n>-<slug>`, `start_point` the base branch); the
  brief (who and where, the goal, the files it owns and "theirs, do not
  touch", the proof, the rules, whose word); the 30 s tick from the
  workbench conductor and a tick after each press; Runs on (Claude Code,
  Codex, pi on any engine) and **when idle** ("Ready · waiting for qwen");
  spend as a core question for pi on a hosted engine with no limit;
  `HOLDSPEAK_PROGRAMS=off`.
- **Done when**: two steps hand, the third waits for them; a pi step waits
  for its idle engine, then dispatches; with the switch off nothing ticks.
- **Tests**: T1 `tests/unit/test_program_hand.py`,
  `tests/unit/test_program_service.py`
  (`test_the_brief_names_who_where_theirs_and_the_proof`,
  `test_a_pi_step_waits_for_its_idle_engine_then_dispatches`,
  `test_the_idle_gate_reads_the_engine_lanes`,
  `test_a_hosted_pi_engine_with_no_spend_limit_is_a_core_question`),
  `tests/integration/test_program_run.py::test_programs_off_ticks_nothing`.
- **Not in this slice**: a tick at once on a coder frame (PG12).

## PG5. Review, findings, the PR and the merge (Shipped)

- **Goal**: a green step is reviewed, its PR opened and merged by the
  level, with two rounds before him.
- **Files**: `hs/services/program_runner.py`, `hs/services/agent_review.py`,
  `hs/delivery/follow_through.py`, `hs/delivery/pr_receipts.py`.
- **Changes**: AG12's review pair at the step's depth; REQUIRED back to the
  builder, SHOULD and NOTE by the level; `gh pr create` from the launch's
  repository; Secure asks Merge?, Normal and YOLO merge on green and PASS;
  merged is the follow-through's receipt; a race of 2 or 3 parks the
  losers; a human review gate (`gate_review = person`) holds the merge for
  that person's approval on GitHub.
- **Done when**: the rig Program of design §12 runs end to end at Secure
  and at Normal; a red gate gets round 2 then parks; a race parks its
  loser; a person review holds the merge.
- **Tests**: T1 `tests/integration/test_program_run.py`
  (`test_three_steps_at_secure_wait_for_his_merge`,
  `test_three_steps_at_normal_merge_without_a_press_and_say_so`,
  `test_a_red_gate_gets_round_two_then_parks`,
  `test_normal_parks_a_failed_step_and_carries_on`,
  `test_a_race_of_two_parks_the_loser`,
  `test_a_person_review_holds_the_merge_until_their_approval`,
  `test_a_diff_outside_the_owned_files_is_a_core_question`).
- **Not in this slice**: agreement across the race losers' diffs.

## PG6. The handover note, Decided for you and Overturn (Shipped)

- **Goal**: the Program's state is a desk Note he and any new agent read
  first; every engine decision is listed with its rule and can be undone
  while it can.
- **Files**: `hs/services/program_service.py`, `hs/kernel/program_ops.py`,
  `hs/kernel/runtime.py`, `hs/services/desk_kernel.py`.
- **Changes**: the Note `program-<id>` titled "Program: <title>",
  rewritten on each change (Your turn, Steps, Parked, Decided for you, Last
  checked; "Done · date · n PRs · time" at the end), filed to the Project;
  each decision is a checkpoint with `by: engine` and a kernel operation
  `program.step`; `overturn` undoes a Later task, a Skip, a parked step or
  an added step, never a merge.
- **Done when**: the note is rewritten at each change in the rig run; an
  overturned decision is marked and undone.
- **Tests**: T1 `tests/integration/test_program_run.py`,
  `tests/unit/test_kernel_effect_fence.py`.
- **Not in this slice**: promoting a Skip or an engine merge to a proposed
  decision record (PG16).

## PG7. The desk's tools: REST, MCP and the frame (Shipped)

- **Goal**: he, an orchestrating agent and a step's own agent reach the
  same service.
- **Files**: `hs/web/routes/programs.py`, `hs/web_server.py`,
  `hs/mcp/families/program.py`, `hs/mcp/families/__init__.py`,
  `hs/mcp/tool_authority.py`, `hs/realtime_frames.py`,
  `web/src/runtime/frames.ts`,
  `docs/internal/philo/phase-5/residual-set.json`.
- **Changes**: fifteen routes under `/api/programs` (each through
  `run_in_threadpool`); twelve `program.*` tools (`decide` and `overturn`
  AUTHORITY, his press; `checkpoint` and `step_done` only for the calling
  launch's own step); the `program_changed` frame.
- **Done when**: an agent cannot decide; a launch cannot write another
  step's checkpoint; the frame has a consumer.
- **Tests**: T1 `tests/unit/test_program_service.py::test_mcp_authority_rules`,
  `tests/unit/test_realtime_frame_registry.py`; T2
  `web/src/runtime/frames.test.ts`.
- **Not in this slice**: none.

## PG8. The Program in the ecosystem, hub half (Shipped)

- **Goal**: a Program lives in its Project, knows its origin and its
  person, and leaves its work behind (design §9b).
- **Files**: `hs/services/needs_you_membership.py`,
  `hs/services/project_service.py`, `hs/services/project_update_service.py`,
  `hs/services/people_service.py`, `hs/services/monday_brief_service.py`,
  `hs/delivery/follow_through.py`.
- **Changes**: `program_items` in Needs you (merge asks, findings left,
  engine-parked steps, a person to ask, core questions, close; due word
  "now"); the Room's Programs read; the steward update's Programs
  paragraph; the Monday brief's count; the person's Programs line and the
  1:1 brief's "To show them" and "To ask"; From the desk closes its action
  on merge with the PR as evidence.
- **Done when**: a From the desk Program closes its action on merge; the
  1:1 brief lists the merged step; Needs you carries only his kinds.
- **Tests**: T1 `tests/integration/test_program_run.py`
  (`test_from_the_desk_closes_its_action_on_merge`,
  `test_the_one_on_one_brief_lists_a_merged_step_to_show`),
  `tests/unit/test_program_service.py::test_program_items_carry_only_his_kinds`,
  `tests/unit/test_project_room_read.py`.
- **Not in this slice**: the faces of these seams (PG10).

## PG9. The Programs window and the Program window (Shipped)

- **Goal**: he sees every Program, waiting first, and drives one from its
  own window (design §9; canvas direction C, the ledger).
- **Files**: `desk/programs/` (ProgramsWindow.tsx, ProgramWindow.tsx,
  StepRow.tsx, StationTrack.tsx, RoomPrograms.tsx, PersonPrograms.tsx, fromNote.ts, api.ts, types.ts, programs.css,
  `__fixtures__/`), `desk/applications.ts` (`surface-programs`, ⌃7, the
  `program:` pullout family), `desk/pullouts/registry.ts`,
  `web/scripts/gen-icons-d.py` (the program sprite).
- **Changes**: the list in bands (Your turn, Running, Drafting, Done,
  Parked); the Your turn well with its verbs; the board of 32 px rows with
  the station track; the Decided for you, Checkpoints and Gate folds;
  Control ▾; Agent: … ▾ with When idle (the Engines name guard refuses
  "Runs on" on a face); 393 as two-line rows with a
  StateChip.
- **Done when**: every state of design §4 draws from the recorded
  fixtures; each your-turn verb presses through to the rendered outcome;
  still, fit, contrast and 44 px at 393.
- **Tests**: T2 `desk/programs/__tests__/programs.app.test.tsx`; T3 the
  sweep cases `surface-programs` and `pullout:program` at 1440 and 393.
- **Not in this slice**: editing a step's brief on the phone; a race shot
  (the rig recorded no race fixture).

## PG10. The seams on the faces (Shipped)

- **Goal**: a Program shows where his other work shows.
- **Files**: `desk/needsYou.ts`, the Conductor row, the Dock lamp, the Room
  fold, the person's room, the Note's toolbar fold.
- **Changes**: Needs you rows grouped by the Program's title; "Step 4 of
  <title>" under an agent in Agents; the Agents lamp takes the worst
  Program state; the Room's Programs fold; the person's Programs line; the
  Note's **Run as a program**; the place line and the "No project" token.
- **Done when**: each seam draws from the recorded fixtures at 1440 and
  393.
- **Tests**: T2 the app files of each seam.
- **Not in this slice**: Today's "Since morning" line (PG18); a browser shot
  of the person line, the Room fold and the Note verb (pinned in the app
  tests only).

## PG11. The documents (Shipped)

- **Goal**: he, an agent and a new chat can learn Programs from the docs.
- **Files**: `docs/programs.md`, `agent/skills/holdspeak-programs/SKILL.md`,
  this file, the design's "Built" section, `docs/internal/UX-CANON.md`,
  `README.md`, `docs/internal/betterment/INVENTORY.md`, `TRACKER.md`,
  `pm/STATUS.md`, the generated docs (`scripts/gen_docs.sh`).
- **Done when**: `scripts/gen_docs.sh` is clean; the docs guards are green.
- **Tests**: `tests/unit/test_docs_navigation.py`,
  `tests/unit/test_product_copy.py`, `tests/unit/test_api_surface.py`.
- **Not in this slice**: none.

---

## Left for later slices

## PG12. Tick on the coder frame (Left)

- **Goal**: a step moves on the moment its agent's turn ends, not on the
  next 30 s tick.
- **Files**: `hs/services/program_runner.py`, the coder frame's hub-side
  listener.
- **Changes**: a launch that belongs to a step ticks its Program on its
  `intel_status` (scope `coder`) frame and on the Heartbeat's
  `desk_changed("launch", …)`.
- **Done when**: in the rig, a fake turn end moves the step to Checking
  with no wait.
- **Tests**: T1 `tests/integration/test_program_run.py`.
- **Not in this slice**: none.

## PG13. The Program's level drives the desk's answers (Left)

- **Goal**: a Program at YOLO on a desk at Secure gets YOLO's answers for
  its own agents.
- **Files**: `hs/services/agent_responder.py`, the gate's decision path.
- **Changes**: `AgentResponder` and the gate read the Program's level for a
  launch that belongs to a step; every other launch keeps the desk's mode.
- **Done when**: the rows of design §6 for routine questions and
  approvals hold per Program.
- **Tests**: T1 the responder's and the gate's tests.
- **Not in this slice**: per-step levels.

## PG14. Automations run a program (Left)

- **Goal**: a schedule or a Watch event starts a Program from a template.
- **Files**: the Automations Do kinds, `hs/program_templates.py`.
- **Changes**: a Do kind **Run a program** (template + Project).
- **Done when**: a schedule starts a From the desk Program on a project.
- **Tests**: T1 the Automations kind tests.
- **Not in this slice**: Watch-driven templates other than From the desk.

## PG15. Start a program on a call (Left)

- **Goal**: "start the overnight program on the hub" on a call is
  `program.start` behind his spoken yes.
- **Files**: `hs/calls/`.
- **Changes**: `program.start` and `program.get` in the call palette; start
  held for his yes (the Calls gate, as built).
- **Done when**: the fake ai-phone rig starts a Program after a spoken yes.
- **Tests**: T1 the Calls rig.
- **Not in this slice**: decide on a call.

## PG16. Decisions from a Program (Left)

- **Goal**: a skipped finding or an engine merge may become a proposed
  decision record.
- **Files**: `hs/services/program_service.py`, the decision record service.
- **Changes**: a Skip's reason and a merge's rule become a proposed record
  linked to the PRs (`decision_record.link_work`).
- **Done when**: a Skip shows as a proposed decision in the Room.
- **Tests**: T1.
- **Not in this slice**: auto-confirm.

## PG17. The first Program is the engine's own history (Left)

- **Goal**: on his desk, the refactor program (#1584 to #1598) is
  re-created from its PRs and shows Done (design §13, §15).
- **Files**: a one-time script or an MCP session; no product code.
- **Changes**: `program.create` + `program.plan` with the merged PRs as
  steps in state Merged.
- **Done when**: the Programs window on his desk shows it Done with its PR
  numbers.
- **Tests**: none (his desk).
- **Not in this slice**: none.

## PG18. Programs on Today (Left)

- **Goal**: "Programs: 1 running, 1 waits on you" in Today's Since morning
  when a Program moved today (design §9 Seams).
- **Files**: the Today face, the Today read.
- **Changes**: one line from `program.list`, only when not zero.
- **Done when**: a Program that moved today shows the line at 1440 and 393.
- **Tests**: T2 the Today app file.
- **Not in this slice**: The Week's count.
