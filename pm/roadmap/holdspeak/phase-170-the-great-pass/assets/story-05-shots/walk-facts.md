# HS-170-05 walk facts

Generated: 2026-09-05T04:20:02.074603
Hub: 127.0.0.1:60874

## arrival

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| headline | (owner's real desk) | Nothing needs you | DATA | board=(owner's real desk), real=Nothing needs you |
| sections_present | (varies by desk state) | meetings | DATA | real desk state |
| section_count | (varies) | 1 | DATA | 1 sections visible |
| next_slot | (varies) | NEXT · SCHEDULED RECORDING · 15:34 | DATA | real desk content |
| capture_bar_verbs | (Talk, Develop a thought, Record meeting, ...) | TalkDevelop a thoughtRecord meetingSchedule | DATA | real desk content |
| headline | (owner's real desk) | Nothing needs you | DATA | board=(owner's real desk), real=Nothing needs you |
| sections_present | (varies by desk state) | meetings | DATA | real desk state |
| section_count | (varies) | 1 | DATA | 1 sections visible |
| next_slot | (varies) | NEXT · SCHEDULED RECORDING · 15:34 | DATA | real desk content |
| capture_bar_verbs | (Talk, Develop a thought, Record meeting, ...) | TalkDevelop a thoughtRecord meetingSchedule | DATA | real desk content |

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
| row:0:verb | Open or Run intelligence | Open | DATA | real desk content |
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
| row:4:tokens | (date, duration, state) | AUG 11·INTERRUPTED | DATA | real desk content |
| row:4:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:5:title | (real meeting) | Meeting | DATA | real desk content |
| row:5:tokens | (date, duration, state) | AUG 11·INTERRUPTED | DATA | real desk content |
| row:5:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:6:title | (real meeting) | Meeting | DATA | real desk content |
| row:6:tokens | (date, duration, state) | AUG 11·INTERRUPTED | DATA | real desk content |
| row:6:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:7:title | (real meeting) | Meeting | DATA | real desk content |
| row:7:tokens | (date, duration, state) | AUG 11·INTERRUPTED | DATA | real desk content |
| row:7:verb | Open or Run intelligence | Open | DATA | real desk content |
| detail:needs_you_label | NEEDS YOU N | --- | DATA | real desk content |
| detail:needs_you_rows | (varies) | 3 | DATA | real desk content |
| headline | N meeting(s) need(s) intelligence | Nothing needs you | DATA | real desk content |
| row:0:title | (real meeting) | Already titled | DATA | real desk content |
| row:0:tokens | (date, duration, state) | AUG 22·2 WORDS·QUEUED | DATA | real desk content |
| row:0:verb | Open or Run intelligence | Open | DATA | real desk content |
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
| row:4:tokens | (date, duration, state) | AUG 11·INTERRUPTED | DATA | real desk content |
| row:4:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:5:title | (real meeting) | Meeting | DATA | real desk content |
| row:5:tokens | (date, duration, state) | AUG 11·INTERRUPTED | DATA | real desk content |
| row:5:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:6:title | (real meeting) | Meeting | DATA | real desk content |
| row:6:tokens | (date, duration, state) | AUG 11·INTERRUPTED | DATA | real desk content |
| row:6:verb | Open or Run intelligence | Open | DATA | real desk content |
| row:7:title | (real meeting) | Meeting | DATA | real desk content |
| row:7:tokens | (date, duration, state) | AUG 11·INTERRUPTED | DATA | real desk content |
| row:7:verb | Open or Run intelligence | Open | DATA | real desk content |
| detail:needs_you_label | NEEDS YOU N | --- | DATA | real desk content |
| detail:needs_you_rows | (varies) | 3 | DATA | real desk content |

