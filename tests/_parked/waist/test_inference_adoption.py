# PARKED 2026-11-09 (door/own-choice-park-waist): their methods are parked: no product caller once the engine door chose on its own.
# Moved from tests/unit/test_inference_adoption.py; its helpers are still there.

from tests.unit.test_inference_adoption import *  # noqa: F401,F403


def test_composite_is_published_only_after_every_operation_freezes(tmp_path: Path) -> None:
    db = Database(tmp_path / "composite.db")
    _ready_route(db, profiles=("quick",))
    service = ProductionInferenceAdoptionService(db)
    with pytest.raises(Exception):
        service.admit_composite(
            OWNER,
            command_id="speech-composite",
            operations=[
                {
                    "capability_id": "ask.answer",
                    "operation_id": "composite-good",
                    "payload": _payload(),
                },
                {
                    "capability_id": "speech.rewrite",
                    "operation_id": "composite-no-assignment",
                    "payload": _payload("rewrite"),
                },
            ],
        )
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_adoption_composites"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_adoption_material_snapshots"
        ).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == 0


def test_speech_style_operation_freezes_against_existing_route_without_reresolution(
    tmp_path: Path,
) -> None:
    from holdspeak.services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY

    db = Database(tmp_path / "two-phase.db")
    _ready_route(db, profiles=("quick", "deep"))
    service = ProductionInferenceAdoptionService(db)
    route = service.plans.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-session-route",
        capability_id="ask.answer",
    )
    assignment = InferenceAssignmentService(db).resolve_effective(
        OWNER, capability_id="ask.answer"
    )
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "retarget-after-session-open",
            "expected_revision": assignment["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": "deep", "profile_revision": 1}],
        },
    )
    reference = "speech-style-material"
    service.evidence.stage(
        planning_reference=reference,
        capability_id="ask.answer",
        operation_id="speech-style-operation",
        contract="ask.answer",
        contract_revision="1",
        payload=_payload("late material"),
        reserved_output_tokens=64,
    )
    frozen = service.plans.freeze_operation_for_route(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-late-operation",
        route_plan_id=route["id"],
        operation_id="speech-style-operation",
        planning_reference=reference,
    )
    assert frozen["route_plan"]["sha256"] == route["sha256"]
    assert [item["profile_id"] for item in frozen["route_plan"]["entries"]] == [
        "quick", "deep",
    ]


def test_next_run_summary_and_override_are_invocation_scoped(tmp_path: Path) -> None:
    db = Database(tmp_path / "next-run.db")
    _ready_route(db, profiles=("quick", "deep"))
    service = ProductionInferenceAdoptionService(db)
    before = service.next_run_summary(OWNER, capability_id="ask.answer")
    assert [item["profile_id"] for item in before["chain"]] == ["quick", "deep"]
    service.apply_next_run_override(
        OWNER,
        command_id="override-one-run",
        invocation_id="ask-next-run",
        capability_id="ask.answer",
        entries=[{"profile_id": "deep", "profile_revision": 1}],
    )
    selected = service.next_run_summary(
        OWNER, capability_id="ask.answer", invocation_id="ask-next-run"
    )
    unchanged = service.next_run_summary(OWNER, capability_id="ask.answer")
    assert selected["source"] == "invocation"
    assert [item["profile_id"] for item in selected["chain"]] == ["deep"]
    assert [item["profile_id"] for item in unchanged["chain"]] == ["quick", "deep"]


def test_migrated_ask_cancelled_after_provider_return_publishes_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    """The MIGRATED (routed) Ask path: the owner cancels while the provider is
    in flight; the provider then returns.

    The cancel reaches the child through ``stop_operation`` (it queried a table
    that does not exist and raised, so the late answer was published). No
    ``ask_results`` row, no PUBLISHED stage, and the receipt records the return.
    """
    from holdspeak.services.ask_service import AskService
    from tests._cancel_after_return import (
        SIGNAL_FIRST, assert_provider_return_on_record, force_cancel_order,
    )

    db = Database(tmp_path / "routed-ask-cancel.db")
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
    service = AskService(db, broker=broker)
    settled = force_cancel_order(monkeypatch, SIGNAL_FIRST)
    cancels: list[Any] = []
    cancel_ended = threading.Event()

    def cancel() -> None:
        try:
            cancels.append(service.cancel(OWNER, "ask_migratedcancel"))
        except BaseException as exc:  # noqa: BLE001 - the failure is the finding
            cancels.append(exc)
        finally:
            cancel_ended.set()

    class Engine:
        active_provider = "fixture"
        active_model = "routed-model"

        def run_prompt(self, **_kwargs: Any) -> str:
            threading.Thread(target=cancel, daemon=True).start()
            # Return only when the adapter has answered the cancel signal, or
            # when the cancel ended with no signal (the defect).
            deadline = time.monotonic() + 120
            while not settled.is_set() and not cancel_ended.is_set():
                assert time.monotonic() < deadline, "the cancel neither settled nor ended"
                settled.wait(0.01)
            return "late routed answer"

    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: Engine()
    try:
        answer: Any = asyncio.run(service.ask(OWNER, "What changed?", invocation_id="ask_migratedcancel"))
    except Exception as exc:  # noqa: BLE001 - the refusal is the answer here
        answer = exc
    assert cancel_ended.wait(120)

    assert len(cancels) == 1 and not isinstance(cancels[0], BaseException), cancels
    assert "late routed answer" not in repr(answer)
    assert isinstance(answer, Exception), answer
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM kernel_projection_stages WHERE state='PUBLISHED'"
        ).fetchone()[0] == 0
        children = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchall()
    assert len(children) == 1
    assert_provider_return_on_record(db, str(children[0][0]), fenced=True)


