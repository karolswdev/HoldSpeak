# HS-171-03 — The needs-you aggregate

- **Project:** holdspeak
- **Phase:** 171
- **Status:** in-progress
- **Depends on:** HS-171-02
- **Unblocks:** HS-171-04, HS-171-05
- **Owner:** unassigned

## Problem

`GET /api/desk/needs-you` (projects.py:380) exists from HS-170-04 but
queries every active Room per request (the N+1 the arc names). On a desk
with 10 projects this is 10 sequential Room reads per API call. The
cadence tick should refresh this aggregate once and cache it; subsequent
reads serve the cache until the next tick.

## Scope

- In:
  - A server-side cache for the needs-you aggregate, invalidated by
    the cadence tick (HS-171-02).
  - The route serves the cached aggregate; response time < 50 ms from
    cache.
  - The cache stores the full payload: count, project IDs, items
    (with projectId, projectName, ref, title, why, severity), and
    the next scheduled item.
  - A bus event or a manual refresh forces cache invalidation (the
    owner can always get a fresh read).
- Out:
  - Changing the needs-you computation logic (the per-Room
    `_read_room_needs_you` in project_service.py:573 stays as-is).
  - Websocket push of the aggregate (the shade polls; push is a
    future enhancement).

## Acceptance criteria

- [ ] The route returns a cached response; a second call within the
      cadence interval does not re-query every Room (measured by
      counting `_read_room_needs_you` calls in a rig; Article IX.1).
- [ ] Response time < 50 ms from cache (measured in the rig).
- [ ] A cadence tick invalidates the cache; the next call re-queries.
- [ ] A manual refresh (`?fresh=1` (the route's name for it) or a bus event) invalidates the
      cache.
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k needs_you_cache`
  - Cache hit: second call does not call `_read_room_needs_you`.
  - Cache invalidation: cadence tick clears the cache.
  - Force refresh: `?force=true` clears the cache.
- Integration: the rig boots a hub with two projects, calls the route
  twice, asserts the second is faster than the first.
- Manual: n/a (the shade integration is HS-171-04).

## Notes / open questions

- The cache lifetime equals the cadence interval (HS-171-02). If the
  owner sets 15 min, the cache is valid for 15 min. Stale-for-one-tick
  is acceptable (Article V: watching is free).
