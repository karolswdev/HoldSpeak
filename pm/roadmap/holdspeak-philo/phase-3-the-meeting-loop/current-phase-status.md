# Phase 3 - The Meeting Loop

**Last updated:** 2026-09-24 (exit 1 proved by the integrated PHILO-4-02 lane; owner sitting remains open).

## Goal

One imported meeting, its summary arriving on the arrival with the actual host, found again after a restart, one decision recorded from it and seen in the next day's dated brief. This is the council's "next useful result" (`docs/internal/philo/graph/COUNCIL.md`, the decision page). A fourth story, the thought's receipt, is included pending the owner's ruling on D3.

## Authority

The owner, 2026-09-22: "should there be a need to act (and, let's be honest, there will be) - then the outcome is codified as Phase 3 of Philo and real engineering and come-to-Jesus-so-HoldSpeak-doesn't-lose-its-spirit-moment happens there and then." This phase is that outcome. The council record is the charter's source; the owner ratifies this charter and rules the open dissent (D3).

## The roots

"Don't forget our roots here … we're actually intended to work 90% of our time on the desk, with beautiful, cohesive interfaces that guide us, and all of this grounded in the ideology of Workbench 2.0+ on steroids." The council's roots verdict: the desk guides on the way in and stops guiding where a result must come back to the face. This phase is the seams: the summary comes back to the arrival, the decision can be recorded, the brief tells the truth about itself, the thought tells him when his words were kept.

## Status of this charter

RATIFIED by the owner, 2026-09-23: D1 synthetic meeting material first (his recording when he chooses); D2 the lane reproduces the documented install in isolation; D3 FOUR stories (04 is in); D4 the built dark ember stays. Build starts.

## Scope

- **In:** the four stories below and their closure evidence; the proof repairs named per story (import wait, one-trigger recipe, a lawful failure reply, restart evidence, the producer-clock boundary, the synthetic meeting, the isolated install check).
- **Out:** the council's deferred list (first-value recovery destinations, receipt targets and restore, Recall refresh, local time, arrival Record feedback, Concierge alternatives, Thread Keep-as-note, raw controls) — real costs, not dependencies; PHILO-2-07 owns the tooling and doc corrections.

## Exit criteria (evidence required)

- [x] The end-to-end chain runs on the rig with retained observations at 1440 and 393: import completes → summary on the arrival with the actual host → the same summary after a restart → a decision recorded → the next producer-day's dated brief contains it. **Paid by [Phase 4 The Morning](../phase-4-the-morning/current-phase-status.md) exit 1 on the PHILO-4-02 lane (2026-09-24): as-written step 5 `20260924T072614Z` at 1440 and `20260924T072514Z` at 393 PASS; one Generate, decision first and all nine row hit points owned; new id/date, old triage and cumulative restart proof retained. [Integrated evidence](../phase-4-the-morning/evidence-story-02.md). The PR remains open; no owner sitting is claimed.**
  **Earlier closure (2026-09-24, before Phase 4).** Steps 1–4 PASS at both widths (`assets/closure/`: 1 `20260924T011648Z`/`012020Z`, 2 `012038Z`/`012106Z`, 3 `012132Z`/`012202Z`, 4 `012742Z`/`012814Z`). Step 5 as written is BLOCKED at both widths (`013355Z`/`013440Z`): with yesterday's brief rows untriaged the Arrival draws no Generate verb (`ChairHome.tsx:1260`). After Ack on every row, the next-day brief has the decision under a new id (protocol), but the Arrival shows it only behind `1 more` (`013738Z`/`014018Z` FAIL); one more move shows it in the brief view (`014258Z`/`014339Z` PASS). Detail: [final summary](final-summary.md).
