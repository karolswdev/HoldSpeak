# Status

The one status file. Update it when a PR merges. Rules: `CLAUDE.md`, "How we work now".
The old roadmap under `pm/roadmap/` is history; it is not updated. Its shots and run
dumps are on branch `archive/evidence-2026-10-04` (`pm/ARCHIVE.md`).

**Last updated:** 2026-11-01. Programs PG-IMPORT IMP1, the step report (BroCrew: "a finished piece of work comes back with its outcome, what was checked, what wasn't, and where the files are"). Each engine checkpoint on a step records what the engine saw (`undo.seen`: the moved head commit, the checked commit and verdict, the PR, the state); a step reaching Merged, Done, Parked or Failed records its diff file names once (`facts.files`, `ProgramRunner.step_files`, the engine's check logs left out). `brief_words.step_report` builds `report` on each such step in `/api/programs/{id}`: `observed` ("Checked:", each line citing the engine checkpoint that saw it; a fact no engine checkpoint saw is left out), `claimed` ("The agent says:", the agent's report lines and its own checkpoint lines), `not_checked` ("Not checked:", Your word nobody judged, a review that did not run, the gate check off, waived), `files` ("Files:", 12 and "and N more"); the agent's text is now `report_text`. The open step (`StepFold`) reads the four registers as plain labels in that order (in place of the story); the briefing page has a **Report** pane (rows). A Done Program carries `finished` / `finished_words` ("finished" or "finished · needs a decision" for a delivery row, an undecided finding or proposed step): grey words in the list row's line cell (in the steps line at 393) and under the Program window's line, never the Your turn lamp. Tests `tests/unit/test_program_step_report.py` (4; the fence: garbled engine lines give the same Checked register, no `seen` gives none), `test_brief_in_his_terms.py` (the Report pane), vitest `programs.app.test.tsx` (3 new) and `briefing.app.test.tsx` (Report opens), the desk sweep's new `program-done` case (a Done Program, its step open, at 1440 and 393). Fixed on the way: a Done last station on the Program window's line drew a dark band over the whole line. Fixtures re-recorded (`record_program_fixtures.py`, now with the agent's words on the Done program; `test_program_delivery.py`, `test_desk_reach.py` and the other Programs writers with `HOLDSPEAK_WIRE_WRITE=1`). Open: IMP2 to IMP7.

**Before it:** 2026-11-01. The live proof's false refusals (run 3, #116 and #130, "Refused by rule (YOLO): git") found and fixed (lane PG-EXEC). Read from the real Claude Code's own session transcripts: each refused call was a fine commit that, in the same Bash call, also wrote a check log in Claude Code's own session scratchpad (`/private/tmp/claude-<uid>/<the worktree path with - for each other character>/<session>/scratchpad/`), which the gate read as a write outside the worktree. `tool_gate_rules.agent_scratch_roots`: that folder of the launch's own worktree now counts as the agent's own scratch for Bash paths and file writes; any other folder outside stays outside. A refusal's (and a rule allow's) Decided-for-you checkpoint now keeps `undo.detail`: the whole redacted command (not the 120-character head) and the cwd, rule and scope the gate saw. Fence: the proof's two commands (they fail on the old classifier) and three more commit shapes (a `$(cat <<'EOF' …)` message, `cd <wt> &&`, `git -C <wt>`) in `tests/integration/test_program_execution_perfection.py`; the detail in `tests/unit/test_program_control_level.py`.

**Before it:** 2026-11-01. DIR7 in Settings ▸ Reach: "When to reach you" is the ladder, its rungs in the hub's order (Desk · Phone · Telegram · Call), each with its wait as a picker (Desk at once; Phone At once/Off via `phone_app`; Telegram's four choices; Call by the Reach you rules); quiet hours and the digest hour were already on the page. Fixture `reach.phone_off.json` recorded in `tests/integration/test_desk_reach_settings.py`. Open work: the Dreaming template in the picker; the owner's live verdict.

**Before it:** 2026-11-01. The live proof on his hub reached Done (program-d995d9060cd6: 3 steps at YOLO, a scratch repository with a bare origin, check `sh -c 'test -f README.md'`, the real Claude Code in tmux): 2 min 46 s from Start to Done, zero Your turn items, zero presses, three merges on the bare remote's main (after #1698 and #1700); parked after. Then DIR9's page half and DIR10 in part (lane PG-EXEC): one briefing page carries up to 12 held items in order (`kind: digest`, 12 h), each decided alone and settled to its line, the page's count following; the morning message links one page for the night's held items. `holdspeak/services/briefing_sources.py`: a Desk decision to review (Confirm, `PrimitiveService.update_decision_status`) and a held call (Call now `ring_held`, Let it wait `decline`) are packages answered through their own verbs; Later records the next touch for them. Recorded page shapes: `web/src/briefing/__fixtures__/reach.digest.json`, `reach.digest.answered.json`, `reach.decision.json` (the briefing face does not draw several items yet: the window lane). Open: the other held sources (meeting proposals, project proposals, agents' questions, sends and gate holds page-only), DIR9's sentence-to-shape preview, and the page face for a digest.

**Before it:** 2026-11-01. JRN2's face: the library Button **Tonight** on a Door task's row in Needs you and in the ⋯ menu of a found task line in a Note (`programs/TonightVerb.tsx`, `POST /api/programs/tonight`); after the press the row says "Tonight · in <night program>"; a refusal is the hub's words in place. Fixtures `tonight.added.json` and `tonight.refused.json` recorded in `tests/integration/test_desk_program_night.py`. Open work: DIR7 Reach ladder settings; the Dreaming template in the picker; the owner's live verdict.

**Before it:** 2026-11-01. The Programs list in direction A (canvas program-window-2026-10-31.html "List" mounts): each row is the title, a lamp and the hub's line in his terms (`brief_words.list_line`: "Step 2 of 3 waits on you since 21:43", "Runs step 4 of 8, Claude Code, 11 min", "Done, 14 PRs, 28 Oct"), a mini track (`list_track`) and the Met count; no column heads. Fixtures re-recorded. Open work: JRN2 Tonight verb, DIR7 Reach ladder settings, the owner's live verdict.

**Before it:** 2026-11-01. The live proof's second run (program-acccc69962b8, his hub) stalled at the launch: Claude Code's folder-trust prompt kept "No, exit" selected because the one Down landed while the prompt still drew (`trust_state: timeout`; Programs read the waiting pane as "The agent asks a question"). `first_message._Trust` (and the Codex screen) now presses the move again when the cursor did not move, after 1.5 s, at most 3 times, and looks for the prompt for 60 s (was 20); the one confirm is unchanged. Test `tests/unit/test_agent_hand.py::test_a_down_the_prompt_did_not_take_is_pressed_again_then_one_confirm`.

**Before it:** 2026-11-01. Programs PG-IMPORT design (the best of BroCrew, the owner's sister project, rebuilt on our engine): `docs/internal/betterment/programs/BROCREW-IMPORT-2026-11-01.md` names seven slices with BroCrew's rule, what Programs has today and the change: IMP1 the step report in registers (Checked, The agent says, Not checked, Files) and the achromatic "finished · needs a decision" mark; IMP2 the to-do row (Done, Can't do it) and the ending word; IMP3 wait sentences and Since you were last here on Today; IMP4 never wider than the parent (closes the open control ruling); IMP5 the `because` on each routed request and four honest refusals of a late answer; IMP6 take it over and hand it back on a step's lane; IMP7 the forest (later). IMP1 and IMP2 build next. Open: IMP3 to IMP7.


**Before it:** 2026-11-01. Programs: the live proof's causes (lane PG-EXEC). On his hub, a 3-step YOLO program on a scratch repository with a bare `origin` and the check `sh -c 'test -f README.md'` (program-2633c39e2151) stalled at step 1: (1) a plain check command (no `== section` lines, no verdict line) was judged red, "the log does not end with the check's verdict line", on a green exit; now such a log is judged by the engine's exit line and red lines (`program_verifier.verify_text`), and any non-zero exit is red in every form. (2) After "New commit …; the check runs", the end of the turn that made the commit was read as "The turn ended with no commit; asked the agent to commit" (then "ended its turn twice with no commit", parked); that turn's end is now taken as the commit's (`commit_turn_open`). (3) A remote that is not on GitHub has no PR: HoldSpeak pushes the branch and merges it into the base itself (rebase on `origin/<base>`, fast-forward push), by the same merge rule ("Merged step 1 into main on the remote (…)"; his Merge row at Secure: "into main"). The Programs rig's `origin` is now a GitHub URL rewritten to its bare repository (`url.<bare>.insteadOf`); `Rig(github=False)` keeps the bare path. Fence: three new cases in `tests/integration/test_program_execution_perfection.py`, one in `tests/unit/test_program_verifier.py`.

**Before it:** 2026-11-01. Journey J2 "The dreaming program" on the hub (LANG12 rest, JRN3, JRN4; lane PG-EXEC). (a) The **Dreaming** template (`program_templates.DREAMING`): night 23:30–07:00 · at most 8 steps, YOLO, pi on the home engine when idle, budget 64k, review at glance, the home engine as planner when the library has it, `within` = the design's folders the repository has; a night Program may start empty. (b) **The backlog by rule** at the window's start, once a night (`program_night.read_backlog`): open Door tasks with the word "dream" and the Program's own Later tasks become steps for the cheap planner (one `program.night_item@1` call each; REAL qwen3.8-27b replies recorded by `scripts/record_program_night_reply.py --only backlog`), up to `at most`; YOLO adds with Overturn, below YOLO one line. (c) **JRN3 red main**: the base branch's newest finished GitHub run (`gh run list`; the hub had no reader of the main watcher's runs) failed → one "Make main green" step first, the rest "waits: main is red", "Main is green again" when a run passes; the digest says how long the night waited. **Two red steps in a row** stop the night ("the night stopped after 2 red steps"; the digest says so). (d) **The window's end**: a working step's agent is asked to commit; at its turn's end or 10 min later the engine commits what is left and parks it "Night ended; parked with a commit" (not a Your turn row); the next night it goes on in the same worktree. (e) **JRN4**: the night's line is the morning's one Telegram message at the digest hour, with the night's held count and the first item's briefing page; that morning's plain digest is not sent again. Tests `tests/unit/test_program_dreaming.py` (6, frozen clock). Open: canon/test-report backlog sources, `within` on the diff, one page for several items (DIR9), the template in the New program picker (`web/src/desk/programs/api.ts`, window lane), the Reach settings face (DIR7).

**Before it:** 2026-11-01. Programs LANG13 in the window: the `delivery` Your turn row is the Program window's headline (Merge or Skip at Secure; Retry or Skip after a failure), each choice with its consequence from `brief_words`; it is briefable (the page, Telegram and the call read the same lines); the Done window says "Delivered to dw app/1 (PR #n)" under the track. Fixtures recorded in `tests/integration/test_program_delivery.py` (`program.delivery_*.json`). Open work: the owner's live verdict.

**Before it:** 2026-11-01. The fold, built (design #1694, direction B): every fold on the desk (the kit's FoldGadget and Disclosure, Today's three folds, Needs you's Show/Hide) says Show or Hide at the right, no triangle; menus keep their caret. The Program window: the body announces it scrolls (ScrollHint) and the Steps caption counts the steps; Drafting at 393 puts the tray before a long goal (the first sentence, the tray, then the goal in full); Open lane only on a step whose lane is alive. Open work: the owner's live verdict.

**Before it:** 2026-11-01. The fold design (owner: "that left chevron something: fuck off. Invent something a lot clearer"): canvas `docs/internal/betterment/canvases/fold-2026-11-01.html`, three directions on the Program window's Decided for you and Ledger and on Today's folds, at 1440 and 393. Chosen: B, the title, its count and a Show · Hide verb at the right; the open section under a hairline rule. Menus keep their caret. The kit build follows.

**Before it:** 2026-11-01. Programs LANG13, the delivery at Done (lane PG-EXEC). A Program with `delivery dw <project>/<phase>[/<story>]` writes ONE delivery when it closes (`holdspeak/services/program_delivery.py`): a scratch worktree at the base head on `program/<slug>/delivery` (never his working tree), the repository's own rails (`missioncontrol_bridge.dw_argv_base`): `dw story create` when no story is named, `dw story evidence --from-file` with the Program's Done (§8.3), `dw story status … done`; one commit, push and PR "Delivery: <title> done", merged at Normal and YOLO, his Merge/Skip row at Secure. Ledger lines `kind = delivery`: "Delivered to dw app/1 (PR #12)"; a failure "Could not deliver to dw app/1/07: Delivery Workbench did not take the evidence" (dw's or git's words in `undo.detail`) and his Retry/Skip row (Your turn kind `delivery`; `decide(kind="delivery")`). No migration: the ledger is the record. Fence `tests/integration/test_program_delivery.py` (the real dw rails copied into a scratch repository). Open: the link at create (`dw context`, acceptance lines as proposed requirements), a milestone's `dw phase close`, refusing the line on HoldSpeak's own repository (§8.1), the faces' buttons for the `delivery` row (window lane).

**Before it:** 2026-11-01. Programs PG-WINDOW follow-up (from live shots on his hub): Drafting in direction A (the goal as the headline edited in place; Start with what it checks, Plan it, Ask me first in the tray; each step a row that opens to its fields, its gate as plain words with pickers and what it must prove; the spreadsheet rows parked); step rows say the hub's story, never a raw engine note; no empty What it must prove; no step opens by itself while one waits on him (every step in view); Copy page link moved from the tray to the words row. Fixtures re-recorded. Open work: the owner's live verdict.

**Before it:** 2026-11-01. Programs LANG11, the Measure kind (lane PG-EXEC). A `measure` requirement now runs at CHECK like a Check (and at the end check): the last output line that names the metric and then a number gives the value, in the bound's unit (ms, s, min; kB, MB, GB), compared with the bound (`p95 < 100 ms`, also in words: `total under 2 s`, `files at most 3`, `errors equal to 0`). The evidence line is in his words, "Measured 1.4 s, under 2 s", on the requirement and the step's ledger ("R1 · Met · …"); over the bound is a red round for the builder; a command that did not run or printed no number is Unmet, "Not measured: the command ended with exit 127". A Measure gates like a Check (a check made a measure no longer lowers the bar). A walk stays Your word: his row carries `walk` (the lines he does); HoldSpeak never runs it. `program_verifier.verify_measure_log`, `program_requirements.RUN_KINDS`; docs/programs.md updated. Open: LANG13 (delivery at Done), LANG12 rest, LANG14.

**Before it:** 2026-11-01. Reach tests read no wall clock (lane PG-EXEC). `test_reach_telegram::test_the_ladder_sends_once_at_once_and_waits_in_quiet_hours` failed from 00:00 to 00:59: with quiet hours (0, 0) the digest hour is 0, so the first tick sent the digest too. It and its siblings (`test_reach_later` "later means tomorrow", `test_program_night` night line) now run at `program_rig.local_noon()` (today 12:00, built naive then zoned: on 2026-11-01, the DST change, `replace(hour=12)` kept the night's offset and read 11:00). The Programs rig's Phone service reads quiet hours at the same noon (`frozen_quiet_phone`), so a recorded answer never says "held for the morning" because of the hour it was recorded; the recorded Programs and briefing fixtures were re-recorded at night with it ("Reached you: a message", the YOLO rule). Timestamps and clock words in fixtures still carry the recording time (shape-compared only).

**Before it:** 2026-11-01. Programs execution perfection, part 2 (lane PG-EXEC). (1) At YOLO a Program step's call the gate reads `unparsed` is never held for him: in its own worktree (the hub checks the folder) it is allowed by rule ("Allowed by rule (YOLO): env"); a call aimed outside the worktree, or one naming a destructive word (`tool_gate_rules.destructive_word`: sudo, rm -r/-f, git push --force, git reset --hard, git clean, mkfs, dd, chmod -R, curl into a shell, …), is refused by rule ("Refused by rule (YOLO): sudo"), the agent told not to retry it another way. Policy `operation_policy._resolve_tool_gate` (reason codes `yolo_program_unparsed_inside`, `yolo_program_destructive`, `yolo_program_outside`), the gate's `_decide_by_mode` denies a `refused` outcome, rules in `program_rules` `gate_approval`. A plain launch at desk YOLO and Programs at Normal and Secure keep the hold. (2) A parked Program asks nothing of him: `your_turn` is empty while parked (status line "Parked · …", no waits), Park revokes its open briefing pages; Resume raises again what is still held. Fence: `tests/integration/test_program_execution_perfection.py` (the YOLO 3-step run's first call is an unparsed pipe through the real classifier and policy) and `tests/unit/test_program_control_level.py` (the real hook and GateService).

**Before it:** 2026-10-31. Programs PG-WINDOW build (direction A, the line and the note; design #1685): the hub adds `brief` (goal, step, what happened, question, what waits on it, each choice's consequence) to each `your_turn_items` row and `story` (at most three plain lines) to each step, from `brief_words.py`; the Program window draws the program's station track at the top, the held item as the headline with the choice tray (no tinted box), the open step under its row with What it must prove (requirement lines, Add a requirement at the step) and What the agent did, Done when as the last row, and the shape bar as the composer at the foot; the step rows lost the six dots; `check:` never names a flag. Fixtures re-recorded. New sweep case `program-held`. Fixtures re-recorded on top of #1686 and #1687. Open work: the owner's live verdict.

**Before it:** 2026-10-31. Programs PG-NIGHT (LANG8, LANG12 in part, JRN2 hub), #1687: a step over its budget's working share is not handed ("Ready · Too big for qwen · 41k of 32k"); YOLO has the planner split it into 2 to 4 parts (Decided for you, Overturn), Secure and Normal get the split as a `step_change` proposal (Apply splits, Skip runs it as it is), no planner is a core question (`holdspeak/services/program_split.py`). A Program with `night` hands steps only in its window ("sleeps until 23:30", `at most`), plans each item added to tonight into one tiny step inside `within` at the window's start, and after it writes one "Since last night" line on top of the note and through Reach's Telegram rung (`holdspeak/services/program_night.py`). `program.add_to_night` + `POST /api/programs/tonight` (319 tools). Planner replies are real qwen3.8-27b recordings (`tests/fixtures/program_night_reply.json`). Open: the Dreaming template, the backlog read by rule, the two-red stop, `within` on the diff, the Program's `planner` line, JRN2's faces, JRN3, JRN4 (the phone message).

**Before it:** 2026-10-31. Programs execution perfection (lane PG-EXEC; the owner's three engine failures in thirteen minutes on program-ed167ae4478b "README touch" at YOLO). (1) YOLO held the agent's commit for him: its message used `$(printf ...)`, the gate read it `unparsed`, and the runner released only `inside`; now a held commit at YOLO in the step's own worktree is allowed by rule ("Allowed the commit by rule (YOLO)"), one aimed outside it is refused by rule, and the commit row exists only at Secure and Normal. (2) Resume of a parked step surfaced `worktree_duplicate`: Resume always went back to Ready and re-handed; now a step with a green check on its commit goes on from its check in the same worktree, and any re-hand stops the earlier launch and continues in the step's own worktree. (3) Start now refuses, in words, a folder that is not git, a repository with no `origin` when a step opens a PR, and a check whose program is not there; a push or PR failure at run time writes its ledger line and his row in words ("Could not push its branch: this repository has no remote; parked"), git's stderr kept in the checkpoint's `undo.detail` and the parked reason. (4) A skipped step is never counted done: the wire has `skipped`, the status line says "1 skipped"; `check: -c` for `sh -c '…'` now reads `check: echo`. Fence: `tests/integration/test_program_execution_perfection.py` (3 steps at YOLO, a bare remote, every commit held `unparsed`, Done with zero Your turn items and zero owner presses). Open work: at YOLO the gate still holds a non-commit call it reads `unparsed` (step 2's `env | grep …` expired with no decision); a local-only delivery for Programs does not exist (merge: none per step is the way); the owner's live verdict.

**Before it:** 2026-10-31. Programs PG-WINDOW design (owner: the Program window must be one object; "UX will be key. If it means canvas? It means that."): canvas `docs/internal/betterment/programs/canvases/program-window-2026-10-31.html` (three directions at 1440 and 393 on one mid-run state) and `docs/internal/betterment/programs/PROGRAM-WINDOW-2026-10-31.md`. Chosen: A, the line and the note (the station track at the top, the held item as the chief-of-staff brief with the choice tray, requirements and the agent's story inside the open step, the composer at the foot). Open work: the build (W1 to W5) follows at once; the owner's live verdict.

**Before it:** 2026-10-30. Continuous terminals (lane TERMINAL-LIVE): native Terminals receives actual local tmux output through an authenticated NDJSON stream, with bounded replay, explicit resync, immutable target checks and cancellable cleanup. The focused Type view measures its well; a typed `process.resize@1` command verifies the host size before xterm adopts it. Refusal preserves actual geometry; split layouts keep their size. Input and resize share target sequencing. Closing a view or hub output service leaves the shell and pane pipe alive. Required quick check GREEN: build; 3,863 UI tests in 329 files; 192 web guards; 5,264 affected Python tests; 129 Desk sweeps; 27 canon guards; 1,194 repository guards. Final private-tmux producer recheck: six passed. Measured xterm/receipt/tmux/stty sizes match at desktop and phone; read-only panes retain 100×30. TypeScript, new terminal Python lint and changed-doc navigation pass. Record: `docs/internal/betterment/terminal-workspace/TERMINAL-LIVE.md`; logs `.tmp/terminal-live/quick-merge/`; shots `.tmp/evidence-shots/terminal-live/`. Engine none. Open verification debt: explicit opt-in for the legacy live-LAN summary test (deselected here; stub kept), a background Thread fixture warning about `deployment_revisions`, and unchanged web-server E731. Local single-pane scope only; deployment, postmerge tape, providers/devices and owner appearance acceptance remain unverified.

**Before it:** 2026-10-31. Programs and Direction, 17 PRs in one day: #1664 PG-REQ design, #1665 PG-REQ build (requirements, browse, adjust), #1666 PG-LANG design, #1667 PG-JOURNEYS design, #1668 LANG1 the Program text (parse, print, diff, `program.text`, `program.text_apply`), #1669 PG-DIRECTION design, #1670 LANG2 the Text view and the change well, #1671 the fields the text could not write (SCHEMA_VERSION 89: review depth, planner, budget, night, within, delivery, rounds, measure, walk, step remove), #1672 the owner approved every default, #1673 LANG3/LANG4 shaping by a typed sentence, #1674 DIR1 to DIR3 the briefing page over the tailnet, #1675 LANG5 shaping by voice and on a call, #1676 LANG6/LANG7 the planning draft and sizing, #1677 a held commit never strands a step (Allow the commit / Not now), #1678 DIR4 to DIR6 Later and the ladder, Telegram, Settings ▸ Reach (schema 91), #1679 DIR8 the call that decides, #1680 LANG9/LANG10 the interview rounds; then this docs PR (LANG15 and the Direction docs: `docs/programs.md`, new `docs/reach.md`, the skill, RECIPE, TRACKER, UX-CANON). The hub was redeployed by hand: no main watcher ran. Open work: LANG8 (the dispatcher's size refusal and split), LANG11 (the Measure verifier: a Measure is "Not measured yet"), LANG12, LANG13, LANG14, DIR7 (the composed digest; today a plain list), DIR9 (the page half), DIR10, JRN1 to JRN6 and JRN8 to JRN14. Needs the owner: a Telegram bot token in Settings ▸ Reach for the first real pairing (untested against a real bot); his word on the Program's Allow the commit row versus the desk's own cut-off rule for a held commit; his live verdict on the new faces.

**Before it:** 2026-10-31. Programs PG-REQ, requirements, browse and adjust (owner: programs "are not that clear to browse, adjust … how to add additional requirements/checks, see how they are met"). The design #1664 merged (`docs/internal/betterment/programs/PROGRAMS-REQUIREMENTS-2026-10-31.md`, canvas direction A). The build PR from `lane/programs-requirements-build-20261031`, three lanes: HUB (REQ1–REQ8: one table `program_requirements`, SCHEMA_VERSION 88; four kinds Check, Review, Shot, Your word, judged on the step's commit; Your word holds the merge at every level; the end check on the base branch; "What must be true" in the brief; template defaults; change, move, insert before and amend a step by the frozen table; `program.require`, `program.step_update`, `program.amend`, 310 tools), FACES (REQ9–REQ12: Find and filter, the Requirements board, the step fold, the shot pullout), DOCS (REQ13: `docs/programs.md` Requirements, Find and filter, Change a running program; the skill; RECIPE "PG-REQ"; TRACKER; UX-CANON). Open work: the end check's Review needs a reviewer launch over the base diff (until then it is his word); an agent's edit of one of his requirements is refused (it proposes a new one); the faces' live verdict on his desk.

**Before it:** 2026-10-30. Workspace flow (lane WORKSPACE-FLOW): the selected brief, Project and agent state lead Sessions, with a clear terminal/agent action and shared selected-row treatment. Project resources use existing Ask/Hand controls; a file prepares a reviewed source snapshot with exact repository/worktree/path and paired read revision. Cancel returns to the same inspected file. Task drafts and acknowledged Notes survive refusal/reopen; Project, keyboard and late-response guards retain the right destination and newer words. One scrolling form keeps phone actions reachable. Required quick check GREEN: build; 1,667 related UI tests in 110 files; 192 web guards; four real private-shell browser cases; 129 Desk sweeps; 27 canon guards; 1,194 repository guards. Final TypeScript, lint and changed documentation navigation pass. Desktop, phone and narrow desktop captures were inspected. Logs: `.tmp/workspace-flow/quick-ship3/`; shots: `.tmp/evidence-shots/connected-workspace/`. Engine mode none; agent refusal is recorded and intercepted, while Note creation and Project filing use the real isolated hub. Record: `docs/internal/betterment/terminal-workspace/WORKSPACE-FLOW.md`. Existing snapshot/PTY/remote/restart/GitHub limits remain. File context does not override the Project repository resolver or resume the selected shell. Deployment, postmerge tape, provider/device proof and owner appearance acceptance remain unverified.

**Before it:** 2026-10-30. Connected workspace (lane CONNECTED-WORKSPACE): Terminals joins Project/brief, exact launch and MCP configuration, independent terminals, worktree files, staged changes, Project resources and Program/agent doors. Existing local shells can register a Git top folder and file its source in a Project from Context. File edits keep text and original hash across reload; a real conflict supports Read latest and explicit Save reviewed edit. Stage/Commit refusals retain input and retry the correct operation. Queued starts join through the acknowledged Note/Project; late replies cannot close a newer start form or take focus. Source/worktree scope, NUL-safe Git paths, fresh registry reads and refusal-before-registration persistence are covered. README has a new actual capture; user guides and generated API references match implementation. Required quick check GREEN: build; 4,889 related web tests; 192 web guards; 2,321 affected Python tests (two intentional skips), including four real private-shell browser cases; 128 Desk sweeps; 27 canon guards; 1,185 repository guards. TypeScript, Python lint and changed documentation navigation pass. Shots: `.tmp/evidence-shots/connected-workspace/`; record: `docs/internal/betterment/terminal-workspace/CONNECTED-RESULT.md`. Engine mode none: launch/MCP/Program browser metadata is seeded; no provider/device run is claimed. Open: bounded snapshot transport, host PTY resize, SSH/remote output, reboot restoration and a two-way GitHub Issues board. Deployment, postmerge full tape and owner appearance acceptance are not claimed.

**Before it:** 2026-10-30. Terminals UI correction (lane TERMINAL-FLOW), following the owner's rejection of #1652's experience. Terminal output joins the shared Toolbar and StatusBar without a page inset. Type focuses at the press; grant replies do not move focus. Message is optional, retains drafts and returns focus on close. Inventory uses kit list rows, shows each folder once, folds secondary actions and keeps one creation form open. Shell name/folder drafts survive form changes. Acknowledged input requests a coalesced screen read instead of waiting for the periodic poll. Error words distinguish connection, view-only and send states. Required quick check GREEN: build; 4,752 related web tests; 192 web guards; 2 real-shell browser cases; 128 Desk sweep cases; 27 canon checks; 1,185 repository guards. Real private-shell browser walk: 2 passed at 1440 and 393, with narrow desktop resize, delayed grant/focus, actual Message output, compact hit ownership, independent input, reload and close-without-kill. TypeScript, Ruff and changed documentation navigation passed. Shots: `.tmp/evidence-shots/terminal-flow/`; record: `docs/internal/betterment/terminal-workspace/FLOW-CORRECTION.md`. Open: bounded snapshots, host PTY resize and full folder inspection beyond hover. Deployment, postmerge tape and owner appearance acceptance are not claimed.

**Before it:** 2026-10-30. Native Terminals, PR #1652 (lane TERMINALS): an independent HoldSpeak implementation inspired by nodeterm's parallel-terminal workflow. Go > Work > Terminals replaces the cramped pane picker with a searchable local tmux inventory and independent Desk windows. New shell accepts a local folder; the existing Start an agent flow is available. Each window owns input/output, grant and retained draft; the existing compositor owns tiling and persisted placement. Closing a view leaves the process alive; terminal-only reload restores it. Rich process fingerprints guard window identity and typing grants across pane-number reuse. Shared PaneWell gains quiet/Find headers, stable input and readable dark-screen text. Required quick check GREEN: build; 4,744 related web tests; 192 web guards; 863 affected Python tests (one intentional skip); 128 Desk sweep cases; 27 canon checks; 1,185 repository guards. The real-shell walk proves independent input, folder selection, narrow native resize, menu/focus, reload and close-without-kill. Public navigation passes across 74 documents. Runtime shots inspected at 1440 and 393. Record: `docs/internal/betterment/terminal-workspace/RESULT.md`; guide: `docs/TERMINALS.md`. Open work: bounded recent-screen polling; host PTY resize, remote output transport and machine-reboot process restoration are not implemented. Hook labels remain correlated metadata. Existing token/architecture baseline debt is recorded, with no new allowlist. Deployment, postmerge full tape and owner appearance acceptance are not claimed.

**Before it:** 2026-10-30. Development-instructions committee, PR #1635. Three independent UI, verification and backend reviewers assembled the root `AGENTS.md` plus scoped `web/AGENTS.md` and `holdspeak/AGENTS.md`; CLAUDE.md links them for both brains. Current UI patterns, recovery, tokens, container reflow, keyboard/touch/voice, isolated verification, composed hub services, authority and persistence are explicit. Conflicting historical premerge gates were removed from the active entry point; existing roles and owner rulings remain. All committee conditions applied. Quick check GREEN: build, 126 Desk sweep cases, 27 canon checks, 1,185 repository guards. Local instruction links and 73 public documents pass navigation checks; Settings shots inspected at 1440 and 393. Product source is unchanged. Record: `docs/internal/checks/agents-development-2026-10-30/README.md`. Open work: existing product debt below; postmerge tape/deployment/review and live owner acceptance are not claimed.

**Before it:** 2026-10-30. Phone push host (this PR, lane PHONE-APNS-HOST): Settings ▸ Calls ▸ Phone ▸ Push gets **Builds from: App Store · Xcode** (`host` `app_store` | `development`, stored beside the key parts in the keystore; `ApnsPush` sends to `api.push.apple.com` or Apple's development host `api.sandbox.push.apple.com`); the Test push's stale answer adds "If this is an Xcode build, pick Xcode under Builds from"; `docs/phone.md` one paragraph. The Record lamp reads "Recording on another view" in sentence case (the lamp species' mono caps lifted for it). Open work: Programs PG14, PG15, PG16, PG20, PG21; Phone PH11, PH15; the Line LINE-5 and the LICENCE slice (awaiting his ruling).

**Before it (2026-10-29):** Phone PH12 and PH14 (#1619, lane PHONE-NEXT): the heartbeat (a Needs you row about security or data loss), a recorded meeting's aftercare asks and an agent question the desk could not draft now reach his phone through `PhoneService.reach` (the rules by level and quiet hours; a `phone.reach` kernel operation each; once per thing; nothing when no phone is paired and no number is set); the phone's runner releases the messages held in quiet hours when they end, one push each, "Held overnight: …". Tests: 12 new hub cases in `tests/integration/test_phone_flow.py`. Open work: Phone PH11, PH13, PH15, PH16; the Line LINE-5, LINE-6, the LICENCE slice.

**Before it (2026-10-29):** Extended documentation accuracy, PR #1614. Source-audited 71 top-level guides plus README and CONTRIBUTING; corrected 43 public documents. Fixed actual control/command, SDK, retention, and availability claims; two documentation generators now select their own checkout, with two regression cases. Focused contracts: 129 passed; final tooling checks: 21 passed. Required quick check GREEN: build, 104 affected tests, 124 Desk sweep cases, 27 canon checks, 1,156 repository guards. No product behavior/default changed. Audit and limits: `docs/internal/checks/core-docs-accuracy-2026-10-29/result.md`. Open work: wire or retire the stored actuator config flags (not enforced by Desk/Mission Control), the Firefox credential path, stale helper/page-set comments, physical/live validation, and the existing remote CSS token gate. An initial bare-Desk stillness failure passed on the full repeat without changing tests.

**Before it (2026-10-29):** README three-judge panel, PR #1613, owner-requested merge with `gh`. Applied independent product, editorial, and visual findings: explicit context-to-agent loop, Quick start near the opening, 31% less text, consistent image presentation, seven screenshots retained. Panel means after revision: modernity 8.7/10, concision 7.7, attractiveness 8.0, potential 8.7. Reports and decisions: `docs/internal/checks/readme-panel-2026-10-29/`. Required quick check GREEN: build, 60 affected tests, 124 Desk sweep cases, 27 canon checks, 1,156 repository guards; isolated HOME and machine lock. Corrected prior documentation vocabulary regressions and removed one fixed debt entry. Product source and test assertions are unchanged. Open work: the existing remote web-quality CSS token gate (184 raw values in unchanged product files); live owner aesthetic acceptance is not claimed.

**Before it (2026-10-29):** Core documentation refresh, PR #1612. The owner requested merge with `gh`. The README presents the agentic web Desk with seven screenshots and simpler flows; 64 public Markdown files were updated. Local checks: 130 focused checks for the core refresh, then 88 for the final README revision; navigation across 73 public documents; README preview inspected at 1440 and 393. Product code is unchanged. At head `75976ff4e`, CI Documentation Navigation passed; DeskOS Web Quality failed, and unit, integration, and scoped browser jobs were still running. Open work: classify that CI failure and complete post-merge review. No live product flow, full tape, or pre-merge quick check is claimed.

**Before it (2026-10-28):** 2026-10-28 — PROGRAMS, the orchestration engine (owner: "one, holistic PR … a proper, well built-out, well specified, and well delightful software orchestration engine that runs on top of HoldSpeak"): one PR from `lane/programs-20261028`, three lanes (PG-HUB engine merged into the program branch; PG-FACES the two windows and the seams, merged into the program branch `bad00fb76`; PG-DOCS). Merged on main before it: the hub-stalling refactor program #1584, #1585, then off the loop parts 1–9 #1586–#1594, #1595 Needs you rebuilt only on Retry, #1597 one desk write reads only what it changed, #1598 the loop guard's allowlist is empty.

**Before it (2026-10-27):** 2026-10-27 23:30 — THE WINDOW PROGRAM (WINDOW-PROGRAM-2026-10-27.md #1504; 'go with suggestions'). MERGED SINCE 17:50: the atlas pass 2 #1533 (every window re-shot and rescored; README hero shots regenerated); wave 3 ZONE #1534; DELIGHT #1535 + #1540 (canvas delight-2026-10-27.html: kind hues, lamps that pulse, task ticks, first-paint fade, Done settle, empty states with objects, Today by the hour, counts tick, depth tokens, small joys); the agent window #1537 (canvas agent-window-2026-10-27.html, A the step log); the Note steps 4–6 #1529; Ask's hub gaps #1530 (streaming, references with facts, claims kept, slow asks recovered) + W4-ASK #1538; wave 4 PHONE #1539, WORDS #1541; the first-use fence #1532; the Context word #1536. Hub on 13c98b789; the hub is also on the tailnet (Tailscale Serve, https://karols-macbook-pro.tailad9943.ts.net, tailnet only). LIVE BUG found and worked around tonight: an unreachable engine's connect timeout hangs the hub's reads (the desk shows Loading forever) — lane HUB TIMEOUTS running (connect timeouts, no synchronous probes on read routes, the Loading face times out honestly). RUNNING: AGENT 2 (slice 2, the done/Idle truth, the Agents window split), HUB TIMEOUTS, the whole browser suite on main. OPEN CALLS for the owner: the Note's title from its first line (clashes with Q8); the token drift --desk-snap-bottom 84 vs 60; moving the engine groups back to the LAN/Tailscale engine when home. Honest progress: ~70 % (every window on the grammar, delight slices 1–2 shipped, docs images current; left: the owner's live verdict, the agent/Live third slices, the remaining joys).)

## Current phase

**The Line — 2026-10-29 (owner: "I'm choosing the second").** HoldSpeak's
own phone line for Calls: baresip 4.12 (BSD-3) as a supervised child, our
`aupipe` module, Parakeet in and Pocket TTS out, the hub driving it over a
text-only wire. Design `docs/internal/betterment/line/LINE-DESIGN-2026-10-29.md`
(with "Built") #1606, canvas #1607 (direction A), the node #1608, the faces and
docs in the LINE-4b PR (Settings ▸ Calls ▸ Line, the Calls window's Line words,
`docs/calls.md` "The Line", `NOTICE`), recipe `line/RECIPE.md`. His hub today:
Not running; the Line needs its own Python 3.13 venv (onnxruntime has no cp314
wheel). Merged since: LINE-3 the home box #1610, Install the Line on karol
#1615, LINE-3b Telnyx #1617, LINE-6 the Engines speech rows #1622. Left (open work):
LINE-5 barge-in measured, the LICENCE slice (Kokoro and faster-whisper's PyAV
pull GPL into the hub; awaiting his ruling); his word on the SIP password custody
(CONFIG); his live verdict on the faces.

**Phone — 2026-10-28 (owner: "Do it. And definitely swallow the paradigm and
'vendor' it… we literally absorb and rewrite and refactor it into HoldSpeak").**
agentring (Apache-2.0, 10b0e55) absorbed and rewritten on the hub: one PR from
`lane/phone-20261028`, three lanes (PH-HUB merged into the program branch
`a65f523e4`; PH-FACES; PH-DOCS). Design
`docs/internal/betterment/phone/PHONE-DESIGN-2026-10-28.md` (with "Built"),
recipe `phone/RECIPE.md` (PH1–PH16; PH1–PH10 in this PR), absorption
`phone/ABSORBED-FROM-AGENTRING.md`, the agentring notice in `NOTICE`, user doc
`docs/phone.md`, skill `agent/skills/holdspeak-phone/SKILL.md`. The hub is the
relay (`holdspeak/phone/`): the event log with `seq` and replay, messages with
replies, the call state machine, pairing by QR with a device token, signed
pushes (NullPush until his Apple key), the number transport through Calls with
answer-later, `phone_rules.reach` by control level with quiet hours, the kernel
op `phone.reach`, 15 routes, 4 `phone.*` MCP tools (305 in 52 families;
`phone.call` EGRESS, not offered to launches), Needs you rows, `may_call` on
Programs (on in Overnight), `HOLDSPEAK_PHONE=off`. Shipped since (lane
PHONE-NEXT): PH12 the heartbeat / aftercare / agent-question reaches and PH14
the morning release #1619, PH13 APNs over HTTP/2 #1622, PH16 and PH17 his
Apple push key in Settings and "Reached you" on Today #1623, the push host
(Builds from: App Store · Xcode, this PR). Left (open work): PH11 SMS, PH15
urgent through Do Not Disturb; the
iPhone app is the Program `program-29a6d2ef5d55` in Drafting (his Start); his
Telnyx line for calls on the number; his live verdict on the faces.

**Programs — 2026-10-28.** Design
`docs/internal/betterment/programs/PROGRAMS-DESIGN-2026-10-28.md` (with its
"Built, 2026-10-28" section), recipe `programs/RECIPE.md` (PG1–PG18; PG1–PG11
in this PR), canvas direction C "the ledger" (`programs/CANVAS-NOTES-2026-10-28.md`),
user doc `docs/programs.md`, skill `agent/skills/holdspeak-programs/SKILL.md`.
A Program is a goal cut into steps; each step is one agent (Claude Code, Codex,
or pi on any engine, when idle) in one worktree; a verified check log, a
review, a PR and a merge by the control level (Secure · Normal · YOLO); only
core questions reach him; Decided for you with Overturn; a handover note on
the desk. 12 `program.*` MCP tools (301 tools in 51 families), 15 routes, the
`program_changed` frame, `HOLDSPEAK_PROGRAMS=off` for rig hubs. Left (open
work): PG14 Automations, PG15 Calls, PG16 decisions, PG20 hidden-ref
checkpoints, PG21 the verified provider matrix in Engines; his live verdict on
the two windows. PG13 and PG13b (the Program's level drives the answers, the
gate and the launch flags) shipped #1620, #1621. Shipped 2026-10-29 (lane
PROGRAMS-NEXT): PG12 a coder frame ticks its Program (1 s debounce, one tick
at a time per Program), the race fixture and shot (`program.race.json`),
PG18 the Programs line on Today at any hour (`/api/today/since-morning`
`programs` block).

**Calls — 2026-10-28 (owner: "place calls and use them to integrate with a
specific HoldSpeak instance… push things forward, prepare things, send things";
then "deliver on it fully… a note on my holdspeak desktop that explains which
service I am supposed to sign up to and how to book it up in settings").**
Design `docs/internal/betterment/calls/CALLS-DESIGN-2026-10-28.md` + canvas
(#1549): HoldSpeak does not build telephony; it drives the owner's own
oxnw/ai-phone install (Apple Silicon only, so beside the hub on the Mac) in
relay mode as a separate process; the home box over Tailscale is the agent's
mind (ai-phone's brain too). The hub slice: `holdspeak/calls/` (adapter, the
call runner on the `calls.turn` capability with the Ask palette + channel.send
+ nudge.send held for his spoken yes behind allowed numbers + a passphrase,
read back from the turn's record, transcript saved as a Note), the five
`calls.*` settings keys, six REST routes, the `call_state` frame, four MCP
tools, `docs/calls.md`; proofs run the fake ai-phone as a real subprocess with a
recorded home-engine reply. The faces: the Calls window (Go ▸ Work ▸ Calls),
Settings ▸ Calls (the install checklist with the exact commands; Telnyx
recommended for a real number), the phone Calls row. Left: the owner installs
ai-phone and presses the line; a handset icon; recorded fixtures for the faces;
channel 0 (the phone web app's call screen); HoldSpeak calling others.

Merged after it the same night: #1551 the Calls faces, #1552 two midnight test
reds (stale setups), #1553 + #1555 the Door's now and overdue columns name the
day and another person's item waits on them (the Monday brief lists every
waited-on item), #1554 Settings expects Calls and the phone Go fits 393
(Archive under Drawers ▸), #1556 delight slice 4 (the Calls telephone icon, the
live lamp species, the Yes/No settle, the Record breath, Activity empties),
#1557 Live slice 3 (the microphone check before Start, the transcript_pass
frame, level + saved mark), #1558 agent window slice 3 (Done closes a launch,
checked state, the step fold, honest test colours). Whole browser suite on
main c0df24678: 419 passed. In flight: delight slice 5 (the depth scale, Today
in the evening).
Then the same day: #1560 delight slice 5 (every popover on the depth scale; a
real CSS bug: a shadow list that begins with a token whose value is none draws
nothing; Today's "Since this morning" after 17:00), #1561 atlas pass 3 (every
window re-shot and rescored; 26 defects in the owner's words), #1562 the
void-shadow guard, WAVE 6 from the atlas (#1563 People/Needs you/Calendar/
Archive, #1564 Settings saved lamp + Calls pane words, #1565 palette and Ask
references, #1566 Decision object and reader + Project drawer + Room Ask box,
#1567 Processes/Mode/Activity/agent band, #1569 recipe.run follows Answers +
Cadence words + Speak focus ring, #1570 every write-failure band in plain
words, #1571 Saved per Settings window + two test pins), #1568 the wave 7
canvas and #1572 its build (Mission control captions on a slate veil, the
Record ring and clock, Context's pad). Whole browser suite on main after each
batch: green modulo the Engines stillness flake. Open owner calls: the Note's
first-line title; moving engine groups back from Codex when he is home.
Evening: #1574 the last failure surfaces and the whole Rhythm face in plain
words, #1575 mono text keeps its line through the webfont swap (the recurring
Engines stillness red, fixed at its cause: a metric-twin fallback font + a
guard), #1576 / #1578 / #1580 the remaining plainFailure callers, REFUSED
receipts and success receipts in one case, #1577 feedback capture skips hidden
subtrees (the recurring Firefox lifecycle red, fixed at its cause), #1579 four
unit guards that were never in quick_check fixed at cause and added to it, plus
the Remote access test case made fast. Whole browser suite on main 7981babc8:
419 passed, 0 failed (the first fully green run with no flake). Left in the
words wave: Runs on's success receipts and ~150 state-token vocabularies in
caps.

**The window grammar — 2026-10-24 (owner: "still look like pages inside OS-like
containers"; "make it look nice and attractive, not boring"; then "that tilt…
absolute cringe" → icon direction D picked: "Yes, I like D").** Design and
diagnosis: `docs/internal/betterment/native-experience/WINDOW-GRAMMAR-2026-10-24.md`;
icons: `docs/internal/betterment/ICONS-D-2026-10-24.md`. Merged the same day:
#1457 Note/Room, #1458 Settings rail/grid/status bar, #1459 kit Toolbar/StatusBar/
dense ObjectList + chrome + Meetings/Projects + Components Window group, #1460
Automations/automation window/Agents, #1461 People/person/Decisions, #1462
convergence onto the kit species, #1463 three browser reds (Ask return raise,
Room re-read hold-still), #1464 kit polish (avatar rows, fold join, narrow status
bar, idle tone, DotWord, Room foot), #1465 Activity/meeting window/Needs you +
scoped Settings Back, #1466 desk chrome (floor labels, badges, menu bar, Talk,
dock), #1467 toolbar wrap, #1468 the D icon family (47 sources, 20 px export,
title chip, zone colours), #1469 Setup/New Project/Processes/Needs-you rows +
the Engines and Speak bands, #1470 Ask/Today, #1471 Today's Needs-you rows are
the Needs-you window's rows; this PR: Engines as a list view (glyph, Engine,
Where, Used for, State) with What-runs-where as a label/control grid and a
status bar carrying the selected engine's verbs and egress; Speak's status-bar
readout (Not ready / Ready · engine, ticking time), the level meter in the bar,
a quiet Copy verb (`copy` glyph); Voice commands toolbar; Components Window ▸
List + inspector. Every window in the manifest now follows the grammar.
#1473 Room folds duplicate Watch rows (two Jira Watches read the same issues:
26 rows for 13); #1474 New Decision opens its own window and Create opens
the record in the Decisions window on the grammar (owner 2026-10-25: "opens up
a cluster… of a window"); #1476 the dock: one 84 px tile width (owner: "random
inconsistencies between those icons"), the live tag in the word's row, lamps on
the icon; #1477 every decision record opens in the Decisions window reader
(Room This-week click, Room drawer, Prepare citation, WHY with one record) and
Today ▸ Decisions opens the Decisions window instead of swapping Today's content. #1479 the Needs-you dense row: the name gives, the meta keeps its
width (a Jira row's Project wrapped one letter per line, 350 px tall); the
Open link row's host chip removed. OWNER RULING 2026-10-25 evening: the
ever-present egress labels (LAN, 192.168.1.36, the Jira host chip) "feel like
an ancient relic now" → no host / address / scope chip on rows, toolbars or
status bars of working windows; egress disclosed at the choice or the act
(Settings ▸ Engines, Send preview, Setup). MERGED #1481: 26 site groups in 34 files
lose their chips (Today, Needs you, Room, Meetings, Ask, Speak, Agents, drawers,
Activity, Automations; engines by name, hosts as hover titles, Activity's Who =
You / Another device); kept at the act (Send preview, Destinations, Settings ▸
Engines / What runs where, Hand confirm, Setup, Door); UX-CANON A.9 amended;
inventory docs/internal/betterment/native-experience/EGRESS-LABELS-2026-10-25.md;
guard tests/unit/test_egress_labels_canon.py + a sweep `labels` fence. Left: the
menu-bar trust badge (⌂ This device / → Your network) unchanged; Workbench,
Delivery board/dossier, Rhythm and the tool inspector still wear chips; dead
code kept for its tests (useDraftEgress, saidOnFace, isLanHost). OWNER FEEDBACK
2026-10-25 22:23 (bundle ee299edf, the Room at 935 × 509 with 13 overdue Jira rows):
"this window is a joke… looks this white… looks like shit" → MERGED #1483: the Now
wing is one column (an empty second column is not drawn; two columns only ≥ 1100 px
with a week to show), the Needs-you rows a list view (one line, 32 px, name
ellipsized with its title on hover, verbs right), `whyFaceWords` says the hub's
caps why in sentence case (Overdue · 48 days; the hub's words unchanged). OWNER 2026-10-25
23:00: "YOU'RE BEING so fucking reactive… what about some proactivity" → THE WINDOW AUDIT
(docs/internal/betterment/native-experience/WINDOW-AUDIT-2026-10-25.md, #1485): all 35 sweep
windows shot on a seeded desk at 1440 and judged; seven lanes MERGED the same night and
redeployed one by one: #1486 ⌘K palette + Capture, #1487 Live meeting, #1488 decision
doors (meeting decision without a record, WHY with several records, Review decisions
Current only), #1489 egress left-overs (Workbench, Delivery, Rhythm, tool inspector; dead
code parked), #1490 Speak (title keeps its width via stripMenu, one toolbar, one status bar,
dense wings, Commands wing), #1491 Memory window + Settings ▸ Accounts, #1492 seven small
defects (Processes columns, Check sources, Person band, Prepare… caption, Today Since rows
dot + word, Needs-you status bar, Room facts/Sources fold sentence case, Calendar snapshot +
Context). Left from the audit: the Room's Sources fold still floats Register / Add source /
Raw in a band above its rows and its rows are two lines; Speak's Journal name column does
not flex and its times are mono; PrReceiptsSection still wears a GitHub egress badge; the
"Hold ⌥R anywhere" hint shows only once speech is set up; the Room's failure lines and
people tokens are still caps; ObjectList has no per-row verb slot (Speak wings keep their
own rows). FLAKY under parallel vitest, pass alone every time (fix forward: make them
deterministic): settings.app.test.tsx (Remote access, runtime identity),
settingsLeave.philo17.test.tsx, routeInFooter.test.tsx, ThoughtWorkspaceWindow.test.tsx.
CATCH 2026-10-25: his hub had served main 33fdbce59
since 2026-10-24 (no watcher alive); redeployed from
/Users/karol/dev/tools/wt-desk-main-20261025 (see memory reference_owner_hub_redeploy).
Open fix-forward: a meeting decision with no record yet and WHY with several
governing records still open the Decisions page inside Today; "Review
decisions" lost its Current-only preset; Today's rows still wear mono-caps
tokens (AGENT LAUNCHED, MEETING RECORDED); Engines Remove (DELETE refuses bound engines; unbind rules
first), the Add-an-engine panel and Download fold still wear caps tokens,
Speak's Clean-up chip and the Journal/Blocks/Learned/Configure wings are not
dense lists yet (no seeded rows to prove them), Ask's EngineLine "No engine"
mono caps, Memory/BeliefCard chips. Owner aesthetic acceptance is live on his
desk; nothing is claimed accepted.

**Owner-authorized React desktop execution — Astra / Sol High (2026-10-23).**
The owner authorized execution of P01–P10 against the 47-family map and seven
journeys, superseding this initiative's earlier design-only and reviewer-only
holds. The product definition is #1435. Three first slices are merged and
running: repository windows/read browser + Resources (#1438), Settings You
save recovery + Forms (#1439), captured Thought voice + Editing (#1443).
No package or whole journey is marked complete; owner visual acceptance is open.

The first P04 selected-Thought Ask/save/source-return slice is #1446, with
four real-browser cases at 1440/393 and required quick green: build, 4,269 UI
tests, 110 desk sweep, 27 canon and 1,126 repository guards. It includes independent Ask context, open/closed source return,
stale-range refusal and the same source frame in Components. Root inspected
the final captures; changed-source current caret stays visible and pending
work names Ask. Saved Markdown provenance is editable; at that first slice, active Notes still lacked source/thread doors and
server-side source pinning. Both continued in #1448 below; captured frontend
text alone was not inference source freezing. [Execution](../docs/internal/betterment/native-experience/EXECUTION.md)
keeps actual PRs, scoped proof and remaining package/journey acceptance.

Last verified deployment — #1455: backend
`b00d95eded8eab88d5bac81d5579934c6f769432`, frontend `3e1c98209c61a463`; database ownership true, no identity diagnoses, health/Desk/
Conductor/Engines return 200. CLI/MCP match this source; feedback is enabled
and Presence stays off. Six workflow/component slices and the shared zoom/growth/Stop repairs run on this revision. The Room/list visual continuation is still unmerged; its integration finding is recorded below.
The completed pinned #1443 tape passed all 44 Python batches and its full web
baseline (5,528 passed). Its 11 browser failures are zoom/Room/Thought checks
repaired in #1444/#1445 and the stale Forms specimen cases repaired below.
That pinned full tape is RED; no latest-main full-suite green is claimed. Earlier wire, optional-plugin and doc-probe repairs
are recorded below. Recipe closeout remains 115/117.


Note-version / saved-link continuation — #1448: canonical Thought revision/body hash
now travels with the accepted Ask; changed/gone sources refuse before dispatch,
and admitted text stays with normal/CLI/LOOP turns without losing original
Desk Memory. Active saved Notes gain explicit source/thread Buttons in Linked
items; Clear quote and whole-Note Ask retain origin range/caret. Server and
frontend advisory fixes received final RATIFY. Required quick green: build,
4,286 UI tests, 961 affected checks (six known skips), 110 desk sweep, 27 canon,
1,126 repository guards; changed browser cases cover1440/393 and phone targets.
This is bounded P04/J1/P10, not full P04/J3 or owner aesthetic acceptance.
The separate P01 low-window growth clamp — #1449 — is reviewed and required quick
green: 4,281 UI, nine affected browser, 110 sweep, 27 canon, 1,126 guards.
It moves only y to keep actual expanded height in the work area and preserves
owner sizing/zoom/identity. Synthetic growth, real gestures and normal-motion
Stage/Exposé/initial mount are covered; no ASR claim.

Range fixture static correction — #1450: the merged #1448 handoff fixture omitted
required range.text. A direct typecheck verified TS2345; the fixture is aligned
without product changes. Whole-tree typecheck and required quick pass (nine
editor, 110 sweep, 27 canon, 1,126 guards). Earlier author success was not proof
of final merged type state. Source/return runtime proofs remain separately scoped.

Zoom restore — #1444: content-sized windows retain auto height across first
zoom, restore and reopen; owner-sized windows retain fixed geometry. The bug
was reproduced on pre-P01 main. Required quick green: build, 4,219 related UI
tests, five Chair glass cases, 110 desk sweep, 27 canon, 1,126 repository guards.

Room / Thought glass — #1445: stale Sent history and desktop Send Back
selectors now follow current controls. Manual receipt and real folder bytes/
identity/retry checks remain; clipboard uses a local buffer. No product code
changes. Required quick green: build, 43 affected browser cases, 110 desk sweep,
27 canon and 1,126 repository guards.

Design Reference glass — #1447: old Forms assertions now follow the shared Settings
You writer/fields. Alias, held ACK, refusal/Retry, newer draft and Reset are
observed without production writes; other pattern checks remain. Required
quick green: build, both affected width cases, 110 desk sweep, 27 canon and
1,126 repository guards. No product code changes.

Optional meeting plugin route — #1440: an inherited summary assignment with
no compatible optional plugin now records exclusion instead of refusing core
summary admission before dispatch. Core capability checks remain strict.
The four original reds and two existing optional/core pins pass; required
quick green: build, 113 affected cases, 110 desk sweep, 27 canon and 1,126
repository guards. This is a producer repair, not P05 completion. Wire/Stop
fixture repairs and the remaining full-tape observations stay separate.

Recorded producer wires / Stop assertions — #1441: six recordings are rebuilt
from their isolated rigs; test clocks keep the original Tuesday lanes,
spoken due dates, coverage ordering and Changed facts stable. Stop assertions
now require #1437's stopped status and Meeting identity. Eight focused replay
cases pass on main with #1440, and four frontend consumers pass 85 cases.
Required quick green: build, 123 affected cases, 110 desk sweep, 27 canon and
1,126 repository guards. No product code changed; this is no new P06 job or
full-suite green claim. A later pinned-tape security-doc claim is being
inspected separately.

Security-doc probe — #1442: the claim remains accurate; its probe's expected
reference set now includes the persisted RemoteConfig field as well as the
MCP settings route. No listener/peer behavior or security prose changes.
The exact claim and all 47 registered claims pass; required quick green:
build, 47 affected cases, 110 desk sweep, 27 canon and 1,126 repository guards.
The remaining inherited pinned-tape Chair zoom-height failure is reproduced
on pre-P01 main and is being fixed separately; no full-suite green claim.

Captured Thought voice / Editing reference — #1443: active CodeMirror binds
one editor/range/document generation; stale words stay with their Note through
Desk memory and explicit insertion uses one undo. Components shares the exact
document/binder/recovery with local IO. Final Sol fix re-check RATIFY; six
browser cases pass at 1440/393, including named fake transcript transport
through production MicButton and default retention, two notes, close/reopen,
real Note saves and one Undo. Copy uses isolated browser test IO; no hardware
or ASR-quality claim. Root inspected final shots and fixed clipped/overlapping
recovery controls before acceptance. Required quick green: build, 4,217
related UI tests, six affected cases, 110 desk sweep, 27 canon and 1,126
repository guards. This is partial P03/P10; other input policies, per-Note
audio retry, native Talk and owner visual acceptance remain open. P04's owned
source/selection return is in progress; the deployed runtime is updated after
this merge, with its exact identity recorded at the next delivery update.

The earlier hold below is retained as history; it no longer pauses execution.

**Owner correction — strategy before further implementation (2026-10-23).**
The bounded repair closeout is complete: Ask #1433, Settings #1434,
Capture #1436 and Meeting outcomes #1437. Refine the plan and strategy
before starting further planned product changes. The proposed refinement
and advisory re-check are in draft #1435; it remains UNCHECKED, awaiting
Muad'Dib. The 47 audit records are evidence, not an automatic build queue.
The larger project-update Stop draft is parked at `54a7436b7` outside main;
its last edits and new tests are unverified.


Meeting Stop/save truth — #1437: the route retains runtime stop, Meeting, persistence
and cleanup facts. Recording store and LiveCore share the outcome parser;
confirmed Stop idles even when saving fails, and explicit still-recording
responses stay active/refused. DB-saved partial outcomes retain an Open
Meeting door. Capture recovery is limited to the verified recoverable-row
case, not failed JSON/aftercare. The global Stop receipt now survives the
live-to-record window transition; clean Stop clears only its own verb/subject.
Focused proof: 40 frontend cases, two native Stop response cases and nine
route/integration cases passed. Required quick green: build, 4,187 related
web tests, 40 affected Python/browser cases, 110 desk sweep, 27 canon and
1,126 repository guards. Root inspected narrow Live and desktop stopped-record
captures; broader recovery, hardware, identity/edit and summary jobs stay open.

Capture first words repair — #1436: New Note keeps the attempt's seed and captured
keys through failed creation, Retry, timeout and editable-field handoff.
Successful delayed creation also delivers the snapshot to that Note without
rearming keyboard interception. No new editor or draft store. Focused proof:
34 cases across three files passed. Required quick green: build, 4,169
related web tests, five real-browser key/window cases, 110 desk sweep,
27 canon and 1,126 repository guards; 1440/393 key-handoff captures inspected. Restart/global-receipt durability and broader Capture/voice
workflow conditions remain open.

Settings leave/return repair — #1434: leave supersession is scoped to captured write
identities and confirmed acceptance. Later refused edits remain visible with
Retry; failed leave-only edits and late responses preserve newer local work.
The permanent component regression replaces the parked reproduction as repair
proof: 66 focused cases across five files passed; required quick green with 4,155 related web
tests, seven affected Python/browser cases, 110 desk sweep, 27 canon and
1,126 repository guards. Root inspected 1440/393 Settings captures.
The dirty-debounce receipt and other Settings audit findings remain open.


Native-experience repair wave — #1433, Ask saved-thread selection: the first small
repair gives saved-thread reads their own generation. An older response or
failure cannot replace the selected thread, New Ask or a closed window.
Focused component proof: 46 tests passed, with seven new assertions red on
the unpatched component. Required quick green: build, 143 related Vitest, 110 desktop sweep,
27 canon and 1,126 repository guards. Three focused glass cases passed;
Firefox answer captures were inspected at 1440 and 393. Deployment identity
is checked after merge. Settings, Capture and both Stop findings remain open; this
does not close the audit or claim owner UX acceptance.


Adversarial workflow audits — #1431: all 47 native-experience
family audits have an independent review and root reconciliation in
`docs/internal/betterment/native-experience/adversarial/README.md`.
Audit-sufficiency verdicts: 32 conditional, 15 do-not-ratify; 204 proposed
acceptance challenges. These are not executed workflows or product readiness.
The reconciliation corrects active/retained routes and misleading public-job
associations, preserves the current stack and existing shared behavior, and
orders small repairs before framework extraction and the explorer/Components
proof. Required publication quick: build, 37 focused docs checks, 110 desk-sweep
cases, 27 canon and 1,126 repository guards passed; 53 Markdown navigation
checks and all 47 record/anchor validations passed. No product repair is
included in this packet.

The reproduced Settings return conflict is repaired above; the original
control retained the draft and Retry while the leave/return case lost it.
Ask saved-thread read authority shipped in #1433. Capture first-word retention is repaired in #1436; Meeting stop/save
truth is repaired in #1437. The larger automation Stop candidate is parked on
`fix/update-stop-repair-20261023` at `54a7436b7`, not merged or deployed;
its final edits and new regressions are unverified. The owner clarified that
strategy/design refinement precedes further implementation.
See `adversarial/SYNTHESIS.md` for first consumers, retained boundaries and
owner/capture/AT/performance limits. Presence remains off.

Desktop application-model correction — #1430: the owner
clarified that near-native apps, windows and explorers are the unit of design,
not pages in small containers. Research now defines application/window/resource
identity, lifecycle, independent view selection/history, contextual commands,
editing, view modes and supported cross-window transfer. The explorer-style
resource workflow is a first acceptance workload alongside Settings; no new
file-manager product or unsupported filesystem operation is claimed shipped.
Scope: `docs/internal/betterment/native-experience/APPLICATION-MODEL.md`.
The owner also requires a whole-product use-case audit; existing job,
capability, recipe and surface inventories are reconciled with application
behavior/evidence in `native-experience/USE-CASE-AUDIT.md` and its JSON
snapshot. Source coverage is distinct from live task verification.
The capability probe is hardened for missing optional APIs and its reproduction
command now actually isolates HOME. Required check: build, 40 documentation/harness checks, 110 desk sweep cases, 27 canon and 1,126 repository guards passed; final added audit records pass 40 focused checks and seven Markdown navigation checks; all source-set crosswalks, 145 reference paths and real three-engine probes verified.


Native-experience research within React — #1429: the
owner chose the current stack and asked for substantial research toward a
nearly OS-native experience. Research, source audit, compatibility evidence
and a proposed production-pattern delivery sequence are in
`docs/internal/betterment/native-experience/README.md`.
No UI-stack replacement, package addition or product-code change is included.
The initial packet proposed a Settings preference checkpoint; the owner's
application-model clarification above extends it to explorer/resource behavior
alongside preferences, then Ask and People. These are proposed work packages, not
adoption or aesthetic acceptance. Required checks: build, 37 focused documentation checks, 110 desk sweep cases, 27 canon and 1,126 repository guards passed; nine changed Markdown files have valid local navigation; isolated Chromium/Firefox/WebKit capability probes passed.


Shared surface modernization — #1428: the owner requires the
in-desk design reference, common layout/material adoption, compositor
consistency and documentation reconciliation across active surface families.
Components now offers working local form, reading, list, conversation and
progress patterns, plus the retained controls catalogue. Shared interior
rules reach manifest surfaces, object windows and specialised hosts; bounded
editors, terminals and the Chair retain their task layouts. Frame, Dock and
keyboard front authority use the mounted compositor snapshot.

Scope, adoption and observations:
`docs/internal/betterment/MODERNIZATION-IMPLEMENTATION-2026-10-22.md`.
Required check: build, 4,162 related web cases, 59 affected browser cases including strict Firefox feedback capture and resize/drag checks, 110 desk sweep cases, 27 canon and 1,126 repository guards passed; typecheck passed.
Owner aesthetic acceptance remains open. This does not change the betterment
recipe count or claim every functional/native/provider operation is complete.
The completed main787c55c8 tape is red: 12 Python and nine browser failures;
web baseline and strict Firefox timing pass. The previous main62358 tape was
red: 13 Python and nine browser failures. Root compared failed-test names:
three newly observed 393px Room checks still require an inline History tab
that now folds into a menu; their helper and live menu navigation need a
focused fix-forward. One newly observed scheduled-microphone failure remains
unattributed. Other run-to-run differences do not prove repairs. These facts
are separate from the green required quick and the research recommendations.
Native Presence was closed and its enabled setting saved false at the owner's
request on 2026-10-23. Its rendering fault remains unverified and it must stay
off until repaired and explicitly re-enabled.

Richer desktop icons — #1427: the owner rejected #1426's art as
“toilet bowls” and too basic. All shared object, dock/system and Settings
art now uses angled construction, coloured fronts, layered
paper, metal facets and distinct agent portraits. Names, sizes, real image
states, layout and behaviour remain. The rejected SVGs and PNGs are parked.
PNG bytes now participate in the frontend build identity, so an icon-only
change is distinguishable from the previous loaded build.
Scope/canvas: `docs/internal/betterment/RICHER-ICONS-2026-10-22.md`.
Required quick: build, 6 affected checks including actual Ask and Settings at 1440/393 and the real Vite PNG fingerprint regression, 110 desk sweep cases, 27 canon and 1126 repository guards passed; 15 focused source/asset/registry checks and deterministic export passed; all 142 new PNGs have edge clearance and the parked 47 SVGs plus 142 PNGs match preceding main byte-for-byte. Owner aesthetic acceptance stays open.

The completed preceding main9b43917e7 tape has 12 Python and eight browser
failures, all present on the earlier tape; web baseline and strict Firefox
timing pass. Seventeen browser failures from main937d7ea5c no longer fail.
The remaining inherited functional failures stay open. This art correction
does not claim a whole-suite green or aesthetic acceptance of #1426.

Illustrated icons — #1426: owner chose crisp illustrated icons for
the next shared visual pass. SVG originals replace dense pixel art across
world objects, the dock/system and Settings; optical32 renders keep small
icons legible. Existing PNG/state contracts remain; common sampling is
smooth and desktop dock pictures32px inside the same shelf.
Scope/canvas: `docs/internal/betterment/ILLUSTRATED-ICONS-2026-10-22.md`.
Required quick: build, 4128 related web cases, 54 affected browser cases including strict feedback PNG capture and Chromium/Firefox pressed-hover-focus checks, 110 desk sweep cases, 27 canon and 1126 repository guards passed; 15 focused source/asset/container checks, typecheck, 18 focused prior-tape regressions and two deterministic export/check cycles also passed. Owner visual judgment stays open.

The completed main937d7ea5c tape is red: 12 Python, 25 browser and one
web failure (5,419 web passes). All 12 Python and eight browser failures
match the earlier tape. The new cases expose desktop corner hit ownership,
disabled contrast, clipped menu labels, a misplaced phone media block and
visual readers that still expect the superseded 28px/deep-blue material or
cannot parse CSS4 colours. This delivery fixes those shared rules and updates
the readers to the settled design while retaining their hit, contrast and
clipping floors. The strict feedback capture check also found that the generic
pressed Button rule outranked Send's selected destination. Its specificity is
reduced and its place after hover retained, so an owner can draw its selected
state. The Arrange-all fixture waits for the real project title before it
compares names and order. The original tape result remains in
`wt-main-tape-modern-shell-pressed-20261022/.tmp/delivery/tape/summary.json`.


Pressed-state fix-forward — #1425: post-merge review of #1424
found that hover could override primary/danger pressed fills. Shared pressed
rules now follow hover rules. Real Chromium/Firefox checks cover hover plus
keyboard focus at 1440/393. Required quick: build, 15 related web cases, 8 component browser cases including all four Chromium/Firefox pressed-hover-focus regressions at 1440/393, 110 desk sweep cases, canon and repository guards passed; all four new cases also fail on the prior stylesheet.
The material reader's replacement border/radius coverage is a low-priority
follow-up; existing hit, contrast, clipping and type floors remain strict.


Modern shell — #1424: owner's 2026-10-22 direction “Workbench
meets PopOS.” Shared tokens, frames, menus, controls and dock move to fine
borders, soft depth, pale chrome and clear sans labels; Ask and Settings use
the same material. Pixel identity and window/voice/keyboard behavior remain.
Canvas and scope: `docs/internal/betterment/MODERN-SHELL-2026-10-22.md`.
Required quick: build, 4130 related web cases, actual Ask/gallery/frame browser checks at 1440/393, 110 desk sweep cases, canon and repository guards passed; 56 focused cases, typecheck and token generation passed; standalone raw-token gate remains inherited red 120→102 with zero branch-new findings and unchanged allowlist. Owner visual judgment remains open.

Earlier completed full tape on 448772a89: 12 Python and 10 browser failures;
web baseline and strict Firefox capture timing passed. These inherited reds
remain open; this visual pass does not claim a full-suite green.

Open owner feedback: `24575f6781aeca1391e89669ad78f7c8` reports “Meeting
analysis running” during Ask/agent work. Notification provenance needs a
separate functional fix; original report/audio/screenshot remain read-only.


Conversation fix-forward (#1423): shared end anchoring keeps the
answer actions in view when Tools changes the reading height; shared composer
material owns the editor cascade. /design/components now carries a local
interactive composer specimen under the legacy PR host class. The PR reply
screen is parked; the gallery is a reference, not live PR adoption.
Required quick: build, 4130 related product web cases and seven actual browser cases passed; a local jsdom Send fixture correction passed 10 cases in the final required quick with byte-unchanged product web code; other required checks: 110 desk sweep cases, 27 canon and 1,126 repository guards passed; 56 focused Ask/shared composer/hook/gallery checks and typecheck passed; Firefox at 1440/393 verifies Tools end anchoring, preserved earlier reading, actual gallery editor material and capture/action hit geometry. Owner aesthetic judgment remains open.


Shared conversation design: #1422 develops Ask into a
continuous paper reading/writing surface with a strong intro, bounded readable
turns and an integrated composer. The new presentation-only ComposerWell
library species also serves DeskComposer retained by parked PR reply actions. The /companion route opens Agents; this is not live PR adoption. Host-owned
submission, keyboard, voice scopes, engine/egress and durable drafts stay in
their callers. One mic per editor. Saved Threads already open in Ask; their
parked screen is not revived. Contract and settled canvas:
`docs/internal/betterment/CONVERSATION-DESIGN-2026-10-21.md` and
`web/src/desk/surface/contract.md`. Required quick:
build, 4125 related web cases, real Firefox long-document checks at 1440/393, 110 desk sweep cases, 27 canon and 1,126 repository guards passed after the microphone mapping correction; web code is byte-unchanged from the product check; 50 focused Ask/shared PR composer checks, 71 microphone guard checks and typecheck passed. Live aesthetic judgment remains open.

The prior d1691b773 full main tape completed: 12 Python and 10 browser failures;
web and strict Firefox capture timing passed. The five J9 category setup
failures are resolved. Other inherited failures remain open, with no new full
suite green claimed for the visual work.


The owner's Ask feedback is implemented by #1421: compact
paper composer, an empty-state Ask pictogram and prompt starters, and a
reading area for the conversation. Enter moves a sent question into the
conversation and clears the durable composer immediately. Answer completion,
Stop, Retry and a duplicate Enter retain a newer follow-up draft. Engine and
egress remain beside Ask; tools are available in a fold. Original report
`3c7c52ae3ccfdd5ee7e29ddaadaf10e6` remains read-only. Canvas and scope:
`docs/internal/betterment/ASK-FEEDBACK-2026-10-21.md`.
Required quick: build, 136 related web cases, Ask and J9 real browser checks including Firefox at 1440/393, 110 desk sweep cases, 27 canon and 1,116 repository guards passed; 39 focused Ask cases and typecheck passed. Owner live aesthetic judgment is open.
The prior f9ec7ccd6 full tape finished with 12 Python and 15 browser failures.
Five new graph-walk failures came from setup pressing the now-hidden System
Builder tools toggle. Both J9 setup cases now choose This Mac through the real
category button first; existing smoke predicates remain strict. The Needs
confirmation failure and inherited tape failures remain open.



Post-merge review of #1419 found that a rejected native-agent or spend-limit
save can escape an async UI callback. The focused fix catches that rejection,
retains the spend draft and restores a usable retry. The regression drives a
503 response and then a successful actual writer retry. Required quick:
build, 58 related web cases including a refused-save/draft/retry regression, 110 desk sweep cases at 1440/393, 27 canon and 1,116 repository guards passed.

The owner's 2026-10-21 Automation builder and Settings reports are implemented
in this change. Blank automations open a five-step guided editor using the
existing real settings and engine admission. Settings shows one category at a
time, with pictograms and a paper pane; local category children stay mounted.
The dropdown uses the existing Workbench choice control with a clear closed
face. Both reports and their original files remain read-only. Settled canvas
and scope: `docs/internal/betterment/SETTINGS-BUILDER-FEEDBACK-2026-10-21.md`.
Required quick: build, 4117 related web cases, 18 affected checks, including 13 real browser cases at 1440/393, 110 desk sweep cases with feedback enabled, 27 canon and 1,116 repository guards passed; typecheck passed; six separately timed Firefox captures passed unchanged 3-second/1-second budgets. The owner judges the appearance
on the delivered desk; this is not acceptance of the whole OS's design.

The owner's Agent and New Automation feedback is now implemented in the
reported faces: the Agent has its real portrait, readable report, visible tool
activity, real screen-report fallback and Refresh, with existing answer,
Direct, terminal and receipts preserved. New Automation uses shared choice-card
material, 32px pictograms and compact facts, with Start from scratch first
and narrow-container reflow. The creation path still saves one automation per
press. Canvas and scope: `docs/internal/beauty-delight/REPORTED-FACES.md` and
`reported-faces.html`. Required quick: build, 4112 related web cases, 10 affected browser cases, 110 desk sweep cases with feedback enabled, 27 canon and 1,116 repository guards passed; typecheck, 61 focused web cases and nine focused browser cases also passed; real saved images inspected at 1440 and 393. The owner judges
the delivered appearance live; this implements these two reports without
claiming a completed redesign of every Desk face.

Firefox Settings feedback capture now freezes resolved styles once, preserves
pseudo-elements and SVGs, and avoids copying inherited theme tokens onto every
node. The same loaded 1,303-element window went from about 15.2 seconds with
7.3-second interface stalls to 1.1–1.4 seconds with a maximum 404 ms pause.
Capture cancellation reaches pending image/font work and removes temporary DOM.
A pinned screenshot-library font accessor is corrected for Firefox. Six real
Firefox reports saved at 1440/393, including interrupted-save Retry with the
same bytes, original audio, screenshot and values. The owner's two completed
reports are intact; the third attempt did not reach disk. Required quick:
build, 37 related web cases, 22 affected Firefox/Chromium/Send browser cases, 110 desk sweep cases with feedback enabled, 27 canon and 1,116 repository guards passed; saved window images inspected at 1440 and 393. Diagnosis and measured evidence locations:
`docs/internal/ui-feedback/FIREFOX-CAPTURE.md`. This fixes feedback capture;
the Agent and New Automation design reports were addressed in #1418; the new
2026-10-21 builder and Settings reports are the current follow-up.

The owner’s audio report of the Adr Drafter window starts the beauty and
delight reference in `docs/internal/beauty-delight/`. Shared Send uses
readable full-width destination rows with the selected preview directly
below; the artifact reader presents useful material on paper and moves
source details into a fold. Known no-decisions ADR results read honestly
without an outgoing Send area; original Copy/Send document bytes stay intact.
This first reference improves these shared surfaces; it is not a completed
redesign of every Desk face.

Feedback saves its original audio, image and context before transcription,
then uses the same configured, admitted speech engine as Speak. It attaches
`transcript.txt` to the report. A speech failure keeps Saved, Copy path and
New feedback available and offers Retry transcription against the same WAV.
The raw transcript bypasses dictation punctuation, clipboard substitution
and command processing. Required quick: build, 23 destination web cases, 37 affected speech/browser cases, 110 desk sweep cases with feedback enabled, 27 canon and 1,116 repository guards passed; final reference images inspected at 1440 and 393.


The owner can opt into audio feedback with `HOLDSPEAK_UI_FEEDBACK=1`.
Every window has a Feedback title-bar button that captures that window directly.
Desk > Give feedback also selects an element without running its action. A report
keeps the selected window's PNG, original WAV, rendered field values and
window identity together under `~/.local/share/holdspeak/feedback/`.
Capture freezes before recording, and Retry saves that same bundle. Password
and credential fields are excluded. Recording uses the existing microphone
session and audio floor. A speech failure does not prevent saving the original
report. No external delivery is required. The flag is off by default. Usage and the settled design are in
`docs/internal/ui-feedback/`. This owner development tool adds no betterment
recipe slice. Direct window button check: build/typecheck, 4,102 related web cases, four real feedback browser cases at 1440/393, 110 desk sweep cases with feedback enabled, 27 canon and 1,116 repository guards passed.
Initial capture check: build/typecheck, 83 related Vitest cases, 2 real feedback browser cases, 110 desk sweep cases, 27 canon and 1,116 repo guards; the preceding unchanged backend check passed 293 affected Python cases.

The full main tape pinned to `66beb450a` finished red: 11 Python, 11 browser
and one web failure (the Settings remote-access case reached its five-second
limit). No feedback case failed. Broader People, route receipt, retained
chrome and other tape failures remain open; this is not a whole-suite green.

The required check also exposed an existing launch watcher shutdown race:
a session ending after close could let the old watcher settle its launch.
The watcher now checks shutdown again before settlement. An event-controlled
regression fails on the original main source and passes with the two-line
guard; an active watcher still settles normally.

Ask can open the canonical person prep and meeting windows, arrange them,
report the changes in Wrote and restore the previous windows through Undo.
The person prep is `pullout:people:<id>`; `surface-people` is the roster.
Hydration registers the prep lens before mounting that same pullout identity.
The existing run trace records before/after revisions; Undo preserves newer
owner placement through compare-and-set. No second ledger or arranger is added.

The deterministic real-Hub check places Mira at (10,28,710,812) and Platform
sync at (720,28,710,812), with the exact seam and full working height. The
393 check shows safe in-band sheets (0,44,393,752), without claiming a tile.
After normal desk load, a canonical HTTP raise presents Mira at the front;
all nine points of her header are owned and its shot is visible.
The final real LAN run on qwen3.8-27b reached its first strict tile in
16.270 s, then Wrote/Undo reported Restored and removed only the new windows.
Its current observation is run `20261020T100334Z`; older timing files are
not the evidence for this run. Four successful model turns took 8.778 s
(discovery), 3.931 s (batched opens), 3.333 s (arrange) and 1.456 s (prose).
No retries or provider failure explain the delay. S9 remains Part: the
recipe's under-10-second gate is not met. Existing-person lens changes were
not observed in this fresh-open check.

Focused checks pass: 10 Python and 44 web, plus build. Both widths were
inspected. The first full check passed 4,193 related web tests, 1,620
backend checks, all 110 sweep, 27 canon and 1,116 guards. Its four failures
were a stale held-call coverage reply and the longer Send tool description.
The actual held-call writer now records Send coverage. The shorter prepare
description preserves both discovery examples and the owner-only boundary,
ends with the required Needs sentence, and fits the original prompt budget.
The memory comparison names only that description change; all other tool
and prompt bytes, and every original palette-size limit, remain strict.
All 61 focused Python checks pass. Required quick: Final delta: all 59 affected backend checks, 110 desk-sweep checks, 27 canon guards and 1,116 repository guards passed; build green. All 18 held-call face checks and 61 focused regressions passed; the unchanged window product passed 4,193 related web checks.

The main watcher found two first-run producer recordings missing the saved
Builder tools and Remote settings fields. The existing private-Hub writers
regenerated all 48 replies in the LAN and denied-calendar scenarios; both
writers and both normal replays pass. Strict whole-reply checks remain.
Speech stays unassigned after choosing a LAN chat engine, and only the
owner's Settings press opens the doubled calendar permission door once.
No product behavior changes. Required quick: All 5 first-run backend checks, 110 desk-sweep, 27 canon and 1,116 repository guards passed; build green. Both actual recording writers and normal replays also passed.

Needs shows each owner-prepared Send once, with its destination, source and
frozen preview. Unknown-delivery retry reuses the original command and
operation; rows without that provenance offer Check. Completed automations
prepare once and retain their name through owner Send. Manual preparation
of that same artifact remains labelled as the owner’s action.

Summary and Follow-ups use confirmed decisions and open confirmed actions.
Canonical edits and Desk decisions linked to the meeting appear once in the
outbound words; unconfirmed proposals stay out. Markdown remains frozen,
and email renders safe HTML with the matching plain text. Existing retained
rows without Markdown stay readable. No new queue or authority is added.

The integrated Send branch joins the reviewed content, Needs and automation
changes with the sheet and Edit path. Earlier checks passed 195 integrated
backend cases, 28 web consumers, six real Needs Send browser cases and the
two actual sheet/Edit cases. The focused fixes also passed 286 backend/browser
and 39 web checks, with three actual recording writers. Public metadata no
longer duplicates the body; the existing privacy fence passes. The Slack
Markdown expectation reads the actual renderer, and the canonical footer
replaces the old inline Send that the longer Summary covered on the phone.
The combined source passes type check, build, all 67 selected web checks and
all 47 focused backend/browser checks. Those include six Needs cases, both
sheet/Edit widths, the longer phone Summary, exact bytes and original-operation
replay. Retained Back and Room Send selectors now target the shared header
and footer; their original saved-document and operation assertions remain.
All 169 checks in the five updated retained web-consumer files also pass.
The original draft-save, held-send, retry and native/manual receipt assertions
remain strict. Both real uncertain-send reload cases pass; the Room receipt
locator follows its Send control into the canonical footer. The required
check covers these final retained browser selectors.
The first full combined check passed all 4,094 related web tests, 2,383
affected backend/browser checks, all 110 sweep, 27 canon and 1,116 guards.
Two Send whole-reply recordings still contained the removed public body;
their actual producer writers now pass and have refreshed all three replies.
The final delta replays the full Send backend file and recorded face consumer.
Required quick: Final delta: all 8 Send backend checks and 10 recorded face checks passed; all 110 desk-sweep, 27 canon and 1,116 repository guards passed; build green. The preceding full product check passed 4,094 related web and 2,383 other affected backend/browser checks.
The first real Send recipe remains open for the owner's five presses.

Send opens one shared sheet in the result's window. Destinations are chips;
Add destination saves and selects inline. Its footer keeps Send on screen,
and Back restores the original result and opening focus. The record's own
footer is absent while the sheet is open. Saved paths retain their case and
wrap inside the window. Native receipts and sent-by-hand records share Sent.

Edit makes a Note copy from the frozen preview and selects the same
destination. The real Note editor stores the changed line, and Send carries
those exact rendered bytes. The original meeting Summary stays unchanged.

The actual private-Hub case passes at 1440/393: meeting and Note Send,
inline Add, Back focus, Edit/store/send, exact file bytes, unchanged source,
and one durable Sent row after reload. All nine pointer points hit at both
widths; the phone Send owns a 44 px target. Both shots were inspected.
Earlier 34 focused web checks passed. The old retained form-persistence
check now uses Summary/Follow-ups while retaining its reload and per-object
assertions. The combined required check above covers this sheet.
The first real Send recipe remains open for the owner's five presses.

Other devices now saves its switch and displayed host/port in the existing
config through SettingsService. The remote gate, its read route and the
System fact read that same durable value. There is no process-only writer
or cache. Owner-only access and credential custody remain unchanged.

The real private Hub preserves enabled, host and a partial port edit across
restart. All 77 focused backend checks pass on the locked FastAPI 0.128.0.
The active Guide uses Works, Not ready and Does not work with the existing
reason text; a row without a fix gets no invented fix verb. Its six recorded
consumer checks, type check and build pass. Required quick:
Final delta: 75 affected checks, 110 desk-sweep, 27 canon and 1,116 repository guards passed; build green. The unchanged product also passed 4,084 related web consumers in the first broader run.
The first broader run passed 4,084 related web and 3,121 backend checks,
110 sweep, 27 canon and 1,116 guards. Three earlier consumer expectations
are reconciled with plugin inheritance and accepted People references. The
three focused regressions pass: explicit OFF still excludes a plugin, and
an explicitly undisclosed host is still refused with its receipt.
The fresh watcher pinned to `b8be8b36a` passed its first 5,921 Python
checks (16 skipped, one xfailed); the remaining full tape is still pending.

Speech route plans now use the same assignment order as Engines: explicit
capability or speech group, without falling through to the chat default.
Installed meeting plugins follow Meeting summaries before their group or
the global assignment. This changes the frozen runtime route, as well as
what the face reports. No assignment or engine is changed on the owner’s
desk. The worker collected and passed 46 focused checks against real SQLite
assignment producers. Required quick: 245 affected checks passed; all 110 desk-sweep, 27 canon and 1,116 repository guards passed; build green.

The main watcher’s retained browser adapters now follow the current doors:
Watch sources through Sources then RAW; meeting and decision icons through
explicit Desk membership; and a real drag onto the Agents Dock tile. The
checks retain exact review identity, run counts, nine-point hit testing,
receipt geometry and duration, one meeting window, and one agent launch.
All 13 selected cases pass on the real private Hub, including both widths.
The first two attempts failed in rig setup (Node path and a test-list parser)
and did not exercise these paths. The late-count Search case now queries
Projects before measuring, then delays the browser response without
blocking the test driver. The original top-ten and no-row-move assertions
pass in the actual private Hub. Required quick: 4,116 related web checks and all 55 Room/window browser cases passed; the earlier 13 focused source/receipt/agent cases passed; all 110 desk-sweep, 27 canon and 1,116 repo guards passed; build green.

Wallpaper has one home in Settings Desk. New windows use the shared content
size and placement rules; remembered heads move only when they collide, and
later owner drags and resizes retain their exact saved geometry. The Window
menu supplies Arrange front and Arrange all, preserving sizes and order.

Root passed 117 scoped web checks, type check and build. The actual private
Hub walk passed at 1440/393: six app heads, remembered collision, exact owner
resize/reopen, Arrange all with a Project drawer, Needs headline readback and
Settings. Jupiter label contrast measured 17.12:1. The broader check also caught stale menu/wallpaper assertions, a
Stage/Zoom free-height mismatch, the Chair's minimum overriding a thumbnail,
and a late New Project footer shift. These are fixed at the shared frame:
free content height stays in its existing geometry record, compositor plates
own their minimum, and the creation form retains its declared footer seat.
A Hub-inherited window follows that row; collision reseating runs on the
owner's reopen. All 74 scoped consumers, type check and build pass. The final
two real-Hub reload/collision walks pass; the prior five other window cases
also passed. The full required quick: 4,116 related web checks and all 19 window browser cases passed; all 110 desk-sweep, 27 canon and 1,116 repo guards passed; build green. Shell S9 and the unfinished Send slices remain open.

Failed native sign-in setup now cleans up through coder_factory. The
factory accepts only the just-minted private sign-in session name, revokes
its temporary agent credential and records the cleanup. A cleanup failure
preserves the original terminal-setup refusal. The lifecycle census stays
strict; no new direct tmux writer is admitted.

The watcher on 5bf3dc0c8 found seven Python failures (16,996 passed,
27 skipped and one xfailed) and two old creation-browser endpoint assertions.
Complete People and automation MCP/folder replies are re-recorded from real
producers. The deterministic drafter retains one confirmed linked Project
decision while recording no inferred memory. Creation still writes nothing
before a name, then one canonical decision. The People response also carries
the current saved Builder preference. Root passed 26 earlier producer checks
and 73 consumers, then 27 factory/sign-in/census/creation/producer checks and
12 People consumers on the integrated source. Required quick:
434 affected checks passed; all 110 desk-sweep, 27 canon and 1,116 repo guards passed; build green.. The remaining full tape is still separate.

Search uses one ranked stream, the last six successful opens, exact About
for Cmd+Enter and live object verbs. Protected People support Open, Ask,
Prep and Keep/Remove through the existing filing operation. Mode recipes
keep their semantic kind. Builder tools is a hub preference with the saved
revision, shared browser refresh and existing MCP settings access.

Root passed 65 collected backend/browser cases, including real person
Keep/Remove and Prep at 1440/393, exact Cmd+Enter About, phone search and
Builder persistence across two browsers. The 150 focused web consumers,
type check and build pass. The complete Settings wire group was recorded
through both actual producer writers. P9's canonical decision prompt and
front-project context are integrated. The first required check caught old
Search labels, grouping and cold-start assertions, the Runs-on rig using its
wrong owner token, a phone Hand hit-area overlap and an action-list left
rail. The shared styles and test adapters are corrected without changing
product authority or relaxing the geometry/canon checks. Required quick:
580 related web checks and 19 affected browser cases passed; all 110 desk-sweep, 27 canon and 1,116 repo guards passed; build green..

The final fix proof passed all 48 selected Search consumers, eight collected
browser cases (first use, Note editor, Runs-on Undo and strict Search hit
areas at both widths), 15 canon checks, type check and build.

The older pinned full tape finished red: 16,962 Python and 314 browser
cases passed, with five Python and four browser failures repaired by
#1397/#1400. Its web run passed 5,351 and failed two Settings cases; both
pass in the current focused run. A fresh full run must confirm integration.
The S4/S1/S0 Search follow-ups and the already-fixed Interview ordering
entry are reconciled with their retained proof.

P9 gives each decision one canonical record. New Decision carries About and
Why through the admitted decision.create path. Project This week, Decisions,
the decision window and Meeting Decide resolve that record. Legacy source
rows remain; the idempotent migration copies all of them without replacing
later canonical edits. Proposed decisions stay out of project evidence until
Confirm. A decision with no project membership stays out after Confirm too.

Root independently passed 188 final focused Python/browser checks and 87
web checks, including actual private-hub 1440/393 browser flows with strict
hit/focus checks, the real Confirm PUT, receipt hit areas and unchanged
canonical-ID readback. The preceding focused run passed 85 cases and 96 web
consumers. Type check and build pass. The final checks exposed two adapter
seams: Needs must carry proposed status, and its operation must use the raw
canonical ID while the row retains decision:<id>. Both are covered by the
actual flow. The combined API census has 810 routes and 675 OpenAPI paths.
The first required check passed 5,536 other affected cases, 4,076 other
web checks and all 110 desk-sweep cases. It caught a source-link write after
the creation receipt, four old callback/verb assertions, an obsolete receipt
fault URL, the changed Today recording, and two copy/scan checks. Source links
now come from the frozen tags inside the admitted producer; the adapter only
reads the resulting record through its existing service helper. The complete
Today response was re-recorded from its real producer. All final focused
checks, including residual identity, copy and zero-counter checks, pass.
The next check passed 617 affected cases, 4,079 web checks, all 110 sweep,
27 canon and 1,116 repo guards. Its one stale Today consumer expected the
Monday weekend lookback; the complete Tuesday recording correctly excludes
Friday's meetings. The expectation now matches that real recording.
Required quick: 617 affected Python/browser checks and 4,079 web checks passed in the integrated run; final Tuesday-consumer delta passed all 16 web checks, 110 desk-sweep, 27 canon and 1,116 repo guards; build green..

The follow-up audit closes five old entries already delivered by #1267,
#1303, #1304 and #1319. The source and retained proof are recorded in the
resolved ledger; the remaining entries stay open.

Send S8 keeps an unchecked published update sendable. Preview says
"Not checked yet: no claim in this update was accepted" above the words;
the existing frozen document retains the warning through Prepare, Send and
readback. A successful delivery records unchecked and the warning in its
existing proof and history. The owner's press remains required. Mixed
updates retain their existing omission behavior; source claims are unchanged.

Root independently passed 95 collected focused cases, including both real
1440/393 browser sends to a private folder, exact preview/file byte equality,
saved receipt/history readback and refusal of an agent's direct Send. All ten
Send web consumers, type check and build pass. The recorded consumer uses
a complete real producer response. No live external delivery is claimed.
Required quick: 4,079 web and 505 affected Python/browser checks passed; 110 desk-sweep, 27 canon and 1,116 repo guards passed; build green.

AG14 completes automations that hand work to native agents. Do selects Hand;
With lists installed native profiles, and Review by uses compatible native
reviewers. Owner-only binding changes are checked before any write. Agent
drafts stay drafts; the runner does not claim an agent started when queued.

Scheduled Hand uses the existing durable owner delegation and parent receipt,
without requiring an unrelated inference assignment. Repeated ticks and
events do not launch twice. Changing the native profile, reviewer, instruction,
sources or Put it in fences the old authority and turns the schedule off until
the owner approves When again. Hand remains prepare-only for Send destinations.

Root independently passed 28 focused cases, including schedule authority,
the real private-hub queue/Done/Today/readback loop and ordinary Do → With →
Review browser flows at 1440/393. The native leaf is a private fixture process;
live Claude/Codex provider work is not claimed. All 32 web consumers, type
check and build pass. The chosen native agent shows its human name.
Required quick: 4,078 web and 4,273 Python checks passed (1 skipped); 110 desk-sweep, 27 canon and 1,116 repo guards passed; build green.
The first required run passed all 4,078 web checks, 4,264 other affected
checks, 110 desk sweep, 27 canon and 1,116 guards. Its eight failures were
the canonical schema snapshot and seven recorded response shapes. Root
regenerated the snapshot from a fresh DB and the complete responses from
the real producer (26 cases pass). The extra schedule fencing is limited to
native Hand work; ordinary Run instruction edits retain their schedule.
All 24 focused schedule/schema cases and 32 web consumers pass afterward.

Project automation NEW now follows the latest completed artifact and its read
state. The artifact carries the exact project-update ID; Open latest fetches
that update and uses the existing result-open path. An owner draft alone
does not show NEW. Legacy or foreign update links open the automation rather
than guessing at a draft. Failed reads keep NEW.

Root independently verified five actual runner/producer cases and both real
browser widths (seven passed), plus 44 web consumers, type check and build.
The browser reads the exact delivered body, clears NEW, preserves the owner
draft and repeats Open safely. The wire fixture records the full manual,
completed, opened, read, legacy and foreign responses from the real hub.
Provider inference is the repository's recorded leaf; live-model quality is
not claimed. This closes a P7/P8 follow-up and adds no slice.
Required quick: Final delta quick passes 36 web, two actual current Room browser cases, 110 desk sweep, 27 canon and 1,116 repository guards; build passes. The product run passed 2,154 affected cases (two skipped) and 4,113 other web checks. The separate five actual runner/producer cases and 44 Room consumers also pass..
The first required run passed 2,154 affected cases (two skipped) and 4,113
other web checks. It caught a Note reveal assertion that read before its
scroll/focus effect, and a phone Search sprite still loading outside the
swept window. The Note check now waits for that effect (36 focused cases
pass); the sweep waits for visible chrome sprites as well as the face's
visible images. No focus, visibility, size or contrast assertion was waived.

S4 delivers the explicit Floor: fresh desks show Inbox, Work, Personal,
Reference and Archive. Meetings and people appear only after Keep on desk;
Remove uses the existing membership operations, and removing a note files it
in Inbox. Empty packaged Meetings/Decisions drawers and the Desk membership
record are hidden. Existing records remain intact.

The existing desk position store preserves first-seen rectangles across late
producer replies. Root corrected a new-column overlap by reserving saved
positions even while their source reply is pending. The real private-Hub walk
imports three meetings and creates three people without new Floor icons,
keeps one meeting, adds a late note, and appends 14 more projects. Every
existing rectangle stays exact and no pair overlaps. Current 1440/393 shots
and measured rows are under `.tmp/evidence-shots/s4-root/` in the Floor lane.
All 19 seed and 63 web checks, type check and build pass.
S4 remains partial: mode recipes in Search and the individual person
Object-menu adapter finish with S5. The real Keep proof above is a meeting;
individual People are not ordinary Items primitives. This merge adds no
completed slice.
The Agents Dock tile now accepts the existing drag-to-hand path. The actual
browser drag opens the exact note preview without launching or editing it.
All 71 focused web cases pass. The current arrival case opens the bell and
observes the real Needs-you row at both widths; both walks pass. Four reds
from the pinned main browser tape were old Dock controls, count expectations
and an exact Today label; their real browser replacements pass with the
membership, touch-size and cross-window latency assertions retained.
Required quick: 4,078 related web, 34 affected Python/browser, 110 desk sweep, 27 canon and 1,116 repository guards pass; build passes. The separate current arrival walk passes at 1440 and 393..

P10 offers only watch actions with an existing runtime path. A new
project.observe evaluation writes its observation without a pending effect;
legacy effect rows remain readable. Provider manifests, Steward serializers
and meeting transcriber construction now live in shared services. HTTP and
MCP use those same contracts, with no MCP imports from web routes.

The worker passed 504 focused cases, then six retained boundary
and producer regressions. An actual private database observation creates no
new effect and preserves the legacy pending row. The AST fence covers all 37
MCP Python files, including relative and alias import forms. Shared helper
identities and wires retain parity. Root independently verified 27 focused cases covering the whole import boundary, actual fresh observation and retained legacy row, provider HTTP/MCP parity, Steward policy round-trip, import parity, and remote-owner refusal before file access.
Required quick: Final delta quick passes 67 affected cases, 110 desk sweep, 27 canon and 1,116 repository guards; build passes. The preceding product quick passed 3,424 other affected cases with two skips; its one failure patched the old HTTP factory seam and is corrected by the final check..

ST8 starts the installed GitHub or Atlassian CLI browser sign-in from the
Accounts row and seats its native terminal there. Keyboard input uses the
existing admitted process input path and immutable target identity. On native
exit, the existing Check re-reads the account before the row can say Works.
Unsupported browser flows and failed/disappearing terminals give a named
failure. Target setup failures clean only the newly created sign-in session.

Root reviewed the owner-only operation and target mismatch refusal, then ran
123 focused checks: 122 passed and the new operation exposed one missing
producer case. The completed producer contract suite passes all 65 cases.
Actual private-Hub browser cases at 1440/393 feed Enter through embedded xterm,
the real command transport and native tmux process, then read back Works and
the account login. Only provider CLI responses are recorded; owner credentials
and real OAuth acceptance remain unobserved. The combined API census has
810 routes and 674 OpenAPI paths. The product check passes 7,051 affected
Python/browser checks (four skips), 110 desk sweep, 27 canon and 1,116 guards;
4,094 other web checks pass. One old terminal assertion expected a payload
without its required session/agent binding; it now checks the full payload
while retaining immutable target and server-derived authority assertions.
Final delta quick: 17 terminal web checks, 110 desk sweep, 27 canon and 1,116 repository guards pass; build passes. The preceding product run passed 7,051 affected Python/browser checks and 4,094 other web checks.

The main watcher pinned to 2833d225d found five failures after its first
6,073-test shard passed. This fix re-records the actual Setup agent/Settings
producer shapes, aligns Capture's backend window action with its manifest,
and retains the fresh prior-account status check in the Confluence test.
Only recordings with changed response shapes are replaced; whole unchanged
captures remain intact. The independent focused rerun passes all 64 Python
checks (including the phone Capture/Today/Capture roundtrip) and 62 web
consumers. No provider sign-in or owner database is used.
Required quick: 79 affected Python/browser, 110 desk sweep, 27 canon and 1,116 repository guards pass; build passes; the separate 62 web consumers pass.

The P5/P6 source-link follow-up is closed by an actual producer contract:
found_links reports linked/failed per meeting or note. New and existing project
Add paths use it. A failed selection stays selected with its producer error;
Retry sends only that item to the already-created project. Missing individual
results stay failed. No successful source or project is created again.

Root collected and passed 57 affected Python cases, including the real HTTP
partial-failure and two-size browser Retry, plus 40 Door web cases and build.
The durable resource readback finds each successful relationship once. The
owner's database and provider credentials were not used. This closes follow-up
work and adds no slice. Required quick: 241 affected Python/browser, 110 desk sweep, 27 canon and 1,116 repository guards pass; related web checks and build pass.

P7/P8 make the project update an ordinary automation, initially manual. Friday
at 15:00 changes that same record. Room opens its newest result and reads the
actual engine assignment. A refused Friday change keeps the manual state and
offers Try again. The old steward controls remain under More.

Update agents use eligible linked project sources. Private one-to-ones, People
and unlinked meetings stay out of prompts, tool reads and native MCP resources.
Explicit owner-filed actions remain eligible. An agent writes its own separate
draft and cannot replace an owner-edited draft. Workbench delivery adopts the
exact returned result once; applying it adds no duplicate.

Root verified 70 affected Python checks and 561 Room web checks. Four actual
Workbench runner cases cover plain/tool-written output with and without owner
edits. Native hub credentials exercise both filtered tool reads and resource
refusals, with ordinary credentials retaining their existing access. Real hub
Room geometry passes at 1440/393. Native model output quality is not claimed;
the engine leaf is recorded. Required quick: Final delta quick passes 4,074 related web checks, 54 affected Python/browser checks including both current Room geometry cases, 110 desk sweep, 27 canon and 1,116 repository guards; build passes. The preceding product run passed 4,110 web and 4,571 other affected Python checks. Empty-state and recorded-wire contracts now include the automation, the display-only engine reader has its exact census classification, and the verb says Open latest. Known fix-forward: Room NEW still follows draft lifecycle and must use the existing automation artifact read state. The pinned 2833d225d main watcher has passed its first shard (6,073 passed, five skipped); the full tape remains incomplete. The prior 41f4ebc9f tape completed red, with its known failures corrected in later focused checks..

Shell S3 gives the desktop Dock Today, Meetings, People, Agents and Speak;
the phone has Today, Capture, Meetings, People and Agents. Both use the
application manifest. Phone words stay visible in five whole 76-pixel tiles;
each owns its hit area. Ctrl/Cmd 1–5 follow the desktop order. Needs you is
Ctrl-J and Settings is Ctrl-comma, with the typing guard preserved.

Tile facts come from the existing Needs you, meeting, one-to-one, mic and
agent producers. Zero counts stay hidden. Phone orb and Dock layout controls
leave the Dock. Root reviewed actual two-size geometry and key-opening
proof, then verified 31 guard/menu checks and TypeScript. Earlier 116 focused
Dock/key checks pass. The inherited writer census now excludes parked
history; Setup's duplicate viewport layout follows its window container.
No guard is widened. Root also repaired the current walk instructions for
Setup and Settings while retaining the outcome predicates and sealed pass
records. Eight of nine checks passed immediately. The remaining phone check
exposed a real bug: a Settings section anchor still consumed Back as if it
were a child page. Settings now returns to its caller in one Back press;
the actual same-receipt, nine-point hit and durable identity check passes.
The integrated product run passes 4,073 web checks and all nine current walk
cases. Its remaining web assertion clicked the removed Dock Reset button;
the retained verb now exercises the same persistence assertions. The exact
Agents-key census follows Ctrl-4, and the atlas gate fence recognizes current
and historical entrance words. API census failures exposed unpinned FastAPI
0.150 in this worker environment, against 0.128 in uv.lock; Root restored the
locked dependency set instead of publishing a five-route partial census.
With locked dependencies, all 774 affected Python census/atlas checks and
27 shell checks pass. Final delta quick also repeats the nine real-hub walk
cases under the locked backend. The next sweep caught a real 32-pixel shift when the People 1:1 tag arrived.
Meetings and People now reserve their tag width before the read, and the Dock
limits the 1:1 fact to its local day. Root held and released the real People
response: all five target rectangles stayed exact; the browser case passes
in 6.28s. The 27 Dock/read web checks also pass, including today/tomorrow.
Required quick: Final delta quick against the verified product source passes 10 actual Dock browser cases, 110 desk sweep cases, 27 canon and 1,116 repository guards; build passes. The preceding product run passed 4,076 related web and 768 other affected Python/browser checks. Last observed desk before this merge: backend aa4ecd9d3, frontend 212132a1074a6815, PID 32823. Each merge deploys its exact source; GET /api/system/identity reports the running identity..

ST9 adds `holdspeak setup`, `holdspeak setup --yes`, MCP `setup.status` and
`setup.use`. They use the running hub and the shared Setup producers.
Use all re-reads the inventory, keeps each result, continues after a failure,
and distinguishes pending work. Agents can read status; adoption requires
an owner press. Caller-supplied row inventories are ignored.

Root's focused collection and run both cover 123 checks. The CLI-to-MCP
proof reaches real hub operations and provider adapters, checks three
account connections, saves a calendar, installs both native agents' tools,
hooks and skills, and reads all adopted rows back as Works. Only native
CLI/provider responses and EventKit are simulated; files and records are
in the rig. A separate scratch-hub probe covers real HTTP discovery and
agent-read/owner-use authority. Live OAuth and owner account acceptance
remain unobserved. The first integrated quick found an accidental seeded Thread palette expansion,
stale operation/exposure counts and an old People settings wire. Setup inventory
now stays MCP-only in the seeded palettes; their original byte limits and tool
counts pass unchanged. The actual People producer re-recorded its wire. The
write-announcement walk now builds valid required oneOf inputs. All 270 checks
covering those seams pass. Required quick: 3,767 affected Python/browser checks pass (three skipped), plus 108 desk sweep, 27 canon and 1,116 repository guards; build passes.

AG15 shows Claude Code and Codex processes the owner started in tmux in
Agents you started yourself. Native executable, pane ancestry and session
facts identify the process; registered HoldSpeak launches stay out.
Existing screen rules and secret filtering supply state. Owner Answer,
Allow and Deny re-read the prompt and use the admitted input transport.
These rows have no Stop, brief or autonomy controls.

Root collected and ran 31 focused checks, including real private-tmux
browser cases at 1440/393. The fake native process receives the typed answer
and approval key through real hub routes. Evidence frames show the full
question and controls. An additional private-tmux producer/transport probe
returned operation op_8edbe1d3e86d4b0681a811b8f98d0ac5. Installed Claude and
Codex executable shapes were inspected without starting a model. Native
interactive-agent acceptance remains unobserved. Shared test and walk rigs
force discovery off; the isolated positive rig opts in after boot.
The first required quick passes 4,072 web checks, 1,221 affected Python/browser,
108 desk sweep and 27 canon checks. Three repository guards found missing API
exports and the new read-only ps/tmux census classification. Root regenerated
both API exports from the app and classified that exact local reader; all
input writes still use admitted process.input. Final delta quick against that
verified product source: 14 affected Python, 108 desk sweep, 27 canon and 1,116 repository guards pass; build passes. The prior product run also passed 4,072 web and 1,221 affected Python/browser checks.

ST7 makes Settings one page with You, Speak, Meetings, Notices, Accounts,
Agents, Desk and This Mac. The desktop index sits beside the page; phone
section words wrap. Existing writers, secrets, grants, revisions, retry and
Saved feedback remain in place. More folds hold advanced controls; Telegram
is in Accounts. Old scopes and Search open the corresponding section/row.
Engines has its own real window, including the old Concierge alias and
first-use recovery. Today, Speak and Meetings have their Settings links.

Root restored meaningful writer, grant and credential consumer coverage
that the original layout candidate had parked. Final focused checks pass:
111 web checks and 72 Python checks, with the earlier five real-route browser cases. These exercise the
heartbeat write/Saved/readback, Quiet-hours Search and a real hub-owned
Engines window at 1440/393. The two-size first-use walk also passes through real fixture speech, note custody, engine setup, meeting summary and finding saved work after restart. Old wing-only tests remain parked.
The integrated Settings/first-use browser rerun passes all 12 cases. Setup keeps
name entry disabled until its initial read completes, so early typing cannot
be discarded. The sweep waits only for visible images within its target
window; offscreen lazy wallpaper does not prevent a face from settling.
The main sweep also exposed Door's late source rows moving the active Paste
controls. Paste now precedes those asynchronous rows. The separate P5
per-item link failure/Retry follow-up remains open until its producer and
real HTTP consumer proof are complete. All 61 Settings/calendar writer
checks pass after scoping their queries and advancing the actual debounce
clock in the retry scenario; no timeouts or assertions were removed.
Required quick: 4,072 web, 73 affected Python/browser, 108 desk sweep, 27 canon and 1,116 repository guards pass; build passes.

Shell S2 gives Desk seven New kinds in order: Note, Meeting, Decision,
Project, Person, Automation and Drawer. The phone reads the same registry.
HoldSpeak holds Settings, Engines, Accounts, Wallpaper, Setup and Keyboard
shortcuts. Refresh is in Builder. Retired creation/menu verbs retain their
implementation but leave menus, Search and keys; Ctrl-T now also makes a note.
The keyboard sheet groups Apps, New, Windows and Desk.

New Drawer uses the existing directory producer and starts its selected name
in the active desk. Root found that the rename store had no active field,
then exposed covered and overlapping fields through actual browser presses.
The shared rename field now occupies the drawer caption seat; open windows
move to their Dock entries so the owner can see and type the name. Real
create/type/Enter/readback passes at 1440/393, including a hit test proving
another object does not cover the field. All 125 focused shell checks pass. The first broad check found nine old New-list/shortcut assertions; the updated 68-check consumer set passes, retaining parked-verb behavior and exact key/menu membership. All six creation browser cases passed in that run.
Required quick: 4,083 web, six creation browser, 108 desk sweep, 27 canon and 1,116 repository guards pass; build passes.
Last observed running desk before this merge: backend 2d60f6961,
frontend 24e6d924e7e355e5, PID 96598; identity/import/database ownership and
/health, /, /conductor, /models passed. Each merge deploys its exact source;
GET /api/system/identity is the current running identity.


ST6 gives the owner one Setup press to install hooks, the native user-scope
HoldSpeak MCP entry and the packaged skill for Claude Code and Codex.
Each agent shows its actual hooks/tools/skill readback. Stop using my desk
removes only HoldSpeak-owned bindings and preserves foreign configuration.
An earlier agent failure remains visible if a later agent succeeds. The row
refreshes after install and removal; failure words retain a retry.

Current integrated focused proof: 54 Python checks, including both real-route
browser cases at 1440/393, and 13 web checks pass. The browser verifies the
three Codex bindings, mixed failure, owned removal, foreign preservation and
refreshed state. Separate scratch-HOME probes exercised the installed native
Claude/Codex MCP add/remove commands and MCP initialize. Native interactive
agent acceptance remains unobserved; no owner agent files were changed.
The frozen d4cf5fac7 check passed 4,080 related web checks and 2,245 affected
pytest checks; its only remaining failure was the generated operation export.
That export is now regenerated from the corrected result declaration.
Required final delta quick: 64 affected Python, 108 desk sweep, 27 canon and 1,116 repository guards pass; the build passes. The preceding frozen-source run passed 4,080 web and 2,245 affected Python checks; its stale generated export is corrected by this delta.

C12 shows Recording · mm:ss in the macOS menu bar itself, using the
meeting's start stamp. Stop in its menu calls the existing runtime Stop.
The presence page's connection lamp supplies availability; a disconnected
desk reads Desk not running and disables Stop. An idle update clears the
recording title and stale Stop state, including after the panel linger.

The visible-title check fails before the fix. All 30 focused presence checks
pass afterward, including the real Foundation Objective-C action target and
the parent Stop-event bridge. A real Foundation dictionary regression also
caught and fixes the disconnect read ignoring WebKit's native value.
The former focused runtime set also passed.
Native menu rendering and physical recording remain unobserved. Required
quick: 427 affected pytest, 108 sweep, 27 canon and 1,116 repo guards pass.

C11 ships five closed desk phrases in Speak. Record, Stop and New note
use authenticated MCP operations; Ask and Today use the existing Desk openers.
New note opens the exact stored note returned by the producer. Commands is
now the Voice commands wing of Speak; a saved Off choice remains off.
A saved Commands window migrates to that wing. Desk-command tests show an
explicit Preview and do not run a connector; the guide describes the new
defaults and the separate custom-action tests.
Synchronous command dispatch stays off the event loop.

Record releases the ended browser claim before starting Meeting. A real
recording exposed a missing Stop path: its microphone claim rejected the
second Talk. The fix admits only the closed Stop command during recording,
without taking or releasing Meeting's claim. Ordinary dictation, field
microphones and other commands retain the named refusal; no journal row is
written. The regression fails before the fix and passes after it.

Focused Python: 33 checks pass, including actual MCP/controller Record and
spoken Stop, responsiveness and the restricted recording path. Native audio
is simulated in process; C10 separately verifies child ownership. The real
authenticated note-write browser proof passes at 1440/393. Native hardware
and concurrent native/browser microphone acceptance remain unobserved.
Required quick: 4,092 web, 320 affected pytest, 108 sweep, 27 canon and 1,116 repo guards pass.

AG12 adds Review by to Hand to agent and Start an agent. A builder commit
starts a reviewer helper in its own read-only worktree. Explicit MUST
findings return to the builder, with at most two rounds; the pair retains
one Result. Unresolved findings or an unreadable reviewer result still need
the owner. Durable pair state overrides stale terminal-screen state in both
the fleet and lane.

The real isolated hub with two fake agent processes completed MUST → builder
fix commit → second review clear. Reviewer credentials refuse writes,
preparation, sending and helper creation. Focused checks: 18 agent-flight
checks and 130 web consumer checks pass. The actual completed producer pair
renders Done · New and its two-round Result at 1440/393. Native interactive
agents are not inferred from the fake processes. Required quick:
4,076 web, 9,304 affected pytest, 108 sweep, 27 canon and 1,116 repo guards pass.

Setup ST3–ST5 share one found-things window on first run and later visits.
Use selects real discovered engine IDs and the composed Everything-else
assignment; it does not wire speech to a chat model. Calendar, People and
agent rows report their producer outcome. Unknown success bodies remain
unconfirmed. The microphone Check opens the actual doctor section in place;
late microphone admission is cancelled when the window closes. The existing
Settings guide alias opens Setup. Retired sources and tests are parked.

Focused verification: 66 web checks, two real-route browser cases at 1440/393,
12 Settings/Setup sweep cases, 16 product-copy checks and TypeScript pass.
The browser records the actual LAN Use and microphone-doctor response bodies.
The frozen-source check passed 4,072 related web checks and 5,186 affected
pytest checks. Its sweep exposed one retired /welcome selector; the current
route check now requires the visible Setup heading. Required final delta
quick from frozen source 7052755f3: 108 sweep, 27 canon and 1,116 repo guards pass. No native hardware or owner-provider
acceptance is inferred from the isolated checks.

The meeting-window regression now selects the failed-summary member when P5
also offers the same-title meeting as a project source. Both 1440/393 browser
walks pass, retaining the single-window assertions across every live door.
The web check now uses the same eight-worker bound as pytest, under the shared
lock. All 5,387 web checks pass in 111.97 seconds with eight workers; the prior
two-worker related run took 268.49 seconds for 4,071 cases. No checks or
assertions are removed. Required quick: 14 affected pytest, 110 sweep, 27 canon and 1,116 repo guards pass.


C10 moves native meeting streams and the capture journal into one child process.
The parent receives durable PCM and levels. Stop gives the child one second,
then terminates it; only confirmed child exit releases the floor for another
Record. Missing terminal status remains a capture failure with a recoverable
journal. The C9 queue and writer failure guarantees remain intact. Focused
integrated capture checks: 54 pass. Native hardware is not observed.
A later successful capture for the same calendar event clears its failed-fire
attention row and retains the failed schedule and receipt; an earlier success
does not clear a later failure (three focused checks).

The pinned b2c642b42 regression tape has 16,877 non-browser passes and two stale
Needs-you assertions: P5 now adds a muted matching-meeting candidate. Both
assertions now name that candidate while retaining the six canonical members
and mutation checks; all six focused cases pass. The tape also found two
meeting-window walks selecting a same-title project suggestion instead of the
failed-summary member; that browser repair is merged in #1383. The tape
finished red at that older pin and does not cover C10. Its 13 browser failures
are repaired by #1381/#1383; its web writer census failure is repaired by
#1381. Exact pinned totals: 16,877 pytest pass/two fail; 320 browser pass/13
fail; 5,383 web pass/one fail. A newer integrated tape remains required. Final required quick: 1,029 affected pytest, 110 sweep, 27 canon and
1,116 repo guards pass. Capture is observed at 1440/393 on an isolated hub.
Two prior bare-desk settle timeouts did not recur in the focused six-case
check or the final full sweep; failure diagnostics retain actual state and shots. Before this merge, the running desk is backend
76dc385df, frontend 8ebab34a8ee7b2d2, PID 61369; deployment follows the merge.


Capture now keeps its designed CSS seat while unarranged. A slow Coming up
read no longer freezes the window against a temporary placeholder height; reopening
uses the same default position. An owner move, resize or zoom keeps its saved
geometry. Four focused browser cases pass, including moved and resized windows.
Required quick: 4,103 web, 110 sweep, 27 canon and 1,116 repo guards pass.
The Capture fence also passes at 1440/393.

C9 #1379 moves PCM admission into a bounded queue and writes the buffer/journal on
one writer thread. Stop seals admission, aborts native streams, flushes accepted
items, then snapshots. Queue refusal and writer failure survive into the saved
Meeting and recoverable journal marker; Stop does not claim complete capture.
Focused callback/durability checks: 32 pass, including the blocked journal and
same-ID PCM recovery. Required quick: 160 affected, 110 sweep, 27 canon and
1,116 repo guards pass. Capture shots pass at 1440/393. Native
hardware is not exercised; C10 now delivers the child-process boundary.

**Betterment recovery: 93/117 recipe implementations merged.** Codex owns
recovery and delivery at the owner's request. The desk is currently on
backend `53783b27f`, frontend `fcc01f42cb0f8823`, PID 71110 (#1385).
Four HTTP checks pass and the actual desk renders at 1440/393. These are
delivery observations; owner acceptance remains separate. All three baseline non-browser
regression shards passed: 16,784 checks, 27 skips and one expected failure.
The original baseline remains at `wt-betterment-tape-20261019`, pinned to
`bd3acff8f`; its three browser shards exposed six stale controls now covered
by #1370 and #1371. That run was superseded before browser shard four, with
all results retained. The full tape completed at low priority in
`wt-desk-betterment-20261019-notes`, pinned to `ec3dde784`: 16,840 pytest pass,
four fail, 27 skip and one expected failure; 320 browser pass, 12 fail and one
skip; 5,369 web pass and one fail. Its non-browser shards found four failures: two producer
wires are fixed in D10; the curated MCP resource and launched-helper census
checks are now repaired. The parked New knowledge verb is no longer published.
The census requires the five helper tools to refuse an unlaunched principal
with launch_only and HTTP 403; a valid launched principal still dispatches.
Focused checks: 63 pass. Required quick check: 247 affected pytest, 110 sweep,
27 canon and 1,116 repo guards pass. This fixes the identified cases; the
pinned full tape does not cover subsequent main revisions. The twelve browser
failures are five retired Rhythm-host expectations, three retired Conductor
controls, two retired note-editor expectations, one 1px Button census and one
Capture seat shift. The web failure is the explicit Record-home auto-record
projection missing from the writer allowlist. All twelve identified browser failures and the Record-home writer allowlist
are repaired in verified delivery slices. The pinned tape retains its original
results; a fresh low-priority tape is queued at `b2c642b42` and does not include
this Memory/browser slice. #1376 is deployed;
identity, database ownership and four HTTP checks pass. The populated Projects sweep also found rows
moving as independent status reads finish; its regression fails before the
atomic first-read repair. After the repair, 4,090 web checks, 110 sweep cases,
27 canon checks and 1,116 repo guards pass.

Accounts Check now reads the active acli profile under the existing account
lock when its registry has no known prior profile. It checks the selected
account and restores the actual prior account in finally. An unreadable,
malformed or failed status read refuses Check before any switch. Known-prior
restoration remains intact. All 132 focused checks pass with a fake CLI;
the owner's auth state is untouched. Required quick: 326 affected Python, 108 desk sweep, 27 canon and 1,116 repository guards pass; the build passes.

Q11/Q12 make Memory an answer desk and put the two directions of what is owed
first in a person’s window. Pages have their own pass budget and continue past
a HoldSpeak-made LAN default to the owner’s chosen Everything-else engine.
Why uses source-linked beliefs; project and People links remain independent.
Whole-desk Ask clears the prior About scope, and Recall keeps the current
decision before its predecessor. The existing tool-palette limit stays fixed.
Root corrected an over-generous deterministic writer and recorded distinct
answers through the real extraction, consolidation, page and read producers.
The recorded Person consumer passes. At 1440/393, Go opens Memory, Mira shows
both directions, and one source press opens her actual 1:1 transcript. These
use deterministic model boundaries; live-model quality is unobserved.
Focused producer/page checks: 82; recall-order checks: two. Final quick check:
4,098 web, 1,083 affected pytest, 110 sweep, 27 canon and 1,116 repo guards.
Q11/Q12 #1375 is on the running desk. Its two existing pages render at
1440/393 without page errors. Both remain stale with ten new sources; a
fresh live-model page write is not observed. The routing follow-up now carries
the selected Memory head through the real page writer and physical runner.
LAN and cloud doubles prove that the owner-selected fallback determines the
physical revision and receipt; clearing that head refuses another call. The
model leaf is doubled; no new owner page was written. Focused routing checks
pass; the required quick check runs 102 affected pytest and 110 sweep cases.

P5/P6 #1377 preserves provider sites through paste, validation, preview and saved
watches. Matching uses provider, site and scope; an unknown site or ambiguous
bare key names the problem without selecting another account. Preview is an
admitted owner HTTP operation. Found meetings and notes can be added together
or removed from the selection; the same Door adds sources to an existing
project. Waiting-on Nudges use the item's exact saved destination and stored
action text. Preview and preparation do not send; the owner presses Send.
The Room field keeps the shared Ask window and its project scope.
Two-size isolated browser proof: five presses, three meetings and two notes;
the existing-project Add sources path also passes. Focused provider/preview
checks: 46; destination-bound nudge checks: two; initial related web: 4,138
pass with one old request assertion, now corrected. Required final quick:
six web, 96 affected pytest, 110 sweep, 27 canon and 1,116 repo guards pass.
The added document kind passes the real Send/stale-preparation census; the
API and exact identity-helper classifications are current. The phone reader
allows only the recipe's declared, reachable filter choices; unreachable
text and ordinary horizontal overflow still fail. P5/P6 is deployed; source import, database ownership and four HTTP checks pass.
Live external provider authentication remains unobserved.

The eleven retired-control and painted-plate browser findings pass across
Conductor, note, graph-walk and kit checks (30 browser checks). The graph and
current atlas checks also pass 756 focused cases. The next required sweep
found the Memory RAW fold moving 421px on a held first read. Its independent
answer, directory and belief reads now hold the lower controls until their
first batch settles; Ask stays available. Final required quick: 4,110 web,
30 affected browser, 110 desk sweep, 27 canon and 1,116 repository guards pass.
Earlier HTML-route settlement timeouts did not recur in the focused rerun or
the final sweep. Timeout diagnostics now report actual unsettled elements;
no timeout or assertion was relaxed. Capture default placement shipped in #1380.

AG13 #1374 packages the HoldSpeak skill and prints it with `holdspeak --skill`.
Claude launches discover the private copy through `--add-dir`; Codex launches
discover the repository-native copy without changing CODEX_HOME or auth.
Connect preserves foreign settings and installs user skills in their native
roots. An offline native Codex probe finds the skill without a model call.
The wheel contains the text. Required quick check: 1,305 affected pytest,
110 sweep, 27 canon and 1,116 repo guards pass. Existing hooks-only readiness
upgrades remain ST6. AG13 is deployed. Its real terminal wrapper prints the exact packaged
18-line skill; source import, database ownership and four HTTP checks pass.

Projects repair #1373 is deployed. Its actual list is observed at 1440/393
without page errors after the atomic first read.

D10 #1372 makes `today.get` a declared read composed from the same Needs you,
day, Since yesterday and Prepared producers as the Today face. Its real-hub
MCP parity check passes. The agent palette can read it; owner decisions and
sends keep their existing authority. Cadence attention names the real action,
uses a qualified artifact source before a meeting fallback, and opens that
source directly. It no longer shows a generic Cadence summary. The owner
has two valid automation-attention rows; neither was dropped to change the
number. Current Accounts and scheduled-recording wires were recorded from
their producers. Quick check: 5,931 affected pytest (four skipped), 106 sweep,
27 canon and 1,116 repo guards; the first-run consumer passes 31 web checks.
The service inventory is split out of runtime composition within its existing
line budget. D10 is on the running desk. Its real Cadence popup is observed
at 1440/393 without page errors: both valid rows remain, the source opens
directly, and no generic summary appears.

#1371 updates the browser checks to the adopted Q8 note
window. The real saved body, direct footer verbs and keyboard focus ring are
checked at 1440/393. The uncertain-send check now opens Send… from that footer;
it still proves one send and one result after an uncertain response and retry.
The two affected browser files pass 14 checks. The retired formatting-rail
case is parked. This closes the six known browser failures in baseline shards
one through three together with #1370; the remaining baseline shards are open.

P4 #1349 puts Projects and Decisions in Go and offers Write update for the
chosen project in Search. Project rows retain the Now state and reason;
a failed read says Not read. Root inspected Blocked, At risk and a deliberately
unread project on the actual isolated hub at 1440/393. Focused producer/face
checks passed 22 pytest and 47 web checks. Broad recovery checks passed
4,104 web and found an asynchronous focus assertion; its corrected file passes
8 checks. Browser recovery now opens Plan, checks the adopted Now head, and
holds two populated active folds rather than the retired Files fold. Final
quick check: 8 web, 36 browser, 110 sweep, 27 canon and 1,116 repo guards.
The earlier affected non-browser checks passed unchanged. P4 is on the running
desk; Projects is observed at 1440/393 without page errors.

AG11 #1369 gives launched agents one owned helper with prompt, wait, read and
question-only answer tools. The owner can Allow a Secure helper from Needs you;
other agents cannot allow it. Recovery reproduced two stale-wait races and
binds delivery to the helper's actual session and question episode. A real-hub
fake builder starts a helper, prompts it, waits for Done and reads its result;
root inspected the nested rows at 1440/393. Real Claude/Codex execution remains
unobserved. Final quick check: 4,055 web, 188 affected pytest (one skipped),
106 sweep, 27 canon and 1,116 repo guards. After integrating Capture and the
People fix, the shared Needs you seams pass 43 web and 19 pytest checks.
AG11 is on the running desk; identity and four HTTP checks pass.

Recovery follow-up #1370 fixes two reproduced People-store defects: optional SQLite
journals can disappear during the permission check, and setup/readiness held
connections until garbage collection. The journal race fails twice before the
fix; three retained-connection checks fail before explicit closure. All 12
People-store checks pass after both fixes. The required quick check passed
285 affected pytest, 106 sweep, 27 canon and 1,116 repo guards; the three
additional connection checks ran as a separate focused red/green proof.
The two stale compact-agent browser assertions now check the full question,
wrapping and drawer geometry; both pass. Six closed follow-up rows are parked
in FOLLOWUPS-RESOLVED-2026-10-19.md. These repairs do not establish that every
historic People 503 has the same cause. #1370 is on the running desk; identity
and four HTTP checks pass.

The owner's Record home is observed at 1440/393, without page errors, after
C7/C8 deployment. The terminal wrapper now imports that deployed source;
15 existing Claude/Codex hook commands follow the wrapper. Previous files
are parked beside their originals. New sessions use the updated commands;
existing sessions can retain their startup hook configuration. The MCP
sidecar remains a live-hub proxy. User-scope MCP/skill setup remains ST6.

C7/C8 #1363 gives Meetings its Record wing, durable failed/missed occurrence
words, and a Needs you Record now press that starts the named calendar
meeting. Talk receipts use plain words; Capture speech reaches the saved
note handoff. Root inspected the real-hub fixture at 1440/393. Focused worker
checks passed 81 pytest and 172 web checks. Broad recovery checks found
three old receipt/settings assertions and one window-focus browser case;
the assertions now follow the current face and use the actual Go press.
The final quick check is green: 21 web, 18 browser, 106 sweep, 27 canon and
1,116 repo guards. Hardware microphone/recording use remains unobserved.
C7/C8 is on the running desk. The owner's existing drawer and its three
members were observed read-only at both sizes after Q8/Q10, without page errors.

ST1 #1347 gives Rhythm, Wallpaper and Calendar one Settings home, preserves
old doors and unifies quiet hours. Recovery fixed a real phone defect: two
44 px stepper arrows left no room for the value. Its two-size browser test
fails on the old CSS and passes after the fix, including a saved Increase
press. The initial broad check passed 4,062 related web and 1,383 affected
pytest checks but found two stale browser selectors. After updating the
Engines navigation assertion, the final incremental quick check is green:
18 browser, 106 sweep, 27 canon and 1,116 repo guards. ST1 is on the
owner's running desk; Rhythm is observed at 1440/393 without page errors.

Q9 follow-up #1365 uses declared operations through HTTP and MCP, with Edit
and Dismiss before Confirm. Dismissed rows stay dismissed. Quick check:
118 related web, 6,457 affected pytest (7 skipped), 106 sweep, 27 canon,
1,116 repo guards. Q9 is on the owner's running desk.

AG10 #1367 recovers the local fixes absent from superseded #1364. A real-hub
fake-agent walk reads a meeting through MCP, commits a file and shows Done,
one file changed, branch and Looked at at 1440/393. Quick check: 142 related
web, 243 affected pytest, 106 sweep, 27 canon, 1,116 repo guards.

P3 #1350 gives the project Now wing its state and reason, head facts,
owner actions, Waiting on by person and This week with source links.
Recovery carries each confirmed decision's source meeting through the wire
and renders its chip. Current isolated-hub shots show the populated head
facts at 1440/393; the original recovered seed also shows owed items and the
confirmed decision. Broad check: 4,083 web passed with one old People test
checking folds before Prep completed, 2,233 pytest passed (2 skipped),
106 sweep, 27 canon and 1,116 repo guards. The asynchronous assertion now
waits for the folds; final incremental check is green: 40 web, 106 sweep,
27 canon and 1,116 repo guards. P3 is on the owner's running desk; runtime identity and four HTTP checks pass.

ST2 #1346 recovers truthful Accounts states, Found on this Mac, Use and
Remove/Undo. Check restores the previous Jira/Confluence acli profile. Four
recovery tests failed before the fix when restoration returned nonzero or
raised; the service now persists and returns the plain restoration failure.
Provider behavior is exercised with an isolated stub. Broad check: 4,069
web and 385 pytest passed; the sweep hit an intermittent People brief 503.
The final incremental quick check passed 335 pytest, 106 sweep, 27 canon
and 1,116 repo guards. The People 503 remains open; this retry does not
prove it fixed. ST2 is on the owner's running desk; runtime identity and four HTTP checks pass.

Q8/Q10 #1368 recovers the phone note footer and existing Knowledge
collections as named drawers, including members, About chips and the
Filed strip. The old New Knowledge verb is parked; stored data and tools
stay. The old menu-doc PR #1355 is incorporated and WEB_DESK.md now describes
the current desk. Broad check: 4,241 web, 547 pytest, 106 sweep and 27 canon
passed; one stale atlas guard failed. After updating the mutable cases and
filing vocabulary, final incremental check passed 194 web, 106 sweep,
27 canon and 1,116 repo guards. Four real-hub atlas walks pass at 1440/393:
find an existing drawer, and add/remove a decision without removing the
decision. Populated drawer and About-chip shots were also inspected at both
widths. After merging delivered P3/ST2, the final merge check is green:
106 sweep, 27 canon and 1,116 repo guards. Q10 awaits deployment;
live-engine answers remain unverified.

**Initial recovery snapshot — owner ruling 2026-10-19.**
Batch seven stopped at Claude's usage limit. At recovery, main had 69 of
117 slice implementations merged and the desk served batch six at
`b8908dc72` (runtime identity checked). Eight betterment PRs were open:
#1346, #1347, #1349, #1350, #1355, #1363, #1364 and #1365.
Local-only commits and unfinished edits are preserved in their original
worktrees. In particular, AG10's latest fixes are not on its PR branch;
Q11, AG11 and the remaining atlas repairs are uncommitted. The four confirmed failures are repaired in this recovery PR: API
markdown/manifest parity and three recorded-wire checks in People/Today.
The hub re-records its own answers; the Today face checks keep the task in
its correct Needs-you home. Focused validation: four pytest checks and 28
Today/People web checks pass. Pending-PR recovery and delivery continue. This is not a completion or owner-acceptance claim.
Exact recovery map: `docs/internal/betterment/RECOVERY-2026-10-19.md`.
Codex owns delivery for this task at the owner's request; implementation
workers hold for SHIP and Codex verifies and merges.

**Betterment batch six — delivered 2026-10-18 (main `b8908dc72`).** The
desk's tools are complete (7 of 7): M5 #1330 (HTTP engines get the Ask
palette, at most 10 passes), M6 #1331 (`provider.github_pr_get`, MCP only).
Ask: Q3 #1332 (Search asks; one section per kind; plain memory rows),
Q5+Q6 #1335 (one verb, Ask about this; the Room's field asks in Ask; About
shortcuts, chips, drop on Ask; Send… under an answer). Agents: AG3 #1333
(the desk's answers visible, a choice typed as the bare number), AG4 #1334
(hand from the front window, Needs you More and Search; a sentence; branch
from the title). Daily: D5 #1336 (Brief and The week windows retired; old
desks reopen on Today), D8 #1337 (notices only for what needs him; morning
notice; 1:1 prep notice; held while Today/Needs you is in front; People
503 on an empty store fixed; "People is not set up on this Mac"). The
owner's first real automation on a real engine worked. Reds on `f6b0c1be0`
(FAST 6, browser 4 + 2 import errors) fixed forward in #1338: three real
defects (stale MCP verb catalogue, missing face words, a global
`document.querySelector`), the rest stale. Web baseline green. Desk hub
restarted from `wt-desk-betterment-20261018d`; 4 checks 200; backend
`b8908dc72`. Slices: 60 of 117 (`docs/internal/betterment/TRACKER.md`).

**Betterment batch five — delivered 2026-10-18 (main `87e1f742c`).** Automations,
Engines and the desk's tools are complete as designed. A6 #1322 (Put it in;
new results on Today and the Dock; Run-now race; "automation" in refusals),
A8 #1325 (New Workflow parked), A9 #1318 (old automations show their tasks;
Make this one automation), A10 #1324 (an agent reads a folder, read only;
a made-one prompt goes once), E6 #1320 (one name, Engines; Try it on more
rows), E7 #1323 (pi and Gemini CLI engines), M3 #1319 (automations on MCP;
memory call without tools; cadence reads confirmed promises), M4 #1321
(engines on MCP). Reds fixed forward: #1327 (all stale expectations; no
regression; Codex agent launches still mount the Conductor palette).
Owner report fixed: #1328 — macOS "A keychain cannot be found" popups came
from test hubs with a scratch HOME asking the Keychain (made frequent by D6);
the key stores now refuse before asking when HOME has no keychain.
Verified on `c8401c507`: browser 346 passed; FAST 7 / web 1 red, fixed in
#1327 (quick check + web baseline green). Desk hub restarted from
`wt-desk-betterment-2026-10-18b`; 4 checks 200; backend `87e1f742c`.
Slices: 52 of 117 (`docs/internal/betterment/TRACKER.md`). Next: the
owner's walk — one real automation on a real engine.

**Betterment batch four — delivered 2026-10-18 (main `eff269a6b`).** A5 #1309
(one About picker, by name, shared with Ask; drop a note or meeting; event
subject), A7 #1314 (Automations home, one row each; four starters; schedules
saved Off; the §6 Friday-update job in 5 presses at 1440 and 393), E4 #1311
(Add an engine by kind: service / agent on this Mac / server on my network /
model on this Mac / another HoldSpeak; Anthropic supported), E5 #1315 (What
runs where: one row per job, Try it, Undo; the switchboard behind Builder
tools; speech never routes to a chat engine; no retry on CLI timeout; budgets
follow the engine's real context; plugins follow the summary's engine),
D6 #1312 (People suggested from meetings, 1:1 series and Jira; Who are you?),
D7 #1313 (1:1 prep: owes me / I owe with Nudge and Done; last time; folds),
AG5 #1308 (working at once, default 6, a queue), AG6 #1310 (Resume after a
restart, Resume all). Reds fixed forward: #1316 (incl. a real launch-ledger
race: concurrent read-modify-write lost the "registered" state).
Verified on `f9a6ce2af` before the fix: FAST 4 red, web 0 branch-new, browser
13 red; all 17 fixed in #1316 (109/109 on the failing files). Desk hub
restarted from `wt-desk-betterment-2026-10-18`; /health, /, /conductor,
/models 200; backend `eff269a6b`. Not walked by eye yet.
Progress: ~52 of 117 recipe slices merged.

**Betterment batch three — delivered 2026-10-18 (main `873c95627`).** A4 #1304
(When and With edit in place: plain schedules with Next, GitHub event starts,
engine picker with one-press Add, spend limit per automation; engine change
re-freezes a live schedule), M2 #1301 (each result shows Looked at / Wrote /
Prepared from the hub's own call record, plus cost), Q4 #1302 (one Ask window;
every Ask is a thread; the Thread window parked), Q7 #1305 (Ask uses the desk's
tools on tool engines; Wrote with Undo; holds with Allow once / Deny; sends
only prepared), D4 #1303 (Today is one page; the brief made without a press).
Reds fixed forward: #1306 (incl. the thread tool-gate census and 3 new safety
tests: an Ask/Thread can never turn on a schedule or change an engine).
Verified: FAST 16,515 passed / 0 failed; web 0 branch-new; browser green.
Desk hub restarted from `wt-desk-betterment-20261018c`; 4 checks 200; backend
`873c95627`. Not walked by eye yet.

**Betterment batch two — delivered 2026-10-18 (main `8f46d9867`).** A3 #1293
(the Automations window: When/Do/About/With/Put it in, results below),
E3 #1294 (model picker, one engine per model, real context size), AG1/AG2
#1292/#1295 (Agents name; one-press Answer/Allow with the command shown),
D2/D3 #1291/#1296 (Needs you filters and one verb per row; promises kept on
arrival with Drop/Undo; a re-summary never revives a dropped promise).
Reds fixed forward: #1298 #1299. Process: quick_check gained a ~50 s
"repo guards" step (#1297) so census/ratchet reds stop reaching main.
Verified on main before delivery: FAST 16,491 passed (the one red fixed in
#1299), web 5,543 / 0 branch-new, browser 348 passed. Desk hub restarted
from `wt-desk-betterment-20261018b`; /health, /, /conductor, /models 200;
backend `8f46d9867`. Not walked by eye yet.

**Betterment build — delivered to his desk 2026-10-18 (main `ee6f42227`).**
All 38 decisions adopted ("defaults"). Merged since the designs: P0 #1253,
A0 #1256, C1 #1255, C2 #1258, S0/S1 #1257/#1259, Q0 #1260, ST0 #1261,
AG0 #1262, Send S1 #1268, Q1/Q2 #1267/#1269, A1 #1270 (Automations name),
E1 #1273 + M1 #1278 + E2 #1279 (Claude Code / Codex as engines with the
desk's tools, spend limits), C3/C4 #1271/#1275, D0/D1 #1264/#1277, A2 #1280,
P2/P1 #1276/#1283; M0 live CLI check #1266. Fix-forward of the reds these
caused: #1263 #1272 #1274 #1281 #1282 #1284 #1285 #1286 #1287 #1288 #1289.
No main watcher was running; the orchestrator ran the full suites itself:
FAST 16,449 passed / 0 failed; web 5,515 passed / 0 branch-new; browser
suite green after #1287–#1289. Desk hub restarted from
`wt-desk-betterment-20261018` (Python 3.12, all extras), port 8765;
/health, /, /conductor, /models answer 200; runtime reports backend
`ee6f42227`. Not walked live by eye yet. Open items:
`docs/internal/betterment/FOLLOWUPS.md`.

**Betterment: every cluster designed (owner, 2026-10-17).** The master plan
`docs/internal/betterment/PLAN.md` covers all 45 features in 10 clusters
under one product model. Eleven job-first designs, each with a live walk,
code map and recipe, are on main. Every owner decision is on one page:
`docs/internal/betterment/DECISIONS.md` (38, each with a default). Truth-fix
slices that need no decision start at once.

**#1253 merged:** Draft update no longer freezes the hub (model call off the
event loop) and a failure says why in the Room, with Try again.

**#1248 merged:** `/api/setup/discover-models` sends the environment
`OPENAI_API_KEY` only to `https://api.openai.com` (found by the Engines map).

**Daily work: readable documents and useful save/return paths — #1247.** Decision now
keeps unfinished writing across close/reload and clears only acknowledged
fields. Ask gives the answer more room, opens its exact saved artifact and
preserves the question/context on return. Thread commands are searchable with
bounded choices and working keyboard selection; Keep/Retry exposes the exact
saved note without losing the reply draft. Shared Workbench materials remain.

279 focused checks pass. Ordinary quick GREEN:4,167 related web,109 sweep and17 canon. Actual isolated1440/393 walks cover creation,
draft recovery, answer editing, exact save/open/return and keyboard/focus;
Ask's provider reply is declared replay. Independent review caught and closed
background Escape and missing Retry continuation. The release check, merged
head, formal review and idle delivery are retained in the
[release record](../docs/internal/DAILY-DELIGHT-2026-10-17/RELEASE.md).
[Exact merged verification and local delivery](https://github.com/karolswdev/HoldSpeak/pull/1247#issuecomment-6243418855) are updated after merge.
Owner aesthetic acceptance is open. Prior Room phone review and People503
findings remain explicitly tracked; this UI pass does not claim to fix them.

**Daily usability: Decision, Ask and Thread — #1243/#1244 delivered.** The
owner's three named faces now share content-led Workbench paper, compact
controls and useful phone layouts. New decision starts in the decision editor.
Ask retains an answer while editing, separates sent and question sources, and
carries a saved Note/passage independently of desktop icon selection. Thread
exposes Sources and Commands without losing drafts, bounds expanded details,
names command actions and keeps Stop explicit while writing.

Actual isolated desktop/phone walks cover creation, reading, editing and
expanded source controls, including real pointer ownership and picker focus.
Ask uses a declared recorded provider reply. Ordinary quick GREEN:304 related
web,12 affected browser,109 sweep and17 canon. Astra formal review RATIFY.
Merged product `ac55cd318` full run: **16,697 passed,1 failed,26 skipped,
1 expected failure**, plus3 mandatory live-bus passes. Its sole stale atlas
source anchor is corrected; all26 anchor checks pass. The next full run
reproduced recall contention before any chat turn (code5, SQLITE_BUSY). A
deterministic fresh-connection regression now proves the cause: empty vector
deletion starts a deferred transaction before first-use FTS preparation. The
minimal no-op guard is fixed forward; exact verification is linked below.
[Final merged verification](https://github.com/karolswdev/HoldSpeak/pull/1244#issuecomment-6239495252) retains the exact subsequent head
and result; the previous run is not called green.

The idle local hub serves build `22aa76d6327046a1` from
`wt-daily-recall-delivery-20261017`, PID82970, port8765 (before the next delivery); source/build agree and four
HTTP checks pass. The actual printed Desk address was opened. Owner visual
acceptance and live provider/native behavior remain open.
[Design, release, evidence and limits](../docs/internal/DAILY-EXPERIENCE-2026-10-17/RELEASE.md).

**Tonight: three daily repairs complete — #1240/#1241 delivered, full-main GREEN.**
Send retains the exact command and preview through reload; Retry cannot turn
that press into a second delivery. Meeting outcome publication resumes saved
results without inference, and Confirm/Done retains the exact action through
reload, including historical unlinked confirmations. Workbench refuses missing
explicit sources before dispatch and preserves sources/context on Re-run.
Paired1440/393 runtime observations and failing-before/passing-after checks
cover all three. The full-main SQL coverage finding was fixed forward without
changing its ceiling or transaction behavior.

Final merged product`8277534ea`: **16,671 passed, zero failures,26 skipped,
1 expected failure**,670.76seconds; mandatory live bus3 passed in24.00seconds.
The12 warning types and optional/native/provider/harness skips remain explicit.
Ordinary quicks, TypeScript,75 doc guards and27 atlas checks pass; source/build
`426015d9eee42d70`. [Astra review](https://github.com/karolswdev/HoldSpeak/pull/1241#issuecomment-6231273159)
RATIFY. Idle local delivery from `wt-tonight-release-record-20261017`, PID30260,
port8765; health/Desk/Conductor/Models200. Owner acceptance and real external
provider/native execution are separate. The unexplained first sweep503 remains
tracked below; later sweeps pass.
[Release, exact evidence and limits](../docs/internal/TONIGHT-THREE-2026-10-17/RELEASE.md).

**Full-main recovery — GREEN, #1238 delivered (2026-10-17).** Merged product
head `00025d6f6` completes the isolated local full suite: **16,580 passed,
zero failures,26 skipped,1 expected failure**,516.12seconds; mandatory live bus
separately passes3 in24.05seconds. JUnit reconciliation accounts for all116
tracked identities:113 exact passes and3 retired Dock cases whose four recorded
replacements pass; no unresolved case. Actual Mermaid rendering also passes.
The12 warnings and native/provider/harness skips remain explicit in the linked
record; remote nightly is pending. This is local full verification, not a
claim of physical audio/provider execution or owner visual acceptance.

The preceding main `add3c231c` ran to
completion: 3 failed / 16,571 passed / 27 skipped / 1 expected failure, plus
3 mandatory live-bus passes. R093 reopened on the runtime module budget;
R114/R115 now track crash recovery discovery and a transiently missing PR
receipt. The caller/helper split is AST-equivalent and passes27 scoped checks;
the receipt's atomic publication passes its original real-hub case plus a
deterministic before/after boundary regression. Meeting audio sealing and final
checkpoint recovery pass97 checks with the real SIGKILL proof and exact audio
retained. The release check exposed a midnight-dependent Brief test (R116);
its controlled event/assignment clock now passes all126 service checks without
changing production staleness. Combined ordinary quick GREEN:727 affected /
109 desktop-phone sweep /17 canon;28 doc guards pass. Merged `00025d6f6`;
[formal Astra review](https://github.com/karolswdev/HoldSpeak/pull/1238#issuecomment-6230527009)
RATIFY. Idle hub delivered from `wt-meeting-stop-module-20261017`, PID61678,
port8765; health/Desk/Conductor/Models200. Frontend `2759d0c6c13d4b6b` equals
source. Verification and delivery name the same product head.
[Follow-through](../docs/internal/MEETING-STOP-NATIVE-2026-10-16/MODULE-FOLLOWUP.md).

**Meeting Stop — #1237 delivered (2026-10-17).** Postmerge review reproduced two
additional paths: cleanup-worker launch failure hid an unclosed device, and
a delayed duplicate Stop overwrote Saved with Saving. The bounded corrections
preserve audio/save/floor custody and admit one runtime Stop before visible
effects. Three regressions fail before repair; all 18 owned checks now pass
with real isolated DB/journal rows and controlled native streams. Ordinary
quick GREEN: 120 affected / 109 sweep / 17 canon; 28 doc guards pass.
Merged `add3c231c`; formal Astra review RATIFY with the subsequent full-run
findings above fixed forward. Idle local hub delivered from
`wt-meeting-stop-review-fixes-20261017`, PID25584, port8765; four HTTP checks
return 200. Frontend `2759d0c6c13d4b6b` matches source; backend head is named
separately. Actual driver recovery is unverified.
[Follow-up](../docs/internal/MEETING-STOP-NATIVE-2026-10-16/POSTMERGE-FOLLOWUP.md).

**Thought and Send — #1236 delivered (2026-10-16).** A lost Send answer followed by
Back and a newer note edit showed new text above Retry for the old command.
The shared Send well now retains the original preview with its pending command;
Retry recovers the same send, and a distinct Send again uses the newer words.
Real local file/row/return checks pass at 1440/393. The final recovery tape
finished with **1 failed / 16,514 passed**: the Thought test asserted a footer
while the frame still loaded. Its deterministic held-read check now proves
exact buffered text, focus and send custody. New Project create/reopen/reload
also passes with one exact project row. The historical queue now includes
113 distinct cases, including a previously unrecorded long-context case from
the earlier runtime tape. Ordinary quick GREEN: 4,119 related web / 17 Thought
browser / 109 Desk sweep / 17 canon. Source/build `2759d0c6c13d4b6b` agree.
Merged main `20f6113b5`, formal Astra review RATIFY; the idle local hub serves
that exact build from `wt-thought-send-recovery-20261016`, PID20767, port8765.
Four HTTP checks return 200. Full-main follow-through is the active next check.
[Continuation and proof](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/THOUGHT-SEND.md).

**Night Train fidelity — #1235 (2026-10-16).** Corrects the rejected #1234
scene: supported curved book pages, steady camera, actual multisampled
postprocessing and bounded retina resolution; connected mountain relief with
upward normals/closed edges; masonry station, pitched roof, braced canopy,
recessed windows and framed lanterns with warm pools/shadows. Updated real GL
picker still. Quick GREEN:4,146 related web /109Desk sweep /17canon;24focused
checks and TypeScript pass. Real1440/393 picker selection/Close/reload walks
pass on actual MetalM2Max, with renderer identity in provenance. Build
`3ebdb08ab76ecc2b`; live delivery follows merge. Root inspected raw edge/station
crops and continuous moving frames; interior crops remain pixel-stable.
Owner aesthetic judgment and formal Muad’Dib postmerge review remain open.
Tooling debt: unforced graph persistent Chromium uses SwiftShader; its10s
interaction timeouts remain recorded, software responsiveness is not claimed.
[Review and limits](../docs/internal/NIGHT-TRAIN-FIDELITY-2026-10-16/VERIFICATION.md).

**Night Train — #1234 (2026-10-16).** Close seated compartment, walnut and
emerald fabric, warm reading lamp, ceramic cup and open book, actual subtle
glass reflection and fine rain. Outside: shaded mountain relief, lake glints,
clustered firs and passing station lights on a platform. Tree flow follows its
ground. Desktop/phone compositions and reduced motion/resize are checked in
actual GL; final real picker walks pass at both widths. Quick GREEN:4,133
related /109sweep /17canon; final test-only delta GREEN:4related /109sweep /
17canon;11focused checks and final TypeScript pass. Build `e3f7871900a082c1`.
The actual rendered first frame supplies the picker/fallback still. Local M2Max
frame measurements are recorded; actual phone hardware and owner aesthetic
judgment remain open. Formal postmerge review remains open.
[Review and limits](../docs/internal/NIGHT-TRAIN-2026-10-16/VERIFICATION.md).

**Meeting stop — #1233 delivered (2026-10-16).** The owner's Stop
hung in CoreAudio and blocked the web event loop. Stop now runs off the loop;
PCM admission closes atomically, audio finalizes before slow downstream work,
and both native streams clean up independently under one bounded deadline.
A device cleanup failure preserves the save result and keeps the audio floor
unavailable until restart. Same-ID saving, concurrent Stop, callback cutoff and
responsive API checks pass: 51 focused tests; quick GREEN 125 affected / 109
sweep / 17 canon. Independent source counsel found no blocker. The owner's
interrupted meeting and its complete audio were recovered; Desk is responsive.
Delivered from merged main `c76fbb892` on the verified idle hub; base model
loaded with no error and global hotkey available. Actual driver recovery is
not claimed. Formal postmerge review remains open.
[Build and limits](../docs/internal/MEETING-STOP-NATIVE-2026-10-16/BUILD.md) ·
[Recovery](../docs/internal/MEETING-STOP-NATIVE-2026-10-16/RECOVERY.md).

**Physical moon sizes — #1230 (2026-10-16).** Owner feedback supersedes
visibility enlargement. All eight natural moons in Mars/Jupiter/Saturn use
NASA/JPL physical radius ratios. Actual irregular Mars mesh volume is normalized;
shadow/haze inputs shrink with body radii. All three picker/fallback stills are
regenerated. Combined build `0ce82ada178bf199`; quick GREEN: 4,154 web / 705 affected /
109 sweep / 17 canon; TypeScript and 32 focused checks pass. Six actual GL
compositions cover desktop/phone; two real Mars picker readiness walks pass.
Orbit spacing/time remain authored. Independent source counsel found no blocker;
Delivered on the recovered idle hub, build `0ce82ada178bf199`; formal postmerge
review and owner judgment remain open.
[Correction and proof](../docs/internal/ORBITAL-PLACES-2026-10-16/SCALE-CORRECTION.md).

**Browser recovery — #1231 delivered (2026-10-16).** Activity owns Finished
receipts with exact source doors, readable phone titles and one-Back return.
Phone swipe/Depth, Capture/Today, Go toggle, record-window identity and Chair
geometry are repaired. Room claim contrast is 17.12:1 at both widths (1.03:1
before). Broad quick GREEN: **4,169 web / 183 affected / 109 sweep / 17 canon**.
Final Activity delta quick GREEN: **4,117 related web / 109 sweep / 17 canon**;
TypeScript, 639 graph checks, actual layout/return and counterfactual readability
proof pass. Merged `9079a4be2`; formal Astra postmerge review RATIFY. Idle-hub
delivery serves build `372447f4cba801bb`, PID 16443, port 8765, with source/build
agreement and four successful HTTP checks. The later #1232 full run reached 16,514 passes and reopened R071 only;
the active continuation above repairs that readiness check and records the
additional R113 identity from the older #1228 tape.
[Queue and limits](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/REGRESSION-RECOVERY.md) ·
[Delivery record](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/POSTMERGE-RECOVERY.md).

**Orbital places — #1229 (2026-10-16).** Change places adds live Mars with
Phobos/Deimos and Saturn with layered rings, Titan/Enceladus. Local terrain/sky,
actual rendered picker/fallback stills, existing motion/visibility controls.
Final build `37302e41750eb272`; quick GREEN: 4,105 web / 705 affected / 109
sweep / 17 canon; TypeScript passes. Actual isolated 1440/393 journeys prove
selection/reload, moving frames, drawer input, pause/reduced motion and Quiet
cleanup. Four real graph readiness cases pass; unavailable-WebGL fallback is
observed for Mars desktop and Saturn phone. Independent scene counsel finds
no blocker. Formal postmerge review and owner visual judgment remain open.
[Design, credits and verification](../docs/internal/ORBITAL-PLACES-2026-10-16/README.md).

**Runtime recovery — #1228 delivered (2026-10-16).** Each hub owns its
last-known store, so an earlier bare service cannot bind its recall to another DB.
LAN discovery admits a frozen target set before transport and rejects late model
bodies; calendar checks observe completed capture and stop their timers. Focused
proof: 254 memory/calendar checks and 59 scanner/effect/route checks pass; three
new late-body regressions fail before the fix. Ordinary quick GREEN: **575 affected /
109 sweep / 17 canon**. Desktop/phone shots inspected; source/build match
`f6ef8ac2099dde8b`. Merged `58a0d4552`; formal Astra postmerge review RATIFY.
Idle-hub delivery was delivered on port 8765, PID 76313; all four HTTP checks return 200.

**Recovery copy — #1227 delivered (2026-10-16).** Commands recovers an uncertain
Add by GET and edits the saved row without duplicates or lost newer fields. Read
failures keep shown material; Models reports pending initial reads. Quick GREEN:
**4,076 web / 16 copy / 109 sweep / 17 canon**; TypeScript passes. Actual Commands
recovery at 1440/393 and three held-read Models cases pass. Merged `e834f2c5b`;
formal Astra postmerge review RATIFY. Build `f6ef8ac2099dde8b`, PID 63584, was delivered
on port 8765; health, Desk, Conductor and Models return 200.

**Regression contracts — #1226 delivered (2026-10-16).** Brief fixtures pin
presentation timezone; bounded memory score roundoff preserves exact same-process
retrieval. Wire fixtures match producers; CI retains historical regression commits.
Meeting context extraction preserves consumption order; SQL shapes and stale guard
records are corrected. Quick GREEN: 579 affected / 109 sweep / 17 canon (one existing
expected failure), plus 11 wire-consumer checks. Merged `5c26bd0fa`; formal Astra
postmerge review RATIFY. Build `08b3ac3cbb13ef50`, PID 33619, was delivered on port 8765;
health, Desk, Conductor and Models return 200. Desktop/phone shots inspected.

**Journal recovery — #1225 delivered (2026-10-16).** Concurrent stores reserve
sequence and prior hash under SQLite’s write lock; failures release the local
lock and roll back. Merged `f6871e8df`; formal Astra postmerge review RATIFY.
Quick GREEN: 44 affected / 109 sweep / 17 canon. Build `6e3600ca4e4d1251` is
the prior delivery on port 8765, PID 28926 (superseded by #1226); health, Desk, Conductor and Models return 200.
Three regression checks fail on the original implementation and pass fixed.
The wider recovery queue remains active.

**Broader regression recovery — delivered; full-main follow-up pending (2026-10-16).** The owner expanded the
work to resolve the full-tape failures. All 112 distinct failing cases across the
five completed tapes are now tracked with fix ownership and next proof in
the [recovery queue](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/REGRESSION-RECOVERY.md).
The latest completed tape (#1226, before later repairs) has 82 failures / 16,400
passes; every failure is already in the queue. Copy, runtime and browser repairs are
delivered, including the additional Room ink and Activity title findings. #1231
full-main is queued and #1228 is in progress. Inherited status does not close a case.

**Owner desktop density feedback — #1223 (2026-10-16).**
Artifact footer actions retain vertical clearance on first open and through
resize. Desktop Dock is 60 px with 24 px art; Screen art 48 px with tighter rows.
Window movement reaches the actual 28 px top bar (phone 44 px). Shared reading
renders checklist children and retains compact task text. Verified build
`ca987454c0b44162`; quick GREEN: 4,168 web / 109 sweep / 17 canon, typecheck/tokens pass.
Actual 1440/393 walks cover 400/600/320 px windows, drag/resize/reload, exact Copy,
footer hit points, phone More and unchanged artifact content. Independent Sol
counsel RATIFY. [Direction and verification](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/FOLLOWUP-DENSITY.md).
Merged as `6788a92f1`; normal idle-hub delivery was delivered on port 8765, PID 96844.
Formal Astra postmerge review RATIFY. The earlier B full tape is red; its two
attributed wire-fixture mismatches are corrected in #1224. Broader inherited
and unattributed failures remain.
[Postmerge delivery record](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/POSTMERGE-DENSITY.md).


**Flagship daily work, creation and recovery — #1221 (2026-10-16).**
People Prep inspects either exact commitment, preserves newer Add drafts and
empty-edit focus, and gives phone fields a full row. Project promotes pending
Review. Thread retains `/todo` commands through pending/refused/unknown results,
return and reload; caret-zero Enter cannot invoke an unrelated slash command.
Ask/helper reads have exact Retry. Remote separates failed reads from named
unconfirmed writes and keeps draft/row state on GET-only Reload.
Final quick GREEN: 4104 web / 109 sweeps / 17 canon; TypeScript, atlas and
generated-doc checks pass. Actual desktop/phone/narrow daily, task/Keep and
Remote recovery journeys pass, with real producer readbacks and declared
failure/recorded-material boundaries. Build `a7145045f5dbab3c` matches source.
[Delivery and evidence](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/DELIVERY-CDE.md)
and [all-family coverage](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/COVERAGE.md).
Merged as `14ae17b68`; normal idle-hub delivery was delivered on port8765, PID79705,
with exact merged/source/build agreement. Formal Astra postmerge review RATIFY:
[release record](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/POSTMERGE-CDE.md).
Full main tape 38950387547 (B) completed red: 103 failures / 16,327 passes,
with 96 failure names shared with the preceding tape. This forward fix aligns
the two follow-through wire fixtures with their real nullable hold fields;
the isolated producer fences and 32 web consumer checks pass. CDE tape
38957119404 remains in progress; no full-tape green is claimed.
Owner density feedback was delivered by #1223, build `ca987454c0b44162`,
PID 96844 on port 8765; formal Astra postmerge review RATIFY.
[Delivery and fixture follow-up](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/POSTMERGE-DENSITY.md).
Owner live judgment remains separate.
The bounded kickoff implementation/delivery is complete; every parent family
has explicit current/carried/unknown coverage. `/todo` remains non-idempotent:
explicitly sending again after an unknown result can create another task.
The inherited graph census debt and native/provider/external-operation limits
remain named. No whole-product aesthetic acceptance is claimed.


**Flagship Brief/source reading — #1220 (2026-10-16).**
Brief prioritizes standing answers/changed work, Day the next meeting, and
Memory title/meaning. Explicit citations inspect exact held tasks and pending
or rejected outputs without changing snooze/review state or public-list rules.
Source-local failure/Retry, retained Brief Send/scroll and task drafts are
implemented. Full Material/AgentWords share Markdown headings/lists/tables/code;
new captures retain original line structure. Old flattened text is not rebuilt.
Independent Sol counsel findings were fixed, including delayed Assign A reading
current B rather than replacing it. Actual isolated phone/desktop journeys
prove assignment persistence with the hold, pending output state, Codex asks
rendering, failed-read recovery and return. Verification/release identifiers
are in [Delivery B](../docs/internal/FLAGSHIP-EXPERIENCE-PLAN-2026-10-16/DELIVERY-B.md).
Normal local delivery follows merged tree/build equality. Formal postmerge
review, full main tape and owner aesthetic acceptance remain separate.
Release quick GREEN:4185 web/1599 affected Python/109 sweeps/17 canon;
build`c15a5e7c1ef79062`. The connected C/D/E continuation is delivered in #1221 above. Healed work is preserved; this first delivery
does not declare the whole product aesthetically accepted.


**Cohesive Desk entry — #1219 (2026-10-16).** Phone launchers use the
existing paper/ink menu material with clear Apps/Projects/Drawers/New sections;
long names wrap and native activation preserves exact destinations. Presence
uses the shared Workbench material, shows complete activity text and returns
to Desk with query/auth intact. Get ready's existing composition and real
Continue later handoff are preserved. Complete quick GREEN:287web/651affected
Python/109sweeps(noexpectedfailures)/17canon; TypeScript, generated docs and
graph join pass. Actual eight-state desktop and ten-state phone walks pass on
build1db394185ca801fe; five phone native opens reach exact stored destinations
once, all36desktop/63phone hit+pointer samples own and full long text fits.
Official Presence→Desk graph passes both widths. The final paired proof closes
the entry gaps from the completion audit; no further concrete UI blocker is
established in this finite pass. Normal owner hub deployment follows exact
merged tree equality; root records delivery privately. Owner live judgment,
formal postmerge review and the main tape outcome remain separate. Inherited
Presence can retain the last producer label after disconnect while the lamp
turns off; runtime mapping is unchanged. This does not claim all provider or
native hardware states. [Proof and limits](../docs/internal/COHESIVE-DESK-ENTRY-2026-10-16/README.md).

**Cohesive conditional controls — #1218 (2026-10-16).** Library Thread
replay/Rails/phase Story controls keep native activation and exact identities;
phone Rails sits above the Dock. Ask has one completion receipt, honest zero
grounding and named cached citations with complete long-title wrapping.
Resourcefulness has visible routine choices, concise limits, stored progress
and exact Save/Retry labels. Capability preserves multiline material and the
shared Pad appends late speech to current edits. PR draft outcomes are readable
without claiming accepted agents started. Armed Review Edit+Defer fits narrow
surfaces; desktop footer Retry owns the bottom points while edge/corner resize
works. Complete quick GREEN:3963web/651affectedPython/109sweeps(noexpectedfailures)/
17canon; TypeScript and generated documentation checks pass. Actual paired
control/policy/Calendar tasks include real policy and ICS/config persistence;
exact graph Search→Delivery entry passes both widths. Build52f6ff3c43024642 has
the frozen product; unchanged earlier proof is explicitly carried forward.
Formal postmerge review and owner judgment are separate. The next entry scope
from this release is closed by #1219 above; its baseline found a clipped
Presence label and undersized phone return target while Get ready worked. [Proof and limits](../docs/internal/COHESIVE-EDGE-CONTROLS-2026-10-16/README.md).

**Desk navigation and calendar review — #1217 (2026-10-16).** Explicit
Search Close restores focus and preserves keyboard intent; same-title meetings
show date/time and attendees, retaining exact identities. Search mic and phone
chrome targets are proved healed, with only their obsolete exceptions removed.
Empty Context suppresses zero meters and stays null-safe; Needs fits three
complete phone rows. Calendar review uses readable library fields/ledgers,
stable typing focus, mounted pending/refused drafts, exact Retry and returned
source receipts. Failure stays beside Retry after scrolling. Complete quick
GREEN:3912web/697affectedPython/109sweeps(noexpectedfailures)/17canon; TypeScript
passes. Actual16phone/18desktop state walks on c52c05eebc4eb5fa include real
Context save, exact meeting GET/window scopes and corrected calendar ICS/config
writes. Search Close graph cases pass both widths. Formal postmerge review is
separate. [Proof and limits](../docs/internal/DESK-NAVIGATION-DELIGHT-2026-10-16/README.md).
Whole-app goal remains active: Thread replay/Rails action controls, Ask zero
grounding and Resourcefulness are being refined. Additional source findings
confirm Capability multiline material loses paragraph breaks on edit and PR
draft success prints an opaque operation ID. Actual desktop Retry bottom-row
pointer samples hit the inherited bottom resize edge; centre-click works,
phone 44 px samples allpass. This common frame seam is assigned next, preserving
resize and restoring full action ownership. Armed Review Edit+Defer phone fit
is still to observe. No target waiver or provider/audio acceptance claim.

**Cohesive workflows — #1216 (2026-10-16).** The whole-app audit fixes
Workbench Close/refusal/reopen and ordered drafts, exact Add/Coder Retry,
honest Conductor/Lane decisions and accepted-read recovery, policy Retry
ownership, selected account Recheck and latest reads, calendar A/B edits,
speech test ownership/floor release, People/meeting read recovery and Project
source partial outcomes. Active Thought context uses library material and
storage-safe local retry identities; Get Info resolves canonical kind/ID
lineage and opens the actual Note; New Project/common actions use the kit.
Actual desktop review caught a narrow attached-context footer, separately
corrected to readable context/action rows. Complete final quick GREEN:
4039web/672affectedPython/107sweeps(twoexistingxfails)/17canon; TypeScript passes.
Root read fourteen-state actual isolated task walks at 1440/393 on build
c5c94f74427b5104, real attach/detach refs/calendar saves, canonical source open,
and actual Search→NewProject graph entry both widths on preceding6655519build
with unchanged NewProject source. An intermediate phone picker timeout passed
exact reproduction and unchanged complete rerun; no waiver. Formal postmerge
review remains separate from bounded source counsel. The whole-app goal stays
active: Search Close/meeting identity/mic target, empty Context meters and
Needs spacing are the next bounded pass; Week zoom and populated calendar
snapshot remain to assess. [Proof and limits](../docs/internal/COHESIVE-WORKFLOWS-2026-10-15/README.md).

**Thread, Ask and notifications — #1215 (2026-10-15).** Shared Workbench paper
traffic and bounded question pads; measured Thread modes, pointer editing and
real load/reply recovery. Ask retries the exact submitted question/sources,
keeps their lineage, preserves newer typed/speech work, and closes a pending
local view without late updates. Existing notices share a bounded stack above
the Dock, full payload wells, reachable phone actions and reduced-motion pulse;
#1214 journal exclusion/dismissal remain. Actual Keep walk found and fixed the
artifact store rejecting canonical note sources. Quick GREEN: 3855 web /761
affected Python /107 sweeps (two existing xfails) /17 canon; TypeScript passes.
Root read twelve-state conversation and seven-state notices walks at 1440/393
on build228dd99cb87915de, actual Keep artifact prompt/refs, and real Search→Ask
cases at both widths. Inference/runtime frame replay boundaries are explicit;
no real model/mic execution claim. Source counsel and later root seam checks are
separately scoped. Broader whole-app audit is active, not closed by this pass.
[Proof and limits](../docs/internal/THREAD-ASK-REFINEMENT-2026-10-15/README.md).

**Attention dismissal — #1214 (2026-10-15).** Owner could not clear the
Dictation needs review popup, then challenged its usefulness. Read-only live
counts showed13 successful dismissals and19 identical warnings still queued.
Journal projections no longer interrupt through Qlippy; journal/Attention
records remain. Other-source Dismiss writes only the visible presentation,
then quiets historical popup backlog in that tab. Pending/refused writes stay
on the exact row with Retry; newer eligible attention can show. Quick GREEN:
300 web /66 affected Python /107 sweeps (two existing xfails) /17 canon;
TypeScript passes. Root read six-state actual isolated1440/393 interactions,
no-popup/reload, real visible-row dismissal with two untouched rows retained,
and a newer eligible source appearing. Source counsel RATIFY; four-row sampler
and storage-denied reload limitations are recorded. [Proof](../docs/internal/ATTENTION-DISMISS-2026-10-15/README.md).

**In Jupiter's orbit — #1213 (2026-10-15).** The owner asked for a large
Jupiter, passing Galilean moons and rare Pioneer sightings, then reviewed the
live scene and asked for a richer universe and flowing atmosphere. One lazy
Wallpaper/Places choice now has local NASA cloud/star maps, galactic dust and
layered stars, independent opposing cloud jets/eddies/storm circulation, four
moon spheres with transit shadows, and rare geometric visitors. Shared Motion,
reduced motion, visibility suspension and still fallback remain in use.
Final quick GREEN: 3821 web / 651 affected Python / 107 sweeps (two existing
xfails) / 17 canon; build and release TypeScript pass. Root read real amended
1440/393 product walks, moving frame samples, drawer hit/open, frozen Motion
and reduced-motion states, WebGL-disabled fallback and real Wallpaper graph
choice cases. Six old catalog-count tests were reproduced and corrected with
registry-derived membership/wrap/direct-link coverage, 21 focused passes; no
product change for that correction. Delegated source counsel RATIFY is
separate from formal postmerge review. [Proof and limits](../docs/internal/JUPITER-ORBIT-2026-10-15/README.md).

**Desk drawers and live wallpapers — #1212 (2026-10-15).** The owner asked
to restore actual drawers and interactive Three.js scenery on the current
Screen. Root folders now use canonical drawer icons and phone Go rows; real
children and members open in the existing contents window. Menu Open works,
legacy bare refs suppress only their resolved object, and filing cycles retain
a reachable root. Nested drawers show their real parent. The Screen mounts
the selected lazy Atmosphere behind its controls, keeps still fallback until
ready or on WebGL failure, and exposes the existing saved Motion setting.
Quiet allocates no scene. Final quick GREEN: 3798 web / 651 affected Python /
107 sweeps (two existing xfails) / 17 canon; build and TypeScript pass. Root
read actual desktop/phone folder and filing cases, changing pixels for all
eight scenes, Motion/reduced-motion checks and WebGL-disabled fallback.
Bounded delegated source counsel closed three findings in one fix round;
the final parent-caption correction is separately verified. No owner live
acceptance, hardware performance, full main tape or formal postmerge review
inferred. [Proof and limits](../docs/internal/DESK-DRAWERS-LIVE-2026-10-15/README.md).

**Decision readers and shared window seams — #1211 (2026-10-15).** Continued
the owner-directed Workbench refinement. Shared compact Send folds defer
ordinary preview/destination reads, keep prepared/history/failure discovery
and held Retry; prepared bytes remain frozen while ordinary decision previews
refresh after accepted field changes. Text Save awaits its writer, retains
refused/newer drafts, and keeps exact-value Retry. Front windows now cover
shared resize seams in paint and pointer ownership; exposed drag/key behavior
remains. Final quick GREEN: 3764 web / 651 affected Python / 107 sweeps
(2 existing xfails) / 17 canon; TypeScript passed. Root read actual 15-state
desktop / 13-state phone walks and real multiline Save graph cases with
pointer/native touch. Independent source counsel closed one pending Retry
mismatch. The wider run caught one older Room eager-preview test; its explicit
Send coverage retains exact record identity and one-well checks, 16/16 green.
No owner acceptance, provider dispatch, full main tape or formal postmerge
review inferred. [Proof and limits](../docs/internal/DECISION-DELIGHT-2026-10-15/README.md).
[Next refinements](../docs/internal/DECISION-DELIGHT-2026-10-15/NEXT-SURFACES.md):
duplicate speech controls, repeated Send heading and record source-fact grouping.

**Follow-through and attention surfaces — #1210 (2026-10-15).** The owner's
confusing Follow-through report drove a substantive Workbench pass: readable
populated date/review ledgers, full owner/date/source facts, direct actions and
inline assignment/date controls. Canonical Snooze works before collection;
represented decision/action mirrors are suppressed, including filtered reads.
Newer drafts and exact Retry survive refresh/lane moves; newly refused writes
scroll into view. People receipts stay in memory. Cadence rows use actual loop
writers. Brief keeps the latest selection and names late Retry subjects;
decision status uses explicit library choices, and paper readers show the
requested-record failure/recovery. Final quick GREEN: 365 web / 1335 affected
Python / 107 sweeps (2 existing xfails) / 17 canon; TypeScript passes.
Root read 14-state Follow and 11-state neighbor walks at each width, actual
isolated task/status writers, and official Snooze pointer/touch graph cases.
Independent source review RATIFY after the two neighbor fixes; root corrected
offscreen refusal feedback. An unchanged Engines stillness case moved 54px
once; exact replay and the final full sweep passed without a waiver. No owner
acceptance, provider/model execution, encrypted People store, full main tape or
postmerge review inferred. [Proof and limits](../docs/internal/FOLLOW-THROUGH-2026-10-15/README.md).
[Next targets](../docs/internal/FOLLOW-THROUGH-2026-10-15/NEXT-SURFACES.md): shared
divider overpaint, automatic Send preview, editor save/refusal and preview
freshness. These four findings are addressed by #1211 above.

**Opened Workbench and Accounts — #1209 (2026-10-15).** The owner's
opened-workbench/controls report drove a complete bounded pass: multiline
instruction composer, grouped Agent/Engines/Starts when, folded roster,
library mode/schedule cycles and paper item instruction/result material.
Known missing-engine Runs offers repair; Home counts real item states.
Shared Pad remeasures on width changes, fixing reproduced clipped text.
Accounts' wrapping status and provider actions fit; Add stays within its
provider row. Mounted Add forms keep refusal/Retry and drafts through
Cancel/sign-in detours for populated and empty providers. Existing writes,
source completion, priority, references and late-save fences remain.
Final quick GREEN: 4935 web / 709 affected Python / 107 desk sweeps
(2 existing xfails) / 17 canon; release TypeScript passes. Root inspected
16-state final production walks at 1440/393, actual isolated CRUD/Retry and
width resize; graph multiline Add passes at both widths. Independent Sol
source review RATIFY after one bounded fix re-check; its initially missed
Accounts lifecycle regression is recorded. No owner acceptance, native
provider health, microphone hardware, full main tape or postmerge review
inferred. [Direction, verification and limits](../docs/internal/ACCOUNT-WORKBENCH-2026-10-15/README.md).

**Continued surface refinement — #1208 (2026-10-15).** The five
remaining ranked targets now use the existing Workbench kit: Schedule,
email recipient editing, Room History, Knowledge membership and plain
session terminal handoff. Failed reads differ from empty results; real retry
restores work. Recipient edits keep saved keys and provider-specific presence;
full-width multiline fields clear their mic. Terminal replaces the long
report, restores unsent work on Back and handles new Speak requests directly.
Root inspected18-state production walks at 1440/393, actual isolated Schedule
and destination saves, local key Check/Retry, History recovery and Knowledge
member opening; graph Knowledge cases pass at both widths. Final quick GREEN:
3712web /651affected Python /107desk sweeps (2existing xfails) /17canon; build and release TypeScript pass. Independent Sol source review
RATIFY after two P2 fixes/recheck; root live corrections cover row specificity,
receipt clipping and shared Pad text clearance. No Muad'Dib check or owner
acceptance inferred. Full main tape/postmerge review remain separate.
[Design, focused proof, live verification and limits](../docs/internal/SURFACE-REFINEMENT-2026-10-15/README.md).

**Continued visual refinement — #1207 (2026-10-15).** After the shared
picker release, two bounded audits and actual production captures drove a
repair pass across Tool Inspector, Thread questions, Agent editing,
Workbench results/read recovery and compact Calendar selection. Existing
library species supply named inset sheets, populated field labels, typed
answers, local actions and one result reader. Exact GitHub repository and
proposal identity stay visible; distinct outcomes/egress use the footer.
Runs/Memory failures no longer claim empty, and retry rereads their own
resource while retaining known content. Stored mint_attempted reaches the
wire, proved through real runner/publication. Calendar chooser remains
visible and keeps URL entry with an existing source. Final quick GREEN:
3685web /896affected Python /107desk sweeps (2existing xfails) /17canon;
release TypeScript/build pass. Root read13-state production walks1440/393,
real Agent Done flush and Calendar recovery graph/native-touch393. Independent
Sol source review RATIFY after one destination fix/recheck; root live caught
and fixed Inspector structural positioning. No Muad'Dib check or owner
acceptance inferred. Next source candidates and runtime limits are below.
[Design, audit, focused proof, live evidence and limits](../docs/internal/VISUAL-REFINEMENT-2026-10-15/README.md).

**App-wide Workbench pickers — #1206 (2026-10-15).** The owner accepted
the Settings sheets and rejected browser-native dropdown menus. One shared
core now renders square Workbench popup rows, checked current choice,
separate active highlight, unavailable ghost state and bounded scrolling.
The visible native select retains labels, form values, defaults/reset,
required/disabled/ref and native events. Pointer, keyboard, Escape no-save,
Tab exit and outside actions preserve the existing writers. Semantic
snapshot comparison keeps menus open across unrelated parent renders.
Source census:47 CycleGadget callsites after the Thread enum adoption,
plus the legacy Select consumer; all share the core. No per-face menus,
new dependencies or ceiling increases. Final quick GREEN:3880web /708
affected Python /107desk sweeps (2existing xfails) /17canon; build and
final TypeScript pass. Root read13-state real production walks at 1440/393,
actual language/export saves and refusal/Retry, nine-point phone targets,
and graph language-save cases including native touch393. Source review
RATIFY after one lifecycle fix/recheck; no Muad'Dib check or owner visual
acceptance claimed. Physical Safari/iOS and assistive technology remain
unverified; source coverage is not a live walk of every consumer. Owner
requested the next broad visual audit after this release. The compact Calendar chooser limitation was closed by #1207. Full main tape/postmerge review
remain separate.
[Implementation, census, exact proof and limits](../docs/internal/WORKBENCH-PICKERS-2026-10-14/README.md).

**Shared Settings primitives — #1205 (2026-10-14).** The owner rejected
Voice's flat form and requested a reusable foundation. Existing library
species now provide inset sheets with named headings and local actions,
explicit row widths, native On/Off checks, narrow labelled table fields,
balanced preference columns and etched dividers. Voice, Meetings, Rhythm,
Sounds, People and System adopt them. Real producer verification caught
Add symbol sending an invalid blank array and poisoning unrelated writes;
incomplete entries now remain local drafts, while valid values use the
existing writer. Normalization, unrelated saves, refusal/Retry and armed
Forget pass. Final quick GREEN: 3650 web /651 affected Python /107 desk
sweeps (2 existing xfails) /15 canon; build and TypeScript pass. Root read
canvas and production faces at 1440/393, symbol loops, full/bounded fields,
phone hit ownership and calendar-save graph cases. Independent Sol source
review RATIFY after one correction/recheck; no Muad'Dib check or owner
visual acceptance claimed. Remote address and optional TTS missing-model
reads are declared layout substitutions, not hardware/connection proof.
The existing P2 compact Calendar chooser failure with an in-use source
and unavailable discovery was closed by #1207. Desktop matrix retains
17 states before this failure; phone visibility is not chooser completion.
Add feed remains the explicit URL entry. Owner live judgment, real native
devices, remote connection, speech/model quality and external dispatch
remain open; incomplete symbols persist only in the Settings instance.
Full main tape and postmerge review remain separate.
[Implementation, exact proof and limits](../docs/internal/SETTINGS-PRIMITIVES-2026-10-14/README.md).

**Settings usability and Workbench revision — #1204 (2026-10-14).** One
substantial release audits every Settings module and nested account/calendar/
destination flow. The owner rejected the first visual pass; the revised build
keeps native Workbench material with a uniform Work/Desk directory, readable
type, paired wide groups, proportioned controls and paired phone choices.
Accounts names providers/sites and opens setup commands explicitly. Drafts
survive refusal and sign-in detours; parked paths wrap fully. Calendar names,
identities, disabled sources and multiple calendars survive ordinary edits;
assignment-aware GET/PUT avoids retired-selector refusal. Changed-path writes
retain newest failed edits and Retry. Rhythm, Telegram and device preferences
persist; read failures remain unknown rather than empty/ready.
Final quick GREEN:3647web /1131affected Python /107desk sweeps (2existing xfails)
/15canon; production build and frontend TypeScript pass. Root inspected actual
18-state main and6-state Accounts/destination walks at 1440/393, production
calendar graph saves, long paths and phone hit ownership in isolated HOME/DB.
Sol workers built; independent Sol source reviews RATIFY after bounded fixes.
No Muad'Dib check or postmerge review is claimed. Open: owner live acceptance,
real EventKit/provider sign-in/audio/model quality/external sends/scheduled
firing. Already dropped calendars cannot be reconstructed; explicit native
selection can refresh a blank name. Calendar refresh health still needs a
latest-read fact; no framework was added. Full main tape remains separate.
[Audit, rejection history, visual revision and exact proof](../docs/internal/SETTINGS-AUDIT-2026-10-14/README.md).

**Settings navigation and direct trials — #1203 (2026-10-14).** The owner
found Accounts/Engines could not open, a second Try confirmation, contradictory
Answers failure, missing waiting and unclear job names. One navigation state
now owns Settings wings, hub doors, Back and repeated scope entries. Guide
keeps the settings writer mounted; actual before/after captures cover pending
save, refusal and Retry. Try starts on its row at both widths with the library
animation, destination chips and actual sample input/output. Five fixed public
samples use existing adopted routes; successful empty output remains successful.
Custom tasks and Background work name routing groups; task details are folded.
A live capture also found loopback falsely required off-machine confirmation;
preview now uses the existing endpoint locality classifier. Final quick check
GREEN: 3597 web /676 Python /107 desk sweeps (2 existing xfails) /15 canon;
build and frozen frontend TypeScript passed. Actual UI→HTTP→kernel→terminal DB
captures pass all five jobs at 1440/393, including animated waiting, one request,
phone target ownership and unchanged domain/assignment snapshots. The provider
leaf is replayed; this does not prove physical model quality. Open: owner's
microphone/LAN/cloud response, external sign-in and owner acceptance; one sample
is not every task; ID guard does not bind a same-profile endpoint retarget.
Root bounded review RATIFY; no Muad'Dib, independent whole-change or postmerge
review claimed. Full main tape remains separate.
[Repair and actual verification](../docs/internal/SETTINGS-TRIALS-2026-10-14/README.md).

**Deep usability audit and repair — #1202 (2026-10-14).** The owner clarified
that Send was an example and requested a deep pass across existing surfaces.
Three bounded Sol audit/build lanes, shared-read repair, independent actual
1440/393 verification, and one implementation review plus fix recheck. People
leads with readable context and keeps private/shared note drafts. Room retains
refused corrections and confirmed work through read failure. Workbenches lead
with work, keep full inlet drafts and phone source selection, and refresh the
chooser after creation. Schedule keeps the whole operation and protects newer
edits/reopened forms from older acceptance. Knowledge edits real membership;
retained unsupported text can become a Note. Editors flush before Done/Close
motion, report actual saving/refusal and retry; Workflow prompt/step editing
fits, and its title-bar Edit opens the actual editor. Ask merges async source
choices. Transient collection reads keep known buckets;401/403 and successful
empty reads remain authoritative. Final quick check GREEN:3717 web /550
Python /107 sweep (2 existing xfails) /15 canon; build, frozen TypeScript,
metadata generation and actual corrected Ask walks at both widths passed.
Initial audit metadata failures were fixed and the whole quick check rerun.
Independent recheck RATIFY; no Muad'Dib or postmerge review claimed. Open:
existing Workbench item-body timer/unmount custody, compact Grounding heading,
Settings phone inner poses, populated runs and successful Delivery dossier;
owner judgment, real model/agent/terminal/microphone, external dispatch,
physical devices, schedule firing, full main tape and postmerge review.
[Deep audit, repair and evidence limits](../docs/internal/DEEP-USABILITY-2026-10-14/README.md).

**Note and shared Send refinement — #1201 (2026-10-14).** The owner
opened a Note and rejected Send. Send now owns the body with full-width frozen
preview, visible Add destination, one outer scroll region and separate dispatch/
receipt. Back returns to the same Note; the mounted writer saves first and
retains revision/conflict/Close fences. Meetings Send to unfolds the actual
scoped record’s well. Retained Note checks exposed desktop question/context
clipping and phone Reads return focus; bounded host fixes cover both. Final
quick check GREEN: 3,537 web / 546 Python/browser / 107 sweep (two existing
xfails) / 15 canon; production build and TypeScript passed. Actual isolated
Note/Meeting file bytes match frozen DB payloads at 1440/393; revision, receipt,
pointer, custody, focus and restart checks remain. Owner judgment, actual
email/Slack delivery, real model/LAN inference, microphone, physical devices,
full main tape and postmerge review remain open. Deterministic interview
fixtures do not prove the owner’s engine.
[Refinement and verification](../docs/internal/SEND-REFINEMENT-2026-10-14.md).

**Surface audit and repair — #1200 (2026-10-14).** One substantial PR,
requested after the owner rejected Conductor's session screen. Three bounded
Sol audits and six Sol implementation lanes reused the current component and
service framework. Sessions lead with work/project, state, captured report and
one answer well; terminal and management controls open on request. Meetings
retains live Record/Stop inside Meetings with Back. Week scans closed rows;
Send/Decide and optional Ask context open on request. First use, Engines and
phone Settings are clearer. Memory carries actual owners and recorded sources;
History searches titles and opens the existing item. Failed actions retain
context and receipts; Thread controls support ordinary keyboard entry.
Final quick check GREEN: 3,581 web / 641 Python / 107 sweep (two existing
xfails) / 15 canon. Production build, TypeScript and focused actual-open graph
walks at 1440/393 passed. Open: owner judgment, real agent answer delivery,
terminal keys, microphone, model inference, external dispatch, main tape and
postmerge review. Memory source has component opener coverage; its live click
remains unobserved. Unseen audit-tail surfaces receive no usability claim.
[Audit](../docs/internal/SURFACE-AUDIT-2026-10-14/README.md) ·
[Repair and verification](../docs/internal/SURFACE-REPAIR-2026-10-14.md).

**Model discovery and download repair — #1199 (2026-10-13).** Settings →
Engines → Find on LAN returns actual model choices; Use it adds a library
profile without changing job assignments. The production scanner found the
owner's 192.168.1.43:8080 / qwen3.8-27b from interface addresses (read only).
Qwen 4B used the publisher's Xet identifier as its file checksum; catalog
revision 5 corrects it, and retry can reuse a fully verified rejected file.
Initial Send reads now report pending honestly, closing the traced Week
settling gap. Engines owns one footer; off-machine confirmations stay clear
of the Dock and the Settings return remains available. Quick check GREEN:
3,472 web / 1,707 Python (2 existing availability skips) / 106 sweep (3 existing xfails) / 15 canon. Typecheck and architecture/API generation green; 9 engine
browser cases passed, including both LAN cases and actual More → Undo.
Open: owner browser acceptance, actual model installation/inference, Linux
hardware, full main tape and postmerge review.
[Handover](../docs/internal/HANDOVER-MODEL-DISCOVERY-DOWNLOAD-2026-10-13.md).

**Daily journeys — #1198 (2026-10-13).** One substantial follow-through PR
on #1197: linked People Prep → Record with validated calendar provenance;
Outcomes → corrected task/owner/date → durable accepted work; selected Note
text → Task or visible Ask quote with its canonical source. More uses the
shared menu, phone rows remain readable, Ask is quieter, and hosted surfaces
keep scroll by scope. Pending edits cannot be bypassed by Confirm all; both
single and bulk confirmations keep success when only the reread fails.
Week detail refreshes keep their reading marker while retaining current rows.
Final quick check GREEN: 3,508 web, 1,302 Python, 106 sweep (3 existing
known reds xfailed), 15 canon. Typecheck and architecture/API generation green;
10 isolated real-hub journey walks at 1440/393 passed. Owner desk judgment,
real microphone/LAN inference remain open. The Week settling gap was traced
to the lazy Send well and corrected in #1199.
[Handover](../docs/internal/HANDOVER-DAILY-JOURNEYS-2026-10-13.md).

**Productivity implementation — #1197 (2026-10-13).** One combined PR at the
owner’s request, built from the October 13 verbs/windows/words/attention
designs on #1196. The owner chose **Inside Meetings, with Back**; this
supersedes the October 10 separate meeting window interpretation below.
Notes can create Tasks, join Projects, and ground Ask. Meeting Outcomes,
durable Done/Reopen, accepted People prep, chosen engine routing, Settings
Engines/Accounts, phone Go/Back/More, and one attention source are integrated.
Quick check GREEN: 3,699 web, 4,709 Python (3 model-dependent skips),
106 sweep (3 existing known reds xfailed), 15 canon guards; typecheck and
6 API manifest checks green; 8 real isolated-hub walks at 1440/393 passed.
[Handover](../docs/internal/HANDOVER-PRODUCTIVE-DESK-2026-10-13.md).

PHILO Phase 17, The Usable Desk (ACTIVE, 2026-10-10/11). Owner: "in a speedy fashion, also start addressing very heavy and very taxing usability issues of the entire system… so cumbersome… confusing." Four eyes-on walks → `docs/internal/philo/phase-17/USABILITY-INVENTORY.md` (#1057; U01–U37, 10 BLOCKS — all ten addressed). OWNER RULINGS 2026-10-10: "everything must become one desk" (DONE #1069); "a meeting opens in one window" (DONE #1082); doors per app = Muad'Dib's call (DONE #1078). MUAD'DIB RULINGS: HS-201-10's no-auto-summary superseded for chosen/local engines (#1064); every project opener opens the Room (#1068); canon words: "agents" = personas, "coders" = live coding sessions (POSITIONING 181-182; #1084); Weekly update stays a /prompt starter (#1085). MERGED: #1058 #1059 #1060 #1061 #1062 #1063 #1064 #1066 #1067 #1068 #1069 #1070 #1071 #1073 transcribe #1074 #1075 runs-on foot #1077 #1078 doors #1079 #1080 brief cover #1081 day-one autoflow fence #1083 Runs on words #1084 coders + Room words #1085 first run #1086 #1087 Conductor open. #1088–#1091 #1093 evalerror #1094 phonepass #1095 redact. OWNER 2026-10-11, THE TEST DIET: "each time we run a test suite it fucking takes hours … didn't we just build out a declarative compositor framework … programmatic e2e … without relying much (or at all) on playwright?" → "I do like your plan, and approve you immediately working on it." Plan: the browser suite (209 files, 441 checks, 30 min) is mapped check by check: 104 → hub tests, 178 → vitest one file per app, 37 → ONE generic compositor sweep (every app via /api/desk/windows at 1440+393: fit, console, readable, clip, overlap, library Button, no-move, 12 px floor, material, wings, routes, zero egress), 80 stay real browser (drag, focus, touch, multi-browser, geometry, clipboard), 39 duplicates; parked, never deleted, in tests/e2e/_parked/. WAVE 1 MERGED #1103 (integrates #1102 sweep, #1098 MEET, #1099 ROOM, #1100 AGENTS, #1101 DESK): 76 browser files parked, live 209 → 137 incl. the sweep (76 checks, ~55 s at -n 8), ~320 fast tests on recorded real hub answers; whole browser suite 13.5 min at -n 8 (was 30 at -n 4). Every lane had one Astra round; every round found dropped after-press transitions or lying doubles, all paid. CLAUDE.md: -n 8 under the lock; THE TEST DIET tiers. WAVE 2 MERGED: #1106 (21 more parked; live 137 → 116), #1107 (lying doubles re-recorded under a strict shape guard; six -n 8 flakes fixed by cause; product: card redactor no longer mangles op-ids yet still catches Markdown/hyphen-bounded cards, node cursor written atomically, steward receipts carry and open their ref, thread reads carry parent_thread_id, GET /api/updates/{id}), #1105 (gadgets ⌘K test waits for the ranked list). #1108 fixed the sweep's known reds (Places, Processes, raw Delivery rows, Components, two bevels, chair:needs on the phone) and held five windows still while late reads land (meeting, Agents, Room footer, Needs you, Rhythm); the whole browser suite is GREEN on its head: 660 passed, 1 xfail. Whole browser suite 12 min at -n 8 (was 30 at -n 4 this morning); FAST 6.5 min (was 11). OWNER CALLS OPEN: (1) the Components catalog's topology demo at 393 (zoom to fit, or stacked); (2) Runs on paints jobs before detection by ratified design — hold them still? The sweep's KNOWN_REDS are product defects to fix (Dock 393 overlap, Places star, Processes clip, raw buttons in Companion/Components, two flat Buttons, chair:needs not drawn on the phone; MAYBE: late reads moving rows). MAIN: whole e2e 866/869 after #1082 (remaining reds paid by #1090/#1091). LESSON: whole e2e on main after every 2–3 merges. Day-grouping canvas published for ratification: https://claude.ai/artifact/15XaGDbJgaFfUFmcTR7BrT (questions: end cut vs PHILO-15 B30 middle cut; full name on select). NEXT: day grouping on the desk (canvas first), the words pass (Settings U35, remaining jargon), the 393 phone pass, Phase 17 close + handover. OPEN from merged lanes (unresolved after review caps): #1059 printed iPad address may be a VPN's; signed-out screen is the old failure face; iPad unverified; any 401 forgets the token. #1063 a failing manual Evaluate never records last_error. #1061 Plan 1:1 with a date; agents cannot write they-owe. #1062 no MCP read of the combined decisions ledger. #1064 a Stop in the same second as a brief build reads fresh. #1066 atlas J1/J4 readiness dependencies are prose; speech row built without a canvas. #1069 four p13 atlas cases wait for dock chips (off since Phase 16); place sound gone; recipe Get Info only via window Object menu. #1070 dragging a background window by its bare bar can miss (likely U28b); Trust window past the 1440 edge; macOS may take ⌃1–⌃4. #1083 at 1440 the Meetings wire draws the group engine while the lead names the summary engine; the loopback parity table is shared JSON (both sides fenced). #1084 HS-174 remote receipt still seeded (real mint needs remote listener + agent credential + non-loopback MCP client); "ready" cannot prove sign-in (Keychain). #1085 the reopen flag is memory-only. test_hs202_first_use_smoke one unexplained [1440] failure in 32 solo runs. Rig: the test lock polls (not FIFO); background test runs need timeout 7200000.

PHILO Phase 15, The First Day, is CLOSED (2026-10-08; handovers `docs/internal/HANDOVER-MUADDIB-XXXV.md` and, NEWEST, `HANDOVER-MUADDIB-XXXVI.md` (the night after: pi #1022, AgentWords #1026, the owner's FRESH DESK, state parked at `~/HoldSpeak-parked-2026-10-08/`, and PART II THE TEST DOCTRINE: the orchestrator alone runs system-level tests, workers run file-named budgets, one bounded brief, one bounded review); 22 lanes, two rehearsals, B01–B90 logged, 73 paid in a merged lane (B43 B55 B57 B75 in part; the rest of each is its own bounce), 17 open (B32 B49 B76–B90); the "59" written at close was a tally, not a count; reconciled 2026-10-08 against the three ledgers and the lane PRs, `DAY-ONE.md` v2 is the owner's runbook; NEXT: the owner's real first day from the runbook, every bounce the next phase's inventory; chartered 2026-10-07 by Muad'Dib under the owner's autonomy grant; charter `docs/internal/philo/phase-15/PROPOSAL.md` #964; inventory `DAY-ONE-INVENTORY.md`, 18 ranked gaps). No new face: the owner's first real day rehearsed end to end on real metal with isolated credentials, every bounce paid in a lane, then `DAY-ONE.md` as the runbook. In flight: 01 MERGED #967 (the 'No engine for summaries' blocker asks the ROUTE POLICY: the hub's assignments API gives each meeting capability a `queue` answer resolved through the meeting-queue policy's own sources (global default included) and the hub blocker, its TS twin, the Concierge summary row and the Meetings headline all read it; RULING: a fresh HOME's row is TRUE, so the five empty-brief atlas cases set up an engine through the rig first (all pass at both widths); RULING: summaries OFF HOLDS: a new additive table `inference_capability_off`, the Concierge's OFF press writes it even with no exact assignment, the queue resolution stops at OFF before the default, `InferenceRoutePlanService` refuses with `context.off`; OFF is a deliberate state, never a failure: a queued job (Stop- or Run-admitted; OFF wins over the stale-route check) ends `skipped · Summaries off.` with no error, no Retry, no Needs-you row, no Brief item; a live HTTP/MCP run under OFF answers 409 `summaries_off` and the observer records `refused_by_setting`, not an exception, so the Brief's breakage collector stays empty; the backlog queues nothing under OFF; the Meetings headline reads 'Summaries off' over the unsummarised count and the route chip SUMMARIES OFF; a meeting skipped by OFF rejoins the backlog when OFF clears (the exact Meetings choice) with the receipt SUMMARIES ON · queued, one provider call; a meeting the owner skipped stays skipped; RATIFIED: a new global default preserves an explicit OFF; Astra r1 DNR → r2 DNR (capped) → the two leftovers fixed with producer-backed red-then-green fences and verified by Muad'Dib (21 unit, 4 glass, FAST green 14,833)). Open from #967: `test_phase200_intel_drain.py` singleton-drainer tests fail only in parallel (pass serially); inherited glass debt confirmed by Astra on clean main (hs200_continuity, hs200_coverage, hs201_09 wait for Chair windows that now start closed; connect-engine's old blocker selector) → lane 06; 02 MERGED #966 (the Concierge's add-engine row has an optional KEY field, library species with a visible caption (`StringGadget.caption` added to the species), password type exempt from the mic law by rule (the scanner now also skips comments at any depth: an apostrophe in a comment had ended the tag scan and blinded the mic rule); a key is validated as a header-safe token BEFORE any header is built (typed → 400 `key_invalid`, stored/env → 422), the Check exception path logs the class only, the key lives in the 0600 profile key store and never in the receipt/config/DB/log; KEY REQUIRED / KEY INVALID · BAD CHARACTERS chips, no sentences; the real .43 box takes any key, so the keyed path is proven on a local stub; `holdspeak doctor` runs the same `collect_doctor_checks` list the Setup page runs, honours `--strict`/`--connectors`, then the 10 hub checks; CONDUCTOR.md and OPERATIONS.md corrected; Astra r1 DNR (key in log, invisible name) → r2 RWC, both conditions paid; FAST green with one load flake passing alone). Open from #966: the 393 Concierge footer receipt overlaps Cancel ('7 WAIT…Cancel', inherited); `test_hs201_09_connect_engine_glass.py` and the j3 `concierge_use_for_summaries.assigned_ready` atlas case block before reaching the Concierge (old `arrival-display` / Chair-section entry paths; A1/A5 casualties); no complete browser walk of keyed Check → save; 03 MERGED #968 (a WAV import ALWAYS reaches a final status: the placeholder row was born `active` and only success ever changed it, so a failed import waited 300 s forever; now `_fail_import` writes `import_failed` + `transcription_status: failed` + the cause, the worker catches BaseException (CANCELLED) and a thread that cannot start writes IMPORT DID NOT START; on hub start `recover_interrupted_imports` marks every row still importing as failed · INTERRUPTED BY A RESTART (fenced on a real hub); sync keeps `failed`/`complete` and the detail (it had turned everything but record_only back to `active`); the walk tool stops at `failed` (j4 with no model: 7.7 s, not 300); `MeetingSummarySlab` owns the summary and the Chair composes it once (component consolidation; the old 'summary twice' symptom was the first-use smoke's `arrival-display` wait plus strict-mode duplicates across two windows); `test_hs202_first_use_smoke.py` re-anchored to the screen and the drawer, green in strict mode at both widths with its expected-failures list empty; Astra r1 RWC, four conditions paid incl. the restart recovery; FAST green). Open from #968: a failure write that itself fails leaves `active` until the next hub start (logged); the j5 `route_disclosed`/`planned_host_disclosed` atlas cases block at the old `concierge-add-engine` setup step; `philo13_08 decide [393]` red on main ("no Chair window to step past"); no `meeting.transcription_status == active` consumer treats it as membership (checked). 04 MERGED #974 (the PARKED DRAWER: the Parked icon opens a drawer of every parked object across kinds (meetings, Workbench items, archived Projects) through `GET /api/desk/parked` composed from the per-kind reads, owner-only (401/403 fenced through the real hub), every meeting page followed with NOT READ · PARTIAL when a page fails; Open goes where the object lives, Restore uses the kind's own route and the park receipt; the People icon already opened People (fenced); Resend is the email DEFAULT (SendGrid selectable; the operation schemas say so; the legacy fallback kept); a DENIED calendar on the first-run card offers Open System Settings (owner-only, HTTP-only kernel op `calendar.open_settings` with a fixed URL and a receipt; its `/usr/bin/open` site classified in the effect fence) and Check again; Astra r1 RWC, conditions paid and verified; FAST green 14,849; shots ratified by Muad'Dib). Open from #974: Settings has no macOS calendar path (ICS only) so the denied-state verbs exist on the first-run card only; a connector sign-in still saves no Send destination; no real permission change or email was exercised. Rehearsal 1 part A MERGED #977 (`docs/internal/philo/phase-15/rehearsal-1a/BOUNCES.md`: 30 bounces, 76 shots; the worst: B01 Whisper looped one word ×250 at a hard 30 s window and lost an action item behind '299 WORDS'; B02 no decisions ever (decision_capture off by default); B03 no Confirm outside a Project; B04 the Brief lies after a full day; B05 READY then TOOL INCOMPATIBLE). 06 MERGED #981 (the inherited browser-test reds on main were all stale gestures from Phase 14 — windows that now start closed, the Needs section that became a drawer; nine files + the shared `chair_windows.py` helper re-anchored, no product gap, no assertion weakened beyond two A5 dispositions (the COVERAGE · 3 OF 4 count, the Next line's order); the blocker-row check restored on its `data-object-id` identity red-then-green; `philo13_08` presses retry only on a detached row; Astra RWC, condition paid; 19 glass green under the lock; tests/e2e-only so main's FAST covers it). Open from #981: `test_philo8_03_then_guard.py` misses a 10 s wait for the Floor's 3D view under load (10/10 alone); whether the Meetings reload's loading line (`Surface.tsx:232`) is a visible flicker to the owner is unknown. ALSO MERGED #979: `scripts/test_lock.py`, one test run on the machine at a time (owner catch 2026-10-07: lanes running tests concurrently broke each other). 07 MERGED #982 (THE TRANSCRIPT NEVER LIES SILENTLY: the import reads Whisper's own segment timestamps so a segment touching a window cut is decoded whole in the next window (the next decode still starts at the hard cut after a kept full-window segment); each window decodes with Whisper's loop guards explicit and a looping window is decoded once more at a higher temperature; a loop is Whisper's shape only (the same 1–4 words 10+ times or 1–12 chars 20+ times), never a ratio; RULING: a mark never deletes recognised words, it appends `[unclear m:ss–m:ss]` and the WARN · N UNCLEAR SPAN lamp counts valid marks on the record, the list row and the Chair with one definition and an authoritative zero; a retry replaces the first decode only with fewer loops AND at least as many real words; the sent meeting_summary carries 'Transcript: N unclear spans' from the marks; the import title is the humanised stem; the Meetings footer keeps N RECORDS and shows a run receipt beside it (QUEUED hh:mm → RAN · hh:mm, bound to meeting+run id, fresh runs only, kept across reload); the two literal census counts removed, the seam registrations kept; Priya Shah's action survives the real fixture in every run (main lost it 6/6); Astra r1 DNR → r2 DNR (capped) → the three leftovers fixed and verified by Muad'Dib (24 fences incl. the real Whisper test; FAST green). Open from #982: 'the LAN summary's title wins' (the summary has no title field; auto-title runs only after a recording stops); a true Whisper loop now shows its repeated words plus the mark (honest, ugly); no live LAN run of the footer transition observed. 08 MERGED #983 (A MEETING YIELDS DECISIONS AND CONFIRMABLE ACTIONS ON DAY ONE: the deferred summary carries decisions and action items as structured items on the route the owner saw (Run summary skips the plugin chain by design; no new egress); the live window keeps its own three-field result; on the real LAN model the fixture gives 3 decisions + 2 action items, confirmed from the Needs row at both widths for meetings in no Project; Confirm KEEPS the proposal's kind (`decision_records.kind` additive column read by every list/search/review/MCP/preparation/Brief consumer; the Room's action row reads 'Action:'); Defer hides the whole linked obligation until expiry; RULING: never merge two obligations by similarity alone (same normalised text AND owner AND due date; the staging/production pair fenced); a reply WITHOUT `decisions` reads DECISIONS · NOT EXTRACTED · <engine> and DECISIONS NOT PROVEN on the compatibility row, `[]` is honestly empty; old-hash profiles still route so the owner's LAN profile is not 'incompatible'; the summary-items writer split into `kernel/summary_items_projection.py`; API surface regenerated; the wire fixture regenerated through the real producer after #982; Astra r1 DNR → r2 DNR (capped) → leftovers fixed and verified by Muad'Dib (FAST green 14,908)). Open from #983: no `proposal.defer` MCP tool; the decisions-and-actions artifact lands on the Desk floor; records before the `kind` column default to decision; the ux-canon raw-ids scanner counts snake_case literals inside JSX expressions as rendered text (three lanes hit it today). 13 MERGED #991 (the 'onboarding hooks flake' red in every FAST today was a PRODUCT BUG: the Codex trust step waited with `select.select`, which refuses file descriptors ≥ 1024, so a long-running hub's 'Use it' for Codex could fail with 500; now `selectors.DefaultSelector` (kqueue/epoll); a failed start after the child spawns closes the selector and kills the child (fenced with a real subprocess that errors / never answers); a second test leak fixed (a credential cache saved under the run's HOME); Astra RWC code-read, condition paid; FAST 14,912 passed, ZERO failed). Open from #991: which tests leave > 1024 descriptors open in an xdist worker is unknown (unhandled `sr-autostop` threads and streaming turns after dropped tables are likely contributors). REHEARSAL 1 PART B MERGED #992 (`docs/internal/philo/phase-15/rehearsal-1b/BOUNCES-B.md`, B31–B57, 108 shots): the Conductor loop finished once on real metal (Codex on the LAN box → PR #1 on a throwaway repo → merged → origin closed → update sent to the Folder) with five workarounds outside the face; worst: B41 Codex's folder-trust screen never answered (the parser joins Codex's 'Note:' paragraph into the path); B43 YOLO holds every heredoc/apply_patch inside the agent's own worktree (9 holds in 19 min); B38 a Door-made Project has NO REPOSITORY and nothing registers one; B47 the YOLO responder spoke as the owner and re-ordered finished work; B52 the merge closed the item but the weekly update has no Merged row. RIG LAW learned: TMUX_TMPDIR inside the isolated HOME (else the hub joins the owner's tmux server), GIT_CONFIG_NOSYSTEM=1 (Xcode's osxkeychain helper touched the owner's Keychain once; outcome unknown, owner told), PEOPLE_KEYSTORE_FILE inside the HOME. 12 MERGED #989 (the UGLY bounces: four D1 Dock sprites drawn with PixelLab (Intelligence clipboard, Desk memory chip, Delivery outbox, Panes windows; picks ratified by Muad'Dib), a fence that every Dock item has a sprite; the Meetings record takes the window's full width (the list is a strip above it); Intelligence opens at its declared 640×620 with populated items (a saved size wins); the Send well keeps the owner's 2026-10-05 auto-open for the lone built-in folder and names it `HoldSpeak/Sent` (path on hover; no underscore italics); an empty Project reads NEW, the Door's create reads CREATE; footer receipts stay in their cell (ellipsis + title, wrap when narrow, 1.3 line-height so glyphs are not cut); a room-ledger `nowrap` rule no longer beats the chip wrap variant (The week's topics fit at 393); desk labels break at spaces first, then `_ - . /`, a long name is cut in the MIDDLE so a distinguishing suffix stays, drawer Icons and List wrap (List no longer clips); five scoped-glass reds re-anchored to the new truths; Astra r1 RWC, conditions paid; FAST 14,912 zero failed). Open from #989: a test that finds a desk icon by its visible text misses a middle-cut name (use the title/aria-label); the Dock's own labels still cut at the end; `test_finish_face_polish::test_the_named_faces_say_names_and_plain_reasons` fails only in loaded multi-file runs (cause unknown); INHERITED reds found: `test_philo13_04_faces_glass` ×4 expect SUMMARY STORED where the rail now reads 1 TO REVIEW since #983 (the rail is right; the test's claim needs re-anchoring → lane 18), the zoom test measures a closed Brief window (→ lane 18), hs145 has no Close Settings after Connect calendar (→ lane 18).  14 MERGED #996 (CODEX LAUNCH + LANE TRUTH, B41 B42 B46 B48 B50 paid on a real Codex 0.159 launch against the LAN model, throwaway repo PR #2: the launch's PR title and number ride the agent's record and the Room; `turn_end` (asks / idle / done) classifies the agent's last words in Python and TS alike and the lane station, rail entry, ask-well caption and Needs lamp read it; a question is a QUESTION whatever follows (shared `asks_a_question` in `agent_context/models.py`, mirrored in `needsYou.ts`); the Re-brief route `POST /api/agent/launches/{id}/rebrief` in the API surface; the exact-path trust fence stays (macOS `/tmp` symlink matched through its real path, siblings never); Astra r1 → r2 DNR (capped) → the leftovers verified by Muad'Dib, FAST 15,005 green). Open from #996: B49 VERIFIED RIG-ONLY 2026-10-08 (owner consent): Codex 0.161 signed in with ChatGPT, given the launch flags against an isolated hub, called `project.list` and `desk.needs_you` in one turn, CAUSE (same day, Codex 0.161 pointed at the LAN box through a logging proxy): Codex sends our MCP server to the model as ONE tool of type `namespace` (`mcp__holdspeak`, the 250 tools nested), a Responses-API tool type OpenAI serves and llama.cpp's Responses shim drops, so Qwen sees resources only ("mcp__holdspeak isn't in my directly exposed tool list") and reads `holdspeak://desk/verbs` instead; on 0.159 the same gap showed as `tool_search`; any non-OpenAI model behind Codex has it; OWNER'S WORD 2026-10-08: SPIKE `pi` as a third harness for the LAN model (branch `spike/pi-harness`, report only, `docs/internal/spikes/PI-HARNESS.md`): MCP tools, the gate hook, brief in / turn end out; SPIKE MERGED #1020 (22 min): VERDICT YES, pi (`@earendil-works/pi-coding-agent` 1.1.0, MIT, own MCP client, OpenAI-compatible providers) can be the third harness: on qwen3.8-27b it called `project.list` and `desk.needs_you` through our server (core tools must be `direct`, its tool_search missed one); its `tool_call` extension event blocks a call fail-closed and the real `holdspeak gate hook` held and denied an `echo` under `pi:spike`; tmux paste delivers the brief and `agent_end` reports the turn end, classified done/question by our models; FIVE GAPS to build (`pi` in GATE_AGENTS and the hook CLIs, a `pi-default` profile, a per-launch config adapter with `PI_CODING_AGENT_DIR` and a literal hub URL, one maintained extension `holdspeak-pi.ts` for gate + turn end, lower-case tool names mapped to Bash/Edit/Write); scars: kill the process group on stop (orphan hook), expiry deny lacks "do not try again", close stdin in print mode; BUILT AND MERGED #1022 (owner's word, "a great path forward"): pi IS THE THIRD CODING-AGENT HARNESS: `pi` in GATE_AGENTS and both hook CLIs, profile `pi-default`, per-launch `holdspeak/delivery/pi_launch.py` (isolated `PI_CODING_AGENT_DIR`, models.json from the coding placement with the key from env only, mcp.json with a literal hub URL and the credential header, core tools direct, `PI_OFFLINE=1`, stdin closed in print mode), one maintained extension `holdspeak/agent_context/pi_extension/holdspeak-pi.ts` (gate fail-closed on PreToolUse, rider on session start / prompt / tool result / agent end / shutdown), a PixelLab sprite; proven on real metal against the LAN box, a Hand to pi in YOLO: brief received, `project.list` called through our MCP, `cat /etc/hosts` held OUTSIDE THE WORKTREE and denied with the reason, PI ASKS read on the lane, Stop killed pi and its hook (shots `docs/internal/philo/phase-16/01-shots/`). Astra r1 DNR four MUSTs, r2 DNR two MUSTs, all six PAID and verified by Muad'Dib: (1) every pi MCP call goes through the gate and THE HUB decides from the caller's own launch record (`GateService._decide_mcp`): pre-approved (Normal/YOLO) passes to the palette, Secure holds every non-read tool (a name ending get/list/read/search is a read only when undeclared), a caller with no launch stays held, the env flag is a hint only; (2) pi's read/grep/find/ls pass only inside the worktree (symlinks resolved), outside goes to the gate as Read and holds in YOLO too; (3) the launch record keeps `process_group {pgid, sid, leader, start}` and Stop signals only processes of that group and session not older than the launch, so a dead leader's children die and a recycled id is left alone; (4) the expiry deny ends "Do not try it again in a different form"; (5) a Write's completion matches as its admission did (operation `succeeded`); FAST 15,318 green after the two `ps` probes were classified in the effect census. RESIDUALS (Astra MAY): the launch dir stays after credential revocation until merge cleanup (holds pi transcripts, no secret); a hold waiting at Stop stays WAITING until it expires; no live project-item Hand from the desk: the Room's ITEMS list has no Hand verb (CANVAS QUESTION for the owner); pi's `edit` through the gate not walked on metal (node test only); the pi option on the confirm line only in vitest; a recycled group whose own leader also exited cannot be told apart by start time; session receipts read a pi session as a plain tmux pane (a `pi-hooks` adapter needs one contract-schema value under `pm/roadmap/`, read-only); the pi folder records the engine's 16k context while the box serves 49k; every pi MCP call costs one hub round trip; one vitest run (12 s) ran outside the lock; the lane ran the doc generators once with the real HOME, which added `pi-default` to the owner's real `agent_profiles.json` (harmless, now the product's own entry); pi 1.1.0 is installed per rig, not on the owner's machine, and a desk without pi on PATH must read it as NOT FOUND like a missing codex (verify on the owner's first hand); CORRECTION: pi 1.1.0 IS on the owner's PATH (nvm) and doctor reads `pi hooks installed`. OWNER CATCHES 2026-10-08, paid: his `~/.codex/config.toml` deprecated `[features].codex_hooks` renamed to `hooks` (backup beside it); his Codex hooks.json was an older template ("partial" = no PermissionRequest), reinstalled through the product installer (ccgram entries kept) and re-trusted through the card's own trust step, doctor now `Claude Code hooks installed; Codex hooks installed; pi hooks installed`; MERGED #1024 `holdspeak agent-hook install|uninstall --agent pi` (pi has no hook file, its hooks ride every launch as the extension: the CLI accepts pi and `all`, prints `pi: nothing to write · HOOKS RIDE EVERY LAUNCH · EXTENSION IN · <path>`, writes nothing for pi, the "remove any time" footer only when a file was written, `--settings-path` with pi = usage error; Astra one round, two copy MUSTs paid, her MAY paid; FAST 15,323). GOTCHA (cost three FAST runs): a worktree venv synced with `uv sync --all-extras` (faster-whisper, ctranslate2, av …) exhausts an xdist worker's file descriptors about 7 min into FAST (`OSError: Too many open files` in `popen-gw1`, then thousands of errors); sync a worktree with `uv sync --extra dev` only, the main checkout's set; plain `uv sync` removes pytest; lane 13's open question (which tests hold > 1024 descriptors) stands; OWNER CATCH 2026-10-08 ("why is the agent's answer not rendered nicely here? The '**bold**', the ``"): MERGED #1026 AN AGENT'S WORDS RENDER: one library component `web/src/desk/components/AgentWords.tsx` is the only renderer of text an agent wrote (untrusted: paragraphs, bold, italic, inline/fenced code, lists, headings as bold lines, links as text + URL never an anchor, images as alt text, HTML shown as text, never innerHTML; long ids wrap at `/ _ - .`), on 11 surfaces (ask well, approve well, turn-end lines, SENT line, rail SAYS/ASKS/IDLE/DONE, Needs ASKS row, Brief TO ANSWER, Coder and Session window questions, Companion ledger cell, Mission Control tooltip as plain text); the hub and `needsYou.ts` carry the raw question up to 4000 chars beside the short title; RULING: a compact row shows THE ASK (the last paragraph ending "?"), else the start, cut at a word; RULING: the 393 SENT line stops at `project_item:pitem_ …` (the title bar names the item); canvas `docs/internal/philo/phase-16/02-canvas/agent-words.html` ratified by Muad'Dib; shots `docs/internal/philo/phase-16/02-shots/`; Astra r1 RWC three MUSTs paid (compact cut inside an unbreakable token: every rect measured, the token itself cut with the ellipsis inside the box, re-measure on width change; a rendered Chromium fence at 393 that failed before and passes after; PR body + canvas reconciled), r2 RATIFY; FAST 15,322 + the web copy guard after `__tests__` fixtures were excluded from its scan (an agent's real words as test input are not glass). RESIDUALS: Astra MAY a positive rendered test for a two-line paragraph with one unit spanning both lines; an id with no `/ _ - .` after a short head is dropped whole from a compact row; the shots seed Claude Code so the caption reads CLAUDE CODE ASKS with pi's words; two scoped glass reds inherited from main (`test_rebrief_receipt_survives_send` waits for `/steer` but Re-brief posts `/rebrief`; `test_hs201_09_connect_engine…[393]` finds no Models menu item); the owner's own `~/.codex/config.toml` still sets the deprecated `[features].codex_hooks` (0.161 wants `hooks`), a notice, not ours. ORIGINAL: B49 FOUND NOT FIXED: Codex 0.159 defers every MCP tool behind tool search (`tool_search_always_defer_mcp_tools` forced), and the LAN model has no tool search, so the launched agent sees `holdspeak: connected (138 tools)` yet is offered none of them; not verified on an OpenAI model (no key on the rig); a stream error ends a turn without the Stop hook, so the lane's last word can lag; `conductor.test.tsx` carries an inherited red; B43/B45 holds under `agent:launch:<id>` read HELD "—" (lane 15 pays)).  15 MERGED #998 (YOLO WORKS IN ITS WORKTREE + THE DESK ANSWERS AS THE DESK, B43 B44 B45 B47: RULING the 120-char held-command head STAYS; B44 is a design limit: a long held command is CUT, keeps Deny + Open (Raw), the row reads `CUT · APPROVE IN RAW`; the word a hold names leaves the agent only if it already appears in the redacted head, filtered AFTER every hub override (a branch past the head is omitted, `PUSH TO ANOTHER BRANCH`), the hub re-checks before storing; any pipe into an interpreter is held `RUNS CODE · <name>`, a `cd` to a missing folder or inside a pipeline `FOLDER NOT RESOLVED · <dir>`, a write through a symlink out of the worktree held; Astra's three secret probes and four escape probes fenced through the real hook and hub; a DONE/IDLE report is not a Needs row (lane station, rail, Conductor lamp) and is recorded on the triage path (`record_turn`) with no model, answer or notification, remembering the words it read; RULING order question > problem > done > chitchat (a failed check after DONE goes to the owner); "no further action" / "deployed successfully" read DONE, a negated problem word ("no errors") is not a problem, in Python and `needsYou.ts` alike; a routine answer must quote a brief line and give no command outside the quote ("please"/"kindly" and any imperative sentence go to the owner as REAL); HELD counts and THE DESK ANSWERED receipt on the lane; one `turn_end` field shared with #996; Astra r1 → r2 DNR (two P1s + two P2s paid) → verified by Muad'Dib, FAST 15,160 green). Open from #998: a secret in an unknown format inside a command under 120 chars is stored whole by design; the real Codex launch was not re-run after round 1 (fences only); `conductor.test.tsx` "LIST keeps the asking agent first" is an inherited vitest red (jsdom canvas suspected, unproven)).. 16 MERGED #1000 (A PROJECT KNOWS ITS REPOSITORY, B37 B38 B39: a Project registers its GitHub repository (owner/name) in a registrations file; the hand to Codex in YOLO clones it into a sibling worktree bound to github.com (URL `https://github.com/<owner>/<name>`, `GH_HOST=github.com` on the call; an origin on another host is parked beside as `.not-github-<stamp>` and the hand refuses `clone_host_mismatch`); a registrations file that exists but cannot be read, truncated or zero bytes alike, reads REPOSITORY · NOT READ with Retry (Register hidden) and the hand, the preview and registration all refuse `repository_store_unreadable` without overwriting it (RULING: only an absent file means no registrations); the kernel target and receipt name `repository:github.com/<owner>/<name>`; CLONED · owner/name · hh:mm rides the answer and a later launch refusal, never back to CLONES; Get Info shows the clone's Folder; the clone token wraps at 393; the owner's agent flip is remembered per Project; the Door shows no "0 open PRs"; a meeting drops into a Project; Astra r1 → r2 DNR (two P2s paid: preview keeps NOT READ whatever source resolves; Info names the folder) → verified by Muad'Dib, FAST 15,038 green after one census fix (an aware UTC stamp on the parked clone). Open from #1000: a sibling worktree does not isolate credentials (inherited custody debt); the kernel receipt's ref cannot hold the `~` folder path (the hand's answer carries it); the "THIS BECOMES THE PROJECT'S NAME" prose line is still on the Door; new fences were not shown failing on the r1 head; two 393 cases in hand.test.tsx now pick rows by accessible name (per-word spans from #989)).  Queued: ; 17 MERGED #1002 (A MERGED PR REACHES THE PUBLISHED UPDATE ONCE, B50 B51 B52 B53: a merge is reported in the update that is actually PUBLISHED, once, as `Merged: <PR title> (PR #n) <link>` (a discarded or superseded draft, or a published body the owner cut the row from, does not use it up; a merge row matches as a whole line, PR #1 never inside #10); while a launch has an open PR the Heartbeat polls it round-robin by last-read stamp, at most 10 per poll, one `gh pr view` each, every 120 s from the previous START (≤ 300 gh calls/h; none with no open PR; a failed read keeps its PR in the rotation), so the receipt lands within one poll with up to ten open PRs and within ceil(n/10) polls beyond, no press; the Room receipt `DONE · <PR title> · PR #n MERGED · time` with Open PR and the GITHUB.COM chip; the sent document opens `# <Project> · Update · <date>` and names never ids (coverage in plain words); RULING: an unsupported model claim is OMITTED whole from Send/Copy, continuation lines included (an emptied section reads "Not checked.", the last line "N claims not checked, kept on the desk.", the stored update keeps every claim and its UNVERIFIED lamp); RULING: an update with nothing verified is refused NOTHING VERIFIED (`nothing_verified`, 400 at preview and prepare, before any byte is frozen; Source Coverage is not content; a verified merge row keeps it sendable); the Draft-with-model egress chip reads `UPDATE DRAFTS · <host>`; Astra r1 → r2 DNR (both leftovers paid) → verified by Muad'Dib, FAST 15,058 green after one load flake (`test_conductor_r4_hand_close::test_kept_worktree_stays_registered`, KeyError 'cleanup' under load, 36 passed alone). Open from #1002: the folder Send chip still reads THIS DEVICE, not `FOLDER · <name>` (~30 tests + the egress canon); at 393 the Room receipt wraps `CONTRIBUTING.md` across lines in a ~109 px column (a receipt row of its own at narrow widths is a face decision); the drafter's manifest now carries `closure_lines` (fixture regenerated)).; 18 MERGED #1001 (THE REST OF THE FIRST AFTERNOON, B31 B33 B34 B35 B36 B40 B54–B57 + stale glass: one gh sign-in truth (the stored check, else gh's config read as `SIGNED IN · KAROLSWDEV · FROM GH CONFIG` with no check time; footer NOT CHECKED until a real probe); every "no model" word reads the hub's summary route, explicit OFF reads SUMMARIES OFF on all five faces, doctor and MCP; Install hooks per ready agent without hooks, with a receipt; the default agent is the first with a KNOWN sign-in, `CLAUDE CODE · SIGN-IN UNKNOWN` on the selected card, both-unknown reads `CLAUDE CODE · YOLO`; drawer/Conductor icon labels two lines middle-cut; the aftercare card's count is live, leaves at zero, and a null/missing count reads COUNT · NOT READ with the card kept; RULING B57: exact self-name recognition (full name, first name, aliases) never depends on the People store; only the ONE-EDIT match ("Carol" = Karol) needs no Person with that exact name, an unreadable store turns the fuzzy match OFF, an explicit Person link always wins; a You group (Your name / Also called) in Settings › People shared with first run; a found needs-you 500 (reused `people` variable) fixed; six stale glass files re-anchored (philo13_04 asserts the count then SUMMARY STORED; the no-summary row reads NOT RUN after #985, OFF only when summaries are off); merged with #1000's port of its default-agent code (one copy of each function); Astra r1 → r2 DNR (both paid) → verified by Muad'Dib, FAST 15,102 green, philo13_04 20 passed alone after two load reds). Open from #1001: Jira/Confluence read NEVER CHECKED until a probe while the first-run card counts their acli profiles; a GitHub sign-in adds no Send destination; `needsYou.ts` carries no fuzzy owner match (faces show the hub's answer); doctor's route fallback reads the local DB even for a remote hub; hs168 has two cases skipped without a real gh sign-in).. 09 MERGED #980 (THE MORNING TELLS THE TRUTH: the owner's same-day Generate REGENERATES the day's brief (same id, newer time, fresh items, shelf states kept; the scheduled job still makes one a day); the Brief lists the day's additions (Decision made, Project added, Person added, people counted from creation stamps only); title "Brief · Wednesday 7 Oct 2026" on the Chair window's title bar; one date range; The week is never empty (this week's decisions and due items, one NO CALENDAR · Connect Button, else NOTHING THIS WEEK); ONE NUMBER from the hub: members with an agent's ask folded + each unread source + each arming recording, read by the drawer head, the Dock badge and the bell; a self-made decision is DECIDED not to review; every Needs row shows its kind word; a window opened by the owner's gesture comes to the front; the scheduled Brief is KEY-FREE (People never read, counted by stamps) and SAYS so with one counted row "NOT READ · People (locked) · Generate for the full brief", kept whenever People was not actually read (a refused owner read too); an unread source is counted once as a source not read, never also a waiting thing; the Send well reloads its preview when generated_at changes; the atlas regenerate cases prove the new claim (add a decision between generations); Astra r1 DNR → r2 RWC (capped) → the three leftovers fixed and verified by Muad'Dib (17 glass + 1 xpass, FAST 14,927 zero failed)). Open from #980: the heartbeat's notification identities still come from items and members, so an arming recording or an unread source raises the count without a new notification; the two graph-walk reds (j1.first_words_continue_later.idle waits for the retired arrival-headline; j4.meetings_import.imported errors on an isolated HOME without Whisper) are red on clean main too; lane 05's `test_pressing_generate_regenerates_the_scheduled_brief` now XPASSES: un-xfail it (hygiene); `DeskApp.test.tsx` still fails to load on main (a mock lacks useTrustWindow, since #939).  11 MERGED #986 (DOCTOR SPEAKS PLAINLY: one honest line when the hub is not running (HUB · NOT RUNNING · start it with holdspeak, exit 0); the model hint names the file that is missing; only the real starter model gets SKIP + Set up local AI, a missing custom model is FAIL with its name and path; rows renamed in the owner's words (Dictation AI model, Meeting plugins, Where AI runs, Cloud AI check, notes readable; engine ids print as llama.cpp / OpenAI-compatible server, wire ids kept in data); the Agents card says 2 AGENTS FOUND with a TOOL token on tmux; connection tokens one per line; FIVE SEED NOTES (Start here, About me, 1:1 prep, Current priorities, Weekly update), the developer guard notes parked as text in docs/internal/PARKED-SEED-NOTES.md; THE PHONE MENUS FIT A PHONE (RULING, Phase 15 amendment to PHILO-13-17 C7 Q3 recorded in the Phase 15 PROPOSAL): at 393 Go = Needs you / Brief / The week / Capture, the Dock's places, the Projects, New ▸ Thought / Meeting / Project / Person; no keycaps anywhere at 393 (shared menu renderer + Search rows); Desk/Object/Window reached from the window's own menu (long press at 393, right click at 1440); a new walker action long_press in the closed UI vocabulary; two atlas cases re-anchored and walked with real touch; nine glass files re-anchored; Astra r1 RWC → r2 RWC, conditions paid; FAST 14,944 zero failed). Open from #986: a fresh desk's Desk and Chase guardrail evaluations load nothing (the guard notes are parked; intended for day one; an existing desk keeps its notes); NO desk verb restores a parked guard note on Desk or Chase (modes load notes by fixed id; the doc gives the two API routes); the printed-output jargon fence protects listed strings, not plain English; the atlas case walks long_press at 393 only (1440 uses the bar's Desk menu); doctor with an isolated HOME and no URL falls back to 127.0.0.1:8765 where another hub may answer; Knowledge/Agent/Workflow/Workbench/Thread creation lose their direct Chair-menu route at 393 (Search and the Floor's New menu remain).  10 MERGED #985 (THE ENGINE SETUP TELLS THE TRUTH: READY only from the authority: the Concierge asks the same checks a real assignment runs (read-only fit), every picker/probe/saved-row path reads it, a probe can only turn a row FAILED; groups read READY / LIMITED (the owner-facing names of what cannot run, as tokens) / INCOMPATIBLE / UNKNOWN · TRY; the library and starter profiles claim the result schemas the executor really checks, so the owner's 27B LAN box reads READY for Thoughts, Writing, Meetings and Speech (RULED: READY = ready to attempt through a validated adapter); a malformed structured result is a named receipt on the Thought window (STRUCTURED RESULT · NOT USABLE · engine), the vitest uses the real projection; a blocked work counts as served by its own assignment only when that assignment is bound, enabled and ready; the internal Chat group is no longer a row; speech is proposed only from speech engines (the device's Whisper); the LAN box on first run: Use a server on my network opens the Concierge's own add-engine row, a cold Mac keeps Set up speech · 144 MB (Whisper only) beside it, the gesture sets the Default for AI work once, the card reads THIS DEVICE / LAN · host / the host; Use these refuses a WAITING group (SPEECH RECOGNITION · WAITS · SPEECH DOWNLOAD); the Models window stays and shows the receipt USING · model · N GROUPS · N LIMITED · DEFAULT SET, every failed group as GROUP · TOKEN, the cause said once with its count, failures survive a reload (persisted on the kernel receipt); the chip reads → LAN · 192.168.1.43, never external reach; an importing meeting reads IMPORTING and never All summaries done; one decimal size rule everywhere; the tool probe (1 token, fixed text, no owner material) goes only to a keyless private/loopback IP or under the owner's MY SERVER token (RULED acceptable; it can reach a keyed gateway by his choice); the .43 box answered: /props supports_tools true, a tool call 200 in 0.68 s; Astra r1 DNR → r2 DNR (capped) → the four leftovers fixed and verified by Muad'Dib (15 glass, FAST 14,951 with one known flake passing alone)). Open from #985: whether a malformed structured result is a NAMED failure on the dictation and meeting-plugin faces is untraced (the Thought window is); the Check line still reads READY · model · TOOLS; the 393 menu-bar chip shows only its glyph (the LAN fact in its title); a model-switch/update Codex prompt is not a trust prompt (not re-verified); test_thread_service::test_keep_defaults_to_a_note flakes in FAST (twice today, passes alone).  Building: 05 MERGED #975 (STRONG DEFAULTS: the Conductor's routine answers already ran on the global default (owner work via `run_owner_draft`); the lane chip's NOT SET was a face defect: it cached an empty read and read a this-device default as a cloud host; now read on every open and on `desk_changed`; the morning Brief GENERATES ITSELF at 06:00 (`brief_enabled`, `brief_hour`; the cadence loop job stays off; quiet hours do not hold it; no model, no egress) under a new READ-ONLY principal `brief-conductor` (the `read` right only; it cannot create a profile, an assignment or a decision; the roster read now requires `read` not OWNER); a source the rule cannot read becomes `NOT READ · <source>` with the receipt GENERATED · PARTIAL (the Door fallback included); Settings › Rhythm gets a Morning brief group; Anthropic reads NOT SUPPORTED YET (readiness `not_supported`, connect refused 422 over HTTP and MCP storing nothing, the library summary `none_ready` when nothing is ready, OpenRouter / OpenAI-compatible offered beside); Astra r1 DNR → r2 DNR (capped) → the three leftovers fixed and verified by Muad'Dib (glass 4 + 1 xfail, FAST green). Open from #975: `test_pressing_generate_regenerates_the_scheduled_brief` xfail until #980 (lane 09) lands; a hub started after 06:00 generates on its first tick (~09:05 for a 09:00 start); the Anthropic execution adapter is queued; the old `anthropic_runtime_missing` reason is gone (no consumer found)). REHEARSAL 2 MERGED #1008 (`docs/internal/philo/phase-15/rehearsal-2/BOUNCES-C.md`, B58–B89: P0 0, P1 7, P2 14, P3 11, 78 shots; the second morning on main c078a7938 under a time-machine clock at 07:05 and 08:10: the Brief made itself key-free but carried none of yesterday's decision, launch, PR, merge or sent update (B58); the open Brief window showed yesterday's until a reload (B59); Needs you counted two STALE source rows HoldSpeak caused by its own quiet hours and Retry only reloaded (B60 B61); YOLO held the agent's ordinary reads and its own test run, 11 holds in 12 min, and a cut call's Raw showed the pane with no Approve (B62 B63); NOTHING VERIFIED read only the model's tag and an all-inference draft with a false Next Action went out (B64); the merge receipt reached the Room at the first poll with no press and the published update carried `Merged: <title> (PR #4)` once; folder Send works; one Needs number held. Re-observed fixed: B02–B04 B08–B12 B14 B19–B21 B30 B35 B36 B38 B39 B41 B42 B45 B46 B50–B54; B43 B57 partly. NOT REACHED: Claude Code (no key), email (no Resend key), live recording, calendar, People, Parked, The week, the lane at 393). 19 MERGED #1010 (THE BRIEF CARRIES THE DAY, B58 B59 B65 B73: the morning Brief has a row for every confirmed decision, done action, agent launch, PR opened (gh `createdAt` stored once as `pr_opened_at`, backfilled on the next poll for PRs known before), PR merged (Room-repo merges by no agent too, deduped by URL) and update sent or published, each plain words with its local time, each opening its object; RULING ORDER (Astra's, adopted): merged PR → sent update (published as fallback) → opened PR → confirmed decision → done action → agent launch → recorded/added/requested rows, newest first within a kind, the Chair's 3-row cap stays; RULING PERIOD: the 07:10 Brief covers the previous day 17:00 through 07:10 inclusive; a launch ledger or Room record that exists but cannot be parsed reads `NOT READ · Agents` / `NOT READ · Room merges` with the reason (`LaunchLedger.read_all()` raises `LaunchLedgerNotRead`), and NEVER DELETE: before any save after a failed read the exact bytes are parked as `agent_launches.json.not-read-<stamp>`, a failed park blocks the save; a removed file clears the cache; the open Brief window re-reads on the hub's write announcement and on page focus (no timed poll); a hub started after the Brief hour makes the missing Brief at once; the 2-minute launch poll also discovers a NEW PR by `gh pr list --head <branch>` inside the 10-per-poll ceiling, retired when the list is empty and the branch is gone from the clone; Brief details are plain words and local time (no JSON, hash, UTC); the Chair rows show their detail in the library row's `cells` slot (face change ruled by Muad'Dib under the autonomy grant, no canvas); Astra r1 DNR → r2 RWC (park-aside paid) → FAST 15,181 green after two of this lane's reds). Open from #1010: a RENAMED branch (old local ref gone, PR under the new name) retires discovery; recovery only by re-registering the worktree and a sweep; the glass launch row is hand-written in the follow-through's shape (the launch-to-merge path is unit-proven); the Chair has no timed poll fallback).  20 MERGED #1011 (YOLO LETS THE AGENT READ; RAW APPROVES A CUT CALL, B62 B63 B66 B67 B68: in YOLO an agent reads git config, runs `gh --version`/`gh auth status`/`gh pr view`, expands `$?` and a worktree-reading `$(…)` as text printed by echo/printf, runs a script inside its worktree, and may redirect or tee such output inside the worktree, without a hold; a `$(…)` used as a test/[ operand, path, program or assignment holds; substitutions are resolved in the EFFECTIVE folder after every `cd` with symlinks resolved (Astra's `cd sub && echo "$(cat secret)"` escape fenced through the real hook and hub); writes of git config, pushes to another branch and anything outside the worktree still hold; a cut call (over the 120-char head, which STAYS) is approved in RAW: the hook also sends the whole redacted command to the hub, kept in `gate_full_calls` only while HELD (the insert is conditional on HELD in one statement, the decision deletes in its transaction; Astra's race fenced), owner-only `GET /api/gate/proposals/{id}/command` (agent 403), NOT encrypted (Astra's ruling: the temporary owner-only redacted store is acceptable under the #998 risk); the observer scrubs `args_full` at any depth and withholds the whole `full_call` result, fenced by real agent + owner MCP reads of `pipeline://events/recent[/GateService]` at HTTP 200 with records present; `whole` only at the declared length, else Raw reads `HELD · <reason> · CUT · n OF m CHARS` with Deny only; Raw's Approve/Deny leave `APPROVED · hh:mm` / `DENIED · hh:mm` (409 → `NOT DECIDED · hh:mm · ALREADY <state>`); a Deny reaches the agent with its reason word ("denied from the desk: OUTSIDE THE WORKTREE · /tmp/pr_body.md … Do not try it again in a different form"); a queued Re-brief has Take back (`TAKEN BACK` / `NOT TAKEN BACK · ALREADY SENT`, owner-only); RULING B68: "blocked by the desk / the gate / the owner / from the desk" is a decision, "blocked by" anything else (hook, firewall, branch protection, a failing check) is a problem, Python and `needsYou.ts` alike; Astra r1 DNR (4 P1 + 3 P2 paid) → r2 RWC (two conditions paid) → FAST 15,259 green). Open from #1011: a secret in an unknown shape inside a cut command lives redacted-only in the owner's temporary store while held; the real Codex launch was not re-run; two inherited glass reds not reproduced on main (`test_philo14_c2_lane_actions_glass::test_rebrief_receipt_survives_send` waits on `/steer` since #996 moved Re-brief to `/rebrief`; `test_hs201_09_connect_engine_glass` at 393 wants a Models menu item); `scripts/gen_docs.sh` stops on an out-of-range line cited by `voice.json` (`meetingPathBlocker.ts:95`)).  21 MERGED #1012 (THE SECOND MORNING TELLS NO LIES, B60 B61 B64 B69–B72 B74 B75: RULING a source is never STALE because of HoldSpeak's own quiet hours: a held sweep moves every armed Watch's next check to the quiet end (`WatchService.hold_armed_until`), the rows read `QUIET UNTIL HH:MM`, are not counted, are not Brief "Not observed" rows, `quiet` ranks between stale and available; the first sweep after the quiet end runs at once; a source that missed its check before quiet began stays STALE (`missedCheckAt` kept when a past next check is moved forward); Retry on a source row re-checks THAT source with a receipt (`CHECKED · Meetings · 07:06` / `NOT CHECKED · … · <reason>`) and carries the GITHUB.COM badge on a remote source; a connector that exits 0 with no output is a failed check `connector_no_answer`, a valid `[]` a successful unchanged read; RULING B64: verification is decided on the claims set, not formatting: a claim is verified only when it is not an inference and has evidence refs, or the owner reviewed it; a sentence not covered by a verified claim is omitted whatever its formatting, headings included (only the drafter's six section headings pass); an update with zero verified claims is refused NOTHING VERIFIED at preview and prepare; Accept / Reject on every claim row in the editor (owner-only route `POST /api/updates/{id}/claims/{span}/review`; `OMITTED`, `REVIEWED · hh:mm`); current acceptance overrides old flags and markers; only NEW owner-authored words count as reviewed (pasting or re-formatting the model's sentence is not review; the UNVERIFIED mark is recognised in any styling); a Project with nothing observed drafts one unreviewed `NOTHING TO REPORT` claim that sends as "Nothing to report." once accepted; one freshness state per source in the Room and Needs, a next check never in the past; a done action's Room row reads `DONE · <time>`; the drafter drops a model sentence that repeats a Merged row, matched on repository AND number; the Updates list names the model and host, never the assignment id; source rows read `GitHub · owner/repo`, `Meetings`, `yesterday 21:23`; the Door reads a gh-config sign-in as ready and offers Choose a repository at once; Astra r1 DNR (4 P1 + 2 P2 paid) → r2 DNR (2 formatting P1s + the NOTHING TO REPORT ruling paid) → FAST 15,282 green after seven of this lane's reds). Open from #1012: B75's rehearsal-2 NEVER CHECKED on Settings › Connections after a SIGNED IN first run is not explained; the claim-review verb has an HTTP route only, no registry operation (rigs save an owner line instead); the Accept/Reject controls appear only while the update is a draft).  22 MERGED #1015 (DAY-ONE.md v2, THE RUNBOOK: sections 0–10, every step Do / See / Else / Paid with the face words and the bounce id; v1 parked as `DAY-ONE-v1.md`; section 10 lists every unpaid bounce; NEW B90 (lane 22): the second-morning Brief starts at 17:00 the day before, Friday 17:00 on a Monday, so day-one work done before 17:00 is not in it). Queued from rehearsal 2: B76 drag-drop a meeting onto a Project does nothing; B77 a commitment the transcript says reads NO SOURCE; B78 'Carol' stays his name in the Room, the agent brief and updates; the P3s B79–B89. Held for load: 11 (doctor/first-run copy, seed clutter, the 393 Go menu), 12 (UGLY: Dock sprites, layouts, the Send well path). Queued from the inventory: the Anthropic key does nothing (no execution adapter); YOLO answers nothing routine without a Cadence-drafts model; launch → PR → merge has no glass/atlas proof; the Brief does not generate itself (cadence loop off by default); the 393 Concierge footer overlap; `test_hs201_09` waits for the removed `arrival-display`; the j5 route_disclosed/planned_host cases block at the old `concierge-add-engine` setup step.

PHILO Phase 14, The Desk Is Objects, is CLOSED 2026-10-07 (chartered, canvassed, built and closed in one day; 21 product/docs PRs; handover `docs/internal/HANDOVER-MUADDIB-XXXIV.md`; built shots https://claude.ai/artifact/FgdD7jmm9YXv3Y7xcBf8hf; canvas https://claude.ai/artifact/E7E4JwVzSD9ieY6hpDQFjY). Record of every merge and every open condition follows.

**PHILO Phase 14 — The Desk Is Objects** (chartered 2026-10-07 on the owner's three
catches: the Conductor's face "stinks", the Desk went "Windows 1.0", features are
"apps" and the explorer shows `[ ]`). Proposal: `docs/internal/philo/phase-14/PROPOSAL.md`.
Three movements: A objects (drawers, icons from the mold, drag as composition, apps become
views), B material (bevels back, chips become lamps, the Chair as a screen not tiles),
C the Conductor as objects (agent icon, drop to hand, the agent's window as its lane).
Merged: C0 lane backend #925 (the hub keeps the agent's timeline: `agent_session_events`, spooled by the hook with no DB wait and drained on lane/coder reads; worktree commits/files read on request; PR `ci`+`checks` kept; `control_mode` on the launch; `GET /api/agent/launches/{id}/lane` owner-only, every served text secret-redacted before the cut, `not_read` on failed reads; Astra r1 DNR → r2 RWC; FAST green after two fence corrections). Open from #925 (Astra's condition): the spool drains only on a lane or `/api/coders/sessions` read, no hub timer, so events collect on disk while nothing reads (≤5000 files per drain); Codex `apply_patch` input shape unverified; no MCP tool for the lane. Merged: lane 00 canvas #927 (`docs/internal/philo/phase-14/canvas/`, 45 shots, ALL FENCES HELD; page https://claude.ai/artifact/E7E4JwVzSD9ieY6hpDQFjY). The owner deferred ("all three are viable ... you just need to push it through"); RULED: **A Workbench** + C's station track on the lane; icons get a PixelLab overhaul (owner: "pretty cringe"). Owner 2026-10-07: "go as autonomous as you possibly can - you make ALL the calls, including the icon selection": Muad'Dib ratifies canvases and picks the icon direction; shots stay in the PRs as the record. Merged: B1 species #932 (the object species in `web/src/desk/surface/objects/`: DeskIcon+IconLamp, IconGrid with 2-D roving, ObjectList with no `[ ]` and an a11y-true 393 fold, GetInfo, TimelineRail, StationTrack, AskWell, PRCard, FilesChanged, ConfirmLine, NeedsRow, DropTarget/DragGhost; bevel grammar; lamp tones info/ask; Astra r1 DNR → r2 RWC; FAST green, two real-hub tests and four vitest files failed only under load 160+ and pass alone). Open from #932 (Astra's r2 conditions): the Chromium probe does not exercise native Space/Enter on DeskIcon/ObjectList nor compare NeedsRow's computed lamp colour (jsdom covers them); TimelineRail has no paging and StationTrack takes precomputed stations (C2 owns the mapping). Merged: A0b the mold #934 (D1 Workbench+ installed: 17 world sprites by kind with `_sel`/`_stale`, one kind one silhouette, `agentSpriteName` picks Claude Code/Codex, 16 Dock/chrome glyphs redrawn; the old mold PARKED under `web/public/desk/sprites/_parked-2026-10-07/`; Astra r1 DNR (Codex turned Claude on hover) → r2 RATIFY; FAST green). Open from #934: kb/roadmap wear `artifact`, story wears `note`, capability kinds keep `cartridge` until they get icons; `game`/`layout` fall to note; the idle mic and Speak glyph are dark on the dark Dock; the 32 px world set is scaled, not drawn (redraw with the list view); memory stays the chip. Merged: C2 the agent's lane #933 (a launched agent's face is its LANE: `web/src/desk/lane/`; station track, the question with voice answer + Use draft + egress, the vertical rail from the C0 route, PR card + files changed, Deny/Approve on a held call, Re-brief, Stop (two presses; ends the agent's session; the launch becomes `stopped_by_owner`), Open PR; the tmux pane behind the title bar's Raw; every lane action bound to its own launch/session; an answer must name the current `wait_id` (409 `wait_not_current`); every unread collection reads NOT READ; Astra r1 DNR → r2 DNR (3 left) → Muad'Dib verified the 3 fixes by running her 8 real-hub fences; FAST green). Open from #933: the lane's species are local copies of B1's (`lane/species.tsx`), swap to `surface/objects` later; BRIEF shows word count not sources/KB/checks (hub lacks it); RUN shows no result unless the event carries one; Files changed has names only (no +/−); the draft chip reads NOT SET without a drafting model; `npm run typecheck` fails at `HandSheet.test.tsx:464` on main too (inherited). Merged: C2b #941 (the lane composes the library species; `lane/species.tsx` parked; AskWell gains `listenSignal`/`inputRef`/`disabled`/`arm`; `busy` disables only Answer, a send stalled 20 s reads `NOT CONFIRMED` and never resends by itself; the 393 footer wraps; Astra r1 RWC, conditions paid and verified by Muad'Dib; FAST green). Merged: A2 the drawer #937 (a Project opens as a DRAWER: `web/src/desk/drawer/`; icons or a real list; Get Info window with Rename/Park/Open; the Room one press away (RULING: the drawer is the Project's face, the Room its intelligence); the Floor list is the ObjectList species, `[ ]` is gone; members carry the producer's id+kind; drawers and Info windows return after reload; Park leaves `PARKED · <name>` + Restore; NOT READ/PARTIAL on failed reads; GITHUB.COM at Open PR; nine atlas list cases re-anchored and run; Astra r1 DNR → r2 RWC; FAST green). Open from #937 (Astra's r2 conditions, with owners): a flight `decision_record:<id>` member has no Open verb (lane C4/fold); the Chair's Needs-you ProjectButton (`ChairHome.tsx:1658`) and the `:1800` fallback, plus the other `openProjectRoom` calls at 768/781/1799/1833/2031, still open the Room instead of the drawer (lane A1/A5 own chair/: a follow-up A2b after A1 merges); `members.length || 0` in DrawerWindow.tsx:61 is scanner debt (HeadFacts hides zero; no display effect); the inherited `test_philo13_06_open_glass[1440]` red on main (A1's cascade fix addresses it). Merged: A1 the screen #939 (THE CHAIR IS THE A-1 SCREEN: `web/src/desk/screen/`; drawers with the Room's own count (`roomCounts`), loose objects, agents, the Conductor drawer (count notch; the ask lamp only when one asks or a call is held), Needs you, Parked; the four tiles parked under `data-layout="tiles"`, never set; windows float, saved positions restored, unsaved placed by C1-1 or cascaded; one-press TALK at the screen's foot-left; phone Needs you/Brief/The week = Go's first rows; failed membership reads read NOT READ + Retry, never loose; arrows by rendered position (`surface/roving.ts`); Astra r1 DNR → r2 RWC; FAST green). Open from #939 (Astra's r2 conditions): the J2 atlas case `engines_both_missing` does not create its own no-assignment precondition (host-dependent; make the setup deterministic); two marked glass specs (J3 in test_philo13_06, the fresh-Chair case in test_philo13_09) no longer start fresh under the `chair_windows_open` marker — fence opening from the screen; the fresh-arrival test's 393 path uses Enter, not Go; ~40 membership GETs on a 20-Project desk (cached, shared); the long desk scrolls uncapped; `DeskApp.test.tsx` fails on import on main too (mock lacks `useTrustWindow`). Merged: C3 drop to hand #946 (drag a handable object from the screen or a drawer onto the Conductor drawer or an agent icon: a ghost and a dotted path, the target lit; in YOLO a ConfirmLine (item → agent, `CLAUDE CODE · YOLO · hs/<branch>`, Brief ▸, Cancel, Hand, the launch's egress chip) then the receipt; Secure/Normal open the HandSheet on the dropped agent; at 393 no drag, the confirm line from the verb; the hub emits a coder frame on session registration and the confirm re-reads flights until the agent appears; Escape cancels the hand; Astra r1 DNR → r2 RWC; FAST green). Open from #946 (Astra's r2 conditions): the registration frame carries the raw `agent:session-id` in `capability.id` to every websocket client (not a credential; the same shape as the existing coder frames; ruled: keep, record); a registration burst can cause two `/api/coders/sessions` reads per browser; the new agent's icon can sit behind the still-open drawer (evidence shows it in the DOM, not unobscured); no issue object exists on the screen/drawer to drag yet; drag from LIST rows not wired; the Door/Room row verbs and ⌘K still open the sheet in YOLO. Merged: C4 the fold #947 (the Conductor drawer window `web/src/desk/conductor/`: ready agents (version, hooks, sign-in; Install hooks), live agents keyed `launch:<id>` with lamps, askers first, ended launches of the last 24 h with their receipts; `N AT WORK · N ASK`, `N OF M` from the hub's own live count and cap (`/api/coders/sessions` serves `launches` and `history`; flights carry `launched_at`/`ended_at`); Stop/ARM bound to the pressed launch via `laneStore.stopLaunch`; the Dock's Agents is now Conductor (⌘3, `/conductor`); the Agents application (`CompanionCore`) and the Chair's AGENTS section PARKED; the MCP verb `go.inspect-personas-and-coders` → `go.open-conductor`; the C2 glass setup goes Dock → Conductor → Open; Astra r1 DNR → r2 RWC; FAST green). Open from #947 (Astra's r2 conditions): the 24 h history is bounded by the ledger's 200 records and a vanished session with no stop/merge timestamp falls back to `launched_at` as its end; the saved agents' (recipes') Dock roster is gone (they stay under Floor → List → agent); the atlas has no Conductor case; the `ComponentsPage` a11y vitest times out under load in every lane (not in the inherited baseline; passes alone). Merged: A2b #945 (every generic Project path opens the drawer: the Needs-you Project button, its Project-only fallback, the screen's drawer icon, the palette, the primitive's surface key; explicit Room paths stay: the drawer's Room Button, the coverage repair, the Door's create, and a proposal row opens the Room with THAT proposal selected; degraded Room reads read `DECISIONS · NOT READ · PARTIAL` + Retry; a decision record's hand-off can launch: the tmux session name is bounded to 59 chars (40 of the slug + 8-hex hash + suffix), the full id stays on the launch; Prepare opens a decision record through `/api/decision-records/<id>`; Astra r1 RWC → r2 RWC; FAST green). Open from #945 (Astra's r2 conditions): the 8-hex name digest is not collision-proof (two 40-char-equal slugs share a prefix; the random suffix makes an exact collision unlikely; ledger identity is the full id); the committed launch fence inserts rows with a `source_type` the producer refuses (fence with the real `DecisionRecordService`); a malformed/legacy record with no usable source gets an Open that fails without a receipt; the proposal fence checks selection and Confirm, not focus/scroll; seven inherited glass reds (five in test_philo11_05a expecting the Chair's Brief area, two in test_builtin_send_folder expecting the palette to reach the Room) and the J10/J11(1440) atlas cases → lane A1b. Merged: A1b the arrival fences #951 (the inherited glass reds and 84 atlas cases re-anchored to the screen: every case that reads a Chair window opens it first, Window ▸ Chair ▸ name at 1440, Go ▸ name at 393, the Dock's Speak for Capture; the retired Go ▸ Chair submenu steps gone; first-value gate checks read `chair-desk`; the 393 aftercare chains wait for Capture and return with Go ▸ The week; J3 is its own fresh-Chair test; the census walk knows the Conductor; Astra's r1 ran 130 of 176 walks and timed out without a verdict, her data mined by Muad'Dib (no assertion weakened anywhere; 106 walks were gesture debt) → r2 swept by the lane: 59 of 84 changed cases pass at both widths; FAST green). Open from #951 (Astra's walks + the lane's, with owners): PRODUCT GAP `philo603.toast.arrival`: Capture starts closed at 1440 so the MEETING READY card has no slot and floats over The week's summary (at 393 the summary under the card has no geometry) → lane A1c/B2; at 393 after a trigger the aftercare card takes the front (`j6.summary_text`, closure s2) → a `then` wait; the fresh-HOME brief always carries a 'No engine for summaries' item so five 'empty/ALL HANDLED' cases fail (j10 reload_persisted, j10 route retained_after_reload, p11 brief_last_ack/defer, philo404 all_handled) → re-anchor or decide; `p11.meeting_summary.chair.sent` sends 200 but no sent row matches the case's destination (unchecked); rig gaps: `route_failure` substitution unimplemented (j11.create_refused, j2.read_pending/read_unknown), `browser_audio_device` (j4 record_start/record_only); setup debt: j2.summary_missing_only and j3.speech_missing (assignments set/clear 400), j3.profile_unbind (profile_id never captured), j9 shade cases (provider reply not installed in the hub process), j4.meeting_stop (meeting_active false), `arrival-run-intel` never appears (j3 assigned_ready/profile_delete, j9.shade_open); j2 `expected_revision: 1` is a known weak point; WAV imports on an isolated HOME stop at the 300 s fixture limit unless `HF_HOME` points at the real Whisper cache with `HF_HUB_OFFLINE=1` (also Astra's j5 block); 46 atlas walks were never run by Astra (her hour ran out). Merged: C0b the spool timer #953 (the hub drains `~/.holdspeak/agent-events/` on its own 2 s tick while a launch is live, under the reads' file lock, 5000 files a pass, oldest first; liveness through the production `LaunchReads` path, a failed or timed-out tmux probe is UNKNOWN and drains anyway (never cached as none-live); when the last agent dies the timer drains once more then idles on one ledger stat; a file whose rows committed but whose unlink failed is never replayed in-process; no notify added because the question path (`agent_sessions.json` → coder frames) and the held-call path (`GateService.on_launch_hold`) never depended on the spool; Astra r1 DNR → r2 RATIFY (she re-ran her tmux reproduction: 101 probes, zero spooled files); FAST green). Open from #953: the committed-but-not-unlinked memory is process-local, so a hub restart between a failed unlink and the retry can replay those rows (Tenet 7 debt); events of coder sessions HoldSpeak did not launch still drain only on a read; a read that arrives while the timer holds the lock reads the DB as is (newest event up to one tick late); `drain_spool` swallows SQLite errors on insert without a log line (incl. 'database is locked'); the real-hub timer test skips without tmux (CI unverified). Merged: A1d #959 (the 393 'loose notes with no icons' seen in a re-shoot was the glass test shooting before the sprites decoded, NOT a product defect: every `/desk/sprites/` request 200, all screen images 64×64 at both widths; `_images_loaded` helper in `tests/e2e/glass_infra.py` waits for every image in scope and fails naming each unloaded src; the fresh-arrival test waits for the seeded note then the images; Astra RATIFY, no conditions; tests/e2e-only diff, covered by main's FAST). Open from #959: at 393 the seventh Needs-you row (Priya Nair) sits under the Dock, scroll reach unverified; a loose `person` shows the people-ledger icon (kinds.ts maps person → people; A0c #956 fixes it). Merged: A0c the 32 px world set #956 (18 kinds drawn at 32 with PixelLab from the D1 64s, picks and every candidate on `docs/internal/philo/phase-14/icons/32px/sheet.html`; `web/public/desk/sprites/32/` with `_sel`/`_stale`; `spriteUrl(..., size)` and `listSprite(url)`; ObjectList, NeedsRow, ConfirmLine, PRCard, the drawer badge and the lane title show the 32, the screen/drawers/Get Info/drag ghost keep the 64; `kinds.ts` gives every kind its own D1 file (action item, PR and person were wearing note/artifact/ledger); CODEX KEEPS ITS FACE ON EVERY FACE: the screen's compose, the drawer's members, the lane title, the hand confirm line and the Components gallery all dropped the agent and drew Claude Code's robot for Codex, fixed at source with a 12-case `agentIdentity.test.ts` fence; the long-red `test_philo14_a0b_codex_sprite_glass.py` was that inherited defect, not a stale test, and passes with its assertion unchanged; the idle mic and Speak Dock glyphs lightened, originals parked; Astra r1 RWC, conditions fixed and verified (FAST green 14,777; a0b + a0c glass green). Open from #956: window title icons (drawer, Conductor, Info; 20 px) still scale the 64; kb/roadmap wear `artifact`, story `note`, capability kinds `cartridge`; the cartridge 32 loses its DATA text and `conductor-drawer` touches the bottom edge (no rim there in `_sel`); the lightened Dock glyphs unchecked on a dark-theme Dock. INHERITED, found by this lane: six tests red on main since A5 #935 (3 in `openGrammar.philo1306.test.tsx`, `a2_drawer` Needs-you Project button → drawer, `a2b_paths` proposal row → Room with selection ×2) → lane A5b building. Merged: A1c the summary card's slot #954 (RULING: when a summary lands and Capture is closed, Capture OPENS at both widths and the MEETING READY card sits in Capture's slot, nothing floats over another window; an unmoved Capture grows 100 → 300 px bottom-anchored while the card stands and Needs you shrinks by the same; a Capture the owner moved or sized keeps its geometry and the whole receipt is reachable by scroll (`justify-content: safe center`); Capture grows only while ITS slot holds the card (a card in Meetings leaves it alone); the card's host is React state (`publishAftercareHost`), never a selector (the null-read guard caught a `document.querySelector` in r2 and it was removed); browser geometry fences in `test_philo14_a1c_aftercare_capture_glass.py` incl. the exact seat after Dismiss; seven aftercare atlas cases re-anchored to the A5 drawer's `needs-row-verb` and walked at both widths; Astra r1 RWC → r2 RWC (product conditions cleared); FAST green). Open from #954: the null-read guard's regex misses `document.querySelector<T>(` so main's existing slot lookup in `AmbientLayer.tsx` is unfenced (widen the pattern in a hygiene lane; the lookup itself predates A1c); 28 non-aftercare atlas cases still click `arrival-blocker-verb-*`; `philo603.toast.floor_list` (393) and `floor_spatial_fallback` block on `.desk-hub-dot` / `.desk-world-canvas` setup steps unrelated to the card; the first real-LAN closure s2 walk at 1440 drew no summary in 300 s (second passed; cause unknown). Merged: B2 the material pass #958 (library-only: the plated Button is RAISED again (a high-specificity 'materials spike' block in global.css had overridden the bevel with a glass top line), `:active`/`aria-pressed` sunken, disabled flat; StateChip is a LAMP (a 10 px raised square in the state's tone beside its word; a lit lamp always has a word or, when the row already says it, `wordless` with the `aria-label`); `surface-token[data-chip]` a flat fact with a lamp for warn/danger/ok; FilterTokens and ProjectButton lightly raised (RULING: UX-CANON D amended, filters are lightly raised tokens, wings keep the full Steel bevel, never alike), the active one sunken; SurfaceVerbs a raised strip; one sunken well per window body; a Room-row 5 px growth regression caught by the Room rig and fixed in the library; new `test_philo14_b2_material_glass.py` reads computed material on six faces at both widths incl. a held filter strip through the real people-access API; `test_hs145` re-anchored to the A5 drawer; Astra r1 RWC (visual direction PASSES on all 24 shots), four conditions fixed and verified; FAST green). Open from #958: the old `desk-chip` family in older pullouts and the Settings footer `gadget-chip` NOT SET are still flat chips; EgressChip untouched by design; the raised bevel on dark plates is subtle at 1x (raise `--bevel-light-strong`/`--bevel-dark` if the owner wants more depth); the HS-145 intermittent Close Settings timeout is unexplained. Merged: A5b the Needs drawer keeps its paths #965 (CAUSE WAS PRODUCT: A5 moved the Needs-you window to the drawer but the A2b paths stayed in the Chair's dead `NeedsYouSection`; now NeedsRow carries the library ProjectButton at the end of the fact line (hidden with one Project; the fact no longer repeats the name) and it opens the DRAWER; a proposal row opens the ROOM with that proposal selected and gets a Room button beside Confirm; the Room REVEALS a requested proposal from any posture (History → ROOM view; Review/Update/Steward/Prepare close as their own Close does; the 393 Update restore no longer reopens over the request); RULING: a proposal request NEVER saves the Update draft (Astra r2 found the auto-save racing a pending save and overwriting newer text) — `stepAside()` keeps the open update, the unsaved text, the stored draft and any save error, sends nothing; 3 vitests + 9 glass tests green again (none baselined); `arrivalAttention.test.tsx` re-ruled to one Project button per row; hs144's empty-Door check now asserts no member rows; Astra r1 DNR → r2 DNR (capped) → the no-save ruling fenced (held-save and 500 variants at both widths) and verified by Muad'Dib: a2b+a2 glass 24, project-room+needs vitest 523, FAST green). Open from #965 (Astra's MISSED, for the lane that PARKS the dead `NeedsYouSection` in `ChairHome.tsx`): the sources disclosure's per-projection URL/selected proposal is gone (the drawer never reads `item.sources`); keyboard access to an object with an action (the `door` branch renders only the action; body opening is mouse-only); the commitment owner → People path falls back to `action_item:<id>`; decision/proposal/unassigned rows discard `observedWord`; a standalone agent's Project shortcut; immediate post-write state relies on an async reread; Hand to agent, ranking, the five-row cap and source disclosure were removed by A5 on purpose (record as dispositions). Also: at 393 the Project button wraps under the fact (accepted by canon); `philo3_01 receipt_hits[1440]` fails only under load; the 393 variants of the no-save fence cannot test the race (a reopen gets a fresh Room). Merged: A5 Needs you as a smart drawer #935 (Needs you is a drawer of objects: `web/src/desk/needs/`; ONE OBJECT ONE ROW, every ask folded into its item whatever the item's mute or wait (the row shows the most urgent, held call before question, `+N MORE`, and opens the lane); headline = Dock badge = screen notch = counted rows; ARMED/NEXT/Connect calendar/Muted restored; a refused Cancel reads `NOT CANCELLED · <reason>` + Retry, a cancelled recording leaves `CANCELLED · <meeting> · hh:mm`; a CUT command (the hook's 120-char head is a design limit; the hook now also sends the REDACTED command's length, never the raw) reads `<head>… +N CHARS` with Deny and Open/Raw and NEVER Approve on any surface (drawer row, lane HELD list, system shade) through one `db.gate.command_view`; the agent-facing gate reply is unchanged (its schema lives under `pm/roadmap/`); the owner's reads carry `args_shown`/`args_cut`/`args_hidden`; 37 inherited glass re-anchored; Astra r1 DNR → r2 DNR (3 left) → Muad'Dib verified the lane's round 3 (fences named in the PR body); FAST green: the kernel real-hub test and the philo11 document rig errored under load 88 and passed alone). Open from #935 (Astra's r2 conditions, with owners): the 1440 before/after shots in the PR are the same picture for the held-cut and held-armed rows (re-shoot in the material pass B2); the red phase of the new fences was shown by the lane, not independently; `drawer` and `lane` species are two copies of the row (fold when B2 lands); the agent-facing reply keeps the head only (by design). In flight: A1c #954 (the summary card opens Capture at both widths; Astra r1 running), B2 material, A0c 32 px set. In flight: A5 Needs you #935 (port 37 glass; ARMED/NEXT/Connect calendar/Muted restored; one object one row; Astra r2 DNR → Muad'Dib verifies the three last fixes). (the canvas species into the library: DeskIcon, IconLamp, IconGrid, ObjectList, TimelineRail, StationTrack, ConfirmLine, NeedsRow, GetInfo; the bevel grammar), C2 the agent's lane (board A-4 + C-4 track on the C0 route), A0 the icon mold (PixelLab, three directions, a sheet). Queued behind B1: A1 the screen (the Chair's tiles retire; board A-1), A2 the drawer (A-2, A-2L), A5 Needs you as a drawer (A-5); then C3 drop to hand (A-3).

PHILO Phase 13, The Desk, is complete (18/18 stories, closed 2026-10-03).
Record: `pm/roadmap/holdspeak-philo/phase-13-the-desk/current-phase-status.md`.

Now: the fast-lane change (owner ruling 2026-10-03): remove the commit gate; stop
committing generated docs and line-number test maps; split the tests.

## Open work

- **Terminals (2026-10-30):** UI correction follows the owner's rejection of #1652. The live appearance verdict remains open. Output is still a bounded recent-screen snapshot; host PTY resize, remote transport and reboot process restoration remain open. Inventory full paths are hover titles; touch/keyboard path inspection and equal-folder-name disambiguation are follow-ups. See `docs/internal/betterment/terminal-workspace/FLOW-CORRECTION.md`.

- **Words (2026-10-30/31): DONE.** CSS closed (#1634); sources at UPPER_DEBT 21 lines, all
  compare keys, ids, initials and acronyms (#1637, #1640, #1643). Left only: caps literals
  that never call `toUpperCase()` (the AgentsCard HOOKS family, the "AGENTS · n" caption).
- **Quick check time:** done (#1656): a CSS change runs 64 web files, ~3.4 min.
- **Watch:** `test_delivery_spool_real_hub::test_a_spooled_event_reaches_the_event_log_with_no_reader`
  red once under load on 2026-10-31 (green alone). Go ▸ Builder lists the older panes launcher
  as a second "Terminals" row (parking candidate). Slow desk vitest = whole-face role-name lookups
  on big faces with all CSS loaded (#1650): scope the query.
- **Desk stacking (2026-10-30):** the seed posts only this load's real raises (#1639).
- **Programs (2026-10-28):** PG15 and PG17 in
  `docs/internal/betterment/programs/RECIPE.md` (PG12, PG13, PG13b, PG14, PG16, PG18, PG20, PG21 and the race shot
  #1618, PG13 #1620 and PG13b #1621 shipped); his live verdict on the Programs
  window and the Program window.

- **Phone (2026-10-28):** PH11 SMS and PH15 urgent through Do Not Disturb in
  `docs/internal/betterment/phone/RECIPE.md`; his live verdict on the faces.

- **The Line (2026-10-29):** LINE-5 barge-in measured; the LICENCE slice
  (Kokoro and faster-whisper's PyAV pull GPL into the hub) awaits his ruling.

- **Adversarial review follow-through:** the 47 records and shared delivery
  priorities are in `docs/internal/betterment/native-experience/adversarial/README.md`.
  Repair Settings leave/return conflict suppression first (isolated component
  regression failed; no-leave control passed). Capture first-word retention,
  project-update Stop/late effect, Ask A/B read fencing and Meeting save outcome
  are source-backed priorities. Then prove the explorer/Components consumer
  pair and complete the cross-app jobs. These findings are open; no product
  fix or owner acceptance is claimed by the review packet.

- Pre-change full tape at `83d790151` completed red: 11 Python and 11 browser
  cases failed; web baseline passed. Source logs remain in
  `wt-main-tape-agent-automation-delight-20261020/.tmp/delivery/tape/`.
  The new Settings/builder delivery gets its own pinned tape after merge;
  required quick and scoped behavior must pass before deployment.

**Daily surfaces #1243:** owner visual acceptance remains open. The saved
Decision Send row still repeats its label beside the button; this is visible
polish debt in the new1440/393 Background shots, separate from the verified
writing/save path. The recurrent memory-index lock has a reproduced cause and
minimal correction, recorded in the daily release record. The exact startup
writer in the full run remains unidentified; the regression independently uses
a real competing Note write. Postmerge verification and current local delivery
are kept in the linked final verification record. Earlier #1214 Ask/Thread
findings must be judged against the new face-specific proofs, not assumed all
closed.

**People availability observed during daily verification:** the recall-fix
quick reported503 from `/api/people/relationships` on Places1440 and
`/api/people/relationships/{id}/brief` on Settings. The exact Settings repeat
also failed once; its next diagnostic run passed. Cause remains unknown.
Per-worker isolated keyfiles exclude shared native-key access. Failure-chain
diagnostics now accompany the next check; no People behavior is changed or
error hidden. See the daily release record for the preserved failing logs.

**Tonight follow-through:** the first integrated sweep saw one Components-window
HTTP503; the focused reproduction and final109-case sweep pass. Its endpoint
and cause remain unknown; future failures now retain the URL. Track rather
than excuse or invent a fix. The alternate localhost/127.0.0.1 origin entry
mismatch remains separate; use the actual address printed by `holdspeak web`.
Send recovery is tab-scoped; stale Meeting repair is bounded to saved pending
publication/succeeded states. Real external delivery/provider/native execution
and owner acceptance are not established by the isolated proofs.

**From #1214 and owner's next direction:** refine notifications, Thread and
Ask as coherent Workbench faces. Source audit found Ask mutable retry/Keep
lineage and pending-close seams, Thread inline-editor focus loss and dead
sibling arrows; verify and repair in the next bounded face pass. The existing
four-row ambient sampler is not exhaustive; older eligible rows remain in
Attention. Denied sessionStorage cannot retain the popup cutoff across a full
reload. No source-counsel blocking condition remains. Owner live judgment,
formal postmerge review, remote CI and full main tape remain separate.

**From #1213:** owner live judgment, formal postmerge review, remote CI and
full main tape remain separate. Artistic scale, moon timing and bounded
weather are not ephemerides or fluid simulation. Software WebGL checks do not
establish hardware performance; forced-time visitor samples do not establish
natural long-session waiting. No source-counsel condition remains. Keep the
serving worktree and requested standalone preview while they are in use.

**From #1212:** owner live judgment, full main tape and formal postmerge review
remain separate. Inherited runtime debt: if a scene throws during first
resize/render after runtime listeners attach, the runtime cannot return its
partial cleanup. The host releases its own observer and keeps still fallback;
this pass does not claim disposal of that partially constructed renderer.
Continue the bounded surface refinement record below. No source-counsel
condition remains; no backend, filing writer or guard ceiling changed.

**From #1211:** continue the bounded surface audit in the linked next-refinements
record. No confirmed source finding remains from this pass. Owner live judgment,
formal postmerge review and full main tape are separate. Existing remote CI
token-gate/API-reference debt was reproduced on #1209/#1210; this pass does not
claim it repaired. Held Send has focused transport-test coverage, not a live
provider-dispatch claim.

**From #1209:** opened Workbench/controls and the reported Accounts row are
refined and verified on isolated production faces at 1440/393. Continue
bounded inspection of remaining existing surfaces. Owner live judgment,
full main tape and Astra postmerge review remain separate. Native sign-in,
provider health, microphone hardware, actual model execution and schedule
firing were not established by these UI/CRUD checks. No confirmed source
review finding remains open; no guard ceiling changed.

**From #1208:** the five #1207 source candidates are repaired and
observed on isolated production faces at 1440/393. Continue bounded inspection
of existing surfaces; plain no-pane terminal still repeats Back in its body
and footer, a visual follow-up. OS clipboard, owner tmux/control, microphone,
external email dispatch, native calendar, model quality and scheduled firing
remain unverified. Thread has focused question-control coverage but no
established production elicitation emitter. Owner live judgment, full main
tape and Astra postmerge review remain due. No source-review P2 remains open.

**From #1198:** two intermediate full sweeps observed a Week 1440 layout
movement (166 / 118 px). Six focused checks, three complete diagnostic sweeps,
the unchanged #1197 baseline, and the final unmodified quick check passed;
the original movement's cause remains unproven. No fence or known-red
allowance was relaxed. Owner usability, real microphone/calendar capture,
LAN model quality/latency, full main tape, and Astra's postmerge review remain
unobserved/due. Automatic Finish extraction remains later work with the real
subject-aware durable producer; see the handover for exact boundaries.

**From #1197:** owner desk judgment and real LAN latency remain unobserved;
the reported 122-second Ask delay has no verified runtime cause. Automatic
task extraction on Finish, the remaining full words sweep, and legacy branch
retirement after a week of real use remain later work. Existing sweep target
known reds remain. An isolated test background thread outlived its DB
(`deployment_revisions` missing); warning retained in quick-r3/py.log.
Postmerge Astra review and the full main watcher tape remain due; findings
fix forward under the October 12 fast cycle. Sol owns this handoff; the next
main-watcher/reviewer session owns the postmerge findings.

Now: PHILO PHASE 16, THE COMPOSITOR (owner bounce 2026-10-08: "too sterile, zero concept of a compositor, zero regard to delighting the user"; 2026-10-09 "Orchestrate away. Approval granted."). Guidelines `docs/internal/philo/phase-16/COMPOSITOR.md` (§1–§13) and the canvas `01-canvas/compositor.html` (artifact WBa6SK1fx2RqX9prBf45Do, v3) RATIFIED and merged #1030: one light, the depth ladder (FRONT/NEAR/FAR/SEATED), title bar B + icon/sans/lamp, the interior joins the material (slate ground, paper wells, steel verbs, blue selection), the interior kit (§11), the composition doctrine for internal apps (§12), ten software-design lessons from PhreshOS/system (§13: the hub owns windows; anticipate-then-follow; depth counter; layers as a type; share+px geometry; one motion owner; departure snapshots; shared-resize boundaries; one rule per row; the registry). Owner picks on the canvas defaults: backdrop floor, sans titles, stage shelf left, slate interior. Lanes (Part II, handover XXXVI): 16a-A1 the material and the chrome MERGED #1032 (Astra r1 DNR 4 MUSTs → r2 RATIFY; FAST green 15323; scoped glass 36 files, 4 reds paid: the shell's solid ground colour under the gradient, two chip fences ported to seat tiles, one fence's front gesture; rulings carried: selection paper on #4a6aa0 = 4.76:1 AA accepted; ember under the far veil 4.38:1 accepted (two planes back); FAST not rerun for the CSS-only fix commit eb8a21815 by Muad'Dib's judgment; flake to watch: test_philo13_07_remembers_glass TestSliceTwoReturns[393] 'Decision title' textbox timeout, passed alone; known: Rainy City is no longer the default atmosphere (Quiet Desk is; a saved scene wins); the NEAR plane appears live only when A2 merges) · 16a-A2 the compositor core MERGED #1034 (Astra r1 DNR 5 MUSTs + a second Tile fault found; r2 one MUST (Zoom during Stage measured a box in flight) paid and verified by Muad'Dib; FAST 2 reds paid (A8 zero in CompositorLayer; a querySelector in the Esc handler); scoped glass 32 files: 4 reds: the Chair Window-menu fence ported; three INHERITED on main, confirmed by a run on main: test_palette_two_line_glass[393] contrast 2.6:1 on the ⌘K palette (A1's remap: a real regression), test_philo8_01_zone_name_glass[393] (Go has only New ▸ at 393 since PHILO-15 11), test_philo13_12_gadgets_glass::test_gadgets_393 (keycaps omitted at 393, DeskMenu.tsx:439): a reds lane runs; rulings carried: the z band keeps the front alone at 77 and windows past 36 share 42; two windows whose minimums cannot fit side by side overlap with no divider; Window ▸ Stage off-viewport at 1440×280 (keys work); anticipate.ts, share+px in the store, the tempo setting and the Switcher redraw wait for 16b; the StrictMode entrance guarantee unverified) · 16a-A3 the interior kit MERGED #1035 (Astra r1 DNR 6 findings → r2 RATIFY; the canvas's Needs-you fold RETRACTED (HS-200-15/B11 outrank it); FAST 3 reds paid (a border-left rail, a viewport media query in the kit, A8 zeros); scoped glass 65 files: 21 reds paid incl. three real layout regressions (a foot overlap, the Room ask well covering Steward, the hs169 scope line); residual reds on its final run are ALL time-dependent quiet-hours fences owned by lane 16a-R (attention ×2, preparation brief ×6, test_phase200_recipe_catalog::test_a_watch_read_long_ago_is_stale_not_available at 03:xx) plus one Prepare regression from C (lane 16a-C2); FAST 15328 otherwise; backlog: the meeting's old wells (summary/send/decide/transcript, MD/SRT/Park, list chrome) stay; 'Read hh:mm' omitted (no read time exists); the 393 kit-verb fence measures height/halo not pointer ownership; the 'No engine for summaries' status line atop the Meetings window; live172_walk.py not runnable as pytest) · 16c Runs on (the Models app as a Switchboard) MERGED #1036 (Astra r1 DNR 8 MUSTs incl. one SECURITY (a pending Try-on-host consent re-resolved the engine at confirm), r2 two left (the host compare; stacked Undo) paid in 456ce3b5c and verified by Muad'Dib: consentHolds compares job + engine id + host at confirm and on refresh; FAST 3 reds paid (api-surface manifest regenerated; A8 matches rewritten; census rows 16-03); scoped glass 52 files, 14 reds paid: the foot's receipt ink on steel (A1's --text-muted remap: now --wb-ink-dim on .desk-surface-foot inside a window), the Settings hub fence (one Runs on row), the held-filter probe measured outside the window; FAST not rerun after the fix commit by Muad'Dib's judgment; backlog: a per-object wire on the board (per-subject overrides parked), 25 atlas cases still drive the old Concierge flow (orchestrator's), FOUND shows addresses only (files need an artifact id detect lacks), test_hs201_09 keeps its pre-existing talk to the real LAN engine, route-probe adapters per capability (Try it is REACHED for all but Thoughts & notes), a phone cannot make an inherited engine a job's own wire; Meaning search stays as a row under the board (ratified)) · 16a-R the inherited reds MERGED #1039 (the ⌘K palette's contrast red was a reduced-motion `transition-duration: 0.01ms !important` in react-app.css after tokens.css's 0ms, so every colour change was a transition and the fence read the frame before it settled: now 0ms; the palette's selected hit is the Workbench blue with paper ink, the N OPEN badge without its white wash (Astra's one MUST); three 393 fences ported (Go has only New ▸; no keycaps at 393; attention counts exclude quiet); the night-dependent fences seeded past the quiet window (preparation brief 20 h, recipe catalog 24 h); the remembers 393 flake did not reproduce ×3; scoped glass 63 + FAST 15329 green on the first head; FAST not rerun for the fence/CSS second commit by Muad'Dib's judgment) · 16a-C2 MERGED #1041 (a task handed back after a Runs on patch comes to the front: returnToTask.raiseWindowOf; scoped glass 98 green; FAST green but for the recipe-catalog night fence #1039 had already fixed on main) · 16c-atlas MERGED #1044 (27 Concierge atlas cases: 24 ported to Runs on, 1 parked with its successor, j4/j10 untouched; graph_walk rig 1.5.3 doubles 192.168.77.43 and every rig hub sets HOLDSPEAK_LOOPBACK_ENGINE_PORTS empty (no walk reaches a real engine); HOLDSPEAK_DEFAULT_ASSIGNMENT=off stops the default-assignment writer for read-only walks; the new case summary_completes proves patch → import → summary succeeded through the exact row; the three j9 recipes use a failure reply; tests/e2e/live_runson_walk.py replaces the parked live170 walk (read-only, any non-GET fails it, roster diffed); Astra r1 DNR 4 MUSTs → r2 RATIFY; FAST 15335 green; MAYs: the live walk's roster fingerprint omits existing capability assignments' engines/revisions (Astra changed a summary assignment and it stayed equal); live-pass-lane-brief.md:15 still prescribes --engine real which replay cases reject; still red on main and NOT this lane's: test_graph_walk_smoke [j4.meetings_import.imported] (Whisper will not load in an isolated HOME) and [j1.first_words_continue_later.idle] (selector missing on main: arrival-headline/chair-first-value), test_hs202_first_use_smoke[393] record-refresh flake (2.5 s wait on the record); six atlas cases blocked by pre-existing case defects: shade door_stale (setup deletes the meeting), speech_missing (assignments/clear 400 invalid shape), profile_delete (imports no meeting), profile_unbind ({profile_id} never captured), intel_running (cannot see 'claimed' with an instant replay)) · 16a-R2 MERGED #1047 (the first-use record-refresh 'flake' was the fence's viewport check, not a late record: now waits on the record's state then scrolls and asserts the viewport; j1 first-words case reads the chair desk; j4 import case runs on an import-transcriber double (a boundary without a reply is refused before boot: schema + guard); speech_missing/profile_unbind/intel_running (replays accept delay_s) pass; door_stale and profile_delete NOT APPLICABLE by product ruling with successors (new case profile_delete_refused: 409 model_profile_referenced + roster identity unchanged); RIG ISOLATION: a fresh isolated desk showed the owner's real macOS calendar names (EventKit is per user): HOLDSPEAK_MACOS_CALENDAR=0 in every rig hub; Astra one MUST paid; FAST 15343 + graph join green; OPEN rig gaps: the Agents card on a fresh isolated HOME reads the real machine's agents ('pi · SIGNED IN · HOOKS' from outside HOME); engine_reply/cli_runner boundaries without a reply still boot without their double; record_only.no_speech_head blocks on a missing browser_audio_device substitution; other atlas cases still observe at arrival-blocker (stale since PHILO-14 A5); every other WAV-importing case still loads real Whisper) · 16-RIG MERGED #1049 (the rig never reads or writes the owner's state: the rig hub inherited his environment, so the agent detector followed CLAUDE_CONFIG_DIR/CODEX_HOME/ANTHROPIC_API_KEY out of HOME and the pi row was hard-coded signed in; both rig envs now set CLAUDE_CONFIG_DIR, CODEX_HOME, PI_CODING_AGENT_DIR, GH_CONFIG_DIR, XDG_CONFIG_HOME, the People and channel keystores INSIDE the isolated HOME, drop ANTHROPIC_API_KEY, GIT_CONFIG_NOSYSTEM=1, HOLDSPEAK_TEST_NO_REAL_CLI=1; four switches, all default ON on his desk: HOLDSPEAK_AGENT_STATE (sign-in/hooks answer not_read, never a false no; the doctor reads real state), HOLDSPEAK_ACTIVE_TARGET (no AppleScript read of his front window; readiness answers source not_read), HOLDSPEAK_DESKTOP_NOTIFY (no Notification Center posts; heartbeat records not_posted_in_rig, not an error; libnotify too), HOLDSPEAK_CHANNEL_KEYSTORE_FILE (a 0600 JSON store; the Keychain stays the default); engine_reply/cli_runner boundaries without a reply refused before boot; nested-then boundaries install their double before boot; Astra r1 DNR 2 MUSTs paid, verified by Muad'Dib by reading; FAST 15393 + 56 browser cases green; a test-pollution leak fixed (test_philo10_atlas left a memory Slack store on the module); NOTE: HOOKS UNKNOWN token on the Agents card went in without a canvas (rig-only); OPEN: heartbeat sweeps in a rig record not_posted_in_rig; the G3 audit table lives in the lane report) · 16a-R3 MERGED #1051 (thirteen browser reds proved inherited on main by 16b's full-suite run, paid at cause: ONE product fix (the thought window's foot receipt wraps: lane 12's B27 nowrap outranked the thought foot's wrap; both receipt lines carry data-wrap); the rest fences/rigs reading retired details while the face was right per canon (a zero-claim draft is refused since B64; the Foot's receipt line is uppercase mono by §C; the ember token resolves inside the window; a two-line icon label keeps its name in title; drawer-head became drawer-facts; a kit Ledger with no count draws no head); plus the two STATUS extras (Re-brief posts /rebrief and answers 202 mid-turn: the fence ends the turn and points the seeded launch at the rig's pane; hs176's caption rule); Astra RATIFY code-read; scoped glass 22 files 103 green; FAST 15394; not reproduced: finish_face_polish 'config version' (one failure then 3 passes); for a face review: a Setup readiness row cuts its detail at 1440 ('config versio…')) · 16b MERGED #1046 WINDOW AUTHORITY TO THE HUB (§13 L1: the hub owns the desk's windows; every browser is a view of one desk; agents reach the same windows): holdspeak/services/desk_window_service.py (open/close/move/resize/raise/send_back/seat/zoom/arrange/stage shelf; geometry as share+px; ONE monotonic revision per desk with expected_revision → 409; one frame per write; adoption recorded once; rows+revision one snapshot), /api/desk/windows, six windows.* declared operations as MCP desk_window_* (WORK; the five writes under a pass-through launch rule; Secure holds every write), web/src/desk/compositor/hubWindows.ts (the browser is a presentation: hub seeds, cache = first paint only before adoption, write-through with anticipate, per-id applied revisions, a failed write restores the hub's row, windows the hub opened here never write their mount back, keepalive opens survive a reload; adapters for Chair/application/pullout/zone/info/roadmap/repository/workbench/conductor/project drawer/parked drawer/lane; inspectors, editors, delivery-*, trust, session, schedule, attention, ask, intelligence:desk stay VIEW-LOCAL (refused by name window_not_on_hub)); glass: two browser contexts on one hub see one desk, follow a raise live, an MCP arrange tiles both; Astra r1 DNR 5 MUSTs, r2 3 MUSTs (one snapshot; failed write restores; the lane follows), all paid, verified by Muad'Dib by reading; the whole browser suite run three times on its heads (45 → 22 → 4 reds + 2 errors, every remaining one inherited); FAST 15461; final: 916 passed; residual on main (not 16b): test_philo13_09_prep ERROR ×2 (People routes 503 in the rig seed) and test_hs200_people_preparation ×2 ('ready' where 'locked' expected) = lane 16a-R4 MERGED #1055 (one cause: _boot sets the People keystore inside HOME since #1049 and the two rigs kept their own path after the boot; now one source of truth glass_infra.people_key_file; the hub reads the key file on every get, so a damaged file locks at once; backlog: ~30 glass files carry a dead setenv of the keystore before _boot); PHASE 16 LANES COMPLETE 2026-10-10 (handover docs/internal/HANDOVER-MUADDIB-XXXVII.md #1054); NEXT: the owner's real day on the compositor (Mac + iPad = one desk); Phase 17 named from his bounces; test_finish_face_polish ×2 flaky under load ('config version' .first hidden; R3 saw it pass 3×); backlog: defaultGeometry as shares in the registry; a lane opened only through a steering session is not synced; the owner's first press after a remote change ends the quiet period; a window that unmounts without closing (393 sheet) is not sent as closed; rigs that open several pages on one hub must clear_hub_windows (the pattern is in glass_infra); not verified on a real iPad. HS-110-01's "no shadows, no gradient" is AMENDED by §2 (light returns; glass stays dead).

Now: THE CONDUCTOR, hardening (owner 2026-10-06: "address a lot of the things you pointed out as still being open"): merged R2 #911 (credentials, grants and ownership survive a restart, hashed; durable revokes; no token on argv; held gate calls survive a restart), R6 #913 (session footer verbs are library Buttons; picker rows 44 px at 393; A1 ratchet 81). Merged also: R3 #914 (Codex gated and supervised like Claude Code: exact hook trust via the owner-only install, per-launch hooks, YOLO -a never + workspace-write + network for its own branch, close-keyword hold, gh limited to the agent's own forms), R5 #915 (/keep makes a Note, 30 min question windows, Mission Control on the runtime bus, venv activate in YOLO, door.get for agents, four flakes fixed at cause, the hub holds its port from pick to serve on IPv4 and IPv6), R4 #912 (Jira and GitHub issues handable, every origin closes or links, owner on the Secure confirm, registry cleanup, every merge in the weekly update with a persisted watermark and paging, a read-only GitHub issues Watch, tests cannot reach the real gh/acli). Merged also: R1 #916 (the real loop with real Claude Code 2.1.288 and Codex 0.159.0; bracketed paste with control characters refused; Stop question for Claude; acceptEdits in Normal/YOLO with Edit/Write/MultiEdit/NotebookEdit gated by a symlink-safe worktree check; held gate calls in Needs you as one TO APPROVE row per wait; steer grounds only what you attach). Merged also: R7 #919 (owner rulings 2026-10-06/07: launched agents READ People via MCP with no People cut, writes owner-only; people.mcp_access setting, default on, owner-only CONFIG op with a receipt, the env var overrides; Settings › People built as ratified (K7a) with a disabled strip under the override and a READ FAILED + Retry state; off hides People from the owner's MCP discovery except people.access.set). THE HARDENING PUSH IS COMPLETE (R1–R7). Building R7 (owner ruling 2026-10-06: agents READ People via MCP, no People cut for agents; a people.mcp_access setting, default on, with a canvas board for its control). Known on main, not ours: the meeting window shows its summary twice (first-use smoke strict-mode, tests/e2e test_hs202_first_use_smoke.py); J4 meetings import times out (import_failed, transcription stays active). Limits: R1: no actual-atlas walk of the launch→PR→merge loop (the rig lacks an agent double, a GitHub-shaped clone step and a gh double at PR receipts); whether per-launch settings strip inherited additionalDirectories is unverified (the gate is the guard); the R1 walk was not credential-isolated (the owner's keychain and auth.json were symlinked; keychain refresh unknown); future walks use an isolated CLAUDE_CONFIG_DIR/CODEX_HOME login or API keys. Flakes to watch: test_workbench_runner_migration deadline expiry, test_agent_hand_round1 thread hand (load). R4: a merge window with 30+ PRs created in the same second stops at window_dense (no loss, needs a look); the Room link of a merged PR is not visible on any face yet (needs a canvas); report_merged_prs has no screen control; GitHub issue rows are kept out of the desk-wide Needs you count. R5: the live hub's preferred-port path is IPv4-only (as before). R3: the R1-edited transport test expects bracketed paste. Limits: a revoke SQLite refused is lost if the hub crashes before the retry; an agent shell that exits >0.3 s after start is reported spawned (K2 registration timeout catches it).

Now: THE CONDUCTOR (owner 2026-10-05: "work with agents, semi-autonomously, as an orchestrator, out of the box"). Plan: `docs/internal/CONDUCTOR.md` (#893). Merged: K0 #894 (steer keeps picked refs; qualified watch events classify as closed; device reply window 30 min), K1 #895 (detect claude/codex/tmux, one-press hook install as owner-only kernel op `agent_hooks.install` with receipts, doctor Coding agents check, Setup keeps `info`), K3 #896 (blocked coders join Needs you as R5 TO ANSWER / TO APPROVE, wait episodes, immediate edge notify, strict registry read), K2 #898 (Hand to agent: declared op `agent.hand` behind POST /api/agent/hand + MCP + Thread `/agent`; grounded brief with full redaction (People cut removed by R7); new worktree; rider hooks via --settings; gate armed per path under a file lock; folder-trust answered once in its own pane; brief typed after registration, persisted, resumable via POST /api/agent/launches/{id}/deliver). K4 #900 (the Heartbeat follows each agent PR by identity: same repo, no fork, the launch branch, merged after launch; closes the origin on merge with PR evidence, or a Door confirm in Secure whose dismissal is final; the weekly update reports each closure once by key; cleanup kills the session and removes only a clean, merged worktree the launch created). K5 #904 (supervision by the ratified Control-mode mapping, YOLO default: the hook classifies each Bash call in the agent process and the hub checks the verdict against the launch; only system programs and builtins earn read authority; routine questions answered under policy with receipts, real ones to Needs you with a draft; 3 live launches, 6 answers/h, 2 h quiet / 8 h budgets raise Door items; also fixed K2's every-Bash-call-denied parent bug). Canvas RATIFIED 2026-10-06 (#902). F1 #905 merged (first-run Agents card, Hand to agent on desk objects and Door/Room rows, the docked launch sheet with a side-effect-free preview and a delivery receipt that follows pending → delivering → sent/held/not sent with Send again). K6 #903 (every launched agent gets the HoldSpeak MCP with Reach off: CONDUCTOR palette of 133 tools (90 reads, 43 mutators each with one launch rule; no egress/authority/config, no People family, no model-composing tools); launch-scoped memory read and decision proposals; insert-only creation; kind:id ownership; People cut on every MCP and HTTP answer (removed by R7: agents read People, owner ruling 2026-10-06); credentials swept independently of PRs). F2 #906 merged (in-flight state on Door and Room rows, AGENTS lists every session and its item, the Needs you agent row with Speak answer, the answer well with Enter to send, the merge receipt). THE CONDUCTOR IS COMPLETE on main: K0–K6 + F1 + F2 (#893 plan, #894 #895 #896 #898 #900 #904 #903 #905 #906). Next: the owner's real use; the open items below (DRAFT, for the owner). Waiting on the owner: the Control-mode mapping (K5). Open: F2 limits: the 'Arm pane … for rename and kill' raw button with a sentence (main's, breaks UX-CANON A.1/A.3); no atlas case for the launch→PR→merge transition (the rig lacks launch, PR double and Run now steps); merges proven with a fake gh and a transcription double, not on a real desk; GitHub issue rows cannot be handed (no issue kind in agent_brief). K6 limits: door.get refuses every agent (Thought lane); `--allowedTools mcp__holdspeak` not verified to skip the interactive approval prompt. R2 limits (#911): a revoke whose SQLite write failed is refused in memory and retried before every later write and on a repeated revoke, but if the hub stops before a retry succeeds the credential comes back at the next start (Astra round 2: no new persistence mechanism); a new window in a launch's tmux session does not get the token; across a machine reboot only the wall-clock deadline applies; an agent shell that exits more than 0.3 s after start is still reported spawned (the K2 registration timeout catches it). K5 limits: Codex is not gated (its PreToolUse hook exists; the 5 s hook timeout vs a 300 s hold needs work); `source .venv/bin/activate` and PATH= prefixes wait even in YOLO; a worktree program called by path runs in YOLO (accepted by Astra); routine classification quality on the LAN model is unobserved. F1/F2 deviations: no Hand to agent on GitHub issue rows (no issue kind in agent_brief); the main session-window footer layout bug is being fixed in F2; tests/e2e hs144 cold-open test waits for a heading that is now a button (stale on main?). Flake: tests/unit/test_inference_runner.py cancel-retry (once). K4 limits: merges of PRs no agent made reach the weekly update only through a Room Watch that reads merged PRs (Room watches stay open-only; a merged-only query is the owner's call); origins other than action items and decisions are `not_closable`; the Secure confirm item has no owner (UNASSIGNED); a removed worktree stays in the Delivery registry; drafts made before #900 carry no closure_keys; MissionControlConveyor's coder-frame refresh listens for an `hs-broadcast` event nothing sends; other agent-question lookups still use 120 s (dictation routes, dictation_runner); K1/K3 live hook delivery and credential validity not observed on a real desk; the Needs you coder row renders generically until the faces land; flakes to watch: tests/unit/test_philo5_codex_seams.py restart case (once); tests/integration/test_phase200_one_composition_root_processes.py sidecar cold start (twice on K2 FAST, passes alone). K2 limits: the trust answer knows Claude Code 2.1.x's prompt only; Codex startup prompts are not answered; `/agent` needs an explicit project_id when the attached Project stored no sources.

Done: the README sells the whole product (owner 2026-10-05: "we're still selling it short"): #891 merged, Astra ratified on iteration 2. What's inside table; sections for Ask AI and Threads, cited memory, Send to six destinations, coder steering, Extend everything, MCP. Product bug found in review: Thread `/keep` asks for a Note but `thread_service.py` ignores `as_kind` and always records an Artifact (README says Artifact until fixed).

Done: the README as the front page (owner 2026-10-05: "the main readme should be alluring enough"): #889 merged, Astra ratified on iteration 2. Hero card, pitch, two current Desk shots (docs/assets/readme/), pillars, a How it works diagram, quick start, comparison. The hero shot shows a temporary test path; replace it with a clean capture when convenient.

Done: docs sweep (owner 2026-10-05): #887 merged. A Sonnet 5.5 fleet rewrote README, CONTRIBUTING and every docs/*.md against source; Astra ratified on iteration 2. Open: five overlapping docs marked "(overlaps X)" in docs/README.md (INFERENCE_TARGETS, DATA_MODEL, SYSTEM_INTEGRATION_MAP, WEB_UI_UX_SYSTEM_AUDIT, API_REFERENCE), park or merge them; generated PLATFORMS.md is a stale snapshot (regenerate or park); API_REFERENCE prose lives in scripts/philo_api_reference.py; Mermaid render not verified locally; FirstWords.tsx "Keep as Note" vs FirstRun.tsx "Keep as note".

Done: finish it all as one onboarding experience (owner 2026-10-05): #866–#872, #875–#877, #882 merged. Open for the owner: the 1440 Dock with five projects; whether Stop should summarise again; person pages (no non-People key).

Done: strong defaults, batteries included (owner direction 2026-10-05): #855, #856 and #859 merged: a fresh install now gets local AI from one first-run press. His desk: assign his LAN server as the default (and memory) when his hub next runs.

Now: prepare for the owner's week of real use (assignment 2026-10-03): inventory
(`docs/internal/INVENTORY-2026-10-03.md`), clean up, polish, wire memory into every
process; and the native memory system (`docs/internal/MEMORY-DESIGN.md`, slice 1 merged).

Test state on main (2026-10-05, after #864): FAST 13,846 passed with the #861 fix in; web 3,431 passed, 0 failed. After a batch of merges, run FAST, the web baseline and the scoped browser tests before calling it done.

| Item | Owner | PR |
|---|---|---|
| Memory dates: Kestrel (r09) found only with vectors (strict xfail); live extraction occasionally returns an empty answer (2 of 68 repeats); a one-word capitalised password with no digit ("secret: Hunter") is kept | — | — |
| First run: the browser copy of the needs-you rule (web/src/desk/needsYou.ts) lacks the person-identity guard (no production caller today); physical mic and real model inference not verified | — | — |
| Send folder: six older Send glass rigs park the built-in (direct DB write) to keep their ratified boards; Google Drive / OneDrive provider ids unverified on real installs (fall back to SYNCED). Onboarding: a sign-in connects the account but saves no Send destination; no System Settings verb when Calendar access is denied (needs a hub route); real EventKit, gh/acli auth and transcription unverified on his desk | — | — |
| Defaults: the 4B starter's meeting analysis is untested on real hardware; the real faster-whisper fence skips in CI (needs a cached model) | — | — |
| Defaults: never run against a real Ollama/LM Studio/llama.cpp server; a binding disabled and re-enabled between the backlog tick and the claim consumes the mark (manual retry); GitHub Enterprise entry.egress_host says github.com; meeting import does not write the backlog mark; real EventKit prompt/read unverified | — | — |
| Memory: thread rows saved before the origin column ('' origin) that were project hits and later refiled still replay (accepted, Astra #852); Chase has about 440 bytes of palette room at 32k | — | — |
| Memory pages: never run with the real LAN model; no person pages (no non-People key exists for a person scope) | owner | — |
| Memory observations: never run with the real LAN model; no benchmark group; join default search only by naming kind `observation` | — | — |
| Memory facts: never run through the product path with the real LAN model | — | — |
| Memory: summary and topic as their own chunks not built — needs one transition over vectors, facts, observations and pages (MEMORY-DESIGN.md); the Desk memory face does not show the four new kinds; beliefs show only under the All filter | — | — |
| Memory: the agent tool turn (RecipeService.chat → run_recipe) is retired code with no caller; Recipe chat runs as a thread turn whose default tools include memory.search (proved by tests/unit/test_thread_memory_search_live.py). The update draft and Prep are not fitted to a token budget (their path has none) | — | — |
| Memory: live meeting analysis and voice resolve read no memory (a lookup is 100–400 ms against a 50 ms bar) | — | — |
| Memory: the decision-promotion self-recall test passes before the fix; mint through DecisionLifecycleService.promote (Astra, #830) | — | — |
| Memory: not measured on the owner's real desk; new items take up to 120 s to become searchable by meaning | — | — |
| ⌘K: after Tab the selected and the focused rows share one plate and read as one block when adjacent (pre-existing) | — | — |
| The Dock overflows at 1440 with five projects (the ratified shelf scrolls; Places and Record go off the right edge): owner's design call pending — recommendation: pin Places and Record; Calendar cannot tell no-vision-model from a failed model (the hub sends one code); Ask shows "GROUNDED ON 0 OF 0" (a counter of zero); older thread rows and task-resume Ask answers show no route lamp | owner / — | — |
| Times: a ZoneInfo datetime with fold=1 still loses the fold (timestamps.py:160); about 68 rarer time compares stay textual (one shape per column after the backfill); old rows not rewritten in sync-written columns; a calendar refresh announces every time | — | — |
| Decisions (housekeeping #867): fold the older ReactionService watch system into WatchService (Workbench automations are its only face); three primitives/decisions routes are unreachable in the hub; six routes have no caller (incl. POST /api/setup/local-ai/cancel); connector_fixtures.py lives in the product package; heartbeat.run_now builds WatchService without the Jira adapter; a test left tmux session hs10605_kill_62847 on the owner's server | owner | — |
| Runs on (16c): a per-object wire on the board (thought/workbench/agent/recipe/project overrides; the parked AssignmentEditor sheet edited them; the contextual atom now only reads them and opens Runs on); FOUND model files and an unrecorded Whisper (add-to-library needs a detected_artifact_id detect does not carry); Try it through the route for jobs other than Thoughts & notes (route_probe accepts only ask.answer); the phone list cannot pin an inherited engine as a job's own; 25 atlas cases still drive the Concierge flow (Add = use for summaries; the window closes) | — | — |

## Last merged (newest first)

- **#1657 — After the terminal workspace merges:** `/terminals` in the preflight sweep; the phone's Go fits again (Voice commands is a wing of Speak there); the Terminals glass waits for its rows; XtermPane no longer scrolls a disposed terminal.
- **#1656 — The quick check's vitest step runs the honest related set** (`scripts/vitest_related.py`: barrel edges by name, a cap at the direct rings plus every app file); a stylesheet change runs 64 web files, not 429.
- **#1655, #1654, #1652 — (owner) The native parallel terminal workspace,** insets removed, connected to Projects, worktrees and review.
- **#1653 — Programs PG21:** the Engines fold says whether an agent's usage-limit notice is verified from a real stop on this desk or documented, with its last stop and reset; the parser reads "weekly limit" and a dated reset.
- **#1651 — STATUS through #1650.**
- **#1650 — The Settings leave vitest** scopes its lookups (5.4 s → 1.1 s under load); a no-canvas shim ends the jsdom getContext error storm.
- **#1649 — Programs PG20:** every checkpoint pins the worktree to `refs/holdspeak/checkpoints/<step>/<n>`; a handoff names the ref it continues from; "Start from here" on a checkpoint row (REST + MCP `program.start_from`, ladder-gated for agents).
- **#1648 — Every web census runs on every quick check** (19 files, ~7 s); screen.css on the shell exceptions; the Phone reach write through the one Calls writer; the calls app press inside act.
- **#1647 — The Today vitest** waits for the once-per-day flag the effect writes (the two reds of 2026-10-30).
- **#1646 — STATUS through #1645.**
- **#1645 — Settings ▸ This Mac: a stopped grant keeps its row with remote access off;** "Filing stopped" and Allow filing stay in the same place (the whole Agents list used to vanish).
- **#1644 — Programs PG16:** his Skip, a rule's Skip above NOTE and a merge by rule propose a decision record linked to the Program and its PR; the Project drawer's Proposed decisions fold; "Proposed as a decision" on the checkpoint row; never auto-confirmed; a NOTE-rule Skip proposes nothing.
- **#1643 — The words wave ends at the source:** the Hand sheet and the agents card say their words together; the grant row uses the egress table's words; UPPER_DEBT 56 → 21, none of which draws a word.
- **#1642 — The Send glass pin follows #1640** (File · Slack).
- **#1641 — STATUS through #1640.**
- **#1640 — Words: the caps vocabularies say their words at the source** (egress receipts and refusals, about 200 channel words, plain failures, object kinds, Runs on, settings prefs, the send well's "By you"); the ObjectList Kind cell no longer draws PROJECT raw; UPPER_DEBT 86 → 56.
- **#1639 — The seed sends the hub only real raises:** the Chair's mount reorder is a local view rule; a reload with a slow window read no longer changes the stacking; the hub stays the one authority.
- **#1638 — The Project's Info window reads its name live:** Get Info pressed before the Room read landed no longer stays "Info: Project" (the compositor 1440 flake, fixed at cause).
- **#1637 — The toUpperCase debt 136 → 86:** `wireWords`; the lane window's receipts and the Engines chip's host in words; text the user typed shows as typed.
- **#1636 — A scheduled fire writes "recording" and its outcome in one write;** the rig waits for the fire thread (the week's FAST flake, fixed at cause).
- **#1635 — (owner) Practical agent guidance:** root `AGENTS.md`, `web/AGENTS.md`, `holdspeak/AGENTS.md`; CLAUDE.md links them.
- **#1634 — The words wave closes in CSS:** 190 caps rules in 48 files gone; caps only on the eyebrow, the key caps and two first letters; a ratchet freezes `toUpperCase()` so it can only shrink.
- **#1633 — STATUS through #1632.**
- **#1632 — Words: field and check-box labels in sentence case at the species** (gadgets.css: caption, token check, check word, group legend); the eyebrow keeps its caps by UX-CANON §C; the Hand sheet's caps words become words; two ratchet tests on the label species.
- **#1631 — Engines words:** the Add picker's chip and token sources in sentence case, "On the other Mac" keeps its Mac, the Wiring fold's label is a quiet caption; a guard keeps caps out of the Engines sources.
- **#1630 — Engines under the window grammar (direction B):** two lists (what HoldSpeak does, with the engine picker in the row · the engines in words), hosts in the engine's fold, Builder tools no longer swaps the face for the parked switchboard; ListRow gains selected/lit/expanded/progress/fold.
- **#1629 — Eight FAST guards fixed at cause;** every guard file runs on every quick check (the always-run list in `scripts/quick_check.sh`).
- **#1628 — The egress chip** says its words in sentence case and shows hosts as typed; no caller uppercases a host or a vendor; the ratchet covers chips.
- **#1627 — Three clock reds:** tests pin every clock the hub reads; `usage_limit._local_zone` takes the zone from the pinned moment; Phone flow tests start outside quiet hours.
- **#1626 — Programs PG14:** the Do kind `run_program` on automations; the Overnight starter is real; `openPullout('program:<id>')` fixed.
- **#1625 — Lamp words:** every lamp in sentence case (Listening, Reconnecting, Offline); `tests/unit/test_lamp_words_guard.py` is the ratchet.
- **#1624 — Phone push host (lane PHONE-APNS-HOST):** Builds from: App Store · Xcode on the Push group (`host` `app_store` | `development` beside the key parts; `ApnsPush` sends to Apple's production or development host); the stale Test push answer names the Xcode choice; the Record lamp in sentence case.
- **#1623 — Phone: save the Apple push key in Settings ▸ Calls ▸ Phone ▸ Push, Test push with Apple's answer in plain words, and the "Reached you" line on Today (PH16, PH17).**
- **#1622 — Phone PH13 and Line LINE-6:** APNs sends over HTTP/2 and says why a push would not go; the Line's two speech models are Engines rows with their licences and a Download press.
- **#1621 — Programs PG13b:** the launch flags follow the Program's level, a helper inherits its step's level, and every printed level says Secure · Normal · YOLO.
- **#1620 — Programs PG13:** a step's agents follow their Program's control level, not the desk's mode; the desk's routine answers and the tool gate resolve the level per launch and log what they decided under Decided for you.
- **#1619 — Phone PH12 + PH14 (lane PHONE-NEXT):** the heartbeat, meeting aftercare and agent-question reaches through `PhoneService.reach`; the morning release of held messages ("Held overnight: …", one push each). Recipe `docs/internal/betterment/phone/RECIPE.md` marks both shipped.
- **#1618 — Programs:** a coder frame ticks its Program at once (PG12), the race fixture and shot (PG9's leftover), and the Programs line on Today at any hour (PG18).
- **#1617 — A real number from Telnyx:** Connect makes the SIP credential connection and keeps its password in the keystore, Find numbers lists ten with their costs, Buy moves money only on his press through a quote and a kernel receipt, Assign points the number at the Line.
- **#1616 — The bell slot:** the bell reserves its count's width before the Needs you read lands, so the menu bar's right cluster no longer shifts 27 px after the desk settles.
- **#1615 — Install the Line on karol:** add a machine, a one-time code sheet with the whole command and Copy, the row reads Ready on the first hello, pick it as the place, Revoke.
- **#1614 — docs:** reconcile extended guides with current behavior.
- **#1613 — docs:** make the README a concise visual product tour.
- **#1612 — docs:** represent HoldSpeak's agentic Desk and core work flows.
- **#1611 — Engines reads again:** assignment copies carry their own material, the owner's three bad rows are repaired at startup, and a read never refuses an internal capability's row.
- **#1610 — The Line on the home box:** enrolment by a one-time code into a scoped node credential, the pinned Linux build, the systemd and launchd units, readiness from the last hello; one real call Mac → rig hub → karol measured.

- **#1437 — Meeting stopped/save truth:** runtime facts survive HTTP and both Stop doors; non-clean outcomes persist when the live window becomes the record. 40 focused web cases, two native response cases, nine integration cases and final quick green: 4,187 related web, 40 affected Python/browser, 110 sweep, 27 canon, 1,126 repo guards. API consumer docs regenerated. Broader recovery/hardware/UX acceptance stays open; strategy-first #1435 is the next work.

- **#1436 — Capture attempt retention:** seed/gap typing survives refused or delayed Note creation, timeout and editable-field handoff, with exact Retry and no renewed interception. 34 focused cases and required quick green: 4,169 related web tests, five browser cases, 110 sweep, 27 canon, 1,126 repo guards; inspected 1440/393 key-handoff captures. Reload/global-receipt durability remains open.

- **#1434 — Settings leave/return retention:** supersession names covered jobs and accepted leave paths; later same-value conflicts retain the draft and Retry uses the authoritative revision. 66 focused cases, 4,155 related web tests, seven affected Python/browser cases and required quick green; 1440/393 captures inspected. Other Settings audit conditions remain open.

- **#1433 — Ask saved-thread authority:** older reads cannot overwrite a new selection, New Ask or Close. Seven regression assertions red before the repair; 46 focused/143 related component tests, three glass cases, required quick and inspected 1440/393 captures green. Other audit findings remain open.

- **#1432 — review evidence wording:** distinguish the executed publication checks from the additional Settings fixture/control. Local post-merge packet review re-check is RATIFY; product findings remain open.
- **#1431 — 47 adversarial workflow reviews:** independent whole-job/convergence/user-value reviews, root reconciliation and corrected delivery priorities; 204 proposed acceptance challenges. Product fixes remain open; isolated Settings return conflict reproduced. Required quick green.
- **#1430 — desktop application/use-case audit:** app/window/resource contracts, whole-product behavioral inventory and gaps, explorer-style acceptance workload, and hardened capability verification. No product UI or dependency change.

- **#1429 — native-experience research:** retained React stack, source audit, primary-source research, three-engine capability probe and proposed production-pattern delivery. No product UI or dependency change.

- **#1428 — shared surface framework and reference:** working local patterns, common interior material/layout, mounted front authority, responsive window heads, and current author documentation. Required quick proof is in Current phase; exact deployed merge/build is checked through `/api/system/identity`.

- **#1422 — common conversation design:** shared ComposerWell used in Ask and PR replies, continuous paper and readable turn hierarchy.

- **#1421 — Ask feedback:** clear sent input immediately, retain the next draft, compact paper conversation and composer.

- **#1420 — automation save errors:** rejected native-agent and spend-limit saves show a refusal, keep the draft and permit retry. Fixes the post-merge finding on #1419.

- **#1419 — owner feedback, 2026-10-21:** guided Automation
  builder, one-category Settings, clear selection and pictograms, and a Done
  action on the saved feedback receipt. Required quick proof is above; exact
  deployed source is reported by the desk identity endpoint.

- **#1372 — D10:** Today through the shared operation registry and the actual attention source; merged and deployed at `3b90f077a`.
- **#1371 — note regressions:** current editor/footer, keyboard focus and exact uncertain-send retry; merged and deployed at `ec3dde784`.


- #1349 — Projects P4: Projects/Decisions in Go, project state and reason, scoped Write update and withheld dead verbs.

- #1369 — Agents AG11: owned helpers, pinned question delivery, Secure Allow and nested results.

- #1370 — People readiness closes SQLite connections and tolerates journal cleanup; full-question agent browser checks and follow-up reconciliation.

- #1363 — Capture C7/C8: one recording home, truthful failed occurrences, direct Record now and saved speech handoff.

- **#1214 — Useful attention and dismissal.** Dictation journal entries stay
  out of Qlippy. Visible-only Dismiss closes old popup backlog, with exact
  failed Retry and tab cutoff. Quick300/66/107/17 green;14 focused and actual
  six-state1440/393 observations. Delegated source counsel RATIFY.
- **#1213 — In Jupiter's orbit.** Rich local NASA sky/cloud maps, layered
  stars and galactic dust, independently flowing weather, four passing moons
  with shadows and rare Pioneer/Voyager visitors. Quick 3821/651/107/17 green;
  actual amended 1440/393 faces, Motion/fallback and choice graph cases.
  Delegated source counsel RATIFY; formal postmerge review remains separate.
- **#1212 — Desk drawers and live Three.js wallpapers.** Canonical root/child
  drawers, real contents/menu opening, cycle reachability and parent captions;
  selected live scenery, still fallback and shared Motion control. Quick
  3798/651/107/17 green; actual 1440/393 flows and real filing graph cases.
  Delegated source counsel RATIFY; formal postmerge review remains separate.
- **#1211 — Decision readers and shared window seams.** Compact reusable Send,
  exact save recovery/newer-draft continuity, current ordinary previews and
  front-window pointer ownership. Quick 3764/651/107/17 green; actual 1440/393
  walks and real pointer/touch multiline Save cases. Source counsel RATIFY.
- **#1210 — Follow-through and attention surfaces.** Readable task ledger,
  inline Manage with retained drafts/exact Retry, canonical Snooze before
  collection and duplicate suppression; Brief selection/decision readers.
  Quick 365/1335/107/17 green; actual 1440/393 walks and real Snooze graph cases.

- **#1209 — Opened Workbench and Accounts.** Named multiline composer,
  coherent configuration and library cycles, readable item material,
  honest progress and engine repair; shared Pad width-resize clipping fixed.
  Account status contained, Add within provider row, refusal/draft lifecycle
  preserved. Quick 4935/709/107/17 green; 16-state walks at both widths;
  real graph Add pointer/touch passes. Source review RATIFY after fixes.
- **#1208 — Continued surface refinement.** Schedule, email recipients/key
  reuse, History recovery, Knowledge unavailable members and terminal handoff;
  shared Pad mic clearance. Quick GREEN,1440/393 production walks and one
  independent source review/recheck. [Record](../docs/internal/SURFACE-REFINEMENT-2026-10-15/README.md).

- **#1207 — Continued visual refinement.** Shared Workbench composition across
  Inspector/Thread/Agent/Workbench/Calendar; honest recovery, one result reader,
  stored mint fact wire. Quick GREEN,1440/393 production walks, independent
  source review RATIFY. [Record](../docs/internal/VISUAL-REFINEMENT-2026-10-15/README.md).

- **#1199 — Model discovery and download repair (2026-10-13).** Bounded
  Find on LAN; corrected signed Qwen catalog and default artifact locators;
  fully verified quarantine reuse; Week Send readiness; one engine footer
  with reachable confirmation and Settings return. Quick check GREEN
  (3,472 web / 1,707 Python (2 existing availability skips) / 106 sweep (3 existing xfails) / 15 canon); final typecheck green, 9 engine browser cases and 2 isolated
  graph entry walks passed. Owner installation/inference remain unobserved.
  [Handover](../docs/internal/HANDOVER-MODEL-DISCOVERY-DOWNLOAD-2026-10-13.md).

- **#1198 — Daily journeys, one combined PR (2026-10-13).** Prep → Record;
  inline Outcomes correction and durable destinations; selected Note → Task /
  Ask; draft-safe bulk confirmation, honest reread Retry, scoped scroll place,
  quieter Ask and readable desktop/phone rows. Quick check GREEN (3,508 web /
  1,302 Python / 106 sweep / 15 canon), final typecheck green, 10 real isolated
  hub walks passed. Remaining observations are explicit above and in handover.
- **#1197 — Productive desk, one substantial PR (2026-10-13).** Meetings record
  inside its app with Back and reload; one Outcomes review and durable Done;
  accepted actions in People prep; Note → Task/Project/Ask with saved source;
  chosen engines before legacy markers; one-press Room draft and plain retry;
  Engines/Accounts in Settings, durable close, job sizes, phone Go/Back/More;
  one attention list, plain Note words and a quieter fresh desk. Retired faces
  and tests parked. Quick check GREEN (3,699 web / 4,709 Python / 106 sweep /
  15 canon), typecheck and API manifest green, eight isolated real-hub walks
  passed at 1440/393. Owner/model observations and deferred scope above.
- #1148–#1187 — THE DIET, PUSH 2 (owner 2026-10-12: "I need that to be pushed and pushed more"). Measured first: the count is not the cost (6,943 FAST tests under 0.05 s cost 75 s together; 821 over 1 s cost 1,753 s). BROWSER: live files 118 → 34, phase-named 98 → 0; what stays needs a real browser (drag, keys, focus, touch, mic, multi-browser, exact geometry), one tests/e2e/test_<app>_glass.py per app plus shared rigs; ~84 files parked in tests/e2e/_parked/ with a successor per check (README). VITEST: 168 source pins (CSS, markup, source censuses) retired, 10 files parked in web/src/_parked/; KEEP-RULE scans kept. FAST WALL: one hub per module and event waits, not sleeps (#1157, #1161, #1163, #1174), reconcile in one query (#1180), quick_check affected 3 → 0.6 s (#1178), a per-worker template test DB with re-stamped seeds and a real_schema opt-out (#1186): FAST 355 → 262 s wall, 2,553 → 1,900 test-s, same load. PRODUCT BUGS FOUND AND FIXED: a failed hub start kept the DB owner claim (#1173, plus an autouse leak guard in tests/conftest.py that fixed 12 order-dependent FAST reds); Accept on a proposal stalled 5 s and lost its pipeline event (#1168); /api/setup/status always said 127.0.0.1 and never saw the token (#1183); Memory moved 30 px on a slow first read and every surface window's lazy fallback read as settled (#1182); Chair week row moved 140 px at 393 (#1156); System shade egress testid never reached the DOM (#1169). CI no longer installs WebKit (no live test uses it). SWEEP: one fence each over every app: 44 px targets at 393 and reduced motion in `still` (#1185), Missed shade + Door both-picked cases (#1187), no private LAN literal in web/src (#1181; the topology endpoint placeholder showed the owner's LAN engine); palette rows 26 → 44 px and filter tokens fixed; KNOWN_REDS: menu-bar titles, palette mic, dictation Edit stack value at 393. Open: T2 owed (9_03 Room words need a recorded Room wire; doors D6/D7; Record→Stop; Brief-day); the C3 drag starts in the parked Project drawer.
- #1126–#1143 — THE FAST DIET (owner 2026-10-12: "we still have almost 16k tests. What gives?"): seven area lanes classified every fast test (KEEP-BEHAVIOR / KEEP-RULE / FAKE / DUP / STALE). Result: 1,073 → 984 files, 12,863 → 12,521 test functions, ~15,875 → 15,739 collected, phase-named files 284 → 87; 146 files parked in tests/_parked/ (not collected); retired tests each name a successor; ~15 new behavior tests (hook redaction, brief clock, scheduled brief, hub shutdown clears every conductor, ProfileService refusals, settings PUT, heartbeat backfill and others). Real bug fixed on the way: a calendar test left the DB singleton on its own tmp DB (13 later tests failed 'no such table'). Lesson: most fast tests are real behavior; the waste was phase-named clutter, not thousands of fakes. Open: the graph-walk calibration red (2 slow tests, a transcription double no longer installed after a move), the desk-sweep flake inside quick_check, ~87 phase-named files that others import or docs cite.
- #1113–#1125 — the fast cycle (#1114, #1115, #1121, #1123), the topology fit (#1113, #1116), flake fixes by cause (#1117–#1122, #1124, #1125).
- flakes (bus) — test_live_bus boots on its own DB and HOME and a free port (it shared the shard HOME's default DB and a fixed 8917; both reproduced red); roomInFlight.f2 waits take 5 s (not reproduced in 240 repeats).
- #1124 — flakes (still): late first reads say they are reading (speech row, destinations, People 1:1 caption); four held-read cases fence it; FirstWords and needsYou.app test races fixed.
- flakes (still) — the desk sweep `still` flakes were late first reads: the speech row (Live 46 px, Speak 58 px), the destinations group (Settings 135-764 px) and the People 1:1 caption (Conductor drawer 24 px). Each now says it is reading (aria-busy) until its first read ends; four held-read cases fence it (red before, green after).
- #1122 — flake: the Runs on Try it wait read `REACHED · qwen3.8 27B` exactly; the probe adds `· N MS` when it measures over 0 ms (under load only). The fake engine answers in 5 ms; the wait reads the ms token.
- #1120 — flake: the person window kept Prep over his first tab press (the mount lens effect ran after the press); the mount run now only keeps the place.
- test_lock priority (fix/test-lock-priority) — `HOLDSPEAK_TEST_LOCK_PRIORITY=low` runs (the main watcher's shards) never take the lock while a HIGH run (the default: quick checks, lane runs) waits; waiter markers `<lock>.waiters/<pid>.<prio>`, stale ones removed; the flock stays the mutual exclusion; poll 1 s. Fence: test_test_lock_priority.py.
- quick_check hardened (fix/quick-check-harden) — Astra's five fix-forwards: vitest fails on any unhandled error but jsdom's canvas "Not implemented"; affected tests by AST (`from holdspeak.pkg import mod`, scripts/*.py, tests/uat + tests/e2e files, `QUICK_TESTS`; web files outside web/src reported NOT COVERED); the sweep must prove it ran (≥60 passed, never skipped); a bad base or git error is red; the build runs under the lock. Each fix proven red by a planted case.
- #1119 — the dock outage receipt named whichever Desk read rejected first (READ ARTIFACTS / NOTES / MEETINGS by timing; the 393 dock glass red on main ab43627c6). It now names the first failed read in the Desk's order (Meetings), every time; fenced by loadAllOutage.test.ts.
- #1118 — the 393 remembers red on main was the test: a touch tap hit the Room's Draft update while it was still disabled (engine read pending); `_press` now waits for an enabled control (10/10 green).
- steward-order fix-forward — steward runs list newest first when two start in one second (rowid breaks the created_at tie in db/steward.py); the steward shape fence red on main ab43627c6; fixture re-recorded; 10/10 green.
- #1111 — THE REFIT (supersedes #1110): owner-driven live redesign, 2026-10-11/12 ("the UI is just abysmal… fast iterations"; "never MUI/bootstrap — our design system, made better"). Plain chrome words (Today, Archive, Desk, Terminals, Your network); shared kit (kit-pill, Steps, AskWell quiet, compact 13/12 px type, 19 px headlines); Today = the day as a timeline (owner pick C); Brief cleaned (one chip per source, pages speak as you, folded Send); Meetings (steps, summary first, REC lamp, Import/Review/Artifacts); People (Prep-first, owed both ways, agenda Remove route, bounded roster reads); Speak (setup first, Talk plate, Journal spine, Learned); Room (plan spine, signals plate, folds); Settings (two-plate home, plain Guide via doctor face_words, GitHub one row); Conductor (asks and held calls on plates, one-press Approve, lane window). Hub stops in seconds on Ctrl-C. Astra: #1110 four MUSTs + #1111 three MUSTs paid. Whole suite green: browser 672, FAST 15848, web baseline clean. OPEN OWNER CALLS: Components topology demo at 393; Runs on paints jobs before detection.
- #1105–#1109 — test diet done (see above).
- #1108 — sweepreds: the desk sweep's known layout reds fixed; five windows wait for their first reads (8 s cap) so idle never moves; the hub-opened Chair window draws on the phone without covering active work.
- #1107 — test diet final B: recorded doubles + strict shape guard; flakes fixed by cause; card redactor boundary; atomic node cursor; steward receipt refs; parent_thread_id; GET /api/updates/{id}.
- #1106 — test diet final A: 21 more browser files parked on recorded-answer successors.
- #1105 — gadgets ⌘K leg waits for the palette's ranked list.
- #1103 — THE TEST DIET wave 1: the desk sweep (#1102) + MEET (#1098), ROOM (#1099), AGENTS (#1100), DESK (#1101) moves; product fixes found on the way: thread status_line on the wire; Room merge-poll notice proven; Needs-you Confirm count corrected by a recorded answer.
- #1097 — palette rank: Projects draw ranked (the list waits ≤600 ms for its rank reads); Enter pressed during the hold runs on the ranked row; Esc or typing cancels. Regression: gadgets G4 ⌘K (fix in flight).
- #1095 — Phase 17 redact: one redactor (holdspeak/redaction.py) on every provider/model/channel/actuator/factory error path, the observer (tree redaction before encoding), MCP error results, log files and uvicorn's loggers; redact before every cut; linear patterns, 1 MB hard cap, 64k output cut; ports and cause words survive. Astra 2 iterations; iteration 2's four leaks fixed pre-authorized and verified by the author. Ledger: an Authorization header redacts to end of line, taking any address after it (safe direction).
- #1094 — Phase 17 phonepass: the Room draws after its sections' first reads (reads register as they mount; 8 s cap; late sections stack below in resolve order; a Project change remounts); palette rows keep their places before rank limits; the People caption clears the Conductor notch. Ledger: palette keyboard index can drift when an earlier row leaves; the palette grows within one opening; a late row can repeat its section band; FILES settles at once if the global flights read already ended.
- #1093 — Phase 17 evalerror: a source's evaluation error is stored redacted and bounded and shown in Details; any Authorization scheme and cut URL passwords redacted; the original provider error survives a failed diagnostic write.
- #1091 — Phase 17 snapjump: a title press never tiles a window (no native drag during a title hold; snap reads the real pointer; only a real release tiles)
- #1090 — Phase 17 words: Settings in plain words (headline names the engines; Other devices; Reset desk to defaults; one RAW fold; Setup failing checks first); name/aliases editable in Settings ▸ People; delayed saves are newest-wins and flush on leave/unmount; doctor reads the re-pointed config file
- #1089 — Phase 17 mainreds4: eleven stale fences after the Phase 17 merges; UpdatePosture waits for the engine read
- #1082 — Phase 17 meetingwin: a meeting opens in one window (pullout:meeting:<id>) from every door; live → record in the same window; Meetings app is the list; a person icon opens the person; hub migration of old scoped windows; recording freshness epoch; returned person/meeting windows are not pruned on reload
- #1087 — Phase 17: a deliberate Conductor open always shows it (hub opens keep the seat); _open_lane through Go; glass shots via evidence_dir + a write guard
- #1086 — Phase 17: two main reds were stale rigs (Settings via the HoldSpeak menu; the import rig unloads the old page before a reset)
- #1085 — Phase 17 first run: Start here = three jobs with door buttons; Get ready reopens from Setup; Open my desk; one line per card; recovery doors work fresh and reopened
- #1084 — Phase 17 coders: "coders" on Conductor faces, ready = can run, hooks token; Room: Watch sources, one Draft update (waits for the engine read), Off/Tell me/Do it, Receipts under History
- #1083 — Phase 17 Runs on words: plain lead line per job with the effective route (summary override first), outcome names, hostPlace mirrors the backend loopback rule exactly (shared JSON table), one chip per meeting
- #1081 — Phase 17: the owner's default day one fenced end to end (Import → real conductor → summary + receipt in the open record, no reload)
- #1080 — Phase 17: a hidden Chair window keeps its plane across 393↔1440; a real close retires it
- #1079 / #1077 — Phase 17: rigs whose subject is the manual Run press turn auto-summary off
- #1078 — Phase 17 doors: one primary door per app + menus as the index; Dock = Intelligence/Speak/Meetings; Go 9 rows + Projects/Tools; Missed/Memory; next 1:1 on the People icon; an open restores a hidden window; Ask AI on the phone Go
- #1075 — Phase 17: Runs on's empty foot hides; the HIT fence scrolls only user-scrollable boxes and fails sibling-covered centres
- #1073 — Phase 17 transcribe: an audio-only meeting gets Transcribe once speech is ready (atomic claim, frozen route, owned fields only, summary rule)
- #1074 — Phase 17: the meaning-search refusal fence re-signs in after a 401 (the sign-in fix forgets a refused token)
- #1070 — Phase 17 windows: a Room keeps its identity across reloads and views; first places saved; new windows clear of the icons and of the home windows' seats; ⌃-based keys a browser tab passes; Meetings opens 920×720
- #1069 — Phase 17 one desk: the Screen is the only desk; the Floor parked; window Object ▸ menu (Delete for off-desk kinds); delete receipt above every window; zone windows retired; the chosen place as the backdrop
- #1068 — Phase 17 sources: Add source in the Room; sign-in command in each row; every project opener opens the Room; Register and Park receipts in the Room
- #1064 — Phase 17 summaries: a summary after every meeting on a chosen or local engine (disclosed route + receipt); the brief rebuilds when stale, covers the previous workday, keeps itself on a failed rebuild
- #1062 — Phase 17 decisions: a meeting shows its decisions (record state); a decision hit opens the decision; Intelligence → Decisions lists every decision, paged
- #1071 — Phase 17: a check precondition waits 15 s for a loading face (rig 1.5.4); the first-run walk flake under load
- #1066 — Phase 17 speech: one speech-readiness truth (the admitted route's model + a runnable backend) on Speak, Live meeting, Runs on, Setup; "Set up speech" in place; audio-only meetings say why; the REC clock follows the live frame
- #1067 — Phase 17 webreds: the six Phase 16 vitest reds at their causes (Runs on foot container query; keymap typing() on a non-Element)
- #1063 — Phase 17 needsyou: one row per cause+repair+host (30 signed-out sources → one row, Details behind); work first; one count on the icon and the bell; Reconnect focuses its Settings row
- #1061 — Phase 17 people: "They owe you" (report_owes) on Now and Prep; agents never count private People items; plain labels; Add person stays on the list
- #1060 — Phase 17 thoughtsend: a thought is sendable (note source); Copy and Send on the Thought foot; Send waits for a clean save
- #1059 — Phase 17 wayin: the desk stays signed in across tabs, bookmarks and restarts (token per origin; a 401 forgets only the refused token); a plain sentence when signed out; --no-open prints the URL; a 0.0.0.0 bind prints this Mac's and the LAN address
- #1058 — Phase 17 objverbs: the Chair's selection is the store's (Object menu, right-click, F2 work on the Chair); New Note starts untitled; untitled notes keep a shown name in pickers
- #1057 — Phase 17 usability inventory (four walks, U01–U37)
- #1055 — Phase 16 R4: the two People reds on main (one keystore path in the glass rig)
- #1054 — Handover XXXVII: Phase 16 The Compositor; CLAUDE.md one-hub-one-desk rig rule
- #1046 — Phase 16 B: window authority to the hub (DeskWindowService, /api/desk/windows, MCP desk_window_*, the browser as a presentation; two browsers = one desk)
- #1051 — Phase 16 R3: thirteen inherited browser reds at their causes; the thought foot wraps its receipt
- #1049 — Phase 16 RIG: the rig never reads or writes the owner's state (agent config paths, active window, notifications, channel keys, gh config, git system config; replyless boundaries refused before boot)
- #1047 — Phase 16 R2: the last reds on main at their causes, the blocked atlas cases, rig hubs never read the macOS calendar
- #1044 — Phase 16 C-atlas: the Concierge atlas cases ported to Runs on; the rig reaches no real engine; the read-only live walk
- #1041 — Phase 16 C2: a returning task comes back to the front (Prepare behind the Runs on window)
- #1039 — Phase 16 R: the inherited reds (the palette's reduced-motion transition; three 393 fences; the quiet-hours fences; the badge wash)
- #1035 — Phase 16 A3: the interior kit (eight species in the library + contract) and the four faces composed from it (Needs you, the Room window, the Conductor, the meeting)
- #1036 — Phase 16 C: Runs on, the Models app as a Switchboard (SurfaceSwitchboard; drag to patch with CAS + revision-bound Undo; Try it; FOUND with Use it; downloads in place; the Concierge, the pickers, Adjust and the assignment sheet parked; ten browser files ported)
- #1034 — Phase 16 A2: the compositor core (seven pure modules, planes from a depth counter, the nine verbs and keys, Exposé as live windows, the derived divider, the moments)
- #1032 — Phase 16 A1: the material and the chrome (the light, the slate interior remap, the depth ladder CSS, title bar B + icon/sans/lamp, the backdrop floor, dock seats for every window)
- #1030 — Phase 16 The Compositor: the guidelines (§1–§13) and the ratified canvas (v3: compositor, interior kit, Runs on switchboard)
- #985 — Phase 15 10: READY means ready; speech is speech; the LAN box on first run; receipts, not surprises
- #986 — Phase 15 11: doctor speaks plainly; five seed notes; the phone menus fit a phone
- #980 — Phase 15 09: the Brief regenerates and is dated; The week is never empty; one Needs count; windows come to the front
- #989 — Phase 15 12: four Dock sprites; honest widths and labels; the Send well reads folder names; an empty Project reads NEW
- #992 — Phase 15 02: rehearsal 1 part B, the bounce log
- #991 — Phase 15 13: the Codex trust step survives > 1024 open descriptors (the FAST flake was a product bug)
- #983 — Phase 15 08: a meeting yields decisions and confirmable action items on day one
- #982 — Phase 15 07: the transcript never loops silently; windows rarely cut sentences; honest titles and footers
- #975 — Phase 15 05: the default feeds the Conductor; the Brief generates itself; Anthropic reads NOT SUPPORTED YET
- #981 — Phase 15 06: the inherited glass reds re-anchored to the screen and the drawer
- #979 — test_lock: one test run at a time on the machine
- #977 — Phase 15 02: rehearsal 1 part A, the bounce log
- #974 — Phase 15 04: the Parked drawer; Resend default; a denied calendar has a way forward
- #967 — Phase 15 01: the summaries blocker asks the route policy; OFF holds and is never a failure
- #968 — Phase 15 03: the summary draws once; a WAV import always reaches a final status
- #966 — Phase 15 02: the LAN model's key on the Concierge; doctor runs the whole list
- #965 — Phase 14 A5b: the Needs drawer keeps the Project → drawer and proposal → Room paths; a proposal request never saves
- #958 — Phase 14 B2: the material pass (bevels back, chips to lamps, the window well)
- #954 — Phase 14 A1c: the summary card opens Capture; the 393 aftercare waits
- #956 — Phase 14 A0c: the 32 px world set drawn at 32; Codex keeps its face on every face
- #959 — Phase 14 A1d: the fresh-arrival glass waits for the sprites (393 icons were a test race)
- #935 — Phase 14 A5: Needs you as a smart drawer (one object one row; no Approve on a cut call)
- #953 — Phase 14 C0b: the agent-event spool drains on a hub timer
- #951 — Phase 14 A1b: the arrival fences and 84 atlas cases re-anchored to the screen
- #945 — Phase 14 A2b: every generic Project path opens the drawer; decision-record hand-offs launch
- #947 — Phase 14 C4: the Agents application and AGENTS section fold into the Conductor drawer
- #946 — Phase 14 C3: drop to hand (board A-3)
- #939 — Phase 14 A1: the screen (the Chair's tiles retire; the Chair is the A-1 screen)
- #937 — Phase 14 A2: the drawer (a Project opens as a drawer; the list is a list; `[ ]` gone)
- #941 — Phase 14 C2b: the lane composes the library species; 393 footer; stalled-send recovery
- #933 — Phase 14 C2: the agent's lane window (board A-4 + C-4's track; tmux behind Raw)
- #934 — Phase 14 A0b: the D1 icon mold installed (world sprites, states, Dock); old mold parked
- #932 — Phase 14 B1: the object species (library only)
- #931 — Phase 14 A0: the icon mold sheet; ruled D1 Workbench+
- #927 — Phase 14 canvas: The Desk Is Objects, three alternatives + control (harness and shots only)
- #925 — Phase 14 C0: the launch lane backend (events, worktree facts, lane route; secrets redacted before the cut)
- #924 — Phase 14 charter: The Desk Is Objects

- #882 — ⌘K two-line memory hits (owner pick B): the matching passage with the query marked, a FoundBy token (KEYWORD/MEANING/TIME/NAME/LINK) and the day; selected/hovered/focused rows at 5.24:1
- #877 — Memory where the work lives (owner pick B): beliefs in Desk memory with evidence and history; standing pages in the Room (project) and the Brief (desk); withdrawn evidence hides at once on any desk change; pages bound to their scope; SOURCES counts distinct sources
- #872 — Backend coherence: one needs-you number on every face (palette re-reads on open and on change); roadmaps read cached (~60 ms warm); every stored stamp aware UTC (census fence), DST-safe, a one-time backfill of old local stamps (sync-written columns excluded) and instant compares on the queues; People text scrubbed from old Brief sends; background writers and MCP announce
- #876 — Onboarding on one screen (owner pick A): Calendar and Connections cards under the first-run three; Ready on top with his name and three verbs (Record the next meeting, Dictate, Ask about this week); every card lit; macOS prompt only on press
- #875 — Route in footer (owner pick C): a lamp per Ask/chat turn from its receipt (least private sent attempt; FALLBACK marked); the footer carries the last turn's host, model and its own receipt; failed Asks keep their route; one egress classifier everywhere
- #871 — Memory leftovers: every read tool replays as a re-read stub (classed by its originating call); the routed Thought reflects pages and observations; thread time bounds as instants; dead runners stop holding extraction; secrets are never search keys; hand-attached sources redacted (schema text kept)
- #870 — Memory accuracy: dates by named month and reported tense, both years by tense (EXTRACTOR_VERSION 4, re-recorded live); the initial-alias rule; one cited input must hold every content word of a page sentence; content-hash page staleness
- #869 — Face polish: 393 Dock pages start on a whole item; the Chair reopens at its tile; Roadmap from the palette opens by its own name; honest Calendar tokens; palette matching stays within a word; paths shortened only under the known HOME; Processes names its targets; product words decision/thread/workbench; Roadmap rows no longer overlap at 393
- #868 — Defaults: hub on 8765 with a fallback; doctor's token only to loopback; blank MLX = not set up; a loopback rescan until a default exists; a durable summary backlog for meetings saved with no engine (honours Skip; drains only to a local or owner-chosen engine); the meeting-intel queue follows the global default; onboarding backends (macOS Calendar via EventKit, ICS check, gh/acli detection)
- #867 — Housekeeping: typed MCP errors; long MCP tools run in parallel under per-key locks (atomic open_review / draft_update / watch.test); a PR review after a story edit is a new run; tmux test rig isolated; 1,363 dead lines parked; DB open about twice as fast; nightly tmp space fixed
- #864 — Built-in "HoldSpeak folder" Send destination (~/Documents/HoldSpeak/Sent; XDG Documents on Linux), re-created if deleted; saved folders still refuse when missing; a synced Documents (iCloud, Dropbox, Google Drive, OneDrive, any File Provider) is labelled and receipted as leaving the device
- #862 — First run review fixes: a late mic grant is stopped; the owner's aliases never claim a named other person; FOUND shows one true default; a blocked mic shows tokens, not a paragraph
- #861 — API manifest and census for the first-run FOUND control (main was red after #859)
- #859 — First run "C1 · Heard first" (ratified): one Set up local AI press; First words lights when speech lands; his first sentence played back big; his name and aliases count in needs-you; FOUND engines with Use it. Merged on the owner's word before Astra's review finished
- #856 — llama.cpp runtime in the base install; one-press Set up local AI (sha-pinned Whisper, embedding and starter models, one egress receipt); no download at boot or on load; the starter serves meeting analysis; meetings summarised by default when an engine exists
- #855 — Batteries-included default: a local engine on this machine becomes "Default for AI work" by itself (loopback only, no proxy, no redirects; made_by stored with the assignment); LAN and cloud engines are proposals; memory follows a local or owner-made default
- #853 — Heartbeat: every_sweep no longer notifies in quiet hours; quiet-hours tests use fixed clocks (they failed nightly 2–3 and across DST)
- #852 — Chat no longer replays withdrawn recall: saved grounding is re-read per turn; saved memory tool results replay as a re-read note; containers keep live members
- #850 — Memory slice 6, backend: Ask and chat ground pages, then observations, then recall; refitted before every pass; `memory.page` in the chat palettes except Plan, no palette larger than before
- #848 — Memory slice 5, backend: standing pages per project and desk (dark until `memory.page` is assigned); every sentence checked against its cited inputs; withdrawn inputs withheld at read; drafters read pages as context
- #846 — The Door week test seeds inside the local week with one pinned clock (it failed on Sunday evenings)
- #845 — Memory dates by tense (next such day for things to come, last for things done), spans keep their length, no title-named projects; observation tables refuse rowid rewrites (EXTRACTOR_VERSION 2)
- #843 — Memory slice 4: observations with evidence and history (dark until `memory.consolidate` is assigned); each text version is served only while its own evidence is live in scope
- #841 — Nine harder relation questions: keyword search answers none, the entity walk answers all; a strict expected-fail for the initial alias
- #839 — Memory slice 3: fact extraction, entities and the entity walk (dark until `memory.extract` is assigned); facts serve only while their source text is live; extraction yields to foreground calls on the same engine
- #837 — The calendar test seeds its event in the local week (it failed every Sunday evening west of UTC)
- #836 — Recipe chat searches memory through the thread turn, proven by a live test; the agent tool turn is recorded as retired code
- #834 — An edited dictation is remembered by its new words (memory and the Journal search); Replay's before-text is the edited text
- #832 — Memory slice 2: Brief items, dictation, steward runs and Room answers are remembered; keyword search over the memory index works with no engine; time ranges compare as instants
- #830 — Memory for every AI job: one policy row per capability; cadence, decision, PR review and rails drafts read memory; memory fits the job's token budget; no self-recall
- #829 — Memory reads a time phrase from the question ("last week", "in September", "since Monday")
- #827 — Muad'Dib and the Fedaykin run on Opus 5.5 (owner ruling 2026-10-04)
- #819 — Evidence moved to branch `archive/evidence-2026-10-04` (16,389 files, 2.3 GB; `pm/ARCHIVE.md`); the tree is 10,612 files, 172 MB
- #812, #814, #799–#811 — The long-standing red browser tests fixed (29 stale tests, the rig's late-step verdict)
- #798, #801–#805 — Regressions from the 2026-10-03 merges fixed (merged rows keep sources, lamp labels, windows clear the Dock)
- #797 — The default run is green after "every write announces"
- #795, #796 — Memory slice 1: meaning search fused with keyword search; local embedding model; privacy and egress fences
- #787 — The memory design
- #794 — Floor list: a row can be selected and Get Info opens; rename works
- #777, #768 — Prep, the meeting summary, the 1:1 brief and the update draft read memory
- #785, #771 — Every write announces itself; the Room, People and Intelligence views follow
- #788 — One needs-you rule on the hub; every face reads its number
- #790, #781, #792 — Every New verb opens its window at once; the Thought window keeps every key
- #775, #779, #772 — "Name an owner", Workbench Run with no engine, Context save
- #789, #793, #778 — Faces that contradicted themselves; the Agents roster; times in the owner's zone (and a schedule repair)
- #786, #770, #774 — Summaries, sends, updates, Prep, calendar and actions are findable; Decide decisions findable in their Project; the palette searches content
- #791, #782–#784 — The default test run made green
- #767 — The sent Brief carries no People data; a stale prepared Brief refuses to send
- #769 — Chat guardrail and compaction find their engine by route
- #766 — Every MCP tool runs on the hub (11 were broken); calls stay in order
- #776 — An owned item reads "To review", not "Unassigned"
- #773 — The 2026-10-03 inventory
- #772 — Context saves; a failed save reads as plain words
- #765, #764 — Astra is the reviewer; one final review round, at most 2 iterations
- #763 — Fast tests
- #763 — Fast tests: 5 min 40 s default run, scoped browser tests, nightly full
- #762 — Generated docs out of git; test maps cite text, not lines; no count checks
- #761 — The commit gate is removed (branch, PR, one review, merge)
- #755 — Phase 13 close, Astra's record (B0 done; 18/18)
- #747 — Phase 13 B2
- #748 — Phase 13 B4, windows
- #759 — Phase 13 title bar design
- #760 — Fedaykin are Fable 5.1 (docs)
- #758 — Phase 13 story 11 close
- #757 — Phase 13 B0 reds fixed
- #754 — Phase 13 C4
- #756 — Phase 13 H-C4 attendees fix
- #753 — Phase 13 close, Astra's record


Pending-run Stop repair — #1451 — is merged and running. Independent Sol
advisory RATIFY, 42 focused unit tests, 1440/393 real cancellation/late-answer
proof and final types pass. Required quick passed 22 related UI, 2 browser,
110 sweep, 27 canon and 1,126 guards. The producer Stop is unobstructed; no
remote physical-abort claim is made. P06 now has final source advisories and
five passing focused browser cases; final integration checks pass
after the opener forwarding correction passed 196 focused tests. Latest full
tape is not green. Zoom/reload geometry and browser-test corrections remain
separate delivery; the earlier Send timeout cause is still unverified.


Browser test readiness follow-on — #1452: Conversation now waits for Patterns before
choosing the wide button or narrow picker. Both reference widths and the393
real Send/Edit/Back/folder-byte scenario pass (3/3). The earlier Send timeout
has not reproduced and its cause remains unknown; retained pointer/return
state diagnostics cover recurrence. #1452 merged after the required quick
passed all 18 affected browser cases,110 sweep,27 canon and1,126 guards.

The combined browser check found a stale P04 expectation for the global card
parked in #1451. The two source jobs now verify actual inline progress and
reachable Stop without that card;1440/393 pass. Required final quick passed:18 affected browser cases,110 sweep,27 canon
and1,126 guards. No full-suite green is claimed.
Historical deployment receipt for #1451: backendc7fec7ef3f2fc43bd878df5e02fc38ce68492777,
frontend f2eef8675d5cce2e, PID42688, owns_database true, diagnoses empty,
four health/routes200. CLI/MCP match and feedback defaults on; Presence off.

P06/J3 first whole filed-source job is built in wave7 and received final Sol
advisory RATIFY for navigation and Room. Five real-browser cases pass across
focused runs at 1440/393: A/B Note source isolation, Ask version pin, saved
source/Thread doors, exact original Project row return, current missing/moved/
read-failure/Retry/supersession states, and local Components Files. Canonical
closed-source reopen is browser proof on desktop; legacy bare-key is unit
proof. Required final quick and whole-tree types pass; no full P06 or owner
aesthetic acceptance is claimed. Job origin is transient navigation, not added material
or automatic filing. The #1451 delivery introduced unobstructed pending Ask Stop.


Owner requested a whole-plan reality check. DELIVERY-PLAN now has explicit
P01–P10 delivery/remaining scope and a near-term visual adoption pass across
the already-built cross-app path. Six workflow/component slices have shipped;
no full package or 47-family/visual acceptance is claimed. P06 integration
found 15 ordinary opener call-shape regressions across 10 existing test files;
shared forwarding now passes 196/196 focused tests without changing their
expectations; final integration quick and types pass.
See native-experience/EXECUTION.md for actual source/PR/proof boundaries.


Verified deployment #1452: PID62168, backend b18fcc0d93d3f20a681869c00d1d9126ce97cc16,
frontend f2eef8675d5cce2e; owns_database true, diagnoses empty, four routes200.
CLI/MCP match, feedback defaults on and Presence remains off. This is the
last verified deployment before the Project delivery, not a claim that a
future merged revision has already been observed.


Project filed-source delivery — #1453: required final quick GREEN (build,4,309 related
UI tests,5 affected browser cases,110 sweep,27 canon,1,126 guards), final
whole-tree TypeScript exit0. It preserves Note-only pinned Ask material,
saved source/Thread doors and exact transient Project return without filing
answers or adding Project context. Six bounded workflow/component slices are
now delivered; no whole package/47-family/visual acceptance or full-tape green.
The reconciled plan puts shared Room/list visual hierarchy first, then Note/
Ask content balance before widening Meeting/Agent migration. Independent final
NAV, Room and docs advisories are RATIFY; local Sol, not Muad'Dib checks.


Zoom/reload normal-rect follow-on — #1454 — is source-reviewed (Sol RATIFY) and has
focused unit/browser proof. Optional autoRects preserves an unsized normal
frame through reload while leaving owner sizing and auto height separate.
Integrated with #1453, required quick and final types pass:4,310 UI,10
Frame glass,110 sweep,27 canon,1,126 guards. Close/reopen while still zoomed is not newly established by this
bounded reload case. No new whole-package or full-tape green claim.


Verified deployment #1453: PID69936, frontenddc40153929c4c785,
backend12366e1e32685bc541a740b3f7640f6ee39681fc. Database ownership true,
diagnoses empty, four routes200; CLI/MCP aligned, feedback on and Presence off.
First visual Room/list slice is now active in wave8 against the updated plan:
Canvas B/F painted first, product build in progress; no visual acceptance yet.


Firefox feedback lifecycle extension — #1455 — is test-only and source-reviewed:
final Sol RATIFY, explicit slow Firefox2/2 at1440/393. Measured zero mic/save
starts through cancelled capture; same-bundle ASR-only Retry, late old result
fencing and usable Settings return pass through real routes with a local
admitted stand-in. No owner-provider/hardware or old-freeze-cause claim.
Required quick passes (build,110 sweep,27 canon,1,126 guards); explicit slow
Firefox2/2 is separate proof, not quick affected cases. Full P10 stays partial.

Visual wave8 has four focused Chromium cases and final local source advisory
RATIFY after retained-refresh geometry and reference outcome fixes. The first
combined run passed6/9 and found three arrival/fault-injection rig races;
those three now pass concurrently without product or assertion changes.
Final required combined quick is rerunning; owner visual acceptance stays open.


Verified deployment #1455: PID31240, frontend3e1c98209c61a463,
backendb00d95eded8eab88d5bac81d5579934c6f769432, owns_database true,
diagnoses empty, four routes200. CLI/MCP aligned, feedback defaults on,
Presence off. Visual slice's final combined integration check remains open.


Latest completed #1454 full tape is RED: Hand-again instruction timing,
Components arrival, Thought393 caret hit ownership and three Room late-read
geometry cases. Components arrival is corrected in unmerged wave8. The
Thought hit blocker and44px late Sources/Plan movement remain unresolved;
Files retained-refresh stability does not close them. The current wave8
integration also reproduced a real Project focus handoff failure: focus was
attempted while the loading body was visibility:hidden and marked consumed.
A narrow presentation-ready correction is in progress. No final integrated
green or visual acceptance is claimed. Details: native-experience/EXECUTION.md.


Room/list visual continuation: final required quick GREEN — build,4,314 UI,
all9 affected browser cases together,110 sweep,27 canon,1,126 guards;
whole-tree types exit0. The real hidden-body Project focus failure is fixed
through existing presentation readiness, with12 focused section checks, both
full-job widths and3 extra desktop runs passing. Sources fault recovery now
releases only on the real Retry click; the fixture guard excludes only the
ambient Desk heartbeat. Delivery PR1456. Remaining Thought393 hit
ownership, delayed Sources/Plan movement and Hand timing findings above stay
open; this is bounded adoption, with owner visual acceptance still open.
