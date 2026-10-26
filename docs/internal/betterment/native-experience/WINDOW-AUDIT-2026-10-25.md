# The window audit of 2026-10-25 (every window, seeded desk, 1440)

Owner, 2026-10-25 23:00, after three one-screenshot fix cycles (the dock, the
Needs-you row, the Room): "YOU'RE BEING so fucking reactive… what about some
proactivity finally from you?" This audit is the answer: every case the desk
sweep opens (35 windows), shot on a seeded isolated hub at 1440 with a dense
Room (13 late milestones), each judged against
WINDOW-GRAMMAR-2026-10-24.md and the egress ruling of 2026-10-25 (UX-CANON A.9).

## On the grammar (no defect worth a lane)

Today, Needs you, Meetings, the meeting Outcomes, Projects, the Room (Now,
after #1483), People, Decisions, New decision, Agents, Automations, the
automation window, Activity, Processes (bar the column defect below),
Settings (You, Notices, Rhythm, Wallpaper), Engines, Setup, the New Project
door, the Note, Components.

## Defects, grouped into lanes (all launched 2026-10-25 23:10)

| Lane | Window(s) | What the shot shows |
| --- | --- | --- |
| speak | Speak (surface-dictation) | Title squeezed to "S…" by five wings; the foot is a Clean-up strip, a floating Choose engine, a dotted level bar, a caps hint, and three bordered Buttons on the status-bar edge; the Journal/Blocks/Learned/Commands wings are not dense lists. |
| live | Live meeting (surface-live) | Old page grammar: "Ready to record audio only" + Start meeting floating; HUGGINGFACE.CO and REC mono-caps chips; "Link · connected" loose; a centred mono "READY" footer. |
| palette | ⌘K palette; Capture (chair:capture) | Palette is a terminal: mono rows, mono-caps section captions, "3 OPEN" caps; Capture has three 60 px tile buttons and mono times. |
| caps | Processes, New Project, Person, Meeting, Today, Needs you, Room folds, Calendar snapshot, Context | Started time breaks mid-number and Where wraps three lines; "Check sources" wraps; an empty grey selected band under "Priya owes me"; a lone "Prepare…" in a blank band; MEETING RECORDED caps tokens; NEXT caps in the Needs-you status bar; mono-caps head facts and fold tokens in the Room; CAN'T READ / NO SCREENSHOT chips and dead footers. |
| chips | Memory window; Settings ▸ Accounts | Memory is a page (Ask well + plain-name lists + RAW + dead footer); Accounts rows are cards with mono account/host lines and verbs in blank bands. |
| egress2 | Workbench, Delivery board/dossier, Rhythm, tool inspector | Still wear host / scope chips (#1481 left them). |
| decisions2 | Decisions paths from Today | A meeting decision without a record and WHY with several records still open the Decisions page inside Today; Review decisions lost Current-only. |

## Method (repeatable)

`tests/e2e/test_desk_sweep.py` fixtures (`desk`, `pw_browser`, `_page`,
`_hub_open`, `CASES`) in a scratch test that opens every case, seeds 12 late
milestones into the seeded Room, shoots the desk per case into a scratch
folder, and writes a report.json of window boxes and console errors. The
scratch test is removed before quick_check. Shots are judged by eye against
the grammar; the fix list goes to parallel lanes; the owner judges live.
