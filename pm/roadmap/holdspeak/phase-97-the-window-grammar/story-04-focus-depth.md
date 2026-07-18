# HS-97-04 — Focus and depth

- **Project:** holdspeak
- **Phase:** 97
- **Status:** backlog
- **Depends on:** HS-97-01
- **Unblocks:** HS-97-06, HS-97-09

## Problem

The front window and every window behind it wear the same material:
same fill, same border, same (currently absent) shadow. Nothing tells
the user where their keyboard will land. And motion tells only half a
story: windows spring in but vanish in a single frame on close;
minimize teleports the window away while its dock chip appears
unannounced. Depth and motion are how an OS says what just happened.

## Scope

- In:
  - focus states on the one material: the front window carries the full
    elevation and a keyline; rest windows drop to a quieter shadow and
    border (component tokens, not private recipes — the HS-96-04
    grammar extends, it does not fork);
  - close motion: an exit animation (scale/fade, compositor-only);
  - minimize/restore motion: the window contracts toward its dock chip
    and returns from it (graceful fallback when the chip is not yet in
    the DOM);
  - `useReducedMotion` honored on every new transition;
  - the storm re-run: the new states stay inside the Phase 95 frame
    envelope.
- Out:
  - dock redesign (HS-97-07); exposé (HS-97-06).

## Acceptance criteria

- [ ] Front vs rest windows are visually distinct (focused elevation +
      keyline vs quiet), driven by tokens; shots at 1440 show three
      stacked windows reading as separate planes.
- [ ] Close animates out; minimize animates toward the dock chip and
      restore back; reduced-motion renders all three instant.
- [ ] Storm median within the Phase 95 envelope on the assembled build.
- [ ] Web suite + guards green; no new validator allow-list entries.

## Test plan

- vitest for the state classes; the walk's focus/motion leg (screenshot
  of a 3-stack with distinct depth); the storm; `npm run check`.

## Evidence required

- Shots, storm numbers, suite output, the token diff.
