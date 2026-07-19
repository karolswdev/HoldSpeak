# HS-99-05 — The dock is alive

- **Project:** holdspeak
- **Phase:** 99
- **Status:** backlog
- **Depends on:** HS-99-01
- **Unblocks:** HS-99-08

## Problem

The dock is the OS's heartbeat and ours is static: chips that only
tint. The reference's taskbar carries the life of the system — a
running underline that grows on hover, icons that swell, a frosted
two-layer material.

## Scope

- In:
  - running-window indicator: an underline pill on each open window's
    chip (front chip full-width, rest 90%, grows on hover);
  - hover motion: chip icon scale (compositor-only, duration/easing
    tokens, reduced-motion instant);
  - the frosted two-layer material (tint layer + blur layer) on the
    dock and its transients, tokens preserved;
  - chip enter/exit animation (fade in; fade + width collapse out);
  - the Phase 97 shelf floors intact (one shelf, orb centered,
    launcher registry).
- Out:
  - dock badges/counts (no truthful source yet; rider).

## Acceptance criteria

- [ ] Open windows read on the dock at a glance (underline); hover
      swells the chip; enter/exit animates; reduced-motion instant.
- [ ] Shelf walk leg green; storm within envelope.
- [ ] `npm run check` + python suite green.

## Test plan

- vitest dock tests; shelf walk leg; storm; shots; `npm run check`.

## Evidence required

- Shots, storm numbers, walk output, suite output.
