# HS-200-05 walk facts — physical voice, correction and custody

- Generated: 2026-09-07T20:00:31.376572
- Hub: 127.0.0.1:49381
- Mode: READ-ONLY

## Census

| Field | Before | After |
|---|---|---|
| `applied_total` | 0 | None |
| `backend_version` | 0.4.0 | None |
| `correction_keys` | [] | None |
| `corrections_enabled` | True | None |
| `corrections_size` | 0 | None |
| `database_id` | f45cac74169bd16e | None |
| `egress_boundary` | cloud | None |
| `engine_backend` | auto | None |
| `journal_count` | 9 | None |
| `journal_enabled` | True | None |
| `journal_retention` | 500 | None |
| `journal_sources` | {'browser': 8, 'dictation': 1} | None |
| `journal_taught_from` | 0 | None |
| `journal_with_applied` | 0 | None |
| `process_pid` | 13122 | None |
| `process_started_at` | 2026-09-07T20:00:09.561011 | None |
| `ready` | True | None |
| `runtime_detail` | auto: fallback to llama_cpp | None |
| `runtime_status` | available | None |
| `schema_loaded` | 77 | None |

## Decision table

| Beat | Expected | Observed | Write? | Verdict |
|---|---|---|---|---|
| beat 0: corrections_enabled | True (else beat 5 teaches into a silent no-op) | True | none | MATCH |
| beat 0: engine readiness | (a runtime that can hear him) | available / backend=auto / egress=cloud | none | DATA |
| R1 Speak (1440+393) | four wings; well mic-less; Talk present; a named mic phase | 8 facts MATCH | DENIED (Talk / Open mic) | MATCH |
| R2 Journal (1440+393) | his rows only | 2 facts MATCH | DENIED (Clear / Delete / Replay / Export) | MATCH |
| R3 Learned (1440+393) | his rules with honest APPLIED counts | 2 facts MATCH | DENIED (Teach / Forget) | MATCH |

## Face facts

| Face | Field | Expected | Observed | Verdict | Why |
|---|---|---|---|---|---|
| speak@1440 | wings | SPEAK JOURNAL BLOCKS LEARNED | SPEAK JOURNAL BLOCKS LEARNED | MATCH | the four wings of the Speak surface |
| speak@1440 | well_mic_count | 0 | 0 | MATCH | ONE mic authority (Article IV.3): the well carries none |
| speak@1440 | talk_present | >= 1 | 2 | MATCH | `Talk` is the face's one transport (the runner never presses it) |
| speak@1440 | mic_ownership_phase | CLOSED | HELD | OPEN | SEGMENTING | SUSPENDED | CLOSED | MATCH | AC2: the face names who owns the mic, one word |
| journal@1440 | row_sources | HOTKEY / BROWSER / DICTATION | BROWSER, DICTATION, HOTKEY | DATA | AC1: a hotkey dictation leaves a row tagged HOTKEY; the runner adds none |
| learned@1440 | applied_tokens | real firings only | (none) | DATA | AC4: `N APPLIED` counts retained journal rows that named the rule |
| speak@393 | wings | SPEAK JOURNAL BLOCKS LEARNED | SPEAK JOURNAL BLOCKS LEARNED | MATCH | the four wings of the Speak surface |
| speak@393 | well_mic_count | 0 | 0 | MATCH | ONE mic authority (Article IV.3): the well carries none |
| speak@393 | talk_present | >= 1 | 2 | MATCH | `Talk` is the face's one transport (the runner never presses it) |
| speak@393 | mic_ownership_phase | CLOSED | HELD | OPEN | SEGMENTING | SUSPENDED | CLOSED | MATCH | AC2: the face names who owns the mic, one word |
| journal@393 | row_sources | HOTKEY / BROWSER / DICTATION | BROWSER, DICTATION, HOTKEY | DATA | AC1: a hotkey dictation leaves a row tagged HOTKEY; the runner adds none |
| learned@393 | applied_tokens | real firings only | (none) | DATA | AC4: `N APPLIED` counts retained journal rows that named the rule |

## Defects

- (none)

## Surprises

- (none)

## Errors

- (none)
