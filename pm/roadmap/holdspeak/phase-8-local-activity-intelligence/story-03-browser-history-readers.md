# HS-8-03 - Safari and Firefox history readers

- **Project:** holdspeak
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HS-8-01, HS-8-02
- **Unblocks:** actual local activity ingestion
- **Owner:** unassigned

## Problem

HoldSpeak needs source readers that can safely import Safari and Firefox
history metadata into the activity ledger without mutating browser
databases or depending on live browser state. In this personal local
tool, available readers should run by default once the persistence and
privacy controls exist.

## Scope

- **In:**
  - Safari reader using the audited schema and safe copy path.
  - Firefox profile discovery and `places.sqlite` reader.
  - Default-enabled import behavior for readable local sources.
  - Copy main SQLite files plus `-wal`/`-shm` companions before reading.
  - Incremental import using per-source checkpoints.
  - Tests with fixture SQLite databases.
- **Out:**
  - Page content scraping.
  - Cookies, cache, credentials, or private browsing.
  - Network calls.

## Acceptance Criteria

- [ ] Safari fixture history imports into the ledger.
- [ ] Firefox fixture history imports into the ledger.
- [ ] Locked/live database strategy is safe and read-only.
- [ ] WAL-mode databases are copied with companion files where present.
- [ ] Readable sources are enabled by default.
- [ ] Incremental import avoids reimport churn.
- [ ] Focused and full tests pass.

## Test Plan

- To be finalized after HS-8-02.
