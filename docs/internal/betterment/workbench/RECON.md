# Workbench: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. I walked the
job as a first-time user on a fresh desk, at 1440x900 and 393x852. I did not
fix anything. All shots are in `shots/` (88 files). The rig is in the
footnote.[^rig]

The job I walked: find Workbench, learn what it is, make one, give it work,
configure it, run it, watch it, read the result, run it again, schedule it,
and find it again later.

## How I found it

On the desk at 1440 there is no Workbench icon on the floor, no Workbench in
the dock, and no Workbench in the **Go** menu (`01-find-desk-1440.png`,
`01-find-menu-go-1440.png`). I opened all four menus. The only entry is
**Desk ▸ New Workbench**, the seventh of nine "New …" verbs
(`01-find-menu-desk-1440.png`). There is no way to open the list of
workbenches from a menu.

What worked: **Search ⌘K**, type "workbench". The palette shows
`Workbenches · PROGRAM` and `New Workbench · VERB`
(`01-find-palette-1440.png`). Enter opens the Workbenches window. With an
empty palette, Workbenches is the first program listed
(`23-palette-empty-1440.png`), but a newcomer does not open an empty palette
to browse.

At 393 the launcher lists Apps, Drawers and New. Workbench is not in any of
them (`01-find-launcher-full-393.png`). Search is the only way in. After one
workbench exists, Enter on "workbench" opens that workbench object, not the
program, because the object is the first hit (`01-find-palette-393.png`).

After I closed every window, nothing on the desk led back to my workbench
(`21-desk-after-close-1440.png`). Search "TODO" found two different things,
both named "TODO Agent": one `AGENT`, one `WORKBENCH`
(`23-find-again-palette-1440.png`).

## Friction log

"Presses" counts presses and typed fields. "Wait" is the measured system
time. "Est. time" is my estimate for a first-time user who reads the screen.

