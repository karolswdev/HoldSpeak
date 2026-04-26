"""Block-config YAML loader for the DIR-01 dictation pipeline (HS-1-05).

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §8 + §9.2 + §9.8.

YAML shape (§8.2)::

    version: 1
    default_match_confidence: 0.6
    blocks:
      - id: ai_prompt_buildout
        description: ...
        match:
          examples: [...]
          negative_examples: [...]
          extras_schema:
            stage: { type: enum, values: [...] }
          threshold: 0.7
        inject:
          mode: append   # append | prepend | replace
          template: |
            {raw_text}
            ...

The loader ships with **safe YAML loading** (DIR-S-001), strict
schema validation with actionable error messages (DIR-D-002), and
**project replacement** semantics (DIR-F-008): if a project-scope
file is present it fully supersedes the global file. Templates are
shape-validated at load time (DIR-S-002) — only `{name}` and
`{a.b.c}` placeholders are allowed. Actual substitution lives in
HS-1-06's `kb-enricher` stage.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from holdspeak.plugins.dictation.grammars import (
    BlockSet,
    BlockSpec,
)

SUPPORTED_VERSION = 1

_VALID_PLACEHOLDER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
_PLACEHOLDER_FINDER_RE = re.compile(r"\{([^{}]*)\}")


class BlockConfigError(ValueError):
    """Raised when block-config YAML fails to load or validate.

    The message names the offending file (when known) and the path
    inside the document (e.g. ``blocks[2].inject.template``).
    """


class InjectMode(str, Enum):
    APPEND = "append"
    PREPEND = "prepend"
    REPLACE = "replace"


@dataclass(frozen=True)
class MatchSpec:
    examples: tuple[str, ...]
    negative_examples: tuple[str, ...] = ()
    extras_schema: Mapping[str, tuple[str, ...]] | None = None
    threshold: float | None = None


@dataclass(frozen=True)
class InjectSpec:
    mode: InjectMode
    template: str


@dataclass(frozen=True)
class Block:
    id: str
    description: str
    match: MatchSpec
    inject: InjectSpec


@dataclass(frozen=True)
class LoadedBlocks:
    version: int
    blocks: tuple[Block, ...]
    default_match_confidence: float
    source_path: Path | None

    def to_block_set(self) -> BlockSet:
        """Project to the constraint-domain `BlockSet` consumed by `grammars.py`."""
        return BlockSet(
            blocks=tuple(
                BlockSpec(
                    id=b.id,
                    extras_schema=dict(b.match.extras_schema or {}),
                )
                for b in self.blocks
            ),
            default_match_confidence=self.default_match_confidence,
        )


def validate_template(template: str, *, where: str) -> None:
    """Reject anything beyond simple `{name}` / `{a.b.c}` placeholders.

    Templates are user-authored but MUST NOT execute Python (DIR-S-002).
    `str.format` would happily evaluate format specs, conversions, and
    attribute / item access — we forbid all of that at load time so a
    later substitution implementation cannot accidentally enable it.
    """
    for match in _PLACEHOLDER_FINDER_RE.finditer(template):
        inner = match.group(1).strip()
        if not inner:
            raise BlockConfigError(f"{where}: empty placeholder '{{}}'")
        if not _VALID_PLACEHOLDER_RE.match(inner):
            raise BlockConfigError(
                f"{where}: placeholder {{{inner}!r}} is not a simple "
                "dotted name. Only {{name}} or {{a.b.c}} are allowed."
            )


def save_blocks_yaml(path: Path, data: Mapping[str, Any]) -> None:
    """Validate `data` and write it to `path` atomically (`WFS-CFG-006`).

    Validation runs first via the same `_build_loaded_blocks` rules
    used on read; on failure `BlockConfigError` is raised and `path`
    is left untouched. On success the YAML is written to a sibling
    temp file and `os.replace`-d into place so a partial / clobbered
    target is not observable.
    """
    _build_loaded_blocks(data, source=path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.tmp.{os.getpid()}"
    serialized = yaml.safe_dump(dict(data), sort_keys=False, allow_unicode=True)
    try:
        tmp.write_text(serialized, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def load_blocks_yaml(path: Path) -> LoadedBlocks:
    """Load + validate a single blocks.yaml file."""
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise BlockConfigError(f"{path}: malformed YAML: {exc}") from exc
    if data is None:
        raise BlockConfigError(f"{path}: file is empty")
    if not isinstance(data, dict):
        raise BlockConfigError(
            f"{path}: top-level YAML must be a mapping, got {type(data).__name__}"
        )

    return _build_loaded_blocks(data, source=path)


def resolve_blocks(
    global_path: Path | None,
    project_root: Path | None,
) -> LoadedBlocks:
    """Resolve global vs. project blocks per §8.1.

    If a `<project_root>/.holdspeak/blocks.yaml` file exists, it
    **fully replaces** any global file (DIR-F-008). If only the global
    file exists, return that. If neither exists, return an empty
    `LoadedBlocks`.
    """
    if project_root is not None:
        project_file = project_root / ".holdspeak" / "blocks.yaml"
        if project_file.exists():
            return load_blocks_yaml(project_file)
    if global_path is not None and global_path.exists():
        return load_blocks_yaml(global_path)
    return LoadedBlocks(
        version=SUPPORTED_VERSION,
        blocks=(),
        default_match_confidence=0.6,
        source_path=None,
    )


def _build_loaded_blocks(data: Mapping[str, Any], *, source: Path) -> LoadedBlocks:
    where = str(source)
    version = data.get("version")
    if version is None:
        raise BlockConfigError(f"{where}: missing required key 'version'")
    if version != SUPPORTED_VERSION:
        raise BlockConfigError(
            f"{where}: unsupported version {version!r}; "
            f"only version {SUPPORTED_VERSION} is supported"
        )

    default_conf = data.get("default_match_confidence", 0.6)
    if not isinstance(default_conf, (int, float)):
        raise BlockConfigError(
            f"{where}: 'default_match_confidence' must be a number, "
            f"got {type(default_conf).__name__}"
        )
    if not 0.0 <= float(default_conf) <= 1.0:
        raise BlockConfigError(
            f"{where}: 'default_match_confidence' must be in [0.0, 1.0]"
        )

    blocks_data = data.get("blocks")
    if not isinstance(blocks_data, list):
        raise BlockConfigError(
            f"{where}: 'blocks' must be a list, got {type(blocks_data).__name__}"
        )

    blocks: list[Block] = []
    seen_ids: set[str] = set()
    for idx, b in enumerate(blocks_data):
        bw = f"{where}: blocks[{idx}]"
        if not isinstance(b, dict):
            raise BlockConfigError(f"{bw}: must be a mapping")
        block = _build_block(b, where=bw)
        if block.id in seen_ids:
            raise BlockConfigError(f"{bw}: duplicate block id {block.id!r}")
        seen_ids.add(block.id)
        blocks.append(block)

    return LoadedBlocks(
        version=SUPPORTED_VERSION,
        blocks=tuple(blocks),
        default_match_confidence=float(default_conf),
        source_path=source,
    )


def _build_block(b: Mapping[str, Any], *, where: str) -> Block:
    bid = b.get("id")
    if not isinstance(bid, str) or not bid:
        raise BlockConfigError(f"{where}.id: must be a non-empty string")
    description = b.get("description")
    if not isinstance(description, str):
        raise BlockConfigError(f"{where}.description: must be a string")

    match_data = b.get("match")
    if not isinstance(match_data, dict):
        raise BlockConfigError(f"{where}.match: must be a mapping")
    match = _build_match(match_data, where=f"{where}.match")

    inject_data = b.get("inject")
    if not isinstance(inject_data, dict):
        raise BlockConfigError(f"{where}.inject: must be a mapping")
    inject = _build_inject(inject_data, where=f"{where}.inject")

    return Block(
        id=bid,
        description=description,
        match=match,
        inject=inject,
    )


def _build_match(data: Mapping[str, Any], *, where: str) -> MatchSpec:
    examples = data.get("examples")
    if not isinstance(examples, list) or not all(isinstance(e, str) for e in examples):
        raise BlockConfigError(f"{where}.examples: must be a list of strings")
    if not examples:
        raise BlockConfigError(f"{where}.examples: must contain at least one example")

    neg = data.get("negative_examples", [])
    if not isinstance(neg, list) or not all(isinstance(e, str) for e in neg):
        raise BlockConfigError(
            f"{where}.negative_examples: must be a list of strings"
        )

    extras_raw = data.get("extras_schema")
    extras_schema: dict[str, tuple[str, ...]] | None
    if extras_raw is None:
        extras_schema = None
    else:
        if not isinstance(extras_raw, dict):
            raise BlockConfigError(f"{where}.extras_schema: must be a mapping")
        compiled: dict[str, tuple[str, ...]] = {}
        for key, spec in extras_raw.items():
            if not isinstance(key, str):
                raise BlockConfigError(
                    f"{where}.extras_schema: keys must be strings, "
                    f"got {type(key).__name__}"
                )
            if not isinstance(spec, dict):
                raise BlockConfigError(
                    f"{where}.extras_schema.{key}: must be a mapping with 'type' and 'values'"
                )
            if spec.get("type") != "enum":
                raise BlockConfigError(
                    f"{where}.extras_schema.{key}.type: only 'enum' is supported"
                )
            values = spec.get("values")
            if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                raise BlockConfigError(
                    f"{where}.extras_schema.{key}.values: must be a list of strings"
                )
            if not values:
                raise BlockConfigError(
                    f"{where}.extras_schema.{key}.values: must declare at least one value"
                )
            compiled[key] = tuple(values)
        extras_schema = compiled

    threshold = data.get("threshold")
    if threshold is not None:
        if not isinstance(threshold, (int, float)):
            raise BlockConfigError(f"{where}.threshold: must be a number")
        if not 0.0 <= float(threshold) <= 1.0:
            raise BlockConfigError(f"{where}.threshold: must be in [0.0, 1.0]")
        threshold = float(threshold)

    return MatchSpec(
        examples=tuple(examples),
        negative_examples=tuple(neg),
        extras_schema=extras_schema,
        threshold=threshold,
    )


def _build_inject(data: Mapping[str, Any], *, where: str) -> InjectSpec:
    mode_raw = data.get("mode")
    if not isinstance(mode_raw, str):
        raise BlockConfigError(f"{where}.mode: must be a string")
    try:
        mode = InjectMode(mode_raw)
    except ValueError as exc:
        modes = ", ".join(m.value for m in InjectMode)
        raise BlockConfigError(
            f"{where}.mode: {mode_raw!r} is not one of {{{modes}}}"
        ) from exc

    template = data.get("template")
    if not isinstance(template, str):
        raise BlockConfigError(f"{where}.template: must be a string")

    validate_template(template, where=f"{where}.template")

    return InjectSpec(mode=mode, template=template)
