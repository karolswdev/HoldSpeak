# The Operational Surface Audit — 2026-09-13

**Who asked, and what for.** The owner asked for a deep introspection of what
the last ten to fifteen phases did to HoldSpeak's operational surfaces, which
flows actually work, and whether the long-standing "MCP for everything" vision —
**a crude X11, where the primitives travel instead of the pixels** — is reachable
from where the code stands. His words: *"which window is open, which is active,
all of its controls… since we're building everything out of a common building
block, isn't it? I hope so!"*

Four audit lanes ran over `main` @ `cfa4fd61`, read-only. Every number here is
measured — a generator re-run, an AST pass, a `sqlite3 -readonly` query — not
read off a document. Where a document and the code disagree, the code wins and
the contradiction is named. The two headline defects were re-verified by the
orchestrator by hand before being written down.

---

## 0. The answer in one page

**The product has a large, coherent, genuinely browser-free API.** 222 MCP tools,
675 HTTP routes, 19 CLI commands, 217 tables. This is not a thin shell over a UI;
the services are real and most of them can be driven without a browser.

**Two missing function calls stop it from being a daily product**, and they are
not design debates — they are callers that do not exist:

1. **Nothing drains the intel queue.** A finished meeting writes an `intel_jobs`
   row that nothing in the running product ever executes.
2. **Nothing ever arms a watch.** A watch can only become schedulable inside the
   very function that only runs on already-schedulable watches.

**His desk proves both**: 718 heartbeat evaluations → 1 notification ever;
1 meeting session ever (cancelled); **0 intel snapshots, 0 decisions,
0 commitments, 0 watch effects**; 32 watches of which **2** are armed.

**On the X11 vision, the honest answer is that the premise is half true and the
vision splits cleanly in two.** There IS a real declarative layer — a 22-entry
application manifest, a 20-kind primitive table, a 67-verb registry, one window
frame used by 19 hosts, 88% of interactive UI composed from ~74 library species.
There is NO server-side representation of screen state, by written policy, and
the verb surface exposed to MCP is **a catalog of refusals**: 45 of 50 desk verbs
are marked `ui_only`, and the 5 that are dispatchable **do not intersect the UI's
verb registry at all**.

The split that matters:

| Half | Constitutional standing | Real blocker |
|---|---|---|
| **READ** — snapshot which window is open, which is active, what controls it has | **Permitted today.** Article XI.5: reads and presentation "owe the kernel no admission and no receipt" | The state lives in `localStorage` + Zustand in one browser tab. Nothing outside that tab's JS can answer the question. |
| **DRIVE** — invoke those controls remotely | **Deliberately deferred.** Article XI.3; the registry's own header says the wire face "WAITS for the kernel's userland dispatch" | The broker exists (`/api/kernel/*`). A UI-verb operation kind does not. |

So the vision is not blocked by a wall. It is blocked by **where the state
lives** (read half) and **one missing operation kind** (drive half) — plus the
fact that the verb namespace has already forked three ways with no test binding
them.

---

## 1. What the last fifteen phases actually built

**Project Rooms arc (157–169), all merged.** HTTP surface 568 → 631 routes,
20 new tables, 47 MCP tools.

