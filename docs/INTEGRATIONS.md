# Integrations and connectors

Source audit at `675401a857b85336d4acaa8c65383dfc9636e4c8`. This is an
implementation inventory. A manifest, route or test assertion does not prove a
provider credential, public release or owner use.

## Connector model

An activity connector declares a validated `ConnectorManifest` and may
implement `Discover`, `Preview`, `Enrich`, `Clear`, or `Snapshot`
(`holdspeak/connector_sdk.py::ConnectorManifest` and protocols, lines 97-190,
713-779). The registry loads first-party packs from
`holdspeak/connector_packs/__init__.py::ALL_PACKS` and optional Python files
from `~/.holdspeak/connector_packs/` through
`holdspeak/connector_pack_loader.py::build_registry` (line 279). User packs
run in-process with user permissions; this is a trust boundary, not a sandbox.
Duplicate first-party ids, missing manifests and import/validation errors are
reported as discovery errors.

The lifecycle is manifest → dry-run preview → enabled enrichment → scoped
clear. `holdspeak/activity_connector_preview.py::dry_run` returns planned
commands, proposed annotations/candidates, warnings and permission notes; each
list has a cap of 100 and dry-run must not mutate the database. The served
routes are `GET /api/activity/enrichment/connectors`, `PUT
/api/activity/enrichment/connectors/{connector_id}`, `GET
/api/activity/enrichment/connectors/{connector_id}/dry-run`, `GET
/api/activity/enrichment/connectors/{connector_id}/runs`, and scoped
annotations/candidates routes. See `web.routes.activity.enrichment` in
[`api-surface.json`](api-surface.json).

| Connector | Manifest and source | Read/write boundary | Current evidence status |
|---|---|---|---|
| Firefox companion | `holdspeak/connector_packs/firefox_ext.py::MANIFEST`, `CAPTURED_FIELDS` | Loopback event accepts URL, title, visited time and tab/window ids; rejects private browsing, page bodies, cookies, headers, form data and non-HTTP(S) URLs | `experimental`; temporary add-on, no store distribution |
| GitHub CLI | `github_cli.MANIFEST`, `::is_command_allowed` | Local `gh`; `pr view`, `pr list`, `issue view`, `run list` only; writes such as merge/close/auth are rejected | `experimental`; `gh` and auth not verified |
| Jira CLI | `jira_cli.MANIFEST`, `::is_command_allowed` | Local `jira`; `issue view` and `issue list` only; no create/assign/transition/auth login | `experimental`; CLI/auth not verified |
| Atlassian CLI Jira | `acli_jira.MANIFEST`, `::is_command_allowed` | Local `acli jira`; auth status/switch, project list/view, workitem search/view | `experimental`; read-only command pack |
| Atlassian CLI Confluence | `acli_confluence.MANIFEST`, `::is_command_allowed` | Local `acli confluence`; auth status/switch, space list/view, page view, blog list/view; no page search or writes | `experimental`; known-ID/page and blog limitations are explicit |
| Calendar candidates | `calendar_activity.MANIFEST`, `::run` | Reads local activity rows for Google Calendar, Outlook, Meet and Teams domains; writes candidate rows; no CLI/network | `experimental`; deterministic local derivation |
| Meeting context | `meeting_context.MANIFEST`, `::run` | Reads upstream GitHub/Jira annotations and calendar candidates; writes one per-project briefing annotation, updating in place | `experimental`; pipeline freshness 600 seconds |

`holdspeak/activity_connectors.py::reload_registry` exposes first-party versus
user source labels. The SDK validator requires a non-empty id, known kind and
capabilities, a CLI name for `cli_enrichment`, and a network permission when
`requires_network` is true. `PermissionGate` enforces `shell:exec`,
`network:outbound`, `loopback:http`, and `fs:read` before the operation
(`holdspeak/connector_runtime.py::PermissionGate`, lines 115-245).

The focused assertions in `tests/unit/test_connector_sdk.py` cover manifest
validation and closed protocols; `tests/unit/test_connector_runtime.py` covers
permission refusals; `tests/unit/test_connector_pack_loader.py` covers user
pack discovery, collisions and structured errors; and
`tests/unit/test_connector_fixture_harness.py` checks dry-run non-mutation.
The fixture records under `tests/fixtures/connectors/` cover GitHub, Jira and
calendar happy/empty paths. They were inspected and not run here.

## Provider and activity routes

The broader provider layer has concrete served routes, with credentials held by
the host configuration rather than payloads:

