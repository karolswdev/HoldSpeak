# HS-129-11 — The walk

- **Project:** holdspeak
- **Phase:** 129
- **Status:** backlog
- **Depends on:** HS-129-01, HS-129-02, HS-129-03, HS-129-04, HS-129-05, HS-129-06, HS-129-07, HS-129-08, HS-129-09, HS-129-10
- **Unblocks:** none
- **Owner:** unassigned

## The thesis (the bar)

The phase's claim — one grammar, every plane — is proven only on glass, on
the real hub, with the audit-B methodology re-run against the fixed product.
This story is non-waivable and cannot be closed by tests alone.

### What changes

1. A reusable walk harness (extending audit B's script) that: opens every
   dock surface, every Go entry, every primitive-kind pullout (via the
   object-open helper from HS-129-10), and the egress/Trust window;
   scrolls each top/middle/bottom; resizes small; maximizes; and repeats
   the core set at 393×852.
2. Automated assertions inside the walk: footer bounding-box pinned to
   window bottom (tall AND short content); title bar stationary under
   scroll; no horizontal overflow; no console errors; window height ≤
   working band.
3. The full evidence pack: screenshots at 1440 + 393 for every surface,
   named per the audit-B convention, captured into the phase evidence.
4. Full test suite + `npm run check` + `uv run pytest -q` (with the metal
   exclusion) green at the walk commit.

## Acceptance criteria

1. Every walked surface passes the pinned-foot, stationary-head,
   no-overflow, and height-cap assertions at both widths.
2. The audit-B P0–P2 defects each have a before (audit shot) and after
   (walk shot) pair in evidence.
3. Zero console errors across the walk (the Pixi/WebGL deprecation
   warnings are recorded, not counted as failures).
4. The suite, typecheck, build, and tokens gate are green in the same
   evidence capture.

## Test plan

- Walk: the harness run itself IS the test; evidence captured via
  `.githooks/dw evidence capture` around the harness + suite commands.
- Owner: the final screenshots are the sitting exhibit; the phase closes
  only on the owner's acceptance.
