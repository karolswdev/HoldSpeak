# Evidence — HS-25-06 — Runtime-Lifecycle Knob Audit

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## Audit outcome

Both knobs suspected of silently no-op'ing turned out to be **real and reachable**.
Nothing was removed; behavior is now pinned by tests and the one
endpoint-dependent flag is documented as advisory.

### `eviction_idle_seconds` — works

- Config field: `config.py:156` (`LLMRuntimeConfig.eviction_idle_seconds`).
- Plumbed: `assembly.py:116` → `runtime.build_runtime` → adapter ctor.
- Effect: `MlxRuntime._maybe_evict` (`runtime_mlx.py:184`) sets `self._loaded = None`
  when `eviction_idle_seconds > 0` and idle time is exceeded; called from
  `classify` (line 143) and `rewrite` (line 173). `LlamaCppRuntime` has the
  equivalent at line 163. Default `0` = disabled.

### `intel_cloud_store` — works, endpoint-dependent

- Effect: `intel.py:627` adds `store=True` to the cloud `create()` kwargs when
  enabled. HoldSpeak forwards it; whether the *endpoint* honors it is outside our
  control (OpenAI does; many compatible servers ignore unknown fields).
- Resolution: documented as **advisory** in `docs/MEETING_MODE_GUIDE.md`.

## Files touched

- `tests/unit/test_runtime_knob_audit.py` — **new**, 5 cases.
- `docs/MEETING_MODE_GUIDE.md` — `intel_cloud_store` advisory note.
- (No production code changed — both knobs already functioned.)

## Verification artifacts

```
$ uv run pytest -q tests/unit/test_runtime_knob_audit.py
5 passed
  - eviction fires when idle beyond threshold; not within window; never when disabled (0)
  - cloud_store=True  -> create() kwargs include store=True
  - cloud_store=False -> no "store" key

$ uv run ruff check tests/unit/test_runtime_knob_audit.py
All checks passed!

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
9 failed, 1865 passed, 13 skipped
  (+5 vs HS-25-05 baseline; the 9 are the same documented pre-existing failures.)
```

## Acceptance criteria — re-checked

- [x] `eviction_idle_seconds` kept + proven by test (real, not dead).
- [x] `intel_cloud_store` proven forwarded + documented advisory.
- [x] No audited knob silently no-ops without the user being told.
- [x] Findings recorded here.

## Deviations from plan

The story allowed "prove it works OR remove." Both proved real, so both were
kept — the earlier "possibly dead" framing was incorrect.

## Follow-ups

None.
