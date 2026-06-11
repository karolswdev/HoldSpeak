# Evidence — HS-58-01: The positioning canon

**Date:** 2026-06-11
**Branch:** `phase-58-front-door`

## 1. What shipped

**`docs/internal/POSITIONING.md`** — the keystone the rest of the phase
aligns to:

- **The one-liner** built on the user's lead-angle decision: "One local
  copilot, two modes: dictation that types anywhere and learns how you
  work, and meetings that end with decisions, actions, and follow-ups
  instead of a recording. Nothing leaves your machine." Plus the short
  form for tagline tiers.
- **The three owner decisions recorded verbatim as fixed** (lead angle
  "one copilot, two modes"; audience developers; comparisons named +
  honest) with a no-relitigating note.
- **Four pillars, each with shipped proof points**: everything-local
  including the LLM (models contract, egress posture, the non-loopback
  bind refusal, secret filtering); the learning loop with receipts
  (journal, correction memory, digest, replay); meetings end closed
  (plugins, actuators with the never-acts invariant, aftercare, import,
  facets); honest by construction (doctor, schema policy + backups, the
  honest-copy test locks).
- **The named competitive frame** (as-of-dated, architecture-level by
  design): OS dictation, local Whisper menu-bar apps (superwhisper,
  MacWhisper, VoiceInk), AI dictation services (Wispr Flow, Aqua Voice),
  Talon, raw Whisper tooling — each with "what they do better / what we
  do better / pick them if", plus HoldSpeak's own honest trade-offs
  (0.x, bring-your-own model, heavier setup, no Windows, Wayland
  best-effort).
- **The canonical feature-name table**: one name per surface
  ("the dictation journal", "the correction memory", "voice commands",
  "meeting aftercare", "the archive", "Qlippy, the mascot", …) with the
  banned synonyms listed beside each.
- **The voice rules**: the humanizer standard, the no-dash rule (prose
  only; code blocks exempt), the honesty bar (claims need shipped proof;
  comparisons credit the other tool; limits next to strengths), why-ledes,
  developer register.
- **A maintenance section**: when the comparison table must be revisited,
  and that the name table grows one row per shipping phase.

**`CLAUDE.md`** — the canon added to the source-canon list, so every
future phase (docs or not) is bound to it.

## 2. Alignment with the owner decisions

All three decisions were collected directly from the user before writing
(lead angle / audience / comparisons) and are encoded as Decisions 1-3 in
the canon, each with a sentence of operational consequence (what it means
for how docs get written).

## 3. Tests

The canon is internal: the Phase-51 vocab guard must NOT scan it (it
deliberately contains competitive and positioning language) — confirmed by
the guard's scope test (non-recursive `docs/*.md` only; `docs/internal/`
excluded) and the green doc slice.

```
$ uv run pytest -q tests/ -k "doc"
77 passed, 2 skipped
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2641 passed, 17 skipped
```

(Docs-only; suite count unchanged.)
