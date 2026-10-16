# Next connected walks — preparation only

2026-10-16. Source-derived procedure for the bounded candidates in
NEXT-DAILY.md and NEXT-CREATION.md. No walk, test, browser or product change was
performed for this document. Root settles implementation and runs the cases.
HOLD FOR SHIP. Tenets 1/3/5/7: reuse the rig, real authorities and current faces.

## Small execution shape

Use `scripts/graph_walk.py` and its `Hub`, `Hub.api`, isolation and provenance
helpers, following `agent/skills/holdspeak-capability-verifier/SKILL.md`,
“Walk a case”. Reuse `cli: seed_people_prep`; do not build another People rig.
Adapt the first delivery's `.tmp/flagship/tour.py` only for the connected poses
and extra readbacks. A small producer helper may call existing repositories or
services where no HTTP producer exists; record its exact method and resulting
IDs. Do not inject finished review observations, rendered responses or cards.

Each invocation owns one temporary HOME outside the owner's real HOME, one hub,
one browser context and a new output directory. Keep People key/state beneath
that HOME. Test/build/browser execution stays serialized through
`scripts/test_lock.py`; never ports 8765/4488, owner providers or microphone.
Capture revision/dirty/build, actual producer IDs, request method/body/outcome,
source readback and before/after shots. A browser fault or delayed response is
a declared boundary substitution, not a hub failure. Use existing `http_fault`
and `http_fault_lift` for failure/recovery cases.

Run the connected faces at 1440 and touch 393. Also resize the actual owning
window to 600 px on desktop, as the first delivery did; viewport width alone
does not establish a narrow window. Inspect the target well, visible next
action, title wrapping, local scroll and return position. One case has one
named terminal predicate; use setup checks for earlier links. Keep protocol
cases separate from face cases and carry observed results forward by path.

Suggested new case stems (not minted here): `case.flagship.prep.commitment`,
`case.flagship.prep.newer_draft`, `case.flagship.project.review`,
`case.flagship.thread.todo`, `case.flagship.thread.keep_recorded` and
`case.flagship.settings.remote_read`. Parameterize the three Prep fields in
the bounded interaction check; do not create a new browser suite per field.

## C: People Prep → both commitments → linked Project Review

Reuse the producer and setup in
`docs/internal/philo/graph/atlas-phase13-astra.json`:
`case.p13.people.prep.protocol` and `case.p13.people.prep`. The exact producer is
`scripts/philo13_b4_fixture.py:seed_people_prep`, already called by the rig's
`seed_people_prep` CLI step. It uses the ICS conductor, `save_meeting`, real
People routes/encrypted store and `ProjectService.create_project`; no SQL seed.

Capture `relationship_id`, `event_uid`, `event_source_id`, `project_id`,
`meeting_id`, `session_id` and `action_id` from its returned `ids`. Fixed meeting
and action identities are `philo13-b4-meeting` and `philo13-b4-owned-action`;
relationship/project/session IDs must come from the producer. Confirm the
suggestion with `POST /api/people/relationships/{relationship_id}/calendar-links`
using `{uid:event_uid, source_id:event_source_id, label:event_title}`. Read
`GET .../{relationship_id}/brief`: next event UID/source, linked project ID,
accepted open action ID/source meeting and agenda must match those captures.

Produce the two **People commitments**, independently of the meeting action:

| Genuine call | Capture/readback |
| --- | --- |
| `POST /api/people/relationships/{r}/requests`, `{body:"Review Priya's migration options"}` | `request.id`; a request alone is not a commitment. |
| `POST /api/people/requests/{request_id}/accept`, `{}` | `commitment.id` as `leader_commitment`; direction `leader_owes`, open state. |
| `POST /api/people/relationships/{r}/owed`, `{body:"Send the compatibility notes"}` | `commitment.id` as `report_commitment`; direction `report_owes`, open state. |
| `GET /api/people/commitments/{id}/execution` for each captured ID | Exact commitment, relationship, direction/body/state and execution links. |

Open the real relationship's Prep. Press each obligation title, verify the
inspector addresses its own captured commitment and appears in its owning
section, then Close and return to that row. Opening must leave state/history
and execution links unchanged; do not call Workbench dispatch to prove reading.
The existing execution GET supports both directions
(`holdspeak/web/routes/people.py:278`; `PeopleService.get_commitment`).

