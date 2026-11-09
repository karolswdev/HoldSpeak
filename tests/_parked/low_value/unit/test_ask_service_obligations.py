# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_ask_service_obligations.py to restore.

# ruff: noqa


# --- test_ask_v1_contract_shape_hash_guards_service_payload_drift: P6: hashes the internal payload's key/type shape; no value a user sees
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


# --- test_ask_v1_golden_field_names_and_schema_version_are_exact: P6: hashes the internal payload's key/type shape; no value a user sees
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
