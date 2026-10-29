# Activity pre-briefing

Activity pre-briefing collects relevant records from configured activity
connectors and shows a source-linked note before a meeting or work session. It
is a preparation read. It does not record audio, call a model, or send a
message.

## Before you start

Connectors must be configured and the hub must be running. The activity face
shows connector readiness, the current privacy setting, and the last refresh.
A connector can return no records or a named error.

## Find the notes

Open **Activity** and select the pre-briefing note. The route
`GET /api/activity/records` returns saved activity records. Use
`POST /api/activity/refresh` to refresh configured connectors. Candidate
meetings are available from `GET /api/activity/meeting-candidates`.

## Use or dismiss a note

Open a note to inspect its source references. Use the available **Use** or
**Dismiss** control. Using a note adds it as context for the current task. It
does not approve an external effect. Dismissal parks the candidate and does not
delete the source record.

## What a note cites

Each candidate records its connector, source identity, and observed time. The
note is a projection. It is not a transcript and it does not prove that the
source is current after the refresh.

## Which notes appear

Project rules and connector filters decide which records become candidates.
Meeting candidates can be started through
`POST /api/activity/meeting-candidates/{candidate_id}/start`. The route still
uses the ordinary meeting capture and authority path.

## Privacy

Activity connectors are separate egress boundaries. A refresh can send
connector credentials or query data to the configured provider. Activity
pre-briefing does not make a blanket local-only claim. Inspect connector
configuration and the activity privacy setting before refresh.

People data stays in the encrypted People store. Activity pre-briefing does not
copy private People notes into the plain activity ledger.

## Turn it off

Use **Settings > Activity** or `PUT /api/activity/settings` to disable the
refresh or change connector scope. `DELETE /api/activity/records` clears the
activity projection when the route permits it. It does not delete the source
provider records.

## API

| Route | Purpose |
| --- | --- |
| `GET /api/activity/status` | Read readiness and privacy state. |
| `GET /api/activity/records` | Read saved projections. |
| `GET /api/activity/project-rules` | Read project filters. |
| `GET /api/activity/meeting-candidates` | List meeting candidates. |
| `POST /api/activity/refresh` | Refresh configured connectors. |
| `PUT /api/activity/settings` | Change local activity settings. |

## See also

- [Meeting Mode guide](MEETING_MODE_GUIDE.md)
- [Security](SECURITY.md)
- [Project Rooms](PROJECT_ROOMS.md)
