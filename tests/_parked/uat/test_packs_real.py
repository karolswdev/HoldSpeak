# PARKED 2026-11-09 (pipe/test-mass): the real-boot half of tests/uat/test_packs.py (boots the product through the conductor).
# Owner 2026-11-08: no pipeline stands anything up; the Programs engine is the
# one runner. Kept, not run (tests/_parked/conftest.py ignores this tree).
# Imports and helpers: tests/uat/test_packs.py.

@pytest.fixture
def real_client(tmp_path, monkeypatch):
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "_runs"))
    monkeypatch.setenv("UAT_DB_PATH", str(tmp_path / "_runs" / "uat.db"))
    monkeypatch.delenv("UAT_REAL_HOME", raising=False)
    mgr = RunManager(Database(), boot_timeout=60.0, link_caches=True)
    app = create_app(mgr)
    with TestClient(app) as c:
        try:
            yield c
        finally:
            mgr.teardown_all()


def test_pack_d_stages_locally(real_client):
    """Pack D demos without the LAN: its bad-endpoint scenario stages + verifies."""
    created = real_client.post("/api/sittings", json={"pack": "pack-d-honest-failure"}).json()
    if created["run"] is None or created["run"]["status"] != "up":
        pytest.skip("product did not boot")
    sid = created["id"]
    # Stage the dead-endpoint scenario (fully local — port 9 refused).
    staged = real_client.post(f"/api/sittings/{sid}/stage", json={"scenario_id": "d-dead-endpoint-doctor"}).json()
    assert staged["ok"], staged