| # | Step | What I pressed | What I saw (exact text) | What a newcomer expects | Where I got stuck | Presses | Wait / est. time | Shots |
|---|---|---|---|---|---|---|---|---|
| 0 | Open the desk | Load the page, press `Continue later` | `Get ready`, `Speech`, `Set up speech · 144 MB`, `Chat engines`, `Optional setup` | The desk | Not Workbench's fault; noted as the first thing a fresh user meets | 1 | 4 s / 10 s | `00-desk-first-open-1440.png`, `00-desk-first-open-393.png` |
| 1 | Find Workbench | Looked at floor and dock; opened `Go`, `Desk`, `Object`, `Window`; then `Search`, typed "workbench", Enter | Only `Desk ▸ New Workbench`; palette `Workbenches · PROGRAM` | An icon on the floor or dock, or an entry in `Go` | Four menus with no list entry | 7 | 2.5 s to open / 45–60 s | `01-find-*` |
| 2 | Learn what it is | Read the empty window | `Workbenches`, `+ Create`, a `⊞` glyph, `No workbenches yet` | One line that says what a workbench does for me | Nothing on the face says what it is or why I want one | 0 | – / stuck | `02-home-empty-1440.png`, `02-home-empty-393.png` |
| 3 | Make one | `+ Create` | A second window, `New Workbench`, `START FROM A TEMPLATE`: `TODO Agent`, `Triage Agent`, `Meeting Prep Agent`, `Morning Brief`, `Blank`. Card meta like `⏱ 0 2 * * * · 3 items · 3 skills` | Plain choices, plain schedule words | Raw cron text on every scheduled card; "Agent" and "workbench" used as if the same | 1 | 1.5 s / 20 s | `03-create-chooser-1440.png`, `03-create-chooser-393.png` |
| 4 | Pick a template | `TODO Agent` | The chooser closes; a new window `TODO Agent` with `ITEMS RUNS MEMORY ▸ Run`, `TODO Agent · ⏸ 2 AM nightly`, `3 skills`, `Configure`, `ADD ITEM`, three starter items each `○ NEEDS REVIEW`, footer `■ NO ENGINE` `Choose an engine` | A name step; items that say "waiting" | No name asked. Items say `NEEDS REVIEW` before anything ran. The home card says `Choose default` and `Manual` while the window says `2 AM nightly`. The window opens 640x520 and cuts the list | 1 | 2.5 s / 30 s | `04-after-template-1440.png`, `04-after-template-393.png` |
| 5 | Try to run | `▸ Run` | Nothing. The button is disabled (title `No engine`) but is drawn like a live chip | A greyed button, or the engine choice right there | No visible difference between live and dead Run | 1 | – / 10 s | `04-after-template-1440.png` |
| 6 | Give it work (open an item) | Press `Review open PRs` | The row unfolds: `INSTRUCTION`, `Add details...`, `Dismiss`, `Park` | A place to say which PRs, which repo, which meeting | No way to attach a source in the item | 1 | – / 20 s | `06-item-open-1440.png`, `06-item-editor-zoomed-1440.png`, `06-item-editor-393.png` |
| 7 | Point an item at my notes with "@" | Typed `List the open risks from @Plat`, then `@` alone, chose `Inbox`, finished the sentence, `Add` | `No zones match`; bare `@` lists `Decisions · Empty`, `Inbox · 1 item`, `Meetings · Empty`, … The popup lies on top of the item list. After the pick the item reads `List the open risks from and draft a short note for my team` with a chip `▣ refs` | "@" finds my notes and meetings by name | "@" only finds drawers. The pick deletes the word, so the sentence is broken. The chip does not say which drawer | 6 | – / 90 s | `12-add-item-at-ref-1440.png`, `12-add-item-at-bare-1440.png`, `12-add-item-ref-chosen-1440.png`, `12-item-with-ref-open-1440.png` |
| 8 | Drag a note onto the workbench | Dragged `1:1 with Theo, Oct 15` from the floor onto the window | Overlay `NO DROP · NOT A WORKBENCH ITEM` | The note is added as a source | The face refuses a note from the floor | 1 drag | – / 20 s | `13-drag-over-workbench-1440.png`, `13-after-drop-1440.png` |
| 9 | Configure | `Configure` | The item list is replaced (the `ITEMS` tab stays lit). `▴ Collapse`, `AGENT` (`TODO Agent`, `Backlog worker`, `Choose agent`), `ENGINES` (`Item assignment` / `Reference assignment`, `No default model`, `Choose default`), `STARTS WHEN` (`Mode` `MANUAL`), `Skills` `3 INHERITEDS`, `Workspace` | Agent, engine, schedule, in plain words | Two engine slots with no explanation. Skills show raw markdown cut mid-word: `# Action Item Extraction ## Method Scan the input for comm`. Workspace shows a file path | 4 | – / 60 s | `07-configure-1440.png`, `07-configure-choose-agent-1440.png`, `07-configure-skills-workspace-1440.png`, `07-configure-393.png` |
| 10 | Get an engine | Footer `Choose an engine` → `Find on LAN` → `Use it` | A third window, `Settings ▸ ENGINES`. `FOUND · 1`, `LAN`, `qwen3.8-27b`, `192.168.1.43:8080`, `Use it`. Then `1 engine`, but every job still says `no engine`. The workbench still says `NO ENGINE` | "Use it" makes Run work | "Use it" adds the engine to the machine but gives it no job | 3 | LAN scan 3 s / 45 s | `08-choose-engine-1440.png`, `08-find-on-lan-1440.png`, `08-engine-used-1440.png` |
| 11 | Assign the engine | Close Settings → `Choose default` (Item assignment) → press the `Qwen3.8 27B` row | Settings again, now `Custom tasks · runs on`, a bare `OR`, then `1 LIMITED`, `WITHOUT AGENTS`, `PATCHED 18:09 · CUSTOM TASKS → QWEN3.8 27B`, `Undo`. The workbench now says `Uses group · 192.168.1.43:8080` | The same word in both windows | The workbench calls it "Item assignment"; Settings calls it "Custom tasks" | 3 | 2.5 s / 45 s | `09-choose-default-1440.png`, `09-engine-assigned-1440.png` |
| 12 | Run | `▸ Run` | Title chip `Running 1/4`; a blank band with a faint spinner (`◌ Loading`) pushes the whole window down; the row shows `WORKING` with a bar and `● RUNNING`. Footer `last run just now` while it runs | One clear "working on item 1 of 4" line | The page jumps; the spinner is nearly invisible | 1 | about 15–20 s per item; 56 s for three items / – | `14-running-t001s-1440.png` … `14-running-t031s-1440.png`, `14-running-393.png` |
| 13 | Read the result | Press the done row; then `Open artifact` | Row preview in raw markdown: `## Receipt: Review open PRs (wbi_434ac23c9d20) **What I found in the grounding material:** …`. Open row: `RESULT`, `⚠ Review needed`, `⌂ LAN`, the rendered text, `Copy`, `Open artifact`, `Re-run`, `Park`. The artifact window: `⚠ Awaiting review`, `WORKBENCH OUTPUT`, `Copy`, `Dictate about this` | Clean text, and a way to accept or send it | The item says `DONE` and `Review needed` at once. "Awaiting review" has no verb that reviews. Internal ids (`wbi_…`, `note_29f08aec6109`) show in the text | 2 | – / 60 s | `15-done-1440.png`, `18-result-open-1440.png`, `18-result-verbs-1440.png`, `19-open-artifact-1440.png` |
| 14 | Check the run record | `RUNS` tab; press the run row | `RUNS 1`, `0/0 done · NO MODEL`, `FAILED`; detail `egress NO MODEL`, `model —`, `tokens 0`. The home list calls the same run `○ Cancelled` | A record that matches what I just saw | The run made three good receipts on the LAN model, but its record says 0/0, no model, failed. The fourth item stayed `NEEDS REVIEW` although the counter reached `4/4` | 2 | – / 30 s | `16-runs-tab-1440.png`, `16-run-row-pressed-1440.png`, `02-home-populated-1440.png` |
| 15 | Run again | `▸ Run` | `Running 1/1`, then the fourth item `DONE`. Runs: `1/1 done · NO MODEL`, `COMPLETED` | – | Still says `NO MODEL` | 1 | 22 s / – | `20-rerun-t2s-1440.png`, `20-rerun-end-1440.png`, `20-rerun-runs-tab-1440.png` |
| 16 | A run with a failure (393) | Made `Meeting Prep Agent`, `▸ Run` | Item 1 `DONE` with an empty pack: `No prior meeting context available`, `Unknown`, `None identified`, `⚠️ Grounding gap`. Item 2 `✗ FAILED`, `Error: failed`. Runs: `1/2 done · 1 failed · NO MODEL`, `COMPLETED` (green on the home list) | The reason it failed and one retry verb | No reason, here or in the hub record. A run with a failure is green | 2 | 12 s / – | `15-done-393.png`, `15-done-item2-393.png`, `16-runs-tab-393.png`, `24-failed-item-open-393.png` |
| 17 | Retry the failed item (393) | `Re-run` on the item | The item goes back to `○ NEEDS REVIEW`. Nothing runs (I waited 2 minutes) until the top `▸ Run` | "Re-run" runs it | The verb only puts it back in the queue | 1 | 122 s, no run / – | `24-rerun-item-393.png`, `24-rerun-item-end-393.png` |
| 18 | Schedule | `Configure` → `Mode` → `Schedule` → `Schedule` preset → tick `Enabled` | `SCHEDULE`, `2 AM NIGHTLY` (choices `7 AM daily`, `7 AM weekdays`, `2 AM nightly`, `Every hour`), a small checkbox far right of `Enabled`; footer `3 ITEMS■ SAVED` | One control: "Run every night at 2 AM, on/off" | Three controls for one fact. The template's schedule was there but off all along. The only on/off cue in the header is `⏱` versus `⏸` | 4 | – / 40 s | `10-schedule-1440.png`, `10-schedule-enabled-1440.png`, `10-schedule-393.png` |
| 19 | Look at the other start modes | `Mode` → `Event`, then `Idle`, then back to `Schedule` | Event and Idle panels (words below). Back on Schedule, `Enabled` is unticked. The hub confirms `schedule_enabled: false` | Looking does not change anything | Peeking at another mode silently switched the schedule off | 3 | – / 60 s | `10-mode-event-1440.png`, `10-mode-idle-1440.png` |
| 20 | Find it again later | Closed all windows; checked `Needs you`, `Today`, Search | Floor: only the one result I had opened (`TODO Agent: Summar… notes`). `Needs you`: `No engine for summaries` only. `Today`: no mention. Search finds it | Results waiting for review show up where I look each morning | Four results said "Review needed"; no other face knows | 4 | – / 60 s | `21-desk-after-close-1440.png`, `22-needs-you-1440.png`, `25-today-1440.png`, `23-find-again-palette-1440.png` |
| 21 | Rename | Pressed the title, typed, Enter | Title and hub name changed to `Team weekly` | – | Works; but the name was never asked at creation | 2 | – / 10 s | `26-renamed-1440.png` |

