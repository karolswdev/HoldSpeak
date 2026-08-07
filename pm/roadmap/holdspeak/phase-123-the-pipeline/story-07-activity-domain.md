# HS-123-07 — Activity domain

- **Project:** holdspeak
- **Phase:** 123
- **Status:** backlog
- **Depends on:** HS-123-01
- **Unblocks:** HS-123-12
- **Owner:** unassigned

## The thesis (the bar)

Activity is the largest remaining route-owned domain. Its ledger, project-rule,
meeting-candidate, enrichment, deferred-plugin-job, and nudge lifecycles are
currently split across forty audited operations. That leaves a second adapter
unable to use the same history, rules, durable run records, and lifecycle
invariants without reimplementing HTTP handlers.

When this ships, each lifecycle has a transport-neutral service boundary.
Routes under `holdspeak/web/routes/activity/` remain adapters: they parse
request input, obtain the explicit principal, call one named service method,
and translate `ServiceError` to the existing HTTP response. The services own
the domain helper/repository orchestration and preserve the present response
payloads, ordering, authorization, idempotency, and durable audit state.

## Service contract — match `PrimitiveService` exactly

Add six sibling services:

- `ActivityLedgerService`
- `ActivityRulesService`
- `ActivityMeetingCandidateService`
- `ActivityEnrichmentService`
- `PluginJobService`
- `ActivityNudgeService`

Each service follows the Phase 122 `PrimitiveService` shape exactly:

```python
from ..db.core import Database
from ..principals import Principal

class ActivityLedgerService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def status(self, principal: Principal) -> dict[str, Any]:
        ...
```

That means all six constructors are precisely `__init__(self, db: Database)`;
they retain only `self._db`; every public operation takes `principal: Principal`
as its first operation argument; and they return domain data/ordinary Python
payloads, never `Request`, `APIRouter`, `JSONResponse`, or an HTTP status.
Routes may use the established Phase 122 local factory pattern,
`_svc() -> Service: return Service(get_database())`, but may not dereference
`get_database().activity` or `get_database().plugins` themselves. Service
errors come from HS-123-01 and route adapters alone map them to the current
400/403/404/409/500 shapes.

Move the route-local payload shapers into the owning service (or a
transport-neutral activity support module if shared); do not leave a route
helper that reaches persistence or a domain engine. Repositories remain
unchanged persistence adapters, as they do for `PrimitiveService`.

## Extraction recipes — all 40 audited operations

### `ActivityLedgerService` — `holdspeak/web/routes/activity/ledger.py` (7)

Existing helpers/repositories wrapped: `activity_history.discover_browser_history_sources`,
`activity_history.import_browser_history`, `activity_context.build_activity_context`,
and `db.activity` privacy-settings, domain-rule, checkpoint, and record
operations. `status()` owns the former `_activity_status_payload()` assembly,
including source discovery, checkpoint serialization, and the 5,000-record
count; callers which formerly appended a fresh status must receive the same
payload.

| Source line | Route / current operation | Proposed service method | Complexity / preservation recipe |
| --- | --- | --- | --- |
| 31 | `_activity_status_payload()` used by `GET /api/activity/status` | `status(principal)` | Standard. Read privacy settings, rules, checkpoints, discovered sources, and record count; retain `enabled = source.enabled and settings["enabled"]`. |
| 87 | `GET /api/activity/records` | `list_records(principal, project_id, domain, entity_type, limit)` | Standard. Call `build_activity_context(..., refresh=False)`, then retain normalized domain/entity-type filtering and the complete bundle shape. |
| 112 | `POST /api/activity/refresh` | `refresh(principal)` | Standard. Call `import_browser_history(self._db)`, serialize each import result, then append `status(principal)`. |
| 139 | `PUT /api/activity/settings` | `update_settings(principal, settings)` | Standard. Call `update_activity_privacy_settings(enabled, retention_days)` and return settings plus fresh status. |
| 153 | `POST /api/activity/domains` | `upsert_domain_rule(principal, domain, rule)` | Standard. Delegate to `upsert_activity_domain_rule(domain, action)`; preserve repository `ValueError` as the existing validation failure and return fresh status. |
| 169 | `DELETE /api/activity/domains/{domain}` | `delete_domain_rule(principal, domain)` | Standard. Delegate to `delete_activity_domain_rule(domain)` and return deletion result plus fresh status. |
| 183 | `DELETE /api/activity/records` | `delete_records(principal, domain, project_id)` | Standard. Delegate to `delete_activity_records(domain=..., project_id=...)` and return deletion result plus fresh status. |

