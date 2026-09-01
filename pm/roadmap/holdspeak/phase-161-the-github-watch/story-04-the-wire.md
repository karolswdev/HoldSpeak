# HS-161-04 - The wire: providers on HTTP

- **Project:** holdspeak
- **Phase:** 161
- **Status:** backlog
- **Depends on:** HS-161-03
- **Unblocks:** HS-161-05, HS-161-06
- **Owner:** unassigned

## Problem

§10's provider paths: the face needs connection status, discovery,
and the github proposal flow on the wire, plus evaluate_once for the
walk. The house route law throughout.

## Scope

- **In:** `holdspeak/web/routes/providers.py`:
  GET /api/providers (the manifest list — github + native),
  GET /api/providers/github/connection (the live probe result),
  POST /api/providers/github/connection/recheck,
  GET /api/providers/github/discover?query=&cursor= (bounded),
  POST /api/providers/github/validate-repo ({owner_repo}).
  POST /api/watches/{id}/evaluate (evaluate_once — manual).
  The setup routes carry github proposals through the EXISTING
  suggest/clarify/test/finalize paths (verify additively; extend
  only where the clarify scope step needs the wire). Status law;
  envelope where commands speak it; api-surface regen; integration
  tests incl. the auth-degraded path (a fake-runner unauthenticated
  probe → owner_action_required on the wire).
- **Out:** UI (05), scheduling.

## Acceptance criteria

- [ ] Every route: success + failure paths through the real app; the recheck path re-probes live; discovery pagination on the wire.
- [ ] The full compounding loop through HTTP: connect(fake) → discover → clarify → test → finalize → evaluate → the Delta shows the PR transition (integration).
- [ ] api-surface regenerated + fence green; prior pins untouched.

## Test plan

- **Integration:** `tests/integration/test_provider_routes.py`.

## Notes / open questions

- The evaluate route is manual-only; no cron, no conductor (P5's boundary named in the route docstring).
