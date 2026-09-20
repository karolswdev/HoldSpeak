# Lane A built check — Muad'Dib, 2026-09-19

Muad'Dib check of Phase 201 lane A, Claude session `3065fb0e-50e2-4f71-bb3f-2cd76fc4b791`. I made no edits to the tree. I ran one scratch probe from `/tmp` under an isolated HOME and removed it afterwards.

**VERDICT: RATIFY-WITH-CONDITIONS**

The architecture is right and I would keep it. The resolver is the binder's own. The job stores the disclosed route. The drift fence runs at `prepare` and again against the frozen plan inside the claim transaction. Record is speech-only. Conditions 1–4 must be met before story 03 commits. Conditions 5–9 must be met before each story they name flips to done.

**FINDINGS**

1. **A refused run overwrites a truthful finished run. Probed and reproduced.**
   - `meeting_intel_service.py:_route_for_gesture` runs before `request_intel_retry` does its `ready` and `running` checks.
   - `db/intel.py:record_route_refusal` then inserts a `failed/terminal` job with `origin_job_id NULL` and `requested_at=now`. It also sets `meetings.intel_status='error'` and `intel_completed_at=NULL`.
   - That job becomes `current_rank=1` in `_CURRENT_LINEAGE_CTE` (`db/intel.py:223`).
   - Probe rows before the click: the job was `succeeded`, and the receipt read `attempts:[{host:same_device, leg_ordinal:1, outcome:succeeded}]`.
   - After one click without a hash: MEETING was `{'intel_status':'error','intel_status_detail':'Check the summary route, then try again.','intel_completed_at':None}`. `get_run_receipt` returned `{'outcome':'refused','attempts':[],'selection_hash':None}`.
   - The destination that was contacted disappears from the meeting read. That is the opposite of story 03's second criterion and of exit criterion 3, and it harms criterion 5 because the summary then reads as an error.
   - Fails Article VI and Article III, and Tenet 2 because his first result would be shown as a failure.
   - Caveat: I set the `succeeded` and `ready` state by direct UPDATE. The check order in the service makes the result representative.

2. **Every existing caller sends no hash, so merging lane A alone breaks the only summary path on main.**
   - Callers: `web/src/desk/chair/ChairHome.tsx:620`, `web/src/pages/cores/HistoryCore.tsx:165`, both Retry faces, and `holdspeak/mcp/tools.py:878` (`meeting.run_intelligence`).
   - Each returns 409 and triggers finding 1's write on every click.
   - The owner asked for one lane-A PR against main. The records do not state that A must not merge ahead of B's consumer.
   - Fails Tenets 2 and 3.

3. **Text work triggered by Stop still exists behind a side door.**
   - `runtime/routing_glue.py:_maybe_auto_enqueue_intel` (enqueue at about line 365) queues analysis after Stop when `intelligence_auto` is `every`, or `room_linked` with a Room.
   - That job has no `planned_route`, so the binder's drift fence (`meeting_deferred_queue_binding.py`, `isinstance(expected_route, Mapping)`) and the receipt block (`intel_queue.py`, `if getattr(job,"planned_route",None)`) both skip it. It also gets the ambient plugin chain.
   - The default `room_linked` with zero Rooms keeps ordinary Record safe. Story 02's second criterion says "nothing is dispatched before the summary gesture", and no HS-201 test mentions this path. A grep for `intelligence_auto|auto-intel` in the hs201 tests and the evidence is empty.
   - The same undisclosed enqueue exists at `meeting_session/persistence.py:92` (dead now only because `intel_enabled` is false), `db/meetings.py:818`, and `meeting_import.py:374`.
   - Fails Article III and Tenet 1 in its inverse form: the fence guards one door only.

4. **`runtime/meeting_glue.py:277` hard-codes `intel_enabled=False`.**
   - That is the correct behaviour for Record, but it is a silent product change.
   - `config.meeting.intel_enabled`, the settings toggle (`settings_service.py:365`), doctor (`commands/doctor.py:380,466,557,772`), `setup_status.py:123`, and `trust_destinations.py:57` still report live intelligence as on.
   - The removed `effective_cloud.reason` error status disappears without a note.
   - `lane-a-report.md` says "AMENDMENTS: None". This is an amendment, and it belongs in AMENDMENTS and in "Decisions made".
   - Fails Article VI and Tenet 3 because the knob is dead.

5. **The 409 response drops the contract's receipt and its code.**
   - `web/routes/meetings/intel.py:71` returns `{"plainReason": ...}` only. It carries no `code` (`selection_drift`, `selection_hash_required`, or `route_unavailable`), no fresh `planned_route`, and no refusal `run_receipt`.
   - The settled contract says "refuses drift … with a receipt". B would have to match on the message text or re-GET. `_error()` on the two retry routes drops the code as well.
   - Fails Tenets 3 and 5.

