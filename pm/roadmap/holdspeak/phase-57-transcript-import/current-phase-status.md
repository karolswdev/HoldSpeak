# Phase 57 — Transcript Import ("bring your archive", part 2)

**Status:** scaffolded (0/5). Opened 2026-06-11 on user direction, straight
after Phase 56 closed (PR #43): *"can we also do it by simply uploading a
transcript too? I often have transcripts, rarely do I have recordings (but I
don't want you to remove the recording upload affordance, of course!)"*.
Net-new from that conversation (BACKLOG candidate **P**), slotted ahead of
**K** because it is small and completes the Phase-55 "bring your archive"
thesis.

**Last updated:** 2026-06-11 (scaffolded — seams verified against the live
tree: the Phase-55 engine's persistence tail is cleanly factorable, the
route's lifecycle and the /history panel extend without new concepts, no
VTT/SRT parsing exists anywhere yet (greenfield module), and labeled
transcripts will give the speaker facet real multi-speaker data for the
first time.)

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
| HS-57-01 | The transcript parsers | backlog | none |
| HS-57-02 | The engine path + CLI | backlog | HS-57-01 |
| HS-57-03 | API + /history UI | backlog | HS-57-02 |
| HS-57-04 | Docs: transcript import | backlog | HS-57-03 |
| HS-57-05 | Closeout: real-VTT dogfood + final-summary + PR | backlog | HS-57-01..04 |

## Where we are

Scaffolded. Next is **HS-57-01 — the transcript parsers**: the pure
greenfield module with thorough format tests; nothing existing is touched.
