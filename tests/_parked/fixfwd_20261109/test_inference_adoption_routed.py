# PARKED 2026-11-09 (fix forward #2121): the Thought and the dictation stages run through the engine door; the routed admission (route plans, route executions, controller winners, frozen session routes) these pinned is gone.
# Moved from tests/unit/test_inference_adoption.py; its helpers are still there.

from tests.unit.test_inference_adoption import *  # noqa: F401,F403


def test_speech_rewrite_uses_session_frozen_route_and_controller_child(
    tmp_path: Path,
) -> None:
    from holdspeak.services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
    from holdspeak.speech_session.plan import CAPABILITY_REWRITE
    from holdspeak.speech_session.provider import ProviderAdmission

    db = Database(tmp_path / "routed-speech.db")
    _profile(db, "speech-local", claims=("language", _result_claim("speech.rewrite")))
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "assign-speech-rewrite",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "speech.rewrite"},
            "entries": [{"profile_id": "speech-local", "profile_revision": 1}],
        },
    )
    broker = _configure(db)
    route = broker.inference_adoption_service.plans.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-speech-session-rewrite",
        capability_id="speech.rewrite",
        invocation_id="speech-session-one",
    )

    class Engine:
        backend = "llama_cpp"
        active_provider = "fixture"
        active_model = "speech-local"

        @staticmethod
        def rewrite(prompt: str, **_kwargs: Any) -> str:
            return prompt.upper()

        @staticmethod
        def run_prompt(*, user_prompt: str, **_kwargs: Any) -> str:
            return user_prompt.upper()

    engine = Engine()
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine
    parent = broker.parent_run_controller.start(
        OWNER,
        kind="dictation.session",
        definition_ref="speech:test",
        definition_revision="rev-1",
        input_snapshot={"session": "one"},
        deadline_at=time.time() + 30,
        child_budget=4,
    )
    admission = ProviderAdmission(
        broker=broker,
        principal=OWNER,
        plan=SimpleNamespace(),
        parent=parent,
        routed_routes={CAPABILITY_REWRITE: route},
    )
    assert admission.rewrite(
        engine, "route me", max_tokens=32, temperature=0.0
    ) == "ROUTE ME"
    with db._connection() as conn:
        child = conn.execute(
            "SELECT parent_operation_id FROM kernel_operations "
            "WHERE name='inference.invoke'"
        ).fetchone()
        route_attempt = conn.execute(
            "SELECT outcome,child_operation_id FROM inference_route_attempts"
        ).fetchone()
    assert child is not None and str(child["parent_operation_id"]) == parent.operation_id
    assert route_attempt is not None and str(route_attempt["outcome"]) == "succeeded"
    assert str(route_attempt["child_operation_id"] or "")


@pytest.mark.asyncio
async def test_thought_refinement_materializes_only_controller_winner(
    tmp_path: Path,
) -> None:
    from holdspeak.services.refinement_coordinator import RefinementCoordinator
    from holdspeak.services.ask_service import AskService
    from holdspeak.services.refinement_thought_service import (
        INBOX_DIRECTORY_ID,
        RefinementThoughtService,
    )

    db = Database(tmp_path / "routed-thought.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    _profile(
        db,
        "thought-v2",
        claims=("language", _result_claim("thought.interview"), _result_claim("ask.answer")),
    )
    _profile(
        db,
        "writing-v2",
        claims=("language", _result_claim("speech.intent_classify"), _result_claim("speech.rewrite")),
    )
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
        active_model = "thought-v2"

        @staticmethod
        def run_prompt(**_kwargs: Any) -> str:
            return json.dumps(
                {
                    "kind": "question",
                    "question": "What is the next constraint?",
                    "reason": "Keep it concrete.",
                }
            )

    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: Engine()
    thoughts = RefinementThoughtService(db)
    thought = thoughts.create(
        OWNER,
        request_id="routed-thought-capture",
        raw_text="A routed thought",
        source={"kind": "typed"},
    )
    routed_ask = AskService(db, broker=broker)
    coordinator = RefinementCoordinator(db, ask_factory=lambda: routed_ask)
    coordinator._uses_default_ask = True
    await coordinator.start()
    _current, invocation = await coordinator.begin(
        OWNER,
        thought_id=thought["id"],
        request_id="routed-refine",
        expected_aggregate_revision=1,
        expected_working_revision=1,
        expected_attachment_revision=0,
    )
    for _ in range(100):
        if not coordinator.active_ids:
            break
        await asyncio.sleep(0.01)
    current = thoughts.get(OWNER, thought["id"])
    assert current["continuity"]["state"] == "review_ready"
    with db._connection() as conn:
        linked = conn.execute(
            """SELECT re.winning_attempt_id,ra.id route_attempt_id,rr.kernel_operation_id
               FROM refinement_review_results rr
               JOIN inference_route_attempts ra ON ra.child_operation_id=rr.kernel_operation_id
               JOIN inference_route_executions re ON re.id=ra.execution_id
               WHERE rr.invocation_id=?""",
            (invocation["id"],),
        ).fetchone()
    assert linked is not None
    assert str(linked["winning_attempt_id"]) == str(linked["route_attempt_id"])
    with db._connection() as conn:
        review_id = str(conn.execute(
            "SELECT review_result_id FROM refinement_invocations WHERE id=?",
            (invocation["id"],),
        ).fetchone()[0])
    cursor = thoughts.get_workbench(
        OWNER, thought["id"], inference_available=True
    )["workspace_cursor"]
    _continued, continuation = await coordinator.answer_and_continue(
        OWNER, thought_id=thought["id"], review_result_id=review_id,
        command_id="routed-continuation", answer="The exact constraint.",
        expected_aggregate_revision=current["aggregate_revision"],
        expected_working_revision=current["working_revision"],
        expected_attachment_revision=current["attachment_revision"],
        workspace_cursor=cursor,
    )
    with db._connection() as conn:
        child = conn.execute(
            "SELECT route_plan_id,operation_plan_id,route_execution_id FROM refinement_invocations WHERE id=?",
            (continuation["child_invocation_id"],),
        ).fetchone()
    assert child is not None and all(str(value or "") for value in child)
    await coordinator.shutdown()
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == 2