| Phase | What it added to the operational surface |
|---|---|
| 157 The Contract | refs grammar + result envelope. Its own summary: *"nothing imports the new modules yet."* |
| 158 The Room | 3 tables, `/room` route, the Room face. Reconcile proven on a copy of the real DB; 0 projects existed, so the proof was structural. |
| 159 The Interview | the arc's biggest wire — 8 tables, +20 routes, `WatchService`. **Its face is now parked.** |
| 160 The Delta | 4 tables, evidence collectors, the review algorithm. Step 11 shipped as "an identity hook only." |
| 161 The GitHub Watch | first real connector (`gh`, read-only). Live probe, honest zero. |
| 162 The Update Factory | `project_updates`, deterministic + model drafters. Live LAN inference leg. |
| 163 The Steward's Hand | 4 tables, six-phase run engine, manual `run_once` only. |
| 164 The Unattended Desk | the arc's only loop. Zero tables, zero routes. Admits no scheduled-path trigger route. |
| 165 The MCP Family | 37 MCP tools in one stroke. The sidecar could not evaluate watches (no snapshot fetcher). |
| 166 The Jira Parity | second connector; the arc's strongest real leg (live `acli` transition + revert). Found an inherited lie: `older_than`/`newer_than` returned False unconditionally, so one shipped watch had **never** matched. |
| 167 The Room in Use | 8/8 merged, live runner against the real DB. |
| 168 The Connections Door | **the owner walked it and bounced it.** No accepting verdict was ever recorded. |
| 169 The Streamlined Door | one-screen Door + four-question Room. Door routes have no MCP twins. |

**The Tuesday arc (170–176), all merged.** 170 UX-CANON + Concierge (197 MCP
tools; **merged with 3 stories never flipped**). 171 the always-on heartbeat
(**4 stories never flipped**; a P0 — the loop never called the notifier — found
after close). 172 auto-intel + the Confirm chain (counsel found the proposal
bridge had no production call site; its walk wrote to the real DB). 173 the first
bounded external effect (`github_comment` — **nothing was ever actually sent**).
174 Reach: `POST /api/mcp`, scoped remote credentials (**the .43 leg never run**).
175 calendar, week strip, event-born recordings. 176 the Speak Loop — **whose
thesis the owner has since disowned**: *"I honestly don't give too much of a shit
about those corrections."*

**200 The Working Practice**, current: **10 done, 2 in progress, 29 backlog of
41.** Delivered runtime identity + flock, a Critical Journeys CI job, Concierge
repair states, per-source coverage, an eval harness, durable Room asks, and the
working-context wire. Stories 11–23 — the entire daily loop and the pilot — are
backlog, blocked on the owner's canvas verdict.

---

## 2. The flow inventory — what actually works

| # | Flow | Verdict | Browser-free? |
|---|---|---|---|
| 1 | Meeting capture → intel → decisions | **PARTIAL — broken at the drain** | drain only via CLI |
| 2 | Project Room via the Door | COMPLETE | **no** — no MCP tool, no CLI |
| 3 | Project Room via the Interview | COMPLETE headless, **face parked** | **yes** |
| 4 | Watches → evaluation (scheduled) | **WIRED-BUT-DEAD — cannot bootstrap** *(RESOLVED by HS-200-43: arming on create/enable + an ungated reconcile backfill)* | n/a |
| 5 | Watches → evaluation (manual) | COMPLETE, **but writes no effects** *(RESOLVED by HS-200-43: both paths mint effects through `_record_effects_if_any`)* | yes |
| 6 | Observations → draft → publish update | COMPLETE | **yes** |
| 7 | Claim review on an update | **UNREACHABLE — no route, tool or face** | — |
| 8 | Steward run (manual) | COMPLETE | **yes** |
| 9 | Steward run (unattended) | WIRED, never armed — depends on #4 *(#4 RESOLVED by HS-200-43; unattended execution still waits on the owner's policies, which stay OFF by his ruling)* | n/a |
| 10 | Calendar → scheduled recording | WIRED-BUT-UNPROVEN | arming yes, firing no |
| 11 | Daily brief / cadence | PARTIAL — tick off by default, no face calls `run-now` | **yes, fully** |
| 12 | Dictation → desktop typing | **COMPLETE for beat 1, on his own hand** | hotkey no |
| 13 | Ask / Thought refinement | COMPLETE | **yes — needs neither browser nor hub** |
| 14 | Delegation to a supervised worker | PARTIAL | raw HTTP only |
| 15 | Working-context promotion (200-10) | PARTIAL — fences live, verb unreachable | no face, no tool, no CLI |

