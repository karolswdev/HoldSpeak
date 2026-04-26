# HS-1-05 — Step 4: Block config loader

- **Project:** holdspeak
- **Phase:** 1
- **Status:** done
- **Depends on:** HS-1-04 (the loaded `BlockSet` feeds `grammars.py`)
- **Unblocks:** HS-1-06 (built-in `intent-router` + `kb-enricher` stages), HS-1-09 (doctor checks the loader path)
- **Owner:** unassigned

## Problem

DIR-01 §8 defines the block-config YAML schema: a versioned list of
blocks with id, description, match examples, optional negative
examples, optional `extras_schema`, and an `inject` block (mode +
template). The runtime needs a typed, validated, in-memory
representation of this file plus the resolution rule from §8.1: if a
project-scope file exists, it **fully replaces** global blocks for
that project (no merge — DIR-F-008).

The schema-compiler in HS-1-04 (`grammars.py`) already defines
`BlockSpec` / `BlockSet` for the constraint domain (id +
extras_schema). The loader produces a richer `Block` (description,
examples, inject mode + template) and exposes a `to_block_set()`
bridge so the constraint compiler keeps working off the same source
of truth.

Per §9.2 / §9.8:

- `DIR-D-001` Block config schema MUST be versioned via top-level
  `version: 1`.
- `DIR-D-002` Loader MUST validate against the schema and produce
  actionable error messages on malformed YAML.
- `DIR-D-003` No DB schema changes; recent-runs introspection is
  in-memory (already addressed in HS-1-03).
- `DIR-S-001` Loader MUST treat configs as trusted but MUST NOT
  execute arbitrary code (`yaml.safe_load`, no `!!python/object`).
- `DIR-S-002` Templates MUST NOT execute shell or Python; the loader
  rejects template strings that contain expression-like constructs
  outside `{key}` substitution. Concretely: format-spec syntax in
  placeholders (`{x:!r}`, `{x.method()}`) is rejected; only dotted
  paths are accepted (resolved at template-application time in
  HS-1-06).

## Scope

- **In:**
  - `holdspeak/plugins/dictation/blocks.py`:
    - `InjectMode` enum (`APPEND`, `PREPEND`, `REPLACE`).
    - `MatchSpec` (frozen dataclass): `examples`, `negative_examples`,
      `extras_schema: Mapping[str, tuple[str, ...]]`, `threshold:
      float | None`.
    - `InjectSpec` (frozen dataclass): `mode: InjectMode`, `template:
      str`.
    - `Block` (frozen dataclass): `id`, `description`, `match`,
      `inject`.
    - `LoadedBlocks` (frozen dataclass): `version: int`, `blocks:
      tuple[Block, ...]`, `default_match_confidence: float`,
      `source_path: Path | None`. Provides
      `to_block_set() -> grammars.BlockSet`.
    - `BlockConfigError(ValueError)` with a message format that names
      the offending file + path inside the document
      (`blocks[2].inject.template`).
    - `load_blocks_yaml(path: Path) -> LoadedBlocks` — single-file
      load with `yaml.safe_load` + structural validation +
      template-shape validation.
    - `resolve_blocks(global_path: Path | None, project_root: Path |
      None) -> LoadedBlocks` — implements §8.1 resolution: if
      `<project_root>/.holdspeak/blocks.yaml` exists, returns that;
      else falls back to `global_path` if present; else returns an
      empty (zero-block) `LoadedBlocks`. **Project blocks fully
      replace global** — no merge (DIR-F-008).
    - `validate_template(template: str) -> None` — accepts only
      `{name}` and `{name.path.to.field}` placeholders (alphanumeric
      + underscore + dot). Rejects format-specs (`:`), conversions
      (`!r`/`!s`/`!a`), method calls, square brackets, and other
      f-string magic (DIR-S-002).
  - Add `PyYAML>=6.0` to core dependencies in `pyproject.toml`
    (already transitively available via uvicorn[standard], but the
    loader uses it explicitly and the project should declare it).
  - `tests/unit/test_dictation_blocks.py` covering:
    - Happy-path load of a §8.2 fixture.
    - `to_block_set()` returns a `BlockSet` whose constraint compiler
      output matches the loaded extras enums (cross-check via
      `grammars.equivalent_value_sets`).
    - Version validation (`version: 1` required; missing → error;
      future version → error with version string in message).
    - Required fields present; `description`, `match`, `inject` all
      validated.
    - `extras_schema` shape: `{type: enum, values: [...]}` round-trips
      to `(values...)`.
    - Project replacement (DIR-F-008): `resolve_blocks` returns the
      project file's blocks verbatim when present, ignores global.
    - Project-missing → falls back to global; both-missing → empty
      `LoadedBlocks`.
    - Malformed YAML → `BlockConfigError` mentions the file path.
    - Unsafe YAML tag (`!!python/object/apply:os.system`) → safe-load
      raises (DIR-S-001).
    - Template shape validation (DIR-S-002): `{x}`, `{x.y}`,
      `{x.y.z}` accepted; `{x:!r}`, `{x()}`, `{x[0]}`, `{1+2}` rejected
      with actionable error.
