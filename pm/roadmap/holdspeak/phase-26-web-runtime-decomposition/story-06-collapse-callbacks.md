# HS-26-06 — Collapse Callback Wiring + Sync-DB-in-Async Audit

- **Project:** holdspeak
- **Phase:** 26
- **Status:** backlog
- **Depends on:** HS-26-02, HS-26-03, HS-26-04, HS-26-05
- **Unblocks:** HS-26-07
- **Owner:** unassigned

## Problem

`MeetingWebServer` takes 40+ callable callbacks in its constructor — hard to
reason about and a drag on testing. Once routes read from the shared context
(HS-26-01..05), most callbacks become redundant. Separately, several async
handlers call sync DB functions (`db.get_meeting`, `db.list_artifacts`) directly,
which can block the event loop / WS broadcast cadence under load.

## Scope

### In

- Replace the callback bag with the shared runtime-context object: route modules
  call context methods instead of injected callbacks.
- Materially reduce `MeetingWebServer`'s constructor parameter count; document
  the new wiring.
- Audit sync DB calls made from async handlers; offload (thread pool / async
  wrapper) only those that demonstrably stall the broadcast loop, and document
  the rest.

### Out

- A full async DB rewrite (explicitly out — targeted offload only).
- Behavior/API changes.

## Acceptance criteria

- [ ] Constructor callback count is materially reduced; remaining params
      justified.
- [ ] Route modules read from the shared context, not injected callbacks.
- [ ] Sync-DB-in-async audit recorded; any offload is covered by a test or a
      documented rationale.
- [ ] Existing web tests pass unchanged.

## Test plan

- Unit: `uv run pytest -q tests/ -k web` — full web suite green; add coverage for
  any handler whose data access was offloaded.
- Integration: WS broadcast cadence unaffected during a meeting (spot-check).
- Manual: n/a.

## Notes / open questions

- Keep this story behavior-preserving like the rest; the win is structure, not
  new features.
