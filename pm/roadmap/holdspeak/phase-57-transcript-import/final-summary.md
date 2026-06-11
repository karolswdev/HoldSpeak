# Phase 57 — Transcript Import ("bring your archive", part 2): final summary

**Status:** CLOSED (5/5) — 2026-06-11 (opened and closed the same day)
**Branch → PR:** `phase-57-transcript-import` → PR to `main`, merged on green CI
**Backlog:** candidate **P** shipped (net-new on user direction, straight
after Phase 56: *"I often have transcripts, rarely do I have recordings"*).

## What the phase shipped

Upload a transcript — `.vtt` (the common Teams/Zoom/Meet export), `.srt`,
or plain `.txt` — on /history or via `holdspeak import`, and it becomes a
**real meeting** through the exact Phase-55 pipeline: same persistence,
same deferred intel, same search/facets/aftercare. The recording upload is
untouched (the user's explicit constraint, stated in the docs and locked
by the unmodified Phase-55 tests).

The transcript path is the *cheaper* sibling (no Whisper, no ffmpeg, no
model load — sub-second imports; the route never constructs a transcriber,
locked by a poisoned factory in tests and dogfoods) and carries one genuine
upgrade: **real multi-speaker labels** from VTT voice tags and `Name:`
prefixes, where audio import is single-label. The speaker facet works
across imported transcripts for the first time.

The honesty contract, end to end: real timestamps only from cue-timed
formats (plain text gets evenly spaced approximate times, never presented
as real moments); speaker names only from the file (never invented);
zero-cue input refused actionably (an import never silently creates an
empty meeting); the source file is not retained.

## Story by story

1. **HS-57-01 — the parsers** (`holdspeak/transcript_parse.py`, pure +
   greenfield): wild-VTT tolerance (BOM, CRLF, hour-less timings, voice
   tags without close tags, NOTE/STYLE blocks, styling tags, mislabeled
   suffixes rescued by the WEBVTT header), SRT comma times, the
   conservative ≤3-word `Name:` rule with a structure-label blocklist.
   22 tests + a purity lock.
2. **HS-57-02 — the engine + CLI**: the Phase-55 persistence tail factored
   verbatim into `_persist_import` (one tail, two callers; audio
   byte-identical); `import_transcript`; `validate_format` learns the
   trio; the CLI branches before any model load. 12 tests.
3. **HS-57-03 — API + UI**: the route worker branches by suffix on the
   same placeholder → `importing` → resolve / `import_failed` lifecycle;
   the panel becomes "Import a recording or transcript" with per-kind
   honest notes. 4 route tests + page locks; live browser dogfood 3/3.
4. **HS-57-04 — docs**: the Meeting Mode Guide's import section, extended
   honestly (formats, both honesty rules, the refusal posture,
   recordings-unchanged); guards green, zero dashes in new text.
5. **HS-57-05 — closeout**: the real-metal dogfood below; this summary;
   BACKLOG/README flips; PR.

## The closeout dogfood (real metal, zero mocks)

A realistic multi-speaker VTT through the real API → **real intel on the
`.43` llama.cpp endpoint** → the server-side speaker facet → a real spoken
WAV (`say` → real MLX Whisper) in the same run:

```
PASS  the VTT became a real meeting (5 segments, real cues, both speakers)
PASS  real intel ready on http://192.168.1.43:8080/v1
      summary: The team approved the database migration for Thursday night
      with Marek on call and decided to move two strong backend candidates
      to onsite i…
PASS  the server-side speaker facet filters by a transcript-carried name
PASS  the recording path still works: real Whisper heard 'we agreed to run
      the database migration on thursday night.'
PASS  /history rendered both imports with zero page errors
RESULT: PASS
```

The intel summary is an accurate digest of the fictional meeting, and the
snapshot extracted 2 action items — visible on the archive screenshot
(`story05-archive.png`: "infra weekly" Ready / 5 segments / 2 action items
/ both tags, beside the Whisper-imported "spoken followup").

## Real finds along the way

- **Untitled imports were named after the temp file** (`tmpvgz3bb27`) — a
  latent Phase-55 bug on the audio path too; the route now resolves the
  default title from the uploaded filename.
- **The binary-garbage gate counted U+FFFD as printable**, so utf-8-replaced
  binary uploads would have imported as "transcripts"; the parser now
  counts replacement chars as garbage.
- The `Name:` rule was tightened from 4 words to 3 during testing (a
  4-word sentence fragment matched; a missed label is cheaper than a
  fabricated one).

## Numbers

- Suite: 2602 (phase open) → **2641 passed, 17 skipped** (phase close);
  +39 tests (22 parsers, 12 engine, 4 route, 1 page lock).
- 5 stories, 5 shipping commits + scaffold, evidence in-commit throughout.

## What did NOT ship (deliberately)

DOCX/PDF/HTML transcripts, post-import transcript editing, word-level
timing, diarization — out of scope by the phase doc.

## Follow-ups

- None required. Next per the agreed sequence: **K — languages +
  spoken-symbol dictionary**.
