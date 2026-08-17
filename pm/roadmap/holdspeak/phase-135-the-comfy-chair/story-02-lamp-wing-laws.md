# HS-135-02 — Lamps wrap, wings look pressable

- **Project:** holdspeak
- **Phase:** 135
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

Two ratified laws fix P0/P1 face bugs. L6: `gadget-lamp` uses
`white-space: nowrap` (`gadgets.css:641` region) so system messages
bleed past window edges at BOTH widths (face-walk P0; two lamps at
1440 in settings-models). L7: inactive wings/filing-strip tabs render
as plain text (`pullout.css:300-301` region, `--text-faint`, no
background) — counsel's own-eyes finding across Intelligence and
window strips.

## Scope

### In

Per assets/design-laws.md L6 + L7 verbatim (and the counsel ruling's
amendments — no `--desk-lamp-max-width` token; apply CSS directly):

- L6: inline lamps truncate with full-text title affordance; block
  system messages get the `.is-block` wrap variant; the two
  settings-models lamps become block. No nowrap bleed remains
  anywhere a lamp renders.
- L7: inactive wings get `color: var(--text-muted)` +
  `background: var(--wash-1)`; hover escalates per the law; active
  treatment unchanged. Applies to pullout wings AND window filing
  strips.
- Tests: a lamp-overflow regression test (long message, assert no
  overflow past container) and a wing-affordance style assertion in
  the web suite's style-testing idiom (find the house pattern first).

### Out

- Any other L-law; new tokens; content changes to lamp messages.

## Acceptance criteria

- [ ] settings-models renders both system lamps fully inside the
  window at 1440 (screenshot in evidence).
- [ ] Inactive tabs visibly read as controls (before/after screenshot
  pair).
- [ ] Tests green; zero visual regressions in touched suites.

## Test plan

- `cd web && npx vitest run` scoped to touched suites + new tests;
  before/after shots ride evidence (full walk rides HS-135-13).