### `ActivityRulesService` — `holdspeak/web/routes/activity/rules.py` (6)

Existing helpers/repositories wrapped: `db.activity.list_activity_project_rules`,
`create_activity_project_rule`, `update_activity_project_rule`,
`delete_activity_project_rule`, `preview_activity_project_rule`, and
`apply_activity_project_rules`. The service owns the project-rule and
activity-record serialization presently performed by
`_activity_project_rule_payload` and `_activity_record_payload`; the route may
still determine which Pydantic fields were supplied, then pass an ordinary
`fields` mapping.

| Source line | Route | Proposed service method | Complexity / preservation recipe |
| --- | --- | --- | --- |
| 73 | `GET /api/activity/project-rules` | `list(principal, include_disabled=True)` | Standard. Preserve `include_disabled` and the `{"rules": [...]}` payload. |
| 84 | `POST /api/activity/project-rules` | `create(principal, fields)` | Standard. Preserve defaults: empty required strings, priority `100`, and enabled `True`; repository validation remains domain validation. |
| 108 | `PUT /api/activity/project-rules/{rule_id}` | `update(principal, rule_id, fields)` | Standard. Update only fields identified by `_model_fields_set`; map missing rule to the existing not-found service error. |
| 136 | `DELETE /api/activity/project-rules/{rule_id}` | `delete(principal, rule_id)` | Standard. Preserve the repository boolean deletion payload. |
| 146 | `POST /api/activity/project-rules/preview` | `preview(principal, rule_data, records)` | Standard. Use the existing repository preview with its 50-result bound; preserve count and serialized matches. `records` is the typed/payload input to preserve the audited service signature, not a route-owned DB lookup. |
| 170 | `POST /api/activity/project-rules/apply` | `apply(principal, limit)` | Standard. Delegate to `apply_activity_project_rules(limit=limit)` and preserve `{"updated": count}`. |

### `ActivityMeetingCandidateService` — `holdspeak/web/routes/activity/candidates.py` (6)

Existing helpers/repositories wrapped: `activity_candidates.preview_calendar_meeting_candidates`,
`db.activity` candidate CRUD/list/start methods, `_parse_iso_datetime`, and
the candidate payload serializer. The service owns input normalization and
candidate payloads. The route owns only HTTP parsing and WebContext callback
adaptation; no callback, `Request`, broadcast implementation, or FastAPI type
may enter the service constructor.

| Source line | Route | Proposed service method | Complexity / preservation recipe |
| --- | --- | --- | --- |
| 64 | `GET /api/activity/meeting-candidates/preview` | `preview(principal, limit)` | Standard. Load the bounded record set and call `preview_calendar_meeting_candidates`; retain count and candidate payloads. |
| 85 | `GET /api/activity/meeting-candidates` | `list(principal, source_connector_id, status, limit)` | Standard. Preserve repository validation, filters, ordering, count, and candidate serialization. |
| 109 | `POST /api/activity/meeting-candidates` | `create(principal, fields)` | Standard. Preserve default connector/status/confidence and ISO datetime parsing before repository creation. |
| 134 | `PUT /api/activity/meeting-candidates/{candidate_id}/status` | `update_status(principal, candidate_id, status)` | Standard. Preserve repository status validation and the missing-candidate result. |
| 158 | `POST /api/activity/meeting-candidates/{candidate_id}/start` | `start(principal, candidate_id)` | **Complex.** Service owns candidate lookup and final durable `mark_activity_meeting_candidate_started` transition. It must preserve the order: reject missing candidate; invoke the already-established meeting-start capability; best-effort apply nonblank candidate title; extract the meeting id; mark candidate started only after start succeeds; return meeting data plus a title-update warning when appropriate. Keep the existing 501 capability absence, callback invocation, and `meeting_started` broadcast at the adapter/capability seam; pass their transport-neutral result into the service rather than leaking `WebContext` into it. |
| 217 | `DELETE /api/activity/meeting-candidates` | `delete(principal, source_connector_id, status)` | Standard. Delegate to `delete_activity_meeting_candidates` and retain validation and deletion count. |

