# Counsel on built — HS-200-17 (three executable recipe contracts)

- **Reviewer:** Fedaykin (counsel-on-built), 2026-09-18
- **Tree:** `/private/tmp/muaddib-xxiii/wt17`, branch `feat/hs-200-17`, uncommitted over main `ba48baf3`
- **Verdict:** **BOUNCE** — one P0 (a false coverage state on the wire), plus two P1s and five P2s.

## What I ran

```
$ HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_recipe_catalog.py \
      tests/integration/test_phase200_recipe_catalog.py -rf
97 passed in 4.92s

$ HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_doc_claims.py \
      tests/unit/test_thread_tool_gate.py tests/unit/test_api_surface.py \
      tests/unit/test_phase200_one_composition_root.py tests/unit/test_thread_tool_loop.py -rf
102 passed in 18.59s

$ HOME=$(mktemp -d) uv run pytest -q tests/unit/test_doc_drift_guard.py \
      tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_thread_modes.py -rf
71 passed in 10.54s

$ .githooks/dw check holdspeak
(6 ERROR lines, all pre-existing: phase-101 evidence, four missing final-summary.md,
 CLAUDE.md managed-block drift. None name phase-200 or story 17.)
```

## Mutation probes — do the fences actually go red?

I mutated the catalog in-process (no file edits) and re-ran each fence:

```
RED   M1 flip weekly_update scheduled trigger available=True -> unit fence red, doc-claim predicate False
RED   M2 rename a qualified_ref -> resolve_step raises, doc-claim predicate False
RED   M3 point MAX_PRIORITIES at a bogus constant -> CatalogError
RED   M4 raise the decision limit to 9999 -> "inside the service cap" fence red
GREEN M5 set weekly_update max_claims to 1 -> NO fence noticed
RED   M6 add practice_recipe.list to CHAT_PALETTE -> palette fence red
```

Five of six fences are real. M5 is finding P1-1.

## Findings

### P0-1 — `observed_coverage` reports `available` for a watch that cannot be checked

`holdspeak/services/recipe_catalog.py:969-1000` derives the `watch` coverage
state from `connector_watches` by hand and diverges three ways from the C4
producer it claims to reuse (`holdspeak/services/needs_you_aggregate.py:616-657`):

| situation | C4 producer (`_watch_coverage`) | `observed_coverage` (measured) |
|---|---|---|
| never checked (`last_success_at` NULL) | `unavailable`, reason "never checked" | `stale` |
| checked once, long ago | `stale` past `DEFAULT_SOURCE_STALE_AFTER_S` (6h) | `available` |
| `state='cant_check'` | `failed` | **`available`** |

Measured on a real `Database` (probe script, not a double):

```
watch last read 2024-01-01 -> available
watch NEVER read            -> stale
watch cant_check            -> available
```

The third row is the P0: `practice_recipe.compile` and
`GET /api/automations/practice-recipes/{id}/plan` return
`"kind": "watch", "state": "available"` for a source the product already knows
it cannot read. That is a fake all-clear in the C4 vocabulary the descriptor
borrows, it falsifies this story's own docstring ("a source with nothing behind
it is `unavailable`, never `available`",
`holdspeak/services/recipe_catalog.py:44-48`), and it falsifies the sentence
this story added to a user-facing doc: "it never reports an all-clear it did not
observe" (`docs/USER_GUIDE.md:998-999`).

The fence agrees with the code rather than the producer:
`tests/integration/test_phase200_recipe_catalog.py:170-176`
(`test_an_unread_watch_is_stale_not_available`) asserts the divergent mapping
and there is no test at all for `cant_check` or for an aged `last_success_at`.
This is the `reference_lying_test_doubles` family: the fixture was minted by
hand rather than through the producer, and the assertion was written against the
new code's behaviour instead of the shipped validator's constants.

Blast radius, stated honestly: `watch` is an *optional* source in both
descriptors that declare it, so no plan's `ready` flag is wrong today. What is
wrong is the row the wire returns and the doc sentence that describes it.

**Fix in one line:** derive `watch` (and the other kinds) through the shipped
C4 mapping — `cant_check` → `failed`, paused/never-checked → `unavailable`,
`last_success_at` older than `DEFAULT_SOURCE_STALE_AFTER_S` → `stale` — and
change the fence to assert against that constant, with a `cant_check` case.

### P1-1 — `weekly_update`'s `max_claims: 40` is an invented number no code enforces

`holdspeak/services/recipe_catalog.py:563-569` declares
`Limit("max_claims", "literal:40", "Claims carried into one update draft before
the section is truncated.")`.

