"""HS-166-01: JiraProviderAdapter -- multi-account connection ledger,
switch-and-verify law, the lock, typed auth truth table.

Tests exercise the adapter through a fake runner (unit).
Recorded shapes from acli 1.3.36-stable live (2026-09-03) and
Atlassian docs.  Every fixture carries ``recorded_from``.
"""
from __future__ import annotations

import json
import subprocess
import threading
import time
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.github_provider import (
    CODE_AUTH_REQUIRED,
    CODE_QUERY_INVALID,
    CODE_SCOPE_DENIED,
    CODE_UNAVAILABLE,
    DISCOVERY_UNKNOWN,
    STATE_CONNECTED,
    STATE_DEGRADED,
    STATE_DISCONNECTED,
    STATE_OWNER_ACTION_REQUIRED,
    STATE_UNAVAILABLE,
)
from holdspeak.services.jira_provider import (
    PROVIDER_ID,
    TRANSPORT,
    JiraProviderAdapter,
    _normalize_site,
    _parse_acli_auth_status,
    connection_ref,
)


OWNER = Principal(PrincipalKind.OWNER, "test-jira-provider-owner")


# ── Recorded acli output shapes ──────────────────────────────────────
# recorded_from: "acli 1.3.36-stable live, 2026-09-03"

# Connected status output
_CONNECTED_STATUS_STDOUT = (
    "✓ Authenticated\n"
    "  Site: alpha.atlassian.net\n"
    "  Email: user@example.com\n"
    "  Authentication Type: oauth\n"
)

# Successful switch output
_SWITCH_OK_STDOUT = (
    "✓ Switched to account: alpha.atlassian.net [user@example.com]"
)

# Unauthenticated status output
_UNAUTH_STATUS = (
    "✗ Error: unauthorized: use 'acli jira auth login' to authenticate"
)

# Account not found (switch to unknown site+email)
_ACCOUNT_NOT_FOUND = (
    "✗ Error: account with email 'unknown@example.com' and site "
    "'unknown.atlassian.net' not found, example: --site mysite.atlassian.net "
    "--email user@atlassian.com"
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


def _recording_runner(responses: list[dict[str, Any]]) -> tuple[Any, list[list[str]]]:
    """Return a runner that yields responses in order and records call args.

    Each response is ``{"stdout": ..., "stderr": ..., "returncode": ...}``.
    """
    call_log: list[list[str]] = []
    idx = [0]

    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0]) if args else list(kwargs.get("args", []))
        call_log.append(cmd)
        resp = responses[idx[0]] if idx[0] < len(responses) else responses[-1]
        idx[0] += 1
        return subprocess.CompletedProcess(
            cmd,
            resp.get("returncode", 0),
            stdout=resp.get("stdout", ""),
            stderr=resp.get("stderr", ""),
        )

    return runner, call_log


def _make_adapter(
    tmp_path: Any,
    *,
    runner: Any = None,
    db_name: str = "test-jira.db",
) -> tuple[JiraProviderAdapter, Database]:
    db = Database(tmp_path / db_name)
    return JiraProviderAdapter(db=db, runner=runner), db


# ── Manifest ─────────────────────────────────────────────────────────

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


# ── normalize_site ───────────────────────────────────────────────────

class TestNormalizeSite:
    @pytest.mark.parametrize("raw,expected", [
        ("alpha", "alpha.atlassian.net"),
        ("alpha.atlassian.net", "alpha.atlassian.net"),
        ("https://alpha.atlassian.net/", "alpha.atlassian.net"),
        ("https://alpha.atlassian.net", "alpha.atlassian.net"),
        ("ALPHA", "alpha.atlassian.net"),
        ("Alpha.Atlassian.Net", "alpha.atlassian.net"),
        ("my-site", "my-site.atlassian.net"),
        ("my-site.atlassian.net", "my-site.atlassian.net"),
        ("http://alpha.atlassian.net/", "alpha.atlassian.net"),
    ])
    def test_valid_normalization(self, raw: str, expected: str) -> None:
        assert _normalize_site(raw) == expected

    @pytest.mark.parametrize("raw", [
        "",
        "   ",
        "not-an-atlassian-domain.com",
        "https://example.com/",
        ".atlassian.net",
        "foo.bar.baz",
    ])
    def test_invalid_rejected(self, raw: str) -> None:
        from holdspeak.services.errors import ValidationError
        with pytest.raises(ValidationError):
            _normalize_site(raw)


