# HSEGHS001HS104-142-05 - Model Setup Wizard

- **Project:** holdspeak
- **Phase:** 142
- **Status:** done
- **Depends on:** HSEGHS001HS104-142-03
- **Unblocks:** pleasant local/hosted/tool candidate selection
- **Owner:** product

## Problem

The one-screen model catalog made every detected, suggested, hosted, and
experimental choice compete at once. Compact cards truncated exact model names
and turned truthful setup into a scanning exercise instead of a decision.

## Scope

- **In:** Replace the catalog wall with a three-step location/model/review
  wizard, wrap full model names, preserve one action seat, and prove the
  interaction at 1440 and 393.
- **Out:** New catalog entries, recommendation authority, runtime execution, or
  changes to server-owned setup facts.

## Acceptance criteria

- [x] Only one of device, OpenRouter, or tool-experiment choices is visible at
  a time.
- [x] The model list and action seat never coexist with the full catalog.
- [x] Exact model labels wrap and never use ellipsis.
- [x] Location, model, and review are keyboard-operable and selection alone
  never mutates settings or starts a download.
- [x] Review exposes at most one lawful primary action.
- [x] Real 1440/393 walks cover detected local, Hammer, and hosted choices.

## Test plan

- **Unit:** focused `InferenceCapabilityPanel` behavior and action tests.
- **Integration:** production web build plus isolated Models setup glass.
- **Manual / device:** inspect all three wizard states at desktop and narrow
  width for wrapping, focus, and information density.

## Notes / open questions

No server authority changed. The wizard filters the existing authoritative
projection and delegates every mutation to the same application commands.
