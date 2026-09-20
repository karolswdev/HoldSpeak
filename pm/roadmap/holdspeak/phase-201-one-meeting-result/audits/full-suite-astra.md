# Lane A full-suite classification — Astra, 2026-09-19

Session `01a0bbc3-9bbd-7513-a76d-f6cc139fae2d`. Charter baseline
`fdc3fc45bccf2b3b995ae9f4d13cb58691717a75`.

The quiet full run used isolated HOME, Node 22, the shared read-only browser
cache and `uv run --extra dev pytest -q -n auto --ignore=tests/e2e/test_metal.py`.
No workers edited during it. Product/test index snapshot:
`18f67176b9146ddd441b13c60b70687674c1230f`. The run imported the combined
lane worktree; the index stamp is not import provenance.

```text
24 failed, 11159 passed, 125 skipped, 4 xfailed in 1642.14s (0:27:22)
```

Complete output: [full-suite-astra.log](full-suite-astra.log). No full-suite
green is claimed. All post-run changes are test expectations, canonical
contract snapshots and records; product code did not change. The affected
focused suites are recaptured in evidence 02 and 03.

| Count | Classification | Evidence and disposition |
|---|---|---|
| 7 | a — canonical contract artifacts stale after the intended change | API manifest, DB schema, routing-authority census, private-helper census, and three inference-capability census assertions. Snapshots/line anchors updated without relaxing the guards. Focused rerun in evidence 03. |
| 2 | a — former recording posture | Dictation-session test expected the old live+speech budget; unassigned Stop test expected implicit text work. Speech-only budget/members and zero queued aftercare are asserted; active bundle aftercare stays covered. Focused rerun in evidence 02. |
| 2 | a — old integration callers, migrated | `TestIntelQueueApiEndpoints::test_intel_jobs_list_retry_and_process` and `test_partial_intel_names_retained_work_and_supports_retry_or_skip` posted without `expected_selection_hash` and received 409 in the full run. Both pass on the byte-checked charter baseline: [baseline-legacy-callers.log](baseline-legacy-callers.log). Muad'Dib assigned these two test files to A at closure. Both fixtures now create an exact compatible assignment and submit the current read-model hash; Astra's broader web-server/recovery/HTTP capture passes 98 tests (evidence 03). New HS-201 HTTP tests cover valid, missing and stale hashes on all three endpoints. |
| 9 | inherited baseline failures | Nine original tests reproduced on byte-checked charter sources: [collection and module origins](baseline-glass-collect.log), [raw run](baseline-glass-run.log). Two doc-drift guards; HS-153 guardrail deny focus; both HS-171 zero-badge widths; four HS-200 preparation tests. One preparation width times out waiting for the running state on baseline rather than failing the next Stop assertion; it is not an identical stack trace. All seven browser cases fail before any new summary-selection behavior. |
| 2 | inherited baseline failures | Daily-loop widths fail at preparation before the meeting: [baseline-daily-loop.log](baseline-daily-loop.log). |
| 1 | inherited baseline failure | UAT ledger is already stale: [baseline-ledger.log](baseline-ledger.log). No unrelated regeneration in this lane. |
| 1 | c — parallel-run interference, two quiet passes | The canon scanner's no-write test fingerprints `git status`; browser workers changed historical evidence during the full run. Two independent quiet runs pass; raw output is below. Interference is an inference from the changed status, not a proven exact writer. |

The four strict xfails are the ratified Phase 200 proposal-chain regression,
not an inherited failure. Live summary readiness is a fixture precondition.
Each proposal scenario now imports, links and successfully queues its own run
before installing the xfail marker. The original proposal/Review assertions
remain. The affected six tests are rerun after this test-only tightening.

## Homes and limits

The integration callers are fixed. The inherited suite failures are assigned to
Phase 201's lane A debt ledger and `../lane-a-handoff.md` for integration
follow-up. The production proposal regression is parked in `../../BACKLOG.md`
under “Phase 201 parked summary follow-through”, with a disclosed-route
return path. The owner may overrule that amendment at the sitting.

Restored 402 tracked historical PNGs and six JSON/Markdown artifacts from
HEAD; parked six untracked historical shots under `.tmp`. New Phase 201
restart shots remain. No owner desk state, microphone, main checkout or
lane B worktree was used.

## Quiet scanner reruns

Both runs use fresh isolated HOME with only the named node, after all workers
stopped editing. No assertion changed.

```text
.                                                                        [100%]
1 passed in 1.10s
```

```text
.                                                                        [100%]
1 passed in 0.85s
```

`git diff 18f67176b9146ddd441b13c60b70687674c1230f -- holdspeak` is empty after these follow-ups.
