# Integrations and connectors

HoldSpeak reads external activity through connectors and sends prepared work
through saved destinations or approved actuators. A connector read does not
grant permission to write to that provider.

## Connectors

A connector pack has a validated `ConnectorManifest` in
`holdspeak/connector_sdk.py`. Built-in packs load from
`holdspeak/connector_packs/__init__.py::ALL_PACKS`. User packs load from
`~/.holdspeak/connector_packs/` inside the HoldSpeak process. A user pack is
not sandboxed and runs with the process user's permissions.

The lifecycle is discover, preview, enable, and scoped clear. A dry run lists
planned commands, candidates, warnings, and permission notes. It does not
write Desk records. `PermissionGate` checks `shell:exec`, `network:outbound`,
`loopback:http`, and `fs:read` before each connector operation.

| Connector | Reads |
| --- | --- |
| Firefox companion | Loopback URL, title, visit time, and tab/window ids. It rejects private browsing, page bodies, cookies, headers, form data, and non-HTTP(S) URLs. |
| GitHub CLI | Local `gh pr view`, `gh pr list`, `gh issue view`, and `gh run list`. |
| Jira CLI | Local `jira issue view` and `jira issue list`. |
| Atlassian Jira | `acli jira` auth status, project list/view, and work-item search/view. |
| Atlassian Confluence | `acli confluence` auth status, spaces, page view, blog list/view. It has no page search. |
| Calendar activity | Local activity rows for calendar, Meet, and Teams domains. |
| Meeting context | GitHub and Jira annotations plus calendar candidates for a Project. |

The command packs allow listed read commands only. A merge, close, create, or
login command is refused.

Connector routes include:

- `GET /api/activity/enrichment/connectors`
- `PUT /api/activity/enrichment/connectors/{connector_id}`
- `GET /api/activity/enrichment/connectors/{connector_id}/dry-run`
- `GET /api/activity/enrichment/connectors/{connector_id}/runs`
- scoped annotation and candidate clear routes

## Provider routes

Provider credentials stay in host configuration. They do not ride in route
payloads or Desk records.

| Provider | Main routes |
| --- | --- |
| Calendar | `/api/calendar/sources`, `/api/calendar/events`, link and snapshot routes |
| GitHub | `/api/providers/github/connection`, recheck, discover, and repository validation |
| Jira | Connection, recheck, discover, search, and scope validation routes |
| Confluence | Connection, recheck, discover, and validation routes |
| Project sources | Project resources, watches, and activity-rule routes |
| People | The encrypted People store. See [People integration](PEOPLE_INTEGRATION.md). |

The full route list is in [`api-surface.json`](api-surface.json). A provider
read can fail because its CLI, sign-in, connection, or scope is unavailable.
Read the named refusal before retrying.

## Saved execution destinations

An Automation chooses **My Inbox**, **Needs you**, **Today**, or a saved destination for its output.
Saved destinations can target a local folder, GitHub, Jira, Confluence, email, or Slack. The destination row shows its boundary.

For an external saved destination, HoldSpeak first calls `channel.prepare`.
The result waits for your **Send** press. A prepared result is not an external
send and does not prove that the provider received anything.

## Actuators

An actuator turns a reviewed draft into a proposed external effect. The
executor checks `approved` status, the master switch, the destination
allow-list, and the current authority binding. It consumes a scoped grant,
calls the connector, and writes a terminal Receipt.

| Effect | Propose | Decide |
| --- | --- | --- |
| GitHub issue | `POST /api/desk/actuators/github/propose` | `POST /api/desk/actuators/github/{proposal_id}/decision` |
| Slack message | `POST /api/desk/actuators/slack/propose` | `POST /api/desk/actuators/slack/{proposal_id}/decision` |
| Webhook | `POST /api/desk/actuators/webhook/propose` | `POST /api/desk/actuators/webhook/{proposal_id}/decision` |

The executor records `failed` with an audit row when the provider rejects the
call. The stored proposal payload is the only execution input.

## Not available

HoldSpeak has no GitLab connector, connector marketplace, or remote pack
download. Add a local pack only when its permissions and source boundary are
acceptable.

## See also

- [Execution destinations](EXECUTION_DESTINATIONS.md): route and receipt rules.
- [Automation](AUTOMATION.md): output targets and prepared sends.
- [Security and privacy](SECURITY.md): provider data boundaries.
