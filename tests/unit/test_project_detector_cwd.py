"""Unit tests for `holdspeak.plugins.dictation.project_root.detect_project_for_cwd`.

Covers anchor priority, walk semantics, name derivation fallbacks,
optional `kb` loading, and the `$HOME` boundary.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.plugins.dictation.project_root import detect_project_for_cwd


def _mk(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def test_holdspeak_anchor_beats_git_at_same_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _mk(tmp_path / "proj")
    _mk(root / ".holdspeak")
    _mk(root / ".git")

    ctx = detect_project_for_cwd(root)

    assert ctx is not None
    assert ctx["anchor"] == "holdspeak"
    assert ctx["root"] == str(root.resolve())


def test_git_anchor_beats_pyproject_at_same_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _mk(tmp_path / "proj")
    _mk(root / ".git")
    (root / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")

    ctx = detect_project_for_cwd(root)

    assert ctx is not None
    assert ctx["anchor"] == "git"


def test_walks_up_from_nested_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _mk(tmp_path / "proj")
    _mk(root / ".git")
    nested = _mk(root / "src" / "deep" / "module")

    ctx = detect_project_for_cwd(nested)

    assert ctx is not None
    assert ctx["root"] == str(root.resolve())
    assert ctx["anchor"] == "git"


def test_returns_none_outside_any_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    bare = _mk(tmp_path / "no_project_here" / "deep")

    assert detect_project_for_cwd(bare) is None


def test_name_derivation_pyproject_then_cargo_then_package_then_dirname(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    # 1. pyproject.toml wins.
    a = _mk(tmp_path / "a")
    _mk(a / ".git")
    (a / "pyproject.toml").write_text('[project]\nname = "alpha-pkg"\n', encoding="utf-8")
    (a / "Cargo.toml").write_text('[package]\nname = "alpha-rust"\n', encoding="utf-8")
    (a / "package.json").write_text(json.dumps({"name": "alpha-js"}), encoding="utf-8")
    assert detect_project_for_cwd(a)["name"] == "alpha-pkg"

    # 2. Cargo.toml when no pyproject.
    b = _mk(tmp_path / "b")
    _mk(b / ".git")
    (b / "Cargo.toml").write_text('[package]\nname = "beta-rust"\n', encoding="utf-8")
    (b / "package.json").write_text(json.dumps({"name": "beta-js"}), encoding="utf-8")
    assert detect_project_for_cwd(b)["name"] == "beta-rust"

    # 3. package.json when no toml files.
    c = _mk(tmp_path / "c")
    _mk(c / ".git")
    (c / "package.json").write_text(json.dumps({"name": "gamma-js"}), encoding="utf-8")
    assert detect_project_for_cwd(c)["name"] == "gamma-js"

    # 4. Dirname when no manifests.
    d = _mk(tmp_path / "delta_dir")
    _mk(d / ".git")
    assert detect_project_for_cwd(d)["name"] == "delta_dir"


def test_kb_absent_when_no_project_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _mk(tmp_path / "proj")
    _mk(root / ".holdspeak")  # anchor exists, but no project.yaml inside

    ctx = detect_project_for_cwd(root)
    assert ctx is not None
    assert "kb" not in ctx


def test_kb_loaded_when_project_yaml_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _mk(tmp_path / "proj")
    _mk(root / ".holdspeak")
    (root / ".holdspeak" / "project.yaml").write_text(
        "stack: python\nrecent_adrs_short: ADR-007\n", encoding="utf-8"
    )

    ctx = detect_project_for_cwd(root)
    assert ctx is not None
    assert ctx.get("kb") == {"stack": "python", "recent_adrs_short": "ADR-007"}


def test_does_not_escape_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If HOME has anchors, they are not returned for a child without its own anchors."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Plant an anchor at HOME itself.
    _mk(tmp_path / ".git")
    child = _mk(tmp_path / "child" / "deep")  # no anchors here or at "child"

    assert detect_project_for_cwd(child) is None
