"""Project knowledge-base authoring helpers (HS-4-03 / `WFS-CFG-003`).

`<project_root>/.holdspeak/project.yaml` carries an optional `kb`
mapping consumed by the kb-enricher stage's `{project.kb.*}`
template placeholders (DIR-01 §8.4). This module provides read /
write / delete primitives with the same atomic-write semantics
(`WFS-CFG-006`) used for `blocks.yaml`, plus key/value validation
that ensures placeholders resolve cleanly via
`kb_enricher._lookup`'s dotted-name traversal.

Companion to `project_root.py` (which auto-detects the root and
lazily loads the kb dict for read-only consumption); this module
is the write side.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

KB_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ProjectKBError(ValueError):
    """Raised when a project-kb document fails to load or validate."""


def kb_path_for(root: Path) -> Path:
    return root / ".holdspeak" / "project.yaml"


def read_project_kb(root: Path) -> dict[str, Any] | None:
    """Return the `kb` mapping or `None` when the file is absent.

    Raises `ProjectKBError` for malformed YAML, non-mapping top-level,
    or a `kb` value that isn't a mapping. A missing `kb` key is treated
    as `{}` — the file may exist for other reasons (future extensions).
    """
    path = kb_path_for(root)
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        raise ProjectKBError(f"{path}: malformed YAML: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ProjectKBError(
            f"{path}: top-level YAML must be a mapping, got {type(data).__name__}"
        )
    kb = data.get("kb", {})
    if kb is None:
        return {}
    if not isinstance(kb, dict):
        raise ProjectKBError(
            f"{path}: 'kb' must be a mapping, got {type(kb).__name__}"
        )
    _validate_kb_mapping(kb, where=str(path))
    return kb


def write_project_kb(root: Path, kb: Mapping[str, Any]) -> None:
    """Validate `kb` and atomically write `<root>/.holdspeak/project.yaml`.

    Validation runs first; on failure `ProjectKBError` is raised and
    no file is touched. On success the YAML is written to a sibling
    temp file and `os.replace`-d into place (`WFS-CFG-006`).
    """
    path = kb_path_for(root)
    _validate_kb_mapping(kb, where=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {"kb": dict(kb)}
    serialized = yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
    tmp = path.parent / f".{path.name}.tmp.{os.getpid()}"
    try:
        tmp.write_text(serialized, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def delete_project_kb(root: Path) -> bool:
    """Remove `<root>/.holdspeak/project.yaml`. Returns True if removed.

    The `.holdspeak/` directory itself is preserved — it's also the
    strongest project-anchor signal in `detect_project_for_cwd()`,
    so deleting it would silently downgrade detection.
    """
    path = kb_path_for(root)
    if not path.exists():
        return False
    path.unlink()
    return True


def _validate_kb_mapping(kb: Mapping[str, Any], *, where: str) -> None:
    for key, value in kb.items():
        if not isinstance(key, str):
            raise ProjectKBError(
                f"{where}: kb keys must be strings, got {type(key).__name__}"
            )
        if not KB_KEY_RE.match(key):
            raise ProjectKBError(
                f"{where}: kb key {key!r} must match [A-Za-z_][A-Za-z0-9_]* "
                "so {{project.kb.<key>}} placeholders resolve cleanly"
            )
        if value is not None and not isinstance(value, str):
            raise ProjectKBError(
                f"{where}: kb[{key!r}] must be a string or null, "
                f"got {type(value).__name__}"
            )
