# HSEGHS001HS104-135-05 — The privacy proof

- **Project:** holdspeak
- **Phase:** 135
- **Status:** ready
- **Depends on:** 135-01, 135-02, 135-03
- **Unblocks:** 135-06
- **Owner:** primary adjudicator

## Problem

Encryption claims are not evidence. The release gate is a hostile sentinel sweep
through every durable and observable surface plus enforceable refusal policy.

## Scope

- **In:** SECURITY/threat-model update; data-class/policy/refusal table; byte/table/
  log/error/receipt/broadcast/sync/export/FTS/Cadence leak tests; network/model spies;
  removal of adjacent content-bearing logging found by the audit when in scope.
- **Out:** compliance certification, legal advice, recovery/retention engine for
  features not shipped.

## Acceptance criteria

- [ ] Sentinels are absent from every forbidden surface after full lifecycle and
  forced failure paths; only authorized API responses/process memory decrypt them.
- [ ] Production key backend allow-list and no-fallback behavior are tested.
- [ ] Policy code hard-refuses scoring/ranking, employment recommendations,
  sentiment/personality/health/flight-risk inference, activity proxies, automated
  opportunity allocation, capture, model egress, sync, export, and connectors.
- [ ] SECURITY truthfully documents custody, no recovery/backup, device-only scope,
  and key-loss behavior without saying merely local equals secure.

## Test plan

- **Unit/integration:** dedicated no-leak and refusal matrices plus forced crypto,
  route, logger, sync, and projection failures.
- **Full gate:** parallel pytest excluding Metal, web tests/build, PMO checks.
- **Manual/device:** inspect raw files and live network activity during the walk.
