"""Runtime self-test for the setup model assistant (HS-42-06).

Tests the configured dictation (intelligent-typing) runtime and reports a plain
pass/fail + detail, reusing the existing `resolve_backend` for local backends and
a time-boxed HTTP preflight for an OpenAI-compatible endpoint. The HTTP getter is
injectable so the default test suite never makes a real outbound call.
"""
from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .logging_config import get_logger

log = get_logger("setup_runtime")


def _default_http_get(url: str, *, headers: dict[str, str], timeout: float) -> int:
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - explicit http(s) preflight
        return int(getattr(resp, "status", 200) or 200)


def _default_http_json(
    url: str, *, headers: dict[str, str], timeout: float
) -> tuple[int, bytes]:
    req = Request(url, headers=headers, method="GET")
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 - user-requested model discovery
        return int(getattr(resp, "status", 200) or 200), resp.read()


CONTEXT_WINDOW_PRESETS = [8192, 16384, 32768, 65536, 131072, 200000, 1000000]


def discover_endpoint_models(
    base_url: str,
    *,
    api_key: str | None = None,
    timeout_seconds: float = 4.0,
    http_get: Optional[Callable[..., tuple[int, bytes]]] = None,
) -> dict[str, Any]:
    """Ask an OpenAI-compatible ``/models`` endpoint for its real model ids."""
    base = str(base_url or "").strip().rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {
            "ok": False,
            "models": [],
            "detail": "Enter a complete http:// or https:// server address.",
        }
    if parsed.username or parsed.password:
        return {
            "ok": False,
            "models": [],
            "detail": "Do not put credentials in the server address.",
        }

    models_url = f"{base}/models"
    headers = {"Accept": "application/json"}
    if str(api_key or "").strip():
        headers["Authorization"] = f"Bearer {str(api_key).strip()}"
    getter = http_get or _default_http_json
    try:
        code, raw = getter(models_url, headers=headers, timeout=timeout_seconds)
    except HTTPError as exc:
        if exc.code in {401, 403}:
            detail = "The server requires a key. Save the connection, set its hub key, then try again."
        elif exc.code == 404:
            detail = "The server has no /models route. Check whether the address should end in /v1."
        else:
            detail = f"The server returned HTTP {exc.code} for /models."
        return {"ok": False, "models": [], "detail": detail, "status": exc.code}
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        return {
            "ok": False,
            "models": [],
            "detail": f"Could not reach the model server: {exc}",
        }
    if not 200 <= int(code) < 300:
        return {
            "ok": False,
            "models": [],
            "detail": f"The server returned HTTP {code} for /models.",
            "status": int(code),
        }
    try:
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except (AttributeError, json.JSONDecodeError):
        return {
            "ok": False,
            "models": [],
            "detail": "The server answered, but /models did not return JSON.",
        }
    rows = payload.get("data") if isinstance(payload, dict) else None
    models = sorted(
        {
            str(row.get("id") or "").strip()
            for row in rows or []
            if isinstance(row, dict) and str(row.get("id") or "").strip()
        },
        key=str.casefold,
    )
    return {
        "ok": True,
        "models": models,
        "detail": (
            f"Found {len(models)} model{'s' if len(models) != 1 else ''}."
            if models
            else "Connected, but the server reported no models. You can enter one manually."
        ),
        "status": int(code),
    }


def discover_local_models(home: Path | None = None) -> dict[str, Any]:
    """List real MLX directories and GGUF files visible to this product run."""
    root = (home or Path.home()).expanduser()
    mlx_root = root / "Models" / "mlx"
    gguf_root = root / "Models" / "gguf"
    mlx = sorted(
        (path for path in mlx_root.iterdir() if path.is_dir()),
        key=lambda path: path.name.casefold(),
    ) if mlx_root.is_dir() else []
    gguf = sorted(
        (path for path in gguf_root.rglob("*.gguf") if path.is_file()),
        key=lambda path: path.name.casefold(),
    )[:200] if gguf_root.is_dir() else []
    return {
        "platform": {
            "system": platform.system().lower(),
            "machine": platform.machine().lower(),
            "apple_silicon": platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"},
        },
        "mlx": [{"label": path.name, "value": str(path)} for path in mlx],
        "gguf": [{"label": path.name, "value": str(path)} for path in gguf],
        "context_presets": CONTEXT_WINDOW_PRESETS,
    }


