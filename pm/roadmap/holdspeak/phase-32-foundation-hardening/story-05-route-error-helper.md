# HS-32-05 — Route error-handling helper

- **Status:** done (2026-06-02). Evidence: [evidence-story-05.md](./evidence-story-05.md).

## Goal

Remove the duplicated error-handling boilerplate across the web routes. Today the
same `except Exception as e: log.error(...); return JSONResponse({"error": str(e)},
status_code=500)` block is repeated ~22× in `activity.py` and 15+× in
`dictation.py` (and siblings) — so any change to error shape means editing dozens
of handlers. Extract one helper.

## Scope

- A single decorator (or FastAPI exception handler) that wraps a route to produce
  the consistent logged-500 JSON response.
- Apply it to the duplicated blocks; delete the inline try/excepts they replace.
- Preserve the exact current response shape and status codes (behavior-preserving);
  this is deduplication, not an error-contract change.
- Note: leave intentional non-500 / specific-exception handling as-is.

## Test plan

- Existing route tests that assert on error responses — green, unchanged.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- Record the before/after count of hand-written 500 handlers removed.

## Done when

- [x] One error-handling helper exists and is applied across the duplicated blocks.
- [x] Error response shape/status codes unchanged; route error tests green.
- [x] Handler-count reduction recorded; full suite green; ruff clean.

## Evidence

[evidence-story-05.md](./evidence-story-05.md). `error_500(exc, logger, detail)`
in `runtime_support.py` replaces the canonical `log.error + JSONResponse(500)`
block at **48 sites** (activity 32 / projects 8 / meetings 7 / system 1) →
−48 handler lines. Behavior byte-identical. **Chose a helper function over the
deferred "decorator" default** because handlers have nested try/except + specific
non-500 handling a whole-handler decorator would swallow. Suite green **1952/14**.
