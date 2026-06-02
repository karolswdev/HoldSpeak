# Evidence — HS-31-03 (remaining repos + retire the god-class)

**Shipped:** 2026-06-02 (two commits: extraction, then the `MeetingDatabase → Database` rename).
The last three domains are extracted and the god-class is gone — in substance *and* name.

## What changed

Three repositories extracted from the container (verbatim moves, AST-based since the
helpers were scattered through the file):

| File | Repo | Methods | Lines |
|---|---|---|---|
| `plugins.py` | `PluginArtifactRepository` — intent windows, plugin runs/jobs, artifacts | 15 | 814 |
| `projects.py` | `ProjectRepository` — projects, associations, detection log | 15 | 463 |
| `activity.py` | `ActivityRepository` — local activity-intelligence ledger | 51 | 1553 |

The container (`core.py`) is now **1,224 lines** (from the original **5,481, −78%**): only
`__init__`, `_connection`, `_ensure_schema`, `_apply_schema`, the schema SQL, and the
`get_database` singleton. It was then renamed `MeetingDatabase → Database` (145 references
across 41 files); **`grep -r MeetingDatabase` in code returns nothing.** The full public
surface is still re-exported from `holdspeak/db/__init__.py`.

## The decomposition, end to end

| File | Lines | | File | Lines |
|---|---|---|---|---|
| core.py (container) | 1224 | | meetings.py | 890 |
| activity.py | 1553 | | intel.py | 394 |
| plugins.py | 814 | | models.py | 345 |
| projects.py | 463 | | base.py / __init__.py | 49 / 17 |

One 5,481-line god-object → a container + 5 domain repositories + shared models/base.

## Extraction method

AST-based extraction by method name (helpers like `_row_to_project` were buried in the
activity tail, so line-slicing wouldn't do), with a **coverage assertion**: every method
must land in exactly one category (stay / drop / plugins / projects / activity), and every
"activity" method name must contain `activity`/`connector` — the script fails loudly otherwise.

## Cross-domain

The only inter-repo call among the three is Activity→Project (`get_project`, 4 sites in the
project-rule methods), rewritten to `self._db.projects.get_project(...)` via the container
back-reference established in HS-31-02. No project/plugin/activity method calls meetings/intel.

## Call sites

- **~469 call sites** moved to `db.{plugins,projects,activity}.*` across ~45 production + test files.
- **11 fake-db doubles** gained the matching repo self-properties (`plugins`/`projects`/`activity`).
- The rename updated 145 `MeetingDatabase` references across 41 files.

## Iterative import-discovery (surfaced by the suite, all fixed)

The verbatim move needed module imports the slicer's fixed header didn't carry:
`import uuid` (activity), `import json` (plugins), `from urllib.parse import …` + `Iterator`
(activity). Two non-grep-able call sites were fixed by hand: `connector_runtime.py`'s
`self._db.<method>` handle, `activity_history.py`'s external call to the **private**
`_normalize_activity_url`, and a `kwargs["db"].upsert_activity_record` subscript receiver
in a test. Each was found by running the suite and reading the failure.

## Tests ran

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2062 passed, 14 skipped** (== baseline),
  green after both the extraction commit and the rename commit.
- `uv run ruff check holdspeak/db/` → **All checks passed!**
- Smoke: all five repos resolve on `Database`; cross-domain activity→project works; the
  container carries no domain methods.

## Decisions

- **God-class retired by rename, no alias.** `MeetingDatabase → Database` with no
  backwards-compat alias (greenfield) — the name was a misnomer for the whole-DB container.
- **Out of scope / left as-is:** the pre-existing `F841` (`current_time`) in `meeting_session.py`.
- Roadmap *history* (e.g. evidence-story-01/02) keeps the `MeetingDatabase` name — it
  describes the state at that time and is not rewritten.