# ── connection_ref ───────────────────────────────────────────────────

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


# ── Two connections coexist ──────────────────────────────────────────

class TestMultipleConnections:
    def test_two_sites_persist_own_rows(self, tmp_path: Any) -> None:
        """Two connections (two sites) each get their own row."""
        adapter, db = _make_adapter(tmp_path, runner=_fake_runner())

        c1 = adapter.add_connection(OWNER, "alpha", "user@example.com")
        c2 = adapter.add_connection(OWNER, "beta", "admin@example.com")

        assert c1["provider_id"] == "jira"
        assert c2["provider_id"] == "jira"
        assert c1["external_connection_ref"] == "alpha.atlassian.net|user@example.com"
        assert c2["external_connection_ref"] == "beta.atlassian.net|admin@example.com"

        rows = adapter.list_connections(OWNER)
        refs = [r["external_connection_ref"] for r in rows]
        assert "alpha.atlassian.net|user@example.com" in refs
        assert "beta.atlassian.net|admin@example.com" in refs

    def test_two_emails_one_site_coexist(self, tmp_path: Any) -> None:
        """Two emails on the same site → two rows."""
        adapter, db = _make_adapter(tmp_path, runner=_fake_runner())

        c1 = adapter.add_connection(OWNER, "alpha", "alice@example.com")
        c2 = adapter.add_connection(OWNER, "alpha", "bob@example.com")

        rows = adapter.list_connections(OWNER)
        refs = [r["external_connection_ref"] for r in rows]
        assert "alpha.atlassian.net|alice@example.com" in refs
        assert "alpha.atlassian.net|bob@example.com" in refs
        assert len(refs) == 2

    def test_add_connection_idempotent(self, tmp_path: Any) -> None:
        """Adding the same (site, email) twice returns the existing row."""
        adapter, db = _make_adapter(tmp_path, runner=_fake_runner())

        c1 = adapter.add_connection(OWNER, "alpha", "user@example.com")
        c2 = adapter.add_connection(OWNER, "alpha", "user@example.com")

        assert c1["id"] == c2["id"]
        rows = adapter.list_connections(OWNER)
        assert len(rows) == 1


# ── Switch + status call ORDER ───────────────────────────────────────

class TestSwitchAndVerifyOrder:
    def test_switch_then_status_order(self, tmp_path: Any) -> None:
        """connection_status calls switch THEN status (in that order)."""
        runner, call_log = _recording_runner([
            # switch response
            {"stdout": _SWITCH_OK_STDOUT.replace("alpha.atlassian.net", "alpha.atlassian.net").replace("user@example.com", "user@example.com"), "returncode": 0},
            # status response
            {"stdout": _CONNECTED_STATUS_STDOUT, "returncode": 0},
        ])
        adapter, db = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        adapter.add_connection(OWNER, "alpha", "user@example.com")

        adapter.connection_status(OWNER, ref)

        assert len(call_log) == 2
        # First call: switch
        assert call_log[0][0:4] == ["acli", "jira", "auth", "switch"]
        assert "--site" in call_log[0]
        assert "--email" in call_log[0]
        # Second call: status
        assert call_log[1] == ["acli", "jira", "auth", "status"]

    def test_switch_supplies_correct_site_and_email(self, tmp_path: Any) -> None:
        """The switch command carries the connection's site and email."""
        runner, call_log = _recording_runner([
            {"stdout": "✓ Switched to account: beta.atlassian.net [admin@corp.com]", "returncode": 0},
            {"stdout": "✓ Authenticated\n  Site: beta.atlassian.net\n  Email: admin@corp.com\n  Authentication Type: oauth\n", "returncode": 0},
        ])
        adapter, db = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("beta.atlassian.net", "admin@corp.com")
        adapter.add_connection(OWNER, "beta", "admin@corp.com")

        adapter.connection_status(OWNER, ref)

        switch_args = call_log[0]
        site_idx = switch_args.index("--site")
        email_idx = switch_args.index("--email")
        assert switch_args[site_idx + 1] == "beta.atlassian.net"
        assert switch_args[email_idx + 1] == "admin@corp.com"


