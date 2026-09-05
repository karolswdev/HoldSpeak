# HS-170-05 walk facts

Generated: 2026-09-05T02:38:05.121679
Hub: 127.0.0.1:51435

## arrival

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| headline | (owner's real desk) | Nothing needs you | DATA | board=(owner's real desk), real=Nothing needs you |
| sections_present | (varies by desk state) | brief, meetings | DATA | real desk state |
| section_count | (varies) | 2 | DATA | 2 sections visible |
| headline | (owner's real desk) | Nothing needs you | DATA | board=(owner's real desk), real=Nothing needs you |
| sections_present | (varies by desk state) | brief, meetings | DATA | real desk state |
| section_count | (varies) | 2 | DATA | 2 sections visible |

## settings-hub

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| headline | No default model | All set | DATA | board=No default model, real=All set |
| row:Models | NO DEFAULT 3 ENGINES | 8 ENGINES | DATA | board=NO DEFAULT 3 ENGINES, real=8 ENGINES |
| row:Connections | 2 CONNECTED | 2 CONNECTED | MATCH | exact |
| row:Voice | LIVE CLAUDE CODE | ✓LIVE CODEX_CLI | DATA | board=LIVE CLAUDE CODE, real=✓LIVE CODEX_CLI |
| row:Meetings | INTELLIGENCE OFF | ✓INTELLIGENCE ON | DATA | board=INTELLIGENCE OFF, real=✓INTELLIGENCE ON |
| row:Rhythm | NO LOOPS | NO LOOPS | MATCH | exact |
| row:Sounds & Presence | ON | ✓ON | MATCH | substring |
| row:System | THIS DEVICE MESH OFF | THIS DEVICE MESH OFF | MATCH | exact |
| posture | YOLO | Posture↻SecureNormalYOLO | MATCH | substring |
| footer_egress | THIS DEVICE | THIS DEVICE | MATCH | exact |
| footer_written | WRITTEN HH:MM | WRITTEN 08:15 | MATCH | timestamp found |
| headline | No default model | All set | DATA | board=No default model, real=All set |
| row:Models | NO DEFAULT 3 ENGINES | 8 ENGINES | DATA | board=NO DEFAULT 3 ENGINES, real=8 ENGINES |
| row:Connections | 2 CONNECTED | 2 CONNECTED | MATCH | exact |
| row:Voice | LIVE CLAUDE CODE | ✓LIVE CODEX_CLI | DATA | board=LIVE CLAUDE CODE, real=✓LIVE CODEX_CLI |
| row:Meetings | INTELLIGENCE OFF | ✓INTELLIGENCE ON | DATA | board=INTELLIGENCE OFF, real=✓INTELLIGENCE ON |
| row:Rhythm | NO LOOPS | NO LOOPS | MATCH | exact |
| row:Sounds & Presence | ON | ✓ON | MATCH | substring |
| row:System | THIS DEVICE MESH OFF | THIS DEVICE MESH OFF | MATCH | exact |
| posture | YOLO | Posture↻SecureNormalYOLO | MATCH | substring |
| footer_egress | THIS DEVICE | THIS DEVICE | MATCH | exact |
| footer_written | WRITTEN HH:MM | WRITTEN 08:15 | MATCH | timestamp found |