Six of fifteen flows are fully driveable without a browser. That is the good
news, and it is the foundation the MCP vision would stand on.

---

## 3. The two missing callers

### 3.1 Nothing drains the intel queue

On stop, `_maybe_auto_enqueue_intel` (`holdspeak/runtime/routing_glue.py:324`)
writes an `intel_jobs` row. Then nothing happens.

- `IntelQueueWorker` (`holdspeak/intel_queue.py:677`) and
  `start_intel_queue_worker` (`:874`) — a complete polling worker with backoff
  and alerting — have **zero production callers**. Verified: every reference is
  the module itself, a test, or `scripts/phase107_closeout_beats.py`.
- `drain_intel_queue` has exactly two production callers:
  `holdspeak/commands/intel.py:110` (the CLI) and
  `holdspeak/services/meeting_intel_service.py:37`, reached only by
  `POST /api/intel/process`. **No face calls that route** (`grep -rn
  "intel/process" web/src` → 0).
- The face's `Run intelligence` button does not run intelligence:
  `MeetingIntelService.run_intelligence` (`meeting_intel_service.py:55`) calls
  `request_intel_retry` and returns `{"state": "queued"}`.

**Where it entered:** Phase 172's settled design asserted the opposite —
*"The deferred queue worker already picks up queued jobs. No new worker needed;
the existing `_deferred_plugin_queue_loop` processes them"*
(`phase-172-the-loop-closes/assets/settled-design-loop-closes.md:317-320`). That
loop calls `process_next_plugin_run_job` — **a different queue entirely.**

**Consequence on his desk:** `intel_snapshots` = **0**. One job has sat `queued`
since 2026-09-10.

### 3.2 Nothing ever arms a watch

`list_due_watches` requires `next_evaluation_at IS NOT NULL`
(`holdspeak/db/automations.py:451`). Every write of that column in the package:
`watch_service.py:922` and `:1009` — and both sit **inside `evaluate_due`**
(function starts at `:850`; confirmed by AST). No creation path passes it:
`grep -rn "next_evaluation_at=" holdspeak/` outside those two lines returns only
the parameter's own default declaration.

**A watch that has never been evaluated by the scheduler can never be selected by
the scheduler.** The Door and Interview creation paths set only
`baseline_state="pending"`.

**Consequence on his desk:** 32 watches, 30 enabled, **2 armed**.

### 3.3 And when a watch IS evaluated by hand, it records no effects

*(RESOLVED by HS-200-43: `_match_and_record_effects` is reached from
`_record_effects_if_any`, which both `evaluate_due` and `evaluate_once` call,
so a manual evaluation mints the same effects under the same idempotency key
and `ProjectStewardService.run_due` can read them. The finding below is left
standing as the dated record of what was measured.)*

`_match_and_record_effects` (`watch_service.py:958`) has one caller, inside
`evaluate_due`. So `project.watch.evaluate` — the MCP tool — can never trigger
the steward. `watch_effects` on his desk: **0**.

---

## 4. His real desk, 2026-09-13 (read-only)

| Operation (kernel ledger) | Count |
|---|---|
| `heartbeat.sweep` / `heartbeat.notify` | 724 / 718 — **1 notification ever sent** |
| `inference.invoke` | 147 |
| `dictation.session` / `desktop.type_text` | 35 / 30 |
| **`meeting.session`** | **1, cancelled, 2026-08-18** |

| | |
|---|---|
| meetings 7 (5 empty, longest 30s) | **intel_snapshots 0** |
| projects 10 — 9 archived walk seeds, **1 active** | project_updates 5, observations 12 |
| **decisions 0 · decision_records 0 · commitments 0** | action_items 1 |
| connector_watches 32 — **2 armed** | **watch_effects 0**, evaluations 3 |
| steward_policies 9, **all unattended disabled** | **cadence_nudges 0**, loops both killed |
| monday_briefs **1**, from 2026-08-19 | **calendar_events 0**, **speakers 0** |
| threads 10 — all messages on 2026-08-31 | **interview_sessions 0** |
| **kernel_schedule_ticks 0 · tool_turns 0 · work_attempts 0** | |

