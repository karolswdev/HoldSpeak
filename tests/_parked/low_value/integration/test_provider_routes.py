# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_provider_routes.py to restore.

# ruff: noqa


# --- TestListProviders::test_native_provider_has_families: P1/P6: asserts literal family names and capability flags of the static provider list
# (was a method of class TestListProviders)
def test_native_provider_has_families(self, rig) -> None:
    _db, client, _log, _ctx = rig
    resp = client.get("/api/providers")
    native = [p for p in resp.json()["providers"] if p["provider_id"] == "native"][0]
    assert "meetings" in native["families"]
    assert "decisions" in native["families"]
    assert "door" in native["families"]


# --- TestListProviders::test_github_provider_has_capabilities: P1/P6: asserts literal family names and capability flags of the static provider list
# (was a method of class TestListProviders)
def test_github_provider_has_capabilities(self, rig) -> None:
    _db, client, _log, _ctx = rig
    resp = client.get("/api/providers")
    github = [p for p in resp.json()["providers"] if p["provider_id"] == "github"][0]
    assert github["capabilities"]["discover"] is True
    assert github["capabilities"]["read"] is True
