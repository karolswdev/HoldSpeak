# Meeting aftercare

Aftercare reads saved meeting data and builds a deterministic view of open
actions, decisions, and changes since the previous meeting. It does not call a
model, send a message, or write a meeting record.

## Where you see it

- The **Meeting ready** card opens a meeting with aftercare content.
- The **Send** section offers **Digest** and **Follow-up** documents.
- `GET /api/meetings/{meeting_id}/aftercare` returns the digest data.
- `GET /api/meetings/{meeting_id}/followup-draft` returns the draft text.

No card appears when there is no open work, decision, or detected change.

## How it works

`compute_meeting_aftercare` in `holdspeak/meeting_aftercare.py` reads the
current meeting, finds the previous meeting in the same Project, and compares
their saved records. It does not infer a new fact.

1. Open action items are grouped by owner. Named owners sort alphabetically.
2. Meeting decisions are read from saved decision artifacts and de-duplicated.
3. The previous meeting is selected by meeting start time and Project link.
4. New, closed, and still-open actions are compared by stable identity.
5. Transcript timestamps resolve to source segments when evidence exists.
6. The result is rendered as a digest or a follow-up draft in memory.

## Digest shape

The API returns these logical groups when they contain data:

| Group | Meaning |
| --- | --- |
| `open_by_owner` | Current open action items by owner. |
| `decisions` | Decisions linked to this meeting. |
| `new_items` | Actions that were not open in the previous meeting. |
| `closed_items` | Actions that closed since the previous meeting. |
| `changed` | The previous and current saved state comparison. |
| `moments` | Transcript timestamps resolved to evidence. |

An empty group is omitted from user text. Aftercare does not manufacture a
zero-count status line.

## Transcript moments

An action item or decision can carry a source timestamp. The resolver maps the
timestamp to the nearest saved transcript segment. If no segment exists, the
item remains valid and its evidence is marked unavailable.

## Follow-up draft

`build_followup_draft` renders decisions, open actions, and the change since the
previous meeting as plain Markdown. It uses no model and does not persist the
draft. The draft is not proof that a message was sent.

## Project comparison

Aftercare uses the meeting's saved Project links. If no previous meeting is
linked to that Project, the change section is empty. It does not search every
meeting by similar title.

## Boundaries

Aftercare has no authority to confirm proposals, change a person record, file a
GitHub issue, or send a destination message. Those are separate operations.
Sending uses channel destination binding and the central control policy. The
default **YOLO** mode can run an eligible fixed destination without another
prompt, while hard invariants and receipts still apply.

People data remains in the encrypted People store. Aftercare can show only the
People projection that the active service explicitly provides. It does not copy
private People notes into the main database or a follow-up draft.

## API

| Route | Purpose |
| --- | --- |
| `GET /api/meetings/{meeting_id}/aftercare` | Read the digest model. |
| `GET /api/meetings/{meeting_id}/followup-draft` | Render the draft. |
| `POST /api/meetings/{meeting_id}/aftercare/file-issue` | Propose a GitHub issue. |
| `POST /api/meetings/{meeting_id}/export/slack` | Send through the configured Slack channel operation. |

## See also

- [Meeting Mode guide](MEETING_MODE_GUIDE.md#after-the-meeting)
- [Meeting intelligence](MEETING_INTELLIGENCE.md)
- [People security](PEOPLE_SECURITY.md)
- [Authority](AUTHORITY.md)
