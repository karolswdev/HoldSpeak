# Phase 176 - The Speak Loop

**Last updated:** 2026-09-05.

## Goal

Dictation becomes a daily tool. The correction is taught once, kept
forever, and applied to the next matching utterance. The journal is a
live stream of everything the owner spoke into the desk. The voice law
is satisfied: MicButton on every text input across the desk, not just
the seven surfaces that have it today. The desk answers the hand:
speak, see it land, judge it, teach it, see the teaching applied. The
learning loop that has never been trained gets its first real data.

## Status

**PLANNED 0/8.**

**Depends on:** Phase 170 merged (the Speak face is rebuilt in 170's
Great Pass; the correction flow and journal stream build on that
rebuilt face).

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Tuesday, 09:30. He holds the key, speaks a sentence about a
PostgreSQL migration. The text lands in the editor. He sees "postgress"
and taps Correct: "PostgreSQL." The correction is saved. Ten minutes
later he dictates again: "...the PostgreSQL schema..." — the pipeline
applies the correction automatically. In the Speak window the journal
shows every utterance as a live stream: source, target, latency, the
correction that fired. The learning digest reads "1 correction, reached
3 utterances." He never trained it before; now the desk learns how he
works.

Census facts from THE-TUESDAY-ARC.md section 0 that this phase pays:
dictation_corrections 0 (the "learns how you work" loop untrained);
the correction store exists (corrections.py:1-56, CorrectionStore with
Jaccard matching, durable via DictationCorrectionRepository) but has
never been taught; the journal exists (journal.py:1-50,
DictationJournalRecorder, durable, secret-redacted) but is not a live
stream on the face; MicButton is on 7 surfaces but ~92 text inputs
exist across web/src/desk/ — the voice law (Article IV.1) is not
satisfied.

## Scope

- In:
  - The first correction: the correction flow on the Speak face (tap
    Correct on a landed utterance, type the correction, save; the
    CorrectionStore persists it via DictationCorrectionRepository;
    the pipeline's Jaccard matcher applies it to the next matching
    utterance; the learning digest reads > 0).
  - The journal as a stream: the Journal face
    (web/src/pages/cores/dictation/Journal.tsx) shows utterances as a
    live feed (source, target, latency, corrections applied, intent
    tag from DIR-01); filterable by source
    (dictation/browser/hotkey); searchable by text.
  - The voice law: MicButton on every text input across the desk
    (Article IV.1; UX-CANON.md rule B). The census identifies ~92
    text inputs; 7 have MicButton today. The gap is closed by
    ensuring every StringGadget, EditInPlace, and text input renders
    MicButton.
  - The desk answering the hand: the full loop from speak → land →
    judge → teach → apply, visible in one session on the Speak
    window. The correction fires on the next matching utterance
    without the owner reopening Settings or restarting the hub.
  - The design on the library before build (canvas at 1440 + 393).
  - His walk on his desk: one correction taught and applied.
- Out:
  - New dictation pipeline stages beyond DIR-01 (the pipeline is
    shipped; this phase uses it, does not extend it).
  - Cloud-based correction or learning (all local; Article III).
  - Correction import/export (the correction store is local; file
    exchange is a future phase).
  - Voice command authoring (the spoken-symbol dictionary and voice
    commands are separate capabilities; this phase is about the
    correction loop).
  - Correction UI beyond the Speak window (the correction flow lives
    on the Speak face; a Settings page for corrections is a future
    candidate).

## Exit criteria (evidence required)

- [ ] A correction is taught via the Speak face, persisted by
      DictationCorrectionRepository, and applied by the pipeline's
      Jaccard matcher to the next matching utterance; the
      correction_count on his desk is > 0.
- [ ] The learning digest (dictation_learning.py) reads > 0
      corrections with honest reach numbers.
- [ ] The journal face shows utterances as a live stream with source,
      target, latency, and corrections applied; filterable by source;
      searchable.
- [ ] MicButton is on every text input across web/src/desk/; the
      census shows 0 uncovered inputs (Article IV.1).
- [ ] The full speak → land → judge → teach → apply loop works in one
      session without restart.
- [ ] The design on the canvas at 1440 + 393 is ratified by the owner
      before the build.
- [ ] His walk on his desk: one correction taught and applied, the
      journal as a stream, MicButton everywhere; his word.
