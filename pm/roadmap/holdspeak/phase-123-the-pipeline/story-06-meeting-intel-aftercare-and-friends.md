# HS-123-06 — Meeting intel, aftercare, and friends

- **Project:** holdspeak
- **Phase:** 123
- **Status:** done
- **Depends on:** HS-123-01
- **Unblocks:** HS-123-12
- **Owner:** unassigned

## The thesis (the bar)

HS-122-04 established `MeetingService` for capture lifecycle and core meeting
queries. The remaining meeting routes still own intelligence jobs, recovery,
aftercare, insights, speakers, action-item review/editing, and conflict
recovery. They alter the same durable meeting record and must use a
principal-aware service boundary rather than becoming a second application
layer inside route modules.

When this ships, `MeetingService` is extended and, only where cohesion requires
it, focused collaborators such as `MeetingIntelService` or
`MeetingAftercareService` are injected behind it. Every listed route is a thin
adapter.

## Phase 122 pattern to follow

Follow HS-122-04 exactly, reinforced by HS-123-01:

- Existing `MeetingService` construction is the starting seam. Construct
  extended/focused services once with database and narrow domain collaborators;
  never import or accept `WebContext`, FastAPI types, or route helpers.
- Each public method begins with `Principal`. A service returns domain data or
  shared service errors, and the adapter preserves the existing HTTP status and
  response shape.
- Put authorization, meeting lookup, state transitions, persistence,
  idempotency/retry decisions, provenance, and external side effects in the
  service. Routes only parse transport input, invoke one service operation, map
  errors, and serialize.
- Preserve current job/recovery identifiers, state values, ordering, and named
  failure behavior. This story must not make a retry silently create a second
  job or a recovery path lose provenance.

## Required service ownership

Extend `MeetingService` for meeting facets, capture recovery, sync-conflict
read/resolve, speaker management, insight reads, action-item operations, and
other coherent meeting-record operations. A focused service is preferred for
intel queue processing/recovery and aftercare/external delivery if doing so
keeps collaborators narrow. Regardless of class placement, the named service
methods in the table are required and all take `Principal`.

For all retry/recovery/process operations, make the idempotency key/state guard
an explicit service responsibility. Tests must cover duplicate calls, already
completed/skipped recovery, missing job/meeting, authorization denial, and the
existing structured failure response.

## Audited handler map

### `holdspeak/web/routes/meetings/intel.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 146 | `api_list_intel_jobs` — `GET /api/intel/jobs` | `MeetingIntelService.list_jobs(principal, filters)` | Medium — preserve queue filtering/order and job visibility. |
| 213 | `api_intel_queue_summary` — `GET /api/intel/summary` | `MeetingIntelService.queue_summary(principal)` | Medium — retain aggregate state/count semantics. |
| 237 | `api_process_intel_jobs` — `POST /api/intel/process` | `MeetingIntelService.process_jobs(principal, payload)` | **Complex** — queue selection, processing, durable job transitions, inference/side effects, and receipts. |
| 301 | `api_retry_intel_job` — `POST /api/intel/retry/{meeting_id}` | `MeetingIntelService.retry_job(principal, meeting_id)` | High — retry guard/idempotency and named failure preservation. |
| 344 | `api_get_meeting_intel_recovery` — `GET /api/meetings/{meeting_id}/intel-recovery` | `MeetingIntelService.get_recovery(principal, meeting_id)` | Medium — retain recovery projection and access checks. |
| 357 | `api_retry_meeting_intel_recovery` — `POST /api/meetings/{meeting_id}/intel-recovery/retry` | `MeetingIntelService.retry_recovery(principal, meeting_id, payload)` | High — state guard, idempotency, and requeue semantics. |
| 390 | `api_skip_meeting_intel_recovery` — `POST /api/meetings/{meeting_id}/intel-recovery/skip` | `MeetingIntelService.skip_recovery(principal, meeting_id, payload)` | High — durable skip/provenance and terminal-state guard. |

