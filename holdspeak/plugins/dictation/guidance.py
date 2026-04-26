"""Shared setup guidance for dictation runtime dependencies and models."""

from __future__ import annotations

import platform
import shlex
from pathlib import Path
from typing import Any, Optional


def _quote_path(path: Path) -> str:
    return shlex.quote(str(path))


def _system_name(system: str | None) -> str:
    return system if system is not None else platform.system()


def _machine_name(machine: str | None) -> str:
    return machine if machine is not None else platform.machine()


def runtime_install_command(
    backend: str,
    *,
    system: str | None = None,
    machine: str | None = None,
) -> str:
    """Return the local install command for one dictation LLM backend."""
    if (
        backend == "llama_cpp"
        and _system_name(system) == "Darwin"
        and _machine_name(machine) == "arm64"
    ):
        return 'CMAKE_ARGS="-DGGML_METAL=on" uv pip install -e \'.[dictation-llama]\''
    if backend == "llama_cpp":
        return "uv pip install -e '.[dictation-llama]'"
    return "uv pip install -e '.[dictation-mlx]'"


def runtime_model_download_command(backend: str, model_path: Path) -> Optional[str]:
    """Return the default model download command for a concrete backend."""
    expanded = model_path.expanduser()
    if backend == "mlx":
        return (
            "huggingface-cli download mlx-community/Qwen3-8B-MLX-4bit "
            f"--local-dir {_quote_path(expanded)}"
        )
    if backend == "llama_cpp":
        parent = expanded.parent
        return (
            f"mkdir -p {_quote_path(parent)} && "
            "huggingface-cli download bartowski/Qwen2.5-3B-Instruct-GGUF "
            "Qwen2.5-3B-Instruct-Q4_K_M.gguf "
            f"--local-dir {_quote_path(parent)} --local-dir-use-symlinks False"
        )
    return None


def runtime_guidance(
    *,
    kind: str,
    requested_backend: str,
    resolved_backend: Optional[str] = None,
    model_path: Optional[Path] = None,
    system: str | None = None,
    machine: str | None = None,
) -> dict[str, Any]:
    """Return browser-facing remediation guidance without mutating anything."""
    backend = resolved_backend or requested_backend
    links = [
        {
            "label": "README: Optional Dictation LLM Backend",
            "target": "README.md#optional-dictation-llm-backend",
        }
    ]

    if kind == "missing_model" and model_path is not None:
        expanded_model_path = model_path.expanduser()
        commands = [
            {
                "label": "Create model directory",
                "command": f"mkdir -p {_quote_path(expanded_model_path.parent)}",
            }
        ]
        download = runtime_model_download_command(backend, expanded_model_path)
        if download is not None:
            commands.append({"label": "Download default model", "command": download})
        return {
            "kind": kind,
            "backend": backend,
            "title": f"Add the {backend} model",
            "summary": (
                "The dictation pipeline is enabled, but the selected runtime model "
                "path does not exist."
            ),
            "model_path": str(expanded_model_path),
            "next_step": (
                f"Place a compatible {backend} model at {expanded_model_path} "
                "or update the model path in Runtime."
            ),
            "commands": commands,
            "links": links,
        }

    commands: list[dict[str, str]] = []
    if requested_backend == "auto":
        if _system_name(system) == "Darwin" and _machine_name(machine) == "arm64":
            commands.append({
                "label": "Install MLX extra",
                "command": runtime_install_command("mlx", system=system, machine=machine),
            })
        commands.append({
            "label": "Install llama_cpp extra",
            "command": runtime_install_command("llama_cpp", system=system, machine=machine),
        })
    else:
        commands.append({
            "label": f"Install {requested_backend} extra",
            "command": runtime_install_command(
                requested_backend,
                system=system,
                machine=machine,
            ),
        })

    return {
        "kind": kind,
        "backend": requested_backend,
        "title": f"Install the {requested_backend} runtime",
        "summary": "The selected dictation runtime backend is not importable in this environment.",
        "model_path": None,
        "next_step": "Install the runtime extra, then refresh readiness before downloading a model.",
        "commands": commands,
        "links": links,
    }


def doctor_runtime_install_fix(
    requested_backend: str,
    *,
    system: str | None = None,
    machine: str | None = None,
) -> str:
    """Return terminal-facing install guidance for `holdspeak doctor`."""
    guidance = runtime_guidance(
        kind="unavailable",
        requested_backend=requested_backend,
        system=system,
        machine=machine,
    )
    commands = [item["command"] for item in guidance["commands"]]
    if requested_backend == "mlx":
        return f"Install the MLX dictation backend: {commands[0]}"
    if requested_backend == "llama_cpp":
        return f"Install the llama_cpp dictation backend: {commands[0]}"
    return "Install one dictation backend: " + " OR ".join(commands)


def doctor_model_fix(backend: str, target: Path) -> str:
    """Return terminal-facing model guidance for `holdspeak doctor`."""
    guidance = runtime_guidance(
        kind="missing_model",
        requested_backend=backend,
        resolved_backend=backend,
        model_path=target,
    )
    download = next(
        (
            item["command"]
            for item in guidance["commands"]
            if item["label"] == "Download default model"
        ),
        None,
    )
    model_name = (
        "Qwen3-8B-MLX-4bit"
        if backend == "mlx"
        else "Qwen2.5-3B-Instruct-Q4_K_M.gguf"
    )
    return f"Create the model directory and download {model_name}: {download}"
