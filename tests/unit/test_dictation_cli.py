"""Unit tests for `holdspeak dictation` CLI (HS-1-08)."""

from __future__ import annotations

import io
from pathlib import Path
from types import SimpleNamespace

import pytest

import holdspeak.commands.dictation as cli
import holdspeak.plugins.dictation.assembly as assembly
from holdspeak.config import Config


_VALID_BLOCKS_YAML = """\
version: 1
default_match_confidence: 0.6
blocks:
  - id: ai_prompt_buildout
    description: User is building out a prompt for an AI assistant.
    match:
      examples:
        - "Claude, please build me a function that..."
      negative_examples:
        - "What time is it?"
    inject:
      mode: append
      template: |
        {raw_text}

        --- (HoldSpeak context appended)
"""

_INVALID_BLOCKS_YAML = """\
version: 1
blocks:
  - id: bad_block
    description: missing match section
    inject:
      mode: append
      template: "{raw_text}"
"""


@pytest.fixture
def tmp_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    blocks_path = tmp_path / "blocks.yaml"
    blocks_path.write_text(_VALID_BLOCKS_YAML, encoding="utf-8")
    monkeypatch.setattr(assembly, "DEFAULT_GLOBAL_BLOCKS_PATH", blocks_path)
    monkeypatch.setattr(cli, "Config", _ConfigStub)
    return blocks_path


class _ConfigStub:
    """Stand-in for `Config.load()` returning a default config.

    Used so the CLI doesn't read the real user config file.
    """

    @classmethod
    def load(cls) -> Config:
        return Config()


# ---------------------------------------------------------------------------
# dry-run
# ---------------------------------------------------------------------------


def test_dry_run_falls_back_to_no_llm_when_runtime_unavailable(monkeypatch, tmp_blocks):
    def _broken_factory(**_kwargs):
        from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError
        raise RuntimeUnavailableError("no model configured")

    monkeypatch.setattr(assembly, "build_runtime", _broken_factory)

    args = SimpleNamespace(dictation_action="dry-run", text="hello there")
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)

    text = out.getvalue()
    assert rc == 0
    assert "warning: LLM runtime unavailable" in text
    assert "[intent-router]" not in text  # skipped when llm_enabled=False
    assert "[kb-enricher]" in text
    assert "final_text:" in text


def test_dry_run_prints_each_stage_when_runtime_loaded(monkeypatch, tmp_blocks):
    class _StubRuntime:
        backend = "stub"

        def load(self) -> None:
            pass

        def info(self):
            return {"backend": "stub"}

        def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
            return {
                "matched": True,
                "block_id": "ai_prompt_buildout",
                "confidence": 0.95,
                "extras": {},
            }

    def _factory(**_kwargs):
        return _StubRuntime()

    monkeypatch.setattr(assembly, "build_runtime", _factory)

    args = SimpleNamespace(dictation_action="dry-run", text="claude do thing")
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)

    text = out.getvalue()
    assert rc == 0
    assert "warning: LLM runtime unavailable" not in text
    assert "[intent-router]" in text
    assert "[kb-enricher]" in text
    assert "matched=True block_id=ai_prompt_buildout" in text
    assert "(HoldSpeak context appended)" in text


# ---------------------------------------------------------------------------
# blocks
# ---------------------------------------------------------------------------


def test_blocks_ls_prints_loaded_block_ids(tmp_blocks):
    args = SimpleNamespace(dictation_action="blocks-ls", project=None)
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    assert rc == 0
    assert "ai_prompt_buildout" in out.getvalue()


def test_blocks_ls_reports_empty_when_no_blocks_file(tmp_path, monkeypatch):
    monkeypatch.setattr(assembly, "DEFAULT_GLOBAL_BLOCKS_PATH", tmp_path / "missing.yaml")
    args = SimpleNamespace(dictation_action="blocks-ls", project=None)
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    assert rc == 0
    assert "no blocks loaded" in out.getvalue()


def test_blocks_show_prints_block_spec(tmp_blocks):
    args = SimpleNamespace(
        dictation_action="blocks-show",
        block_id="ai_prompt_buildout",
        project=None,
    )
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    assert rc == 0
    body = out.getvalue()
    assert "id: ai_prompt_buildout" in body
    assert "inject.mode: append" in body
    assert "(HoldSpeak context appended)" in body


def test_blocks_show_returns_usage_exit_when_id_missing(tmp_blocks):
    args = SimpleNamespace(
        dictation_action="blocks-show",
        block_id="not_a_real_block",
        project=None,
    )
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    assert rc == 2
    assert "no block with id" in out.getvalue()


def test_blocks_validate_passes_on_valid_yaml(tmp_blocks, monkeypatch):
    args = SimpleNamespace(dictation_action="blocks-validate", project=None)
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    assert rc == 0
    assert "ok:" in out.getvalue()


def test_blocks_validate_fails_on_invalid_yaml(tmp_path, monkeypatch):
    bad = tmp_path / "blocks.yaml"
    bad.write_text(_INVALID_BLOCKS_YAML, encoding="utf-8")
    monkeypatch.setattr(assembly, "DEFAULT_GLOBAL_BLOCKS_PATH", bad)

    args = SimpleNamespace(dictation_action="blocks-validate", project=None)
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    assert rc == 2
    assert "error:" in out.getvalue()


def test_blocks_validate_no_op_when_file_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(assembly, "DEFAULT_GLOBAL_BLOCKS_PATH", tmp_path / "absent.yaml")
    args = SimpleNamespace(dictation_action="blocks-validate", project=None)
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    assert rc == 0
    assert "nothing to validate" in out.getvalue()


# ---------------------------------------------------------------------------
# runtime status
# ---------------------------------------------------------------------------


def test_runtime_status_reports_resolved_backend(monkeypatch, tmp_blocks):
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime.resolve_backend",
        lambda requested, **_kw: ("llama_cpp", "stubbed for test"),
    )
    args = SimpleNamespace(dictation_action="runtime-status")
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    text = out.getvalue()
    assert rc == 0
    assert "resolved backend: llama_cpp (stubbed for test)" in text


def test_runtime_status_reports_unavailable_without_failing(monkeypatch, tmp_blocks):
    from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError

    def _refuse(requested, **_kw):
        raise RuntimeUnavailableError("no backend installed in this env")

    monkeypatch.setattr("holdspeak.plugins.dictation.runtime.resolve_backend", _refuse)
    args = SimpleNamespace(dictation_action="runtime-status")
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    text = out.getvalue()
    assert rc == 0
    assert "resolution: unavailable" in text


# ---------------------------------------------------------------------------
# dispatcher edges + argparse normalization
# ---------------------------------------------------------------------------


def test_unknown_action_returns_usage_exit(tmp_blocks):
    args = SimpleNamespace(dictation_action=None)
    out = io.StringIO()
    rc = cli.run_dictation_command(args, stream=out)
    assert rc == 2
    assert "usage:" in out.getvalue()


def test_normalize_args_collapses_nested_subparsers():
    args = SimpleNamespace(dictation_action="blocks", dictation_blocks_action="ls", project=None)
    cli.normalize_args(args)
    assert args.dictation_action == "blocks-ls"

    args2 = SimpleNamespace(dictation_action="runtime", dictation_runtime_action="status")
    cli.normalize_args(args2)
    assert args2.dictation_action == "runtime-status"

    args3 = SimpleNamespace(dictation_action="blocks", dictation_blocks_action=None)
    cli.normalize_args(args3)
    assert args3.dictation_action is None
