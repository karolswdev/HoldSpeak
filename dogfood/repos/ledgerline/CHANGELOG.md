# Changelog

All notable changes to ledgerline are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to semantic versioning.

## [Unreleased]
### Added
- Tracking for LL-134: a `reason` field on reversing posting groups
  (chargeback / refund / correction) for audit. Append-only.

## [0.4.0] — 2026-05-04
### Added
- Reconciliation job (`reconcile`) that verifies the ledger sums to
  zero and agrees with the gateway; drift pages within the SLO.

### Fixed
- LL-122 partial: reconciliation now buckets by posting timestamp
  (work in progress for cross-day settlements).

## [0.3.1] — 2026-04-18
### Fixed
- **LL-118**: double-post under a gateway retry storm. The
  check-and-record on the idempotency key is now atomic; concurrent
  retries with the same key can no longer both post. Postmortem:
  `docs/POSTMORTEM-2026-04-double-post.md`.

## [0.3.0] — 2026-03-09
### Added
- Idempotency: the `Idempotency-Key` header and the
  `idempotency_keys` store. Retried charges are no-ops. (ADR-0002)

## [0.2.0] — 2026-02-03
### Added
- `POST /charges` FastAPI endpoint over the posting engine.

## [0.1.0] — 2026-01-12
### Added
- The append-only double-entry posting engine (`post`, `reversal`)
  on SQLite. (ADR-0001)
