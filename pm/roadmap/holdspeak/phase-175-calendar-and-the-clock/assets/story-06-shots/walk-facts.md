# HS-175-06 walk facts

Generated: 2026-09-05T18:00:31.575258
Hub: 127.0.0.1:54644

## door-api

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| calendar_configured | (true when at least one source connected) | False | DATA | calendar adapter state |
| upcoming_count | (varies) | 1 | DATA | upcoming events + scheduled recordings |
| upcoming_has_room | (true when an event links to a Room) | False | DATA | event-to-Room link in upcoming |
| upcoming_has_armed | (true when an event auto-created a recording) | False | DATA | armed schedule in upcoming |
| week_days | 7 (Mon-Sun strip) | 0 | DATA | WEEK strip day count from door payload |
| week_total_dots | (matches N MEETINGS THIS WEEK) | 0 | DATA | sum of dots across WEEK strip days |
| auto_record | (off / with_url / all) | off | DATA | meeting auto-record setting |
| cadence_status | 200 | 404 | DATA | GET /api/cadence returned HTTP 404 |

## arrival

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| next_line | (NEXT <title> <time> -- from calendar or schedule) | NEXT · SCHED | DATA | NEXT line on arrival (12-char prefix) |
| no_calendar_state | false (calendar should be configured) | False | MATCH | NO CALENDAR banner on arrival |
| week_strip_present | (true when calendar configured -- TODO face) | False | DATA | WEEK strip on arrival face |
| meeting_row_count | (varies) | 3 | DATA | meeting rows on arrival |
| meeting_rows_with_room | (varies, >0 when events are linked to Rooms) | 0 | DATA | meeting rows carrying ROOM token |
| meeting_rows_with_arms | (varies, >0 when auto-record is on) | 0 | DATA | meeting rows carrying ARMS token |
| next_line | (NEXT <title> <time> -- from calendar or schedule) | NEXT · SCHED | DATA | NEXT line on arrival (12-char prefix) |
| no_calendar_state | false (calendar should be configured) | False | MATCH | NO CALENDAR banner on arrival |
| week_strip_present | (true when calendar configured -- TODO face) | False | DATA | WEEK strip on arrival face |
| meeting_row_count | (varies) | 3 | DATA | meeting rows on arrival |
| meeting_rows_with_room | (varies, >0 when events are linked to Rooms) | 0 | DATA | meeting rows carrying ROOM token |
| meeting_rows_with_arms | (varies, >0 when auto-record is on) | 0 | DATA | meeting rows carrying ARMS token |

## settings-calendar

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| calendar_source_count | (>= 1 when calendar configured) | 2 | DATA | calendar source rows in Settings Meetings |
| ics_source_count | (varies) | 0 | DATA | ICS/HTTPS sources |
| snapshot_source_count | (varies) | 0 | DATA | SNAPSHOT sources |
| auto_record_value | (OFF / WITH URL / ALL -- from Settings face) | Auto-record↻ARM ALL CALENDAR MEETINGSARM ROOM MEETINGS ONLYOFF | DATA | Auto-record CycleGadget value on face |
| calendar_source_count | (>= 1 when calendar configured) | 2 | DATA | calendar source rows in Settings Meetings |
| ics_source_count | (varies) | 0 | DATA | ICS/HTTPS sources |
| snapshot_source_count | (varies) | 0 | DATA | SNAPSHOT sources |
| auto_record_value | (OFF / WITH URL / ALL -- from Settings face) | Auto-record↻ARM ALL CALENDAR MEETINGSARM ROOM MEETINGS ONLYOFF | DATA | Auto-record CycleGadget value on face |

## room-sources

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| sources_section_present | true | True | MATCH | SOURCES section on Room face |
| source_row_count | (varies) | 2 | DATA | source rows in SOURCES section |
| source_row:0 | (provider . scope . tokens) | github . karolswdev/HoldSpeak . 2 OPEN PRS . · 2 CHECKS FAILING | DATA | source row content |
| source_row:1 | (provider . scope . tokens) | unknown . KAN . 1 DUE THIS WEEK | DATA | source row content |
| meetings_source_present | (true when meeting Watch adapter is registered) | False | DATA | MEETINGS source row in Room SOURCES |
| sources_section_present | true | True | MATCH | SOURCES section on Room face |
| source_row_count | (varies) | 2 | DATA | source rows in SOURCES section |
| source_row:0 | (provider . scope . tokens) | github . karolswdev/HoldSpeak . 2 OPEN PRS . · 2 CHECKS FAILING | DATA | source row content |
| source_row:1 | (provider . scope . tokens) | unknown . KAN . 1 DUE THIS WEEK | DATA | source row content |
| meetings_source_present | (true when meeting Watch adapter is registered) | False | DATA | MEETINGS source row in Room SOURCES |

## rhythm-brief

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| brief_row_label | (Monday brief or Weekly brief) | Monday brief | DATA | brief row primary label in Rhythm |
| brief_row_tokens | (DAILY HH:MM token) | DAILY 08:00 | DATA | brief row tokens (cadence + time) |
| generate_now_present | true | True | MATCH | Generate now verb on brief row (present but never pressed) |
| generate_now_text | Generate now | Generate | DATA | Generate now verb label |
| brief_facts | (varies) |  | DATA | brief facts section below the row |
| brief_row_label | (Monday brief or Weekly brief) | Monday brief | DATA | brief row primary label in Rhythm |
| brief_row_tokens | (DAILY HH:MM token) | DAILY 08:00 | DATA | brief row tokens (cadence + time) |
| generate_now_present | true | True | MATCH | Generate now verb on brief row (present but never pressed) |
| generate_now_text | Generate now | Generate | DATA | Generate now verb label |
| brief_facts | (varies) |  | DATA | brief facts section below the row |

## Shots

- arrival @ 1440: `walk-arrival-1440.png`
- settings-calendar @ 1440: `walk-settings-calendar-1440.png`
- room-sources @ 1440: `walk-room-sources-1440.png`
- rhythm-brief @ 1440: `walk-rhythm-brief-1440.png`
- arrival @ 393: `walk-arrival-393.png`
- settings-calendar @ 393: `walk-settings-calendar-393.png`
- room-sources @ 393: `walk-room-sources-393.png`
- rhythm-brief @ 393: `walk-rhythm-brief-393.png`

## Defects

1. ARRIVAL: duplicate meeting rows (A.7) -- same title+badge seen twice: ['AUG 20Sprint']

