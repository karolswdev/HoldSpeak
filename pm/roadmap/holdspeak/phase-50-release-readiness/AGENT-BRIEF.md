# Phase 50 — Agent Brief (read this first)

You are picking up **Phase 50 — Release Readiness ("cut a real 0.x")** for
HoldSpeak. This brief is self-contained: the mission, the exact code seams (mapped
against the live tree at scaffold time), the rules of the road, and a per-story
definition of success. Read it, then read
[`current-phase-status.md`](./current-phase-status.md) and the story you're
working. If this brief disagrees with the live status docs or the codebase, the
**codebase wins** — re-verify before trusting any line or number below.

---

## 0. Mission

HoldSpeak has shipped 49 phases of deep features. It has never been cut as a real
release. The DB is `SCHEMA_VERSION = 1`, greenfield, and **not release-stable**:
the next schema bump silently rebuilds an existing user's database and loses their
data, with no backup. The in-code version disagrees with the package version. The
install script pins git HEAD, not a tag. `doctor` never looks at the database it
depends on.

This is the bet that lets the open-source push actually **ship**. Everything else
polishes a thing that is not formally shippable.

Make HoldSpeak safe to install, upgrade, and trust:

- **One true version,** surfaced honestly.
- **A safe-by-default schema policy:** never silently destroy a user's data on
  upgrade. Refuse a newer-than-known DB; back up before any destructive action.
- **Backup the user can run** before they upgrade.
- **`doctor` that tells the truth** about the database and config it found.
- **Config that can evolve** without silently dropping fields.
- **A clean-machine install that actually works,** documented as the verified path.
- **Docs that state the upgrade/backup policy** and a release checklist.

This phase is **release engineering + safety**. It does not add product features.
It does not change meeting capture, dictation, plugins, or synthesis behavior.

---

## 1. The one thing you must not get wrong

**Never destroy a user's data on upgrade.** Today
`holdspeak/db/core.py:_ensure_schema` rebuilds the schema whenever the stored
version is below `SCHEMA_VERSION` (`db/core.py:625-658`), and `SCHEMA_SQL` is a
single `executescript` (`db/core.py:31-587`). Bump the version and an existing
user's data is gone.

- **Refuse, don't wipe.** A DB whose stored version is **newer** than this build
  must be refused with a clear message (do not downgrade-rebuild it). A DB whose
  version is **older** must be backed up before any schema change, and the user
  told where the backup is.
- **Backup before any destructive action, always.** No migration/rebuild path runs
  without first copying the SQLite file to a timestamped backup.
- **Honest over silent.** `doctor` and `/api/setup/status` report the real schema
  and config state, including "unexpected" / "newer than this build". No silent
  coercion that hides a problem.
- **Behavior-preserving.** This is plumbing. Meeting capture, dictation, plugins,
  synthesis, and routing stay byte-identical. The default fresh-install path
  (empty DB -> created at the current version) must be unchanged.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md` §"Contract template", **7** checkboxes; `mkdir -p
  .tmp` first; the hook validates and deletes it). A story flipping to `done`
  ships its `evidence-story-{n}.md` in the same commit; **one** done-flip per
  commit. The phase-exit story needs `evidence-story-{last}.md` **and**
  `final-summary.md` in the same commit. Status line is the list-item form
  `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates: the story header status,
  this phase `current-phase-status.md` (row + Last-updated + "Where we are"), the
  project `README.md` (phase row + Current-phase + Last-updated), and any canon doc
  the story touched (`README.md`, `docs/GETTING_STARTED.md`, `pyproject.toml`).
- **One PR per phase, merged when CI green** (Unit · Integration macOS · E2E macOS
  · Linux Smoke · Route screenshots). Work on a phase branch; at close, push +
  open a PR to `main` + merge with a merge commit on green. Memory
  `feedback_merge_phases_via_pr`.
- **Tests actually run.** Flip a story to `done` only after running the relevant
  tests and reading the output. Full suite:
  `uv run pytest -q --ignore=tests/e2e/test_metal.py`. Type-check is not validation.
