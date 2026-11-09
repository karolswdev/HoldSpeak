# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_github_provider.py to restore.

# ruff: noqa


# --- TestManifest: P1/P6: manifest keys, booleans and a hash of its own constants
class TestManifest:
    def test_manifest_shape(self) -> None:
        adapter = GitHubProviderAdapter()
        m = adapter.manifest()
        assert m["provider_id"] == PROVIDER_ID
        assert m["transport"] == TRANSPORT
        assert m["capabilities"]["discover"] is True
        assert m["capabilities"]["read"] is True
        assert m["capabilities"]["subscribe"] is False
        assert m["capabilities"]["effect"] is False

    def test_manifest_version_is_hash_of_capabilities(self) -> None:
        import hashlib
        adapter = GitHubProviderAdapter()
        m = adapter.manifest()
        expected = hashlib.sha256(
            json.dumps(m["capabilities"], sort_keys=True).encode()
        ).hexdigest()[:12]
        assert m["version"] == expected

    def test_manifest_version_stable(self) -> None:
        a = GitHubProviderAdapter().manifest()
        b = GitHubProviderAdapter().manifest()
        assert a["version"] == b["version"]

    def test_manifest_revision_is_integer(self) -> None:
        m = GitHubProviderAdapter().manifest()
        assert isinstance(m["revision"], int)
        assert m["revision"] >= 1
