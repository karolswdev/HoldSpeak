# HS-100-02 — The judgment

- **Project:** holdspeak
- **Phase:** 100
- **Status:** done
- **Depends on:** HS-100-01
- **Unblocks:** HS-100-03

## Problem

The UI has been audited many times for consistency, never for
purpose. With the grounding in hand, every surface must answer one
question: which job does this serve, and does it serve it well?

## Scope

- In:
  - a full walk of the product as it stands (main + the parked spike
    branch), surface by surface, FLOW by FLOW (not screenshots of
    single windows: the whole path from intent to felt value);
  - **docs/internal/UIUX_JUDGMENT.md**: every window/flow judged
    keep / merge / re-shape / kill against the grounding's jobs, with
    the reasoning; the desk metaphor itself judged honestly (where
    the spatial world helps the jobs, where it is in the way);
  - the mangled paths named end-to-end (e.g. "from 'I just had a
    meeting' to 'the actions are filed' takes N windows and M
    unexplained concepts");
  - the spike's materials work judged as input: what carries into the
    thesis, what does not.
- Out:
  - proposing the new design (HS-100-03).

## Acceptance criteria

- [ ] Every registered surface and desk component appears in the
      judgment table with a verdict and a job citation.
- [ ] At least the three core flows are traced end-to-end with
      friction counts (windows touched, concepts required, dead ends).
- [ ] The desk-metaphor judgment is explicit, with evidence both ways.

## Test plan

- Cross-check: the judgment table covers the SURFACES registry +
  desk component inventory with zero omissions (scripted census).

## Evidence required

- The document; the census output; the flow traces.
