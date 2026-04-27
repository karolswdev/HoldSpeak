# Phase 8 Summary - Local Activity Intelligence

Phase 8 shipped a private, local-first Local Attention Ledger for
HoldSpeak.

## Shipped Workflows

- Audit local browser-history sources and privacy boundaries.
- Persist normalized activity records and import checkpoints.
- Read Safari and Firefox history through read-only SQLite snapshots.
- Copy WAL/SHM companions so recent Safari rows are not missed.
- Extract deterministic work entities from URL/title metadata.
- Make local activity context available to plugins and dictation
  contracts.
- Expose `/activity` with source visibility, recent records, pause,
  refresh, retention, clear controls, and domain exclusions.
- Add project mapping rules with preview, CRUD, backfill, and import-time
  assignment.
- Scope optional assisted enrichment connectors for calendar/Outlook,
  Firefox extension capture, and local `gh`/`jira` CLI annotations.

## Privacy Contract

- No cookies.
- No credentials.
- No cache or page body scraping.
- No private browsing access.
- No hidden network enrichment.
- Default browser-history ledger is local and inspectable.
- Assisted enrichment remains individually visible, disabled by default,
  previewable, and deletable.

## Verification

Focused activity sweep:

```text
91 passed in 2.59s
```

Full non-Metal regression:

```text
1155 passed, 13 skipped in 27.84s
```

Whitespace:

```text
git diff --check
```

No output.