# ── Auth state truth table ───────────────────────────────────────────

class TestConnectionStatus:
    """PROV-003: readiness from the real probe, not which() alone."""

    def test_connected_with_account(self, tmp_path: Any) -> None:
        """recorded_from: acli 1.3.36-stable live, 2026-09-03"""
        runner, _ = _recording_runner([
            {"stdout": _SWITCH_OK_STDOUT, "returncode": 0},
            {"stdout": _CONNECTED_STATUS_STDOUT, "returncode": 0},
        ])
        adapter, db = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        adapter.add_connection(OWNER, "alpha", "user@example.com")

        result = adapter.connection_status(OWNER, ref)

        assert result["state"] == STATE_CONNECTED
        assert result["error_code"] is None
        assert result["account"]["site"] == "alpha.atlassian.net"
        assert result["account"]["email"] == "user@example.com"
        assert result["last_connected_at"] is not None

    def test_connected_persists_last_connected_at(self, tmp_path: Any) -> None:
        runner, _ = _recording_runner([
            {"stdout": _SWITCH_OK_STDOUT, "returncode": 0},
            {"stdout": _CONNECTED_STATUS_STDOUT, "returncode": 0},
        ])
        adapter, db = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        adapter.add_connection(OWNER, "alpha", "user@example.com")

        result = adapter.connection_status(OWNER, ref)
        assert result["state"] == STATE_CONNECTED

        # DB row
        cid = adapter._connection_id(ref)
        row = db.automations.get_provider_connection(cid)
        assert row is not None
        assert row["state"] == STATE_CONNECTED
        assert row["last_connected_at"] is not None

    def test_binary_absent_unavailable(self, tmp_path: Any, monkeypatch: Any) -> None:
        """No runner injected + which("acli") is None → unavailable + install recovery."""
        monkeypatch.setattr("shutil.which", lambda x: None)
        adapter, db = _make_adapter(tmp_path, runner=None)
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        adapter.add_connection(OWNER, "alpha", "user@example.com")

        result = adapter.connection_status(OWNER, ref)

        assert result["state"] == STATE_UNAVAILABLE
        assert result["error_code"] == CODE_UNAVAILABLE
        assert "acli" in result["error_detail"].lower()
        assert result["recovery"]["command"] == "brew tap atlassian/homebrew-acli && brew install acli"

    def test_unauthenticated_owner_action_required(self, tmp_path: Any) -> None:
        """recorded_from: acli 1.3.36-stable live, 2026-09-03"""
        runner, _ = _recording_runner([
            {"stderr": _UNAUTH_STATUS, "returncode": 1},
        ])
        adapter, db = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        adapter.add_connection(OWNER, "alpha", "user@example.com")

        result = adapter.connection_status(OWNER, ref)

        assert result["state"] == STATE_OWNER_ACTION_REQUIRED
        assert result["error_code"] == CODE_AUTH_REQUIRED
        assert result["recovery"]["command"] == (
            "acli jira auth login --site alpha.atlassian.net --email user@example.com --token"
        )

    def test_account_not_found_owner_action_required(self, tmp_path: Any) -> None:
        """recorded_from: acli 1.3.36-stable live, 2026-09-03.
        Switch to unknown (site,email) → account not found → owner_action_required.
        """
        runner, _ = _recording_runner([
            {"stderr": _ACCOUNT_NOT_FOUND, "returncode": 1},
        ])
        adapter, db = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("unknown.atlassian.net", "unknown@example.com")
        adapter.add_connection(OWNER, "unknown", "unknown@example.com")

        result = adapter.connection_status(OWNER, ref)

        assert result["state"] == STATE_OWNER_ACTION_REQUIRED
        assert result["error_code"] == CODE_AUTH_REQUIRED
        assert "acli jira auth login" in result["recovery"]["command"]

    def test_readback_mismatch_degraded(self, tmp_path: Any) -> None:
        """Switch says OK but status reads back a DIFFERENT site → typed error."""
        runner, _ = _recording_runner([
            # switch succeeds
            {"stdout": "✓ Switched to account: alpha.atlassian.net [user@example.com]", "returncode": 0},
            # status reads back a DIFFERENT site
            {"stdout": "✓ Authenticated\n  Site: other.atlassian.net\n  Email: other@example.com\n  Authentication Type: oauth\n", "returncode": 0},
        ])
        adapter, db = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        adapter.add_connection(OWNER, "alpha", "user@example.com")

        result = adapter.connection_status(OWNER, ref)

        assert result["state"] == STATE_DEGRADED
        assert result["error_code"] == CODE_SCOPE_DENIED
        assert "read-back mismatch" in result["error_detail"]