- **Greenfield discipline, but this is the exception that defines the policy.** The
  repo has been greenfield-with-no-compat by design (memory
  `feedback_holdspeak_not_really_released`). This phase is where that ends: it
  *defines* the forward compatibility/upgrade contract. Do not retrofit a
  migration ladder for historical versions (there are none in the wild). Do build
  the **forward** policy: from this release on, upgrades are safe.
- **Write like a human.** No em or en dashes, no emoji-decorated bullets, no
  rule-of-three padding, no "not X but Y". Plain and direct. (`humanizer` skill;
  `docs/internal/DOCS_STYLE.md` is the voice authority.)

---

## 3. The ground truth (code seams, mapped + verified at scaffold)

Re-verify before trusting; line numbers drift.

**Version (single-source-of-truth is broken today):**
- `pyproject.toml:3` — `version = "0.2.1"`.
- `holdspeak/__init__.py:3` — `__version__ = "0.1.0"` (**mismatch**).
- `pyproject.toml:172-173` — console entry `holdspeak = "holdspeak.main:main"`.
- `scripts/install.sh` (~l.15, ~l.134) — installs from `git+https...@main` HEAD,
  not a tag; runs `holdspeak doctor` post-install (~l.161).

**DB schema (the data-loss risk):**
- `holdspeak/db/core.py:28` — `SCHEMA_VERSION = 1`.
- `holdspeak/db/core.py:31-587` — `SCHEMA_SQL` (full schema, one `executescript`).
- `holdspeak/db/core.py:625-636` — `_ensure_schema()` reads `MAX(version)` from the
  `schema_version` table; if `current < SCHEMA_VERSION`, calls `_apply_schema()`.
- `holdspeak/db/core.py:638-658` — `_apply_schema()` runs `SCHEMA_SQL` +
  records the version. **No backup. No newer-than-known guard.**
- `holdspeak/db/core.py:27` — `DEFAULT_DB_PATH = ~/.local/share/holdspeak/holdspeak.db`.
- Phase 31 (HS-31-04) squashed the old migration ladder to this single greenfield
  schema, so there is no ladder to reuse and none needed for historical versions.

**doctor + setup status:**
- `holdspeak/commands/doctor.py` — 16 checks; `run_doctor_command` at l.996-1027;
  **no database/schema check today**.
- `holdspeak/web/routes/setup.py:23-39` — `GET /api/setup/status` ->
  `build_setup_status()`.
- `holdspeak/setup_status.py:151-195` — `build_setup_status()` composes doctor
  checks + trust + presence + first-run.
- Tests: `tests/...test_doctor_command.py`, `test_setup_status_doctor_drift.py`
  (`-k doctor`).

**Config:**
- `holdspeak/config.py:15` — `CONFIG_FILE = ~/.config/holdspeak/config.json`.
- `holdspeak/config.py:405-448` — `Config.load()` tolerates unknown keys (warns,
  defaults the section). `Config.save()` at l.450-456. **No `config_version`.**

**Backup / export (partial):**
- `holdspeak/meeting_exports.py:192-245` — per-meeting export (md/json/txt).
- `holdspeak/web/routes/meetings.py:450-499` — `GET /api/meetings/{id}/export`.
- **No whole-DB backup anywhere.** The SQLite file is a single path; a safe backup
  is a file copy (or `sqlite3` `.backup`) to a timestamped sibling.

**Docs to reconcile (already fairly honest):**
- `README.md:20-22` — "early / pre-release ... isn't on PyPI yet" (accurate; keep
  honest, sync any version string).
- `README.md:92-112`, `docs/GETTING_STARTED.md:13-59` — clone + `uv pip install -e .`
  install path + first-run `/welcome`.

---

## 4. Per-story definition of success

