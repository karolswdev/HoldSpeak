# HS-26-02 — Extract Meeting / Speaker / Intel Routes

- **Project:** holdspeak
- **Phase:** 26
- **Status:** backlog
- **Depends on:** HS-26-01
- **Unblocks:** HS-26-07
- **Owner:** unassigned

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

- [ ] Listed routes are served from the new module; none remain inline in
      `_create_app()`.
- [ ] Existing web tests for meetings/speakers/intel pass unchanged.
- [ ] Route-inventory diff shows identical paths/methods for the moved set.

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (meeting or speaker or intel)"`.
- Integration: meeting start/stop + transcript fetch via the runtime.
- Manual: n/a.

## Notes / open questions

- If `routes/meetings.py` gets unwieldy, split speaker/intel into their own
  modules — record the split in this story's notes.