**His config explains most of the zeros**, and that is important — several of
these are not broken, they are *off*: `cadence.enabled = False`;
`meeting.intelligence_auto = room_linked` with **zero** room-linked meetings;
`calendar.sources = []`; `meeting.auto_record = off`;
`meeting.diarization_enabled = False`.

**His hub is running code from before the 200-10 merge** — the DB is at schema
v77 with no `context_promotions` table. The newest surface has never touched his
machine.

**A correction to the record:** an audit lane flagged a discrepancy with handover
XVIII, which reported 326 `external.egress` operations with 325 rows of test
pollution, against its measured 241 with 1 indeterminate. There is no
discrepancy — **the orchestrator deleted those 325 rows on 2026-09-09 on the
owner's instruction** ("Clean them"), with a backup at
`~/.local/share/holdspeak/holdspeak.db.pre-egress-cleanup-2026-09-09.bak`.

---

## 5. MCP / HTTP / UI parity

| Surface | Count |
|---|---|
| MCP tools | **222** (40 namespaces, 19 families) |
| HTTP routes | **675** (generator re-run; `api-surface.json` matches exactly, zero drift) |
| Web desk verbs | **52** declared + 15 generated = 67 |
| Service methods reachable from **MCP** | **225 of 568 — 40%** |
| Service methods reachable from **HTTP** | 407 — 72% |
| **UI can, MCP cannot** | **195 method names** |
| MCP can, HTTP cannot | 13 |
| Routes with no shipped caller | 114 |

**The UI-only clusters are exactly where daily work happens:** `MeetingService`
21 methods (rename, bookmark, edit action item, import, recover capture),
`ProjectService` 17, `ActivityEnrichmentService` all 13, `WorkbenchService` 13,
`ThreadService` 10 — **MCP has one thread tool, `thread.set_status`** —
`PeopleService` 10, and `AuthorityService` 6: **no MCP tool touches control mode
or grants at all.**

**Deliberate refusals, which must not be mistaken for gaps** (10 recorded):
no MCP `promote`/`revoke_promotion` (a model must not mint a canonical record);
four verbs absent from the sidecar for capability reasons; provider writes
read-only; the People disclosure boundary; thought/refine schemas accept no
content; `desk.verb` refusing UI-only verbs; OWNER refused off-loopback on
`/api/mcp`; secrets unwritable through generic settings.

**But the recorded default is parity**, on the record since Phase 127:
*"Receipts are a desk capability, not a UI-only feature. MCP must expose the same
receipt lifecycle."* And coder steering's absence is classified by the Phase 200
baseline as **a defect to repair (HS-200-28)**, not a refusal.

**No constitutional article constrains the MCP surface.** `CONSTITUTION.md`,
`UX-CANON.md` and `AUTHORITY.md` contain zero occurrences of "MCP". Every
refusal above is phase-level.

---

## 6. The common building block — the premise, measured

**Partly true, and true only inside one browser tab.**

What is real:

- **22-entry application manifest** (`web/src/desk/applications.ts:48-428`) whose
  own docstring says the Dock, Go commands, keybindings and mark menu "are
  projections of this table."
- **20-kind primitive table** (`web/src/lib/primitives.ts:419-682`), each kind
  declaring capabilities and a surface declaration.
- **67-verb registry** (`web/src/desk/verbRegistry.ts`), one keymap, one
  window-menu adapter derived from it.
- **One window frame** (`DeskWindow.tsx`) adopted by **19 hosts**.
- **1,909 library-species usages vs 250 raw interactive elements — 88.4%
  composed.** `Button` alone: 754 usages.

What cuts against it:

