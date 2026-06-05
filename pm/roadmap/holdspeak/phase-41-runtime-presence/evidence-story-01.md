# Evidence — HS-41-01 — Runtime activity contract + state mapping

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-41-runtime-presence`
- **Owner:** unassigned

## What shipped

The platform-agnostic foundation for every presence surface — one normalized
activity contract, salvaged from the codex spike (PR #17) and ported clean (no
Tk, no GUI deps).

- `holdspeak/runtime_activity.py` — `VALID_ACTIVITY_STATES` (idle / listening /
  recording / transcribing / processing / typing / complete / meeting_live /
  saving / error), `normalize_activity_state` (unknown → idle), `RuntimeActivity`
  (dataclass → `to_dict`, includes the window policy), `RuntimeActivityTracker`
  (snapshot + started-at-preserving update), and `desktop_window_policy(state)`
  (transient hidden / active / linger visibility with per-state linger timings).
- `tests/unit/test_runtime_activity.py` — the window policy is transient, the
  tracker preserves `started_at` across same-state updates, and unknown states
  normalize to idle.

The codex `TkPresenceRenderer` is **not** ported (rejected — see the phase
status doc). Only the pure contract + tests come over here.

## Verification artifacts

> `uv run` is broken on this machine; tests run via `.venv/bin/python -m pytest`.

- Targeted: `.venv/bin/python -m pytest -q tests/unit/test_runtime_activity.py`
  → `3 passed`.
- Ruff (touched files) → `All checks passed!`.
- Full suite: `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`
  → `2224 passed, 16 skipped` (2221/16 at Phase-40 close; +3) — **no new
  dependency** pulled into the default suite.

## Acceptance criteria — re-checked

- [x] `runtime_activity.py` exists with the contract + tracker + window policy;
      pure (no GUI imports — `import holdspeak.runtime_activity` pulls only
      `dataclasses`/`datetime`/`typing`).
- [x] Unit tests pass; the default suite gains them with no new deps.
- [x] States cover the dictation + meeting lifecycle.

## Deviations from plan

- Bundled with the phase scaffold (status doc + 7 story files) in this commit —
  the phase-open + HS-41-01 as one atomic chunk, documented here.
