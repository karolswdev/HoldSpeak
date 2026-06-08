# Evidence — HS-53-07: close the loop (the selection feeds the model, proven on metal)

Write-once record of the story that turned "Dictate with this" from a visible
affordance into a real capability: the selected `ActivityRecord` now reaches the
rewrite prompt, and a live LLM demonstrably writes a different, issue-grounded
result because of it.

## The gap this closed

A real-metal trace for the closeout found the loop open in two places:

- `dictation_runner.run_dictation_pipeline` built the activity context with **no**
  `selected_record_id` — the live path never read the pin.
- `project_rewriter.py` read only `activity["target"]` / `activity["agent"]` —
  the rewriter never consumed `records`, so HS-53-03's `records[0]` pin was inert.

So clicking "Dictate with this" changed nothing the model saw. This story fixes
both ends and proves the fix on the `.43` Qwen3.5-9B-Q6 endpoint.

## What shipped

- **`holdspeak/dictation_selection.py`** — a process-local, one-shot,
  recency-bounded selection pin. `set_selected_record(id)` parks the choice;
  `consume_selected_record(max_age_seconds=300)` returns it once and clears it (a
  stale pin is dropped unused); `clear_selected_record()` / `peek_selected_record()`
  round it out. Process-local by design: the pin is ephemeral intent that lives
  for the seconds between a click and the next utterance, and the web server +
  dictation runner share one process. It mirrors the recency-bounded
  `get_recent_awaiting_agent_session` lookup the agent-reply path already uses.

- **`run_dictation_pipeline` consumes the pin** (`dictation_runner.py`): right
  before building the activity context it calls `consume_selected_record()` and
  passes the id to `build_activity_context(selected_record_id=...)`. No pending
  pin -> `None` -> the default daily path is byte-identical.

- **The project-rewriter names the record to the model**
  (`project_rewriter.py:_selected_activity_context`): when
  `activity["selected_record_id"]` matches a record in `activity["records"]`, it
  formats a one-line source-cited reference — `github_issue owner/repo#N titled
  "..." (url)` — and injects it into **both** the draft and refine prompts, with a
  rule: *"ground the rewrite in that specific issue/PR/page and reference it by
  name."* No selection -> empty string -> byte-identical prompt. An unknown id (no
  matching record) is inert — no fabrication.

- **Two routes + frontend wiring** (`web/routes/activity/nudges.py`,
  `web/src/scripts/dictation-app.js`):
  - `POST /api/activity/nudges/select {record_id}` validates the id against the
    real ledger (`get_activity_record`; unknown -> 400) and parks it.
  - `POST /api/activity/nudges/select/clear` drops it.
  - "Dictate with this" now POSTs the selection (in addition to the localStorage
    affordance pin); "Clear" POSTs the clear. The visible pin is the affordance;
    the POST is what actually arms the next dictation.

## The real-metal proof (the heart of the story)

`dogfood_real_llm.py` drives the **real** project-rewriter against
`192.168.1.43:8080` over the `.hs`-grounded demo fixture, running the *same*
generic dictation twice. The dictation names its subject only as "the issue I was
just looking at" — so any concrete reference can only come from the selected
record:

- **CONTROL (no selection):** *"Review the open issues in the `ledgerline`
  repository and select the most recent relevant item…"* — generic, grounded in
  the payments/ledger `.hs` context. No `#412`, no `--since`, no export.
- **TREATMENT (selected `github_issue karolswdev/HoldSpeak#412`):** *"Implement
  the `--since` flag in `src/ledgerline/api/charges.py` to filter exported ledger
  entries by date as requested in HoldSpeak#412…"* — fully grounded in the
  selected issue, down to a contextual `.hs/memory` doc-suggestion about the
  `--since` flag.

```
.venv/bin/python pm/roadmap/holdspeak/phase-53-activity-prebriefing/dogfood_real_llm.py
-> [PASS] TREATMENT references the selected issue (matched: ['412', '--since', 'since flag'])
   [PASS] CONTROL does NOT reference the issue (matched: none)
   [PASS] the selection changed the output
   RESULT: PASS
```

Full transcript: `dogfood-real-llm-transcript.txt`.

## Two real product guards surfaced (and respected)

- **The rewrite stage is `.hs`-gated.** Without repo-local `.hs` context the
  rewriter no-ops (the DIR-01 design). The selected record augments an existing
  rewrite; it does not force one. The dogfood runs in the `.hs` demo fixture —
  the realistic surface for "dictate a reply with this issue as context".
- **`_rewrite_too_long` caps a draft at ~4x the input.** A one-line dictation
  caps the draft length, so a very short utterance + a long grounded task is
  rejected back to the input (a genuine guard against ballooning). The dogfood
  uses a realistic-length dictation so the grounded output fits — exactly how the
  feature behaves in product. This is honest about the constraint rather than
  papering over it.

## Why this is honest

- **Byte-identical default.** No pin -> `selected_record_id is None` ->
  `build_activity_context` unchanged; `_selected_activity_context` returns `""` ->
  the prompt is byte-for-byte what it was. Locked by
  `test_no_selection_leaves_prompt_unchanged` + the HS-53-03 default-path tests.
- **No fabrication.** An unknown id (select route or rewriter) is a clean 400 / an
  inert empty string — never a stub.
- **One-shot + recency-bounded.** A click that is never followed by a dictation
  decays; a single dictation consumes the pin once. `test_stale_pin_is_dropped_unused`,
  `test_set_then_consume_returns_id_once`.

## Tests

```
uv run pytest -q tests/unit/test_dictation_selection.py \
  tests/unit/test_dictation_selected_record_prompt.py \
  tests/integration/test_web_activity_nudges_api.py \
  tests/unit/test_dictation_project_rewriter.py \
  tests/unit/test_activity_context_selected.py
-> 47 passed

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2540 passed, 17 skipped   (was 2523 at HS-53-05; +17:
   8 selection + 5 prompt-grounding + 4 select/clear routes)

cd web && npm run build  -> 13 pages, no warnings; 0 _built/ tracked
```

## Files touched

- `holdspeak/dictation_selection.py` (new) — the one-shot selection pin.
- `holdspeak/dictation_runner.py` — consume the pin, pass `selected_record_id`.
- `holdspeak/plugins/dictation/builtin/project_rewriter.py` —
  `_selected_activity_context` + injection into both prompt builders.
- `holdspeak/web/routes/activity/nudges.py` — `select` + `select/clear` routes.
- `web/src/scripts/dictation-app.js` — POST the selection on "Dictate with this",
  POST clear on "Clear".
- `tests/unit/test_dictation_selection.py` (new) — 8 tests.
- `tests/unit/test_dictation_selected_record_prompt.py` (new) — 5 tests.
- `tests/integration/test_web_activity_nudges_api.py` — 4 select/clear route tests.
- `tests/unit/test_activity_routes_split.py` — route-table lock updated (+2 -> 42).
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/dogfood_real_llm.py` (new) +
  `dogfood-real-llm-transcript.txt` — the real-metal proof.
