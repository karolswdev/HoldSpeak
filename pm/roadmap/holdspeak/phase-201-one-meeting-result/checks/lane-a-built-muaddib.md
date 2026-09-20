# Counsel on built — Muad'Dib (via a fresh Opus reviewer), 2026-09-19: lane A (HS-201-02, 03, 05, 07 backend), PR #588

TWO-BRAINS §4. Read-only in wt-201-a; focused tests re-run by the reviewer. Astra's lane report: lane-a-report.md; his handoff: lane-a-handoff.md.

## VERDICT

**RATIFY-WITH-CONDITIONS — do not merge #588 yet.** The settled contract is built exactly as written, the nine mid-lane conditions are discharged in the final code, and the parked pipeline does **not** cost the owner his summary. Two gates remain: lane B's hash consumers, and CI.

## FINDINGS

**1. The parked pipeline is lawful. Traced, not assumed.**
After an analysis-only run the summary text is written to `intel_snapshots.summary` by `holdspeak/kernel/meeting_plugin_projection.py:271-277` (`_write_bound_analysis`). The plugin exclusion is surgical: `holdspeak/db/intel.py:1449-1451` zeroes only `plugin_members`/`plugin_route` when `planned_route_json` is set — the `meeting.deferred_analysis` member and its publication are untouched. It is read back by `holdspeak/db/meetings.py:558` (`_load_latest_intel`), exposed as the `intel` key on the meeting read model (`holdspeak/meeting_session/models.py:215`), served by `GET /api/meetings/{id}` (`holdspeak/services/meeting_service.py:344`). Proven end-to-end, restart included, at `tests/e2e/test_hs201_lane_a_glass.py:77` and `:89` (`saved.intel.summary == engine.result.summary`).
**One face renders it today:** `web/src/desk/pullouts/MeetingPullout.tsx:122-123`. The Phase 200 Review face reads the proposals table only (`web/src/pages/cores/history/reviewModel.ts:69-81`; backend `holdspeak/services/proposal_bridge_service.py:938-956`) and never touches `intel_snapshots`.
**Decision: the parking is lawful for One Meeting Result.** Exit criterion 4 is reachable and the field already exists on the read model. But it is not on the walk path: `pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/lane-a/meeting-after-restart-1440.png` shows the Meetings core after restart with the transcript, the `RAN` badge and the hardcoded `THIS DEVICE` chip — **no summary text**. `web/src/pages/cores/history/MeetingDetail.tsx:51-52` reads only `intelOff`/`intelState`. That is lane B's HS-201-04 criterion ("the summary is shown on the record with its meeting"), already chartered — not a lane A defect. Two B-side gaps worth naming now: `intel.topics` is declared at `MeetingPullout.tsx:24` and never read (Article VI, counters/fields of zero), and Review must render "Not run", per the handoff.

**2. The contract is exact.** `holdspeak/services/meeting_route_projection.py:97-133` emits `{status, reason_code, selection_hash, legs}` with legs `{ordinal, host, boundary, profile_id, profile_revision, deployment_revision_id}`; `unavailable` forces empty legs and a null hash (`:95`), so `local` is impossible in that state. `run_receipt` is minted at `holdspeak/db/intel.py:2479-2494` as `{receipt_id, job_id, meeting_id, selection_hash, outcome, attempts[{leg_ordinal, host, outcome, operation_id}]}`. Carried on: meeting list + detail (`meeting_service.py:728-747`, resolved **once** per request — condition 9), recovery (`meeting_intel_service.py:222`), job list (`:66`), run response (`:203-204`). All three endpoints accept `expected_selection_hash` (`holdspeak/web/routes/meetings/intel.py:78, 94, 110`); MCP requires it (`holdspeak/mcp/tools.py:285-288`).
Drift is refused **before dispatch twice**: at the service (`meeting_intel_service.py:110` → `require_expected_selection`) and again inside the claim transaction against the *actual frozen plan* re-read from `inference_route_plans` (`meeting_deferred_queue_binding.py:276-307`). Reproduced: `tests/unit/test_hs201_run_receipt.py:59 test_missing_or_stale_hash_refuses_before_request_or_provider` asserts `calls == []` — `request_intel_retry` is never reached.

**3. The mid-lane defect is fixed, with a red-capable fence.** `_guard_gesture_state` (`meeting_intel_service.py:57-75`) runs before `project_route`/`record_route_refusal`; `record_route_refusal` re-checks the same state inside `BEGIN IMMEDIATE` and writes nothing for `ready|running|reserved|queued` (`db/intel.py:2379-2382`). Test: `tests/unit/test_hs201_route_counsel.py:50 test_missing_hash_does_not_replace_a_completed_run` — asserts the receipt, the job id and `intel_status == "ready"` are all unchanged after a hash-less click. Also `:76` (queued owner not hidden) and `:95` (protected state wins, zero jobs written).

```
5 passed in 2.24s   # ::test_missing_or_stale_hash_refuses_before_request_or_provider
                    # ::test_missing_hash_does_not_replace_a_completed_run
                    # tests/e2e/test_hs201_route_execution.py
```

**4. Story 02 — I ran it.**
```
185 passed, 11 skipped in 43.65s
```
(11 skips are all `llama_cpp` optional-extra, `tests/unit/test_dictation_session_admission.py`.) Matches Astra's claim exactly. Untitled-meeting coverage is in `tests/unit/test_hs201_record_stop_hook.py`.

