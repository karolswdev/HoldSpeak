# HS-160-05 - The wire: the review routes, and /room stops saying absent

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-160-04
- **Unblocks:** HS-160-06, HS-160-07
- **Owner:** unassigned

## Problem

The face and the walk need the wire: open/read/decide/accept over
HTTP with the command contract, and the /room projection's `review`
section graduating from `absent` to the real pending-count +
proposals summary (§6.2's review block; the §15 snapshot shape).

## Scope

- **In:** routes (module per the house pattern):
  `POST /api/projects/{id}/reviews` (open_review),
  `GET /api/projects/{id}/reviews/{review_id}` (the frozen window),
  `GET /api/projects/{id}/delta` (current open window or the
  no-open-review honest state),
  `POST .../proposals/{pid}/decide` ({verb, patch?, deferred_until?}),
  `POST .../reviews/{review_id}/accept`. Command params + envelope
  results + the status law (404/400/409 per the house convention).
  `/room`: the `review` section becomes
  {state:'ok', last_accepted_at, pending_count, open_review_id} —
  CONTRACTS-P0's section vocabulary honored (absent only when the
  domain truly has nothing... it EXISTS now, so ok with zeros —
  Art VI honesty the other direction: zeros are zeros, not absence).
  api-surface regen. Integration tests through the real app: the
  full loop (collect → open → decide ×N → accept → cursor visible
  in /room) + failure paths.
- **Out:** the face (06), MCP (P6).

## Acceptance criteria

- [ ] Every route: success + failure tests; the full loop through the real app; envelope + status law consistent with 158/159.
- [ ] /room review section real; CONTRACTS-P0.md amended (the review-section shape) in the same commit — names before use.
- [ ] api-surface regenerated + fence green; 157-159 pins untouched-green (additive only).

## Test plan

- **Integration:** `tests/integration/test_review_routes.py`.

## Notes / open questions

- get_delta with no open review returns the honest empty state WEB-STA-004 will render — shape it now, name it in CONTRACTS-P0.
