# Evidence — HS-50-07: Closeout (dogfood + final-summary + PR)

Write-once record of the verified exit for Phase 50. The phase is CLOSED (7/7).

## The dogfood (`dogfood-transcript.txt`)

A self-contained script drives the DB layer directly (stamps the
`schema_version` table; bumps the in-process `SCHEMA_VERSION` to simulate a
version change without a real schema edit). No real mic, no LLM. It prints PASS
per check and exits non-zero on any failure. Every line passed:

- **One true version.** `holdspeak.__version__` (0.2.1) equals the
  `pyproject.toml` version.
- **Fresh / empty DB.** Created at the current `SCHEMA_VERSION`; `doctor` reports
  it PASS.
- **Same version.** No-op reopen takes no backup.
- **Older DB.** A backup is taken, the schema is applied, and the seeded row is
  intact in both the live DB and the backup; `doctor` PASS after the upgrade.
- **Newer DB.** Refused with `SchemaVersionError`; the message says "newer
  HoldSpeak" and "left untouched"; the file is byte-for-byte unchanged; `doctor`
  reports FAIL.
- **Config honesty.** A config newer than this build is kept (not silently reset)
  and still loads its data.

Final line: `RESULT: PASS - HoldSpeak is safe to install, upgrade, and trust.`
(exit 0). The transcript also shows the real machinery firing: the
"Backed up ... before applying the schema" warning on the older-DB path and the
"config_version 4 is newer than this build" warning on the config path.

## Suite + build

```
uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2451 passed, 17 skipped

cd web && npm run build
-> Complete; 12 pages built

git ls-files holdspeak/static/_built
-> (empty: 0 tracked)
```

## Closeout bookkeeping

- `final-summary.md` written (the full phase narrative + invariants + deferred
  maintainer steps).
- Phase status flipped to **CLOSED (7/7)**; the story-status table and "Where we
  are" updated.
- Project `README.md` (Current phase + Last updated + phase row) flipped to CLOSED.
- `BACKLOG.md` candidate C flipped to **shipped → phase-50 (CLOSED 7/7)** (table
  row + section heading).
- PR to `main` opened and merged on green CI.

## Deferred (recorded in final-summary)

- The PyPI publish is a deliberate maintainer step once the gate is green.
- Pushing the `v0.2.1` tag is a release-time step; `install.sh` already pins it by
  default with `HOLDSPEAK_REF=main` as the working dev fallback until then.
