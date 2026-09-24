# Phase 3 — The Meeting Loop: final summary

**Technical closure 2026-09-24 (UTC).** All four stories are merged: A1 #613, A2 #616, A3 #615, A4 #614. The chain ran on the rig at 1440 and 393. Steps 1–4 pass. Step 5 does not pass as written. Exit 1 stays open. The owner's sitting (exit 3) stays open. It is his.

Technical completion and usefulness are reported separately below.

## What he can do now that he could not on 2026-09-22

- **Record a decision.** Search → New Decision opens the decision window in Edit. Done titles it by the first line. A failed write or read is named with Retry. On 2026-09-22 the route answered 500.
- **See the summary on the Arrival.** One Run on the meeting row. The summary lands on the row with the contacted host (`192.168.1.43 · LAN`). No refresh. On 2026-09-22 no summary was ever observed on the rig.
- **Find the same summary after a restart.** Same meeting id, same text, same run receipt.
- **Read a dated brief with the decision.** The next producer-day's brief has a new id and the row `Review decision: <title>`. A failed brief read says so, with Retry.
- **See when his thought was kept.** The Thought foot says `KEPT · <time>`, `SAVING…`, `DID NOT SAVE · <cause>` with Retry, or `CHANGED ELSEWHERE` with Reload.

## His mornings

- **Monday after a meeting:** import it, press Run once, read the summary on the Arrival with the host on it. Restart the hub; it is still there.
- **After that meeting:** write the decision on the desk. It reads back after a reload.
- **The next morning:** the brief can carry that decision. **But:** if yesterday's brief still has an untriaged row, the Arrival has no Generate verb. He must Ack every row first. Then the new decision is the fifth row, behind `1 more`. See "What he still cannot do".

## Both brains, per story

| Story | Built by | Checked by | Verdict | Record |
|---|---|---|---|---|
| A1 Record the decision | Muad'Dib | Astra | DO-NOT-RATIFY ×2, RATIFY-WITH-CONDITIONS ×2, **RATIFY r5** at `70ba1850`; merged #613 | [checks/story-01-built-astra.md](checks/story-01-built-astra.md) |
| A2 See and find the summary | Astra (Luna) | Muad'Dib | **RATIFY-WITH-CONDITIONS ×2**, both paid; merged #616 | [checks/story-02-built-muaddib.md](checks/story-02-built-muaddib.md) |
| A3 The dated brief | Muad'Dib | Astra | RATIFY-WITH-CONDITIONS r1, **RATIFY r2** at `9e9f913b`; merged #615 | [checks/story-03-built-astra.md](checks/story-03-built-astra.md) |
| A4 The thought's receipt | Muad'Dib | Astra | RATIFY-WITH-CONDITIONS r1, **RATIFY r2**; owner ratified the canvas; merged #614 | [checks/story-04-built-astra.md](checks/story-04-built-astra.md) |

This closure is authored in Muad'Dib's lane. Astra's check of it is owed before it is acted on (TWO-BRAINS §1).

## The chain on the rig

One hub per run, a fresh mkdtemp HOME per run, the actual LAN engine. `GET http://192.168.1.43:8080/v1/models` names `Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`, `owned_by: llamacpp`. All 24 observations have their database under their own run HOME, also after each restart (checked by script). Nothing touched the owner's desk. Cases: `docs/internal/philo/graph/atlas-phase3.json`, `case.closure.chain.*`. Each case runs every earlier link in the same hub before its trigger. Runs: [`assets/closure/`](assets/closure/). Captures: [evidence-story-02.md](evidence-story-02.md), 2026-09-24T01:16Z–01:45Z (the chain has no story; PHILO-3-02 owns the summary).

