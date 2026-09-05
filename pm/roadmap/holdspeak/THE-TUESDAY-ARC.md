# The Tuesday Arc — where HoldSpeak becomes a set of tools he cannot do without

Written 2026-09-05 on the owner's directive, verbatim: "LET'S MERGE AND
DEVISE ADDITIONAL PLANS THAT WILL LOOK AT SOME OF THE OPPORTUNITIES FOR
HOLDSPEAK TO REALLY BECOME AN EXTREMELY POWERFUL SET OF TOOLS." Grounded
in three read-only recon passes over the code AND his real desk
(sqlite, read-only, 2026-09-05). The standing bar is unchanged: value to
a Senior Architect managing three people on a Tuesday; the Constitution
binds every line; design on the library before build; his word on his
desk is every phase's exit.

## 0. The census in one paragraph (his desk, 2026-09-05)

715 kernel operations, all receipted. 189 MCP tools in 34 families. 21
desk applications. And on the desk that matters: meeting intelligence
has NEVER run (8 meetings; 0 plugin runs; 0 intel snapshots; 6 of 8 have
intelligence disabled); decision_records 0; decision_commitments 0;
dictation_corrections 0 (the "learns how you work" loop untrained);
cadence_loops 0, cadence_nudges 0 (nothing runs unattended); the Monday
brief ran ONCE (1839 items on 2026-08-24) and never again;
calendar_events 0; workbench_runs 0; the model assignments were painful
enough that the co-creator got lost ("he doesn't know how to use this
product"). What DOES run: the Watches (GitHub + Jira connected, 32
watches, evaluations succeeding since 2026-09-03), three steward runs,
five updates, and — since yesterday — the one-screen Door and the
four-question Room. The chain is alive from Door to Room and dead from
meeting to commitment. Nothing reaches him; he must open the desk to
know.

## 1. The thesis

Five gaps, in dependency order. Each gap is a phase. Each phase ends on
his word at his desk, and each carries a hygiene lane (the 169 ledger).

| # | Gap on his desk | The phase | Unblocks |
|---|---|---|---|
| 1 | No model he trusts is assigned; every intelligent feature is starved | **170 The Concierge** | 172, 173, and the ask well |
| 2 | Nothing runs while he is away; the desk never reaches him | **171 The Heartbeat** | every Watch, the brief, the notifications |
| 3 | Meetings produce recordings, not decisions, commitments or 1:1 prep | **172 The Loop Closes** | the People pillar; the tagline |
| 4 | The steward observes but cannot write a word or nudge a person | **173 The Steward's Hand and Voice** | the weekly update; the bottleneck report |
| 5 | HoldSpeak lives on one Mac, one terminal, two connectors | **174 Reach** | overnight runs on .43; a third tool; the phone |

## 2. The phases

### Phase 170 — The Concierge (the model front door)

**Tuesday moment.** He opens Settings → Models once. It says: "Found:
llama.cpp on 192.168.1.43 (Q6, 24k context) · a cloud key in your
keychain · 7 local files." One screen proposes one assignment set
(dictation, meetings, the ask, the steward's drafter, the thread) with
the egress chip on every row; he presses `Use these`. Done, forever,
until he wants "advanced".

**What exists.** inference_assignments (10 rows, groups unassigned on
his desk), the Intelligence Router (143), the Model Library (7
artifacts, 7 deployments), the 156 front door's link card, the .43
endpoint law (memory), the assignment editor the owner got lost in.
His words (2026-08-31): "A) Let me download it for you... B) Easy to
then go in and dig into some 'advanced'... This is what matters, man."

**What ships.** ONE screen on the Door's grammar: detect (LAN probe of
known hosts, keychain keys, local GGUF) → propose (one row per
capability group, a beveled picker with the detected candidates first,
the egress host on the row, the count-as-test = a 1-token probe with
latency) → `Use these`. The dual authority (legacy profiles vs the
Model Library) collapses to the library — the model-era collapse the
backlog names. Adjust holds "advanced". MCP twins. The design on the
library first; the canvas; his word.

