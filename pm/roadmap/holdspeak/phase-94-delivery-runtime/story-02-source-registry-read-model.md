# HS-94-02 — Delivery Source registry and coherent read model

- **Project:** holdspeak
- **Phase:** 94
- **Status:** backlog
- **Depends on:** HS-94-01
- **Unblocks:** HS-94-03, HS-94-04, HS-94-05

## Problem

`~/.holdspeak/delivery_workbench.json` maps a label to one local path. Every
open client independently launches state, event, session, and GitHub reads.
The four responses can describe different moments, raw paths reach clients,
and a second worktree or remote clone cannot be represented.

## Scope

- In:
  - `holdspeak/delivery/` package with provider, registry, collector, read-model,
    contract, and route boundaries;
  - versioned Delivery Source/Worktree registry;
  - migration adapter for the v1 project map;
  - local source discovery under configured roots, including linked worktrees;
  - opaque IDs and protected path storage;
  - one single-flight collector per source;
  - coherent `delivery_schema: 1` snapshot, revision, ETag, and event cursor;
  - last-known-good plus per-provider freshness/error;
  - bounded `dw`/git/`gh` concurrency and metrics;
  - compatibility `/api/missioncontrol/*` reads backed by the new projection.
- Out:
  - remote node transport;
  - terminal control;
  - new product UI;
  - automatic scanning of the whole filesystem.

## Acceptance criteria

- [ ] Registry represents several worktrees of one source and the same repository
      fingerprint on several nodes without ID collision.
- [ ] Clients receive no repo root, credential-bearing remote URL, or raw asset
      path.
- [ ] A snapshot carries one revision and internally consistent source, project,
      phase, Story, worktree, receipt, and freshness rows.
- [ ] One source failure retains its last-known snapshot with observed time and
      does not erase healthy sources.
- [ ] Unsupported schemas disable only the affected source capability.
- [ ] Ten simultaneous Web/native clients cause the same `dw`/`gh` invocation
      count as one client after the initial collection.
- [ ] Cached snapshot route p95 is below 100 ms in the flagship fixture; source
      refresh remains off the event loop and bounded.
- [ ] The existing map imports without destructive rewrite and existing conveyor
      tests pass through the facade.

## Test plan

- registry migration/round-trip and secret/path redaction;
- worktree discovery with removed/detached worktree;
- collector single-flight and cancellation;
- coherent-snapshot race fixture where a Story changes mid-refresh;
- ETag/304 and replay cursor;
- source timeout/schema mismatch/`gh` absence;
- concurrency test with ten clients;
- measured live refresh against the HoldSpeak roadmap.

## Implementation direction

- Derived snapshots are rebuildable; durable config, attempts, commands, and
  Receipts are not.
- A manual Refresh invalidates the collector and returns current state; it does
  not block an HTTP request on a fleet of CLIs.
- Cache GitHub separately at a slower cadence and match it to worktree branch/PR
  before projecting a Story receipt.
- Translate current belt/coder frames into delivery invalidations during
  migration, then let the collector own client fan-out.
- Add density guards so `missioncontrol_bridge.py` and the new routes do not
  become monoliths.

## Evidence required

- process-invocation log for 1 versus 10 clients;
- measured cached/refresh latency;
- snapshot examples with live, stale, incompatible, and unavailable sources;
- linked-worktree registry capture;
- compatibility route parity capture.
