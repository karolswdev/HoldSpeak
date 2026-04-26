"""Unit tests for shared dictation runtime setup guidance."""

from __future__ import annotations

from pathlib import Path

from holdspeak.plugins.dictation.guidance import (
    doctor_model_fix,
    doctor_runtime_install_fix,
    runtime_guidance,
    runtime_install_command,
)


def test_llama_cpp_install_command_uses_metal_on_apple_silicon() -> None:
    command = runtime_install_command("llama_cpp", system="Darwin", machine="arm64")

    assert 'CMAKE_ARGS="-DGGML_METAL=on"' in command
    assert "dictation-llama" in command


def test_runtime_guidance_auto_offers_backend_commands() -> None:
    guidance = runtime_guidance(
        kind="unavailable",
        requested_backend="auto",
        system="Darwin",
        machine="arm64",
    )

    commands = [item["command"] for item in guidance["commands"]]
    assert len(commands) == 2
    assert any("dictation-mlx" in command for command in commands)
    assert any("dictation-llama" in command for command in commands)


def test_doctor_model_fix_reuses_download_command(tmp_path: Path) -> None:
    target = tmp_path / "models" / "qwen.gguf"

    fix = doctor_model_fix("llama_cpp", target)

    assert "huggingface-cli download" in fix
    assert str(target.parent) in fix
    assert "Qwen2.5-3B-Instruct-Q4_K_M.gguf" in fix


def test_doctor_install_fix_reuses_runtime_guidance() -> None:
    fix = doctor_runtime_install_fix("llama_cpp", system="Linux", machine="x86_64")

    assert "uv pip install" in fix
    assert "dictation-llama" in fix
