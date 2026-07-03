# Evidence — HSM-18-04 — The spoken-symbol dictionary, ported to Swift

**Status:** done (2026-07-03). The port landed 2026-06-27 (PR #147 —
`Providers/Transcription/SpokenSymbols.swift`, a faithful `text_processor.py` port:
built-ins + user symbols merged into **one combined longest-first pass**, user-wins, on the
DICTATION path only — never the verbatim meeting transcriber). This closeout ships the
missing user half:

## The user dictionary

- `SpokenSymbols.UserSymbol` is `Codable`; the list persists as plain JSON under
  `SpokenSymbols.userSymbolsKey` (`loadUserSymbols` / `saveUserSymbols` /
  `configured()` — the built-ins + persisted-user processor). A corrupt store falls back
  to built-ins, never a crash. Empty/absent = built-ins only, byte-identical.
- **The fill site honors it:** `VoiceCaptureState.stopAndTranscribe` now processes through
  `SpokenSymbols.configured()` — every speak-to-fill mic in the app applies the user's
  entries.

## The editor (Settings → SPOKEN SYMBOLS)

"Your symbols · Say the phrase · it types the symbol": rows of spoken-phrase + symbol
fields — **each with a speak-to-fill mic** (`MicFillField`) — an attach-mode menu
(keep spaces / left / right / both), delete, Add. Persisted on change. Sits directly under
the Spoken language card (the 18-03 sibling).

Screenshot: [`hsm-18-04-symbol-editor.png`](./screenshots/hsm-18-04-symbol-editor.png) —
three user rows (tilde → `~`, arrow → `→`, dash → `—` with attach-both) in place.

## Proven

- `swift test` **425 passed**, incl. `testUserSymbolsRoundTripAndConfigure` (round-trip +
  the user-wins proof: "self dash aware tilde" → "self—aware ~" — the user's em-dash beats
  the built-in hyphen in the ONE combined pass) and `testCorruptStoreFallsBackToBuiltins`.
- Meeting-capture app builds + the editor screenshot above.

## Honest boundaries

- User symbols are device-local (the story's scope): they shape the on-device speak-to-fill
  path. The hub's own `spoken_symbols` config governs hub-side dictation; syncing the two
  dictionaries is deliberately out (a future parity candidate, not silently divergent —
  each side's editor labels its own scope).
- The spoken "tilde on the real mic" walk rides 18-06.
