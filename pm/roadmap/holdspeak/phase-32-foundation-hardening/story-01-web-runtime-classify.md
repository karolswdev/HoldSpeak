# HS-32-01 — Class-ify `web_runtime.py` (`WebRuntime`)

- **Status:** done (2026-06-02). Evidence: [evidence-story-01.md](./evidence-story-01.md).

## Goal

Convert the 1,702-line procedural `run_web_runtime()` — which threads runtime
state through 9+ `nonlocal` variables — into a `WebRuntime` class whose state is
instance attributes and whose lifecycle is methods, matching the clean
`controller.py` (TUI) path. Behavior-preserving.

## Scope

- Introduce `WebRuntime` (or equivalent): `nonlocal`-threaded state → `self.*`;
  the inline closures → methods; `run_web_runtime()` becomes a thin
  `WebRuntime(...).run()` shim so the entry point is unchanged.
- Preserve startup/shutdown ordering, the meeting lock, the device/hotkey press
  paths, and the intel-worker wiring exactly.
- No API or behavior change; this is internal shape only.

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- The existing web/runtime tests are the regression gate; record which exercise
  startup/shutdown and the press paths.

## Done when

- [x] Runtime orchestration lives on a `WebRuntime` class; no module-level
      `nonlocal`-threaded god-function remains.
- [x] Entry point (`run_web_runtime` / `main.py` wiring) unchanged externally.
- [x] Full suite green; ruff clean.

## Evidence

[evidence-story-01.md](./evidence-story-01.md). Suite green at **2063 passed,
14 skipped** (baseline-identical); `web_runtime.py` ruff-clean; 10 `nonlocal`
vars → `self.*`; `run_web_runtime()` is a thin `WebRuntime(...).run()` shim.