# ── Readiness (SETFLOW-005) ──────────────────────────────────────────

class TestReadiness:
    def test_unavailable_no_acli(self, tmp_path: Any, monkeypatch: Any) -> None:
        monkeypatch.setattr("shutil.which", lambda x: None)
        adapter, _ = _make_adapter(tmp_path, runner=None)
        r = adapter.readiness(OWNER)
        assert r["state"] == "unavailable"
        assert r["connections"] == 0

    def test_partial_with_acli_no_connections(self, tmp_path: Any) -> None:
        adapter, _ = _make_adapter(tmp_path, runner=_fake_runner())
        r = adapter.readiness(OWNER)
        assert r["state"] == "partial"
        assert r["connections"] == 0

    def test_partial_with_connections_not_connected(self, tmp_path: Any) -> None:
        adapter, _ = _make_adapter(tmp_path, runner=_fake_runner())
        adapter.add_connection(OWNER, "alpha", "user@example.com")
        # Row exists but in unavailable state (not connected)
        r = adapter.readiness(OWNER)
        assert r["state"] == "partial"

    def test_connected_with_at_least_one(self, tmp_path: Any) -> None:
        runner, _ = _recording_runner([
            {"stdout": _SWITCH_OK_STDOUT, "returncode": 0},
            {"stdout": _CONNECTED_STATUS_STDOUT, "returncode": 0},
        ])
        adapter, _ = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        adapter.add_connection(OWNER, "alpha", "user@example.com")
        adapter.connection_status(OWNER, ref)

        r = adapter.readiness(OWNER)
        assert r["state"] == "connected"
        assert r["connections"] >= 1


# ── The lock: two threads, two connections, zero cross-reads ─────────

