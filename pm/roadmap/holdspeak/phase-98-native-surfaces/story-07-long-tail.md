# HS-98-07 — The long tail, seam retired

- **Project:** holdspeak
- **Phase:** 98
- **Status:** done
- **Depends on:** HS-98-02..06
- **Unblocks:** HS-98-08, HS-98-09

## Problem

Commands (303), Profiles (320), Companion (123), and RuntimeDocs (82)
still speak the page grammar (Cadence converted in HS-98-01), and
`react-app.css` still ships page classes the desk no longer uses.
The seam is only retired when the allowlist is empty and the dead CSS
is gone.

## Scope

- In:
  - the remaining cores re-composed in the kit;
  - the guard allowlist EMPTY — every core native, the allowlist
    mechanism itself now refusing new entries;
  - `react-app.css` audited: selectors used by no shipped surface
    deleted; classes still used by legitimate page shells (welcome,
    presence) stay and are named in the evidence;
  - the token gate allow-list re-checked for entries the pruning
    stales.
- Out:
  - deleting `react-app.css` wholesale (page shells remain).

## Acceptance criteria

- [ ] Guard green with an EMPTY allowlist; plant still fails.
- [ ] `react-app.css` pruned; a grep census in evidence names every
      surviving class's consumer.
- [ ] Production build + all walk legs green after pruning; `npm run
      check` + python suite green.

## Test plan

- Seam guard; grep census; full walk chain; `npm run check`.

## Evidence required

- Census, pruning diff stat, walk output, suite output.
