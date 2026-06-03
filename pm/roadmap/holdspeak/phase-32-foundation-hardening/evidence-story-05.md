# Evidence — HS-32-05 (Route error-handling helper)

**Shipped:** 2026-06-02. The duplicated `log.error(f"<detail>: {e}"); return
JSONResponse({"error": str(e)}, status_code=500)` block — hand-written **48×**
across the web route modules — is now a single helper, `error_500(...)`. A
change to the error contract is now a one-line edit instead of 48.

## The helper — `holdspeak/web/runtime_support.py`

```python
def error_500(exc, logger, detail) -> JSONResponse:
    logger.error(f"{detail}: {exc}")
    return JSONResponse({"error": str(exc)}, status_code=500)
```

Lives in the neutral `runtime_support` module (where `_meeting_callback_payload`
/ `_parse_iso_datetime` already live), exported as `error_500` (with an
`_error_500` alias for naming consistency). Behavior-preserving: same log line,
same response body `{"error": str(exc)}`, same 500 status. `detail` is the
already-formatted message, so an f-string call site keeps its interpolation
(`error_500(e, log, f"Failed to run pipeline {pipeline_id}")`) and the log line
is reproduced exactly.

## Applied — 48 call sites across 4 files (before → after)

| File | canonical 500 blocks replaced |
|---|---|
| `activity.py` | 32 |
| `projects.py` | 8 |
| `meetings.py` | 7 |
| `system.py` | 1 |
| **total** | **48** |

Each site went from the 2-line `log.error(...)` + `return JSONResponse(...500)`
to a single `return error_500(e, log, <detail>)`. Net **−48 handler lines** of
duplicated error construction (route files: 69 insertions / 98 deletions incl.
the 4 import additions). Applied via a reviewed line-based codemod that matched
the exact canonical pair (`log.error(f"…: {e}")` immediately followed by the
canonical 500 return, same indent) — verified to find exactly the 48 expected
sites and leave everything else untouched.

## Decision — helper function, not the deferred "decorator" default

The phase deferred this with a default of "a decorator, so per-route opt-in stays
explicit." On inspecting the code that default doesn't hold up: many handlers
have **nested** `try:`/`except` and **specific** (non-500) handling — e.g. a
`404`/`400` `except` before the generic one. A whole-handler decorator catching
`Exception` would **swallow or reorder** that specific handling (the scope note
"leave intentional non-500 / specific-exception handling as-is" forbids that).
The helper-function-in-`except` instead dedups exactly the canonical 500
construction at each site, leaving every handler's structure and any specific
handling intact — and per-route opt-in stays explicit (each `except` chooses to
call it). It is also far lower-risk (a localized 2→1 line substitution, no
body-dedent across 48 multi-line handlers). The try/except scaffolding remains,
but the *duplication that mattered* (the response shape) is centralized — which
is the story's stated goal.

## Tests / verification

- New `tests/unit/test_route_error_helper.py` (3): response shape + 500 status;
  the `log.error(f"<detail>: {e}")` line is reproduced (incl. an f-string detail
  like "Failed to run pipeline 42"); `str(exc)` body for a `KeyError`.
- The 48 call sites are exercised by the existing route tests
  (`test_web_server.py`, `test_web_activity_api.py` → **126 passed**), which
  assert on the 500 error responses — unchanged and green.
- Functional check: `error_500(ValueError("boom"), log, "…")` → status 500, body
  `{"error":"boom"}` — byte-identical to the old inline response.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1952 passed, 14
  skipped** (+3 helper tests; the route behavior was already covered, so no
  route tests changed). Route modules + `runtime_support` ruff-clean.

## Out of scope (as the story says)

- `dictation.py`'s 500s use a *different* response shape (not the canonical
  `{"error": str(e)}`), so they are **not** part of this dedup — left as-is.
- Specific/non-500 `except` clauses (404/400/etc.) were not touched.
