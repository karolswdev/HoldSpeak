# Evidence — HS-57-01: The transcript parsers

**Date:** 2026-06-11
**Branch:** `phase-57-transcript-import`

## 1. What shipped

**`holdspeak/transcript_parse.py`** — pure (no I/O, no db, no config; locked
by test): `parse_transcript(text, filename, *, fallback_speaker)` →
`ParsedTranscript(cues, has_real_timestamps, speakers_found)`.

- **VTT:** BOM + CRLF tolerated; header required (and content beginning
  `WEBVTT` is parsed as VTT regardless of suffix — tools mislabel exports);
  NOTE/STYLE/REGION blocks skipped; cue-identifier lines ignored;
  hour-optional `MM:SS.mmm` timings; `<v Name>` voice tags (closing tag
  optional; a bare cue continues the previous voice, per the VTT voice
  model); inline styling tags stripped; multi-line cue text joined;
  `end <= start` clamped.
- **SRT:** numeric indices ignored; comma-decimal timings; `Name: text`
  first-line prefixes via the shared conservative rule; unlabeled cues
  continue the previous speaker.
- **TXT:** the conservative `Name:` rule (starts with a letter,
  letters/space/`.'-` only — digits excluded so clock times never match,
  ≤3 words, a real space after the colon so URLs never match, plus a
  blocklist of structure labels like Note/Agenda/Action); unlabeled lines
  continue the current voice (chat-style wrapping); synthetic
  evenly-spaced timestamps (6 s); `has_real_timestamps=False`.
- **Honesty flags:** `speakers_found` lists ONLY file-carried labels;
  `has_real_timestamps` is True only for cue-timed formats.
- **Refusals:** empty input, binary garbage (printable-ratio gate),
  header-less `.vtt`, header-only VTT, timing-less `.srt`, unsupported
  suffixes — all `TranscriptParseError` with actionable messages; an
  import can never silently produce an empty meeting.

One rule tightened during testing: the name-prefix limit went from 4 words
to 3 — "The plan is simple: ship it" is a 4-word name-shaped fragment, and
the conservative posture says a missed speaker label is cheaper than a
fabricated one.

## 2. Tests

`tests/unit/test_transcript_parse.py` — 22 tests: a Teams/Zoom-shaped VTT
fixture (BOM, CRLF, NOTE, identifiers, voice-tag-without-close, styling
tags, hour-less timing, voice continuity), multi-line joins, header
refusals, fallback-speaker honesty, suffix-mislabel rescue, end-clamp; SRT
comma times + name prefixes + refusal; TXT label/continuation, the
name-rule negative table (URL, clock time, Note:/Agenda:, 4-word fragment),
fallback; empty/binary/suffix refusals; the purity lock and the suffix
registry.

```
$ uv run pytest -q tests/unit/test_transcript_parse.py
22 passed in 0.03s
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2624 passed, 17 skipped
```

(2602 → 2624.) Nothing existing touched — the module is greenfield.