| Step | Predicate | 1440 | 393 | Result |
|---|---|---|---|---|
| 1 Import complete (J4) | trigger waits for `transcription_status: complete`, duration > 0, ≥ 1 segment; minted id is `/meetings/0/id` | `20260924T011648Z` (import 30.6 s) | `20260924T012020Z` (8.7 s) | **PASS** |
| 2 Summary on the row with the host (J6) | `192.168.1.43` inside `[data-testid=summary-record-attempts]`, which draws only inside a non-empty summary slab | `20260924T012038Z` (7.6 s) | `20260924T012106Z` (7.2 s) | **PASS** |
| 3 Same summary after a restart (J7) | the reloaded face text equals the summary read before the restart; restart record: `summary_retained`, `receipt_retained`, `meeting_identity_retained` all true | `20260924T012132Z` | `20260924T012202Z` | **PASS** |
| 4 Decision recorded through the face (A1) | `/decisions/0/title` = `Keep summary retrieval on the local desk` (planted decision two, source in Context) — persistence by protocol; the 393 `after.png` shows the decision window with empty fields, so a settled visible save confirmation is NOT established | `20260924T012742Z` | `20260924T012814Z` | **PASS** |
| 5 Next-day brief has it (J10), as written | Generate again on the Arrival after the day advance; the ledger holds `Review decision: …` | `20260924T013355Z` | `20260924T013440Z` | **BLOCKED** — no Generate verb |
| 5, triage detour | Ack every day-one row, then Generate again | `20260924T013738Z` | `20260924T014018Z` | **FAIL** on the Arrival face — the row is behind `1 more`; the API brief has it |
| 5, one more move | as the detour, then the fold (`1 more` at 1440, `2 more` at 393); the brief view's lookback rows hold the title (DOM containment; at 393 `REVIEW DECISION` sits at the bottom with its title under the footer — readable delivery NOT shown) | `20260924T014258Z` | `20260924T014339Z` | **PASS** |

Step 5 facts. The day-one brief has no decision (setup check). The producer clock read `advance_days=1 now=2026-09-24T…`. The trigger answered 200 with a new id, `GENERATED SEP 24`, and `sections.decisions = [Review decision: Keep summary retrieval on the local desk]` in every detour run. Protocol: the dated brief contains the decision. Face: two moves, and only after triage.

All runs are kept. None is selected:

- `20260924T011751Z`, `012339Z` (step 5 as written, before the window-close step): BLOCKED, the same missing verb.
- `20260924T011937Z` (detour, 1440): BLOCKED. The decision window covers the BRIEF section's Generate again.
- `20260924T012420Z` (detour, 393): FAIL. The next-day Generate answered **500** (`UNIQUE constraint failed: monday_brief_items.id`). The rig caused the breakage row that collides: a restart snapshot sent `GET /api/decisions/{decision_id}` with the placeholder unfilled, and the hub recorded the failed read as a pipeline breakage. The product defect is real (below). The rig now never sends an unfilled read (`scripts/graph_walk.py` `snapshot`).
- `20260924T012231Z`, `012305Z` (step 4, before that rig fix): PASS, with the same literal read in the record. Re-run clean as `012742Z`, `012814Z`.
- `20260924T012848Z`, `013121Z` (detour, first recipe): FAIL, the same three-row cap (`1 more` at 1440, `2 more` at 393).
- `20260924T013558Z` (one more move, 1440): BLOCKED. The model made three actions, so two Acks were not enough. The Acks are now count-tolerant.
- `20260924T013640Z` (one more move, 393): PASS.

**Technical completion: steps 1–4 pass at both widths. Step 5 passes by protocol, and on the face only after a detour. Exit 1 stays open.**

## Usefulness (partial, mapped, no run selected)

Source: `tests/fixtures/philo3_architect_meeting.txt`, WAV sha256 `165ea975…d47b2`. 22 of the 24 runs produced a summary; all 22 are counted.

| Planted | Got (22 summaries) | Result |
|---|---|---|
| D1 use SQLite for the local meeting ledger | ASR "SQ like" in 22/22; SQLite in 0 summaries | **Lost** (corrupted) |
| O1 Maya Chen | "Mayyachan" in 22/22 ASR, summaries and actions; "Maya Chen" in 0 | **Corrupted** |
| A1 Maya writes the migration plan by Friday | action + Friday in 22/22 (owner corrupted) | Recovered, wrong owner |
| D2 keep summary retrieval on the local desk after a hub restart | "restart" in 22/22; "local desk" in 9/22 | **Partial** |
| O2 Leo Martinez | action owner in 22/22 | Recovered |
| A2 Leo tests restart retrieval on Tuesday | action + Tuesday in 22/22 | Recovered |
| D3 use a recorded provider reply for isolated rig tests | in 19/22 summaries | Mostly recovered |
| O3 Priya Shah | in 16/22 summaries; a Priya action in 4/22 | **Partial** |
| A3 Priya adds the named failure fence before ship | ASR "named failure offense" in 22/22; "fence" in 0; the 4 Priya actions are "Research …", "Start scanning for …", "Use a recorded provider reply …", "Add named failure offense before ship"; none has a deadline | **Lost** |
| The decision in the dated brief | typed by the rig from planted D2; in the next-day brief in every SUCCESSFUL next-day generation (the retained detours also include BLOCKED and HTTP 500 outcomes) | Delivered by protocol (typed, not extracted) |

What the face loses after extraction: the Arrival's NEEDS YOU and BRIEF rows say `UNASSIGNED` and `NO DUE DATE` for both actions. The structured actions carry Mayyachan/Friday and Leo Martinez/Tuesday. The brief view shows `Due Friday` but still `UNASSIGNED`.

