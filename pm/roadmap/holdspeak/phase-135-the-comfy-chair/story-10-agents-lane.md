# HS-135-10 — The Agents lane

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** HS-135-05
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

What's running and what's asking, fourth lane: sessions blocked-first
with the Answer verb one tap away — the steering deck's front porch.

## Scope

### In

- The lane composes the Agents/companion surface: crew/session/blocked
  counts, sessions blocked-first (the existing sort), each with its
  state badge and — for blocked sessions — the Answer verb opening the
  session window (single-instance); recent agent receipts (who did
  what) to the curated bound where the surface exposes them;
  header-click opens the Agents window.

### Out

- New steering verbs; delivery/PR surfaces (their windows exist);
  agent identity redesign.

## Acceptance criteria

- [x] Seeded blocked session renders first with Answer; the verb
  opens the session window (test).
- [x] Counts truthful; empty state honest ("No sessions" with the
  verbs that exist).

## Test plan

- `cd web && npx vitest run` — new lane suite + companion suites
  touched.
