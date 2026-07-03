"""Unit tests for the DIR-01 pluggable LLM runtime (HS-1-04)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.request import Request, urlopen

import pytest

from holdspeak.plugins.dictation.grammars import (
    BlockSet,
    BlockSpec,
    StructuredOutputSchema,
)
from holdspeak.plugins.dictation.runtime import (
    LLMRuntime,
    RuntimeUnavailableError,
    build_runtime,
    resolve_backend,
)


def _schema() -> StructuredOutputSchema:
    return StructuredOutputSchema.from_block_set(
        BlockSet(
            blocks=(
                BlockSpec(
                    id="ai_prompt_buildout",
                    extras_schema={"stage": ("buildout", "refinement")},
                ),
                BlockSpec(id="documentation_exercise"),
            )
        )
    )


# ---------------------------------------------------------------------------
# resolve_backend — auto-resolution matrix
# ---------------------------------------------------------------------------


def test_auto_prefers_mlx_on_arm64_when_importable():
    backend, reason = resolve_backend(
        "auto",
        on_arm64=lambda: True,
        mlx_importable=lambda: True,
        llama_cpp_importable=lambda: True,
    )
    assert backend == "mlx"
    assert "mlx" in reason


def test_auto_falls_back_to_llama_cpp_when_mlx_missing():
    backend, reason = resolve_backend(
        "auto",
        on_arm64=lambda: True,
        mlx_importable=lambda: False,
        llama_cpp_importable=lambda: True,
    )
    assert backend == "llama_cpp"
    assert "fallback" in reason


def test_auto_picks_llama_cpp_off_arm64():
    backend, _ = resolve_backend(
        "auto",
        on_arm64=lambda: False,
        mlx_importable=lambda: True,  # irrelevant off arm64
        llama_cpp_importable=lambda: True,
    )
    assert backend == "llama_cpp"


def test_auto_raises_when_no_backend_available():
    with pytest.raises(RuntimeUnavailableError, match="No dictation runtime"):
        resolve_backend(
            "auto",
            on_arm64=lambda: False,
            mlx_importable=lambda: False,
            llama_cpp_importable=lambda: False,
        )


def test_explicit_mlx_off_arm64_raises_with_remediation():
    with pytest.raises(RuntimeUnavailableError, match="darwin/arm64"):
        resolve_backend(
            "mlx",
            on_arm64=lambda: False,
            mlx_importable=lambda: True,
            llama_cpp_importable=lambda: True,
        )


def test_explicit_mlx_without_mlx_lm_raises():
    with pytest.raises(RuntimeUnavailableError, match="mlx-lm"):
        resolve_backend(
            "mlx",
            on_arm64=lambda: True,
            mlx_importable=lambda: False,
        )


def test_explicit_llama_cpp_without_lib_raises():
    with pytest.raises(RuntimeUnavailableError, match="llama-cpp-python"):
        resolve_backend(
            "llama_cpp",
            llama_cpp_importable=lambda: False,
        )


def test_explicit_openai_compatible_without_lib_raises():
    with pytest.raises(RuntimeUnavailableError, match="openai"):
        resolve_backend(
            "openai_compatible",
            openai_importable=lambda: False,
        )


def test_explicit_openai_compatible_resolves_when_client_available():
    backend, reason = resolve_backend(
        "openai_compatible",
        openai_importable=lambda: True,
    )
    assert backend == "openai_compatible"
    assert reason == "explicit"


def test_explicit_backends_never_fall_back():
    """If the user pins mlx and it's unavailable, do not silently use llama_cpp."""
    with pytest.raises(RuntimeUnavailableError):
        resolve_backend(
            "mlx",
            on_arm64=lambda: True,
            mlx_importable=lambda: False,
            llama_cpp_importable=lambda: True,  # available, but should be ignored
        )


def test_unknown_backend_rejected():
    with pytest.raises(RuntimeUnavailableError, match="Unknown"):
        resolve_backend("totally_made_up")


# ---------------------------------------------------------------------------
# build_runtime — factory wiring with mocked backends
# ---------------------------------------------------------------------------


