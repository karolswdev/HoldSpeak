# HS-59-02 — The spoken-symbol dictionary

- **Project:** holdspeak
- **Phase:** 59
- **Status:** backlog
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
- [ ] Processor matrix: each attach mode lands its spacing; a user entry
      overrides a built-in with the same spoken phrase; multi-word
      phrases win over shorter prefixes; an empty dictionary is
      byte-identical (locked against a golden set of built-in cases).
- [ ] Malformed entries refuse with a clean 400; valid entries round-trip.
- [ ] The settings editor ships (page locks + screenshot); build clean.
- [ ] POSITIONING.md gains the canonical-name row ("the spoken-symbol
      dictionary").

## Test plan
- Unit matrix on TextProcessor; config validation; page locks. Full suite.