Total for the whole job, a first-time user who already has a LAN engine: about
45 presses, three windows besides the workbench, and 12–15 minutes. Two steps
(attach my notes, retry a failure) did not succeed the way I expected.

## Words and concepts a newcomer would not understand

Copied exactly as shown.

- **Workbench** itself: never defined on any face. "Workbench" and "Agent"
  are both used for the same thing (`TODO Agent` the template, the agent, and
  the workbench; Search lists `TODO Agent · AGENT` and `TODO Agent · WORKBENCH`).
- `NEEDS REVIEW` on items that have not run (it means "waiting").
- `⚠ Review needed` / `⚠ Awaiting review` on a `DONE` item, with no review
  verb.
- `P2`, `P3` (priority; the cycle button's title says `Priority 3. Click to
  cycle`, the face never says it).
- `0 2 * * *`, `0 7 * * 1-5` (raw cron on template cards).
- `3 skills`, `Skills`, `3 INHERITEDS` (and the plural is wrong).
- `Item assignment`, `Reference assignment`, `No default model`, `Choose
  default`, `Uses group · 192.168.1.43:8080`.
- Settings words met on the way: `Custom tasks · runs on`, `OR`, `1 LIMITED`,
  `WITHOUT AGENTS`, `PATCHED 18:09 · CUSTOM TASKS → QWEN3.8 27B`.
- Menubar chip after the LAN scan: `→ LAN-SCAN:6A759D29035E32C4D19D02A54A…`,
  later `→ YOUR NETWORK`.
- `Workspace` and `~/.holdspeak/workbenches/workbench_5f8d4a06a199/`.
- `Backlog worker`, and the agent list `Chase`, `Desk`, `Draft`,
  `Interview`, `Plan`, `Project` with no description.
- `@` lookup says `No zones match`; "zone" is not a word the desk uses on its
  drawers.
- `▣ refs` chip.
- `Park` versus `Dismiss` versus `Clear done`.
- `RUNS`, `MEMORY`, `MEMORIES 3`, `OBS`, `Clear` (memory rows).
- `WORKING`, `RUNNING`, `Running 1/4`, `◌ Loading`.
- `0/0 done · NO MODEL`, `FAILED` vs `Cancelled` vs `COMPLETED` vs
  `Completed`.
- `egress`, `NO MODEL`, `tokens 0`, `⌂ LAN`.
- `WORKBENCH OUTPUT`, `Open artifact`, `Dictate about this`.
- `## Receipt:`, `**What I found in the grounding material:**`, `wbi_…`,
  `note_…` (raw markdown and internal ids in previews and results).
- Event mode: `EVENT TRIGGER · READ-ONLY · 35 MIN REFRESH`,
  `OWNER/REPOSITORY`, `+ GitHub · Review requested`, `+ Jira · Assigned to me
  · SETTINGS REQUIRED`, `REPOSITORY REQUIRED`, `No event triggers yet`.
- Idle mode: `LOCAL DATA`, `ONE ITEM / RUN`, `30 MIN IDLE`, `6H COOLDOWN`,
  `TARGET 2 / NIGHT`, `22:00–07:00`, `IDLE POLICY`, `Idle after 1–1440 min`,
  `Cooldown 1–168 hr`, `Nightly target 1–8 items`, `Overnight only`, `Night
  starts`, `Night ends`, `local time`, `:00`, `✓ DEVELOP LOOSE IDEAS`, `LOOSE
  IDEAS DIRECTORY · OLDEST REVISED NOTE`, `✓ PREPARE RECOVERY PLANS`,
  `INCOMPLETE WORK · DRAFT PLAN`, `SELECTED MAINTENANCE ONLY`, `PENDING WORK
  UNTOUCHED`, `SOURCE DATA · REVIEW-ONLY`, `RUNS AS OWNER`, `Enable overnight
  resourcefulness`, `PAUSED`, `NO RESOURCEFUL WORK STARTS`.
- `Edit in Agent`.

## Verbs that did nothing, failed, or did something else

One line each; the fix direction is in the last clause.

1. `▸ Run` with no engine is disabled but drawn as live
   (`04-after-template-1440.png`). Show the engine choice in its place.
2. `Use it` (Settings, found engine) adds the engine but the workbench still
   cannot run (`08-engine-used-1440.png`). One press should make Run work.
3. `@` in the instruction finds drawers only, and the pick deletes the typed
   word (`12-item-added-1440.png`). Let "@" find notes and meetings and keep
   the sentence.
4. Dragging a note from the floor onto the workbench: `NO DROP · NOT A
   WORKBENCH ITEM` (`13-drag-over-workbench-1440.png`). The handler only takes
   one drag type.[^drop] Accept the desk's own notes and meetings.
5. First run: the counter reached `Running 4/4`, three items were done, the
   fourth stayed pending, and the record says `0/0 done · NO MODEL · FAILED`
   (`16-runs-tab-1440.png`) or `Cancelled` (`02-home-populated-1440.png`).
   The record must match what happened.
6. Every run record says `NO MODEL`, `tokens 0`, `egress NO MODEL`, though
   the LAN model wrote every receipt (`16-run-row-pressed-1440.png`).
7. A failed item says only `Error: failed`; the hub keeps no reason
   (`24-failed-item-open-393.png`).[^err] Say why.
8. Item `Re-run` puts the item back in the queue; it does not run it
   (`24-rerun-item-end-393.png`). Run it, or call it what it does.
9. `Open artifact` opens `Awaiting review` with no way to review or accept
   (`19-open-artifact-1440.png`). Give the review state a verb or drop it.
10. Switching `Mode` away from Schedule and back silently turned `Enabled`
    off; the hub stored `schedule_enabled: false` (`10-mode-idle-1440.png`).
    Do not change saved state on a look.
11. `Choose an engine` and `Choose default` each open the Settings window on
    top of the workbench instead of choosing in place (`08-choose-engine-1440.png`,
    `09-choose-default-1440.png`).
12. Template starter items (`Monday standup`, `1:1 with manager`, `Review open
    PRs`) have no source, so the Meeting Prep result is an empty pack that
    says `Unknown` (`15-done-393.png`). Ask for the source when the template
    is picked.
13. One `503 (Service Unavailable)` reached the browser console when I pressed
    `Open artifact`. I did not find which request. Listed under Unknown.

Not pressed, so not judged: `Dismiss`, `Park`, `Clear done`, memory `Clear`,
`Edit in Agent`, `Change`, `Copy`, `Dictate about this`, the Event and Idle
controls.

## Visual problems

- **It opens small and stacks windows.** The workbench opens at 640x520 and
  cuts its own list (`04-after-template-1440.png`). Create opens a second
  window over the first (`03-create-chooser-1440.png`); the engine choice opens
  a third (`08-choose-engine-1440.png`). I zoomed to work at all.
- **No hierarchy.** The add-item form is the biggest thing on the face, above
  the work. At 393 the first result text is about 1300 px down, under the form
  (`18-result-open-393.png`). There is no display-size fact; every row looks
  the same weight.
- **The name is said three times**: menubar `TODO Agent`, title bar `TODO
  Agent`, header `TODO Agent ·` (`04-after-template-1440.png`).
- **Raw text.** Markdown marks (`##`, `**`) and ids in item previews
  (`15-done-1440.png`); raw markdown cut mid-word in Skills
  (`07-configure-skills-workspace-1440.png`); a file path in Workspace.
- **Status chips fight.** `DONE` (green) next to `⚠ Review needed` (amber);
  `COMPLETED` on a run with a failure; `FAILED` and `Cancelled` for one run.
- **Running moves the page.** A blank band with a faint spinner appears above
  the header and pushes everything down while the run goes
  (`14-running-t003s-1440.png`, `14-running-393.png`).
- **Clipping and overlap.** `▴ Collapse` text overflows its button at both
  widths (`07-configure-1440.png`, `07-configure-393.png`). `3 ITEMS■ SAVED`
  has no gap (`10-schedule-enabled-1440.png`). The `@` popup lies on top of
  the item list (`12-add-item-at-ref-1440.png`). Receipt previews are cut
  through the middle of a line at 393 (`02-home-populated-393.png`).
  `Re-run` and `Park` sit at different heights (`15-done-item2-393.png`).
- **A brown left stripe** marks the two unassigned engine rows
  (`07-configure-1440.png`); it looks like the accent rail the canon forbids.
- **Configure takes over the body** but the `ITEMS` tab stays lit, so the
  user does not know where they are (`07-configure-1440.png`).
- **Mixed materials.** White mono template cards, cream ledgers with black
  borders (`RECENT RUNS`, `MEMORIES`), grey inset forms, a big blue primary
  button in Settings, and three different chip styles on one row. The
  workbench face does not look like one object.
- **Mode panels change size a lot.** Idle opens a long form of number
  steppers (`10-mode-idle-1440.png`); Event opens a repository field and two
  "+" buttons with an empty state (`10-mode-event-1440.png`).
- **Every workbench has the same robot icon**, while the template cards had
  their own glyphs (`⚡ ◈ ▣ ☀`).
- **393 header crowding.** `‹ Back`, three wing tabs, a striped gap and
  `▸ Run` fill the title strip; the `Running 1/2` chip replaces Run in the
  same place (`14-running-393.png`).
- Two unlabeled squares (`⊞`, `↻`; "Overview" and "Reset layout" by their
  accessible names) appear in the dock once a window opens. This is the
  desk's, not Workbench's, but a newcomer sees it here first.

## What worked

- Search finds it, and one template press makes a workbench with items.
- With an engine, the receipts were good. The TODO Agent read my seeded
  Platform sync notes, cited them by name, and said what it could not do
  (`18-result-open-1440.png`). The fourth item's receipt noticed that my
  sentence was cut and said so.
- The `MEMORY` wing kept three sensible lessons from the run
  (`17-memory-tab-1440.png`).
- `Find on LAN` found the engine in 3 seconds.
- Rename from the title works.

## Unknown (not verified)

- How the agent got my notes. I never attached them (the only ref was the
  Inbox drawer), but the receipts cite `Platform sync notes, Oct 16` with its
  id. The face gives no sign of this. I did not trace it.
- Why the first run was recorded as cancelled with 0 attempts, and why the
  fourth item was skipped in it.
- Why `1:1 with manager` failed. The hub stores only `Error: failed`.
- Whether the 2 AM schedule fires. I did not wait for it. No face shows the
  next run time.
- The source of the one `503` in the console.
- Drag was driven by a synthetic pointer. The face itself drew the `NO DROP`
  overlay, so I believe a real mouse sees the same, but I did not try a real
  mouse.

## Verdict

Workbench has a real engine under a face that hides it. When it ran, it
wrote useful, cited receipts from my notes. But a first-time user cannot
find it on the desk, is never told what a workbench is, cannot point an item
at the meeting or note it is about, has to cross three windows and two
names ("Item assignment", "Custom tasks") to get one engine working, and then
reads a run record that says the work failed with no model while the items
say done and also "review needed" with no way to review. Schedules switch
themselves off when you look at another mode, retry does not retry, and
failures have no reason. The face is a stack of grey forms, raw cron, raw
markdown, internal ids and uppercase jargon (`3 INHERITEDS`, `WITHOUT
AGENTS`, `RUNS AS OWNER`). For a senior architect with three reports, it
reads like an internal admin panel for a pipeline, not a tool that does his
Monday work. The owner's reaction is fair.

[^rig]: Isolated hub `scripts/graph_walk.py serve` on ports 8791 and 8792
    with `_isolated_hub_env` (scratch `HOME` from `mktemp -d`, all isolation
    switches), run from the code of the owner's desk worktree
    (`wt-daily-delight-delivery-20261017`, `217001b2e`, merge of #1247) so the
    face is the one he sees. Real LAN engine `qwen3.8-27b` at
    `192.168.1.43:8080`; real replies, nothing faked. Seed: two notes through
    `POST /api/notes` (a platform sync and a 1:1), plus the shipped templates
    `TODO Agent` and `Meeting Prep Agent` and a `Blank`. The second hub
    (8792) had no engine and no workbenches, for the empty and no-engine
    states. Both hubs stopped and both scratch HOMEs removed afterwards.
    Chromium headless via Playwright, 1440x900 and 393x852 (mobile, touch,
    scale 2).
[^drop]: `web/src/desk/components/WorkbenchWindow.tsx:574` (`workbenchDropVerb`
    accepts only `application/x-desk-item`).
[^err]: `holdspeak/services/workbench_runner.py:347` writes
    `result=f"Error: {outcome.error or outcome.outcome}"`; the stored value
    was `Error: failed`.
