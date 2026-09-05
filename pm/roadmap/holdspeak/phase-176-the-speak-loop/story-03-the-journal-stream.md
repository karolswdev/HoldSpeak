# HS-176-03 — The journal as a stream

- **Project:** holdspeak
- **Phase:** 176
- **Status:** backlog
- **Depends on:** HS-176-01
- **Unblocks:** HS-176-05
- **Owner:** unassigned

## Problem

The journal exists (journal.py:1-50, DictationJournalRecorder writes
one durable row per pipeline run) and the Journal face exists
(Journal.tsx on the Speak window), but it is not a live stream. The
owner cannot see his utterances arrive in real time, cannot filter by
source (dictation / browser / hotkey), and cannot search by text. The
voice-typing act is invisible as a feed; the arc says "the journal as
a stream."

## Scope

- In:
  - The Journal face (Journal.tsx) rebuilt to the HS-176-01 artboard
    as a live stream: utterances appear in real time as the pipeline
    runs (pushed via the WebSocket bus, not polled).
  - Each utterance row shows: source badge (dictation / browser /
    hotkey), raw text, processed text, latency, corrections applied
    (if any), intent tag from DIR-01 (if matched).
  - Filter tokens for source: one-tap filter by dictation / browser /
    hotkey (the flat-token grammar from UX-CANON.md rule D).
  - Search: a text search over the journal's durable rows (FTS or
    LIKE; the journal table has raw_text and processed_text).
  - Scroll-to-load: the stream shows the most recent N utterances
    with pagination on scroll-up.
- Out:
  - Journal export (CSV, JSON; a future candidate).
  - Journal deletion or editing (the journal is append-only and
    immutable; the owner can clear corrections but not journal rows).
  - Real-time analytics or charts over the journal (the learning
    digest is the aggregation surface).

## Acceptance criteria

- [ ] The Journal face shows utterances as a live stream; a new
      utterance appears within 1 s of the pipeline run completing
      (Article IX.1).
- [ ] Each row shows source, raw text, processed text, latency,
      corrections applied, and intent tag (Article VI.1).
- [ ] Source filter tokens (dictation / browser / hotkey) filter the
      stream; the face matches the HS-176-01 artboard.
- [ ] Search by text returns matching journal rows.
- [ ] Scroll-to-load paginates the stream without loading the full
      history.
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k journal_stream`
  - A pipeline run writes a journal row; the row is readable via the
    journal query API.
  - Source filter returns only matching rows.
  - Search returns matching rows.
- Integration: the rig boots a hub, runs a pipeline, asserts the
  journal row appears in the query API response with all fields.
- Manual: the owner dictates three sentences; the Journal face shows
  them as a live stream; he filters by source; he searches by a word
  from the second sentence.

## Notes / open questions

- The WebSocket bus frame for journal updates: propose a new frame
  type `dictation.journal.entry` carrying the minimal row (id,
  source, raw_text, processed_text, latency, corrections_applied,
  intent_tag). The frame is a read (Article V.1: watching is free).
- The existing Journal.tsx may need a substantial rewrite to support
  the stream + filters + search. The scope is the face, not the
  underlying recorder (which is already durable and functional).
