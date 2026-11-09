"""PHILO-9-01 (F14): a base install imports the MCP catalogue.

Red on main ``ffbeb04b``: ``holdspeak/operations.py`` imports ``jsonschema``,
which only the ``test`` and ``dev`` extras declared, so a venv built from the
base dependencies alone failed ``import holdspeak.mcp.tools`` with
``ModuleNotFoundError: No module named 'jsonschema'``.

The fence builds a REAL clean venv from ``[project].dependencies`` only (no
extras, no project install; the tree is put on ``PYTHONPATH``) and imports the
catalogue in it. ``UV_CACHE_DIR`` is honoured, so an isolated-HOME run can
reuse the warm cache.
"""
from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    tomllib = None


def _base_dependencies() -> list[str]:
    assert tomllib is not None
    return list(tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"])


def test_base_dependencies_declare_jsonschema() -> None:
    names = [dep.split(">")[0].split("=")[0].split(";")[0].strip().lower() for dep in _base_dependencies()]
    assert "jsonschema" in names


# Owner ruling 2026-10-03 (fast tests): this test builds a clean venv and installs the base dependencies (60 s to 130 s). It is marked slow: the fast
# run (`-m "not slow"`) leaves it out; the nightly full run and a direct run keep it.
