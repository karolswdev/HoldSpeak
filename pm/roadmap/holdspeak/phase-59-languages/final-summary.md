# Phase 59 — Speak Your Language: final summary

**Status:** CLOSED (4/4) — 2026-06-11 (opened and closed the same day)
**Branch → PR:** `phase-59-languages` → PR to `main`, merged on green CI
**Backlog:** candidate **K** shipped; candidate **O** (wake word) is next
per the standing user direction ("K, then O"), with the misfire-safety
conditions recorded on its BACKLOG row.

## What the phase shipped

One thesis: **the input layer adapts to you.**

1. **The spoken language setting.** Whisper speaks ~99 languages and
   HoldSpeak finally exposes it: `model.language` ("auto" default) pins
   transcription through the one shared Transcriber, so dictation, live
   meetings, and imported recordings all follow one setting. The vendored
   registry (`holdspeak/languages.py`, pure, import-locked) validates at
   the settings boundary: a typo fails the write with an actionable
   message and changes nothing. The byte-identical guarantee is
   structural: the backend kwarg is conditionally built, so the auto call
   shape IS the pre-knob call (fake-backend assertions, both backends,
   both ways; all four construction sites source-locked).
2. **The spoken-symbol dictionary.** User spoken→symbol entries
   ("tilde" → `~`, "arrow" → `→`, "double colon" → `::`) with the
   built-ins' attach semantics, merged user-wins over the punctuation
   table, the symbol always literal (never a regex template). Editable in
   the Voice-typing settings; empty by default and byte-identical, proven
   the strong way: all 55 pre-existing TextProcessor tests pass
   unmodified against the restructured matcher.

## The real find

Per-table processing order broke cross-table phrases: the built-in
`colon` (attach-left pass) ate the inside of a user's `double colon`
(attach-both), turning "std double colon vector" into "std double:
vector". `_process_punctuation` is now one combined pass sorted
longest-first across every table; the built-ins never overlapped across
tables, so their behavior is unchanged (the golden lock + the untouched
55-test file are the proof).

## The closeout dogfood (real metal)

```
spoken (Anna/de): 'Das Meeting beginnt morgen um neun Uhr und wir
                   besprechen die Datenbank Migration.' (4.7s)
pinned de  : 'Das Meeting beginnt morgen um 9 Uhr und wir besprechen
              die Datenbank-Migration.'
auto-detect: 'Das Meeting beginnt morgen um 9 Uhr und wir besprechen
              die Datenbank-Migration.'
PASS  real Whisper transcribed real German with the language pinned
PASS  the dictionary fired through the real settings round-trip
      ('std::vector', 'x → y')
PASS  fresh config defaults: language='auto', spoken_symbols=[]
PASS  the default TextProcessor is byte-identical on the golden cases
RESULT: PASS
```

Real German speech (macOS `say`, voice Anna) through real Whisper,
near-verbatim with the language pinned; auto-detect also succeeded on
this 4.7-second sentence, reported honestly (the pin earns its keep on
SHORT utterances, exactly as the docs say). The dictionary entries
traveled the real plumbing: the settings API → the saved config → the
exact TextProcessor construction web_runtime performs.

## Numbers

- Suite: 2645 (phase open) → **2683 passed, 17 skipped** (+38: 14 knob,
  4 settings-language, 17 dictionary, 3 settings-symbols).
- 4 stories + scaffold, one commit each, evidence in-commit.
- Two settings surfaces shipped (the language select with the
  registry-lockstep test; the symbol editor), two screenshots reviewed.

## What did NOT ship (deliberately)

Per-utterance language switching, translation, language-specific built-in
command sets, UI localization — out of scope by the phase doc.

## Follow-ups

- None required. Next per the standing direction: **O — wake word**, with
  the conditions on its BACKLOG row (arms-not-types, unmissable armed
  indicator via presence, a local engine with a real false-accept story,
  off by default).
