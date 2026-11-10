# PARKED 2026-11-09 (door/speech-capture): the classify stage runs on the runner's engine for the revision the door picked (provider._DoorSpeechAdapter); the pipeline runtime's own response_format leg is no longer called.
# Moved from tests/unit/test_one_path_cardinality.py; its helpers are still there.

from tests.unit.test_one_path_cardinality import *  # noqa: F401,F403


def test_dictation_response_format_rejection_is_one_attempt_until_routed(
    tmp_path, monkeypatch
):
    """Scenario: retry/fallback. Surface: dictation pipeline.

    Each attempt (the rejected ``response_format`` leg, then the compatibility
    retry) is a SEPARATE ``inference.invoke`` child with its own attempt
    ordinal, receipt, and physical dispatch -- never one logical retry hiding
    inside a single admitted child.
    """
    import json

    from holdspeak.config import Config
    from holdspeak.plugins.dictation.grammars import StructuredOutputSchema
    from holdspeak.plugins.dictation.runtime_openai_compatible import OpenAICompatibleRuntime
    from holdspeak.speech_session import AdmittedDictationRuntime, SpeechProviderFailure, admit_hold_session

    db = Database(tmp_path / "dictation-cardinality.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    db.profiles.upsert(
        profile_id="prof_cardinality", name="prof_cardinality", kind="openAICompatible",
        base_url="http://127.0.0.1:1234/v1", model="qwen-local",
    )
    broker = _configure(db)
    monkeypatch.setattr(
        "holdspeak.intel.providers._configured_engine", lambda: object()
    )
    counts = _instrument(broker.inference_runner)

    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router", "project-rewriter"]
    config.dictation.runtime.profile_id = "prof_cardinality"
    session = admit_hold_session(config_snapshot=config)

    leaf = _Leaf()

    class _RejectingCompletions:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def create(self, **kwargs: Any) -> dict[str, Any]:
            leaf.hit()
            self.calls.append(kwargs)
            if "response_format" in kwargs:
                raise _BadRequest("unsupported response_format")
            return {
                "choices": [{"message": {"content": json.dumps(
                    {"matched": True, "block_id": "ai_prompt_buildout", "confidence": 0.8, "extras": {}}
                )}}]
            }

    class _BadRequest(Exception):
        __name__ = "BadRequestError"

    completions = _RejectingCompletions()

    class _Client:
        def __init__(self, **kwargs: Any) -> None:
            self.chat = type("_Chat", (), {"completions": completions})()

    backend = OpenAICompatibleRuntime(
        model="qwen-local", base_url="http://127.0.0.1:1234/v1", api_key_env="", client_factory=_Client,
    )
    schema = StructuredOutputSchema(
        block_ids=("ai_prompt_buildout",), extras_per_block={"ai_prompt_buildout": {}},
    )
    runtime = AdmittedDictationRuntime(backend, session.provider())

    with pytest.raises(SpeechProviderFailure):
        runtime.classify("CARDINALITY_RETRY_PROBE", schema, max_tokens=64, temperature=0.0)

    assert len(completions.calls) == 1

    children = _assert_reconciled(
        db, parent_operation_id=session.operation_id, counts=counts, leaf=leaf,
        expect_children=1,
    )
    outcomes = [_receipt(db, row["operation_id"])["outcome"] for row in children]
    assert outcomes == ["failed"]
    assert [row["parent_operation_id"] for row in children] == [session.operation_id]
    assert counts == {"engine_factory": 1, "dispatch": 1}
