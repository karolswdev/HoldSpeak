# Automations: recipe

Build order for `DESIGN.md`. One slice = one PR in the fast cycle
(`CLAUDE.md`). File and line references come from `MODEL.md` and `RECON.md`
(2026-10-17); check them against main before you start.

Rules for every slice:

- Tests never touch the owner's real HOME, DB or Keychain.
- Faces obey `docs/internal/UX-CANON.md`: the library Button, no modals, no
  counters of zero, no prose blocks.
- Nothing is deleted. A retired component moves to a `_parked/` folder or
  behind RAW.
- Keep the stored kind `workbench` and the routes. Rename only what the user
  sees.
- Do not lose these: item results, output artifacts, run receipts, skills,
  schedule delegations, event and idle rows, and
  `~/.holdspeak/workbenches/<id>/memory.jsonl` (`MODEL.md` §6).

Dependencies: A4's engine line uses the Engines picker (`../engines/RECIPE.md`
E5) when it exists; until then it uses the minimal picker in A4. A10 needs
Engines E1.

---

## A0. Tell the truth (backend repairs, no new face)

- **Goal:** what the existing face reports is true.
- **Files:** `holdspeak/services/workbench_runner.py`,
  `holdspeak/kernel/workbench_projection.py`,
  `holdspeak/services/workbench_service.py`,
  `web/src/desk/components/WorkbenchAutomations.tsx` (the mode switch),
  `web/src/desk/components/WorkbenchWindow.tsx` (item Re-run), tests.
- **Changes:**
  - The run row records the model, engine, egress and tokens that actually
    ran. Status is `completed` only with zero failures; with some failures
    it is `completed_with_failures`, shown amber. Find why the first run in
    the recon was stored as `cancelled` with `0/0`, and why item 4 was
    skipped although the counter reached 4/4 (`RECON.md` step 14). Fix the
    cause.
  - A failed item stores the reason in words (`workbench_runner.py:347`
    writes only `Error: failed`). Carry the adapter's error and refusal
    detail into it.
  - Changing the start mode in the face never writes `schedule_enabled`.
    Only the switch writes it (`RECON.md` step 19).
  - Item **Re-run** queues the item *and* starts a run.
- **Done when:** a run of three items, one of which fails on purpose (a stub
  engine that refuses it), records `2/3 done · 1 failed`, the model name and
  the tokens. The failed item reads the stub's reason. Peeking at Event and
  then going back leaves the schedule on. Re-run gives a new result without
  a second press.
- **Tests:** T1 (`tests/integration/test_desk_workbenches.py`, and the
  runner unit tests); T2 for the mode switch.
- **Not in this slice:** any rename or layout change.

## A1. The name, and finding it

- **Goal:** the user sees "Automations" and can reach it in one press.
- **Files:** `web/src/desk/applications.ts`, the Go menu and the phone
  launcher sources, `web/src/pages/cores/WorkbenchesHomeCore.tsx` (title and
  empty line), `NewWorkbenchChooser.tsx` (title), the palette entries,
  `web/src/desk/voice/grammars/workbench.ts` (say "automation"), user docs.
- **Changes:** every visible "Workbench" or "Workbenches" becomes
  "Automation" or "Automations". Add the app to Go and to the launcher's
  Apps. Make the empty line "An automation does one job for you, again and
  again." In the palette, the program comes before the objects for the
  query "automation". Template names lose "Agent".
- **Done when:** no visible "workbench" text remains on the desk (a canon
  guard on built UI strings). Automations opens from Go (1440) and from
  Apps (393) in one press.
- **Tests:** the T3 sweep; T2 for the home empty state.
- **Not in this slice:** the new window.

## A2. One automation = one instruction + sources; each run = one result

- **Goal:** a schedule or Run now does useful work without typed tasks.
- **Files:** `holdspeak/db/schema.py` (additive: `instruction`,
  `sources_json` and `output_target` on `workbenches`; the one schema adds
  columns itself), `holdspeak/db/workbenches.py`,
  `services/workbench_service.py`, `services/workbench_runner.py`,
  `workbench_conductor.py` (the scheduled tick), `services/reaction_service.py`
  (event starts), `routes/primitives/workbenches.py`, the
  `workbench_*` MCP tools, `docs/workbenches.json`.