## meetings

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| headline | N meeting(s) need(s) intelligence | Nothing needs you | DATA | real desk content |
| row:0:title | (real meeting) | Already titled | DATA | real desk content |
| row:0:tokens | (date, duration, state) | AUG 22·2 WORDS·QUEUED | DATA | real desk content |
| row:0:verb | Open or Run intelligence |  | DATA | real desk content |
| row:1:title | (real meeting) | Sprint Review | DATA | real desk content |
| row:1:tokens | (date, duration, state) | AUG 20·NO TRANSCRIPT | DATA | real desk content |
| row:1:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:2:title | (real meeting) | Sprint Review | DATA | real desk content |
| row:2:tokens | (date, duration, state) | AUG 20·NO TRANSCRIPT | DATA | real desk content |
| row:2:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:3:title | (real meeting) | Meeting | DATA | real desk content |
| row:3:tokens | (date, duration, state) | AUG 17·1 MIN·26 WORDS·SKIPPED | DATA | real desk content |
| row:3:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:4:title | (real meeting) | Meeting | DATA | real desk content |
| row:4:tokens | (date, duration, state) | AUG 11·REC | DATA | real desk content |
| row:4:verb | Open or Run intelligence | Retry | DATA | real desk content |
| row:5:title | (real meeting) | Meeting | DATA | real desk content |
| row:5:tokens | (date, duration, state) | AUG 11·REC | DATA | real desk content |
| row:5:verb | Open or Run intelligence | Retry | DATA | real desk content |
| row:6:title | (real meeting) | Meeting | DATA | real desk content |
| row:6:tokens | (date, duration, state) | AUG 11·REC | DATA | real desk content |
| row:6:verb | Open or Run intelligence | Retry | DATA | real desk content |
| row:7:title | (real meeting) | Meeting | DATA | real desk content |
| row:7:tokens | (date, duration, state) | AUG 11·REC | DATA | real desk content |
| row:7:verb | Open or Run intelligence | Retry | DATA | real desk content |
| detail:needs_you_label | NEEDS YOU N | --- | DATA | real desk content |
| detail:needs_you_rows | (varies) | 1840 | DATA | real desk content |
| headline | N meeting(s) need(s) intelligence | Nothing needs you | DATA | real desk content |
| row:0:title | (real meeting) | Already titled | DATA | real desk content |
| row:0:tokens | (date, duration, state) | AUG 22·2 WORDS·QUEUED | DATA | real desk content |
| row:0:verb | Open or Run intelligence |  | DATA | real desk content |
| row:1:title | (real meeting) | Sprint Review | DATA | real desk content |
| row:1:tokens | (date, duration, state) | AUG 20·NO TRANSCRIPT | DATA | real desk content |
| row:1:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:2:title | (real meeting) | Sprint Review | DATA | real desk content |
| row:2:tokens | (date, duration, state) | AUG 20·NO TRANSCRIPT | DATA | real desk content |
| row:2:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:3:title | (real meeting) | Meeting | DATA | real desk content |
| row:3:tokens | (date, duration, state) | AUG 17·1 MIN·26 WORDS·SKIPPED | DATA | real desk content |
| row:3:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:4:title | (real meeting) | Meeting | DATA | real desk content |
| row:4:tokens | (date, duration, state) | AUG 11·REC | DATA | real desk content |
| row:4:verb | Open or Run intelligence | Retry | DATA | real desk content |
| row:5:title | (real meeting) | Meeting | DATA | real desk content |
| row:5:tokens | (date, duration, state) | AUG 11·REC | DATA | real desk content |
| row:5:verb | Open or Run intelligence | Retry | DATA | real desk content |
| row:6:title | (real meeting) | Meeting | DATA | real desk content |
| row:6:tokens | (date, duration, state) | AUG 11·REC | DATA | real desk content |
| row:6:verb | Open or Run intelligence | Retry | DATA | real desk content |
| row:7:title | (real meeting) | Meeting | DATA | real desk content |
| row:7:tokens | (date, duration, state) | AUG 11·REC | DATA | real desk content |
| row:7:verb | Open or Run intelligence | Retry | DATA | real desk content |
| detail:needs_you_label | NEEDS YOU N | --- | DATA | real desk content |
| detail:needs_you_rows | (varies) | 1840 | DATA | real desk content |

## speak

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| lands_in_target | Claude Code | Codex CLI | DATA | board=Claude Code, real=Codex CLI |
| engine_caption | DICTATION | DICTATION | MATCH | exact |
| engine_name | Qwen 3.5 0.8B | Migrated intel endpoint | DATA | board=Qwen 3.5 0.8B, real=Migrated intel endpoint |
| engine_egress | THIS DEVICE |  | DATA | no data observed |
| engine_state | READY |  | DATA | no data observed |
| footer_receipt | THIS DEVICE N TODAY | THIS DEVICE9 TODAYReviewExport | DATA | real desk content |
| lands_in_target | Claude Code | Codex CLI | DATA | board=Claude Code, real=Codex CLI |
| engine_caption | DICTATION | DICTATION | MATCH | exact |
| engine_name | Qwen 3.5 0.8B | Migrated intel endpoint | DATA | board=Qwen 3.5 0.8B, real=Migrated intel endpoint |
| engine_egress | THIS DEVICE |  | DATA | no data observed |
| engine_state | READY |  | DATA | no data observed |
| footer_receipt | THIS DEVICE N TODAY | THIS DEVICE9 TODAYReviewExport | DATA | real desk content |

## Shots

- arrival @ 1440: `walk-arrival-1440.png`
- settings-hub @ 1440: `walk-settings-hub-1440.png`
- meetings-list @ 1440: `walk-meetings-list-1440.png`
- meetings-detail @ 1440: `walk-meetings-detail-1440.png`
- speak @ 1440: `walk-speak-idle-1440.png`
- arrival @ 393: `walk-arrival-393.png`
- settings-hub @ 393: `walk-settings-hub-393.png`
- meetings-list @ 393: `walk-meetings-list-393.png`
- meetings-detail @ 393: `walk-meetings-detail-393.png`
- speak @ 393: `walk-speak-idle-393.png`

