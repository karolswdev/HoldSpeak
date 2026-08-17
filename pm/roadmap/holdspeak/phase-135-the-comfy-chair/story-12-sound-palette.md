# HS-135-12 — The desk clicks

- **Project:** holdspeak
- **Phase:** 135
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

Motion is tokenized; audio does not exist — in a voice-first product
(census gap #10). L4 (ratified with conditions): six mechanical
sounds, an `sfx.ts` module (NOT CSS tokens), on by default.

## Scope

### In

Per assets/design-laws.md L4 + the counsel conditions verbatim:

- `sfx.ts`: typed sound enum (key-down, key-up, latch, land, file,
  error per the law), AudioContext playback, per-sound concurrent
  pool cap of 3 (oldest dropped silently), one global toggle persisted
  via Settings (the only writer), `prefers-reduced-motion` also mutes.
- Assets: six mono OGG (WAV fallback), 22050/44100Hz 16-bit,
  sub-120ms, mechanical-dry character; total well under the 100KB
  budget; the `"sound"` documentation section added to
  design-tokens.json (names only — no `--sfx-*` CSS properties, per
  ruling).
- Wiring per the law's trigger table: the hero + Record Orb
  (key-down/up), window open/close (latch), delivery/filing (land,
  file), refusals (error). Wire through the existing seams (window
  manager, mic button), not scattered call sites.
- Settings toggle row (gadget kit) under the appearance/behavior
  group; honest label.

### Out

- Speech audio; notification sounds beyond the six; per-sound volume.

## Acceptance criteria

- [ ] Six sounds play at their triggers (unit tests with a mocked
  AudioContext asserting play calls + pool cap).
- [ ] Toggle silences everything and persists; reduced-motion silences
  regardless of toggle (tests).
- [ ] Bundle size delta under budget (evidence notes the bytes).

## Test plan

- `cd web && npx vitest run` — sfx suite + settings/window seams
  touched.
