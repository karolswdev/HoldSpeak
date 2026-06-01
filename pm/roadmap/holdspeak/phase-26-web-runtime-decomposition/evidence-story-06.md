# Evidence — HS-26-06 — Collapse Callback Wiring + Sync-DB-in-Async Audit

- **Shipped:** 2026-06-01
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

Two behavior-preserving structural changes plus an audit:

### 1. Constructor callback bag → `WebRuntimeCallbacks`

`MeetingWebServer.__init__` took **~30 keyword params** (the on_* behavior
callbacks + device wiring + get_state + project_detector + host/port/auth_token).
Introduced a `WebRuntimeCallbacks` dataclass that bundles every injected
collaborator; the constructor is now:

```python
def __init__(self, callbacks: WebRuntimeCallbacks, *,
             host="127.0.0.1", port=None, auth_token=""):
```

**4 params** (callbacks + 3 scalar bind-config). `__init__` explodes the bundle
onto the existing `self.<attr>` names, so `_create_app`'s `WebContext` build and
the device-WS registration read unchanged — zero churn below the constructor.
All **69 construction sites** (web_runtime, meeting_session, 17 test files) were
updated to pass `WebRuntimeCallbacks(...)` via an AST codemod (preserves each
call's value expressions, incl. lambdas and `**cb` unpacking).

### 2. Route modules fully decoupled from `web_server`

The last cross-module imports from the monolith were re-homed into a neutral
`holdspeak/web/runtime_support.py`: `_UnknownDeviceError`,
`_meeting_callback_payload`, `_parse_iso_datetime`. **No `routes/*` module imports
`web_server` anymore** (verified). `web_server` imports `_parse_iso_datetime` back
(it uses it in `_current_formatted_duration`); `web_runtime` imports
`_UnknownDeviceError` from the neutral module.

### 3. Sync-DB-in-async audit

Recorded in [`audit-sync-db-async.md`](./audit-sync-db-async.md). Finding: ~174
sync SQLite calls across ~118 `async` handlers (activity/meetings/projects), but
none is on the WS broadcast path (broadcasts are scheduled cross-thread via
`run_coroutine_threadsafe` against a 1 Hz duration cadence), and local-SQLite
reads are bounded/sub-ms. **Decision: document, do not offload** (matches the
phase's deferred decision); explicit re-visit trigger + watch-list recorded.

## Files touched

- `holdspeak/web/runtime_support.py` — **new** (62 lines); the 3 re-homed helpers.
- `holdspeak/web_server.py` — removed the 3 helper defs; added `WebRuntimeCallbacks`
  dataclass; collapsed `__init__` (30 → 4 params); imports `_parse_iso_datetime`.
- `holdspeak/web_runtime.py`, `holdspeak/meeting_session.py` — construct via
  `WebRuntimeCallbacks(...)`; import `_UnknownDeviceError` from `runtime_support`.
- `holdspeak/web/routes/{meetings,activity}.py` — import the shared helpers from
  `runtime_support`; docstrings updated. `routes/__init__.py` docstring updated.
- **17 integration test files** — construction sites updated to the bundle.
- `tests/unit/test_web_runtime.py` — `FakeServer`/`FailingServer` stubs now accept
  the positional `callbacks` bundle (merge `vars(callbacks)` back into `kwargs`).
- `pm/.../audit-sync-db-async.md` — **new**, the audit.

## Verification artifacts

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1879 passed, 13 skipped        (no regressions)

$ uv run ruff check holdspeak/web/ holdspeak/web_server.py holdspeak/web_runtime.py
All checks passed!     (the 1 remaining repo error — meeting_session.py
                        `current_time` F841 — pre-dates this story)

$ grep -rn "import .*web_server" holdspeak/web/routes/*.py   # -> none
```

Route-inventory diff vs the original `origin/main` baseline (`f77c2d9`): identical,
122 routes. Constructor arity 30 → 4.

## Decisions / notes

- **Bundle, not a `WebContext`-as-input.** `WebRuntimeCallbacks` holds the
  *externally-injected* collaborators; the server still builds the route-facing
  `WebContext` from it plus server internals (`broadcast` thunk, `ws`,
  `current_formatted_duration`). Two roles, two objects — kept distinct.
- **`__init__` re-explodes onto `self.*`** rather than reading `self._callbacks.*`
  throughout — chosen to keep `_create_app` and the device-WS registration
  untouched (lowest-risk collapse). `self._callbacks` is retained for reference.
- **Full collapse over the lighter option** — per the user's explicit choice;
  all 69 sites updated via codemod + a hand-fix for the one `**cb` call site.

## Acceptance criteria — re-checked

- [x] Constructor callback count materially reduced (30 → 4); remaining params
      (callbacks bundle + host/port/auth_token) justified.
- [x] Route modules read from the shared context, not injected callbacks (since
      HS-26-02..05) — and now import nothing from `web_server`.
- [x] Sync-DB-in-async audit recorded; offload decision covered by a documented
      rationale (no offload, with re-visit trigger).
- [x] Existing web tests pass unchanged (full suite green, 1879).

## Follow-ups

- HS-26-07: decomposition closeout (size + route-inventory evidence; confirm the
  exit criteria; final summary).
