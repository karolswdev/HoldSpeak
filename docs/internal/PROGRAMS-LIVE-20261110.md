# Programs live window — 2026-11-10

Programs uses one master/detail window. The advanced seats from the former
folds, wizard and amendment bar now use the same kit lists, facts and forms.
Retired drawing implementations and their selector tests stay under
`web/src/desk/programs/_parked/grammar-20261110/`.

## Implemented

A Programs desk icon, program link or retained program pullout opens the same
Programs surface. A program link selects its program. A step link also selects
its step. The title is Programs. The master groups the rows as Waits on you,
Running, Tonight and Earlier. The detail has Now, Steps, Text and Ledger tabs.
New program and Amend replace the detail with an inspector form. New program
has Program, Work and Checks tabs; its field values stay when the tab changes. The surface
starts at 900 × 600 with content fitting off, so its first frame cannot shrink
the bounded deck.

Now reads a running step's screen through the existing coder peek operation.
A step with no readable session shows only its own hub checkpoints. These are
separate from the shared kit's decorative motion. Reduced motion stops the kit
animations; incoming hub text can still change.

Park in the Now question stops the whole program. Go on, Park, requirement
answers and text Apply send the program id in the
path, the selected step id, the program revision and the latest visible ledger
checkpoint. The service checks that binding under its lock before an effect.
A refusal keeps the input and asks the owner to read the new question. A kit
question also disarms on a changed target or action identity. A commit answer
additionally sends main's existing held-commit binding. A delivery answer keeps
its delivery checkpoint binding.

Every surface that shows a Programs question keeps its binding: the Desk,
Needs you, briefing page, Telegram message, phone message and call read-back.
A binding contains the program id, step id, step update token and visible
checkpoint. The program revision also protects whole-program text edits.
The service refuses a changed question as `answer_stale`: “This question
changed. Read it again.” A page reread gets the new question; an old message
retains its original question. Commit custody remains an additional check.
Command-only MCP and internal rule dispatch can omit the optional binding;
they do not render an owner question.

The existing `program.step_remove` declared operation now has its DELETE HTTP
projection. Its service permission rules are unchanged.

## Capability seats

