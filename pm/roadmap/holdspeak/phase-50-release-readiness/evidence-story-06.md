# Evidence — HS-50-06: Docs (release + upgrade/backup policy)

Write-once record of the dedicated docs story: the written policy for how
HoldSpeak versions itself, what happens to a user's data on upgrade, how to be
safe, and a maintainer release checklist. Every claim is grounded in the code
shipped earlier in the phase.

## What shipped

**`docs/RELEASING.md`** (new) — the release + upgrade/backup policy:
- **Versions, and where they live.** One source of truth (`pyproject.toml`),
  `__version__` read from package metadata, `SCHEMA_VERSION`, `config_version`.
  Grounded in HS-50-01 and HS-50-04.
- **What happens to your database on upgrade.** The four-way matrix in plain
  words: no database -> create fresh; same version -> nothing; older -> back up
  then apply; newer -> refuse and leave untouched. Plus the config coercion rule.
  Grounded in HS-50-02 (`db/core.py:_ensure_schema`) and HS-50-04 (`config.py`).
- **Back up before you upgrade.** `holdspeak backup` / `holdspeak restore`, where
  the files go, and that restore snapshots the current DB first. Grounded in
  HS-50-03 (`commands/backup.py`, `db/core.py:backup_database`/`restore_database`).
- **What doctor tells you.** The Database and Config check states a user will see.
  Grounded in HS-50-04 (`commands/doctor.py`).
- **Maintainer release checklist.** Bump the version in one place, confirm the
  code agrees, bump `SCHEMA_VERSION`/`CONFIG_VERSION` only if the shape changed,
  run the suite, verify the clean install, set the `HOLDSPEAK_REF` default to the
  tag, tag and push, then publish as a separate deliberate step.

**README reconciliation** (`README.md`)
- New "Upgrading and your data" subsection under install: the one-file database,
  `holdspeak backup` / `restore`, safe-by-default upgrades, and a link to
  `docs/RELEASING.md`. The existing "early / pre-release ... isn't on PyPI yet"
  status line is already honest and was left as-is; the install commands already
  match the verified path.

**GETTING_STARTED reconciliation** (`docs/GETTING_STARTED.md`)
- The diagnostics section now notes that `doctor` reports the database/config
  state, and adds a short backup-before-upgrade pointer to `RELEASING.md`.

## Voice + guards

- Humanizer voice applied: no em or en dashes in the new prose (verified by grep),
  plain and direct, no rule-of-three padding.
- The doc-drift / dangling-link / image-ref guards are green, so every relative
  link in the new and edited docs resolves (`RELEASING.md` links to
  `GETTING_STARTED.md`, `../README.md`, `MODELS.md`; the README and
  GETTING_STARTED links to `docs/RELEASING.md` / `RELEASING.md` resolve).

```
uv run pytest -q tests/unit/test_doc_drift_guard.py
-> 5 passed

uv run pytest -q -k "doc_drift or link or doc_guard or doc" --ignore=tests/e2e/test_metal.py
-> 75 passed, 2 skipped
```

## Grounded, not aspirational

The policy describes only behavior that shipped in HS-50-02 through HS-50-05. It
is forward-looking by design: it does not document a historical migration ladder,
because none was ever published (the standing greenfield reality). It states
plainly that publishing to PyPI is a separate manual step the gate readies but
does not perform.
