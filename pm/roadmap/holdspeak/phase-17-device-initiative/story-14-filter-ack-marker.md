# HS-17-14 — "Heard but filtered" ack marker for word-level Whisper hallucinations

- **Project:** holdspeak
- **Phase:** 17
- **Status:** done
- **Depends on:** HS-17-13 (transcript noise filter)
- **Owner:** karol

## Problem

HS-17-13 filtered Whisper hallucinations out of the LCD pushback path
to stop `Me: ...`, `Remote: You` noise from competing with real
content. Live use surfaced a UX gap: when AIPI-4-11 v2 made the middle
slot persist-until-replaced, filtered segments meant **no flash ever
arrived**, so the user kept seeing stale text and wondered if the
device had heard them at all.

User 2026-05-10: *"the middle doesn't seem to persist"* → after diagnosis,
the diagnosis flipped: the middle did persist, but the filter ate the
new flash before it could replace the stale content.

## Scope

### In

- Split the hallucination filter into two buckets:
  - **Pure silence** (empty / whitespace / only-punctuation): skip
    entirely. No audio worth acknowledging.
  - **Word-level hallucinations** (single-word artifacts like `you`,
    repeated patterns like `you you you`, known YouTube-training-data
    phrases): push a `{speaker}: …` marker instead of skipping. The
    middle slot updates and the user gets feedback.
- New `is_pure_silence(text)` helper in `holdspeak/device_status.py`.
- `push_segment_to_devices` consults both helpers: pure silence → 0
  sends; word-hallucination → ack marker; real text → full push.

### Out

- More granular hallucination categories. Two buckets is enough.
- Custom ack glyphs per category. `…` is fine.

## Acceptance Criteria

- [x] `is_pure_silence(text)` returns True for empty / whitespace /
  only-punctuation strings; False for any word content (even
  hallucinated).
- [x] `push_segment_to_devices` pushes `{speaker}: …` for word-level
  hallucinations; skips entirely for pure silence.
- [x] Unit tests cover both classifier (paramterized over hallucination
  / silence / real content) and dispatch behavior (word-level → ack,
  silence → skip).
- [x] Live-verified: user spoke while Whisper auto-language detected
  garbage → device middle flashed `Karol: …` rather than going stale.

## Notes

- **Why split rather than just `…` everything?** Pure silence
  (no audio at all) shouldn't trigger a flash — it'd be misleading
  ("I heard you" when there was nothing to hear). Word-level
  hallucinations DID involve real captured audio, just unparseable
  text — the ack honestly reports "audio captured, transcription
  empty".
- **Speaker preservation.** The ack uses the segment's `speaker`
  field unchanged so the user can see WHICH leg's audio failed —
  useful when multiple speakers are talking.
- **Cost.** Adds one broadcast per filtered segment. Bounded by
  Whisper's segment-emission rate (typically 1–3 per minute).
- **Companion to AIPI-4-11 v2.** The persist-until-replaced behaviour
  is what makes this fix necessary; without persist-until-replaced,
  filtered segments would just leave the slot empty for the TTL
  duration and the next real segment would replace it anyway.
