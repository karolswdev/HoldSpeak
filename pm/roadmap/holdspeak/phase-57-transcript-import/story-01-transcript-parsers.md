# HS-57-01 — The transcript parsers

- **Project:** holdspeak
- **Phase:** 57
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-57-02
- **Owner:** unassigned

## Problem
HoldSpeak can import a recording but not the file most meeting tools
actually export: a transcript. Nothing in the tree parses VTT/SRT/TXT.

## Scope
- **In:** `holdspeak/transcript_parse.py`, pure (no I/O, no db):
  `parse_transcript(text, filename, *, fallback_speaker) -> ParsedTranscript`
  with cues `{text, speaker, start, end}`, `has_real_timestamps`, and
  `speakers_found`.
  - **VTT:** `WEBVTT` header (BOM/`\r\n` tolerated), cue-identifier lines,
    `HH:MM:SS.mmm --> HH:MM:SS.mmm` with optional hours, `<v Name>` voice
    tags (closing tag optional; bare cues continue the previous speaker),
    other inline tags stripped, NOTE/STYLE/REGION blocks skipped,
    multi-line cue text joined.
  - **SRT:** numeric cue indices, comma-decimal times, `Name: text`
    first-line prefixes via the shared conservative name rule.
  - **TXT:** `Name: text` prefixes (conservative rule: a short name-shaped
    prefix; URLs/clock-times/sentences must not match), raw lines
    otherwise; synthetic evenly-spaced timestamps; `has_real_timestamps`
    False.
  - Garbage / zero-cue input raises `TranscriptParseError` with an
    actionable message.
- **Out:** file handling, persistence, config, UI; DOCX/PDF/HTML.

## Acceptance criteria
- [ ] VTT: a realistic Teams/Zoom-shaped fixture parses with real
      timestamps + voice-tag speakers; spec quirks covered (optional
      hours, missing close tags, NOTE blocks, styling tags, BOM, CRLF).
- [ ] SRT: comma times + `Name:` prefixes parse; indices ignored.
- [ ] TXT: labeled and unlabeled lines parse; the name rule rejects URLs,
      clock times, and ordinary colon sentences; timestamps synthetic and
      monotonic.
- [ ] Malformed input (binary garbage, empty file, header-only VTT) raises
      `TranscriptParseError` with an actionable message.
- [ ] Pure module: no db/config/network imports (locked by test).

## Test plan
- `tests/unit/test_transcript_parse.py` — per-format happy paths, the quirk
  matrix, the name-rule negative table, malformed refusals. Full suite.

## Notes / open questions
- The speakers/timestamp honesty flags exist so downstream (engine, UI,
  docs) can state exactly what the file provided — keep them accurate.
