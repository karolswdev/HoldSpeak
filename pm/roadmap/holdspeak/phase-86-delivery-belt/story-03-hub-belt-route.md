# HS-86-03 — The hub belt: registry, state route, belt frames

- **Project:** holdspeak
- **Phase:** 86
- **Status:** backlog
- **Depends on:** HS-86-02
- **Unblocks:** HS-86-04
- **Owner:** unassigned

## Problem

The desk needs belt state the way it gets everything else: a pull
snapshot plus frames on the one bus. Nothing in the hub knows about
rails repos today. The AI-Headquarters frame means the shape is a
REGISTRY of repos from the first commit, never "this repo".

## Scope

- In: `belt` config (`belt.projects`: absolute paths; default
  `[<this repo>]`, and the dogfood config adds
  `~/dev/reusable-processes`); a `holdspeak/web/routes/belt.py`
  route factory (`build_belt_router(ctx)`) with
  `GET /api/belt/state` → per-repo: `dw state --json`,
  `dw sessions --json`, `dw events --json` (tail), `dw context`
  issues/warnings counts, shelled from `<repo>/.githooks/dw` via
  `asyncio.to_thread` with a short TTL cache; `gh` receipts for the
  repo's open PRs + head-branch check conclusions (`gh pr list/
  checks --json`, same thread pattern, degrade honestly to
  `gh: unavailable` — never a 500); a repo without `.githooks/dw`
  → `{rails: "absent"}`; `scope:"belt"` frames broadcast on `/ws`
  when a poll observes state change (the `_run_frame` vocabulary:
  `{state, scope:"belt", capability:{kind:"belt", id:<repo-slug>,
  name}}`); a fitness test proving no non-GET route registered under
  `/api/belt`; api-surface manifest regenerated AFTER the web call
  site lands (coordinate with HS-86-04 — regen in whichever commit
  adds the consumer last).
- Out: any mutation (B2); persisting belt state (receipts only —
  cache TTL in seconds); importing `dw_pmo` into the hub; auth
  changes (the existing web-runtime posture applies).

## Acceptance criteria

- [ ] `GET /api/belt/state` returns both registered repos with
      phases/stories/sessions/events and PR/check receipts; the
      response's project shapes are the upstream `feed_schema: 1`
      payloads embedded verbatim (no re-modeling).
- [ ] A registered path without rails answers `rails: "absent"`
      inside a 200 — captured in tests.
- [ ] `gh` unavailable (env-forced in test) degrades to a labeled
      absence, never an error.
- [ ] Route tests via the TestClient + WebContext factory pattern;
      the read-only fitness test passes; api-surface guard green.
- [ ] Full suite green.

## Test plan

- Unit: new `tests/unit/test_web_routes_belt.py` (TestClient;
  subprocess + gh injected/faked via ctx or monkeypatch).
- Integration / Cypress: live route hit against the real two-repo
  registry captured in evidence.
- Manual / device: n/a.

## Notes / open questions

- Poll cadence for frames: reuse the existing broadcast loop seams;
  a 10s single-flight poll matches the upstream workbench belt.
