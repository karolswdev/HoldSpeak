# Phase 6 — The Honest Morning — final summary

**CLOSED 2026-09-25** on the owner's review of the closing shots ("Reviewed — close it"): rehearsed, owner-reviewed, not a sitting.

**Status: exit 3 MET on the closing brief's rule; exits 1 and 2 unflipped in the status file (their proof is the per-story evidence below; the flip is the orchestrator's); exit 4 OPEN (2026-09-25).** Five of five stories merged (#646 lane A 01/02, #647 lane B 04/05 and 03's zero omission, #648 the ratified canvas, #649 03's placement; main `f93e76fa`). The closing chain ran on merged main at 1440 and 393: the Phase 4 exit-1 case AS WRITTEN PASS at both widths with the real LAN engine; the reworded S5 `.op` case PASS; the empty-VTT import case PASS at both widths. The Phase 5 rehearsal driver ran three times and was BLOCKED three times by the two INHERITED driver defects (tool selection twice, resource-list reconciliation once); exit 3 closes with that block recorded, not with a completed rehearsal. At 393 the closing case's shot frames row 1 only: the receipt, the caption and the meeting badge sit below the sticky capture bar, so at 393 those three are wire-proved, not glass-proved (the checklist below). Exit 4 (rehearsed, owner-reviewed shots) stays OPEN: Muad'Dib publishes the shots for the owner's review. No sitting is claimed.

## What he can do now that he could not on 2026-09-24

- See a failed import as FAILED on the Arrival, with its short cause in the open well (`IMPORT` / `FAILED  LAST ERROR · NO TRANSCRIPT LINES`), never SAVED.
- Read one time on the brief: the caption and the receipt both read the producer's time in one format (`GENERATED SEP 26 00:00` / `Brief ready · 3 items · SEP 26 00:00`).
- Trust the brief's counts: the head (`3 THINGS WAITING`) and the receipt (`3 items`) agree on the closing run; where they differ, the difference is the lawfully hidden rows (THIS WEEK, shelved), and each label says what it counts.
- Read human words on the brief: `Summary requested: <title>`, `Meeting recorded: <title>`, `Decision did not load` — no `Service.method` on the Arrival or in the stored items.
- See MEETING READY in flow above the capture bar with no zero token (`2 open`), covering nothing, at 1440 and 393.
- Get one Broke row for one missing decision (1:1, both transports).
- Read the decision body at once after Done (every frame from the first read through terminal observation, both widths).

## The morning on the rig

All runs on `feat/philo-6-close` = main `f93e76fa` (rig 1.3.0), each in a fresh HOME with its own hub; the DB path of every run is under `/private/var/folders/…/T/` (the `RUNTIME:` line of each capture). Captures: `evidence-story-02.md` §"Captured run — 2026-09-25T05:59:16Z" through `…06:08:54Z`. Shots and observations: `assets/closing/`.

| # | Run | Width | Engine | Verdict | Predicate / outcome |
|---|---|---|---|---|---|
| 1 | `20260925T055916Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-1440` | 1440 | real LAN | **PASS** (70.3 s) | `Review decision: Keep summary retrieval on the local desk` readable in row 1 (x 256 y 359), hit-test owned by the row |
| 1 | `20260925T060047Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-393` | 393 | real LAN | **PASS** (32.6 s) | the same row readable (x 12 y 356), hit-test owned by the row |
| 2 | `20260925T060007Z-case.closure.chain.s5_next_day_brief_with_breakage.op-astra-1440` | headless | real LAN | **PASS** (21.4 s) | row 0 reads `Decision did not load`; its id captured; one Broke row; the next-day brief's `sections.decisions` non-empty. Zone `Etc/GMT+10`, local 20:00, after close |
| 3 | `rehearsal/20260925T060112Z-his-words-real` | 1440 + 393 | real LAN | **BLOCKED** (241.8 s) | turn 3: Codex chose `door.add_item`, not `desk.create` (tool selection) |
| 3 | `rehearsal/20260925T060532Z-his-words-real` | 1440 + 393 | real LAN | **BLOCKED** (202.6 s) | turn 3: `door.add_item` again (tool selection) |
| 3 | `rehearsal/20260925T060854Z-his-words-real` | 1440 + 393 | real LAN | **BLOCKED** (227.8 s) | turn 3: correct `desk.create` (`decision_0c3fc998963d`), then `MCP exchange reconciliation for 'list_mcp_resource_templates' found no unused matching /api/mcp row` |
| 4 | `20260925T060013Z-case.philo601.import_failed.badge-muaddib-1440` | 1440 | none | **PASS** | `IMPORT` readable (x 306 y 450); row FAILED; no SAVED |
| 4 | `20260925T060021Z-case.philo601.import_failed.badge-muaddib-393` | 393 | none | **PASS** | `IMPORT` readable (x 22 y 364); row FAILED; no SAVED |

The honest-morning checklist against the shots:

| Item | 1440 | 393 |
|---|---|---|
| The decision readable in row 1, unobscured | TRUE — run 1 `…-1440/after.png` | TRUE — run 1 `…-393/after.png` |
| Brief head and receipt agree (except lawfully hidden rows) | TRUE — `3 THINGS WAITING` / `3 items` (after); `4` / `4` (before) | NOT FRAMED — the receipt sits below the sticky capture bar in the case's shot; the wire agrees (`/api/brief/latest` 3 items, head 3; `observation.json` `after.api_reads`) |
| One time format on caption and receipt | TRUE — `GENERATED SEP 26 00:00` / `SEP 26 00:00` | NOT FRAMED (same reason); wire `generated_label` `GENERATED SEP 26 00:01` |
| No raw method name on the Arrival or the brief items | TRUE — glass, and no `Service.` in any `api_reads` | TRUE — the visible rows; no `Service.` in any `api_reads` |
| MEETING READY in flow above the capture bar, no zero token, nothing covered | TRUE — rehearsal `20260925T060112Z…/shots/summary/1440-after.png` (`2 open`) | TRUE — `…/shots/summary/393-after.png` (card between the summary and the capture bar) |
| Meeting row badge and well truthful | TRUE — `RAN` + `192.168.1.43 · LAN`, summary receipt the same host | NOT FRAMED in the chain; TRUE on rehearsal `393-after.png` (receipt `192.168.1.43 · LAN`) |
| No SAVED on a failed import | TRUE — run 4 `…-1440/after.png` | TRUE — run 4 `…-393/after.png` |
| One Broke row per cause | wire only — run 2 `sections.broke` has one row | wire only |
| The decision body present at once after Done | not shot in the closing chain (its Done step passed the title check); proven by story 05's continuous S4 fences at both widths | same |

The Brief view itself (the fold's destination) is not opened by any closing case; its raw row details are disclosed debt (below).

## Both brains, per story

| Story | Built by | Checked by | Verdicts | Merged |
|---|---|---|---|---|
| 01 The honest import badge | Muad'Dib (lane A) | Astra | r1 BOUNCE (the well said SUMMARY · FAILED; broad "unmapped states" claim) → r2 BOUNCE → r3 RATIFY-WITH-CONDITIONS (`checks/lane-a-built-astra.md:3,47,105`), paid | #646 `e64114df` |
| 02 The brief's truth | Muad'Dib (lane A) | Astra | same lane rounds: r1 BOUNCE (a failed operation read as a success; the rehearsal box) → r2 BOUNCE (the fallback's false completion) → r3 RATIFY-WITH-CONDITIONS, paid; the rehearsal moved to exit 3 by SCOPE AMENDMENT | #646 `e64114df` |
| 03 The toast that does not cover | Astra (lane B zero + canvas; placement lane) | Muad'Dib | zero omission + canvas: Astra-invoked claude -p RATIFY-WITH-CONDITIONS (`checks/story-03-canvas-zero-astra-invoked-claude.md`) and Muad'Dib counsel (`checks/lane-b-built-muaddib.md`), paid → owner RATIFIED the placement canvas (`38cf713a`, #648 `d8f608c8`); placement built: Muad'Dib RATIFY-WITH-CONDITIONS (`checks/story-03-placement-built-muaddib.md`), paid in the reconcile. The brief names a canvas r1 BOUNCE; no BOUNCE record for the canvas is in the tree — could not verify | #647 `4d55d4d5`, #649 `f93e76fa` |
| 04 One cause, one row | Astra (lane B) | Muad'Dib | RATIFY-WITH-CONDITIONS (`checks/story-04-built-astra-invoked-claude.md`; `checks/lane-b-built-muaddib.md`), paid | #647 `4d55d4d5` |
| 05 The decision body at once | Astra (lane B) | Muad'Dib | RATIFY-WITH-CONDITIONS (`checks/story-05-built-astra-invoked-claude.md`; `checks/lane-b-built-muaddib.md`), paid | #647 `4d55d4d5` |

## Fences that failed pre-fix

- **01:** `docs/internal/philo/phase-6/badge/red.txt` — `Tests 2 failed | 1 passed (3)`, `import_failed: expected 'SAVED' to be 'FAILED'`; round 2 `badge/round-2/red.txt` 1 failed; round 3 the cause line `brief/round-3/red.txt` 1 failed (`zzR2ImportCause`).
- **02:** `brief/red.txt` — `briefTruth.philo602.test.tsx` 3 failed | 1 passed; round 2 `brief/round-2/red.txt` 2 failed (`briefOutcome.philo602r2`); round 3 on an advancing clock on a `git archive 27ee9559` copy (`brief/round-3/`).
- **03:** zero omission `toast/zero/red-origin-behavior.txt` — `Tests 3 failed | 6 passed (9)`; placement `toast/placement-proof/red-rendered.txt` — `aftercarePlacement.test.tsx` 8 failed.
- **04:** `rows/red-{http,op}-{1440,393}` — missing-decision parity FAIL 2:1 → PASS 1:1 at both widths (`rows/README.md`).
- **05:** `body/red-s4-{393,1440}-continuous.log` — the continuous S4 fence FAIL on archived main → PASS; the first frame is readable on main, so no first-frame red is claimed (`body/diagnosis.md`).

## What he still cannot do (ledgered with homes)

- **The spatial Floor's fixed card at 393:** the WebGL Floor keeps a fixed placement; not drawn in the ratified canvas (`docs/internal/philo/phase-6/toast/placement-proof/lane-report.md:106`; `docs/internal/philo/phase-6/ledger.md:33`).
- **The empty band after Dismiss on the phone** (about 300 px of end-of-scroll clearance above the capture bar) and **the focused-field no-scroll** (typing in the capture bar when the card arrives: no scroll, the card can sit under the sticky bar): Muad'Dib's counsel on built, `checks/story-03-placement-built-muaddib.md:55,57`; intended and fenced, disclosed to the owner.
- **The SAVED holes:** `importing`, `refused` and `live` still fall to SAVED (BACKLOG "PHILO-6 follow-ups" row 1).
- **Double-Broke:** a nested `create_from_meeting` failure makes two identical `Decision did not record` rows (BACKLOG "PHILO-6 lane A follow-ups" row 1); the closing chain did not hit it.
- **The unknown-success fence gap** (BACKLOG "PHILO-6 lane A follow-ups" row 2).
- **The Brief view's raw JSON and overflow:** row details show the observer's argument JSON and exception reprs; at 393 the JSON runs past the edge (BACKLOG "PHILO-6 follow-ups" row 4). The closing op run's brief still stores `detail: "{\"meeting_id\":…}"` and `not_found: NotFound(…)` (`assets/closing/20260925T060007Z…/observation.json`).
- **The raw-id filter:** historical briefs with old raw titles are filtered, not repaired (`checks/lane-a-built-astra.md:13`).
- **The inherited fixture error:** the broad scoped run exits 1 on one fixture error reproduced on untouched main (`docs/internal/philo/phase-6/toast/placement-proof/lane-report.md:113`).
- **The driver defects:** tool selection (Codex picks `door.add_item` for "put this decision on my list") — BACKLOG "PHILO-5-04 follow-ups", MCP discoverability row, Phase 7 story 01/04; resource-list reconciliation — BACKLOG "PHILO-6 follow-ups" row 2 (ASSIGNED Muad'Dib before exit 3; NOT paid — the third attempt hit it). Until both are paid, no ordinary-words rehearsal of the honest morning exists.
- **Not proven:** an already-open Desk refreshing its brief after an agent write; the 393 glass of the receipt, the caption and the meeting badge in the closing case (wire only at 393).

## Laws learned

- A closing case proves what its observe_at frames. At 393 the sticky capture bar hides the receipt and the caption below row 1; a claim about those at 393 needs a frame that shows them, or it stays a wire claim.
- One cause, one row, and one word per cause: when two paths share a word (`Decision did not load`), the capture pins the row by position after a checked text, never by a word match alone.
- A rehearsal driver that fails on its own reconciliation blocks the product proof as hard as a product defect; driver debt goes on the board with an owner and a date before the exit that re-runs it.
- A scope amendment moves a box, not its debt: the rehearsal moved from story 02 to exit 3 and came back BLOCKED for the same inherited reasons.
- An evidence capture exits 0 while its command exits 2; read the recorded `Exit code`, not the wrapper's.
