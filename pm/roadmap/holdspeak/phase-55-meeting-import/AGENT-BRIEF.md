# Phase 55 — Agent Brief (read this first)

You are picking up **Phase 55 — Meeting Import ("bring your archive") + faceted
history search** for HoldSpeak. This brief is self-contained: the mission, the
exact code seams (mapped against the live tree at scaffold time), the rules of
the road, and a per-story definition of success. Read it, then read
[`current-phase-status.md`](./current-phase-status.md) and the story you're
working. If this brief disagrees with the live status docs or the codebase, the
**codebase wins** — re-verify before trusting any line or number below.

---

## 0. Mission

HoldSpeak's meeting intelligence — 14 LLM-backed plugins, artifacts, actions,
aftercare — only works on meetings captured **live**. There is no way to feed
it a recording that already exists (a Zoom export, a Teams download, a voice
memo). That makes the product's strongest feature forward-only, when most
users' highest-value meetings are sitting in their archive.

Two deliverables under one thesis ("the archive becomes useful"):

1. **Import a recording.** A user picks an audio file (WAV natively; common
   compressed formats via ffmpeg when present), HoldSpeak transcribes it
   through the same Whisper backends, creates a real meeting (segments,
   timestamps, a speaker label), enqueues the same deferred intel, and it
   appears at `/history` like any captured meeting — artifacts, aftercare,
   exports and all. Web upload + CLI.
2. **Faceted history search.** `/history` today has one full-text box;
   importing makes archives big enough to need real filters. Add server-side
   facets (date range, speaker, tag, action status) + a Signal-styled filter
   row.

The crux is already proven in miniature: the spoken-meeting e2e harness
(`tests/e2e/test_spoken_meeting_e2e.py:122-223`) reads a WAV from disk,
transcribes it, builds `TranscriptSegment`s, saves a `MeetingState`, and the
whole intel pipeline downstream just works. Phase 55 productizes that seam.

---

## 1. The one thing you must not get wrong

**An imported meeting is a real meeting — never a second-class record, and
never a lie about what import can do.**

- **One pipeline, not two.** Import produces a normal `MeetingState` persisted
  by the normal `save_meeting`, intel via the normal `enqueue_intel_job` →
  `process_next_intel_job`. No parallel storage, no special-cased rendering at
  `/history`. If something downstream (aftercare, exports, search) treats an
  imported meeting differently, that's a bug.
- **Honest about speakers.** There is no single-file diarization in the deps
  (live meetings get labels from the mic/system *streams*, not from magic).
  An import carries **one user-provided speaker label** (defaulting to
  something honest like "Recording"). Do not fake multi-speaker labels; do
  not block the feature on diarization. Say so in the UI and the docs.
- **Honest about formats.** WAV decodes natively. mp3/m4a/etc. require
  `ffmpeg` on PATH — detect it, use it when present, and refuse with a clear,
  actionable message when absent (the doctor-style honesty posture). Never
  ship a half-decoded transcript.
- **Local-only, like everything else.** The file is read, transcribed
  locally, and the audio is **not retained** after import (the transcript is
  the artifact, matching live meetings, which keep no audio). State this.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template
  in `pm/roadmap/PMO-CONTRACT.md`, **7** checkboxes). A story flipping to
  `done` ships its `evidence-story-{n}.md` in the same commit; **one**
  done-flip per commit. The phase-exit story needs evidence **and**
  `final-summary.md` in the same commit.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates the story header, this
  phase's `current-phase-status.md`, the project `README.md`, and any canon
  doc touched.
- **One PR per phase, merged on green CI.** Branch `phase-55-meeting-import`;
  at close push + PR to `main` + merge.
- **Tests actually run.** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- **The web bundle is gitignored.** Edit `web/src`, `cd web && npm run build`,
  commit source only. **Frontend changes follow
  `docs/internal/ARCHITECTURE_WEB_FRONTEND.md`** (Phase 54): styles for
  JS-rendered DOM are `is:global`; check the density budgets before growing
  `history.astro`/`history-app.js` (they are NOT carved yet — keep additions
  lean and cohesive; the guard does not cover them, your judgement does).
- **High UI/UX bar** (`ui-ux-pro-max`): the import affordance is an inviting,
  Signal-styled surface with real progress feedback, not a bare file input.
  Screenshot evidence committed.
