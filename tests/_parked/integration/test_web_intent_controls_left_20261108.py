"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/integration/test_web_intent_controls.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


@pytest.mark.integration
def test_intent_override_put_returns_501_when_callback_unset(bare_client) -> None:
    response = bare_client.put(
        "/api/intents/override",
        json={"intents": ["incident", "comms"]},
    )
    assert response.status_code == 501


@pytest.mark.integration
def test_intent_override_put_invokes_callback_with_intent_list() -> None:
    captured: dict[str, object] = {}

    def on_set(intents):
        captured["intents"] = list(intents) if intents is not None else None
        return {"override_intents": intents or []}

    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=lambda *_a, **_kw: None,
                     on_stop=lambda *_a, **_kw: None,
                     get_state=lambda: None,
                     on_set_intent_override=on_set,
                 ),
                 host="127.0.0.1",
             )
    client = TestClient(server.app)

    response = client.put(
        "/api/intents/override",
        json={"intents": ["incident", "comms"]},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert captured["intents"] == ["incident", "comms"]
