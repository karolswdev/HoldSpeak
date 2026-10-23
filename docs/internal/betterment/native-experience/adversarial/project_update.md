# project_update

Job: Draft a true project update without freezing the Desk  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd`  
Reviewer task: `review_project_update`  
Evidence class: source/assertion review plus static Room captures at 1440 and 393; no execution, live Desk, provider/native action, or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The audit covers the core job: from Room or palette, press Write, read pinned meetings, decisions, actions and caveats, show a deterministic source-grounded draft without blocking the Desk, optionally run the engine, review provenance, edit, save, regenerate, publish, then explicitly Send or Mark delivered. Existing guards cover responsive health, a durable manual engine job (`tests/integration/test_desk_project_room.py:686-730`, `750-797`), deterministic fallback, and source/claim assertions. It is incomplete on source/provider partial failure, task identity across close/restart, first-write automation versus direct engine, and unknown retries through publish/Send. Keep this one project-artifact job, not a generic wizard.

FINDINGS:

1. **P1 — the returned task is not durable at the Room boundary.** The poller is React state and unmount stops it (`web/src/features/project-room/update/useUpdateController.ts:340-420`, `:349`); restoring a place restores draft/body, not the job (`:619-643`). The service can recover/read a durable job (`holdspeak/services/project_update_service.py:2422-2462`), but no project-scoped discovery or reopen contract is named. After switching projects, reload, or hub restart, the owner can lose the answer and press Write again. This fails Tenets 3, 5, and 7. Correction: require `{project_id, base_update_id, job_id, automation_run_id, state, result/update_id}` and define Room, Workbench result, and editor consumers for every state, including late.

2. **P1 — Stop does not stop the real first-write automation side effect.** First Write can start `_run_automation_pass` (`holdspeak/services/project_update_service.py:2302-2343`), which runs Workbench and may write an update (`:2345-2395`); Stop only changes the job row (`:2464-2472`). The existing stop assertion covers the non-automation branch (`tests/integration/test_desk_project_room.py:1218-1225`). A clear Stop can still produce a late update, failing Tenets 3 and 6. Correction: cancel/suppress delivery, or show an explicit late/completing state and resulting update in the same receipt; add the real first-Write/Stop case.

3. **P1 — UI retries omit the backend’s idempotency identity.** Save, regenerate, and publish omit `command_id` (`web/src/features/project-room/update/api.ts:53-64`, `:79-99`), although routes accept it (`holdspeak/web/routes/project_updates.py:203-211`, `:248-260`, `:294-305`). Replay tests supply IDs directly (`tests/integration/test_update_routes.py:488-558`), not through buttons after a lost response. Retry can create extra drafts or report refusal after publish succeeded, failing Tenets 3 and 6. Correction: mint one ID per press, retain through unknown/retry, and read back the canonical row/receipt.

## Convergence

Converge with `projects_room` on `project_id`, `update_id`, source manifest and revision; `automation_schedule` on Workbench run/result; `send_prepare`/`send_commit` on SendWell destination, egress, unknown response and receipt; and `meeting_intelligence`/`decisions` on exact source refs. First consumers: Room Update line, Workbench result, editor, SendWell. Keep the update a derived snapshot, not the canonical meeting/decision record, and Mark delivered distinct from external Send. A generic task surface would erase consent and provenance boundaries.

## User experience

The static captures (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/room-1440.png`, `room-393.png`) show a compact Write action at both widths. They do not show editor, retained task, or outcome; source cannot certify beauty, accessibility, or delight. Immediate deterministic text and source claims should please, but trust falls if Stop, return, or Retry hides or duplicates results. Put the receipt beside the Update line; preserve Room/editor, provenance chips, and explicit Send egress.

CONDITIONS: specify durable identity and close/reopen/restart; resolve automation cancellation versus late completion; bind command IDs to mutating verbs; and state source/provider partial coverage plus publish/Send receipts.

MISSED: (1) highest cost, close/switch/reload/hub restart while running or complete; (2) automation Stop followed by late delivery; (3) network loss on Save, Regenerate, Publish, Send; (4) stale sources, excluded 1:1s, and changed decisions preserving “not read/left out” provenance.

TUESDAY: The one-press draft is promising, but return, Stop, and Retry can still hide or duplicate the Tuesday outcome.

## Acceptance challenges

1. With linked sources and a model refusal, Write keeps the Desk responsive, names the refusal, preserves the deterministic draft/source coverage, and opens an exact citation.
2. Start first-write automation, leave/reload, then reopen after success, failure, or hub restart: the same job/base update appears once, without focus steal or duplicate.
3. Stop automation and allow a late answer: no unintended update, or a receipt clearly says late and offers the bounded next action; original words remain safe.
4. Edit while the engine runs, then lose Save/Publish/Send response: Retry with the same command produces one canonical update and one delivery receipt.

UNKNOWN: No tests were executed, and no live walk, API/provider/native action, or owner-state write was performed. The captures are Room shell states, not the update editor or recovery states. No later complete owner result, performance claim, accessibility assessment, or owner acceptance is established.