### `holdspeak/web/routes/meetings/aftercare.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 39 | `api_get_meeting_aftercare` — `GET /api/meetings/{meeting_id}/aftercare` | `MeetingAftercareService.get_aftercare(principal, meeting_id)` | Medium — preserve assembled aftercare projection. |
| 68 | `api_get_meeting_followup_draft` — `GET /api/meetings/{meeting_id}/followup-draft` | `MeetingAftercareService.get_followup_draft(principal, meeting_id)` | Medium — retain draft provenance/status. |
| 102 | `api_get_meeting_proposals` — `GET /api/meetings/{meeting_id}/proposals` | `MeetingAftercareService.list_proposals(principal, meeting_id)` | Medium — retain visibility/order/lifecycle data. |
| 129 | `api_decide_meeting_proposal` — `POST /api/meetings/{meeting_id}/proposals/{proposal_id}/decision` | `MeetingAftercareService.decide_proposal(principal, meeting_id, proposal_id, decision)` | High — authorization, lifecycle guard, receipt, and provenance. |
| 164 | `api_aftercare_file_issue` — `POST /api/meetings/{meeting_id}/aftercare/file-issue` | `MeetingAftercareService.file_issue(principal, meeting_id, payload)` | **Complex** — external issue action must retain approval/proposal/receipt behavior and idempotency. |
| 261 | `api_export_meeting_to_slack` — `POST /api/meetings/{meeting_id}/export/slack` | `MeetingAftercareService.export_slack(principal, meeting_id, payload)` | **Complex** — external delivery, authorization, target validation, receipt, and failure handling. |

### `holdspeak/web/routes/meetings/insights.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 21 | `api_get_meeting_intent_timeline` — `GET /api/meetings/{meeting_id}/intent-timeline` | `MeetingService.get_intent_timeline(principal, meeting_id)` | Medium — preserve event ordering and redaction. |
| 72 | `api_get_meeting_plugin_runs` — `GET /api/meetings/{meeting_id}/plugin-runs` | `MeetingService.list_plugin_runs(principal, meeting_id)` | Medium — preserve run/provenance projection. |
| 118 | `api_get_meeting_artifacts` — `GET /api/meetings/{meeting_id}/artifacts` | `MeetingService.list_artifacts(principal, meeting_id)` | Medium — preserve artifact ordering/visibility. |

### `holdspeak/web/routes/meetings/speakers.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 23 | `api_list_speakers` — `GET /api/speakers` | `MeetingService.list_speakers(principal, filters)` | Medium — visibility and stable ordering. |
| 53 | `api_get_speaker` — `GET /api/speakers/{speaker_id}` | `MeetingService.get_speaker(principal, speaker_id)` | Medium — not-found/access semantics. |
| 91 | `api_update_speaker` — `PATCH /api/speakers/{speaker_id}` | `MeetingService.update_speaker(principal, speaker_id, patch)` | High — patch validation and speaker identity/meeting provenance. |

### `holdspeak/web/routes/meetings/action_items.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 30 | `api_update_action_item` — `PATCH /api/action-items/{item_id}` | `MeetingService.update_action_item(principal, item_id, patch)` | High — lifecycle/ownership and patch validation. |
| 64 | `api_update_action_item_review` — `PATCH /api/action-items/{item_id}/review` | `MeetingService.review_action_item(principal, item_id, patch)` | High — preserve review transition rules. |
| 96 | `api_edit_action_item` — `PATCH /api/action-items/{item_id}/edit` | `MeetingService.edit_action_item(principal, item_id, patch)` | High — distinguish edit semantics from lifecycle update. |
| 133 | `api_list_all_action_items` — `GET /api/all-action-items` | `MeetingService.list_all_action_items(principal, filters)` | Medium — retain cross-meeting filter/order/visibility. |
| 174 | `api_update_global_action_item` — `PATCH /api/all-action-items/{item_id}` | `MeetingService.update_action_item(principal, item_id, patch)` | High — same canonical mutation path as meeting-scoped update. |
| 234 | `api_review_global_action_item` — `PATCH /api/all-action-items/{item_id}/review` | `MeetingService.review_action_item(principal, item_id, patch)` | High — same canonical review transition. |
| 292 | `api_edit_global_action_item` — `PATCH /api/all-action-items/{item_id}/edit` | `MeetingService.edit_action_item(principal, item_id, patch)` | High — same canonical edit path. |

