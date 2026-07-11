# HSU-3-03 — Trust gate attacks (off-loopback, no-telemetry, schema refusal)

- **Project:** holdspeak-uat
- **Phase:** 3
- **Status:** blocked
- **Depends on:** none
- **Owner:** unassigned

## Problem

The key-never-syncs promise is now *attacked* (shipped). The remaining
trust-boundary claims are still written in the imagined voice: pack-d/05 asserts
the loopback gate "would require one off-loopback"; no-telemetry and the
schema-safe upgrade are described, never fired (`PROTOCOL-COVERAGE.md` §3.6). A
stranger never sees the gate *reject* anything. This story turns each into a
staged do-then-attack beat backed by a probe.

## Scope

- In:
  - A probe `nonloopback_request_rejected`: on a LAN-bound run, a request to a
    protected route WITHOUT the token returns 401, and WITH it returns 200
    (`/health` stays open). Needs the conductor to expose the run's LAN URL to
    the probe.
  - A probe `no_network_beacon`: an idle run emits no outbound beacon over a
    window (best-effort: a local capture / a deny-by-default egress check, or a
    documented honest limitation if full packet capture is out of reach).
  - A probe `newer_db_refused_untouched` + crafted-schema seed recipes
    (`crafted-newer-schema-db` / `crafted-older-schema-db`): boot over a DB whose
    schema version is ahead, assert the product refuses and leaves it untouched
    (the safe-schema-matrix promise).
  - Flip pack-d/05 (loopback gate), pack-d/09 (no-telemetry), pack-d/10
    (schema-safe) to staged beats.
- Out: any product change; a real adversary network (a bounded local check only).

## Acceptance criteria

- [ ] `nonloopback_request_rejected` proves a tokenless off-loopback request is
      401 and a tokened one is 200 — the gate rejects, live.
- [ ] `newer_db_refused_untouched` boots over a crafted ahead-schema DB and
      asserts refusal + the DB file unmodified.
- [ ] `no_network_beacon` either asserts an idle run is silent or documents the
      honest limit of what the harness can observe (never a false green).
- [ ] The unblocked pack-d beats carry real verdicts; tests self-skip where a
      capability (LAN bind, capture) isn't available in CI.

## Test plan

- Integration: LAN-bound run → tokenless 401 / tokened 200; crafted-DB refusal;
  idle-beacon check.
- Manual/device: n/a.

## Notes / open questions

- **Owner decision, 2026-07-09:** do not schedule or implement this story for
  the early MVP. Database drift/schema attacks, idle network observation, and
  token-gate hardening are explicitly below usability and functional progress.
  It remains blocked as historical context and requires a fresh owner decision
  before any work resumes.

- Read `web_auth.py` (`nonloopback_bind_blocked`, `verify_web_token`) and the
  schema-policy / backup-restore seams (`release.schema.safe_upgrade`) — mirror
  the product's own `test_db_schema_policy` / `web_auth` unit tests.