- **No doc has ever claimed it.** Constitution Article II is about *capabilities*,
  not components, and `SYSTEM_PRIMITIVE_COMPONENT_INVENTORY.md:45` rejects the
  idea outright — *"The system should not be flattened into one universal
  object"* — and records at `:185` that **"'Primitive' currently means at least
  five things,"** with four mutually incompatible kind lists.
- **The building block is two blocks.** `components/signal/` supplies the Button;
  `desk/surface/` supplies the containers. `ARCHITECTURE_WEB_FRONTEND.md`
  documents both and never says which won.
- **The species canon documents 23 of 68 exports** against its own law, "a species
  in use is a species documented."
- **The uniformity is in containers, not in a control contract.** `SurfaceVerbs`
  — the species that would declare "these are this surface's verbs" — is used in
  **9 files out of 197**, and it takes `children: ReactNode`, i.e. arbitrary JSX,
  not a spec.

---

## 7. The window model, and why the read half is blocked

**What a window is:** a React component instance rendering `DeskWindow`, plus
geometry rows in a Zustand store. **There is no single enumerable list of open
windows.** Open-ness is spread across **seven parallel collections**
(`web/src/desk/store/compositorSlice.ts:120-133`), only two of which persist.
The one uniform enumeration is a module-level `Map` populated **as a side effect
of React mounting** (`windowRegistry.ts:16-19`, written from one `useEffect` in
`DeskWindow.tsx:714`).

**Open, active and z-order all exist — all derived.** `panelOrder` is the stack;
`frontWindowId()` is a *function*, not a stored field. **There is no
`focusedWindowId` anywhere in the codebase.**

**Where the state lives — the crux:**

> **In one browser tab's memory, backed by `localStorage` (`hs.desk.workspace.v1`).
> The server does not know any of it exists and is never told.**

- `panelOrder` / `windowsById` / `panelRects` appear in 12 client files, **zero of
  which are API or wire modules.**
- Of 675 routes, **none reads or writes layout**. Of 217 tables, none is a
  window, workspace, layout or viewport table. Of 44 realtime frame types, none
  carries screen state.
- It is **written policy**, not an oversight: `holdspeak/db/primitives.py:1073` —
  *"geometry/paint is per-device layout and lives on the surface, never
  canonical"* — and the inventory doc lists layout as "Deliberately not canonical
  or synced." The Swift client carries **two runtime assertions that fire** if
  layout ever leaks into a sync bucket.
- **Two tabs are two divergent desks.** No `storage` listener, no
  `BroadcastChannel` for the workspace document.

**Controls are not enumerable without rendering.** Global verbs are statically
listable, but `ghost(ctx)` — the enabled/disabled state and its reason — calls
`useDesk.getState()`. Per-surface controls have no manifest at all. The proof:
every rig drives the product through Playwright — **1,098 `locator(`, 549
`get_by_test_id`** across 98 files. There is no programmatic control path, no
accessibility-tree export, no `window.__*` automation global outside tests.
Of 630 `data-testid`s, **551 distinct literals are hand-authored**; exactly one
id convention is derived from the registry
(`DeskToolShelf.tsx:567`, `desk-palette-option-${row.id}`).

**And `desk_snapshot` is data, not screen.** Ten lines
(`holdspeak/services/desk_service.py:37-47`), seven keys, each a SQLite `.list()`:
notes, decisions, directories, workflows, chains, profiles, workbenches. The MCP
resource description at `resources.py:158` advertises "Canonical current Desk
state, including its stored objects **and layout**." **No layout is returned.**

---

## 8. The verb surface exposed to MCP is a catalog of refusals

`desk.verb` (`holdspeak/mcp/tools.py:974-989`) resolves against a **local dict of
five lambdas**: `desk.create`, `desk.update`, `desk.delete`,
`workbench.add_item`, `workbench.run`.

**None of those five is an id in `web/src/desk/verbRegistry.ts`. The intersection
between the MCP verb allowlist and the UI's verb registry is empty.**