- **HS-50-01 — One true version.** A single source of truth for the version
  (read package metadata via `importlib.metadata`, or pin `__version__` to
  `pyproject`), the `0.1.0`/`0.2.1` mismatch gone, the version surfaced in `doctor`
  and an API/UI spot, and `scripts/install.sh` able to install a pinned
  tag (with a documented `@main` dev fallback). A test pins code-version ==
  package-version so it cannot drift again.
- **HS-50-02 — Safe-by-default schema policy.** `_ensure_schema` never silently
  rebuilds: a **newer** stored version is refused with a clear error (no
  downgrade-wipe); an **older** version triggers a backup-then-apply path (not a
  bare rebuild); a matching version is a no-op; a fresh empty DB is created exactly
  as today. The data-loss path is closed. Tests cover newer/older/equal/fresh.
- **HS-50-03 — Backup + restore.** A `holdspeak backup` command (and/or a guarded
  API) that copies the live DB to a timestamped file, invoked automatically before
  any destructive schema action (HS-50-02), and documented. Restore is at least
  "here is the file, copy it back"; a real restore path is a plus.
- **HS-50-04 — doctor + config honesty.** A database/schema check added to `doctor`
  and `/api/setup/status` (current DB version vs this build, "unexpected/newer"
  flagged), plus a `config_version` field on `Config` with load-time coercion so an
  evolving config does not silently drop renamed/removed fields. Honest reporting,
  no silent fixes that hide a problem.
- **HS-50-05 — Verified clean-machine install + install contract.** Actually run
  the documented install path on a clean-ish environment (fresh venv / temp HOME),
  fix whatever breaks, pin the install to a tag, and capture the transcript as
  evidence. The "from clone" and "from script" paths both reach a working
  `holdspeak doctor`.
- **HS-50-06 — Docs (dedicated docs story).** A release + upgrade/backup policy
  doc (supported versions, what happens on upgrade, backup-before-upgrade, what
  `doctor` reports on unexpected state) and a maintainer release checklist;
  README/GETTING_STARTED reconciled and honest; doc guards green; every claim
  grounded in code.
- **HS-50-07 — Closeout.** A dogfood that proves the safety properties (fresh
  create; older-version -> backup-then-apply; newer-version -> refused, untouched;
  `doctor` reports schema honestly), full suite green, `final-summary.md`, phase
  CLOSED, PR to `main` merged on green, BACKLOG candidate C flipped to shipped.

---

## 5. Gotchas that will bite you

- **The silent rebuild is the whole point.** Do not "fix" it by adding a real
  migration ladder for old versions (there are none deployed). Fix it by making
  the *forward* policy safe: refuse-newer, backup-then-apply-older, no-op-equal.
- **Don't break the fresh-install path.** An empty/absent DB must still be created
  at the current version with zero friction. Most tests + the dogfood assume this.
- **`reset_database()` + the temp-DB test idiom** (used everywhere, e.g.
  `tests/integration/test_web_meeting_*`) must keep working. Seed deterministic DB
  paths in tests; never touch the developer's real `~/.local/share/holdspeak`.
- **Version single-source.** If you read from `importlib.metadata.version`, it only
  works for an installed package; keep a sensible fallback for the editable/source
  run, and make the drift test robust to both.
- **install.sh runs against the network.** The sandbox cannot reach the network for
  a real `pip install` from git; the clean-machine verification (HS-50-05) may need
  `dangerouslyDisableSandbox` or a documented manual run via the `! <cmd>` session
  prefix. Capture the real transcript either way.
- **Doctor output is user-facing copy.** Apply the humanizer voice to any new
  check's messages.

---

## 6. Where to start

`HS-50-02` (the safe schema policy) is the heart, but `HS-50-01` (one true version)
is the cheapest honest win and unblocks the install/doctor surfacing. Suggested
sequence: 01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07. Read
`story-02-schema-policy.md` first to internalize the refuse-newer /
backup-then-apply / no-op-equal / create-fresh matrix; that matrix is the phase.

Keep it safe-by-default, keep the fresh-install path untouched, never destroy data,
and tell the truth in `doctor`. This is the phase that turns 49 phases of features
into a product someone can actually install, upgrade, and trust.