- **Out:**
  - `holdspeak doctor` integration — that is HS-1-09.
  - Actual template substitution / `kb-enricher` stage — HS-1-06.
  - Auto-discovery of `<project_root>` via `project_detector` —
    callers pass the root explicitly. HS-1-07 wires the detector.
  - Schema-version migrations — only `version: 1` is supported.

## Acceptance criteria

- [x] `holdspeak/plugins/dictation/blocks.py` exists and exposes the
      types and functions listed in Scope.
- [x] `LoadedBlocks.to_block_set()` returns a `grammars.BlockSet`
      whose `default_match_confidence`, block ids, and per-block
      `extras_schema` exactly match the YAML source — verified via
      `equivalent_value_sets` cross-check in
      `test_to_block_set_bridges_to_grammars`.
- [x] `load_blocks_yaml` uses `yaml.safe_load` (DIR-S-001);
      `test_safe_load_rejects_python_object_tag` confirms
      `!!python/object/apply:os.system [...]` raises.
- [x] `version: 1` is required;
      `test_missing_version_rejected` and
      `test_unsupported_version_rejected` cover both error paths and
      the message names the offending version.
- [x] `validate_template` accepts dotted placeholders, rejects format
      specs / conversions / method calls / arithmetic / spaces — see
      the parametrized `test_validate_template_rejects_format_magic`
      cases. Error message names the placeholder.
- [x] `resolve_blocks(global, project_root)` returns the project file
      verbatim when both exist (DIR-F-008); falls back to global; and
      returns an empty `LoadedBlocks` when neither exists.
- [x] `tests/unit/test_dictation_blocks.py` → 24 passed.
- [x] Full regression: `uv run pytest -q tests/` → 848 passed, 13
      skipped, 1 pre-existing hardware-only fail in
      `tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads`.

## Test plan

- **Unit:** `uv run pytest -q tests/unit/test_dictation_blocks.py` —
  cases enumerated in Scope.
- **Regression:** `uv run pytest -q tests/`.
- **Manual:** None.

## Notes / open questions

- The `BlockSet` in `grammars.py` is intentionally narrower than
  `LoadedBlocks` — the constraint compiler only needs the id-and-
  extras-domain projection. Keeping the two types separate avoids
  pulling YAML structure into the GBNF/outlines layer.
- `match.threshold` is optional per block; when absent, the
  `kb-enricher` (HS-1-06) falls back to
  `LoadedBlocks.default_match_confidence`. The loader passes this
  through; it does not enforce policy.
- Path inputs to `resolve_blocks` are explicit so tests are
  deterministic. HS-1-07 will plumb the global default
  (`~/.config/holdspeak/blocks.yaml`) and the
  `project_detector`-resolved project root from the controller.