- [ ] Zero egress (Article III); every operation receipted (Article XI).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-176-01 | The design (the correction flow, the journal stream, the MicButton census on the canvas) | backlog | [story-01-the-design](./story-01-the-design.md) | -- |
| HS-176-02 | The first correction (teach, persist, apply to the next match; learning digest > 0) | backlog | [story-02-the-first-correction](./story-02-the-first-correction.md) | -- |
| HS-176-03 | The journal as a stream (live feed, filterable, searchable; the voice-typing act visible) | backlog | [story-03-the-journal-stream](./story-03-the-journal-stream.md) | -- |
| HS-176-04 | The voice law (MicButton on every text input across the desk; the census gap closed) | backlog | [story-04-the-voice-law](./story-04-the-voice-law.md) | -- |
| HS-176-05 | The desk answering the hand (the full loop: speak, land, judge, teach, apply) | backlog | [story-05-the-desk-answering-the-hand](./story-05-the-desk-answering-the-hand.md) | -- |
| HS-176-06 | The walk (his desk: correction taught, journal streaming, MicButton everywhere, the loop) | backlog | [story-06-the-walk](./story-06-the-walk.md) | -- |
| HS-176-07 | The docs (the Speak Loop in the guide; the correction flow in the architecture) | backlog | [story-07-the-docs](./story-07-the-docs.md) | -- |
| HS-176-08 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | backlog | [story-08-the-close](./story-08-the-close.md) | -- |

## Where we are

PLANNED. Waiting for Phase 170 to merge (the Speak face is rebuilt
in 170's Great Pass).

The recon is complete:

**Correction store today:** exists and is fully wired but untrained.
CorrectionStore (corrections.py:1-56) is a bounded ring buffer
(cap=20) of Correction(kind, key, value, sequence) dataclasses with
Jaccard token-overlap matching. Durably backed by
DictationCorrectionRepository (wired at web_runtime.py:97-109,
web_server.py:225-228). API routes exist: GET/POST/DELETE at
/api/dictation/corrections (pipeline.py:917-1009). Census:
dictation_corrections 0 on the owner's desk.

**Learning digest today:** exists as a read-only aggregation
(dictation_learning.py:1-58) over journal + corrections with honest
reach numbers using the same Jaccard matcher the live pipeline uses.
Computes but never writes. With 0 corrections, the digest is empty.

**Journal today:** DictationJournalRecorder (journal.py:1-50) writes
one durable row per pipeline run (source, raw_text, processed_text,
intent_tag, latency, corrections_applied). The Journal face
(Journal.tsx) exists on the Speak window but is not a live stream
with filtering and search.

**MicButton today:** on 7 surfaces (gadgets.tsx:299,357;
Surface.tsx:1174; ChairHome.tsx:540; ThreadPullout.tsx:751;
NoteEditor.tsx:166; RecipeEditor.tsx:113; DecisionsView.tsx:167).
~92 text inputs exist across web/src/desk/. The voice law
(Article IV.1: "every text input can be spoken into") is not
satisfied — the gap is ~85 uncovered inputs.

**DIR-01 pipeline today:** fully built at holdspeak/plugins/dictation/
(pipeline.py, contracts.py, runtime.py, three backends, grammars.py,
blocks.py, builtin stages, journal, corrections, telemetry_store).
The pipeline is shipped and functional; this phase uses it, does not
extend it.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| Correction quality (Jaccard false positives) | Medium | The ring buffer is capped at 20; the threshold is tunable; a false correction is one tap to remove; the correction flow shows what fired | > 30% of corrections fire on unrelated utterances during the walk |
| MicButton coverage regression | Low | A guard test counts MicButton instances vs text inputs; the ratchet enforces the coverage; the UX-CANON scanner tracks the gap | The guard count drops below the ceiling after a subsequent phase |
| Journal stream performance with large history | Low | The journal is durable rows with an index; the stream paginates; the face shows the most recent N with scroll-to-load | The journal face takes > 500 ms to render 100 entries |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- The exact correction UX on the Speak face (inline edit vs a
  correction well beneath the utterance) -- decided on the canvas.
- Whether the journal stream auto-scrolls to the latest utterance or
  stays at the user's scroll position -- decided at design time.
- The MicButton placement rule for compound gadgets (e.g. a
  StringGadget inside a LedgerRow: does the mic sit inside the
  gadget or on the row?) -- decided on the canvas.
