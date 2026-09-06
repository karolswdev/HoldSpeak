# HS-176-06 walk facts -- The Speak Loop

Generated: 2026-09-06T10:36:34.400861
Hub: 127.0.0.1:49353
Attended: False

## Census

| Field | Before | After |
|-------|--------|-------|
| correction_keys | [] | --- |
| corrections_enabled | True | --- |
| corrections_size | 0 | --- |
| egress_boundary | cloud | --- |
| engine_backend | auto | --- |
| journal_count | 9 | --- |
| journal_enabled | True | --- |
| journal_retention | 500 | --- |
| mic_total | 0 | --- |
| readiness_corrections_enabled | True | --- |
| ready | True | --- |
| runtime_detail | auto: fallback to llama_cpp | --- |
| runtime_status | available | --- |

## Decision table

| Beat | Expected | Observed | WRITE? | Verdict |
|------|----------|----------|--------|---------|
| beat 0: corrections_enabled | True (else the whole loop is a silent no-op) | True | none | MATCH |
| beat 0: engine readiness | (runtime available) | available / backend=auto / egress=cloud | none | DATA |
| R1 Speak (1440+393) | four wings; well mic-less; Talk present | 8 facts, no bounce | none | MATCH |
| R2 Journal (1440+393) | his rows; ALL DICTATION BROWSER HOTKEY; no caption count | 12 facts, no bounce | DENIED (Clear / Delete / Replay) | MATCH |
| R3 Learned (1440+393) | NOTHING LEARNED (rows listed read-only if present) | 4 facts, no bounce | DENIED (Forget) | MATCH |
| R4 Review (1440+393) | crosses to the Journal wing; no Configure door | 4 facts, no bounce | none | MATCH |

## speak@1440

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| wings | SPEAK JOURNAL BLOCKS LEARNED | SPEAK JOURNAL BLOCKS LEARNED | MATCH | the four wings of the Speak surface (design D2(c)) |
| well_mic_count | 0 | 0 | MATCH | ONE mic authority (Article IV.3, ruling R13): the well carries none |
| talk | TALK | TALK | MATCH | the transport is this face's mic authority |
| footer | THIS DEVICE + Review + Export | THIS DEVICE Review Export | DATA | the Speak footer, as found |

## journal@1440

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| filter_tokens | ALL DICTATION BROWSER HOTKEY | ALL DICTATION BROWSER HOTKEY | MATCH | the four source filter tokens (ruling R6: present even when quiet) |
| rows | (his real journal rows) | 9 | DATA | rows rendered on his desk; the runner opens none |
| caption_count | (absent -- the footer's N TODAY is the one count) | (absent) | MATCH | ruling N5b / A.7: the wing carries no caption count |
| guard:clear_journal | DENIED | DENIED (never presses Clear) | MATCH | the runner writes nothing |
| guard:delete_journal_row | DENIED | DENIED (never opens or presses a row's Delete) | MATCH | the runner writes nothing |
| guard:replay_journal_row | DENIED | DENIED (never presses Replay) | MATCH | the runner writes nothing |

## learned@1440

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| empty_state | NOTHING LEARNED | NOTHING LEARNED | MATCH | his desk has taught nothing yet (the expected state before beat 3) |
| guard:forget_correction | DENIED | DENIED (never presses Forget) | MATCH | the runner writes nothing |

## review@1440

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| review_target | the JOURNAL wing (aria-selected=true) | true | MATCH | design D2(b).9: `Review` reviews; it no longer opens the Configure door |
| configure_door | 0 | 0 | MATCH | the Configure door stays the gear's job |

## speak@393

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| wings | SPEAK JOURNAL BLOCKS LEARNED | SPEAK JOURNAL BLOCKS LEARNED | MATCH | the four wings of the Speak surface (design D2(c)) |
| well_mic_count | 0 | 0 | MATCH | ONE mic authority (Article IV.3, ruling R13): the well carries none |
| talk | TALK | TALK | MATCH | the transport is this face's mic authority |
| footer | THIS DEVICE + Review + Export | THIS DEVICE Review Export | DATA | the Speak footer, as found |

## journal@393

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| filter_tokens | ALL DICTATION BROWSER HOTKEY | ALL DICTATION BROWSER HOTKEY | MATCH | the four source filter tokens (ruling R6: present even when quiet) |
| rows | (his real journal rows) | 9 | DATA | rows rendered on his desk; the runner opens none |
| caption_count | (absent -- the footer's N TODAY is the one count) | (absent) | MATCH | ruling N5b / A.7: the wing carries no caption count |
| guard:clear_journal | DENIED | DENIED (never presses Clear) | MATCH | the runner writes nothing |
| guard:delete_journal_row | DENIED | DENIED (never opens or presses a row's Delete) | MATCH | the runner writes nothing |
| guard:replay_journal_row | DENIED | DENIED (never presses Replay) | MATCH | the runner writes nothing |

## learned@393

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| empty_state | NOTHING LEARNED | NOTHING LEARNED | MATCH | his desk has taught nothing yet (the expected state before beat 3) |
| guard:forget_correction | DENIED | DENIED (never presses Forget) | MATCH | the runner writes nothing |

## review@393

| Field | Expected | Observed | Verdict | Why |
|-------|----------|----------|---------|-----|
| review_target | the JOURNAL wing (aria-selected=true) | true | MATCH | design D2(b).9: `Review` reviews; it no longer opens the Configure door |
| configure_door | 0 | 0 | MATCH | the Configure door stays the gear's job |

## Shots

- speak @ 1440: `speak-1440.png`
- journal @ 1440: `journal-1440.png`
- learned @ 1440: `learned-1440.png`
- review @ 1440: `review-1440.png`
- speak @ 393: `speak-393.png`
- journal @ 393: `journal-393.png`
- learned @ 393: `learned-393.png`
- review @ 393: `review-393.png`

## Errors

None.

## Surprises

None.

## Defects

None.

