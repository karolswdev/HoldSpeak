"""HS-42-06: the runtime model-assistant self-test (no real network / no model load)."""
from __future__ import annotations

from types import SimpleNamespace


from holdspeak.setup_runtime import probe_runtime, runtime_choices


def _cfg(*, enabled=True, backend="llama_cpp", **runtime_kw) -> SimpleNamespace:
    runtime = SimpleNamespace(
        backend=backend,
        mlx_model=runtime_kw.get("mlx_model", ""),
        llama_cpp_model_path=runtime_kw.get("llama_cpp_model_path", ""),
        openai_compatible_base_url=runtime_kw.get("openai_compatible_base_url", ""),
        openai_compatible_api_key_env=runtime_kw.get("openai_compatible_api_key_env", "OPENAI_API_KEY"),
    )
    return SimpleNamespace(pipeline=SimpleNamespace(enabled=enabled), runtime=runtime)


def _resolve(monkeypatch, resolved: str) -> None:
    from holdspeak.plugins.dictation import runtime as runtime_module

    monkeypatch.setattr(runtime_module, "resolve_backend", lambda req, **_: (resolved, "stub"))


def test_basic_when_pipeline_disabled() -> None:
    res = probe_runtime(_cfg(enabled=False))
    assert res["ok"] is True and res["status"] == "basic"


def test_local_backend_missing_model(monkeypatch) -> None:
    _resolve(monkeypatch, "llama_cpp")
    res = probe_runtime(_cfg(backend="llama_cpp", llama_cpp_model_path="/no/such/model.gguf"))
    assert res["ok"] is False and res["status"] == "missing_model"


def test_local_backend_ready(monkeypatch, tmp_path) -> None:
    _resolve(monkeypatch, "llama_cpp")
    model = tmp_path / "m.gguf"
    model.write_text("x")
    res = probe_runtime(_cfg(backend="llama_cpp", llama_cpp_model_path=str(model)))
    assert res["ok"] is True and res["status"] == "ok"


def test_local_backend_unavailable(monkeypatch) -> None:
    from holdspeak.plugins.dictation import runtime as runtime_module

    def _raise(req, **_):
        raise runtime_module.RuntimeUnavailableError("mlx requires darwin/arm64")

    monkeypatch.setattr(runtime_module, "resolve_backend", _raise)
    res = probe_runtime(_cfg(backend="mlx"))
    assert res["ok"] is False and res["status"] == "unavailable"


def test_openai_endpoint_reachable(monkeypatch) -> None:
    _resolve(monkeypatch, "openai_compatible")
    calls = {}

    def _get(url, *, headers, timeout):
        calls["url"] = url
        return 200

    res = probe_runtime(
        _cfg(backend="openai_compatible", openai_compatible_base_url="http://lan:8000/v1"),
        http_get=_get,
    )
    assert res["ok"] is True and res["status"] == "ok"
    assert calls["url"] == "http://lan:8000/v1/models"


def test_openai_endpoint_unreachable(monkeypatch) -> None:
    _resolve(monkeypatch, "openai_compatible")

    def _boom(url, *, headers, timeout):
        raise OSError("connection refused")

    res = probe_runtime(
        _cfg(backend="openai_compatible", openai_compatible_base_url="http://lan:8000/v1"),
        http_get=_boom,
    )
    assert res["ok"] is False and res["status"] == "unreachable"


def test_openai_endpoint_unconfigured(monkeypatch) -> None:
    _resolve(monkeypatch, "openai_compatible")
    res = probe_runtime(_cfg(backend="openai_compatible", openai_compatible_base_url=""))
    assert res["ok"] is False and res["status"] == "unconfigured"


def test_runtime_choices_cover_the_four_paths() -> None:
    ids = {c["id"] for c in runtime_choices()}
    assert ids == {"basic", "mlx", "llama_cpp", "openai_compatible"}
