"""Integration tests for HS-3-02: project-context wiring through `Utterance` + blocks loader.

CLI path — `holdspeak.commands.dictation._cmd_dry_run` detects the project
from cwd and prints it on stdout. (The runtime dictation-pipeline path —
`_maybe_run_dictation_pipeline` passing `project_root` through and populating
`Utterance.project` — is covered by `tests/unit/test_web_runtime.py`; the TUI
controller that previously exercised it here was retired in HS-32-07.)
"""

from __future__ import annotations

import io
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pytest

from holdspeak.commands.dictation import _cmd_dry_run


_BLOCKS_YAML = dedent(
    """
    version: 1
    default_match_confidence: 0.6
    blocks:
      - id: project_only
        description: Project-scoped test block
        match:
          examples:
            - "deploy this branch"
        inject:
          mode: replace
          template: "[deploy in {project.name}] {raw_text}"
    """
).strip()


def _seed_project(tmp_path: Path) -> Path:
    """Build a temp project tree with a `.holdspeak/blocks.yaml`."""
    root = tmp_path / "myproj"
    holdspeak_dir = root / ".holdspeak"
    holdspeak_dir.mkdir(parents=True)
    (holdspeak_dir / "blocks.yaml").write_text(_BLOCKS_YAML, encoding="utf-8")
    (root / "pyproject.toml").write_text('[project]\nname = "myproj"\n', encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# CLI path
# ---------------------------------------------------------------------------


def test_cli_dry_run_populates_project_from_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _seed_project(tmp_path)
    monkeypatch.chdir(root)

    args = SimpleNamespace(text="hello world")
    out = io.StringIO()

    rc = _cmd_dry_run(args, out)

    assert rc == 0
    output = out.getvalue()
    assert "project: myproj" in output
    assert "(holdspeak @" in output  # anchor + path summary line
    # The project's .holdspeak/blocks.yaml was loaded, not the global file.
    assert "resolved blocks: 1" in output
    assert ".holdspeak/blocks.yaml" in output


def test_cli_dry_run_reports_no_project_outside_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    bare = tmp_path / "no_project_here"
    bare.mkdir()
    monkeypatch.chdir(bare)

    args = SimpleNamespace(text="hello world")
    out = io.StringIO()

    rc = _cmd_dry_run(args, out)

    assert rc == 0
    assert "project: (none detected)" in out.getvalue()
