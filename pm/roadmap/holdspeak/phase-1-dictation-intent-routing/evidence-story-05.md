# Evidence — HS-1-05 (Block-config loader)

**Story:** [story-05-blocks.md](./story-05-blocks.md)
**Date:** 2026-04-25
**Status flipped:** in-progress → done

## What shipped

- `holdspeak/plugins/dictation/blocks.py` — typed loader for the §8
  YAML schema.
  - `InjectMode` enum (`append | prepend | replace`).
  - Frozen dataclasses: `MatchSpec`, `InjectSpec`, `Block`,
    `LoadedBlocks`. `LoadedBlocks.to_block_set()` projects to the
    constraint domain consumed by `grammars.py`.
  - `load_blocks_yaml(path)` — `yaml.safe_load` + structural and
    template-shape validation. `BlockConfigError` messages name the
    file and the path inside the document
    (`<file>: blocks[2].inject.template: ...`).
  - `resolve_blocks(global_path, project_root)` — §8.1 resolution:
    project file fully replaces global (DIR-F-008); falls back to
    global; returns empty `LoadedBlocks` when neither exists.
  - `validate_template` — accepts only `{name}` / `{a.b.c}`
    placeholders. Rejects format specs (`{x:!r}`), conversions
    (`{x!r}`), method calls (`{x()}`), item access (`{items[0]}`),
    arithmetic (`{1+2}`), empty `{}`, spaces.
- `pyproject.toml` — adds explicit `PyYAML>=6.0` to core
  dependencies (the loader uses it; previously transitively present).
- `tests/unit/test_dictation_blocks.py` — 24 cases.

## DIR requirements verified in this story

| Requirement | Verified by |
|---|---|
| `DIR-D-001` Block schema versioned | `test_missing_version_rejected`, `test_unsupported_version_rejected` |
| `DIR-D-002` Actionable error on malformed YAML | `test_malformed_yaml_message_names_file`, the structural error tests |
| `DIR-F-008` Project blocks fully replace global | `test_resolve_blocks_project_replaces_global` |
| `DIR-S-001` Loader uses safe YAML | `test_safe_load_rejects_python_object_tag` |
| `DIR-S-002` Templates cannot execute code | `test_validate_template_accepts_simple_dotted_placeholders`, `test_validate_template_rejects_format_magic` (parametrized over 7 attack shapes), `test_block_with_evil_template_is_rejected_at_load` |
| Cross-bridge to grammars compiler | `test_to_block_set_bridges_to_grammars` (uses `equivalent_value_sets`) |

## Test output

### Targeted (blocks loader)

```
$ uv run pytest -q tests/unit/test_dictation_blocks.py
........................                                                 [100%]
24 passed in 0.07s
```

The 24 cases break down as:

- 2 happy-path: load a §8.2 fixture, bridge to `grammars.BlockSet`.
- 2 version validation (missing, unsupported).
- 5 structural validation (description, duplicate id, invalid inject
  mode, default_match_confidence range, extras `type: enum` only).
- 4 project-replacement / resolution (project replaces global, project
  missing → global, both missing → empty, no inputs → empty).
- 2 safety (PyYAML safe_load rejects `!!python/object/...`; malformed
  YAML message names the file).
- 9 template-shape (1 happy + 7 parametrized rejection + 1
  end-to-end load-time rejection).

### Full regression

```
$ uv run pytest -q tests/ --timeout=30
...
1 failed, 848 passed, 13 skipped, 3 warnings in 17.42s
FAILED tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads
```

Pre-existing hardware-only Whisper-loader failure, unrelated. Pass
delta: 824 → 848 (+24 new unit cases).

## Files in this commit

- `holdspeak/plugins/dictation/blocks.py` (new)
- `pyproject.toml` (added explicit `PyYAML>=6.0` to core deps)
- `tests/unit/test_dictation_blocks.py` (new)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-05-blocks.md` (new — story authored, status flipped to done in the same commit)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-05.md` (this file)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/README.md` (last-updated line)

## Notes

- `LoadedBlocks.source_path` is `None` for the all-empty fallback so
  callers can distinguish "no config file present" from "loaded an
  empty `blocks: []` file" (HS-1-09's doctor check will use this).
- Story-05 was authored fresh in this commit; same-commit
  backlog→done is intentional and complies with PMO §6 (story flip +
  matching evidence) — same pattern HS-1-03 used.
- `match.threshold` is parsed and surfaced on `MatchSpec` but not
  enforced here; HS-1-06's `kb-enricher` reads it (with the global
  default as fallback) per DIR-F-006.
