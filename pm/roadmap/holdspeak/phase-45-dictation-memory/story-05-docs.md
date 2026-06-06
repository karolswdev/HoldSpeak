# HS-45-05 — Docs: the dictation journal & its privacy posture

- **Project:** holdspeak
- **Phase:** 45
- **Status:** done
- **Depends on:** HS-45-01, HS-45-02, HS-45-03, HS-45-04
- **Owner:** Claude (Opus 4.8)
- **Evidence:** [evidence-story-05.md](./evidence-story-05.md)

## Problem
A persistent record of everything spoken is powerful and sensitive. Users need to
understand — in the docs, not just inferred from the UI — what the dictation
journal records, where it lives, how it's protected, how to curate or disable it,
and how the in-the-moment fix + replay loop works. (Per the standing rule: every
phase gets its own documentation story, after the features land, before
closeout.)

## Scope
- **In:**
  - A new section in `docs/INTELLIGENT_TYPING_GUIDE.md` — "Dictation journal,
    corrections & replay": **what is recorded** (transcript, routing, final
    text, per-stage latency, source), **where it lives** (local SQLite, never
    leaves the machine), **how it's protected** (secret-filtered, retention cap,
    one-click wipe, per-entry delete, the `journal_enabled` toggle), the
    **in-the-moment fix** loop, and **replay**. Include a real screenshot of the
    Journal + the before/after replay from the phase evidence.
  - Cross-link from the root `README.md` (the "Intelligent dictation" blurb) and
    the `docs/` index; a one-line mention in any settings/cockpit doc that names
    the journal toggle.
  - Keep the privacy posture **first-class** (a short "Your dictation stays
    local" callout mirroring the meeting-side framing).
- **Out:** code changes (features ship in 01–04); reference/API docs beyond the
  user guide unless trivially adjacent.

## Acceptance criteria
- [x] `docs/INTELLIGENT_TYPING_GUIDE.md` §12 documents the journal (record/store/
      protect/curate/disable), the in-moment fix loop, and replay, with **three**
      real screenshots (timeline, moment-of-truth, replay before→after).
- [x] Root README (the dictation blurb + the quick-link table) + the `docs/`
      index cross-link the new section; the `journal_enabled`/`journal_retention`
      toggles are named in the section.
- [x] Doc-drift guard + link-check pass (`test_doc_drift_guard.py`, 3 passed —
      incl. the dangling-relative-link check over the new image/section refs).
- [x] No live doc overstates behavior — the posture is explicit: local-only,
      never uploaded/synced, on-by-default-but-toggleable, side-channel.

## Test plan
- Unit: `uv run pytest -q -k "doc_drift or link or doc_guard"` (the existing
  doc-truth/drift + link-check guards).
- Manual: render the guide section; confirm screenshots resolve and links work.

## Notes / open questions
- Reuse the presence-docs pattern (Phase 41) for screenshot placement under
  `docs/assets/` if a dedicated asset dir helps.
