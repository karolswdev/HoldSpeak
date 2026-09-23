# THE COUNCIL — Philo Phase 2, The Graph (PHILO-2-06)

**Status:** DRAFT by Muad'Dib, 2026-09-23, from all four sealed passes (`static-muaddib`, `static-astra`, `live-muaddib`, `live-astra`, main `34323afe`). Astra's check and counter-draft follow under "Astra"; open dissents are verbatim; the owner rules them and the Phase 3 charter. Plain words, per brief §9.

## 1. The decision page

### What works, what fails, what is unverified — the eleven jobs

| Job | Result | Evidence |
|---|---|---|
| J1 Get past the gate | **Works** for Continue later and for typing one sentence and keeping it (both brains, both widths). **Unverified** for speaking: no rig may open a microphone. **Broken** for two failure recoveries: a missing model or a rejected token sends him to "New Project" (Astra static #1). | live-muaddib J1; live-astra J1; static-astra J1 |
| J2 See what the desk asks | **Works on the glass**, unproven by a rig pass: one SETUP row "No engine for summaries", head "1 need you", the calendar offer not counted. | live-muaddib J2 shots |
| J3 Give the desk a summary engine | **Works as a chain** (every J6 run configured the LAN engine through the face and reached READY), **unproven as its own job** (no J3 case reached its trigger by a correct recipe). The Download and cloud Check alternatives are broken (both statics). | live-muaddib J3; static-muaddib #4; static-astra #6, #7 |
| J4 Have one meeting on the desk | **Works** by import (a row by id; the length is not proven at capture). **Unverified** by recording (microphone). | live-muaddib J4; live-astra #5 |
| J5 Know where the summary will run | **Works**: "192.168.1.43 · LAN" beside Run summary before the click, both widths. | live-muaddib J5 |
| J6 Get the summary | **Unverified by the rig.** Every summary in the lane runtime failed because that runtime lacks the model client (`openai` is only in the `test`/`meeting` extras). A diagnostic with the client present shows the real LAN engine summarising in 1.46 s and the host on the receipt. **Usefulness unverified**: the only material is a nine-word pangram. **Broken on the face** by static trace: the arrival refreshes once after the click and nothing tells it the summary landed; a retrying summary reads as "Nothing needs you". | live-muaddib J6 + DIAGNOSTICS; live-astra #1; static-muaddib #1; live-muaddib #2 |
| J7 Find it again after a restart | **Unverified by the rig** (the restart step never fired). Diagnostic: after a restart the row reads RAN and one Open shows the same summary. The two-move count is his. | live-muaddib J7 |
| J8 Voice typing into another app | **Unexercised** by design; his sitting. | atlas |
| J9 Open what the desk remembered | **Works**: the real scheduler minted a sweep receipt, Desk memory shows it, its Open opens Rhythm, both widths, both brains. **Broken beside it**: Rhythm shows UTC (both brains); a dictation receipt's Open opens the wrong window; invocation and steering receipts open nothing; a dismissed card can never return. | live-muaddib J9; live-astra #11; static-muaddib #5, #6; static-astra #5 |
| J10 Get a brief, and another | **Works** same-day: the words stay after a reload; Generate again returns, displays and retains the same brief, proven by id. **Broken**: a populated brief cannot be made because **recording a decision answers 500** (both brains, both widths). A brief load failure is drawn as "No brief yet" (both statics). No date on the face. Next day unexercised (no clock). | live-muaddib J10; live-astra #2; static-astra #4; static-muaddib #7, #8 |
| J11 Develop a thought | **Works** for the words: typed words reach the store by autosave (both brains). **Broken** for the receipt: the face shows KEPT from filing status, never *when* the newest words were kept; there is no Keep verb; "Kept · time" does not exist on this face. | live-muaddib J11; live-astra #12; static-astra #2 |

Two defects from his sitting of 2026-09-21 no longer reproduce (the receipt's Open reaches Rhythm; the empty brief keeps its face).

### The next useful result, and the smallest Phase 3 that buys it

**The result:** one real meeting, summarised on his LAN engine, seen landing on the arrival, found again after a restart, and one decision recorded from it into the next brief. Today the chain breaks at three places he will hit in that order: the arrival never learns the summary landed; a decision cannot be recorded; the thought he writes about it shows no receipt.

**Smallest Phase 3 (ten stories, ranked by owner cost; effort is a build estimate, not a promise):**

| # | Story | Closes | Effort |
|---|---|---|---|
| 1 | **Decisions can be recorded** — `del ctx` before its use in `holdspeak/web/routes/primitives/decisions.py:20,27`; a fence that POSTs and reads one | J10 populated; the shelf; the brief's decisions section | hours |
| 2 | **The summary lands on the arrival** — the Chair subscribes to `intel_complete`/`intel_status` (today only Live does) or the drainer emits `desk_changed`; a retrying job is not "Nothing needs you"; the cause reaches the face | J6 on the arrival; live-muaddib #2; static-muaddib #1 | days |
| 3 | **The thought's receipt** — "Kept · HH:MM" bound to the last successful write, a distinct pending and failure state; the filing state stays separate | J11; the owner's first gripe | days |
| 4 | **A brief that failed to load is not "No brief yet"** — a named load failure with Retry; the date on the face | J10; static-astra #4; static-muaddib #7, #8 | hours |
| 5 | **Every receipt's Open goes somewhere** — dictation receipts open the journal, invocation/steering receipts open their subject, dismissed cards can be restored (a caller for `restore`, `include_dismissed`) | J9's neighbours; static-muaddib #5, #6; static-astra #5 | days |
| 6 | **First-value recovery reaches the right owner** — missing model / rejected token open the engine or access owner, never New Project; capture recovery gets its face; Talk delivers its words | J1's failure branches; static-astra #1; static-muaddib #2, #3 | days |
| 7 | **Local time on every face** — Rhythm and Settings render local time from ISO, or name the zone | J9; both live passes | hours |
| 8 | **Desk memory is one thing** — one name, one face; Recall's recent actions refresh after a write | J9; static-muaddib #10; static-astra #3 | days |
| 9 | **Concierge finishes what it starts** — Download polls to completion or fails visibly and can be retried; cloud Check actually probes | J3 alternatives; both statics | days |
| 10 | **The arrival's Record says something** — Record shows the Live window or its own Stop; import shows its length when the import finishes | J4 | days |

Not in Phase 3 (story 07 of this phase, tooling): the lane runtime's missing client; the six boundary substitutions the rig lacks (fake audio, permission, transport, route failure, remote origin, engine reply files); the atlas recipes that click Run summary in setup or send stale request bodies; a wait for import completion; real meeting material for the summary.

### Decisions for the owner

| # | Question | Recommendation | Alternative | Cost | Decisive evidence | Dissent |
|---|---|---|---|---|---|---|
| D1 | Is the summary useful? Nobody can say from a pangram. | Give the audit one real recording of yours (or one synthetic meeting with planted decisions), imported through the multipart route, before Phase 3 story 2 closes | Keep the fixture and judge only technical completion | one recording; usefulness stays unverified otherwise | live-muaddib J6 usefulness; live-astra #10 | none |
| D2 | Does your own install have the model client? The lane runtime did not, and every summary failed with "openai package is not available". | Run `uv run holdspeak web` from your checkout once and read the first summary's receipt; if it fails the same way, the install extras are Phase 3 story 2's first line | Assume the demo install is fine | if wrong, J6 is broken on your desk today, not only in the rig | live-muaddib DIAGNOSTICS; `pyproject.toml:86,90` | none |
| D3 | The Phase 3 cut and order above. | Ratify as listed; ten stories, the first four in the first lane | Re-cut by your day, not by ours | a re-cut moves nothing in the graph, only the order | this page | Astra's counter-draft may re-rank; recorded below |
| D4 | The ember accent look from Phase 202 (`--accent-ink`), still your call. | See the story-05 shots and say whether it stays | Revert to the lighter ember and accept 2.2:1 labels | one look | phase-202 story-05 shots | none |

### Deferred, and what you still cannot do

- Speak at the gate, record a meeting by microphone, and type by voice into another app: the rig cannot lawfully do them; they are your sitting (SITTING-07 steps 0, 3, 7).
- Anything the clock decides (a next-day brief, a week boundary, the fourteen-day continuity horizon): no mechanism moves the producer's clock; tooling debt, story 07.
- The 225 MCP tools, 29 CLI commands and the connector inputs are enumerated, not walked.
- Ninety percent of a day on the desk is a design aim this audit does not measure; it observed eleven first-use jobs.

## 2. Agreements — both brains, both passes

- Recording a decision answers 500 on a fresh desk (`del ctx` before its use). Both live passes, both widths.
- Rhythm and the settings faces show UTC as if local. Both live passes.
- The Thought face never shows when the newest words were kept; there is no Keep verb. Astra static #2, Muad'Dib live J11, Astra live #12, the story-01 ledger.
- The summary job has no proven completion on the rig; the real engine works when the client is present. Both live passes (Astra: no terminal summary captured; Muad'Dib: the runtime lacks the client, diagnostics show 1.46 s).
- A brief load failure is drawn as absence. Astra static #4, Muad'Dib static #7.
- The Concierge download never finishes and the cloud Check never probes. Muad'Dib static #4, Astra static #6/#7.
- Receipt Open with the wrong source identity (dictation, invocation, steering). Muad'Dib static #6, Astra static #5.
- The receipt's Open reaches Rhythm and the empty brief keeps its face: the two sitting defects are paid. Both live passes.
- Tooling: the six missing boundary substitutions, the missing engine-reply file, the atlas recipes that fire Run summary twice, the stale request bodies. Both live passes name the same set.

## 3. Findings one brain saw — with the other's reply (one round each)

| Finding | Brain | Reply of the other |
|---|---|---|
| The arrival never learns the summary landed (static-muaddib #1) | Muad'Dib | Astra static traced J6 "wired" to the summary slab, not to the arrival's refresh; Astra's live pass saw no terminal summary, so could not observe it. Astra to reply. |
| A retrying summary reads as "Nothing needs you" (live-muaddib #2) | Muad'Dib | Seen in a diagnostic and at source; Astra to reply. |
| First-value recovery for missing model / rejected token opens New Project (static-astra #1) | Astra | Muad'Dib agrees: the same family as the `microphone_unavailable → New Project` defect paid in HS-202-02; the two remaining categories were not covered then. Accepted. |
| Recall's recent actions lose their mode after a write (static-astra #3) | Astra | Muad'Dib did not trace Recall's write path; accepted on Astra's evidence (`useRecallController.ts:143-193`). |
| Capture recovery has no face; `POST …/capture/recover` has no caller (static-muaddib #2) | Muad'Dib | Astra to reply. |
| Talk drops its words (`handleMicText` empty, static-muaddib #3) | Muad'Dib | Astra to reply. |
| Dismiss is forever (no caller for `restore`, static-muaddib #5) | Muad'Dib | Astra's live pass blocked the restore case on a missing adapter; Astra to reply. |
| J1 static verdict: Astra "broken" (recovery owner), Muad'Dib "wired" (the normal path) | both | Not a dissent: different edges of the same job; both true. Recorded as agreement with different evidence. |
| Import "pass" on a 202 with duration 0 (live-astra #5 calls it weak completion; Muad'Dib passed it with the limit stated) | both | Agreement on the fact; the predicate is the atlas's (tooling, story 07): wait for the import to finish and assert the length. |

## 4. Open dissents (verbatim)

The positions below remain open after Astra's first reply. Muad'Dib's words
are copied from his draft or sealed finding; they are not an invented reply
to this check. The owner rules under brief §9. New ledger entries without a
Muad'Dib reply are marked as such in the resolutions file.

### 4.1 Job completion and visible evidence

**Muad'Dib, §1 J4:**
> **Works** by import (a row by id; the length is not proven at capture). **Unverified** by recording (microphone).

**Muad'Dib, §1 J5:**
> **Works**: "192.168.1.43 · LAN" beside Run summary before the click, both widths.

**Muad'Dib, §1 J10:**
> **Broken**: a populated brief cannot be made because **recording a decision answers 500** (both brains, both widths).

**Astra:**
> J4 proves accepted import, not a completed meeting. J5 proves the desktop label; both phone shots leave the meeting control behind Models. J10 proves a broken decision-create route and a blocked decision-backed brief recipe, not that every populated brief is impossible. Use these narrower labels on the decision page.

Evidence: Astra findings 1–2 below, including the raw import row and J5 phone shots.

### 4.2 Summary and restart diagnostics

**Muad'Dib, §1 J6:**
> Every summary in the lane runtime failed because that runtime lacks the model client (`openai` is only in the `test`/`meeting` extras). A diagnostic with the client present shows the real LAN engine summarising in 1.46 s and the host on the receipt.

**Astra:**
> The missing client explains Muad'Dib's reported runtime failure and Astra's first attempt. Astra installed the declared test extra before later attempts, which still blocked on recipes. The 1.46-second completion and restart are Muad'Dib's reported diagnostics, whose raw output is absent; I cannot verify them. Neither is a council-certified completion or an observed arrival refresh.

Evidence: `live-astra.md:29`; `live-muaddib.md:55` (DIAGNOSTICS).

### 4.3 The smallest Phase 3

**Muad'Dib, D3:**
> Ratify as listed; ten stories, the first four in the first lane

**Astra:**
> Ratify three bounded stories for the imported-meeting-to-next-brief result: record the decision; show and retain the summary; show the dated brief and its decision. Include the minimum proof tooling in those estimates. Defer the other product repairs explicitly; they are real costs, but they are not dependencies of this result. A full Desk memory consolidation and alternate engine setup do not belong ahead of the first useful meeting.

Evidence and dependencies: Astra's Phase 3 table below. This is a scope proposal, not authority to start work.

### 4.4 Who diagnoses the install

**Muad'Dib, D2 recommendation:**
> Run `uv run holdspeak web` from your checkout once and read the first summary's receipt; if it fails the same way, the install extras are Phase 3 story 2's first line

**Astra:**
> The lane should reproduce the documented install in an isolated environment and retain the result before asking the owner to use it. The owner should judge a useful summary, not diagnose our missing client. His current installation remains unknown.

Evidence: `README.md:23`, `pyproject.toml:86`, `pyproject.toml:90`; Tenets 2 and 3.

### 4.5 The accent alternative

**Muad'Dib, D4 alternative:**
> Revert to the lighter ember and accept 2.2:1 labels

**Astra:**
> Offer two looks that both meet the 4.5:1 small-text rule, or name a proposed canon amendment. A 2.2:1 label is not an ordinary compliant taste option. Keep this separate from the meeting result.

Evidence: `docs/internal/UX-CANON.md:96` (Contrast); Tenets 5 and 6.

### 4.6 Refusal during import

**Muad'Dib, sealed `fnd.live.run_refused_as_no_transcript_while_transcribing`, bin:**
> product-defect

**Muad'Dib, the same finding's actual:**
> POST /api/meetings/{id}/intelligence/run during the import answered 409 'Meeting has no transcript' (code empty), and ahead of the no-assignment branch, so the atlas's no-assignment case received the empty refusal instead.

**Astra:**
> The request ran before a transcript existed. That evidence establishes the wrong test precondition, not a product defect: the service truthfully refused an empty meeting before checking assignment. Keep the observation, repair the recipe, and require a separate contract or user-visible misleading state before opening a product repair.

Evidence: `holdspeak/services/meeting_intel_service.py:160`; `finding.live_astra.unminted_preconditions`.

### 4.7 Desk memory consolidation

**Muad'Dib, Phase 3 story 8:**
> **Desk memory is one thing** — one name, one face; Recall's recent actions refresh after a write

**Astra:**
> Confusing names and stale Recall results are real, but one face is not required by Tenets 3 and 5. Repair recent-mode refresh separately; a consolidation is outside the minimum meeting result.

Evidence: `web/src/features/project-room/recall/useRecallController.ts:143,159,193`;
`web/src/desk/components/SystemShade.tsx:180`.

## 5. The roots verdict — the observed faces against Tenet 6

The owner said: ninety percent of the day on the desk, interfaces that guide, Workbench 2.0+ on steroids. On the eleven jobs the desk **guides on the way in**: the SETUP row names what is missing, the planned host is beside the verb before the click, the sweep receipt opens the face it belongs to, the brief keeps its words. The desk **stops guiding where a result must come back to the face**: the summary lands in the store and the arrival keeps saying QUEUED; the thought's words are kept and the face says only a filing state; a decision cannot be recorded at all; time is shown in a zone he does not live in; a receipt's Open sometimes opens nothing. The chrome is Workbench; the seams are plumbing. Phase 3 is the seams. This verdict is on the observed faces; it does not measure a working day, and it does not judge the summary's usefulness, which nobody has seen on real material (D1).

## Astra — check and counter-draft

### Check — Astra, 2026-09-23 UTC

Session: `01a0cc44-993b-7b32-a30b-394d7af593cc`. Checked Muad'Dib's draft
`20eafcb7` against all four sealed Markdown/JSON passes on `34323afe`, their
recorded observations, selected shots at both widths, and the cited source.
No product was run and no owner state was read. This is counsel on the
decision record, not a PHILO-2-06 done call or Phase 3 ratification.

VERDICT: **DO-NOT-RATIFY** the decision page as written. The core defect
list is useful, but its job labels and proposed minimum would misdirect a
tired owner's ruling.

FINDINGS:

1. **Some job labels exceed the evidence.** J4 is accepted upload only:
   the [raw import result](observations/astra/20260923T015710Z-case.j4.meetings_import.imported-astra-1440/observation.json)
   has meeting `33e5e08c`, `intel_status=importing`, duration `0.0` and zero
   segments. J5 is visible beside Run summary at
   [1440](observations/muaddib/20260923T020212Z-case.j5.meeting_open.planned_host_disclosed-muaddib-1440/after.png),
   but both phone shots show Models covering the meeting control
   ([planned-host case](observations/muaddib/20260923T020239Z-case.j5.meeting_open.planned_host_disclosed-muaddib-393/after.png),
   [route case](observations/muaddib/20260923T020019Z-case.j5.meeting_open.route_disclosed-muaddib-393/after.png)).
   The DOM's `visible: true` is not proof of an unobscured control. This is
   a proof gap, not a window-stacking defect. J10's decision route really
   answers 500, but the populated recipe never reaches Generate; other
   brief collectors exist (`holdspeak/services/monday_brief_service.py:258`).
   Say **decision-backed populated brief unverified; decision creation broken**.
   J2 proves one displayed state, not the setup truth table. J3 proves the
   successful setup chains, not "every J6 run" or provider execution.
   **Tenets 2, 3 and 7; Article IX; brief §3.**

2. **Reported diagnostics become established facts in J6 and the roots
   verdict.** `live-muaddib.md` explicitly says the diagnostic output is
   not in the tree. I cannot verify the reported 1.46 seconds, executed
   host, restart, or the combined QUEUED/FAILED shot. `live-astra.md:29`
   records the client installation before later recipe blocks, so the
   missing client does not explain both complete passes. The missing
   arrival refresh and misleading retry state are supported by source,
   not a sealed terminal observation. Retain that distinction in §§1, 2
   and 5. **Tenets 2 and 7; Articles VI and IX.**

3. **Ten stories are not the minimum for the stated result, and its
   prerequisites are missing.** §1 adds alternate setup, voice, Thought,
   Rhythm and a three-face memory consolidation to an imported meeting
   and decision. It defers the clock while promising the *next* brief.
   Same-day Generate returns the existing brief
   (`holdspeak/services/monday_brief_service.py:194`); recording a decision
   after an empty brief therefore does not prove inclusion. The charter
   must own import completion, actual execution, restart and a real
   producer-day transition in its closure evidence. A repaired POST alone
   does not close the shelf or the populated brief. **Tenets 1, 2, 3 and 7;
   brief §9.**

4. **The resolution seed loses findings and crosses bins.** It omits 13
   of the 47 finding IDs in the sealed passes, including my Thread note
   defect and atlas-control finding and all three doc-drift findings.
   It places `finding.live_astra.summary_recipe` under a product defect;
   duplicate Run requests are tooling debt. The old placeholder-control
   findings also need revision-aware disposition: current `atlas.json:3355`
   clicks the receipt, and `atlas.json:5399` fills Note body and checks the
   saved words. Do not schedule the old selectors again. The additions
   below and in JSON preserve all 47 IDs, without changing a sealed pass.
   **Tenets 2 and 3; brief §§8–9.**

5. **Two owner decisions ask for the wrong kind of ruling.** D2 hands
   install diagnosis to the owner although the declared dependencies and
   source-install recipe can be checked in isolation. D1 should default
   to a synthetic meeting with inspectable decisions and action owners;
   asking him for material need not block preparation. D4's 2.2:1 option
   conflicts with the small-text rule. Present compliant looks separately.
   **Tenets 2, 3, 5 and 6; `README.md:23`, `pyproject.toml:86`,
   `docs/internal/UX-CANON.md` §C.**

CONDITIONS: Before the page is treated as settled, narrow the job labels,
attribute the unretained diagnostics, choose a bounded cut with explicit
proof dependencies, and reconcile the recorded dissent. Preserve every
finding and its bin, including already-addressed preparation debt. These
edits supply my positions; they do not silently rewrite Muad'Dib's page or
declare his acceptance. Before PHILO-2-06 closes, the lane owner must also
deliver the charter/merged-graph obligations in story 06 and carry the
open dissents into the phase status record.

MISSED: By owner cost: (1) the next-day decision-to-brief dependency;
(2) phone J5 evidence hidden behind Models; (3) the distinction between
the declared install and a test-extra runtime; (4) my kept Thread text
becoming an artifact instead of a note; (5) already-changed atlas controls
and the omitted doc-drift ledger. The first three can invalidate the next
useful-result claim; the others can send work to the wrong place.

TUESDAY: **Not yet** — the page makes accepted work look completed and
asks him to ratify ten stories before one useful meeting loop is proven.

UNKNOWN: No PR existed for `docs/philo-2-06-council` at this check
(`gh pr list --head …` returned `[]`); the reviewed artifact is the local
draft commit. No new run, owner install, real microphone, native delivery,
useful summary, terminal J6/J7 evidence, next-day brief or 90% working day
was verified. I reviewed the named proof below, not every census control
or every screenshot. The generated join and Phase 3 charter remain lane
deliverables, not outputs of this restricted two-file reply.

### Replies to §3 and the other pending positions

The §3 rows are left intact as Muad'Dib's text. This table answers every
"Astra to reply" row and the two rows presented as agreement.

| Finding | Astra's reply and evidence |
|---|---|
| Arrival never learns the summary landed | **Agree, source-backed.** `ChairHome.tsx:756` refreshes once; `useDeskChangedRefresh.ts:41` listens to `desk_changed`; `LiveCore.tsx:160,177` consumes intel frames. Import emits the desk event at `meeting_service.py:289`; the intel drainer does not. My static summary-slab trace did not establish arrival refresh. A terminal on-glass run is still owed. |
| Retrying summary says Nothing needs you | **Agree with the source defect; diagnostic unverified.** `ChairHome.tsx:628` counts only FAILED from `intelStatus`; its row's separate status/receipt logic is at `1949`. `intel_queue.py:513` retries a failed publication. Count a failure needing attention and expose the cause truthfully; do not turn all healthy queued work into a demand on the owner. |
| Missing model / rejected token opens New Project | **Agree.** My `static-astra.md` finding 1 follows `dictationRecovery.ts:69`, `FirstWords.tsx:473` and `applications.ts:348`. The microphone branch is a different, repaired edge. |
| Recall loses recent mode after a write | **Agree.** `useRecallController.ts:143` loads recent; `159` makes refresh a no-op without a query; `193` calls it after the write. Retry also loses recent mode (`103`; `RecallFace.tsx:375`). A targeted refresh repair does not require consolidating three faces. |
| Capture recovery has no face | **Agree.** `meeting_session/transcribe_loop.py:316` publishes actions; `LiveCore.tsx:218` keeps only the alert; `web/routes/meetings/crud.py:149` owns recovery. A source search finds no production frontend caller of that route. This is a missing recovery door, not observed audio loss; keep/checkpoint recovery needs its own capture scope. |
| Talk drops its words | **Agree.** `ChairHome.tsx:2345` leaves the callback empty and passes no grammar. `desk/components/MicButton.tsx:183` dispatches the no-grammar result to that callback; `pipeline` requests processing, not a destination. No live voice result was observed. |
| Dismiss is forever | **Agree for the Desk face, not data destruction.** No production face requests dismissed rows or calls projection restore. `holdspeak/db/projections.py:152` retains a real restore operation and clears the dismissal. My blocked live case does not prove the endpoint broken. The missing user return path is the defect. |
| J1 wired versus broken | **Agree on distinct edges.** Normal typed/deferred paths work; two named recovery destinations are broken. Neither verdict erases the other. |
| Import pass on 202 | **Agree on the row; disagree with the whole-job Works label.** The raw predicate proves admission. Completed import, length, transcript and no automatic summary still need terminal evidence; no product length defect follows from duration zero during import. |
| Desk memory is one thing (`res.desk_memory_one_thing`) | **Agree on confusing names; disagree that one face is the necessary remedy.** `SystemShade.tsx:180` distinguishes receipts and their targets; the shade, search and detail can have separate jobs with clear names. Tenets 3 and 5 do not require collapsing them. Repair Recall's stale result separately and defer a redesign until its job is chosen. |
| Arrival Record says something (`res.arrival_record_says_something`) | **Agree on source.** `ChairHome.tsx:2371` only starts recording; `RecordOrb.tsx:62` also opens Live. This does not prove a duration bug in Import, which is a different path. Defer native capture from the proposed imported-meeting result, with the missing feedback/recovery explicitly unpaid. |

### Findings restored, split or narrowed

These are dispositions of historical findings, not new executions. The
JSON keeps original finding IDs and Muad'Dib's existing positions. New
rows quote his sealed position where one exists; otherwise they say that
his council reply is not recorded. Agreement with a defect does not imply
agreement with the ten-story cut: `astra_disposition` records my proposed
scope separately from the draft's `disposition`.

| Finding(s) | Bin and Astra disposition |
|---|---|
| `finding.live_astra.summary_recipe` (mis-binned); `fnd.live.atlas_import_timing_and_run_order` (omitted) | **Tooling debt.** Split from arrival product wiring. Fix import waits, one Run trigger and correlated completion for proposed A2. Current recipes can fail with the client installed (`live-astra.md:59`). |
| `fnd.live.lane_runtime_lacks_meeting_client` | **Tooling debt**, with a separate install question. Scope the failed runtime accurately; retain a disposable documented-install check for A2. Do not assert the owner's installation failed. `pyproject.toml:86,90`; `live-astra.md:29`. |
| `fnd.astra.thread_keep_note_is_artifact` | **Product defect; deferred after the selected jobs.** `thread_service.py:1755` accepts `as_kind` but always records an artifact. The callback is real; its result type is wrong. Keep a named follow-up for Thread → Keep as note → Notes lookup. |
| `fnd.astra.atlas_controls_not_bound_to_results`; `fnd.atlas.placeholder_triggers` | **Historical tooling debt, selectors/predicate corrected before the live passes.** Current `atlas.json:3355,5399,5408` and the J9/J11 observations prove the specific repair. Stale-target, acknowledge and dismiss cases still lack successful live closure; track their remaining adapters/replies, not the removed placeholder clicks. |
| `fnd.faces.raw_controls_outside_the_library` | **Product debt; narrow the count claim.** Real raw buttons exist (`WorkbenchWindow.tsx:178`; `DeskToolInspector.tsx:274`). 183 raw-element handler sites are not 183 proven Button violations: the census also counts form/input/container handlers. Pay actual verb violations in touched faces; retain the wider census for classification. Tenet 5; UX-CANON A.1. |
| `fnd.live.run_refused_as_no_transcript_while_transcribing` | **Disagree with product-defect; tooling precondition demonstrated.** Preserve Muad'Dib's original bin in the sealed pass and record my proposed re-bin here. `meeting_intel_service.py:160` refuses an empty transcript truthfully; the intended no-assignment state was not reached. Open dissent §4.6. |
| `fnd.live.boundary_substitutions_missing`; `fnd.live.atlas_request_shapes_drift` | **Tooling debt.** Agree; `graph_walk.py:2262` and `inference_assignment_service.py:570`. Implement only the boundaries and request repairs required to prove the selected result now; park the rest with their blocked cases. |
| `fnd.live.atlas_predicates_and_states`; `fnd.live.passes_that_prove_less` | **Tooling debt.** Agree on wrong setup and weak results, with one correction: assigned speech is not healthy speech. `live-astra.md` J2 and finding 5 retain that distinction. Keep serial J10 replacement runs; the interrupted/overlapping originals never become proof. |
| `fnd.docs.desk_changed_comment_drift` | **Doc drift → PHILO-2-07.** Agree: `useDeskChangedRefresh.ts:15` contradicts the import event at `meeting_service.py:289`. Correct the current comment; retain the historical graph. |
| `fnd.docs.model_assignment_exposure` | **Doc drift → PHILO-2-07.** Agree that the curated record must name the user path (`ConciergeCore.tsx:569`; `ChairHome.tsx:953`). Correct the exact exposure/surface claim; do not treat the whole capability as live-verified. |
| `fnd.live.lane_brief_engine_address` | **Doc drift → PHILO-2-07.** The brief and atlas differ by `/v1`. Astra's authorized endpoint-only runtime input and Muad'Dib's original atlas both remain evidence; align future instructions without rewriting either pass (`astra-inputs/j6-address-resolution.json`). |

The three bins now have explicit homes. PHILO-2-07 owns factual correction
and graph maintenance. Its present criteria do not charter a wholesale
implementation of six rig adapters; the selected proof repairs below are
part of Phase 3's proposed cost. Remaining tooling debt stays listed.

### Counter-draft: the decision I would put before the owner

**Next useful result:** import one meeting with inspectable decisions and
action owners; see its summary arrive with the actual host; find that same
summary after restart; record one decision from it and see that decision
in the next day's dated brief. Start with synthetic material. A real owner
recording can follow when he judges usefulness. This proposal does not
certify microphone capture or native voice typing.

**Current result:** typed entry and immediate note custody work; one
SETUP state is visible; LAN configuration was observed; import completion
is unverified; planned-host disclosure is visible on desktop and still
unverified on the phone; summary and restart are unverified; the sweep
receipt opens Rhythm at both widths; an empty same-day brief survives;
decision creation is broken; Thought saves words but shows no save time.
Other populated brief paths and next-day generation remain unverified.

**Proposed minimum: three stories.** The estimates include the bounded
proof repairs, not only the code fix. They are estimates, not commitments.
Each UI change still needs the checked canvas design and 1440/393 shots.

| Priority / proposed story | Owner result and affected edges/states | Effort and dependencies | Evidence that closes it |
|---|---|---|---|
| **A1 Record the decision** (draft #1) | The existing decision face saves a decision from the reviewed meeting and can reopen it; create/read failure is named. `POST /api/decisions`; J10 populated/shelf setup. | **Hours** for the route fix and focused checks; **up to a day** for the existing face path and source reference. No engine dependency for the fix. The final meeting chain uses A2. | Face create → exact ID/text/source read back → reopen after reload, both widths. Exercise the shelf separately before claiming it works. No claim that this alone closes the brief. |
| **A2 See and find the summary** (draft #2, bounded J4/J5/J7 proof) | Completed import with length and transcript; one Run; actual host and summary appear on arrival without manual refresh; useful retry/failure state; same summary after hub restart. J4 import; J5 planned route; J6 queued/running/ready/failure; J7 restart/open. | **2–4 days**, including one synthetic meeting, documented-install reproduction, import wait, one-trigger recipe, lawful failure reply and retained restart evidence. Runs independently of A1. Fix install/length behavior only if the bounded check establishes a product fault. | Retain transcript, summary and terminal host receipt correlated to one meeting; compare planted decisions/actions without assuming usefulness. Unobscured pre-click host and terminal face at 1440/393; restart same isolated store, reopen same result in at most two moves. Owner usefulness remains a separate judgment. |
| **A3 Read the dated brief with that decision** (draft #4 plus missing dependency) | Brief load failure is distinct from absence, Retry reads again, date is visible, a new day's brief contains the decision; same-day regeneration retains the same ID. J10 absent/loading/failure/populated/reload/same-day/next-day. | **1–3 days**, including the minimum verified producer-clock boundary and case repair. Depends on A1 for a populated brief and A2 for the final meeting-to-brief chain. No machine-clock change. | First generate an empty brief, then record the decision. Prove the same-day identity contract; advance the isolated producer's day through a verified mechanism and prove a new dated brief includes the exact decision reference. Retain its words/ID after reload; show load failure and successful Retry at both widths. If the clock boundary cannot be proven, keep next-day completion open. |

A1 can land quickly while A2's proof is prepared; A2 is the largest owner
blocker. A3 closes the stated result. There is no dependency on cloud
Check, a model download, three-face consolidation, Thread notes or native
capture. The one end-to-end chain is closure evidence for these stories,
not a fourth generic audit phase.

**Deferred costs, in order:** Thought's current-write receipt remains
unpaid; native Talk/Record and capture recovery need their own verified
voice/capture result before anyone calls them usable; first-value error
destinations still mislead; receipt targets/restore and Recall's recent
refresh remain broken; Rhythm/Settings need honest local times; alternate
engine setup remains broken; Thread Keep as note and wider component
cleanup follow. Clear memory names can be designed with that work, without
presuming one combined face. Deferral is not permission to call those
jobs done. If live recording is required for the very next sitting,
replace the import-only scope explicitly and add its feedback/recovery
and lawful capture proof before starting; do not bury that work in A2.

| Owner decision | Recommendation | Alternative and cost | Evidence / dissent |
|---|---|---|---|
| Which next useful result? | The imported meeting → retained summary → decision → next-day brief, in A1–A3. | Add Thought or native capture now as an explicit scope increase; their proof and repair cost delays this result. | Three-story table; open dissent §4.3. |
| What material tests usefulness? | Prepare a synthetic architect meeting with known decisions, owners and actions; show him the input and output together. | He supplies a recording when ready. A pangram can test transport only and cannot close usefulness. | `finding.live_astra.summary_fixture`; D1's synthetic option adopted. |
| Who checks installation? | The lane verifies the documented source install in isolation and keeps the evidence. | Owner-led diagnosis adds a setup task to his first use; his current install stays unknown either way until observed. | `README.md:23`, `pyproject.toml:86,90`; dissent §4.4. |

D4 remains a separate visual choice with the contrast condition in §4.5.
No new owner answer is required to commit this counter-draft; it records
the choices for the council's ruling.

### Roots verdict and reviewed proof

I agree that the desk stops guiding when a result fails to return to its
face. The observed successes are narrower and worth keeping: the sweep's
Open reaches Rhythm, empty brief text remains after reload, and Thought
keeps the typed words. The shots also show the local clock beside an
unlabelled UTC time and a filing token where a save receipt is required.
Those are breaks in guidance under Tenets 3, 6 and 7. The arrival summary,
Talk and capture recovery findings are source traces awaiting live proof.
Workbench chrome alone cannot establish the modularity or usable working
day promised by Tenets 5 and 6. Neither pass measured that day.

Proof inspected includes the J4 row and J5 shots linked above; the J10
decision-create 500 records at
[1440](observations/astra/20260923T022649Z-case.j10.arrival_generate_brief.populated-astra-1440/observation.json)
and [393](observations/astra/20260923T022704Z-case.j10.arrival_generate_brief.populated-astra-393/observation.json);
Rhythm at
[1440](observations/astra/20260923T022312Z-case.j9.shade_receipt_open.rhythm_face-astra-1440/after.png)
and [393](observations/astra/20260923T022332Z-case.j9.shade_receipt_open.rhythm_face-astra-393/after.png);
Thought at
[1440](observations/astra/20260923T024756Z-case.j11.thought_keep.kept-astra-1440/after.png)
and [393](observations/astra/20260923T024837Z-case.j11.thought_keep.kept-astra-393/after.png),
with its exact saved words in each raw record; and the serial replacement
brief runs at
[1440](observations/astra/20260923T023227Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440/observation.json)
and [393](observations/astra/20260923T023602Z-case.j10.arrival_generate_again.same_day_idempotent-astra-393/observation.json)
and their after shots. No unretained diagnostic is included as observed
proof.

### Validation of this reply

- The repository graph validator returned `OK` for all four sealed JSON
  passes. System Python lacked `jsonschema`; the successful check used an
  isolated HOME with `uv run --no-project --with jsonschema --with pyyaml`.
  It imported only the graph validator, not the product.
- The resolution audit found **47 finding IDs, each exactly once, in 20
  unique resolutions**, with no pending Astra position. Source bins are
  preserved; the one proposed re-bin is explicit. All added evidence
  paths and all Markdown file links exist.
- Muad'Dib's Markdown outside §4 is byte-identical to `20eafcb7`; his
  existing JSON positions and draft dispositions are preserved.
- `.githooks/dw check holdspeak-philo` returned `dw check: ok`.
  `git diff --check` passed. Only the two council files changed;
  PHILO-2-06 remains in-progress. No product tests or runtime were run.
