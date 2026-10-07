# PHILO Phase 14 — The Desk Is Objects: the proposal

Written 2026-10-07 by Muad'Dib after the owner's three catches of the same
day. Read with `docs/internal/CONDUCTOR.md` (what the Conductor does) and
`docs/internal/philo/phase-13/PROPOSAL.md` (what Phase 13 set out to do to
the Desk, and did only in part).

## 1. What he asked

Owner, 2026-10-07, in order:

1. On the Conductor: "We spent a lot of time building out conductor
   (promising, melikey) but holy fuck does its interface ABSOLUTELY
   STINK ... We need a proper phase to address it stat. This has got to
   be our GEM of a functionality."
2. On the Desk: "when you decided that our 'desk' (the real OS-like
   experience) was something you could just abandon and evolve us not as
   a workbench 2.0+ on steroids, but frankly, more into windows 1.0
   territory".
3. On the whole: "Most of the features you'd been building out are ...
   just kind of ... apps. And the old 'desk' feeling of putting together
   drawers, files, different types of entities, somehow is lost in all of
   your materials. In fact, the file explorer is that super ass fucked up
   one with [ ] still in the copy".

The three are one diagnosis. The Conductor's face is bad in the way the
whole Desk has gone bad, and the Desk has gone bad because we built
applications where Workbench builds objects.

## 2. What I found (one paragraph per truth)

**Nobody ruled the drift.** Phase 13 ratified the Workbench look (Steel,
2026-10-02) and the quiet title bar (B, 2026-10-03). Then the Conductor's
faces were composed in two days by worker fleets from library species,
on top of that frame, without anyone asking what a window's *contents*
look like in that material. I shipped the shots without seeing it.

**The Chair is tiles.** `web/src/desk/chair/chair.css:15` says it: "the
Chair is a Workbench SCREEN of four windows". Needs you, Brief, The week,
Capture: fixed, same size, edge to edge. That is the Windows 1.0 model
(tiled panels), not a Workbench screen (icons, drawers, windows you open,
drag and stack).

**The material is gone from the live chrome.** Bevels survive in one
element of the Chair (`chair.css:692`) and in a *parked* hero. Everything
else is a flat dark panel. The owner's directives of 2026-08-17 ("beautified
AND functionalized, never a POS") and 2026-10-01 ("really lean on
steroids") are on record and unpaid on these faces.

**The library ate the face.** UX-CANON A.3 ("no prose") and A.1 ("every
verb is the library Button"), read literally by workers, produced: every
fact a monospace uppercase chip in a thin border, every verb a flat grey
box, rows wearing six chips each (`NO DUE DATE · UNASSIGNED · ⚠ CLAUDE
CODE · WAITING`). That is a terminal pretending to be Intuition.

**We have the object model and do not use it.** `web/src/lib/primitives.ts`
declares twenty `PrimitiveKind`s (meeting, note, decision, project,
artifact, repository, **coder**, thread, people, ...), each with a label,
a sync class and a surface declaration; `web/src/desk/world.ts` lays them
out as world objects; the icon mold holds 180 sprites
(`web/public/desk/sprites`: automaton, cartridge, cassette, ...). Yet every
feature since Phase 9 shipped as an application window with a list inside
it: Needs you, Brief, The week, Agents, Delivery, Intelligence, Desk
memory, now the Conductor. The owner's thing is never on the desk; it is
inside an app.

**The explorer is a text-mode list.** `DeskListView.tsx:305` renders the
selection mark as the literal strings `"[ ]"` / `"[x]"` inside a ghost
Button. It was born as "the semantic list mode ... for keyboard and
screen-reader use" (HS-93-08) and became the Floor's file explorer.

**The Conductor has no home.** An agent's life is spread over five places:
a `Hand to agent` Button on a row; a launch sheet that ends in `LAUNCHED ·
BRIEF SENT · Close`; an `AGENTS` section inside **The week**; a Dock
window "Agents" that read "No sessions" while two ran; a Room row wearing
`⚠ CLAUDE CODE · WAITING`. The "session" window is the old tmux steering
console (`pane %0`, `RAW LINES 1 Δ 4S`, a KEYS strip, `CLASSIFY · Keep as
note · e.g. HS-87-05 · Pin`, `Arm rename/kill`). The owner's job there is
to read "Jordan or Avery?" and answer; what the agent has *done* (files,
commits, tests, its last words) is absent. Status is three words:
WAITING, WORKING, PR OPEN. The row says UNASSIGNED while an agent works
it. The launch sheet collapses the brief, names none of its "7 CHECKS",
and shows a branch (`HS/ACTION-M-STANDUP-A1`) nobody would type. There is
no Stop, Re-brief, Approve/Deny on the row, diff, or review.

**The hub already holds the timeline; it throws it away.** Audit of
2026-10-07 (read-only, on `c1a6ce50b`): per launch the hub has the brief
text, the origin, the branch, the launch time, the follow-through (PR
number, url, state, review decision, merged SHA and time), every gated
tool call in order with a 120-character head and its verdict
(`gate_proposals`), every wait with its draft and verdict and every
answer typed (`steering_audit`), the pane tail on demand, work-attempt
state changes with timestamps, and Claude's transcript path (every
assistant message and tool use). What it lacks is cheap: the session
record is overwritten per hook event instead of appended
(`agent_context/sessions.py`); Stop's `last_assistant_message` is read
for a question and dropped; nothing runs `git log`/`git diff --name-only`
in the worktree while the agent works; the PR row's `ci` field is not
kept on the launch. No route returns `brief_text`, `branch` or
`launched_at`. The drafted answer rides on the Needs-you row and no face
shows it.