For each agenda/You owe/They owe Add, submit text A, then type B before A's
response reaches the UI. A small browser response gate may let the **real POST
commit**, hold its response, accept B typing, then release A. Record that seam;
verify one A record through the appropriate brief/one-on-one/commitment reads
and B still in the original person's field. Back/tab/reopen and a second
relationship must not move B. A separate browser `http_fault` refusal must
retain A, create no A record and expose the exact failed action. Do not replace
this with a successful-looking fabricated Add response.

For a genuine pending Project Review, use the same linked project/meeting:

1. `POST /api/projects/{p}/meetings/{m}`, `{}`, confirms the association.
2. `PATCH /api/action-items/{action_id}/edit` with an explicit prior-date `due`
   produces a real overdue action; derive yesterday from the run clock and
   record it. The B4 action is already accepted. Read the action and
   `GET /api/follow-through/board?project_id={p}` and verify the exact ID is
   overdue before opening Review.
3. `POST /api/projects/{p}/reviews`, `{}`, runs the production collector and
   freezes a review. Capture its returned review/proposal IDs; read
   `GET /api/projects/{p}/delta` and
   `GET /api/projects/{p}/reviews/{review_id}`. Find the proposal whose evidence
   names `action_item:{action_id}`. The real FollowThrough adapter emits
   `followthrough.overdue`, which produces `risk_attention`; never insert that
   observation or use the unit review rig's `_NoOpCollector`.
4. Return to Prep, open its linked Project, press its pending Review lead and
   inspect that captured evidence/proposal. Decide one captured proposal with
   the existing UI. For `accept`, the genuine endpoint is
   `POST /api/projects/{p}/reviews/{review}/proposals/{proposal}/decide`,
   `{verb:"accept", command_id:<unique command>}`. Read the frozen review plus
   project items and verify that proposal's actual decision/result. Review
   acceptance is a separate `POST .../reviews/{review}/accept`; do not imply
   it happened merely because an individual proposal was decided.

If no proposal is produced, record blocked with the collector/source result;
do not manufacture a positive pending count. Leave/return must retain the same
project and show the actual pending/decided state. A zero/unavailable review
pose must not present invented work as the head action.

## D: real Thread task creation and saved material

The shortest provider-free success loop needs **no model turn**:

1. `POST /api/threads`, `{title:"Platform migration tasks"}`; capture `id`.
   `PUT /api/authority/control-mode`, `{control_mode:"yolo"}`, applies only to
   this isolated hub. Record/read the authority policy; this is a declared
   local-tool fixture posture, not the owner's setting.
2. Open `thread:{id}`, type `/todo Send the platform plan`, and press the
   actual composer Send/Enter. Capture `POST /api/threads/{id}/todo`,
   `{text:"Send the platform plan"}`. The production route reaches
   `ThreadService.todo_from_thread` → `ThreadToolExecutor` → in-process MCP
   `door.add_item` (`tests/unit/test_thread_todo.py`; `_thread_factory.py`).
3. Read `GET /api/threads/{id}` and the isolated DB: exactly one new
   `action_items` row with that task, `source_type='thread'`, and
   `source_ref='thread:{id}'` for this empty Thread; no meeting ID. Read the
   returned `receipt_id`, system `tool_call` part and tool result. Open the
   produced task through its canonical ID and return to the same Thread.

For pending/newer-draft custody, gate the real `/todo` response as above; verify
one durable task while later B typing survives A's accepted response. A browser
HTTP refusal before dispatch must preserve A and create no task. Switch to a
second captured Thread and back/remount to prove failure/words remain owned by
the first. Empty `/todo` must create nothing. A transport disconnect after
dispatch proves an **unknown outcome**; inspect task/receipt before any retry.
There is no endpoint idempotency key: do not claim automatic replay is safe.
Safe-mode tool approval/denial is a distinct held-executor walk, not necessary
to this bounded input-custody case.

