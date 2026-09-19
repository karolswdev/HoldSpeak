# The Inventory — 2026-09-19

**What this is.** A full inventory of HoldSpeak on `main` at `16d78b0b`
(everything merged, nothing outstanding), taken the day the owner said:
*"we've added a shit-ton of things, but I still fail to understand most
of it from a usability perspective."* Five workers swept the faces, the
capabilities, the roadmap, the docs, and the owner's real desk (read-only).
Their full reports are the appendices in `inventory-2026-09-19/`. This
document is the synthesis and the plan.

**The one-paragraph answer.** The product is real, large and mostly
honest on the machine side: 693 routes, 225 MCP tools, 118 capabilities,
only 3 dead. The owner uses exactly one of them daily (dictation). The
rest has near-zero traffic, not because it is missing, but because
**(a) the faces do not lead to it** (the Project Room, the centrepiece of
ten phases, is reachable from one invisible keystroke because every
visible route to it is a silent no-op), **(b) the same question has two
answers and the one on screen is not always the one that ran** (two
model stacks, two config roots, three screens called "Models", five
"run a thing" primitives, fifteen background loops with no roster), and
**(c) nobody has watched the owner use it since 2026-09-04**, and that
walk was a bounce. The plan below is one arc, five phases, in the only
order that makes the product usable: make it reachable, make it
one-answer, make it visible, make it runnable, then put one real week
of his life through it and watch.

---

## 1. State of the tree

| Item | State |
|---|---|
| Branch / commit | `main` @ `16d78b0b`, clean, equal to `origin/main` |
| Open PRs | **none.** PR #583 (HS-200-16, the two-day loop) was the last; merged today on verification (its 4 red checks were a subset of main's 6) |
| Phase-200 branches | 42, 43, 11, 12, 14, 15, 44, 45, 46, 05, 17, 18, 16 — **all merged** |
| CI on `main` | **RED** — 6 tests: `test_transcriber_init_race::test_boot_warm_is_reused_by_a_legacy_dictation`, `test_phase200_task_resume::test_custody_survives_the_database_file_being_recreated`, `test_phase200_ci_isolation::test_the_running_suite_is_itself_isolated`, `test_hs153_practice_glass::test_guardrail_row_renders_and_deny_focused`, `test_hs200_task_resume_glass` ×2 (a saved ask survives a hub restart; the custody token at 1440) |
| Worktrees | 28 registered; 2 prunable (`wt42`, `wt43`); the `muaddib-xx`/`xxiii` and `.claude/worktrees` sets are all merged branches and can be removed |
| Local branches unmerged | 27, all pre-156 or agent scratch (`agent/hs-113-*`, `phase-130*`, `hsm-*`); none is live work |
| Roadmap bookkeeping | 12 unflipped stories in merged phases (170, 171, 172, 176); 5 phases with all stories done and no final-summary; README phase table stale past ~153; `dw next` returns HS-91-10 (stale) |

The owner's desk: the 138 MB history was moved by the owner to
`~/.local/share/holdspeak/retired-2026-09-19/` at 12:12 today and the hub
restarted on a fresh DB (schema v79, current code). A month-old MCP
sidecar (PID 55661, since 2026-08-26) still holds three read-write
handles on the retired file. Kill it before it writes anywhere.

---

## 2. The product by the numbers

| Layer | Count | Of which reachable by a human from a screen |
|---|---|---|
| HTTP routes | 693 | 525 called by the web desk, 89 by iOS, **136 by nothing** |
| MCP tools | 225 in 20 families | whole families with no face: heartbeat, desk-level watches, practice recipes, scheduled-recording list/update/delete, cadence run-now |
| Capabilities (grouped) | 118 | **62 with a face, 38 partial, 15 headless, 3 dead** |
| Services | 112 modules | — |
| DB tables | 220 (249 on disk) | — |
| Background loops | 15 (4 conductors + heartbeat + 10 more) | **no roster anywhere**; 3 visible only in log lines; 3 with no ownership gate |
| Config leaf keys | 112 in `config.json` + 9 separate stores in a second root | ~33 hidden behind RAW folds |
| Mechanisms that can pick a model | **29**, in 3 stacks, arbitrated by a table with no face | 16 concepts to answer "which model runs my meeting summary?" |
| Web "applications" | 22 | **5** on the dock, 4 menu words, the rest behind ⌘K |
| Real routes | **3** (`/`, `/welcome`, `/presence`) | 15 demoted paths redirect to `/`; any unknown URL lands on `/` silently |
| Canonical feature names (POSITIONING) | 73 | 10 doc-canonical names render nowhere; 13 UI labels are declared nowhere |
| Docs | ~130 files | generated references exact; the clone-to-desk path documented **nowhere** |
| Phases ≥100 | 82 folders, 774 stories | 628 done · 137 backlog · 8 in-progress · 1 blocked |