### `ActivityEnrichmentService` — `holdspeak/web/routes/activity/enrichment.py` (14)

Existing helpers/repositories wrapped: `activity_connectors.enrichment_descriptors`,
`KNOWN_CONNECTOR_IDS`, `get_descriptor`; `activity_connector_preview.dry_run`
and `MAX_LIMIT`; `activity_extension.ingest_extension_events`; connector-pack
`PermissionGate`; `connector_runtime.PipelineRunner`; `activity_github` and
`activity_jira` preview/run helpers; `connector_sdk.resolve_setting`; CLI
status helpers; and `db.activity` connector, annotation, candidate, record,
and run repositories. The service owns connector serialization and all bounds,
manifest/capability checks, default setting resolution, and run-record-facing
payloads.

| Source line | Route | Proposed service method | Complexity / preservation recipe |
| --- | --- | --- | --- |
| 52 | `GET /api/activity/enrichment/connectors` | `list_connectors(principal)` | Standard. Enumerate descriptors, materialize missing connector state, attach descriptor metadata and per-connector CLI status, and retain top-level GitHub/Jira CLI-status compatibility keys. |
| 113 | `PUT /api/activity/enrichment/connectors/{connector_id}` | `update_connector(principal, connector_id, settings)` | Standard. Verify known connector and manifest-declared setting keys before upsert; retain enabled/settings semantics and unknown-key validation message. |
| 152 | `POST /api/activity/extension/events` | `ingest_extension_events(principal, events)` | Standard but security-sensitive. Preserve `firefox_ext` `loopback:http` permission-gate enforcement before `ingest_extension_events(self._db, events)` and retain rejected-event behavior. |
| 172 | `GET /api/activity/enrichment/connectors/{connector_id}/dry-run` | `dry_run(principal, connector_id, limit)` | Standard. Normalize to `MAX_LIMIT`, call connector dry-run, and map unknown connector without HTTP types. |
| 205 | `DELETE /api/activity/enrichment/connectors/{connector_id}/annotations` | `clear_annotations(principal, connector_id)` | Standard. Require a known annotations-capable descriptor, delete annotations **and matching connector runs**, and return both counts. |
| 244 | `DELETE /api/activity/enrichment/connectors/{connector_id}/candidates` | `clear_candidates(principal, connector_id)` | Standard. Require a known candidates-capable descriptor, delete candidates **and matching connector runs**, and return both counts. |
| 274 | `GET /api/activity/annotations` | `list_annotations(principal, source_connector_id, annotation_type, activity_record_id, limit)` | Standard. Clamp limit to 1–500 and preserve annotation serialization/order. |
| 321 | `GET /api/activity/briefing` | `briefing(principal)` | Standard. Fetch the newest `meeting_context_briefing` annotation and newest `meeting_context` run; preserve nullable `briefing` and `last_run`. |
| 384 | `POST /api/activity/enrichment/pipelines/{pipeline_id}/run` | `run_pipeline(principal, pipeline_id)` | **Complex.** Validate descriptor existence and `kind == "pipeline"`, construct `PipelineRunner(self._db, principal=principal)`, run it, preserve `UnknownPipelineError`/`NotAPipelineError`, and return `PipelineRunResult.to_payload()`. The service owns pipeline execution, step ordering/skips/failures, permissions, and durable run records. |
| 419 | `GET /api/activity/enrichment/connectors/{connector_id}/runs` | `list_runs(principal, connector_id, limit)` | Standard. Validate descriptor first, clamp limit to 1–200, then serialize run history. |
| 438 | `GET /api/activity/enrichment/github/preview` | `preview_github(principal, limit)` | Standard. Materialize GitHub connector state, load bounded PR and issue context as today, call `preview_github_cli_enrichment`, and retain connector payload. |
| 462 | `POST /api/activity/enrichment/github/run` | `run_github(principal, settings)` | **Complex.** Materialize and require enabled GitHub connector; resolve request overrides or manifest defaults for limit/timeout/max-bytes; preserve all clamps; collect PR and issue records; call `run_github_cli_enrichment(..., principal=principal)`; reload connector state; return results and durable run outcome. |
| 538 | `GET /api/activity/enrichment/jira/preview` | `preview_jira(principal, limit)` | Standard. Materialize Jira connector state, load bounded ticket records, call `preview_jira_cli_enrichment`, and retain connector payload. |
| 562 | `POST /api/activity/enrichment/jira/run` | `run_jira(principal, settings)` | **Complex.** Mirror the GitHub run contract for Jira: enabled check, manifest/request setting resolution and clamps, ticket selection, `run_jira_cli_enrichment(..., principal=principal)`, connector reload, results, and durable run outcome. |