- **Changes:**
  - A run with an `instruction` mints one occurrence item. Its title is
    "<name>, <date>" or the event's title, its body is the instruction, and
    its grounding is `sources_json` (plus the event's subject). The run then
    runs that item. The old queue behaviour stays for automations without
    an instruction.
  - Hydrate all sources into one prompt.
  - The time limit applies to each item and comes from the engine. Keep 60 s
    for HTTP engines, and use the preset's timeout for CLI engines.
  - Migration on read: an old automation with a recipe gets its Do text from
    the recipe's `user_template`, or else its `system_prompt`. Nothing is
    rewritten in the DB until he edits it.
  - Results: an occurrence's artifact is created with status `new`, not
    `pending-review` (decision 1). Opening it sets `read`. Check the artifact
    status vocabulary first and add the value additively.
  - `output_target`: `inbox` (default) writes the result as an Inbox note
    with a link back to the automation. `needs_you` adds a Needs-you row. A
    destination calls `channel_prepare` (he presses Send).
- **Done when:** an automation with an instruction, two note sources and the
  Every-minute test schedule produces one Inbox note per tick, which reads
  both notes. An event (a recorded GitHub review-request fixture) produces
  one result about that PR. An old template automation still runs its
  queue.
- **Tests:** T1 hub tests that drive the conductor tick with a controlled
  clock and a recorded engine reply.
- **Not in this slice:** the face.

## A3. The automation window

- **Goal:** the sentence on top, and the results below it.
- **Files:** new `web/src/desk/components/automation/AutomationWindow.tsx`,
  `SentenceLine.tsx`, `ResultCard.tsx`, `automation.css`; the window
  registration in `applications.ts`; new
  `web/src/desk/__tests__/automation.app.test.tsx`. Park
  `WorkbenchWindow.tsx`, `WorkbenchAutomations.tsx`,
  `WorkbenchResourceful.tsx`, `WorkbenchRunsWing.tsx` and
  `workbench-config.css` (still reachable behind RAW for old queue
  automations).
- **Changes:**
  - Build the layout in DESIGN §4: five sentence lines (When, Do, About,
    With, Put it in) as read-only values for now, each one pressable; Run
    now; the On/Off switch; Results with the newest open and rendered; one
    line for each older result; NEW; failure words; Run again; the "What it
    has learned" fold (with Forget for each lesson).
  - Do edits in place (a text box with the mic). The other lines open their
    editors in A4 to A6; until then they show their value.
  - Show the running state inside the newest card, with no layout jump.
  - The window opens at no less than 880×640 at 1440.
  - Render markdown and hide internal ids.
  - Use the library material only; one chip style.
- **Done when:** at 1440 and 393 a starter automation shows its sentence and
  its newest rendered result above the fold. Run now shows "Working…" in
  place, then the result. A failure shows its reason and Run again. The
  sweep finds no clipping and no overlap.
- **Tests:** T2 `automation.app.test.tsx` on recorded hub answers; the T3
  sweep picks the window up from `applications.ts`.
- **Not in this slice:** the When, About and Put-it-in editors.

## A4. When, and With

- **Goal:** schedule it in plain words, and pick its engine in place.
- **Files:** `automation/WhenEditor.tsx`, `automation/WithEditor.tsx`, the
  vitest; `services/workbench_service.py` (store a schedule from a
  structured choice and return `next_run_at`).
- **Changes:**
  - When: three choices. *Schedule* (every day / weekday / week on [day] /
    hour, at [time]) is stored as cron and never shown as cron. *When
    something happens* lists only the events the hub can deliver today; the
    slice first lists what exists in `reaction_service.py` presets and the
    event bus. "A meeting ends" is added only if a real event exists.
    *Only when I press Run now.* Show "Next: <day time>".
  - With: the Engines picker (or, before Engines E5, a list of engines
    plus Found engines, with one-press Add). It writes the subject
    assignment `subject:workbench:<id>:capability:workbench.item`. Show the
    egress chip. Under the engine there is an optional **Spend limit per run**
    for this automation, which overrides the engine's limit. Each result shows
    its reported cost. Re-freeze the schedule delegation when With changes, so a
    scheduled run uses the new engine (`MODEL.md`: scheduled runs ignore
    later engine changes today).
- **Done when:** "Every Friday at 3 PM" takes at most 3 presses and shows
  "Next: Fri 15:00". On a desk with no engine but a found LAN engine,
  With → Add makes Run now work, with no other window opened.
- **Tests:** T2; T1 for `next_run_at` and the delegation re-freeze.
- **Not in this slice:** About.

## A5. About

- **Goal:** point the automation at real things by name.
- **Files:** `automation/AboutEditor.tsx`, the vitest; the desk search
  endpoint it calls (reuse the palette's search; do not build a second
  one); the window's drop handler (`WorkbenchWindow.tsx:574` today accepts
  only `application/x-desk-item`).