---

## 3. What the owner actually uses (the retired DB, Aug → today)

| Thing | Count | Read |
|---|---|---|
| Dictation | 19 sessions, 31 typed deliveries, last **09:26 today** | **the one live surface** |
| Meetings | 9, ~83 s of audio total, 4 stuck `recording` since Aug | never a real one end to end |
| Intel snapshots | **0, ever** | queue drains every 15 s since HS-200-42; **every claim refused** by a dangling profile id `legacy-legacy-intel` (the known double-prefix scar); meeting sessions refused admission too. The fresh DB has no legacy migration, so this defect may be gone with the wipe. Unverified until a meeting runs. |
| Decisions / commitments / follow-through | 0 / 0 / 0 | the payoff of phases 109–127–172–200 has never fired once |
| Rooms | 1 active (32 sources), 5 updates, 3 steward runs (09-03/04) | the one thing besides dictation he touched |
| Watches | 32; 4 armed; 5 evaluations ever; **0 effects** | arming fixed by 43 but the only path that mints an armable watch is inside the parked Interview (HS-200-52) |
| Heartbeat | 1,270 sweeps, 1,264 notify ops, **1 notification ever** | runs; says nothing |
| Cadence | 2 loops, both `killed`; `cadence.enabled=false`; no settings route | off |
| Calendar | `calendar.sources=[]`, 0 events | phase 175 never had a source |
| People ledger | 0 rows, ever | phases 138/149/172 unused |
| Threads / chat | 10 threads, last message 2026-08-30 | dormant |
| Monday brief | 1, 2026-08-19 | once |
| Interview | 0 sessions; face parked | unused |
| Corrections | 0 | the "learns how you work" pillar untrained; owner: "not my use case" |
| Log | 41 MB; ~148,000 `ignoring unknown key` warnings from keys the product wrote; 42,417 rejected WebSocket handshakes every 12 s from an orphan tab; wake word on, dependency broken | noise |

**Verdict:** a very large surface with one pulse. Three counts would have
to move for "I use this on a Tuesday": `intel_snapshots > 0`, a real
meeting weekly, `decisions > 0`. A fourth, nearly free: one calendar
source.

---

## 4. Why it is not usable — the five reports converge

### 4.1 The faces do not lead anywhere (appendix 01)

1. **Every on-face route into the Project Room is a silent no-op.**
   Eight call sites call `openSurfaceOr("project-room", "/projects", …)`;
   `project-room` is not a registered surface key (the keys are the
   application `action`s in `web/src/desk/applications.ts`, and no alias
   maps it), `/projects` is not a route, the `*` catch-all navigates to
   `/`. Sites: `ChairHome.tsx:542, 555, 1323, 1460`,
   `SystemShade.tsx:450, 586`, `RecallFace.tsx:84`,
   `MeetingReview.tsx:272`. The only working opener is ⌘K
   (`DeskToolShelf.tsx:253`, key `open-project-memory`, scope
   `project:<id>`). Tests assert the call, not the result. **Verified by
   the orchestrator, not just the worker.**
2. **"Open" on a meeting from the arrival opens Meetings with nothing
   selected** (`ChairHome.tsx:1743` passes a bare id; `HistoryCore.tsx:40`
   wants `meeting:<id>`).
3. **There is no navigation.** 22 applications, 5 dock icons, 4 menu
   words, and the only complete index is ⌘K, an invisible keystroke.
4. **The cold arrival is a dead end.** Every section is `length > 0 ?
   … : null`; a fresh desk shows a headline, "No brief yet / Generate"
   (which runs against no model and no data), and four capture verbs over
   550 px of black. No Project verb, no model warning, no next step.
