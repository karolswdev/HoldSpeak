# Phase 57 — Agent Brief (read this first)

You are picking up **Phase 57 — Transcript Import ("bring your archive",
part 2)** for HoldSpeak. Self-contained: mission, verified code seams, rules,
per-story success. If this brief disagrees with the live status docs or the
codebase, the **codebase wins** — re-verify before trusting any line number.

---

## 0. Mission

Phase 55 made recordings importable — but the user said it plainly: *"I often
have transcripts, rarely do I have recordings."* Most meeting tools (Teams,
Zoom, Meet) export a transcript file, not audio. Phase 57 lets a user upload
a **transcript** (`.vtt`, `.srt`, `.txt`) and get the same real meeting the
audio path produces — segments, timestamps, speakers, deferred intel,
search/facets/aftercare — **without removing or degrading the recording
upload** (explicit user constraint).

The transcript path is the *cheaper* sibling: no Whisper, no ffmpeg, no
windowing. Everything downstream of segments already works; the new work is
parsing + plumbing + honest UI copy.

One genuine upgrade over the audio path: labeled transcripts carry **real
multi-speaker names** (VTT `<v Name>` voice tags; `Name: line` prefixes),
where audio import v1 is single-label. Speaker facets get genuinely useful.

---

## 1. The one thing you must not get wrong

**An imported transcript is a real meeting — and never a lie about timing or
speakers.**

- **One pipeline, not three.** The transcript path reuses the audio path's
  persistence tail (`MeetingState` → `save_meeting` → the live-mirrored
  intel-enqueue conditions) — factor it, don't fork it. The audio path stays
  byte-identical (its tests must pass unmodified).