### `holdspeak/web/routes/meetings/crud.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 88 | `api_meeting_facets` — `GET /api/meetings/facets` | `MeetingService.facets(principal, filters)` | Medium — retain available-filter/count semantics. |
| 132 | `api_recover_meeting_capture` — `POST /api/meetings/{meeting_id}/capture/recover` | `MeetingService.recover_capture(principal, meeting_id, payload)` | **Complex** — recovery state machine and idempotency. |
| 148 | `api_meeting_sync_conflicts` — `GET /api/meetings/{meeting_id}/sync-conflicts` | `MeetingService.list_sync_conflicts(principal, meeting_id)` | Medium — preserve conflict visibility/order. |
| 158 | `api_resolve_meeting_sync_conflict` — `POST /api/meetings/{meeting_id}/sync-conflicts/{conflict_id}/resolve` | `MeetingService.resolve_sync_conflict(principal, meeting_id, conflict_id, payload)` | High — validate conflict/current state and preserve resolution provenance. |

The CRUD module also contains HS-122-owned list/get/delete/export handlers.
They must continue to delegate to `MeetingService`; they are not a reason to
create a second service construction path.

## Implementation steps

1. Read all six modules and classify every existing collaborator: meeting
   store, job queue, capture runtime, inference/plugins, proposal/gate service,
   issue/Slack adapter, and sync state. Inject each at a service seam.
2. Extend the existing meeting service for cohesive record operations; create
   focused intel/aftercare services only where external/job collaborators would
   otherwise make it incoherent. Give each a clear constructor and explicit
   principal methods.
3. Move queue/retry/recovery state guards together with their persistence.
   Tests must prove duplicate retry/process and skip/retry terminal-state cases
   do not create illegal transitions.
4. Move external issue/Slack execution with proposal/approval/receipt behavior
   intact. Never have a route call an external adapter after a service merely
   returns a draft.
5. Route action-item aliases through the same canonical service methods so the
   two URL families cannot diverge.
6. Replace handlers with adapter-only code, update composition wiring, and add
   service plus route regression tests for success, denial, not-found/conflict,
   retry/recovery, and external-failure cases.

## Acceptance criteria

- [ ] Every handler in the audited map has named service ownership and an
      explicit principal path.
- [ ] Intel process/retry/recovery/skip and capture recovery retain existing
      idempotency, state guards, durable state, provenance, and named failures.
- [ ] Aftercare proposal decisions, issue filing, and Slack export preserve
      authorization, approval/proposal, external-side-effect, and receipt
      semantics.
- [ ] Speaker, insight, action-item, facets, and conflict operations preserve
      existing authorization, ordering, and payload/status behavior.
- [ ] Meeting route handlers access neither the database nor route-owned domain
      helpers; service modules import no FastAPI, `WebContext`, or routes.
- [ ] Focused meeting route/service regressions and `uv run pytest -q` pass.

## Builder verification

```bash
rg -n "def (list_jobs|queue_summary|process_jobs|retry_job|get_recovery|retry_recovery|skip_recovery|get_aftercare|file_issue|export_slack|recover_capture|resolve_sync_conflict)" holdspeak/services
! rg -n "get_database\(|ctx\.get_database" holdspeak/web/routes/meetings/intel.py holdspeak/web/routes/meetings/aftercare.py holdspeak/web/routes/meetings/insights.py holdspeak/web/routes/meetings/speakers.py holdspeak/web/routes/meetings/action_items.py holdspeak/web/routes/meetings/crud.py
! rg -n "holdspeak\.web\.routes|WebContext|fastapi" holdspeak/services/meeting_service.py holdspeak/services/meeting_intel_service.py holdspeak/services/meeting_aftercare_service.py
uv run pytest -q
```

If focused service filenames differ, run the final import grep against every
new meeting service module.

## Files in scope

- `holdspeak/services/meeting_service.py`
- New focused services under `holdspeak/services/` only where needed, expected
  candidates: `meeting_intel_service.py`, `meeting_aftercare_service.py`
- `holdspeak/web/routes/meetings/intel.py`
- `holdspeak/web/routes/meetings/aftercare.py`
- `holdspeak/web/routes/meetings/insights.py`
- `holdspeak/web/routes/meetings/speakers.py`
- `holdspeak/web/routes/meetings/action_items.py`
- `holdspeak/web/routes/meetings/crud.py`
- Meeting/application composition wiring and related intel, aftercare, insight,
  speaker, action-item, recovery, conflict, route, and service tests