- **User-facing docs obey the Phase-51 guard** (product-tense, no roadmap
  vocabulary) and get a `humanizer` pass.
- **Real-metal proof posture** (Phase-53 lesson): the closeout dogfood runs a
  **real audio file through real Whisper**; intel-on-`.43` is the bonus pass
  when the LAN endpoint is reachable (sandboxed Bash can't reach it — use the
  documented escape hatch).

---

## 3. The ground truth (code seams, mapped + verified at scaffold)

Re-verify before trusting; line numbers drift.

**The proven file→meeting recipe** (`tests/e2e/test_spoken_meeting_e2e.py`):
- `:149` reads a WAV via `scipy.io.wavfile.read` → int16 → `float32/32768.0`;
- `Transcriber.transcribe(audio)` (`holdspeak/transcribe.py:342`) takes
  **numpy float32 mono @ 16 kHz** and returns text (timeout-guarded,
  HS-25-05); no file-path overload exists;
- builds `TranscriptSegment(text, speaker, start_time, end_time)` per chunk;
- `:213-223` persists `MeetingState(id, started_at, segments, title)` via
  `db.meetings.save_meeting(state)` — and everything downstream works.

**Persistence** (`holdspeak/db/`):
- `meetings` table (`db/core.py:144`): id, started_at, ended_at, title,
  duration_seconds, intel_status(+detail/requested/completed), mic_label,
  remote_label. `segments` (`:169`): meeting_id, text, speaker, speaker_id,
  start_time, end_time (REAL seconds). FTS5 over segment text + speaker.
- `MeetingRepository.save_meeting(state)` (`db/meetings.py:66`) upserts
  meeting + segments + tags in one transaction. `MeetingState` lives at
  `holdspeak/meeting_session.py:152`.

**Audio:** `holdspeak/audio.py` has `_linear_resample_mono()` for sample-rate
conversion. scipy reads WAV. ffmpeg is not a dependency — shell out to it for
compressed formats **iff** present on PATH (decode to 16 kHz mono WAV/PCM).

**Intel:** after save, `db.intel.enqueue_intel_job(meeting_id,
transcript_hash, reason)` (`db/intel.py:22`); the queue
(`holdspeak/intel_queue.py:99`, `process_next_intel_job`) and the web/CLI
drains already exist (`holdspeak/commands/intel.py`). The live path enqueues
at `meeting_session.py:1474` — mirror its conditions (intel enabled +
deferred + non-empty transcript).

**Web routes:** `holdspeak/web/routes/meetings.py` — `GET /api/meetings`
(`:273`; limit/offset/`search` → `db.meetings.search_transcripts`, full-text
only, **no server-side facets**). **No POST-create route and no multipart
upload handler anywhere in the codebase** — `POST /api/meetings/import` is
greenfield (FastAPI `UploadFile`; `python-multipart` may need adding to deps —
check).

**History surface:** `web/src/pages/history.astro` + `history-app.js`
(Alpine-style factory). Search is a text box wired to the `search` param;
some filtering exists client-side only. These files are large and uncarved —
land the lightest cohesive addition, not a redesign.

**Speakers:** live labels come from the mic/system streams (`mic_label`,
`remote_label`); `SpeakerDiarizer` (resemblyzer) identifies speakers on the
**system stream** in real time. Nothing diarizes a single mixed file. Import
v1: one label.

**CLI:** `holdspeak/main.py` dispatches subcommands; handlers live in
`holdspeak/commands/`. Pattern to follow for `holdspeak import`.

---

## 4. Per-story definition of success

- **HS-55-01 — The import engine.** `holdspeak/meeting_import.py`: decode
  (WAV via scipy natively; mp3/m4a/ogg/flac via ffmpeg-on-PATH, refused
  honestly when absent) → mono float32 @ 16 kHz (resample as needed) →
  **windowed transcription** (~30 s windows so segments carry real
  start/end times) → `MeetingState` (user title/tags/speaker label; duration
  from the audio; `started_at` from file mtime or now) → `save_meeting` →
  intel enqueued under the same conditions as live. Progress callback for
  callers (CLI/API). Unit-tested with an injected fake transcriber +
  generated WAVs (format detection, resampling, windowing/timestamps, the
  ffmpeg-absent refusal, intel-enqueue conditions). No UI.