**Constraints.** Article III (the probe names its host; a cloud key
never crosses the face); no prose; no counters of zero; migrations
minimal (the collapse is additive: profiles become library entries,
tombstones never deleted).

**Size.** M (one screen + the collapse + the probe). **Risk.** The
collapse touches every caller of the legacy profiles — a census first.

### Phase 171 — The Heartbeat (the desk that reaches him)

**Tuesday moment.** 08:05. His Mac shows one notification: "HoldSpeak ·
3 need you across 2 projects." He clicks; the system shade opens with
NEEDS YOU across every Room, the overnight deltas since he last looked,
and the Monday brief already regenerated. He never opened a Room to
learn it.

**What exists.** `needsYou` per Room (169 wire); the SystemShade and the
attention bell (approve-queue, aftercare, corrections — no Room items);
the Monday brief pipeline (ran once, 1839 items); the cadence engine
(0 loops); the conductor heartbeat (five serial loops per minute);
`next_evaluation_at` (null on his watches — the scheduler never stamps
it); the Cocoa presence host with AppKit but NO notification call
(Linux has libnotify); the dock counts for coder sessions.

**What ships.** (a) The scheduler stamps `next_evaluation_at` and the
unattended sweep actually runs (the 164 machinery, now on a cadence he
sets in one row: "every 15 min while I work, hourly otherwise"); (b)
`GET /api/projects/needs-you` — one aggregate across active Rooms; (c)
the shade gains PROJECTS (rows = Rooms with their needs-you count and
the first WHY), the dock badge carries the total; (d) macOS
notifications on the EDGE of that count (UNUserNotificationCenter from
the Cocoa child; quiet hours; per-project mute — the iPad's
quiet-mode precedent); (e) the Monday brief recurs on its own loop and
lands in the shade; (f) a PROJECTS section in ⌘K. The five conductor
loops become parallel with their own failure boundaries.

**Constraints.** Article III (nothing leaves; notifications are local);
Article V (watching is free — these are reads); ledger not gate; every
tick receipted.

**Size.** M. **Risk.** Notification fatigue — the edge rule and quiet
hours are the design, not an afterthought.

### Phase 172 — The Loop Closes (meetings → decisions → commitments → 1:1)

**Tuesday moment.** The standup ends. Within a minute the Room's SINCE
YOU LOOKED reads "Standup · 2 decisions · 3 action items"; NEEDS YOU
gains "Confirm: Marek owns the PostgreSQL migration · by Fri" with
`Confirm` / `Edit` / `Drop`. Before his 1:1 with Ania at 14:00, the
People card reads: "2 PRs waiting on her 3+ days · 1 commitment overdue
· last meeting: 5 items, 2 open." He walks in prepared.

**What exists.** 14 intelligence plugins (never run on his desk); the
follow-through service with provenance (meeting, segment, speaker,
timestamp) and the propose/approve/execute shape; decision_records +
decision_commitments (0 rows); meeting_projects; the Room's DECISIONS &
COMMITMENTS section (169) reading through the meeting link; the 1:1
brief (people_service) computing commitments/agenda/notes; Watch
entities carrying `assignee` (Jira) and `reviewRequests` (GitHub);
People profiles (5) — and NO resolver between a person's name and a
Watch entity's assignee/reviewer. The .43 model for local extraction.

