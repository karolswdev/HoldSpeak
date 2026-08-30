# HS-150-01 — The owner gesture (aliases + resolution + delegated_at)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-150-02, HS-150-03, HS-150-06
- **Owner:** unassigned

## Problem

Owner strings are free text with no lawful path to a person
(census plane 1: five write paths, zero links, inference
forbidden), and delegation records WHO but never WHEN (no
delegated_at anywhere).

## Scope

### In (settled-design D1)

- `owner_aliases: [<string>…]` in the relationship's ENCRYPTED
  payload; `link_owner_alias` / `unlink_owner_alias` /
  `resolve_relationship_by_owner` (readiness-guarded, the
  by-series clone; case-insensitive in-memory compare, never
  logged/persisted as comparison); invariant P2
  (`owner_alias_taken` naming the holder); reserved strings
  "Me"/"Remote"/"you" refused by name; HTTP + MCP through the
  People family's exact gate patterns.
- `delegated_at` on action_items (bare timestamp — the schema grep
  pin stays green): set on the delegate verb and wherever the
  owner string CHANGES; **counsel finding 4 is law**: the intel
  upsert (meetings.py:415) gains a VALUE-CHANGE CASE guard so
  re-extraction never churns owner or delegated_at (mirror the
  status/review_state guard pattern beside it); edit_action_item
  compares old vs new before stamping; commit_decision INSERTs
  fresh (true stamp). Backfill NOT attempted (honest null). A
  deliberate test: re-run intel upsert with the SAME owner →
  delegated_at untouched; with a CHANGED owner → stamped.
- Tests through the 149 seam: alias roundtrip, P2, reserved
  refusals, guarded resolution, delegated_at on every owner-write
  path, the schema pin extended.

### Out

- All UI (02); the brief (03); any plaintext person reference.

## Acceptance criteria

1. Alias → resolve roundtrip (headless); P2 refusal named; unalias
   restores none; reserved strings refuse.
2. Locked sidecar → resolution "unavailable", never no-match.
3. Every owner-string write path stamps delegated_at when the
   owner changes; unchanged owner leaves it untouched.
4. The schema grep pin green with delegated_at present.

## Test plan

people_service + follow_through/meetings owner-write focused
suites + new tests; the seam env; the pin.