- **HS-55-02 — Import API + CLI.** `POST /api/meetings/import` (multipart:
  file + optional title/speaker/tags): creates the meeting row up front in a
  visible "importing" state, transcribes on a background thread (the web
  server must stay responsive), updates the row as segments land, finishes
  by enqueueing intel; failures mark the meeting honestly (clear detail,
  removable). A status surface the UI can poll (extend the meeting row /
  list payload rather than inventing a parallel job API if it fits). CLI:
  `holdspeak import <file> [--title --speaker --tag]` — synchronous with
  progress output, same engine. Tested (route happy path + failure + status
  progression; CLI via the engine).
- **HS-55-03 — The /history import UI.** An inviting "Import a recording"
  affordance on `/history` (Signal-styled panel: file picker, title,
  speaker label, the honest format/speaker notes), upload with progress,
  the meeting appearing in the list in its importing state and resolving in
  place. Focus-safe, `is:global` for JS-rendered DOM, screenshots committed,
  `npm run build` clean.
- **HS-55-04 — Faceted history search.** Server-side filters on
  `GET /api/meetings`: `date_from`/`date_to`, `speaker`, `tag`,
  `has_open_actions` (composable with the existing `search`); a `/history`
  filter row (date range, speaker select fed from real data, tag select,
  open-actions toggle) that reads as part of the Signal surface. Tested
  server-side per facet + combined; page-content test for the row.
- **HS-55-05 — Docs.** The import flow + facets documented product-tense
  (extend `docs/MEETING_MODE_GUIDE.md` and/or a focused guide linked from
  the docs index): what import does, formats (the ffmpeg dependency stated
  plainly), the one-speaker-label truth, audio-not-retained, intel parity.
  Passes the Phase-51 guard; `humanizer` run.
- **HS-55-06 — Closeout.** Dogfood: generate a real multi-utterance WAV
  (`say`, the spoken-e2e pattern) → import via the API → real Whisper
  transcript → meeting at `/history` with segments + timestamps → intel
  enqueued (and processed against `.43` when reachable) → facets filter it.
  Full suite green; `final-summary.md`; phase CLOSED; BACKLOG candidate I
  flipped; PR merged on green.

---

## 5. Gotchas that will bite you

- **`Transcriber.transcribe` wants 16 kHz mono float32.** Resample and
  downmix *before* transcribing; a 44.1 kHz stereo file fed raw produces
  garbage, not an error.
- **Windowing is the timestamp story.** One `transcribe()` call returns one
  text blob with no timing — transcribe per window and stamp window times on
  the segments. Don't promise word-level timing the backend doesn't give.
- **Long files vs. the web server.** An hour of audio takes minutes of
  Whisper. The route must not block the event loop or time out: meeting row
  first, work on a thread, visible progress. The transcription timeout
  (HS-25-05) applies **per call** — per window, not per file.
- **`python-multipart`** is required for FastAPI `UploadFile`; verify it's a
  dependency before relying on it (pin it in `pyproject.toml` if not).
- **Mirror, don't fork, the intel-enqueue conditions** from
  `meeting_session.py:1474` — intel disabled or empty transcript means no
  job, same as live.
- **`history.astro`/`history-app.js` are uncarved monoliths.** Phase 54's
  guard doesn't cover them; don't let this phase be the one that makes them
  worse. Cohesive, minimal additions; the Phase-54 doc's style rules apply.
- **FTS + facets compose in SQL,** not in Python — filter in the query, not
  by post-filtering a 50-row page (facets must see the whole archive).
- **The spoken-e2e tests are hardware-ish** (`say` exists on macOS only) —
  follow the existing harness's gating pattern for any real-Whisper test.
- **`reset_database()` between tests** (the established pattern) — the
  import engine takes a `db` handle; don't reach for globals.

---

## 6. Where to start

`HS-55-01` (the engine) is first: it's the productized version of a recipe
the e2e harness already proves, and everything else surfaces it. Build it
file-in → meeting-out with an injected transcriber and real unit tests, then
hang the API/CLI (02), the UI (03), and the facets (04) off it. Suggested
sequence: 01 → 02 → 03 → 04 → 05 → 06. Keep imported meetings
indistinguishable downstream, keep the speaker/format/audio-retention story
honest, and prove the whole loop on real audio at closeout. This is the
phase that makes the archive part of the product.
