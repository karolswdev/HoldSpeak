"""Integration tests for HS-3-02: project-context wiring through `Utterance` + blocks loader.

Two end-to-end paths verified:

1. **Controller path** — `HoldSpeakController._build_dictation_pipeline()`
   detects the project from cwd and (a) passes `project_root` through
   to `assembly.build_pipeline`, (b) populates `Utterance.project`
   for every utterance.
2. **CLI path** — `holdspeak.commands.dictation._cmd_dry_run` does the
   same and prints the detected project on stdout.
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.commands.dictation import _cmd_dry_run
from holdspeak.config import Config


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


# ---------------------------------------------------------------------------
# Controller path
# ---------------------------------------------------------------------------


def test_controller_pipeline_build_passes_project_root_and_utterance_carries_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real `_build_dictation_pipeline` runs; we capture the `project_root`
    `assembly.build_pipeline` receives + the `utt.project` the pipeline sees."""

    monkeypatch.setenv("HOME", str(tmp_path))
    root = _seed_project(tmp_path)
    monkeypatch.chdir(root)

    # Avoid touching unrelated controller subsystems.
    from tests.unit.test_controller import (
        _FakeApp,
        _FakeDictationPipeline,
        _FakePipelineRun,
        _FakeTranscriber,
        _patch_runtime_deps,
    )

    _patch_runtime_deps(monkeypatch)

    captured: dict[str, Any] = {}

    fake_pipeline = _FakeDictationPipeline(
        _FakePipelineRun(final_text="OK", total_elapsed_ms=1.0),
    )

    def _fake_build_pipeline(
        cfg, *, on_run=None, project_root=None, global_blocks_path=None,
        runtime_factory=None,
    ):
        captured["project_root"] = project_root
        return SimpleNamespace(
            pipeline=fake_pipeline,
            blocks=SimpleNamespace(blocks=[]),
            runtime_status="unavailable",
            runtime_detail="stub",
        )

    import holdspeak.plugins.dictation.assembly as assembly_module
    monkeypatch.setattr(assembly_module, "build_pipeline", _fake_build_pipeline)

    from holdspeak.controller import HoldSpeakController

    config = Config()
    config.dictation.pipeline.enabled = True
    app = _FakeApp(config)
    controller = HoldSpeakController(app, preloaded_transcriber=_FakeTranscriber())

    out = controller._maybe_run_dictation_pipeline(
        "hello",
        audio_duration_s=1.0,
        transcribed_at=datetime.now(),
    )

    assert out == "OK"
    # `project_root` flowed through to the loader.
    assert captured["project_root"] == root.resolve()
    # `Utterance.project` carries the detected context.
    assert len(fake_pipeline.calls) == 1
    utt = fake_pipeline.calls[0]
    assert isinstance(utt.project, dict)
    assert utt.project["name"] == "myproj"
    assert utt.project["anchor"] == "holdspeak"
    assert utt.project["root"] == str(root.resolve())


def test_controller_apply_runtime_config_clears_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-detection happens on the next pipeline build after a config edit."""
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _seed_project(tmp_path)
    monkeypatch.chdir(root)

    from tests.unit.test_controller import (
        _FakeApp,
        _FakeTranscriber,
        _patch_runtime_deps,
    )

    _patch_runtime_deps(monkeypatch)
    from holdspeak.controller import HoldSpeakController

    config = Config()
    app = _FakeApp(config)
    controller = HoldSpeakController(app, preloaded_transcriber=_FakeTranscriber())

    controller._dictation_project = {"name": "stale", "root": "/x", "anchor": "git"}
    controller.apply_runtime_config()

    assert controller._dictation_project is None