- `ProjectUpdateService` contains no claim cap, no constant, and no truncation
  at any value (`grep -n "\b40\b" holdspeak/services/project_update_service.py`
  returns nothing; its module constants are all string tokens).
- `max_claims` is bound to no step: `draft_update` binds only
  `("project_id", "generator")`, so `call_arguments` never passes it.
- No test can see it — probe M5 above changed it to `1` and every fence stayed
  green. The only other occurrence in the repo is the evidence file.

So the `why` sentence describes behaviour the product does not have, and three
canon texts assert the opposite of what the code does: the module docstring
("every limit is read off the **real constant** the executing service enforces
rather than transcribed here", `recipe_catalog.py:19-22`), the phase status line
("every limit is read off the constant the executing service enforces rather
than transcribed", `current-phase-status.md:92`), and the same sentence in
`pm/roadmap/holdspeak/README.md`. `decision_review`'s `literal:200` is a
legitimate caller choice (it is really bound and really clamped), but its `why`
transcribes the service's inline `500` too.

### P1-2 — `decision_review` declares an input the plan cannot honour

`recipe_catalog.py:410-413` declares
`InputField("interval_days", "integer", False, "How far back the review looks,
in days.", default=7)`. No step binds it (`("project_id",)`, `("limit",)`,
`("project_id",)`), and neither `FollowThroughService.board`
(`follow_through_service.py:128-135`) nor `DecisionRecordService.list_records`
(`decision_record_service.py:479-491`) takes a time window at all. A caller
reading the descriptor — which is the entire point of a descriptor — will
believe the review window is configurable. Nothing fences an orphaned input.

### P2 findings

1. **The schedule doc-claim predicate is self-referential.**
   `tests/unit/doc_claims/registry.py:660-700` proves the descriptors *declare*
   `available=False`; it does not prove that no sweep step invokes a prepared
   recipe. Its own `truth` text promises "When HS-200-21/33/35 adds a sweep
   step, this predicate goes False", which is only true if that builder also
   remembers to flip the flag. Add a direct check (e.g. `recipe_catalog` is not
   imported by `heartbeat_service` / the sweep modules).
2. **`UnknownRecipe` is not a `ServiceError`,** so over MCP it falls through to
   the generic handler in `holdspeak/mcp/server.py:429` and the caller gets a
   message with no `code`, unlike the HTTP route's `{"code": "unknown_recipe"}`.
   Verified by probe; untested either way.
3. **The HTTP plan route catches only `UnknownRecipe`**
   (`holdspeak/web/routes/automations.py:151-155`). A `CatalogError` — a limit
   constant that vanished, a coverage state outside C4 — becomes a 500 rather
   than a typed answer. Unreachable today; unfenced.
4. **Two fences read source text,** not behaviour:
   `test_the_sweep_is_driven_by_a_wall_clock_loop_not_a_manual_call` and
   `test_the_named_owner_really_has_a_recurring_driver` assert substrings such
   as `"sweep_interval" in driver`. A reformat breaks them; a gutted loop would
   not.
5. **`observed_coverage` counts completed commitments as coverage** — the
   `action_items` join filters on no `status`, so a project whose every item is
   done still reports `commitment: available`.

## What I verified as sound

- **All six qualified refs resolve to the real methods named**, with the right
  parameters: `PreparationBriefService.prepare` / `.preview_manifest`,
  `FollowThroughService.board`, `DecisionRecordService.list_records`,
  `ProjectUpdateService.draft_update`. `resolve_step` checks the bound names
  against `inspect.signature`, and probe M2 shows a renamed ref goes red.
- **The preparation limits really do import** `MAX_PRIORITIES` /
  `MAX_QUESTIONS` / `MAX_OBLIGATIONS` from
  `preparation_brief_service.py:73-75`; probe M3 shows a broken source raises.
- **Claim 5 (the honesty claim) holds.** All three descriptors carry
  `TriggerBinding(TRIGGER_SCHEDULED, "HeartbeatService", available=False, …)`,
  compiling under `scheduled` always yields exactly one
  `trigger_owner_not_wired` gap and `ready == False`, and probe M1 shows both
  the unit fence and the doc-claim predicate go red the moment a descriptor
  claims otherwise. More importantly, **nothing in the change executes
  anything**: there is no run path at all (the only consumers of
  `recipe_catalog` are three read-only MCP tools and three GET routes), so no
  code here can report a scheduled — or any — run as having happened. The cited
  negative evidence checks out too: `project.steward.trigger` still raises
  `scheduler_not_wired` (`holdspeak/mcp/families/project.py:1675-1688`), and the
  heartbeat conductor really is the wall-clock loop that calls `run_sweep`
  (`holdspeak/runtime/heartbeat.py:127-141`).
- **Claim 6 holds.** `tests/integration/test_phase200_recipe_catalog.py` builds
  a real `Database` with a real project, meeting, decision, commitment, watch
  and project items, and calls the resolved function objects on real service
  instances — a real brief row, a real board, real decision records, a real
  update draft with real claim kinds from `CLAIM_KINDS`/`SUPPORT_STATES`. No
  service-side doubles. The scheduled leg is proven only as "compiles to a
  byte-identical call", which the test says in those words.
- **Claim 3 holds.** `gap()` refuses a blank `missing` or `supplied_by` and a
  state outside `COVERAGE_STATES`, at the constructor, fenced both ways.
- **Claim 7 holds.** `practice_recipe.*` is classified in `_TOOL_CLASSES` but
  absent from `CHAT_PALETTE` (probe M6 red on widening), excluded from the
  thread palettes at `thread_modes.py:39-45`, and the family reaches the
  database only through `db_or(get_database)` — the same pattern as
  `inference_assignments.py:117` and `sequence.py:94`; the shipped AST guard
  (`test_phase200_one_composition_root`) passes.
- **The evidence file is honest**, including a captured run that failed the
  em-dash doc guard and the corrected re-run.

## Conditions to clear the bounce

1. Derive every kind in `observed_coverage` through the shipped C4 mapping so a
   `cant_check` watch reports `failed`, a never-checked one `unavailable`, and
   an aged one `stale` past `DEFAULT_SOURCE_STALE_AFTER_S`.
2. Replace `test_an_unread_watch_is_stale_not_available` with a fence asserted
   against `needs_you_aggregate`'s own constants, adding a `cant_check` case.
3. Delete the `max_claims` limit, or bind it to a real cap in
   `ProjectUpdateService` and fence it — and correct its `why` either way.
4. Correct the "every limit is read off the constant the executing service
   enforces" sentence in the module docstring, `current-phase-status.md` and
   `pm/roadmap/holdspeak/README.md` to match the `literal:` carve-out the code
   actually uses.
5. Remove `interval_days` from `decision_review`, or bind it to a step that
   consumes it; add a fence that every declared input is bound by some step or
   explicitly marked unbound.
6. Strengthen `_no_prepared_recipe_has_a_wired_schedule` to assert that no sweep
   module imports `recipe_catalog`, so the predicate fails on the real event it
   describes.

---

## Re-read (2026-09-18, after the payment)

- **Reviewer:** Fedaykin (counsel-on-built, re-read), same tree, still uncommitted over `ba48baf3`
- **Verdict:** **RATIFY-WITH-CONDITIONS** (3, all documentary/test-hygiene). The P0 is
  genuinely paid, by delegation, and the delegation survives the attack.

### What I ran

```
$ HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_recipe_catalog.py \
      tests/integration/test_phase200_recipe_catalog.py -rf
114 passed in 6.05s

$ HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_doc_claims.py \
      tests/unit/test_api_surface.py tests/unit/test_thread_tool_gate.py \
      tests/unit/test_phase200_one_composition_root.py \
      tests/unit/test_doc_drift_guard.py tests/unit/test_mcp_sidecar_doc_drift.py \
      tests/unit/test_thread_modes.py -rf
164 passed in 21.33s

# the shared producer's own callers, after it grew a third
$ HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_attention_coverage.py \
      tests/unit/test_phase200_attention.py tests/unit/test_hs171_aggregate_notify.py \
      tests/unit/test_hs172_loop_wire.py tests/unit/test_hs171_heartbeat_wire.py \
      tests/unit/test_phase200_continuity.py \
      tests/integration/test_phase200_attention_coverage.py -rf
189 passed in 18.84s
```

### 1. The delegation is real, and I could not break it

`observed_coverage` (`holdspeak/services/recipe_catalog.py:1067-1144`) derives
**no** state from a table. Watch, meeting and commitment come from
`needs_you_aggregate.room_coverage` (`needs_you_aggregate.py:587-610`) reduced
by `worst_state`; `project` is assembled from the two seams the aggregate
itself uses (`_classify_read_failure`, `list_projects`) and nothing else.

The producer's two original call sites genuinely route through the new seam —
not a copy: `needs_you_aggregate.py:446-449` and `:500-502` each replaced a
`_section_coverage` + `_watch_coverage` pair with one `room_coverage(...)`
call, arguments and order unchanged. `room_coverage` is a two-line fan-out
over the same two privates. 189 aggregate-side tests pass unchanged.

`worst_state` cannot read better than its sources: `_WORST_FIRST` is
worst-first over the five `COVERAGE_STATES` and `[]` returns `unavailable`.
The fence iterates `COVERAGE_STATES` itself
(`tests/integration/test_phase200_recipe_catalog.py:318-325`), so a state
missing from the ordering goes red rather than silently falling through.

**I hunted for a surviving disagreement and found none in the dangerous
direction.** By construction the non-project kinds are the producer's own
rows; the early returns (Room raises, Project not listed) leave the other
kinds at the `unavailable` default, never `available`. For `project`, the
catalog says `available` under exactly the aggregate's condition (named by
`list_projects` **and** `needsYou.state == "ok"`). The only divergence left is
conservative and is P2-1 below.

### 2. The "pre-existing producer timezone bug" is NOT real — the claim is wrong

I checked it independently and it does not reproduce through the production
chain. Both writers of `last_success_at` use SQLite `datetime('now')`, i.e.
**naive UTC** (`holdspeak/db/automations.py:168`,
`holdspeak/services/watch_service.py:875` — those are the only two writers in
the tree). `aware_iso` then labels a naive value UTC, which is correct by
construction (`holdspeak/services/project_service.py:104-121`), and
`_older_than` converts the aware stamp to local *and* the horizon is already
local naive (`build_aggregate` passes `datetime.now()`), so both sides land on
one clock. Measured on the real chain, a watch read seconds ago is
`available` in every timezone:

```
TZ=UTC                  stored 2026-09-18 23:33:36  -> available
TZ=America/Los_Angeles  stored 2026-09-18 23:33:36  -> available
TZ=Pacific/Midway       stored 2026-09-18 23:33:37  -> available
TZ=Pacific/Kiritimati   stored 2026-09-18 23:33:37  -> available
TZ=Europe/Warsaw        stored 2026-09-18 23:33:37  -> available
```

What actually happens is the reverse of the claim: the **fixture** in
`test_a_watch_read_moments_ago_is_available`
(`tests/integration/test_phase200_recipe_catalog.py:275-278`) seeds
`datetime.now()` — a **local**-naive stamp, which no production writer ever
produces — and `aware_iso` correctly-but-wrongly reads it as UTC. The `TZ=UTC`
pin is compensating for the test's own non-production stamp, not for a
producer defect. It hides nothing about the story's contract (the
catalog-equals-producer assertion holds in every timezone), but the docstring
at `:245-259` states a product defect that does not exist, and that statement
was carried to the orchestrator as a disclosed pre-existing bug. Leaving the
*producer* unfixed is right — there is nothing to fix. The docstring is the
thing to fix. **(P1-A below. Do not charter a story off it.)**

