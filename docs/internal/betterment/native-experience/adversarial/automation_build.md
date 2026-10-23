# automation_build — adversarial review

workflow id: automation_build  
job: Create one automation with instruction, sources and one result  
baseline: main55572802181d6a8045f6d27e3c722aaf5694dbbd  
reviewer task name: review_automation_build  
evidence class: source inspection, existing assertions, and desk-sweep captures; no execution or owner observation

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The real job is home/launcher → starter or scratch record → name, Do, About,
With, When and Put it in → Run now → one readable result → close/reopen or
return from Today and find that result. The active host is
`AutomationWindow`; the old queue is only behind RAW
(`web/src/desk/components/automation/AutomationHost.tsx:1-26`). The recorded
fast path is credible for a named starter: one window, engine add, and result
within six presses (`web/src/desk/__tests__/automation.app.test.tsx:775-823`).
The audit is not yet a complete brief for scratch creation, delayed/terminal
outcomes, or the return path after a scheduled run.

FINDINGS:

1. **P1 — scratch naming is not joined to the creation path.** The picker posts `New automation` (`web/src/desk/components/WorkbenchTemplatePicker.tsx:98-108`), and the specialized window shows a plain title (`web/src/desk/components/automation/AutomationWindow.tsx:591-619`). This does not prove renaming is impossible: the common primitive update map supports workbench names (`web/src/desk/store/dataSlice.ts:94-111`), and the common rename contract permits them (`web/src/desk/infoContract.ts:138-142`). Owner cost: indistinguishable scratch names or a hunt for the existing rename door. This fails Tenets 3 and 7. Correction: trace and test that door from creation through reopen; expose the existing EditInPlace/name species in the builder only if that path remains awkward. Do not invent a naming screen or say only parked code can rename.

2. **P1 — item results and parent-run outcomes are not one audited lifecycle.** The face filters occurrence-item results to `done`/`failed` and separately shows claimed work as running (`web/src/desk/components/automation/AutomationWindow.tsx:343-359`). `results_of` projects item state (`holdspeak/services/automation_runs.py:927-972`), while the parent runner retains succeeded/cancelled/expired/failed/indeterminate disposition and partial counts (`holdspeak/services/workbench_runner.py:196-217`). The audit does not join them. Owner cost: a retained item or receipt may not explain what happened to the interrupted parent. This fails Tenets 3 and 6. Correction: map the actual parent/occurrence/result IDs and existing states into return/retry behavior; preserve completed work. Do not invent universal partial/delayed item states or call the running indicator absent.

3. **P1 — refresh failure is silently stale.** `load` keeps the old detail
   after a failed refresh (`web/src/desk/components/automation/AutomationWindow.tsx:311-325`),
   but the error is rendered only when no detail exists (`web/src/desk/components/automation/AutomationWindow.tsx:658-660`). A
   returned window can present old sources, schedule or result as current.
   This fails Tenet 6. Mark the retained view `STALE`, keep edits/results
   visible, and provide the local retry; include this in the close/reopen and
   Today return acceptance rather than clearing the useful last read.

## Convergence

`automation_schedule` owns scheduler/event firing; share the automation
identity, occurrence/result lifecycle, `next_run_at`, and `OP_OUTCOME`, with
the first consumer being a closed-window scheduled run. `engines_assignment`
owns readiness and destination facts; reuse `assignment_summary` and the
existing With/Egress composition (`AutomationWindow.tsx:770-789`), while
keeping automation's plain-language choice separate from the Engines app.
`source_context` owns named source identity; reuse About chips and provenance,
but retain the event subject boundary. `send_prepare`/`send_commit` own the
existing `SendWellsFold` result action (`ResultCard.tsx:89-103`), not a second
send flow. `today_followthrough` consumes `fetchAutomationNews`
(`web/src/desk/api.ts:1238-1251`) and opens this same window. Do not merge
these families into one wizard: their permissions, egress, and recovery
contracts differ.

## User experience

The 1440 capture shows a quiet sentence, one result well, and one-window
craft (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/automation-1440.png`).
The 393 capture keeps the sentence and Run now reachable, but the result body
continues below the viewport
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/automation-393.png`); this supports a
scrollable mobile flow, not a claim that the result is above the fold. The
existing assertions prove the fast starter and readable failure words, not
schedule firing, stale recovery, or owner delight.

CONDITIONS: Trace the scratch-name path; specify and prove actual parent/item terminal and stale
states with durable return/retry; hand the scheduled tick and Today/news
reopen scenario explicitly to `automation_schedule`/`today_followthrough`.

MISSED: (1) named scratch automation surviving close/reopen; (2) scheduler
fire while the window is closed and result discovery; (3) hub restart or
indeterminate completion; (4) source deletion between setup and run.

TUESDAY: A named starter is fast and legible, but scratch naming and truthful
delayed/recovery return are not yet dependable.

## Acceptance challenges

1. Start from scratch, name it, add one source and instruction, choose an
   engine, run once, close, reopen from Automations, and read the same result.
2. Enable a schedule, close the window, let one controlled tick claim and
   finish, then open Today’s NEW row; opening it clears NEW without losing the
   result or source names.
3. Exercise an actual supported parent cancellation/indeterminate outcome or partial completed count; after a
   refresh/reopen the state, reason, run identity and allowed retry remain.
4. Remove a referenced source before the run; the face names the missing
   source, keeps the automation, and reruns only after correction.

UNKNOWN: No tests, builds, live Desk/API/provider/native actions, scheduled
run, owner data, performance measurement, or owner acceptance were performed.
The captures are prior evidence only; source and test existence do not prove
execution.
