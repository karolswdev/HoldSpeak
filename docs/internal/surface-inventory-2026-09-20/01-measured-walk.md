# The measured walk — every face, with numbers (2026-09-20)

Rig: `scripts/surface_census_walk.py`. Run at 2026-09-20 16:48:07 -0600.
Repo HEAD `93f9524f`, branch `audit/surface-inventory-2026-09-20`.

Every number here is read from the live product by the browser: `scripts/surface_census_measure.js` runs inside the page against the surface's own element. Rules are `docs/internal/surface-inventory-2026-09-20/00-rulebook.md` section B, plus the section-A counts a script can take honestly (U1/U2/U3/U4/A7) and the door check C3.

**Honesty.** A face this rig could not open is `UNOPENED` with the reason. A measure it cannot take is `NOT ASSESSED` (`null`), never `0`. M11 (spacing rhythm) and M12 (motion) are NOT ASSESSED by this rig — see §6.

## 1. What was walked

| | |
|---|---|
| Desks | cold, rich |
| Widths | 1440, 393 |
| Surfaces in the inventory | 100 |
| Legs walked (surface x desk x width) | 344 |
| Legs MEASURED | 287 |
| Legs UNOPENED | 57 |
| Shots | 287 |

**cold desk seed** — counts: `{}`

**rich desk seed** — counts: `{"engine_assigned": 1, "meetings": 12, "note_words": 2000, "people": 0, "projects": 3, "sources": 32, "thoughts": 5}`

Seeding calls the API refused (6) — the rich desk is poorer than the brief asked, and every face below was measured on what actually landed:

- `POST /api/people/setup -> 503 (people sidecar): {'detail': 'people_store_unavailable'}`
- `POST /api/people/relationships -> 503 (relationship): {'detail': 'people_store_unavailable'}`
- `POST /api/people/relationships -> 503 (relationship): {'detail': 'people_store_unavailable'}`
- `POST /api/people/relationships -> 503 (relationship): {'detail': 'people_store_unavailable'}`
- `POST /api/people/relationships -> 503 (relationship): {'detail': 'people_store_unavailable'}`
- `POST /api/decisions -> 500 (create decision): {'error': "cannot access free variable 'ctx' where it is not associated with a value in enclosing scope"}`

- calendar: sources cleared (PUT /api/settings)
- engine: profile=hs202-lan-engine rev=1 binding=binding-hs202-lan-engine
- speech.transcribe deliberately NOT assigned: the capability admits only `local` boundaries, so a LAN endpoint is refused by the product (holdspeak/inference_capabilities.py:1063) — the Speak face is measured with a real unassigned half.
- meeting states seeded: Quarterly platform architect→RAN (2 h), Kickoff — Küresel Müşteri Po→REC (live), Incident review — ingest sta→CAPTURE FAILED, Roadmap triage→SUMMARY QUEUED, Vendor call — custody→SUMMARY RUNNING, Security review→SUMMARY FAILED, 1:1 — Aleksandra Wiśniewska-→RAN, Architecture guild→RAN, Platform sync→SAVED, Hiring loop debrief→OFF, Quarterly planning→RECOVERABLE, Retro→INTERRUPTED
- desk inventory (per-kind routes; -1 = the route refused, NOT a zero): {"chain": 1, "coder": 0, "decision": 0, "directory": 7, "kb": 2, "meeting": 12, "note": 16, "project": 3, "recipe": 7, "repository": 1, "roadmap": 4, "thread": 1, "workbench": 1, "workflow": 1}
- refs opened by the walk: {"artifact": "artifact:hs202-artifact-9ade7608", "chain": "chain:chain_be4e9818606d", "directory": "directory:dir_26449676258f", "intelligence": "intelligence:desk", "kb": "kb:kb_8dcbd182f083", "meeting": "meeting:hs202-meeting-00", "note": "note:note_584f6829d879", "people": "people:people", "project": "project:proj-2120c22ff56e", "recipe": "recipe:recipe_d0320b62db84", "repository": "repository:src_e79f53ac7d7fd815", "thought_note": "note:note_thought_3f15931d832fd829", "thread": "thread:th_0659b3944c5e", "workbench": "workbench:workbench_a2bf46588a6c", "workflow": "workflow:workflow_2c978751fc0d"}

## 2. Every surface, both widths, both desks

`ovf` = M1 horizontal overflow px (document, or content past its window — the 3px resize-handle affordance every window carries is subtracted; see §4). `cut` = M2 elements with text cut. `out` = M3 verbs outside the window or viewport. `folds` = M4 closed folds. `empty` = M5. `dup` = M6 strings shown twice. `<12px` / `<44px` = M7. `contrast` = M8 failures / assessed. `err` = M9 console + HTTP. `fonts` = M10 distinct stacks. `raw` = U1 raw buttons. `prim` = U4 filled primaries. `0-ctr` = U3. `prose` = A7 sentences. `ms` = M13 open→settled.

### Activity  <sub>`app-activity`</sub>

- Family: application · Door: Go > Activity
- Opened by the rig via: `go:Activity`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3449 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3374 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3409 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3446 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Activity”
- **M7** target 16x14px — “Minimize Activity”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Activity”
- **M7** target 16x14px — “Minimize Activity”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Agents  <sub>`app-agents`</sub>

- Family: application · Door: Dock / Go > Agents
- Opened by the rig via: `go:Agents`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3413 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3360 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3443 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3527 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Agents”
- **M7** target 16x14px — “Minimize Agents”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Agents”
- **M7** target 16x14px — “Minimize Agents”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Ask AI  <sub>`app-ask`</sub>

- Family: application · Door: Dock / Go > Ask AI
- Opened by the rig via: `go:Ask AI`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 1/1 | 0 | 0 | 9 | n/a | 2/20 | 0 | 2 | 5 | 0 | 1 | 0 | 3595 | M4, M7, M8, U1, U3 |
| cold | 393 | ok | 0 | 0 | 0 | 1/1 | 0 | 0 | 9 | 6 | 2/20 | 0 | 2 | 4 | 0 | 1 | 0 | 3452 | M4, M7, M8, U1, U3 |
| rich | 1440 | ok | 0 | 0 | 0 | 1/1 | 0 | 0 | 9 | n/a | 2/20 | 0 | 2 | 5 | 0 | 1 | 0 | 3455 | M4, M7, M8, U1, U3 |
| rich | 393 | ok | 0 | 0 | 0 | 1/1 | 0 | 0 | 9 | 6 | 2/20 | 0 | 2 | 4 | 0 | 1 | 0 | 3565 | M4, M7, M8, U1, U3 |

<details><summary>cold @1440 — evidence</summary>

- **M4** fold “Ground this ask” is closed over: “”
- **M7** 10px — “SESSION · 0 TURNS” `div.desk-pullout-body.desk-ask-body > div.surface-traffic > div.surface-well > div.surface-well-head`
- **M7** 11px — “NO TRAFFIC” `div.surface-traffic > div.surface-well > div.surface-well-body > div.surface-traffic-empty`
- **M7** 9px — “ASK” `div.desk-chat-well > div.desk-chat-composer > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 10px — “GROUNDING” `div#ask > div.desk-pullout-body.desk-ask-body > section.gadget-group > h4.gadget-group-label`
- **M7** 10px — “▤” `details.gadget-fold.desk-ground-fold > summary > span.gadget-fold-glyph > span.desk-ground-glyph`
- **M7** 10px — “Ground this ask” `div.desk-ground > details.gadget-fold.desk-ground-fold > summary > span.gadget-fold-title`
- **M8** 3.5:1 (needs 4.5) rgb(168, 110, 74) on rgb(36, 40, 51) at 16px — “✦”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 9px — “CTX 0.0K/16.4K”
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-mic": 1, "gadget-transport-key": 1}
- **U3** “SESSION · 0 TURNS” `div.desk-pullout-body.desk-ask-body > div.surface-traffic > div.surface-well > div.surface-well-head`

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** fold “Ground this ask” is closed over: “”
- **M7** 10px — “SESSION · 0 TURNS” `div.desk-pullout-body.desk-ask-body > div.surface-traffic > div.surface-well > div.surface-well-head`
- **M7** 11px — “NO TRAFFIC” `div.surface-traffic > div.surface-well > div.surface-well-body > div.surface-traffic-empty`
- **M7** 9px — “ASK” `div.desk-chat-well > div.desk-chat-composer > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 10px — “GROUNDING” `div#ask > div.desk-pullout-body.desk-ask-body > section.gadget-group > h4.gadget-group-label`
- **M7** 10px — “▤” `details.gadget-fold.desk-ground-fold > summary > span.gadget-fold-glyph > span.desk-ground-glyph`
- **M7** 10px — “Ground this ask” `div.desk-ground > details.gadget-fold.desk-ground-fold > summary > span.gadget-fold-title`
- **M7** target 16x14px — “Close Ask AI”
- **M7** target 16x14px — “Minimize Ask AI”
- **M7** target 34x34px — “Speak”
- **M7** target 49x28px — “ASK”
- **M7** target 125x36px — “Choose default”
- **M7** target 58x24px — “Cancel”
- **M8** 3.5:1 (needs 4.5) rgb(168, 110, 74) on rgb(36, 40, 51) at 16px — “✦”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 9px — “CTX 0.0K/16.4K”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-mic": 1, "gadget-transport-key": 1}
- **U3** “SESSION · 0 TURNS” `div.desk-pullout-body.desk-ask-body > div.surface-traffic > div.surface-well > div.surface-well-head`

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** fold “Ground this ask” is closed over: “”
- **M7** 10px — “SESSION · 0 TURNS” `div.desk-pullout-body.desk-ask-body > div.surface-traffic > div.surface-well > div.surface-well-head`
- **M7** 11px — “NO TRAFFIC” `div.surface-traffic > div.surface-well > div.surface-well-body > div.surface-traffic-empty`
- **M7** 9px — “ASK” `div.desk-chat-well > div.desk-chat-composer > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 10px — “GROUNDING” `div#ask > div.desk-pullout-body.desk-ask-body > section.gadget-group > h4.gadget-group-label`
- **M7** 10px — “▤” `details.gadget-fold.desk-ground-fold > summary > span.gadget-fold-glyph > span.desk-ground-glyph`
- **M7** 10px — “Ground this ask” `div.desk-ground > details.gadget-fold.desk-ground-fold > summary > span.gadget-fold-title`
- **M8** 3.5:1 (needs 4.5) rgb(168, 110, 74) on rgb(36, 40, 51) at 16px — “✦”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 9px — “CTX 0.0K/16.4K”
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-mic": 1, "gadget-transport-key": 1}
- **U3** “SESSION · 0 TURNS” `div.desk-pullout-body.desk-ask-body > div.surface-traffic > div.surface-well > div.surface-well-head`

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** fold “Ground this ask” is closed over: “”
- **M7** 10px — “SESSION · 0 TURNS” `div.desk-pullout-body.desk-ask-body > div.surface-traffic > div.surface-well > div.surface-well-head`
- **M7** 11px — “NO TRAFFIC” `div.surface-traffic > div.surface-well > div.surface-well-body > div.surface-traffic-empty`
- **M7** 9px — “ASK” `div.desk-chat-well > div.desk-chat-composer > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 10px — “GROUNDING” `div#ask > div.desk-pullout-body.desk-ask-body > section.gadget-group > h4.gadget-group-label`
- **M7** 10px — “▤” `details.gadget-fold.desk-ground-fold > summary > span.gadget-fold-glyph > span.desk-ground-glyph`
- **M7** 10px — “Ground this ask” `div.desk-ground > details.gadget-fold.desk-ground-fold > summary > span.gadget-fold-title`
- **M7** target 16x14px — “Close Ask AI”
- **M7** target 16x14px — “Minimize Ask AI”
- **M7** target 34x34px — “Speak”
- **M7** target 49x28px — “ASK”
- **M7** target 125x36px — “Choose default”
- **M7** target 58x24px — “Cancel”
- **M8** 3.5:1 (needs 4.5) rgb(168, 110, 74) on rgb(36, 40, 51) at 16px — “✦”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 9px — “CTX 0.0K/16.4K”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-mic": 1, "gadget-transport-key": 1}
- **U3** “SESSION · 0 TURNS” `div.desk-pullout-body.desk-ask-body > div.surface-traffic > div.surface-well > div.surface-well-head`

</details>

### Calendar snapshot  <sub>`app-calendar-snapshot`</sub>

- Family: application · Door: NO DOOR: opened only by dropping an .ics on the desk (GlassDropLayer.tsx:68); it needs a dropped-file payload as its scope, which this rig does not forge
- Opened by the rig via: `unopenable`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### The Chair (home)  <sub>`app-chair`</sub>

