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

None yet. Astra's counter-draft fills this section; the owner rules any that remain.

## 5. The roots verdict — the observed faces against Tenet 6

The owner said: ninety percent of the day on the desk, interfaces that guide, Workbench 2.0+ on steroids. On the eleven jobs the desk **guides on the way in**: the SETUP row names what is missing, the planned host is beside the verb before the click, the sweep receipt opens the face it belongs to, the brief keeps its words. The desk **stops guiding where a result must come back to the face**: the summary lands in the store and the arrival keeps saying QUEUED; the thought's words are kept and the face says only a filing state; a decision cannot be recorded at all; time is shown in a zone he does not live in; a receipt's Open sometimes opens nothing. The chrome is Workbench; the seams are plumbing. Phase 3 is the seams. This verdict is on the observed faces; it does not measure a working day, and it does not judge the summary's usefulness, which nobody has seen on real material (D1).

## Astra — check and counter-draft

*(pending)*