- **Changes:** the picker finds meetings, notes, drawers, projects and
  people by name, including relative sets ("This week's meetings", "Notes
  in <drawer>"). Each pick is a named chip, and typed text is never deleted.
  A desk object dropped on the window becomes a chip. For event starts, the
  line reads "the <thing> that happened" and is not editable.
- **Done when:** adding "Platform sync notes" by typing "plat" takes 2
  presses, and the result cites it. Dropping a floor note adds its chip.
  1440 and 393.
- **Tests:** T2; a T4 real-browser test only for the drop.
- **Not in this slice:** folders (A10).

## A6. Put it in, and where results show up

- **Goal:** results arrive where he looks.
- **Files:** `automation/PutEditor.tsx`; the Today face and the Needs-you
  service (a "new result" row source); the vitests.
- **Changes:** the choices are My Inbox, Needs you, a file, or a saved
  destination (it prepares the send; he presses Send). Today shows "<name>
  has a new result" while a result is NEW. The dock badge on Automations
  shows the NEW count (absent at zero).
- **Done when:** a scheduled run creates the Inbox note, Today shows the
  row, and opening it clears NEW everywhere.
- **Tests:** T1 for the row source; T2 for Today.
- **Not in this slice:** none.

## A7. Home, New automation, and starters

- **Goal:** a first-time user goes from nothing to a result in at most 6
  presses.
- **Files:** `web/src/pages/cores/WorkbenchesHomeCore.tsx`,
  `NewWorkbenchChooser.tsx` / `WorkbenchTemplatePicker.tsx`,
  `holdspeak/workbench_templates.py`, the vitest.
- **Changes:** home rows show name, When, With and NEW. Starters are the
  four in DESIGN §4, each defined as instruction + sources + When + Put it
  in, with highlighted blanks. A template press no longer copies a new
  recipe each time. Retire TODO, Triage and Morning Brief as starters (they
  stay in code, hidden).
- **Done when:** New → Friday team update → With → Claude Code (or LAN) →
  Run now → a result is readable, in at most 6 presses. The DESIGN §6
  walk passes, with timing recorded.
- **Tests:** T2; one graph-walk case for the §6 job at 1440 and 393.
- **Not in this slice:** none.

## A8. Park what the sentence replaces

- **Goal:** one way to automate.
- **Files:** the New menu source (remove "New Workflow"; decision 2), the
  Agents list entry points, `WorkbenchResourceful.tsx` behind RAW.
- **Changes:** move the entries, do not delete them. MCP tools stay.
- **Done when:** the New menu has one Automation verb, and the RAW view
  still reaches the parked faces.
- **Tests:** T3 sweep.

## A9. Old automations

- **Goal:** his existing workbenches open in the new window.
- **Files:** `AutomationWindow.tsx`; `workbench_service.py`.
- **Changes:** a queue automation (no instruction, pending items) shows its
  items as a list under Results, with "Make this one automation", which
  copies the agent's prompt into Do. Nothing is lost.
- **Done when:** a recorded old TODO workbench opens, shows its items and
  results, and converts in 1 press.
- **Tests:** T2 on a recorded fixture.

## A10. An agent works in a folder (after Engines E1)

- **Goal:** "When GitHub asks me to review, summarize the PR and the risky
  files" works with Claude Code or Codex.
- **Files:** `intel/cli_engine.py` (run in a chosen folder, read-only);
  `AboutEditor.tsx` (a "Folder" source, offered only when With is an
  agent); `workbench_runner.py`.
- **Changes:** the CLI runs in the chosen folder with its read-only or
  tools-off preset (`--sandbox read-only` for Codex; Claude with read tools
  only). The egress chip says the vendor.
- **Done when:** with a fake CLI that lists its cwd, the result names the
  folder's files. In the rig, a recorded review-request event produces the
  summary.
- **Tests:** T1 with a fake CLI on PATH in the scratch HOME.