class _FakeRuntime:
    def __init__(self, *, backend: str, **kwargs: Any) -> None:
        self.backend = backend
        self.kwargs = kwargs
        self.loaded = False

    def load(self) -> None:
        self.loaded = True

    def info(self) -> dict[str, Any]:
        return {"backend": self.backend, **self.kwargs}

    def classify(
        self,
        prompt: str,
        schema: StructuredOutputSchema,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        # Echo a structurally-valid response so callers can assert shape.
        bid = schema.block_ids[0]
        return {
            "matched": True,
            "block_id": bid,
            "confidence": 0.9,
            "extras": {},
        }


def _factories() -> dict[str, Any]:
    return {
        "mlx": lambda **kw: _FakeRuntime(backend="mlx", **kw),
        "llama_cpp": lambda **kw: _FakeRuntime(backend="llama_cpp", **kw),
        "openai_compatible": lambda **kw: _FakeRuntime(backend="openai_compatible", **kw),
    }


def test_build_runtime_returns_llmruntime_protocol_conformant_object():
    rt = build_runtime(
        backend="llama_cpp",
        llama_cpp_importable=lambda: True,
        factories=_factories(),
    )
    assert isinstance(rt, LLMRuntime)
    assert rt.backend == "llama_cpp"


def test_build_runtime_passes_mlx_kwargs():
    rt = build_runtime(
        backend="mlx",
        mlx_model="~/Models/mlx/CUSTOM",
        warm_on_start=True,
        on_arm64=lambda: True,
        mlx_importable=lambda: True,
        factories=_factories(),
    )
    assert rt.kwargs["model"] == "~/Models/mlx/CUSTOM"
    assert rt.kwargs["warm_on_start"] is True


def test_build_runtime_passes_llama_kwargs():
    rt = build_runtime(
        backend="llama_cpp",
        llama_cpp_model_path="/tmp/x.gguf",
        n_ctx=4096,
        n_gpu_layers=20,
        llama_cpp_importable=lambda: True,
        factories=_factories(),
    )
    assert rt.kwargs["model_path"] == "/tmp/x.gguf"
    assert rt.kwargs["n_ctx"] == 4096
    assert rt.kwargs["n_gpu_layers"] == 20


def test_build_runtime_passes_openai_compatible_kwargs():
    rt = build_runtime(
        backend="openai_compatible",
        openai_compatible_model="qwen-local",
        openai_compatible_base_url="http://127.0.0.1:1234/v1",
        openai_compatible_api_key_env="LOCAL_LLM_KEY",
        openai_compatible_timeout_seconds=3.5,
        openai_importable=lambda: True,
        factories=_factories(),
    )
    assert rt.backend == "openai_compatible"
    assert rt.kwargs["model"] == "qwen-local"
    assert rt.kwargs["base_url"] == "http://127.0.0.1:1234/v1"
    assert rt.kwargs["api_key_env"] == "LOCAL_LLM_KEY"
    assert rt.kwargs["timeout_seconds"] == 3.5


# ---------------------------------------------------------------------------
# OpenAICompatibleRuntime — classify round-trip with a mocked client
# ---------------------------------------------------------------------------


class _FakeOpenAICompletions:
    def __init__(self, payload: dict[str, Any] | str) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        content = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
        return {
            "choices": [
                {
                    "message": {
                        "content": content,
                    }
                }
            ]
        }


class _FakeOpenAIClient:
    def __init__(self, *, payload: dict[str, Any], **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.completions = _FakeOpenAICompletions(payload)
        self.chat = type("_Chat", (), {"completions": self.completions})()


class _FakeBadRequestError(Exception):
    pass


class _TimeoutCompletions:
    def create(self, **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        raise TimeoutError("fake endpoint timeout")


class _TimeoutClient:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.chat = type("_Chat", (), {"completions": _TimeoutCompletions()})()


class _ResponseFormatRejectingCompletions:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if "response_format" in kwargs:
            raise _FakeBadRequestError("unsupported response_format")
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(self.payload),
                    }
                }
            ]
        }


