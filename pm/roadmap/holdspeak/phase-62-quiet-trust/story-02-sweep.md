# HS-62-02 — The sweep

- **Project:** holdspeak
- **Phase:** 62
- **Status:** done
- **Depends on:** HS-62-01
- **Unblocks:** HS-62-03, HS-62-04
- **Owner:** unassigned

## Problem
Beyond the cards, the web UI carries reassurance tails everywhere:
history notes, flashes, the welcome rail, the settings lead, tooltips.

## Scope
- **In:** every inventory line from the brief §3: `history.astro` draft
  notes + file-issue loop-note + proposal-note + proposal-guard;
  `history-app.js` flashes; `welcome.astro` rail foot; `settings.astro`
  lead + wake em-copy tail; `LocalPill.astro` tooltip;
  `ContextSection.astro` tail. Cut the reassurance, keep the function
  (what the control does); keep behavioral warnings verbatim. Update the
  HS-61 surface locks to the new copy. Build clean.
- **Out:** the journal "Preview only" state string; `commands.astro`
  danger copy; docs (HS-62-03).

## Acceptance criteria
- [x] A grep sweep for the reassurance phrases over web/src returns only
      the allowed explain-once surfaces (recorded in evidence).
- [x] The slack/aftercare locks pin the new shorter copy; suite green.
- [x] `cd web && npm run build` clean; 0 `_built/` tracked.

      See `evidence-story-02.md`.

## Test plan
- Updated `test_history_slack_surfaces.py` + any other copy locks; the
  full suite.