5. **"New Project" is floor-scoped** and the default surface is the
   Chair, so the verb that creates the central object is invisible from
   the default screen.
6. **The model prerequisite is discovered four times, announced never.**
   `AI needs a model`, `MODEL · NOT SET`, `NO MODEL`, `No model
   configured` — and nothing on the arrival. The Concierge cold state is
   `7 GROUPS · 7 WAITINGS` and a disabled `Use these`.
7. **"Models" names three screens** (Concierge window, Settings→Models
   module, Model Library); "Context" has five meanings; "Cadence" two;
   the Settings module for cadence is called **Rhythm**; "Desk memory"
   is both the bell and a window that is six faces depending on scope.
8. First launch **seeds 21 objects unasked** on every exit path of
   FirstWords; the deliberate Seed verb is on the Floor, which arrival
   forces off.
9. Seven of twenty primitive kinds (incl. `project`, `workbench`) fall to
   a `FallbackPullout` with no content and no verbs.
10. Dev surfaces ship: the Components catalog, RAILS/Delivery/Roadmap/Story
    objects from the PMO tooling.

### 4.2 Two answers to every question (appendix 02)

1. **Two model-selection stacks** (plus a third for speech), arbitrated
   by `inference_assignment_migrations` rows with no face; 29 mechanisms.
2. **The meeting host badge is computed from the stack that does not
   run** (`meeting_intel_service.py:82-90` vs
   `meeting_deferred_queue_binding.py:133`): a LAN assignment shows
   `local` while the run egresses to 192.168.1.43. A truthfulness defect
   in the one place the Constitution forbids one (Article III).
3. **SERVICE principals are default-deny to group scope**, so a
   `meetings` group assignment set in the editor is invisible to the
   meeting queue; the editor shows green for a row that does nothing.
4. **Five writers of group assignments, last-writer-wins, no `set_by`**:
   re-running the Concierge silently stomps a hand edit.
5. **Two config roots** (`~/.config/holdspeak/` and nine stores under
   `~/.holdspeak/`), plus `~/.local/share/holdspeak/` and the HF cache;
   nothing names the split. Two independent `settings.hub`
   implementations (web vs MCP) have already drifted.
6. **Five "run a thing" primitives** (recipes, chains, workflows,
   workbenches, practice recipes) plus reactions and automations; a
   practice recipe cannot even be named as scheduled work (HS-200-48).
7. **Fifteen loops, no roster.** Nowhere to see what runs on your
   behalf; three loops write under `HOLDSPEAK_ALLOW_UNOWNED_DB` while the
   hub prints "scheduled work OFF" (one of them starts recordings).
8. `desk.verb` is a catalog of refusals (5 dispatchable verbs, empty
   intersection with the UI's 67); `desk_snapshot` advertises layout and
   returns none.
9. Only path that mints an armable watch is `create_from_setup`, behind
   the parked Interview.
10. Dead: `review_claim`, `/api/model-profiles` (8 routes, 0 callers),
    8 of 10 repository write routes.

### 4.3 Built for a user nobody watched (appendix 03)

- Last owner walk on his own desk: **2026-09-04, Phase 168, bounced.**
  169 merged on trust; 170–176 all "attended walk OWED"; 200's G0 and G1
  closed on the 2026-09-19 ruling, which the evidence labels *accepted,
  not observed*. Every quality signal since 09-04 is machine-derived.
- The two things he personally complained about are the two still not
  finished: connector configuration (168 bounced, 169 never walked) and
  the Models door (HS-170-03 still `in-progress` on main; the model-era
  collapse parked in BACKLOG).
- Phase 200's own top risk ("feature delivery outruns owner use",
  likelihood High) has fired: 47–53 were chartered the night of 09-18
  while the R1 pilot sat unstarted. G3 (7 stories) and G4 (13) build
  autonomy on a daily loop that has never run for a day.
- Positioning pillar 2 (learns how you work) and pillar 3 (meetings end
  closed) have **zero** owner use. Pillar 1 partly (dictation on a cloud
  engine with `KEY NOT SET` on his Speak face at last census).

### 4.4 Documented for someone who already has it running (appendix 04)

