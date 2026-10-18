# Projects, updates and decisions: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. I walked the
cluster's jobs as a first-time user on a fresh desk, at 1440x900 and
393x852. I fixed nothing. All shots are in `shots/` (77 files). The rig is
in the footnote.[^rig]

The seed: three meetings with real transcripts (a payments platform sync, an
architecture review of the event bus, a 1:1 with Mira), summarized by the
real LAN engine (14 s each); two notes ("Payments migration: open risks",
"Notes for Friday update"); three people (Mira Okafor, Theo Lindqvist, Jun
Park). I made the project through the face.

The jobs I walked: make a project and connect its sources; see where it
stands; write the Friday update; let the steward help; keep a decision; find
it all again.

## The headline: Draft update, walked for real

Recon R1 (2026-10-13) said: one press, 91 s, nothing. **It still happens.**

| Try | Sources linked | What I pressed | Wait | What I saw | What the hub did | Shots |
|---|---|---|---|---|---|---|
| 1 | none (new project) | Room ▸ `Draft update` | 37 s | Spinner on the button, then an editor: `## Progress - **[UNVERIFIED]** Nothing to report.` … `## Source Coverage - **[UNVERIFIED]** All sources consulted successfully.` | Saved a model draft | `05-draft-t001s-1440.png` … `05-draft-t040s-1440.png` |
| 2 | 3 meetings, 2 notes, 1 confirmed decision | Room ▸ `Draft update` | 96 s, then nothing | Spinner, then the Room again, unchanged, for 180 s. No word on the face. The console shows `409 (Conflict)` | Answered 409, saved nothing | `09-draft2-t002s-1440.png` … `09-draft2-t180s-1440.png` |
| 3 | same | the same route, called directly | 82 s | `{"code":"project_update_model_failed","message":"The update engine did not make a draft.","reason":"not_usable"}` | While it ran, `/health` took **74 s** to answer: the whole hub froze | none (API) |
| 4 | same | MCP `project.draft_update`, records only | **0.1 s** | A usable draft: each meeting summary, the decision, seven actions with owners and dates | Saved a draft | `27-update-deterministic-open-1440.png`, `-393.png` |

So the press that matters does two bad things at once. It freezes every
window on the desk for about 80 s, and when the engine's answer is not
usable it shows nothing. Meanwhile the same project data makes a good plain
draft in a tenth of a second, and "Ask this project" answered "What is at
risk for the October release?" correctly in under 20 s
(`24-ask-project-t020s-1440.png`).

The records draft is not ready to send as it stands:

