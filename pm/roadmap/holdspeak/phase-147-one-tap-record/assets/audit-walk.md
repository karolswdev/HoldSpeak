# Phase 147 audit — live behavioral walk (the before-pictures)

Opus walk agent, 2026-08-28, real hub against an isolated HOME,
seeded through production HTTP authorities only (four ICS calendar
events via CalendarIngestConductor refresh, one recurring scheduled
recording, one synced meeting with an action item). Shots banked in
[`audit-walk-shots/`](./audit-walk-shots/). Zero console errors, zero
overflow, zero occlusion at either width — the rail is clean; this
phase is pure new-verb work, not repair.

## The verdict: the job is IMPOSSIBLE today

Clicking a calendar EVENT row does **nothing** — the `<li>` is
passive (0 buttons; the only link is the external "Meeting link").
Photographic proof: `door-event-click-1440.png` /
`door-event-click-393.png` are pixel-identical to the populated
shots.

Closest approximation: header "Schedule recording" → a form with NO
pre-fill (`schedule-form-no-prefill-1440.png` — empty title, current
time) → manually retype the event's title and start time → submit.
**2 clicks + full manual data entry**, producing a timer with zero
association to the event.

## Shot index

| Shot | Proves |
|---|---|
| `door-populated-1440/393.png` | 5-column board + 5-row rail (4 EVENT + 1 SCHEDULED RECORDING), chronological, STARTS countdowns; 393 stacks cleanly, titles ellipsize |
| `door-event-click-1440/393.png` | Event row click is a no-op at both widths |
| `schedule-create-form-1440/393.png` | The Phase 136 create window: Title (+mic), ONCE/RECURRING, When, Duration 60 MIN, Cancel/Schedule; docks to bottom at 393 |
| `schedule-form-no-prefill-1440.png` | The form has no concept of "for this event" |
| `schedule-created-1440.png` | A submitted one-shot appears on the rail; Door re-fetches after creation |
| `meetings-surface-1440/393.png` | Where a recorded event's meeting lands (Import / Record meeting buttons) |
| `door-meeting-follow-up-1440.png` | The meeting's action item in the NOW column with Done/Dismiss/Snooze/Delegate — the inline-verb precedent |
| `door-api-response.json` | The upcoming[] wire shape: source, target_ref, title, starts_at, ends_at, location, meeting_url, state, source_id, source_label; NO lawful_verbs on upcoming items |

## Live facts a code census could miss

- `UpcomingRail` is stateless display (props: `upcoming`,
  `calendarConfigured`) — an action needs a callback prop or a
  store/API call from the row.
- `DoorUpcomingItem` already carries everything a one-tap arm needs
  (title, starts_at, ends_at, id, target_ref).
- One-shot creation via UI works end to end today
  (`one_shot: True` confirmed in the API response).
- CaptureHero renders armed/countdown state ONLY off live
  `scheduled_recording.*` broadcasts (not seen in this walk — no
  recording was armed).
- Door re-fetches on `deskUpdatedAt` and `scheduledRecordings` store
  changes (`DoorBoardLane.tsx:335-345`); calendar events refresh only
  when the ingest conductor runs.
- Empty states are already honest ("No calendar connected" +
  Connect button; "No future time scheduled").
- The natural home for the tap: on each EVENT row, rightmost `auto`
  grid column beside STARTS, or a `grid-column: 2 / -1` line like
  location/link (`.door-upcoming-row`, `DoorBoardLane.tsx:492-503`).
