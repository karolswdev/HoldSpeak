# PARKED 2026-11-09 (door/thought-dictation-meeting): the Thought runs through the engine door; the placement-based Ask path (a named target, the frozen placement claim, the v1 contract) is gone.
# Moved from tests/unit/test_ask_service_obligations.py; its helpers are still there.

from tests.unit.test_ask_service_obligations import *  # noqa: F401,F403


def test_real_migrated_ask_cancellation_after_stage_is_completed_and_not_duplicated(rig, monkeypatch):
    db, broker, _ = rig
    stager = broker.projection_stager
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: AskEngine())
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: AskEngine())
    stage_committed = threading.Event()
    release_publish = threading.Event()
    staged_ids: list[str] = []
    replies: list[dict[str, Any]] = []
    failures: list[BaseException] = []

    class ChoreographedAdapter:
        def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: threading.Event) -> dict[str, str]:
            return {"output": "late-but-staged", "provider": "test-provider", "model": "test-model"}

        def cancel(self) -> str:
            return "cancelled"

    real_publisher = stager.publisher

    def pause_after_stage(invocation_id: str, kind: str, encoder: Any) -> Any:
        publisher = real_publisher(invocation_id, kind, encoder)

        def stage_then_pause(output: Any) -> str:
            result_ref = publisher(output)
            staged_ids.append(invocation_id)
            stage_committed.set()
            assert release_publish.wait(2)
            return result_ref

        return stage_then_pause

    # The service uses the broker-owned shared runner; only the adapter and
    # the stager's publisher need choreography.
    monkeypatch.setattr(ask_service_module, "CanonicalPromptAdapter", ChoreographedAdapter)
    monkeypatch.setattr(stager, "publisher", pause_after_stage)
    service = AskService(db, broker=broker)

    def invoke_ask() -> None:
        try:
            replies.append(asyncio.run(service.ask(OWNER, "What changed?", lens="Brief", operation_capability=_V1)))
        except BaseException as exc:
            failures.append(exc)

    worker = threading.Thread(target=invoke_ask)
    worker.start()
    assert stage_committed.wait(2) and staged_ids
    stage = stager.get(staged_ids[0])
    assert stage is not None and stage.state == "STAGED"

    # The real Ask callback has committed the stage and runner is PUBLISHING:
    # Round-13 says this is completed, not a cancellation that may rewrite it.
    # Cancellation goes through the SERVICE seam — and through a SECOND
    # service instance, as a separate HTTP request would construct it: the
    # broker-owned runner is what makes the in-flight invocation reachable
    # across per-request service lifetimes.
    second_request_service = AskService(db, broker=broker)
    assert second_request_service is not service
    assert second_request_service.cancel(OWNER, stage.invocation_id)["disposition"] == "completed"
    release_publish.set()
    worker.join(5)
    assert not worker.is_alive() and not failures
    assert replies[0]["output"] == "late-but-staged"
    assert stager.finalize(stage.invocation_id) == replies[0]

    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results WHERE invocation_id=?", (stage.invocation_id,)).fetchone()[0] == 1
        assert conn.execute("SELECT state FROM kernel_projection_stages WHERE invocation_id=?", (stage.invocation_id,)).fetchone()[0] == "PUBLISHED"
    cancel_operations = [
        broker.store.operation(event["operation_id"])
        for event in broker.events(0, {}, OWNER)["events"]
        if broker.store.operation(event["operation_id"])["name"] == "inference.cancel"
    ]
    # A truthful completed disposition creates no cancellation child receipt to
    # race the successful invocation receipt.
    assert cancel_operations == []


def test_ask_v1_contract_shape_hash_guards_service_payload_drift(rig, monkeypatch):
    db, broker, _ = rig
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: AskEngine())
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: AskEngine())
    captured: list[tuple[str, str, dict[str, Any]]] = []
    original = ServiceContract.for_payload.__func__

    def capture(cls: type[ServiceContract], contract: str, revision: str, payload: dict[str, Any]) -> ServiceContract:
        captured.append((contract, revision, dict(payload)))
        return original(cls, contract, revision, payload)

    monkeypatch.setattr(ServiceContract, "for_payload", classmethod(capture))
    result = asyncio.run(AskService(db, broker=broker).ask(OWNER, "What changed?", lens="Brief", operation_capability=_V1))
    assert result["output"] == "contract answer"
    assert captured and captured[-1][0:2] == (ASK_SERVICE_CONTRACT, ASK_SERVICE_SCHEMA_VERSION)
    payload = captured[-1][2]
    actual_shape = {name: type(value).__name__ for name, value in payload.items()}
    missing = sorted(set(_DECLARED_ASK_V1_SHAPE) - set(actual_shape))
    unexpected = sorted(set(actual_shape) - set(_DECLARED_ASK_V1_SHAPE))
    assert not missing, f"holdspeak.ask@1 declared fields missing from service payload: {missing}"
    assert not unexpected, f"holdspeak.ask@1 service payload has undeclared fields: {unexpected}"
    assert actual_shape == _DECLARED_ASK_V1_SHAPE
    assert payload["schema_version"] == ASK_PAYLOAD_SCHEMA_VERSION == 1
    shape_hash = "sha256:" + hashlib.sha256(json.dumps(actual_shape, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert shape_hash == _DECLARED_ASK_V1_SHAPE_SHA256


def test_ask_v1_golden_field_names_and_schema_version_are_exact(rig, monkeypatch):
    db, broker, _ = rig
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: AskEngine())
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: AskEngine())
    captured: list[dict[str, Any]] = []
    original = ServiceContract.for_payload.__func__

    def capture(cls: type[ServiceContract], contract: str, revision: str, payload: dict[str, Any]) -> ServiceContract:
        if contract == ASK_SERVICE_CONTRACT and revision == ASK_SERVICE_SCHEMA_VERSION:
            captured.append(dict(payload))
        return original(cls, contract, revision, payload)

    monkeypatch.setattr(ServiceContract, "for_payload", classmethod(capture))
    asyncio.run(AskService(db, broker=broker).ask(OWNER, "Golden ask", operation_capability=_V1))
    payload = captured[-1]
    missing = sorted(_GOLDEN_ASK_V1_FIELDS - set(payload))
    unexpected = sorted(set(payload) - _GOLDEN_ASK_V1_FIELDS)
    assert not missing, f"holdspeak.ask@1 golden fields missing: {missing}"
    assert not unexpected, f"holdspeak.ask@1 golden fields added or renamed: {unexpected}"
    assert payload["schema_version"] == 1
