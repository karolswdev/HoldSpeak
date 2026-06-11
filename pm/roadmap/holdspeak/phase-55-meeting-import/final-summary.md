# Phase 55 — Meeting Import ("bring your archive") + faceted history search: final summary

**Closed:** 2026-06-11 (opened and closed the same day). 6/6 stories shipped.
From [backlog](../BACKLOG.md) candidate **I**, the second step of the agreed
sequence **54 → I → J → K**.

## What shipped

Meeting intelligence was live-capture-only; the highest-value meetings most
users have are recordings sitting in their archive. Now:

- **The import engine** (`holdspeak/meeting_import.py`): WAV decodes natively
  (stdlib `wave` — scipy is dev-only), compressed formats decode via
  ffmpeg-on-PATH with an honest, actionable refusal when absent; audio is
  downmixed/resampled to the transcriber contract; ~30 s windowed
  transcription stamps real segment start/end times; an all-empty transcript
  refuses the import rather than saving a mystery row; `started_at` comes
  from the file's mtime so old recordings sort where they happened; the
  intel-enqueue conditions mirror the live path exactly. The source audio is
  not retained.
- **`POST /api/meetings/import`** (multipart; `python-multipart` added):
  refuses bad formats up front, saves a visible `importing` placeholder row
  immediately, returns 202, transcribes on a daemon thread with the Whisper
  transcriber built lazily in the worker; progress rides the meeting row
  (the intel queue's load→mutate→save pattern); failures mark
  `import_failed` with the actionable detail. Plus the previously **missing**
  `DELETE /api/meetings/{id}` (the repo method had no HTTP route) and
  **`holdspeak import <file>`** (synchronous, per-window progress).
- **The /history import UI**: an "Import a recording" opener + accent-edged
  panel (drag/drop + browse, metadata fields, the honest notes verbatim), a
  pulsing "Importing…" pill with live window progress on the card, in-place
  resolution via a quiet import-only poll, and a Remove affordance on failed
  imports. Proven live with a real browser upload (zero page errors).
- **Faceted history search**: `date_from`/`date_to` (bare end dates
  inclusive), `speaker`, `tag`, `has_open_actions` — filtering in SQL over
  the whole archive, composing with each other and with full-text `search`
  (FTS ids flow through the same faceted query); `GET /api/meetings/facets`
  feeds the `/history` filter row; one `meetingsQuery()` builder keeps
  filters alive across search, refresh, and the import poll.
- **Docs**: "Import an Existing Recording" + "Find Meetings in Your Archive"
  in the Meeting Mode Guide (the three honest truths in plain prose,
  humanizer-checked), docs-index + root-README one-liners.

Honest v1 limits, stated everywhere they matter: one user-chosen speaker
label (no single-file diarization dependency exists, and HoldSpeak does not
guess boundaries it cannot verify); ffmpeg required for compressed formats;
audio not retained; an imported meeting is a real meeting — one pipeline,
indistinguishable downstream (locked by a parity test).

## Proven on real metal (the Phase-53 posture)

The closeout dogfood ran with **no fakes anywhere**: real `say` speech →
the real import route → real MLX Whisper ("small") transcribed both
utterances **verbatim** across their two windows → the deferred intel job
processed for real on the LAN llama.cpp endpoint
(`192.168.1.43:8080`, Qwen3.5-9B-Q6), reaching `ready` with a *correct*
summary of the synthetic meeting → the facets included it (speaker+tag) and
excluded it (wrong speaker). And the first run accidentally proved the
honest-failure path on real metal too: this machine's config pins
`model.backend="faster-whisper"` (not installed), and the row was marked
`import_failed` with the actionable install hint, removable in one click.

## Real finds along the way

1. **`DELETE /api/meetings/{id}` did not exist** — the repo's
   `delete_meeting` had no HTTP route at all (HS-55-02 added it).
2. **Search results had a broken status pill** — the old search branch
   returned full `to_dict()` payloads whose nested `intel_status` object
   broke the card's class binding; unifying both branches on the summary
   shape fixed it (HS-55-04).
3. **The detail endpoint nests `intel_status`** (`{state, detail}`) while
   the list is flat — recorded for future UI work.

## Numbers

23 new tests (8 engine, 1 parity, 4 route, 4+1 page locks, 5 facets);
final suite **2568 passed, 17 skipped**; three committed dogfoods
(`dogfood_story03.py` browser upload, `dogfood_story06.py` real metal) and
five reviewed screenshots.

## Lessons

- **The e2e harness was the spec.** Productizing a recipe a test already
  proved (file → transcribe → MeetingState) made the engine a one-story job.
- **Ride existing rows, don't invent job APIs.** Import status/progress on
  the meeting row meant `/history` needed one poll loop and zero new
  payload shapes.
- **Dogfood failures are claims to verify** (again): the backend crash was a
  machine-config quirk that *proved* the failure path; the fix belonged in
  the dogfood, not the product.

## Follow-ups (not this phase)

- Surface ffmpeg presence in `doctor` (a one-line capability hint).
- `history.astro`/`history-app.js` grew ~+400 cohesive lines this phase and
  remain uncarved — they stay the named candidates for a Phase-54-style
  decomposition.
- Speaker diarization for imports stays out until a real dependency choice
  is made deliberately.
