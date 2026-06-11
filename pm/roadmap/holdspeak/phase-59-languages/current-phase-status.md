# Phase 59 — Speak Your Language (languages + the spoken-symbol dictionary)

**Status:** in-progress (3/4). Opened 2026-06-11 on user direction ("K, then
O" → "Kkkkk"), right after the Phase-58 follow-ups merged (PRs #46, #47).
From the [project backlog](../BACKLOG.md): candidate **K**, the cheapest
reach-expansion on the board, under one thesis: **the input layer adapts to
you**. Candidate **O** (wake word) is queued behind it per the same user
direction, with the misfire-safety conditions recorded in the conversation.

**Last updated:** 2026-06-11 (**HS-59-03 done: docs.** The User Guide
(the punctuation table's home; extend-don't-fragment) gains "Speak your
language" (Auto-detect explained, the honest short-utterance note, the
one-setting-covers-everything statement) and the spoken-symbol dictionary
woven in beside the built-in table (three real examples, user-wins, all
four attach modes with `std::vector`); Getting Started gets the pointer.
Zero dashes in new prose; doc slice 81 green; suite 2683 (docs-only).
**HS-59-02 (prior): the spoken-symbol
dictionary.** `dictation.spoken_symbols` (default empty) validated
actionably in `__post_init__`; `TextProcessor` merges user entries over
the pristine built-ins (user wins; symbols are literal, never regex
templates); web_runtime threads it; the Voice-typing settings editor
ships. **A real find**: per-table ordering let built-in "colon" eat the
user's "double colon" — `_process_punctuation` is now ONE combined
longest-first pass across every table, with the strongest byte-identical
proof available: the golden lock AND all 55 pre-existing processor tests
pass unmodified. POSITIONING gains the canonical rows. 20 tests;
screenshot reviewed; full suite **2683 passed, 17 skipped** (+20).
**HS-59-01 (prior): the language knob, end to
end.** `holdspeak/languages.py` (pure, import-locked) vendors the
99-language Whisper registry with `normalize_language` (auto/codes/names,
actionable refusal); `ModelConfig.language="auto"` coerces older shapes;
the Transcriber facade normalizes once and threads BOTH backends with a
conditionally-built kwarg, so the auto call shape is byte-identical
structurally (fake-backend assertions both ways); all four construction
sites threaded + source-locked; the settings boundary validates (a typo
fails the write and changes nothing); the Voice section gains the
"Spoken language" select with the honest auto-detect hint, its option
list set-equality-locked to the Python registry. 18 tests; screenshot
reviewed; full suite **2663 passed, 17 skipped** (+18).
Earlier: scaffolded — seams verified: neither Whisper
backend is ever passed a `language` (today IS auto-detect; the only literal
`language="en"` is the silent warm-up call), so "auto" as the default knob
is byte-identical by construction; four `Transcriber(` construction sites
must thread the knob; the punctuation table is a hardcoded class attribute
with attach semantics ready to merge user entries over.)

## The thesis — why this phase

Whisper speaks ~99 languages and HoldSpeak exposes none of it: no config,
no per-utterance pinning, nothing in settings. Auto-detect works until a
short utterance in your language gets detected as a neighbor's. And the
punctuation vocabulary is frozen at what we hardcoded: personal symbols
("tilde" → `~`, "arrow" → `→`) are classic daily-driver value. Both land on
the same seam set (config → the shared Transcriber / TextProcessor →
settings UI) and both serve dictation AND meetings through the one shared
transcriber.

## Goal

A `model.language` knob ("auto" default, byte-identical) that pins
transcription everywhere the one Transcriber is built, plus a user-defined
spoken-symbol dictionary merged over the built-in punctuation table (user
wins), both editable in settings, both honest in docs, proven on real
non-English speech at closeout.

## Scope

- **In:** the language knob end to end (HS-59-01); the spoken-symbol
  dictionary (HS-59-02); docs (HS-59-03); closeout with a real-metal
  non-English dogfood (HS-59-04).
- **Out:** per-utterance language switching mid-session; translation;
  language-specific punctuation command sets (the built-ins stay English;
  the dictionary is the user's tool for the rest); wake word (next phase);
  UI translation/localization of HoldSpeak itself.

## Exit criteria (evidence required)

- `model.language` ("auto" default) reaches BOTH backends as `None`/code;
  byte-identical at default (fake-backend kwarg assertions both ways);
  threaded through all four construction sites; validated at the settings
  boundary against a vendored code set; settings UI + round-trip.
  (HS-59-01)
- `dictation.spoken_symbols` (default empty, byte-identical, locked) with
  attach semantics, user-wins merge, longest-first across merged tables;
  the settings editor; clean 400 on malformed entries; the canonical-name
  row added to POSITIONING.md. (HS-59-02)
- Docs canon-clean (the live voice guard passes); the honest
  short-utterance auto-detect note; meetings/import covered by the same
  knob, stated. (HS-59-03)
- Real metal: a real non-English spoken utterance through real Whisper
  pinned vs. auto; the dictionary through the real pipeline; defaults
  byte-identical; full suite green; `final-summary.md`; BACKLOG K flipped;
  PR merged on green. (HS-59-04)

## Invariants

- **"auto" is byte-identical** to today (no `language` reaches a backend).
- **An empty dictionary is byte-identical** (TextProcessor output locked).
- **One Transcriber serves dictation, meetings, and import** — the knob
  applies to all three or none.
- **Honest docs**: auto-detect's short-utterance weakness stated plainly.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-59-01 | The language knob, end to end | done | none |
| HS-59-02 | The spoken-symbol dictionary | done | none |
| HS-59-03 | Docs: languages + the dictionary | done | HS-59-01, HS-59-02 |
| HS-59-04 | Closeout: real-metal dogfood + final-summary + PR | backlog | HS-59-01..03 |

## Where we are

**HS-59-01 → HS-59-03 shipped 2026-06-11.** Built, locked, and
documented. Next is **HS-59-04 — closeout**: real non-English speech
through real Whisper (pinned vs. auto), the dictionary through the real
pipeline, final-summary, PR.
