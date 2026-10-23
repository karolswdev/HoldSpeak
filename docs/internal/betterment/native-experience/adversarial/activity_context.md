# activity_context — adversarial review

workflow id: activity_context  
job: Inspect current-device activity and the always-on context  
baseline: main55572802181d6a8045f6d27e3c722aaf5694dbbd  
reviewer task: review_activity_context  
evidence class: source review plus desk-sweep captures; no execution or owner acceptance

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The audit names two real entry points, but not one job. Activity opens a
current-device ledger, refreshes local browser databases, and should return the
architect to work. Context edits a singleton owner document and ends only when
a later agent run receives that revision. The manifest confirms separate
windows (`web/src/desk/applications.ts:285-301,340-355`). One resource model
would hide local Safari/Firefox collection (`holdspeak/activity_history.py:54-134`)
versus external GitHub/Jira capabilities
(`holdspeak/connector_packs/github_cli.py:106-116`), and retained local context
versus a run that may carry it to a provider.

FINDINGS:

1. **High — the family is over-broad for implementation.** The inventory gap
   says “context/resource identity,” but defines neither identity nor terminal
   outcome. Cost: a worker can invent one adapter or lose the singleton revision
   model (Tenets 3 and 5). Correction: keep `activity_context` for traceability
   but specify two tracks: local activity resources with source/checkpoint
   identity, and one owner-context document with revision/hash identity. Share
   only existing app/window/feedback seams.

2. **High — disabled, absent, stale, and failed collectors are not a user
   contract.** Status has readable sources, checkpoints, and last errors
   (`holdspeak/services/activity_ledger_service.py:16-33`), but the face only
   reads the global `enabled` bit (`web/src/pages/cores/ActivityCore.tsx:85-110`)
   and discards refresh results (`:72-84`). A paused importer returns disabled
   (`holdspeak/activity_history.py:175-184`), while `build_activity_context`
   still reads stored rows and the runtime injects it into every plugin
   (`holdspeak/activity_context.py:53-126`; `holdspeak/web_runtime.py:264-270`).
   Cost: the architect cannot tell “no source,” “paused,” “read failed,”
   or “old retained rows.” Pausing new collection is distinct from reuse of retained history; source does not establish that pause promises to disable both
   (Tenets 1 and 3). Correction: define/render these states, state retained-row visibility and plugin reuse accurately. Preserve a collection-only pause if that is the intended contract; do not infer a privacy violation or add another toggle merely because retained history remains usable. Keep external connector
   egress separate; do not label it local.

3. **High — Context can overwrite a newer edit.** The PUT accepts only content
   (`holdspeak/web/routes/constitutional.py:36-52`); the backend reads the
   current revision and increments it without a precondition
   (`holdspeak/constitutional_context.py:54-87`). Two Desk windows can therefore
   save stale text after the other window. Cost: loss of the senior architect's
   briefing (Tenet 7). Correction: require current revision/hash, return a
   named conflict, offer in-world reload/choose, and stamp the accepted
   revision/hash into the receipt.

4. **Medium — the fast path stops at inspection.** Activity records have no
   row-level route to the existing selected-record/dictation handoff
   (`web/src/pages/cores/ActivityCore.tsx:139-205`; `tests/integration/test_web_activity_nudges_api.py:149-168`).
   Context has retry and plain save failure copy, but history-load failure is
   silently swallowed (`web/src/pages/cores/ConstitutionalContextCore.tsx:48-53`).
   Cost: the owner may not know whether this is inspection-only or a route to another task (Tenets 3 and 7). Correction: bound the inspection job, or specify the existing supported trigger → inspect → use → return path, and expose named
   refresh/history outcomes without adding a screen.

## Convergence

First consumers are `speech_dictation` (selected activity record), `source_context`
(project/object identity), and `feedback` (pending/refused/indeterminate
 outcomes). `meeting_aftercare` may consume meeting candidates, but should not
 inherit browser-collector identity. `accounts` owns external provider health;
 `setup` owns device readiness. Reuse `APP_ID`, `RESOURCE_ADAPTER`,
`ASYNC_STALE`, `SOURCE`, and `FEEDBACK`; retain separate local-ledger,
connector-egress, and singleton-context boundaries. Merging them into one
generic context page would erase the very privacy and revision semantics this
audit must make visible.

## User experience

Captures show a calm shell and direct Context pad. Activity says “No activity
yet” while a populated Finished section sits below
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-activity-393.png`);
without source readiness or refresh outcome this is not a trustworthy Tuesday
read. The Context capture is quiet, but does not prove Save reached the next
run; this is a source/capture inference, not owner acceptance.

CONDITIONS: Split the tracks; define collector/egress and paused-state
semantics; add revision-conflict and next-run convergence rules; cover the
challenges below using existing controls and services.

MISSED:

1. A fresh device with no readable browser source versus a disabled source.
2. Safari succeeds while Firefox fails, then refresh and return to work.
3. Two Context windows save the same document concurrently.
4. A saved revision is consumed by a later run and appears in its receipt.

TUESDAY: Not yet—the owner can open both windows, but cannot reliably know why
Activity is empty or whether a Context edit is the one the next run uses.

## Acceptance challenges

1. With no browser files, Activity says source unavailable (not merely “No
   activity yet”); with tracking paused, it shows the settled retained-row and
   plugin-injection behavior.
2. With readable Safari and a failing Firefox source, Refresh reports each
   outcome, keeps the successful source identity, and a second refresh does not
   duplicate records (the checkpoint guard remains).
3. Select an existing activity nudge, complete the real dictation handoff, and
   verify the selected record is pinned once, then cleared on the next run.
4. Save Context in window A, attempt a stale save in window B, resolve it
   in-world, and verify the next run receipt carries the accepted revision/hash.

UNKNOWN: No tests, builds, live Desk calls, provider/native actions, performance
measurements, or owner walk were run for this review. The captures are prior
desk-sweep artifacts, not fresh proof at this baseline. Cross-window conflict,
fresh collector availability, and external-provider egress were not observed.