## speak

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| lands_in_target | Claude Code | Codex CLI | DATA | board=Claude Code, real=Codex CLI |
| engine_caption | DICTATION | DICTATION | MATCH | exact |
| engine_name | Qwen 3.5 0.8B | GPT 5 mini | DATA | board=Qwen 3.5 0.8B, real=GPT 5 mini |
| engine_egress | THIS DEVICE | API.OPENAI.COM | DATA | board=THIS DEVICE, real=API.OPENAI.COM |
| engine_state | READY | ⚠KEY NOT SET | DATA | board=READY, real=⚠KEY NOT SET |
| footer_receipt | THIS DEVICE N TODAY | THIS DEVICE9 TODAYReviewExport | DATA | real desk content |
| lands_in_target | Claude Code | Codex CLI | DATA | board=Claude Code, real=Codex CLI |
| engine_caption | DICTATION | DICTATION | MATCH | exact |
| engine_name | Qwen 3.5 0.8B | GPT 5 mini | DATA | board=Qwen 3.5 0.8B, real=GPT 5 mini |
| engine_egress | THIS DEVICE | API.OPENAI.COM | DATA | board=THIS DEVICE, real=API.OPENAI.COM |
| engine_state | READY | ⚠KEY NOT SET | DATA | board=READY, real=⚠KEY NOT SET |
| footer_receipt | THIS DEVICE N TODAY | THIS DEVICE9 TODAYReviewExport | DATA | real desk content |

