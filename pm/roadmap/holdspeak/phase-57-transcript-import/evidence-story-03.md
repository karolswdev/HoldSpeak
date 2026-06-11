# Evidence — HS-57-03: API + /history UI

**Date:** 2026-06-11
**Branch:** `phase-57-transcript-import`

## 1. What shipped

**The route** (`holdspeak/web/routes/meeting_import.py`): the worker
branches by suffix — a transcript upload runs `import_transcript` on the
same placeholder → `importing` → engine-save / `import_failed` lifecycle
and **never constructs a transcriber** (the per-kind speaker default is
resolved in the worker: `Transcript` vs. `Recording`); the placeholder
detail reads "Parsing transcript…" for transcripts. Audio behavior
untouched (the Phase-55 route tests pass unmodified).

**The panel** (`web/src/pages/history.astro`): "Import a recording or
transcript" (opener + title + lede), the accept list adds
`.vtt,.srt,.txt` (audio list untouched, asserted), the drop copy reads
"audio or transcript file", and the honest notes are per-kind: recordings
keep the ffmpeg / one-speaker-label truths; transcripts state that speaker
names are read from the file when it carries them and timestamps are real
for vtt/srt and approximate for plain text; either way the source file is
not kept and everything stays local.

## 2. Two real bugs found and fixed

1. **The untitled-import title fell back to the temp file's stem** (a
   latent Phase-55 bug, audio path included): the engine only ever sees
   the temp upload (`tmpvgz3bb27.vtt`), so `title or path.stem` produced
   noise. The route now resolves the default title from the UPLOADED
   filename before handing off. Found by the new route test.
2. **The binary-garbage gate counted U+FFFD as printable** — callers read
   bytes with `errors="replace"`, so a binary upload arrived as a wall of
   perfectly printable replacement chars and imported as a "transcript".
   The parser's gate now counts U+FFFD as garbage (a small HS-57-01
   amendment, noted here per the findings rule).

## 3. Live dogfood (real browser, real upload, poisoned transcriber)

`dogfood_story03.py` — the transcriber factory raises on construction, so
the no-model path is proven live:

```
PASS  the panel reads 'recording or transcript' with the per-kind honest notes
PASS  the browser-uploaded VTT became a real meeting: speakers
      ['Priya Sharma', 'Sam Kowalski']…, real cue starts [1.0, 5.5, 11.5, 15.5],
      intel 'queued', no transcriber ever built
PASS  zero page errors across the whole run
RESULT: PASS
```

Screenshots reviewed: `story03-panel.png` (the extended panel + honest
notes), `story03-importing.png` (the lifecycle pill caught live —
"Parsing transcript…"), `story03-resolved.png` (the resolved card:
"weekly product sync", Queued, 0:19, 4 segments, both tags).

## 4. Tests + suite

`tests/integration/test_web_transcript_import_api.py` — 4 tests under a
poisoned-factory fixture: the VTT happy path (file speakers + real cue
starts + title from the uploaded name), the TXT fallback speaker, the
binary-garbage `import_failed` + removable row, the header-only-VTT
parser message. Page locks extended in
`test_web_history_import_ui.py` (+1 test: the accept-list trio + the
audio list untouched; the honest-truths lock updated to the per-kind
copy).

```
$ uv run pytest -q tests/integration/test_web_transcript_import_api.py \
    tests/integration/test_web_meeting_import_api.py tests/unit/test_transcript_parse.py \
    tests/unit/test_transcript_import_engine.py tests/integration/test_web_history_import_ui.py
48 passed in 2.23s
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2641 passed, 17 skipped
$ (cd web && npm run build)   # clean; 0 _built/ tracked
```

(2636 → 2641: +4 route tests + 1 page lock.)