- Family: application · Door: arrival
- Opened by the rig via: `chair`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 1/13 | 0 | 3 | 1 | 0 | 0 | 0 | 4949 | M10, M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 6 | 1/13 | 0 | 3 | 1 | 0 | 0 | 0 | 3037 | M10, M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 46 | 0/0 | 0 | 0 | 174 | n/a | 3/220 | 0 | 3 | 1 | 2 | 0 | 0 | 3052 | M10, M3, M7, M8, U1, U4 |
| rich | 393 | ok | 0 | 0 | 55 | 0/0 | 0 | 0 | 174 | 40 | 3/220 | 0 | 3 | 1 | 2 | 0 | 0 | 2971 | M10, M3, M7, M8, U1, U4 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 11px — “Connect calendar” `div.arrival-headline > div.arrival-head-tokens > span.arrival-next > button.btn.btn--ghost`
- **M7** 10px — “SETUP” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Choose an engine” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M7** 10px — “BRIEF” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Generate” `div > section.surface-section > header.surface-section-head > button.btn.btn--ghost`
- **M7** 9px — “Talk” `footer.arrival-capture-bar > span.arrival-capture-talk > button.desk-mic.gadget-transport-key > span.gadget-transport-word`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (11); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (1)
- **U1** 1 raw buttons vs 6 library — {"desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 11px — “Connect calendar” `div.arrival-headline > div.arrival-head-tokens > span.arrival-next > button.btn.btn--ghost`
- **M7** 10px — “SETUP” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Choose an engine” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M7** 10px — “BRIEF” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Generate” `div > section.surface-section > header.surface-section-head > button.btn.btn--ghost`
- **M7** 9px — “Talk” `footer.arrival-capture-bar > span.arrival-capture-talk > button.desk-mic.gadget-transport-key > span.gadget-transport-word`
- **M7** target 124x24px — “Connect calendar”
- **M7** target 124x24px — “Choose an engine”
- **M7** target 71x24px — “Generate”
- **M7** target 134x28px — “Write a thought”
- **M7** target 127x28px — “Record meeting”
- **M7** target 84x28px — “Schedule”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (11); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (1)
- **U1** 1 raw buttons vs 6 library — {"desk-mic": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M3** verb “SRCgithub acme-platform/service-15●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “SRCgithub acme-platform/service-16●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-16” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M3** verb “SRCgithub acme-platform/service-17●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-17” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M3** verb “SRCgithub acme-platform/service-18●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M7** 11px — “Connect calendar” `div.arrival-headline > div.arrival-head-tokens > span.arrival-next > button.btn.btn--ghost`
- **M7** 10px — “COVERAGE · 9 OF 40” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “SRC” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-lead > span.arrival-source-emblem.surface-coverage-emblem`
- **M7** 10px — “CANT CHECK” `li.surface-ledger-row > div.surface-ledger-line > span.surface-coverage-meta > span.surface-state-chip.surface-coverage-token`
- **M7** 11px — “●” `div.surface-ledger-line > span.surface-coverage-meta > span.surface-state-chip.surface-coverage-token > span.surface-state-chip-icon`
- **M7** 10px — “NEVER OBSERVED” `li.surface-ledger-row > div.surface-ledger-line > span.surface-coverage-meta > span.surface-coverage-observed`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Continue”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Run summary”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (182); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (37); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 1 raw buttons vs 40 library — {"desk-mic": 1}
- **U4** filled primaries: “Continue”, “Run summary”

</details>

<details><summary>rich @393 — evidence</summary>

- **M3** verb “SRCgithub acme-platform/service-09●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-09” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M3** verb “SRCgithub acme-platform/service-10●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-10” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M3** verb “SRCgithub acme-platform/service-11●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-11” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M7** 11px — “Connect calendar” `div.arrival-headline > div.arrival-head-tokens > span.arrival-next > button.btn.btn--ghost`
- **M7** 10px — “COVERAGE · 9 OF 40” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “SRC” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-lead > span.arrival-source-emblem.surface-coverage-emblem`
- **M7** 10px — “CANT CHECK” `li.surface-ledger-row > div.surface-ledger-line > span.surface-coverage-meta > span.surface-state-chip.surface-coverage-token`
- **M7** 11px — “●” `div.surface-ledger-line > span.surface-coverage-meta > span.surface-state-chip.surface-coverage-token > span.surface-state-chip-icon`
- **M7** 10px — “NEVER OBSERVED” `li.surface-ledger-row > div.surface-ledger-line > span.surface-coverage-meta > span.surface-coverage-observed`
- **M7** target 124x24px — “Connect calendar”
- **M7** target 77x24px — “Reconnect: github acme-platform/service-…”
- **M7** target 77x24px — “Reconnect: github acme-platform/service-…”
- **M7** target 77x24px — “Reconnect: github acme-platform/service-…”
- **M7** target 77x24px — “Reconnect: github acme-platform/service-…”
- **M7** target 77x24px — “Reconnect: github acme-platform/service-…”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Continue”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Run summary”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (182); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (37); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 1 raw buttons vs 40 library — {"desk-mic": 1}
- **U4** filled primaries: “Continue”, “Run summary”

</details>

### Commands  <sub>`app-commands`</sub>

- Family: application · Door: Go > Commands
- Opened by the rig via: `go:Commands`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3465 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3349 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3433 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3430 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Commands”
- **M7** target 16x14px — “Minimize Commands”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Commands”
- **M7** target 16x14px — “Minimize Commands”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Components  <sub>`app-components`</sub>

- Family: application · Door: NO DOOR: no Go row; a designer's route
- Opened by the rig via: `route:/design/components`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 231+2in | 2 | 29 | 1/1 | 1 | 2 | 134 | n/a | 26/204 | 0 | 3 | 33 | 2 | 0 | 0 | 2904 | C3, M1, M10, M2, M3, M4, M5, M6, M7, M8, U1, U4 |
| cold | 393 | ok | 355+3in | 3 | 30 | 1/1 | 1 | 2 | 134 | 41 | 26/204 | 0 | 3 | 32 | 2 | 0 | 0 | 2910 | C3, M1, M10, M2, M3, M4, M5, M6, M7, M8, U1, U4 |
| rich | 1440 | ok | 231+2in | 2 | 29 | 1/1 | 1 | 2 | 134 | n/a | 26/204 | 0 | 3 | 33 | 2 | 0 | 0 | 2935 | C3, M1, M10, M2, M3, M4, M5, M6, M7, M8, U1, U4 |
| rich | 393 | ok | 355+3in | 3 | 30 | 1/1 | 1 | 2 | 134 | 41 | 26/204 | 0 | 3 | 32 | 2 | 0 | 0 | 2916 | C3, M1, M10, M2, M3, M4, M5, M6, M7, M8, U1, U4 |

<details><summary>cold @1440 — evidence</summary>

- **M1** content overflows its window by 231px — widest child `div.surface-topology > div.surface-topology-map-area > div.surface-topology-viewport > svg` “”
- **M1 (inner)** `div.desk-surface-body > section.surface-section > div.surface-progress-plan > div.sr-only` overflows by 114px — “Download weights”
- **M1 (inner)** `div.desk-surface-body > section.surface-section > div.surface-topology > div.surface-topology-map-area` overflows by 246px — “Chat & agents, SummariesTranslation*This Mac✓MLX, llama.cppLAN Server✓…”
- **M2** `div.desk-surface-body > section.surface-section > div.surface-progress-plan > div.sr-only` hides 114px on x — “Download weights”
- **M2** `div.desk-surface-body > section.surface-section > div.surface-topology > div.surface-topology-map-area` hides 246px on x — “Chat & agents, SummariesTranslation*This Mac✓MLX, llama.cppLAN Server✓qwen3.6-35bCloud API—”
- **M3** verb “Outcomes” is outside its viewport — `div > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M3** verb “Record” is outside its viewport — `div > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M3** verb “Configure” is outside its viewport — `section.surface-section > div > span.desk-wings > button.desk-wing.desk-wing-door`
- **M3** verb “Delete row 1” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Delete row 2” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “+ ADD” is outside its viewport — `div.desk-surface-body > section.surface-section > div.gadget-table > button.gadget-table-add`
- **M4** fold “RAW · SPECIMEN” is closed over: “Quiet row, caret, trailing tokendetails semantics, keyboard-free”
- **M4** tab bar `div.desk-surface-body > section.surface-section > div > span.desk-wings`: Outcomes, Record, ⚙︎
- **M4** tab bar `section.surface-section > div > span.desk-wings > span.desk-wings-tabs`: Outcomes, Record
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M6** “Download weights” appears 2x
- **M6** “Local” appears 2x
- **M7** 11px — “Primary verb” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--primary`
- **M7** 10px — “Buttons and verbs” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Dense action” `div.desk-surface-body > section.surface-section > div.surface-actions > button.btn.btn--secondary`
- **M7** 9px — “TALK” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 9px — “STOP” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 9px — “KILL” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M8** 2.97:1 (needs 4.5) rgb(242, 243, 245) on rgb(188, 128, 88) at 11px — “Primary verb”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Primary”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 16px — “■”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “STOP”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 10px — “Apply”
- **M8** 3.86:1 (needs 4.5) rgb(118, 126, 141) on rgb(33, 35, 40) at 12px — “Loading”
- **M8** 3.86:1 (needs 4.5) rgb(118, 126, 141) on rgb(33, 35, 40) at 12px — “Disabled”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “Size”
- **M8** 5 text leaves NOT ASSESSED (painted over an image or gradient)
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (179); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (27); Arial (3)
- **U1** 33 raw buttons vs 12 library — {"desk-light": 3, "gadget-transport-key": 4, "desk-mic": 2, "(no class)": 2, "desk-wing": 3, "gadget-table-add": 1, "surface-row-open": 1, "surface-action-notice-btn": 2, "surface-disclosure-trigger": 6, "surface-plan-action-btn": 2, "surface-choice-confirm-btn": 1, "signal-btn": 1, "surface-provenance-inspect": 1, "surface-receipt-inspect": 1, "surface-topology-node": 3}
- **U4** filled primaries: “Primary verb”, “Primary”

</details>

<details><summary>cold @393 — evidence</summary>

- **M1** content overflows its window by 355px — widest child `div.surface-topology > div.surface-topology-map-area > div.surface-topology-viewport > svg` “”
- **M1 (inner)** `div.surface-row-line > span.surface-row-main > span.surface-row-text > small` overflows by 50px — “title + meaningful detail; unknowns omitted”
- **M1 (inner)** `div.desk-surface-body > section.surface-section > div.surface-progress-plan > div.sr-only` overflows by 114px — “Download weights”
- **M1 (inner)** `div.desk-surface-body > section.surface-section > div.surface-topology > div.surface-topology-map-area` overflows by 370px — “Chat & agents, SummariesTranslation*This Mac✓MLX, llama.cppLAN Server✓…”
- **M2** `div.surface-row-line > span.surface-row-main > span.surface-row-text > small` hides 50px on x — “title + meaningful detail; unknowns omitted”
- **M2** `div.desk-surface-body > section.surface-section > div.surface-progress-plan > div.sr-only` hides 114px on x — “Download weights”
- **M2** `div.desk-surface-body > section.surface-section > div.surface-topology > div.surface-topology-map-area` hides 370px on x — “Chat & agents, SummariesTranslation*This Mac✓MLX, llama.cppLAN Server✓qwen3.6-35bCloud API—”
- **M3** verb “Decrease Gallery number” is outside its viewport — `span.gadget-row-gadget > span.gadget-string.gadget-stepper > span.gadget-arrows > button`
- **M3** verb “Outcomes” is outside its viewport — `div > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M3** verb “Record” is outside its viewport — `div > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M3** verb “Configure” is outside its viewport — `section.surface-section > div > span.desk-wings > button.desk-wing.desk-wing-door`
- **M3** verb “Delete row 1” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Delete row 2” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M4** fold “RAW · SPECIMEN” is closed over: “Quiet row, caret, trailing tokendetails semantics, keyboard-free”
- **M4** tab bar `div.desk-surface-body > section.surface-section > div > span.desk-wings`: Outcomes, Record, ⚙︎
- **M4** tab bar `section.surface-section > div > span.desk-wings > span.desk-wings-tabs`: Outcomes, Record
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M6** “Download weights” appears 2x
- **M6** “Local” appears 2x
- **M7** 11px — “Primary verb” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--primary`
- **M7** 10px — “Buttons and verbs” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Dense action” `div.desk-surface-body > section.surface-section > div.surface-actions > button.btn.btn--secondary`
- **M7** 9px — “TALK” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 9px — “STOP” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 9px — “KILL” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** target 16x14px — “Close Components”
- **M7** target 16x14px — “Minimize Components”
- **M7** target 97x24px — “Primary verb”
- **M7** target 76x28px — “Primary”
- **M7** target 91x28px — “Secondary”
- **M7** target 62x28px — “Ghost”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Primary verb”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Primary”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 16px — “■”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “STOP”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 10px — “Apply”
- **M8** 3.86:1 (needs 4.5) rgb(118, 126, 141) on rgb(33, 35, 40) at 12px — “Loading”
- **M8** 3.86:1 (needs 4.5) rgb(118, 126, 141) on rgb(33, 35, 40) at 12px — “Disabled”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “Size”
- **M8** 5 text leaves NOT ASSESSED (painted over an image or gradient)
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (179); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (27); Arial (3)
- **U1** 32 raw buttons vs 12 library — {"desk-light": 2, "gadget-transport-key": 4, "desk-mic": 2, "(no class)": 2, "desk-wing": 3, "gadget-table-add": 1, "surface-row-open": 1, "surface-action-notice-btn": 2, "surface-disclosure-trigger": 6, "surface-plan-action-btn": 2, "surface-choice-confirm-btn": 1, "signal-btn": 1, "surface-provenance-inspect": 1, "surface-receipt-inspect": 1, "surface-topology-node": 3}
- **U4** filled primaries: “Primary verb”, “Primary”

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 231px — widest child `div.surface-topology > div.surface-topology-map-area > div.surface-topology-viewport > svg` “”
- **M1 (inner)** `div.desk-surface-body > section.surface-section > div.surface-progress-plan > div.sr-only` overflows by 114px — “Download weights”
- **M1 (inner)** `div.desk-surface-body > section.surface-section > div.surface-topology > div.surface-topology-map-area` overflows by 246px — “Chat & agents, SummariesTranslation*This Mac✓MLX, llama.cppLAN Server✓…”
- **M2** `div.desk-surface-body > section.surface-section > div.surface-progress-plan > div.sr-only` hides 114px on x — “Download weights”
- **M2** `div.desk-surface-body > section.surface-section > div.surface-topology > div.surface-topology-map-area` hides 246px on x — “Chat & agents, SummariesTranslation*This Mac✓MLX, llama.cppLAN Server✓qwen3.6-35bCloud API—”
- **M3** verb “Outcomes” is outside its viewport — `div > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M3** verb “Record” is outside its viewport — `div > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M3** verb “Configure” is outside its viewport — `section.surface-section > div > span.desk-wings > button.desk-wing.desk-wing-door`
- **M3** verb “Delete row 1” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Delete row 2” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “+ ADD” is outside its viewport — `div.desk-surface-body > section.surface-section > div.gadget-table > button.gadget-table-add`
- **M4** fold “RAW · SPECIMEN” is closed over: “Quiet row, caret, trailing tokendetails semantics, keyboard-free”
- **M4** tab bar `div.desk-surface-body > section.surface-section > div > span.desk-wings`: Outcomes, Record, ⚙︎
- **M4** tab bar `section.surface-section > div > span.desk-wings > span.desk-wings-tabs`: Outcomes, Record
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M6** “Download weights” appears 2x
- **M6** “Local” appears 2x
- **M7** 11px — “Primary verb” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--primary`
- **M7** 10px — “Buttons and verbs” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Dense action” `div.desk-surface-body > section.surface-section > div.surface-actions > button.btn.btn--secondary`
- **M7** 9px — “TALK” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 9px — “STOP” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 9px — “KILL” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M8** 2.97:1 (needs 4.5) rgb(242, 243, 245) on rgb(188, 128, 88) at 11px — “Primary verb”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Primary”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 16px — “■”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “STOP”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 10px — “Apply”
- **M8** 3.86:1 (needs 4.5) rgb(118, 126, 141) on rgb(33, 35, 40) at 12px — “Loading”
- **M8** 3.86:1 (needs 4.5) rgb(118, 126, 141) on rgb(33, 35, 40) at 12px — “Disabled”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “Size”
- **M8** 5 text leaves NOT ASSESSED (painted over an image or gradient)
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (179); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (27); Arial (3)
- **U1** 33 raw buttons vs 12 library — {"desk-light": 3, "gadget-transport-key": 4, "desk-mic": 2, "(no class)": 2, "desk-wing": 3, "gadget-table-add": 1, "surface-row-open": 1, "surface-action-notice-btn": 2, "surface-disclosure-trigger": 6, "surface-plan-action-btn": 2, "surface-choice-confirm-btn": 1, "signal-btn": 1, "surface-provenance-inspect": 1, "surface-receipt-inspect": 1, "surface-topology-node": 3}
- **U4** filled primaries: “Primary verb”, “Primary”

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 355px — widest child `div.surface-topology > div.surface-topology-map-area > div.surface-topology-viewport > svg` “”
- **M1 (inner)** `div.surface-row-line > span.surface-row-main > span.surface-row-text > small` overflows by 50px — “title + meaningful detail; unknowns omitted”
- **M1 (inner)** `div.desk-surface-body > section.surface-section > div.surface-progress-plan > div.sr-only` overflows by 114px — “Download weights”
- **M1 (inner)** `div.desk-surface-body > section.surface-section > div.surface-topology > div.surface-topology-map-area` overflows by 370px — “Chat & agents, SummariesTranslation*This Mac✓MLX, llama.cppLAN Server✓…”
- **M2** `div.surface-row-line > span.surface-row-main > span.surface-row-text > small` hides 50px on x — “title + meaningful detail; unknowns omitted”
- **M2** `div.desk-surface-body > section.surface-section > div.surface-progress-plan > div.sr-only` hides 114px on x — “Download weights”
- **M2** `div.desk-surface-body > section.surface-section > div.surface-topology > div.surface-topology-map-area` hides 370px on x — “Chat & agents, SummariesTranslation*This Mac✓MLX, llama.cppLAN Server✓qwen3.6-35bCloud API—”
- **M3** verb “Decrease Gallery number” is outside its viewport — `span.gadget-row-gadget > span.gadget-string.gadget-stepper > span.gadget-arrows > button`
- **M3** verb “Outcomes” is outside its viewport — `div > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M3** verb “Record” is outside its viewport — `div > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M3** verb “Configure” is outside its viewport — `section.surface-section > div > span.desk-wings > button.desk-wing.desk-wing-door`
- **M3** verb “Delete row 1” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Delete row 2” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M4** fold “RAW · SPECIMEN” is closed over: “Quiet row, caret, trailing tokendetails semantics, keyboard-free”
- **M4** tab bar `div.desk-surface-body > section.surface-section > div > span.desk-wings`: Outcomes, Record, ⚙︎
- **M4** tab bar `section.surface-section > div > span.desk-wings > span.desk-wings-tabs`: Outcomes, Record
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M6** “Download weights” appears 2x
- **M6** “Local” appears 2x
- **M7** 11px — “Primary verb” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--primary`
- **M7** 10px — “Buttons and verbs” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Dense action” `div.desk-surface-body > section.surface-section > div.surface-actions > button.btn.btn--secondary`
- **M7** 9px — “TALK” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 9px — “STOP” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 9px — “KILL” `section.surface-section > span.gadget-transport-row > button.gadget-transport-key > span.gadget-transport-word`
- **M7** target 16x14px — “Close Components”
- **M7** target 16x14px — “Minimize Components”
- **M7** target 97x24px — “Primary verb”
- **M7** target 76x28px — “Primary”
- **M7** target 91x28px — “Secondary”
- **M7** target 62x28px — “Ghost”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Primary verb”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Primary”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 16px — “■”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “STOP”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 10px — “Apply”
- **M8** 3.86:1 (needs 4.5) rgb(118, 126, 141) on rgb(33, 35, 40) at 12px — “Loading”
- **M8** 3.86:1 (needs 4.5) rgb(118, 126, 141) on rgb(33, 35, 40) at 12px — “Disabled”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “Size”
- **M8** 5 text leaves NOT ASSESSED (painted over an image or gradient)
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (179); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (27); Arial (3)
- **U1** 32 raw buttons vs 12 library — {"desk-light": 2, "gadget-transport-key": 4, "desk-mic": 2, "(no class)": 2, "desk-wing": 3, "gadget-table-add": 1, "surface-row-open": 1, "surface-action-notice-btn": 2, "surface-disclosure-trigger": 6, "surface-plan-action-btn": 2, "surface-choice-confirm-btn": 1, "signal-btn": 1, "surface-provenance-inspect": 1, "surface-receipt-inspect": 1, "surface-topology-node": 3}
- **U4** filled primaries: “Primary verb”, “Primary”

</details>

### Connections  <sub>`app-connections`</sub>

- Family: application · Door: Go > Connections
- Opened by the rig via: `go:Connections`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3386 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3402 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3521 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3465 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Context  <sub>`app-context`</sub>

- Family: application · Door: Go > Context
- Opened by the rig via: `go:Context`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3463 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3410 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3443 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3460 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Context”
- **M7** target 16x14px — “Minimize Context”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Context”
- **M7** target 16x14px — “Minimize Context”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Desk memory  <sub>`app-desk-memory`</sub>

- Family: application · Door: Go > Desk memory
- Opened by the rig via: `go:Desk memory`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3572 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3419 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3494 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3422 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Desk memory”
- **M7** target 16x14px — “Minimize Desk memory”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Desk memory”
- **M7** target 16x14px — “Minimize Desk memory”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### The Floor  <sub>`app-floor`</sub>

- Family: application · Door: Dock ▧ / Desk menu
- Opened by the rig via: `custom:floor`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0+18in | 17 | 0 | 0/0 | 0 | 0 | 1 | n/a | 0/44 | 0 | 3 | 36 | 0 | 0 | 0 | 6578 | M1, M10, M2, M7, U1 |
| cold | 393 | ok | 410+7in | 7 | 19 | 0/0 | 0 | 6 | 63 | 43 | 18/115 | 0 | 3 | 19 | 0 | 1 | 0 | 6186 | M1, M10, M2, M3, M6, M7, M8, U1, U3 |
| rich | 1440 | ok | 0+40in | 42 | 0 | 0/0 | 0 | 0 | 1 | n/a | 1/71 | 0 | 3 | 61 | 0 | 0 | 0 | 7037 | M1, M10, M2, M7, M8, U1 |
| rich | 393 | ok | 694+17in | 17 | 53 | 0/0 | 0 | 15 | 139 | 73 | 51/232 | 0 | 3 | 19 | 0 | 2 | 0 | 6237 | M1, M10, M2, M3, M6, M7, M8, U1, U3 |

<details><summary>cold @1440 — evidence</summary>

- **M1 (inner)** `main#main > div#desk-next > div.desk-world > div.desk-world-a11y` overflows by 11px — “DecisionsInboxMeetingsPersonalReferenceWorkWeekly update1:1 prepEffect…”
- **M1 (inner)** `div#desk-next > div.desk-world > div.desk-world-a11y > button` overflows by 65px — “Decisions”
- **M1 (inner)** `div#desk-next > div.desk-world > div.desk-world-a11y > button` overflows by 36px — “Inbox”
- **M1 (inner)** `div#desk-next > div.desk-world > div.desk-world-a11y > button` overflows by 61px — “Meetings”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 65px on x — “Decisions”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 36px on x — “Inbox”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 61px on x — “Meetings”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 58px on x — “Personal”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 68px on x — “Reference”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 35px on x — “Work”
- **M7** 10px — “⌘K” `div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-chip.desk-tools-launch > kbd`
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (17); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (14); Arial (13)
- **U1** 36 raw buttons vs 2 library — {"desk-mark": 1, "desk-verbbar-title": 4, "gadget-chip": 1, "desk-bell": 1, "desk-chip": 1, "desk-mic": 1, "(no class)": 17, "desk-dock-launch": 9, "desk-orb": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M1** content overflows its window by 410px — widest child `main#main > div#desk-next > div.desk-dock > div.desk-orb-wrap` “”
- **M1 (inner)** `div#desk-next > div.desk-listmode > section.desk-list-face > h2#desk-list-title` overflows by 111px — “Desk items”
- **M1 (inner)** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` overflows by 69px — “PERSONAL”
- **M1 (inner)** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` overflows by 40px — “WORK”
- **M1 (inner)** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` overflows by 69px — “PERSONAL”
- **M2** `div#desk-next > div.desk-listmode > section.desk-list-face > h2#desk-list-title` hides 111px on x — “Desk items”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 69px on x — “PERSONAL”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 40px on x — “WORK”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 69px on x — “PERSONAL”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 67px on x — “MEETINGS”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 75px on x — “REFERENCE”
- **M3** verb “Desk memory” is outside its viewport — `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-bell`
- **M3** verb “Search ⌘K” is outside its viewport — `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-chip.desk-tools-launch`
- **M3** verb “Attention” is outside its viewport — `thead > tr > th > button.desk-sortable-table-sort`
- **M3** verb “Chase” is outside its viewport — `tbody > tr.desk-sortable-table-row > td > button.btn.btn--ghost`
- **M3** verb “Desk” is outside its viewport — `tbody > tr.desk-sortable-table-row > td > button.btn.btn--ghost`
- **M3** verb “Draft” is outside its viewport — `tbody > tr.desk-sortable-table-row > td > button.btn.btn--ghost`
- **M6** “NOTE” appears 10x
- **M6** “ZONE” appears 6x
- **M6** “AGENT” appears 6x
- **M6** “1 ITEM” appears 4x
- **M6** “PERSONAL” appears 2x
- **M6** “KNOWLEDGE” appears 2x
- **M7** 10px — “17 ITEMS · 6 ZONES” `div.desk-listmode > section.desk-list-face > div.desk-list-census > span`
- **M7** 10px — “17 SHOWNS of 17” `div.desk-listmode > section.desk-list-face > div.desk-list-census > p.desk-list-status`
- **M7** 10px — “Name” `thead > tr > th > button.desk-sortable-table-sort.is-current`
- **M7** 10px — “↑” `tr > th > button.desk-sortable-table-sort.is-current > span.desk-sortable-table-direction`
- **M7** 10px — “Kind” `thead > tr > th > button.desk-sortable-table-sort`
- **M7** 10px — “Zone” `thead > tr > th > button.desk-sortable-table-sort`
- **M7** target 106x22px — “HoldSpeak”
- **M7** target 31x26px — “Go”
- **M7** target 133x24px — “Privacy and trust: ⌂ This device”
- **M7** target 34x22px — “Desk memory”
- **M7** target 88x24px — “Search ⌘K”
- **M7** target 40x13px — “Name ↑”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “↑”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (72); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (30); Arial (13)
- **U1** 19 raw buttons vs 25 library — {"desk-mark": 1, "desk-verbbar-title": 1, "gadget-chip": 1, "desk-bell": 1, "desk-chip": 1, "desk-sortable-table-sort": 4, "desk-dock-launch": 9, "desk-orb": 1}
- **U3** “0 ITEMS” `table.desk-sortable-table > tbody > tr.desk-sortable-table-row > td`

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1 (inner)** `main#main > div#desk-next > div.desk-world > div.desk-world-a11y` overflows by 11px — “DecisionsInboxMeetingsPersonalPlatform — çalışma zoneReferenceWorkKick…”
- **M1 (inner)** `div#desk-next > div.desk-world > div.desk-world-a11y > button` overflows by 65px — “Decisions”
- **M1 (inner)** `div#desk-next > div.desk-world > div.desk-world-a11y > button` overflows by 36px — “Inbox”
- **M1 (inner)** `div#desk-next > div.desk-world > div.desk-world-a11y > button` overflows by 61px — “Meetings”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 65px on x — “Decisions”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 36px on x — “Inbox”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 61px on x — “Meetings”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 58px on x — “Personal”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 164px on x — “Platform — çalışma zone”
- **M2** `div#desk-next > div.desk-world > div.desk-world-a11y > button` hides 68px on x — “Reference”
- **M7** 10px — “⌘K” `div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-chip.desk-tools-launch > kbd`
- **M8** 4.2:1 (needs 4.5) rgb(255, 255, 255) on rgb(168, 110, 74) at 12px — “3”
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (42); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (15); Arial (14)
- **U1** 61 raw buttons vs 2 library — {"desk-mark": 1, "desk-verbbar-title": 4, "gadget-chip": 1, "desk-bell": 1, "desk-chip": 1, "desk-mic": 1, "(no class)": 42, "desk-dock-launch": 9, "desk-orb": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 694px — widest child `div.desk-listmode > section.desk-list-face > div.desk-sortable-table-wrap.desk-list-sortable > table.desk-sortable-table` “Name ↑KindZoneAttentionZONESDecisionsZONE0 ITEMSInboxZONE7 ITEMSMeetin…”
- **M1 (inner)** `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tl > button.gadget-chip.gadget-chip-egress` overflows by 96px — “→ External reach enabled”
- **M1 (inner)** `div#desk-next > div.desk-listmode > section.desk-list-face > h2#desk-list-title` overflows by 111px — “Desk items”
- **M1 (inner)** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` overflows by 43px — “ATTN 1”
- **M1 (inner)** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` overflows by 43px — “ATTN 1”
- **M2** `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tl > button.gadget-chip.gadget-chip-egress` hides 96px on x — “→ External reach enabled”
- **M2** `div#desk-next > div.desk-listmode > section.desk-list-face > h2#desk-list-title` hides 111px on x — “Desk items”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 43px on x — “ATTN 1”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 43px on x — “ATTN 1”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 69px on x — “PERSONAL”
- **M2** `tr.desk-sortable-table-row > td > button.btn.btn--ghost > span.sr-only` hides 40px on x — “WORK”
- **M3** verb “Desk memory: 3 need attention” is outside its viewport — `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-bell`
- **M3** verb “Search ⌘K” is outside its viewport — `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-chip.desk-tools-launch`
- **M3** verb “Kind” is outside its viewport — `thead > tr > th > button.desk-sortable-table-sort`
- **M3** verb “Zone” is outside its viewport — `thead > tr > th > button.desk-sortable-table-sort`
- **M3** verb “Attention” is outside its viewport — `thead > tr > th > button.desk-sortable-table-sort`
- **M3** verb “Quarterly platform architecture review — migration…” is outside its viewport — `tbody > tr.desk-sortable-table-row > td > button.btn.btn--ghost`
- **M6** “NOTE” appears 16x
- **M6** “MEETING” appears 12x
- **M6** “ZONE” appears 7x
- **M6** “INBOX” appears 7x
- **M6** “AGENT” appears 7x
- **M6** “1 ITEM” appears 3x
- **M7** 10px — “46 ITEMS · 7 ZONES · 3 ATTNS” `div.desk-listmode > section.desk-list-face > div.desk-list-census > span`
- **M7** 10px — “46 SHOWNS of 46” `div.desk-listmode > section.desk-list-face > div.desk-list-census > p.desk-list-status`
- **M7** 10px — “Name” `thead > tr > th > button.desk-sortable-table-sort.is-current`
- **M7** 10px — “↑” `tr > th > button.desk-sortable-table-sort.is-current > span.desk-sortable-table-direction`
- **M7** 10px — “Kind” `thead > tr > th > button.desk-sortable-table-sort`
- **M7** 10px — “Zone” `thead > tr > th > button.desk-sortable-table-sort`
- **M7** target 106x22px — “HoldSpeak”
- **M7** target 31x26px — “Go”
- **M7** target 134x24px — “Privacy and trust: → External reach enab…”
- **M7** target 55x22px — “Desk memory: 3 need attention”
- **M7** target 88x24px — “Search ⌘K”
- **M7** target 40x13px — “Name ↑”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “↑”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “ATTN 1”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “ATTN 1”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “ATTN 1”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “[ ]”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (149); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (69); Arial (14)
- **U1** 19 raw buttons vs 55 library — {"desk-mark": 1, "desk-verbbar-title": 1, "gadget-chip": 1, "desk-bell": 1, "desk-chip": 1, "desk-sortable-table-sort": 4, "desk-dock-launch": 9, "desk-orb": 1}
- **U3** “0 ITEMS” `table.desk-sortable-table > tbody > tr.desk-sortable-table-row > td`
- **U3** “0 ITEMS” `table.desk-sortable-table > tbody > tr.desk-sortable-table-row > td`

</details>

### Intelligence  <sub>`app-intelligence`</sub>

- Family: application · Door: Dock ◈
- Opened by the rig via: `custom:intelligence`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 3/10 | 0 | 3 | 7 | 0 | 0 | 0 | 3608 | M10, M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 9 | 3/10 | 0 | 3 | 6 | 0 | 0 | 0 | 3542 | M10, M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 3/10 | 0 | 3 | 7 | 0 | 0 | 0 | 3543 | M10, M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 9 | 3/10 | 0 | 3 | 6 | 0 | 0 | 0 | 3612 | M10, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Acknowledge” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** 11px — “Defer” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** 11px — “Speak” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Acknowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Defer”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Speak”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (7); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); Arial (1)
- **U1** 7 raw buttons vs 3 library — {"desk-light": 3, "intelligence-segment": 3, "desk-chip": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Acknowledge” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** 11px — “Defer” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** 11px — “Speak” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **M7** target 80x27px — “Generate”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Acknowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Defer”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Speak”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (7); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); Arial (1)
- **U1** 6 raw buttons vs 3 library — {"desk-light": 2, "intelligence-segment": 3, "desk-chip": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Acknowledge” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** 11px — “Defer” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** 11px — “Speak” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Acknowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Defer”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Speak”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (7); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); Arial (1)
- **U1** 7 raw buttons vs 3 library — {"desk-light": 3, "intelligence-segment": 3, "desk-chip": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Acknowledge” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** 11px — “Defer” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** 11px — “Speak” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **M7** target 80x27px — “Generate”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Acknowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Defer”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Speak”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (7); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); Arial (1)
- **U1** 6 raw buttons vs 3 library — {"desk-light": 2, "intelligence-segment": 3, "desk-chip": 1}

</details>

### Live meeting  <sub>`app-live`</sub>

- Family: application · Door: NO DOOR: no Go row; reached only from a Record verb (RecordOrb.tsx:69)
- Opened by the rig via: `route:/live`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | n/a | 1/10 | 0 | 2 | 4 | 1 | 0 | 0 | 2877 | C3, M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | 4 | 1/10 | 0 | 2 | 3 | 1 | 0 | 0 | 2893 | C3, M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | n/a | 1/10 | 0 | 2 | 4 | 1 | 0 | 0 | 2918 | C3, M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | 4 | 1/10 | 0 | 2 | 3 | 1 | 0 | 0 | 2851 | C3, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-live > header.desk-pullout-head.desk-window-handle > span.desk-wings`: ⚙︎
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Start meeting” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--primary`
- **M7** 10px — “Transcript” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “⌂ This device” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-egress > span.gadget-chip.gadget-chip-egress`
- **M7** 10px — “READY” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Start meeting”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-live > header.desk-pullout-head.desk-window-handle > span.desk-wings`: ⚙︎
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Start meeting” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--primary`
- **M7** 10px — “Transcript” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “⌂ This device” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-egress > span.gadget-chip.gadget-chip-egress`
- **M7** 10px — “READY” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** target 16x14px — “Close Live meeting”
- **M7** target 16x14px — “Minimize Live meeting”
- **M7** target 27x24px — “Configure meeting”
- **M7** target 104x24px — “Start meeting”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Start meeting”
- **U1** 3 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-live > header.desk-pullout-head.desk-window-handle > span.desk-wings`: ⚙︎
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Start meeting” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--primary`
- **M7** 10px — “Transcript” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “⌂ This device” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-egress > span.gadget-chip.gadget-chip-egress`
- **M7** 10px — “READY” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Start meeting”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-live > header.desk-pullout-head.desk-window-handle > span.desk-wings`: ⚙︎
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Start meeting” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--primary`
- **M7** 10px — “Transcript” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “⌂ This device” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-egress > span.gadget-chip.gadget-chip-egress`
- **M7** 10px — “READY” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** target 16x14px — “Close Live meeting”
- **M7** target 16x14px — “Minimize Live meeting”
- **M7** target 27x24px — “Configure meeting”
- **M7** target 104x24px — “Start meeting”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Start meeting”
- **U1** 3 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 1}

</details>

### Meetings  <sub>`app-meetings`</sub>

- Family: application · Door: Dock ▣ / Go > Meetings
- Opened by the rig via: `go:Meetings`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3615 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3617 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3669 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3851 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Models (Concierge)  <sub>`app-models`</sub>

- Family: application · Door: Go > Models
- Opened by the rig via: `go:Models`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3448 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3412 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3445 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3427 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Models”
- **M7** target 16x14px — “Minimize Models”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Models”
- **M7** target 16x14px — “Minimize Models”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### New Project  <sub>`app-new-project`</sub>

- Family: application · Door: NO DOOR: no Go row; reached from the Chair's start actions
- Opened by the rig via: `route:/setup`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 14 | n/a | 5/21 | 0 | 3 | 4 | 4 | 0 | 0 | 2866 | C3, M10, M7, M8, U1, U4 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 14 | 8 | 5/21 | 0 | 3 | 3 | 4 | 0 | 0 | 2872 | C3, M10, M7, M8, U1, U4 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 14 | n/a | 5/21 | 0 | 3 | 4 | 4 | 0 | 0 | 2878 | C3, M10, M7, M8, U1, U4 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 14 | 8 | 5/21 | 0 | 3 | 3 | 4 | 0 | 0 | 2878 | C3, M10, M7, M8, U1, U4 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 11px — “THIS BECOMES THE PROJECT'S NAME” `div.desk-surface-body > div.door-root > div.door-outcome-well > span.door-outcome-caption`
- **M7** 11px — “SOURCES” `div.desk-surface-body > div.door-root > div.door-sources-section > span.door-section-label`
- **M7** 10px — “SIGN IN” `ul.door-sources-list > li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip`
- **M7** 11px — “⚠” `li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip > span.surface-state-chip-icon`
- **M7** 11px — “Connect” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--primary`
- **M7** 10px — “SIGN IN” `ul.door-sources-list > li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “THIS BECOMES THE PROJECT'S NAME”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Create Project”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (12); "JetBrains Mono", monospace (6); Inter, system-ui, sans-serif (3)
- **U1** 4 raw buttons vs 5 library — {"desk-light": 3, "desk-mic": 1}
- **U4** filled primaries: “Connect”, “Connect”, “Connect”, “Create Project”

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 11px — “THIS BECOMES THE PROJECT'S NAME” `div.desk-surface-body > div.door-root > div.door-outcome-well > span.door-outcome-caption`
- **M7** 11px — “SOURCES” `div.desk-surface-body > div.door-root > div.door-sources-section > span.door-section-label`
- **M7** 10px — “SIGN IN” `ul.door-sources-list > li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip`
- **M7** 11px — “⚠” `li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip > span.surface-state-chip-icon`
- **M7** 11px — “Connect” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--primary`
- **M7** 10px — “SIGN IN” `ul.door-sources-list > li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip`
- **M7** target 16x14px — “Close New Project”
- **M7** target 16x14px — “Minimize New Project”
- **M7** target 34x34px — “Speak outcome”
- **M7** target 64x24px — “Connect”
- **M7** target 64x24px — “Connect”
- **M7** target 64x24px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “THIS BECOMES THE PROJECT'S NAME”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Create Project”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (12); "JetBrains Mono", monospace (6); Inter, system-ui, sans-serif (3)
- **U1** 3 raw buttons vs 5 library — {"desk-light": 2, "desk-mic": 1}
- **U4** filled primaries: “Connect”, “Connect”, “Connect”, “Create Project”

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “THIS BECOMES THE PROJECT'S NAME” `div.desk-surface-body > div.door-root > div.door-outcome-well > span.door-outcome-caption`
- **M7** 11px — “SOURCES” `div.desk-surface-body > div.door-root > div.door-sources-section > span.door-section-label`
- **M7** 10px — “SIGN IN” `ul.door-sources-list > li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip`
- **M7** 11px — “⚠” `li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip > span.surface-state-chip-icon`
- **M7** 11px — “Connect” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--primary`
- **M7** 10px — “SIGN IN” `ul.door-sources-list > li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “THIS BECOMES THE PROJECT'S NAME”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Create Project”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (12); "JetBrains Mono", monospace (6); Inter, system-ui, sans-serif (3)
- **U1** 4 raw buttons vs 5 library — {"desk-light": 3, "desk-mic": 1}
- **U4** filled primaries: “Connect”, “Connect”, “Connect”, “Create Project”

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 11px — “THIS BECOMES THE PROJECT'S NAME” `div.desk-surface-body > div.door-root > div.door-outcome-well > span.door-outcome-caption`
- **M7** 11px — “SOURCES” `div.desk-surface-body > div.door-root > div.door-sources-section > span.door-section-label`
- **M7** 10px — “SIGN IN” `ul.door-sources-list > li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip`
- **M7** 11px — “⚠” `li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip > span.surface-state-chip-icon`
- **M7** 11px — “Connect” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--primary`
- **M7** 10px — “SIGN IN” `ul.door-sources-list > li.surface-ledger-row > div.surface-ledger-line > span.surface-state-chip`
- **M7** target 16x14px — “Close New Project”
- **M7** target 16x14px — “Minimize New Project”
- **M7** target 34x34px — “Speak outcome”
- **M7** target 64x24px — “Connect”
- **M7** target 64x24px — “Connect”
- **M7** target 64x24px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Connect”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “THIS BECOMES THE PROJECT'S NAME”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Create Project”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (12); "JetBrains Mono", monospace (6); Inter, system-ui, sans-serif (3)
- **U1** 3 raw buttons vs 5 library — {"desk-light": 2, "desk-mic": 1}
- **U4** filled primaries: “Connect”, “Connect”, “Connect”, “Create Project”

</details>

### People  <sub>`app-people`</sub>

- Family: application · Door: NO DOOR: no Go row; Desk menu > Open People (verbRegistry.ts:336)
- Opened by the rig via: `palette:Open People`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3946 | C3, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3851 | C3, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3839 | C3, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3908 | C3, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close People”
- **M7** target 16x14px — “Minimize People”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close People”
- **M7** target 16x14px — “Minimize People”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Change places  <sub>`app-places`</sub>

- Family: application · Door: Go > Change places
- Opened by the rig via: `go:Change places`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3140 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3158 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3196 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3134 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Change places”
- **M7** target 16x14px — “Minimize Change places”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Change places”
- **M7** target 16x14px — “Minimize Change places”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Processes  <sub>`app-processes`</sub>

- Family: application · Door: Go > Processes
- Opened by the rig via: `go:Processes`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3093 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3112 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3218 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3205 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Processes”
- **M7** target 16x14px — “Minimize Processes”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Processes”
- **M7** target 16x14px — “Minimize Processes”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Rhythm (cadence)  <sub>`app-rhythm`</sub>

- Family: application · Door: Go > Rhythm
- Opened by the rig via: `go:Rhythm`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3455 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3372 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3446 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3508 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Rhythm”
- **M7** target 16x14px — “Minimize Rhythm”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Rhythm”
- **M7** target 16x14px — “Minimize Rhythm”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Runtime docs (an alias onto Settings' Guide wing)  <sub>`app-runtime-docs`</sub>

- Family: application · Door: NO DOOR: no Go row; /docs/dictation-runtime is an alias of configure-settings scoped to the Guide wing (applications.ts:162), so it draws the Settings window
- Opened by the rig via: `route:/docs/dictation-runtime`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | n/a | 0/39 | 0 | 2 | 5 | 0 | 0 | 0 | 2852 | C3, M4, M6, M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | 6 | 0/39 | 0 | 2 | 4 | 0 | 0 | 0 | 2824 | C3, M4, M6, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | n/a | 0/39 | 0 | 2 | 5 | 0 | 0 | 0 | 2934 | C3, M4, M6, M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | 6 | 0/39 | 0 | 2 | 4 | 0 | 0 | 0 | 2868 | C3, M4, M6, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 124x24px — “Run runtime test”
- **M7** target 117x24px — “Check readiness”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 124x24px — “Run runtime test”
- **M7** target 117x24px — “Check readiness”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings  <sub>`app-settings`</sub>

- Family: application · Door: Dock / Go > Settings
- Opened by the rig via: `go:Settings`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3477 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3450 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3479 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3396 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Speak (dictation)  <sub>`app-speak`</sub>

- Family: application · Door: Dock ⌁ / Go > Speak
- Opened by the rig via: `go:Speak`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3370 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3377 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3552 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3430 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Workbenches  <sub>`app-workbenches`</sub>

- Family: application · Door: Go > Workbenches
- Opened by the rig via: `go:Workbenches`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3340 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3453 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3459 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3409 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Workbenches”
- **M7** target 16x14px — “Minimize Workbenches”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Workbenches”
- **M7** target 16x14px — “Minimize Workbenches”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### Activity — the gear door (Candidates and connectors)  <sub>`door-activity`</sub>

- Family: wing · Door: Go > Activity > the gear door 'Candidates and connectors'
- Opened by the rig via: `custom:door:Activity|#surface-activity|Candidates and connectors`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 1 | 2 | 17 | n/a | 0/25 | 0 | 2 | 7 | 0 | 0 | 0 | 6325 | M5, M6, M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 1 | 2 | 17 | 12 | 0/25 | 0 | 2 | 6 | 0 | 0 | 0 | 6400 | M5, M6, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 1 | 2 | 17 | n/a | 0/25 | 0 | 2 | 7 | 0 | 0 | 0 | 6444 | M5, M6, M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 1 | 2 | 17 | 12 | 0/25 | 0 | 2 | 6 | 0 | 0 | 0 | 6331 | M5, M6, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M6** “first-party” appears 5x
- **M6** “cli_enrichment” appears 4x
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Meeting candidates” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **U1** 7 raw buttons vs 6 library — {"desk-light": 3, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M6** “first-party” appears 5x
- **M6** “cli_enrichment” appears 4x
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Meeting candidates” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Activity”
- **M7** target 16x14px — “Minimize Activity”
- **M7** target 72x23px — “Records”
- **M7** target 59x23px — “Rules”
- **M7** target 27x24px — “Candidates and connectors”
- **M7** target 91x24px — “Refresh now”
- **U1** 6 raw buttons vs 6 library — {"desk-light": 2, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M6** “first-party” appears 5x
- **M6** “cli_enrichment” appears 4x
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Meeting candidates” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **U1** 7 raw buttons vs 6 library — {"desk-light": 3, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M6** “first-party” appears 5x
- **M6** “cli_enrichment” appears 4x
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Meeting candidates” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Activity”
- **M7** target 16x14px — “Minimize Activity”
- **M7** target 72x23px — “Records”
- **M7** target 59x23px — “Rules”
- **M7** target 27x24px — “Candidates and connectors”
- **M7** target 91x24px — “Refresh now”
- **U1** 6 raw buttons vs 6 library — {"desk-light": 2, "desk-wing": 3, "desk-mic": 1}

</details>

### Agents — the gear door (How it connects)  <sub>`door-agents`</sub>

- Family: wing · Door: Go > Agents > the gear door 'How it connects'
- Opened by the rig via: `custom:door:Agents|#surface-companion|How it connects`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | n/a | 2/19 | 0 | 2 | 6 | 0 | 0 | 0 | 6410 | M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | 5 | 2/19 | 0 | 2 | 5 | 0 | 0 | 0 | 6317 | M7, M8, U1 |
| rich | 1440 | ok | 0+1in | 1 | 0 | 0/0 | 0 | 0 | 6 | n/a | 2/19 | 0 | 2 | 6 | 0 | 0 | 0 | 6415 | M1, M2, M7, M8, U1 |
| rich | 393 | ok | 0+1in | 1 | 0 | 0/0 | 0 | 0 | 6 | 6 | 2/19 | 0 | 2 | 5 | 0 | 0 | 0 | 6344 | M1, M2, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Sessions” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “Crew” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Sessions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Crew”
- **U1** 6 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Sessions” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “Crew” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** target 16x14px — “Close Agents”
- **M7** target 16x14px — “Minimize Agents”
- **M7** target 66x23px — “Roster”
- **M7** target 79x23px — “Delivery”
- **M7** target 27x24px — “How it connects”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Sessions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Crew”
- **U1** 5 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 3}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1 (inner)** `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary` overflows by 75px — “The reviewer — an agent with a deliberately long name”
- **M2** `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary` hides 75px on x — “The reviewer — an agent with a deliberately long name”
- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Sessions” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “Crew” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “OK” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell > span.gadget-lamp`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Sessions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Crew”
- **U1** 6 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1 (inner)** `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary` overflows by 213px — “The reviewer — an agent with a deliberately long name”
- **M2** `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary` hides 213px on x — “The reviewer — an agent with a deliberately long name”
- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Sessions” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “Crew” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “OK” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell > span.gadget-lamp`
- **M7** target 16x14px — “Close Agents”
- **M7** target 16x14px — “Minimize Agents”
- **M7** target 66x23px — “Roster”
- **M7** target 79x23px — “Delivery”
- **M7** target 27x24px — “How it connects”
- **M7** target 363x26px — “The reviewer — an agent with a deliberat…”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Sessions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Crew”
- **U1** 5 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 3}

</details>

### Meetings — the gear door (Meeting plumbing)  <sub>`door-meetings`</sub>

- Family: wing · Door: Go > Meetings > the gear door 'Meeting plumbing'
- Opened by the rig via: `custom:door:Meetings|#surface-meetings|Meeting plumbing`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 2 | 0/0 | 1 | 2 | 15 | n/a | 0/29 | 0 | 2 | 10 | 0 | 0 | 0 | 6283 | M3, M5, M6, M7, U1 |
| cold | 393 | ok | 0 | 0 | 2 | 0/0 | 1 | 2 | 15 | 9 | 0/29 | 0 | 2 | 9 | 0 | 0 | 0 | 6372 | M3, M5, M6, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 2 | 0/0 | 1 | 2 | 19 | n/a | 0/37 | 0 | 2 | 13 | 0 | 0 | 0 | 6425 | M3, M5, M6, M7, U1 |
| rich | 393 | ok | 0+2in | 2 | 2 | 0/0 | 1 | 2 | 19 | 12 | 0/37 | 0 | 2 | 12 | 0 | 0 | 0 | 6390 | M1, M2, M3, M5, M6, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M3** verb “Speak Mic device” is outside its window — `div.gadget-row > span.gadget-row-gadget > span.gadget-string > button.desk-mic.is-idle`
- **M3** verb “Speak System audio device” is outside its window — `div.gadget-row > span.gadget-row-gadget > span.gadget-string > button.desk-mic.is-idle`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M6** “Nothing here” appears 4x
- **M6** “device name” appears 2x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Actions” `div.surface-door > section.surface-section > header.surface-section-head > h3`
- **U1** 10 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M3** verb “Speak Mic device” is outside its viewport — `div.gadget-row > span.gadget-row-gadget > span.gadget-string > button.desk-mic.is-idle`
- **M3** verb “Speak System audio device” is outside its viewport — `div.gadget-row > span.gadget-row-gadget > span.gadget-string > button.desk-mic.is-idle`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M6** “Nothing here” appears 4x
- **M6** “device name” appears 2x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Actions” `div.surface-door > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **U1** 9 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M3** verb “Speak Mic device” is outside its window — `div.gadget-row > span.gadget-row-gadget > span.gadget-string > button.desk-mic.is-idle`
- **M3** verb “Speak System audio device” is outside its window — `div.gadget-row > span.gadget-row-gadget > span.gadget-string > button.desk-mic.is-idle`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M6** “Nothing here” appears 3x
- **M6** “device name” appears 2x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Actions” `div.surface-door > section.surface-section > header.surface-section-head > h3`
- **U1** 13 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 5, "surface-row-open": 3, "desk-mic": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1 (inner)** `div.surface-row-line > button.surface-row-open > span.surface-row-text > strong` overflows by 19px — “Kernel: the ledger, the receipts, and the undo”
- **M1 (inner)** `div.surface-row-line > button.surface-row-open > span.surface-row-text > strong` overflows by 203px — “Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3)”
- **M2** `div.surface-row-line > button.surface-row-open > span.surface-row-text > strong` hides 19px on x — “Kernel: the ledger, the receipts, and the undo”
- **M2** `div.surface-row-line > button.surface-row-open > span.surface-row-text > strong` hides 203px on x — “Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3)”
- **M3** verb “Speak Mic device” is outside its viewport — `div.gadget-row > span.gadget-row-gadget > span.gadget-string > button.desk-mic.is-idle`
- **M3** verb “Speak System audio device” is outside its viewport — `div.gadget-row > span.gadget-row-gadget > span.gadget-string > button.desk-mic.is-idle`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M6** “Nothing here” appears 3x
- **M6** “device name” appears 2x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Actions” `div.surface-door > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **U1** 12 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 5, "surface-row-open": 3, "desk-mic": 2}

</details>

### Speak — the gear door (Configure dictation)  <sub>`door-speak`</sub>

- Family: wing · Door: Go > Speak > the gear door 'Configure dictation'
- Opened by the rig via: `custom:door:Speak|#surface-dictation|Configure dictation`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 7 | 2/2 | 1 | 0 | 44 | n/a | 0/82 | 0 | 2 | 14 | 0 | 1 | 1 | 6544 | A7, M3, M4, M5, M7, U1, U3 |
| cold | 393 | ok | 0 | 0 | 9 | 2/2 | 1 | 0 | 44 | 21 | 0/82 | 0 | 2 | 13 | 0 | 1 | 1 | 6635 | A7, M3, M4, M5, M7, U1, U3 |
| rich | 1440 | ok | 0 | 0 | 7 | 2/2 | 1 | 0 | 44 | n/a | 0/82 | 0 | 2 | 14 | 0 | 1 | 1 | 6537 | A7, M3, M4, M5, M7, U1, U3 |
| rich | 393 | ok | 0 | 0 | 9 | 2/2 | 1 | 0 | 44 | 21 | 0/82 | 0 | 2 | 13 | 0 | 1 | 1 | 6720 | A7, M3, M4, M5, M7, U1, U3 |

<details><summary>cold @1440 — evidence</summary>

- **M3** verb “Edit task_focus value” is outside its window — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its window — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Edit constraints value” is outside its window — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its window — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “+ ADD” is outside its window — `section.gadget-group > div.gadget-sheet > div.gadget-table > button.gadget-table-add`
- **M3** verb “Edit Project instructions” is outside its window — `div.surface-door > section.gadget-group > div.gadget-sheet > button.surface-edit-in-place`
- **M4** fold “Wire details” is closed over: “pipeline enabledtruemax total latency ms600backendautoidcodex_clilabelCodex CLIc…”
- **M4** fold “Raw trace” is closed over: “{ "capture_messages": false, "registry_path": "/var/folders/q7/5dzz5g2116b3lq8rh…”
- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Pipeline” `div.desk-surface-body > div.surface-door > section.gadget-group > h4.gadget-group-label`
- **U1** 14 raw buttons vs 8 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 1, "surface-edit-in-place": 4, "gadget-table-add": 1}
- **U3** “0 (beside "runs")” `div.gadget-fold-body > dl.surface-facts > div > dd`
- **A7** 14 words — “Install either holdspeak[dictation-mlx] (darwin/arm64) or holdspeak[dictation-llama] (cross-platform), or configure dictation.runtime.backen…”

</details>

<details><summary>cold @393 — evidence</summary>

- **M3** verb “Edit stack value” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Edit task_focus value” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Edit constraints value” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M4** fold “Wire details” is closed over: “pipeline enabledtruemax total latency ms600backendautoidcodex_clilabelCodex CLIc…”
- **M4** fold “Raw trace” is closed over: “{ "capture_messages": false, "registry_path": "/var/folders/q7/5dzz5g2116b3lq8rh…”
- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Pipeline” `div.desk-surface-body > div.surface-door > section.gadget-group > h4.gadget-group-label`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **U1** 13 raw buttons vs 8 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 1, "surface-edit-in-place": 4, "gadget-table-add": 1}
- **U3** “0 (beside "runs")” `div.gadget-fold-body > dl.surface-facts > div > dd`
- **A7** 14 words — “Install either holdspeak[dictation-mlx] (darwin/arm64) or holdspeak[dictation-llama] (cross-platform), or configure dictation.runtime.backen…”

</details>

<details><summary>rich @1440 — evidence</summary>

- **M3** verb “Edit task_focus value” is outside its window — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its window — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Edit constraints value” is outside its window — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its window — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “+ ADD” is outside its window — `section.gadget-group > div.gadget-sheet > div.gadget-table > button.gadget-table-add`
- **M3** verb “Edit Project instructions” is outside its window — `div.surface-door > section.gadget-group > div.gadget-sheet > button.surface-edit-in-place`
- **M4** fold “Wire details” is closed over: “pipeline enabledtruemax total latency ms600backendautoidcodex_clilabelCodex CLIc…”
- **M4** fold “Raw trace” is closed over: “{ "capture_messages": false, "registry_path": "/var/folders/q7/5dzz5g2116b3lq8rh…”
- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Pipeline” `div.desk-surface-body > div.surface-door > section.gadget-group > h4.gadget-group-label`
- **U1** 14 raw buttons vs 8 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 1, "surface-edit-in-place": 4, "gadget-table-add": 1}
- **U3** “0 (beside "runs")” `div.gadget-fold-body > dl.surface-facts > div > dd`
- **A7** 14 words — “Install either holdspeak[dictation-mlx] (darwin/arm64) or holdspeak[dictation-llama] (cross-platform), or configure dictation.runtime.backen…”

</details>

<details><summary>rich @393 — evidence</summary>

- **M3** verb “Edit stack value” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Edit task_focus value” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M3** verb “Edit constraints value” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-cell > button.surface-edit-in-place`
- **M3** verb “×” is outside its viewport — `div.gadget-table > div.gadget-table-row > span.gadget-table-verbs > button.btn.btn--ghost`
- **M4** fold “Wire details” is closed over: “pipeline enabledtruemax total latency ms600backendautoidcodex_clilabelCodex CLIc…”
- **M4** fold “Raw trace” is closed over: “{ "capture_messages": false, "registry_path": "/var/folders/q7/5dzz5g2116b3lq8rh…”
- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M5** empty-heading `div.gadget-sheet > div.gadget-row > span.gadget-row-gadget > label.gadget-check`
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Pipeline” `div.desk-surface-body > div.surface-door > section.gadget-group > h4.gadget-group-label`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **U1** 13 raw buttons vs 8 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 1, "surface-edit-in-place": 4, "gadget-table-add": 1}
- **U3** “0 (beside "runs")” `div.gadget-fold-body > dl.surface-facts > div > dd`
- **A7** 14 words — “Install either holdspeak[dictation-mlx] (darwin/arm64) or holdspeak[dictation-llama] (cross-platform), or configure dictation.runtime.backen…”

</details>

### Intelligence — Brief  <sub>`intel-brief`</sub>

- Family: wing · Door: the dock's Intelligence verb > the 'Brief' segment (web/src/desk/pullouts/IntelligencePullout.tsx:12)
- Opened by the rig via: `custom:intel-view:Brief`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 3/10 | 0 | 3 | 7 | 0 | 0 | 0 | 4790 | M10, M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 9 | 3/10 | 0 | 3 | 6 | 0 | 0 | 0 | 4789 | M10, M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 3/10 | 0 | 3 | 7 | 0 | 0 | 0 | 4863 | M10, M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 9 | 3/10 | 0 | 3 | 6 | 0 | 0 | 0 | 4838 | M10, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Acknowledge” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** 11px — “Defer” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** 11px — “Speak” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Acknowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Defer”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Speak”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (7); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); Arial (1)
- **U1** 7 raw buttons vs 3 library — {"desk-light": 3, "intelligence-segment": 3, "desk-chip": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Acknowledge” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** 11px — “Defer” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** 11px — “Speak” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **M7** target 80x27px — “Generate”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Acknowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Defer”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Speak”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (7); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); Arial (1)
- **U1** 6 raw buttons vs 3 library — {"desk-light": 2, "intelligence-segment": 3, "desk-chip": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Acknowledge” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** 11px — “Defer” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** 11px — “Speak” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Acknowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Defer”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Speak”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (7); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); Arial (1)
- **U1** 7 raw buttons vs 3 library — {"desk-light": 3, "intelligence-segment": 3, "desk-chip": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Acknowledge” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** 11px — “Defer” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** 11px — “Speak” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **M7** target 80x27px — “Generate”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Acknowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Defer”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “Speak”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (7); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); Arial (1)
- **U1** 6 raw buttons vs 3 library — {"desk-light": 2, "intelligence-segment": 3, "desk-chip": 1}

</details>

### Intelligence — Decisions  <sub>`intel-decisions`</sub>

- Family: wing · Door: the dock's Intelligence verb > the 'Decisions' segment (web/src/desk/pullouts/IntelligencePullout.tsx:12)
- Opened by the rig via: `custom:intel-view:Decisions`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 7 | n/a | 1/11 | 0 | 2 | 8 | 0 | 0 | 0 | 4480 | M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 7 | 9 | 1/11 | 0 | 2 | 7 | 0 | 0 | 0 | 4580 | M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 7 | n/a | 1/11 | 0 | 2 | 8 | 0 | 0 | 0 | 4682 | M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 7 | 9 | 1/11 | 0 | 2 | 7 | 0 | 0 | 0 | 4607 | M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 11px — “BACK” `div#pullout:desk > div.desk-pullout-body.desk-surface-body > div.intelligence-header > button.btn.btn--ghost`
- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “WHY” `section.intelligence-view > div.receipts-view > div.receipts-search > span.receipts-search-prefix`
- **M7** 11px — “WHY ONLY” `section.intelligence-view > div.receipts-view > div.receipts-search-actions > button.btn.btn--ghost`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “ALL DECISIONS”
- **U1** 8 raw buttons vs 2 library — {"desk-light": 3, "intelligence-segment": 3, "desk-mic": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 11px — “BACK” `div#pullout:desk > div.desk-pullout-body.desk-surface-body > div.intelligence-header > button.btn.btn--ghost`
- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “WHY” `section.intelligence-view > div.receipts-view > div.receipts-search > span.receipts-search-prefix`
- **M7** 11px — “WHY ONLY” `section.intelligence-view > div.receipts-view > div.receipts-search-actions > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 365x27px — “BACK”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “ALL DECISIONS”
- **U1** 7 raw buttons vs 2 library — {"desk-light": 2, "intelligence-segment": 3, "desk-mic": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “BACK” `div#pullout:desk > div.desk-pullout-body.desk-surface-body > div.intelligence-header > button.btn.btn--ghost`
- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “WHY” `section.intelligence-view > div.receipts-view > div.receipts-search > span.receipts-search-prefix`
- **M7** 11px — “WHY ONLY” `section.intelligence-view > div.receipts-view > div.receipts-search-actions > button.btn.btn--ghost`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “ALL DECISIONS”
- **U1** 8 raw buttons vs 2 library — {"desk-light": 3, "intelligence-segment": 3, "desk-mic": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 11px — “BACK” `div#pullout:desk > div.desk-pullout-body.desk-surface-body > div.intelligence-header > button.btn.btn--ghost`
- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “WHY” `section.intelligence-view > div.receipts-view > div.receipts-search > span.receipts-search-prefix`
- **M7** 11px — “WHY ONLY” `section.intelligence-view > div.receipts-view > div.receipts-search-actions > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 365x27px — “BACK”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “ALL DECISIONS”
- **U1** 7 raw buttons vs 2 library — {"desk-light": 2, "intelligence-segment": 3, "desk-mic": 2}

</details>

### Intelligence — Follow-through  <sub>`intel-followthrough`</sub>

- Family: wing · Door: the dock's Intelligence verb > the 'Follow-through' segment (web/src/desk/pullouts/IntelligencePullout.tsx:12)
- Opened by the rig via: `custom:intel-view:Follow-through`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/6 | 0 | 2 | 6 | 0 | 0 | 0 | 4551 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/6 | 0 | 2 | 5 | 0 | 0 | 0 | 4578 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/6 | 0 | 2 | 6 | 0 | 0 | 0 | 4611 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/6 | 0 | 2 | 5 | 0 | 0 | 0 | 4658 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **U1** 6 raw buttons vs 0 library — {"desk-light": 3, "intelligence-segment": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **U1** 5 raw buttons vs 0 library — {"desk-light": 2, "intelligence-segment": 3}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **U1** 6 raw buttons vs 0 library — {"desk-light": 3, "intelligence-segment": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **U1** 5 raw buttons vs 0 library — {"desk-light": 2, "intelligence-segment": 3}

</details>

### The Presence HUD (/presence)  <sub>`page-presence`</sub>

- Family: application · Door: NO DOOR in the browser: the native desktop overlay loads it (holdspeak/desktop_presence_cocoa.py:341)
- Opened by the rig via: `route:/presence`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | n/a | 0/2 | 0 | 2 | 0 | 0 | 0 | 0 | 16639 | C3, M7 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | 1 | 0/2 | 0 | 2 | 0 | 0 | 0 | 0 | 16637 | C3, M7 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | n/a | 0/2 | 0 | 2 | 0 | 0 | 0 | 0 | 16646 | C3, M7 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | 1 | 0/2 | 0 | 2 | 0 | 0 | 0 | 0 | 16640 | C3, M7 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “Ready” `main#main > div.desk-next.presence-body > section.presence-card > span.gadget-lamp`

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 10px — “Ready” `main#main > div.desk-next.presence-body > section.presence-card > span.gadget-lamp`
- **M7** target 72x27px — “← Desk”

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “Ready” `main#main > div.desk-next.presence-body > section.presence-card > span.gadget-lamp`

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 10px — “Ready” `main#main > div.desk-next.presence-body > section.presence-card > span.gadget-lamp`
- **M7** target 72x27px — “← Desk”

</details>

### The Welcome arrival page (/welcome)  <sub>`page-welcome`</sub>

- Family: application · Door: NO DOOR: nothing in web/src links to /welcome outside routes.tsx:22 — its own header calls it a compatibility arrival route
- Opened by the rig via: `route:/welcome`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | n/a | 0/1 | 0 | 4 | 2 | 0 | 0 | 0 | 17191 | C3, M10, M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | 5 | 0/1 | 0 | 4 | 2 | 0 | 0 | 0 | 16848 | C3, M10, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | n/a | 0/1 | 0 | 4 | 2 | 0 | 0 | 0 | 16697 | C3, M10, M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | 5 | 0/1 | 0 | 4 | 2 | 0 | 0 | 0 | 16867 | C3, M10, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “Voice typing” `main#main > section.welcome-card > section.desk-first-words > span.surface-eyebrow`
- **M8** 7 text leaves NOT ASSESSED (painted over an image or gradient)
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (4); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Arial (1)
- **U1** 2 raw buttons vs 3 library — {"desk-first-talk": 1, "desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 10px — “Voice typing” `main#main > section.welcome-card > section.desk-first-words > span.surface-eyebrow`
- **M7** target 99x21px — “Click to dictate”
- **M7** target 20x20px — “Speak Your dictated text”
- **M7** target 55x28px — “Copy”
- **M7** target 112x28px — “Keep as Note”
- **M7** target 127x28px — “Continue later”
- **M8** 7 text leaves NOT ASSESSED (painted over an image or gradient)
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (4); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Arial (1)
- **U1** 2 raw buttons vs 3 library — {"desk-first-talk": 1, "desk-mic": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “Voice typing” `main#main > section.welcome-card > section.desk-first-words > span.surface-eyebrow`
- **M8** 7 text leaves NOT ASSESSED (painted over an image or gradient)
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (4); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Arial (1)
- **U1** 2 raw buttons vs 3 library — {"desk-first-talk": 1, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 10px — “Voice typing” `main#main > section.welcome-card > section.desk-first-words > span.surface-eyebrow`
- **M7** target 99x21px — “Click to dictate”
- **M7** target 20x20px — “Speak Your dictated text”
- **M7** target 55x28px — “Copy”
- **M7** target 112x28px — “Keep as Note”
- **M7** target 127x28px — “Continue later”
- **M8** 7 text leaves NOT ASSESSED (painted over an image or gradient)
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (4); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Arial (1)
- **U1** 2 raw buttons vs 3 library — {"desk-first-talk": 1, "desk-mic": 1}

</details>

### Artifact pullout  <sub>`pullout-artifact`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:artifact`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 162 | 0 | 12 | 1/1 | 1 | 0 | 4 | n/a | 3/23 | 0 | 3 | 20 | 0 | 0 | 0 | 3179 | M1, M10, M3, M4, M5, M7, M8, U1 |
| rich | 393 | ok | 169 | 0 | 12 | 1/1 | 1 | 0 | 4 | 19 | 3/23 | 0 | 3 | 19 | 0 | 0 | 0 | 3194 | M1, M10, M3, M4, M5, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 162px — widest child `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > span.desk-project-choice` “+ Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3…”
- **M3** verb “+ Personal” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Platform — çalışma zone” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Reference” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Work” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Custody — what the ledger holds” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Everyday context” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M4** fold “Filed · Desk root” is closed over: “Zone+ Decisions+ Inbox+ Meetings+ Personal+ Platform — çalışma zone+ Reference+ …”
- **M5** empty-section `div#desk-next > div#pullout:hs202-artifact-9ade7608 > div.desk-pullout-body.desk-surface-body > section` — “Plugin output”
- **M7** 10px — “Plugin output” `div#pullout:hs202-artifact-9ade7608 > div.desk-pullout-body.desk-surface-body > section > h3`
- **M7** 10px — “Zone” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Knowledge” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Projects” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Zone”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Knowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Projects”
- **M10** Arial (17); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (5); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 20 raw buttons vs 0 library — {"desk-light": 3, "desk-chip": 17}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 169px — widest child `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > span.desk-project-choice` “+ Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3…”
- **M3** verb “+ Personal” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Platform — çalışma zone” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Reference” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Work” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Custody — what the ledger holds” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Everyday context” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M4** fold “Filed · Desk root” is closed over: “Zone+ Decisions+ Inbox+ Meetings+ Personal+ Platform — çalışma zone+ Reference+ …”
- **M5** empty-section `div#desk-next > div#pullout:hs202-artifact-9ade7608 > div.desk-pullout-body.desk-surface-body > section` — “Plugin output”
- **M7** 10px — “Plugin output” `div#pullout:hs202-artifact-9ade7608 > div.desk-pullout-body.desk-surface-body > section > h3`
- **M7** 10px — “Zone” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Knowledge” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Projects” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** target 16x14px — “Close Ingest cut-over plan (v3) — çalışm…”
- **M7** target 16x14px — “Minimize Ingest cut-over plan (v3) — çal…”
- **M7** target 94x27px — “+ Decisions”
- **M7** target 69x27px — “+ Inbox”
- **M7** target 90x27px — “+ Meetings”
- **M7** target 89x27px — “+ Personal”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Zone”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Knowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Projects”
- **M10** Arial (17); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (5); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 19 raw buttons vs 0 library — {"desk-light": 2, "desk-chip": 17}

</details>

### Chain pullout  <sub>`pullout-chain`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:chain`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Coder pullout  <sub>`pullout-coder`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:coder`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Decision pullout  <sub>`pullout-decision`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:decision`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Zone (directory) pullout  <sub>`pullout-directory`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:directory`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Game pullout (FallbackPullout)  <sub>`pullout-game`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:game`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Intelligence pullout  <sub>`pullout-intelligence`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:intelligence`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 1/10 | 0 | 1 | 8 | 0 | 0 | 0 | 3208 | M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 8 | 1/10 | 0 | 1 | 7 | 0 | 0 | 0 | 3220 | M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “WHY” `section.intelligence-view > div.receipts-view > div.receipts-search > span.receipts-search-prefix`
- **M7** 11px — “WHY ONLY” `section.intelligence-view > div.receipts-view > div.receipts-search-actions > button.btn.btn--ghost`
- **M7** 10px — “ALL DECISIONS” `section.intelligence-view > div.receipts-view > div.receipts-search-actions > span`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “ALL DECISIONS”
- **U1** 8 raw buttons vs 1 library — {"desk-light": 3, "intelligence-segment": 3, "desk-mic": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 11px — “Brief” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Follow-through” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment`
- **M7** 11px — “Decisions” `div.desk-pullout-body.desk-surface-body > div.intelligence-header > div.intelligence-segments > button.intelligence-segment.is-active`
- **M7** 11px — “WHY” `section.intelligence-view > div.receipts-view > div.receipts-search > span.receipts-search-prefix`
- **M7** 11px — “WHY ONLY” `section.intelligence-view > div.receipts-view > div.receipts-search-actions > button.btn.btn--ghost`
- **M7** 10px — “ALL DECISIONS” `section.intelligence-view > div.receipts-view > div.receipts-search-actions > span`
- **M7** target 16x14px — “Close Intelligence”
- **M7** target 16x14px — “Minimize Intelligence”
- **M7** target 359x28px — “Brief”
- **M7** target 359x28px — “Follow-through”
- **M7** target 359x28px — “Decisions”
- **M7** target 20x20px — “Speak Search decisions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “ALL DECISIONS”
- **U1** 7 raw buttons vs 1 library — {"desk-light": 2, "intelligence-segment": 3, "desk-mic": 2}

</details>

### Knowledge pullout  <sub>`pullout-kb`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:kb`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Layout pullout (FallbackPullout)  <sub>`pullout-layout`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:layout`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Meeting pullout  <sub>`pullout-meeting`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:meeting`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 162+1in | 1 | 15 | 1/1 | 0 | 0 | 7 | n/a | 3/28 | 0 | 3 | 20 | 0 | 0 | 0 | 3278 | M1, M10, M2, M3, M4, M7, M8, U1 |
| rich | 393 | ok | 169+1in | 1 | 12 | 1/1 | 0 | 0 | 7 | 20 | 3/28 | 0 | 3 | 19 | 0 | 0 | 0 | 3209 | M1, M10, M2, M3, M4, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 162px — widest child `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > span.desk-project-choice` “+ Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3…”
- **M1 (inner)** `div#desk-next > div#pullout:hs202-meeting-00 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` overflows by 666px — “Quarterly platform architecture review — migration, custody, and the r…”
- **M2** `div#desk-next > div#pullout:hs202-meeting-00 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` hides 666px on x — “Quarterly platform architecture review — migration, custody, and the roadmap for the çalışma group (ünïcode) 2026”
- **M3** verb “+ Decisions” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Inbox” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Meetings” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Personal” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Platform — çalışma zone” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Reference” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M4** fold “Filed · Desk root” is closed over: “Zone+ Decisions+ Inbox+ Meetings+ Personal+ Platform — çalışma zone+ Reference+ …”
- **M7** 11px — “Review meeting” `div#pullout:hs202-meeting-00 > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.btn.btn--ghost`
- **M7** 10px — “CUSTODY” `div#pullout:hs202-meeting-00 > div.desk-pullout-body.desk-surface-body > span.summary-topics > span.surface-token`
- **M7** 10px — “INGEST” `div#pullout:hs202-meeting-00 > div.desk-pullout-body.desk-surface-body > span.summary-topics > span.surface-token`
- **M7** 10px — “RECEIPTS” `div#pullout:hs202-meeting-00 > div.desk-pullout-body.desk-surface-body > span.summary-topics > span.surface-token`
- **M7** 10px — “Zone” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Knowledge” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Zone”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Knowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Projects”
- **M10** Arial (17); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (9); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2)
- **U1** 20 raw buttons vs 1 library — {"desk-light": 3, "desk-chip": 17}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 169px — widest child `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > span.desk-project-choice` “+ Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3…”
- **M1 (inner)** `div#desk-next > div#pullout:hs202-meeting-00 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` overflows by 673px — “Quarterly platform architecture review — migration, custody, and the r…”
- **M2** `div#desk-next > div#pullout:hs202-meeting-00 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` hides 673px on x — “Quarterly platform architecture review — migration, custody, and the roadmap for the çalışma group (ünïcode) 2026”
- **M3** verb “+ Personal” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Platform — çalışma zone” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Reference” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Work” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Custody — what the ledger holds” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Everyday context” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M4** fold “Filed · Desk root” is closed over: “Zone+ Decisions+ Inbox+ Meetings+ Personal+ Platform — çalışma zone+ Reference+ …”
- **M7** 11px — “Review meeting” `div#pullout:hs202-meeting-00 > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.btn.btn--ghost`
- **M7** 10px — “CUSTODY” `div#pullout:hs202-meeting-00 > div.desk-pullout-body.desk-surface-body > span.summary-topics > span.surface-token`
- **M7** 10px — “INGEST” `div#pullout:hs202-meeting-00 > div.desk-pullout-body.desk-surface-body > span.summary-topics > span.surface-token`
- **M7** 10px — “RECEIPTS” `div#pullout:hs202-meeting-00 > div.desk-pullout-body.desk-surface-body > span.summary-topics > span.surface-token`
- **M7** 10px — “Zone” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Knowledge” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** target 16x14px — “Close Quarterly platform architecture re…”
- **M7** target 16x14px — “Minimize Quarterly platform architecture…”
- **M7** target 110x24px — “Review meeting”
- **M7** target 94x27px — “+ Decisions”
- **M7** target 69x27px — “+ Inbox”
- **M7** target 90x27px — “+ Meetings”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Zone”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Knowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Projects”
- **M10** Arial (17); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (9); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2)
- **U1** 19 raw buttons vs 1 library — {"desk-light": 2, "desk-chip": 17}

</details>

### Note pullout  <sub>`pullout-note`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:note`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 3/10 | 0 | 3 | 5 | 1 | 0 | 0 | 3206 | M10, M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 6 | 3/10 | 0 | 3 | 4 | 1 | 0 | 0 | 3295 | M10, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “ONE QUESTION” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.thought-note-ask-label`
- **M7** 10px — “NO ENGINE YET” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.surface-token`
- **M7** 11px — “Choose an engine” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > button.btn.btn--secondary`
- **M7** 10px — “READS · NOTHING” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-egress > span.thought-note-reads`
- **M7** 10px — “KEPT” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** 11px — “Change” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-verbs > button.btn.btn--secondary`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Finish”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “ONE QUESTION”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “READS · NOTHING”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (8); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 5 raw buttons vs 3 library — {"desk-light": 3, "surface-edit-in-place": 1, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 11px — “ONE QUESTION” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.thought-note-ask-label`
- **M7** 10px — “NO ENGINE YET” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.surface-token`
- **M7** 11px — “Choose an engine” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > button.btn.btn--secondary`
- **M7** 10px — “READS · NOTHING” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-egress > span.thought-note-reads`
- **M7** 10px — “KEPT” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** 11px — “Change” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** target 16x14px — “Close Thought”
- **M7** target 16x14px — “Minimize Thought”
- **M7** target 28x28px — “Speak the note”
- **M7** target 124x40px — “Choose an engine”
- **M7** target 58x40px — “Change”
- **M7** target 69x40px — “Finish”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Finish”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “ONE QUESTION”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “READS · NOTHING”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (8); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 4 raw buttons vs 3 library — {"desk-light": 2, "surface-edit-in-place": 1, "desk-mic": 1}

</details>

### People pullout  <sub>`pullout-people`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:people`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 1/3 | 0 | 2 | 3 | 1 | 0 | 0 | 3195 | M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 3 | 1/3 | 0 | 2 | 2 | 1 | 0 | 0 | 3194 | M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Set up People”
- **U1** 3 raw buttons vs 1 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close People”
- **M7** target 16x14px — “Minimize People”
- **M7** target 120x28px — “Set up People”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Set up People”
- **U1** 2 raw buttons vs 1 library — {"desk-light": 2}

</details>

### Project pullout (FallbackPullout)  <sub>`pullout-project`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:project`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0+1in | 1 | 59 | 0/0 | 0 | 2 | 116 | n/a | 1/219 | 0 | 3 | 6 | 1 | 0 | 0 | 3227 | M1, M10, M2, M3, M6, M7, M8, U1 |
| rich | 393 | ok | 0+2in | 2 | 68 | 0/0 | 0 | 2 | 120 | 41 | 2/226 | 0 | 3 | 5 | 1 | 0 | 0 | 3245 | M1, M10, M2, M3, M6, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1 (inner)** `div.room-section-rise.room-ask-container > div.room-ask-section > div.room-ask-well > button.btn.btn--ghost` overflows by 19px — “Submit”
- **M2** `div.room-section-rise.room-ask-container > div.room-ask-section > div.room-ask-well > button.btn.btn--ghost` hides 19px on x — “Submit”
- **M3** verb “GHacme-platform/service-09⚠CAN'T CHECKRemove” is outside its window — `div.surface-ledger > ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Remove” is outside its window — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--ghost`
- **M3** verb “GHacme-platform/service-28⚠CAN'T CHECKRemove” is outside its viewport — `div.surface-ledger > ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Remove” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--ghost`
- **M3** verb “GHacme-platform/service-22⚠CAN'T CHECKRemove” is outside its viewport — `div.surface-ledger > ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Remove” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--ghost`
- **M4** tab bar `div.desk-surface-windows > div#surface-project-memory > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Room, History
- **M4** tab bar `div#surface-project-memory > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Room, History
- **M6** “To get started with GitHub CLI, please run: gh auth login” appears 30x
- **M6** “Nothing needs you” appears 2x
- **M7** 10px — “Room” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “History” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “ON TRACK” `div.room-section-rise > div.room-head > div.room-head-chips > span.surface-state-chip`
- **M7** 11px — “●” `div.room-head > div.room-head-chips > span.surface-state-chip > span.surface-state-chip-icon`
- **M7** 11px — “Draft update” `div.room-head > div.room-head-chips > span.room-head-trailing > button.btn.btn--primary`
- **M7** 10px — “NEEDS YOU” `div.room-section-rise > section.surface-section > header.surface-section-head > h3`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Draft update”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (181); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (37); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 6 raw buttons vs 36 library — {"desk-light": 3, "desk-wing": 2, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1 (inner)** `div.desk-surface-windows > div#surface-project-memory > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` overflows by 130px — “Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3)”
- **M1 (inner)** `div.room-section-rise.room-ask-container > div.room-ask-section > div.room-ask-well > button.btn.btn--ghost` overflows by 19px — “Submit”
- **M2** `div.desk-surface-windows > div#surface-project-memory > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` hides 130px on x — “Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3)”
- **M2** `div.room-section-rise.room-ask-container > div.room-ask-section > div.room-ask-well > button.btn.btn--ghost` hides 19px on x — “Submit”
- **M3** verb “GHacme-platform/service-11⚠CAN'T CHECKRemove” is outside its viewport — `div.surface-ledger > ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Remove” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--ghost`
- **M3** verb “GHacme-platform/service-13⚠CAN'T CHECKRemove” is outside its viewport — `div.surface-ledger > ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Remove” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--ghost`
- **M3** verb “GHacme-platform/service-25⚠CAN'T CHECKRemove” is outside its viewport — `div.surface-ledger > ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Remove” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--ghost`
- **M4** tab bar `div.desk-surface-windows > div#surface-project-memory > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Room, History
- **M4** tab bar `div#surface-project-memory > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Room, History
- **M6** “To get started with GitHub CLI, please run: gh auth login” appears 30x
- **M6** “Nothing needs you” appears 2x
- **M7** 10px — “Room” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “History” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “ON TRACK” `div.room-section-rise > div.room-head > div.room-head-chips > span.surface-state-chip`
- **M7** 11px — “●” `div.room-head > div.room-head-chips > span.surface-state-chip > span.surface-state-chip-icon`
- **M7** 11px — “Draft update” `div.room-head > div.room-head-chips > span.room-head-trailing > button.btn.btn--primary`
- **M7** 10px — “NEEDS YOU” `div.room-section-rise > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Platform Modernisation — Ingest, C…”
- **M7** target 16x14px — “Minimize Platform Modernisation — Ingest…”
- **M7** target 52x23px — “Room”
- **M7** target 72x23px — “History”
- **M7** target 343x24px — “Draft update”
- **M7** target 64x24px — “Steward”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Draft update”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “SUN 16:38”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (185); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (40); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 5 raw buttons vs 36 library — {"desk-light": 2, "desk-wing": 2, "desk-mic": 1}

</details>

### Agent (recipe) pullout  <sub>`pullout-recipe`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:recipe`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Repository pullout (FallbackPullout)  <sub>`pullout-repository`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:repository`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 3 | 0 | 13 | 0/0 | 16 | 3 | 13 | n/a | 3/151 | 0 | 2 | 10 | 0 | 0 | 0 | 4001 | M1, M3, M5, M6, M7, M8, U1 |
| rich | 393 | ok | 15+1in | 1 | 3 | 0/0 | 16 | 3 | 13 | 12 | 3/151 | 0 | 2 | 9 | 0 | 0 | 0 | 3832 | M1, M2, M3, M5, M6, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1** the document scrolls sideways: 1443px in 1440px
- **M3** verb “Close wt-202-audit” is outside its viewport — `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-close`
- **M3** verb “Minimize wt-202-audit” is outside its viewport — `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-min`
- **M3** verb “Maximize wt-202-audit” is outside its viewport — `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-max`
- **M3** verb “Files” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M3** verb “PRs” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M3** verb “Issues” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M4** tab bar `div#desk-next > div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Files, PRs, Issues
- **M4** tab bar `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Files, PRs, Issues
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M6** “folder” appears 18x
- **M6** “1h ago” appears 16x
- **M6** “file” appears 3x
- **M7** 11px — “audit/surface-inventory-2026-09-20” `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.repo-branch`
- **M7** 10px — “306 dirty” `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.repo-dirty`
- **M7** 10px — “Files” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “PRs” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Issues” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “root” `div#repository:src_e79f53ac7d7fd815 > div.desk-repo-body.desk-surface-body > nav.repo-breadcrumb > button.btn.btn--ghost`
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Stage”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Commit”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “↑”
- **U1** 10 raw buttons vs 3 library — {"desk-light": 3, "desk-wing": 3, "desk-sortable-table-sort": 3, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 15px — widest child `div#repository:src_e79f53ac7d7fd815 > div.desk-repo-body.desk-surface-body > nav.repo-breadcrumb > span.gadget-cycle` “↻agent/hs-104-01-capability-ledgeragent/hs-104-02-tool-call-gateagent/…”
- **M1 (inner)** `div#desk-next > div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` overflows by 25px — “wt-202-auditaudit/surface-inventory-2026-09-20383 dirty”
- **M2** `div#desk-next > div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` hides 25px on x — “wt-202-auditaudit/surface-inventory-2026-09-20383 dirty”
- **M3** verb “Stage” is outside its viewport — `div.surface-footer-layout > div.surface-footer-verbs > div.repo-footer-actions > button.btn.btn--secondary`
- **M3** verb “Speak Commit message” is outside its viewport — `div.surface-footer-verbs > div.repo-footer-actions > span.gadget-string > button.desk-mic.is-idle`
- **M3** verb “Commit” is outside its viewport — `div.surface-footer-layout > div.surface-footer-verbs > div.repo-footer-actions > button.btn.btn--secondary`
- **M4** tab bar `div#desk-next > div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Files, PRs, Issues
- **M4** tab bar `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Files, PRs, Issues
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M6** “folder” appears 18x
- **M6** “2h ago” appears 16x
- **M6** “file” appears 3x
- **M7** 11px — “audit/surface-inventory-2026-09-20” `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.repo-branch`
- **M7** 10px — “383 dirty” `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.repo-dirty`
- **M7** 10px — “Files” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “PRs” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Issues” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “root” `div#repository:src_e79f53ac7d7fd815 > div.desk-repo-body.desk-surface-body > nav.repo-breadcrumb > button.btn.btn--ghost`
- **M7** target 16x14px — “Close wt-202-audit”
- **M7** target 16x14px — “Minimize wt-202-audit”
- **M7** target 59x23px — “Files”
- **M7** target 46x23px — “PRs”
- **M7** target 66x23px — “Issues”
- **M7** target 34x24px — “root”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Stage”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Commit”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “↑”
- **U1** 9 raw buttons vs 3 library — {"desk-light": 2, "desk-wing": 3, "desk-sortable-table-sort": 3, "desk-mic": 1}

</details>

### Roadmap pullout (FallbackPullout)  <sub>`pullout-roadmap`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:roadmap`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Story pullout (FallbackPullout)  <sub>`pullout-story`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:story`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Thread pullout  <sub>`pullout-thread`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:thread`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 35 | 0 | 3 | 0/0 | 0 | 0 | 7 | n/a | 2/12 | 0 | 3 | 12 | 0 | 0 | 0 | 3202 | M1, M10, M3, M7, M8, U1 |
| rich | 393 | ok | 42 | 0 | 1 | 0/0 | 0 | 0 | 7 | 12 | 2/12 | 0 | 3 | 11 | 0 | 0 | 0 | 3201 | M1, M10, M3, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 35px — widest child `div#pullout:th_0659b3944c5e > div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab` “Project”
- **M3** verb “The platform thread” is outside its window — `div#pullout:th_0659b3944c5e > div.desk-pullout-body.desk-surface-body > div.thread-head > button.thread-title`
- **M3** verb “Call: off” is outside its window — `div.desk-pullout-body.desk-surface-body > div.thread-head > div.thread-head-instruments > button.thread-call-chip.thread-call-chip--off`
- **M3** verb “Project” is outside its window — `div#pullout:th_0659b3944c5e > div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab`
- **M4** tab bar `div#desk-next > div#pullout:th_0659b3944c5e > div.thread-foot > div.thread-mode-tabs`: Desk, Interview, Chase, Draft, Plan, Project
- **M7** 11px — “CALL” `div.desk-pullout-body.desk-surface-body > div.thread-head > div.thread-head-instruments > button.thread-call-chip.thread-call-chip--off`
- **M7** 11px — “Desk” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** 11px — “Interview” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** 11px — “Chase” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** 11px — “Draft” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** 11px — “Plan” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “CALL”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 13px — “Send”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (9); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 12 raw buttons vs 1 library — {"desk-light": 3, "thread-title": 1, "thread-call-chip": 1, "thread-mode-tab": 6, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 42px — widest child `div#pullout:th_0659b3944c5e > div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab` “Project”
- **M3** verb “Project” is outside its viewport — `div#pullout:th_0659b3944c5e > div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab`
- **M4** tab bar `div#desk-next > div#pullout:th_0659b3944c5e > div.thread-foot > div.thread-mode-tabs`: Desk, Interview, Chase, Draft, Plan, Project
- **M7** 11px — “CALL” `div.desk-pullout-body.desk-surface-body > div.thread-head > div.thread-head-instruments > button.thread-call-chip.thread-call-chip--off`
- **M7** 11px — “Desk” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** 11px — “Interview” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** 11px — “Chase” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** 11px — “Draft” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** 11px — “Plan” `div.thread-foot > div.thread-mode-tabs > button.thread-mode-tab > span.thread-mode-label`
- **M7** target 16x14px — “Close The platform thread”
- **M7** target 16x14px — “Minimize The platform thread”
- **M7** target 339x22px — “The platform thread”
- **M7** target 42x21px — “Call: off”
- **M7** target 56x19px — “Desk”
- **M7** target 91x19px — “Interview”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “CALL”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 13px — “Send”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (9); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 11 raw buttons vs 1 library — {"desk-light": 2, "thread-title": 1, "thread-call-chip": 1, "thread-mode-tab": 6, "desk-mic": 1}

</details>

### Workbench pullout (FallbackPullout)  <sub>`pullout-workbench`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:workbench`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0+1in | 1 | 5 | 0/0 | 0 | 1 | 13 | n/a | 2/45 | 0 | 3 | 25 | 0 | 0 | 0 | 3246 | M1, M10, M2, M3, M6, M7, M8, U1 |
| rich | 393 | ok | 0+1in | 1 | 13 | 0/0 | 0 | 1 | 13 | 24 | 2/45 | 0 | 3 | 24 | 0 | 0 | 0 | 3293 | M1, M10, M2, M3, M6, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1 (inner)** `div#desk-next > div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` overflows by 4px — “The platform workbench”
- **M2** `div#desk-next > div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` hides 4px on x — “The platform workbench”
- **M3** verb “Choose default” is outside its window — `div.contextual-assignment > article.capability-assignment-row > div > button.btn.btn--ghost`
- **M3** verb “Manual” is outside its window — `div.wb-config-panel > section.surface-section > div.wb-start-mode > button.desk-chip`
- **M3** verb “Schedule” is outside its window — `div.wb-config-panel > section.surface-section > div.wb-start-mode > button.desk-chip`
- **M3** verb “Event” is outside its window — `div.wb-config-panel > section.surface-section > div.wb-start-mode > button.desk-chip`
- **M3** verb “Idle” is outside its window — `div.wb-config-panel > section.surface-section > div.wb-start-mode > button.desk-chip`
- **M4** tab bar `div#desk-next > div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Items, Runs, Memory
- **M4** tab bar `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Items, Runs, Memory
- **M6** “No default model” appears 2x
- **M7** 10px — “Items” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runs” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Memory” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10.83px — “· Bind an agent first” `header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.desk-chip > small.quiet`
- **M7** 10px — “▴ Collapse” `div#workbench:workbench_a2bf46588a6c > div.desk-surface-body.wb-body > div.wb-config-panel > button.wb-config-collapse.desk-chip`
- **M7** 10px — “AGENT” `div.wb-config-panel > section.surface-section > header.surface-section-head > h3`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 13px — “Add”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “~/.holdspeak/workbenches/workbench_a2bf46588a6c/”
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (19); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (17); Arial (9)
- **U1** 25 raw buttons vs 2 library — {"desk-light": 3, "surface-edit-in-place": 1, "desk-wing": 3, "desk-chip": 8, "wb-config-collapse": 1, "desk-mic": 2, "surface-row-open": 7}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1 (inner)** `div.surface-row-line > button.surface-row-open > span.surface-row-text > strong` overflows by 28px — “The reviewer — an agent with a deliberately long name”
- **M2** `div.surface-row-line > button.surface-row-open > span.surface-row-text > strong` hides 28px on x — “The reviewer — an agent with a deliberately long name”
- **M3** verb “Close The platform workbench” is outside its viewport — `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-close`
- **M3** verb “Minimize The platform workbench” is outside its viewport — `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-min`
- **M3** verb “Edit Workbench name” is outside its viewport — `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > button.surface-edit-in-place.wb-title-edit`
- **M3** verb “Items” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M3** verb “Runs” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M3** verb “Memory” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M4** tab bar `div#desk-next > div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Items, Runs, Memory
- **M4** tab bar `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Items, Runs, Memory
- **M6** “No default model” appears 2x
- **M7** 10px — “Items” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runs” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Memory” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10.83px — “· Bind an agent first” `header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.desk-chip > small.quiet`
- **M7** 10px — “▴ Collapse” `div#workbench:workbench_a2bf46588a6c > div.desk-surface-body.wb-body > div.wb-config-panel > button.wb-config-collapse.desk-chip`
- **M7** 10px — “AGENT” `div.wb-config-panel > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close The platform workbench”
- **M7** target 16x14px — “Minimize The platform workbench”
- **M7** target 166x20px — “Edit Workbench name”
- **M7** target 59x23px — “Items”
- **M7** target 52x23px — “Runs”
- **M7** target 66x23px — “Memory”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 13px — “Add”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “~/.holdspeak/workbenches/workbench_a2bf46588a6c/”
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (19); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (17); Arial (9)
- **U1** 24 raw buttons vs 2 library — {"desk-light": 2, "surface-edit-in-place": 1, "desk-wing": 3, "desk-chip": 8, "wb-config-collapse": 1, "desk-mic": 2, "surface-row-open": 7}

</details>

### Workflow pullout  <sub>`pullout-workflow`</sub>

- Family: pullout · Door: double-click the object on the Floor
- Opened by the rig via: `pullout:workflow`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 162 | 0 | 15 | 1/1 | 0 | 0 | 7 | n/a | 5/28 | 0 | 3 | 21 | 1 | 0 | 0 | 3189 | M1, M10, M3, M4, M7, M8, U1 |
| rich | 393 | ok | 169 | 0 | 12 | 1/1 | 0 | 0 | 7 | 23 | 5/28 | 0 | 3 | 20 | 1 | 0 | 0 | 3202 | M1, M10, M3, M4, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 162px — widest child `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > span.desk-project-choice` “+ Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3…”
- **M3** verb “+ Decisions” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Inbox” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Meetings” is outside its window — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Personal” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Platform — çalışma zone” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Reference” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M4** fold “Filed · Desk root” is closed over: “Zone+ Decisions+ Inbox+ Meetings+ Personal+ Platform — çalışma zone+ Reference+ …”
- **M7** 11px — “Edit Workflow” `div#pullout:workflow_2c978751fc0d > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.btn.btn--ghost`
- **M7** 10px — “Steps” `div#pullout:workflow_2c978751fc0d > div.desk-pullout-body.desk-surface-body > section > h3`
- **M7** 10px — “Zone” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Knowledge” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Projects” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 11px — “Dictate about this” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 13px — “Run”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Edit”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Zone”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Knowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Projects”
- **M10** Arial (17); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (8); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (3)
- **U1** 21 raw buttons vs 3 library — {"desk-light": 3, "desk-mic": 1, "desk-chip": 17}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 169px — widest child `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > span.desk-project-choice` “+ Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3…”
- **M3** verb “+ Personal” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Platform — çalışma zone” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Reference” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Work” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Custody — what the ledger holds” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M3** verb “+ Everyday context” is outside its viewport — `div.desk-pullout-filed > div.desk-pullout-filed-axis > div.desk-pullout-lineage > button.desk-chip.quiet`
- **M4** fold “Filed · Desk root” is closed over: “Zone+ Decisions+ Inbox+ Meetings+ Personal+ Platform — çalışma zone+ Reference+ …”
- **M7** 11px — “Edit Workflow” `div#pullout:workflow_2c978751fc0d > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.btn.btn--ghost`
- **M7** 10px — “Steps” `div#pullout:workflow_2c978751fc0d > div.desk-pullout-body.desk-surface-body > section > h3`
- **M7** 10px — “Zone” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Knowledge” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 10px — “Projects” `div.gadget-fold-body > div.desk-pullout-filed > div.desk-pullout-filed-axis > span.surface-eyebrow`
- **M7** 11px — “Dictate about this” `footer.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Nightly ingest”
- **M7** target 16x14px — “Minimize Nightly ingest”
- **M7** target 104x24px — “Edit Workflow”
- **M7** target 34x34px — “Speak to fill run nightly ingest materia…”
- **M7** target 51x27px — “Run”
- **M7** target 95x27px — “Assignments”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 13px — “Run”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Edit”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Zone”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Knowledge”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Projects”
- **M10** Arial (17); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (8); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (3)
- **U1** 20 raw buttons vs 3 library — {"desk-light": 2, "desk-mic": 1, "desk-chip": 17}

</details>

### Settings — Guide wing  <sub>`settings-guide`</sub>

- Family: settings · Door: Go > Settings > Guide
- Opened by the rig via: `custom:settings-wing:Guide`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | n/a | 0/39 | 0 | 2 | 5 | 0 | 0 | 0 | 3421 | M4, M6, M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | 6 | 0/39 | 0 | 2 | 4 | 0 | 0 | 0 | 3458 | M4, M6, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | n/a | 0/39 | 0 | 2 | 5 | 0 | 0 | 0 | 3431 | M4, M6, M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | 6 | 0/39 | 0 | 2 | 4 | 0 | 0 | 0 | 3466 | M4, M6, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 124x24px — “Run runtime test”
- **M7** target 117x24px — “Check readiness”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 124x24px — “Run runtime test”
- **M7** target 117x24px — “Check readiness”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings module — Assignments  <sub>`settings-module-assignments`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'Assignments' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:Assignments`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Settings module — Connections  <sub>`settings-module-integrations`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'Connections' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:Connections`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5524 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5444 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5559 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5553 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings module — Meetings  <sub>`settings-module-meetings`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'Meetings' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:Meetings`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5433 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5443 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5588 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5553 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings module — Models  <sub>`settings-module-models`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'Models' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:Models`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5464 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5384 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5590 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5561 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings module — Rhythm  <sub>`settings-module-rhythm`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'Rhythm' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:Rhythm`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5446 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5513 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5603 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5469 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings module — Sounds & Presence  <sub>`settings-module-sounds`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'Sounds & Presence' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:Sounds & Presence`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5162 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5169 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5215 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5223 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings module — System  <sub>`settings-module-system`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'System' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:System`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5413 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5513 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5566 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5550 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings module — Voice  <sub>`settings-module-voice`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'Voice' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:Voice`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Settings module — Wallpaper  <sub>`settings-module-wallpaper`</sub>

- Family: settings · Door: Go > Settings > the hub ledger row 'Wallpaper' > Open (web/src/pages/cores/settingsPrefs.tsx:430)
- Opened by the rig via: `custom:settings-module:Wallpaper`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5391 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5452 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/5 | 0 | 1 | 5 | 0 | 0 | 0 | 5696 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/5 | 0 | 1 | 4 | 0 | 0 | 0 | 5450 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “« PREFS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-verbs > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 64x20px — “« PREFS”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 2}

</details>

### Settings — Settings wing  <sub>`settings-settings`</sub>

- Family: settings · Door: Go > Settings
- Opened by the rig via: `custom:settings-wing:Settings`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | n/a | 0/39 | 0 | 2 | 5 | 0 | 0 | 0 | 3425 | M4, M6, M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | 6 | 0/39 | 0 | 2 | 4 | 0 | 0 | 0 | 3407 | M4, M6, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | n/a | 0/39 | 0 | 2 | 5 | 0 | 0 | 0 | 3458 | M4, M6, M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 3/4 | 0 | 2 | 6 | 6 | 0/39 | 0 | 2 | 4 | 0 | 0 | 0 | 3547 | M4, M6, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 124x24px — “Run runtime test”
- **M7** target 117x24px — “Check readiness”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** fold “Apple Silicon with MLX” is closed over: “INSTALLuv pip install -e '.[dictation-mlx]'MODEL PATH~/Models/mlx/SELECTDICTATIO…”
- **M4** fold “Local GGUF with llama.cpp” is closed over: “INSTALLuv pip install -e '.[dictation-llama]'MODEL PATH~/Models/gguf/VALUEFULL M…”
- **M4** fold “OpenAI-compatible endpoint” is closed over: “INSTALLuv pip install -e '.[dictation-openai]'DESTINATIONSERVER URL · MODELKEY E…”
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M4** tab bar `div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Settings, Guide
- **M6** “INSTALL” appears 4x
- **M6** “MODEL PATH” appears 2x
- **M7** 10px — “Settings” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Guide” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runtime reference” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Verify” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Run runtime test” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** 11px — “Check readiness” `span.surface-row-main > span.surface-row-text > small > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Settings”
- **M7** target 16x14px — “Minimize Settings”
- **M7** target 79x23px — “Settings”
- **M7** target 59x23px — “Guide”
- **M7** target 124x24px — “Run runtime test”
- **M7** target 117x24px — “Check readiness”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 2}

</details>

### The ＋Create menu (empty Floor only)  <sub>`state-create-menu`</sub>

- Family: chrome · Door: the Floor's ＋Create verb — it renders ONLY inside EmptyDesk (web/src/desk/components/EmptyDesk.tsx:37), so a furnished Floor has no Create face
- Opened by the rig via: `custom:create-menu`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Delivery / RAILS board  <sub>`state-delivery`</sub>

- Family: state · Door: the dock's Delivery verb
- Opened by the rig via: `custom:delivery`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 10 | n/a | 1/13 | 0 | 1 | 4 | 0 | 0 | 0 | 4317 | M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 10 | 5 | 1/13 | 0 | 1 | 3 | 0 | 0 | 0 | 4303 | M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 10 | n/a | 1/13 | 0 | 1 | 4 | 0 | 0 | 0 | 4336 | M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 10 | 5 | 1/13 | 0 | 1 | 3 | 0 | 0 | 0 | 4337 | M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “▤ Delivery” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.desk-mc-title`
- **M7** 10px — “Hub” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > span.gadget-chip.gadget-chip-egress`
- **M7** 11px — “↻” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.btn.btn--ghost`
- **M7** 11px — “%0 · local” `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell`
- **M7** 11px — “UNGATED” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell > span.surface-token`
- **M7** 10px — “Integration” `div#delivery-board > div.desk-pullout-body.desk-surface-body > section.gadget-group > h4.gadget-group-label`
- **M8** 4.02:1 (needs 4.5) rgb(168, 110, 74) on rgb(26, 29, 37) at 10px — “Hub”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 3, "desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 10px — “▤ Delivery” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.desk-mc-title`
- **M7** 10px — “Hub” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > span.gadget-chip.gadget-chip-egress`
- **M7** 11px — “↻” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.btn.btn--ghost`
- **M7** 11px — “%0 · local” `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell`
- **M7** 11px — “UNGATED” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell > span.surface-token`
- **M7** 10px — “Integration” `div#delivery-board > div.desk-pullout-body.desk-surface-body > section.gadget-group > h4.gadget-group-label`
- **M7** target 16x14px — “Close Delivery”
- **M7** target 16x14px — “Minimize Delivery”
- **M7** target 25x24px — “Refresh”
- **M7** target 345x26px — “ccgram%0 · localUNGATED”
- **M7** target 20x20px — “Speak GitHub repo”
- **M8** 4.02:1 (needs 4.5) rgb(168, 110, 74) on rgb(26, 29, 37) at 10px — “Hub”
- **U1** 3 raw buttons vs 1 library — {"desk-light": 2, "desk-mic": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “▤ Delivery” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.desk-mc-title`
- **M7** 10px — “Hub” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > span.gadget-chip.gadget-chip-egress`
- **M7** 11px — “↻” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.btn.btn--ghost`
- **M7** 11px — “%0 · local” `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell`
- **M7** 11px — “UNGATED” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell > span.surface-token`
- **M7** 10px — “Integration” `div#delivery-board > div.desk-pullout-body.desk-surface-body > section.gadget-group > h4.gadget-group-label`
- **M8** 4.02:1 (needs 4.5) rgb(168, 110, 74) on rgb(26, 29, 37) at 10px — “Hub”
- **U1** 4 raw buttons vs 1 library — {"desk-light": 3, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 10px — “▤ Delivery” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.desk-mc-title`
- **M7** 10px — “Hub” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > span.gadget-chip.gadget-chip-egress`
- **M7** 11px — “↻” `div#delivery-board > header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.btn.btn--ghost`
- **M7** 11px — “%0 · local” `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell`
- **M7** 11px — “UNGATED” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell > span.surface-token`
- **M7** 10px — “Integration” `div#delivery-board > div.desk-pullout-body.desk-surface-body > section.gadget-group > h4.gadget-group-label`
- **M7** target 16x14px — “Close Delivery”
- **M7** target 16x14px — “Minimize Delivery”
- **M7** target 25x24px — “Refresh”
- **M7** target 345x26px — “ccgram%0 · localUNGATED”
- **M7** target 20x20px — “Speak GitHub repo”
- **M8** 4.02:1 (needs 4.5) rgb(168, 110, 74) on rgb(26, 29, 37) at 10px — “Hub”
- **U1** 3 raw buttons vs 1 library — {"desk-light": 2, "desk-mic": 1}

</details>

### The Desk menu  <sub>`state-desk-menu`</sub>

- Family: chrome · Door: the menu bar
- Opened by the rig via: `custom:bar-menu:Desk`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | n/a | 0/21 | 0 | 1 | 13 | 0 | 0 | 0 | 2896 | M7, U1 |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | n/a | 0/21 | 0 | 1 | 13 | 0 | 0 | 0 | 2999 | M7, U1 |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “N” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⇧” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “N” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **U1** 13 raw buttons vs 0 library — {"(no class)": 13}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “N” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⇧” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “N” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **U1** 13 raw buttons vs 0 library — {"(no class)": 13}

</details>

### The First Sentence gate  <sub>`state-first-sentence`</sub>

- Family: state · Door: arrival on a cold desk
- Opened by the rig via: `custom:first-sentence`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | n/a | 2/7 | 0 | 2 | 2 | 0 | 0 | 0 | 3145 | M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | 4 | 2/7 | 0 | 2 | 2 | 0 | 0 | 0 | 3066 | M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “Voice typing” `div#desk-next > main.chair.chair-first-value > section.desk-first-words > span.surface-eyebrow`
- **M8** 4.21:1 (needs 4.5) rgb(118, 126, 141) on rgb(26, 27, 31) at 12px — “Copy”
- **M8** 4.21:1 (needs 4.5) rgb(118, 126, 141) on rgb(26, 27, 31) at 12px — “Keep as Note”
- **U1** 2 raw buttons vs 3 library — {"desk-first-talk": 1, "desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 10px — “Voice typing” `div#desk-next > main.chair.chair-first-value > section.desk-first-words > span.surface-eyebrow`
- **M7** target 20x20px — “Speak Your dictated text”
- **M7** target 55x28px — “Copy”
- **M7** target 112x28px — “Keep as Note”
- **M7** target 127x28px — “Continue later”
- **M8** 4.21:1 (needs 4.5) rgb(118, 126, 141) on rgb(26, 27, 31) at 12px — “Copy”
- **M8** 4.21:1 (needs 4.5) rgb(118, 126, 141) on rgb(26, 27, 31) at 12px — “Keep as Note”
- **U1** 2 raw buttons vs 3 library — {"desk-first-talk": 1, "desk-mic": 1}

</details>

### The Go menu  <sub>`state-go-menu`</sub>

- Family: chrome · Door: the menu bar
- Opened by the rig via: `custom:go-menu`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 13 | n/a | 0/43 | 0 | 1 | 15 | 0 | 0 | 0 | 2857 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 13 | 15 | 0/43 | 0 | 1 | 15 | 0 | 0 | 0 | 2878 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 13 | n/a | 0/43 | 0 | 1 | 15 | 0 | 0 | 0 | 2947 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 13 | 15 | 0/43 | 0 | 1 | 15 | 0 | 0 | 0 | 2961 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “1” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “I” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “2” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **U1** 15 raw buttons vs 0 library — {"(no class)": 15}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “1” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “I” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “2” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** target 371x28px — “⌁Speak⌘1”
- **M7** target 371x28px — “✦Ask AI⌘I”
- **M7** target 371x28px — “▣Meetings⌘2”
- **M7** target 371x28px — “⚙Settings⌘4”
- **M7** target 371x28px — “▧Change places⌘⇧P”
- **M7** target 371x28px — “◉Agents and coder sessions⌘3”
- **U1** 15 raw buttons vs 0 library — {"(no class)": 15}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “1” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “I” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “2” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **U1** 15 raw buttons vs 0 library — {"(no class)": 15}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “1” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “I” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “2” `nav.desk-menu-list.desk-work-menu > button > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** target 371x28px — “⌁Speak⌘1”
- **M7** target 371x28px — “✦Ask AI⌘I”
- **M7** target 371x28px — “▣Meetings⌘2”
- **M7** target 371x28px — “⚙Settings⌘4”
- **M7** target 371x28px — “▧Change places⌘⇧P”
- **M7** target 371x28px — “◉Agents and coder sessions⌘3”
- **U1** 15 raw buttons vs 0 library — {"(no class)": 15}

</details>

### The Interview  <sub>`state-interview`</sub>

- Family: state · Door: a Project Room > Interview
- Opened by the rig via: `custom:interview`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Meetings — a queued meeting  <sub>`state-meetings-queued`</sub>

- Family: state · Door: Go > Meetings
- Opened by the rig via: `custom:meetings`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3281 | U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3198 | M7, U1 |

<details><summary>rich @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

### The Object menu  <sub>`state-object-menu`</sub>

- Family: chrome · Door: the menu bar
- Opened by the rig via: `custom:bar-menu:Object`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 4 | n/a | 1/14 | 0 | 1 | 10 | 0 | 0 | 0 | 2825 | M7, M8, U1 |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 4 | n/a | 1/14 | 0 | 1 | 10 | 0 | 0 | 0 | 2941 | M7, M8, U1 |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “· Select a Project” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-label > small.quiet`
- **M7** 10px — “F2” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “Delete” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “Select an object” `main#main > div#desk-next > nav.desk-menu-list.desk-work-menu > span.desk-menu-ghost-hint`
- **M8** 3.6:1 (needs 4.5) rgb(118, 126, 141) on rgb(36, 40, 51) at 10px — “Select an object”
- **U1** 10 raw buttons vs 0 library — {"is-ghost": 10}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “· Select a Project” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-label > small.quiet`
- **M7** 10px — “F2” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “Delete” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “Select an object” `main#main > div#desk-next > nav.desk-menu-list.desk-work-menu > span.desk-menu-ghost-hint`
- **M8** 3.6:1 (needs 4.5) rgb(118, 126, 141) on rgb(36, 40, 51) at 10px — “Select an object”
- **U1** 10 raw buttons vs 0 library — {"is-ghost": 10}

</details>

### The ⌘K palette  <sub>`state-palette`</sub>

- Family: chrome · Door: ⌘K
- Opened by the rig via: `custom:palette`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0+1in | 1 | 0 | 0/0 | 0 | 0 | 40 | n/a | 31/99 | 0 | 2 | 30 | 0 | 0 | 0 | 2879 | M1, M2, M7, M8, U1 |
| cold | 393 | ok | 0+1in | 1 | 1 | 0/0 | 0 | 0 | 40 | 30 | 31/99 | 0 | 2 | 30 | 0 | 0 | 0 | 2920 | M1, M2, M3, M7, M8, U1 |
| rich | 1440 | ok | 0+3in | 3 | 5 | 0/0 | 0 | 1 | 46 | n/a | 34/111 | 0 | 2 | 33 | 0 | 0 | 0 | 2904 | M1, M2, M3, M6, M7, M8, U1 |
| rich | 393 | ok | 0+4in | 4 | 6 | 0/0 | 0 | 1 | 46 | 33 | 34/111 | 0 | 2 | 33 | 0 | 0 | 0 | 2918 | M1, M2, M3, M6, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M1 (inner)** `div#desk-next > aside#desk-tool-shelf > label.desk-tool-search > span.sr-only` overflows by 187px — “Search tools and Desk items”
- **M2** `div#desk-next > aside#desk-tool-shelf > label.desk-tool-search > span.sr-only` hides 187px on x — “Search tools and Desk items”
- **M7** 10px — “VERBS” `aside#desk-tool-shelf > ul#desk-palette-listbox > li > span.desk-deck-band`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.open-people > span.desk-deck-kind`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.intelligence-brief > span.desk-deck-kind`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.new-note > span.desk-deck-kind`
- **M7** 11px — “⌘N” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.new-note > kbd`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.new-decision > span.desk-deck-kind`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “▸”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Open People”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **U1** 30 raw buttons vs 0 library — {"desk-mic": 1, "desk-deck-row": 29}

</details>

<details><summary>cold @393 — evidence</summary>

- **M1 (inner)** `div#desk-next > aside#desk-tool-shelf > label.desk-tool-search > span.sr-only` overflows by 187px — “Search tools and Desk items”
- **M2** `div#desk-next > aside#desk-tool-shelf > label.desk-tool-search > span.sr-only` hides 187px on x — “Search tools and Desk items”
- **M3** verb “SModelsSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:models`
- **M7** 10px — “VERBS” `aside#desk-tool-shelf > ul#desk-palette-listbox > li > span.desk-deck-band`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.open-people > span.desk-deck-kind`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.intelligence-brief > span.desk-deck-kind`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.new-note > span.desk-deck-kind`
- **M7** 11px — “⌘N” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.new-note > kbd`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.new-decision > span.desk-deck-kind`
- **M7** target 20x20px — “Speak Search tools and Desk items”
- **M7** target 363x26px — “▸Open PeopleVERB”
- **M7** target 363x26px — “▸Show today's briefVERB”
- **M7** target 363x26px — “▸New NoteVERB⌘N”
- **M7** target 363x26px — “▸New DecisionVERB⌘⇧N”
- **M7** target 363x26px — “▸New KnowledgeVERB”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “▸”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Open People”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **U1** 30 raw buttons vs 0 library — {"desk-mic": 1, "desk-deck-row": 29}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1 (inner)** `div#desk-next > aside#desk-tool-shelf > label.desk-tool-search > span.sr-only` overflows by 187px — “Search tools and Desk items”
- **M1 (inner)** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-f427b66bc8a4 > span.desk-deck-label` overflows by 79px — “Open Kernel: the ledger, the receipts, and the undo”
- **M1 (inner)** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-2120c22ff56e > span.desk-deck-label` overflows by 331px — “Open Platform Modernisation — Ingest, Custody and the Long Memory (Wav…”
- **M2** `div#desk-next > aside#desk-tool-shelf > label.desk-tool-search > span.sr-only` hides 187px on x — “Search tools and Desk items”
- **M2** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-f427b66bc8a4 > span.desk-deck-label` hides 79px on x — “Open Kernel: the ledger, the receipts, and the undo”
- **M2** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-2120c22ff56e > span.desk-deck-label` hides 331px on x — “Open Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3)”
- **M3** verb “SSounds & PresenceSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:sounds`
- **M3** verb “SWallpaperSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:wallpaper`
- **M3** verb “SMeetingsSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:meetings`
- **M3** verb “SRhythmSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:rhythm`
- **M3** verb “SModelsSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:models`
- **M6** “VERBS” appears 2x
- **M7** 10px — “VERBS” `aside#desk-tool-shelf > ul#desk-palette-listbox > li > span.desk-deck-band`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.open-people > span.desk-deck-kind`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.intelligence-brief > span.desk-deck-kind`
- **M7** 10px — “PROJECTS” `aside#desk-tool-shelf > ul#desk-palette-listbox > li > span.desk-deck-band`
- **M7** 10px — “PROJECT” `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-f427b66bc8a4 > span.desk-deck-kind`
- **M7** 10px — “PROJECT” `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-086197d84e2c > span.desk-deck-kind`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “▸”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Open People”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “PROJECT”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “PROJECT”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “PROJECT”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **U1** 33 raw buttons vs 0 library — {"desk-mic": 1, "desk-deck-row": 32}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1 (inner)** `div#desk-next > aside#desk-tool-shelf > label.desk-tool-search > span.sr-only` overflows by 187px — “Search tools and Desk items”
- **M1 (inner)** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-f427b66bc8a4 > span.desk-deck-label` overflows by 98px — “Open Kernel: the ledger, the receipts, and the undo”
- **M1 (inner)** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-086197d84e2c > span.desk-deck-label` overflows by 19px — “Open Küresel Müşteri Portalı — discovery”
- **M1 (inner)** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-2120c22ff56e > span.desk-deck-label` overflows by 350px — “Open Platform Modernisation — Ingest, Custody and the Long Memory (Wav…”
- **M2** `div#desk-next > aside#desk-tool-shelf > label.desk-tool-search > span.sr-only` hides 187px on x — “Search tools and Desk items”
- **M2** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-f427b66bc8a4 > span.desk-deck-label` hides 98px on x — “Open Kernel: the ledger, the receipts, and the undo”
- **M2** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-086197d84e2c > span.desk-deck-label` hides 19px on x — “Open Küresel Müşteri Portalı — discovery”
- **M2** `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-2120c22ff56e > span.desk-deck-label` hides 350px on x — “Open Platform Modernisation — Ingest, Custody and the Long Memory (Wave 3)”
- **M3** verb “SVoiceSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:voice`
- **M3** verb “SSounds & PresenceSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:sounds`
- **M3** verb “SWallpaperSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:wallpaper`
- **M3** verb “SMeetingsSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:meetings`
- **M3** verb “SRhythmSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:rhythm`
- **M3** verb “SModelsSETTINGS” is outside its viewport — `aside#desk-tool-shelf > ul#desk-palette-listbox > li > button#desk-palette-option-settings:models`
- **M6** “VERBS” appears 2x
- **M7** 10px — “VERBS” `aside#desk-tool-shelf > ul#desk-palette-listbox > li > span.desk-deck-band`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.open-people > span.desk-deck-kind`
- **M7** 10px — “VERB” `ul#desk-palette-listbox > li > button#desk-palette-option-desk.intelligence-brief > span.desk-deck-kind`
- **M7** 10px — “PROJECTS” `aside#desk-tool-shelf > ul#desk-palette-listbox > li > span.desk-deck-band`
- **M7** 10px — “PROJECT” `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-f427b66bc8a4 > span.desk-deck-kind`
- **M7** 10px — “PROJECT” `ul#desk-palette-listbox > li > button#desk-palette-option-project.open.proj-086197d84e2c > span.desk-deck-kind`
- **M7** target 20x20px — “Speak Search tools and Desk items”
- **M7** target 363x26px — “▸Open PeopleVERB”
- **M7** target 363x26px — “▸Show today's briefVERB”
- **M7** target 363x26px — “▣Open Kernel: the ledger, the receipts, …”
- **M7** target 363x26px — “▣Open Küresel Müşteri Portalı — discover…”
- **M7** target 363x26px — “▣Open Platform Modernisation — Ingest, C…”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “▸”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Open People”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “PROJECT”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “PROJECT”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “PROJECT”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “VERB”
- **U1** 33 raw buttons vs 0 library — {"desk-mic": 1, "desk-deck-row": 32}

</details>

### Project Room  <sub>`state-room`</sub>

- Family: state · Door: Go > Desk memory (scoped to a project)
- Opened by the rig via: `custom:room`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | n/a | 0/2 | 0 | 2 | 3 | 0 | 0 | 0 | 3108 | U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 2 | 0/2 | 0 | 2 | 2 | 0 | 0 | 0 | 3090 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | n/a | 0/9 | 0 | 1 | 4 | 0 | 0 | 0 | 3227 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | 9 | 0/9 | 0 | 1 | 3 | 0 | 0 | 0 | 3196 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **U1** 3 raw buttons vs 0 library — {"desk-light": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** target 16x14px — “Close Desk memory”
- **M7** target 16x14px — “Minimize Desk memory”
- **U1** 2 raw buttons vs 0 library — {"desk-light": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “SEARCH THE DESK” `div.room-body.desk-memory-body > header.recall-head > div.recall-head-tokens > span.surface-token`
- **M7** 11px — “Search” `div.room-body.desk-memory-body > div.desk-chat-well.recall-well > div.desk-chat-composer > button.btn.btn--secondary`
- **M7** 11px — “All” `div.room-body.desk-memory-body > div.recall-filters > span.surface-filter-tokens > button.btn.btn--secondary`
- **M7** 11px — “Decisions” `div.room-body.desk-memory-body > div.recall-filters > span.surface-filter-tokens > button.btn.btn--ghost`
- **M7** 11px — “Commitments” `div.room-body.desk-memory-body > div.recall-filters > span.surface-filter-tokens > button.btn.btn--ghost`
- **M7** 11px — “Briefs” `div.room-body.desk-memory-body > div.recall-filters > span.surface-filter-tokens > button.btn.btn--ghost`
- **U1** 4 raw buttons vs 6 library — {"desk-light": 3, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 10px — “SEARCH THE DESK” `div.room-body.desk-memory-body > header.recall-head > div.recall-head-tokens > span.surface-token`
- **M7** 11px — “Search” `div.room-body.desk-memory-body > div.desk-chat-well.recall-well > div.desk-chat-composer > button.btn.btn--secondary`
- **M7** 11px — “All” `div.room-body.desk-memory-body > div.recall-filters > span.surface-filter-tokens > button.btn.btn--secondary`
- **M7** 11px — “Decisions” `div.room-body.desk-memory-body > div.recall-filters > span.surface-filter-tokens > button.btn.btn--ghost`
- **M7** 11px — “Commitments” `div.room-body.desk-memory-body > div.recall-filters > span.surface-filter-tokens > button.btn.btn--ghost`
- **M7** 11px — “Briefs” `div.room-body.desk-memory-body > div.recall-filters > span.surface-filter-tokens > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Desk memory”
- **M7** target 16x14px — “Minimize Desk memory”
- **M7** target 20x20px — “Dictate into the search”
- **M7** target 58x24px — “Search desk memory”
- **M7** target 48x26px — “Filter: All”
- **M7** target 91x26px — “Filter: Decisions”
- **U1** 3 raw buttons vs 6 library — {"desk-light": 2, "desk-mic": 1}

</details>

### Panes (the session picker)  <sub>`state-terminal`</sub>

- Family: state · Door: the dock's Panes verb
- Opened by the rig via: `custom:terminal`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 279 | 0 | 0 | 0/0 | 0 | 0 | 2 | n/a | 1/4 | 0 | 2 | 3 | 0 | 0 | 0 | 4326 | M1, M7, M8, U1 |
| cold | 393 | ok | 279 | 0 | 2 | 0/0 | 0 | 0 | 2 | 3 | 1/4 | 0 | 2 | 3 | 0 | 0 | 0 | 4330 | M1, M3, M7, M8, U1 |
| rich | 1440 | ok | 279 | 0 | 0 | 0/0 | 0 | 0 | 2 | n/a | 1/4 | 0 | 2 | 3 | 0 | 0 | 0 | 4345 | M1, M7, M8, U1 |
| rich | 393 | ok | 279 | 0 | 2 | 0/0 | 0 | 0 | 2 | 3 | 1/4 | 0 | 2 | 3 | 0 | 0 | 0 | 4355 | M1, M3, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M1** content overflows its window by 279px — widest child `main#main > div#desk-next > div.desk-panepicker.is-open > div.desk-panepicker-list` “＋SPAWN%0ccgram · zsh”
- **M7** 9px — “SPAWN” `div.desk-panepicker-list > div.desk-panepicker-spawn > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 11px — “ccgram · zsh” `div.desk-panepicker.is-open > div.desk-panepicker-list > button.desk-panepicker-item.is-active > span.desk-panepicker-meta`
- **M8** 4.29:1 (needs 4.5) rgb(168, 110, 74) on rgb(20, 22, 28) at 12px — “%0”
- **U1** 3 raw buttons vs 0 library — {"desk-mic": 1, "gadget-transport-key": 1, "desk-panepicker-item": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M1** content overflows its window by 279px — widest child `main#main > div#desk-next > div.desk-panepicker.is-open > div.desk-panepicker-list` “＋SPAWN%0ccgram · zsh”
- **M3** verb “SPAWN” is outside its viewport — `div.desk-panepicker.is-open > div.desk-panepicker-list > div.desk-panepicker-spawn > button.gadget-transport-key`
- **M3** verb “%0ccgram · zsh” is outside its viewport — `div#desk-next > div.desk-panepicker.is-open > div.desk-panepicker-list > button.desk-panepicker-item.is-active`
- **M7** 9px — “SPAWN” `div.desk-panepicker-list > div.desk-panepicker-spawn > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 11px — “ccgram · zsh” `div.desk-panepicker.is-open > div.desk-panepicker-list > button.desk-panepicker-item.is-active > span.desk-panepicker-meta`
- **M7** target 20x30px — “Speak New session name”
- **M7** target 67x30px — “SPAWN”
- **M7** target 265x30px — “%0ccgram · zsh”
- **M8** 4.29:1 (needs 4.5) rgb(168, 110, 74) on rgb(20, 22, 28) at 12px — “%0”
- **U1** 3 raw buttons vs 0 library — {"desk-mic": 1, "gadget-transport-key": 1, "desk-panepicker-item": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 279px — widest child `main#main > div#desk-next > div.desk-panepicker.is-open > div.desk-panepicker-list` “＋SPAWN%0ccgram · zsh”
- **M7** 9px — “SPAWN” `div.desk-panepicker-list > div.desk-panepicker-spawn > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 11px — “ccgram · zsh” `div.desk-panepicker.is-open > div.desk-panepicker-list > button.desk-panepicker-item.is-active > span.desk-panepicker-meta`
- **M8** 4.29:1 (needs 4.5) rgb(168, 110, 74) on rgb(20, 22, 28) at 12px — “%0”
- **U1** 3 raw buttons vs 0 library — {"desk-mic": 1, "gadget-transport-key": 1, "desk-panepicker-item": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 279px — widest child `main#main > div#desk-next > div.desk-panepicker.is-open > div.desk-panepicker-list` “＋SPAWN%0ccgram · zsh”
- **M3** verb “SPAWN” is outside its viewport — `div.desk-panepicker.is-open > div.desk-panepicker-list > div.desk-panepicker-spawn > button.gadget-transport-key`
- **M3** verb “%0ccgram · zsh” is outside its viewport — `div#desk-next > div.desk-panepicker.is-open > div.desk-panepicker-list > button.desk-panepicker-item.is-active`
- **M7** 9px — “SPAWN” `div.desk-panepicker-list > div.desk-panepicker-spawn > button.gadget-transport-key > span.gadget-transport-word`
- **M7** 11px — “ccgram · zsh” `div.desk-panepicker.is-open > div.desk-panepicker-list > button.desk-panepicker-item.is-active > span.desk-panepicker-meta`
- **M7** target 20x30px — “Speak New session name”
- **M7** target 67x30px — “SPAWN”
- **M7** target 265x30px — “%0ccgram · zsh”
- **M8** 4.29:1 (needs 4.5) rgb(168, 110, 74) on rgb(20, 22, 28) at 12px — “%0”
- **U1** 3 raw buttons vs 0 library — {"desk-mic": 1, "gadget-transport-key": 1, "desk-panepicker-item": 1}

</details>

### Thought window  <sub>`state-thought`</sub>

- Family: state · Door: Speak > a thought
- Opened by the rig via: `custom:thought`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 3/10 | 0 | 3 | 5 | 1 | 0 | 0 | 3202 | M10, M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 6 | 3/10 | 0 | 3 | 4 | 1 | 0 | 0 | 3247 | M10, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “ONE QUESTION” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.thought-note-ask-label`
- **M7** 10px — “NO ENGINE YET” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.surface-token`
- **M7** 11px — “Choose an engine” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > button.btn.btn--secondary`
- **M7** 10px — “READS · NOTHING” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-egress > span.thought-note-reads`
- **M7** 10px — “KEPT” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** 11px — “Change” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-verbs > button.btn.btn--secondary`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Finish”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “ONE QUESTION”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “READS · NOTHING”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (8); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 5 raw buttons vs 3 library — {"desk-light": 3, "surface-edit-in-place": 1, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 11px — “ONE QUESTION” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.thought-note-ask-label`
- **M7** 10px — “NO ENGINE YET” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.surface-token`
- **M7** 11px — “Choose an engine” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > button.btn.btn--secondary`
- **M7** 10px — “READS · NOTHING” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-egress > span.thought-note-reads`
- **M7** 10px — “KEPT” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** 11px — “Change” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-verbs > button.btn.btn--secondary`
- **M7** target 16x14px — “Close Thought”
- **M7** target 16x14px — “Minimize Thought”
- **M7** target 28x28px — “Speak the note”
- **M7** target 124x40px — “Choose an engine”
- **M7** target 58x40px — “Change”
- **M7** target 69x40px — “Finish”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Finish”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “ONE QUESTION”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “READS · NOTHING”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (8); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 4 raw buttons vs 3 library — {"desk-light": 2, "surface-edit-in-place": 1, "desk-mic": 1}

</details>

### Trust window (Data boundaries)  <sub>`state-trust`</sub>

- Family: state · Door: the egress badge in the desk chrome (DeskChrome.tsx:259)
- Opened by the rig via: `custom:trust`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 1 | 0/0 | 0 | 13 | 14 | n/a | 0/135 | 0 | 3 | 4 | 0 | 0 | 0 | 3213 | M10, M3, M6, M7, U1 |
| cold | 393 | ok | 0 | 0 | 1 | 0/0 | 0 | 13 | 14 | 3 | 0/135 | 0 | 3 | 3 | 0 | 0 | 0 | 3133 | M10, M3, M6, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 1 | 0/0 | 0 | 13 | 14 | n/a | 0/135 | 0 | 3 | 4 | 0 | 0 | 0 | 3443 | M10, M3, M6, M7, U1 |
| rich | 393 | ok | 0 | 0 | 1 | 0/0 | 0 | 13 | 14 | 3 | 0/135 | 0 | 3 | 3 | 0 | 0 | 0 | 3436 | M10, M3, M6, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M3** verb “Review privacy settings” is outside its viewport — `div#trust > div.desk-surface-body > p > button.desk-chip.quiet`
- **M6** “Destination” appears 7x
- **M6** “Operation” appears 7x
- **M6** “Where it goes” appears 7x
- **M6** “Data” appears 7x
- **M6** “Allowed by” appears 7x
- **M6** “Runs without you” appears 7x
- **M7** 10px — “Meeting summary” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** 10px — “Dictation intelligence” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** 10px — “Slack” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (119); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (15); Arial (1)
- **U1** 4 raw buttons vs 0 library — {"desk-light": 3, "desk-chip": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M3** verb “Review privacy settings” is outside its viewport — `div#trust > div.desk-surface-body > p > button.desk-chip.quiet`
- **M6** “Destination” appears 7x
- **M6** “Operation” appears 7x
- **M6** “Where it goes” appears 7x
- **M6** “Data” appears 7x
- **M6** “Allowed by” appears 7x
- **M6** “Runs without you” appears 7x
- **M7** 10px — “Meeting summary” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** 10px — “Dictation intelligence” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** 10px — “Slack” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** target 16x14px — “Close Data boundaries”
- **M7** target 16x14px — “Minimize Data boundaries”
- **M7** target 162x27px — “Review privacy settings”
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (119); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (15); Arial (1)
- **U1** 3 raw buttons vs 0 library — {"desk-light": 2, "desk-chip": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M3** verb “Review privacy settings” is outside its viewport — `div#trust > div.desk-surface-body > p > button.desk-chip.quiet`
- **M6** “Destination” appears 7x
- **M6** “Operation” appears 7x
- **M6** “Where it goes” appears 7x
- **M6** “Data” appears 7x
- **M6** “Allowed by” appears 7x
- **M6** “Runs without you” appears 7x
- **M7** 10px — “Meeting summary” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Enabled” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** 10px — “Dictation intelligence” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** 10px — “Slack” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (119); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (15); Arial (1)
- **U1** 4 raw buttons vs 0 library — {"desk-light": 3, "desk-chip": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M3** verb “Review privacy settings” is outside its viewport — `div#trust > div.desk-surface-body > p > button.desk-chip.quiet`
- **M6** “Destination” appears 7x
- **M6** “Operation” appears 7x
- **M6** “Where it goes” appears 7x
- **M6** “Data” appears 7x
- **M6** “Allowed by” appears 7x
- **M6** “Runs without you” appears 7x
- **M7** 10px — “Meeting summary” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Enabled” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** 10px — “Dictation intelligence” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** 10px — “Slack” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “Off” `div.desk-surface-body > section.surface-section > header.surface-section-head > span.gadget-lamp`
- **M7** target 16x14px — “Close Data boundaries”
- **M7** target 16x14px — “Minimize Data boundaries”
- **M7** target 162x27px — “Review privacy settings”
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (119); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (15); Arial (1)
- **U1** 3 raw buttons vs 0 library — {"desk-light": 2, "desk-chip": 1}

</details>

### The Window menu  <sub>`state-window-menu`</sub>

- Family: chrome · Door: the menu bar
- Opened by the rig via: `custom:bar-menu:Window`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 12 | n/a | 1/20 | 0 | 1 | 8 | 0 | 0 | 0 | 2986 | M7, M8, U1 |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 12 | n/a | 1/20 | 0 | 1 | 8 | 0 | 0 | 0 | 2987 | M7, M8, U1 |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “⌃” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “↑” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “W” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “M” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M8** 3.6:1 (needs 4.5) rgb(118, 126, 141) on rgb(36, 40, 51) at 10px — “No window open”
- **U1** 8 raw buttons vs 0 library — {"is-ghost": 8}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “⌃” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “↑” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “W” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “⌘” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M7** 10px — “M” `nav.desk-menu-list.desk-work-menu > button.is-ghost > span.desk-menu-keycaps > kbd.desk-menu-well`
- **M8** 3.6:1 (needs 4.5) rgb(118, 126, 141) on rgb(36, 40, 51) at 10px — “No window open”
- **U1** 8 raw buttons vs 0 library — {"is-ghost": 8}

</details>

### Exposé (all windows)  <sub>`win-expose`</sub>

- Family: state · Door: the Window menu / its keybinding
- Opened by the rig via: `custom:expose`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### The Floor as a list  <sub>`win-list-view`</sub>

- Family: application · Door: the Floor at a narrow width, or the list view toggle
- Opened by the rig via: `custom:list-view`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| cold | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### New Workbench chooser  <sub>`win-new-workbench`</sub>

- Family: state · Door: Desk menu > New Workbench (createPrimitive('workbench') never persists — web/src/desk/store/dataSlice.ts:182)
- Opened by the rig via: `custom:new-workbench`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | n/a | 4/21 | 0 | 2 | 8 | 0 | 0 | 0 | 3641 | M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | 2 | 4/21 | 0 | 2 | 7 | 0 | 0 | 0 | 3476 | M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | n/a | 4/21 | 0 | 2 | 8 | 0 | 0 | 0 | 3556 | M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | 2 | 4/21 | 0 | 2 | 7 | 0 | 0 | 0 | 3624 | M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “START FROM A TEMPLATE” `div.wb-picker > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “⏱ 0 2 * * * · 3 items · 3 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “Manual · 2 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “⏱ 0 7 * * 1-5 · 2 items · 3 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “⏱ 0 7 * * 1-5 · 3 items · 2 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 2 * * * · 3 items · 3 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “Manual · 2 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 7 * * 1-5 · 2 items · 3 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 7 * * 1-5 · 3 items · 2 skills”
- **U1** 8 raw buttons vs 0 library — {"desk-light": 3, "wb-picker-card": 5}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 10px — “START FROM A TEMPLATE” `div.wb-picker > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “⏱ 0 2 * * * · 3 items · 3 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “Manual · 2 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “⏱ 0 7 * * 1-5 · 2 items · 3 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “⏱ 0 7 * * 1-5 · 3 items · 2 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** target 16x14px — “Close New Workbench”
- **M7** target 16x14px — “Minimize New Workbench”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 2 * * * · 3 items · 3 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “Manual · 2 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 7 * * 1-5 · 2 items · 3 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 7 * * 1-5 · 3 items · 2 skills”
- **U1** 7 raw buttons vs 0 library — {"desk-light": 2, "wb-picker-card": 5}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “START FROM A TEMPLATE” `div.wb-picker > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “⏱ 0 2 * * * · 3 items · 3 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “Manual · 2 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “⏱ 0 7 * * 1-5 · 2 items · 3 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “⏱ 0 7 * * 1-5 · 3 items · 2 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 2 * * * · 3 items · 3 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “Manual · 2 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 7 * * 1-5 · 2 items · 3 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 7 * * 1-5 · 3 items · 2 skills”
- **U1** 8 raw buttons vs 0 library — {"desk-light": 3, "wb-picker-card": 5}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 10px — “START FROM A TEMPLATE” `div.wb-picker > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “⏱ 0 2 * * * · 3 items · 3 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “Manual · 2 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “⏱ 0 7 * * 1-5 · 2 items · 3 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** 10px — “⏱ 0 7 * * 1-5 · 3 items · 2 skills” `section.surface-section > div.wb-picker-grid > button.wb-picker-card > span.wb-picker-card-meta`
- **M7** target 16x14px — “Close New Workbench”
- **M7** target 16x14px — “Minimize New Workbench”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 2 * * * · 3 items · 3 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “Manual · 2 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 7 * * 1-5 · 2 items · 3 skills”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “⏱ 0 7 * * 1-5 · 3 items · 2 skills”
- **U1** 7 raw buttons vs 0 library — {"desk-light": 2, "wb-picker-card": 5}

</details>

### Repository window  <sub>`win-repository`</sub>

- Family: state · Door: a repository row on the Floor
- Opened by the rig via: `pullout:repository`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 3 | 0 | 13 | 0/0 | 16 | 3 | 13 | n/a | 3/151 | 0 | 2 | 10 | 0 | 0 | 0 | 3826 | M1, M3, M5, M6, M7, M8, U1 |
| rich | 393 | ok | 15+1in | 1 | 3 | 0/0 | 16 | 3 | 13 | 12 | 3/151 | 0 | 2 | 9 | 0 | 0 | 0 | 3845 | M1, M2, M3, M5, M6, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1** the document scrolls sideways: 1443px in 1440px
- **M3** verb “Close wt-202-audit” is outside its viewport — `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-close`
- **M3** verb “Minimize wt-202-audit” is outside its viewport — `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-min`
- **M3** verb “Maximize wt-202-audit” is outside its viewport — `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-max`
- **M3** verb “Files” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M3** verb “PRs” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M3** verb “Issues” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M4** tab bar `div#desk-next > div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Files, PRs, Issues
- **M4** tab bar `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Files, PRs, Issues
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M6** “folder” appears 18x
- **M6** “1h ago” appears 16x
- **M6** “file” appears 3x
- **M7** 11px — “audit/surface-inventory-2026-09-20” `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.repo-branch`
- **M7** 10px — “291 dirty” `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.repo-dirty`
- **M7** 10px — “Files” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “PRs” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Issues” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “root” `div#repository:src_e79f53ac7d7fd815 > div.desk-repo-body.desk-surface-body > nav.repo-breadcrumb > button.btn.btn--ghost`
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Stage”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Commit”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “↑”
- **U1** 10 raw buttons vs 3 library — {"desk-light": 3, "desk-wing": 3, "desk-sortable-table-sort": 3, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 15px — widest child `div#repository:src_e79f53ac7d7fd815 > div.desk-repo-body.desk-surface-body > nav.repo-breadcrumb > span.gadget-cycle` “↻agent/hs-104-01-capability-ledgeragent/hs-104-02-tool-call-gateagent/…”
- **M1 (inner)** `div#desk-next > div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` overflows by 25px — “wt-202-auditaudit/surface-inventory-2026-09-20369 dirty”
- **M2** `div#desk-next > div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` hides 25px on x — “wt-202-auditaudit/surface-inventory-2026-09-20369 dirty”
- **M3** verb “Stage” is outside its viewport — `div.surface-footer-layout > div.surface-footer-verbs > div.repo-footer-actions > button.btn.btn--secondary`
- **M3** verb “Speak Commit message” is outside its viewport — `div.surface-footer-verbs > div.repo-footer-actions > span.gadget-string > button.desk-mic.is-idle`
- **M3** verb “Commit” is outside its viewport — `div.surface-footer-layout > div.surface-footer-verbs > div.repo-footer-actions > button.btn.btn--secondary`
- **M4** tab bar `div#desk-next > div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Files, PRs, Issues
- **M4** tab bar `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Files, PRs, Issues
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M5** empty-heading `tr.desk-sortable-table-row > td > span > label.gadget-check`
- **M6** “folder” appears 18x
- **M6** “1h ago” appears 16x
- **M6** “file” appears 3x
- **M7** 11px — “audit/surface-inventory-2026-09-20” `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.repo-branch`
- **M7** 10px — “369 dirty” `div#repository:src_e79f53ac7d7fd815 > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > span.repo-dirty`
- **M7** 10px — “Files” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “PRs” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Issues” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “root” `div#repository:src_e79f53ac7d7fd815 > div.desk-repo-body.desk-surface-body > nav.repo-breadcrumb > button.btn.btn--ghost`
- **M7** target 16x14px — “Close wt-202-audit”
- **M7** target 16x14px — “Minimize wt-202-audit”
- **M7** target 59x23px — “Files”
- **M7** target 46x23px — “PRs”
- **M7** target 66x23px — “Issues”
- **M7** target 34x24px — “root”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Stage”
- **M8** 3.5:1 (needs 4.5) rgb(118, 126, 141) on rgb(39, 42, 50) at 11px — “Commit”
- **M8** 3.92:1 (needs 4.5) rgb(168, 110, 74) on rgb(28, 31, 39) at 10px — “↑”
- **U1** 9 raw buttons vs 3 library — {"desk-light": 2, "desk-wing": 3, "desk-sortable-table-sort": 3, "desk-mic": 1}

</details>

### Roadmap window  <sub>`win-roadmap`</sub>

- Family: state · Door: a roadmap row on the Floor
- Opened by the rig via: `pullout:roadmap`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

### Schedule a meeting  <sub>`win-schedule-create`</sub>

- Family: state · Door: the Chair's 'Schedule' verb (web/src/desk/chair/ChairHome.tsx:2293)
- Opened by the rig via: `custom:schedule`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | n/a | 1/10 | 0 | 1 | 5 | 1 | 0 | 0 | 2859 | M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | 6 | 1/10 | 0 | 1 | 4 | 1 | 0 | 0 | 2869 | M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | n/a | 1/10 | 0 | 1 | 5 | 1 | 0 | 0 | 2936 | M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | 6 | 1/10 | 0 | 1 | 4 | 1 | 0 | 0 | 2938 | M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M7** 10px — “Recording starts on its own at the set time” `div#schedule:__create__ > div.desk-surface-body > section.gadget-group > h4.gadget-group-label`
- **M7** 11px — “↻” `div.gadget-row > span.gadget-row-gadget > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** 11px — “↻” `div.gadget-row > span.gadget-row-gadget > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** 11px — “Cancel” `div#schedule:__create__ > div.desk-surface-body > div > button.btn.btn--ghost`
- **M7** 11px — “Schedule” `div#schedule:__create__ > div.desk-surface-body > div > button.btn.btn--primary`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Schedule”
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-mic": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 10px — “Recording starts on its own at the set time” `div#schedule:__create__ > div.desk-surface-body > section.gadget-group > h4.gadget-group-label`
- **M7** 11px — “↻” `div.gadget-row > span.gadget-row-gadget > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** 11px — “↻” `div.gadget-row > span.gadget-row-gadget > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** 11px — “Cancel” `div#schedule:__create__ > div.desk-surface-body > div > button.btn.btn--ghost`
- **M7** 11px — “Schedule” `div#schedule:__create__ > div.desk-surface-body > div > button.btn.btn--primary`
- **M7** target 16x14px — “Close Schedule recording”
- **M7** target 16x14px — “Minimize Schedule recording”
- **M7** target 20x20px — “Speak Title”
- **M7** target 32x34px — “Speak”
- **M7** target 58x24px — “Cancel”
- **M7** target 71x24px — “Schedule”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Schedule”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-mic": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M7** 10px — “Recording starts on its own at the set time” `div#schedule:__create__ > div.desk-surface-body > section.gadget-group > h4.gadget-group-label`
- **M7** 11px — “↻” `div.gadget-row > span.gadget-row-gadget > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** 11px — “↻” `div.gadget-row > span.gadget-row-gadget > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** 11px — “Cancel” `div#schedule:__create__ > div.desk-surface-body > div > button.btn.btn--ghost`
- **M7** 11px — “Schedule” `div#schedule:__create__ > div.desk-surface-body > div > button.btn.btn--primary`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Schedule”
- **U1** 5 raw buttons vs 2 library — {"desk-light": 3, "desk-mic": 2}

</details>

<details><summary>rich @393 — evidence</summary>

- **M7** 10px — “Recording starts on its own at the set time” `div#schedule:__create__ > div.desk-surface-body > section.gadget-group > h4.gadget-group-label`
- **M7** 11px — “↻” `div.gadget-row > span.gadget-row-gadget > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** 11px — “↻” `div.gadget-row > span.gadget-row-gadget > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** 11px — “Cancel” `div#schedule:__create__ > div.desk-surface-body > div > button.btn.btn--ghost`
- **M7** 11px — “Schedule” `div#schedule:__create__ > div.desk-surface-body > div > button.btn.btn--primary`
- **M7** target 16x14px — “Close Schedule recording”
- **M7** target 16x14px — “Minimize Schedule recording”
- **M7** target 20x20px — “Speak Title”
- **M7** target 32x34px — “Speak”
- **M7** target 58x24px — “Cancel”
- **M7** target 71x24px — “Schedule”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Schedule”
- **U1** 4 raw buttons vs 2 library — {"desk-light": 2, "desk-mic": 2}

</details>

### The window switcher (⌃`)  <sub>`win-switcher`</sub>

- Family: state · Door: ⌃` (web/src/desk/keymap.ts)
- Opened by the rig via: `custom:switcher`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 1 | 43 | n/a | 1/91 | 0 | 5 | 35 | 0 | 0 | 0 | 5167 | M10, M6, M7, M8, U1 |
| cold | 393 | ok | 863 | 0 | 13 | 0/0 | 0 | 1 | 42 | 45 | 1/86 | 0 | 5 | 30 | 0 | 0 | 0 | 5126 | M1, M10, M3, M6, M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 52 | 0/0 | 0 | 1 | 307 | n/a | 5/406 | 0 | 5 | 35 | 3 | 0 | 0 | 5226 | M10, M3, M6, M7, M8, U1, U4 |
| rich | 393 | ok | 902+1in | 1 | 83 | 0/0 | 0 | 1 | 306 | 89 | 5/401 | 0 | 5 | 30 | 3 | 0 | 0 | 5208 | M1, M10, M2, M3, M6, M7, M8, U1, U4 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M6** “No meetings yet” appears 2x
- **M7** 10px — “⌘K” `div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-chip.desk-tools-launch > kbd`
- **M7** 11px — “Connect calendar” `div.arrival-headline > div.arrival-head-tokens > span.arrival-next > button.btn.btn--ghost`
- **M7** 10px — “SETUP” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Choose an engine” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M7** 10px — “BRIEF” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Generate” `div > section.surface-section > header.surface-section-head > button.btn.btn--ghost`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (62); Arial (13); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (9); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (4); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (3)
- **U1** 35 raw buttons vs 18 library — {"desk-mark": 1, "desk-verbbar-title": 4, "gadget-chip": 1, "desk-bell": 1, "desk-chip": 1, "desk-mic": 2, "desk-light": 6, "desk-wing": 7, "desk-dock-launch": 9, "desk-orb": 1, "desk-dock-reset": 2}

</details>

<details><summary>cold @393 — evidence</summary>

- **M1** content overflows its window by 863px — widest child `main#main > div#desk-next > div.desk-dock > button.desk-dock-reset` “”
- **M3** verb “Desk memory” is outside its viewport — `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-bell`
- **M3** verb “Search ⌘K” is outside its viewport — `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-chip.desk-tools-launch`
- **M3** verb “Agents” is outside its viewport — `main#main > div#desk-next > div.desk-dock > button.desk-dock-launch.desk-dock-app`
- **M3** verb “Settings” is outside its viewport — `main#main > div#desk-next > div.desk-dock > button.desk-dock-launch.desk-dock-app`
- **M3** verb “Floor” is outside its viewport — `main#main > div#desk-next > div.desk-dock > button.desk-dock-launch`
- **M3** verb “Desk memory” is outside its viewport — `main#main > div#desk-next > div.desk-dock > button.desk-dock-launch`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M6** “No meetings yet” appears 2x
- **M7** 11px — “Connect calendar” `div.arrival-headline > div.arrival-head-tokens > span.arrival-next > button.btn.btn--ghost`
- **M7** 10px — “SETUP” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Choose an engine” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M7** 10px — “BRIEF” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 11px — “Generate” `div > section.surface-section > header.surface-section-head > button.btn.btn--ghost`
- **M7** 9px — “Talk” `footer.arrival-capture-bar > span.arrival-capture-talk > button.desk-mic.gadget-transport-key > span.gadget-transport-word`
- **M7** target 106x22px — “HoldSpeak”
- **M7** target 31x26px — “Go”
- **M7** target 133x24px — “Privacy and trust: ⌂ This device”
- **M7** target 34x22px — “Desk memory”
- **M7** target 88x24px — “Search ⌘K”
- **M7** target 124x24px — “Connect calendar”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (57); Arial (13); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (9); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (4); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (3)
- **U1** 30 raw buttons vs 18 library — {"desk-mark": 1, "desk-verbbar-title": 1, "gadget-chip": 1, "desk-bell": 1, "desk-chip": 1, "desk-mic": 2, "desk-light": 4, "desk-wing": 7, "desk-dock-launch": 9, "desk-orb": 1, "desk-dock-reset": 2}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M3** verb “SRCgithub acme-platform/service-15●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “SRCgithub acme-platform/service-16●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-16” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M3** verb “SRCgithub acme-platform/service-17●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-17” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M3** verb “SRCgithub acme-platform/service-18●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M6** “192.168.1.43 · LAN” appears 5x
- **M7** 10px — “⌘K” `div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-chip.desk-tools-launch > kbd`
- **M7** 11px — “Connect calendar” `div.arrival-headline > div.arrival-head-tokens > span.arrival-next > button.btn.btn--ghost`
- **M7** 10px — “COVERAGE · 9 OF 40” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “SRC” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-lead > span.arrival-source-emblem.surface-coverage-emblem`
- **M7** 10px — “CANT CHECK” `li.surface-ledger-row > div.surface-ledger-line > span.surface-coverage-meta > span.surface-state-chip.surface-coverage-token`
- **M7** 11px — “●” `div.surface-ledger-line > span.surface-coverage-meta > span.surface-state-chip.surface-coverage-token > span.surface-state-chip-icon`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Continue”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Run summary”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Retry”
- **M8** 4.2:1 (needs 4.5) rgb(255, 255, 255) on rgb(168, 110, 74) at 12px — “3”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (330); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (45); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (14); Arial (14); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (3)
- **U1** 35 raw buttons vs 62 library — {"desk-mark": 1, "desk-verbbar-title": 4, "gadget-chip": 1, "desk-bell": 1, "desk-chip": 1, "desk-mic": 2, "desk-light": 6, "desk-wing": 7, "desk-dock-launch": 9, "desk-orb": 1, "desk-dock-reset": 2}
- **U4** filled primaries: “Continue”, “Run summary”, “Retry”

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 902px — widest child `main#main > div#desk-next > div.desk-dock > button.desk-dock-reset` “”
- **M1 (inner)** `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tl > button.gadget-chip.gadget-chip-egress` overflows by 96px — “→ External reach enabled”
- **M2** `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tl > button.gadget-chip.gadget-chip-egress` hides 96px on x — “→ External reach enabled”
- **M3** verb “Desk memory: 3 need attention” is outside its viewport — `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-bell`
- **M3** verb “Search ⌘K” is outside its viewport — `div#desk-next > div.desk-menubar > div.desk-chrome.desk-chrome-tr > button.desk-chip.desk-tools-launch`
- **M3** verb “SRCgithub acme-platform/service-09●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-09” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M3** verb “SRCgithub acme-platform/service-10●CANT CHECKNEVER…” is outside its viewport — `section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line`
- **M3** verb “Reconnect: github acme-platform/service-10” is outside its viewport — `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-trailing > button.btn.btn--secondary`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M4** tab bar `div.desk-surface-windows > div#surface-settings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Settings, Guide
- **M6** “192.168.1.43 · LAN” appears 5x
- **M7** 11px — “Connect calendar” `div.arrival-headline > div.arrival-head-tokens > span.arrival-next > button.btn.btn--ghost`
- **M7** 10px — “COVERAGE · 9 OF 40” `div > section.surface-section > header.surface-section-head > h3`
- **M7** 10px — “SRC” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-lead > span.arrival-source-emblem.surface-coverage-emblem`
- **M7** 10px — “CANT CHECK” `li.surface-ledger-row > div.surface-ledger-line > span.surface-coverage-meta > span.surface-state-chip.surface-coverage-token`
- **M7** 11px — “●” `div.surface-ledger-line > span.surface-coverage-meta > span.surface-state-chip.surface-coverage-token > span.surface-state-chip-icon`
- **M7** 10px — “NEVER OBSERVED” `li.surface-ledger-row > div.surface-ledger-line > span.surface-coverage-meta > span.surface-coverage-observed`
- **M7** target 106x22px — “HoldSpeak”
- **M7** target 31x26px — “Go”
- **M7** target 134x24px — “Privacy and trust: → External reach enab…”
- **M7** target 55x22px — “Desk memory: 3 need attention”
- **M7** target 88x24px — “Search ⌘K”
- **M7** target 124x24px — “Connect calendar”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Continue”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Run summary”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Retry”
- **M8** 4.2:1 (needs 4.5) rgb(255, 255, 255) on rgb(168, 110, 74) at 12px — “3”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (325); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (45); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (14); Arial (14); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (3)
- **U1** 30 raw buttons vs 62 library — {"desk-mark": 1, "desk-verbbar-title": 1, "gadget-chip": 1, "desk-bell": 1, "desk-chip": 1, "desk-mic": 2, "desk-light": 4, "desk-wing": 7, "desk-dock-launch": 9, "desk-orb": 1, "desk-dock-reset": 2}
- **U4** filled primaries: “Continue”, “Run summary”, “Retry”

</details>

### The System shade (Missed)  <sub>`win-system-shade`</sub>

- Family: state · Door: the dock's 'Desk memory' launcher (web/src/desk/components/AttentionDrawer.tsx:73)
- Opened by the rig via: `custom:shade`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | n/a | 1/3 | 0 | 2 | 0 | 0 | 0 | 0 | 4079 | M7, M8 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 1 | 1 | 1/3 | 0 | 2 | 0 | 0 | 0 | 0 | 4082 | M7, M8 |
| rich | 1440 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

<details><summary>cold @1440 — evidence</summary>

- **M7** 11px — “Missed” `div#desk-next > div.desk-shade > div.desk-shade-head > span.desk-shade-title`
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 12px — “Desk memory”

</details>

<details><summary>cold @393 — evidence</summary>

- **M7** 11px — “Missed” `div#desk-next > div.desk-shade > div.desk-shade-head > span.desk-shade-title`
- **M7** target 91x24px — “Desk memory”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 12px — “Desk memory”

</details>

### Thought workspace window  <sub>`win-thought-workspace`</sub>

- Family: state · Door: a Note pullout > 'Develop this thought' (web/src/desk/pullouts/NotePullout.tsx:483)
- Opened by the rig via: `custom:thought-workspace`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 3/10 | 0 | 3 | 5 | 1 | 0 | 0 | 4958 | M10, M7, M8, U1 |
| rich | 393 | UNOPENED | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

<details><summary>rich @1440 — evidence</summary>

- **M7** 11px — “ONE QUESTION” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.thought-note-ask-label`
- **M7** 10px — “NO ENGINE YET” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > span.surface-token`
- **M7** 11px — “Choose an engine” `div.thought-note-window > section.thought-note-ask > div.thought-note-ask-row > button.btn.btn--secondary`
- **M7** 10px — “READS · NOTHING” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-egress > span.thought-note-reads`
- **M7** 10px — “KEPT” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** 11px — “Change” `footer.surface-footer > div.surface-footer-layout.thought-note-foot > div.surface-footer-verbs > button.btn.btn--secondary`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Finish”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 11px — “ONE QUESTION”
- **M8** 4.03:1 (needs 4.5) rgb(118, 126, 141) on rgb(28, 31, 39) at 10px — “READS · NOTHING”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (8); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 5 raw buttons vs 3 library — {"desk-light": 3, "surface-edit-in-place": 1, "desk-mic": 1}

</details>

### Workbench window  <sub>`win-workbench`</sub>

- Family: state · Door: Workbenches > a row
- Opened by the rig via: `pullout:workbench`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rich | 1440 | ok | 0+1in | 1 | 5 | 0/0 | 0 | 1 | 13 | n/a | 2/45 | 0 | 3 | 25 | 0 | 0 | 0 | 3322 | M1, M10, M2, M3, M6, M7, M8, U1 |
| rich | 393 | ok | 0+1in | 1 | 13 | 0/0 | 0 | 1 | 13 | 24 | 2/45 | 0 | 3 | 24 | 0 | 0 | 0 | 3202 | M1, M10, M2, M3, M6, M7, M8, U1 |

<details><summary>rich @1440 — evidence</summary>

- **M1 (inner)** `div#desk-next > div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` overflows by 4px — “The platform workbench”
- **M2** `div#desk-next > div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title` hides 4px on x — “The platform workbench”
- **M3** verb “Choose default” is outside its window — `div.contextual-assignment > article.capability-assignment-row > div > button.btn.btn--ghost`
- **M3** verb “Manual” is outside its window — `div.wb-config-panel > section.surface-section > div.wb-start-mode > button.desk-chip`
- **M3** verb “Schedule” is outside its window — `div.wb-config-panel > section.surface-section > div.wb-start-mode > button.desk-chip`
- **M3** verb “Event” is outside its window — `div.wb-config-panel > section.surface-section > div.wb-start-mode > button.desk-chip`
- **M3** verb “Idle” is outside its window — `div.wb-config-panel > section.surface-section > div.wb-start-mode > button.desk-chip`
- **M4** tab bar `div#desk-next > div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Items, Runs, Memory
- **M4** tab bar `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Items, Runs, Memory
- **M6** “No default model” appears 2x
- **M7** 10px — “Items” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runs” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Memory” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10.83px — “· Bind an agent first” `header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.desk-chip > small.quiet`
- **M7** 10px — “▴ Collapse” `div#workbench:workbench_a2bf46588a6c > div.desk-surface-body.wb-body > div.wb-config-panel > button.wb-config-collapse.desk-chip`
- **M7** 10px — “AGENT” `div.wb-config-panel > section.surface-section > header.surface-section-head > h3`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 13px — “Add”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “~/.holdspeak/workbenches/workbench_a2bf46588a6c/”
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (19); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (17); Arial (9)
- **U1** 25 raw buttons vs 2 library — {"desk-light": 3, "surface-edit-in-place": 1, "desk-wing": 3, "desk-chip": 8, "wb-config-collapse": 1, "desk-mic": 2, "surface-row-open": 7}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1 (inner)** `div.surface-row-line > button.surface-row-open > span.surface-row-text > strong` overflows by 28px — “The reviewer — an agent with a deliberately long name”
- **M2** `div.surface-row-line > button.surface-row-open > span.surface-row-text > strong` hides 28px on x — “The reviewer — an agent with a deliberately long name”
- **M3** verb “Close The platform workbench” is outside its viewport — `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-close`
- **M3** verb “Minimize The platform workbench” is outside its viewport — `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-traffic > button.desk-light.desk-light-min`
- **M3** verb “Edit Workbench name” is outside its viewport — `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-pullout-title.desk-window-title > button.surface-edit-in-place.wb-title-edit`
- **M3** verb “Items” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M3** verb “Runs” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M3** verb “Memory” is outside its viewport — `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M4** tab bar `div#desk-next > div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Items, Runs, Memory
- **M4** tab bar `div#workbench:workbench_a2bf46588a6c > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Items, Runs, Memory
- **M6** “No default model” appears 2x
- **M7** 10px — “Items” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Runs” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Memory” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10.83px — “· Bind an agent first” `header.desk-pullout-head.desk-window-handle > span.desk-window-actions > button.desk-chip > small.quiet`
- **M7** 10px — “▴ Collapse” `div#workbench:workbench_a2bf46588a6c > div.desk-surface-body.wb-body > div.wb-config-panel > button.wb-config-collapse.desk-chip`
- **M7** 10px — “AGENT” `div.wb-config-panel > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close The platform workbench”
- **M7** target 16x14px — “Minimize The platform workbench”
- **M7** target 166x20px — “Edit Workbench name”
- **M7** target 59x23px — “Items”
- **M7** target 52x23px — “Runs”
- **M7** target 66x23px — “Memory”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 13px — “Add”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “~/.holdspeak/workbenches/workbench_a2bf46588a6c/”
- **M10** Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (19); "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (17); Arial (9)
- **U1** 24 raw buttons vs 2 library — {"desk-light": 2, "surface-edit-in-place": 1, "desk-wing": 3, "desk-chip": 8, "wb-config-collapse": 1, "desk-mic": 2, "surface-row-open": 7}

</details>

### Activity — Records wing  <sub>`wing-activity-records`</sub>

- Family: wing · Door: Go > Activity > the 'Records' wing
- Opened by the rig via: `custom:wing:Activity|#surface-activity|Records`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 1 | 0 | 7 | n/a | 0/10 | 0 | 2 | 7 | 0 | 0 | 0 | 6323 | M5, M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 1 | 0 | 7 | 8 | 0/10 | 0 | 2 | 6 | 0 | 0 | 0 | 6346 | M5, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 1 | 0 | 7 | n/a | 0/10 | 0 | 2 | 7 | 0 | 0 | 0 | 6379 | M5, M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 1 | 0 | 7 | 8 | 0/10 | 0 | 2 | 6 | 0 | 0 | 0 | 6352 | M5, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Records” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **U1** 7 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Records” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Activity”
- **M7** target 16x14px — “Minimize Activity”
- **M7** target 72x23px — “Records”
- **M7** target 59x23px — “Rules”
- **M7** target 27x24px — “Candidates and connectors”
- **M7** target 91x24px — “Refresh now”
- **U1** 6 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Records” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **U1** 7 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Records” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Activity”
- **M7** target 16x14px — “Minimize Activity”
- **M7** target 72x23px — “Records”
- **M7** target 59x23px — “Rules”
- **M7** target 27x24px — “Candidates and connectors”
- **M7** target 91x24px — “Refresh now”
- **U1** 6 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 3, "desk-mic": 1}

</details>

### Activity — Rules wing  <sub>`wing-activity-rules`</sub>

- Family: wing · Door: Go > Activity > the 'Rules' wing
- Opened by the rig via: `custom:wing:Activity|#surface-activity|Rules`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 1 | 0 | 6 | n/a | 0/9 | 0 | 2 | 7 | 0 | 0 | 0 | 6304 | M5, M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 1 | 0 | 6 | 7 | 0/9 | 0 | 2 | 6 | 0 | 0 | 0 | 6350 | M5, M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 1 | 0 | 6 | n/a | 0/9 | 0 | 2 | 7 | 0 | 0 | 0 | 6385 | M5, M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 1 | 0 | 6 | 7 | 0/9 | 0 | 2 | 6 | 0 | 0 | 0 | 6340 | M5, M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Project rules” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **U1** 7 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Project rules” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Activity”
- **M7** target 16x14px — “Minimize Activity”
- **M7** target 72x23px — “Records”
- **M7** target 59x23px — “Rules”
- **M7** target 27x24px — “Candidates and connectors”
- **M7** target 91x24px — “Refresh now”
- **U1** 6 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Project rules” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **U1** 7 raw buttons vs 1 library — {"desk-light": 3, "desk-wing": 3, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Records, Rules, ⚙︎
- **M4** tab bar `div#surface-activity > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Records, Rules
- **M5** empty-heading `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > label.gadget-check`
- **M7** 10px — “Records” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Rules” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Refresh now” `div.desk-surface-body > div.surface-verbs > span.surface-verbs-actions > button.btn.btn--secondary`
- **M7** 10px — “Watching” `div.surface-verbs > span.surface-verbs-actions > span.gadget-checkline > span.gadget-checkline-word`
- **M7** 10px — “Project rules” `div.desk-surface-body > section.surface-section > header.surface-section-head > h3`
- **M7** target 16x14px — “Close Activity”
- **M7** target 16x14px — “Minimize Activity”
- **M7** target 72x23px — “Records”
- **M7** target 59x23px — “Rules”
- **M7** target 27x24px — “Candidates and connectors”
- **M7** target 91x24px — “Refresh now”
- **U1** 6 raw buttons vs 1 library — {"desk-light": 2, "desk-wing": 3, "desk-mic": 1}

</details>

### Agents — Delivery wing  <sub>`wing-agents-delivery`</sub>

- Family: wing · Door: Go > Agents > the 'Delivery' wing
- Opened by the rig via: `custom:wing:Agents|#surface-companion|Delivery`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/4 | 0 | 1 | 6 | 0 | 0 | 0 | 6326 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/4 | 0 | 1 | 5 | 0 | 0 | 0 | 6301 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | n/a | 0/4 | 0 | 1 | 6 | 0 | 0 | 0 | 6362 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 3 | 5 | 0/4 | 0 | 1 | 5 | 0 | 0 | 0 | 6357 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **U1** 6 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** target 16x14px — “Close Agents”
- **M7** target 16x14px — “Minimize Agents”
- **M7** target 66x23px — “Roster”
- **M7** target 79x23px — “Delivery”
- **M7** target 27x24px — “How it connects”
- **U1** 5 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 3}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **U1** 6 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** target 16x14px — “Close Agents”
- **M7** target 16x14px — “Minimize Agents”
- **M7** target 66x23px — “Roster”
- **M7** target 79x23px — “Delivery”
- **M7** target 27x24px — “How it connects”
- **U1** 5 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 3}

</details>

### Agents — Roster wing  <sub>`wing-agents-roster`</sub>

- Family: wing · Door: Go > Agents > the 'Roster' wing
- Opened by the rig via: `custom:wing:Agents|#surface-companion|Roster`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | n/a | 2/11 | 0 | 2 | 6 | 0 | 0 | 0 | 6314 | M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 5 | 5 | 2/11 | 0 | 2 | 5 | 0 | 0 | 0 | 6325 | M7, M8, U1 |
| rich | 1440 | ok | 0+1in | 1 | 0 | 0/0 | 0 | 0 | 6 | n/a | 2/11 | 0 | 2 | 6 | 0 | 0 | 0 | 6321 | M1, M2, M7, M8, U1 |
| rich | 393 | ok | 0+1in | 1 | 0 | 0/0 | 0 | 0 | 6 | 6 | 2/11 | 0 | 2 | 5 | 0 | 0 | 0 | 6494 | M1, M2, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Sessions” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “Crew” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Sessions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Crew”
- **U1** 6 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 3}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Sessions” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “Crew” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** target 16x14px — “Close Agents”
- **M7** target 16x14px — “Minimize Agents”
- **M7** target 66x23px — “Roster”
- **M7** target 79x23px — “Delivery”
- **M7** target 27x24px — “How it connects”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Sessions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Crew”
- **U1** 5 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 3}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1 (inner)** `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary` overflows by 75px — “The reviewer — an agent with a deliberately long name”
- **M2** `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary` hides 75px on x — “The reviewer — an agent with a deliberately long name”
- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Sessions” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “Crew” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “OK” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell > span.gadget-lamp`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Sessions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Crew”
- **U1** 6 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 3}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1 (inner)** `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary` overflows by 213px — “The reviewer — an agent with a deliberately long name”
- **M2** `ul.surface-ledger-rows > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary` hides 213px on x — “The reviewer — an agent with a deliberately long name”
- **M4** tab bar `div.desk-surface-windows > div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Roster, Delivery, ⚙︎
- **M4** tab bar `div#surface-companion > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Roster, Delivery
- **M7** 10px — “Roster” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Delivery” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “Sessions” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “Crew” `div#surface-companion > div.desk-surface-body > div.surface-ledger > h4.surface-ledger-band`
- **M7** 10px — “OK” `li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-cell > span.gadget-lamp`
- **M7** target 16x14px — “Close Agents”
- **M7** target 16x14px — “Minimize Agents”
- **M7** target 66x23px — “Roster”
- **M7** target 79x23px — “Delivery”
- **M7** target 27x24px — “How it connects”
- **M7** target 363x26px — “The reviewer — an agent with a deliberat…”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Sessions”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 10px — “Crew”
- **U1** 5 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 3}

</details>

### Meetings — Artifacts wing  <sub>`wing-meetings-artifacts`</sub>

- Family: wing · Door: Go > Meetings > the 'Artifacts' wing
- Opened by the rig via: `custom:wing:Meetings|#surface-meetings|Artifacts`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 0/9 | 0 | 2 | 8 | 0 | 0 | 0 | 6348 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 7 | 0/9 | 0 | 2 | 7 | 0 | 0 | 0 | 6373 | M7, U1 |
| rich | 1440 | ok | 214 | 0 | 8 | 0/0 | 0 | 1 | 101 | n/a | 1/114 | 0 | 2 | 8 | 1 | 0 | 0 | 6334 | M1, M3, M6, M7, M8, U1 |
| rich | 393 | ok | 461 | 0 | 12 | 0/0 | 0 | 1 | 101 | 17 | 1/114 | 0 | 2 | 7 | 1 | 0 | 0 | 6431 | M1, M3, M6, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “RECORDS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **U1** 8 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 5}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “RECORDS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **U1** 7 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 5}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 214px — widest child `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body > div.meetings-stream-row-head` “Quarterly platform architecture review — migration, custody, and the r…”
- **M3** verb “Platform syncSEP 19 · OFFSEP 19·45 MIN·88 WORDS·OF…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Run summary” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Hiring loop debriefSEP 19 · OFFSEP 19·45 MIN·88 WO…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Run summary” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “RetroSEP 19 · INTERRUPTEDSEP 19·35 WORDS·INTERRUPT…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M6** “192.168.1.43 · LAN” appears 5x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “SEP 20” `div.meetings-stream-row-body > div.meetings-stream-tokens > span > span.meetings-stream-fact`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Retry”
- **U1** 8 raw buttons vs 10 library — {"desk-light": 3, "desk-wing": 5}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 461px — widest child `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body > div.meetings-stream-row-head` “Quarterly platform architecture review — migration, custody, and the r…”
- **M3** verb “1:1 — Aleksandra Wiśniewska-KowalczykSEP 20 · RANS…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its viewport — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Architecture guildSEP 19 · RANSEP 19·45 MIN·88 WOR…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its viewport — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Platform syncSEP 19 · OFFSEP 19·45 MIN·88 WORDS·OF…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Run summary” is outside its viewport — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M6** “192.168.1.43 · LAN” appears 5x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “SEP 20” `div.meetings-stream-row-body > div.meetings-stream-tokens > span > span.meetings-stream-fact`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Retry”
- **U1** 7 raw buttons vs 10 library — {"desk-light": 2, "desk-wing": 5}

</details>

### Meetings — Outcomes wing  <sub>`wing-meetings-outcomes`</sub>

- Family: wing · Door: Go > Meetings > the 'Outcomes' wing
- Opened by the rig via: `custom:wing:Meetings|#surface-meetings|Outcomes`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 1 | 8 | n/a | 0/12 | 0 | 3 | 9 | 0 | 0 | 0 | 6514 | M10, M6, M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 1 | 8 | 10 | 0/12 | 0 | 3 | 8 | 0 | 0 | 0 | 6536 | M10, M6, M7, U1 |
| rich | 1440 | ok | 214 | 0 | 12 | 0/0 | 0 | 1 | 103 | n/a | 1/117 | 0 | 3 | 9 | 1 | 0 | 0 | 6569 | M1, M10, M3, M6, M7, M8, U1 |
| rich | 393 | ok | 461 | 0 | 15 | 0/0 | 0 | 1 | 103 | 20 | 1/117 | 0 | 3 | 8 | 1 | 0 | 0 | 6518 | M1, M10, M3, M6, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M6** “No meetings yet” appears 2x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Record meeting” `div#surface-meetings > div.desk-surface-body > div.meetings-head-verbs > button.btn.btn--secondary`
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (9); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 9 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M6** “No meetings yet” appears 2x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Record meeting” `div#surface-meetings > div.desk-surface-body > div.meetings-head-verbs > button.btn.btn--secondary`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (9); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 8 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 214px — widest child `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body > div.meetings-stream-row-head` “Quarterly platform architecture review — migration, custody, and the r…”
- **M3** verb “1:1 — Aleksandra Wiśniewska-KowalczykSEP 20 · RANS…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Architecture guildSEP 19 · RANSEP 19·45 MIN·88 WOR…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Platform syncSEP 19 · OFFSEP 19·45 MIN·88 WORDS·OF…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Run summary” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M6** “192.168.1.43 · LAN” appears 5x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Record meeting” `div#surface-meetings > div.desk-surface-body > div.meetings-head-verbs > button.btn.btn--secondary`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Retry”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (104); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (12); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 9 raw buttons vs 12 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 461px — widest child `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body > div.meetings-stream-row-head` “Quarterly platform architecture review — migration, custody, and the r…”
- **M3** verb “Vendor call — custodySEP 20 · RUNNINGSEP 20·45 MIN…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Security reviewSEP 20 · FAILEDSEP 20·45 MIN·88 WOR…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Retry” is outside its viewport — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “1:1 — Aleksandra Wiśniewska-KowalczykSEP 20 · RANS…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its viewport — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Architecture guildSEP 19 · RANSEP 19·45 MIN·88 WOR…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M6** “192.168.1.43 · LAN” appears 5x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Record meeting” `div#surface-meetings > div.desk-surface-body > div.meetings-head-verbs > button.btn.btn--secondary`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Retry”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (104); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (12); "Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (1)
- **U1** 8 raw buttons vs 12 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 1}

</details>

### Meetings — Record wing  <sub>`wing-meetings-record`</sub>

- Family: wing · Door: Go > Meetings > the 'Record' wing
- Opened by the rig via: `custom:wing:Meetings|#surface-meetings|Record`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | n/a | 2/14 | 0 | 2 | 8 | 2 | 0 | 0 | 6339 | M7, M8, U1, U4 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | 10 | 2/14 | 0 | 2 | 7 | 2 | 0 | 0 | 6456 | M7, M8, U1, U4 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 9 | n/a | 2/15 | 0 | 2 | 8 | 2 | 0 | 0 | 6430 | M7, M8, U1, U4 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 9 | 10 | 2/15 | 0 | 2 | 7 | 2 | 0 | 0 | 6350 | M7, M8, U1, U4 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Close” `div.desk-surface-body > section.surface-section > header.surface-section-head > button.btn.btn--ghost`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Record meeting”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 12px — “Import”
- **U1** 8 raw buttons vs 3 library — {"desk-light": 3, "desk-wing": 5}
- **U4** filled primaries: “Record meeting”, “Import”

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Close” `div.desk-surface-body > section.surface-section > header.surface-section-head > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Record meeting”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 12px — “Import”
- **U1** 7 raw buttons vs 3 library — {"desk-light": 2, "desk-wing": 5}
- **U4** filled primaries: “Record meeting”, “Import”

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Close” `div.desk-surface-body > section.surface-section > header.surface-section-head > button.btn.btn--ghost`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Record meeting”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 12px — “Import”
- **U1** 8 raw buttons vs 3 library — {"desk-light": 3, "desk-wing": 5}
- **U4** filled primaries: “Record meeting”, “Import”

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “Close” `div.desk-surface-body > section.surface-section > header.surface-section-head > button.btn.btn--ghost`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 12px — “Record meeting”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 12px — “Import”
- **U1** 7 raw buttons vs 3 library — {"desk-light": 2, "desk-wing": 5}
- **U4** filled primaries: “Record meeting”, “Import”

</details>

### Meetings — Review wing  <sub>`wing-meetings-review`</sub>

- Family: wing · Door: Go > Meetings > the 'Review' wing
- Opened by the rig via: `custom:wing:Meetings|#surface-meetings|Review`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | n/a | 0/9 | 0 | 2 | 8 | 0 | 0 | 0 | 6387 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 6 | 7 | 0/9 | 0 | 2 | 7 | 0 | 0 | 0 | 6343 | M7, U1 |
| rich | 1440 | ok | 214 | 0 | 8 | 0/0 | 0 | 1 | 101 | n/a | 1/114 | 0 | 2 | 8 | 1 | 0 | 0 | 6339 | M1, M3, M6, M7, M8, U1 |
| rich | 393 | ok | 461 | 0 | 12 | 0/0 | 0 | 1 | 101 | 17 | 1/114 | 0 | 2 | 7 | 1 | 0 | 0 | 6360 | M1, M3, M6, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “RECORDS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **U1** 8 raw buttons vs 0 library — {"desk-light": 3, "desk-wing": 5}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “RECORDS” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout > div.surface-footer-receipt > span.surface-footer-receipt-line`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **U1** 7 raw buttons vs 0 library — {"desk-light": 2, "desk-wing": 5}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M1** content overflows its window by 214px — widest child `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body > div.meetings-stream-row-head` “Quarterly platform architecture review — migration, custody, and the r…”
- **M3** verb “Platform syncSEP 19 · OFFSEP 19·45 MIN·88 WORDS·OF…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Run summary” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Hiring loop debriefSEP 19 · OFFSEP 19·45 MIN·88 WO…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Run summary” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “RetroSEP 19 · INTERRUPTEDSEP 19·35 WORDS·INTERRUPT…” is outside its window — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its window — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M6** “192.168.1.43 · LAN” appears 5x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “SEP 20” `div.meetings-stream-row-body > div.meetings-stream-tokens > span > span.meetings-stream-fact`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Retry”
- **U1** 8 raw buttons vs 10 library — {"desk-light": 3, "desk-wing": 5}

</details>

<details><summary>rich @393 — evidence</summary>

- **M1** content overflows its window by 461px — widest child `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body > div.meetings-stream-row-head` “Quarterly platform architecture review — migration, custody, and the r…”
- **M3** verb “1:1 — Aleksandra Wiśniewska-KowalczykSEP 20 · RANS…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its viewport — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Architecture guildSEP 19 · RANSEP 19·45 MIN·88 WOR…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Open” is outside its viewport — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M3** verb “Platform syncSEP 19 · OFFSEP 19·45 MIN·88 WORDS·OF…” is outside its viewport — `div.meetings-stream > div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-body`
- **M3** verb “Run summary” is outside its viewport — `div.meetings-stream-rows > div.meetings-stream-row > div.meetings-stream-row-verb > button.btn.btn--ghost`
- **M4** tab bar `div.desk-surface-windows > div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Outcomes, Review, Record, Artifacts, ⚙︎
- **M4** tab bar `div#surface-meetings > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Outcomes, Review, Record, Artifacts
- **M6** “192.168.1.43 · LAN” appears 5x
- **M7** 10px — “Outcomes” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Review” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Record” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Artifacts” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “SEP 20” `div.meetings-stream-row-body > div.meetings-stream-tokens > span > span.meetings-stream-fact`
- **M7** target 16x14px — “Close Meetings”
- **M7** target 16x14px — “Minimize Meetings”
- **M7** target 79x23px — “Outcomes”
- **M7** target 66x23px — “Review”
- **M7** target 66x23px — “Record”
- **M7** target 85x23px — “Artifacts”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 11px — “Retry”
- **U1** 7 raw buttons vs 10 library — {"desk-light": 2, "desk-wing": 5}

</details>

### Speak — Blocks wing  <sub>`wing-speak-blocks`</sub>

- Family: wing · Door: Go > Speak > the 'Blocks' wing
- Opened by the rig via: `custom:wing:Speak|#surface-dictation|Blocks`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 10 | n/a | 1/13 | 0 | 2 | 9 | 0 | 0 | 0 | 6440 | M7, M8, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 10 | 9 | 1/13 | 0 | 2 | 8 | 0 | 0 | 0 | 6584 | M7, M8, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 10 | n/a | 1/13 | 0 | 2 | 9 | 0 | 0 | 0 | 6566 | M7, M8, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 10 | 9 | 1/13 | 0 | 2 | 8 | 0 | 0 | 0 | 6529 | M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “↻” `div.surface-stream-head > span.surface-stream-controls > span.gadget-cycle > span.gadget-cycle-glyph`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “No routing blocks on this scope yet”
- **U1** 9 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 5, "surface-tile-ghost-btn": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “↻” `div.surface-stream-head > span.surface-stream-controls > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “No routing blocks on this scope yet”
- **U1** 8 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 5, "surface-tile-ghost-btn": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “↻” `div.surface-stream-head > span.surface-stream-controls > span.gadget-cycle > span.gadget-cycle-glyph`
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “No routing blocks on this scope yet”
- **U1** 9 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 5, "surface-tile-ghost-btn": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “↻” `div.surface-stream-head > span.surface-stream-controls > span.gadget-cycle > span.gadget-cycle-glyph`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “No routing blocks on this scope yet”
- **U1** 8 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 5, "surface-tile-ghost-btn": 1}

</details>

### Speak — Journal wing  <sub>`wing-speak-journal`</sub>

- Family: wing · Door: Go > Speak > the 'Journal' wing
- Opened by the rig via: `custom:wing:Speak|#surface-dictation|Journal`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 12 | n/a | 0/15 | 0 | 2 | 9 | 0 | 0 | 0 | 6452 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 12 | 14 | 0/15 | 0 | 2 | 8 | 0 | 0 | 0 | 6649 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 12 | n/a | 0/15 | 0 | 2 | 9 | 0 | 0 | 0 | 6544 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 12 | 14 | 0/15 | 0 | 2 | 8 | 0 | 0 | 0 | 6583 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “ALL” `div.surface-ledger-head > span.surface-ledger-controls > span.surface-filter-tokens.journal-filters > button.btn.btn--secondary`
- **U1** 9 raw buttons vs 6 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “ALL” `div.surface-ledger-head > span.surface-ledger-controls > span.surface-filter-tokens.journal-filters > button.btn.btn--secondary`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **U1** 8 raw buttons vs 6 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “ALL” `div.surface-ledger-head > span.surface-ledger-controls > span.surface-filter-tokens.journal-filters > button.btn.btn--secondary`
- **U1** 9 raw buttons vs 6 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 11px — “ALL” `div.surface-ledger-head > span.surface-ledger-controls > span.surface-filter-tokens.journal-filters > button.btn.btn--secondary`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **U1** 8 raw buttons vs 6 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 1}

</details>

### Speak — Learned wing  <sub>`wing-speak-learned`</sub>

- Family: wing · Door: Go > Speak > the 'Learned' wing
- Opened by the rig via: `custom:wing:Speak|#surface-dictation|Learned`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | n/a | 0/11 | 0 | 2 | 8 | 0 | 0 | 0 | 6511 | M7, U1 |
| cold | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | 9 | 0/11 | 0 | 2 | 7 | 0 | 0 | 0 | 6519 | M7, U1 |
| rich | 1440 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | n/a | 0/11 | 0 | 2 | 8 | 0 | 0 | 0 | 6572 | M7, U1 |
| rich | 393 | ok | 0 | 0 | 0 | 0/0 | 0 | 0 | 8 | 9 | 0/11 | 0 | 2 | 7 | 0 | 0 | 0 | 6599 | M7, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “THIS DEVICE” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout.speak-footer > div.surface-footer-egress > span.gadget-chip.gadget-chip-egress`
- **U1** 8 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 5}

</details>

<details><summary>cold @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “THIS DEVICE” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout.speak-footer > div.surface-footer-egress > span.gadget-chip.gadget-chip-egress`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **U1** 7 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 5}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “THIS DEVICE” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout.speak-footer > div.surface-footer-egress > span.gadget-chip.gadget-chip-egress`
- **U1** 8 raw buttons vs 2 library — {"desk-light": 3, "desk-wing": 5}

</details>

<details><summary>rich @393 — evidence</summary>

- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 10px — “THIS DEVICE” `footer.desk-surface-foot.surface-footer > div.surface-footer-layout.speak-footer > div.surface-footer-egress > span.gadget-chip.gadget-chip-egress`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **U1** 7 raw buttons vs 2 library — {"desk-light": 2, "desk-wing": 5}

</details>

### Speak — Speak wing  <sub>`wing-speak-speak`</sub>

- Family: wing · Door: Go > Speak > the 'Speak' wing
- Opened by the rig via: `custom:wing:Speak|#surface-dictation|Speak`

| desk | w | status | ovf | cut | out | folds | empty | dup | <12px | <44px | contrast | err | fonts | raw | prim | 0-ctr | prose | ms | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 1440 | ok | 0 | 1 | 0 | 0/0 | 0 | 0 | 26 | n/a | 9/31 | 0 | 4 | 11 | 0 | 0 | 0 | 6448 | M10, M2, M7, M8, U1 |
| cold | 393 | ok | 0 | 1 | 0 | 0/0 | 0 | 0 | 26 | 12 | 9/31 | 0 | 4 | 10 | 0 | 0 | 0 | 6328 | M10, M2, M7, M8, U1 |
| rich | 1440 | ok | 0 | 1 | 0 | 0/0 | 0 | 0 | 26 | n/a | 9/31 | 0 | 4 | 11 | 0 | 0 | 0 | 6437 | M10, M2, M7, M8, U1 |
| rich | 393 | ok | 0 | 1 | 0 | 0/0 | 0 | 0 | 26 | 12 | 9/31 | 0 | 4 | 10 | 0 | 0 | 0 | 6511 | M10, M2, M7, M8, U1 |

<details><summary>cold @1440 — evidence</summary>

- **M2** `div.desk-surface-body > div.speak-face > div.speak-lands-in > label.gadget-check-token.is-off` hides 14px on y — “DRY RUN”
- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 9px — “Talk” `div.speak-face > div.speak-transport > button.desk-mic.gadget-transport-key > span.gadget-transport-word`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 9px — “Level”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “LANDS IN”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “·”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “DRY RUN”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “DICTATION”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “·”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “HOTKEY”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (26); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (2); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "JetBrains Mono", monospace (1)
- **U1** 11 raw buttons vs 4 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 1, "gadget-transport-key": 1, "surface-disclosure-trigger": 1}

</details>

<details><summary>cold @393 — evidence</summary>

- **M2** `div.desk-surface-body > div.speak-face > div.speak-lands-in > label.gadget-check-token.is-off` hides 14px on y — “DRY RUN”
- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 9px — “Talk” `div.speak-face > div.speak-transport > button.desk-mic.gadget-transport-key > span.gadget-transport-word`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 9px — “Level”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “LANDS IN”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “·”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “DRY RUN”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “DICTATION”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “·”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “HOTKEY”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (26); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (2); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "JetBrains Mono", monospace (1)
- **U1** 10 raw buttons vs 4 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 1, "gadget-transport-key": 1, "surface-disclosure-trigger": 1}

</details>

<details><summary>rich @1440 — evidence</summary>

- **M2** `div.desk-surface-body > div.speak-face > div.speak-lands-in > label.gadget-check-token.is-off` hides 14px on y — “DRY RUN”
- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 9px — “Talk” `div.speak-face > div.speak-transport > button.desk-mic.gadget-transport-key > span.gadget-transport-word`
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 9px — “Level”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “LANDS IN”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “·”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “DRY RUN”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “DICTATION”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “·”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “HOTKEY”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (26); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (2); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "JetBrains Mono", monospace (1)
- **U1** 11 raw buttons vs 4 library — {"desk-light": 3, "desk-wing": 5, "desk-mic": 1, "gadget-transport-key": 1, "surface-disclosure-trigger": 1}

</details>

<details><summary>rich @393 — evidence</summary>

- **M2** `div.desk-surface-body > div.speak-face > div.speak-lands-in > label.gadget-check-token.is-off` hides 14px on y — “DRY RUN”
- **M4** tab bar `div.desk-surface-windows > div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings`: Speak, Journal, Blocks, Learned, ⚙︎
- **M4** tab bar `div#surface-dictation > header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs`: Speak, Journal, Blocks, Learned
- **M7** 10px — “Speak” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing.is-on`
- **M7** 10px — “Journal” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Blocks” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 10px — “Learned” `header.desk-pullout-head.desk-window-handle > span.desk-wings > span.desk-wings-tabs > button.desk-wing`
- **M7** 11px — “⚙︎” `header.desk-pullout-head.desk-window-handle > span.desk-wings > button.desk-wing.desk-wing-door > span`
- **M7** 9px — “Talk” `div.speak-face > div.speak-transport > button.desk-mic.gadget-transport-key > span.gadget-transport-word`
- **M7** target 16x14px — “Close Speak”
- **M7** target 16x14px — “Minimize Speak”
- **M7** target 59x23px — “Speak”
- **M7** target 72x23px — “Journal”
- **M7** target 66x23px — “Blocks”
- **M7** target 72x23px — “Learned”
- **M8** 3.79:1 (needs 4.5) rgb(242, 243, 245) on rgb(168, 110, 74) at 9px — “Talk”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 9px — “Level”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “LANDS IN”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “·”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “DRY RUN”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “DICTATION”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “·”
- **M8** 4.38:1 (needs 4.5) rgb(118, 126, 141) on rgb(21, 23, 29) at 11px — “HOTKEY”
- **M10** "JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace (26); system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif (2); Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif (2); "JetBrains Mono", monospace (1)
- **U1** 10 raw buttons vs 4 library — {"desk-light": 2, "desk-wing": 5, "desk-mic": 1, "gadget-transport-key": 1, "surface-disclosure-trigger": 1}

</details>

## 3. The worst surfaces, ranked by failing rules

| # | surface | family | rules failed | ids |
|---|---|---|---|---|
| 1 | Components | application | 12 | C3, M1, M10, M2, M3, M4, M5, M6, M7, M8, U1, U4 |
| 2 | The Floor | application | 9 | M1, M10, M2, M3, M6, M7, M8, U1, U3 |
| 3 | The window switcher (⌃`) | state | 9 | M1, M10, M2, M3, M6, M7, M8, U1, U4 |
| 4 | Artifact pullout | pullout | 8 | M1, M10, M3, M4, M5, M7, M8, U1 |
| 5 | Meeting pullout | pullout | 8 | M1, M10, M2, M3, M4, M7, M8, U1 |
| 6 | Project pullout (FallbackPullout) | pullout | 8 | M1, M10, M2, M3, M6, M7, M8, U1 |
| 7 | Repository pullout (FallbackPullout) | pullout | 8 | M1, M2, M3, M5, M6, M7, M8, U1 |
| 8 | Workbench pullout (FallbackPullout) | pullout | 8 | M1, M10, M2, M3, M6, M7, M8, U1 |
| 9 | Repository window | state | 8 | M1, M2, M3, M5, M6, M7, M8, U1 |
| 10 | Workbench window | state | 8 | M1, M10, M2, M3, M6, M7, M8, U1 |
| 11 | Meetings — the gear door (Meeting plumbing) | wing | 7 | M1, M2, M3, M5, M6, M7, U1 |
| 12 | Speak — the gear door (Configure dictation) | wing | 7 | A7, M3, M4, M5, M7, U1, U3 |
| 13 | Workflow pullout | pullout | 7 | M1, M10, M3, M4, M7, M8, U1 |
| 14 | The ⌘K palette | chrome | 7 | M1, M2, M3, M6, M7, M8, U1 |
| 15 | Meetings — Outcomes wing | wing | 7 | M1, M10, M3, M6, M7, M8, U1 |
| 16 | The Chair (home) | application | 6 | M10, M3, M7, M8, U1, U4 |
| 17 | New Project | application | 6 | C3, M10, M7, M8, U1, U4 |
| 18 | Thread pullout | pullout | 6 | M1, M10, M3, M7, M8, U1 |
| 19 | Meetings — Artifacts wing | wing | 6 | M1, M3, M6, M7, M8, U1 |
| 20 | Meetings — Review wing | wing | 6 | M1, M3, M6, M7, M8, U1 |
| 21 | Ask AI | application | 5 | M4, M7, M8, U1, U3 |
| 22 | Runtime docs (an alias onto Settings' Guide wing) | application | 5 | C3, M4, M6, M7, U1 |
| 23 | Agents — the gear door (How it connects) | wing | 5 | M1, M2, M7, M8, U1 |
| 24 | Panes (the session picker) | state | 5 | M1, M3, M7, M8, U1 |
| 25 | Trust window (Data boundaries) | state | 5 | M10, M3, M6, M7, U1 |
| 26 | Agents — Roster wing | wing | 5 | M1, M2, M7, M8, U1 |
| 27 | Speak — Speak wing | wing | 5 | M10, M2, M7, M8, U1 |
| 28 | Intelligence | application | 4 | M10, M7, M8, U1 |
| 29 | Live meeting | application | 4 | C3, M7, M8, U1 |
| 30 | Activity — the gear door (Candidates and connectors) | wing | 4 | M5, M6, M7, U1 |

## 4. Top findings

- **U1** — 2082 raw `<button>` renders against 869 library Buttons across 287 measured legs. Every raw one is a bounce by UX-CANON A.1 (the library Button is `web/src/components/signal/Signal.tsx:36`, which stamps `btn btn--<variant>`). Seam: the library Button is `web/src/components/signal/Signal.tsx:36` (it stamps `btn btn--<variant>`); every visible `button` without `.btn` is a bounce.
- **M6** — 54 of 287 legs state something twice on one screen; 155 duplicate strings in all.
- **M8** — 560 text elements below WCAG AA out of 8647 assessed; 48 more NOT ASSESSED (painted over a wallpaper or gradient).
- **M7** — 4358 text elements render below 12px. Seam: the interior type scale lives in `web/src/styles/tokens.css`; menu keycaps are `.desk-menu-well` (`web/src/desk/components/DeskMenu.tsx:242`).
- **M7 (touch)** — at 393, 1350 verbs are under 44px across 140 legs. Seam: the interior type scale lives in `web/src/styles/tokens.css`; menu keycaps are `.desk-menu-well` (`web/src/desk/components/DeskMenu.tsx:242`).
- **M1** — 47 legs overflow horizontally (document, window, or an inner clip). Seam: window furniture: `.desk-window-edge-r { right: -3px }` `web/src/desk/components/window-chrome.css:42` (subtracted); the dock is `web/src/desk/components/window/Dock.tsx`.
- **M2** — 124 elements show text that is cut off.
- **U3** — 11 counters of zero rendered (UX-CANON A.8 forbids them). Seam: zone rows carry their count in the aria-label even at zero (the Floor's zone buttons).
- **A7** — 4 sentences over 12 words outside note/transcript content. Seam: the empty Floor's prose line is `web/src/desk/components/EmptyDesk.tsx` (“or right-click for more options”).
- **U4** — 16 legs draw more than one filled primary.
- **M9** — 0 legs carry a console error or a 4xx/5xx.
- **M10** — 63 legs render more than two font stacks.
- **C3** — 8 surfaces have no door a stranger can find: Calendar snapshot, Components, Live meeting, New Project, People, Runtime docs (an alias onto Settings' Guide wing), The Presence HUD (/presence), The Welcome arrival page (/welcome). Seam: the Go shelf is a projection of `group` in the application manifest (`web/src/desk/tools.ts:4`); an application with no `group` has no Go row.

## 5. What could not be opened

| surface | desk | w | why |
|---|---|---|---|
| Calendar snapshot | cold | 1440 | NO DOOR: opened only by dropping an .ics on the desk (GlassDropLayer.tsx:68); it needs a dropped-file payload as its scope, which this rig does not forge |
| Calendar snapshot | cold | 393 | NO DOOR: opened only by dropping an .ics on the desk (GlassDropLayer.tsx:68); it needs a dropped-file payload as its scope, which this rig does not forge |
| Calendar snapshot | rich | 1440 | NO DOOR: opened only by dropping an .ics on the desk (GlassDropLayer.tsx:68); it needs a dropped-file payload as its scope, which this rig does not forge |
| Calendar snapshot | rich | 393 | NO DOOR: opened only by dropping an .ics on the desk (GlassDropLayer.tsx:68); it needs a dropped-file payload as its scope, which this rig does not forge |
| Chain pullout | rich | 1440 | ?open=chain:chain_be4e9818606d drew no `.desk-pullout` within 12s (the ref resolves against the LOADED desk store — web/src/desk/store/compositorSlice.ts:137 warns `unknown id` otherwise) |
| Chain pullout | rich | 393 | TimeoutError: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for get_by_role("button", name="Floor").first
    - locator resolved to <button type="button" aria-label="Floor" aria-pressed="false" class="desk-dock-launch" data-testid="chair |
| Coder pullout | rich | 1440 | no seeded coder — NOT SEEDABLE: read from the companion process (/api/coders/status) |
| Coder pullout | rich | 393 | no seeded coder — NOT SEEDABLE: read from the companion process (/api/coders/status) |
| Decision pullout | rich | 1440 | no seeded decision — one seeded object of this kind |
| Decision pullout | rich | 393 | no seeded decision — one seeded object of this kind |
| Zone (directory) pullout | rich | 1440 | ?open=directory:dir_26449676258f drew no `.desk-zone-window` within 12s (the ref resolves against the LOADED desk store — web/src/desk/store/compositorSlice.ts:137 warns `unknown id` otherwise) |
| Zone (directory) pullout | rich | 393 | TimeoutError: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for get_by_role("button", name="Floor").first
    - locator resolved to <button type="button" aria-label="Floor" aria-pressed="false" class="desk-dock-launch" data-testid="chair |
| Game pullout (FallbackPullout) | rich | 1440 | no seeded game — NOT SEEDABLE: SyncClass local (web/src/lib/primitives.ts:26) |
| Game pullout (FallbackPullout) | rich | 393 | no seeded game — NOT SEEDABLE: SyncClass local (web/src/lib/primitives.ts:26) |
| Knowledge pullout | rich | 1440 | ?open=kb:kb_8dcbd182f083 drew no `.desk-pullout` within 12s (the ref resolves against the LOADED desk store — web/src/desk/store/compositorSlice.ts:137 warns `unknown id` otherwise) |
| Knowledge pullout | rich | 393 | TimeoutError: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for get_by_role("button", name="Floor").first
    - locator resolved to <button type="button" aria-label="Floor" aria-pressed="false" class="desk-dock-launch" data-testid="chair |
| Layout pullout (FallbackPullout) | rich | 1440 | no seeded layout — NOT SEEDABLE: SyncClass local (web/src/lib/primitives.ts:26) |
| Layout pullout (FallbackPullout) | rich | 393 | no seeded layout — NOT SEEDABLE: SyncClass local (web/src/lib/primitives.ts:26) |
| Agent (recipe) pullout | rich | 1440 | ?open=recipe:recipe_d0320b62db84 drew no `.desk-pullout` within 12s (the ref resolves against the LOADED desk store — web/src/desk/store/compositorSlice.ts:137 warns `unknown id` otherwise) |
| Agent (recipe) pullout | rich | 393 | TimeoutError: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for get_by_role("button", name="Floor").first
    - locator resolved to <button type="button" aria-label="Floor" aria-pressed="false" class="desk-dock-launch" data-testid="chair |
| Roadmap pullout (FallbackPullout) | rich | 1440 | no seeded roadmap — read-only, derived from pm/roadmap/ (roadmaps.py:179) |
| Roadmap pullout (FallbackPullout) | rich | 393 | no seeded roadmap — read-only, derived from pm/roadmap/ (roadmaps.py:179) |
| Story pullout (FallbackPullout) | rich | 1440 | no seeded story — NOT SEEDABLE: no wire endpoint (web/src/desk/api.ts:522) |
| Story pullout (FallbackPullout) | rich | 393 | no seeded story — NOT SEEDABLE: no wire endpoint (web/src/desk/api.ts:522) |
| Settings module — Assignments | cold | 1440 | the Settings hub has no 'Assignments' row with an Open verb (probe: no-row (8 rows: Models⚠NO DEFAULTOpen / Connections1 CONNECTEDOpen / Voice✓LIVEAUTOOpen / Meetings✓INTELLIGENCE ON · AFTER ROOM ME / RhythmEVERY 15 MINOpen / Sounds & Presence✓ONOpen / WallpaperRainy CityOpen / SystemTHIS DEVICEMESH OFFREMOTE OFFOpen); the module roster is web/src/pages/cores/settingsPrefs.tsx:40) |
| Settings module — Assignments | cold | 393 | the Settings hub has no 'Assignments' row with an Open verb (probe: no-row (8 rows: Models⚠NO DEFAULTOpen / Connections1 CONNECTEDOpen / Voice✓LIVEAUTOOpen / Meetings✓INTELLIGENCE ON · AFTER ROOM ME / RhythmEVERY 15 MINOpen / Sounds & Presence✓ONOpen / WallpaperRainy CityOpen / SystemTHIS DEVICEMESH OFFREMOTE OFFOpen); the module roster is web/src/pages/cores/settingsPrefs.tsx:40) |
| Settings module — Assignments | rich | 1440 | the Settings hub has no 'Assignments' row with an Open verb (probe: no-row (8 rows: Models⚠NO DEFAULT1 ENGINEOpen / Connections1 CONNECTEDOpen / Voice✓LIVEAUTOOpen / Meetings✓INTELLIGENCE ON · AFTER ROOM ME / RhythmEVERY 15 MINOpen / Sounds & Presence✓ONOpen / WallpaperRainy CityOpen / SystemTHIS DEVICEMESH OFFREMOTE OFFOpen); the module roster is web/src/pages/cores/settingsPrefs.tsx:40) |
| Settings module — Assignments | rich | 393 | the Settings hub has no 'Assignments' row with an Open verb (probe: no-row (8 rows: Models⚠NO DEFAULT1 ENGINEOpen / Connections1 CONNECTEDOpen / Voice✓LIVEAUTOOpen / Meetings✓INTELLIGENCE ON · AFTER ROOM ME / RhythmEVERY 15 MINOpen / Sounds & Presence✓ONOpen / WallpaperRainy CityOpen / SystemTHIS DEVICEMESH OFFREMOTE OFFOpen); the module roster is web/src/pages/cores/settingsPrefs.tsx:40) |
| Settings module — Voice | cold | 1440 | TimeoutError: Locator.wait_for: Timeout 12000ms exceeded.
Call log:
  - waiting for locator("#surface-settings .prefs-hub") to be visible
 |
| Settings module — Voice | cold | 393 | TimeoutError: Locator.wait_for: Timeout 12000ms exceeded.
Call log:
  - waiting for locator("#surface-settings .prefs-hub") to be visible
 |
| Settings module — Voice | rich | 1440 | TimeoutError: Locator.wait_for: Timeout 12000ms exceeded.
Call log:
  - waiting for locator("#surface-settings .prefs-hub") to be visible
 |
| Settings module — Voice | rich | 393 | TimeoutError: Locator.wait_for: Timeout 12000ms exceeded.
Call log:
  - waiting for locator("#surface-settings .prefs-hub") to be visible
 |
| The ＋Create menu (empty Floor only) | cold | 1440 | no ＋Create verb: it lives only inside EmptyDesk (web/src/components/EmptyDesk.tsx:37) and the Floor is never empty — the product furnishes zones on first boot (.desk-empty present=0). So this face has NO DOOR on any real desk. |
| The ＋Create menu (empty Floor only) | cold | 393 | no ＋Create verb: it lives only inside EmptyDesk (web/src/components/EmptyDesk.tsx:37) and the Floor is never empty — the product furnishes zones on first boot (.desk-empty present=0). So this face has NO DOOR on any real desk. |
| The ＋Create menu (empty Floor only) | rich | 1440 | no ＋Create verb: it lives only inside EmptyDesk (web/src/components/EmptyDesk.tsx:37) and the Floor is never empty — the product furnishes zones on first boot (.desk-empty present=0). So this face has NO DOOR on any real desk. |
| The ＋Create menu (empty Floor only) | rich | 393 | no ＋Create verb: it lives only inside EmptyDesk (web/src/components/EmptyDesk.tsx:37) and the Floor is never empty — the product furnishes zones on first boot (.desk-empty present=0). So this face has NO DOOR on any real desk. |
| The Desk menu | cold | 393 | no 'Desk' title in the menu bar at this width |
| The Desk menu | rich | 393 | no 'Desk' title in the menu bar at this width |
| The Interview | rich | 1440 | no Interview verb on the Room at this width |
| The Interview | rich | 393 | no Interview verb on the Room at this width |
| The Object menu | cold | 393 | no 'Object' title in the menu bar at this width |
| The Object menu | rich | 393 | no 'Object' title in the menu bar at this width |
| The Window menu | cold | 393 | no 'Window' title in the menu bar at this width |
| The Window menu | rich | 393 | no 'Window' title in the menu bar at this width |
| Exposé (all windows) | cold | 1440 | no Expose verb found in the Window menu at this width (windows open: Meetings, Settings) |
| Exposé (all windows) | cold | 393 | no Expose verb found in the Window menu at this width (windows open: Meetings, Settings) |
| Exposé (all windows) | rich | 1440 | no Expose verb found in the Window menu at this width (windows open: Meetings, Settings) |
| Exposé (all windows) | rich | 393 | no Expose verb found in the Window menu at this width (windows open: Meetings, Settings) |
| The Floor as a list | cold | 1440 | the Floor drew no .desk-list-view and no List toggle was found — list view is automatic only at <=720px (web/src/desk/DeskApp.tsx:190) |
| The Floor as a list | cold | 393 | the Floor drew no .desk-list-view and no List toggle was found — list view is automatic only at <=720px (web/src/desk/DeskApp.tsx:190) |
| The Floor as a list | rich | 1440 | the Floor drew no .desk-list-view and no List toggle was found — list view is automatic only at <=720px (web/src/desk/DeskApp.tsx:190) |
| The Floor as a list | rich | 393 | the Floor drew no .desk-list-view and no List toggle was found — list view is automatic only at <=720px (web/src/desk/DeskApp.tsx:190) |
| Roadmap window | rich | 1440 | no seeded roadmap — a roadmap under pm/roadmap/ |
| Roadmap window | rich | 393 | no seeded roadmap — a roadmap under pm/roadmap/ |
| The System shade (Missed) | rich | 1440 | no 'Desk memory' launcher in the dock at this width |
| The System shade (Missed) | rich | 393 | no 'Desk memory' launcher in the dock at this width |
| Thought workspace window | rich | 393 | no 'Develop this thought' verb on the note pullout (web/src/desk/pullouts/NotePullout.tsx:483) |

## 6. What this rig does NOT measure

- **M11 (spacing on the 4/8 rhythm)** — NOT ASSESSED. Computed gaps are resolved pixels; a token-derived 6px and a hand-typed 6px are indistinguishable to the DOM, so a count here would be a guess.
- **M12 (reduced motion, animation ≤ 400 ms)** — NOT ASSESSED. This walk settles animations before it shoots, which is the opposite of measuring them; a separate pass with `prefers-reduced-motion` toggled is the honest way.
- **D1/D2 (raw hex, raw px, the type scale)** — NOT ASSESSED at runtime: computed styles have already resolved the tokens. This is a source audit.
- **M4's 'not signalled' half** — this rig counts folds, tab bars and scroll containers and says what each hides. Whether the surface *signals* the hidden content is a reading, made in §4 from the counts, not a number.
- **M8 over an image or gradient** — text painted over a wallpaper or gradient is skipped and counted in `skippedOverImage`, never scored 0.
- **U3 in accessible names** — the rig counts zero-counters in VISIBLE text only. Names read by assistive tech are not scanned, and at least one zero counter lives there: the Floor's zone rows render ``${row.count} items`` unconditionally (`web/src/desk/components/DeskListView.tsx:214`), so an empty zone announces “<name> zone, 0 items”.
- **C1/C2/C4/C5** — the coherence rules are a reading across faces, not a per-surface number; they belong to the inventory's other lanes.