Running the catalog tests under extreme offsets did find one genuinely
TZ-fragile fence, a different one:

```
TZ=Pacific/Midway       114 passed
TZ=America/Los_Angeles  114 passed
TZ=Pacific/Kiritimati   1 failed  -- test_a_watch_read_long_ago_is_stale_not_available
```

At UTC+14 that test's aged seed (an **aware** UTC stamp) shifts forward into
freshness against a horizon built from a **UTC-naive** `now`, which
`_older_than` treats as local. The catalog-equals-producer assertion still
passes; only the absolute `== "stale"` fails. This is the same clock-contract
gap in the other direction, and it is a new hazard the extraction created:
`room_coverage(..., now=)` is now **public** and its docstring never says the
parameter is local wall clock. Both production callers pass `now=None`
(`holdspeak/web/routes/automations.py:165`,
`holdspeak/mcp/families/practice_recipe.py:145`) so nothing shipped is wrong.
**(P1-B below.)**

### 3. Mutation table, re-run by me

In-process plugins, no file edits, against the full 114-test scoped set:

```
RED  the P0 itself -- observed_coverage re-derives watch, cant_check -> available
     4 failed: test_a_cant_check_watch_is_failed_not_available,
     test_a_watch_read_long_ago_is_stale_not_available,
     test_many_watches_reduce_to_the_worst_never_the_best,
     test_the_seeded_project_agrees_with_the_producer_on_every_kind

RED  worst_state -> best-first
     2 failed: test_many_watches_reduce_to_the_worst_never_the_best,
     test_worst_state_orders_every_c4_state

RED  weekly_update regains Limit("max_claims", "literal:40")   [the hole I found green]
     3 failed: test_nothing_is_declared_that_no_step_can_read[weekly_update],
     test_the_fence_sees_an_invented_literal_limit,
     test_weekly_update_declares_no_cap_because_none_exists
```