### `PluginJobService` — `holdspeak/web/routes/activity/plugin_jobs.py` (4)

Existing helpers/repositories wrapped: `db.plugins.list_plugin_run_jobs`,
`get_plugin_run_job_summary`, `get_plugin_run_job`, `retry_plugin_run_job`, and
`complete_plugin_run_job`. The service owns job/summary serialization,
`datetime.now()` retry scheduling, existence checks, and the invariant that a
running job cannot be retried or cancelled.

| Source line | Route | Proposed service method | Complexity / preservation recipe |
| --- | --- | --- | --- |
| 36 | `GET /api/plugin-jobs` | `list(principal, status, meeting_id, limit)` | Standard. Preserve queue filters, retry-scheduled computation, and full job fields. |
| 83 | `GET /api/plugin-jobs/summary` | `summary(principal)` | Standard. Preserve all aggregate fields and ISO timestamp/null behavior. |
| 143 | `POST /api/plugin-jobs/{job_id}/retry-now` | `retry(principal, job_id)` | Standard lifecycle transition. Reject absent/running jobs, schedule `retry_plugin_run_job` immediately with the existing manual-retry reason, then return the refreshed job. |
| 190 | `POST /api/plugin-jobs/{job_id}/cancel` | `cancel(principal, job_id)` | Standard lifecycle transition. Reject absent/running jobs, then call `complete_plugin_run_job` and retain success payload. |

`POST /api/plugin-jobs/process` is deliberately not one of the 40 audited
extractions: it is a WebContext runtime-control callback, not a direct domain
handler in this story's audit. Do not silently fold it into `PluginJobService`
unless its callback capability is separately made transport-neutral.

### `ActivityNudgeService` — `holdspeak/web/routes/activity/nudges.py` (3)

Existing helpers/repositories wrapped: `activity_nudges.compute_nudges`,
`db.activity.get_activity_privacy_settings`, `dismiss_nudge`, and
`get_activity_record`; plus the domain operation
`dictation_selection.set_selected_record`. The service owns nudge payloads,
identifier/record validation, and the record-exists-before-selection invariant.

| Source line | Route | Proposed service method | Complexity / preservation recipe |
| --- | --- | --- | --- |
| 45 | `GET /api/activity/nudges` | `list(principal, project_id, limit)` | Standard. Call `compute_nudges(self._db, project_id=..., limit=...)`, retain citations/order, and return `activity_enabled` from privacy settings. |
| 67 | `POST /api/activity/nudges/{nudge_id}/dismiss` | `dismiss(principal, nudge_id)` | Standard. Strip and require an id before `dismiss_nudge`; retain the returned clean id. |
| 90 | `POST /api/activity/nudges/select` | `select(principal, record_id)` | Standard but stateful. Parse/validate integer record id, require a real activity record, then call `set_selected_record` so the one-shot dictation context contract remains intact. |