| Provider/capability | Served routes and source module | Boundary |
|---|---|---|
| calendar events/sources | `GET /api/calendar/sources`, `GET /api/calendar/events`, `POST /api/calendar/events/{event_id}/link`, `POST /api/calendar/snapshot`, `POST /api/calendar/snapshot/confirm` (`web.routes.calendar_sources`, `calendar_events`, `calendar_snapshot`) | ICS/configured calendar reads and local event links; snapshot is a model-backed review path |
| GitHub project connection | `GET /api/providers`, `GET /api/providers/github/connection`, `POST /api/providers/github/connection/recheck`, `GET /api/providers/github/discover`, `POST /api/providers/github/validate-repo` | configured adapter status and bounded discovery; no token in projections |
| Jira connection/discovery | `GET /api/providers/jira/connections`, `POST /api/providers/jira/connections`, `POST /api/providers/jira/connections/{ref}/recheck`, `GET /api/providers/jira/discover`, `POST /api/providers/jira/search`, `POST /api/providers/jira/validate-scope` | connection uses site+email metadata; credentials are not stored by the `acli` pack |
| Confluence discovery | `GET /api/providers/confluence/connections`, `POST /api/providers/confluence/connections/{ref}/recheck`, `GET /api/providers/confluence/discover`, `POST /api/providers/confluence/validate` | read-only spaces/pages/blogs through configured adapter |
| People and calendar links | `GET /api/people/relationships`, `POST /api/people/relationships`, `POST /api/people/resolve`, `GET /api/people/readiness`, `POST /api/people/relationships/{relationship_id}/calendar-links`, `DELETE /api/people/relationships/{relationship_id}/calendar-links` | protected People boundary; People content is sensitive and not placed on cloud routes by ThreadService |
| project sources and watches | `GET /api/projects/{project_id}/resources`, `PUT /api/projects/{project_id}/resources/{resource_ref:path}`, `DELETE /api/projects/{project_id}/resources/{resource_ref:path}`, `GET /api/projects/{project_id}/watches`, `GET /api/activity/project-rules`, `POST /api/activity/project-rules/preview` | source references, snapshots, and watch proposals; external action remains separate |
| Slack/companion delivery | `POST /api/desk/actuators/slack/propose`, `POST /api/desk/actuators/slack/{proposal_id}/decision` | configured webhook; preview and approval are distinct from send |

The route count or a route name is not a semantic contract. Read the handler,
provider and receipt path before adding a new capability. Several provider
routes have no focused assertion in this bounded lane; those are explicit
unknowns in the metadata shard.

## Actuators

Actuators turn a reviewed artifact or draft into a proposed external effect.
The generic proposal shape is `holdspeak/plugins/actuators.py::ActuatorProposal`
(lines 41-84). `ActuatorProposalService._propose` validates text, destination
configuration, source identity and an idempotency key, records a proposal, and
then applies the lifecycle (`holdspeak/services/actuator_service.py`, lines
50-100). The concrete desk routes are:

| Effect | Preview/proposal | Decision |
|---|---|---|
| GitHub issue | `POST /api/desk/actuators/github/propose` | `POST /api/desk/actuators/github/{proposal_id}/decision` |
| Slack message | `POST /api/desk/actuators/slack/propose` | `POST /api/desk/actuators/slack/{proposal_id}/decision` |
| configured webhook | `POST /api/desk/actuators/webhook/propose` | `POST /api/desk/actuators/webhook/{proposal_id}/decision` |
| configured status | `GET /api/desk/actuators/status` | reports booleans only; never URL/secret material |

`ActuatorExecutor.execute` requires `approved`, checks the master and
allow-list policy, recomputes the authority binding immediately before egress,
consumes a scoped grant atomically, invokes the injected connector, and writes
a terminal receipt. A connector exception produces `failed` with audit, not a
green result (`holdspeak/plugins/actuator_executor.py::ActuatorExecutor.execute`,
lines 91-232). The statuses are proposed, approved, rejected/failed and
executed; the stored payload is the sole execution input.

GitHub issue creation is a separate opt-in write connector
(`holdspeak/plugins/builtin/github_issue_actuator.py::GithubIssueActuator`);
GitHub PR comment/status are separate connector builders. Webhook delivery
enforces host allow-listing in `WebhookPostActuator`. The unit assertions in
`tests/unit/test_actuator_executor.py`, `test_github_issue_actuator.py`,
`test_github_pr_actuator.py`, and `test_webhook_post_actuator.py` cover
approval, grants, authority mismatch, no-egress refusal, audit and connector
failure. Integration assertions in
`tests/integration/test_web_companion_github.py`, `_slack.py`, and `_webhook.py`
cover proposal/deduplication/approval/Yolo, target scoping and secret
redaction. None were run here.

## Other capabilities found

Calendar, Jira, Confluence, GitHub, People, project resources, Slack,
companion webhooks, Firefox activity, and the deterministic Meeting context
pipeline are source-present. No `gitlab` or `reaches` connector module or
served provider route was found in the bounded source inventory. That is an
inventory limit, not proof that no future adapter may exist. No connector
marketplace, remote package distribution or arbitrary provider call is part of
the current manifest contract.