| Prior capability | Current seat or remaining work |
| --- | --- |
| Find, select and open a program | Master selection list; program and step links select in this window |
| Open the active agent | Master toolbar Open; an agent-answer item opens its session |
| Start a draft or night program | Now completion verb |
| Park / Resume | Master toolbar; Park also answers the shown Now question |
| Add a step to tonight | Master toolbar Add to tonight; existing Tonight verb remains |
| Running progress and agent output | StepTrack, step header and LiveWell |
| Core, merge, finding, review, limited, race, lesson, delivery and proposal answers | Now question choice; chosen answer, identity and revision sent together |
| Failed or stale write | Failed writes stay in status; a stale refusal is a plain pane line above Read the new question, with counts kept |
| Finished recap | Now figures and per-step PR/time rows; Open PR and Open recap |
| Parked and tonight facts | Now parked reason/time/by with Resume; night-list neighbors and its steps |
| List and select steps | Steps selection list |
| Add / insert / edit / amend a step | Steps list verbs and inspector form |
| Move a step | Steps Move up/down; Alt+ArrowUp/Down |
| Remove an unstarted step | Steps Remove step; Cancel / Remove step question |
| Skip a parked step | Steps Skip; Cancel / Skip question |
| Race | Steps > Race: two or three agents; contender list, facts and bound Pick question |
| Take over / hand back / hand off | Steps verbs; handoff agent in the inspector |
| Check log and PR | Steps Open log / Open PR |
| Requirements, gate, report, handoffs | Steps tabs, selection lists, facts and inspector forms |
| Requirement met / unmet / waive / send back | Requirements selection, reason and Cancel / answer question |
| Add / edit requirement; shot thumbnail and Open shot | Steps > Requirements: Add/Edit form, Evidence/Facts tabs, ImageWell and Open shot |
| Interview rounds | Steps > Rounds: list, offered or typed answer, next/skip/done/reopen and text-change review |
| Program text editing | Text fills its pane; Apply previews changes; Cancel / Apply question commits the frozen proposal |
| Explicit lowering of a gate | Selected text change checkbox before Apply |
| Sentence amendment and single-program draft planning | Amend form; engine response reviewed in the same text-change seat |
| New program | Inspector: project/folder, title, goal, template, control, agent, reviewer, person and check command |
| New program spending note | New program > Checks; note in USD, never a cap |
| Project-choice read failure and its old Retry control | New program has Retry projects; input remains after a read failure |
| Wizard Back, Escape and close | The form tabs keep fields; Escape or Cancel returns to the selected program; closing the window closes the form without a later result reopening it |
| Program-specific spoken routing and explicit Open Engines / Open text repair controls | Amend dictation uses Programs routing; failed engine read has Open Engines and Open text |
| Answer notes beyond requirement reasons | Every Now answer and Race question has a note; agent answers stay in the agent session |
| Goal, control, allowed agents, idle and other language fields | Edit program inspector: Program, Agents, Checks, Limits and Night tabs; touched fields only |
| Ledger, decisions, findings, lessons and family | Ledger tabs, lists and facts; Start from here, Overturn, Open program and Open Door task |
| Action/decision/note/item to program | Existing Run as a program entry; resulting program opens this window |
| Room and People program references | Kit two-line list rows; People keeps To show them / To ask groups |
| Room decisions | Kit selection list and selection verbs |
| Copy/revoke briefing page; open reach thread; context doors | Ledger > Context; question row has Copy page link and Cancel / Revoke link |
| Multi-program planning, splitting a large step, changing agents in bulk | Amend > Plan; planned-program selection and Apply all; selected large text change has Split; Steps > Agents rereads before replacing a draft |
| Carry an action on a manually added step | Steps Add form: Carry the program action is off until selected |
| Spoken and call-held amendments, accumulated sentences, keep/drop/overturn of that well | Amend dictation and Add a sentence; held proposals open review; Applied has Keep / Overturn, Cancel drops a held proposal |
| Findings Door links and detailed handoff redaction/continuation reader | Ledger > Findings opens the Door; Handoffs reads redacted text, earlier turns and continuation |
| All prior press-through app tests | Active tests by seat replay recorded hub replies; see PROGRAMS-TEST-SEATS-20261110.md for the retired-selector inventory |

Park and Resume retain worktrees. Remove and Skip name the selected step in an
in-window question. Requirement answers name the selected requirement. Text Apply
has its own in-window question, separate from preview. These questions disarm
when their target changes. Overturn and Start from here remain direct service
verbs as before.

## Shared material

ListPane has a deck composition with a bounded master and detail. LivePane fits
a live header, reading well, facts and question. Its read-only fact rows use
compact spacing; its well grows with the lines up to its maximum. Controls retain the kit's target size. The gallery Program deck
uses the same composition, including its four waiting facts at 393.

ImageWell is a named kit piece in the gallery. StepTrack condenses long station
names to numbered stations and the full current name below. The list owns its
two-line row height. InspectorQuestion supports fields, a named alternative to
Cancel, and a separate disarm callback so a changed question cannot press Park.
It retains main's action identity check and leading destination slot.

The old thin StationTrack still serves the briefing page. Its existing skin
moved from the retired app sheet into the surface kit; this does not move the
briefing page onto the new Program StepTrack. Programs imports no app stylesheet.

## Evidence and limits

The glass uses HTTP responses and socket frames recorded by the real
Programs service in `tests/integration/test_program_answer_binding.py`.
The state tape has engine mode **none**. Planning and restored seats use **replayed** engine replies; wire mode is **recorded**. A fake local
agent produces the service transitions; no real provider or owner device is
used. The running well shots prove two different recorded frames, and the
motion checks compare normal and reduced preferences.

Every Programs state has PNG and bounds JSON under
`.tmp/evidence-shots/programs10/`. The PR records the exact final checks and
shot names. These are implementation and fixture observations, not owner
visual acceptance. The finished figure counts **core questions to you** from
kept core-question ledger entries; it does not claim a full historical count of
all question kinds.
