# HS-26-06 — Collapse Callback Wiring + Sync-DB-in-Async Audit

- **Project:** holdspeak
- **Phase:** 26
- **Status:** done
- **Depends on:** HS-26-02, HS-26-03, HS-26-04, HS-26-05
- **Unblocks:** HS-26-07
- **Owner:** Claude (agent)

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

- [x] Constructor callback count is materially reduced; remaining params
      justified. (30 → 4 via `WebRuntimeCallbacks` bundle.)
- [x] Route modules read from the shared context, not injected callbacks. (And
      now import nothing from `web_server` — shared helpers re-homed to
      `web/runtime_support`.)
- [x] Sync-DB-in-async audit recorded; any offload is covered by a test or a
      documented rationale. (See `audit-sync-db-async.md` — no offload, with
      documented rationale + re-visit trigger.)
- [x] Existing web tests pass unchanged. (Full suite green, 1879.)

## Test plan

- Unit: `uv run pytest -q tests/ -k web` — full web suite green; add coverage for
  any handler whose data access was offloaded.
- Integration: WS broadcast cadence unaffected during a meeting (spot-check).
- Manual: n/a.

## Notes / open questions

- Keep this story behavior-preserving like the rest; the win is structure, not
  new features.
- **Scope decision (user):** the literal AC1 (collapse the constructor) was kept
  over the lighter "keep constructor, document it" option — `WebRuntimeCallbacks`
  bundle + codemod of all 69 construction sites. The `__init__` re-explodes the
  bundle onto `self.*` so `_create_app` / device-WS wiring stay untouched.
- The 3 cross-cutting helpers were re-homed to `web/runtime_support` so no
  `routes/*` module imports `web_server`. See `evidence-story-06.md`.
