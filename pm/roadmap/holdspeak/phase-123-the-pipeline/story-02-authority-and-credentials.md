# HS-123-02 — Authority and credentials

- **Project:** holdspeak
- **Phase:** 123
- **Status:** backlog
- **Depends on:** HS-123-01
- **Unblocks:** HS-123-12
- **Owner:** unassigned

## The thesis (the bar)

Control mode, grants, policy evaluation, and secrets are authority boundaries,
not HTTP behaviors. Every adapter must receive the same principal checks,
revocation behavior, policy result, and secret redaction. A route must not
rebuild any of those rules from a request and direct persistence access.

When this ships, `AuthorityService` owns policy and the grant lifecycle, and
`CredentialService` owns the write-only secret lifecycle. The authority and
secret routes are transport adapters over those services.

## Phase 122 pattern to follow

Follow the service seam established by HS-122-04, then apply the HS-123-01
error vocabulary:

1. Construct the service at composition time with the database and the narrow
   collaborators it needs; do not give it `WebContext`, `Request`, `Response`,
   or a router.
2. Every public operation takes an explicit `Principal` as its first domain
   argument. The adapter obtains it using the existing principal dependency and
   passes it unchanged.
3. The service returns the current route response data or raises a shared
   `ServiceError` subtype/code. The route alone maps that stable domain failure
   to the existing HTTP status and JSON shape.
4. Keep request parsing, schema coercion, and response serialization in the
   route. Move authorization, persistence, revocation, secret handling, and
   policy decisions into the service.
5. Preserve existing response shapes and status codes. This is an extraction,
   not an authority-policy redesign.

## Required service contract

Create `holdspeak/services/authority_service.py` with at least:

- `get_policy(principal)` for the policy/control-mode read currently exposed by
  the authority module.
- `get_control_mode(principal)` and
  `set_control_mode(principal, mode)`. `set_control_mode` must retain the
  existing mode validation and revoke affected grants in the same atomic
  boundary/order as the route does today.
- `evaluate(principal, request)` for policy evaluation. `request` is a typed
  service DTO or existing domain request value, never FastAPI's `Request`.
- `list_grants(principal, actor=None)`,
  `issue_grant(principal, proposal_id, ...)`,
  `revoke_grant(principal, grant_id)`, and
  `list_grant_uses(principal, grant_id)`.

Create `holdspeak/services/credential_service.py` unless the application
already has an equally narrow credential component. Its API must explicitly
separate redacted metadata reads from value-bearing writes:

- `list_redacted(principal)` and, if the current route exposes one,
  `get_redacted(principal, secret_id)`;
- `replace(principal, secret_id, value, metadata_or_patch)`;
- `rotate(principal, secret_id, rotation_input)`;
- `delete(principal, secret_id)`.

Do not return, log, serialize, place in an exception, or retain a secret value
outside the write operation. Tests should use a sentinel value and assert it is
absent from every read/list/error response.

## Audited handler map

### `holdspeak/web/routes/authority.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 30 | `api_authority_policy` — `GET /api/authority/policy` | `AuthorityService.get_policy(principal)` | Low — read; preserve policy shape and disclosure rules. |
| 66 | `api_set_control_mode` — `PUT /api/authority/control-mode` | `AuthorityService.set_control_mode(principal, mode)` | High — mode validation plus grant revocation must remain indivisible. |
| 120 | `api_evaluate_operation` — `POST /api/authority/evaluate` | `AuthorityService.evaluate(principal, evaluation_request)` | Medium — preserve policy inputs, allow/deny result, and reason shape. |
| 166 | `api_list_grants` — `GET /api/authority/grants` | `AuthorityService.list_grants(principal, actor)` | Medium — actor filtering and redaction are domain behavior. |
| 176 | `api_issue_grant` — `POST /api/authority/grants` | `AuthorityService.issue_grant(principal, proposal_id, ...)` | High — preserve proposal linkage, authorization, grant material, and lifecycle. |
| 233 | `api_revoke_grant` — `DELETE /api/authority/grants/{grant_id}` | `AuthorityService.revoke_grant(principal, grant_id)` | High — preserve ownership checks, idempotency/not-found behavior, and use cutoff. |
| 248 | `api_grant_uses` — `GET /api/authority/grants/{grant_id}/uses` | `AuthorityService.list_grant_uses(principal, grant_id)` | Medium — preserve grant visibility and ledger ordering. |