@pytest.mark.asyncio
async def test_routed_thought_resumes_exact_predispatch_execution_after_restart(
    tmp_path: Path,
) -> None:
    from holdspeak.services.ask_service import AskService
    from holdspeak.services.refinement_coordinator import RefinementCoordinator
    from holdspeak.services.refinement_thought_service import (
        INBOX_DIRECTORY_ID,
        RefinementThoughtService,
    )

    db = Database(tmp_path / "routed-thought-restart.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    _profile(
        db,
        "thought-v2",
        claims=("language", _result_claim("thought.interview"), _result_claim("ask.answer")),
    )
    _profile(
        db,
        "writing-v2",
        claims=(
            "language",
            _result_claim("speech.intent_classify"),
            _result_claim("speech.rewrite"),
        ),
    )
    broker = _configure(db)
    broker.inference_adoption_service.migrate_legacy_config(
        OWNER,
        SimpleNamespace(
            thoughts=SimpleNamespace(inference_target_id="thought-v2"),
            dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="writing-v2")),
        ),
    )

    entered, release = threading.Event(), threading.Event()

    class Engine:
        active_provider = "fixture"
        active_model = "thought-v2"

        @staticmethod
        def run_prompt(**_kwargs: Any) -> str:
            entered.set()
            release.wait(2)
            return json.dumps(
                {
                    "kind": "question",
                    "question": "What survived the restart?",
                    "reason": "Use the frozen route.",
                }
            )

    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: Engine()
    thoughts = RefinementThoughtService(db)
    thought = thoughts.create(
        OWNER,
        request_id="restart-thought-capture",
        raw_text="A restartable routed thought",
        source={"kind": "typed"},
    )
    routed_ask = AskService(db, broker=broker)
    first = RefinementCoordinator(db, ask_factory=lambda: routed_ask)
    first._uses_default_ask = True
    await first.start()

    async def simulate_crash_before_task(*_args: Any, **_kwargs: Any) -> bool:
        return False

    first.submit = simulate_crash_before_task  # type: ignore[method-assign]
    _current, invocation = await first.begin(
        OWNER,
        thought_id=thought["id"],
        request_id="restart-routed-refine",
        expected_aggregate_revision=1,
        expected_working_revision=1,
        expected_attachment_revision=0,
    )
    execution_id = str(invocation["route_execution_id"])
    await first.shutdown()

    replacement = RefinementCoordinator(db, ask_factory=lambda: routed_ask)
    replacement._uses_default_ask = True
    recovered = await replacement.start()
    assert invocation["id"] in recovered
    assert await asyncio.to_thread(entered.wait, 2)
    current = thoughts.get(OWNER, thought["id"])
    _stopped, disposition = await replacement.stop(
        OWNER,
        thought_id=thought["id"],
        invocation_id=invocation["id"],
        expected_aggregate_revision=current["aggregate_revision"],
    )
    assert disposition in {"cancelled", "pending", "refused"}
    assert disposition != "owner_unavailable"
    release.set()
    for _ in range(100):
        if not replacement.active_ids:
            break
        await asyncio.sleep(0.01)
    with db._connection() as conn:
        owner = conn.execute(
            "SELECT dispatch_host_id,dispatch_lease_epoch FROM refinement_invocations WHERE id=?",
            (invocation["id"],),
        ).fetchone()
        executions = conn.execute(
            "SELECT id,state,terminal_outcome FROM inference_route_executions"
        ).fetchall()
    assert (str(owner["dispatch_host_id"]), int(owner["dispatch_lease_epoch"])) == (
        replacement.host_id,
        replacement._lease_epoch,
    )
    assert [(str(row["id"]), str(row["state"])) for row in executions] == [
        (execution_id, "terminal")
    ]
    await replacement.shutdown()