To add a provider-free **saved reading result**, import a declared transcript
through `POST /api/threads/import` with
`{threads:[{title:"Recorded migration answer",created_at:<fixed ISO>,messages:[{role:"user",text:"Summarize the migration"},{role:"assistant",text:<multiline recorded answer>}]}]}`.
Capture the resulting thread ID from `imported` and its assistant message ID
from the real Thread GET. Press its existing Keep as note/artifact. Genuine
`POST /api/threads/{id}/keep` accepts `{message_id:<captured>,as:"artifact"}`;
read `/api/artifacts/{returned artifact_id}` and verify exact Markdown and
`sources[].source_ref='thread:{thread_id}/{message_id}'`. Close/reopen that
qualified saved ref. This proves import → reading → Keep → durable source;
the imported answer is recorded material, not a newly completed model turn.

For Ask, preserve the already healed transmission/Keep/citation chain below.
The new bounded unavailable-context pose can use a real `POST /api/projects`
source, then fault the browser's `GET /api/projects` once before opening Ask.
Verify unavailable is distinct from empty, Retry makes the real project
selectable and selection/input survive return. This invokes no model. An
end-to-end newly generated Ask answer requires an explicitly declared provider
replay or real provider and remains outside this provider-free preparation;
calling `/api/ask/keep` with invented output is not proof of a completed Ask.

## Ambient and Settings: reachable recovery, separate authorities

**Do not stage the dormant Ambient Approve/Decline compatibility branch.**
Current non-learning runtime frames, including `actuator_proposed`, refresh
durable projections; only learning events enqueue the local cards. Source
worker/root corrected this reachability during preparation. Do not inject a
local card or browser event to invent an owner journey.

If new Ambient proof is needed, use the existing durable projection path:
while the browser is connected, call
`POST /api/meetings/{B4 meeting}/aftercare/file-issue`,
`{action_item_id:<accepted B4 action>,repo:"walk/never-execute"}`. This real
producer records a **meeting actuator proposal** and emits `actuator_proposed`
(`MeetingAftercareService.file_issue`). Capture its `proposal.id`; read
`GET /api/meetings/{m}/proposals` and `GET /api/desk/projections`, locating the
actual source identity. If no reachable projection appears, record blocked;
do not fabricate one. Inspect its real Review/source opener, then return to
the exact entity. Durable projection Dismiss/refusal already has exact-row
custody proof; carry that forward rather than repairing it again.
Actuator, follow-through bridge and frozen Project Review proposal IDs are
different authorities. Approval is not execution; no connector is run here.

For Settings Other devices, use genuine `GET /api/settings/remote` from the
isolated hub. Fault that GET once, open the face, verify a read failure and
Retry, lift the fault and verify actual enabled/bind/credential values return.
Then fault `PUT /api/settings/remote` once while toggling enabled; verify the
stored GET value stays unchanged and the failed subject remains identifiable.
A successful reload is a read recovery, not a retried or accepted write.
Root settles the label/Retry behavior before build. Avoid issuing credentials
unless that specific pose is needed; real credentials are minted by
`POST /api/settings/remote/credentials` and their one-time tokens must stay out
of artifacts. Existing hub-recorded wire source:
`tests/integration/test_remote_settings_wire.py`.

## Carry forward; keep unknown

Preserve the healed chains recorded in
`docs/internal/BRIEF-REFERENCE-OPEN-2026-10-16/PLAN-AUDIT-SYSTEM.md:17`:
#1215 Ask transmission/Keep lineage and Thread reply/load recovery; #1216
Workbench Close/refusal/reopen, ordered drafts and exact Add/Coder recovery;
#1217–1218 Search focus/meeting identity, Calendar draft/Retry ownership,
Thread replay/Rails native controls, Ask grounding and Settings preference
recovery. These are carried historical evidence, not checks executed here.
The original Ask/Thread release record is
`docs/internal/THREAD-ASK-REFINEMENT-2026-10-15/README.md:77` and its Keep/return
sections; the system audit above links the matching release/status records.

Also preserve `case.delight.prep.draft` and `case.delight.prep.refusal` in
`atlas-delight.json`: person-keyed agenda survives reload, and the recorder-free
hub names its refusal without clearing words. Retain first-delivery exact
held-source/review-state, document grammar and return-context checks. Do not
reopen those repairs just to populate the next walk.

All procedures above still need execution on the implementation's build.
Native recording, microphone/keys, real calendar/provider/connector behavior,
new model/agent completion and owner visual acceptance remain unknown. A DB
producer, recorded transcript or declared browser fault does not establish
those capabilities.
