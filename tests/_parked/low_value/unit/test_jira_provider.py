# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_jira_provider.py to restore.

# ruff: noqa


# --- TestManifest: P6/P1: manifest key-set parity, version recomputed from the product's own formula, revision is an int; no value a user sees
class TestManifest:
    def test_manifest_shape_parity_with_github(self) -> None:
        """Jira manifest has the EXACT same key set as GitHub's."""
        from holdspeak.services.github_provider import GitHubProviderAdapter
        gh_keys = set(GitHubProviderAdapter().manifest().keys())
        jira_keys = set(JiraProviderAdapter().manifest().keys())
        # Jira adds requires_cli (brief's requirement)
        assert gh_keys.issubset(jira_keys)
        # Verify required keys present
        m = JiraProviderAdapter().manifest()
        assert m["provider_id"] == PROVIDER_ID
        assert m["transport"] == TRANSPORT
        assert m["capabilities"]["discover"] is True
        assert m["capabilities"]["read"] is True
        assert m["capabilities"]["subscribe"] is False
        assert m["capabilities"]["effect"] is False
        assert m["requires_cli"] == "acli"

    def test_manifest_version_is_hash_of_capabilities(self) -> None:
        import hashlib
        m = JiraProviderAdapter().manifest()
        expected = hashlib.sha256(
            json.dumps(m["capabilities"], sort_keys=True).encode()
        ).hexdigest()[:12]
        assert m["version"] == expected

    def test_manifest_version_stable(self) -> None:
        a = JiraProviderAdapter().manifest()
        b = JiraProviderAdapter().manifest()
        assert a["version"] == b["version"]

    def test_manifest_revision_is_integer(self) -> None:
        m = JiraProviderAdapter().manifest()
        assert isinstance(m["revision"], int)
        assert m["revision"] >= 1


# --- TestConnectionRef: P1/P5: a format string's literal output and that two different inputs differ; the multi-connection tests assert the same refs
class TestConnectionRef:
    def test_round_trip(self) -> None:
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        assert ref == "alpha.atlassian.net|user@example.com"
        assert "|" in ref

    def test_two_sites_distinct(self) -> None:
        r1 = connection_ref("alpha.atlassian.net", "user@example.com")
        r2 = connection_ref("beta.atlassian.net", "user@example.com")
        assert r1 != r2

    def test_two_emails_one_site_distinct(self) -> None:
        r1 = connection_ref("alpha.atlassian.net", "alice@example.com")
        r2 = connection_ref("alpha.atlassian.net", "bob@example.com")
        assert r1 != r2
