# HS-94-02 progress record — Delivery Source registry and coherent read model

**Captured:** 2026-07-16<br>
**Acceptance status:** done; the formal p95 latency measurement rides the
HS-94-10 assembled campaign (the zero-shell-out mechanism is test-pinned).

## What shipped

`holdspeak/delivery/` — the phase's foundation package:

- **registry.py** (`registry_schema:1`, `~/.holdspeak/delivery_sources.json`):
  opaque `src_`/`wt_` identities; the fingerprint is sha256 over the
  credential-free normalized origin URL and root commit (path/token can
  never enter the digest); several worktrees of one clone share a source,
  two clones of one upstream differ, a per-registry salt prevents
  cross-node collisions; `node_id` reserved nullable. The v1 map imports
  non-destructively, once.
- **collector.py**: one provider per source over the vendored dw
  (capabilities + state + cursored events), single-flight with a freshness
  re-check at leadership acquisition, a global subprocess semaphore,
  classified path-free failure details, last-known-good retention, bounded
  replay buffers.
- **read_model.py** (`delivery_schema:1`): one revision covers every
  collection by construction; `cur_` cursors compose per-source dw cursors
  opaquely; event fields ride an allow-list.
- **routes/delivery.py**: `/api/delivery/{snapshot,sources,events}` with
  ETag/304, all collection via `asyncio.to_thread`, a lazy collector so app
  assembly has no side effects; the legacy `/api/missioncontrol/*` bridge
  stays untouched alongside (the contract keeps compat routes until proven
  caller-free).

## Verification

36 new tests (17 registry + 19 read-model/routes) including: a real
end-to-end lane driving the vendored dw against a scratch rails repo
(snapshot → real story flip → cursor replay); ten concurrent readers
costing exactly three dw invocations; cached snapshot and event replay
shelling out zero times; one failing source keeping last-known-good without
erasing the healthy one; recursive wire-hygiene walks (no paths, no
credentials); schema mismatch disabling only the affected capability.
Combined delivery/missioncontrol/dw lane: 123 passed. API surface
regenerated after the routes existed (314 routes, 5 surface tests green).
Captured at close in [evidence-story-02](./evidence-story-02.md).
