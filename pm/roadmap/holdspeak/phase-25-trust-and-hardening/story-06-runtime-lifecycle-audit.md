# HS-25-06 — Runtime-Lifecycle Knob Audit (eviction, cloud_store)

- **Project:** holdspeak
- **Phase:** 25
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-25-07
- **Owner:** unassigned

## Problem

Two config knobs may silently no-op, which erodes trust in the config surface:

- `eviction_idle_seconds` — eviction logic *exists* (`runtime_mlx.py:180-182`,
  `runtime_llama_cpp.py:163`, plumbed via `runtime.py:147`) but defaults to `0`
  (disabled) and it is unclear whether anything ever schedules an eviction
  check, so the idle-model-unload it implies may never happen.
- `intel_cloud_store` (`config.py:71`) — passed to the cloud client via
  `extra_body={"store": ...}`; if the endpoint doesn't recognize it, the user's
  "don't retain my data" choice silently fails.

Each must be resolved to *proven-working* or *removed with rationale* — and
removal must follow verification, not assumption (the eviction code is real).

## Scope

### In

- For `eviction_idle_seconds`: determine whether eviction is ever triggered in a
  running system. If yes, cover it with a test. If it can never fire, either
  wire a trigger or remove the knob + its plumbing with a recorded rationale.
- For `intel_cloud_store`: verify whether the target endpoint honors the
  `store` flag; if it can silently no-op, either validate/confirm it or surface
  that the setting is advisory in docs + `doctor`, so the user isn't misled.
- Record findings for both in the evidence file.

### Out

- The egress *decision* (HS-25-01) — this story only audits the `store` flag's
  effectiveness, not whether cloud is used.
- Broader config-surface review beyond these two knobs.

## Acceptance criteria

- [x] `eviction_idle_seconds` **kept** (it is real, not dead): config field
      (`config.py:156`) → `assembly.py:116` → adapter; `_maybe_evict` unloads the
      model. Proven by `tests/unit/test_runtime_knob_audit.py` (fires when idle,
      not within window, never when disabled).
- [x] `intel_cloud_store` **kept**: proven to be forwarded as `store=True` when
      enabled (and omitted when off) — same test file — and documented as
      **advisory** (endpoint must honor OpenAI's `store`) in
      `docs/MEETING_MODE_GUIDE.md`.
- [x] No audited knob silently no-ops without the user being told (eviction
      works; `cloud_store` forwarding is real + its endpoint-dependence is
      documented).
- [x] Findings recorded in `evidence-story-06.md`.

## Test plan

- Unit: `uv run pytest -q tests/ -k "runtime and evict"` (if kept) and
  `-k "intel and store"` — assert the flag's actual effect or its advisory
  handling.
- Integration: dictation + intel suites stay green after any removal.
- Manual: n/a.

## Notes / open questions

- Per repo norm: *look before deleting*. The eviction logic is real code, not a
  stub — confirm it is genuinely unreachable before removing anything.
- If `store` can't be verified against the default endpoint, advisory-documenting
  is acceptable; silently leaving it is not.

## Closeout

Shipped 2026-05-31. See [evidence-story-06.md](./evidence-story-06.md).

Audit outcome: **both knobs are real and working** — the pre-phase suspicion that
they might be no-ops was wrong. Nothing removed (per the look-before-deleting
discipline); behavior pinned by tests, and `intel_cloud_store`'s
endpoint-dependence is now documented so the user is never misled.
