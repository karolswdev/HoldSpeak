# Evidence - HS-200-10

- **Story:** HS-200-10 - Promote reusable working context into canonical records
- **Status:** done
- **Date:** 2026-09-09

## Proof

### Captured run — 2026-09-09T13:45:15Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4v1Plhxfn6 uv run pytest -q tests/unit/test_phase200_working_context.py tests/unit/test_db.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d90f032f8b62990ab42edfacc119deece5c9d279

```text
........................................................................ [ 67%]
..................................                                       [100%]
106 passed in 31.14s
```

### Captured run — 2026-09-09T13:46:55Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.rEQputdzTA uv run pytest -q tests/unit/test_phase200_working_context_index.py tests/unit/test_phase200_working_context_l4_origin.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d90f032f8b62990ab42edfacc119deece5c9d279

```text
............................................                             [100%]
44 passed in 21.76s
```

### Captured run — 2026-09-09T13:47:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.yB7SHGTKPl uv run pytest -q tests/integration/test_phase200_working_context.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d90f032f8b62990ab42edfacc119deece5c9d279

```text
.........................                                                [100%]
25 passed in 7.76s
```

### Captured run — 2026-09-09T13:47:31Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.5L3cwLSXUY uv run pytest -q tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_api_surface.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d90f032f8b62990ab42edfacc119deece5c9d279

```text
.......................                                                  [100%]
23 passed in 24.71s
```

## The full CI-shape suite

The clean run that was owed since 2026-09-08 (when 274 e2e failures turned out to
be pure CPU starvation beside the owner's live walk and had to be thrown away):

```
HOME_REAL=$HOME; HOME=$(mktemp -d) \
  PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright \
  npm_config_cache=$HOME_REAL/.npm \
  uv run pytest -q --ignore=tests/e2e/test_metal.py -n auto -rf

10 failed, 10742 passed, 98 skipped in 1725.45s (0:28:45)
```

**Every one of the ten is e2e glass, and none of them is this branch's.** Seven
pass on a serial re-run — CPU starvation under `-n auto`, the known rig family.
The remaining three were checked against `main` rather than assumed: a worktree at
`2481d328`, with `holdspeak.__file__` verified to resolve INTO the worktree before
any result was trusted (the naive `uv run` there silently picks up a system
Python 3.14 and skips everything, which reads as a pass).

| Test | Serial | On `main` @ `2481d328` |
|---|---|---|
| `test_hs153_practice_glass::test_guardrail_row_renders_and_deny_focused` | fails | **fails identically** |
| `test_hs171_command_deck_glass::test_command_deck_projects_1440` | fails | **fails identically** |
| `test_hs171_command_deck_glass::test_command_deck_projects_393` | fails | **fails identically** |

Same assertion on main, down to the message (`Gamma (0 items) should have no
badge — assert 1 == 0`). **Inherited, not branch-new. This branch adds no failure
to the suite.**

An earlier full run of the same tree showed four census failures. Three were
inherited from `main` — the HS-200-05 MLX fix (`6716dc10`, merged as #569) moved
six `transcribe.py` call sites by ~50 lines and never re-registered them, and
`dbb86ce6` never touched that file. The fourth was ours: 200-10's sync work moved
two `sync_service.py` `profile_id` sites from `:687`/`:702` to `:844`/`:859`. All
four fixtures are re-registered here and all 18 census tests pass above.

**Suite hygiene defect, found and worked around, NOT fixed.** A full run rewrites
**388 tracked evidence PNGs** from phases 141-176 plus seven JSON/markdown assets
from 162-170 — other phases' shipped proof, modified as a side effect of running
tests. Both runs this sitting were followed by a restore pass before staging.
Without one, a commit silently rewrites other phases' evidence. Ledgered for its
own fix.

## Counsel-on-built (2026-09-09)

Two counsel Fedaykin, one on the boundary and the retrieval routes, one on the
verb, the reverse index, sync and the consumers. **Both: RATIFY-WITH-CONDITIONS.**
Their findings, the rulings on them, and what changed are recorded in
[story-10](story-10-scoped-working-context.md) under "Counsel-on-built
(2026-09-09)" and in rulings B2, B3 and B4.

The central claim survived the hunt: the boundary lane enumerated every path that
reads a note body and found **no undisclosed route**. Two P0s were found, both in
the lane the design had reasoned about least, and both are fixed here:

- **P0-1** — L4's replay fence keyed on a REMOTE wall clock against a LOCAL one,
  so on a device that had not yet synced, a relevance-frozen body read as
  "arrived by reference" forever. Fixed by recording the ORIGIN on `thread_refs`
  and consulting no clock at all. **Reproduced against the pre-fix code on the
  real cross-device path before the fix was trusted**, in both directions — the
  leak, and the silent loss of a by-reference attach when the promotion clock
  landed later than the attach.
- **P0-2** — `revoke_promotion` overwrote `unavailable` with `stale`, sending a
  consumer to refresh a record that is gone. Fixed; both marks are preserved.

Two latent fail-open seams are closed (the backfill's per-consumer `SAVEPOINT`,
which also closed a NON-latent defect — a swallowed exception left a transaction
open on the connection reconcile was still using, so step 4's `BEGIN` would raise
and the desk could not open; and `_drop_promoted`, which returned members
unfenced for a handle lacking `promoted_refs`). AC4 is exercisable for the first
time: `promotions()` had no route and no tool, so no `promotion_id` could be
obtained and nothing could be revoked.

## What is NOT closed, stated here so it is not discovered later

1. **A model in an ordinary Thread reads a promoted body with one `desk.list`
   call.** Ruling B4. F0 fences RELEVANCE and reduces no part of that exposure.
   Disclosed at file:line in the settled design, pinned positively by
   `test_desk_snapshot_and_sync_pull_still_carry_the_body`, and now stated in the
   story file rather than only in an asset.
2. **Detach then re-attach clears a standing `forbidden`.** Ruling B2, corrected:
   the earlier claim that a consumer is "fenced forever by every route" was FALSE.
   Pinned by `test_a_detach_then_reattach_currently_clears_a_standing_forbidden`.
   Not closed on this commit — the fix collides with the ratified P0-2 test, and
   `context_dependents` is write-only today, so nothing fences on it yet.
3. **The lattice is unproven against a real consumer.** Stories 11, 13, 17 and 20
   land the first one.
4. Below-P0, carried and not fixed: `context_promotion_suppressions` does not
   sync, so a re-promotion on a second device reports success while the row stays
   revoked; `disclosure_state` is unvalidated on merge; the sync pull windows can
   diverge above ~50 promotions (the owner has 0); completed Thoughts keep index
   rows; and the `create(seed_refs=)` route passes web-sent dicts through
   unvalidated so `freeze_refs` writes a stringified dict into `ref_id` — that one
   PREDATES this story and belongs to the route lane.

## The law, applied on purpose

`reference_lying_test_doubles` earned its place again. Every fix above was written
test-first and watched FAIL against the shipped code; every new fence was mutated
out and watched go red. **Two mutants SURVIVED and were reported rather than
banked as green** — one lane found its belt was dead code and deleted it, another
found a stamp no leak test could ever reach and wrote a test that says in its own
docstring that it guards a receipt, not a fence. And one of this story's own
existing tests was proven blind: re-run against the deletion of the very predicate
it claimed to guard, `test_the_backfill_never_clears_a_forbidden_mark` stayed
GREEN. It now drives the real backfill.
