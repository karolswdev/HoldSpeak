# HS-160-05 - The wire: the review routes, and /room stops saying absent

- **Project:** holdspeak
- **Phase:** 160
- **Status:** done
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

## What shipped

- `project_reviews.py`: five routes (open/get-window/delta/decide/
  accept) — thin, owner-scoped, the house status law; envelope
  results where the service speaks them. api-surface 594→599.
- /room review section GRADUATED: {state ok, last_accepted_at,
  pending_count, open_review_id} — with an honest conditional: no
  wired delta_service (legacy direct-construction tests) → absent
  stays absent; production sees the real section. Both shapes + the
  WEB-STA-004 delta empty state appended to CONTRACTS-P0.
- THE FULL LOOP through the real app: seed → open (≥3 proposals) →
  frozen window byte-identical → decide accept/dismiss/defer →
  accept → /room pending 0 + cursor visible → reopen: deferred
  suppressed, no duplicates. 17 + regression 30 green; 88 scoped.

## Notes / open questions

- get_delta's empty state shaped + named in CONTRACTS-P0, as chartered.
- Banked: same-kind+target+patch observations collide on the deterministic pprop_ PK within one window — pre-existing service truth (the identity doing its job); fixtures vary fact_json.