The exact mutation that was silently green last pass is now caught three
times over. `unreachable_declarations`
(`holdspeak/services/recipe_catalog.py:736-756`) runs over all three real
descriptors, not only synthetic ones
(`tests/unit/test_phase200_recipe_catalog.py:158-169`), and its
constant-source exemption is itself fenced (`:189-197`).

`max_claims` and `interval_days` are gone from the descriptors
(`recipe_catalog.py:621` `limits=()`, `:466-472` inputs are `project_id`
alone). `decision_review`'s surviving `literal:200` is legitimate under the
stated rule: it is bound by the `decisions` step (`:503`) and its `why` no
longer transcribes the service's inner ceiling.

### 4. The corrected canon sentences, and the new doc claim

All three now state the rule the code follows — "a service's own constant
where a cap exists, a literal only where a step really passes it, otherwise
none": module docstring `recipe_catalog.py:21-33`,
`current-phase-status.md:92`, `pm/roadmap/holdspeak/README.md:345`. Each is
true of all three descriptors as shipped, and the first of them is now
executable.

`SCHEDULED_TRIGGER_OWNER` (`recipe_catalog.py:128-133`) is the chain, and
every link exists: `connector_watches.evaluation_cadence_minutes` /
`next_evaluation_at` in the schema, `HeartbeatService.run_sweep`
(`heartbeat_service.py:345`) calling `WatchService.evaluate_due` (`:400`),
`project.steward.run_once` in the real `ACTION_KINDS` registry, and
`ProjectStewardService.run_due` (`project_steward_service.py:141-159`). All
three bindings stay `available=False`.

