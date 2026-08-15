# Evidence - HS-132-09

- **Story:** HS-132-09 - The receipt names what loaded
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:37:49Z

- **Command:** `env HOME=/tmp/hs132-09-home uv run pytest -q tests/unit/test_deployment_identity.py tests/unit/test_ask_no_retarget.py tests/unit/test_meeting_placement_policy.py tests/unit/test_one_path_census.py tests/unit/test_web_routes_ask.py tests/unit/test_web_routes_recipe_chat.py tests/unit/test_receipt_model_honesty.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e91ab491588295c61d8c48b9db98c95384d5a121

```text
........................................................................ [ 80%]
.................                                                        [100%]
89 passed in 60.77s (0:01:00)
```

## Orchestrator notes

- The fence (test_receipt_model_honesty.py, 11 tests) asserts readiness ==
  frozen revision == engine.active_model == result model == placement
  receipt == advertised /api/models row == wire model, across this_machine
  / onDevice / openAICompatible / meshNode / hub-default-cloud; proven to
  bite by injecting a pre-HS-131-13 imposter engine (caught at the
  executed-model assertion and shown reaching the receipt).
- All ten _hub_model_name stubs removed from the ask/recipe route tests —
  the stubbing that let this class regress unnoticed is gone; fixtures now
  pin a real model file.
- Bonus fix found while fencing: a ready onDevice destination naming only
  a model_file was dropped from /api/models entirely.
- Worker blast-radius sweep: 320 + 152 + 48 additional focused tests green
  (one-path spine, sync, runner migrations, egress boundary, doctor).
- Ledger (recorded, unfixed): onDevice display-name vs file-stem needs an
  owner call on which is canonical; AskService(hub_model=...) and the
  ask.py injection are dead wiring for a later deletion; keyless cloud
  manifest rows fall back to the local name with runnable=False, pinned
  together with paired_device_target by the fence.
