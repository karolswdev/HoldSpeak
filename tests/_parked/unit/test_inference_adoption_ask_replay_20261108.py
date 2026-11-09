"""Parked 2026-11-08: an answer no longer runs through the routed controller
(it runs through the engine door, ``tests/unit/test_ask_engine_door.py``), so
the controller's crash replay is not Ask's. Kept as written; not collected.
From ``tests/unit/test_inference_adoption.py``."""
# ruff: noqa
def test_terminal_routed_ask_replay_stages_once_after_pre_stage_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from holdspeak.services.ask_service import AskService

    db_path = tmp_path / "routed-ask-replay.db"
    db = Database(db_path)
    _profile(db, "thought-v2", claims=("language", _result_claim("thought.interview")))
    _profile(db, "writing-v2", claims=("language", _result_claim("speech.intent_classify")))
    broker = _configure(db)
    broker.inference_adoption_service.migrate_legacy_config(
        OWNER,
        SimpleNamespace(
            thoughts=SimpleNamespace(inference_target_id="thought-v2"),
            dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="writing-v2")),
        ),
    )

    class Engine:
        active_provider = "fixture"
        active_model = "routed-model"

        @staticmethod
        def run_prompt(**_kwargs: Any) -> str:
            return "replayed answer"

    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: Engine()
    monkeypatch.setattr(
        broker.projection_stager,
        "stage",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("pre-stage crash")),
    )
    with pytest.raises(RuntimeError, match="pre-stage crash"):
        asyncio.run(
            AskService(db, broker=broker).ask(
                OWNER, "Recover this Ask", invocation_id="ask_replay_crash"
            )
        )
    with db._connection() as conn:
        execution = conn.execute(
            "SELECT id,terminal_outcome FROM inference_route_executions"
        ).fetchone()
        assert execution["terminal_outcome"] == "succeeded"
        assert conn.execute("SELECT COUNT(*) FROM kernel_projection_stages").fetchone()[0] == 0

    fresh_db = Database(db_path)
    fresh_broker = _configure(fresh_db)
    fresh_broker.inference_runner._engine_factory = lambda _revision, **_kwargs: Engine()
    result = asyncio.run(
        AskService(fresh_db, broker=fresh_broker).ask(
            OWNER, "Recover this Ask", invocation_id="ask_replay_crash"
        )
    )
    assert result["output"] == "replayed answer"
    with fresh_db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_projection_stages").fetchone()[0] == 1

    calls: list[object] = []
    replay = fresh_broker.inference_adoption_service.execute(
        OWNER,
        execution_id=str(execution["id"]),
        adapter=_AskAnswerAdapter(CanonicalPromptAdapter()),
        publish=lambda output, reservation: calls.append((output, reservation)) or "never",
    )
    assert replay["outcome"] == "succeeded"
    assert calls == []


