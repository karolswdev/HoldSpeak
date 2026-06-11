# HS-57-02 — The engine path + CLI

- **Project:** holdspeak
- **Phase:** 57
- **Status:** backlog
- **Depends on:** HS-57-01
- **Unblocks:** HS-57-03
- **Owner:** unassigned

## Problem
The parsers produce cues; nothing turns them into a persisted meeting. The
Phase-55 engine's persistence tail (state → intel posture → save → enqueue)
is exactly what they need — but it is welded to the audio path.

## Scope
- **In:**
  - Factor the persistence tail of `import_meeting` into a shared helper;
    the audio path calls it **byte-identically** (its tests pass
    unmodified).
  - `import_transcript(path, *, db, config, title, speaker, tags,
    started_at, meeting_id) -> ImportResult`: read + parse (HS-57-01) →
    segments with the file's real timestamps (or the synthetic ones) and
    speakers (fallback: the user label) → the shared tail. `started_at`
    defaults to file mtime; `ended_at` from the last cue. `ImportResult`
    stays truthful (no fake window counts).
  - `validate_format` learns `.vtt/.srt/.txt` (audio messages untouched).
  - The CLI (`holdspeak import <file>`) branches by suffix; transcripts
    build no transcriber and report cue/segment counts.
- **Out:** the web route/UI (HS-57-03); any change to audio behavior.

## Acceptance criteria
- [ ] The audio path is byte-identical: existing engine/route tests pass
      unmodified; the tail is one function with two callers.
- [ ] `import_transcript` mirrors the live intel-enqueue conditions and
      enqueues with the final transcript hash.
- [ ] Saved segments carry the file's real cue timestamps (VTT/SRT) or the
      synthetic ones (TXT), and the file's speaker labels reach the db
      (visible to the speaker facet / FTS).
- [ ] Zero-cue input refuses with the parser's actionable message; nothing
      is persisted.
- [ ] CLI: a `.vtt` imports without constructing a transcriber.

## Test plan
- Unit: tail-parity (audio fixtures before/after), transcript engine
  (timestamps both ways, speakers, intel conditions on/off, refusal).
  CLI smoke via the engine. Full suite.

## Notes / open questions
- Decide and document `ImportResult` semantics for transcripts
  (windows_total/empty = 0; duration from cues).