**What ships.** (a) Meeting intelligence runs by default after every
meeting linked to a Room, on the local model (170's assignment), and
its decisions + action items arrive as PROPOSALS in NEEDS YOU (Article
IV: voice arms, it does not fire); `Confirm` writes the decision record
and the commitment through the kernel; (b) the People ↔ Watch resolver
(display name / alias ↔ assignee / reviewer; local, never egressed);
(c) the 1:1 brief and the People card read from Watches + commitments +
meetings — the chief-of-staff loop closed; (d) a meeting's mention of a
repo/issue becomes a SUGGESTED source row in the Room (offered, never
applied); (e) People reachable from the Room and the shade (the 393
gap paid).

**Constraints.** People stays encrypted (the resolver works inside its
boundary); Article V (every extracted item is a proposal); Article III
(local model; the egress chip if he assigns a cloud one).

**Size.** L (the first phase that makes the tagline true). **Risk.**
Extraction quality on the local model — the deterministic fallback is
"here is the transcript segment; you name the decision".

### Phase 173 — The Steward's Hand and Voice

**Tuesday moment.** Monday 18:00 the steward drafted this week's update
from the real deltas — prose a stakeholder can read, every claim with
its ref, unverified claims marked. He edits two sentences and
publishes. Tuesday 09:00 the Room reads "Ania is the review bottleneck
this week: 47 h median, 3 PRs waiting" and the steward asks: "Nudge
her on #612?" — one receipted comment if he says yes.

**What exists.** The steward's six phases with five INTERNAL effects
and zero external writes; the deterministic drafter with the claim
schema (UPD-001/002) and the model drafter as an identity stub
(UPD-003); the eligible-effect policy gate; `reviewRequests`,
`reviewDecision`, `updatedAt` on every PR entity; 16 validated Watch
conditions of which the templates use a subset; `gh` allow-listed for
reads only.

**What ships.** (a) The model drafter — claims preserved, prose
rewritten, unverified marked, the egress chip on the draft; (b)
reviewer-latency and issue-aging derivations at evaluation time
(per-person medians; time-in-status) surfacing as NEEDS YOU rows and
Room tokens; (c) the FIRST bounded external effect: `github.comment`
(the reviewer nudge) behind the policy gate with a terminal receipt and
the comment URL; (d) flaky-CI and merge-queue depth from `branch_ci`'s
history (limit 10) and one search; (e) the release-readiness scorecard
as a Room token row.

**Constraints.** Article V:1 (watching free, acting armed — the effect
kind is opt-in per project); Article XI:2 (admitted, receipted);
Article VI (unverified claims are marked, never smoothed).

**Size.** M–L. **Risk.** The first external write is a constitutional
event — counsel reads it before the owner.

### Phase 174 — Reach (the .43 runner, a third tool, the phone)

**Tuesday moment.** The MacBook is closed overnight; the .43 box on the
tailnet ran the sweep and the drafter; his phone buzzed once at 07:40
with the count; at his desk ⌘K "gov" lands in the Room. His team's
Linear (or Confluence) shows up in SOURCES like GitHub does.

**What exists.** MCP-008's six-story charter (Muad'Dib IV §1b); the
hub's authenticated off-loopback bind; AgentCredentialStore; the
connector grammar (~730 lines per new CLI-backed provider — the census
priced it); the Bonjour mesh + the iPad app's notification center
(dormant track); ⌘K indexing objects without a PROJECTS section.

**What ships.** MCP-008 (Streamable HTTP on the hub, scoped non-OWNER
credentials, egress badges on remote reads, the .43 box as the
overnight runner with its transcript as the live proof); ONE third
connector chosen by his team's reality (Linear via its CLI, or
Confluence via the acli already in hand — never Slack: no CLI, no
relay, the census says structurally hard); LAN companion notifications
via the mesh when the iPad track wakes. 

**Constraints.** Article III (no hosted relay; listener opt-in; badges);
Article XI (bounded delegation, never OWNER); one implementation across
stdio/web/remote.

**Size.** L. **Risk.** Credential surface; the .43 box must stay on the
tailnet.

## 3. What is NOT a phase (adoption, owed to him, not built)

