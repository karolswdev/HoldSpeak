# PARKED 2026-11-09 (door/speech-capture): the config-based dictation engine chooser (plan.dictation_local_deployment_identity) is gone: the engine door's assignment chain picks the engine.
# Moved from tests/unit/test_finish_defaults.py; its helpers are still there.

from tests.unit.test_finish_defaults import *  # noqa: F401,F403


def test_auto_plans_llama_cpp_when_no_mlx_model_is_set(mlx_installed) -> None:
    from holdspeak.config import Config
    from holdspeak.speech_session.plan import _pipeline_terms, dictation_local_deployment_identity

    terms = _pipeline_terms(Config())
    identity = dictation_local_deployment_identity(terms)
    assert identity is not None, "a blank MLX model must not leave dictation without an artifact"
    assert identity.engine == "llama_cpp"
    assert identity.model_path.endswith("Qwen3.5-4B-Q4_K_M.gguf")


def test_auto_still_plans_mlx_when_the_owner_names_a_model(mlx_installed) -> None:
    from holdspeak.config import Config
    from holdspeak.speech_session.plan import _pipeline_terms, dictation_local_deployment_identity

    config = Config()
    config.dictation.runtime.mlx_model = "~/Models/mlx/Some-Model-4bit"
    identity = dictation_local_deployment_identity(_pipeline_terms(config))
    assert identity is not None and identity.engine == "mlx"
    assert identity.model == "Some-Model-4bit"
