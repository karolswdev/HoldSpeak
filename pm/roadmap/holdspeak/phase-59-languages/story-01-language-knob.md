# HS-59-01 — The language knob, end to end

- **Project:** holdspeak
- **Phase:** 59
- **Status:** backlog
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
- [ ] Fake-backend tests assert the kwarg both ways per backend: "auto" →
      no language (byte-identical call shape), "pl" → `language="pl"`.
- [ ] All four construction sites thread `config.model.language` (grep
      lock or per-site tests).
- [ ] An invalid code is refused at the settings write with an actionable
      message; "auto" and valid codes round-trip; an older config without
      the field coerces forward.
- [ ] The settings model section exposes the knob (page lock + screenshot).

## Test plan
- Unit on the Transcriber threading (fake impls); config round-trip +
  validation; settings page lock. Full suite.
