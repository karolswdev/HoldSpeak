# HS-98-05 — The config pair

- **Project:** holdspeak
- **Phase:** 98
- **Status:** backlog
- **Depends on:** HS-98-01
- **Unblocks:** HS-98-09

## Problem

Settings (557 lines) and Setup (164) are where trust is configured —
and they read as web forms in cards. An OS settings surface is dense
sections of labeled controls on one material, not a page of panels.

## Scope

- In:
  - `SettingsCore`: sections per config cluster (hairline + quiet
    label), Signal controls (Switch/Select/TextInput stay — they are
    token-native) on dense setting rows (label left, control right,
    collapsing by container width); scope deep-links
    (`integration:destinations`) land on their section;
  - `SetupCore`: the guided steps as one quiet sequence in the idiom;
  - both off the guard allowlist.
- Out:
  - config schema/API changes; the welcome wizard (a page shell, out
    of phase scope).

## Acceptance criteria

- [ ] Both cores off the allowlist; guard green.
- [ ] The config round-trip walk leg passes (save → reload →
      byte-identical).
- [ ] Scoped open (Integrations alias) lands on the right section,
      shown in a shot; reflow shots; `npm run check` + python suite
      green.

## Test plan

- Existing settings vitest + config walk leg; scoped-open shot; reflow
  shots; `npm run check`.

## Evidence required

- Before/after shots, walk output, guard output, suite output.
