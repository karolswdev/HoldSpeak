# HS-45-05 — Docs: the dictation journal & its privacy posture

- **Project:** holdspeak
- **Phase:** 45
- **Status:** backlog
- **Depends on:** HS-45-01, HS-45-02, HS-45-03, HS-45-04
- **Owner:** unassigned

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
- [ ] `docs/INTELLIGENT_TYPING_GUIDE.md` documents the journal (record/store/
      protect/curate/disable), the in-moment fix loop, and replay, with a real
      screenshot.
- [ ] Root README + docs index cross-link the new section; the journal toggle is
      named where settings are documented.
- [ ] Doc-drift guard + link-check pass (`uv run pytest -q -k "doc or link"` /
      the repo's doc-guard tests).
- [ ] No live doc overstates behavior (no claim the journal is cloud-synced or
      on-by-default-without-opt-out wording that contradicts the toggle).

## Test plan
- Unit: `uv run pytest -q -k "doc_drift or link or doc_guard"` (the existing
  doc-truth/drift + link-check guards).
- Manual: render the guide section; confirm screenshots resolve and links work.

## Notes / open questions
- Reuse the presence-docs pattern (Phase 41) for screenshot placement under
  `docs/assets/` if a dedicated asset dir helps.