- His own attended walk of the Door and the Room (169's exit).
- Dictation for real sentences and the first correction (the learning
  loop exists; it has never been taught).
- The Thread as a work tool (10 test threads, none for work) and the
  Workbench (1, never run) — 170–172 give them an engine; then a week
  of use decides whether they stay.

## 4. The hygiene lane (folds into every phase)

From the 169 ledger and the census: the per-source Adjust well; steward
settings under sources; park the 167 wings' faces, setup/ and the
`configure-setup` manifest entry; the door window hugging its content;
MCP twins for the door routes; the four legacy-wrapping writes in one
transaction (158 S-1, open since); empty-patch revisions (158 N-1); the
sidecar fetcher seam (165); the second acli account proof (166); the
nine tsc-erroring web files (150); the five conductor loops in
parallel. Each phase's 07 takes the ones its tree touches.

## 5. The recommended order and the first ask

170 → 171 → 172 → 173 → 174. 170 first because every intelligent
feature downstream is starved without it and it is the owner's own
loudest bounce. 171 second because a desk that reaches him changes
Tuesday even before the meetings close their loop. If he wants the
tagline true fastest, 172 may run in parallel with 171 once 170 lands
(different seams: meetings/People vs scheduler/shade).

The first ask of the next sitting: his word on this order — and his
attended walk of 169's door, which every phase above assumes he owns.

## 6. The long arc to 180 (the owner's goal, 2026-09-05)

The owner's words, verbatim: **"Goal set: Fedaykin satisfied all phases
all the way up to 180, delivering all their might into making
HoldSpeak an ultimately useful, beautiful, cohesive system."** — and,
the same night: "Fedaykin need to make a huge UX pass of everything.
Is our canon kept?"

The road, one phase active at a time, each face ratified by him on the
canvas before build, each phase merged on its gates and his word:

| Phase | Name | The Tuesday it buys |
|---|---|---|
| 170 | **The Great Pass** (horizontal) | the face canon written and mechanical; every surface shot and swept at the species; the Concierge and the top Tuesday faces rebuilt to their artboards |
| 171 | The Heartbeat | the desk reaches him: the sweep runs unattended, needs-you across Rooms in the shade and the dock, macOS notifications on the edge, the brief recurring |
| 172 | The Loop Closes | meetings → decisions and action items as proposals → commitments → the 1:1 brief from real signals (the People ↔ Watch resolver) |
| 173 | The Steward's Hand and Voice | the update that writes itself with claim refs; review latency and issue aging; the first bounded external effect (the reviewer nudge) behind the gate with a receipt |
| 174 | Reach | MCP remote on the .43 runner; one CLI-backed third connector; companion notifications over the mesh |
| 175 | The Calendar and the Clock | real calendar events on the desk (the 146 adapter used); scheduled recordings born from events; the meeting Watch adapter; the week as the brief's frame |
| 176 | The Speak Loop | dictation as a daily tool: the correction taught once and kept, the journal as a stream, the voice law on every input, the desk answering the hand |
| 177 | The Thread at Work | the desk chat as a work tool: Draft / Chase / Plan recipes over real Room data; the ask grounded on Watches and the Room; every effect admitted with a receipt |
| 178 | The Portfolio | many Rooms as one desk: a Projects surface, cross-project needs-you in depth, release readiness, dependency alerts, ⌘K to any Room |
| 179 | The Companion | the phone and the iPad as the desk's reach — the Swift recreation from the finished web spec (the standing rule), LAN-only, no relay |
| 180 | The Proof | a measured week of real use on his desk; Gate B partner feedback; the doctor's honest bill of health; the release candidate — "HoldSpeak not really released" becomes released |

Laws that carry the whole road: the Constitution above all; design on the
library before build and his word on the canvas; build what was ratified
(artboard beside shot every round); every verb the library Button; no
prose; no modals; no counters of zero; egress where egress happens;
scoped tests by workers, the gates by the orchestrator; live walks never
beside the parallel suite; scars become laws in UX-CANON.md. The order
of 171–174 may bend to his word after 170's census; 175–180 are named,
not chartered — each is chartered on his word when its turn comes.
