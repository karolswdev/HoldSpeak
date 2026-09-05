# HS-170-01 Census

Raw button count includes window chrome (3 traffic lights at 1440,
2 at 393) + wing tabs + gear icons. Subtract chrome to get content
raw buttons. Zero counter probe only catches `.surface-token` / `[data-chip]`
elements; bare-text zeros (e.g. "RUNNING 0") are noted manually.

| key | width | window | raw btns | sentences | type steps | clipped | footer | zero ctrs | notes |
|-----|-------|--------|----------|-----------|------------|---------|--------|-----------|-------|
| configure-cadence | 393 | 393x533 | 3 | 0 | 4 (10, 11, 12, 13) | no | yes | 0 | Stranger sees two-column empty; duplicate "Run now" verb (header + body) |
| configure-cadence | 1440 | 640x619 | 4 | 0 | 4 (10, 11, 12, 13) | no | yes | 0 | Same; duplicate "Run now" is redundant but honest |
| configure-commands | 393 | 393x332 | 3 | 0 | 5 (10, 11, 12, 13, 17) | no | yes | 0 | "0 commands" bare-text zero counter; CANON BREAK rule 8 |
| configure-commands | 1440 | 640x619 | 4 | 0 | 5 (10, 11, 12, 13, 17) | no | yes | 0 | "0 commands" + double "Add command" verbs; bare-text zero counter |
| configure-settings | 393 | 393x449 | 12 | 0 | 3 (10, 11, 12) | no | yes | 0 | 8 category cards are raw buttons; clean grid; POSTURE cycle |
| configure-settings | 1440 | 1392x760 | 13 | 0 | 3 (10, 11, 12) | no | yes | 0 | Stranger sees 8 icon cards 4x2; maximized; only 3 type steps (borderline rule C) |
| configure-setup | 393 | 393x702 | 2 | 3 | 5 (10, 11, 12, 13, 14) | no | yes | 0 | Check descriptions are prose sentences; CANON BREAK rule A3 |
| configure-setup | 1440 | 640x619 | 3 | 3 | 5 (10, 11, 12, 13, 14) | no | yes | 0 | NEEDS ATTENTION badge + PASS/WARN checklist; 3 sentences in check descriptions |
| design-components | 393 | 393x702 | 36 | 0 | 11 (6, 9, 10, 11, 12, 13, 13.3, 14, 15, 16, 17) | YES | yes | 0 | Component catalog -- raw buttons ARE specimens; clipping expected; not a user face |
| design-components | 1440 | 640x619 | 37 | 0 | 11 (6, 9, 10, 11, 12, 13, 13.3, 14, 15, 16, 17) | YES | yes | 0 | Same: catalog surface; raw buttons and clipping are the demo content |
| dictate | 393 | 393x702 | 12 | 0 | 7 (9, 10, 11, 12, 13, 14, 16) | no | yes | 0 | Dense cockpit; TALK/OPEN mode buttons raw; pipeline row tokenized |
| dictate | 1440 | 640x619 | 13 | 0 | 7 (9, 10, 11, 12, 13, 14, 16) | no | yes | 0 | Stranger sees voice cockpit: level meter, IDLE, pipeline; ~10 content raw btns; CANON BREAK rule A1 (TALK, OPEN not library Button) |
| inspect-activity | 393 | 393x312 | 6 | 0 | 5 (10, 11, 12, 13, 17) | no | yes | 0 | Empty "No activity yet"; gear icon is raw; WATCHING badge good |
| inspect-activity | 1440 | 640x619 | 7 | 0 | 5 (10, 11, 12, 13, 17) | no | yes | 0 | RECORDS tab + FILTER input + "No activity yet" empty; clean |
| inspect-personas-and-coders | 393 | 393x375 | 5 | 0 | 5 (10, 11, 12, 13, 17) | no | yes | 0 | "CREW 0 SESSIONS 0 BLOCKED 0" three bare-text zeros; CANON BREAK rule 8 |
| inspect-personas-and-coders | 1440 | 640x619 | 6 | 0 | 5 (10, 11, 12, 13, 17) | no | yes | 0 | Stranger sees CREW 0 / SESSIONS 0 / BLOCKED 0; three zeros in header; "No sessions" + "No agents" honest but header zeros break rule 8 |
| inspect-processes | 393 | 393x356 | 2 | 0 | 3 (10, 11, 12) | no | yes | 0 | EIGHT bare-text zeros; CANON BREAK rule 8 (WORST OFFENDER) |
| inspect-processes | 1440 | 640x619 | 3 | 0 | 3 (10, 11, 12) | no | yes | 0 | Stranger sees wall of zeros: RUNS 0, NEEDS YOU 0, RUNNING 0, WAITING 0, UNKNOWN 0, RECENTLY ENDED 0, CURSOR 0, RUNS 0; LOUDEST CANON BREAK on the desk |
| open-constitutional-context | 393 | 393x398 | 4 | 0 | 4 (10, 11, 12, 13) | no | yes | 0 | STATUS row + textarea with placeholder examples; clean |
| open-constitutional-context | 1440 | 640x619 | 5 | 0 | 4 (10, 11, 12, 13) | no | yes | 0 | Stranger sees rev/tokens/chars status + one textarea; clean; "rev 0" informational |
| open-people | 393 | 393x224 | 2 | 0 | 1 (12) | no | yes | 0 | ONLY 1 type step; CANON BREAK rule C (need >=3) |
| open-people | 1440 | 640x619 | 3 | 0 | 1 (12) | no | yes | 0 | Stranger sees "Set up People" button + one-liner; ONLY 1 TYPE STEP; most barren face; CANON BREAK rule C |
| open-project-memory | 393 | 393x702 | 7 | 0 | 6 (10, 11, 12, 14, 15, 26) | no | yes | 0 | Room at mobile; "1 need you" headline; GITHUB.COM egress chip present |
| open-project-memory | 1440 | 800x619 | 8 | 0 | 6 (10, 11, 12, 14, 15, 26) | no | yes | 0 | Stranger sees "1 need you" 26px display; best-composed face; 6 type steps; egress chip canon-correct |
| open-workbenches | 393 | 393x257 | 3 | 0 | 3 (12, 13, 17) | no | yes | 0 | "+ Create" + "No workbenches yet"; clean empty state |
| open-workbenches | 1440 | 640x619 | 4 | 0 | 3 (12, 13, 17) | no | yes | 0 | One verb + one empty-state line; clean but sparse; 3 type steps (borderline) |
| project-setup | 393 | 393x403 | 5 | 0 | 4 (10, 11, 12, 13) | no | yes | 0 | Door at mobile; SIGN IN warning chips on sources; compact |
| project-setup | 1440 | 640x580 | 6 | 0 | 4 (10, 11, 12, 13) | no | yes | 0 | Stranger sees name input + two source rows (GitHub, Jira) + SIGN IN warnings; streamlined |
| record-live | 393 | 393x334 | 3 | 0 | 5 (10, 11, 12, 13, 17) | no | yes | 0 | "Start meeting" CTA + empty transcript; clean |
| record-live | 1440 | 640x619 | 4 | 0 | 5 (10, 11, 12, 13, 17) | no | yes | 0 | Stranger sees "Ready to record" + "Start meeting"; "connected ready" status; clean |
| review-calendar-snapshot | 393 | 393x205 | 2 | 1 | 3 (10, 12, 14) | no | yes | 0 | Full sentence on face; CANON BREAK rule A3; no recovery verb |
| review-calendar-snapshot | 1440 | 640x619 | 3 | 1 | 3 (10, 12, 14) | no | yes | 0 | Stranger sees prose error "This review window opened without an import..."; CANON BREAK A3; no verb to fix it |
| review-meetings | 393 | 393x247 | 7 | 0 | 3 (10, 11, 12) | no | yes | 0 | "1 RECORDS" grammar; Import + Record meeting; compact row |
| review-meetings | 1440 | 640x619 | 8 | 0 | 3 (10, 11, 12) | no | yes | 0 | Stranger sees Import/Record verbs + one meeting row; "1 RECORDS" plural (minor); 3 type steps |
