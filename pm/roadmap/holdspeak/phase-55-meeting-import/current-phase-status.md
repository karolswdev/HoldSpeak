# Phase 55 — Meeting Import ("bring your archive") + faceted history search

**Status:** in-progress (4/6). Opened 2026-06-11 on user direction (the agreed post-53
sequence **54 → I → J → K**), right after Phase 54 closed + merged (PR #41).
From the [project backlog](../BACKLOG.md): candidate **I** (meeting import +
faceted history search).

**Last updated:** 2026-06-11 (**HS-55-04 done: faceted history search.**
`GET /api/meetings` gains `date_from`/`date_to` (bare end date inclusive),
`speaker`, `tag`, `has_open_actions` — all filtering **in SQL over the whole
archive** and composing with `search` (FTS ids flow through the same faceted
query); `GET /api/meetings/facets` feeds the new `/history` filter row (dates,
speaker/tag selects, an open-actions toggle, Clear-when-active), with one
`meetingsQuery()` builder driving every meetings fetch so filters survive
search, refresh, and the import poll. A real fix fell out: the old search
branch returned nested `intel_status` objects that broke the status pill on
every search result — both branches now share the flat summary shape. 5 facet
API tests (incl. the whole-archive `limit=1` proof + the no-params regression)
+ a facet-row page lock; live Playwright pass (3 → 2 cards on speaker=Alice,
zero page errors, screenshot reviewed). Full suite **2568 passed, 17 skipped**
(+6). **HS-55-03 (prior): the /history import UI.** An
"Import a recording" opener in the meetings toolbar + an accent-edged panel
(dashed drag/drop + browse target, Title/Speaker/Tags, the honest notes
verbatim: ffmpeg for compressed, one speaker label, audio not kept, local
only). Submit posts multipart with `started_at_ms` from `File.lastModified`;
the card renders a reduced-motion-safe pulsing "Importing…" pill with the
window-progress detail, followed by **in-place resolution** via a quiet 2 s
poll that runs only while an import is in flight (re-armed after page
refresh, self-stopping). Failures render a danger pill + detail with a
Remove affordance placed outside the card button (valid HTML) →
holdspeakConfirm → the new DELETE route. Proven live by a real browser
upload (`dogfood_story03.py`: RESULT PASS, zero page errors; 3 screenshots
reviewed). 4 page-content locks; `npm run build` clean; full suite **2562
passed, 17 skipped** (+4). **HS-55-02 (prior): the import API + CLI.**
`POST /api/meetings/import` (multipart; `python-multipart` added — it was
absent) refuses bad formats up front via the engine's new `validate_format()`,
saves a visible `intel_status="importing"` placeholder row immediately,
returns **202** with the meeting id, and runs the engine on a daemon thread
with the Whisper transcriber built lazily inside the worker. Progress rides
the meeting row (`intel_status_detail`, the intel queue's load→mutate→save
pattern) so `/history` polling needs nothing new; success resolves to the
live-mirrored intel posture; failure marks `import_failed` with the
actionable detail. Also shipped the missing `DELETE /api/meetings/{id}` (the
repo's `delete_meeting` had no HTTP route) and `holdspeak import <file>`
(synchronous, per-window progress, refusal smoke-tested for real). 4 route
integration tests incl. responsiveness-under-import; full suite **2558
passed, 17 skipped** (+4). Found for HS-55-03: the detail endpoint nests
`intel_status` as `{state, detail}` (the list is flat).
**HS-55-01 (prior): the import engine.**
`holdspeak/meeting_import.py` — PCM WAV via the stdlib `wave` module (scipy is
dev-only), compressed formats via ffmpeg-on-PATH with an honest refusal +
install hint when absent, downmix/resample to the 16 kHz mono transcriber
contract, ~30 s windowed transcription stamping real segment start/end times
(all-empty transcripts refuse the import — no mystery rows), a normal
`MeetingState` (`started_at` from file mtime) through the normal
`save_meeting`, and the live path's exact intel-enqueue conditions mirrored.
8 unit tests + a downstream-parity integration test (lists / full-text
searches / exports like a live meeting). Full suite **2554 passed, 17
skipped** (+9). Earlier: scaffolded — AGENT-BRIEF + six stories, seams mapped
against the live tree.)

## The thesis — why this phase

Meeting intelligence (14 plugins, artifacts, aftercare) only works on meetings
captured live; most users' highest-value meetings already exist as recordings.
Grounded in the live tree:

- **The file→meeting recipe is already proven** by the spoken-meeting e2e
  harness (`tests/e2e/test_spoken_meeting_e2e.py:122-223`): WAV from disk →
  `Transcriber.transcribe` (numpy float32 mono @ 16 kHz, `transcribe.py:342`)
  → `TranscriptSegment`s → `save_meeting(MeetingState)` — and intel, history,
  aftercare, and exports downstream all just work. Phase 55 productizes it.
- **Nothing imports today**: no POST-create meeting route, no multipart upload
  handler anywhere, no CLI for it.
- **Search has no facets**: `GET /api/meetings` supports full-text `search`
  only (`web/routes/meetings.py:273`); any filtering is client-side on one
  page of results. Import makes archives big enough to need real filters.

## Goal

Import an existing recording into the full meeting-intelligence pipeline (web
upload + CLI), producing a real meeting — segments with timestamps, one honest
speaker label, deferred intel, `/history` parity — and give `/history`
server-side faceted search (date range, speaker, tag, action status). Local
only; audio not retained; honest about formats (ffmpeg for compressed) and
about the single speaker label (no diarization in v1).

## Scope

- **In:** the import engine (HS-55-01); the import API + background job + CLI
  (HS-55-02); the `/history` import UI (HS-55-03); server-side facets + the
  filter row (HS-55-04); docs (HS-55-05); closeout with a real-audio dogfood
  (HS-55-06).
- **Out:** single-file speaker diarization (no dependency for it; v1 is one
  user-provided label, stated honestly); retaining/serving imported audio
  (the transcript is the artifact, like live meetings); video files; batch
  import queues (one file per request/invocation); any change to live
  capture, MIR routing, or plugin behavior; carving `history.astro` (additions
  stay lean; the Phase-54 treatment of that page is its own future phase).

## Exit criteria (evidence required)

- A file-in → meeting-out engine: WAV native + ffmpeg-assisted compressed
  formats (honest refusal without ffmpeg), resampled/downmixed correctly,
  windowed transcription with real segment timestamps, `save_meeting` + the
  same intel-enqueue conditions as live; unit-tested with an injected
  transcriber. (HS-55-01)
- `POST /api/meetings/import` (multipart) creating a visible importing-state
  meeting, transcribing off-thread, finishing into intel enqueue, failing
  honestly; plus `holdspeak import <file>`; tested. (HS-55-02)
- An inviting, Signal-styled import affordance on `/history` with progress
  and in-place resolution; screenshots; `npm run build` clean. (HS-55-03)
- Server-side `date_from`/`date_to`/`speaker`/`tag`/`has_open_actions`
  filters composing with `search`, + the `/history` filter row; tested per
  facet and combined. (HS-55-04)
- Product-tense docs passing the Phase-51 guard, `humanizer` run, linked in
  the docs index. (HS-55-05)
- A real-audio dogfood (`say` → WAV → import API → real Whisper → `/history`
  with segments → intel enqueued, processed on `.43` when reachable → facets
  filter it); full suite green; `final-summary.md`; phase CLOSED; BACKLOG
  candidate I flipped; PR merged on green. (HS-55-06)

## Invariants

- **An imported meeting is a real meeting** — one pipeline, no second-class
  records, indistinguishable downstream.
- **Honest surfaces:** one speaker label (no fake diarization), ffmpeg stated
  as the compressed-format dependency, audio not retained.
- **Local-only.** Nothing egresses; intel follows the existing egress posture.
- **The web server stays responsive** during an import (background thread,
  per-window transcription timeouts).
- **Frontend follows the Phase-54 architecture doc**; `/history` additions
  stay lean (the page is an uncarved monolith).

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-55-01 | The import engine (file → meeting) | done | none |
| HS-55-02 | Import API + background job + CLI | done | HS-55-01 |
| HS-55-03 | The /history import UI | done | HS-55-02 |
| HS-55-04 | Faceted history search (API + filter row) | done | none |
| HS-55-05 | Docs: import + facets | backlog | HS-55-03, HS-55-04 |
| HS-55-06 | Closeout: real-audio dogfood + final-summary + PR | backlog | HS-55-01..05 |

## Where we are

**HS-55-01 → HS-55-04 shipped 2026-06-11.** Both halves of the thesis are
real: the archive imports (engine → API/CLI → live browser flow) and the
archive filters (server-side facets + the row, with the search-pill fix
along the way).

Next is **HS-55-05 — docs**: the import flow + facets documented
product-tense (the three honest truths verbatim), passing the doc guards,
linked from the docs index.

## Open decisions (defaults chosen; flag to change)

- **Windowed transcription (~30 s)** is the segment/timestamp story — honest
  window-level timing, not fabricated word-level timing.
- **`started_at` defaults to the file's mtime** (override via title form/CLI
  flags is out; a simple `--started-at`/form field may ride along if cheap) —
  so an old recording sorts where it happened, not where it was imported.
- **Import status rides the meeting row** (e.g. `intel_status`-style fields or
  a dedicated import status surfaced through the existing list payload) rather
  than a parallel job API — pick whichever keeps `/history` polling trivial,
  document the choice in evidence.
- **Facets**: date range, speaker, tag, open-actions. Artifact-type faceting
  is out (v1) unless it falls out for free.
