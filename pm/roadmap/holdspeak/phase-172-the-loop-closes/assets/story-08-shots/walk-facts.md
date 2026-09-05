# HS-172-08 walk facts

Generated: 2026-09-05T10:01:10.761135
Hub: 127.0.0.1:56116

## intel-settings

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| hub_meetings_host | (resolved model host or null) | api.openai.com | DATA | from GET /api/settings/hub |
| hub_meetings_auto | room_linked / every / off | room_linked | DATA | from GET /api/settings/hub |
| hub_meetings_intelligence | true / false | True | DATA | from GET /api/settings/hub |
| raw_intel_profile_id | (profile id or empty) | legacy-intel | DATA | from GET /api/settings -> meeting.intel_profile_id |
| raw_intelligence_auto | room_linked / every / off | room_linked | DATA | from GET /api/settings -> meeting.intelligence_auto |

## meeting-intel

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| target_meeting | Already titled | Already titled (id=meeting-...) | DATA | real desk content |
| proposals_count | (varies) | 0 | DATA | real desk content |
| intel_run | SKIPPED | SKIPPED: not LAN: api.openai.com (host=api.openai.com) | DATA | host guard denied: not LAN: api.openai.com |

## people

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| relationship_count | (varies) | 1 | DATA | real desk content |
| watch_summary:prs_waiting | (count) | 0 | DATA | PRs waiting on <person> |
| watch_summary:open_assignments | (count) | 0 | DATA | open assignments for <person> |
| watch_summary:open_commitments | (count) | 0 | DATA | open commitments for <person> |
| prep_display | (person name[:2]***) | Je*** | DATA | prep display (truncated for privacy) |
| prep_prs_row | (present if prs > 0) | False | DATA | PRS WAITING row |
| prep_assignments_row | (present if assigns > 0) | False | DATA | ASSIGNMENTS OPEN row |
| prep_receipt | PREPARED HH:MM | --- | DATA | prep footer |

## room

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| project_name | (owner's project) | Complete delivery of governance framework for EverDriven Software Architecture | DATA | real desk content |
| headline | (N need you or Nothing needs you) | Nothing needs you | MATCH | substring |
| proposal_rows | (varies) | 0 | DATA | real desk content |
| decision_rows | (varies) | 0 | DATA | real desk content |
| suggested_source_rows | (varies) | 0 | DATA | real desk content |
| source_rows | (varies) | 2 | DATA | real desk content |
| people_section | PEOPLE N |  | DATA | real desk content |
| project_name | (owner's project) | Complete delivery of governance framework for EverDriven Software Architecture | DATA | real desk content |
| headline | (N need you or Nothing needs you) | Nothing needs you | MATCH | substring |
| proposal_rows | (varies) | 0 | DATA | real desk content |
| decision_rows | (varies) | 0 | DATA | real desk content |
| suggested_source_rows | (varies) | 0 | DATA | real desk content |
| source_rows | (varies) | 2 | DATA | real desk content |
| people_section | PEOPLE N |  | DATA | real desk content |

## meeting-detail

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| detail_title | (meeting title[:12]) | Already titl | DATA | real desk content |
| detail_facts | DATE . N MIN . RAN . N S . host . LAN | AUG 22·1 MIN·INTELLIGENCE QUEUED·Migrated intel endpoint · CLOUD | DATA | real desk content |
| ran_chip | true | False | DATA | no RAN chip |
| egress_chip | (host . LAN or THIS DEVICE) | Migrated intel endpoint · CLOUD | DATA | real desk content |
| needs_you_caption | NEEDS YOU N | NEEDS YOU | DATA | real desk content |
| needs_you_rows | (varies) | 0 | DATA | real desk content |
| detail_title | (meeting title[:12]) | Already titl | DATA | real desk content |
| detail_facts | DATE . N MIN . RAN . N S . host . LAN | AUG 22·1 MIN·INTELLIGENCE QUEUED·Migrated intel endpoint · CLOUD | DATA | real desk content |
| ran_chip | true | False | DATA | no RAN chip |
| egress_chip | (host . LAN or THIS DEVICE) | Migrated intel endpoint · CLOUD | DATA | real desk content |
| needs_you_caption | NEEDS YOU N | NEEDS YOU | DATA | real desk content |
| needs_you_rows | (varies) | 0 | DATA | real desk content |

## arrival

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| headline | (N need you or Nothing needs you) | Nothing needs you | MATCH | substring |
| proposal_rows | (varies) | 0 | DATA | real desk content |
| meeting_rows | (varies) | 3 | DATA | real desk content |
| meetings_has_RAN | true | False | DATA | no RAN chip |
| sections_present | (varies by desk state) | meetings | DATA | real desk state |
| headline | (N need you or Nothing needs you) | Nothing needs you | MATCH | substring |
| proposal_rows | (varies) | 0 | DATA | real desk content |
| meeting_rows | (varies) | 3 | DATA | real desk content |
| meetings_has_RAN | true | False | DATA | no RAN chip |
| sections_present | (varies by desk state) | meetings | DATA | real desk state |

## settings-meetings

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| display_headline | After every meeting / After room meetings / Off | After room meetings | DATA | real desk content |
| intelligence_cycle | AFTER EVERY MEETING / ROOM-LINKED ONLY / OFF | AFTER ROOM MEETINGS | DATA | real desk content |
| intelligence_egress | (host . LAN or THIS DEVICE) | → 192.168.1.43:8081 | DATA | intel model host chip |
| display_headline | After every meeting / After room meetings / Off | After room meetings | DATA | real desk content |
| intelligence_cycle | AFTER EVERY MEETING / ROOM-LINKED ONLY / OFF | AFTER ROOM MEETINGS | DATA | real desk content |
| intelligence_egress | (host . LAN or THIS DEVICE) | → 192.168.1.43:8081 | DATA | intel model host chip |

## Shots

- people-prep @ 1440: `walk-people-prep-1440.png`
- room @ 1440: `walk-room-1440.png`
- meeting-detail @ 1440: `walk-meeting-1440.png`
- arrival @ 1440: `walk-arrival-1440.png`
- settings-meetings @ 1440: `walk-settings-meetings-1440.png`
- room @ 393: `walk-room-393.png`
- meeting-detail @ 393: `walk-meeting-393.png`
- arrival @ 393: `walk-arrival-393.png`
- settings-meetings @ 393: `walk-settings-meetings-393.png`

## Defects

None.

