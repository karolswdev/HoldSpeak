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

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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


@pytest.mark.timeout(600)
@pytest.mark.skipif(shutil.which("uv") is None, reason="the clean venv is built with uv")
@pytest.mark.skipif(tomllib is None, reason="reads pyproject with tomllib")
def test_clean_base_install_imports_the_mcp_catalogue(tmp_path: Path) -> None:
    venv = tmp_path / "venv"
    subprocess.run(["uv", "venv", "-q", str(venv), "--python", f"{sys.version_info.major}.{sys.version_info.minor}"],
                   check=True, capture_output=True, text=True)
    requirements = tmp_path / "base.txt"
    requirements.write_text("\n".join(_base_dependencies()) + "\n", encoding="utf-8")
    python = venv / "bin" / "python"
    subprocess.run(["uv", "pip", "install", "-q", "--python", str(python), "-r", str(requirements)],
                   check=True, capture_output=True, text=True)
    probe = subprocess.run(
        [str(python), "-c", "import holdspeak.mcp.tools, holdspeak.operations; print('IMPORT OK')"],
        cwd=str(tmp_path), env={"PYTHONPATH": str(REPO), "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True,
    )
    assert probe.returncode == 0, probe.stderr[-2000:]
    assert "IMPORT OK" in probe.stdout
