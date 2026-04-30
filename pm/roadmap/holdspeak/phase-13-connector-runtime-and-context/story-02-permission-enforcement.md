# HS-13-02 - Permission enforcement at runtime gates

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-01
- **Unblocks:** trustworthy local-user packs (HS-13-04)
- **Owner:** unassigned

## Problem

Phase 11's manifest declares permissions (`shell:exec`,
`network:outbound`, `loopback:http`, etc) but the runtime
doesn't check them. A connector pack can declare
`requires_network: false` and still call out to GitHub. The
permissions are documentation, not enforcement — exactly the
kind of "rule that everybody nods at and nobody honors" we
shouldn't ship.

## Scope

- **In:**
  - Build a `PermissionGate` helper in
    `holdspeak/connector_runtime.py` (new) that wraps the
    operations connector packs are allowed to invoke
    (`run_subprocess`, `open_outbound_socket`, `read_file`).
  - Each gate consults the calling pack's manifest before
    permitting the operation; permission missing → raise
    `PermissionDenied` with the connector id, requested
    operation, and the manifest's declared permissions in the
    error.
  - `activity_github.run_github_cli_enrichment` and
    `activity_jira.run_jira_cli_enrichment` route their
    `subprocess` calls through `PermissionGate.run_subprocess`.
  - Web extension event ingestion already binds 127.0.0.1 by
    default; the gate adds a defense-in-depth check that the
    connector's manifest has `loopback:http` before processing
    any extension event.
  - Permission-violation rejections persist a connector
    `last_error` so the operator sees them in `/activity`.
- **Out:**
  - Sandbox / process isolation. Permission gates are an
    in-process check, not a security boundary.
  - Per-call permission grants (e.g. "this one subprocess
    only"). The check is per-pack, declared once.

## Acceptance Criteria

- [ ] `PermissionGate.run_subprocess` raises `PermissionDenied`
  when the calling pack's manifest lacks `shell:exec`.
- [ ] Same for `open_outbound_socket` (`network:outbound`) and
  `read_file` (`fs:read`).
- [ ] gh/jira pack runs route through the gate.
- [ ] A `PermissionDenied` exception bubbles up to the runtime
  and is persisted as `connector.last_error`; the `/activity`
  Connectors panel shows it.
- [ ] Unit tests cover every permission/operation pair.
- [ ] Existing pack run tests still pass (the gh/jira packs
  declare the right permissions, so behaviour is unchanged for
  honest packs).

## Test Plan

- Unit: build a fake "evil" pack with `requires_network: false`
  and assert the gate rejects an outbound socket attempt.
- Unit: same for `shell:exec` against a pack lacking it.
- Integration: run gh/jira enrichment through the gate path,
  assert success (manifests already declare `shell:exec` +
  `network:outbound`).
- Integration: dry-run does not trip the gate (it's mutation-
  free and shouldn't shell out).

## Notes

In-process permission checks aren't a security boundary — a
malicious pack can still bypass them by calling `subprocess`
directly. The point is *honest* enforcement: a pack that
declares one shape and behaves differently fails loud, in
tests, every time.
