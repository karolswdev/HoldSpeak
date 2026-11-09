# PARKED 2026-11-09 (door/speech-capture): the config-based local dictation chooser (plan.dictation_local_deployment_identity, the plan's frozen deployments) is gone: the engine door's assignment chain picks the engine at each call.
# Moved from tests/unit/test_speech_side_door_admission.py; its helpers are still there.

from tests.unit.test_speech_side_door_admission import *  # noqa: F401,F403


def test_local_construction_freezes_the_dictation_artifact_not_mutated_config(
    tmp_path, monkeypatch
) -> None:
    """A blank profile still freezes the dictation model, not the meeting dial."""
    from holdspeak.plugins.dictation.assembly import _try_build_runtime

    database = Database(tmp_path / "local-artifact.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)
    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router"]
    config.dictation.runtime.profile_id = ""
    config.dictation.runtime.backend = "llama_cpp"
    config.dictation.runtime.llama_cpp_model_path = "/frozen-dictation-model.gguf"
    config.meeting.intel_realtime_model = "/unrelated-meeting-model.gguf"
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))
    entry = SpeechEntry(
        admit_text_entry_session(
            principal=OWNER,
            insertion_aim=AIM_BROWSER_REHEARSE,
            config_snapshot=config,
            registry_snapshot=database,
        )
    )
    revision = entry.plan.deployment(entry.plan.primary(CAPABILITY_INTENT_CLASSIFY))
    assert revision.model_path == "/frozen-dictation-model.gguf"

    config.dictation.runtime.llama_cpp_model_path = "/retargeted-after-admission.gguf"
    seen: dict[str, Any] = {}

    class Runtime:
        backend = "llama_cpp"
        model_path = "/frozen-dictation-model.gguf"

    def factory(**kwargs: Any) -> Runtime:
        seen.update(kwargs)
        return Runtime()

    try:
        runtime, status, _detail = _try_build_runtime(
            config.dictation, factory, entry.provider
        )
    finally:
        entry.cancel()

    assert isinstance(runtime, Runtime)
    assert status == "loaded"
    assert seen["llama_cpp_model_path"] == "/frozen-dictation-model.gguf"


def test_local_identity_preserves_a_dotted_mlx_artifact_name() -> None:
    """The frozen engine, not a filename suffix guess, identifies an MLX model."""
    from holdspeak.speech_session.plan import dictation_local_deployment_identity

    artifact = "~/Models/mlx/Qwen3.5-8B-MLX-4bit"
    identity = dictation_local_deployment_identity(
        {
            "runtime_backend": "mlx",
            "runtime_mlx_model": artifact,
            "runtime_llama_cpp_model_path": "/unused.gguf",
        }
    )

    assert identity is not None
    assert identity.engine == "mlx"
    assert identity.model_path == artifact
    assert identity.model == "Qwen3.5-8B-MLX-4bit"


@pytest.mark.parametrize(
    ("system", "machine", "mlx_present", "expected_engine", "expected_artifact"),
    [
        pytest.param(
            "Darwin",
            "arm64",
            True,
            "mlx",
            "/frozen-auto-mlx",
            id="apple-mlx",
        ),
        pytest.param(
            "Darwin",
            "arm64",
            False,
            "llama_cpp",
            "/frozen-auto-llama.gguf",
            id="apple-import-failure-falls-back",
        ),
        pytest.param(
            "Linux",
            "x86_64",
            False,
            "llama_cpp",
            "/frozen-auto-llama.gguf",
            id="llama-fallback",
        ),
    ],
)
def test_auto_local_identity_freezes_one_deterministic_engine_and_artifact(
    system,
    machine,
    mlx_present,
    expected_engine,
    expected_artifact,
    monkeypatch,
) -> None:
    """`auto` is resolved once in the plan and construction cannot choose again."""
    import importlib
    import platform

    from holdspeak.speech_session.plan import dictation_local_deployment_identity

    monkeypatch.setattr(platform, "system", lambda: system)
    monkeypatch.setattr(platform, "machine", lambda: machine)

    real_import = importlib.import_module

    def import_optional(name, package=None):
        if name == "mlx_lm":
            if mlx_present:
                return object()
            raise ImportError("mlx_lm import failed")
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", import_optional)
    identity = dictation_local_deployment_identity(
        {
            "runtime_backend": "auto",
            "runtime_mlx_model": "/frozen-auto-mlx",
            "runtime_llama_cpp_model_path": "/frozen-auto-llama.gguf",
        }
    )

    assert identity is not None
    assert identity.engine == expected_engine
    assert identity.model_path == expected_artifact


# PARKED 2026-11-09 (door/speech-capture): revision_target.agrees (the frozen-target binding) is gone: the model call runs on the runner's engine for the revision the door picked.

def test_concrete_local_revision_rejects_a_different_loader_on_the_same_path() -> None:
    from holdspeak.speech_session.revision_target import agrees

    runtime = SimpleNamespace(backend="llama_cpp", model_path="/models/shared")
    revision = SimpleNamespace(
        engine="mlx", model_path="/models/shared", endpoint="", model="shared"
    )

    assert agrees(runtime, revision) is False
