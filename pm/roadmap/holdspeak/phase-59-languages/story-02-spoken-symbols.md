# HS-59-02 — The spoken-symbol dictionary

- **Project:** holdspeak
- **Phase:** 59
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-59-03, HS-59-04
- **Owner:** unassigned

## Problem
The punctuation vocabulary is a hardcoded class attribute. "Tilde",
"arrow", "backtick", a team's jargon — personal vocabulary is daily-driver
value and there is nowhere to put it.

## Scope
- **In:** `dictation.spoken_symbols` (default empty): entries
  `{spoken, symbol, attach}` with attach ∈ left/right/both/none (none =
  plain replacement, the safe default). `TextProcessor` takes the entries
  and merges them over the built-ins (user wins on a spoken-phrase
  conflict; longest-first matching holds across the merged tables;
  `re.escape` on spoken phrases). `web_runtime` threads the config. The
  settings editor (dictation section): add/remove rows, attach picker,
  live preview of one example. Round-trip with a clean 400 on malformed
  entries (empty spoken/symbol, bad attach).
- **Out:** language-specific built-in command sets; regex entries;
  per-target dictionaries.

## Acceptance criteria
- [x] Processor matrix: each attach mode lands its spacing (incl. the
      literal-symbol guarantee); user overrides a built-in (class tables
      un-mutated) and can move one to another mode; multi-word phrases
      win over shorter prefixes ACROSS tables — a real find: per-table
      ordering let built-in "colon" eat the user's "double colon"; the
      pass is now one combined longest-first sweep, with the 55 existing
      processor tests passing unmodified as the byte-identical proof.
- [x] Malformed entries refuse with a clean 400 (and the bad write
      changes nothing); valid entries round-trip normalized.
- [x] The settings editor ships (page locks + screenshot with three
      seeded rows); build clean.
- [x] POSITIONING.md gains the canonical-name rows ("the spoken-symbol
      dictionary" + "the spoken language setting").
      See `evidence-story-02.md`.

## Test plan
- Unit matrix on TextProcessor; config validation; page locks. Full suite.
