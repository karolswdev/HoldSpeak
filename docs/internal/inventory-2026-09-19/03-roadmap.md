# HoldSpeak — delivery history and what is outstanding

Inventory of `pm/roadmap/holdspeak/` at `main` / `16d78b0b`, 2026-09-19. Read-only.
Machine view: `.githooks/dw check holdspeak` (8 ERROR lines, exit 0) and
`.githooks/dw context holdspeak --compact`.

**Headline numbers.** 82 phase folders numbered >= 100. 774 stories in those
folders: **628 done, 137 backlog, 8 in-progress, 1 blocked**. Of the 137
outstanding, **94 sit in five never-started or parked phases** (121, 177, 178,
179, 180, 190) and **30 sit in Phase 200**.

---

## 0. Three things the roadmap itself gets wrong

Stated up front because they distort every count below.

| Problem | Evidence |
|---|---|
| **The README phase ledger is stale and contradicts the story files.** It lists 110 as `done` (its 7 stories are all `backlog`), 111 as `in-progress`, 150/152/153 as `not-started` (152/153 are 6/6 done), and stops enumerating around 153 — phases 157–200 are absent from the table. | `pm/roadmap/holdspeak/README.md:929-1048` vs `phase-110-the-cohesion/story-*.md`, `phase-152-the-hands/current-phase-status.md:2` |
| **Merged phases still carry unflipped stories.** 170 (03, 05, 07 `in-progress`; 04 `backlog`), 171 (01, 05, 08 `in-progress`; 10 `backlog`), 172 (10 `backlog`), 176 (06 `backlog`) — all merged to main per the handover. The roadmap cannot tell you what shipped. | `phase-170-the-great-pass/current-phase-status.md:37-41`; `phase-171-the-heartbeat/current-phase-status.md:128-137`; `docs/internal/project-rooms/HANDOVER-MUADDIB.md:41-52` |
| **Seven phases are "all stories done, no final-summary"** (152, 153, 154, 156, 200) plus two orphan-evidence errors (101, 170). `dw check` prints all of them. | `.githooks/dw check holdspeak` |

---

## 1. Phase ledger, 100 → 200

"Walked" = did the **owner** exercise it on his own machine. `shots` = he ruled
on screenshots only. `no` = nobody watched him use it.

