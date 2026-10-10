# Phase 17 usability inventory (2026-10-10)

The owner, 2026-10-10: "Could we, please, in a speedy fashion, also start addressing very heavy and very
taxing usability issues of the entire system? It's so cumbersome to use. Instead of delighting, it's confusing."

Four walkers used the real desk on main @ 33ce84d27, each on an isolated hub, as the first user (a Senior
Software Architect with three reports) for one slice of his Tuesday. Eyes first: every finding has a screenshot
(the shots stayed in the session scratch dir and are not in git). Severity: BLOCKS (he cannot finish), TAXES
(he finishes slowly or in doubt), ANNOYS.

## The pattern behind the findings

1. **The desk says READY when it is not.** Speech reads READY with no speech model; a meeting with no transcript
   reads "All summaries done"; Setup passes; the brief says "No engine" after an engine is set. He cannot trust
   the face, so he cannot act on it.
2. **One question, many answers.** Five counts for "what needs me"; six faces with six subsets of a meeting's
   output; two desks (Chair, Floor) with different objects and rules; three faces for one meeting; two homes for
   one project; two 1:1 preps; "Agent" names two things.
3. **Dead ends.** No Send on a thought; no "they owe me"; no Add source after a project exists; no Object verbs on
   the Chair; no way back into first-run; no sign-in after a bookmark.
4. **Internal words on the face.** Steward, Receipts, Harnesses, hooks, Owner string, Grounding, MCP, Actuators,
   assignment, route, wire, governing, deterministic, tombstones, arrival, PREFS.
5. **Windows fight him.** They open on top of the icons, on top of each other, and come back as other windows
   after a reload; the menus teach keys a browser tab keeps for itself.

## BLOCKS

| Id | Job | What happens | Lane |
|---|---|---|---|
| U01 | Act on an object from the Chair | Object menu disabled while an icon is selected; no right-click menu; F2 does nothing (works on the Floor). Hand to agent unreachable by mouse. | objverbs |
| U02 | Open the desk again | Without `?token=` (new tab, bookmark, restart) the page shows `principal_right_required`; token only in sessionStorage. | wayin |
| U03 | First dictation | Speak says READY with no speech model; TALK fails with a cut-off message and no fix. | speech |
| U04 | Record a first meeting | Live meeting says "Ready to record"; the meeting is saved with no transcript while the list says "All summaries done". | speech |
| U05 | See what needs him | Needs you: 31 identical "can't check" source rows above his 3 real items. | needsyou |
| U06 | What did we decide yesterday | Meeting detail shows commitments but not decisions; a decision search hit opens the meeting and drops an untitled icon. | decisions |
| U07 | The brief on a Tuesday | Brief frozen at first generation, no Refresh; window starts 17:00 the day before, so Monday's meetings are missing. | summaries |
| U08 | Thought to something sendable | Thought window has Change and Finish only; a note is not a sendable kind. | thoughtsend |
| U09 | Record what someone owes him | People has no "they owe you" input; the only input records the reverse direction. | people |
| U10 | Add a repo to an existing project | The Room has no Add source; sources only in New Project. | sources |

## TAXES

| Id | Job | What happens | Lane |
|---|---|---|---|
| U11 | Summaries after every meeting | Engine chosen "for summaries", yet each meeting needs "Run summary"; "intel disabled in config" (meeting_glue passes intel_enabled=False). | summaries |
| U12 | Know "what needs me" | Five numbers: bell, Needs-you icon, two dock badges, brief, Processes, List view, Setup. | needsyou |
| U13 | Reconnect a source | Reconnect opens Settings at the top, not Connections. | needsyou |
| U14 | Meetings headline | "No engine for summaries" in large orange while summaries are stored. | summaries |
| U15 | Fix speech after first run | Runs on Speech card "TOOL INCOMPATIBLE · Choose" does nothing; no download outside first run. | speech |
| U16 | Read Runs on | Internal task names ("CADENCE DRAFT · RAILS SUMMARY", "EVERY JOB WITHOUT ITS OWN WIRE"); Settings opens it as a second window over an empty pane. | runson-words |
| U17 | Redo first-run choices | Go → Setup → "Continue arrival" opens a different page; no way back to the Get ready cards; only exit is "Continue later". | firstrun |
| U18 | Know what the product is | "Start here" is privacy text; starter notes are prompts with no button. | firstrun |
| U19 | Setup page | 30+ diagnostics; passes with no speech model. | speech + firstrun |
| U20 | Decisions window | 1 of 4 decisions; "UNASSIGNED GOVERNING", no date, no meeting. | decisions |
| U21 | Six faces of a meeting's output | Needs you, Desk memory, Follow-through, Decisions, meeting detail, project drawer disagree. | decisions + needsyou |
| U22 | Project update | 6 clicks; Draft again makes a new revision; raw ids and machine text in the draft. | later |
| U23 | Meeting Send | Form picker hidden in a `↻ SUMMARY` chip; Follow-up repeats decisions and actions. | later |
| U24 | Meetings window | 640 px, list and detail stacked, 6 footer verbs on 3 rows. | windows |
| U25 | Chair vs Floor | Two desks with different objects; zone labels overprint. | later (needs a ruling) |
| U26 | Open a meeting | Three different faces depending on the door. | later |
| U27 | Keyboard | Menus teach ⌘W/⌘N/⌘1–4, which Chrome keeps for the tab. | windows |
| U28 | Windows | Open at (24,72) over the icons; stacked exactly; only the title label drags; positions and identities change on reload (Room returns as "Desk memory"). | windows |
| U29 | Connect GitHub/Jira | "Unreachable" with no sign-in command; Connect opens Settings over New Project; Jira stays NEVER CHECKED. | sources |
| U30 | Project has two homes | Create opens the Room; dock/icon opens the Drawer; duplicate Ask and Steward. | sources |
| U31 | Project Room words | Receipts, Steward, Policy (Unattended, Effects, Max retries, Cooldown s). | words |
| U32 | Conductor | "3 ready" next to "NO HOOKS · HOOKS MISSING"; no "start on a project". Desk ▸ New Agent is a persona form. | conductor |
| U33 | 1:1 prep | Prep tab lacks you-owe/they-owe; a separate "1:1 prep" sticky; "No 1:1 planned" with no verb. | people |
| U34 | Person labels | "Owner string", "Grounding notes", uneditable empty fields. | people |
| U35 | Settings | "No default model" headline; MCP, Mesh, Actuators, Schema, tombstones, "« PREFS"; free-text mic device. | words |
| U36 | Too many doors | Speak 4 doors, Conductor 4, People 4; "Desk memory" means two things; Go has 17 rows; the dock grows with projects off-screen. | later |
| U37 | Phone | A single tap does nothing; meeting footer takes a quarter of the screen. | later |

## ANNOYS (kept for the words and windows passes)

New note title "New noteAsk…" (objverbs); search has no "Ask: <query>"; decision opens with a Send block on top;
names cut in the middle; "MEETING READY" toast unreadable and says "proposals"; card colours mean nothing;
"127.0.0.1" chip ×4; two record buttons in two windows; Desk menu has 9 "New …" and no "Record a meeting";
Add person jumps into the person; duplicate names accepted; "New relationship" button; History zero counters;
Needs-you "DUE TODAY" with no date; "4 OF 4 AVAILABLE".

## What the walks could not see

Real downloads (huggingface), a real LAN engine, real gh/acli sign-in, real agents, real calendars, real touch,
real Chrome key handling. There is no architect's-desk seed: `holdspeak seed` applies only `fresh-desk`.