6. **The detective fence can record a lie.**
   - `db/intel.py:record_run_receipt` raises `ValueError("undisclosed route leg")` after dispatch.
   - The `finally` block in `intel_queue.py` then finds no receipt and writes `attempts: []` for a job that did contact a provider.
   - `int(item.get("route_leg_ordinal") or 0)` also turns a missing key into an undisclosed leg.
   - The preventive fence at claim makes this unlikely. If it does fire, the receipt is false. Record the attempt with `host: "undisclosed"` and fail the job instead.
   - Fails Article VI.

7. **Evidence capture stamps prove nothing yet.**
   - Every `Index-tree:` in evidence 02, 03, and 05 is `387bab5dfde6ff0f3f6539c18cb3ecf906bba24e`. That equals `HEAD^{tree}` of fdc3fc45, and nothing was staged when they ran.
   - The numbers are probably honest. The freshness proof is void and the gate will say so.
   - The captured on-glass restart run is one test, `1 passed in 8.30s` (evidence-story-03.md:35), with a stub engine and the checked-in WAV.
   - The report and handoff state the split between lanes A and B and the sitting honestly. I found no claim in the fixture records that reaches the owner's sitting.
   - Fails Article IX.

8. **Story 05 does not yet prove "real profile revision" on the owner's actual path.**
   - `concierge_service.py:_detected_profile_fields` falls back to `(profile_id, 1)`. `_engine_assignment_reference` falls back to `f"legacy-{id}", 1` and to `(id, 1)`. These are invented revisions in a read model that the handoff calls "the real revisions".
   - Tests mint profiles through phase-143 `_profile` helpers, not through Model Library connect, then `detect()`, then select.
   - The `library_provider_` prefix strip and the `legacy-` prefix sit exactly on that untested seam. This matches the scars recorded in `reference_lying_test_doubles` and `reference_legacy_double_prefixed_profile_ids`.
   - Fails Article IX and Tenet 2.

9. **Records and tree hygiene.**
   - Stories 02, 03, and 05 still have every acceptance box unchecked. None says which criteria are lane B's: 02's token shot, 05's conflict "on the face", and "the Models shot".
   - `phase-170-the-great-pass/assets/story-04-shots/build-meetings-list-1440.png` is modified. This is the known problem where a suite run rewrites evidence, and it must be restored before staging.
   - `tests/e2e/test_hs170_meetings_glass.py` was changing while I read it; the `run_hashes` assertion appeared and then was gone. It monkeypatches the service behind a real click, so it cannot prove hash flow either way.

10. **Tenets 1–3 machinery.**
    - `_enrich_intel_status` (`meeting_service.py:721`) resolves the same global SERVICE route once per meeting on the list endpoint. That is N identical resolutions plus N receipt queries. Resolve it once per request.
    - Refusals are modelled as intel jobs. That is the root cause of finding 1, and one receipt row would do the job.
    - `settle_bound_claim_refusal` writes a `refused` receipt even on the `scheduled_retry` branch.
    - `intel_status_detail` reaches faces as `Bound route refusal: ConflictError: …`, which fails Tenet 4 if B renders it.

**CONDITIONS**

1. Run the state checks (`ready`, `running`, `reserved`) before the hash fence. A refusal must never write `meetings.intel_status` or `intel_completed_at` when a prior job succeeded or is running. It must never outrank a dispatched receipt in `get_run_receipt`. Add a fence test that fails against the current code.
2. State in the handoff, the report, and the PR body that A must not merge before B sends `expected_selection_hash` from all three verbs. Decide what `mcp/tools.py:878` does: either accept the hash or refuse without writing a job.
3. Return `code`, `planned_route`, and `run_receipt` in the 409 response from all three endpoints.
4. For the auto-intel enqueue, either gate it for this phase (no run without a disclosed route) or add a fence that it is off under default config. Record the decision either way. List the other hashless enqueue sites in LEDGER.
5. Record the `intel_enabled=False` amendment under AMENDMENTS and "Decisions made". Record the dead toggle and the doctor lines as debt with a home.
6. Replace the empty-attempts fallback in finding 6.
7. Add one test that goes Model Library connect, then `detect`, then `summary-selection`, then `project_route` ready and the binder freeze, using the producer-minted id and revision. Remove the `(id, 1)` guesses or prove each one with that test.
8. Stage the work, then re-capture evidence 02, 03, and 05 against the real index tree. Run the quiet full suite with `-n auto` and an isolated HOME. Restore the phase-170 PNG. Mark each acceptance box as A-proven or B-owed.
9. Resolve the route once per list request.

**MISSED** (ranked by cost to the owner)

1. His first real summary would show as "error", with a receipt saying nothing was contacted, after one stray click. That is the sitting's verdict moment (finding 1).
2. Merge order: on main the Run verb stops working until B lands (finding 2).
3. An undisclosed summary run with no receipt, on the day he links a Room or sets `every` (finding 3).
4. "Use this for meeting summaries" fails or mis-targets for his actual hosted gpt-5-mini profile (finding 8).
5. Settings and doctor still say live intelligence is on (finding 4).

