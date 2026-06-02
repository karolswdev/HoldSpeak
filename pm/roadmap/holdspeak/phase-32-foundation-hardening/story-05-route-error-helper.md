# HS-32-05 — Route error-handling helper

**Status:** not-started.

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

- [ ] One error-handling helper exists and is applied across the duplicated blocks.
- [ ] Error response shape/status codes unchanged; route error tests green.
- [ ] Handler-count reduction recorded; full suite green; ruff clean.