def probe_runtime(
    dictation_cfg: Any,
    *,
    http_get: Optional[Callable[..., int]] = None,
    timeout_seconds: float = 4.0,
) -> dict[str, Any]:
    """Test the configured dictation runtime. Returns `{ok, status, backend, detail}`.

    - pipeline disabled → `basic` (no LLM runtime needed; voice typing still works).
    - mlx / llama_cpp → resolve the backend, then check the model path exists.
    - openai_compatible → a time-boxed GET `{base_url}/models` preflight.
    Never raises — every failure is a `{ok: False}` result with a `detail`.
    """
    from .plugins.dictation import runtime as runtime_module

    pipeline = getattr(dictation_cfg, "pipeline", None)
    runtime = getattr(dictation_cfg, "runtime", None)
    if pipeline is None or not getattr(pipeline, "enabled", False):
        return {
            "ok": True,
            "status": "basic",
            "backend": None,
            "detail": "Basic voice typing — no LLM runtime configured. Hold, speak, release works as-is.",
        }

    # HS-84-02: an adopted RuntimeProfile means the LLM leg runs on that
    # endpoint (openai_compatible), so the probe must test THAT — not the raw
    # config fields. Dangling/none ⇒ the configured backend, byte-identical.
    from .intel.providers import effective_dictation_llm

    effective = effective_dictation_llm(runtime)

    requested = getattr(runtime, "backend", "auto")
    if effective.node:
        # a meshNode assignment: the self-test is the node's liveness
        try:
            from .db import get_database

            last_seen = get_database().mesh_relay.worker_last_seen(effective.node)
        except Exception:
            last_seen = None
        if last_seen is None:
            return {"ok": False, "status": "unreachable", "backend": "mesh_relay",
                    "detail": f"Mesh node '{effective.node}' is offline (no worker has polled)."}
        from datetime import datetime

        age = (datetime.now() - last_seen).total_seconds()
        if age > 15:
            return {"ok": False, "status": "unreachable", "backend": "mesh_relay",
                    "detail": f"Mesh node '{effective.node}' is offline (last seen {int(age)}s ago)."}
        return {"ok": True, "status": "ok", "backend": "mesh_relay",
                "detail": f"Ready — mesh node '{effective.node}' is live (seen {int(age)}s ago)."}
    if effective.profile_id:
        resolved = "openai_compatible"
    else:
        try:
            resolved, _reason = runtime_module.resolve_backend(requested)
        except runtime_module.RuntimeUnavailableError as exc:
            return {"ok": False, "status": "unavailable", "backend": requested, "detail": str(exc)}

    if resolved in ("mlx", "llama_cpp"):
        path_attr = "mlx_model" if resolved == "mlx" else "llama_cpp_model_path"
        raw = str(getattr(runtime, path_attr, "") or "").strip()
        if not raw:
            return {"ok": False, "status": "unconfigured", "backend": resolved,
                    "detail": f"No model path set for backend '{resolved}'."}
        path = Path(raw).expanduser()
        if not path.exists():
            return {"ok": False, "status": "missing_model", "backend": resolved,
                    "detail": f"Model not found at {path}."}
        return {"ok": True, "status": "ok", "backend": resolved,
                "detail": f"Ready — {resolved} model at {path}."}

    if resolved == "openai_compatible":
        base = str(effective.base_url or "").strip().rstrip("/")
        if not base:
            return {"ok": False, "status": "unconfigured", "backend": resolved,
                    "detail": "No base URL set for the OpenAI-compatible endpoint."}
        key_env = str(effective.api_key_env or "OPENAI_API_KEY").strip()
        api_key = (os.environ.get(key_env) or "").strip()
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        getter = http_get or _default_http_get
        try:
            code = getter(f"{base}/models", headers=headers, timeout=timeout_seconds)
        except (URLError, OSError, ValueError) as exc:
            return {"ok": False, "status": "unreachable", "backend": resolved,
                    "detail": f"Could not reach {base}: {exc}"}
        if 200 <= int(code) < 300:
            return {"ok": True, "status": "ok", "backend": resolved,
                    "detail": f"Endpoint reachable ({base}, HTTP {code})."}
        return {"ok": False, "status": "error", "backend": resolved,
                "detail": f"Endpoint returned HTTP {code} for {base}/models."}

    return {"ok": True, "status": "ok", "backend": resolved, "detail": f"Backend '{resolved}' resolved."}


def runtime_choices() -> list[dict[str, Any]]:
    """Static reference for the four guided backend choices (HS-42-06 UI)."""
    return [
        {"id": "basic", "label": "Basic voice typing only", "backend": "none",
         "extra": None, "needs": "Nothing — Whisper transcription only.",
         "affects": "Dictation (no LLM rewrite)."},
        {"id": "mlx", "label": "Local Apple Silicon (MLX)", "backend": "mlx",
         "extra": "uv pip install -e '.[dictation-mlx]'", "needs": "An MLX model under ~/Models/mlx/…",
         "affects": "Dictation + meeting intel."},
        {"id": "llama_cpp", "label": "Local GGUF (llama.cpp)", "backend": "llama_cpp",
         "extra": "uv pip install -e '.[dictation-llama]'", "needs": "A GGUF model under ~/Models/gguf/…",
         "affects": "Dictation + meeting intel."},
        {"id": "openai_compatible", "label": "OpenAI-compatible endpoint", "backend": "openai_compatible",
         "extra": "uv pip install -e '.[dictation-openai]'", "needs": "A base URL (LAN, Ollama, vLLM, or hosted).",
         "affects": "Dictation + meeting intel."},
    ]