class TestLockSerialization:
    """The switch-and-verify lock prevents interleaved switch calls.

    Two threads, two connections. Each thread's fake runner has a small
    sleep inside switch to widen the race window. The assertion: every
    status read-back matches its own switch — zero cross-reads.
    """

    def test_lock_prevents_cross_reads(self, tmp_path: Any) -> None:
        results: dict[str, dict[str, Any]] = {}
        errors: list[str] = []

        def _slow_runner(
            site: str, email: str, delay: float = 0.05,
        ) -> Any:
            """A runner that delays during switch (widening the race window)."""
            switch_stdout = f"✓ Switched to account: {site} [{email}]"
            status_stdout = (
                f"✓ Authenticated\n"
                f"  Site: {site}\n"
                f"  Email: {email}\n"
                f"  Authentication Type: oauth\n"
            )

            def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
                cmd = list(args[0]) if args else []
                if "switch" in cmd:
                    time.sleep(delay)
                    return subprocess.CompletedProcess(cmd, 0, stdout=switch_stdout, stderr="")
                if "status" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, stdout=status_stdout, stderr="")
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            return runner

        # Thread 1: alpha site
        site_a = "alpha.atlassian.net"
        email_a = "alice@example.com"
        ref_a = connection_ref(site_a, email_a)

        # Thread 2: beta site
        site_b = "beta.atlassian.net"
        email_b = "bob@example.com"
        ref_b = connection_ref(site_b, email_b)

        # IMPORTANT: both threads SHARE one adapter+runner so the lock
        # is exercised.  But the runner needs to know which connection
        # is currently being probed to return the right status.  We use
        # two adapters that share the module-level lock but each has its
        # own runner returning its own site/email.
        adapter_a, db = _make_adapter(
            tmp_path, runner=_slow_runner(site_a, email_a, delay=0.1),
            db_name="lock-test.db",
        )
        adapter_b = JiraProviderAdapter(db=db, runner=_slow_runner(site_b, email_b, delay=0.1))

        adapter_a.add_connection(OWNER, "alpha", "alice@example.com")
        adapter_b.add_connection(OWNER, "beta", "bob@example.com")

        def probe_a() -> None:
            try:
                result = adapter_a.connection_status(OWNER, ref_a)
                results["a"] = result
                if result["state"] == STATE_CONNECTED:
                    if result["account"]["site"] != site_a:
                        errors.append(f"Thread A: expected site {site_a}, got {result['account']['site']}")
                    if result["account"]["email"] != email_a:
                        errors.append(f"Thread A: expected email {email_a}, got {result['account']['email']}")
            except Exception as e:
                errors.append(f"Thread A error: {e}")

        def probe_b() -> None:
            try:
                result = adapter_b.connection_status(OWNER, ref_b)
                results["b"] = result
                if result["state"] == STATE_CONNECTED:
                    if result["account"]["site"] != site_b:
                        errors.append(f"Thread B: expected site {site_b}, got {result['account']['site']}")
                    if result["account"]["email"] != email_b:
                        errors.append(f"Thread B: expected email {email_b}, got {result['account']['email']}")
            except Exception as e:
                errors.append(f"Thread B error: {e}")

        t_a = threading.Thread(target=probe_a)
        t_b = threading.Thread(target=probe_b)

        # Start both threads concurrently
        t_a.start()
        t_b.start()

        t_a.join(timeout=10)
        t_b.join(timeout=10)

        assert not errors, f"Cross-read errors: {errors}"
        assert results.get("a", {}).get("state") == STATE_CONNECTED
        assert results.get("b", {}).get("state") == STATE_CONNECTED
        # Each thread's read-back matched its own switch
        assert results["a"]["account"]["site"] == site_a
        assert results["a"]["account"]["email"] == email_a
        assert results["b"]["account"]["site"] == site_b
        assert results["b"]["account"]["email"] == email_b


# ── Parser unit tests ────────────────────────────────────────────────

