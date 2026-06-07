# Phase 50 — Release Readiness ("cut a real 0.x")

**Status:** IN PROGRESS (4/7). Opened 2026-06-07 on user direction, right after
Phase 49 closed + merged (PR #33). Picked from the [project backlog](../BACKLOG.md)
candidate C: the bet that actually lets the open-source push ship publicly.

**Last updated:** 2026-06-07 (HS-50-04 done: doctor + config honesty. `doctor` now
has a Database check (read-only `read_schema_version` probe: current=PASS,
older=WARN, newer=FAIL, unreadable=WARN) that also flows into `/api/setup/status`;
`Config` carries a `config_version` that coerces an older/unversioned shape forward
without dropping fields and keeps + flags a newer one; the config doctor check
flags a newer config. Next: HS-50-05, verified clean-machine install.)

## The thesis — why this phase

**HoldSpeak has shipped 49 phases of features and has never been cut as a real
release.** It is a brilliant prototype with no front door. Grounded in the live
tree:

- **The next schema bump destroys user data.** `db/core.py:_ensure_schema`
  (l.625-658) rebuilds the schema via a single `executescript` whenever the stored
  version is below `SCHEMA_VERSION` (l.28). There is no backup and no
  newer-than-known guard. This is the single most dangerous thing in the repo for a
  real release.
- **The version is two different numbers.** `pyproject.toml:3` says `0.2.1`;
  `holdspeak/__init__.py:3` says `0.1.0`. There is no single source of truth.
- **`doctor` never looks at the database.** 16 checks, none for the schema/config
  state it depends on (`commands/doctor.py`).
- **Config can silently drop fields.** `Config.load()` tolerates unknown keys and
  has no `config_version` (`config.py:405-448`), so a rename/remove is invisible.
- **The install pins git HEAD, not a tag** (`scripts/install.sh`), so "install
  HoldSpeak" is not reproducible.

## Goal

Make HoldSpeak safe to install, upgrade, and trust: one true version, a
safe-by-default schema policy (never silently destroy data; refuse-newer,
backup-then-apply-older, no-op-equal, create-fresh), a backup the user can run, a
`doctor` that tells the truth about the DB and config it found, config that can
evolve, a verified clean-machine install, and honest docs with an upgrade/backup
policy. Without changing meeting capture, dictation, plugins, synthesis, or
routing.

## Scope

- **In:** version single-source-of-truth (HS-50-01); the safe schema policy
  (HS-50-02); backup + restore (HS-50-03); doctor + config honesty (HS-50-04);
  verified clean-machine install + pinned install contract (HS-50-05); a release +
  upgrade/backup policy doc + checklist (HS-50-06); closeout (HS-50-07).
- **Out:** product features; changing capture/dictation/plugins/synthesis/routing
  behavior; a historical migration ladder (there are no old versions deployed —
  this defines the *forward* contract); actually publishing to PyPI (this readies
  the gate; the publish act is a maintainer step once the gate is green).

## Exit criteria (evidence required)

- One source of truth for the version; the `0.1.0`/`0.2.1` mismatch gone; surfaced
  in `doctor` + an API/UI spot; a drift test pins it. (HS-50-01)
- `_ensure_schema` never silently rebuilds: refuse-newer, backup-then-apply-older,
  no-op-equal, create-fresh, each tested. (HS-50-02)
- A `holdspeak backup` path copies the live DB to a timestamped file and runs
  automatically before any destructive schema action; documented. (HS-50-03)
- `doctor` + `/api/setup/status` report real schema + config state honestly; a
  `config_version` field + coercion lands. (HS-50-04)
- The documented install path is actually run on a clean-ish environment and
  reaches a working `holdspeak doctor`; the install is pinned to a tag. (HS-50-05)
- A release + upgrade/backup policy doc + a release checklist; README/GETTING_STARTED
  reconciled + honest; doc guards green. (HS-50-06)
- A dogfood proving the safety matrix; full suite green; `final-summary.md`; phase
  CLOSED; PR to `main` merged on green; BACKLOG candidate C flipped to shipped.
  (HS-50-07)

## Invariants

- **Never destroy data on upgrade.** Backup before any destructive action;
  refuse a newer-than-known DB; never downgrade-rebuild.
- **Fresh-install path untouched.** An empty/absent DB is still created at the
  current version with zero friction.
- **Honest over silent.** doctor/config report unexpected state plainly; no silent
  coercion that hides a problem.
- **Behavior-preserving.** Capture, dictation, plugins, synthesis, routing stay
  byte-identical. Existing tests green; the temp-DB / `reset_database()` test idiom
  keeps working.
- **Forward policy, not historical ladder.** Define safe upgrades from this release
  on; do not retrofit migrations for versions that never shipped.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-50-01 | One true version (single source + surfaced) | done | [story-01-version-ssot.md](./story-01-version-ssot.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-50-02 | Safe-by-default schema policy | done | [story-02-schema-policy.md](./story-02-schema-policy.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-50-03 | Backup + restore | done | [story-03-backup-restore.md](./story-03-backup-restore.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-50-04 | doctor + config honesty | done | [story-04-doctor-config-honesty.md](./story-04-doctor-config-honesty.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-50-05 | Verified clean-machine install + pinned contract | backlog | [story-05-install-verification.md](./story-05-install-verification.md) | — |
| HS-50-06 | Docs: release + upgrade/backup policy | backlog | [story-06-docs.md](./story-06-docs.md) | — |
| HS-50-07 | Closeout — dogfood + final-summary + PR | backlog | [story-07-closeout.md](./story-07-closeout.md) | — |

## Where we are

**HS-50-01 (one true version) is done.** `holdspeak/__init__.py` resolves
`__version__` from package metadata with a `pyproject.toml` regex fallback, so the
`0.1.0`/`0.2.1` split is gone. The version shows in the `doctor` runtime check and
the `/api/setup/status` payload. `scripts/install.sh` pins a tag via
`HOLDSPEAK_REF` (default `v0.2.1`, `main` dev fallback).
`tests/unit/test_version_ssot.py` pins it.

**HS-50-02 (safe-by-default schema policy) is done — the heart of the phase.**
`db/core.py:_ensure_schema` now implements the four-way matrix: create-fresh,
no-op-equal, backup-then-apply-older, refuse-newer. `backup_database()` copies the
SQLite file to a timestamped, non-clobbering sibling before any destructive
action; `SchemaVersionError` refuses a newer-than-known DB and leaves it
byte-for-byte untouched. The fresh-install path is unchanged. One honest
correction to the scaffold framing: the live `SCHEMA_SQL` is fully additive today
(`CREATE TABLE IF NOT EXISTS`, no `DROP`/`DELETE`), so there was no literal wipe to
fix; the real unguarded holes closed are "a newer DB silently run by an older
build" and "no backup before a future migration." `tests/unit/test_db_schema_policy.py`
covers all four cells.

**HS-50-03 (backup + restore) is done.** `backup_database` takes a consistent
snapshot via SQLite's `Connection.backup`; `restore_database` validates the backup,
snapshots the current DB first, then puts it in place. `holdspeak backup` and
`holdspeak restore` are wired into the CLI.

**HS-50-04 (doctor + config honesty) is done.** `doctor` has a read-only Database
check (`read_schema_version` probe: current=PASS, older=WARN, newer=FAIL,
unreadable=WARN) that flows into `/api/setup/status` too. `Config` carries a
`config_version` that coerces an older/unversioned shape forward without dropping
fields and keeps + flags a newer one; the config check also flags a newer config.
Honest over silent in both places.

Next: **HS-50-05** (verified clean-machine install) actually runs the documented
install path on a clean-ish environment, fixes whatever breaks, and captures the
transcript. This is the story that needs network for a real `pip install` from git,
so it may run via the `! <cmd>` session prefix or `dangerouslyDisableSandbox`.
**Read [`AGENT-BRIEF.md`](./AGENT-BRIEF.md) first.** Sequence: 01 -> 02 -> 03 -> 04
-> 05 -> 06 -> 07.

## Active risks

- **Closing the data-loss path incorrectly.** Mitigation: the explicit
  refuse-newer / backup-then-apply / no-op / create-fresh matrix, each tested;
  backup before any destructive action.
- **Breaking the fresh-install path.** Mitigation: the fresh-create invariant +
  the dogfood + the existing temp-DB test idiom.
- **Version drift returning.** Mitigation: a single source + a drift test.
- **Network-blocked sandbox for the real install run.** Mitigation: HS-50-05 runs
  the install via the `! <cmd>` session prefix or `dangerouslyDisableSandbox`, and
  captures the real transcript.

## Decisions made (this phase, from user)

- **Release-readiness next.** The user picked backlog candidate C as Phase 50:
  "need this product to finally not suck" — make it formally shippable rather than
  adding more features to something that cannot be released.

## Decisions deferred

- **Version mechanism.** `importlib.metadata` read vs a pinned `__version__`
  constant. Settle in HS-50-01, favoring a single source the drift test can pin.
- **Restore depth.** "Here is your backup file" vs a real `holdspeak restore`
  command. Settle in HS-50-03, favoring the safe minimum first.
- **PyPI now or later.** Whether to actually publish or only ready the gate. Out of
  scope for the build; revisit at close.
