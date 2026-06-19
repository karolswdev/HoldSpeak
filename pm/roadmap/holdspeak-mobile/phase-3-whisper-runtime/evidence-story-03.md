# Evidence — HSM-3-03 — Language selection (99-language parity)

- **Shipped:** 2026-06-18
- **Commit:** Phase-3 core bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/scripts/gen-languages.py` — generator that emits the Swift registry
  **from the desktop `holdspeak/languages.py`**, guaranteeing parity.
- `apple/Sources/Providers/Transcription/Language.swift` — generated: the
  `WhisperLanguage` registry (code→name), `normalize(_:)` ("auto"/""/nil → nil,
  code or English name → code, unknown → throws), `count`, `isValid`.
- `apple/Tests/ProvidersTests/TranscriptionTests.swift` — parity + normalize tests.

## Verification artifacts

`cd apple && swift test` → **13 tests, 0 failures**. Relevant:

```
testLanguageRegistryParityWithDesktop passed   # count == 100 (== desktop registry)
testLanguageNormalize passed                   # auto->nil, pl->pl, Polish->pl, GERMAN->de, klingon throws
testTranscriberConfigAutoIsNil passed          # default "auto" normalizes to nil
```

Parity note: the desktop registry is **100** entries (the "~99 languages" is the
colloquial Whisper figure); the Swift registry is generated from it, so the count
matches by construction.

## Acceptance criteria — re-checked

- [x] Language selection covers the desktop's registry (generated from it; count
  parity asserted), with `auto` the default that normalizes to nil.
- [x] A non-`auto` selection resolves to a Whisper code (pl/de/...); an unknown
  value fails honestly (throws), mirroring desktop's `ValueError`.

## Deviations from plan

The registry is **generated** from desktop rather than hand-written — stronger
parity guarantee; `gen-languages.py` is committed so it can be regenerated if
desktop's list changes.

## Follow-ups

The actual decode honoring the language is HSM-3-01's WhisperKit impl (device).