`POST /api/activity/nudges/select/clear` is not among the audited 40 direct
DB/domain-handler extractions. It remains a small runtime-state adapter around
`dictation_selection.clear_selected_record` unless a later story gives that
state a service owner.

## Scope

- Add the six services at the paths below, using the constructor, explicit
  principal, transport-neutral return, and service-error conventions above.
- Implement every one of the 40 recipes above; do not substitute a single
  god-service or leave a route-owned orchestration branch behind.
- Preserve authorization, privacy gating, record/rule ordering, connector
  manifest validation, plugin-job state transitions, candidate deduplication,
  idempotency, pipeline durable records, and response/error compatibility.
- Move route-local activity payload shapers and persistence/domain work behind
  the named services. Route handlers only adapt HTTP input/output and the two
  explicitly retained WebContext runtime callbacks.
- Add focused service and affected-route tests, including every complex flow:
  candidate start; pipeline run; GitHub run; Jira run.

## Acceptance criteria

- [ ] All six classes exist, each declares `def __init__(self, db: Database) -> None`,
      stores `self._db`, and every listed public operation takes an explicit
      `principal: Principal`.
- [ ] The 40 table rows have exactly one named method owner and the method
      wraps the helpers/repositories named in its section; service modules
      import no `holdspeak.web.routes`, FastAPI, `Request`, `APIRouter`, or
      `JSONResponse`.
- [ ] Activity adapters have no direct activity/plugin repository access. Run:
      ```bash
      rg -n 'get_database\(\)\.(activity|plugins)|\bdb\.(activity|plugins)\.' \
        holdspeak/web/routes/activity/{ledger,rules,candidates,enrichment,plugin_jobs,nudges}.py
      ```
      It returns no matches. The Phase 122 `_svc() -> Service` factory may be
      the only route-level `get_database()` use for these extracted operations.
- [ ] Routes delegate to the six named services. Run:
      ```bash
      rg -n 'Activity(Ledger|Rules|MeetingCandidate|Enrichment|Nudge)Service|PluginJobService' \
        holdspeak/web/routes/activity/{ledger,rules,candidates,enrichment,plugin_jobs,nudges}.py
      ```
      Each of the six service names appears in its owning route module, and no
      audited handler imports the domain helpers listed above.
- [ ] The candidate start seam preserves start → optional title update → durable
      candidate mark → broadcast order, has the current 501/404/400/500
      behavior, and never gives `WebContext` to a service.
- [ ] Pipeline, GitHub, and Jira runs preserve principal propagation, manifest
      setting resolution, bounds, permission/connector checks, idempotency, and
      connector-run persistence. Clear operations still delete paired run rows.
- [ ] Nudge selection still rejects invalid/unknown record ids before setting
      dictation state; extension ingestion still enforces the Firefox loopback
      permission gate; plugin jobs still reject retry/cancel while running.
- [ ] Focused tests cover all six services and the complex/error paths, and
      `uv run pytest -q` passes.

## Files in scope

- New: `holdspeak/services/activity_ledger_service.py`
- New: `holdspeak/services/activity_rules_service.py`
- New: `holdspeak/services/activity_meeting_candidate_service.py`
- New: `holdspeak/services/activity_enrichment_service.py`
- New: `holdspeak/services/plugin_job_service.py`
- New: `holdspeak/services/activity_nudge_service.py`
- `holdspeak/web/routes/activity/ledger.py`
- `holdspeak/web/routes/activity/rules.py`
- `holdspeak/web/routes/activity/candidates.py`
- `holdspeak/web/routes/activity/enrichment.py`
- `holdspeak/web/routes/activity/plugin_jobs.py`
- `holdspeak/web/routes/activity/nudges.py`
- Related activity, connector, plugin-job, route, and service tests
