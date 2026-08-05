# HS-117-12 — The backend cleanup

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-10, HS-117-11
- **Unblocks:** ---
- **Owner:** unassigned

## The thesis (the bar)

`holdspeak/db/core.py` is 2,314 lines. After HS-117-10 extracts
schema and migrations, it will be ~400 lines of `Database` container
and connection management. But the `Database` class still owns 40
repository instances as direct attributes, each constructed in
`__init__`. The 40 repository classes in `holdspeak/db/` all inherit
`BaseRepository` and share a connection factory, but there is no
repository registry or lazy loading -- adding a new table means
editing `Database.__init__`. Meanwhile, `holdspeak/config.py` (1,030
lines) holds ~15 dataclass sections, coercion logic, legacy endpoint
migration, and save/load -- all in one file.

When this story ships, the `Database` container uses a repository
registry (repositories declare themselves; `Database` discovers
them). `config.py` is split into domain sections under
`holdspeak/config/`. Connection management is simplified with a
context-manager protocol.

**Articles served:** VI (honest construction -- a 2,314-line container
is not a container, it is a monolith), X (sustainability -- new
repositories and config sections land without editing the container).

## Deliverables

### 1. Add a repository registry to `BaseRepository`

Extend `holdspeak/db/base.py` with a `_registry` class dict and
`__init_subclass__` that auto-registers each repo by its `table`
class attribute. Each of the 40 repository classes gets a `table`
class attribute (one-liner per file).

### 2. Simplify `Database.__init__`

Replace the 40 explicit repository constructions with a registry-
driven loop over `BaseRepository._registry`. Add typed `__getattr__`
or stubs for IDE support. Verify every `db.meetings`, `db.actions`,
etc. still resolves.

### 3. Extract connection management

Move the connection factory, transaction context manager, and
WAL/journal configuration from `Database` into
`holdspeak/db/connection.py` (~80 lines). `Database` imports and
delegates to it.

### 4. Split `config.py` into domain modules

Create `holdspeak/config/` with:

- `__init__.py` -- re-exports `Config`, `Config.load()`,
  `Config.save()` (backwards compatibility).
- `core.py` -- the `Config` dataclass shell, `load()`, `save()`,
  `_coerce()`, version migration. ~200 lines.
- `meeting.py` -- `MeetingConfig`, `DictationPipelineConfig`.
  ~120 lines.
- `model.py` -- `ModelConfig`, `LLMRuntimeConfig`,
  `InferenceTarget` choices. ~150 lines.
- `device.py` -- `DeviceConfig`, `PresenceConfig`, `MeshConfig`,
  `WakeWordConfig`. ~120 lines.
- `ui.py` -- `UIConfig`, `HotkeyConfig`, `MacrosConfig`. ~100 lines.
- `integrations.py` -- `TelegramConfig`, `RailsObserverConfig`,
  `CadenceConfig`. ~100 lines.

Each section file exports one or more dataclasses. `core.py`
composes them. Total: ~800 lines across 7 files vs. 1,030 in one.

### 5. Update imports

Run project-wide grep for `from holdspeak.config import` and
`from holdspeak.db.core import`. The barrels (`config/__init__.py`,
`core.py`) re-export everything, so most imports are unaffected.
Fix any that import internal symbols by path.

## What NOT to do

- Do NOT change the config file format (`config.json`). The on-disk
  shape is a user contract.
- Do NOT change repository method signatures or SQL. Only the
  wiring changes.
- Do NOT remove `BaseRepository`. It is the correct abstraction.
- Do NOT merge repositories or split them further. 40 repos for
  40 tables is the right granularity.
- Do NOT change `Config.load()` / `Config.save()` behavior. Only
  the file they live in changes.
- Do NOT touch `holdspeak/db/models/` (that was HS-117-10) or
  `holdspeak/errors.py` (that was HS-117-11).

## Test plan

1. `uv run pytest -q` -- all backend tests pass.
2. Verify `core.py` is under 200 lines (post HS-117-10 extraction +
   this cleanup): `wc -l holdspeak/db/core.py` < 200.
3. Verify registry discovers all repositories:
   `uv run python -c "from holdspeak.db.base import BaseRepository;
   assert len(BaseRepository._registry) >= 35"`.
4. Verify config round-trip: load config, save to temp path, diff
   against original -- zero differences.
5. Verify no broken imports:
   `uv run python -c "from holdspeak.config import Config;
   from holdspeak.db.core import Database"` exits 0.
6. `npx tsc --noEmit` -- frontend unaffected.
7. Playwright screenshot walk -- app boots and renders (config
   loads correctly, DB connects).

## Estimated scope

~1,400 lines moved (config.py split + core.py cleanup). ~100 lines
added (registry, connection module, barrels). ~80 lines removed
(40 explicit repo constructions replaced by registry loop). Net:
~20 lines added. 2 new files, 1 new directory, ~45 files touched
(40 repos get a `table` attribute + import updates).
