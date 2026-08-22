# Evidence - HSEGHS001HS104-143-01

- **Story:** HSEGHS001HS104-143-01 - Capability and Route Census
- **Status:** done
- **Date:** 2026-08-21

## Outcome

Story 01 establishes a checked-in, fail-closed baseline for every current
inference execution door, semantic capability caller, mutable routing
authority, owner routing surface, and retry/fallback policy. It changes no
product runtime behavior.

The three generated ledgers are:

- `assets/generated-inference-capability-census.md`
- `assets/generated-routing-authority-census.md`
- `assets/generated-surface-fallback-census.md`

## Census truth

- 99 exact Python model-shaped AST sites with explicit capability/source-owner
  classification; no heuristic or catch-all classification remains.
- 12 direct `InferenceRunner.invoke` entrances and 14 Python physical leaves;
  zero Python bypasses.
- 9 semantic Ask/Recipe/Sequence/Workflow callers, including one current
  `thought.interview` operation with a question-or-synthesis result union.
- 7 Apple/Swift physical leaves named as legacy bypasses with exact Story 06 or
  Story 10 migration ownership.
- 18 mutable routing families with one migration owner, 6 public resolver
  definitions, 63 resolver references, and 41 semantically classified
  `profile_id` reads.
- 33 backend selector/recovery helpers, 27 browser routing surfaces, and 6
  Swift retry/fallback policy sites classified exactly.
- Named blockers remain visible for Story 03/11:
  `PROFILE_SERVICE_OWNER_ENFORCEMENT_GAP` and
  `PROFILE_SYNC_PATH_BEARING_SEAM`.

Mutation fixtures prove that a new model-shaped site, public/late resolver,
mutable pointer read, Ask/Recipe semantic caller, browser selector, Swift
provider open, Swift `.complete` leaf, or Swift retry/fallback branch fails the
gate until it receives an explicit reviewed classification.

## Verification

### Focused census and mutation suite

```text
uv run pytest -q \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_surface_fallback_census.py --tb=short

...................                                                      [100%]
19 passed in 15.34s
```

### Integrated census, one-path, and API surface gate

- **Index-tree:** `3fbbc57774eabe2024dc2eaded64f62481ece382`

```text
uv run pytest -q \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_surface_fallback_census.py \
  tests/unit/test_one_path_census.py \
  tests/unit/test_api_surface.py --tb=short

56 passed in 63.47s
```

The JUnit record reported `errors=0`, `failures=0`, and `skipped=0`.

### Static hygiene

```text
uv run ruff check \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_surface_fallback_census.py
All checks passed!

git diff --check
# clean
```

### DW status

`dw check holdspeak` reaches one inherited, out-of-scope Phase 101 mismatch:

```text
ERROR pm/roadmap/holdspeak/phase-101-the-native-innards/evidence-story-04.md:
evidence exists but matching story is not done
```

Story 01 introduces no Phase 101 change. The inherited mismatch is recorded
here rather than silently repaired or omitted.

## Review result

Independent owner and architecture/counsel reviews both returned **RATIFY**
after the final mutation counterexamples were closed. The review specifically
confirmed current Thought taxonomy, RunsOnPicker/camel-case browser coverage,
kernel late-routing coverage, repository-wide helper discovery, Swift physical
and policy coverage, and singular migration ownership.
