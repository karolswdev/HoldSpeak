"""HS-161-01: GitHubProviderAdapter -- auth truth table, discovery,
validate_repo, manifest, no-credential fence, live probe.

Tests exercise the adapter through a fake runner (unit) and the real
gh CLI (live-marked, skipped when unauthenticated/absent).
"""
from __future__ import annotations

import json
import logging
import subprocess
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.github_provider import (
    CODE_AUTH_REQUIRED,
    CODE_QUERY_INVALID,
    CODE_SCOPE_DENIED,
    CODE_UNAVAILABLE,
    DISCOVERY_FAILED,
    DISCOVERY_PARTIAL,
    DISCOVERY_READY,
    PROVIDER_ID,
    STATE_CONNECTED,
    STATE_DEGRADED,
    STATE_OWNER_ACTION_REQUIRED,
    STATE_UNAVAILABLE,
    TRANSPORT,
    GitHubProviderAdapter,
    _parse_gh_auth_login,
)


OWNER = Principal(PrincipalKind.OWNER, "test-provider-owner")

# ── Credential-sensitive patterns (PROV-004 fence) ───────────────────

_CREDENTIAL_PATTERNS = (
    "ghp_", "gho_", "ghu_", "ghs_", "ghr_",  # GitHub PAT prefixes
    "token", "secret", "password", "bearer", "authorization",
    "credential", "keyring",
)


# ── Fake runner ──────────────────────────────────────────────────────

