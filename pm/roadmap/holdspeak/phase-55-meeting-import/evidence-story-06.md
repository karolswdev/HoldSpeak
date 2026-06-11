# Evidence — HS-55-06: Closeout — real-audio dogfood + final-summary + PR

**Date:** 2026-06-11
**Branch:** `phase-55-meeting-import`

## 1. The real-metal dogfood (no fakes anywhere)

`dogfood_story06.py`: real `say` speech → the real `POST /api/meetings/import`
→ real MLX Whisper (the config's "small" model) → real intel on the LAN
llama.cpp endpoint (`http://192.168.1.43:8080/v1`, reachability probed first):

```
model: small · intel endpoint: http://192.168.1.43:8080/v1
recording: imported board sync.wav (1023 KiB)
PASS  202 with meeting id f5bbe254; transcribing with real Whisper…
      2 segment(s): ['The quarterly budget needs a final review before Friday.',
                     'We decided to ship the import feature next week.']
PASS  real Whisper transcript carries both expected phrases across 2 windows
PASS  real intel ready on http://192.168.1.43:8080/v1
      summary: The board call concluded with a decision to ship the import
      feature next week and set a deadline for the final quarterly budget
      review by Friday.
PASS  facets include (speaker+tag) and exclude (wrong speaker) correctly
PASS  /history screenshot captured
RESULT: PASS
```

Worth noting: real Whisper transcribed both utterances **verbatim**, the two
utterances landed in their two ~30 s windows exactly as designed (the second
was padded past the window boundary), the speaker label survived, and the
Qwen3.5-9B-Q6 summary is a *correct* reading of the synthetic meeting.
Screenshot: `screenshots/story06-imported-ready.png`.

**A bonus honest-failure proof:** the first run crashed on real metal because
this machine's config pins `model.backend="faster-whisper"`, which is not
installed here — and the import behaved exactly as designed: the row was
marked `import_failed` with the actionable detail ("faster-whisper is not
installed. On Linux, install it with…"). The live capture path builds its
`Transcriber` with the same config values, so this is a machine-config quirk,
not an import-specific gap; the dogfood's happy path resolves the backend as
"auto" (the same real Whisper model on MLX) and says so in its source.

## 2. Final state (actually run, actually read)

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2568 passed, 17 skipped in 82.98s (0:01:22)

$ cd web && npm run build
[build] Complete!
$ git ls-files holdspeak/static/_built | wc -l
0
```

(Phase total: 2545 → 2568, +23 tests across the five shipping stories.)

## 3. Tracking flips in this commit

- `final-summary.md` (what shipped, the honest limits, the finds, lessons).
- Phase **CLOSED (6/6)** in `current-phase-status.md` + the project README.
- `BACKLOG.md` candidate **I** flipped to **shipped → phase-55**.

## 4. PR

Branch `phase-55-meeting-import` pushed; PR to `main`; merged on green CI.