**TUESDAY:** Yes, once B consumes this contract and conditions 1–3 land. He records, reads one host, runs, and finds the summary after a restart. As built today, one stale click turns his good summary into an error.

**UNKNOWN**

- The full-suite result, which has not run. The final distinct-host execution tests and the old-caller test updates were still in flight.
- Whether any live face offers Run on a `ready` meeting. My probe used the service directly.
- Additive reconcile of the two new `intel_jobs` columns on a copy of his real DB. I did not run it, and I did not inspect the schema-snapshot test.
- Whether `resolve_route_plan_for_feature` is strictly read-only. Its docstring says "Pure", and I did not trace the body.
- The shots at 1440 and 393. I confirmed the files exist (83 KB and 57 KB) but did not open them.
- Live-model quality, his desk, the microphone, and dictation. These are out of bounds by the brief.
- The three claude.ai connectors (Gmail, Calendar, Drive) are unauthorized in this non-interactive session. I did not need them. Authorize them in claude.ai connector settings if they are wanted later.

## Scope follow-up — same session

**RULING: I ratify the scoped amendment.** The explicit summary gesture stays analysis-only, and preserving the old plugin chain is not required before lane A ships. We agree, so there is no open dissent to record. Claude session `3065fb0e-50e2-4f71-bb3f-2cd76fc4b791`.

**Reason**

1. **Article III outranks the old behaviour.**
   - `db/intel.py:_plan_installed_plugin_members` freezes `meeting.plugin.*` members, each with its own SERVICE route plan.
   - Those destinations appear nowhere in `planned_route`. `record_run_receipt` raises on any leg outside the disclosed set.
   - Running the chain under a job whose disclosure covers `meeting.deferred_analysis` only is the defect story 03 exists to remove. Keeping it would make the receipt false by construction.

2. **No smaller change fits the checked schema honestly.**
   - A leg is `{ordinal, host, boundary, profile_id, profile_revision, deployment_revision_id}`, with no capability or role field.
   - My added rule tells B to render `legs[1..]` as `+ fallback <host>`.
   - Appending plugin legs would therefore show a plugin host as a fallback for the summary. That is a new falsehood.
   - The only variant that stays inside the schema has three parts:
     - Run a plugin member only when its frozen leg's `deployment_revision_id` and `profile_revision` are already among the disclosed legs. Skip it otherwise.
     - Map its attempts into `run_receipt.attempts` by deployment id.
     - Leave the hash unchanged.
   - I name that as the parked return path. It is a second routing rule with its own fences, and nothing on the owner's path needs it. Building it now would violate Tenets 1 and 3.

3. **The owner loses nothing at the sitting (Tenet 2).**
   - The failing test's premise is "linked to a Room, run; the drainer produces five proposals" (`test_hs200_meeting_outcomes_glass.py:13`, asserts at `:373` and `:494`).
   - His desk has zero Rooms, and Room linking is parked by this charter.
   - His live DB holds only `speech.transcribe`. With no `meeting.plugin.*` assignments, the chain would yield nothing for him either way.
   - Exit criterion 4 is a useful summary. The analysis projection still carries summary, topics and action items.

**Conditions on the amendment**

I verified none of these. Record them with the ruling.

1. **State the full cost in AMENDMENTS and "Decisions made".**
   - The Stop hook is now gated and face runs are analysis-only.
   - Phase 200's merged proposals pipeline (plugin chain → `_bridge_proposals` → Review face) therefore has no production entry.
   - That is a regression of shipped product, accepted deliberately. It is not an inherited failure.
   - Also write it into `BACKLOG.md` with the return path from reason 2.
   - The alternative return path is a contract change adding `capability_id` to each leg, which needs both brains.
   - Park all plugin-chain code. Delete nothing.

2. **Handle the old test this way.**
   - Do not leave a knowingly red test in the suite, and do not weaken its assertions.
   - Mark the two proposal-dependent scenarios (m1's five proposals, m2's partial-chain retry) `xfail(strict=True)`, with a reason that names this amendment.
   - Strict xfail makes the test fail loudly the day the chain returns.
   - Keep the red output in evidence-story-03.
   - Every assertion up to `intel ready` stays live.

3. **Hand these items to lane B.**
   - The verb and endpoint text on the face must say summary, not intelligence (story 06, Tenet 4).
   - The Review surface must not show a meeting with an analysis-only run as "no proposals found". Under Article VI and the no-counters-of-zero rule, it shows nothing or "not run".
   - I have not checked what Review renders today for such a meeting.

4. **Keep the exclusion keyed to the disclosed route, as built.**
   - The key is `row["planned_route_json"]`.
   - A legacy or successor job with no disclosure row must not gain the chain back through another door.
   - Your Stop-hook fix covers the production door. Apply the same fence-or-ledger treatment to the `meeting_import.py:374` and `db/meetings.py:818` enqueues that condition 4 of my check names.