def test_openai_compatible_runtime_classify_returns_parsed_json():
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    fake_client: _FakeOpenAIClient | None = None

    def client_factory(**kwargs: Any) -> _FakeOpenAIClient:
        nonlocal fake_client
        fake_client = _FakeOpenAIClient(
            payload={
                "matched": True,
                "block_id": "ai_prompt_buildout",
                "confidence": 0.91,
                "extras": {"stage": "buildout"},
            },
            **kwargs,
        )
        return fake_client

    rt = OpenAICompatibleRuntime(
        model="qwen-local",
        base_url="http://127.0.0.1:1234/v1",
        api_key_env="",
        client_factory=client_factory,
    )
    result = rt.classify("classify this", _schema())
    assert result["block_id"] == "ai_prompt_buildout"
    assert result["extras"] == {"stage": "buildout"}
    assert fake_client is not None
    assert fake_client.kwargs["base_url"] == "http://127.0.0.1:1234/v1"
    call = fake_client.completions.calls[0]
    assert call["model"] == "qwen-local"
    assert call["response_format"] == {"type": "json_object"}


def test_openai_compatible_runtime_rejects_out_of_schema_output():
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    def client_factory(**kwargs: Any) -> _FakeOpenAIClient:
        _ = kwargs
        return _FakeOpenAIClient(
            payload={
                "matched": True,
                "block_id": "not_a_real_block",
                "confidence": 0.91,
                "extras": {},
            }
        )

    rt = OpenAICompatibleRuntime(
        model="qwen-local",
        base_url="http://127.0.0.1:1234/v1",
        api_key_env="",
        client_factory=client_factory,
    )
    with pytest.raises(RuntimeError, match="block_id"):
        rt.classify("classify this", _schema())


def test_openai_compatible_runtime_rejects_malformed_json_response():
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    def client_factory(**kwargs: Any) -> _FakeOpenAIClient:
        _ = kwargs
        return _FakeOpenAIClient(payload="this is not json")

    rt = OpenAICompatibleRuntime(
        model="qwen-local",
        base_url="http://127.0.0.1:1234/v1",
        api_key_env="",
        client_factory=client_factory,
    )

    with pytest.raises(json.JSONDecodeError):
        rt.classify("classify this", _schema())


def test_openai_compatible_runtime_retries_when_response_format_rejected():
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    completions = _ResponseFormatRejectingCompletions(
        {
            "matched": True,
            "block_id": "ai_prompt_buildout",
            "confidence": 0.91,
            "extras": {"stage": "buildout"},
        }
    )

    class _Client:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            self.chat = type("_Chat", (), {"completions": completions})()

    rt = OpenAICompatibleRuntime(
        model="qwen-local",
        base_url="http://127.0.0.1:1234/v1",
        api_key_env="",
        client_factory=_Client,
    )

    result = rt.classify("classify this", _schema())

    assert result["block_id"] == "ai_prompt_buildout"
    assert len(completions.calls) == 2
    assert "response_format" in completions.calls[0]
    assert "response_format" not in completions.calls[1]


def test_openai_compatible_runtime_rewrite_returns_message_text():
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    fake_client: _FakeOpenAIClient | None = None

    def client_factory(**kwargs: Any) -> _FakeOpenAIClient:
        nonlocal fake_client
        fake_client = _FakeOpenAIClient(payload="Rewrite this as a Codex task.", **kwargs)
        return fake_client

    rt = OpenAICompatibleRuntime(
        model="qwen-local",
        base_url="http://127.0.0.1:1234/v1",
        api_key_env="",
        client_factory=client_factory,
    )

    result = rt.rewrite("rewrite this")

    assert result == "Rewrite this as a Codex task."
    assert fake_client is not None
    call = fake_client.completions.calls[0]
    assert call["model"] == "qwen-local"
    assert "response_format" not in call


def test_openai_compatible_runtime_rewrite_wraps_timeout():
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    rt = OpenAICompatibleRuntime(
        model="qwen-local",
        base_url="http://127.0.0.1:1234/v1",
        api_key_env="",
        client_factory=_TimeoutClient,
    )

    with pytest.raises(RuntimeError, match="timeout"):
        rt.rewrite("rewrite this")


