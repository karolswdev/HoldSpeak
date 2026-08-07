# HS-123-03 — Settings service

- **Project:** holdspeak
- **Phase:** 123
- **Status:** backlog
- **Depends on:** HS-123-01
- **Unblocks:** HS-123-12
- **Owner:** unassigned

## The thesis (the bar)

Settings are application state, not HTTP state. The existing settings update
performs a deep merge, validates the resulting complete configuration, persists
it, and applies runtime reconfiguration through `ctx.on_settings_applied`.
Those semantics must become one reusable application operation, available to
MCP and tests without importing `WebContext`.

When this ships, `SettingsService` owns redacted reads and validated updates.
A narrow injected callback performs runtime application after a successful
update; neither its type nor the service imports the web layer.

## Phase 122 pattern to follow

Use the HS-122 service seam and HS-123-01 error boundary:

- Build the service once at application composition with its settings store and
  an `on_settings_applied` callable/protocol. Do not pass `WebContext` to the
  constructor or public methods.
- Every public method starts with an explicit `Principal`; it returns a
  transport-neutral settings DTO/dict or raises a shared service error code.
- The route parses JSON, obtains the principal, invokes one service method,
  maps the shared error to the existing HTTP response, and serializes the
  result. It must not deep merge, validate, persist, or invoke runtime hooks.
- Keep request/response field names, defaults, validation failures, and
  callback ordering unchanged. This story changes ownership, not settings
  policy.

## Required service contract

Create `holdspeak/services/settings_service.py` with this minimum public API:

- `get_settings(principal)` — the permitted full application settings view for
  the normal settings read. Its result must still omit or redact credentials.
- `get_redacted(principal)` — an explicit safe read for callers that must never
  receive secret material. It is the only read API credential-aware callers
  should need.
- `update_settings(principal, patch)` — validates that `patch` is the expected
  patch shape, reads current settings, deep-merges without mutating either
  input, validates the complete merged result, persists it, invokes the
  injected runtime callback with the accepted configuration, then returns the
  same redacted response shape the route returned before extraction.

Use a small protocol/callable such as `SettingsApplied = Callable[[Settings],
None]` (async only if the existing callback is async). The callback receives a
domain settings value, not a request/context object. Define and preserve the
current behavior if application fails after persistence: do not silently
introduce a partial success or rollback policy. Capture it in a regression
test.

Typed section accessors are permitted only where they remove duplicated domain
logic, for example `get_inference_settings(principal)` or
`get_capture_settings(principal)`. Do not turn each JSON key into a speculative
service method.

## Audited handler map

### `holdspeak/web/routes/system/settings.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 59 | `api_get_settings` — `GET /api/settings` | `SettingsService.get_settings(principal)` | Medium — preserve the established public/redacted settings projection. |
| 78 | `api_update_settings` — `PUT /api/settings` | `SettingsService.update_settings(principal, patch)` | High — this is the existing deep-merge, full validation, persistence, and runtime-application transaction. |

The route currently owns the `ctx.on_settings_applied` call. Move that effect
behind the injected service callback. It is explicitly prohibited for
`SettingsService` to accept, store, or import `WebContext` to reach it.

## Implementation steps

1. Read the full settings route and trace all helpers it calls. Record the
   exact merge behavior for nested dictionaries, replacement behavior for
   scalars/lists, validation error body/status, persistence order, and callback
   order before moving code.
2. Put the existing merge helper in the service or a transport-neutral support
   module. It must not mutate the persisted settings object or caller patch.
3. Build a complete candidate configuration before validation; reject an
   invalid candidate before persistence or runtime application.
4. Inject the runtime callback at service construction. Call it exactly where
   the route currently calls `ctx.on_settings_applied`, retaining failure
   behavior and awaiting it if applicable.
5. Redact credentials recursively and test with a sentinel credential in both
   `get_settings` and `get_redacted`. Coordinate the precise credential
   metadata shape with HS-123-02, without duplicating its write lifecycle.
6. Replace the route body with principal acquisition, JSON parsing, one service
   call, domain-error mapping, and serialization. Wire the service through the
   application composition root.

## Acceptance criteria

- [ ] `SettingsService` exposes
      `get_settings(principal)`, `get_redacted(principal)`, and
      `update_settings(principal, patch)`; all public operations take an
      explicit principal.
- [ ] `update_settings` retains the existing nested deep-merge semantics,
      validates the complete merged configuration before persistence, and does
      not mutate its input patch.
- [ ] Runtime reconfiguration is called through an injected callable/protocol,
      in the same order and with the same failure behavior as the existing
      `ctx.on_settings_applied` path.
- [ ] `SettingsService` imports neither FastAPI nor `WebContext`; no service
      method accepts either type.
- [ ] Settings reads never expose secret values; their established response
      shape and authorization remain unchanged.
- [ ] Both settings handlers contain no direct database access, deep merge,
      validation, or runtime callback invocation.
- [ ] Relevant route/service regressions and `uv run pytest -q` pass.

## Builder verification

```bash
rg -n "class SettingsService|def (get_settings|get_redacted|update_settings)" holdspeak/services/settings_service.py
rg -n "on_settings_applied|SettingsApplied|Callable" holdspeak/services/settings_service.py
! rg -n "get_database\(|ctx\.get_database|on_settings_applied|deep_merge" holdspeak/web/routes/system/settings.py
! rg -n "holdspeak\.web\.routes|WebContext|fastapi" holdspeak/services/settings_service.py
uv run pytest -q
```

## Files in scope

- New: `holdspeak/services/settings_service.py`
- `holdspeak/web/routes/system/settings.py`
- Application composition/context wiring that supplies persistence and the
  runtime callback
- Related settings configuration, runtime, route, and service tests