## 3. The phase: from applications to a desk of objects

Three movements, in this order. Each is measured against Tenet 5 (a
component framework in the manner of Intuition), Tenet 6 (Workbench 2.0+
on steroids) and the question "will you use this on a Tuesday?".

### Movement A — Objects (the grammar)

The Desk's unit is the object, not the app.

- **Every kind is an icon from the mold**, on the Floor and inside every
  window: meeting, note, decision, project, artifact, repository, PR,
  person, agent (`coder`), thread. One icon per kind, states as sprite
  variants (lamp when it needs you, ghost when parked), never a chip.
- **A Project is a drawer.** Open it: its objects, as icons or as a list.
  Rooms keep their intelligence (status, decisions, watches) as the
  drawer's own head, not as a separate app.
- **The explorer is a Workbench drawer view**: icon view and list view
  (a real list: name, kind, when, where; sort by header), selection by
  click and rubber band, Get Info, rename in place. `[ ]` goes.
- **Open = its own window.** Any object opens to its window (Phase 13
  ratified this for names; it now holds for every kind). The window's
  head is the object's identity (icon, name, kind, where); verbs are
  the object's verbs.
- **Drag is composition.** Drop an object on a drawer to file it; on a
  person to assign; on a destination to send (Phase 12's parked Floor
  work returns here); **on an agent to hand the work**; on the AI core
  to ask. The Desk Primitive contract (`accepts`/`emits`) comes back as
  the law of what drops where.
- **Applications become views.** Needs you is a smart drawer over the
  same objects (its rows are the objects, with their icons and their own
  verbs). Brief, The week and Delivery are views that open an object on
  press. Intelligence and Settings stay applications; nothing else does
  unless it earns it.

### Movement B — Material (Workbench 2.0+ on steroids)

- **Depth returns.** Windows and gadgets wear the bevel grammar
  (`--bevel-*` exists in the tokens; the Chair uses it once). A control
  you click LOOKS clickable (UX-CANON D); a fact you read is flat text.
- **Chips become lamps.** A status is one lamp on the icon or one token
  on the row, never six chips. Words that are facts (due date, owner,
  when) are text in the list's columns, not tokens.
- **The Chair becomes a screen.** Four windows you open, move and stack
  on a Floor with icons, with a sensible default arrangement remembered,
  instead of four fixed tiles. The Dock stays.
- **The mold inside windows**: object rows lead with their sprite; drawers
  show their contents as icons at 1440 and as a list at 393.
- **Type and copy**: the type steps of UX-CANON C hold; uppercase mono is
  for captions and counts, not for every word on the face.

### Movement C — The Conductor as objects (the gem)

- **An agent is an object.** A launched agent is an icon (from the mold's
  automaton family) in its Project's drawer and in a **Conductor** drawer
  on the desk; a lamp when it asks, a second state when it has a PR.
