# HS-100-06 — B2: the honest mic

- **Project:** holdspeak
- **Phase:** 100
- **Status:** backlog
- **Depends on:** HS-100-05
- **Unblocks:** HS-100-07

## Problem

On non-secure origins (the owner's LAN posture) `navigator.mediaDevices`
is undefined and every MicButton silently returns null — the voice
product loses its voice with no explanation (MicButton.tsx:56; trace B).
Article VI violation by omission.

## Scope

- In: MicButton renders a disabled state WITH its reason (insecure
  origin named, capture-unsupported named) instead of vanishing;
  the reason phrasing passes the vocabulary guard.
- Out: TLS/pairing changes (out of phase scope).

## Acceptance criteria

- [ ] A mic without capture is visible, disabled, and says why.
- [ ] Vitest pins supported / insecure-origin / no-device states.

## Test plan

- `cd web && npx vitest run src/desk/components/MicButton.test.tsx`.

## Evidence required

- Test output; a screenshot of the disabled-with-reason state.
