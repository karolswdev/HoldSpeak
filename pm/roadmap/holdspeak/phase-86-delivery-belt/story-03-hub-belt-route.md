# HS-86-03 — The receipts the conveyor lacks: gh lights + belt frames (hub)

- **Project:** holdspeak
- **Phase:** 86
- **Status:** done
- **Depends on:** HS-86-02
- **Unblocks:** HS-86-04
- **Owner:** unassigned

## Problem

**Re-scoped 2026-07-07 (mid-phase correction):** the survey that
opened this story found Phase 82 already shipped what it planned to
build — `missioncontrol_bridge.py` + `/api/missioncontrol/*` relay
the three contract documents per project-map repo, and the desk
conveyor + approval leg exist. What the RFC's B1 still lacks, hub
side: **PR/CI receipts** (the three documents carry no GitHub state,
so the belt has no PR or check lights) and **belt frames on the one
bus** (the conveyor polls privately at 15 s; no other surface —
iPad, Qlippy — can see belt motion).

## Scope

- In: `receipts_payload(project_map, runner)` in
  `missioncontrol_bridge.py` — per repo, `gh pr list --json
  number,title,url,headRefName,statusCheckRollup` with `cwd=repo`
  (injectable runner; `gh` missing/failing → a typed
  `{"status": "unavailable"}`, never a 500) — and
  `GET /api/missioncontrol/receipts` relaying it. Belt frames,
  emitted on observed change: the state read remembers each repo's
  `generated_at_tree` (module-level, process-lifetime) and, when a
  read observes a different tree, broadcasts
  `{state: "ready", scope: "belt", capability: {kind: "belt",
  id: <repo name>, name: <repo name>}}` on the existing bus (the
  `_run_frame` vocabulary; any poller's read feeds every surface).
  A fitness test proving the belt ADDITIONS register no non-GET
  route. Route tests for receipts + frames (runner injected).
- Out: a hub-side background poller (frames ride reads — decision
  below); any change to the Phase-82 approval leg; evidence file
  serving (HS-86-04 owns it with its consumer); api-surface regen
  (HS-86-04, after the last consumer lands).

## Acceptance criteria

- [ ] `GET /api/missioncontrol/receipts` returns per-repo PR lists
      with check rollups for the live two-repo map; a repo where
      `gh` fails reports `unavailable` inside a 200 (test-forced).
- [ ] Two consecutive state reads with an unchanged tree emit zero
      belt frames; a read observing a changed tree emits exactly one
      frame for that repo, in the pinned vocabulary (broadcast
      captured in tests via ctx).
- [ ] The fitness test enumerates the app's `/api/missioncontrol/*`
      routes added by this story and asserts GET-only.
- [ ] Full suite green.

## Test plan

- Unit: `tests/unit/test_web_routes_missioncontrol.py` extensions
  (TestClient + injected runner + captured broadcast).
- Integration / Cypress: a live receipts hit against the real map,
  captured in evidence.
- Manual / device: n/a.

## Notes / open questions

- Frames-on-read (not a background loop) is deliberate: the conveyor
  already polls at the design's 15 s cadence, so its reads become the
  heartbeat every other surface listens to; zero new lifecycle. If a
  frame-hungry surface ever exists without any poller, B2 revisits.
- Original story text (registry + `/api/belt/state`) superseded: the
  registry IS the operator's project map (`load_project_map`), and
  the state route IS `/api/missioncontrol/state` — both Phase 82.
