"""Unit tests for the DIR-01 block-config loader (HS-1-05)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from holdspeak.plugins.dictation.blocks import (
    BlockConfigError,
    InjectMode,
    LoadedBlocks,
    SUPPORTED_VERSION,
    load_blocks_yaml,
    resolve_blocks,
    validate_template,
)
from holdspeak.plugins.dictation.grammars import equivalent_value_sets


_GLOBAL_YAML = dedent(
    """
    version: 1
    default_match_confidence: 0.65
    blocks:
      - id: ai_prompt_buildout
        description: AI prompt buildout phase
        match:
          examples:
            - "Claude, build a function that..."
            - "ChatGPT, please create..."
          negative_examples:
            - "What time is it"
          extras_schema:
            stage:
              type: enum
              values: [buildout, refinement, debugging]
          threshold: 0.7
        inject:
          mode: append
          template: |
            {raw_text}
            ---
            Repo: {project.name}
            Stack: {project.kb.stack}
      - id: documentation_exercise
        description: Documenting code or systems
        match:
          examples:
            - "This module is responsible for..."
        inject:
          mode: prepend
          template: "<!-- docs: {project.kb.docs_index} -->\\n{raw_text}"
    """
).strip()


_PROJECT_YAML = dedent(
    """
    version: 1
    default_match_confidence: 0.5
    blocks:
      - id: project_only
        description: A project-scoped block
        match:
          examples:
            - "deploy this branch"
        inject:
          mode: replace
          template: "[deploy] {raw_text}"
    """
).strip()


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_load_blocks_yaml_happy_path(tmp_path):
    path = _write(tmp_path, "blocks.yaml", _GLOBAL_YAML)

    loaded = load_blocks_yaml(path)

    assert isinstance(loaded, LoadedBlocks)
    assert loaded.version == SUPPORTED_VERSION
    assert loaded.default_match_confidence == 0.65
    assert loaded.source_path == path
    assert [b.id for b in loaded.blocks] == [
        "ai_prompt_buildout",
        "documentation_exercise",
    ]
    b0 = loaded.blocks[0]
    assert b0.description == "AI prompt buildout phase"
    assert b0.match.examples == (
        "Claude, build a function that...",
        "ChatGPT, please create...",
    )
    assert b0.match.negative_examples == ("What time is it",)
    assert b0.match.extras_schema == {
        "stage": ("buildout", "refinement", "debugging"),
    }
    assert b0.match.threshold == 0.7
    assert b0.inject.mode is InjectMode.APPEND
    assert "{project.name}" in b0.inject.template

    # Block 2 has no extras and no negative examples.
    b1 = loaded.blocks[1]
    assert b1.match.extras_schema is None
    assert b1.match.negative_examples == ()
    assert b1.inject.mode is InjectMode.PREPEND


def test_to_block_set_bridges_to_grammars(tmp_path):
    path = _write(tmp_path, "blocks.yaml", _GLOBAL_YAML)
    loaded = load_blocks_yaml(path)
    bs = loaded.to_block_set()

    assert bs.default_match_confidence == 0.65
    assert bs.block_ids() == ("ai_prompt_buildout", "documentation_exercise")

    from holdspeak.plugins.dictation.grammars import StructuredOutputSchema

    schema = StructuredOutputSchema.from_block_set(bs)
    eq = equivalent_value_sets(schema)
    assert eq["block_ids"] == ("ai_prompt_buildout", "documentation_exercise")
    assert eq["extras_per_block"]["ai_prompt_buildout"]["stage"] == (
        "buildout",
        "refinement",
        "debugging",
    )
    assert eq["extras_per_block"]["documentation_exercise"] == {}


# ---------------------------------------------------------------------------
# Version validation (DIR-D-001)
# ---------------------------------------------------------------------------


def test_missing_version_rejected(tmp_path):
    path = _write(tmp_path, "blocks.yaml", "blocks: []\n")
    with pytest.raises(BlockConfigError, match="missing required key 'version'"):
        load_blocks_yaml(path)


def test_unsupported_version_rejected(tmp_path):
    path = _write(tmp_path, "blocks.yaml", "version: 2\nblocks: []\n")
    with pytest.raises(BlockConfigError, match="unsupported version 2"):
        load_blocks_yaml(path)


# ---------------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------------


def test_missing_description_rejected(tmp_path):
    yaml_text = dedent(
        """
        version: 1
        blocks:
          - id: x
            match:
              examples: ["e"]
            inject:
              mode: append
              template: "{raw_text}"
        """
    ).strip()
    path = _write(tmp_path, "blocks.yaml", yaml_text)
    with pytest.raises(BlockConfigError, match="description"):
        load_blocks_yaml(path)


def test_duplicate_block_id_rejected(tmp_path):
    yaml_text = dedent(
        """
        version: 1
        blocks:
          - id: dup
            description: a
            match:
              examples: ["x"]
            inject:
              mode: append
              template: "{raw_text}"
          - id: dup
            description: b
            match:
              examples: ["y"]
            inject:
              mode: append
              template: "{raw_text}"
        """
    ).strip()
    path = _write(tmp_path, "blocks.yaml", yaml_text)
    with pytest.raises(BlockConfigError, match="duplicate block id"):
        load_blocks_yaml(path)


def test_invalid_inject_mode_rejected(tmp_path):
    yaml_text = dedent(
        """
        version: 1
        blocks:
          - id: x
            description: y
            match:
              examples: ["a"]
            inject:
              mode: nuke
              template: "{raw_text}"
        """
    ).strip()
    path = _write(tmp_path, "blocks.yaml", yaml_text)
    with pytest.raises(BlockConfigError, match="not one of"):
        load_blocks_yaml(path)


def test_default_match_confidence_out_of_range_rejected(tmp_path):
    yaml_text = dedent(
        """
        version: 1
        default_match_confidence: 1.5
        blocks: []
        """
    ).strip()
    path = _write(tmp_path, "blocks.yaml", yaml_text)
    with pytest.raises(BlockConfigError, match=r"\[0\.0, 1\.0\]"):
        load_blocks_yaml(path)


def test_extras_schema_must_be_enum(tmp_path):
    yaml_text = dedent(
        """
        version: 1
        blocks:
          - id: x
            description: y
            match:
              examples: ["a"]
              extras_schema:
                stage:
                  type: free_form
                  values: [whatever]
            inject:
              mode: append
              template: "{raw_text}"
        """
    ).strip()
    path = _write(tmp_path, "blocks.yaml", yaml_text)
    with pytest.raises(BlockConfigError, match="only 'enum' is supported"):
        load_blocks_yaml(path)


# ---------------------------------------------------------------------------
# Project replacement (DIR-F-008)
# ---------------------------------------------------------------------------


def test_resolve_blocks_project_replaces_global(tmp_path):
    global_path = _write(tmp_path / "global", "blocks.yaml", _GLOBAL_YAML)
    project_root = tmp_path / "project"
    _write(project_root / ".holdspeak", "blocks.yaml", _PROJECT_YAML)

    loaded = resolve_blocks(global_path, project_root)

    # Project blocks fully replace global; no merge.
    assert [b.id for b in loaded.blocks] == ["project_only"]
    assert loaded.default_match_confidence == 0.5


def test_resolve_blocks_falls_back_to_global_when_no_project_file(tmp_path):
    global_path = _write(tmp_path / "global", "blocks.yaml", _GLOBAL_YAML)
    project_root = tmp_path / "project"
    project_root.mkdir(parents=True, exist_ok=True)

    loaded = resolve_blocks(global_path, project_root)

    assert [b.id for b in loaded.blocks] == [
        "ai_prompt_buildout",
        "documentation_exercise",
    ]


def test_resolve_blocks_returns_empty_when_neither_exists(tmp_path):
    loaded = resolve_blocks(tmp_path / "nope.yaml", tmp_path / "no_project")

    assert loaded.blocks == ()
    assert loaded.source_path is None
    assert loaded.default_match_confidence == 0.6


def test_resolve_blocks_with_no_global_no_project_root(tmp_path):
    loaded = resolve_blocks(None, None)
    assert loaded.blocks == ()


# ---------------------------------------------------------------------------
# Safety (DIR-S-001)
# ---------------------------------------------------------------------------


def test_safe_load_rejects_python_object_tag(tmp_path):
    yaml_text = dedent(
        """
        version: 1
        blocks: []
        evil: !!python/object/apply:os.system ["echo pwned"]
        """
    ).strip()
    path = _write(tmp_path, "blocks.yaml", yaml_text)
    with pytest.raises(BlockConfigError, match="malformed YAML"):
        load_blocks_yaml(path)


def test_malformed_yaml_message_names_file(tmp_path):
    path = _write(tmp_path, "blocks.yaml", "version: 1\nblocks: [unbalanced")
    with pytest.raises(BlockConfigError, match=str(path)):
        load_blocks_yaml(path)


# ---------------------------------------------------------------------------
# Template shape (DIR-S-002)
# ---------------------------------------------------------------------------


def test_validate_template_accepts_simple_dotted_placeholders():
    validate_template("hello {name}, {project.kb.stack}", where="x")
    validate_template("{a.b.c.d.e}", where="x")
    validate_template("no placeholders here", where="x")


@pytest.mark.parametrize(
    "bad",
    [
        "{name:!r}",
        "{name!r}",
        "{name()}",
        "{items[0]}",
        "{1+2}",
        "{}",
        "{name spaced}",
    ],
)
def test_validate_template_rejects_format_magic(bad):
    with pytest.raises(BlockConfigError):
        validate_template(bad, where="x")


def test_block_with_evil_template_is_rejected_at_load(tmp_path):
    yaml_text = dedent(
        """
        version: 1
        blocks:
          - id: bad
            description: tries to call methods
            match:
              examples: ["x"]
            inject:
              mode: append
              template: "evaluate {os.system('rm -rf /')}"
        """
    ).strip()
    path = _write(tmp_path, "blocks.yaml", yaml_text)
    with pytest.raises(BlockConfigError, match="placeholder"):
        load_blocks_yaml(path)
