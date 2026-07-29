# HS-109-06 - The process window — what is running

- **Project:** holdspeak
- **Phase:** 109
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-109-07
- **Owner:** unassigned

## The thesis (the bar)

Deferred out of Phase 105, then out of 106, and now honestly cheap:
"what is running" as a pure projection over the kernel the product
already has. `read` accepts a `process` view every codec projects
(`process_spawn.py:136-157`, `process_input.py:116-136`,
`inference.py:161-174`), `events` is cursor-based and filterable
(`journal.py:115-132`), and a new core is one row in `SurfaceWindows`
plus one row in `DESK_TOOLS`.

The bar: **one modest read-only window, `read` + `events` ONLY — no
new syscall, no controls, no invented states.** Article XI clause 5
is the design: watching owes authentication and read authority,
never admission. This is the rider, not a second pillar; it must not
consume a mini-phase of polish.

## Problem

The kernel admits, decides, claims, and receipts — and none of it is
visible as a living surface. An owner who cannot see what is running
cannot feel that the kernel is the OS.

## Recipe

1. **The store.** A small cursor-aware poller: replay
   `/api/kernel/events` from the persisted cursor (batches of ≤500),
   derive the operation set and latest lifecycle event per operation,
   hydrate interesting IDs via `/api/kernel/read?view=process`.
   Short-poll like the existing desk stores (`steering.ts` /
   `deliveryTerminal.ts` pattern); persist the cursor so reopening
   does not re-replay from zero.
2. **The window.** `ProcessCore` in the one grammar: sections
   Needs you / Running / Waiting / Unknown / Recently ended; each row
   shows principal, operation kind, target, placement, age;
   parent/correlation IDs group children under their run with simple
   indentation. Recently-ended retains a bounded tail, then drops.
3. **States are projected, period.** `Waiting`, `Running`, `Ended`,
   `Failed`, `Unknown` exactly as the codec projections report. No
   age heuristic may synthesize a state; pending-forever renders as
   what the journal says (the liveness reaper is BACKLOG candidate Y
   and this window must not fake it).
4. **Needs-you is a link, not a control.** A row awaiting decision
   deep-links to the existing decision surface. This window renders;
   it never approves, kills, or retries.
5. **Registered, not bespoke.** One `SURFACES` row, one `DESK_TOOLS`
   row (Go menu + shelf ride the verb registry automatically), window
   restore for free.
6. **Both densities**, real hub, live operations on screen.

## Out of scope

- Any process control (kill/retry/cancel) — deferred with the reaper.
- A new kernel call, view, or route; any spine or codec change. If
  replay cost demands a server-side active-operations read
  projection, that is a FINDING recorded for the charter, not a
  quiet addition.
- Event-native process grouping (`process_id` is not populated by
  append sites today — group by operation/parent/correlation IDs and
  do not claim more).
- Per-object receipt views (DESK_GRAMMAR §7 remainder).

## Acceptance

- The window renders live kernel operations from `read` + `events`
  only — asserted by test that the store touches no other endpoint.
- Cursor replay proven: cold open replays to current; reopen resumes
  from the persisted cursor; a SIGKILL'd-and-restarted hub yields the
  same rows (byte-equal projection) after replay.
- A real steered run shows parent + child rows grouped; a real
  refusal shows in Recently ended with its named reason; an
  awaiting-decision row deep-links to the decision surface.
- No invented states under test: a synthetic pending-forever
  operation stays `Waiting` regardless of age.
- Screenshot walk at 1440 + 393 with real operations on screen.
- Web suite + build green; full suite green; spine byte-unchanged.

## Test plan

- **Unit (web):** event-fold reducer (lifecycle → sections); grouping
  by parent/correlation; bounded ended-tail; cursor persistence.
- **Integration:** replay against a seeded journal incl. restart;
  endpoint-surface assertion.
- **Live (evidence):** the screenshot walk with a real spawned run,
  a real inference, and a real refusal visible.

## Chef's notes

- The event-fold reducer is the one piece worth real tests — write it
  pure (events in, sections out) so the poller is dumb plumbing.
- Privacy classes ride the events; render refs and bounded heads,
  never payload content — the journal already redacts, do not
  un-redact by fetching more.
- Keep it under a day of work. If it wants to grow controls, filters,
  or charts, that is the rider trying to become a pillar — stop.