def _fake_runner(
    stdout: str = "", stderr: str = "", returncode: int = 0,
) -> Any:
    """Return a runner callable producing a fixed CompletedProcess."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0] if args else [],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
    return runner


def _make_adapter(
    tmp_path: Any,
    *,
    runner: Any = None,
    db_name: str = "test.db",
) -> tuple[GitHubProviderAdapter, Database]:
    db = Database(tmp_path / db_name)
    return GitHubProviderAdapter(db=db, runner=runner), db


# ── Manifest ─────────────────────────────────────────────────────────

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


# ── Auth state truth table ───────────────────────────────────────────

class TestConnectionStatus:
    """PROV-003: readiness from the real probe, not which() alone."""

    def test_connected_with_account(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stdout="github.com\n  Logged in to github.com account octocat (keyring)\n",
            returncode=0,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="conn.db")
        result = adapter.connection_status(OWNER)
        assert result["state"] == STATE_CONNECTED
        assert result["error_code"] is None
        assert result["display"]["account"] == "octocat"

    def test_connected_as_variant(self, tmp_path: Any) -> None:
        """The 'as USERNAME' variant of gh auth status."""
        runner = _fake_runner(
            stdout="Logged in to github.com as janedoe\n",
            returncode=0,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="conn-as.db")
        result = adapter.connection_status(OWNER)
        assert result["state"] == STATE_CONNECTED
        assert result["display"]["account"] == "janedoe"

    def test_connected_no_login_parsed(self, tmp_path: Any) -> None:
        """Authenticated but login not parseable -- still connected."""
        runner = _fake_runner(stdout="OK\n", returncode=0)
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="conn-nologin.db")
        result = adapter.connection_status(OWNER)
        assert result["state"] == STATE_CONNECTED
        assert result["display"] == {}

    def test_unauthenticated_not_logged_in(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stderr="You are not logged into any GitHub hosts. Run gh auth login to authenticate.\n",
            returncode=1,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="unauth.db")
        result = adapter.connection_status(OWNER)
        assert result["state"] == STATE_OWNER_ACTION_REQUIRED
        assert result["error_code"] == CODE_AUTH_REQUIRED
        assert "gh auth login" in result["display"]["recovery_hint"]

    def test_unauthenticated_authentication_keyword(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stderr="authentication required\n",
            returncode=1,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="unauth2.db")
        result = adapter.connection_status(OWNER)
        assert result["state"] == STATE_OWNER_ACTION_REQUIRED
        assert result["error_code"] == CODE_AUTH_REQUIRED

    def test_unavailable_no_binary_no_runner(self, tmp_path: Any) -> None:
        """PROV-003: shutil.which alone yields unavailable, never readiness."""
        adapter, db = _make_adapter(tmp_path, runner=None, db_name="nobin.db")
        # Monkeypatch shutil.which to return None
        import shutil
        original = shutil.which
        try:
            shutil.which = lambda *a, **kw: None
            result = adapter.connection_status(OWNER)
        finally:
            shutil.which = original
        assert result["state"] == STATE_UNAVAILABLE
        assert result["error_code"] == CODE_UNAVAILABLE

    def test_degraded_on_probe_exception(self, tmp_path: Any) -> None:
        def exploding_runner(*args: Any, **kwargs: Any) -> Any:
            raise OSError("network timeout")

        adapter, db = _make_adapter(
            tmp_path, runner=exploding_runner, db_name="degraded.db",
        )
        result = adapter.connection_status(OWNER)
        assert result["state"] == STATE_DEGRADED
        assert result["error_code"] == CODE_UNAVAILABLE
        assert "network timeout" in result["error_detail"]

    def test_degraded_on_unknown_error(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stderr="something completely unexpected\n",
            returncode=1,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="degunknown.db")
        result = adapter.connection_status(OWNER)
        assert result["state"] == STATE_DEGRADED
        assert result["error_code"] == CODE_UNAVAILABLE

    def test_prov003_runner_overrides_which(self, tmp_path: Any) -> None:
        """When a runner is injected, shutil.which is irrelevant --
        readiness comes from the probe, not binary presence."""
        runner = _fake_runner(
            stdout="Logged in to github.com account botuser (keyring)\n",
            returncode=0,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="override.db")
        import shutil
        original = shutil.which
        try:
            shutil.which = lambda *a, **kw: None
            result = adapter.connection_status(OWNER)
        finally:
            shutil.which = original
        assert result["state"] == STATE_CONNECTED


# ── Auth login parser ────────────────────────────────────────────────

class TestParseGhAuthLogin:
    def test_account_variant(self) -> None:
        assert _parse_gh_auth_login(
            "Logged in to github.com account octocat (keyring)"
        ) == "octocat"

    def test_as_variant(self) -> None:
        assert _parse_gh_auth_login(
            "Logged in to github.com as janedoe"
        ) == "janedoe"

    def test_no_match(self) -> None:
        assert _parse_gh_auth_login("OK") == ""

    def test_parenthetical_stripped(self) -> None:
        assert _parse_gh_auth_login(
            "Logged in to github.com account (octocat)"
        ) == "octocat"


# ── Connection persistence + no-credential fence ─────────────────────

class TestConnectionPersistence:
    """PROV-004: the row must contain NO credential material."""

    def test_connected_persisted_and_clean(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stdout="Logged in to github.com account octocat (keyring)\n",
            returncode=0,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="persist.db")
        adapter.connection_status(OWNER)

        row = db.automations.get_provider_connection(adapter._connection_id())
        assert row is not None
        assert row["state"] == STATE_CONNECTED
        assert row["provider_id"] == PROVIDER_ID
        assert row["transport"] == TRANSPORT
        assert row["last_checked_at"] is not None
        assert row["last_connected_at"] is not None

        # PROV-004 fence: grep the entire row for credential material
        row_text = json.dumps(row, default=str).lower()
        for pattern in _CREDENTIAL_PATTERNS:
            assert pattern not in row_text, (
                f"PROV-004 violation: credential pattern {pattern!r} found in row"
            )

    def test_connected_no_credential_in_logs(
        self, tmp_path: Any, caplog: Any,
    ) -> None:
        runner = _fake_runner(
            stdout="Logged in to github.com account octocat (keyring)\n",
            returncode=0,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="logfence.db")
        with caplog.at_level(logging.DEBUG, logger="holdspeak.services.github_provider"):
            adapter.connection_status(OWNER)

        all_logs = " ".join(r.message for r in caplog.records).lower()
        for pattern in ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "bearer"):
            assert pattern not in all_logs, (
                f"PROV-004 violation: credential pattern {pattern!r} in log output"
            )

    def test_owner_action_required_persisted(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stderr="You are not logged into any GitHub hosts.\n",
            returncode=1,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner, db_name="oar.db")
        adapter.connection_status(OWNER)

        row = db.automations.get_provider_connection(adapter._connection_id())
        assert row is not None
        assert row["state"] == STATE_OWNER_ACTION_REQUIRED
        assert row["last_error_code"] == CODE_AUTH_REQUIRED

    def test_update_overwrites_state(self, tmp_path: Any) -> None:
        """Verify state transitions persist correctly."""
        runner_bad = _fake_runner(
            stderr="You are not logged into any GitHub hosts.\n",
            returncode=1,
        )
        adapter, db = _make_adapter(tmp_path, runner=runner_bad, db_name="trans.db")
        adapter.connection_status(OWNER)

        row = db.automations.get_provider_connection(adapter._connection_id())
        assert row["state"] == STATE_OWNER_ACTION_REQUIRED

        # Now it becomes connected
        runner_good = _fake_runner(
            stdout="Logged in to github.com account octocat (keyring)\n",
            returncode=0,
        )
        adapter._runner = runner_good
        adapter.connection_status(OWNER)

        row = db.automations.get_provider_connection(adapter._connection_id())
        assert row["state"] == STATE_CONNECTED
        assert row["last_connected_at"] is not None


# ── Discovery ────────────────────────────────────────────────────────

class TestDiscovery:
    """PROV-006: bounded, paginated, stable-ID'd, partial-tolerant."""

    @staticmethod
    def _repo_rows(count: int = 3) -> str:
        return json.dumps([
            {"name": f"repo-{i}", "owner": {"login": "acme"}, "visibility": "public"}
            for i in range(count)
        ])

    def test_basic_discovery(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout=self._repo_rows(3))
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="disc.db")
        result = adapter.discover(OWNER)
        assert result["state"] == DISCOVERY_READY
        assert len(result["items"]) == 3
        assert result["items"][0]["id"] == "acme/repo-0"
        assert result["cursor"] is None

    def test_stable_ids(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout=self._repo_rows(2))
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="stab.db")
        result = adapter.discover(OWNER)
        ids = [item["id"] for item in result["items"]]
        assert ids == ["acme/repo-0", "acme/repo-1"]

    def test_pagination_cursor(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout=self._repo_rows(5))
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="page.db")
        result = adapter.discover(OWNER, limit=2)
        assert len(result["items"]) == 2
        assert result["cursor"] == 2

        # Second page
        result2 = adapter.discover(OWNER, limit=2, cursor=2)
        assert len(result2["items"]) == 2
        assert result2["items"][0]["id"] == "acme/repo-2"

    def test_search_filter(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout=self._repo_rows(5))
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="search.db")
        result = adapter.discover(OWNER, query="repo-3")
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == "acme/repo-3"

    def test_limit_bounded(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout=self._repo_rows(3))
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="bound.db")
        result = adapter.discover(OWNER, limit=999)
        # Limit capped to 100 internally; just verify no crash
        assert result["state"] == DISCOVERY_READY

    def test_empty_result_partial(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout="[]")
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="empty.db")
        result = adapter.discover(OWNER)
        assert result["state"] == DISCOVERY_PARTIAL
        assert result["items"] == []

    def test_error_typed_not_crash(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stderr="authentication required to list repositories", returncode=1,
        )
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="derr.db")
        result = adapter.discover(OWNER)
        assert result["state"] == DISCOVERY_FAILED
        assert result["error_code"] == CODE_AUTH_REQUIRED
        assert result["items"] == []

    def test_invalid_json_typed(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout="not json at all")
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="djson.db")
        result = adapter.discover(OWNER)
        assert result["state"] == DISCOVERY_FAILED
        assert result["error_code"] == CODE_QUERY_INVALID

    def test_non_array_typed(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout='{"not": "an array"}')
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="dna.db")
        result = adapter.discover(OWNER)
        assert result["state"] == DISCOVERY_FAILED
        assert result["error_code"] == CODE_QUERY_INVALID

    def test_partial_rows_skipped(self, tmp_path: Any) -> None:
        """Non-dict rows and rows without owner/name are skipped."""
        data = json.dumps([
            {"name": "good", "owner": {"login": "acme"}, "visibility": "public"},
            "not a dict",
            {"name": "", "owner": {"login": ""}, "visibility": "public"},
        ])
        runner = _fake_runner(stdout=data)
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="partial.db")
        result = adapter.discover(OWNER)
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == "acme/good"

    def test_exception_does_not_crash(self, tmp_path: Any) -> None:
        def exploding(*a: Any, **kw: Any) -> Any:
            raise OSError("boom")

        adapter, _ = _make_adapter(tmp_path, runner=exploding, db_name="explode.db")
        result = adapter.discover(OWNER)
        assert result["state"] == DISCOVERY_FAILED
        assert result["error_code"] == CODE_UNAVAILABLE


