# HS-13-04 - Local-user pack discovery

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-01, HS-13-02
- **Unblocks:** "drop a pack into a directory" extensibility
- **Owner:** unassigned

## Problem

The first-party packs are imported from
`holdspeak.connector_packs` at startup. Authoring a new pack
means contributing back to the repo. The framework is
extensible *in theory* but not *in practice*. Phase 13 makes
local user packs work without modifying the source tree.

## Scope

- **In:**
  - Discover Python files under `~/.holdspeak/connector_packs/`
    at startup; load each as a module; require it to export a
    `MANIFEST: ConnectorManifest`; merge into the runtime
    registry alongside first-party packs.
  - Loader sandboxing — a user pack file lives under a
    user-owned path; the loader logs which file it's loading,
    refuses any pack whose manifest fails validation (with the
    exact errors), and refuses ids that collide with a first-
    party pack.
  - User packs go through the same `PermissionGate`
    (HS-13-02) as first-party — declared permissions are
    enforced regardless of source.
  - `/activity` Connectors panel labels each pack with its
    *source* (`first-party` vs `user`); the user can disable
    user packs with one click without removing the file.
  - A `holdspeak doctor connectors` CLI subcommand lists
    discovered packs + their source + their validation
    state.
- **Out:**
  - Loading packs from the internet, marketplaces, or any
    network source.
  - Cryptographic signing / pack signatures.
  - Auto-update.

## Acceptance Criteria

- [ ] Dropping a valid `.py` file into
  `~/.holdspeak/connector_packs/` causes the runtime to pick
  it up on next start.
- [ ] An invalid manifest (any `validate_manifest` failure)
  rejects the pack with a structured error message; the
  runtime still starts.
- [ ] An id collision with a first-party pack rejects the user
  pack and logs a warning; the first-party pack wins.
- [ ] `/activity` Connectors panel shows the pack's source
  (first-party / user).
- [ ] `holdspeak doctor connectors` lists every pack + state.

## Test Plan

- Unit: discovery against a tmp_path-mocked HOME with valid
  + invalid + colliding fixtures.
- Unit: invalid pack does not crash discovery; surfaces the
  validation error.
- Integration: API connector list reflects user-pack source
  label.

## Notes

The loader is in-process Python `importlib`. This is *not* a
security boundary — a user pack runs with the same
permissions as the runtime user. The `~/.holdspeak/connector_packs/`
path is itself the trust boundary (it's the user's own home
directory).

We considered but rejected: running user packs in a subprocess
or sandbox. The local-only single-user model means the user
already trusts code in their home dir; adding a sandbox here
would be ceremony, not safety.
