"""Unit tests for shared dictation runtime setup guidance."""

from __future__ import annotations

from pathlib import Path

from holdspeak.plugins.dictation.guidance import (
    doctor_model_fix,
    doctor_runtime_install_fix,
    runtime_guidance,
    runtime_docs_target,
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
    assert len(commands) == 3
    assert any("dictation-mlx" in command for command in commands)
    assert any("dictation-llama" in command for command in commands)
    assert any("dictation-openai" in command for command in commands)
    assert guidance["command_bundle"] == "\n".join(commands)
    assert guidance["links"] == [
        {"label": "Dictation runtime setup", "target": "/docs/dictation-runtime"}
    ]


def test_runtime_docs_target_uses_backend_anchors() -> None:
    assert runtime_docs_target("mlx") == "/docs/dictation-runtime#mlx"
    assert runtime_docs_target("llama_cpp") == "/docs/dictation-runtime#llama-cpp"
    assert runtime_docs_target("openai_compatible") == "/docs/dictation-runtime#openai-compatible"
    assert runtime_docs_target("auto") == "/docs/dictation-runtime"


def test_missing_model_guidance_has_copyable_command_bundle(tmp_path: Path) -> None:
    target = tmp_path / "models" / "qwen.gguf"

    guidance = runtime_guidance(
        kind="missing_model",
        requested_backend="llama_cpp",
        resolved_backend="llama_cpp",
        model_path=target,
    )

    commands = [item["command"] for item in guidance["commands"]]
    assert len(commands) == 2
    assert guidance["command_bundle"] == "\n".join(commands)
    assert guidance["links"][0]["target"] == "/docs/dictation-runtime#llama-cpp"


def test_doctor_model_fix_names_the_missing_file(tmp_path: Path) -> None:
    """PHILO-15 11 (B08): the hint named another file from another repository."""
    target = tmp_path / "models" / "qwen.gguf"

    fix = doctor_model_fix("llama_cpp", target)

    assert "qwen.gguf" in fix
    assert str(target.parent) in fix
    assert "Qwen3.5-4B-Instruct-Q4_K_M.gguf" not in fix
    assert "huggingface-cli" not in fix


def test_doctor_model_fix_for_the_products_model_points_at_set_up_local_ai(tmp_path: Path) -> None:
    from holdspeak.intel.models import DEFAULT_INTEL_MODEL_PATH

    target = tmp_path / Path(DEFAULT_INTEL_MODEL_PATH).relative_to("~")

    fix = doctor_model_fix("llama_cpp", target)

    assert "Set up local AI" in fix
    assert fix.endswith("It downloads Qwen3.5-4B-Q4_K_M.gguf.")
    assert "Instruct" not in fix and "huggingface-cli" not in fix


def test_doctor_install_fix_reuses_runtime_guidance() -> None:
    fix = doctor_runtime_install_fix("llama_cpp", system="Linux", machine="x86_64")

    assert "uv pip install" in fix
    assert "dictation-llama" in fix
