# HS-171-05 walk facts

Generated: 2026-09-05T07:20:28.255506
Hub: 127.0.0.1:62559

## heartbeat-settings

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| api_status | 200 | 200 | MATCH | ok |
| sweep_every_minutes | (owner's setting) | 15 | DATA | real desk content |
| notify | (owner's setting) | edge | DATA | real desk content |
| notify_content | (owner's setting) | --- | DATA | real desk content |
| last_sweep_at | (owner's setting) | 2026-09-05T13:05:39+00:00 | DATA | real desk content |
| next_sweep_at | (owner's setting) | 2026-09-05T13:20:39+00:00 | DATA | real desk content |
| quiet_hours | (start-end) | 22-8 | DATA | real desk content |
| muted_projects | (list) | [] | DATA | real desk content |

## sweep

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| api_status | 200 | 200 | MATCH | ok |
| receipt:rooms | (varies) | 0 | DATA | real desk content |
| receipt:watches | (varies) | 0 | DATA | real desk content |
| receipt:duration_ms | (varies) | 3.5 | DATA | real desk content |
| receipt:held | (varies) | True | DATA | real desk content |
| receipt:errors | (varies) | 0 | DATA | real desk content |
| receipt:needs_you_count | (varies) | --- | DATA | real desk content |
| receipt:sweep_id | (varies) | --- | DATA | real desk content |

## rhythm

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| headline | Every 15 min | Every 15 min | MATCH | exact |
| sweep_primary | Sweep | Sweep | DATA | real desk content |
| sweep_interval | EVERY 15 MIN | EVERY 15 MIN | DATA | real desk content |
| sweep_run_now | Run now | Run now | DATA | real desk content |
| sweep_facts | QUIET HH:00-HH:00 . NEXT HH:MM . LAST HH:MM | ⚠HELD · QUIET UNTIL 08:00QUIET 22:00–08:00·NEXT 13:35·LAST 13:20 | DATA | real desk content |
| brief_primary | Monday brief | Monday brief | DATA | real desk content |
| brief_daily | DAILY 08:00 | DAILY 08:00 | DATA | real desk content |
| brief_generate_now | Generate now | Generate now | DATA | real desk content |
| brief_facts | NEXT MON HH:00 . LAST MON DD | NEXT MON 08:00·LAST AUG 19 | DATA | real desk content |
| notify_primary | Notify | Notify | DATA | real desk content |
| notify_gadgets | ON THE EDGE \| COUNT ONLY | ON THE EDGE \| COUNT ONLY | DATA | real desk content |
| notify_held | HELD (quiet hours) | HELD | DATA | quiet hours active |
| mute_toggle:0 | (project name) enabled/muted | ✓ COMPLETE DELIVERY OF GOVERNANCE FRAMEWORK FOR EVERDRIVEN SOFTWARE ARCHITECTURE enabled | DATA | real desk content |
| footer_written | WRITTEN HH:MM | WRITTEN 13:20 | MATCH | timestamp found |
| headline | Every 15 min | Every 15 min | MATCH | exact |
| sweep_primary | Sweep | Sweep | DATA | real desk content |
| sweep_interval | EVERY 15 MIN | EVERY 15 MIN | DATA | real desk content |
| sweep_run_now | Run now | Run now | DATA | real desk content |
| sweep_facts | QUIET HH:00-HH:00 . NEXT HH:MM . LAST HH:MM | ⚠HELD · QUIET UNTIL 08:00QUIET 22:00–08:00·NEXT 13:35·LAST 13:20 | DATA | real desk content |
| brief_primary | Monday brief | Monday brief | DATA | real desk content |
| brief_daily | DAILY 08:00 | DAILY 08:00 | DATA | real desk content |
| brief_generate_now | Generate now | Generate now | DATA | real desk content |
| brief_facts | NEXT MON HH:00 . LAST MON DD | NEXT MON 08:00·LAST AUG 19 | DATA | real desk content |
| notify_primary | Notify | Notify | DATA | real desk content |
| notify_gadgets | ON THE EDGE \| COUNT ONLY | ON THE EDGE \| COUNT ONLY | DATA | real desk content |
| notify_held | HELD (quiet hours) | HELD | DATA | quiet hours active |
| mute_toggle:0 | (project name) enabled/muted | ✓ COMPLETE DELIVERY OF GOVERNANCE FRAMEWORK FOR EVERDRIVEN SOFTWARE ARCHITECTURE enabled | DATA | real desk content |
| footer_written | WRITTEN HH:MM | WRITTEN 13:20 | MATCH | timestamp found |

## shade

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| projects_caption | PROJECTS . N NEED YOU | --- | DATA | real desk content |
| brief_row | Monday brief N THINGS SEP NN Open | --- | DATA | real desk content |
| projects_caption | PROJECTS . N NEED YOU | --- | DATA | real desk content |
| brief_row | Monday brief N THINGS SEP NN Open | --- | DATA | real desk content |

## dock

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| badge_count | (aggregate needs-you count or absent) | • | DATA | real desk content |
| badge_count | (aggregate needs-you count or absent) | • | DATA | real desk content |

## command-deck

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| projects_group_count | (N project entries) | 1 | DATA | real desk content |
| project:0 | Open <name> \| N NEED(S) YOU \| PROJECT | Open Complete delivery of governance framework for EverDriven Software Architecture \|  \| PROJECT | DATA | real desk content |
| groups | PROJECTS, VERBS, PROGRAMS, ... | PROJECTS, VERBS, PROGRAMS, SETTINGS | DATA | real desk content |
| projects_group_count | (N project entries) | 1 | DATA | real desk content |
| project:0 | Open <name> \| N NEED(S) YOU \| PROJECT | Open Complete delivery of governance framework for EverDriven Software Architecture \|  \| PROJECT | DATA | real desk content |
| groups | PROJECTS, VERBS, PROGRAMS, ... | PROJECTS, VERBS, PROGRAMS, SETTINGS | DATA | real desk content |

## notification

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| notify_receipts_route | (no route exists) | NO ROUTE FOR NOTIFY RECEIPTS | DATA | heartbeat.notify receipts not exposed via HTTP; the notifier (desktop_notify.py) tracks last_notified_count in memory |
| last_sweep_at | (timestamp) | 2026-09-05T13:20:30+00:00 | DATA | from GET /api/settings/heartbeat |
| next_sweep_at | (timestamp) | 2026-09-05T13:35:30+00:00 | DATA | from GET /api/settings/heartbeat |
| banner_expectation | NO BANNER (count=0) | count=0, no needs-you items | DATA | no items to notify about |

## Sweep receipt

```json
{
  "kind": "heartbeat.sweep",
  "at": "2026-09-05T13:20:30+00:00",
  "rooms": 0,
  "watches": 0,
  "duration_ms": 3.5,
  "held": true,
  "errors": 0,
  "outcomes": {
    "counts": {},
    "total": 0,
    "failed_watch_ids": []
  }
}
```

## Shots

- rhythm @ 1440: `walk-rhythm-1440.png`
- shade @ 1440: `walk-shade-1440.png`
- dock @ 1440: `walk-dock-1440.png`
- command-deck @ 1440: `walk-command-deck-1440.png`
- rhythm @ 393: `walk-rhythm-393.png`
- shade @ 393: `walk-shade-393.png`
- dock @ 393: `walk-dock-393.png`
- command-deck @ 393: `walk-command-deck-393.png`

## Defects

None.