def test_openai_compatible_runtime_classify_against_fake_chat_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.plugins.dictation.runtime_openai_compatible import (
        OpenAICompatibleRuntime,
    )

    seen: list[dict[str, Any]] = []

    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
            raw = self.rfile.read(int(self.headers.get("content-length") or "0"))
            seen.append(
                {
                    "path": self.path,
                    "authorization": self.headers.get("authorization"),
                    "body": json.loads(raw.decode("utf-8")),
                }
            )
            content = json.dumps(
                {
                    "matched": True,
                    "block_id": "ai_prompt_buildout",
                    "confidence": 0.94,
                    "extras": {"stage": "refinement"},
                }
            )
            payload = json.dumps({"choices": [{"message": {"content": content}}]}).encode(
                "utf-8"
            )
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt: str, *args: Any) -> None:
            _ = (fmt, args)

    class _HttpCompletions:
        def __init__(self, *, base_url: str, api_key: str, timeout: float) -> None:
            self.base_url = base_url.rstrip("/")
            self.api_key = api_key
            self.timeout = timeout

        def create(self, **kwargs: Any) -> dict[str, Any]:
            request = Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(kwargs).encode("utf-8"),
                headers={
                    "content-type": "application/json",
                    "authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310 - localhost test server
                return json.loads(response.read().decode("utf-8"))

    class _HttpClient:
        def __init__(self, **kwargs: Any) -> None:
            self.chat = type(
                "_Chat",
                (),
                {
                    "completions": _HttpCompletions(
                        base_url=kwargs["base_url"],
                        api_key=kwargs["api_key"],
                        timeout=kwargs["timeout"],
                    )
                },
            )()

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("LOCAL_LLM_KEY", "test-key")
    try:
        rt = OpenAICompatibleRuntime(
            model="qwen-local",
            base_url=f"http://127.0.0.1:{server.server_port}/v1",
            api_key_env="LOCAL_LLM_KEY",
            timeout_seconds=2,
            client_factory=_HttpClient,
        )

        result = rt.classify("classify this", _schema())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result["block_id"] == "ai_prompt_buildout"
    assert result["extras"] == {"stage": "refinement"}
    assert seen[0]["path"] == "/v1/chat/completions"
    assert seen[0]["authorization"] == "Bearer test-key"
    assert seen[0]["body"]["model"] == "qwen-local"
    assert seen[0]["body"]["response_format"] == {"type": "json_object"}


# ---------------------------------------------------------------------------
# LlamaCppRuntime — classify round-trip with a mocked Llama
# ---------------------------------------------------------------------------


class _FakeLlamaGrammar:
    def __init__(self, src: str) -> None:
        self.src = src

    @classmethod
    def from_string(cls, src: str) -> "_FakeLlamaGrammar":
        return cls(src)


class _FakeLlama:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.calls: list[dict[str, Any]] = []
        self.next_text = json.dumps(
            {
                "matched": True,
                "block_id": "ai_prompt_buildout",
                "confidence": 0.87,
                "extras": {"stage": "buildout"},
            }
        )

    def create_completion(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"choices": [{"text": self.next_text}]}


def test_llama_cpp_runtime_classify_returns_parsed_json(tmp_path):
    from holdspeak.plugins.dictation.runtime_llama_cpp import LlamaCppRuntime

    model_file = tmp_path / "fake.gguf"
    model_file.write_bytes(b"\x00")

    fake_llama: _FakeLlama | None = None

    def llama_factory(**kwargs: Any) -> _FakeLlama:
        nonlocal fake_llama
        fake_llama = _FakeLlama(**kwargs)
        return fake_llama

    rt = LlamaCppRuntime(
        model_path=str(model_file),
        llama_factory=llama_factory,
    )
    rt._gbnf_factory = _FakeLlamaGrammar  # type: ignore[assignment]

    result = rt.classify("classify this", _schema())
    assert result["matched"] is True
    assert result["block_id"] == "ai_prompt_buildout"
    assert fake_llama is not None
    # GBNF was passed.
    call = fake_llama.calls[0]
    assert isinstance(call["grammar"], _FakeLlamaGrammar)
    assert "matched" in call["grammar"].src


def test_llama_cpp_runtime_missing_model_raises():
    from holdspeak.plugins.dictation.runtime_llama_cpp import LlamaCppRuntime

    rt = LlamaCppRuntime(
        model_path="/nonexistent/path/to/model.gguf",
        llama_factory=_FakeLlama,
    )
    rt._gbnf_factory = _FakeLlamaGrammar  # type: ignore[assignment]

    with pytest.raises(RuntimeUnavailableError, match="not found"):
        rt.load()


def test_llama_cpp_runtime_rewrite_returns_completion_text(tmp_path):
    from holdspeak.plugins.dictation.runtime_llama_cpp import LlamaCppRuntime

    model_file = tmp_path / "fake.gguf"
    model_file.write_bytes(b"\x00")
    llama = _FakeLlama()
    llama.next_text = "Rewrite this as a clean task."

    rt = LlamaCppRuntime(
        model_path=str(model_file),
        llama_factory=lambda **_kwargs: llama,
    )
    rt._gbnf_factory = _FakeLlamaGrammar  # type: ignore[assignment]

    result = rt.rewrite("rewrite this")

    assert result == "Rewrite this as a clean task."
    assert "grammar" not in llama.calls[0]


def test_llama_cpp_runtime_info_reports_backend():
    from holdspeak.plugins.dictation.runtime_llama_cpp import LlamaCppRuntime

    rt = LlamaCppRuntime(
        model_path="/tmp/whatever.gguf",
        llama_factory=_FakeLlama,
    )
    info = rt.info()
    assert info["backend"] == "llama_cpp"
    assert info["loaded"] is False


# ---------------------------------------------------------------------------
# MlxRuntime — classify round-trip with mocked load/generate/processor
# ---------------------------------------------------------------------------


def _make_generator_factory(payload: dict[str, Any], captured: dict[str, Any] | None = None):
    """Test helper: builds a `generator_factory` that returns a fixed JSON payload.

    Mirrors the production seam shape:
    `generator_factory(model, tokenizer, schema_dict) -> callable(prompt, max_tokens) -> str`.
    """
    def _factory(model: Any, tokenizer: Any, schema_dict: dict[str, Any]) -> Any:
        if captured is not None:
            captured["schema_dict"] = schema_dict
            captured["model"] = model
            captured["tokenizer"] = tokenizer

        def _generate(prompt: str, *, max_tokens: int = 128) -> str:
            if captured is not None:
                captured["prompt"] = prompt
                captured["max_tokens"] = max_tokens
            return json.dumps(payload)

        return _generate

    return _factory


def test_mlx_runtime_classify_returns_parsed_json():
    from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

    captured: dict[str, Any] = {}

    def fake_load(model_id: str) -> tuple[str, str]:
        captured["loaded"] = model_id
        return ("model-obj", "tokenizer-obj")

    rt = MlxRuntime(
        model="hf-repo/qwen-mlx",  # not a path; should not require existence
        load_fn=fake_load,
        generator_factory=_make_generator_factory(
            {
                "matched": True,
                "block_id": "documentation_exercise",
                "confidence": 0.55,
                "extras": {},
            },
            captured,
        ),
    )

    result = rt.classify("hi", _schema())
    assert result["block_id"] == "documentation_exercise"
    assert captured["loaded"] == "hf-repo/qwen-mlx"
    assert captured["model"] == "model-obj"
    assert captured["tokenizer"] == "tokenizer-obj"
    # The schema dict the generator received is the one to_outlines emits.
    assert "oneOf" in captured["schema_dict"]
    assert any("block_id" in branch.get("properties", {}) for branch in captured["schema_dict"]["oneOf"])


def test_mlx_runtime_missing_path_raises():
    from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

    rt = MlxRuntime(
        model="~/Models/mlx/does-not-exist",
        load_fn=lambda _: ("m", "t"),
        generator_factory=_make_generator_factory({"matched": False, "confidence": 0.0}),
    )
    with pytest.raises(RuntimeUnavailableError, match="not found"):
        rt.load()


def test_mlx_runtime_info_reports_backend():
    from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

    rt = MlxRuntime(
        model="hf-repo/qwen",
        load_fn=lambda _: ("m", "t"),
        generator_factory=_make_generator_factory({"matched": False, "confidence": 0.0}),
    )
    info = rt.info()
    assert info["backend"] == "mlx"
    assert info["loaded"] is False


# ---------------------------------------------------------------------------
# Cross-backend contract: same prompt → outputs from the same value set
# ---------------------------------------------------------------------------


def test_both_backends_produce_outputs_in_schema_value_set():
    """Both runtimes (mocked at the model level, real at the schema-compiler
    level) MUST produce outputs whose block_id is in the taxonomy and whose
    extras keys conform to the per-block schema."""
    from holdspeak.plugins.dictation.runtime_llama_cpp import LlamaCppRuntime
    from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

    schema = _schema()

    # llama_cpp side.
    llama = _FakeLlama()
    llama.next_text = json.dumps(
        {
            "matched": True,
            "block_id": "ai_prompt_buildout",
            "confidence": 0.7,
            "extras": {"stage": "refinement"},
        }
    )
    rt_llama = LlamaCppRuntime(
        model_path="/tmp/x.gguf",
        llama_factory=lambda **kw: llama,
    )
    rt_llama._gbnf_factory = _FakeLlamaGrammar  # type: ignore[assignment]
    # Touch _llm so load() does not check the path.
    rt_llama._llm = llama

    out_llama = rt_llama.classify("p", schema)

    # mlx side.
    rt_mlx = MlxRuntime(
        model="hf-repo/qwen",
        load_fn=lambda _: ("m", "t"),
        generator_factory=_make_generator_factory(
            {
                "matched": True,
                "block_id": "ai_prompt_buildout",
                "confidence": 0.6,
                "extras": {"stage": "buildout"},
            }
        ),
    )

    out_mlx = rt_mlx.classify("p", schema)

    for out in (out_llama, out_mlx):
        assert out["block_id"] in schema.block_ids
        for k, v in out["extras"].items():
            assert v in schema.extras_per_block[out["block_id"]][k]


# ---------------------------------------------------------------------------
# DIR-C-001: defaults keep DIR-01 fully off
# ---------------------------------------------------------------------------


def test_default_dictation_pipeline_disabled():
    from holdspeak.config import DictationConfig

    cfg = DictationConfig()
    assert cfg.pipeline.enabled is False
    assert cfg.runtime.backend == "auto"


# ---------------------------------------------------------------------------
# _validate_output / _schema_hint — the classify output contract
# ---------------------------------------------------------------------------


def test_validate_output_unwraps_extras_nested_under_block_id():
    """A faithful model mirrors the per-block reference table back
    (``extras: {"<block_id>": {...}}``). That shape validates now — the exact
    0/5 failure a live Qwythos-9B run produced against the flat-only validator."""
    from holdspeak.plugins.dictation.runtime_openai_compatible import _validate_output

    data = {
        "matched": True,
        "block_id": "ai_prompt_buildout",
        "confidence": 0.9,
        "extras": {"ai_prompt_buildout": {"stage": "buildout"}},
    }
    out = _validate_output(data, _schema())
    assert out["extras"] == {"stage": "buildout"}   # unwrapped, flat


def test_validate_output_flat_extras_unchanged_and_bad_keys_still_reject():
    from holdspeak.plugins.dictation.runtime_openai_compatible import _validate_output

    flat = {
        "matched": True,
        "block_id": "ai_prompt_buildout",
        "confidence": 0.5,
        "extras": {"stage": "refinement"},
    }
    assert _validate_output(flat, _schema())["extras"] == {"stage": "refinement"}

    # A nested key that is NOT the chosen block id is still an honest rejection.
    wrong = dict(flat, extras={"documentation_exercise": {"stage": "buildout"}})
    with pytest.raises(RuntimeError, match="not allowed"):
        _validate_output(wrong, _schema())


def test_schema_hint_names_the_flat_extras_shape():
    """The hint's ONLY example of extras used to be the nested per-block table —
    the ambiguity that taught models the wrong shape. It now states the flat
    output contract explicitly."""
    from holdspeak.plugins.dictation.runtime_openai_compatible import _schema_hint

    hint = json.loads(_schema_hint(_schema()))
    assert "FLAT" in hint["extras"]
    assert "ai_prompt_buildout" in hint["extras_allowed_per_block"]


def test_validate_output_accepts_the_honest_no_match():
    """An unconstrained model expresses "none of these blocks" as matched=false
    with a null block_id (the grammar runtimes are forced to name one anyway).
    The router's normalizer accepts that shape; the runtime validator now does
    too, instead of turning honesty into a classify failure."""
    from holdspeak.plugins.dictation.runtime_openai_compatible import _validate_output

    out = _validate_output(
        {"matched": False, "block_id": None, "confidence": 0.2, "extras": {}},
        _schema(),
    )
    assert out == {"matched": False, "block_id": None, "confidence": 0.0, "extras": {}}

    # matched=true with a null/unknown block stays an honest rejection.
    with pytest.raises(RuntimeError, match="not in allowed set"):
        _validate_output(
            {"matched": True, "block_id": None, "confidence": 0.9, "extras": {}},
            _schema(),
        )
