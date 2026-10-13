# Phase 17 designs: the index

The owner, 2026-10-13: "It still feels more of a gimmick than a fucking OS." The
recon ([RECON-2026-10-13.md](RECON-2026-10-13.md)) gave the verdict: "the desk is
a stage set, not a workshop." He then asked for detailed software designs, and
four Fable designers each wrote one cluster:

| Doc | Root causes | What it fixes |
|---|---|---|
| [DESIGN-verbs.md](DESIGN-verbs.md) | R1, R6 | Ask AI, Draft update, the Object menu and Terminals do something or are gone. Every AI run shows its progress and its real reason. One engine line everywhere. |
| [DESIGN-attention.md](DESIGN-attention.md) | R2, R5 | One count of what needs him, and one meeting review. A confirmed commitment reaches the person's 1:1 prep. A thought can become a task, go to a project, or be asked about. |
| [DESIGN-windows.md](DESIGN-windows.md) | R4, phone | The Runs on ghost dies (Runs on becomes Settings ▸ Engines). New windows cascade and fit their content. One notice line. On the phone: one tap opens, Go is home, Back, a four-tile dock. |
| [DESIGN-words.md](DESIGN-words.md) | R3, R7, the cut list | Words, not chips: a glossary of every old term. The desk shows only his things. A five-app dock. A guard so phase words cannot come back. |

Each design cites the code (`path:line`), gives the flows press by press at 1440
and 393 against the recon's cost table, and splits the work into slices of about
a day. Each slice has its tests by tier and says how the owner judges it LIVE.
Nothing is deleted; every cut is parked.

## Three causes the designs found under the recon's symptoms

1. **Two engine settings, and only one is read.** Ask AI and thoughts still read
   the old placement. The 2026-10-08 fresh start left that placement at "this
   machine, not set up". Runs on writes the new assignment, and nothing connects
   the two. One cause explains three symptoms: the 122 s refusal with no reason,
   `NO ENGINE YET` beside a ready engine, and the Brief's "Set up local AI"
   (verbs, slice 1).
2. **Settings opens Runs on while it renders.** Every close re-renders Settings,
   so Runs on reopens itself and the hub saves it. That is the ghost window
   (`SettingsCore.tsx` `models` case; windows, slice 1).
3. **A confirmed commitment leaves the 1:1 prep.** Prep reads `status = 'pending'`
   and Confirm writes `'open'`, so a commitment drops out of prep at the moment
   it is confirmed. Prep also matches aliases only, never the display name
   (`people_service.py` `_brief_owned_actions`; attention, slice 1).

## Where the designs meet (settled here)

- **The dock.** The 1440 dock is the words design's: Today, Speak, Meetings,
  People, Conductor. The 393 dock is the windows design's: Today, Capture,
  Meetings, People. Capture is Speak's phone face. Both are entries in
  `applications.ts`. Words owns the `dock` rows; windows owns the phone order.
- **Runs on.** All three designs that touch it agree: it becomes Settings ▸
  Engines. Windows owns the move. Words owns the name. Verbs owns the engine
  line inside it.
- **The Missed shade.** Attention parks it. Windows moves the toast to one line
  on the bell. Words drops its chips. Build attention's slice first; the other
  two then have nothing left to do there.
- **Ask AI opens empty.** Verbs (OWNER CALL 1) and words (OWNER CALL 3) ask the
  same question. It is asked once below (Q4).
- **The noun.** Words recommends "Note" everywhere, with "Thought" gone as a
  word. Attention designs the verbs on that object. If the owner keeps
  "Thought", only the words change.

## The build order (one PR per slice, on the fast cycle)

The first five slices are the felt difference this week. They need no owner
call.

| # | Slice | Design | Why now |
|---|---|---|---|
| 1 | One engine authority, one failure reason | verbs S1 | Ask AI and thoughts start working on his assigned engine |
| 2 | The ghost dies: Runs on is Settings ▸ Engines | windows S1 | A window that comes back after three closes breaks trust in the window model |
| 3 | The commitment reaches the person's prep | attention S1 | Half a day; the 1:1 loop works end to end |
| 4 | One attention source | attention S3 | Five numbers become one (Q5 stands unless he says otherwise) |
| 5 | The egress rule and the phase-word guard | words S1 | Every later word slice shrinks the guard's debt ledger |
| 6 | The engine line and the run line; the Ask face | verbs S2 | needs Q4 |
| 7 | One review: Outcomes owns Confirm | attention S2 | needs Q6 |
| 8 | Draft update drafts in one press | verbs S3 | needs Q2 |
| 9 | ⌘K: objects first | attention S5 | — |
| 10 | Cascade from the front window; sizes fit content | windows S2 | — |
| 11 | The desk shows his things (seeds, loose icons) | words S5 | needs Q9, Q10 |
| 12 | The dock and Go | words S6 | — |
| 13 | Phone: one tap opens, Go is home | windows S5 | — |
| 14 | Phone: Back, one primary verb, four tiles | windows S6 | needs Q11 |
| 15 | The thought's three verbs (Task, Project, Ask) | attention S4 | — |
| 16 | The Object menu offers only what works | verbs S4 | needs Q3 |
| 17 | A meeting opens in the Meetings window, with Back | windows S3 | needs Q1 |
| 18 | The thought window's words | words S3 | needs Q8 |
| 19 | A thought's tasks are found | attention S6 | needs Q7 |
| 20+ | The remaining slices in each doc's own order | all | — |

## The owner calls (all of them, in one place)

Each one gives the designers' recommendation first.

| # | Call | Recommended | Other | Design |
|---|---|---|---|---|
| Q1 | A meeting opens… | inside the Meetings window, list ▸ detail with Back (as People does) | its own window beside the list, never over it | windows CALL 1 |
| Q2 | Draft update when the engine fails | `Not drafted · <reason>` + Try again + "Draft from the Room's facts" | keep the silent fallback, with its reason on the row | verbs 2 |
| Q3 | A project's danger verb | Archive (restorable) | Delete, through the one receipt | verbs 3 |
| Q4 | Ask AI's five lenses | Ask opens empty; lenses show only when material is added (and stay on the meeting Ask) | five ghost Buttons that fill the draft | verbs 1, words 3 |
| Q5 | The Needs-you icon's count | the lamp stays, the number goes; the bell is the one count | keep both (same number) | attention OC1 |
| Q6 | The transcript span from Review | keep it under More ▸ Show in transcript | cut it; Open transcript stays in the foot | attention OC2 |
| Q7 | When a thought's tasks are found | automatically on Finish, the run shown in the foot | a Find tasks verb | attention OC3 |
| Q8 | One noun for what he writes | Note everywhere; Thread stays for an agent talk | keep Thought for a note being worked on | words 1 |
| Q9 | Persons on the desk | never loose; People is the ledger | a loose icon only for a 1:1 today | words 2 |
| Q10 | The seeds | Start here + the Weekly update starter; the rest parked | all five inside a Start here drawer | words 4 |
| Q11 | Back on the phone | closes the pane (the hub reopens it where it was) | iconifies it | windows CALL 2 |

Q1 reverses how the code read his 2026-10-10 ruling ("a meeting opens in one
window"), so it is his to make. The others are small, and the recommendation
stands if he says nothing.
