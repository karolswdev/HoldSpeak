# HS-53-02 — The nudges API

- **Project:** holdspeak
- **Phase:** 53
- **Status:** done
- **Depends on:** HS-53-01
- **Unblocks:** HS-53-04
- **Owner:** unassigned

## Problem
The nudge engine (HS-53-01) computes nudges in Python; the web UI (HS-53-04) needs them
over HTTP, and a dismiss action needs to reach the dismissal store.

## Scope
- **In:**
  - `GET /api/activity/nudges`: compute the current nudges, drop dismissed ones, return
    the top N with their citations. Returns an empty list when activity tracking is off.
  - `POST /api/activity/nudges/{id}/dismiss`: record the dismissal so the nudge does not
    return.
  - Add to the existing activity routes (`holdspeak/web/routes/activity/`, alongside
    `ledger.py` / `candidates.py`), or a small new `nudges.py` router wired in
    `web/routes/__init__.py`.
- **Out:** the engine (HS-53-01); the UI (HS-53-04); the context override (HS-53-03).

## Acceptance criteria
- [x] `GET /api/activity/nudges` returns the computed nudges (with citations); empty when
      activity is off.
- [x] `POST /api/activity/nudges/{id}/dismiss` persists the dismissal; a re-GET no longer
      returns it.
- [x] A malformed dismiss request returns a clean 4xx.
- [x] Tested with a `TestClient` over a seeded DB (mirror the existing activity route
      tests).
- [x] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Integration: GET returns seeded nudges; POST dismiss removes one; activity-off GET is
  empty (`uv run pytest -q -k "activity and (nudge or route)"`).

## Notes / open questions
- Mirror the shape + error handling of the existing `/api/activity/...` endpoints
  (`ledger.py`, `candidates.py`).
