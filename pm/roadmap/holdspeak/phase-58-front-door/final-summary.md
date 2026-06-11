# Phase 58 — The Front Door (positioning + the user-facing docs, revised): final summary

**Status:** CLOSED (6/6) — 2026-06-11 (opened and closed the same day)
**Branch → PR:** `phase-58-front-door` → PR to `main`, merged on green CI
**Backlog:** candidate **Q** shipped (net-new on user direction: *"a proper
phase. Where we also revise WHAT we are saying, so that we can be explicit
around how to 'sell' this product to our community"*).

## What the phase shipped

For the first time, HoldSpeak's story is a decision, not an accumulation.

1. **The positioning canon** (`docs/internal/POSITIONING.md`, now project
   canon via CLAUDE.md): the one-liner built on the owner's three fixed
   decisions (lead angle **"one copilot, two modes"**; audience
   **developers**; comparisons **named + honest**), four pillars each
   carrying shipped proof points, the named competitive frame
   (architecture-level and as-of-dated so it ages visibly), the canonical
   feature-name table, and the voice rules.
2. **README.md as the pitch**: the hero IS the one-liner; "The two modes"
   gives Dictate and Meet equal billing and finally carries the
   post-Phase-48 surface (voice commands, activity pre-briefing, recording
   AND transcript import, meeting aftercare, faceted search); the four
   pillars; **the "How it compares" section the repo never had** (OS
   dictation, superwhisper/MacWhisper/VoiceInk, Wispr Flow/Aqua Voice,
   Talon, raw Whisper tooling — credit given both directions, closed by
   our own trade-offs paragraph); Qlippy as the delight beat; Contributing
   re-aimed at people who want to build ON HoldSpeak.
3. **Every guide re-framed**: why-ledes that sell the feature's reason to
   exist ("a meeting should end with decisions, owners, and follow-ups,
   not a recording"; "the highest-leverage way to make HoldSpeak yours"),
   canonical names in prose, and the em-dash cleanup the pre-Phase-55
   corpus never had: **171 prose dashes removed across 14 files, every
   replacement hand-chosen**, with exactly one deliberate survivor (a
   verbatim UI quote the canon exempts).
4. **The voice guard**: dashes-zero + AI-vocab tells + canonical-name bans
   locked over the corpus, proven both ways, tuned live to zero false
   positives; the Phase-51 vocabulary pattern widened to single-digit
   phases.

## Before / after

| Metric | Before | After |
|---|---|---|
| Comparison content anywhere | none | a named, dated, both-ways section |
| README feature story reaches | ~Phase 48 | the live tree (Phase 57) |
| Em/en dashes in user-facing prose | ~170+ | **1** (allowlisted verbatim UI quote) |
| Positioning decisions written down | nowhere | canon, binding future phases |
| Voice regression protection | vocabulary only | vocabulary + dashes + AI-vocab + names |
| Suite | 2641 | **2645 passed, 17 skipped** (+4 guard tests) |

## Verified at closeout

- **GitHub's own renderer** (the `readme?ref=` API with the HTML accept
  header): the branch README renders with all 11 images and every key
  section ("One local copilot, two modes", "The two modes", "How it
  compares (as of mid-2026)", the plugin-count claim).
- **Every absolute asset URL** in the README returns 200 (curl-checked,
  including the install script).
- Doc-slice and full suite green throughout; the plugin-count, link,
  image, Qlippy, vocabulary, and new voice locks all pass.

## Real finds along the way

- **`HS-9-03` leaking in the Firefox guide** — roadmap vocabulary that
  survived Phase 51 because the guard's pattern expected two-digit story
  numbers. Fixed in the doc; the pattern widened and the leak added to
  the guard's must-flag list.
- **A verbatim UI quote almost broke**: the first dash pass edited the
  typing guide's quoted replay note; grepping the real `journal.js`
  string caught the desync and the quote was restored, then allowlisted.
- **The "not just" lesson**: the AI-vocab pattern's first cut flagged two
  legitimate logical uses; the shipped pattern targets only the
  negative-parallelism tic. Guards must be tuned on the real corpus, not
  written from theory.

## What did NOT ship (deliberately)

Website/social assets, demo videos, internal-doc rewrites, any behavior
change. The comparison table carries its own maintenance rule (revisit on
material architecture changes and at release-readiness passes).

## Numbers

6 stories + scaffold, one commit each, evidence in-commit throughout.
Suite 2641 → 2645. 14 user-facing files revised + 2 internal docs
(POSITIONING.md new, DOCS_STYLE.md extended) + CLAUDE.md.

## Follow-ups

- None required. **K — languages + spoken-symbol dictionary** remains the
  next feature phase in the agreed sequence.
