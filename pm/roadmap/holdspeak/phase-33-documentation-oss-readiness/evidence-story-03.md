# Evidence — HS-33-03 (`docs/` reorganization + index)

**Shipped:** 2026-06-03. `docs/` now cleanly separates user-facing guides from
internal/historical plans, with a `docs/README.md` index that surfaces the user
journey. History preserved via `git mv`; all live inbound links repointed; a
lightweight link-check added so the move can't silently rot.

## What changed

### Moved to `docs/internal/` (13 files, via `git mv`)

`CROSS_PLATFORM_ROADMAP`, `CROSS_PLATFORM_TASK_BOARD`, `LINUX_PORT_EXECUTION`,
`LINUX_PORT_PLAN`, `RELEASE_HARDENING_CHECKLIST`, and the 8 `PLAN_*` specs
(`PLAN_ACTIVITY_ASSISTED_ENRICHMENT`, `PLAN_ARCHITECT_PLUGIN_SYSTEM`,
`PLAN_INTEL_STREAMING`, `PLAN_MEETING_INTEL_PI`, `PLAN_MEETING_MODE`,
`PLAN_PHASE_DICTATION_INTENT_ROUTING`, `PLAN_PHASE_MULTI_INTENT_ROUTING`,
`PLAN_PHASE_WEB_FLAGSHIP_RUNTIME`).

### Stayed user-facing in `docs/` (11 files)

`GETTING_STARTED`, `USER_GUIDE`, `MEETING_MODE_GUIDE`, `INTELLIGENT_TYPING_GUIDE`,
`AGENT_HOOK_INSTALL`, `FIREFOX_EXTENSION_GUIDE`, `CONNECTOR_DEVELOPMENT`,
`DEVICE_PROTOCOL`, `AIPI_LITE_DEV_WORKFLOW`, `SECURITY`, `MODELS` (from HS-33-01).

### New `docs/README.md` index

A "Start here" user path (Getting Started → User Guide → Meeting Mode → Models →
Intelligent Typing → Security), a "Reference & integrations" group, and an
"Internal / historical plans" pointer to `docs/internal/` (with a note that the
planning-of-record lives under `pm/roadmap/holdspeak/`).

### Live inbound links repointed (`docs/X.md` → `docs/internal/X.md`)

- **`CLAUDE.md`** — the "Source canon" list (4 `PLAN_*` entries).
- **`pm/roadmap/holdspeak/README.md`** — the *live* "Source canon" section + the
  DIR-01 glossary pointer (5 `docs/PLAN_*` refs). (This is the actively-maintained
  roadmap index, not a frozen phase record — see "Deviations".)
- **Root `README.md`** — the plugin-RFC link.
- **Source docstrings** — 11 `holdspeak/plugins/dictation/*.py` +
  `holdspeak/commands/dictation.py` files that cite
  `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`.
- **`scripts/release_gate.py`** — the `--checklist` default path
  (`docs/RELEASE_HARDENING_CHECKLIST.md` → `docs/internal/…`).
- **`tests/integration/test_web_flagship_audit.py`** — the spec docstring ref.
- **`docs/internal/*.md`** — the internal docs' own `docs/X.md` cross-references
  to sibling internal docs.

### Link-check (new test)

`tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link`
— scans every live `docs/**/*.md` (excluding `docs/evidence/` snapshots) for
markdown links with a relative target and asserts each resolves. Catches a
dangling `[text](path)` introduced by a future move.

## Tests ran

- `uv run pytest -q tests/unit/test_doc_drift_guard.py` → **3 passed** (the
  existing stub-rot guard + the scan-sanity check + the new link-check). The
  link-check is non-vacuous: `docs/README.md` alone exercises ~15 relative links.
- `uv run pytest -q tests/integration/test_web_flagship_audit.py` → passed (its
  spec docstring path was repointed; no functional file-open on the moved path).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1953 passed, 15 skipped**.
- Repo-wide grep: **no** `docs/<moved>.md` reference remains outside frozen records
  (`docs/evidence/` + `pm/roadmap/holdspeak/phase-*`) and `docs/internal/`.

## Done-when

- [x] User-facing vs internal/historical docs separated; `docs/internal/` holds
      the plans (history preserved via `git mv`).
- [x] `docs/README.md` index surfaces the user journey.
- [x] No broken inbound links (incl. CLAUDE.md / roadmap source-canon refs); full
      suite green.

## Decisions / deviations

- **Layout = single `docs/internal/`** — the phase's deferred-decision default
  (one folder for plans + a `docs/README.md` index), not a `docs/dev/` or
  `archive/` split.
- **Frozen history left verbatim.** `docs/evidence/` snapshots and the
  `pm/roadmap/holdspeak/phase-*` records still contain `docs/PLAN_*` /
  `docs/CROSS_PLATFORM_*` strings — these are historical captures (git-status
  dumps, past phase summaries) and are kept verbatim by design, the same
  principle the drift guard already encodes ("the PMO roadmap corpus is the
  historical record and is kept verbatim"). Only **live** references were
  repointed.
- **The live roadmap `README.md` (`pm/`) was repointed** despite the phase's
  "`pm/` untouched" line, because its "Source canon" section is an actively
  maintained *index* (updated every commit per the operating cadence), and
  leaving it dangling would defeat the link-check / done-when. The frozen phase
  folders under `pm/` were not touched.