# ── Validate repo (SS8.1 typed fallback) ─────────────────────────────

class TestValidateRepo:
    def test_valid_repo(self, tmp_path: Any) -> None:
        runner = _fake_runner(stdout='[{"number":1}]', returncode=0)
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="vr.db")
        result = adapter.validate_repo(OWNER, "acme/app")
        assert result["valid"] is True
        assert result["error_code"] is None

    def test_invalid_format(self, tmp_path: Any) -> None:
        adapter = GitHubProviderAdapter(runner=_fake_runner())
        for bad in ("noslash", "/leading", "trailing/", ""):
            result = adapter.validate_repo(OWNER, bad)
            assert result["valid"] is False
            assert result["error_code"] == CODE_QUERY_INVALID

    def test_not_found(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stderr="Could not resolve to a Repository with the name 'x/y'. (not found)",
            returncode=1,
        )
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="vrnf.db")
        result = adapter.validate_repo(OWNER, "x/y")
        assert result["valid"] is False
        assert result["error_code"] == CODE_SCOPE_DENIED

    def test_auth_required(self, tmp_path: Any) -> None:
        runner = _fake_runner(
            stderr="authentication required",
            returncode=1,
        )
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="vrauth.db")
        result = adapter.validate_repo(OWNER, "x/y")
        assert result["valid"] is False
        assert result["error_code"] == CODE_AUTH_REQUIRED

    def test_unknown_error(self, tmp_path: Any) -> None:
        runner = _fake_runner(stderr="something weird", returncode=1)
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="vrunknown.db")
        result = adapter.validate_repo(OWNER, "x/y")
        assert result["valid"] is False
        assert result["error_code"] == CODE_UNAVAILABLE

    def test_exception_does_not_crash(self, tmp_path: Any) -> None:
        def exploding(*a: Any, **kw: Any) -> Any:
            raise OSError("timeout")

        adapter = GitHubProviderAdapter(runner=exploding)
        result = adapter.validate_repo(OWNER, "acme/app")
        assert result["valid"] is False
        assert result["error_code"] == CODE_UNAVAILABLE