| # | Name | Status | The one user-visible thing | Owner walked? |
|---|---|---|---|---|
| 100 | The Application Layer | done 13/13 | The desk's UI was judged against four real jobs instead of pixel taste | yes — sitting verdict (`phase-100/final-summary.md:22`) |
| 101 | The Native Innards | **3/4, in-progress since 2026-07-19** | Window interiors stopped looking like "HTML slapped inside a nicer container" | no — closeout sitting never held (`story-04-closeout.md`) |
| 102 | The Refit | **6/7, backlog closeout** | Six named refactors the owner pointed at directly | no (`story-07-closeout.md`) |
| 103 | Foundations & Borrowed Fire | done 7/7 | The desk remembers which windows were open when you closed it | no |
| 104 | Borrowed Fire II: The Watched Hand | done 8/8 | Desk art reforged; agent actions became watchable | **yes** — "Yup. Better. Let's close" |
| 105 | Workbench | done 7/7 | Directories, properties, real object semantics — the desk stopped being a gimmick | partial (chartered from his verdict) |
| 106 | The Kernel | done 10/10 | Every consequential action gets a receipt | **yes** — he drove eight beats, "all passed, make progress" |
| 107 | Close the Side Doors | done 7/7 | Untracked side effects 38 → 15; dictation stayed fast (+25 ms, disclosed) | accepted the latency measurement |
| 108 | The Locked Room | done 7/7 | Typing and terminal access go through one audited door | no |
| 109 | The Long Memory | done 8/8 | Decisions became searchable records; projects remember | no |
| 110 | The Cohesion | **7 stories all `backlog`; status header says done** | The whole desk switched to the opaque Signal Workbench look | shots |
| 111 | The Refinement | done 11/11 | Every program's interior rebuilt for the new look | no — walk was "staged for the owner's sitting" |
| 112 | Enough | done 6/6 | A genuinely fresh install works; 21-shot exhibit | shots |
| 113 | The Forge | **11/15** | The desk became an architect's workspace (composing desk, object lifecycle unbuilt) | no |
| 114 | The Nerve | **0/7 — never executed** | (intended: Ask AI everywhere + egress on every inference path) | n/a |
| 115 | The Polish | done 8/8 | 73 surface violations fixed | no |
| 116 | The Workbench | done 18/19 | Agent workspaces: agent + target + schedule + items, plus a morning brief | no — HS-116-09 walk still `backlog` |
| 117 | The Foundation | done 16/16 | Nothing visible — six internal gravity wells refactored | n/a |
| 118 | The Hopper | **9/10** | Drop a mess in and get work out, without filling a form first | no — "a standing owner-sitting IOU" (`phase-118/current-phase-status.md:12`) |
| 119 | The Revision | done 4/4 | Click-to-toggle mic law; 5 integration regressions fixed | no |
| 120 | The Reckoning | done 11/11 | A full UI audit-and-fix pass: blank pullouts filled, emoji replaced by sprites | no |
| 121 | The Fluency | **0/12 — never executed** | (intended: keyboard-complete paths, universal object verbs, command centre) | n/a |
| 122 | The Backbone | done 12/12 | The desk became scriptable — MCP server, 10 tools | no |
| 123 | The Pipeline | done 13/13 | Every operation goes through one service layer (route bypasses 157 → 2) | n/a |
| 124 | The Observer | done 10/10 | Every service call is recorded and queryable | n/a |
| 125 | The Follow-Through | done 10/10 | Meetings became execution boards — commitments, triage, provenance | no |
| 126 | The Monday Brief | done 9/9 | The desk speaks first: Changed / Broke / Waiting / Decisions | no |
| 127 | The Decision Receipt | done 10/10 | Permanent decision receipts with search and supersession | no |
| 128 | Desk Intelligence | done 10/10 | One pullout showing brief, horizon and intelligence together | no |
| 129 | One Grammar | done 11/11 | One consistent layout grammar across every surface | no — "verdict awaiting the owner's sitting" |
| 130 | One Truth | done 11/11 | The product stopped lying about which model ran and where | no |
| 131 | One Admission Path | done 17/17 | One inference runner owns every AI call and its receipt | no |
| 132 | The Working Desk | done 14/14 | Honest refusals instead of crashes; first green CI | no |
| 133 | The Honest Sidecar | done 11/11 | MCP tools 52 → 82 — the desk drivable from a client | no — "owner sitting pending" |
| 134 | One Owner | done 10/10 | One precedence chain decides where work runs, with provenance | no |
| 135 | The Comfy Chair | done 15/15 | HoldSpeak opens on the Chair — a jobs-first front door | he refined live during the build |
| 136 | Scheduled Recording | done 4/4 | Schedule a recording for a time, one-shot or recurring | no |
| 137 | The One Schema | done 4/4 | Nothing visible — the migration chain replaced by self-reconciling schema | n/a |
| 138 | The People Ledger | done 8/8 | Encrypted local People records and 1:1 commitments | rig walk (55 PASS) |
| 139 | The Settings Reckoning | done 8/8 | Settings cut to seven job-named tiles; 101 controls thinned | no |
| 140 | The First Sentence | **5/6, active** | One obvious first useful act on arrival | **no — the cold walk is the open story**, physical-device legs remain |
| 141 | From Thought to Work | **6/9, active** | Speak a rough thought, develop it, freeze a typed outcome | no |
| 142 | Inference Instrument | done 6/6 | "the old download-and-use verb" a model in one gesture; honest readiness | no |
| 143 | Intelligence Router | done 15/15 | Every AI feature routes through one assignment with fallbacks | no |
| 144 | The Dashboard Door | done 6/6 | The Door board: overdue / now / waiting columns | no |
| 145 | The Door Polish | done 3/3 | The 393-wide board says it scrolls | no |
| 146 | Multiple Calendars | done 7/7 | Many calendars, plus a screenshot-import for a locked-down work calendar | no |
| 147 | One-Tap Record | done 7/7 | See a meeting on the rail, tap Record this once, it arms and follows the event | no |
| 148 | The Menu Grammar | done 6/6 | Amiga-tribute menus instead of a sterile top bar | shots (from his words) |
| 149 | The 1:1 Loop | done 6/6 | Link a 1:1 once; the desk then carries that person's week (PREP lens) | no — "holding for the owner's shot verdict" |
| 150 | Delegation + Chief-of-Staff Brief | done 7/7 | The Door answers "waiting on whom"; the brief reads like a chief of staff | no |
| 151 | Live Intelligence Proof | done 15/15 | record → transcribe → intel → Door → person-brief ran against real models for the first time | no — close held for his attended leg |
| 151b | The Desk Chat: The Thread | done 8/8 | A chat thread you can open from anything on the desk | shots pending |
| 152 | The Hands | done 6/6 (no final-summary) | The thread can call tools — it becomes a manager's hands | no |
| 153 | The Practice | done 6/6 (no final-summary) | Modes, guardrails, annotations and a todo on the thread | no |
| 154 | The Call | done 5/5 (no final-summary) | The thread talks and listens — hands-free voice call state | no |
| 155 | The Crew | **0/5 — never executed** | (intended: a thread delegates to child threads) | n/a |
| 156 | The Front Door | done 8/8 (no final-summary) | First minute: pick pack A/B/C, one confirmation wires everything | **shots — verdict PASSED** |
| 157 | Project Rooms: The Contract | done 5/5, merged #521 | Nothing visible — the Room data contract | n/a |
| 158 | The Room | done 6/6, merged #522 | A Project Room you can open | shots — bounced r1, PASS r2 |
| 159 | The Interview | done 7/7, merged #523 | Answer questions, get a configured project | shots — PASS on round 4 after two bounces |
| 160 | The Delta | done 8/8, merged #524 | "What changed since you looked" with evidence | shots — PASS first sheet |
| 161 | The GitHub Watch | done 7/7, merged #525 | A real GitHub watch on a Room, live | shots — "PASS, close it" |
| 162 | The Update Factory | done 7/7, merged #527 | Draft a project update whose every claim links to evidence | shots — PASS round 4 |
| 163 | The Steward's Hand | done 7/7 | Press once, five real effects happen, each receipted | no |
| 164 | The Unattended Desk | done 7/7 | Two scheduled runs completed with nobody home | no |
| 165 | The MCP Family | done 7/7, merged #531 | An MCP client can drive the whole Room scenario | **"PASS"** (his verdict on the transcript) |
| 166 | The Jira Parity | done 7/7, merged #532 | Jira joins GitHub as a real connected source | live rig on his real acli/site |
| 167 | The Room in Use | done 8/8, merged #549 | His first real project lives in a Room | **no** — "Walk it later — close on the dry run" |
| 168 | The Connections Door | done 7/7 | Settings → Connections: one state, one verb per tool | **YES — and he BOUNCED it** (2026-09-04) |
| 169 | The Streamlined Door | done 7/7, merged #551 | A one-screen Door; the Room as four questions | no — merged on trust, walk owed |
| 170 | The Great Pass | merged #553 (**4/7 flipped**) | The whole desk re-faced to a written UX canon; the Concierge model front door | **no — HS-170-05 is his walk, still `in-progress`** |
| 171 | The Heartbeat | merged #554 (**6/10 flipped**) | macOS notifications: "3 need you across 2 projects" | **no — HS-171-08 still `in-progress`** |
| 172 | The Loop Closes | merged #555 (9/10) | A finished meeting produces confirmable decisions and commitments | no |
| 173 | The Steward's Hand and Voice | merged #556, 9/9 | The steward drafts the weekly update and nudges a reviewer | no |
| 174 | Reach | merged #557, 11/11 | Reach the hub from the tailnet; overnight runs on the .43 box | no |
| 175 | Calendar and the Clock | merged #558, 9/9 | The week strip, `NEXT · …`, recordings that arm 5 min before an event | no — walk owed |
| 176 | The Speak Loop | **7/8, PR #566** | Teach a dictation correction once; it applies to the next matching sentence | **no — HS-176-06 is his walk, `backlog`** |
| 177 | The Thread at Work | **0/8 — PARKED behind 200** | (intended: Draft/Chase/Plan over real Room data) | n/a |
| 178 | The Portfolio | **0/10 — PARKED** | (intended: many Rooms as one portfolio) | n/a |
| 179 | The Companion | **0/11 — PARKED** | (intended: phone/iPad as the desk's reach) | n/a |
| 180 | The Proof | **0/10 — folded into 200's G5** | (intended: a measured week of real use) | n/a |
| 190 | Continuity Contracts (CF-0) | **0/14, 01 blocked on owner ratification** | (intended: one durable contract layer for memory/custody) | n/a |
| 200 | The Working Practice | **23/53, in build** | The desk used as a daily practice: prepare, meet, review, recall | **no — every walk "accepted, not observed"** |

---

## 2. Outstanding work, by phase

### 2a. Stale-but-open legacy stories (all pre-156)

| Phase | Story | Purpose |
|---|---|---|
| 101 | HS-101-04 `in-progress` | The closeout sitting for the window-interior work |
| 102 | HS-102-07 `backlog` | The closeout sitting for the six refactors |
| 110 | HS-110-01..07 `backlog` | The whole material pivot's stories were never flipped (the work shipped) |
| 113 | HS-113-12..15 `backlog` | Composing desk, creation flow, object lifecycle, discoverability — "substantially absorbed by later phases; re-audit before resuming" (`phase-113/current-phase-status.md:3-8`) |
| 114 | HS-114-01..07 `backlog` | Seeded nerve, Ask-AI first class, per-destination probe, egress everywhere, editor proposals, honest target, the walk — **zero commits ever existed**; gaps "largely closed elsewhere" (`phase-114/current-phase-status.md:3-9`) |
| 116 | HS-116-09 `backlog` | The Workbench walk |
| 118 | HS-118-10 `backlog` | The Hopper walk — the standing owner IOU |
| 121 | HS-121-01..12 `backlog` | The whole Fluency phase: kit, one footer, the door must open, safe hands, keyboard-complete, windowcraft, universal verbs, command centre, live desk truth, recovery, egress+confirm, the walk. **Never executed**; several items shipped elsewhere |
| 140 | HS-140-06 `active` | The cold walk — glass and local gates pass; physical-device recovery legs remain |
| 141 | HS-141-07..09 `backlog` | Typed outcomes not magic; one real tool; the thought-to-work walk |
| 155 | HS-155-01..05 `backlog` | The Crew: `chat.subthread`, the conductor, notifications, the child on the desk, the walk |

### 2b. Merged phases with unflipped stories (bookkeeping, not work)

170 (03 Concierge, 04 top faces, 05 **his walk**, 07 close) · 171 (01 design, 05 notifications, 08 **his walk**, 10 close) · 172 (10 close) · 176 (06 **his walk**). Of these, only the three walk stories are genuinely outstanding user-facing work.

### 2c. Parked arcs

| Phase | Stories | Purpose |
|---|---|---|
| 177 The Thread at Work | 01..08 | The desk chat becomes a work tool over Room data |
| 178 The Portfolio | 01..10 | Many Rooms aggregated: cross-project needs-you, release readiness, command deck |
| 179 The Companion | 01..11 | Swift phone/iPad recreation of the finished web spec, LAN-only |
| 180 The Proof | 01..10 | A measured week of real use; Constitution audit; release candidate |
| 190 Continuity Contracts | 01 `blocked`, 02..14 `backlog` | Domain grammar, command core, source spine, private-material vault, remove-and-forget, memory contract shell |

### 2d. Phase 200 — the live one

**Done (23):** 01–17, 41–46.
**Outstanding (30):** 18–40 and 47–53.

Gate structure (`phase-200/current-phase-status.md:25-30`):

| Gate | Stories | State |
|---|---|---|
| G0 Known and recoverable installation | 01-05, 44-46 | **closed 2026-09-19** — 05 on an owner *acceptance*, not a walk |
| G1 Trustworthy daily Project work | 06-16, 41-43 | **story set complete**; 16's attended leg accepted, not observed; gate box still unticked |
| G2 Configurable working practice | 17-23 | 17 done; 18-23 open. **Cannot close before a G4 story lands** |
| G3 Supervised assignments | 24-30 | all open |
| G4 Bounded unattended execution | 31-36, 47-53 | all open; 47-53 is "G4's substance" |
| G5 Adopted release | 37-40 | all open |

Outstanding stories, one line each:

| ID | Purpose |
|---|---|
| 18 | Turn Interview intent into a reviewable setup plan |
| 19 | Apply and recover multi-service recipe setup |
| 20 | Make Interview revisits fast and reliable |
| 21 | Run a configured brief through an existing cadence |
| 22 | Integrate the calendar work daily recipes need |
| 23 | Complete the ten-workday daily-practice pilot |
| 24 | Review the Assignment boundary and pick the first adapter |
| 25 | Persist immutable assignments and canonical run links |
| 26 | Launch one bounded supervised worker |
| 27 | Verify results against the frozen acceptance contract |
| 28 | Make assignment progress and intervention usable |
| 29 | Prove assignment recovery, cancellation and scope change |
| 30 | Prove five supervised assignments on useful tasks |
| 31 | Choose and prove the durable execution host |
| 32 | Scoped credential lifecycle for recurring work |
| 33 | Bind triggers to versioned recipes and assignments |
| 34 | Leases, bounded retry, missed-run policy |
| 35 | Bounded unattended preparation and analysis |
| 36 | Prove unattended operation through real occurrences and restart |
| 37 | Review net value and decide the next investment |
| 38 | Package the verified product and recovery procedures |
| 39 | Rehearse the release without implementation guidance |
| 40 | Close Phase 200 on outcomes and release evidence |
| 47 | A schedule knows its own zone instead of following the hub's clock |
| 48 | A practice recipe is nameable as scheduled work |
| 49 | A scheduled recipe binds its Project and its source scope |
| 50 | A due occurrence reaches the declared executor, not the inference waist |
| 51 | The occurrence's result lands in the Project as the declared record |
| 52 | A surface can create a recurring binding that actually recurs |
| 53 | One real occurrence, on the real clock, with a receipt |

**Chartered 16..53?** All of 18–40 were chartered with the phase (2026-09-06, PR #563). 41–46 were chartered mid-phase from the operational audit; **47–53 were chartered 2026-09-18 night** (`current-phase-status.md:101`).

**Stated dependency order for 47–53, verbatim** (`current-phase-status.md:101`):

> 47 (the zone, startable now, independent of everything) and 52 (the create surface, startable now) in parallel; then 48 (the namespace) → 49 (Project + scope) → 50 (the executor) → 51 (the output) in series, because each one needs the frozen terms the one before it defines; then 53, the first real occurrence, which needs all five of the clock stories. **Only 47 and 52 can start today.**

**Ready to start right now:** **HS-200-47** and **HS-200-52**. Also independently startable: **HS-200-18** (design ratified per `current-phase-status.md:57`) and **HS-200-24** (a design/decision story depending only on 01). Everything in G3/G5 is gated behind 24 or behind the G2/G4 pilots.

One inherited contradiction 50 must settle: 17's `SCHEDULED_TRIGGER_OWNER` names the connector-watch chain as the recurring owner, but that chain is change-driven, not periodic (`holdspeak/services/watch_service.py:1291-1292`).

---

## 3. Promises vs use

Sources for "used by the owner": `docs/internal/OPERATIONAL-SURFACE-AUDIT.md:186-215` (read-only census of his live DB, 2026-09-13) and `pm/roadmap/holdspeak/THE-TUESDAY-ARC.md:12-29` (census, 2026-09-05). "Accepted not observed" (the 2026-09-19 ruling) counts as NOT used.

| Feature / pillar (POSITIONING) | Built? | Walked by a rig? | Used by the owner? | Source |
|---|---|---|---|---|
| **P1 — Everything local, including the intelligence** | yes | yes | **partly** — `inference.invoke` 147 on his desk; but his dictation engine is a cloud engine with no key set | `OPERATIONAL-SURFACE-AUDIT.md:189`; `BACKLOG.md` AG "his dictation engine is a cloud engine without a key" |
| Dictation → types anywhere (the headline mode) | yes | yes | **yes, lightly** — `dictation.session` 35, `desktop.type_text` 30; his hand on the hotkey observed once, 2026-09-08 | `OPERATIONAL-SURFACE-AUDIT.md:189`; `phase-200/current-phase-status.md:99` |
| **P2 — It learns how you work (correction memory, learning digest, replay)** | yes (176) | yes | **NO** — `dictation_corrections` **0**; "the learns-how-you-work loop untrained" | `THE-TUESDAY-ARC.md:19` |
| Dictation journal | yes | yes | yes (rows exist; one blank-transcript row found on his desk) | `BACKLOG.md` AG walk finding |
| **P3 — Meetings end with their loops closed** | yes | yes | **NO** — 7 meetings (5 empty, longest 30 s); `intel_snapshots` **0**; 1 meeting session ever, cancelled | `OPERATIONAL-SURFACE-AUDIT.md:193-195` |
| Meeting intelligence (14 plugins) | yes | yes | **NO — never run on his desk** | `THE-TUESDAY-ARC.md:16-17` |
| Decision records / receipts (109, 127) | yes | yes | **NO** — `decisions 0 · decision_records 0 · commitments 0` | `OPERATIONAL-SURFACE-AUDIT.md:196` |
| Meeting import / archive search | yes | yes | not evidenced | — |
| Actuators (propose → approve → execute) | yes | yes | not evidenced | — |
| **P4 — Honest by construction (`doctor`, honest counts)** | yes | yes | n/a — passive | `POSITIONING.md:75-84` |
| The Desk as the one front door | yes | yes | yes — it is what he opens | `POSITIONING.md:86-131` |
| Project Rooms (Door → Room → Watch) | yes | yes | **yes, the one live surface** — 10 projects (9 archived walk seeds, **1 active**), 5 updates, 12 observations | `OPERATIONAL-SURFACE-AUDIT.md:195` |
| Watches (GitHub + Jira) | yes | yes | **partly** — 32 watches, 30 enabled, **2 armed**, `watch_effects` **0** (HS-200-43 fixes arming; not yet on his hub) | `OPERATIONAL-SURFACE-AUDIT.md:197` |
| Steward (unattended runs) | yes | yes | **NO** — 9 policies, all unattended disabled | `OPERATIONAL-SURFACE-AUDIT.md:198` |
| Heartbeat / notifications (171) | yes | yes | **effectively NO** — 724 sweeps, 718 notify ops, **1 notification ever sent** | `OPERATIONAL-SURFACE-AUDIT.md:186-188` |
| Monday brief (126, 150, 171) | yes | yes | **NO** — ran **once**, 2026-08-19 | `OPERATIONAL-SURFACE-AUDIT.md:199` |
| Cadence / scheduled work (136, 164, 171) | yes | yes | **NO** — `cadence_nudges 0`, both loops killed, `cadence.enabled = False` | `OPERATIONAL-SURFACE-AUDIT.md:198,203` |
| Calendar + one-tap record (146, 147, 175) | yes | yes | **NO** — `calendar_events 0`, `calendar.sources = []`, `meeting.auto_record = off` | `OPERATIONAL-SURFACE-AUDIT.md:199,205-206` |
| People / 1:1 loop (138, 149, 172) | yes | rig (55 PASS) | **NO** — `speakers 0`, no 1:1 evidence | `OPERATIONAL-SURFACE-AUDIT.md:199` |
| Desk Chat / Thread (151b–154) | yes | yes | **NO** — 10 threads, **all messages on 2026-08-31**; `tool_turns 0` | `OPERATIONAL-SURFACE-AUDIT.md:200-201` |
| Interview (159, 200-18..20) | yes | yes | **NO** — `interview_sessions 0`; its face is parked | `OPERATIONAL-SURFACE-AUDIT.md:200`; `:69` |
| MCP sidecar (133, 165, 200-45) | yes (222 tools) | yes | yes — but it is a second unlocked writer on his live DB | `OPERATIONAL-SURFACE-AUDIT.md:406-412` |

Two caveats the audit itself makes: several zeros are **config, not breakage** (`cadence.enabled = False`, `meeting.auto_record = off`, `calendar.sources = []`), and **his hub runs code from before the 200-10 merge** — schema v77, no `context_promotions` table: "the newest surface has never touched his machine" (`OPERATIONAL-SURFACE-AUDIT.md:209-211`).

---

## 4. The owner's recorded confusion, bounces and rejections

| Date | What he said / what confused him | Fix phase | Shipped? |
|---|---|---|---|
| 2026-07-19 | "a lot of the windows you made? Still feel like a bunch of HTML slapped inside a 'nicer' (still not nice enough) looking container" | **101 The Native Innards** | built 3/4; **closeout sitting never held** (`phase-101/current-phase-status.md:5-9`) |
| 2026-07-31 | Accepted 110's material pivot only on condition of an immediate refinement fast-follow | **111 The Refinement** | 11/11 done; his walk never held (`phase-111/final-summary.md:2-4`) |
| 2026-08-17 | "setup flows must be joyful — ugly-but-lawful is rejected" | standing law, UX-CANON rule 12 | in force (`docs/internal/UX-CANON.md:48`) |
| 2026-08-18 | "HoldSpeak has become too complex for the value it asks a new person to find" — ordered the cut, cancelled the Dashboard Door | **140 The First Sentence** | 5/6; the cold walk is still open (`phase-140/current-phase-status.md:5-12`) |
| 2026-08-29 | "a little too sterile… a tribute to the incredible Amiga OS… the top menu toolbar… really poor, right?" | **148 The Menu Grammar** | done 6/6 (`phase-148/final-summary.md:4-6`) |
| 2026-08-31 | The co-creator got lost in Settings → Models — "he doesn't know how to use this product"; his ask: "A) Let me download it for you… B) Easy to then go in and dig into some 'advanced'" | **156 The Front Door**, then **170-03 The Concierge** | 156 done 8/8, shot verdict PASSED; 170-03 built but **still `in-progress`** and never walked (`THE-TUESDAY-ARC.md:22-23`, `:60-70`) |
| 2026-08-31 | "didn't we get rid of the whole compat kind of thing with that big revolution?" — the backend still runs two model eras | model-era collapse, parked in BACKLOG | **NOT shipped** (`BACKLOG.md:1077-1092`) |
| 2026-09-04 | **"I still… get pretty upset around how unintuitive it is to configure the connectors… Even myself — I got confused. Not good, not good."** | **168 The Connections Door** | done 7/7, then **he walked it and BOUNCED it again** (`phase-168/story-05-the-tuesday-walk.md:81`) |
| 2026-09-04 | Bounced 168's door and Room: "still not streamlined at all"; "that interface I really didn't honestly like and/or understand" | **169 The Streamlined Door** | done 7/7, merged — **on trust, not on a walk** (`phase-169/story-05-the-walk.md:67`) |
| 2026-09-19 | "all walks may be considered as passed" | — | closes the stories; explicitly an **acceptance, not an observation** (`phase-200/current-phase-status.md:97-99`) |

Counsel bounces (design and built) are routine and mostly paid in-round: 176 design + built, 200-09, 200-10, 200-11, 200-15, 200-17, 200-45. They are process, not owner confusion.

---

## 5. Parked and superseded

| Item | One line |
|---|---|
| BACKLOG **M** — dictation preview-before-commit | "Show me what you're about to type" for high-stakes targets — parked (`BACKLOG.md:253`) |
| BACKLOG **N** — Windows port | **Rejected by the owner:** "Absolutely not. Not by me." (`BACKLOG.md:257`) |
| BACKLOG **R** — Apple Core AI provider | Parked, toolchain-blocked; the durable answer to the llama.cpp treadmill (`BACKLOG.md:366`) |
| BACKLOG **W** — Jira Desk Sync | Plan filed, never chartered (`BACKLOG.md:608`) |
| BACKLOG **X/Y/Z** — control-posture completion, physical-proof program, Desk-OS owner leg | Owner-evidence programs, all open |
| BACKLOG **Z (Candidate)** — The Inherited Ledger | 96 backend repairs + walk deepening, filed at the 129 sitting (`BACKLOG.md:304`) |
| BACKLOG **AG** — Phase 176 remainders | 16 counsel P2s + two walk findings, incl. **his Speak face reads `KEY NOT SET`** (`BACKLOG.md:1032`) |
| BACKLOG **AI** — Phase 200 G0 remainders | 3 real code defects the 2026-09-19 ruling closed the *story* on but not the *gaps* (`BACKLOG.md:1056`) |
| BACKLOG **AJ** — Phase 200 audit remainders | `bind_host` is decorative, no CIDR check anywhere; verb catalog 45 of 67 with no parity test (`BACKLOG.md:1068`) |
| **Model-era collapse** | Two parallel model authorities still run side by side in the backend; charter never taken (`BACKLOG.md:1077`) |
| Phases **114, 121, 155** | Chartered, zero commits, never executed |
| Phases **177, 178, 179** | Parked behind 200 on the owner's line in the sand, 2026-09-06 |
| Phase **180** | Folded into 200's G5 |
| Phase **190** | Council-ratified charter, 0/14, story 01 blocked on owner ratification; "not on the road" |
| Phases 113 (12-15), 114 | Audit found them "substantially absorbed by later phases; re-audit before resuming" |

---

## 6. What the roadmap says next vs what the history says he needs

### What the roadmap literally says next

1. `.githooks/dw next holdspeak` returns **HS-91-10** ("DeskOS parity walk, UAT, docs, and close") — a phase-91 story left `in-progress` since the React migration. This is noise: the tool walks numerically and 91 is stale.
2. The README's current-phase pointer: **Phase 200 The Working Practice** (`README.md:599`).
3. The only stories the status doc says can start today: **HS-200-47** (a schedule knows its own zone) and **HS-200-52** (a surface can create a recurring binding that actually recurs) — in parallel; then 48 → 49 → 50 → 51 in series; then 53 (`phase-200/current-phase-status.md:101`).
4. Behind those, G2's 18–23 (Interview → setup plan → apply → revisit → scheduled brief → calendar → ten-workday pilot).

### What the delivery history actually says he needs

**Blunt reading: the product has been built for a user nobody has watched.**

**1. Nobody has watched the owner use this product in fifteen months of phases.** The last time he walked a face himself on his own desk was **2026-09-04 (Phase 168) and he bounced it**. Since then: 169 merged on trust; 170, 171, 172, 173, 174, 175, 176 all carry "attended walk OWED"; Phase 200's G0 and G1 both closed on the ruling "all walks may be considered as passed", which the evidence itself labels *accepted, not observed* (`phase-200/evidence-story-16.md:121`, `PILOT-R1.md:30`). Three walk stories are still literally open in merged phases (170-05, 171-08, 176-06). **Every quality signal in this roadmap since 2026-09-04 is machine-derived.**

**2. The census says the shipped feature set is unused, and the reasons are mostly config and reach, not missing features.** `intel_snapshots 0`, `decision_records 0`, `commitments 0`, `cadence_nudges 0`, `calendar_events 0`, `interview_sessions 0`, `dictation_corrections 0`, 1 notification ever, Monday brief ran once (`OPERATIONAL-SURFACE-AUDIT.md:186-206`). Phases 172, 173, 175, 176 and 149/150 built directly on top of those zeros. The honest cheapest next move is not story 47 — it is **turning on the four settings that are off and putting one real week of his data through the loop** (`cadence.enabled`, `calendar.sources`, `meeting.auto_record`, `meeting.intelligence_auto`), then watching what breaks. That is what HS-200-23 and `PILOT-R1.md` describe, and **R1 has not begun** (`current-phase-status.md:97`).

**3. His hub is running pre-200-10 code.** Schema v77, no `context_promotions` table — "the newest surface has never touched his machine" (`OPERATIONAL-SURFACE-AUDIT.md:209-211`). Whatever the last twelve stories shipped, he has not seen any of it. An upgrade of his actual hub outranks every backlog story.

**4. The two things he personally complained about are the two things still not finished.** Connector configuration confused him twice (168 bounce, 169 built-on-trust and never walked by him). The models door lost his co-creator (`feedback_owner_lost_in_models_settings`); the Concierge that answers it — **HS-170-03 — is still marked `in-progress` on main**, and the model-era collapse he asked about on 2026-08-31 is parked in the backlog. Meanwhile his Speak face reads `KEY NOT SET` on his own desk (`BACKLOG.md` §AG), which means **the flagship dictation mode is inert on the owner's machine right now**.

**5. Phase 200 is a 53-story program whose own top risk is "feature delivery outruns owner use" — likelihood High** (`current-phase-status.md:573`). G3 (supervised assignments, 7 stories) and G4 (unattended execution, 13 stories) build autonomy on top of a daily loop that has never run for a day. The risk register's own stop signal — "new scope displaces an observed daily blocker" — has already fired: 47–53 were chartered the night of 2026-09-18 while the R1 pilot sat unstarted.

**Recommended order, against the roadmap's:** (a) upgrade his hub and flip the four off switches; (b) run R1 for one real week and record what he actually touches; (c) pay HS-170-03 / the model-era collapse so a model is assigned and dictation works on his machine; (d) then 47/52 and G2. Stories 24–36 should not start until (b) produces a number.