- The hub port is **random every boot**, no `--port` flag; the four env
  vars that make it operable (`HOLDSPEAK_WEB_PORT/HOST/URL/TOKEN`) are in
  no user guide.
- `holdspeak doctor` runs the **hub** doctor, discards `--strict` and
  `--connectors`, probes `:8765` (never bound) and reports `4 FAIL` on a
  healthy install; the 31-check environment doctor is reachable only from
  `/setup`. Six docs send users to the wrong one.
- State spans **three home trees plus the HF cache**; no doc draws the
  map; backup covers the DB only.
- First boot silently pulls whisper-base from HuggingFace.
- GETTING_STARTED's first instruction names an `<h1>`; the route table
  lists a deleted surface; every model-setup doc says "the Concierge", a
  word that appears nowhere on screen (the window is "Models").
- `holdspeak seed`, the only CLI way to populate a desk, is documented
  nowhere.
- The HS-200-46 claims fence (16 predicates, exact, ratcheted) covers
  **zero** rows of README or GETTING_STARTED; every defect above passes
  CI.
- Four competing terminology sources; 13 conflicts; only
  `product-language.json` (21 terms) is enforced.

### 4.5 The machinery now runs, and the first thing it did was refuse (appendix 05)

The audit's two missing callers are fixed and observably running
(drainer polling, watches arming, scheduled recordings firing, WAL on).
Then every intel claim was refused by a dangling profile id, the queue
hit 100 % failure, and meeting sessions were refused admission. The
fresh DB may have cleared that particular id; nothing has proven it yet.

---

## 5. The plan — one arc: THE USABLE PRODUCT

**Principle.** No new capability until every existing one is either
reachable in one obvious move or parked out of sight. Every phase ends
with the owner in the chair, shots on his desk, and one number from his
real DB. "Accepted, not observed" is retired as a way to close a walk:
the closing evidence for a face is a shot of the owner's desk, and the
closing evidence for a loop is a row in his DB.

**Ordering rule.** Reachable → one-answer → visible → runnable → lived.
Each step is a precondition for judging the next; usability cannot be
assessed through a broken door.

### Day zero (before any phase; hours, not days)

| # | Fix | Where | Size |
|---|---|---|---|
| Z1 | Alias `project-room` → `open-project-memory` in `DESK_APPLICATION_ALIASES`; change the 8 call sites' scope to `project:<id>`; make the RecallFace test assert the window opened, not the call | `web/src/desk/applications.ts:455`, the 8 sites | 1 alias + 8 lines |
| Z2 | Meeting scope grammar: `ChairHome.tsx:1743, 1751` pass `meeting:<id>` | 2 lines | trivial |
| Z3 | Kill the orphan MCP sidecar (PID 55661) holding the retired DB; restart it against the live hub (it is a hub client since 45) | ops | minutes |
| Z4 | Pay the six red tests on `main` or quarantine them with a named owner; CI green is the baseline for everything below | `tests/unit/test_transcriber_init_race.py`, `test_phase200_task_resume.py`, `test_phase200_ci_isolation.py`, `tests/e2e/test_hs153_practice_glass.py`, `test_hs200_task_resume_glass.py` | one lane |
| Z5 | Verify on the fresh DB that a meeting's intel claim is admitted (no `legacy-legacy-*` head). If it is not, add the one-line id repair to the schema reconcile | `inference_assignment_heads` | one query |
| Z6 | Roadmap hygiene: flip the 12 stale stories in merged phases, write the 5 missing final-summaries, refresh the README phase table, park HS-91-10 so `dw next` answers honestly | pm/roadmap | bookkeeping |
| Z7 | Prune the 26 merged worktrees | `git worktree prune` + remove | minutes |

### Phase U1 — The Map (reachable)

*Goal: every face is one obvious move from the arrival; one name per thing.*

1. **A visible index.** A persistent Go rail (left or under the menu
   bar) listing every application by group, with the ⌘K chip beside it.
   The dock stays the five daily verbs. Design on the canvas first
   (UX-CANON A.2); Amiga-grade, not a web sidebar.