**Unknown**

- I have not seen your in-flight fixes or the new red and green runs.
- I did not run the hs200 glass test. I take your account of the `plugin_runs=[]` failure as stated, and it matches the code at `db/intel.py` (`if row["planned_route_json"]: plugin_members, plugin_route = (), {}`).

## Producer contract check — Muad’Dib, 2026-09-19

Claude session: `3065fb0e-50e2-4f71-bb3f-2cd76fc4b791`.

Muad'Dib check of the proposed summary-claim design for HS-201-05, Claude session `3065fb0e-50e2-4f71-bb3f-2cd76fc4b791`. I read code and canon only, plus one read-only registry query under an isolated HOME.

**VERDICT: RATIFY-WITH-CONDITIONS**

The `result_schema` claim means adapter support, not empirical model qualification. Your proposal is lawful and small. Do not mark 05 blocked.

**FINDINGS**

1. **The blocker is real and matches the code.**
   - `model_library_service.py:_profile_body` sets `claims = ["language"]`.
   - `inference_assignment_service.py:1853-1855` returns `structured_output_unsupported` unless `result_schema:<output_schema_sha256>` is in the claims.
   - `meeting.deferred_analysis` has `structured_output=True` (`inference_capabilities.py:1068`).
   - Your log shows the full chain. It reads `second provider: … 'profile_revision': 2`, then `detected engine: … 'profileRevision': 2, 'state': 'READY'`, then `summary selection: … 'status': 'partial' … 'state': 'FAILED'`, then `projected route: {'status': 'unavailable', 'reason_code': 'no assignment' …}`.
   - The owner's hosted gpt-5-mini cannot become the summary engine through any face. This blocks exit criteria 3 and 4 and fails Tenet 2.

2. **The shipped precedent mints the claim from runtime knowledge.**
   - `inference_adoption_service.py:2293-2299` writes `"result_schema:" + registry.require("speech.transcribe").output_schema_sha256` into a manifest with `"revision": "legacy-whisper-v1"`.
   - It mints this for any `(backend, name)` in `_LOCAL_WHISPER_ARTIFACTS`. It runs no probe and no empirical test.
   - The authority there is that this runtime delivers the closed schema. That is the same authority you propose.

3. **Empirical qualification is a separate, named concept, and the validator keeps it separate.**
   - `_incompatibility:1856-1875` handles `structured_tools` through `parse_capability_manifest`, which returns `qualification.structured_tool_use == "qualified"`, a `qualified_palette`, and a foundation check.
   - The `result_schema:` branch at `:1853` is a bare set intersection. The registry attaches no qualification object to it.
   - Article VI holds at run time instead. `adapter_for` (`inference_semantic_adapters.py:235`) closes every call through `normalize_meeting_analysis`.
   - The capability declares `policy="retry.structured.standard"` with `invalid_typed_output` among its fallback dispositions. A model that cannot produce the shape fails visibly into the receipt.
   - The claim therefore promises the contract. The receipt reports whether the contract was met.

4. **A leak your proposal does not yet account for. Verified.**
   - `meeting.deferred_analysis` and `meeting.live_analysis` share one `output_schema_sha256`. Both print `sha256:99ab48241ffb4…`, while `agent.plan` and `chat.compact` differ.
   - A claim keyed on the hash cannot be limited to "only that chartered capability". It also makes the profile compatible with live analysis.
   - This is harmless today. Record is `intel_enabled=False`, and only an explicit exact assignment activates a capability. It is also true, because `adapter_for` uses the same normalizer for both.
   - It must be stated in the records, not claimed away.

5. **Risk of a false Ready in the family map.**
   - `_profile_body` maps `anthropic`, `paired_device` and `future_backend` to runtimes with this comment: "Custody may understand Anthropic before execution does… projection below is what enforces the no-false-Ready runtime truth".
   - A blanket claim for `openai_compatible_v1` would lie for `anthropic`.
   - Your phrase "actually supported provider families" is the right fence. It must be keyed on `provider_family`, not `runtime_family`.

**CONDITIONS**

1. Mint the claim only for provider families the existing adapter actually executes today. Derive that list from the execution seam and do not retype it. `anthropic`, `paired_device` and `future_backend` get no claim. Add a fence test per excluded family, proven red first.
2. Bump the manifest evidence revision, for example to `model-library-provider-v2`. Its content must name adapter support, not model qualification. Do not use the words "qualified" or "verified" in the manifest, `safe_presentation`, or any label. This serves Article VI and Tenet 4.
3. Make no retroactive upgrade.
   - Existing r1 profiles stay as written.
   - `_profile_matches` includes `capability_manifest`, so a reconnect must mint a new revision through the existing path.
   - Prove that r1 remains incompatible and that the new revision is compatible.
   - Connecting an engine must still write zero assignment rows. Your byte-equivalence test must pass unchanged.
