# HS-65-01 — Pre-flight: every route loads clean

- **Project:** holdspeak
- **Phase:** 65
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-65-02, HS-65-04
- **Owner:** unassigned

## Problem
Only dogfooded pages ever had a zero-page-error assertion; a SyntaxError
shipped on /welcome for ~19 phases (the Phase-62 find). Strangers are
about to install this.

## Scope
- **In:** `tests/e2e/test_route_preflight.py`: boot the real server,
  load EVERY page route in Chromium, assert zero uncaught page errors
  per route; `importorskip` playwright + skip cleanly when browsers are
  absent (CI has none); run locally for the evidence; fix what it finds.
- **Out:** per-page behavior tests (exists elsewhere).

## Acceptance criteria
- [x] The sweep covers every route in the built app (enumerated, not
      hand-listed where possible).
- [x] Local run green (or finds fixed + rerun green); CI skip-clean.
- [x] Full suite green.

      See `evidence-story-01.md`.

## Test plan
- The sweep itself + the full suite.
