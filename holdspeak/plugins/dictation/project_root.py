"""Cwd-based project-root detection for the dictation pipeline.

DIR-01 §6.4 declares `Utterance.project: ProjectContext | None  # from
project_detector` and §8.1 says per-project block overrides are
"auto-discovered via project_detector". The MIR-side
`holdspeak/plugins/project_detector.py` is a transcript→KB keyword
scorer, not a cwd-walking project-root finder. This module fills
that gap: a pure function that walks from cwd up to the user's
home and anchors on the first `.holdspeak/`, `.git/`, or recognized
language manifest it finds.

Output is a `ProjectContext` dict (intentionally untyped per the
contract in `holdspeak/plugins/dictation/contracts.py`) carrying at
least `name`, `root`, and `anchor`. If the project root contains
`.holdspeak/project.yaml`, its keys are loaded under a `kb` key.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from holdspeak.plugins.dictation.contracts import ProjectContext

# Priority within a single directory: `.holdspeak/` is the strongest
# signal (explicit project opt-in via DIR-01 §8.1 override blocks),
# then `.git/`, then language manifests.
_ANCHOR_PRIORITY: tuple[tuple[str, str], ...] = (
    (".holdspeak", "holdspeak"),
    (".git", "git"),
    ("pyproject.toml", "pyproject.toml"),
    ("package.json", "package.json"),
    ("Cargo.toml", "Cargo.toml"),
)


def detect_project_for_cwd(start: Path | None = None) -> ProjectContext | None:
    """Walk from `start` (default `Path.cwd()`) toward `$HOME`/root.

    Returns the first ancestor (inclusive of `start`) that contains a
    recognized anchor, or `None` if no anchor is found before the
    walk hits `$HOME` or the filesystem root. `$HOME` itself is never
    treated as a project root.
    """
    cur = (start if start is not None else Path.cwd()).resolve()
    home = Path.home().resolve()

    while True:
        if cur == home:
            return None
        anchor = _check_anchor(cur)
        if anchor is not None:
            return _build_context(cur, anchor)
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def _check_anchor(directory: Path) -> str | None:
    for marker, anchor in _ANCHOR_PRIORITY:
        if (directory / marker).exists():
            return anchor
    return None


def _build_context(root: Path, anchor: str) -> ProjectContext:
    ctx: ProjectContext = {
        "name": _derive_name(root),
        "root": str(root),
        "anchor": anchor,
    }
    kb = _load_optional_kb(root)
    if kb is not None:
        ctx["kb"] = kb
    return ctx


def _derive_name(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        name = _read_toml_name(pyproject, ("project", "name"))
        if name:
            return name
    cargo = root / "Cargo.toml"
    if cargo.is_file():
        name = _read_toml_name(cargo, ("package", "name"))
        if name:
            return name
    pkgjson = root / "package.json"
    if pkgjson.is_file():
        try:
            data = json.loads(pkgjson.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            name = data.get("name")
            if isinstance(name, str) and name:
                return name
    return root.name


def _read_toml_name(path: Path, dotted: tuple[str, ...]) -> str | None:
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return None
    try:
        with path.open("rb") as fh:
            data: Any = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    cursor: Any = data
    for key in dotted:
        if isinstance(cursor, dict) and key in cursor:
            cursor = cursor[key]
        else:
            return None
    if isinstance(cursor, str) and cursor:
        return cursor
    return None


def _load_optional_kb(root: Path) -> dict[str, Any] | None:
    try:
        from holdspeak.plugins.dictation.project_kb import ProjectKBError, read_project_kb
    except ImportError:
        return None

    try:
        return read_project_kb(root)
    except ProjectKBError:
        return None