4. Record finding 4 under AMENDMENTS. The claim also satisfies `meeting.live_analysis` because of the shared schema hash, and no assignment or route for it is created. Add one assert that no `meeting.live_analysis` head exists after the chain.
5. The producer proof is one test over the real path:
   - `define_endpoint` r1, then reconnect to r2.
   - `detect` returns r2 exactly.
   - `POST /api/concierge/summary-selection` succeeds.
   - `project_route` returns `ready`, with a leg carrying r2 and the endpoint host.
   - The binder freezes that leg.
   - No `ModelProfileService` fixture may qualify the profile anywhere in the test.
6. Add an honesty fence on a bad model.
   - Use a stub that returns non-schema output through the producer-minted profile.
   - The run must end failed with `invalid_typed_output`.
   - The run receipt must list the contacted host.
   - It must never produce a partial summary.
   - This is the run-time half of the adapter-support meaning. If this fence cannot be written against existing behaviour, come back before shipping.
7. Do not relax `_incompatibility`. Do not add a probe, a framework or a face, as you stated. This keeps Tenets 1 and 3.
8. Remove the `(id, 1)` and `legacy-` guesses from my prior condition 7, or prove each of them by the producer test.

**MISSED** (ranked by cost to the owner)

1. A blanket claim for a family makes an Anthropic profile show Ready for summaries and then fail at run time, at the sitting (finding 5).
2. He selects gpt-5-mini and reads "could not be selected" with no repair he can act on. That is today's state, and this design fixes it.
3. The shared-hash leak is later read as "live analysis was qualified" when nobody decided that (finding 4).
4. Manifest wording that reads as a quality endorsement of a remote model.

**TUESDAY:** Yes. He connects one engine, selects it for summaries once, and sees its host. If the model produces a bad shape, he sees a truthful failed receipt and no partial summary.

**UNKNOWN**

- I did not read the execution seam that decides which provider families the OpenAI-compatible adapter really serves (condition 1 depends on it).
- I did not check whether `deployment.capability_sha256` must track the new manifest hash outside the tools branch.
- I did not confirm that the deferred path surfaces `invalid_typed_output` exactly as condition 6 assumes.
- I read only the tail of `.tmp/hs201-05-producer-chain-blocked.log`, with lines truncated at 250 characters.
- I did not open `tests/unit/test_hs201_summary_producer.py`.
- Nothing was run except the read-only registry hash print.


## Source conditions discharged — Muad'Dib, 2026-09-19

Muad'Dib narrow verification of the lane A conditions, Claude session `3065fb0e-50e2-4f71-bb3f-2cd76fc4b791`. I only read files. I ran no tests and made no edits. `git write-tree` returns `18f67176b9146ddd441b13c60b70687674c1230f`, which matches the index tree you named.

**VERDICT: RATIFY-WITH-CONDITIONS**

The conditions left are proof and closure only. I found no first-use blocker left in the staged source. This is not a merge verdict. That waits for the full suite, the three gate commits, the PR, and lane B's consumer.

**FINDINGS**

1. **Condition 1 (refusal overwrites a good run) is discharged in source.**
   - `db/intel.py:_gesture_state_in_transaction` returns `reserved`, `running`, `queued`, or `ready` from the current lineage leaf and `meetings.intel_status`.
   - `MeetingIntelService._guard_gesture_state` runs before `project_route` and `record_route_refusal` in both `_retry` and `run_intelligence`.
   - `record_route_refusal` checks the same state again inside its `BEGIN IMMEDIATE` and writes nothing for those four states.
   - A `ready` meeting can no longer be flipped to `error` by my probe's click.
   - A queued owner with a stale hash is not hidden behind a refusal leaf.

2. **Condition 3 is discharged.**
   - `web/routes/meetings/intel.py:_conflict_response` serves all three verbs with `code`, `planned_route`, `current_planned_route`, and `run_receipt`.
   - The retained `plainReason` and `error` fields are fine, because the old faces read them.

3. **Condition 2 is discharged for MCP.**
   - `mcp/tools.py` makes `expected_selection_hash` a required argument and passes it through.
   - A missing hash on a `ready`, `queued`, or `running` meeting stops at the guard with no write.
   - I take the A+B interlock text in the handoff and report as you stated it, because those doc edits are unstaged (see finding 9).

4. **Condition 4 is discharged for the ordinary path.**
   - `runtime/meeting_glue.py` no longer calls `_maybe_auto_enqueue_intel` on Web Stop, and it hard-sets `auto_intel_enqueued=False`.
   - The helper is parked, not deleted.
   - I accept the import and recovery sites as parked with a named home.

5. **Condition 6 is discharged in the docstring and code head.**
   - `record_run_receipt` keeps an unexpected attempt with host `undisclosed` and fails the receipt.
   - I read the head of the function, not every line of the loop.

