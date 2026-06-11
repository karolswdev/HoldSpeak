# Evidence — HS-58-02: README.md, the front door

**Date:** 2026-06-11
**Branch:** `phase-58-front-door`

## 1. What shipped

**`README.md`**, rewritten against the canon (238 lines vs. 217 before —
within the ≈-current-length target while adding a whole new section):

- **The hero** now IS the canon's one-liner: one local copilot, two modes,
  nothing leaves your machine. The intro paragraph frames both places a
  developer's voice does work (the keyboard, the meeting) before any
  mechanics.
- **"The two modes"** replaces the old three-column glance table: Dictate
  and Meet get equal billing, and the tour now carries the post-Phase-48
  shipped surface the old README missed: voice commands, activity
  pre-briefing, recording AND transcript import (with the
  timestamps/speakers truth), meeting aftercare, the propose-approve-
  execute flow, faceted archive search.
- **"Why it's different"** tightened to the canon's four pillars
  (everything-local incl. the LLM / the learning loop with receipts /
  meetings end closed / honest by construction), each linking its proof.
- **"How it compares (as of mid-2026)"** — the section the repo never had:
  named tools (OS dictation, superwhisper/MacWhisper/VoiceInk, Wispr
  Flow/Aqua Voice, Talon, raw Whisper tooling), trade-offs stated in BOTH
  directions, date-stamped, architecture-level on purpose, closed by
  HoldSpeak's own trade-offs paragraph (0.x, bring-your-own model, heavier
  setup, no Windows, Wayland best-effort).
- **Qlippy** gets the delight beat in "See it learn", with the never-acts
  guarantee and the three privacy answers summarized.
- **Kept and tightened**: the status banner, quickstart (extras renamed to
  the canonical "the dictation pipeline"), upgrade-trust section, platform
  table, meeting deep-dive (now mentioning transcript import), AIPI-Lite,
  where-next (canonical names; a Voice Commands row added), configuration.
- **Contributing** now pitches building ON HoldSpeak (plugin authoring +
  connector development as "the doors in") per the developer-audience
  decision.

**`docs/README.md`** — the index hero aligned to the same one-liner.

## 2. The honesty + voice audit

- Zero em/en dashes in both files (grep-verified).
- One humanizer slip caught and fixed during the audit ("not just a
  transcript" → a direct comparative sentence).
- Every new claim maps to a shipped capability; the comparison section
  credits each named tool first; the trade-offs paragraph states ours.
- The plugin-count lock satisfied ("14 built-in plugins", matching the
  registry); absolute raw.githubusercontent image URLs retained for PyPI
  rendering.

## 3. Tests

```
$ uv run pytest -q tests/ -k "doc"
77 passed, 2 skipped
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2641 passed, 17 skipped
```

(Docs-only; suite count unchanged. Plugin-count, link, image, vocab locks
all green over the rewrite.)

## 4. A cadence repair, noted honestly

The HS-58-01 commit shipped without its project-README "Last updated"
entry: the cadence script ran from a stale working directory and its
file write silently targeted a non-existent relative path. Caught while
flipping this story; the README now carries both entries (HS-58-01 +
HS-58-02), repaired in this commit.