# ── Snapshot delegation ──────────────────────────────────────────────

class TestSnapshot:
    def test_snapshot_delegates_to_watch_source(self, tmp_path: Any) -> None:
        """Snapshot must delegate to fetch_watch_snapshot, not fork logic."""
        pr_data = json.dumps([{
            "number": 42, "title": "fix", "url": "https://github.com/a/b/pull/42",
            "state": "OPEN", "isDraft": False, "reviewRequests": [],
            "reviewDecision": "", "statusCheckRollup": [],
            "headRefOid": "abc123", "updatedAt": "2026-01-01T00:00:00Z",
        }])
        runner = _fake_runner(stdout=pr_data, returncode=0)
        adapter, _ = _make_adapter(tmp_path, runner=runner, db_name="snap.db")
        entities = adapter.snapshot(OWNER, {
            "query_kind": "pull_requests",
            "query": {"repository": "acme/app", "state": "open"},
        })
        assert len(entities) == 1
        assert entities[0]["number"] == 42


# ── Live probe (real gh CLI) ─────────────────────────────────────────

def _gh_available() -> bool:
    """Check if gh is installed and authenticated."""
    import shutil
    if shutil.which("gh") is None:
        return False
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


@pytest.mark.skipif(not _gh_available(), reason="gh CLI not authenticated or not installed")
class TestLiveProbe:
    """Live tests against the real gh CLI. Read-only."""

    def test_live_connection_status(self, tmp_path: Any) -> None:
        adapter, db = _make_adapter(tmp_path, db_name="live.db")
        result = adapter.connection_status(OWNER)
        assert result["state"] == STATE_CONNECTED
        assert result["display"].get("account"), "Live probe should return an account"

        # Verify persistence
        row = db.automations.get_provider_connection(adapter._connection_id())
        assert row is not None
        assert row["state"] == STATE_CONNECTED

    def test_live_discover_returns_repos(self, tmp_path: Any) -> None:
        adapter, _ = _make_adapter(tmp_path, db_name="livedisc.db")
        result = adapter.discover(OWNER, limit=5)
        assert result["state"] in (DISCOVERY_READY, DISCOVERY_PARTIAL)
        assert len(result["items"]) >= 1, "Authenticated user should have at least one repo"
        # Stable IDs
        for item in result["items"]:
            assert "/" in item["id"]
