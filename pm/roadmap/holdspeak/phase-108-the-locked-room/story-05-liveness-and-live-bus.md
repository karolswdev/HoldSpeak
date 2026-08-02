# HS-108-05 - Silence ends, and CI watches

- **Project:** holdspeak
- **Phase:** 108
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-108-07
- **Owner:** unassigned

## The thesis

An executor may disappear, but an operation may not remain ambiguous
forever. A browser proof may have local prerequisites, but hosted CI may
not silently skip it.

## Recipe

1. Give every operation spec a claim TTL and execution TTL.
2. Sign both deadlines into the warrant.
3. Add one generic, revision-guarded reaper:
   - awaiting execution past claim TTL -> named refusal;
   - claimed past execution TTL -> indeterminate.
4. Revoke the warrant and write an immutable terminal receipt.
5. Run recovery at web startup and once per second.
6. Put Playwright in the test extra; build the production web bundle and
   install Chromium in CI.
7. Make `HOLDSPEAK_REQUIRE_LIVE_BUS=1` convert missing prerequisites into
   a hard failure and run that gate separately.

## Acceptance

- Late receipts cannot change the reaper's terminal fact.
- Reaping is operation-type agnostic.
- The CI workflow itself is pinned by a unit test.
- The live-bus file runs 3/3 with the production bundle and Chromium.

## Test plan

Kernel broker liveness tests, CI workflow guard, and mandatory live-bus E2E.
