# PARKED 2026-11-09 (door/thought-dictation-meeting): the Thought runs through the engine door; asking a named target (inference_target_id) is gone.
# Moved from tests/unit/test_mesh_liveness_surfaces.py; its helpers are still there.

from tests.unit.test_mesh_liveness_surfaces import *  # noqa: F401,F403


def test_ask_against_offline_mesh_node_is_an_immediate_409(env) -> None:
    from holdspeak.services.errors import ServiceError

    db, _client = env
    prof = _mesh_profile(db)
    with pytest.raises(ServiceError) as offline:
        _thought_ask(db, prof.id)
    assert "mesh node 'walk-edge' is offline (no worker has ever polled)" in str(offline.value)
    # NOTHING was queued — refusal, not queue-then-timeout
    assert db.mesh_relay.claim_next("walk-edge") is None

    db.mesh_relay.touch_worker("walk-edge", now=datetime.now() - timedelta(seconds=60))
    with pytest.raises(ServiceError) as stale:
        _thought_ask(db, prof.id)
    assert "last seen" in str(stale.value)


def test_ask_against_live_mesh_node_proceeds(env, monkeypatch) -> None:
    db, _client = env
    prof = _mesh_profile(db)
    db.mesh_relay.touch_worker("walk-edge")

    class _FakeRelay:
        active_provider = "mesh"
        node = "walk-edge"
        model_hint = "qwen3.5-4b"

        def run_prompt(self, **kwargs):
            return "FROM THE EDGE"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile",
        lambda **kw: _FakeRelay(),
    )
    body = _thought_ask(db, prof.id)
    assert body["output"] == "FROM THE EDGE"
    assert body["egress"] == {"scope": "mesh", "host": "walk-edge"}
