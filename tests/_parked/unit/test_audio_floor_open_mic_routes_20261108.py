"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/unit/test_audio_floor_open_mic.py``: test_floor_route_reports_the_active_owner_by_name (GET /api/dictation/floor is parked). Not collected; its _client helper is in the source file.
"""
def test_floor_route_reports_the_active_owner_by_name() -> None:
    session = VoiceTypingSession()
    client = _client(session)

    assert client.get("/api/dictation/floor").json() == {
        "arbitrated": True,
        "held": False,
        "owner": None,
    }

    session.acquire("meeting")
    assert client.get("/api/dictation/floor").json() == {
        "arbitrated": True,
        "held": True,
        "owner": "meeting",
    }


