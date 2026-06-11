# Phase 57 — Transcript Import ("bring your archive", part 2)

**Status:** in-progress (3/5). Opened 2026-06-11 on user direction, straight
after Phase 56 closed (PR #43): *"can we also do it by simply uploading a
transcript too? I often have transcripts, rarely do I have recordings (but I
don't want you to remove the recording upload affordance, of course!)"*.
Net-new from that conversation (BACKLOG candidate **P**), slotted ahead of
**K** because it is small and completes the Phase-55 "bring your archive"
thesis.

**Last updated:** 2026-06-11 (**HS-57-03 done: API + /history UI.** The
route's worker branches by suffix — a transcript upload rides the exact
recording lifecycle ("Parsing transcript…" placeholder → engine save /
`import_failed`) and **never constructs a transcriber** (a poisoned
factory locks it, in tests AND the live dogfood); per-kind speaker
defaults resolve in the worker. The panel reads "Import a recording or
transcript" with per-kind honest notes (speaker names read from the file;
timestamps real for vtt/srt, approximate for plain text; source not
retained). **Two real bugs found and fixed**: untitled imports fell back
to the temp file's stem (latent Phase-55, audio path included — the route
now resolves the title from the uploaded name) and the binary-garbage
gate counted U+FFFD as printable (a wall of replacement chars imported as
a "transcript"). Live dogfood 3/3: a real browser upload of a
multi-speaker VTT became a real meeting (file speakers, real cue starts,
queued intel), zero page errors, three reviewed screenshots. +5 tests;
full suite **2641 passed, 17 skipped**.
**HS-57-02 (prior): the engine path + CLI.** The
Phase-55 persistence tail factored verbatim into `_persist_import` (the
audio path byte-identical — its test file untouched and green);
`import_transcript` reads, parses, and persists honest segments through
that one tail (real cue timestamps for VTT/SRT, synthetic ordering for
TXT, file-carried speakers with the `Transcript` fallback, mtime
`started_at`, one error type for callers); `ImportResult` stays truthful
(0 windows, a new additive `speakers_found`); `validate_format` learns the
trio without touching audio messages; `holdspeak import notes.vtt`
branches before any model load — the no-transcriber guarantee is
monkeypatch-asserted. 12 tests; zero-cue refusal persists nothing; FTS
reachability asserted. Full suite **2636 passed, 17 skipped** (+12).
**HS-57-01 (prior): the transcript parsers.**
`holdspeak/transcript_parse.py`, pure and greenfield: VTT (BOM/CRLF,
hour-optional timings, voice tags with optional close + the voice
continuity model, NOTE/STYLE skip, tag stripping, suffix-mislabel rescue
when content starts `WEBVTT`), SRT (comma times, `Name:` prefixes), TXT
(the conservative ≤3-word name rule with a structure-label blocklist;
synthetic 6-s spacing). The honesty flags ship: `has_real_timestamps` only
for cue-timed formats, `speakers_found` only file-carried labels. Zero-cue
input refused actionably — an import can never silently produce an empty
meeting. 22 tests incl. a Teams/Zoom-shaped fixture and a purity lock;
full suite **2624 passed, 17 skipped** (+22). Earlier: scaffolded — the
Phase-55 tail is cleanly factorable; no VTT/SRT parsing existed anywhere.)

## The thesis — why this phase

Most meeting tools export a transcript, not audio; the user has transcripts.
Everything downstream of `TranscriptSegment`s (persistence, deferred intel,
search, facets, aftercare, actuators) is already format-agnostic — the
transcript path is the cheaper sibling of Phase 55's audio import: a parser
plus plumbing, no Whisper, no ffmpeg. And it carries one genuine upgrade:
real multi-speaker labels from VTT voice tags / `Name:` prefixes, where
audio import is single-label.

## Goal

Upload a `.vtt`/`.srt`/`.txt` transcript (web or CLI) and get a real meeting
— real cue timestamps and speaker names when the file carries them, honest
synthetic ordering when it does not — through the exact same lifecycle,
intel, and history surfaces as a recording import. The recording upload
stays, untouched.

## Scope

- **In:** the parser module (HS-57-01); the engine path + shared persistence
  tail + `validate_format` + CLI (HS-57-02); the route branch + the
  /history panel extension (HS-57-03); docs (HS-57-04); closeout with a
  real-VTT + real-intel dogfood (HS-57-05).
- **Out:** removing/degrading the recording path (explicit user constraint);
  diarization; DOCX/PDF/HTML transcript formats (the v1 trio is
  VTT/SRT/TXT); editing transcripts post-import; word-level timing.

## Exit criteria (evidence required)

- Parsers: VTT (voice tags, hour-optional times, NOTE/STYLE, tag-stripping),
  SRT (comma times, `Name:` prefixes), TXT (conservative `Name:` rule,
  synthetic timing); malformed input refused actionably; pure + unit-tested.
  (HS-57-01)
- One persistence tail, two callers — the audio path byte-identical with
  its tests unmodified; `import_transcript` mirrors the intel-enqueue
  conditions; real-vs-synthetic timestamps land honestly on saved segments;
  multi-speaker labels reach the db and the speaker facet; CLI imports a
  transcript by suffix. (HS-57-02)
- The route accepts transcripts without building a transcriber (asserted),
  same importing/import_failed lifecycle; the panel reads "recording or
  transcript" with per-kind honest notes; screenshots; build clean.
  (HS-57-03)
- Product-tense docs passing the guards; humanizer run; no dashes in new
  text. (HS-57-04)
- Live dogfood: a realistic multi-speaker VTT through the real API → real
  speaker labels + cue timestamps at /history → real intel on `.43` →
  speaker facet filters by a transcript-carried name; one WAV import in the
  same run proves the audio path untouched. Full suite green;
  `final-summary.md`; BACKLOG P flipped; PR merged on green. (HS-57-05)

## Invariants

- **An imported transcript is a real meeting** — one pipeline, no
  second-class records.
- **Never fake precision**: real timestamps only from files that carry
  them; never invent speaker names.
- **The recording path is byte-identical** (its tests pass unmodified).
- **Local-only; the uploaded file is not retained after import.**

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-57-01 | The transcript parsers | done | none |
| HS-57-02 | The engine path + CLI | done | HS-57-01 |
| HS-57-03 | API + /history UI | done | HS-57-02 |
| HS-57-04 | Docs: transcript import | backlog | HS-57-03 |
| HS-57-05 | Closeout: real-VTT dogfood + final-summary + PR | backlog | HS-57-01..04 |

## Where we are

**HS-57-01 → HS-57-03 shipped 2026-06-11.** The feature is end-to-end
usable: drop a VTT on /history and it becomes a real meeting with the
file's own speakers and timestamps, no model load. Next is **HS-57-04 —
docs**: the Meeting Mode Guide's import section learns the transcript
story (formats, the timestamp/speaker honesty rules, file-not-retained,
intel parity).
