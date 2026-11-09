"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/unit/test_engine_off_the_loop.py`` (the chat half of the recipe test). Not collected (tests/_parked). Restore with ``git revert``.
"""


def _recipe_chat_half(client, spy, rid, time, _assert_off_loop):
    spy.on_loop = None
    resp = client.post(f"/api/recipes/{rid}/chat", json={"question": "hi"})
    # The thread alias returns 201 and dispatches the engine on a daemon
    # thread (the request never blocks the loop). Wait briefly for the
    # daemon to fire the spy before asserting.
    assert resp.status_code == 201
    for _ in range(100):
        if spy.on_loop is not None:
            break
        time.sleep(0.02)
    _assert_off_loop(spy)