Everything else — all `go.*`, all `window.*`, all `system.*`, and 21 names in
`_UI_ONLY_VERBS` — returns a constant stub `{"status": "ui_only"}` that reads and
writes nothing. **`window.close`, `window.minimize`, `window.cycle`,
`window.snap-left/right`, `window.maximize` are in that set: the server knows
those names and deliberately does nothing.**

And the catalog has drifted from the thing it claims to mirror. `resources.py:60`
says *"Mirrors web/src/desk/verbRegistry.ts"*; **20 registry verbs are missing**
(`desk.new-project`, `desk.new-thread`, `desk.settle`, all ten `thread.*`, the
four `desk.intelligence-*`, …) and 13 phantom `go.*` entries remain.
**No parity test binds them.**

---

## 9. Remoteness — two doors, unequal

**Door A: wide, undesigned, works today.** `HOLDSPEAK_WEB_HOST=0.0.0.0` plus the
owner token yields **full OWNER across all 675 routes** and the `/ws` bus. The
auth middleware derives the owner from the token with **no network-location
check**. The iPad track already runs this way.
`docs/USER_GUIDE.md:978` states "The owner's web token is refused on a
non-loopback request" — **true only for `/api/mcp`**; `SECURITY.md` says it
correctly.

**Door B: narrow, designed, off.** `POST /api/mcp` (Phase 174): scoped AGENT
credential, palette-limited, OWNER refused off-loopback, `origin=remote`
receipts. Three defects:

1. **`bind_host` is decorative** — stored, rendered on the settings face, applied
   by nothing. `SECURITY.md`'s "accepts connections on the tailnet address only"
   is **not implemented**; there is no CIDR check anywhere, and zero hits for
   `tailscale|tailnet|ngrok|cloudflared` in any `.py`.
2. **The enable flag is an in-memory dict** with no config field and no boot
   initializer — **every hub restart silently returns Reach to OFF**, and wipes
   every issued credential.
3. **The `DESK` palette resolves to all 222 tools**, identical to `ALL`, because
   both import the same list object that families mutate in place. Measured:
   `PROJECT 57, SWEEP 61, DESK 222, ALL 222`.

Plus: **`POST /api/principals/agents`** — which the web UI does call — mints a
credential with **no palette**, i.e. the full catalogue.

**An MCP write does not reach the open browser.** MCP dispatch composes services
with no broadcast callback; the `/ws` bus is one-way and carries status frames,
not primitive CRUD. The desk has a manual "Refresh from hub" verb for exactly
this reason. A remote write lands in the DB and sits there.

---

## 10. Defects this audit found, ranked

1. **P0 — the MCP sidecar is a second, unlocked writer on the owner's live DB.**
   `.mcp.json` has **no `env` block**, so `uv run holdspeak-mcp` inherits `$HOME`
   and opens `~/.local/share/holdspeak/holdspeak.db` — the same file the running
   hub owns. Verified on the real file: **`PRAGMA journal_mode = delete`, not
   WAL** (`db/connection.py:3` claims "WAL pragmas"; the code sets only
   `foreign_keys=ON`), no `busy_timeout`, and **`holdspeak/mcp/` references the
   owner lock zero times** — while `runtime_lock.py`'s own docstring says *"C10
   forbids introducing a multi-writer SQLite arrangement at all."* Every sidecar
   start runs `reconcile_schema`, a write transaction.
2. **P0 — nothing drains the intel queue** (§3.1). The meeting flow, the
   product's headline, ends in a row nobody reads.
3. **P0 — nothing arms a watch** (§3.2). The unattended half of Project Rooms
   cannot bootstrap.
4. **P1 — the UX-canon guard sees 5% of its own violations.** `A1` reports **4**;
   an independent count finds **187** raw `<button>`. The regex matches
   `<button[\s>/]` against newline-stripped lines, so every multi-line JSX tag is
   invisible. `UX-CANON.md:131` presents the "4 residues" as a fact about the
   code; it is an artifact of the regex — and it underwrites the owner's own
   ruling that every verb is the library Button.
