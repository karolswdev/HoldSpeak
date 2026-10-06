# Integrations and connectors

HoldSpeak reads from other tools through connectors and provider routes. It writes to other tools only through actuators, after you approve. To build a connector, see [Connector development](CONNECTOR_DEVELOPMENT.md). To build an actuator, see [Actuator development](ACTUATOR_DEVELOPMENT.md).

## Connectors

A connector is a pack with a validated `ConnectorManifest` (`holdspeak/connector_sdk.py`). It can implement `Discover`, `Preview`, `Enrich`, `Clear`, or `Snapshot`.

The registry loads the built-in packs from `holdspeak/connector_packs/__init__.py::ALL_PACKS`. It also loads Python files from `~/.holdspeak/connector_packs/` (`holdspeak/connector_pack_loader.py`). A user pack runs in the HoldSpeak process with your permissions. It is not sandboxed. The registry reports duplicate ids, missing manifests, and import errors.

The lifecycle is: manifest, dry run, enabled enrichment, scoped clear. A dry run lists planned commands, proposed annotations and candidates, warnings, and permission notes. Each list holds at most 100 items. A dry run never writes to the database. `PermissionGate` (`holdspeak/connector_runtime.py`) checks `shell:exec`, `network:outbound`, `loopback:http`, and `fs:read` before each operation.

Routes:

- `GET /api/activity/enrichment/connectors`
- `PUT /api/activity/enrichment/connectors/{connector_id}`
- `GET /api/activity/enrichment/connectors/{connector_id}/dry-run`
- `GET /api/activity/enrichment/connectors/{connector_id}/runs`
- `DELETE /api/activity/enrichment/connectors/{connector_id}/annotations` and `/candidates` (scoped clear)

### Built-in connectors

Enable or disable each connector with the `PUT` route above.

| Connector | Module | What it reads |
|---|---|---|
| Firefox companion | `firefox_ext` | Loopback events with URL, title, visit time, and tab and window ids. It rejects private browsing, page bodies, cookies, headers, form data, and non-HTTP(S) URLs. |
| GitHub CLI | `github_cli` | Local `gh`: `pr view`, `pr list`, `issue view`, `run list`. It rejects every other command. |
| Jira CLI | `jira_cli` | Local `jira`: `issue view` and `issue list`. |
| Atlassian CLI Jira | `acli_jira` | Local `acli jira`: auth status and switch, project list and view, work item search and view. |
| Atlassian CLI Confluence | `acli_confluence` | Local `acli confluence`: auth status and switch, space list and view, page view, blog list and view. No page search. |
| Calendar candidates | `calendar_activity` | Local activity rows for Google Calendar, Outlook, Meet, and Teams domains. It writes candidate rows. It uses no CLI and no network. |
| Meeting context | `meeting_context` | GitHub and Jira annotations and calendar candidates. It writes one briefing annotation per Project and updates it in place. |

The command packs allow read commands only. A write such as merge, close, create, or auth login fails the allow-list.

## Provider routes

Credentials stay in host configuration. They never appear in a route payload.

| Capability | Routes |
|---|---|
| Calendar | `GET /api/calendar/sources`, `GET /api/calendar/events`, `POST /api/calendar/events/{event_id}/link`, `POST /api/calendar/snapshot`, `POST /api/calendar/snapshot/confirm` |
| GitHub | `GET /api/providers`, `GET /api/providers/github/connection`, `POST /api/providers/github/connection/recheck`, `GET /api/providers/github/discover`, `POST /api/providers/github/validate-repo` |
| Jira | `GET` and `POST /api/providers/jira/connections`, `POST /api/providers/jira/connections/{ref}/recheck`, `GET /api/providers/jira/discover`, `POST /api/providers/jira/search`, `POST /api/providers/jira/validate-scope` |
| Confluence | `GET /api/providers/confluence/connections`, `POST /api/providers/confluence/connections/{ref}/recheck`, `GET /api/providers/confluence/discover`, `POST /api/providers/confluence/validate` |
| People | See [People integration](PEOPLE_INTEGRATION.md). |
| Project sources and watches | `GET /api/projects/{project_id}/resources`, `PUT` and `DELETE /api/projects/{project_id}/resources/{resource_ref:path}`, `GET /api/projects/{project_id}/watches`, `GET /api/activity/project-rules`, `POST /api/activity/project-rules/preview` |

A Jira connection holds a site and an email. The `acli` packs store no credentials. The full route list is in [`api-surface.json`](api-surface.json).

## Actuators

An actuator turns a reviewed draft into a proposed effect in another tool. `ActuatorProposalService` records the proposal (`holdspeak/services/actuator_service.py`). `ActuatorExecutor.execute` runs it only after approval (`holdspeak/plugins/actuator_executor.py`). The executor:

1. Requires the status `approved`.
2. Checks the master switch and the allow-list.
3. Recomputes the authority binding before egress.
4. Consumes a scoped grant.
5. Calls the connector.
6. Writes a terminal receipt.

A connector error produces `failed` with an audit record. The stored payload is the only input to execution.

| Effect | Propose | Decide |
|---|---|---|
| GitHub issue | `POST /api/desk/actuators/github/propose` | `POST /api/desk/actuators/github/{proposal_id}/decision` |
| Slack message | `POST /api/desk/actuators/slack/propose` | `POST /api/desk/actuators/slack/{proposal_id}/decision` |
| Webhook | `POST /api/desk/actuators/webhook/propose` | `POST /api/desk/actuators/webhook/{proposal_id}/decision` |

`GET /api/desk/actuators/status` reports which destinations are configured as booleans. It never returns a URL or a secret. `WebhookPostActuator` enforces a host allow-list. GitHub issue creation is an opt-in write (`GithubIssueActuator`).

## Not available

HoldSpeak has no GitLab connector, no connector marketplace, and no remote pack download.