The new predicate `_no_prepared_recipe_has_a_wired_schedule`
(`tests/unit/doc_claims/registry.py:702-756`) is neither brittle nor
tautological: past the descriptor-flag check it reads `CadenceService`'s real
verb set, the real `cadence_loops` DDL for a next-fire column, and — the part
that answers my P2-1 — asserts no module in the recurring chain imports
`recipe_catalog`. It goes False on the real event it describes, not only on a
flag a builder might forget. Mirrored as a behavioural test at
`tests/integration/test_phase200_recipe_catalog.py:622-644`.

My other P2s are paid on substance, not by argument: `CatalogError` is now a
`ServiceError` with a code and `UnknownRecipe` a 404 subclass of it
(`recipe_catalog.py:166-184`), the HTTP route maps both
(`automations.py:169-176`), and the two substring fences are re-asserted on
the compiled code object — bytecode names, a stop-event wait, a real tick
constant, and a started thread
(`tests/integration/test_phase200_recipe_catalog.py:591-620`). P2-5
(completed commitments counting as coverage) is no longer this story's: the
catalog now inherits whatever the C4 producer says, which is the point.

### Findings from the re-read

**P0 — none.**

**P1-A. A defect disclosure that is false.** The docstring at
`tests/integration/test_phase200_recipe_catalog.py:245-259` describes a
pre-existing `ProjectService.room` / `_older_than` timezone bug that does not
exist on the production chain (§2). It must not travel to the orchestrator or
a future story as a real defect.

**P1-B. The new public seam has an undocumented clock contract.**
`room_coverage(..., now=)` must be a **local wall-clock** datetime, as
`build_aggregate` passes and as `_older_than` assumes. Nothing says so, and
the one caller that supplies its own `now` (the test harness) supplies a UTC
one and produces a wrong absolute answer at UTC+14. Shipped code is
unaffected.

**P2-1. `observed_coverage` flattens a `list_projects` failure to
`unavailable`.** `recipe_catalog.py:1119-1126` catches bare `Exception` and
falls to "not listed", where the producer would classify `failed` /
`forbidden` via `_classify_read_failure`. Conservative (never an all-clear),
so not a P0 — but it is the one place a hand-rolled answer survives, and a
read failure reads as an absence.

### Conditions (all documentary / test hygiene; none blocks the merge)

1. Correct the docstring at
   `tests/integration/test_phase200_recipe_catalog.py:245-259`: the producer
   is right; the fixture seeds a local-naive stamp no production writer
   produces. Seed `datetime.now(timezone.utc).replace(tzinfo=None)` and drop
   the `TZ=UTC` pin, or keep the pin and say it pins the *fixture*.
2. State the clock contract on `needs_you_aggregate.room_coverage`'s `now`
   parameter (local wall clock), and make
   `test_a_watch_read_long_ago_is_stale_not_available` pass its clock on that
   contract so the scoped suite is green at every offset.
3. Either classify the `list_projects` failure through
   `_classify_read_failure` like the producer, or say in the docstring that a
   list failure is deliberately reported as `unavailable`.

**Verdict: RATIFY-WITH-CONDITIONS.**
