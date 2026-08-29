# HS-149-02 — The link (encrypted series link + resolution)

- **Project:** holdspeak
- **Phase:** 149
- **Status:** done
- **Depends on:** HS-149-01
- **Unblocks:** HS-149-03, HS-149-04, HS-149-06
- **Owner:** unassigned

## Problem

No code path connects a person to a calendar series (census plane
3a: exhaustive-grep DOES NOT EXIST). The keystone gap.

## Scope

### In (settled-design D2)

- `calendar_links: [{uid, source_id, label}]` in the relationship
  ENCRYPTED payload (additive; no migration).
- Service: `link_calendar_series` / `unlink_calendar_series` /
  `resolve_relationship_by_series(uid, source_id)`; invariant P1 —
  a series linked elsewhere refuses `series_already_linked` naming
  the holder; idempotent self-relink; resolution is
  readiness-guarded ("unavailable" ≠ no-match, D1 honesty).
- HTTP routes under /api/people + MCP family tools
  (people.calendar.link/unlink; resolution rides the existing
  detail/grounding reads).
- The stored link records the owner-selected evidence (the event
  title at link time) per the INTEGRATION contract.

### Out

- All UI (03); any plaintext-DB column (FORBIDDEN — resolution is
  read-time only, the 138 law).

## Acceptance criteria

1. Link → resolve roundtrip through the encrypted store (headless
   via the 01 seam); P1 refusal named; unlink restores
   resolvability to none.
2. Locked sidecar → resolution says "unavailable", never empty.
3. Zero new person-referencing columns anywhere in schema.py
   (grep pin in tests).

## Test plan

people_service focused suites (link/resolve/P1/unlink/guarded
resolution), route + MCP tests, the schema grep pin.