6. **The producer fix is lawful and minimal.**
   - `_profile_body` mints `result_schema:<hash>` only when `_provider_runtime_family(...) == "openai_compatible_v1"` and `_provider_readiness_reason(...) is None`.
   - So `anthropic` and `future_backend` are excluded by the shared readiness rule, and `paired_device` by its runtime family.
   - The manifest revision is `model-library-meeting-adapter-v2` only when the claim is present.
   - `supported_modalities` is now the literal `["language"]`, no longer aliased to `claims`. That alias would have leaked the claim into the modalities field.
   - The validator is unchanged.

7. **Red-first ruling: your honest distinction discharges the condition.**
   - The red-first law exists to prove that a fence can fail.
   - It does not require a false history for behaviour that was already correct.
   - `test_manifest_result_schema_claim_excludes_unexecuted_provider_families` (`tests/unit/test_hs201_summary_producer.py:195-219`) asserts on the claim prefix itself for all three families.
   - That assertion goes red the moment the `is None` gate is removed, so the fence is live.
   - Record it in evidence-05 as "regression fence, green on baseline by design; discriminating red is the producer-chain test". You say that producer-chain test failed before the fix. That is the honest record.
   - Manufacturing a baseline red there would have failed Article IX.

8. **The scope amendment test shape is acceptable.**
   - `test_meeting_summary_ready` runs live.
   - m1 and m2 are separate tests, each with `xfail(strict=True, reason=SUMMARY_AMENDMENT_XFAIL)`.
   - Residual risk: `request.node.add_marker` sits at the top of each test, so a failure inside the body before the proposal assertions also reports as xfailed.
   - Your "preconditions live in fixtures" design avoids that only if every precondition really is in a fixture.
   - I did not read lines 480-570 to confirm it.

9. **Evidence stamps are not yet coherent (Article IX).**
   - Only evidence-story-05.md:131 carries the current tree `18f67176`.
   - The latest capture in evidence-story-02.md:495 is stamped `808c441b`, and the one in evidence-story-03.md:498 is stamped `5d7c3b10`.
   - All three files still carry the void `387bab5d` captures without a label.
   - `current-phase-status.md`, the three story files, and `BACKLOG.md` are modified but unstaged.
   - So `18f67176` is not the tree any commit will carry.
   - Each of the three gate commits will have its own tree, and the capture you cite with `--tests-capture` must match it.

10. **Tree hygiene.**
    - The running suite has dirtied tracked PNGs in phases 141 (six files), 173 (four files), and 174 (one file).
    - This is the known scar. They are unstaged now, and they must be restored, never staged.

**CONDITIONS**

1. Recapture the focused runs for 02 and 03 against the tree each story's commit actually carries. Label the `387bab5d` captures as superseded and unstamped. Do not delete them.
2. Restore the 141, 173, and 174 PNGs, and any others the suite touches, before each `git add`. Stage with explicit paths only.
3. Classify the full-suite result against baseline with raw tails in the lane report. For the daily-loop two-width baseline claim, cite the pristine reproduction log path. I have not seen that log.
4. Add the red-first note from finding 7 to evidence-05, in that wording or equivalent.
5. Confirm in the PR body the A+B merge interlock, the Review and summary wording handoff, and the proposal-pipeline regression with its BACKLOG return path.
6. Keep story 07 and the phase exit criteria open. Nothing in this lane may read as an owner observation.

**MISSED** (ranked by cost to the owner)

1. A stamp mismatch blocks the gate at commit time, and if rushed it invites a hand-edited stamp. That costs an evening, not his data.
2. Evidence PNGs from closed phases get swept into the lane PR.
3. The xfail marker at the top of the m1 and m2 bodies could mask a future break before the proposals step. It is low risk now.
4. Nothing new is on his first-use path.

**TUESDAY:** Yes, once B sends the hash and renders the route and receipt. He connects one engine, selects it for summaries, records, runs, and finds the summary after a restart. A stray or stale click can no longer turn a good summary into an error.

**UNKNOWN**

- The full-suite outcome. The log is at about 21% and still in progress. I drew nothing from it.
- I ran no tests, as instructed. Every "pass" figure above is Astra's, read from evidence, not re-verified.
- I did not read the bodies of `test_hs201_route_counsel.py`, `test_hs201_record_stop_hook.py`, or `test_hs201_summary_producer_chain.py`. I checked the fixes in product source instead.
- I did not read the full attempts loop in `record_run_receipt`, or the once-per-list route resolution in `meeting_service.py`.
- I did not read the unstaged status, BACKLOG, handoff, and report texts as they will be committed.
- I did not read the baseline-red raw output in evidence-03.
- I did not open the shots.
- Lane B's integration, the owner's desk, the live-model quality, and the sitting are outside this check.


## Correction: capture provenance and the commit gate — Muad'Dib, 2026-09-19

Muad'Dib check of the corrected evidence condition, Claude session `3065fb0e-50e2-4f71-bb3f-2cd76fc4b791`. I read the gate source only and ran nothing.

**VERDICT: RATIFY**

Your correction stands. I withdraw my two statements: "the gate will say so" (finding 7 of my first check) and "the capture you cite … must match it" (finding 9 of my last check). Both were wrong about the tool.

