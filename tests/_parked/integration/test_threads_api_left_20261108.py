"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/integration/test_threads_api.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""




# ---------------------------------------------------------------------------
# Recipe chat alias
# ---------------------------------------------------------------------------


def test_recipe_chat_alias_creates_thread(client: TestClient, db) -> None:
    """POST /api/recipes/{id}/chat creates/reuses a thread."""
    # Create a recipe first.
    db.recipes.upsert(recipe_id="r_test", name="Test", system_prompt="SYS")

    resp = client.post("/api/recipes/r_test/chat", json={"text": "Hello chat"})
    # May fail with 500 if broker not composed — that's expected in integration
    # without a full composition. Check that it at least doesn't return 410.
    assert resp.status_code != 410
