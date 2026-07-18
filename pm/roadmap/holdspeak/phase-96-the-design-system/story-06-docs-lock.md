# HS-96-06 — Docs and the mechanical lock

- **Project:** holdspeak
- **Phase:** 96
- **Status:** done
- **Depends on:** HS-96-04, HS-96-05
- **Unblocks:** HS-96-07

## Problem

A design system that lives in one agent's head is not a system. The
tokens, scales, specs, and the add-a-surface styling rules need one
documented home, and the locks that keep them true need to be named
where contributors will look.

## Scope

- In:
  - `docs/internal/DESIGN_SYSTEM.md` completed: the token architecture,
    the scales, the component matrices (HS-96-03's doc grows into the
    chapter), the validator and its allow-list policy, the focus/ARIA
    contract, and the Radix decision;
  - web/README's add-a-surface path gains the styling rules (component
    tokens only; the validator will catch you);
  - ARCHITECTURE's frontend section references the design system;
  - the voice/dash/doc guards green on everything touched.
- Out:
  - user-facing marketing docs; the slide system from the skill.

## Acceptance criteria

- [x] The design-system chapter exists and covers tokens, scales, specs,
      locks, and decisions; every value referenced is a token name.
- [x] web/README and ARCHITECTURE point into it; doc guards pass.
- [x] A contributor path test: the docs' add-a-surface styling steps
      name the validator and the spec doc (sweep-verified strings).

## Test plan

- doc drift guard suite; `npm run check`; manual read-through.

## Evidence required

- guard outputs; the doc diff summary.
