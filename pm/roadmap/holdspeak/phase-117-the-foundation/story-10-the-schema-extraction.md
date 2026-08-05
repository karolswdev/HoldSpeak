# HS-117-10 — The schema extraction

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** ---
- **Unblocks:** HS-117-12
- **Owner:** unassigned

## The thesis (the bar)

All persistence models live in one file: `holdspeak/db/models.py`
(1,162 lines, ~30 dataclasses). Schema SQL lives inline in
`holdspeak/db/core.py` (2,314 lines) alongside migrations (version
1-35), the `Database` container, and connection management.
Serialization is manual (`to_dict()` on each model). There is no
shared validation pattern -- status enums are `frozenset` constants
at the top of `models.py` with no enforcement decorator.

When this story ships, models are grouped into domain modules under
`holdspeak/db/models/`, schema SQL is extracted into
`holdspeak/db/schema.py`, and migrations live in
`holdspeak/db/migrations.py`. `core.py` drops from 2,314 to ~400
lines (container + connection management only). A `Serializable`
mixin replaces the hand-written `to_dict()` methods.

**Articles served:** VI (honest construction -- schema is
infrastructure, not an appendix to the container), X
(sustainability -- domain-grouped models are navigable).

## Deliverables

### 1. Extract schema SQL into `holdspeak/db/schema.py`

Move the `SCHEMA_SQL` string and `SCHEMA_VERSION` constant from
`core.py` into `holdspeak/db/schema.py`. This is the CREATE TABLE
block that defines the initial schema shape. `core.py` imports from
the new file.

### 2. Extract migrations into `holdspeak/db/migrations.py`

Move the sequential `ALTER TABLE` / `CREATE TABLE` migration blocks
(versions 1-35) from `core.py` into `holdspeak/db/migrations.py`.
Export a `run_migrations(conn, from_version, to_version)` function.
`core.py` calls it during `Database.__init__`.

### 3. Split `models.py` into domain modules

Create `holdspeak/db/models/` with:

- `__init__.py` -- re-exports everything (backwards compatibility).
- `meeting.py` -- Meeting, IntelJob, IntentWindow, Segment (~5
  dataclasses, ~150 lines).
- `actions.py` -- ActionItem, ActuatorProposal, AuthorityGrant,
  Decision (~4 dataclasses, ~120 lines).
- `knowledge.py` -- KB, Recipe, Note, Chain, Directory,
  DirectoryMembership (~6 dataclasses, ~150 lines).
- `workbench.py` -- Workbench, WorkbenchItem, WorkbenchRun, Skill,
  Workflow, CapabilityInvocation (~6 dataclasses, ~160 lines).
- `activity.py` -- Activity, Project, Artifact, Profile,
  DictationJournal (~5 dataclasses, ~120 lines).
- `infra.py` -- PluginRun, MeshRelayJob, and any remaining
  infrastructure models (~3 dataclasses, ~80 lines).
- `mixins.py` -- the `Serializable` mixin (deliverable 4).

Status `frozenset` constants move with their parent model.

### 4. Add `Serializable` mixin

Create a `Serializable` mixin in `holdspeak/db/models/mixins.py`
that derives `to_dict()` from `dataclasses.fields()`:

```python
import dataclasses

class Serializable:
    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
```

Apply to every model dataclass. Remove the ~30 hand-written
`to_dict()` methods. Verify round-trip equivalence in tests.

### 5. Update all imports

Every file that imports from `holdspeak.db.models` must still work.
The `models/__init__.py` barrel re-exports everything, so most
imports are unaffected. Run a project-wide grep to catch any that
import specific classes by path.

## What NOT to do

- Do NOT change the database schema or migrations. This is a code
  organization story, not a schema change.
- Do NOT switch from dataclasses to Pydantic. The codebase uses
  pure dataclasses deliberately.
- Do NOT touch repository classes (`holdspeak/db/*.py` repos).
  That is HS-117-12.
- Do NOT refactor `Database.__init__` beyond calling
  `run_migrations()`. The container shape is HS-117-12.
- Do NOT change any model's fields or `to_dict()` output shape.
  The `Serializable` mixin must produce identical JSON.

## Test plan

1. `uv run pytest -q` -- all backend tests pass.
2. Verify `core.py` is under 500 lines:
   `wc -l holdspeak/db/core.py` < 500.
3. Verify the old `models.py` is gone:
   `test ! -f holdspeak/db/models.py` (replaced by `models/`).
4. Verify `to_dict()` round-trip: add a parametrized test that
   creates each model with fixture data, calls `to_dict()`, and
   asserts the output matches the pre-refactor snapshot.
5. Verify no broken imports:
   `uv run python -c "from holdspeak.db.models import Meeting,
   ActionItem, KB, Workbench, Activity"` exits 0.
6. `npx tsc --noEmit` -- frontend unaffected (no shared types).

## Estimated scope

~1,200 lines moved (models.py split + schema/migrations extracted
from core.py). ~60 lines added (barrel, mixin, migration runner
function signature). ~30 lines removed (hand-written `to_dict()`
methods replaced by mixin). 3 new files, 1 directory, ~10 files
with updated imports.