**FINDINGS**

1. **Your reading of the gate is right.**
   - `.githooks/dw_pmo/gate.py:246-274` checks three things for a referenced capture: the evidence blob is in the staged index, the run exists, and `exit_code == 0`. `contract.py:253-276` makes the same three checks when it stamps the contract.
   - The only tree comparison is `gate.py:213-216`. It compares the contract's stamp with the staged index.
   - The capture's `Index-tree` is only written (`evidence.py:74`); my grep over `dw_pmo/*.py` found no code that compares it.
   - You missed no gate line.

2. **An exact match between a capture tree and the commit tree cannot happen.**
   - The capture appends to an evidence file that must then be staged, and the status docs change in the same commit.
   - My condition demanded a fixed point that does not exist.
   - The obligation under Article IX is this: the record must not imply more than happened.

3. **Your own stated limit is the correct one and must be written down.**
   - An index stamp records what was staged at capture time.
   - It never records which files pytest imported.
   - The run executed the combined lane worktree.
   - For the red archive, the byte-verified baseline origins prove provenance, not the stamp.

**CONDITIONS**

None are new. The final evidence condition is restated as you wrote it:

- The `387bab5d` captures are labelled superseded for index provenance, with raw output kept.
- Evidence-02 and evidence-03 get fresh focused captures with all product and test source staged.
- `18f67176` is named as the product/test snapshot for the quiet full suite.
- Each evidence file carries one sentence: the runs executed the combined lane worktree, not an isolated index snapshot.
- No stamp is hand-edited.
- Each commit gets a fresh contract stamped against its own final index.
- After the suite, only evidence and tracking files change. If a scoped fix changes a product or test blob, the affected focused capture is re-run and the report says so.

The earlier conditions on PNG restoration, the red-first note, the PR body and story 07 staying open are unchanged. None of them is reopened.

**MISSED**

- I missed this one. I asserted gate behaviour without reading the gate. The cost to the owner would have been a wasted loop, not a wrong merge.
- One item for the ledger, not for this lane. Delivery Workbench records a capture's `Index-tree` that nothing ever verifies. It is a framework matter for `pmo-roadmap`. Add one line under LEDGER if you agree.

**TUESDAY:** No change. This concerns proof records and no face.

**UNKNOWN**

- I did not read `evidence.py`'s `latest_passing_capture` selection logic beyond its use here.
- I did not read `dw verify`'s history-side rules.
- The full-suite result, the commits and the PR remain pending. This check declares none of them green or done.


## Closure-record check — Muad'Dib, 2026-09-19

Muad'Dib closure-record check of lane A, Claude session `3065fb0e-50e2-4f71-bb3f-2cd76fc4b791`. I read the records only. I ran no tests and made no edits. `git diff 18f67176 -- holdspeak` is empty here too.

**VERDICT: RATIFY-WITH-CONDITIONS**

The evidence honestly supports the three backend flips and a review PR. It does not support a merge or any phase exit, and the records do not claim either. Conditions 1–3 and 5 must be in before the flips; condition 4 must be met before merge. I found no new source findings.

**FINDINGS**

1. **The failure arithmetic is true to the raw log.**
   - `audits/full-suite-astra.log` ends with `24 failed, 11159 passed, 125 skipped, 4 xfailed in 1642.14s`.
   - The table sums to 24 (7 + 2 + 2 + 9 + 2 + 1 + 1).
   - I matched all 24 `FAILED` lines to a row in the table.
   - No record calls the suite green. The report, the status "Where we are", and evidence-03:1211 all carry the raw count.

2. **The nine updated expectations tighten the fences.**
   - `test_phase143_routing_authority_census.py` removes the two `meeting_intel_service.py:79/:81` entries for `resolve_meeting_placement`. The mutable-config resolver is gone from the run path, so the census got stricter.
   - The rest of that file is line re-anchoring.
   - `test_phase143_surface_fallback_census.py` classifies the two new concierge helpers and does not exempt them.
   - The `test_phase143_inference_capability_census.py` edits are line moves only.
   - The schema snapshot change is two lines, which are the two new columns.
   - I did not read the diffs of the two posture tests, `test_dictation_session_admission.py` and `test_phase143_meeting_live_cutover.py`.

3. **The capture-stamp correction is applied as agreed.**
   - Evidence 02, 03 and 05 each state "The runs executed the combined lane worktree, not an isolated index snapshot".
   - Each file labels the `387bab5d` captures as superseded and keeps them.
   - The post-suite captures are stamped `15a395aa` (02: 185 passed, 11 skipped; 03: 176 passed, 4 xfailed) and `18f67176` (05: 59 passed).
   - The report records the uncompared-stamp gap as a `pmo-roadmap` follow-up.

