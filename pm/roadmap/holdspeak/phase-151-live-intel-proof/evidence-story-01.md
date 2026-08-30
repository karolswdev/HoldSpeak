# Evidence - HS-151-01

- **Story:** HS-151-01 - The honest dispatch (structured output + the wiring recipe)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T01:28:58Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json uv run --python 3.13.11 pytest -q tests/unit/test_hs151_honest_dispatch.py tests/unit/test_intel_cloud.py tests/unit/test_intel_coerce.py tests/unit/test_intel_extract.py tests/unit/test_intel_queue.py tests/unit/test_phase143_inference_capability_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 60035932e6e871152e52bed5057c6b7bc0c51809

```text
........................................................................ [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
166 passed in 21.00s
```

## Orchestrator triage — 2026-08-30

- Verified by my own hand: 31 story tests + the intel regression
  set + the capability census green in the capture above (the
  builder's fuller 304-test regression sweep also read green).
- Counsel M1 verified in the diff: the response_format-400 path
  follows the max_completion_tokens compat pattern exactly — a
  named signal, a second admitted child, one physical request per
  receipt; forget_endpoint_dialects clears both dialect sets.
- Counsel M2/M4: INTEL_SCHEMA is the one source of truth (prompt
  stringifies, response_format wraps, adapter references), carrying
  the named-owner shape from birth.
- Census drift remapped by the orchestrator: 18 entries, every one
  1:1 same-symbol — engine.py +45 lines (this story's compat
  block), calendar_snapshot_service.py +12 (story 04's
  fence-strip). Both attributions this arc's own; the builder
  STOPPED and reported without touching the guard, per the law.
- scripts/wire_metal_intel.py resolve-proof pinned (a wired fresh
  HOME lets the route plan resolve meeting.deferred_analysis); its
  first live-fire happens in story 03's rig.
