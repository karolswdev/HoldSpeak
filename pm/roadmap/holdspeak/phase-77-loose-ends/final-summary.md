# Phase 77 — Loose Ends: final summary

- **Closed:** 2026-07-02 — **4/4 stories**, open-to-close same day.
- **Branch:** `phase-77-loose-ends` (merged to `main` by PR).
- **Why:** the three follow-ups Phase 72 filed and could not absorb,
  owner-picked while testing is unavailable.

## What shipped

1. **The agent's pinned context survives the hub** (schema v7): the
   iPad-authored `manual_context`/`use_zone_context` persist on every hub
   layer and round-trip byte-faithful through sync — the exact loss
   HS-72-01 documented is now a passing test, and the Swift
   tolerant-decode heals with zero functional change (its design bet).
2. **The Queue HUD renders truth**: the deferred-intel queue broadcasts a
   real `runtime_queue` frame (listable jobs, titles, attempts, summary)
   on every transition; the HUD consumes it as the primary source, with
   departing rows resolving through the ledger's own linger grammar.
3. **The coders-status conflation is dead**: consumers verified first
   (the block was a dead contract), the connector flags moved to their
   own domain (`GET /api/desk/actuators/status`, booleans only, the
   credential rule kept), and `/api/coders/status` speaks only of coder
   sessions.
4. **Docs**: verified silent — no entry point spoke of the changed
   surfaces (AGENT_HOOK_INSTALL's expected shape never included the
   block); the new route's docstring records the history; the manifest
   regenerated at each step.

## The numbers

- Suite: **3095 passed, 37 skipped** at close (3088 at open + 7 new);
  Swift suite green; every fired guard (the canonical snapshot, the
  AGENT_KEYS pin, three migrated integration tests) updated honestly.

## For the future

- Schema is at **v7**. Both v6-facsimile and v5-facsimile upgrade paths
  are locked by tests with the pre-migration backup asserted.
- The HUD's linger grammar is a design contract: resolved jobs SHOW their
  resolution briefly — reconcilers must mark done + prune, never delete
  silently (the proof run caught exactly that).