2. **The arrival tells a stranger what to do.** Cold state shows three
   things, in order, as verbs: *Choose a model* (if none), *New Project*
   (if none), *Record / Import a meeting*. No prose; three Buttons and
   one true line each. "Generate" is withheld until a model and a source
   exist (rule 11).
3. **One name per screen.** Models = the Concierge window only; the
   Settings module becomes *Runs on* (or is folded into the Concierge
   with an Advanced fold); the Model Library becomes the Concierge's
   Advanced fold. "Desk memory" is the window; the bell becomes
   *Attention*. "Context" outside the app is renamed per surface
   (*Note context*, *Decision rationale*). Rhythm keeps its name, the
   word "Cadence" leaves the faces. Enforce with `product-language.json`
   (the one enforced source) and retire the other three.
4. **Pullouts for the seven fallback kinds** at least carry the object's
   name, its verbs and *Open*.
5. **Seed on purpose.** FirstWords never seeds; the Seed verb lives on
   the cold arrival with a receipt and an Undo.
6. **Dev surfaces leave the product build** (Components catalog behind
   a dev flag; RAILS/Delivery objects hidden unless the DW plugin is on).

Exit: the owner sits down cold, reaches every application from the
screen without ⌘K, opens his Room from four different rows, and says so
on a shot.

### Phase U2 — One Answer (the model and the config)

*Goal: "which model runs this?" has one answer, and it is the one on screen.*

1. **Finish the model-era collapse** (BACKLOG, parked since 08-31).
   `routing_generation` becomes a boot-time fact logged and returned by
   `/api/runtime/status`; the legacy stack parks behind a `legacy_routing`
   config flag, default off.
2. **The badge from the frozen route plan**
   (`meeting_intel_service.py:82-90`) — the Article III defect. First.
3. **Effective assignments per principal.** Either SERVICE inherits
   group scope where the boundary permits, or the editor draws the row
   the meeting queue cannot see as unfilled with the reason.
4. **`set_by` on assignment revisions**; bulk writers skip owner rows and
   disclose the skip.
5. **Finish HS-170-03** (the Concierge) as the single model door: "let me
   download it for you" first, Advanced behind a fold. His co-creator's
   ask, verbatim.
6. **One config root.** Move the nine `~/.holdspeak/` stores under the
   XDG roots with a one-release symlink shim; `holdspeak doctor --paths`
   prints the map. Delete the 148,000-warning source (accept the five
   keys the product itself writes).
7. **One `settings.hub`** (web and MCP share it).

Exit: on the owner's desk, a meeting summary runs, the badge names the
host that ran it, and `intel_snapshots` reads 1.

### Phase U3 — On My Behalf (visible machinery)

*Goal: a single screen answers "what is running for me, when, and what did it do last?"*

1. **`GET /api/runtime/schedule`**: one row per loop (name, enabled,
   interval, last run, next run, owner-gated, last outcome), fed by a
   registry every conductor registers into at start.
2. **One face for it**, in Rhythm: heartbeat, cadence, watches,
   scheduled recordings, intel drainer, steward, workbench conductor.
   On/off per row where the loop has a switch; a `run now` where one
   exists. Cadence gets its settings route (today it is a JSON hand
   edit).
3. **Ownership gate on the three ungated loops.**
4. **Collapse the five run-primitives to workbench** as the surviving
   noun; chains/workflows/practice-recipe routes park; recipes stay
   personas (which is what the table is). This pays HS-200-48 by
   removing the reason for it.
5. **Arming leaves `create_from_setup`** into `watch_service.arm_watch`
   so the Door and MCP mint armable watches (this is HS-200-52; it moves
   here).
6. **Honesty fixes**: `desk.verb` returns a real refusal; `desk_snapshot`
   stops advertising layout; a parity test binds the three verb lists.

Exit: the owner opens Rhythm and can say in one breath what the product
did overnight, and turn one thing off.

### Phase U4 — Run It (a stranger from clone to desk)

*Goal: a competent engineer reaches a working desk in one sitting from the docs alone.*

1. **A stable port** (`--port`, `HOLDSPEAK_WEB_PORT` honoured, default
   fixed, documented).
2. **One doctor.** `holdspeak doctor` runs the 31-check environment
   doctor, then the hub probe against the port it actually bound; flags
   do what they say.