4. **The amendments and the accepted regression are stated honestly.**
   - "Decisions made" names the Phase 200 proposal pipeline as "a deliberately accepted regression of shipped product, not an inherited failure".
   - The adapter amendment says "adapter support, not observed model quality" and discloses the shared live/deferred schema hash.
   - The scanner row says its concurrent-writer cause "is an inference … not a proven exact writer". That is the right register.
   - The report states the shots show "the saved transcript in the existing face" and that the stub engine plus fixture WAV "prove plumbing, not … the owner's usefulness verdict".

5. **Material: the B-owed criteria have no home in any B story.**
   - Story 02:25 (the Record refusal token) and story 05:23 and 05:27 (Models renders the result; one gesture, no modal, shots) are left as `- [ ] B-owed`.
   - Story 01 lists under Out: "the Models screen itself (story 05)".
   - Story 06 covers labels only.
   - Neither 01 nor 06 has an acceptance criterion for the token or for the "Use this for meeting summaries" control.
   - After the flips, 05 reads done and no open story requires anyone to build the control the owner must press.
   - That is a first-use hole at the record level. It fails Tenet 2, Tenet 3 because the door is missing, and Article IX.
   - The missing criteria are in lane B, which is my lane. The fix is mine to accept and yours to record.

6. **Material: two integration tests went red because of this lane and have no owner.**
   - The tests are `TestIntelQueueApiEndpoints::test_intel_jobs_list_retry_and_process` and `test_partial_intel_names_retained_work_and_supports_retry_or_skip`.
   - Both exercise story 03's own endpoints, pass on baseline, and fail because of lane A's contract.
   - "Outside A's assigned test directories" describes the brief. It does not assign anyone to fix them.
   - As the merger, I will not merge while tests this PR turned red stay red.
   - The flip is still honest, because the story's criteria are met and the 409 response is the designed behaviour.
   - The merge is not honest until the two tests are migrated. Fails Article IX.

7. **Minor wording: story 02:27 reads "A-proven: Existing admission fences stay green".**
   - Two admission tests had their expectations rewritten to the new posture. That was correct to do.
   - The phrase "stay green" hides the rewrite. Fails Article VI.

**CONDITIONS**

1. Before the 02 and 05 flips, add an "Owed by lane B" table to `current-phase-status.md`. It lists each transferred criterion verbatim with its receiving story:
   - The Record refusal token goes to HS-201-01.
   - The Models summary-selection control, its conflict and partial rendering, and its shots at both widths go to HS-201-06. Use 04 if you judge that the better home, and say why.
   - Muad'Dib accepts this transfer here as lane B's owner. I will add the criteria to the B story files in `wt-201-b`.
   - In 02 and 05, reword the boxes as "transferred to HS-201-NN (see status)", so a done story does not carry an open acceptance box.
2. Run `.githooks/dw gate --porcelain` and `.githooks/dw check holdspeak` before each commit, and read the output. I do not know whether the gate refuses a done story that still has an unchecked criterion.
3. Reword 02:27 to say that two admission expectations were updated to the speech-only posture (name them), and that the other admission fences are unchanged and green.
4. Before merge, not before the flips or the PR: migrate the two integration callers to an exact assignment plus the read-model hash, in this PR, by Astra.
   - As checker and as B's owner I consent to lane A touching those two files in `tests/integration/`.
   - Do not weaken the 409.
   - The PR body lists them under "Merge blockers" beside the A+B interlock.
5. The PR body states these points:
   - This is a review PR with no merge.
   - Both verdicts.
   - The raw suite line and the classification table.
   - The accepted Phase 200 regression with its BACKLOG return path.
   - The two merge blockers.
   - Story 07 and every exit criterion stay open.
6. Commit order is 02, then 03, then 05, one flip per commit, each with its own fresh contract. If the PNG restoration has not been repeated after the last focused reruns, repeat it before each `git add`.

**MISSED** (ranked by cost to the owner)

1. The summary-selection control has no story that owns it. On his Tuesday the backend accepts a gesture that no face offers (finding 5).
2. The two lane-caused red tests would merge as "ledgered" debt and would hide the next real regression on those endpoints (finding 6).
3. A done story that carries open boxes either trips the gate mid-commit or teaches the roadmap that done can include open criteria.
4. Nothing new is wrong in the source.

**TUESDAY:** Not yet from this lane alone, and the records say so. The backend is ready. He still cannot complete the job until B ships the hash on Run and Retry, the refusal token, and the summary-selection control now assigned by condition 1.

**UNKNOWN**

- The diffs of the two rewritten posture tests, which I did not read.
- The baseline reproduction logs, which I did not open beyond their names.
- The full middle of evidence-02, evidence-03 and evidence-05. I read the tails and grepped the rest.
- The `BACKLOG.md` text.
- Whether the full index was re-staged after the per-commit reset. The worktree currently shows product files unstaged.
- The gate's behaviour on unchecked boxes in a done story.
- Lane B integration, the owner's desk, live-model quality and the sitting are outside this check.
- This check is not counsel-on-built of the PR. That check happens after the PR exists and B's consumer lands.
