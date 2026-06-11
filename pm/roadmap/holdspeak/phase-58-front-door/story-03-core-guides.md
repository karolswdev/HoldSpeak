# HS-58-03 — The core guides

- **Project:** holdspeak
- **Phase:** 58
- **Status:** backlog
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
- [ ] Every listed guide opens with a why-lede; names match the canon.
- [ ] Zero em/en dashes in each finished file's prose; humanizer-clean.
- [ ] Doc locks green; any lock update called out in evidence.
- [ ] Meaning preserved (spot-diff review recorded in evidence).

## Test plan
- Doc-guard slice per batch + full suite.