The audit brief counted six mutation/evaluation/grant handlers. The policy read
at current line 30 is in the same module and is included so the module has no
unowned authority operation.

### `holdspeak/web/routes/system/settings_secrets.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 123 | `api_replace_secret` — `PUT /api/settings/secrets/{secret_id}` | `CredentialService.replace(principal, secret_id, value, patch)` | High — write-only input; validate identity and preserve current encrypted/persisted representation. |
| 152 | `api_rotate_secret` — `POST /api/settings/secrets/{secret_id}/rotate` | `CredentialService.rotate(principal, secret_id, rotation_input)` | High — rotation must not expose old/new material and must retain current failure semantics. |
| 171 | `api_delete_secret` — `DELETE /api/settings/secrets/{secret_id}` | `CredentialService.delete(principal, secret_id)` | Medium — preserve authorization, deletion/idempotency semantics, and redacted receipt. |

There is no secret-value read endpoint in this module. If a settings or
credential metadata read exists elsewhere, it must use `list_redacted` or
`get_redacted`, never the write DTO.

## Implementation steps

1. Read the full existing authority and secrets modules before moving code;
   identify their principal acquisition, authorization helpers, persistence
   transaction boundaries, and response/error shapes.
2. Introduce typed service inputs where the current route accepts raw JSON.
   Keep HTTP validation at the adapter edge, but do not leak FastAPI objects
   into the service.
3. Move the current implementation body operation-by-operation. Keep the
   control-mode grant revocation path together in `set_control_mode`; never
   make the route call two service methods to reconstruct it.
4. Wire service instances through the normal application composition seam.
   Route factories may close over a service, but must not lazily call
   `get_database()` or construct a database-backed service per request.
5. Translate shared service errors at each route edge using the HS-123-01
   convention. Preserve all established HTTP status codes and response bodies.
6. Add focused service tests for principal denial, grant issue/revoke/use,
   control-mode revocation, and every secret lifecycle operation. Add route
   regression tests for shape/status and a sentinel-secret non-disclosure test.

## Acceptance criteria

- [ ] `AuthorityService` implements every authority operation in the table and
      accepts an explicit `Principal` on every public operation.
- [ ] `CredentialService` (or a named, equally narrow credential component)
      implements replace, rotate, delete, and redacted metadata reads with an
      explicit `Principal`.
- [ ] A control-mode change preserves current validation and revokes grants in
      the same logical operation; grant issue, revoke, use-ledger, and policy
      evaluation preserve current authorization and response semantics.
- [ ] Secret values are write-only: they do not appear in redacted reads,
      success bodies, errors, logs under test, or service return values.
- [ ] Routes contain parsing, one service invocation, service-error mapping,
      and serialization only; they do not access the database or implement
      authority policy/lifecycle rules.
- [ ] Service modules import neither `holdspeak.web.routes` nor FastAPI or
      `WebContext`.
- [ ] Relevant tests and the full suite pass: `uv run pytest -q`.

## Builder verification

Run these after the extraction (adjust only test filenames, not the asserted
architecture):

```bash
rg -n "class (AuthorityService|CredentialService)|def (get_policy|set_control_mode|evaluate|list_grants|issue_grant|revoke_grant|list_grant_uses|replace|rotate|delete|list_redacted)" holdspeak/services
! rg -n "get_database\(|ctx\.get_database|WebContext" holdspeak/web/routes/authority.py holdspeak/web/routes/system/settings_secrets.py
! rg -n "holdspeak\.web\.routes|fastapi" holdspeak/services/authority_service.py holdspeak/services/credential_service.py
uv run pytest -q
```

## Files in scope

- New: `holdspeak/services/authority_service.py`
- New: `holdspeak/services/credential_service.py`
- `holdspeak/web/routes/authority.py`
- `holdspeak/web/routes/system/settings_secrets.py`
- Service composition/context wiring required to inject these services
- Related authority, grant, settings-secret, route, and service tests
