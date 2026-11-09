"""The repository tree, parsed once per test process.

The censuses read the same files: ``holdspeak/`` (Python) and ``web/src``
(TypeScript). Before 2026-11-09 each census walked and parsed the tree by
itself, so one xdist worker parsed ``holdspeak/`` several times. This module
keeps one cache per process, keyed by path and mtime:

* ``python_files(root)`` / ``ts_files(root)``: the sorted file list.
* ``text_of(path)``: the file text.
* ``ast_of(path)``: the parsed module (shared: never change it).
* ``walk(path)``: the flat ``ast.walk`` node list of that module.

A path is absolute or relative to the repository root.
"""

from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_TEXT: dict[Path, tuple[float, str]] = {}
_AST: dict[Path, tuple[float, ast.Module]] = {}
_WALK: dict[Path, tuple[float, list[ast.AST]]] = {}


def _abs(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def _mtime(path: Path) -> float:
    return path.stat().st_mtime_ns


def _files(root: Path, suffixes: tuple[str, ...], exclude: tuple[str, ...]) -> tuple[Path, ...]:
    # The repository tree does not change during a run: its lists are cached.
    # A root outside it (a test's tmp_path) is listed fresh each time.
    if root.is_relative_to(ROOT):
        return _repo_files(root, suffixes, exclude)
    return _list(root, suffixes, exclude)


@lru_cache(maxsize=None)
def _repo_files(root: Path, suffixes: tuple[str, ...], exclude: tuple[str, ...]) -> tuple[Path, ...]:
    return _list(root, suffixes, exclude)


def _list(root: Path, suffixes: tuple[str, ...], exclude: tuple[str, ...]) -> tuple[Path, ...]:
    out = []
    for path in root.rglob("*"):
        if path.suffix not in suffixes or not path.is_file():
            continue
        parts = path.relative_to(root).parts
        if "__pycache__" in parts or "node_modules" in parts:
            continue
        if any(part in exclude for part in parts):
            continue
        out.append(path)
    return tuple(sorted(out))


def python_files(root: str | Path = "holdspeak", *, exclude: tuple[str, ...] = ()) -> tuple[Path, ...]:
    """Every ``.py`` file under ``root``; ``exclude`` drops any path with that part."""
    return _files(_abs(root), (".py",), tuple(exclude))


def ts_files(
    root: str | Path = "web/src",
    *,
    suffixes: tuple[str, ...] = (".ts", ".tsx"),
    exclude: tuple[str, ...] = (),
) -> tuple[Path, ...]:
    """Every TypeScript file under ``root`` (``suffixes`` widens it, e.g. ``.css``)."""
    return _files(_abs(root), tuple(suffixes), tuple(exclude))


def text_of(path: str | Path) -> str:
    p = _abs(path)
    stamp = _mtime(p)
    hit = _TEXT.get(p)
    if hit is None or hit[0] != stamp:
        hit = (stamp, p.read_text(encoding="utf-8"))
        _TEXT[p] = hit
    return hit[1]


def ast_of(path: str | Path) -> ast.Module:
    p = _abs(path)
    stamp = _mtime(p)
    hit = _AST.get(p)
    if hit is None or hit[0] != stamp:
        hit = (stamp, ast.parse(text_of(p), filename=str(p)))
        _AST[p] = hit
    return hit[1]


def walk(path: str | Path) -> list[ast.AST]:
    p = _abs(path)
    stamp = _mtime(p)
    hit = _WALK.get(p)
    if hit is None or hit[0] != stamp:
        hit = (stamp, list(ast.walk(ast_of(p))))
        _WALK[p] = hit
    return hit[1]
