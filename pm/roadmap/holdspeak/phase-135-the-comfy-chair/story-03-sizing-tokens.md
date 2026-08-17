# HS-135-03 — The sizing tokens land

- **Project:** holdspeak
- **Phase:** 135
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-135-05, HS-135-13
- **Owner:** unassigned

## Problem

~1100 raw px values bypass the token scale because nothing exists
between `--space-8` and component-specific sizes (kit census). L9
(ratified with the counsel's pruning) adds exactly seven tokens:
`--size-touch` (40px), `--size-key` (48px), `--size-chip` (27px),
`--size-btn` (28px), `--size-icon-sm` (16px), `--size-icon-md` (20px),
`--size-icon-lg` (32px). The counsel REJECTED `--size-control`,
`--size-dock-h`, `--size-menubar-h` as duplicates of existing tokens.

## Scope

### In

- The seven tokens added to `web/design-tokens.json` (correct layer),
  `web/scripts/generate-tokens.cjs` run, generated tokens.css
  committed.
- Migration of the HIGHEST-TRAFFIC raw-px sites to tokens: the
  repeated 27/28/40/48px and icon sizes in surface.css, gadgets.css,
  chrome-menus.css (the census's worst files) — repeated values only;
  one-off geometry px stays.
- A drift note in the token JSON (comment) naming the seven and the
  rejected duplicates so nobody re-adds them.

### Out

- Migrating one-off px geometry; any visual change (this story is
  identity-preserving — same rendered pixels, tokenized).

## Acceptance criteria

- [ ] Seven tokens exist in JSON + generated CSS; zero collisions
  (grep).
- [ ] The migrated sites render pixel-identical (spot screenshots or
  computed-style assertions on representative components).
- [ ] Token generator round-trips clean; web suite green.

## Test plan

- `cd web && node scripts/generate-tokens.cjs && npx vitest run`
  (touched suites); computed-style spot checks in evidence.
