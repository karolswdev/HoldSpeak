# HS-26-02 — Extract Meeting / Speaker / Intel Routes

- **Project:** holdspeak
- **Phase:** 26
- **Status:** done
- **Depends on:** HS-26-01
- **Unblocks:** HS-26-07
- **Owner:** Claude (agent)

## Problem

Meeting lifecycle, transcript/search, speaker, action-item, export, and
intel-job routes are the largest cluster in `web_server.py`. With the router
seam from HS-26-01 in place, move them verbatim into a dedicated module.

## Scope

### In

- Move meeting (`/api/meeting*`, `/api/meetings*`), bookmark, speaker
  (`/api/speakers*`), action-item, export, and intel-job (`/api/intel/*`,
  `/api/all-action-items`) routes into `routes/meetings.py` (or split if it
  grows too large).
- Read everything from the shared context; no behavior change.

### Out

- Other domains (HS-26-03..05).
- Callback removal beyond what these routes need (HS-26-06).

## Acceptance criteria

- [x] Listed routes are served from the new module; none remain inline in
      `_create_app()`.
- [x] Existing web tests for meetings/speakers/intel pass unchanged.
- [x] Route-inventory diff shows identical paths/methods for the moved set.

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (meeting or speaker or intel)"`.
- Integration: meeting start/stop + transcript fetch via the runtime.
- Manual: n/a.

## Notes / open questions

- If `routes/meetings.py` gets unwieldy, split speaker/intel into their own
  modules — record the split in this story's notes.
- **Shipped as one module** (`routes/meetings.py`, 1020 lines, 25 routes). Kept
  whole rather than pre-splitting: it is a single verbatim move and the cluster
  is cohesive. Revisit a speaker/intel sub-split at HS-26-07 if navigation suffers.
- **`broadcast` is late-bound** in the wiring (a thunk delegating to
  `self.broadcast`) to preserve the original `self.broadcast` dynamic dispatch — a
  test reassigns `server.broadcast` post-construction. The `on_*` callbacks are
  snapshotted (never reassigned). See `evidence-story-02.md` §Deviations.
