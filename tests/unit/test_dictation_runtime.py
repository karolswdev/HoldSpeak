"""Unit tests for the DIR-01 pluggable LLM runtime (HS-1-04)."""

from __future__ import annotations

import json
from typing import Any

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


class _FakeProcessor:
    def __init__(self, schema: str, *, tokenizer: Any) -> None:
        self.schema = schema
        self.tokenizer = tokenizer


def test_mlx_runtime_classify_returns_parsed_json():
    from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

    captured: dict[str, Any] = {}

    def fake_load(model_id: str) -> tuple[str, str]:
        captured["loaded"] = model_id
        return ("model-obj", "tokenizer-obj")

    def fake_generate(model: Any, tokenizer: Any, **kwargs: Any) -> str:
        captured["generate_kwargs"] = kwargs
        return json.dumps(
            {
                "matched": True,
                "block_id": "documentation_exercise",
                "confidence": 0.55,
                "extras": {},
            }
        )

    rt = MlxRuntime(
        model="hf-repo/qwen-mlx",  # not a path; should not require existence
        load_fn=fake_load,
        generate_fn=fake_generate,
        processor_factory=_FakeProcessor,
    )

    result = rt.classify("hi", _schema())
    assert result["block_id"] == "documentation_exercise"
    assert captured["loaded"] == "hf-repo/qwen-mlx"
    processors = captured["generate_kwargs"]["logits_processors"]
    assert isinstance(processors[0], _FakeProcessor)
    # The schema string is JSON-parseable.
    json.loads(processors[0].schema)


def test_mlx_runtime_missing_path_raises():
    from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

    rt = MlxRuntime(
        model="~/Models/mlx/does-not-exist",
        load_fn=lambda _: ("m", "t"),
        generate_fn=lambda *a, **k: "",
        processor_factory=_FakeProcessor,
    )
    with pytest.raises(RuntimeUnavailableError, match="not found"):
        rt.load()


def test_mlx_runtime_info_reports_backend():
    from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime

    rt = MlxRuntime(
        model="hf-repo/qwen",
        load_fn=lambda _: ("m", "t"),
        generate_fn=lambda *a, **k: "",
        processor_factory=_FakeProcessor,
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
        generate_fn=lambda *a, **k: json.dumps(
            {
                "matched": True,
                "block_id": "ai_prompt_buildout",
                "confidence": 0.6,
                "extras": {"stage": "buildout"},
            }
        ),
        processor_factory=_FakeProcessor,
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