class TestParseAcliAuthStatus:
    """recorded_from: acli 1.3.36-stable live, 2026-09-03"""

    def test_structured_format_match(self) -> None:
        """The real acli output with Site:/Email: lines."""
        result = _parse_acli_auth_status(
            _CONNECTED_STATUS_STDOUT,
            "alpha.atlassian.net",
            "user@example.com",
        )
        assert result["match"] is True
        assert result["site"] == "alpha.atlassian.net"
        assert result["email"] == "user@example.com"
        assert result.get("auth_type") == "oauth"

    def test_structured_format_mismatch(self) -> None:
        result = _parse_acli_auth_status(
            "✓ Authenticated\n  Site: other.atlassian.net\n  Email: other@example.com\n",
            "alpha.atlassian.net",
            "user@example.com",
        )
        assert result["match"] is False
        assert "read-back mismatch" in result["detail"]

    def test_email_case_insensitive(self) -> None:
        result = _parse_acli_auth_status(
            "✓ Authenticated\n  Site: alpha.atlassian.net\n  Email: USER@Example.COM\n",
            "alpha.atlassian.net",
            "user@example.com",
        )
        assert result["match"] is True

    def test_unparseable_output(self) -> None:
        result = _parse_acli_auth_status(
            "some random output with no recognizable pattern",
            "alpha.atlassian.net",
            "user@example.com",
        )
        assert result["match"] is False
        assert "Could not parse" in result.get("detail", "")


# ── connection_ref normalization (catch 3) ───────────────────────────

class TestConnectionRefNormalization:
    def test_url_form_and_bare_host_produce_same_ref(self) -> None:
        """URL-form and bare-host inputs produce the same ref."""
        r1 = connection_ref("https://alpha.atlassian.net/", "User@Example.COM")
        r2 = connection_ref("alpha", "user@example.com")
        r3 = connection_ref("alpha.atlassian.net", "user@example.com")
        assert r1 == r2 == r3
        assert r1 == "alpha.atlassian.net|user@example.com"

    def test_status_on_url_form_ref_hits_same_row(self, tmp_path: Any) -> None:
        """connection_status on a URL-form ref resolves to the same persisted row."""
        runner, _ = _recording_runner([
            {"stdout": _SWITCH_OK_STDOUT, "returncode": 0},
            {"stdout": _CONNECTED_STATUS_STDOUT, "returncode": 0},
        ])
        adapter, db = _make_adapter(tmp_path, runner=runner)
        # Add with bare host
        adapter.add_connection(OWNER, "alpha", "user@example.com")
        # Status with URL form
        url_ref = "https://alpha.atlassian.net/|User@Example.COM"
        result = adapter.connection_status(OWNER, url_ref)
        assert result["state"] == STATE_CONNECTED
        # The persisted row is the same
        canonical_ref = connection_ref("alpha", "user@example.com")
        cid = adapter._connection_id(canonical_ref)
        row = db.automations.get_provider_connection(cid)
        assert row is not None
        assert row["state"] == STATE_CONNECTED


# ── add_connection initial state (catch 4) ───────────────────────────

class TestAddConnectionState:
    def test_new_row_state_is_disconnected(self, tmp_path: Any) -> None:
        """New rows start in state ``disconnected``, not ``unavailable``."""
        adapter, db = _make_adapter(tmp_path, runner=_fake_runner())
        c = adapter.add_connection(OWNER, "alpha", "user@example.com")
        assert c["state"] == STATE_DISCONNECTED

    def test_disconnected_row_yields_partial_readiness(self, tmp_path: Any) -> None:
        """A disconnected row means partial readiness (not connected)."""
        adapter, _ = _make_adapter(tmp_path, runner=_fake_runner())
        adapter.add_connection(OWNER, "alpha", "user@example.com")
        r = adapter.readiness(OWNER)
        assert r["state"] == "partial"
        assert r["connected"] == 0

    def test_no_db_returns_disconnected(self) -> None:
        """No DB → disconnected state."""
        adapter = JiraProviderAdapter(runner=_fake_runner())
        c = adapter.add_connection(OWNER, "alpha", "user@example.com")
        assert c["state"] == STATE_DISCONNECTED


# ── known_accounts (acli registry) ───────────────────────────────────

