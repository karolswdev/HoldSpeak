# PHILO-5-03 — Astra lane report

## LANE

Astra, `feat/philo-5-03-the-atlas`, worktree `../wt-philo-5-03`, base `c4d464985c25b296906608f0b256960d229c786c` (01/02 merged). Luna workers ran at `gpt-5.6-luna`, reasoning `xhigh`. Astra inspected the source, all browser shots, the retained observations, and the scoped test output. No product code or face changed. Every actual hub used a temporary HOME.

PR: [PHILO-5-03 lane PR](https://github.com/karolswdev/HoldSpeak/pulls?q=is%3Apr+head%3Afeat%2Fphilo-5-03-the-atlas). Do not merge; Muad'Dib counsels on built.

## OUTCOME

VERIFIED — [Muad'Dib's precommit check](checks/story-03-precommit-muaddib.md) ratified with record conditions, paid as recorded. All **18 named pairs** pass their durable comparison; **2 additional replay pairs** pass separately. There are **33 selected browser observations**, **20 selected headless operation observations**, and **9 unselected attempts**, all retained in [runs.json](assets/story-03-shots/runs.json). Every selected operation run has a measured total duration. No face verdict comes from an operation run.

The rig sends canonical operations through the owning hub's `/api/mcp`, with the rig owner's bearer token. The adapter projects the operation name to the existing tool or resource; the hub's bound registry executes it. This uses the same HTTP target as the thin stdio proxy, with no second service composition. The isolated-hub/proxy restart test also passes. Shelf's invalid enum is explicitly rejected at the MCP schema before the registry; it is not a registry-reach claim.

## PROOF

| Story box | Result and evidence |
| --- | --- |
| Headless setup, wait, snapshot, restart, owning registry | PASS. [Checked chart](checks/story-03-headless-chart-astra.md), [Muad'Dib check](checks/story-03-headless-chart-muaddib.md); `scripts/graph_walk.py` `Hub.mcp`, `snapshot`, `_restart_detail`, `_op_step`, `run_case`; real S3/S4/S5 op observations and the scoped `test_philo5_graph_op.py` / `test_philo5_codex_seams.py` runs. |
| Every named sibling minted and run | PASS. [pairs.json](assets/story-03-shots/pairs.json), [explicit input](assets/story-03-shots/pairs-input.json), table below. 18 base siblings; no named pair omitted. |
| Durable outcome, identity relationships, refusals | PASS within the recorded scopes. `scripts/philo5_pairs.py` compares named producer/read slots, within-run IDs and timestamps, next-day decision source/created_at, brief-scoped breakage IDs and old shelf retention, Thought body/revisions/time/cursor, and refusal outcomes. It does not compare generated IDs or independent model prose across hubs. Shelf refusal transport origin and the breakage setup exception are retained below. |
| Real and replayed runs separate | PASS. Real runs call `http://192.168.1.43:8080`; replay runs are under `replayed/`, with `engine_mode: replayed` and reply hash. `tests/fixtures/philo5_summary_reply.json` retains the parsed provider result read back from real S2 run `20260924T210729Z`; it is not a raw provider HTTP transcript. |
| Independent 1440/393 face proof | PASS for retained face cases. [faces.json](assets/story-03-shots/faces.json) and [Astra's glass reading](assets/story-03-shots/glass-review.md). **20 of 33 browser observations have a face verdict; 13 have none (protocol-only).** S4's 393 raw shot does not prove saved-content rendering; this remains an explicit unknown. |
| Both atlas files counted; duration recorded | PASS. `atlas.json`: 81 cases, 7 base op siblings. `atlas-phase3.json`: 31 cases, 11 base op siblings, 4 replay variants. **112 cases total**, excluding archived files. Actual durations below, not a latency promise. |
| Fences red and green on real producers / structural mutation | PASS for the scoped fences. [Rig fence source](assets/story-03-shots/fences/verify_fences.py), [pair fence source](assets/story-03-shots/fences/verify_pair_fences.py), [verbatim pair reds/greens](assets/story-03-shots/verification/pair-fences.txt), DW captures at 21:51:35Z and 22:55:40Z. Calibration is labelled fixture proof; actual atlas runs supply product proof. |

Scoped validation: **219 tests collected; 219 passed in 113.35 seconds**. [Collection](assets/story-03-shots/verification/scoped-collect.txt), [run output](assets/story-03-shots/verification/scoped-tests.txt), [graph check](assets/story-03-shots/verification/graph-check.txt). No full suite and no metal test, per lane law. The graph check exits 0 with 14 inherited subtype conflict notes. After the runs, `git status --short | grep '^ M' | grep pm/roadmap/holdspeak/` has no output.

The root's pair mutation changes **`domain_response.title`**, the real field the comparator reads, rather than the retained `response` alias. Originals are hash checked and never edited. The old breakage op blocked during setup: the full pair is BLOCKED, and its actual day-one cause list separately makes `next_day.breakage_causes` FAIL. That diagnostic is not a fabricated final next-day observation.

### Pairs and measured total operation durations

The paired browser is 1440. Independent 393 observations are in `faces.json`. `replayed` rows are separate variants and do not enlarge the count of 18 named pairs.

| Case | Browser run ID | Operation run ID | Equivalence | Op total seconds |
| --- | --- | --- | --- | ---: |
| `case.closure.chain.s1_import_complete` | `20260924T210414Z-case.closure.chain.s1_import_complete-astra-1440` | `20260924T214328Z-case.closure.chain.s1_import_complete.op-astra-1440` | PASS | 3.481 |
| `case.closure.chain.s2_summary_with_host` | `20260924T210729Z-case.closure.chain.s2_summary_with_host-astra-1440` | `20260924T214440Z-case.closure.chain.s2_summary_with_host.op-astra-1440` | PASS | 10.453 |
| `case.closure.chain.s2_summary_with_host.replayed` | `20260924T224620Z-case.closure.chain.s2_summary_with_host.replayed-astra-1440` | `20260924T224812Z-case.closure.chain.s2_summary_with_host.op.replayed-astra-1440` | PASS | 4.909 |
| `case.closure.chain.s3_same_summary_after_restart` | `20260924T213120Z-case.closure.chain.s3_same_summary_after_restart-astra-1440` | `20260924T214529Z-case.closure.chain.s3_same_summary_after_restart.op-astra-1440` | PASS | 12.745 |
| `case.closure.chain.s3_same_summary_after_restart.replayed` | `20260924T224832Z-case.closure.chain.s3_same_summary_after_restart.replayed-astra-1440` | `20260924T225009Z-case.closure.chain.s3_same_summary_after_restart.op.replayed-astra-1440` | PASS | 7.062 |
| `case.closure.chain.s4_decision_recorded` | `20260924T213441Z-case.closure.chain.s4_decision_recorded-astra-1440` | `20260924T215223Z-case.closure.chain.s4_decision_recorded.op-astra-1440` | PASS | 13.628 |
| `case.a1.decision_face_create.opens_and_reopens` | `20260924T213830Z-case.a1.decision_face_create.opens_and_reopens-astra-1440` | `20260924T215349Z-case.a1.decision_face_create.opens_and_reopens.op-astra-1440` | PASS | 2.635 |
| `case.a3.brief_next_day.decision_on_the_face` | `20260924T215956Z-case.a3.brief_next_day.decision_on_the_face-astra-1440` | `20260924T220405Z-case.a3.brief_next_day.decision_on_the_face.op-astra-1440` | PASS | 2.737 |
| `case.a3.brief_next_day.new_id_with_the_decision` | `20260924T220621Z-case.a3.brief_next_day.new_id_with_the_decision-astra-1440` | `20260924T221130Z-case.a3.brief_next_day.new_id_with_the_decision.op-astra-1440` | PASS | 2.732 |
| `case.closure.chain.s5_next_day_brief_has_it` | `20260924T221218Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440` | `20260924T221418Z-case.closure.chain.s5_next_day_brief_has_it.op-astra-1440` | PASS | 12.211 |
| `case.closure.chain.s5_next_day_brief_with_breakage` | `20260924T222649Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440` | `20260924T224125Z-case.closure.chain.s5_next_day_brief_with_breakage.op-astra-1440` | PASS | 12.179 |
| `case.philo404.arrival_triaged_headline.all_handled` | `20260924T222024Z-case.philo404.arrival_triaged_headline.all_handled-astra-1440` | `20260924T222228Z-case.philo404.arrival_triaged_headline.all_handled.op-astra-1440` | PASS | 2.709 |
| `case.j11.thought_keep.receipt_time` | `20260924T221628Z-case.j11.thought_keep.receipt_time-astra-1440` | `20260924T221950Z-case.j11.thought_keep.receipt_time.op-astra-1440` | PASS | 2.647 |
| `case.j6.route_intelligence_run.refusal` | `20260924T222258Z-case.j6.route_intelligence_run.refusal-astra-1440` | `20260924T222352Z-case.j6.route_intelligence_run.refusal.op-astra-1440` | PASS | 2.984 |
| `case.j6.route_intelligence_run.no_assignment` | `20260924T222425Z-case.j6.route_intelligence_run.no_assignment-astra-1440` | `20260924T222621Z-case.j6.route_intelligence_run.no_assignment.op-astra-1440` | PASS | 4.859 |
| `case.j10.arrival_generate_again.same_day_idempotent` | `20260924T223147Z-case.j10.arrival_generate_again.same_day_idempotent-astra-1440` | `20260924T224043Z-case.j10.arrival_generate_again.same_day_idempotent.op-astra-1440` | PASS | 2.714 |
| `case.j10.route_generate_again.same_day_same_id` | `20260924T224233Z-case.j10.route_generate_again.same_day_same_id-astra-1440` | `20260924T224308Z-case.j10.route_generate_again.same_day_same_id.op-astra-1440` | PASS | 2.667 |
| `case.j10.brief_item_shelf.acknowledged` | `20260924T224324Z-case.j10.brief_item_shelf.acknowledged-astra-1440` | `20260924T224402Z-case.j10.brief_item_shelf.acknowledged.op-astra-1440` | PASS | 2.693 |
| `case.j10.brief_item_shelf.deferred` | `20260924T224425Z-case.j10.brief_item_shelf.deferred-astra-1440` | `20260924T224500Z-case.j10.brief_item_shelf.deferred.op-astra-1440` | PASS | 2.675 |
| `case.j10.brief_item_shelf.refused` | `20260924T224519Z-case.j10.brief_item_shelf.refused-astra-1440` | `20260924T224604Z-case.j10.brief_item_shelf.refused.op-astra-1440` | PASS | 2.668 |

### Required reds and greens (verbatim)

```text
RED op removed: calibration CAL-op-success BLOCKED; trigger not dispatched
GREEN calibration CAL-op-success ('pass', 'settled')
GREEN calibration CAL-op-unresolved ('blocked', '-')
GREEN calibration CAL-op-refusal ('pass', 'settled')
GREEN calibration CAL-op-never-completes ('fail', 'incomplete')
GREEN calibration CAL-op-headless-face-block ('blocked', 'settled')
GREEN calibration CAL-op-restart-retains-read ('pass', 'settled')
RED base snapshot: AttributeError 'NoneType' object has no attribute 'evaluate'
GREEN headless snapshot: real producer decision ID read back without a page
RED actual decision.read one-field title skew: FAIL [["decision.title", "fail", "decision.title differs"]]
GREEN actual decision pair: PASS []
GREEN all 18 named pairs plus 2 replay pairs: 20 PASS; original observations unchanged
```

Additional exact restart, decoder, clock, scope, receipt, shelf and Thought reds/greens are in [evidence-story-03.md](evidence-story-03.md) and [pair-fences.txt](assets/story-03-shots/verification/pair-fences.txt).

## LEDGER

- Headless execution, canonical MCP projections, typed capture, refusal waiting and restart: paid by the rig and scoped real-hub tests. Relative import fixture custody and the S4 restart read selection needed two diagnosed rig fixes; corrected actual runs are selected.
- Six observations under `fences/op-calibration/`, plus the absent-op control under `fences/op-removed/`, are labelled fixture-hub calibration records. They are intentionally outside `runs.json` and its product-observation hash check. They prove the rig, not a product atlas case.
- Import fixture SHA256 is retained under observation `provenance.fixture_hashes`, not on the op step itself. Copying that citation onto the step is a low-cost PHILO-5-04 record follow-up; the current hash is retained.
- Nine unselected attempts remain with explicit reasons in `runs.json`; no failed observation or shot was rewritten or removed.
- Shelf invalid-state drift remains: MCP's tool enum refuses before registry dispatch; HTTP reaches the service and answers 422. Both prohibit the state and leave brief/shelf unchanged. The pair records `refusal_origin: transport_schema` and `registry_reached: false`; this branch cannot count toward phase exit criterion 1. [Counsel](checks/story-03-shelf-refusal-muaddib.md).
- HTTP missing-decision read falls through from registry NotFound to the legacy lifecycle service (`holdspeak/web/routes/decisions.py:58-61`): two failure rows for one cause; MCP produces one. Inherited Article XI compatibility debt, assigned to PHILO-5-04. [Counsel and correction](checks/story-03-breakage-source-muaddib.md).
- Existing findings assigned to PHILO-5-04: S4's narrow raw shot lacks saved content; empty import is labelled SAVED on Arrival; a transient meeting toast shows 0 decided. These fail the relevant Tenet 3/4 / UX-CANON expectations; this lane changes no product face. Existing decision-admission Article XI debt stays unruled.

## AMENDMENTS

- S5 uses the existing process-local evening-zone method through `scripts/philo5_breakage_walk.py`, so the producer's day-one failure falls inside the next-day lookback. The machine clock is untouched. Both actual browser widths and the final op run prove overlap, old Ack retention and distinct scoped IDs. [Window check](checks/story-03-breakage-window-muaddib.md).
- The S5 op sibling uses the **same HTTP 404 setup seed** as the browser, then performs brief/decision/shelf actions through canonical ops. This compares equal failure-domain inputs. **Missing-decision refusal parity is not established**; its known transport difference is retained as debt. The final comparison requires both full text/detail causes and source-to-new-ID relationships.
- Thought's blank-note browser create and MCP typed create have different immutable raw custody. The op case starts with a distinct nonempty draft (required by the real producer) and proves the same saved working body, increasing revisions, stable raw identity within each run, matching save/read time, and the saved cursor. It does not claim identical raw content across the two create affordances.
- Atlas descriptions for direct HTTP Ack/Defer now state durable proof only. An already-open Arrival does not refresh after these API triggers. The separate UI-click ALL 2 HANDLED case proves its rendered transition; the phase already accepts reopened reads.

## UNKNOWN

No named pair is omitted. This is rehearsed isolated-hub evidence, not an owner sitting or a completed owner review of the shots. The real ASR output varies on the synthetic audio; transcription quality is not established. The replay retains parsed model output, not wire bytes. S4's 393 saved-content rendering remains unverified. The two inherited transport drifts and decision-admission debt remain for PHILO-5-04. A full test suite was not run, as instructed.

TUESDAY: the owner can inspect a saved decision, retrieve the same summary after restart, see that decision in a dated brief, handle rows, and keep a Thought through the proved paths. These rehearsals do not substitute for his review of the screens.
