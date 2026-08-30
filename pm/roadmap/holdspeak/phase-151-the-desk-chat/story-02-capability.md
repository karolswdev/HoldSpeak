# HS-151-02 - The capability (chat.turn sealed + assigned)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** done
- **Depends on:** HS-151-01
- **Unblocks:** HS-151-03, HS-151-04
- **Owner:** unassigned

## Problem

Every model call is a sealed capability with an assignment chain
(Phase 143). A thread turn is a new job (`chat.turn`); today's
`recipe.chat` is the localStorage chat's capability and carrying two
chat capabilities is a permanent confusion (counsel S1). The runner
(HS-151-03) builds its route plan from the registered capability, so
this precedes it.

## Scope

### In (D2)

- `_capability("chat.turn", …)` in
  `holdspeak/inference_capabilities.py` (`builtin_capability_definitions`),
  text/streaming, tool-capable flag reserved for DC-02.
- Retire `recipe.chat` from the registry; one additive backfill family
  `chat-route-assignments` in `holdspeak/db/reconcile.py`
  `_apply_data_backfills` that copies the `recipe.chat` chain (else
  the `ask.answer` chain) to `chat.turn` once, idempotently.
- The three Phase 143 generated ledgers + their fail-closed tests
  updated in the same commit (`EXPECTED_CALL_SITES` /
  `PRODUCT_RUNNER_ENTRANCES` rows reserved for `thread_service`).
- Assignments settings lists "Desk chat" (no new UI code).

### Out

The turn service itself (HS-151-04); any UI beyond what the registry
lists.

## Acceptance criteria

- [ ] `InferenceCapabilityRegistry.compose()` seals with `chat.turn`
      and without `recipe.chat`; registry sha changes exactly once.
- [ ] Backfill: a DB with a `recipe.chat` assignment gets an identical
      `chat.turn` chain; a DB without gets the Ask chain; running twice
      is a no-op.
- [ ] All three census tests green with the regenerated `.md` ledgers.
- [ ] `RecipeService.chat` callers re-pointed or removed so no caller
      references the retired id (census fail-closed proves it).

## Test plan

- **Unit:** `tests/unit/test_phase143_*census.py` (×3),
  `tests/unit/test_inference_capabilities.py` (or the existing
  registry test), a new backfill test in `tests/unit/test_db.py`.
- **Integration:** n/a.
- **Manual / device:** n/a.

## Notes / open questions

`/api/recipes/{id}/chat` aliasing lands in HS-151-04, so this story may
leave the route temporarily pointing at a 410 stub with a named reason.