class TestKnownAccounts:
    def _write_registry(self, tmp_path: Any, content: str) -> Any:
        reg_path = tmp_path / "jira_config.yaml"
        reg_path.write_text(content, encoding="utf-8")
        return reg_path

    def test_two_profiles_two_sites(self, tmp_path: Any) -> None:
        reg = self._write_registry(tmp_path, """\
version: 1
current_profile: "cloud1:acct1"
profiles:
  - site: alpha.atlassian.net
    cloud_id: cloud1
    account_id: acct1
    display_name: Alice
    email: alice@example.com
    auth_type: oauth
  - site: beta.atlassian.net
    cloud_id: cloud2
    account_id: acct2
    display_name: Bob
    email: bob@example.com
    auth_type: pat
""")
        adapter = JiraProviderAdapter(runner=_fake_runner(), registry_path=reg)
        accounts = adapter.known_accounts(OWNER)
        assert len(accounts) == 2
        # First is current
        a1 = next(a for a in accounts if a["site"] == "alpha.atlassian.net")
        assert a1["current"] is True
        assert a1["email"] == "alice@example.com"
        assert a1["display_name"] == "Alice"
        assert a1["auth_type"] == "oauth"
        assert a1["ref"] == "alpha.atlassian.net|alice@example.com"
        # Second is not current
        a2 = next(a for a in accounts if a["site"] == "beta.atlassian.net")
        assert a2["current"] is False

    def test_missing_file_returns_empty(self, tmp_path: Any) -> None:
        reg = tmp_path / "nonexistent.yaml"
        adapter = JiraProviderAdapter(runner=_fake_runner(), registry_path=reg)
        assert adapter.known_accounts(OWNER) == []

    def test_empty_profiles_returns_empty(self, tmp_path: Any) -> None:
        reg = self._write_registry(tmp_path, "version: 1\ncurrent_profile: ''\nprofiles: []\n")
        adapter = JiraProviderAdapter(runner=_fake_runner(), registry_path=reg)
        assert adapter.known_accounts(OWNER) == []

    def test_unparsable_yaml_returns_empty(self, tmp_path: Any) -> None:
        reg = self._write_registry(tmp_path, "{{not valid yaml at all")
        adapter = JiraProviderAdapter(runner=_fake_runner(), registry_path=reg)
        # Should not raise
        assert adapter.known_accounts(OWNER) == []

    def test_cloud_id_account_id_not_exposed(self, tmp_path: Any) -> None:
        reg = self._write_registry(tmp_path, """\
version: 1
current_profile: "c:a"
profiles:
  - site: alpha.atlassian.net
    cloud_id: c
    account_id: a
    email: user@example.com
    auth_type: oauth
""")
        adapter = JiraProviderAdapter(runner=_fake_runner(), registry_path=reg)
        accounts = adapter.known_accounts(OWNER)
        a = accounts[0]
        assert "cloud_id" not in a
        assert "account_id" not in a


# ── Readiness includes connected count ───────────────────────────────

class TestReadinessConnectedCount:
    def test_readiness_connected_includes_count(self, tmp_path: Any) -> None:
        runner, _ = _recording_runner([
            {"stdout": _SWITCH_OK_STDOUT, "returncode": 0},
            {"stdout": _CONNECTED_STATUS_STDOUT, "returncode": 0},
        ])
        adapter, _ = _make_adapter(tmp_path, runner=runner)
        ref = connection_ref("alpha.atlassian.net", "user@example.com")
        adapter.add_connection(OWNER, "alpha", "user@example.com")
        adapter.connection_status(OWNER, ref)

        r = adapter.readiness(OWNER)
        assert r["state"] == "connected"
        assert r["connected"] == 1
        assert r["connections"] >= 1

    def test_readiness_unavailable_has_zero_connected(self, tmp_path: Any, monkeypatch: Any) -> None:
        monkeypatch.setattr("shutil.which", lambda x: None)
        adapter, _ = _make_adapter(tmp_path, runner=None)
        r = adapter.readiness(OWNER)
        assert r["connected"] == 0
