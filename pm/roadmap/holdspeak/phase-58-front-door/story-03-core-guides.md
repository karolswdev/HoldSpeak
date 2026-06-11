# HS-58-03 — The core guides

- **Project:** holdspeak
- **Phase:** 58
- **Status:** done
- **Depends on:** HS-58-01
- **Unblocks:** HS-58-05
- **Owner:** unassigned

## Problem
The guides a user actually follows open with mechanics, not meaning; the
feature names drift between docs; the pre-Phase-55 text is em-dash
saturated and has never had a voice pass.

## Scope
- **In:** GETTING_STARTED, USER_GUIDE, INTELLIGENT_TYPING_GUIDE,
  MEETING_MODE_GUIDE, DICTATION_COPILOT, VOICE_COMMANDS,
  ACTIVITY_PREBRIEFING, FIREFOX_EXTENSION_GUIDE: a two-sentence why-lede
  per doc aligned to the canon, canonical feature names throughout, the
  full humanizer pass, zero em/en dashes remaining in prose. Meaning,
  commands, and honest limits preserved; pinned phrases (Qlippy
  guarantees etc.) respected or their locks deliberately updated.
- **Out:** the developer/ops docs (04); restructuring beyond ledes +
  voice (no section reshuffles without cause).

## Acceptance criteria
- [x] Every listed guide opens with a why-lede; names match the canon
      (VOICE_COMMANDS + ACTIVITY_PREBRIEFING already opened to standard).
- [x] Zero em/en dashes in each finished file's prose except ONE
      deliberate verbatim UI quote in the typing guide (the string
      `journal.js` really renders; exempt per the canon; will be
      allowlisted by the HS-58-05 guard). 70 dashes removed, each
      replacement hand-chosen.
- [x] Doc locks green; no pinned phrase altered. Bonus find: an `HS-9-03`
      vocab leak in the Firefox guide that the Phase-51 guard's
      two-digit pattern misses — fixed here, guard widening goes to
      HS-58-05.
- [x] Meaning preserved (every edit is punctuation/lede/naming;
      commands, contracts, and honest limits untouched — see
      `evidence-story-03.md`).

## Test plan
- Doc-guard slice per batch + full suite.
