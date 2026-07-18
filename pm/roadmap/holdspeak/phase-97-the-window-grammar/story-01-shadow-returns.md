# HS-97-01 — The shadow returns

- **Project:** holdspeak
- **Phase:** 97
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-97-04, HS-97-09

## Problem

Every desk window renders shadowless. `generate-tokens.cjs`'s
`resolveReference` substitutes a `{ref}` only when the value is nothing
but the reference (`startsWith("{") && endsWith("}")`); composite values
like `"0 26px 70px {primitive.color.shadow.60}"`
(design-tokens.json, the `--desk-window-shadow` row) pass through
verbatim, so the emitted CSS carries a literal `{primitive.…}` and the
browser drops the declaration. `--desk-transient-shadow` (menus,
popovers) is broken the same way. The Phase 96 drift gate compares the
CSS to itself, so it can never notice — the defect class needs its own
mechanical lock.

## Scope

- In:
  - `resolveReference` resolves references embedded anywhere in a
    composite value (all occurrences, still failing loudly on an
    unknown path);
  - regenerate `tokens.css` + `tokens.gen.ts`; the only diffs are the
    healed values;
  - a mechanical gate: token generation (and `--check`) fails if any
    emitted CSS value still contains a `{` — the whole class of
    unresolved-reference bugs locked, not just these two;
  - a before/after screenshot pair at 1440 showing window elevation
    return, LOOKED AT per the standing rule.
- Out:
  - new tokens, new materials, any styling change beyond the heal.

## Acceptance criteria

- [ ] `tokens.css` contains zero `{` characters in emitted values;
      `--desk-window-shadow` and `--desk-transient-shadow` compute to
      valid `box-shadow` values in the browser.
- [ ] The gate fails on a planted composite unresolved reference
      (shown firing in the evidence) and passes clean.
- [ ] Before/after shots show windows casting real shadows on the
      production bundle.
- [ ] `npm run check` green; web suite green.

## Test plan

- `npm run check` (drift + validator + new brace gate); vitest suite;
  the planted-violation demonstration; production shots via the walk
  script.

## Evidence required

- The healed diff, the gate firing, the shots, suite output.
