# HS-96-04 — One material grammar

- **Project:** holdspeak
- **Phase:** 96
- **Status:** backlog
- **Depends on:** HS-96-02, HS-96-03
- **Unblocks:** HS-96-07

## Problem

Phase 95 shipped fast and it shows in the material: surface windows carry
an ad-hoc background/border/shadow recipe beside the pull-out grammar,
the trust window a third; radii wander (8/10/14/16/18/999), elevation is
improvised per panel, and motion durations are scattered literals. The
owner's bar is a desk that reads as ONE built thing.

## Scope

- In:
  - one elevation scale (rest / raised / focused / maximized), one
    radius scale, one motion scale — as component tokens applied across
    pull-outs, surface windows, the trust window, the menu, the shelf,
    the dock, and sheets;
  - the surface-window and trust-window one-off recipes folded into the
    shared window material;
  - spacing rhythm inside window bodies normalized (the ui-styling
    hierarchy discipline: one padding grammar, one gap scale);
  - a before/after visual review at 1440 and 393 — screenshots LOOKED AT,
    per the standing rule.
- Out:
  - layout or behavior changes; new chrome.

## Acceptance criteria

- [ ] One window material: pull-outs, surface windows, and the trust
      window differ only by tokens a reader can point to, not by private
      recipes (grep-verifiable: no window-scoped background/shadow
      literals).
- [ ] Radius/elevation/motion values on the desk come from the scales;
      the validator allow-list did not grow.
- [ ] The before/after review at both viewports is in the evidence with
      the changes named; the frame-budget storm shows no regression.
- [ ] Web suite + guards green.

## Test plan

- `npm run check`; the storm re-run; the screenshot review.

## Evidence required

- diff stats, the named visual changes, shots, storm numbers.