ASR on the same WAV: 76–299 words; 10 of 22 transcripts carry a repetition or garbage run (`さ`×223, `好`×446, "Research"×20, "scanning", "Chapter", "eagle", "Renege", "Robert", `prpr…`, `ander…`, `ajiaji…`, `<|ar|>`), always at Priya's action.

## What he still cannot do

New in this closure (not repaired here):

1. **Make the next brief from the face while yesterday's has an untriaged row.** `BriefSection` (`web/src/desk/chair/ChairHome.tsx:1260`, `:1980`) has Ack/Defer but no Generate. Generate again exists only when no row is untriaged (`:1283`). The brief view offers Generate only when there is no brief (`web/src/desk/pullouts/views/BriefView.tsx:297`). A3's next-day case passed only because its day-one brief was empty.
2. **Generate the next brief when a failure already stored in an earlier brief is selected again.** Breakage items have source-derived ids (`brief-break-pipeline-{event_id}`, `holdspeak/services/monday_brief_service.py:546`; connectors `:575`). Selection keeps the latest failure per service/method or connector over a window that starts at the preceding business close (`:516`, `:145`); when the same failure is selected into a second brief, the plain INSERT (`:305`) reuses its id against a table-wide primary key (`holdspeak/db/schema.py:2441`): 500. Seen once (`20260924T012420Z`, hub log in the observation), with a rig-caused failure row; a Wednesday-evening failure selected Wednesday evening and again Thursday morning takes the same path; a newly encountered failure need not (Astra, closure check). Not reproduced without the rig cause.
3. **See the new decision on the Arrival.** Three brief rows show; the decision was behind the fold (`1 more` at 1440, `2 more` at 393) in every successful next-day generation; after opening the fold at 393 its title sits under the footer (`20260924T014339Z/after.png`).
4. **Reach the brief verbs with a decision window open at 1440.** The window covers the BRIEF section's verbs (`20260924T011937Z/blocked.png`).
5. **See owners and due dates on the Arrival.** See Usefulness.
6. **Read the brief view without raw names.** It prints `MeetingIntelService.run_intelligence` and its JSON (`20260924T014339Z/after.png`). At 393 the decision row is below the window's fold.

Carried from the council ([COUNCIL.md](../../../../docs/internal/philo/graph/COUNCIL.md), "Deferred, explicitly"): first-value recovery destinations; capture recovery's face and Talk's dropped words; receipt targets and restore; Recall's refresh after a write; Rhythm/Settings local time; the arrival's Record feedback; the Concierge download and cloud Check; Thread's Keep-as-note; raw controls on touched faces. Microphone capture and voice typing into another app stay his sitting.

Found by CI on main, not by the rig (Muad'Dib, 2026-09-23): A4's receipt lines (`KEPT · <time>`, `IN INBOX`, both `role=status` inside the Thought region) break the HS-201-12 thought-note glass fence at both widths with a strict-mode locator violation (`tests/e2e/test_hs201_12_thought_note_glass.py`, four cases; main run at `497d90f3`, unchanged by #618 and #616). The fence's `get_by_role("region", name="Thought")` now matches more than one node. A fence repair or a role change on the receipt lines is owed; the face is as ratified.

Carried from the A2 ledger ([deferred-ledger.md](../../../../docs/internal/philo/phase-3/summary/round-2/deferred-ledger.md)): the aftercare panel covers controls (seen again, `20260924T012106Z/after.png`); ASR instability; the lost cross-layer overlap probe; exception-path failures still print queue wording (`intel_queue.py:557`, `:642`); `1 WORDS` has no singular (`web/src/pages/cores/history/TranscriptWell.tsx:74`). Also: the supersede route shadowed with no change callbacks (A1); `.surface-footer-readiness` at 10 px (A4); the Floor/list view at 393 with the receipt row standing (A1 unknown).

## Open ledger

- **Four Constitution article amendments**, proposed in Phase 201, are unruled. They are his.
- **The baseline comparator** (`scripts/check_web_baseline.py`) matches inherited failures by test name. A new failing path under a baselined name reads as "zero branch-new". Key it on id + failing path. Tree task.
- **Rig tooling this closure changed:** `_restart_detail` reads the meeting from `expected.reads` when the case observes a face; `snapshot` never sends a read or protocol path with an unfilled `{name}`. Neither has its own fence; the atlas, calibration, summary-rig, producer-clock and http-fault suites pass (155).
- **Exit 3, the owner's sitting on the finished chain,** is open. His words are the phase's usefulness verdict.