5. **P1 — manual watch evaluation records no effects** (§3.3), so the MCP path
   can never reach the steward. *(RESOLVED by HS-200-43.)*
6. **P1 — `review_claim` is unreachable**: the only occurrence in the product is
   its own definition; the face renders the acceptance token read-only. Every
   claim is permanently `unreviewed`.
7. **P2 — two schedulers on one row.** Both the conductor and the heartbeat call
   `evaluate_due`; **only the heartbeat checks quiet hours.** The quiet-hours
   promise is not kept on the conductor's path. *(RESOLVED by HS-200-43: the
   conductor's watch block is deleted, the heartbeat is the single scheduler,
   and quiet hours now hold evaluation as well as notification. The finding is
   left standing as the dated record of what was measured.)*
8. **P2 — `promote`/`revoke_promotion` reachable from no shipped caller.** The
   read route now exists but nothing in `web/src` fetches it, and the panel emits
   only four kinds. The face being absent is ruling C6; the fetch gap is not.
9. **P2 — `project.steward.trigger` returns `isError: false` on refusal**
   (`{"success": false, "code": "scheduler_not_wired"}`) — a soft refusal a naive
   caller reads as success.
10. **P3 — `jsonschema` is imported at module scope in `mcp/tools.py` but declared
    only in the `test`/`dev` extras**, so the documented
    `uvx --from holdspeak holdspeak-mcp` would ImportError. Static claim.

---

## 11. What the X11 vision actually costs from here

Stated as structure, not as a plan. The owner rules on whether any of it happens.

**The read half — "what is open, what is active, what controls does it have."**
Constitutionally permitted today (Article XI.5). Blocked by one fact: the answer
exists only inside a browser tab. Two shapes are possible and they are very
different in kind:

- *Publish from the tab.* The desk already holds the whole answer; it would
  announce its own window state to the hub, which relays it. Cheap, honest about
  where authority lives, and it dies when no tab is open.
- *Move authority server-side.* Windows become canonical objects. This contradicts
  a written position held consistently from `primitives.py:1073` through the
  inventory doc and enforced by two runtime assertions in the Swift client.
  **This is a canon decision, not a refactor.**

Either way, a **per-surface control manifest** has to exist, and today it does
not: `SurfaceVerbs` takes arbitrary JSX in 9 of 197 files. That is the real work
— not the transport.

**The drive half.** Needs a UI-verb operation kind admitted through the kernel
broker that already exists (`/api/kernel/submit|decide|events|read`, already
consumed by `processWindow.ts`). The deferral is explicit and conditional, not a
prohibition: *"the wire face deliberately WAITS for the kernel's userland
dispatch."* Before that is worth building, the verb namespace has to stop
forking: three hand-maintained lists, 20 verbs already adrift, no parity test.

**The cheapest honest first step, if he wants one:** a parity test binding the
three verb lists, and a real `desk_snapshot` that either returns layout or stops
advertising it. Both are small, both pay down a lie, and both are prerequisites
for anything else here.

---

## 12. What could not be verified

- Whether the double-scheduler produces duplicate provider fetches (static
  reading suggests the txn hook makes the loser find nothing).
- Whether a scheduled recording has ever fired into a real meeting row. No
  real-fire walk exists.
- Whether delegation spawns a real tmux pane and writes the attempt row.
- Whether any remote call has ever crossed a real network on `/api/mcp` — every
  proof uses `TestClient`, whose host is the literal string `"testclient"`.
- Whether SQLite lock contention between a live hub and a live sidecar has
  actually bitten. The absence of WAL, `busy_timeout` and an owner-lock claim is
  proven; the observed failure rate is not.
- The full-suite totals quoted in 167/168/169's final summaries — they sit
  outside any `dw evidence capture`.
- No tests were run for this audit. Every code claim is static; every desk claim
  is a read-only query.