- It pastes the 1:1 with Mira into the team update ("Mira reported a heavy
  cutover load…").
- `Risks & Blockers` says "No risks or blockers in this window", although the
  platform sync flagged the HSM ceremony as a risk and the "open risks" note
  lists four.
- `Source Coverage` always says "All sources consulted successfully": the
  text is a constant.[^coverage]
- The architecture decision (Kafka for ledger events) is missing, because no
  one pressed Confirm on it in that meeting.

## Friction log

"Presses" counts presses and typed fields. "Wait" is measured. "Est." is my
estimate for a newcomer who reads the screen.

| # | Step | What I pressed | What I saw (exact text) | What a newcomer expects | Where I got stuck | Presses | Wait / est. | Shots |
|---|---|---|---|---|---|---|---|---|
| 1 | Find Projects | `Go` | `Speak`, `Meetings`, `Today`, `Ask AI`, `People`, `Conductor`. No Projects | A Projects entry | Desktop Go has no Projects; the phone Go lists each project by name (`25-phone-launcher-393.png`) | 1 | – / 15 s | `01-menu-go-1440.png` |
| 2 | Find New Project | `Desk` | Nine "New …" verbs; `New Project` is ninth | – | – | 2 | – / 10 s | `02-menu-desk-1440.png` |
| 3 | Search "project" | ⌘K, typed | `Project · AGENT`, `New Project`, `Ask this project · Select a Project`, `Draft update · Select a Project`, `Gather · No Room has two windows` | My projects | Three verb rows that cannot work are listed; "Project" is an agent, not a project | 2 | – / 20 s | `02-palette-project-1440.png` |
| 4 | Fill the door | Typed the name | `PROJECT NAME`, `What are you delivering?`, `SOURCES`: GitHub, Jira, Confluence, each `○ NOT SET UP` `Connect`. Footer `NO SOURCES · BLANK PROJECT` in near-invisible grey | Name, people, meetings, sources | Nothing asks about meetings, notes or people, which is where the material already is | 1 | – / 20 s | `03-door-open-1440.png`, `03-door-named-1440.png`, `25-phone-door-393.png` |
| 5 | Connect GitHub | `Connect` | `gh auth login` `Copy` `Recheck` | Sign in here | I must open a terminal | 1 | – / 60 s | `03-door-connect-github-1440.png` |
| 6 | Connect Jira | `Connect` | `Site`, `Email`, `acli jira auth login --site <site> --email <email> --token`, `Copy`, `Add` | Paste my Jira link | A CLI command with three blanks to fill by hand | 1 | – / 90 s | `03-door-connect-jira-1440.png` |
| 7 | Create | `Create Project` | The Room: `Clear here · New`, `Nothing open`, `Ask this project…`, the same three source rows again, `Since you looked` | My meetings about payments | Three meetings say "payments" in their titles; the Room shows none | 1 | 5.7 s / – | `04-room-first-open-1440.png` |
| 8 | Draft update (empty) | `Draft update` | See try 1 above | – | A confident empty update | 1 | 37 s | `05-draft-*` |
| 9 | Add a meeting to the project | Open meeting, `More`, `Add to Project`, `Add to Project ▸`, `Payments migration` | `IN PAYMENTS MIGRATION` | One press, or "Add" on a suggestion in the Room | "Add to Project" in the menu only scrolls to a second "Add to Project ▸" button | 5 per meeting | – / 40 s | `06-meeting-*` |
| 10 | Confirm a decision | `Confirm` on "Keep the old ledger read-only for 30 days" | `DECIDED` | – | Works | 1 | 2 s | `07-decision-confirmed-in-meeting-1440.png` |
| 11 | Read the Room | – | `7 open here` `On track` `CHECKED 2M AGO`; seven rows `WAITING ON THEO/JUN/MIRA/ME`, each with `Hand to coder` and `Open`; five closed folds `SOURCES 1`, `PAGES 3`, `DECISIONS AND OWED 1`, `SINCE YOU LOOKED`, `FILES` | Where it stands: at risk or not, what changed, what was decided, who I wait on | "On track" while the release is blocked. Six of seven rows are my reports' work, each offered to a coding agent. The answers I want are in a fold called `PAGES` | 0 | – / 60 s | `08-room-populated-1440.png`, `13-room-zoomed-pages-1440.png`, `10-phone-desk-393.png` |
| 12 | Open the folds | Each fold | `PAGES`: three pages written by the LAN model in the background: `What did we decide`, `Risks and disputes` (`STALE · 2 NEW SOURCES`), `What changed this week`, each line cited. `FILES`: a 16-row table with `Get Info` | – | This is the status update, already written, hidden in the fourth fold. One page line is wrong ("You will chase the security team"; Jun will) | 5 | – / 90 s | `12-room-fold-*`, `13-room-pages-open-1440.png` |
| 13 | Draft update (with sources) | `Draft update` | See try 2 above | – | 96 s of spinner, then nothing | 1 | 96 s | `09-draft2-*` |
| 14 | Open the update list | ⌘K `draft update for` ↵ | `UPDATES 2`: `DRAFT REV 2 DETERMINISTIC`, `SUPERSEDED REV 1 MODEL` | The palette verb drafts | "Draft update for Payments migration" opens the list, it drafts nothing | 3 | – / 20 s | `26-palette-draft-update-*`, `27-update-list-*` |
| 15 | Read a draft | Press the draft | Raw markdown in a toolbar editor (`## Progress`, `**[UNVERIFIED]**`); footer `UPDATE DRAFT · MODEL · …`, `Save`, `Regenerate`, `Copy`, `Publish`; on the phone the text is mono, 1,300 px long | The update as my manager will read it | Markdown marks and `[UNVERIFIED]` tags; no "for whom" | 1 | – / 60 s | `05-draft-t040s-1440.png`, `27-update-deterministic-open-*` |
| 16 | Publish | `Publish` | `✓ Published`, a SEND well with `HoldSpeak folder`, a preview | – | Works; the preview still holds the 1:1 text | 1 | 3 s | `28-update-published-1440.png` |
| 17 | Let the steward help | `SOURCES` fold ▸ `Watch sources` | A different face: `Close` `Run once` `Policy`, `No runs yet. Run once to start.` | Source settings | The button named "Watch sources" opens the steward | 2 | – / 30 s | `14-room-watch-sources-1440.png` |
| 18 | Steward policy | `Policy` | `Off · Run once only`, `Tell me · Watch · tell me · change nothing`, `Do it · Watch · do the work · never send`, `RAW`, footer `WATCH SOURCES · OFF` | What it will do for me on Friday | Nothing says it drafts the update or nudges reviewers | 1 | – / 30 s | `15-steward-policy-1440.png` |
| 19 | Run the steward | `Run once` | `COMPLETED MANUAL Record`; `Observe 4 sources`, `Compare review opened`, `Propose 1 proposal`, `Act no effect allowed`, `Verify`, `Record`; `REVIEW OPENED` `1 PROPOSAL` `Review` `NO EFFECT ALLOWED` | A draft, or a nudge | A pipeline report. No draft, no nudge | 1 | < 10 s | `16-steward-run-*` |
| 20 | Review its proposal | `Review` | `Review flags`, "Keep the old ledger read-only…", `MEDIUM`, `Decision due for review`, `Accepted decision is due for periodic review`, `pprop_0ccf7c7d06b52c30fcdc0baf15fa22de`, `Accept` `Edit` `Defer` `Dismiss` | – | A decision confirmed 20 minutes before is "due for periodic review". An internal id shows | 1 | – / 30 s | `17-review-open-1440.png` |
| 21 | History | `HISTORY` | `6 today`, `ALL GITHUB JIRA ROOM`, `Resource linked · resource ref`, `Updated · meeting associated`, `Created · name, watches activated` | What happened | Log words, not events he would name | 1 | – / 20 s | `18-room-history-1440.png` |
| 22 | Find the decision | Desk ▸ `Decisions` drawer | `Contents`, `○ No items`, `Filed · Desk root` | My decision | The drawer named Decisions holds no decisions | 1 | – / 15 s | `20-decisions-drawer-1440.png` |
| 23 | Find the decision, again | Dock `Today` ▸ `DECISIONS` | `DECISIONS 1`, "Keep the old ledger read-only…", `Payments platform sync` | – | Found, in the fourth wing of Today | 2 | – / 30 s | `21-today-1440.png`, `22-today-decisions-1440.png` |
| 24 | Record a decision by hand | Desk ▸ `New Decision`, typed, `Create` | A popover with one field `Decision title`; then a decision object on the desk floor, `Filed · Desk root`, `Proposed Accepted Replaced Retired` | Which project, why | It lands loose on the desk, not in the project, not in the Decisions drawer | 3 | – / 30 s | `23-new-decision-1440.png`, `23-new-decision-created-1440.png` |
| 25 | Ask the project | Typed "What is at risk for the October release?", Enter | A cited answer: tokenization blocked on the HSM ceremony; runbook still a draft; bus factor 1 on the ledger schema. Above it, `UNFINISHED 1 · SAVED 20:00 · Resume`; a toast `RUNNING · Meeting analysis` stays on screen | – | The answer is good. The same question is also listed as "unfinished" | 2 | < 20 s | `24-ask-project-*` |
| 26 | Find the project again | Closed the Room; desk icon `Payments migration` | The Room reopens | – | Works (it is a drawer icon with a badge `8`) | 1 | 2 s | `19-find-again-drawer-1440.png` |

Total for "make the project, add my material, get a Friday update I can
send": about 40 presses, a terminal for every outside source, two failed
drafts, and about 25 minutes. The update I could send came from MCP, not
from the face.

## Words a newcomer would not understand

Copied as shown: `Clear here`, `OPEN HERE`, `open here`, `CHECKED 2M AGO`,
`READ 19:32 · NEXT CHECK 19:33`, `Hand to coder`, `PAGES`, `STALE · 2 NEW
SOURCES`, `DECISIONS AND OWED`, `SINCE YOU LOOKED`, `Watch sources` (opens the
steward), `Run once`, `Policy`, `Tell me · Watch · tell me · change nothing`,
`Do it`, `RAW`, `Observe`, `Compare`, `Propose`, `Act`, `Verify`, `Record`,
`REVIEW OPENED`, `NO EFFECT ALLOWED`, `Review flags`, `Materiality Medium`,
`ASSESSMENT`, `source version`, `pprop_…`, `MODEL · OPENAI COMPATIBLE REV 1`,
`DETERMINISTIC REV 2`, `SUPERSEDED`, `**[UNVERIFIED]**`, `INFERENCE ⚠
UNSUPPORTED ○ UNREVIEWED OMITTED`, `Source Coverage`, `Resource linked ·
resource ref`, `Updated · meeting associated`, `Created · name, watches
activated`, `Filed · Desk root`, `Gather · No Room has two windows`,
`Project · AGENT`, `Preparation brief`, `NO SOURCES · BLANK PROJECT`.

## Verbs that did nothing, failed, or did something else

1. Room `Draft update` with real sources: 96 s, then nothing on the face
   (`09-draft2-t120s-1440.png`). The failure is kept in a state that only the
   Update posture draws.[^hidden]
2. The same press freezes the hub: the route calls the model on the server's
   event loop.[^loop]
3. ⌘K `Draft update for Payments migration` opens the list; it does not
   draft (`26-palette-draft-update-result-1440.png`).
4. ⌘K `Draft update · Select a Project`, `Ask this project · Select a
   Project`, `Gather · No Room has two windows` are listed though they cannot
   run (`02-palette-project-1440.png`).
5. `Watch sources` opens the steward, not the sources.[^watchlabel]
6. The steward's `Run once` makes no draft and no nudge; its `Act` step says
   `no effect allowed`. In code it never asks an engine; its draft step is
   the records draft.[^steward]
7. `Hand to coder` on "Ask Theo to pair with Mira two afternoons a week" and
   on every other owed item (`08-room-populated-1440.png`).
8. Meeting `More ▸ Add to Project` scrolls to a second button
   (`06-meeting-add-to-project-1440.png`).
9. Desk ▸ `New Decision` files the decision on the desk floor, outside the
   project and the Decisions drawer (`23-new-decision-created-1440.png`).
10. Review flags a decision made 20 minutes earlier as "due for periodic
    review" (`17-review-open-1440.png`).

Not pressed, so not judged: `Hand to coder`, `Open` on an owed item,
`Regenerate`, `Save`, `Copy`, steward `Tell me` and `Do it`, `Accept` on the
review flag, `Send` from the published update, `Get Info`, `Preparation
brief`.

## Visual problems

- The Room opens at about 800x600 over other windows; the work list fills it,
  and the five folds sit below the fold (`08-room-populated-1440.png`).
  Zoomed, the folds are five grey bars of equal weight
  (`13-room-zoomed-pages-1440.png`).
- Every owed row carries two plated buttons; on the phone three rows fill
  the screen (`10-phone-desk-393.png`).
- The door's footer state `NO SOURCES · BLANK PROJECT` is grey on grey and
  hard to read at both widths (`03-door-open-1440.png`,
  `25-phone-door-393.png`).
- The update editor shows raw markdown with a format toolbar; on the phone the
  draft is mono text over 1,300 px (`27-update-deterministic-open-393.png`).
- The steward face is a blank grey field with a list of pipeline phases
  (`16-steward-run-t010s-1440.png`).
- The meeting icons leave the desk floor once filed into the project; the
  project is a drawer icon with a badge `7`, then `8` (`11-room-after-close-1440.png`).

## What worked

- The meeting summaries from the LAN engine were correct in 14 s each, with
  owners and dates (`06-meeting-open-1440.png`).
- Background memory wrote three useful, cited project pages without being
  asked (`13-room-pages-open-1440.png`).
- "Ask this project" gave a correct, cited risk answer in under 20 s.
- The records draft is fast and structurally right.
- Publish leads straight into Send with a preview (`28-update-published-1440.png`).
- Today ▸ Decisions shows the confirmed decision with its meeting.

## Unknown (not verified)

- Why the engine's draft was `not_usable`. The hub log of the rig kept no
  line about it. The code map lists likely causes (`MODEL.md` §3).
- How much the background memory work slowed the draft. During the walk the
  LAN engine served 58 model calls, most of them memory facts and pages,
  while the drafts ran; llama.cpp on the LAN has one slot.
- GitHub, Jira and Confluence: the rig has no `gh` or `acli` and sends
  nothing off the machine, so no watch ran against a real source. Provider
  sign-in, watch refresh and the steward's nudge on a waiting PR are unwalked.
- The steward's `Tell me` and `Do it` modes on a schedule.
- The Room review on the phone (open per DLT:23). I did not walk it at 393.
- The source of one `500` and one `503` in the console during "Ask this
  project".

## Verdict

The cluster has strong parts that never meet. The meeting summaries, the
background pages and Ask know exactly where the payments project stands. The
Room hides that in a fold, leads with seven "Hand to coder" rows, and says
"On track". The one press he needs on Friday blocks the whole desk for 80 to
100 s and then says nothing, while a usable draft is 0.1 s away. The project
does not find its own meetings, sources need a terminal, the steward is a
second automation engine that reports its pipeline instead of doing the
work, and a decision has four places to live and an empty drawer named
Decisions.

[^rig]: Isolated hub `scripts/graph_walk.py serve` on port 8811 through
    `Hub` and `_isolated_hub_env` (scratch `HOME` from `mktemp -d`, every
    isolation switch, `HOLDSPEAK_TEST_NO_REAL_CLI=1`), started from the owner's
    desk worktree (`wt-daily-delight-delivery-20261017`, `217001b2e`, the
    merge of #1247; its `web/src` and services match main `68e49a296` except
    `holdspeak/web/routes/setup.py`). Real LAN engine `qwen3.8-27b` at
    `192.168.1.43:8080`, assigned as the global default through MCP
    `model_library.define_endpoint` and `inference_assignment.set`. Seed: three
    meetings through `POST /api/sync/push` and real summaries through
    `POST /api/meetings/{id}/intelligence/run`; two notes through
    `POST /api/notes`; People set up through `POST /api/people/setup` and three
    `POST /api/people/relationships`. One meeting was added to the project on
    the face; two meetings and two notes through MCP `project.link` and
    `project.resource.add` to save time. Chromium headless via Playwright,
    1440x900 and 393x852 (mobile, touch, scale 2). The hub stopped and the
    scratch HOME was removed afterwards.
[^coverage]: `holdspeak/services/project_update_service.py:336`.
[^hidden]: `web/src/features/project-room/ProjectRoomCore.tsx:443` calls
    `updateCtrl.draft(...)` with the posture off; on failure
    `web/src/features/project-room/update/useUpdateController.ts:234-245`
    stores the reason and leaves the posture off; the Update posture that
    draws it mounts only when the posture is not off
    (`ProjectRoomCore.tsx:2880`).
[^loop]: `holdspeak/web/routes/project_updates.py:95-106`: an `async def`
    that calls `ops().invoke(...)` with no thread.
[^watchlabel]: `web/src/features/project-room/ProjectRoomCore.tsx:1444-1447`
    (`onClick={() => void stewardCtrl.enterSteward()}`, label `Watch sources`).
[^steward]: `holdspeak/services/project_steward_service.py:1533` calls
    `draft_update(principal, project_id)` with the default generator.
