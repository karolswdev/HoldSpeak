# Evidence — HSM-18-03 — Spoken language at every WhisperKit call site

**Status:** done (2026-07-03). Landed in two increments: the main app (2026-06-27, PR #146 —
`whisperLanguage` in `InferenceConfigStore`, `DecodingOptions(language:)` at the
meeting-capture transcriber, the Signal "Spoken language" picker in Settings), and this
closeout: **the one resolver, at every remaining site**.

## The one resolver

`WhisperLanguage.configuredCode(defaults:)` (`Providers/Transcription/Language.swift`) —
reads the app's setting key (`hs.inf.whisperlang`, now also exposed as
`WhisperLanguage.settingKey`) and normalizes it: `nil`/""/"auto" → `nil` (per-utterance
detection, byte-identical), a code ("pl") or an English name ("Polish") → the code, an
unknown value → `nil` (never a crash at transcribe time). It lives in Providers — which
never links WhisperKit — so each app target wraps the code in its own
`DecodingOptions(language:)` while the key/normalize logic cannot diverge.

## The three call sites

- `Stores.swift` (meeting capture, landed earlier) — refactored onto the shared resolver,
  its inline key/normalize copy deleted.
- `CompanionAnswerApp.swift` (the answer-the-coder mic) — now passes
  `DecodingOptions(language:)`; previously always auto-detect.
- `SpeakHarnessApp.swift` (the on-device speak harness) — same.

## Proven

- `swift test` **425 passed**, incl. `testConfiguredLanguageCodeResolves` (absent / "auto" /
  code / English name / unknown → the exact resolution table above, on an isolated
  UserDefaults suite).
- All three app targets build clean for the simulator (meeting-capture, companion-answer,
  speak-harness — the aux gens stage `Sources/Providers`, so the resolver is present).

## Honest boundaries

Real spoken non-English audio through the aux apps rides the 18-06 device gate (the main
app's German-speech proof was Phase 59's; the wiring here is the same one-knob contract).
The aux apps have no settings UI — they honor the key when their container carries it,
otherwise auto (the pre-knob behavior, byte-identical).
