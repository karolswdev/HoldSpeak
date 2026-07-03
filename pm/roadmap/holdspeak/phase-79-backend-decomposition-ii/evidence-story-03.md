# Evidence — HS-79-03 — `routes/primitives.py` becomes the primitives package

**Status:** done (2026-07-03).

## The move

`holdspeak/web/routes/primitives.py` (1,294 lines, 41 routes, one builder) →
`holdspeak/web/routes/primitives/`:

| Module | Lines | Concern |
|---|---|---|
| notes.py | 97 | Notes CRUD |
| agents.py | 206 | Agents CRUD + the hub run endpoint |
| profiles.py | 103 | Runtime profiles CRUD |
| kbs.py | 97 | KBs CRUD |
| chains.py | 214 | Chains CRUD + run |
| workflows.py | 333 | Workflows CRUD + the graph-aware run |
| directories.py | 167 | Directories + membership edges |
| _shared.py | 159 | `_json_body`, `_new_id`, the run frame/persist tail (stays ONE function), the source-type vocabulary |
| __init__.py | 36 | `build_primitives_router` composes seven; re-exports the public wire vocabulary |

All under the module budget. The run-persist helper was NOT forked: agents, chains,
and workflows import the one `_persist_run_artifact` from `_shared`.

## Verbatim accounting

Programmatic check against `git show HEAD:` (outside the replaced head docstring,
whose route table moved into per-module docs): **zero code-body lines differ**; the
49 non-verbatim lines are lazy in-body imports retargeted one package level deeper,
plus one three-dot→two-dot sibling (`from .workflow_graph` → `from ..workflow_graph`
— caught by the workflow-run tests, which is exactly what they are for). One cosmetic
`# ── Notes ──` section banner superseded by the file split.

**Public surface preserved:** `build_primitives_router` unchanged;
`CANONICAL_SOURCE_TYPES` + `canonical_source_type` re-exported from the package root
(the pinned-vocabulary test imports them there — it caught the missing re-export,
then passed unmodified). **Patch-target edits in tests: zero.**

## Proven

`uv run pytest -q tests/unit` **2407 passed** · `tests/integration` **685 passed** ·
the regenerated `docs/api-surface.json` diff is **module fields only**.