- [x] Every repaired seam has a fence that failed pre-fix. (Scope: the A1–A4 PRODUCT repairs, cited per story in final-summary.md; the closure's two rig-tooling edits have no dedicated fence and are ledgered there.)
  Per story, from the checks and evidence (not re-derived):
  A1 — `tests/unit/test_philo3_01_decision_route.py` against the pre-fix 500 from `git show 7ce95358` (`story-01-record-the-decision.md`:36); `philo301DecisionFace.test.tsx` 4/4 fail on the old head (story-01:42); `philo301DecisionNoLoss.test.tsx` and `philo301RetryKept.test.tsx` fail on the previous code (story-01:40; Astra r2 probes fail/pass); `tests/e2e/test_philo3_01_receipt_hits.py` pre-fix Chair bottom 866 vs 800, capture bar 777 vs dock 727, document 918 vs 852 (story-01:38).
  A2 — round one: queue 4/4, detail 6/6, Arrival vitest 11/11 fail on a `git archive origin/main` copy ([checks/story-02-built-muaddib.md](checks/story-02-built-muaddib.md):15); round two on `dfbaccd5`: pytest 7 failed, vitest 9 failed (plain cause), `test_philo3_summary_counts.py` both fail on `assert []`, refresh 1 failed / 11 passed (:48–50); install fence before-state from the retained log only (:15). Exception-path causes (`intel_queue.py:557`, `:642`) are NOT repaired and have no fence (ledgered).
  A3 — the pre-fix Chair source makes 5/6 new tests fail ([checks/story-03-built-astra.md](checks/story-03-built-astra.md):15); the recipe fence refuses every mutation (advance removed, moved, invalid; early empty generate) (`test_philo_graph_atlas.py`, r2 :41).
  A4 — 6/7 receipt tests and 3/4 floor tests fail on the parent ([checks/story-04-built-astra.md](checks/story-04-built-astra.md):13); the 600 px layout fence fails on the pre-fix CSS (:37).
  The closure's own rig changes (`_restart_detail` read fallback; no unfilled read is sent) are tooling and have no separate fence.
- [x] The owner's sitting on the finished chain, with his words as the phase's final summary; technical completion and usefulness reported separately. **WAIVED by the owner 2026-09-24 ("good to go, no sitting reqd..."): accepted, not observed; his words on usefulness are not claimed. The technical chain (exit 1, closed against Phase 4) stands as the record; usefulness stays PARTIAL as measured (`final-summary.md`).**
  **Open — his.** The technical record and the usefulness map are in [final-summary.md](final-summary.md); his words are not.
- [x] (if D3 includes it) The thought's receipt on the face, canvas-ratified, both widths. (Evidence: the retained receipt walks `assets/story-04-shots/1440-*.png`, `393-*.png`; Astra's RATIFY r2 in `checks/story-04-built-astra.md`; the owner's canvas ratification recorded in merge `8c078662` of #614 — his original utterance is not in the tree.)
  D3 ruled A4 in. The owner ratified the canvas ([assets/story-04-canvas/](assets/story-04-canvas/README.md); merge `8c078662`, PR #614: "the owner ratified the canvas"); Astra r2 RATIFY ([checks/story-04-built-astra.md](checks/story-04-built-astra.md):42); rig `case.j11.thought_keep.receipt_time` at 1440 `20260923T060140Z` and 393 `20260923T060148Z` ([evidence-story-04](evidence-story-04.md)).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-3-01 | Record the decision (A1) | done | [story-01-record-the-decision](./story-01-record-the-decision.md) | [evidence-story-01](./evidence-story-01.md) |
| PHILO-3-02 | See and find the summary (A2) | done | [story-02-see-and-find-the-summary](./story-02-see-and-find-the-summary.md) | [evidence-story-02](./evidence-story-02.md) |
| PHILO-3-03 | Read the dated brief with that decision (A3) | done | [story-03-read-the-dated-brief](./story-03-read-the-dated-brief.md) | [evidence-story-03](./evidence-story-03.md) |
| PHILO-3-04 | The thought's receipt (A4) | done | [story-04-the-thoughts-receipt](./story-04-the-thoughts-receipt.md) | [evidence-story-04](./evidence-story-04.md) |

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The route and the face | 01 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-3-01 | feat/philo-3-01-decision |
| The summary | 02 | Astra (Luna) | Muad'Dib | ../wt-philo-3-02 | feat/philo-3-02-summary |
| The brief | 03 (after 01, 02) | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-3-03 | feat/philo-3-03-brief |
| The thought | 04 | Muad'Dib (Opus 5.5; canvas first, owner ratifies) | Astra | ../wt-philo-3-04 | feat/philo-3-04-thought |

## Where we are

2026-09-24 07:29 UTC: exit 1 proved on the integrated PHILO-4-02 lane by actual as-written closure walks at both widths, without the earlier triage/fold detour. [Phase 4 evidence](../phase-4-the-morning/evidence-story-02.md) retains real LAN summary/restart, unchanged day-one DB rows and an unobscured first decision row. Separate breakage variants also pass. The lane PR remains open for Muad'Dib. Exit 3 (the owner's sitting), ASR/summary usefulness and the other ledgered costs remain open.

2026-09-24 01:45 UTC: CLOSURE CHAIN on the rig (Muad'Dib's lane; Astra's check owed). Actual LAN engine `Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf` at 192.168.1.43:8080; one hub and one fresh HOME per run; 24 observations kept, none selected. Steps 1–4 PASS at 1440 and 393. Step 5 is BLOCKED as written: no Generate verb while yesterday's brief has an untriaged row. With triage the dated brief has the decision, but the Arrival hides it behind `1 more`. Found: the next-day brief can answer 500 when a breakage row repeats (`monday_brief_service.py:546`, `:305`). Usefulness partial: SQLite, Maya Chen and Priya's action lost in 22/22 summaries; owners and due dates lost on the Arrival rows. Exits 2 and 4 flipped; 1 and 3 open. [Final summary](final-summary.md).

2026-09-23 18:30: A2 second Muad'Dib counsel on Astra's round two (PR #616 @ 0624a6a3): RATIFY-WITH-CONDITIONS, both paid in the same commit (the glass-probe wording corrected and its lost cross-layer coverage ledgered; main merged). Every round-one condition verified paid with pre-fix reds reproduced: plain PROVIDER FAILED cause, the queue count seam, refresh continuity, the transcript fold on the library Disclosure, no raw ids. Ledgered for closure: exception-path failures still carry queue wording; aftercare covers the fold at 393; ASR instability; `1 WORDS`. Merge on green CI.

2026-09-23: **A2 BUILT, technical completion verified**. One completed synthetic import → one Run → actual LAN host and summary on Arrival → identical summary/receipt after restart, at both widths. Full web green; Python fallout fixed or reproduced on main and classified. [Lane record](summary-lane-record.md) separates this from **partial usefulness** and the pending owner sitting. Muad'Dib's [recorded counsel on built](checks/story-02-built-muaddib.md) is RATIFY-WITH-CONDITIONS. Round-two corrections and twelve new walks pass across the pre-integration and integrated builds. A3/main is integrated through `5de5d0c3`. Full web: 2,813 tests pass; full Python: 11,559 pass / 12 fail, with nine inherited failures reproduced on main and three old lane expectations/probes corrected by an independent 22-test green capture. Evidence is appended without re-flipping A2. The branch is pushed for Muad'Dib's re-read; his verdict is not presumed. The post-push generated boundary-census drift is corrected and the complete local documentation CI sequence passes. The phase exit stays open.

2026-09-23 19:05: A3 BUILT on the ratified canvas — a brief load failure is named with Retry, READING… while the read is open, No brief yet only on null, the period and generated date on the face; the producer-clock seam (`MondayBriefService(clock=)`, wired through the web server) lets the rig advance the brief's day without touching the machine clock; the next-day brief contains the recorded decision with a new id at both widths; the old J10 next-day case is applicable again. Astra counsel next. A2 (Astra) finishing its proof chain.

2026-09-23: A4 BUILT on the ratified canvas — the Thought foot shows KEPT · time / SAVING… / DID NOT SAVE · cause + Retry / CHANGED ELSEWHERE + Reload with the filing line below; every state shot on a real hub at both widths; the library receipt line raised to the 12 px floor. A1 on PR #613 (Astra counsel). A2 (Astra) in flight.

2026-09-23 16:15: A1 RATIFIED by Astra on round five (RATIFY, no conditions) and merged; the owner passed the shots and ruled the 393 receipt row. A4 merged. A2 (Astra) building the ratified Arrival face and the proof chain. A3 next.

2026-09-23: A1 BUILT — the decisions route saves and reads back (one line); the existing face proven on a real hub at both widths; the shelf passes as protocol cases; four face findings ledgered for the council (New Decision opens nothing on the Chair; no title at create; a failed read is only an aria-label; raw Retry/Dismiss). A2 (Astra) and A4 (build) in flight.

Chartered 2026-09-23 by the council; RATIFIED by the owner the same day (D1–D4). Lanes 01 (Muad'Dib) and 02 (Astra) start in parallel; 04's canvas is drawn in parallel; 03 follows 01 and 02.

PHILO-3-02 checkpoint, 2026-09-23: install committed first as `794f07ff`, then queue as `a28c19f9`, both through the gate without closing a story. The independent base install from fresh source/HOME/venv passes; 17 install/client and 77 queue tests pass, with pre-fix failures retained. The corrected [eight canvas boards](assets/story-02-canvas/README.md), with four additional phone footer views, were published by Muad'Dib and OWNER RATIFIED on 2026-09-23 ("Ratify, build it"). The Arrival and actual-atlas proof seams are building. Technical summary completion and owner usefulness remain separately unverified. See [lane record](summary-lane-record.md) and [check record](checks/summary-design-muaddib.md).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The summary is technically complete but useless to the owner | medium | synthetic material with planted decisions; usefulness reported separately; his sitting decides | he says it is not useful |
| The documented install lacks the model client | corrected at package boundary | D2 before/after install retained; `794f07ff` includes endpoint client in core | real summary still requires the later LAN rig proof |
| The producer-clock boundary needs product change | medium | the smallest mechanism that moves the producer's date under test; never the machine clock | no mechanism without touching production code paths beyond a seam |
| Scope creep from the deferred list | high | the deferred list is explicit; a new story needs the owner's word | a fifth story appears |

## Decisions made (this phase)

- 2026-09-24 — exit 3 (the owner's sitting) WAIVED by the owner ("no sitting reqd..."): accepted-not-observed; the phase's open items stay ledgered — Muad'Dib.

- 2026-09-23 — Astra's closure check on #619: RATIFY-WITH-CONDITIONS on the record (conditions paid in the same commit: the phone face claim, the collision condition, box 2 scope, box 4 links); counsel: charter A5 (Generate reachable with untriaged rows; the decision inside the visible rows at both widths; no id collision across briefs; 1–2 days). The owner: "yes close and open" — Phase 3 closes with exits 1 and 3 open; the A5 set opens as Phase 4 The Morning — Muad'Dib.

- 2026-09-24 — closure run by Muad'Dib's lane: the chain written as seven cumulative atlas cases (`case.closure.chain.*`, atlas-phase3 `phase3-closure`); exit 1 left open on a BLOCKED step 5; the Generate-verb gap, the breakage-id 500, the `1 more` cap and the lost owners/dates ledgered for the owner and the council, not repaired here.

- 2026-09-23 — owner ruled summary open, transcript collapsed by default, word count on the existing fold, one click to open; applied in A2 round two. Aftercare obstruction and ASR instability are ledgered, not repaired in A2.

- 2026-09-23 — chartered from the council's decision page; A1–A3 per Astra's counter-draft, A4 per Muad'Dib's ruling, D3 open — the two brains.

## Decisions deferred

- Tooling flaw found by Astra (A1 r3): `scripts/check_web_baseline.py` compares inherited failures by test NAME, so a new failing path under a baselined name is hidden ("zero branch-new" was false for `containerQueryLaw.test.ts`); key the comparator on id + failing file/path — a tree task after this phase.

- (none) D3 ruled: A4 is in; lane owners assigned above.

## Open dissents

- §4.3 of COUNCIL.md, verbatim there: Astra A1–A3; Muad'Dib A1–A4.