- **Honest timestamps.** VTT/SRT cues carry real start/end times — use them.
  Plain `.txt` has none — synthesize evenly-spaced times for ordering, and
  say so (the aftercare "jump to the moment" provenance is only as real as
  the source; never fake precision the file doesn't have).
- **Honest speakers.** Use the labels the file carries (VTT voice tags,
  `Name:` prefixes). No labels → the user-provided single label, like audio.
  Never invent names.
- **Local-only.** The file is parsed locally and not retained after import
  (the meeting record is the artifact, same as audio).

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate**: fresh `.tmp/CONTRACT.md` (7 boxes) per commit; a
  done-flip ships its `evidence-story-{n}.md` in the same commit; one
  done-flip per commit; phase exit ships `final-summary.md` in-commit.
- **No `Co-Authored-By`. No `--no-verify`.**
- **Operating cadence**: every shipping commit updates the story header,
  `current-phase-status.md`, the project `README.md`, and any canon doc.
- **One PR per phase**, branch `phase-57-transcript-import`, merged on green.
- **Tests**: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **Web bundle gitignored**: edit `web/src`, `cd web && npm run build`,
  commit source only; JS-rendered DOM styles are `is:global`
  (`docs/internal/ARCHITECTURE_WEB_FRONTEND.md`); `history.astro`/
  `history-app.js` are uncarved — lean, cohesive additions only.
- **Docs**: product-tense, Phase-51 vocab guard, no em/en dashes in new
  text, humanizer pass.
- **Real-metal closeout** (standing posture): a real exported-style VTT
  through the real API → real intel on the `.43` endpoint (sandboxed Bash
  can't reach LAN — use `dangerouslyDisableSandbox`).

---

## 3. The ground truth (seams verified at scaffold, 2026-06-11)

**The engine** (`holdspeak/meeting_import.py`):
- `import_meeting(...)` is two halves. Transcription half: decode → resample
  → ~30 s windows → `TranscriptSegment`s. Persistence tail (`:243-282`):
  `MeetingState(id, started_at, ended_at, title, tags, segments)` → the
  live-mirrored intel posture (`config.meeting.intel_enabled` AND
  `intel_deferred_enabled` → `intel_status="queued"` else `"disabled"`) →
  `save_meeting` → `enqueue_intel_job(transcript_hash=state.transcript_hash())`
  → `ImportResult`. **Factor this tail into a helper both paths call.**
- `validate_format(filename)` (`:118`) is the cheap pre-flight the route and
  CLI both call — teach it the transcript suffixes (and keep its honest
  ffmpeg message for audio).
- `ImportResult` carries `windows_total`/`windows_empty` — transcript imports
  have no windows; keep the dataclass honest (0/0 or segment counts — decide
  and document in evidence).

**The route** (`holdspeak/web/routes/meeting_import.py`):
- `POST /api/meetings/import` (multipart; `python-multipart` already a dep):
  `validate_format` up front → placeholder row `intel_status="importing"` →
  background thread → engine → success replaces status via the engine's own
  save; failure → `intel_status="import_failed"` + actionable detail. The
  Whisper transcriber is built lazily inside the worker via the
  monkeypatchable `_transcriber_factory`. **Transcripts must NOT build a
  transcriber** — branch before the factory; keep the same thread + status
  lifecycle so the UI needs nothing new.

**The UI** (`web/src/pages/history.astro` ~`:96-130` + `history-app.js`):
- The "Import a recording" panel: drop zone with
  `accept=".wav,.mp3,...,audio/*"`, metadata fields, honest notes, importing
  pill via the normal list payload poll. Extend the accept list + copy
  ("recording or transcript"), update the honest notes per source kind.

**CLI** (`holdspeak/commands/import_recording.py`): `holdspeak import <file>`
calls `validate_format` + the engine with a progress printer. Branch by
suffix; transcripts need no transcriber and finish near-instantly.

**Parsers — greenfield.** No VTT/SRT parsing exists anywhere in the tree
(verified by grep). New module `holdspeak/transcript_parse.py`:
- **VTT**: `WEBVTT` header; cues `HH:MM:SS.mmm --> HH:MM:SS.mmm` (hours
  optional); `<v Name>text</v>` voice tags (closing tag optional); strip
  other inline tags (`<c>`, `<i>`, timestamps-in-cue); ignore NOTE/STYLE/
  REGION blocks; cue text may span multiple lines.
- **SRT**: numbered cues, `HH:MM:SS,mmm --> HH:MM:SS,mmm` (comma decimal);
  `Name: text` first-line prefixes are common — reuse the TXT speaker rule.
- **TXT**: `Name: text` prefixes (require a short, plausible name — don't
  split a URL or a clock time); raw lines otherwise; timestamps synthetic
  (even spacing; document the rule).
- Speaker continuity: a cue with no label inherits the previous cue's
  speaker in VTT (per spec, a new `<v>` switches; bare cues continue).

**Tests to mirror**: `tests/unit/test_meeting_import.py` (engine, fake
transcriber), `tests/integration/test_web_meeting_import.py` (route
lifecycle). `reset_database()` between tests; the engine takes a `db`
handle.

---

## 4. Per-story definition of success

- **HS-57-01 — The transcript parsers.** `holdspeak/transcript_parse.py`:
  `parse_transcript(text, filename, *, fallback_speaker) -> ParsedTranscript`
  (cues with text/speaker/start/end + `has_real_timestamps: bool` +
  `speakers_found: list[str]`). VTT (voice tags, hour-optional times,
  NOTE/STYLE skip, tag stripping), SRT (comma times, numeric indices,
  `Name:` prefixes), TXT (`Name:` prefixes with a conservative name rule,
  synthetic timing). Pure, no I/O, no db. Thorough unit tests incl.
  malformed inputs (garbage → `TranscriptParseError` with an actionable
  message, never a silent empty meeting).
- **HS-57-02 — The engine path.** The persistence tail factored out
  (audio path byte-identical, its tests unmodified);
  `import_transcript(path, *, db, config, ...) -> ImportResult`;
  `validate_format` learns `.vtt/.srt/.txt`; the CLI branches by suffix.
  Tests: parity of the intel-enqueue conditions, real-vs-synthetic
  timestamp honesty on the saved segments, multi-speaker labels landing in
  the db (and FTS/speaker facets seeing them), empty-transcript refusal.
- **HS-57-03 — API + UI.** The route branches by suffix (no transcriber
  built for transcripts; same placeholder/thread/status lifecycle; failures
  honest). The /history panel becomes "Import a recording or transcript":
  accept list + drop copy + per-kind honest notes (transcripts: timestamps
  real only for VTT/SRT; speaker names read from the file when labeled).
  Route tests (happy + failure + the no-transcriber-built assertion) +
  page-content locks; `npm run build` clean; screenshots committed.
- **HS-57-04 — Docs.** The Meeting Mode Guide's import section gains the
  transcript story (formats, the timestamp honesty rule, the speaker-label
  upgrade, file-not-retained, intel parity). Vocab guard green, no dashes
  in new text, humanizer pass.
- **HS-57-05 — Closeout.** Dogfood: a realistic multi-speaker VTT through
  the real API → meeting at /history with real speaker labels + real cue
  timestamps → real intel on `.43` → facets filter by a transcript-carried
  speaker. The audio path re-proven untouched (one WAV import in the same
  run). Full suite; `final-summary.md`; BACKLOG row flipped; README
  CLOSED; PR merged on green.

---

## 5. Gotchas that will bite you

- **VTT in the wild is messy**: optional hours (`MM:SS.mmm`), BOM at file
  start, `\r\n` endings, cue-identifier lines above timings, voice tags
  without closing tags, inline `<c.classname>` styling. Parse defensively;
  test with a real Teams/Zoom-shaped fixture, not just the spec's
  pretty-printed examples.
- **Don't over-trigger the `Name:` rule in TXT/SRT** — "https://x.test",
  "12:30: lunch", or a sentence with a colon must not become speakers.
  Require a short name-shaped prefix (e.g. ≤4 words, letters/spaces/'.-,
  no digits-only) and document it.
- **`transcript_hash()` feeds the intel queue** — enqueue AFTER the final
  segments are on the state, exactly like the tail does today.
- **`ended_at`/duration**: real cues → last cue's end; synthetic → the
  synthetic total. `started_at` honest default stays file-mtime.
- **The route's `started_at_ms` browser hint** applies to transcripts too.
- **Keep `ImportResult` truthful** for transcripts (no fake window counts).
- **The UI poll keys off `intel_status`** — reuse `importing` /
  `import_failed` exactly; invent nothing.
- **`.txt` is a broad suffix** — the engine must refuse a `.txt` that
  parses to zero cues with an actionable message, not import an empty
  meeting.

---

## 6. Where to start

`HS-57-01` (the parsers) — pure functions, fast tests, zero risk to the
existing path. Then the engine split (02), the route/UI (03), docs (04),
closeout (05). Sequence: 01 → 02 → 03 → 04 → 05. Keep the audio path
byte-identical, keep the timestamp/speaker story honest, and prove the
whole loop on a real VTT + real intel at closeout. This phase finishes
"bring your archive."
