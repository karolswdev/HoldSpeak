# Evidence — HS-53-06: closeout (dogfoods + final-summary + PR)

Write-once record of the phase exit. Two dogfoods prove the feature end to end,
the full suite + web build are green, and the phase is CLOSED with the docs
cadence applied.

## The dogfoods

- **`dogfood.py` (engine math, no LLM)** — seeds activity records + a prior
  meeting, then drives the engine + context path directly: a windowed,
  source-cited nudge is computed; a dismissal persists across a fresh `Database`
  handle; activity-off yields no nudges; selecting a record pins it at
  `records[0]` of the dictation context bundle.

  ```
  .venv/bin/python pm/roadmap/holdspeak/phase-53-activity-prebriefing/dogfood.py
  -> RESULT: PASS   (full transcript: dogfood-transcript.txt)
  ```

- **`dogfood_real_llm.py` (the closed loop on real metal)** — added with HS-53-07.
  Runs the **real** project-rewriter against the `.43` Qwen3.5-9B-Q6 endpoint over
  the `.hs` demo fixture, with the *same* generic dictation, with vs. without a
  selected `github_issue`:

  ```
  .venv/bin/python pm/roadmap/holdspeak/phase-53-activity-prebriefing/dogfood_real_llm.py
  -> [PASS] TREATMENT references the selected issue (matched: ['412', '--since', 'since flag'])
     [PASS] CONTROL does NOT reference the issue (matched: none)
     [PASS] the selection changed the output
     RESULT: PASS   (full transcript: dogfood-real-llm-transcript.txt)
  ```

  CONTROL: *"Review the open issues in the `ledgerline` repository…"* (generic).
  TREATMENT: *"Implement the `--since` flag … as requested in HoldSpeak#412"*
  (grounded in the selected record). The selection demonstrably changes what the
  model writes.

## Suite + build

```
uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2540 passed, 17 skipped   (was 2523 at HS-53-05; +17 from HS-53-07)

uv run pytest -q -k "doc_drift or doc_guard or roadmap or vocab"
-> 8 passed, 2 skipped

cd web && npm run build
-> 13 pages, no warnings; 0 _built/ tracked
```

## Closeout actions

- `final-summary.md` written (the course-correction from no-LLM → real metal is
  recorded honestly).
- Phase flipped to **CLOSED (7/7)**: `current-phase-status.md` header + story
  table, story-06 + story-07 statuses.
- Project `README.md` "Current phase" + "Last updated" updated per the operating
  cadence.
- `BACKLOG.md` candidate **F** flipped to **shipped**.
- PR to `main` opened and merged on green CI.

## Note on bundling

HS-53-06 ships in the same commit as HS-53-07 (`.tmp/BUNDLE-OK.md` rationale):
the closeout's exit criterion (the real-LLM dogfood) is the same artifact that
proves HS-53-07, and the closeout would otherwise reference an unshipped story.
