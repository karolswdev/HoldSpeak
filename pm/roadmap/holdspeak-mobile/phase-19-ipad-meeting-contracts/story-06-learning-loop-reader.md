# HSM-19-06 — The learning-loop reader (read-first)

- **Project:** holdspeak-mobile
- **Phase:** 19
- **Status:** todo (the clients are merged — commit `8f65657`)
- **Depends on:** `HTTPDesktopClient+Learning.swift` (`journalEntries(limit:source:)`,
  `learningDigest(window:)`); hub routes `GET /api/dictation/journal` +
  `GET /api/dictation/learning-digest` (`holdspeak/web/routes/dictation/pipeline.py:478`).
- **Unblocks:** the visible learning loop (HS-48) reaching the iPad.
- **Owner:** unassigned

## Problem

The hub's learning loop — the journal and the "what HoldSpeak learned" digest — has no read
surface on Apple at all. The read clients shipped with **zero callers**. The
`ENTITY-CATALOG.md` deliberately parks on-device journaling; a read-first review surface is
this story's whole scope.

## The design

1. **A learning card on the Dictate tab** (the loop is dictation's afterlife — it belongs
   beside the teleprompter, not under Meetings): the digest's headline numbers
   (corrections made, dictations corrected, the by-kind breakdown) for the week window,
   with an "all time" toggle.
2. **The journal beneath it**: recent entries newest-first (utterance → final text, source
   marked dictation / dry-run), honest at N=0 — a bare hub renders a quiet empty state,
   never an error.
3. **Read-only, stated by shape not prose:** no correction editing, no delete — the card
   simply has no write affordances (Phase 9 owns on-device corrections).

## Scope

- **In:** the digest card + journal list on the Dictate tab, the week/all toggle, honest
  empties, sim proof.
- **Out:** corrections CRUD (hub routes exist, deliberately unsurfaced on this seam);
  on-device journaling; any meeting-side surface.

## Test plan

- `swift test` green (decode covered by `*ClientTests`).
- Sim proof: seeded digest + journal → screenshots of the populated card and the N=0
  state.