**5. Story 03 and 05 — I ran them.**
```
151 passed, 4 xfailed in 112.60s   # 03 set + hs200 glass + api surface
 59 passed in 5.13s                # 05 set
```
The four xfails are `strict=True` and name the ratified amendment. **The manifest revision is not scope creep.** It is ~25 net lines in `holdspeak/services/model_library_service.py:374-383`, reusing the *existing* readiness exclusion (`_provider_readiness_reason:566-573`) so `anthropic`/`future_backend`/`paired_device` get no claim. Without it the owner's hosted `gpt-5-mini` cannot be selected for summaries by any face — exit criteria 3 and 4 are blocked. It adds no probe, no framework, no face (Tenets 1 and 3 hold). One improvement over the check: `supported_modalities` is now the literal `["language"]` (`:396`), closing the alias leak.

**6. Baseline classification — three spot-checks, all honest.** The baseline tree at `.tmp/hs201-baseline/` is byte-identical to charter `fdc3fc45` where it matters — I verified blob hashes for `holdspeak/db/intel.py`, `meeting_intel_service.py`, `runtime/meeting_glue.py`, `intel_queue.py`, `tests/e2e/test_phase200_daily_loop.py`, `tests/e2e/test_hs171_command_deck_glass.py`: all PRISTINE.
- *HS-171 both widths:* pristine test file, both fail in `audits/baseline-glass-run.log` (9 failed, exactly the nine claimed; module origins printed in `baseline-glass-collect.log`). Honest.
- *Daily-loop both widths:* baseline copy line 442 is the `"brief was refused instead of drafted"` assertion, matching the log — it fails at the prepare brief, before meeting creation and before `_run_intelligence` exists. Honest.
- *UAT ledger:* I re-ran it here — `1 failed, 1 passed`, `features.yaml is stale`. Lane A touches no `uat/` file. Honest.

**7. What could touch the owner's real desk.** No config or keychain writes (the Concierge diff writes kernel receipts only). No new background loop; the three ungated loops are untouched, correctly (Tenet 1). Startup adds one stdout line (`holdspeak/runtime/ownership.py:35-42`). Three real items:
- **Two additive nullable columns** on `intel_jobs` (`db/schema.py:154-155`). Additive-only and name-addressed; `tests/unit/test_no_positional_inserts.py` + `test_db.py::TestDatabaseShape` pass (`5 passed`). Nobody has reconciled a **copy of his real DB** — still UNKNOWN, as the check said.
- **The refusal write.** On a meeting with a transcript and no job, a hash-less Run click writes a `failed/terminal` job row and sets `meetings.intel_status='error'` (`db/intel.py:2394-2412`). Today's shipped faces send no hash. On this branch alone, his first Run click makes a good meeting read as an error. This is the interlock, and it is a *desk* consequence, not only a merge-order one.
- **`intel_enabled=False` is hard-coded** (`runtime/meeting_glue.py:274`) while `settings_service.py`, `doctor.py`, `setup_status.py` and `trust_destinations.py` still report live intelligence as on. Recorded as ledger debt, not fixed. Fails **Article VI** and **Tenet 3** (a dead knob) until B retires or reconnects it.

## CONDITIONS

1. No merge until lane B sends `expected_selection_hash` on Chair Run, ledger Retry and record Retry, and CI is green.
2. B renders `intel.summary` on the meeting record (HS-201-04) — the restart shot proves it is absent from the Meetings core today.
3. B renders "Not run" for the unexecuted proposal chain, and either renders `intel.topics` or drops the declaration.
4. Reconcile the two new columns against a **copy** of his real DB before the sitting.

## MISSED

1. The dead `intel_enabled` toggle and its doctor lines (recorded, unpaid).
2. A residual honesty hole: if `bound.execute` (`intel_queue.py:437`) raises *mid-dispatch*, the `finally` at `:629` writes `attempts: []` for a job that may have contacted a provider. The `ValueError` path Muad'Dib named is closed (`db/intel.py:2467-2477` keeps `undisclosed`); this one is narrower and unproven either way.

## TUESDAY

Yes, once B lands. He connects one engine, selects it for summaries, records with no text model, sees one host before the run and the contacted host after, and the summary survives a restart in the DB. He will not *see* that summary until B renders it on the record.

## UNKNOWN

- CI: `mergeStateStatus: UNSTABLE`. Unit Tests IN_PROGRESS; Integration (macOS) and E2E (macOS) QUEUED. Four checks green.
- Whether `bound.execute` can raise after a provider was contacted (finding above).
- Additive reconcile on a copy of his real DB.
- Live model quality, his desk, the microphone, the sitting. Out of bounds.
- I ran no browser glass test beyond those in the 03 set; I did not open the 393 shot.

## Muad'Dib's ruling

Accepted in full. Conditions 1–3 are lane B's story 04 (hash on every run verb; `intel.summary` rendered on the record; "Not run" for the parked chain; `intel.topics` rendered or dropped) and are in that worker's brief. Condition 4 (additive reconcile on a copy of the owner's real DB) is run by the orchestrator before the sitting and recorded in story 07's evidence. Ledgered to lane A: the dead `intel_enabled` knob and its doctor/settings lines (Article VI, tenet 3); the mid-dispatch `attempts: []` hole. Merge order: #588 and #587 land back to back, #587 carrying the consumers, so main never holds a backend whose Run click turns a good meeting into an error.
