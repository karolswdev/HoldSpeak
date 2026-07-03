# HSM-18-04 — The spoken-symbol dictionary, ported to Swift

- **Project:** holdspeak-mobile
- **Phase:** 18
- **Status:** done — see [`evidence-story-04.md`](./evidence-story-04.md). The faithful
  one-pass port landed 2026-06-27; the closeout ships the user half: `UserSymbol` persists
  (Codable, corrupt-safe), the speak-to-fill site applies `SpokenSymbols.configured()`
  (user-wins proven in tests), and Settings gains the "Your symbols" editor — a mic on
  every field. Device-local by scope; the real-mic walk rides 18-06.
- **Depends on:** the hub `TextProcessor` / `text_processor.py` (the canonical spoken-symbol
  contract); `WhisperText.clean` (the current Swift post-transcribe step).
- **Unblocks:** symbol parity ("open paren", "new line", user symbols) on Apple dictation.
- **Owner:** unassigned

## Problem

The spoken-symbol dictionary is entirely absent in Swift. The hub's `TextProcessor` turns
spoken tokens into symbols (built-in tables plus user-defined symbols, one combined
longest-first pass, user entries win) on the canonical dictation path. On Apple,
`WhisperText.clean` only strips control tokens — so "open paren" stays the words "open paren",
and a user's custom symbols do nothing. Same spoken input, divergent output across surfaces.

## The design

1. **Port `TextProcessor` to Swift**, faithfully: the built-in symbol tables plus the user
   symbol map, merged into **one longest-first matching pass** with user-wins precedence (do
   not add per-table loops — the canon is a single combined pass; this is a known footgun,
   see [[project_phase59_languages]]).
2. **Run it after `WhisperText.clean`** at the dictation post-processing point, so the
   pipeline is: WhisperKit → `WhisperText.clean` (control tokens) → `TextProcessor` (symbols).
3. **A symbol editor in `AppSettings`** (add/edit user symbols), each row's value field
   carrying a speak-to-fill mic, mirroring the hub's symbol-dictionary UI.

## Scope

- **In:** the Swift `TextProcessor` (built-in + user symbols, one longest-first pass,
  user-wins); its wiring after `WhisperText.clean`; the `AppSettings` symbol editor.
- **Out:** the language-code selection (18-03); meeting-side symbol application (the same
  ported processor will be reused there in Phase 19, not re-implemented).
