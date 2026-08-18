# HS-139-08 — Open throttle

- **Project:** holdspeak
- **Phase:** 139
- **Status:** ready
- **Depends on:** 139-02
- **Unblocks:** 139-07
- **Owner:** delegated Opus worker; orchestrator adjudicates

## Problem

OWNER RULING (2026-08-17): the security ceremony throttles the owner's
own pipelines with zero threat-model payoff for a single-owner local
product — "loosen them to the point where we may be able to tap into
them soon." This completes the standing ledger-not-gate doctrine:
admission ceremony survives ONLY where it buys a receipt, provenance,
or undo; policy defaults to yes.

## Scope

- **In:** POSTURE (control mode) defaults to YOLO on fresh installs and
  is set to YOLO in the seed; `allow_actuators` defaults true with a
  permissive allowlist default; off-by-default MCP capabilities
  (including the People family's process capability) default ON for the
  local owner process; webhook/allowlist defaults become permissive;
  any remaining consent ceremony that neither produces a receipt nor
  provenance nor undo is removed, with the receipt path proven intact
  where it fires. Each loosened dial is listed in the story report with
  its old → new default.
- **Out — THE HARD BOUNDARY (does not loosen):** encryption at rest and
  key custody (People sidecar, Keychain allow-list); the People policy
  hard-refusal matrix (scoring/surveillance/employment inference); egress
  badges and disclosure surfaces (information, not friction); the
  receipt/refusal ledger itself. Sync/export/connector refusals for
  People content stay (policy, not ceremony).

## Acceptance criteria

- [ ] Fresh install: POSTURE=YOLO, actuators on, MCP families on; a
  fresh-HOME boot test asserts the open posture.
- [ ] Every kernel-admitted operation still writes its receipt; the
  refusal path still fires for the hard-boundary list (tests).
- [ ] The report enumerates every changed default old → new; nothing on
  the hard-boundary list changed (grep + tests green:
  test_people_policy, test_people_no_leaks, custody tests).
- [ ] The owner's live config lands on YOLO at the sitting walk.

## Test plan

- **Unit:** fresh-config default tests; receipt-intact tests per
  loosened gate; hard-boundary suites green.
- **Manual:** 139-07 walk shows the open posture on glass.
