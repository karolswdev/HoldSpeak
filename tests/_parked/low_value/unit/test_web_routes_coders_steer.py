# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_web_routes_coders_steer.py to restore.

# ruff: noqa


# --- test_registry_path_still_works_unchanged: P5: same arm-then-steer path as test_armed_steer_delivers_exactly_as_composed
def test_registry_path_still_works_unchanged(env) -> None:
    # HS-89-02 must not regress Phase 87: an agent:session_id key steers
    # exactly as before.
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post("/api/coders/claude:abc/steer", json={"text": "hi"})
    assert res.status_code == 200 and res.json()["pane_id"] == "%3"
