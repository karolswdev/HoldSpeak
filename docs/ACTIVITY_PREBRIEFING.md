# Activity pre-briefing

Activity pre-briefing shows quiet notes about what you looked at recently.
Each note cites its source. You can use one note as context for your next dictation.
Nothing runs on its own.

If you are new here, read [Getting Started](./GETTING_STARTED.md) first.

## Before you start

Pre-briefing reads the activity ledger. Turn the ledger on first:

1. Open the **Activity** page (`/activity`).
2. Turn on **Watching**.

With **Watching** off, the ledger is empty and no notes appear.
The ledger comes from local Safari and Firefox history.
Connected sources, such as GitHub and Jira, can add detail.

## Find the notes

1. Open the **Dictation** page.
2. Open the gear (**Configure dictation**).
3. Find the **Activity nudges** group.

The page shows up to eight rows. The API returns three by default.
Each row has this form: time, domain, and kind. Example: `14:05 · github.com · GITHUB_ISSUE`.
With no recent activity, the group says **No recent activity to cite**.

## Use or dismiss a note

Each row has two buttons.

- **Use**: Pins the record. Your next dictation receives it as context.
- **Dismiss**: Closes the note. The same note does not return.

The pin is one-shot. HoldSpeak keeps it for five minutes, in memory only.
One dictation consumes it. A restart or a timeout drops it.

Pre-briefing never opens a URL, sends data, or runs a command.

## What a note cites

Every note carries a citation. The API returns it, so you can check the record on `/activity`:

- The entity: a GitHub issue, a pull request, a Jira issue, or a calendar event. Other pages give the domain, the title, and the URL.
- The browser and profile that recorded the visit, for example `safari/default`.
- The date of the last recorded visit.

## Which notes appear

HoldSpeak picks notes with a fixed rule. No model is involved, so the same input gives the same notes.

1. The window starts at the end of your previous meeting. With no earlier meeting, it starts 24 hours ago.
2. A summary note appears when the window holds at least two records. Example: "You touched 5 things since your last meeting".
3. Per-record notes follow. The score rises with recency, with a known entity type, and with a Project match.
4. Records with a weak score do not appear.

## Privacy

- Pre-briefing reads only the activity ledger. It does not watch desktop apps.
- It computes notes on your machine, from your local database. It sends nothing out.
- It does not learn from your dictation.

## Turn it off

Turn off **Watching** on the `/activity` page. The notes stop at once.
You can also keep **Watching** on and dismiss single notes.

## API

| Route | Purpose |
| --- | --- |
| `GET /api/activity/nudges` | List notes. Takes `project_id` and `limit`. |
| `POST /api/activity/nudges/{nudge_id}/dismiss` | Dismiss a note. |
| `POST /api/activity/nudges/select` | Pin a record (`record_id`). |
| `POST /api/activity/nudges/select/clear` | Clear the pin. |

## See also

- [Dictation pipeline](DICTATION_PIPELINE_GUIDE.md)
- [Connector development](CONNECTOR_DEVELOPMENT.md)
