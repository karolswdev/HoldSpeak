# Evidence — HS-52-07: Closeout

Write-once record of the verified exit for Phase 52.

## The dogfood

`dogfood.py` drives `dictation_runner.dispatch_voice_command` directly (no mic),
captured in `dogfood-transcript.txt`, RESULT: PASS:

1. Off by default: a macros-disabled config returns `None` (byte-identical to no
   feature).
2. A non-keyword utterance ("write the weekly report") returns `None` (it would dictate
   normally).
3. A configured `shell` macro ("log it" -> `echo hello-from-voice > <temp>`) fires for
   real through the bounded connector + permission gate; the temp file is verified to
   contain the echoed text, and nothing was typed.
4. A `type_text` macro ("standup") types its snippet via the writer.

The shell case is a genuine end-to-end fire (a real subprocess through the gate), not a
mock, so the dogfood proves the whole path: match -> bounded connector -> guarded
execution.

## Suite + build

```
uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2499 passed, 17 skipped   (the phase started at 2454; +45 across its new tests)

cd web && npm run build
-> clean (/commands/index.html generated)
```

0 `holdspeak/static/_built/` tracked.

## Cadence at close

- `story-07` -> done; `final-summary.md` written.
- Phase flipped to CLOSED (7/7) in `current-phase-status.md`.
- Project `README.md`: phase row -> CLOSED, Current-phase pointer advanced, Last updated.
- `BACKLOG.md`: candidate **B** flipped to shipped; candidate **E** annotated that the
  dictation-dispatch slice landed and the rest stays a watch item.
- PR to `main` opened and merged on green CI.

## Not done (by design)

- Full candidate **E** (the rest of the `web_runtime` decomposition) remains a backlog
  watch item; this phase took only the dictation-dispatch slice.
- A persistent per-fire audit table (deferred; the actuator table is meeting-scoped).