- **Drop to hand.** Drag an action item, decision, note or issue onto an
  agent icon (or the Conductor drawer) to hand the work. In YOLO the
  launch is one confirm line with the brief one press away; in Secure and
  Normal the sheet opens. The brief is shown, not collapsed; its checks
  are listed; the branch reads as the item's name.
- **The agent's window is its lane.** Open the agent: a timeline (brief
  sent → tool calls and its own words → question → commits → PR with its
  checks and review → merged), the question at the top with the voice
  answer under it (Enter sends), the files changed and the diff, the PR
  inline. Verbs: **Answer**, **Approve / Deny** (held calls, on the row),
  **Re-brief**, **Stop**, **Open PR**. Merge stays the owner's press in
  GitHub (the gate holds `gh pr merge`; unchanged).
- **The tmux pane goes behind RAW** (the standing debug rule); it is never
  the face.
- **Backend for the lane** (no canvas needed): append hook events per
  session instead of overwriting; keep Stop's `last_assistant_message`;
  read `git log <base>..HEAD` and `git diff --name-only` in the worktree
  on each coder frame; keep the PR row's `ci` on the launch; a route that
  returns the launch (brief, branch, launched_at, follow-through, events,
  commits, files); the drafted answer on the face.
- **Repairs that ride along**: an item an agent works is assigned to that
  agent, never UNASSIGNED; a question is a lamp, not `⚠`; the Agents
  application and the AGENTS section fold into the Conductor drawer.

## 4. How it runs

1. **Canvas first, one page** (UX-CANON A.2; the title-bar lesson of
   2026-10-03: draw, do not ask). Three real alternatives of the
   desk-as-objects with the Conductor on it — the Floor with drawers and
   an agent object, a Project drawer open, the agent's lane, a drop-to-hand
   moment, Needs you as a smart drawer — at 1440 and 393, drawn on the
   real library and the real desk, with the current desk beside them as
   the control. The owner names a letter. That page also settles the
   material, because the Conductor is the flagship and the Desk inherits
   it.
2. **Build what was ratified**, lane by lane; the ratified board beside
   the built shot every PR; the owner sees shots before merge (A.13).
3. **Astra**: one final review round per PR, at most two iterations
   (CLAUDE.md). Brief her with the ruling and the board up front.
4. **Tests**: FAST before each merge, scoped browser tests on every face
   PR, one real-agent walk (isolated credentials) before Movement C is
   called done.
5. **Status**: `pm/STATUS.md` at each merge.

## 5. Lanes

| Lane | Content | Depends on |
| --- | --- | --- |
| 00 canvas | The one page, three alternatives + control | — |
| C0 lane backend | events appended, commits/files read, launch route, `ci` kept, drafted answer served | — (starts at once) |
| A1 objects | kind icons from the mold everywhere; sprite states; `[ ]` gone; list view as a real list | ratified board |
| A2 drawers | Project drawer; explorer icon/list views; Get Info; open = window | A1 |
| A3 drag | accepts/emits law; drop to file / assign / send / hand / ask | A2 |
| B1 material | bevel grammar on windows and gadgets; chips → lamps; type and copy | ratified board |
| B2 the screen | Chair as windows on a Floor; default arrangement remembered | B1, A2 |
| C1 agent object | agent icon in drawers and the Conductor drawer; lamp states | A1, C0 |
| C2 the lane | the agent's window: timeline, answer, diff, PR, verbs | C0, C1 |
| C3 hand | drop-to-hand; YOLO confirm line; sheet for Secure/Normal; brief shown | A3, C1 |
| C4 fold | Agents app and AGENTS section fold into the Conductor; Needs you rows as objects | C2 |

## 6. Forks, ruled by default (he overrides by looking at the page)

1. **The terminal.** Behind RAW, one press away, never the face.
2. **Needs you.** Stays, as a smart drawer over objects, not an app.
3. **Where agents live.** In the Project drawer *and* in one Conductor
   drawer on the desk (the same objects, two places to find them).
4. **Merge.** His press in GitHub; the Desk shows the PR and its checks.
5. **Launch in YOLO.** One confirm line, the brief one press away (his
   lean of 2026-10-06: "launch straight").

## 7. Not this phase

The OSS "open by default" pass (waiting on his go). The atlas walk of
launch → PR → merge with doubles (CONDUCTOR.md, open). Saved window sets
(Phase 13 fork 4, BACKLOG). Swift/iPad parity (the web Desk is the spec).
