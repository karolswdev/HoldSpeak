# automation_schedule

Job: Schedule or trigger repeat work and recover its result  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_automation_schedule`  
Evidence class: active source and representative assertion inspection, plus static 1440/393 captures; no tests, live Desk/API/provider/native actions, or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The real job starts in Automations: define Do/About/With/Put it in; choose manual, schedule or event; enable it; mint one occurrence; run it; file or prepare the result; then find, read, retry or return after close, restart, refusal or destination failure. The recipe states one occurrence per instruction and the Inbox/Needs/Send boundary (`docs/internal/betterment/workbench/RECIPE.md:85-108`). Automations is active (`web/src/desk/applications.ts:303-318`), while Rhythm is parked under Settings (`web/src/desk/applications.ts:232-250`), so scheduled recording is distinct.

The inventory only names the manifest, recipe and broad capability slice (`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:2737-2758`) plus a migration unit test. It omits the active When picker, conductor, reaction projection, result wire and delivery contract, so it is not sufficient.

FINDINGS:

1. **P1 — trigger scope and evidence are incomplete.** The picker offers four schedule shapes, three GitHub events and manual mode (`web/src/desk/components/automation/WhenEditor.tsx:64-125`); the backend enforces one chosen start and a provider baseline (`holdspeak/services/workbench_service.py:242-316`; `holdspeak/services/automation_when.py:41-89`). The audit does not state this boundary or distinguish parked Rhythm. Owner cost: workers can invent a generic scheduler, failing Tenets 1, 3 and 5. Correction: include these paths; state one-start semantics, limits, owner enable, baseline and alias.

2. **P1 — event failure has no durable user outcome.** Projection exceptions are caught and returned as an ephemeral `projection_failed` result (`holdspeak/services/reaction_service.py:550-618`), while durable projection rows are written only on success (`holdspeak/db/automations.py:305-330`). The Automation window reads Workbench items/results, not reaction attempts (`web/src/desk/components/automation/AutomationWindow.tsx:343-367,828-867`); its event assertion checks only the About words (`web/src/desk/__tests__/automation.app.test.tsx:740-745`). A projection failure can be retried by the heartbeat without a joined user-facing outcome. Failure may occur before a run or after an existing operation already has a durable receipt; the catch does not prove all kernel evidence is absent. This fails Tenets 3, 6 and 7. Correction: join the existing event, deterministic item/request id and any operation receipt first. Retain otherwise unrecorded pre-run failure in the existing projection/attempt path, expose it beside the result, and retry the intended step without a second ledger or model run.

3. **P1 — Put it in failure is not retained.** The recipe promises Inbox, Needs or Send preparation (`docs/internal/betterment/workbench/RECIPE.md:99-101`), but `deliver_run` only logs and returns a failed delivery (`holdspeak/services/automation_runs.py:1027-1056`). `AutomationResult` has no delivery state (`web/src/desk/components/automation/model.ts:10-30`), and the card shows model/egress plus Send, not whether filing succeeded (`web/src/desk/components/automation/ResultCard.tsx:43-103`). The integration assertion observes `filed: false` only in the immediate response (`tests/integration/test_desk_workbenches.py:1292-1299`). The owner can see a good answer and assume it was filed. This fails Tenets 3 and 6. Correction: store one delivery receipt/status per artifact, surface NOT FILED/UNKNOWN with the concrete reason, and retry that delivery idempotently without rerunning the model.

## Convergence

Converge with `automation_build` on workbench/source/occurrence/result identity; `feedback` on operation states; `mcp_tools` on `UsedLines`, egress and child receipts; `send_prepare`/`send_commit` on destination receipts; and `agent_hand`/`agent_result` for hand profile, review and launch identity. First consumers: Automations home/window, Today/Needs, ResultCard and SendWell. Keep schedule/provider authority separate from agent review and external send; do not make a universal scheduler.

## User experience

The captures show a readable one-window sentence and result at 1440 (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/automation-1440.png`) and a stacked 393 layout (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/automation-393.png`). This is a promising manual path, not proof of trigger recovery, delivery truth, accessibility, performance or delight. Put trigger outcome and delivery receipt in the same result path.

CONDITIONS: Add the active trigger boundary, durable event-failure lifecycle, durable delivery outcome, and close/reopen/restart acceptance to the audit. Keep existing Button, egress, NEW and receipt guards; this adds no owner gate.

MISSED:

1. Highest cost: provider failure or stale event with no durable event identity and retry.
2. Destination deleted or external preparation unknown after a successful run.
3. Window close, hub restart, or schedule edit while a run is in flight.
4. Multiple triggers in one minute and one-result/idempotency proof.

TUESDAY: The manual result path is compact, but the owner cannot yet trust that an unattended trigger was delivered or know where to return after failure.

## Acceptance challenges

1. With the window closed, fire the controlled Every-minute schedule, reopen after a hub restart, and show one occurrence, its trigger/run receipt, next fire and result without duplication.
2. Force a supported projection/run failure for one recorded GitHub review event, then recover it: show one event id, a named failure, Retry, and one final result.
3. Run with `inbox` and inject a refused note write at delivery, and verify NOT FILED plus delivery-only Retry; the model runs once and the eventual note has one stable artifact link.
4. Disable or edit a live schedule during an in-flight run, reopen the automation, and show whether disabling affects only future triggers or also cancels current work. Preserve the current run’s authoritative receipt and prevent new occurrences after disable; do not assume disabling must cancel it.

UNKNOWN: No tests were run. No live Desk walk, API/provider/native action, owner-state write, performance/accessibility check or owner acceptance was observed. Captures are static known-state faces; they do not prove schedule firing, EventKit/calendar readiness, notifications or recovery.
