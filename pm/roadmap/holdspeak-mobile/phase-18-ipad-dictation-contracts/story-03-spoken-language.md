# HSM-18-03 — Spoken language at every WhisperKit call site

- **Project:** holdspeak-mobile
- **Phase:** 18
- **Status:** todo — independent on-device port; can run parallel to 18-01/02/04.
- **Depends on:** the WhisperKit transcribe path; `InferenceConfigStore`; the existing
  `WhisperLanguage` registry under `apple/Sources/Providers/`.
- **Unblocks:** correct non-English dictation + meetings on every Apple capture surface.
- **Owner:** unassigned

## Problem

The spoken-language setting is canonical on the hub (one knob drives dictation, meetings, and
import), but **every WhisperKit call site on Apple ignores it**. `Stores.swift:42`,
`CompanionAnswerApp.swift:44`, and `SpeakHarnessApp.swift:108` all omit
`DecodingOptions(language:)` and always auto-detect. Auto-detect is wrong for a user who has
chosen a language: it mis-fires on short utterances and code-switching, the exact failure the
hub's language knob exists to prevent.

## The design

1. **A language setting on the device.** Add `whisperLanguage` to `InferenceConfigStore`
   (default `"auto"` → `nil` at the call site, byte-identical to today). Back it with the
   vendored `WhisperLanguage` registry that already exists on the Providers side.
2. **Pass it at all three sites.** Thread the resolved code (or `nil` for auto) into
   `DecodingOptions(language:)` at `Stores.swift:42`, `CompanionAnswerApp.swift:44`, and
   `SpeakHarnessApp.swift:108`. One resolver, three call sites — no divergence.
3. **A picker in `AppSettings`** with a speak-to-fill-free Menu (a language list is a pick,
   not a dictation), matching the hub's one-knob model.

## Scope

- **In:** `whisperLanguage` in `InferenceConfigStore`; the `DecodingOptions(language:)` wiring
  at all three call sites; the `AppSettings` picker bound to the vendored registry.
- **Out:** the spoken-symbol dictionary (18-04 — a separate text pass); per-meeting language
  overrides (the hub has one knob; match it).
