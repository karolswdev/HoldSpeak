# HS-59-01 — The language knob, end to end

- **Project:** holdspeak
- **Phase:** 59
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-59-03, HS-59-04
- **Owner:** unassigned

## Problem
Whisper speaks ~99 languages; HoldSpeak never passes one. Auto-detect is
the silent default and short utterances in one language get detected as a
neighbor's. There is no knob anywhere: config, settings, or docs.

## Scope
- **In:** `ModelConfig.language: str = "auto"`; `Transcriber(language=…)`
  threading to BOTH backends (`None` for auto — byte-identical; the code
  otherwise; the warm-up call aligned); all four construction sites
  (`web_runtime`, `main.py`, the import route factory, the import CLI);
  validation at the config/settings boundary against a vendored frozen
  set of Whisper codes (no whisper imports in config); the settings field
  (model section) with the language list; `/api/settings` round-trip +
  older-config coercion.
- **Out:** per-utterance switching; translation; meeting-side overrides
  (one knob serves all three consumers by design).

## Acceptance criteria
- [x] Fake-backend tests assert the kwarg both ways per backend: "auto" →
      no language at all (byte-identical call shape, structurally — the
      kwarg is conditionally built), "pl"/"de" → the code.
- [x] All four construction sites thread the knob (source-marker lock;
      web_runtime reads it defensively after its SimpleNamespace fixtures
      exploded the strict read — see evidence).
- [x] An invalid code is refused at the settings write with the
      actionable message AND the bad write changes nothing; "auto"/names/
      codes round-trip normalized; older configs coerce forward.
- [x] The settings Voice section exposes the knob with the honest
      auto-detect hint; the UI option list is set-equality-locked to the
      Python registry. Screenshot reviewed. See `evidence-story-01.md`.

## Test plan
- Unit on the Transcriber threading (fake impls); config round-trip +
  validation; settings page lock. Full suite.