3. **The state map** and the backup scope, in one page; the model
   download announced with size, destination and offline path.
4. **GETTING_STARTED rewritten from a live cold run** and every sentence
   in it bound into the HS-200-46 claims registry, so the clone-to-desk
   path is fenced the way the architecture canon is.
5. **Terminology: one source.** `product-language.json` becomes the
   register; GLOSSARY and DOCS_TERMINOLOGY generate from it; POSITIONING's
   table shrinks to names that render.
6. **The undocumented CLI** (`seed`, `history`, `actions`, `node`)
   documented or parked; the correction-loop surfaces park behind the
   Speak RAW fold (owner: not his use case).

Exit: a worker with no repo knowledge, in a throwaway HOME, reaches a
dictation and a meeting summary using only the docs, and files every
place it had to guess.

### Phase U5 — The Tuesday (lived)

*Goal: one real working week of the owner's life through the loop, watched.*

1. Turn on the four switches on his desk: one calendar source,
   `meeting.auto_record`, `meeting.intelligence_auto`, `cadence.enabled`.
2. Link his one Room to his meetings (`meeting_projects`, today 0).
3. Five workdays. He records the meetings he would have recorded anyway.
   We read his DB counts each evening and his shots each morning. Every
   defect goes on a single list, ranked by how many times it cost him.
4. Nothing new ships during the week except fixes to that list.

Exit: `intel_snapshots`, real meetings, `decisions`,
`decision_commitments`, and one notification he was glad to get. Then,
and only then, the Phase 200 clock (47–53), G2, G3 and G4 are re-read
against what the week showed.

### What parks (never deleted)

- Phase 200 stories 24–36 (assignments, unattended execution) until U5
  produces a number.
- Phase 200 stories 47–51, 53 (the clock) until U3 exists; 52 moves into
  U3.
- The correction loop as a primary face (176's remainders, BACKLOG AG).
- The Interview: unpark or retire in U3 once arming has left it.
- Phases 177–179, 190, 114, 121, 155 stay where they are.

### Process rules for the arc

- **Design on the canvas before build** for U1–U3 faces (UX-CANON A.2);
  the owner ratifies artboards.
- **No "accepted, not observed."** A face closes on a shot from the
  owner's desk; a loop closes on a row in the owner's DB.
- **Shots at 1440 and 393 before merge**, every story.
- **Counsel on built**, one worker per lane, orchestrator merges on
  verification (standing ruling).
- Every phase's evidence includes a fresh read-only census of his desk,
  the same query set as appendix 05, so the trend is on the record.

---

## 6. Appendices

| File | Contents |
|---|---|
| [01-faces.md](inventory-2026-09-19/01-faces.md) | every route, window, pullout; reachability; the 8 broken Room routes; terminology on screen; the cold-start walk; the top-15 verdict |
| [02-capabilities.md](inventory-2026-09-19/02-capabilities.md) | 118 capabilities by domain with FACE?; the audit reconciliation; the 15 loops; 112 config keys; the 29 model mechanisms; the complexity top-10 |
| [03-roadmap.md](inventory-2026-09-19/03-roadmap.md) | the phase ledger 100→200; outstanding stories; promises vs owner use; his recorded confusion; parked work |
| [04-docs-and-running.md](inventory-2026-09-19/04-docs-and-running.md) | the ~130-doc inventory with freshness; the clone-to-desk path as it actually is; CLI; ports and state; terminology conflicts |
| [05-desk-census.md](inventory-2026-09-19/05-desk-census.md) | the read-only census of the retired and live DBs; the intel refusal trace; models and connectors (presence only); log summary |

---

## Check — Astra, 2026-09-19

Per [TWO-BRAINS.md](TWO-BRAINS.md) §3 this plan was checked by Astra before
being acted on. Verdict on §5 as written: **DO-NOT-RATIFY**, ten findings,
every anchor verified. Muad'Dib's response and the ruled re-cut (day zero
gains Z0 data intent and gates Z7; U1–U3 collapse into **Phase U1 — One
Journey**; the rest is re-chartered after its sitting) are recorded in
[inventory-2026-09-19/06-check-astra.md](inventory-2026-09-19/06-check-astra.md).
§5 above stays as authored so the owner sees both minds.