## concierge

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| headline | N engine(s) found | 8 engines found | DATA | real desk content |
| found:0:name | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| found:0:host | (host chip) | 192.168.1.43 · LAN | DATA | real desk content |
| found:0:state | (state) | ●READY | DATA | real desk content |
| found:1:name | (engine name) | Qwythos 9B Claude Mythos 5 1M | DATA | real desk content |
| found:1:host | (host chip) | 192.168.1.43 · LAN | DATA | real desk content |
| found:1:state | (state) | ●READY | DATA | real desk content |
| found:2:name | (engine name) | GPT 5 mini | DATA | real desk content |
| found:2:host | (host chip) | API.OPENAI.COM | DATA | real desk content |
| found:2:state | (state) | ⚠NOT SET | DATA | real desk content |
| found:3:name | (engine name) | Qwen3 8B | DATA | real desk content |
| found:3:host | (host chip) | OPENROUTER.AI | DATA | real desk content |
| found:3:state | (state) | ●READY | DATA | real desk content |
| found:4:name | (engine name) | Qwen3 8B | DATA | real desk content |
| found:4:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:4:state | (state) | ●READY | DATA | real desk content |
| found:5:name | (engine name) | Gemma 4 E4B it qat | DATA | real desk content |
| found:5:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:5:state | (state) | ●READY | DATA | real desk content |
| found:6:name | (engine name) | Qwen3 4B Instruct 2507 | DATA | real desk content |
| found:6:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:6:state | (state) | ●READY | DATA | real desk content |
| found:7:name | (engine name) | Qwythos 9B Claude Mythos 5 1M | DATA | real desk content |
| found:7:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:7:state | (state) | ●READY | DATA | real desk content |
| found:8:name | (engine name) | Quick local Qwen | DATA | real desk content |
| found:8:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:8:state | (state) | ○WAITING | DATA | real desk content |
| found:9:name | (engine name) | Tiny local Qwen | DATA | real desk content |
| found:9:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:9:state | (state) | ○WAITING | DATA | real desk content |
| set:0:group | (group name) |  | DATA | real desk content |
| set:0:engine | (engine name) |  | DATA | real desk content |
| set:0:state | (state) |  | DATA | real desk content |
| set:1:group | (group name) | Thoughts & notes | DATA | real desk content |
| set:1:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:1:state | (state) | ●READY | DATA | real desk content |
| set:2:group | (group name) | Thoughts & notes | DATA | real desk content |
| set:2:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:2:state | (state) | ●READY | DATA | real desk content |
| set:3:group | (group name) | Chat | DATA | real desk content |
| set:3:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:3:state | (state) | ●READY | DATA | real desk content |
| set:4:group | (group name) | Writing & dictation | DATA | real desk content |
| set:4:engine | (engine name) | Qwen3 4B Instruct 2507 | DATA | real desk content |
| set:4:state | (state) | ●READY | DATA | real desk content |
| set:5:group | (group name) | Speech recognition | DATA | real desk content |
| set:5:engine | (engine name) | Quick local Qwen | DATA | real desk content |
| set:5:state | (state) | ○WAITING | DATA | real desk content |
| set:6:group | (group name) | Meetings | DATA | real desk content |
| set:6:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:6:state | (state) | ●READY | DATA | real desk content |
| set:7:group | (group name) | Agents & tools | DATA | real desk content |
| set:7:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:7:state | (state) | ●READY | DATA | real desk content |
| set:8:group | (group name) | Background | DATA | real desk content |
| set:8:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:8:state | (state) | ●READY | DATA | real desk content |
| headline | N engine(s) found | 8 engines found | DATA | real desk content |
| found:0:name | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| found:0:host | (host chip) | 192.168.1.43 · LAN | DATA | real desk content |
| found:0:state | (state) | ●READY | DATA | real desk content |
| found:1:name | (engine name) | Qwythos 9B Claude Mythos 5 1M | DATA | real desk content |
| found:1:host | (host chip) | 192.168.1.43 · LAN | DATA | real desk content |
| found:1:state | (state) | ●READY | DATA | real desk content |
| found:2:name | (engine name) | GPT 5 mini | DATA | real desk content |
| found:2:host | (host chip) | API.OPENAI.COM | DATA | real desk content |
| found:2:state | (state) | ⚠NOT SET | DATA | real desk content |
| found:3:name | (engine name) | Qwen3 8B | DATA | real desk content |
| found:3:host | (host chip) | OPENROUTER.AI | DATA | real desk content |
| found:3:state | (state) | ●READY | DATA | real desk content |
| found:4:name | (engine name) | Qwen3 8B | DATA | real desk content |
| found:4:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:4:state | (state) | ●READY | DATA | real desk content |
| found:5:name | (engine name) | Gemma 4 E4B it qat | DATA | real desk content |
| found:5:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:5:state | (state) | ●READY | DATA | real desk content |
| found:6:name | (engine name) | Qwen3 4B Instruct 2507 | DATA | real desk content |
| found:6:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:6:state | (state) | ●READY | DATA | real desk content |
| found:7:name | (engine name) | Qwythos 9B Claude Mythos 5 1M | DATA | real desk content |
| found:7:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:7:state | (state) | ●READY | DATA | real desk content |
| found:8:name | (engine name) | Quick local Qwen | DATA | real desk content |
| found:8:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:8:state | (state) | ○WAITING | DATA | real desk content |
| found:9:name | (engine name) | Tiny local Qwen | DATA | real desk content |
| found:9:host | (host chip) | THIS DEVICE | DATA | real desk content |
| found:9:state | (state) | ○WAITING | DATA | real desk content |
| set:0:group | (group name) |  | DATA | real desk content |
| set:0:engine | (engine name) |  | DATA | real desk content |
| set:0:state | (state) |  | DATA | real desk content |
| set:1:group | (group name) | Thoughts & notes | DATA | real desk content |
| set:1:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:1:state | (state) | ●READY | DATA | real desk content |
| set:2:group | (group name) | Thoughts & notes | DATA | real desk content |
| set:2:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:2:state | (state) | ●READY | DATA | real desk content |
| set:3:group | (group name) | Chat | DATA | real desk content |
| set:3:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:3:state | (state) | ●READY | DATA | real desk content |
| set:4:group | (group name) | Writing & dictation | DATA | real desk content |
| set:4:engine | (engine name) | Qwen3 4B Instruct 2507 | DATA | real desk content |
| set:4:state | (state) | ●READY | DATA | real desk content |
| set:5:group | (group name) | Speech recognition | DATA | real desk content |
| set:5:engine | (engine name) | Quick local Qwen | DATA | real desk content |
| set:5:state | (state) | ○WAITING | DATA | real desk content |
| set:6:group | (group name) | Meetings | DATA | real desk content |
| set:6:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:6:state | (state) | ●READY | DATA | real desk content |
| set:7:group | (group name) | Agents & tools | DATA | real desk content |
| set:7:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:7:state | (state) | ●READY | DATA | real desk content |
| set:8:group | (group name) | Background | DATA | real desk content |
| set:8:engine | (engine name) | Qwen3.6 35B A3B | DATA | real desk content |
| set:8:state | (state) | ●READY | DATA | real desk content |

## Shots

- arrival @ 1440: `walk-arrival-1440.png`
- settings-hub @ 1440: `walk-settings-hub-1440.png`
- meetings-list @ 1440: `walk-meetings-list-1440.png`
- meetings-detail @ 1440: `walk-meetings-detail-1440.png`
- speak @ 1440: `walk-speak-idle-1440.png`
- concierge @ 1440: `walk-concierge-1440.png`
- arrival @ 393: `walk-arrival-393.png`
- settings-hub @ 393: `walk-settings-hub-393.png`
- meetings-list @ 393: `walk-meetings-list-393.png`
- meetings-detail @ 393: `walk-meetings-detail-393.png`
- speak @ 393: `walk-speak-idle-393.png`
- concierge @ 393: `walk-concierge-393.png`

