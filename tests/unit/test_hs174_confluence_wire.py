"""HS-174-07: Confluence connector wire -- allowlist, provider, WatchSource,
templates, routes, MCP twins, the switch-and-verify order.

Tests exercise the adapter through a fake runner (unit).  No real acli calls.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any

import pytest

from holdspeak.connector_packs.acli_confluence import (
    ALLOWED_SUBCOMMANDS,
    CONNECTOR_ID,
    MANIFEST,
    is_command_allowed,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.confluence_provider import (
    CODE_UNSUPPORTED_BY_CLI,
    PROVIDER_ID,
    ConfluenceProviderAdapter,
)
from holdspeak.services.errors import ServiceError, ValidationError
from holdspeak.services.github_provider import (
    CODE_AUTH_REQUIRED,
    CODE_SCOPE_DENIED,
    CODE_UNAVAILABLE,
    DISCOVERY_READY,
    STATE_CONNECTED,
    STATE_DEGRADED,
    STATE_OWNER_ACTION_REQUIRED,
)
from holdspeak.services.watch_sources import (
    ConfluenceWatchSource,
    fetch_watch_snapshot,
)

OWNER = Principal(PrincipalKind.OWNER, "test-confluence-wire")


# -- Recorded shapes ---------------------------------------------------

_CONNECTED_STATUS = (
    "✓ Authenticated\n"
    "  Site: alpha.atlassian.net\n"
    "  Email: user@example.com\n"
    "  Authentication Type: oauth\n"
)

_SWITCH_OK = (
    "✓ Switched to account: alpha.atlassian.net [user@example.com]"
)


# -- Fake runner -------------------------------------------------------

def _fake_runner(
    stdout: str = "", stderr: str = "", returncode: int = 0,
) -> Any:
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args[0], returncode, stdout, stderr)
    return runner


def _sequenced_runner(responses: list[tuple[str, str, int]]) -> Any:
    """Runner that returns successive responses for each call."""
    idx = {"i": 0}
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        i = idx["i"]
        idx["i"] = i + 1
        if i < len(responses):
            stdout, stderr, rc = responses[i]
        else:
            stdout, stderr, rc = "", "", 1
        return subprocess.CompletedProcess(args[0], rc, stdout, stderr)
    return runner


# =====================================================================
# 1. Allowlist tests
# =====================================================================

class TestAllowlist:
    """The allowlist accepts exactly the design's read-only set."""

    def test_seven_allowed_subcommands(self) -> None:
        assert len(ALLOWED_SUBCOMMANDS) == 7

    def test_all_expected_subcommands_present(self) -> None:
        expected = {
            ("confluence", "auth", "status"),
            ("confluence", "auth", "switch"),
            ("confluence", "space", "list"),
            ("confluence", "space", "view"),
            ("confluence", "page", "view"),
            ("confluence", "blog", "list"),
            ("confluence", "blog", "view"),
        }
        assert ALLOWED_SUBCOMMANDS == expected

    def test_allowed_command_passes(self) -> None:
        assert is_command_allowed(["acli", "confluence", "blog", "list", "--json"])
        assert is_command_allowed(["acli", "confluence", "page", "view", "--id", "123"])

    def test_page_create_rejected(self) -> None:
        assert not is_command_allowed(["acli", "confluence", "page", "create"])

    def test_page_list_rejected(self) -> None:
        """The critical gap: page list does not exist and is not allowed."""
        assert not is_command_allowed(["acli", "confluence", "page", "list"])

    def test_blog_create_rejected(self) -> None:
        assert not is_command_allowed(["acli", "confluence", "blog", "create"])

    def test_space_archive_rejected(self) -> None:
        assert not is_command_allowed(["acli", "confluence", "space", "archive"])

    def test_short_command_rejected(self) -> None:
        assert not is_command_allowed(["acli", "confluence"])

    def test_jira_command_rejected(self) -> None:
        assert not is_command_allowed(["acli", "jira", "auth", "status"])

    def test_manifest_id(self) -> None:
        assert CONNECTOR_ID == "acli_confluence"
        assert MANIFEST.id == "acli_confluence"


# =====================================================================
# 2. Switch-and-verify order
# =====================================================================

class TestSwitchAndVerify:
    """Connection status follows: switch, verify, then read."""

    def test_switch_then_verify_order(self) -> None:
        """The adapter calls switch BEFORE status."""
        calls: list[list[str]] = []

        def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            cmd = list(args[0])
            calls.append(cmd)
            if "switch" in cmd:
                return subprocess.CompletedProcess(cmd, 0, _SWITCH_OK, "")
            if "status" in cmd:
                return subprocess.CompletedProcess(cmd, 0, _CONNECTED_STATUS, "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        adapter = ConfluenceProviderAdapter(runner=runner)
        result = adapter.connection_status(
            OWNER, "alpha.atlassian.net|user@example.com",
        )

        assert result["state"] == STATE_CONNECTED
        # switch must come before status
        switch_idx = next(i for i, c in enumerate(calls) if "switch" in c)
        status_idx = next(i for i, c in enumerate(calls) if "status" in c)
        assert switch_idx < status_idx

        # Verify the switch command uses confluence, not jira
        switch_cmd = calls[switch_idx]
        assert "confluence" in switch_cmd
        assert "jira" not in switch_cmd

    def test_readback_mismatch_returns_degraded(self) -> None:
        wrong_status = (
            "✓ Authenticated\n"
            "  Site: other.atlassian.net\n"
            "  Email: wrong@example.com\n"
        )
        runner = _sequenced_runner([
            (_SWITCH_OK, "", 0),
            (wrong_status, "", 0),
        ])
        adapter = ConfluenceProviderAdapter(runner=runner)
        result = adapter.connection_status(
            OWNER, "alpha.atlassian.net|user@example.com",
        )
        assert result["state"] == STATE_DEGRADED
        assert result["error_code"] == CODE_SCOPE_DENIED


# =====================================================================
# 3. Four connections (two sites x two emails)
# =====================================================================

class TestFourConnections:
    """Two sites x two emails as four connections."""

    def test_four_distinct_refs(self) -> None:
        refs = set()
        for site in ["alpha.atlassian.net", "beta.atlassian.net"]:
            for email in ["a@example.com", "b@example.com"]:
                ref = ConfluenceProviderAdapter.connection_ref(site, email)
                refs.add(ref)
                assert "|" in ref
                assert site in ref
                assert email in ref
        assert len(refs) == 4


# =====================================================================
# 4. Recent blogs snapshot shape
# =====================================================================

class TestRecentBlogsSnapshot:
    """The ConfluenceWatchSource with query_kind=recent_blogs."""

    def test_recent_blogs_returns_entities(self) -> None:
        blog_data = [
            {
                "id": "blog-001",
                "title": "Release Notes Q3",
                "status": "current",
                "spaceId": "12345",
                "authorId": "karol@example.com",
                "createdAt": "2026-09-01T10:00:00Z",
                "version": {"createdAt": "2026-09-04T15:30:00Z"},
            },
            {
                "id": "blog-002",
                "title": "Sprint Review",
                "status": "current",
                "spaceId": "12345",
                "authorId": "alice@example.com",
                "createdAt": "2026-09-02T09:00:00Z",
                "version": {"createdAt": "2026-09-03T12:00:00Z"},
            },
        ]

        runner = _sequenced_runner([
            (_SWITCH_OK, "", 0),
            (_CONNECTED_STATUS, "", 0),
            (json.dumps(blog_data), "", 0),
        ])

        adapter = ConfluenceProviderAdapter(runner=runner)
        source = ConfluenceWatchSource(adapter=adapter)

        entities = source.snapshot(
            OWNER,
            query_kind="recent_blogs",
            query={
                "connection_ref": "alpha.atlassian.net|user@example.com",
                "space_id": "12345",
                "limit": 25,
            },
        )

        assert len(entities) == 2
        assert entities[0]["id"] == "blog-001"
        assert entities[0]["title"] == "Release Notes Q3"
        assert entities[0]["entity_type"] == "blog"
        assert entities[0]["status"] == "current"
        assert entities[1]["id"] == "blog-002"


# =====================================================================
# 5. Pages by ID snapshot
# =====================================================================

class TestPagesByIdSnapshot:
    """The ConfluenceWatchSource with query_kind=pages_by_id."""

    def test_pages_by_id_returns_entities(self) -> None:
        page_data = {
            "id": "page-123",
            "title": "Architecture Decision",
            "status": "current",
            "spaceId": "12345",
            "authorId": "karol@example.com",
            "createdAt": "2026-08-01T10:00:00Z",
            "version": {"createdAt": "2026-09-01T10:00:00Z"},
        }

        runner = _sequenced_runner([
            (_SWITCH_OK, "", 0),
            (_CONNECTED_STATUS, "", 0),
            (json.dumps(page_data), "", 0),
        ])

        adapter = ConfluenceProviderAdapter(runner=runner)
        source = ConfluenceWatchSource(adapter=adapter)

        entities = source.snapshot(
            OWNER,
            query_kind="pages_by_id",
            query={
                "connection_ref": "alpha.atlassian.net|user@example.com",
                "page_ids": ["page-123"],
            },
        )

        assert len(entities) == 1
        assert entities[0]["id"] == "page-123"
        assert entities[0]["title"] == "Architecture Decision"
        assert entities[0]["entity_type"] == "page"


# =====================================================================
# 6. Unsupported page listing returns typed error
# =====================================================================

class TestPageListingUnsupported:
    """A query asking for page listing gets a typed error, not empty."""

    def test_fetch_page_listing_returns_unsupported_by_cli(self) -> None:
        adapter = ConfluenceProviderAdapter(runner=_fake_runner())
        result = adapter.fetch_page_listing(
            OWNER, "alpha.atlassian.net|user@example.com",
        )
        assert result["error_code"] == CODE_UNSUPPORTED_BY_CLI
        assert "page list" in result["error_detail"]
        assert result["items"] == []

    def test_unsupported_query_kind_in_source(self) -> None:
        adapter = ConfluenceProviderAdapter(runner=_fake_runner())
        source = ConfluenceWatchSource(adapter=adapter)
        with pytest.raises(ValidationError, match="recent_blogs and pages_by_id"):
            source.snapshot(
                OWNER,
                query_kind="page_listing",
                query={
                    "connection_ref": "alpha.atlassian.net|user@example.com",
                },
            )


# =====================================================================
# 7. Templates
# =====================================================================

class TestConfluenceTemplates:
    """The two Confluence templates compile to valid WatchSpec@1 drafts."""

    def test_two_templates_exist(self) -> None:
        from holdspeak.confluence_templates import (
            CONFLUENCE_TEMPLATES,
            TEMPLATE_IDS,
        )
        assert len(CONFLUENCE_TEMPLATES) == 2
        assert TEMPLATE_IDS == {
            "watch.confluence.recent_blogs",
            "watch.confluence.pages_by_id",
        }

    def test_recent_blogs_template_compiles(self) -> None:
        from holdspeak.confluence_templates import compile as compile_template
        spec = compile_template(
            "watch.confluence.recent_blogs",
            {
                "connection_ref": "alpha.atlassian.net|user@example.com",
                "space_key": "GOV",
                "space_id": "12345",
            },
        )
        assert spec["schema"] == "WatchSpec@1"
        assert spec["provider"]["id"] == "confluence"
        assert spec["subject"]["kind"] == "recent_blogs"
        assert spec["subject"]["scope"]["connection_ref"] == "alpha.atlassian.net|user@example.com"
        assert spec["subject"]["scope"]["space_key"] == "GOV"

    def test_pages_by_id_template_compiles(self) -> None:
        from holdspeak.confluence_templates import compile as compile_template
        spec = compile_template(
            "watch.confluence.pages_by_id",
            {
                "connection_ref": "alpha.atlassian.net|user@example.com",
                "space_key": "GOV",
                "space_id": "12345",
                "page_ids": ["page-1", "page-2"],
            },
        )
        assert spec["schema"] == "WatchSpec@1"
        assert spec["provider"]["id"] == "confluence"
        assert spec["subject"]["kind"] == "pages_by_id"
        assert spec["subject"]["query"]["page_ids"] == ["page-1", "page-2"]

    def test_unknown_template_refused(self) -> None:
        from holdspeak.confluence_templates import compile as compile_template
        with pytest.raises(ValueError, match="Unknown template"):
            compile_template("watch.confluence.does_not_exist", {})


# =====================================================================
# 8. fetch_watch_snapshot dispatch for "confluence"
# =====================================================================

class TestFetchWatchSnapshotDispatch:
    """The fetch_watch_snapshot dispatcher routes to ConfluenceWatchSource."""

    def test_confluence_connector_id_dispatches(self) -> None:
        blog_data = [
            {"id": "b1", "title": "Post", "status": "current", "spaceId": "s1"},
        ]
        runner = _sequenced_runner([
            (_SWITCH_OK, "", 0),
            (_CONNECTED_STATUS, "", 0),
            (json.dumps(blog_data), "", 0),
        ])
        adapter = ConfluenceProviderAdapter(runner=runner)

        entities = fetch_watch_snapshot(
            OWNER,
            connector_id="confluence",
            query_kind="recent_blogs",
            query={
                "connection_ref": "alpha.atlassian.net|user@example.com",
                "space_id": "s1",
            },
            confluence_adapter=adapter,
        )
        assert len(entities) == 1
        assert entities[0]["id"] == "b1"


# =====================================================================
# 9. Door defaults for Confluence
# =====================================================================

class TestDoorDefaults:
    """The DOOR_DEFAULTS dict includes the Confluence defaults."""

    def test_confluence_door_defaults_present(self) -> None:
        from holdspeak.services.project_door_service import DOOR_DEFAULTS
        assert "confluence" in DOOR_DEFAULTS
        defaults = DOOR_DEFAULTS["confluence"]
        keys = [d["key"] for d in defaults]
        assert "recent_blogs" in keys
        assert "pages_by_id" in keys
        # recent_blogs on by default, pages_by_id off
        by_key = {d["key"]: d for d in defaults}
        assert by_key["recent_blogs"]["on"] is True
        assert by_key["pages_by_id"]["on"] is False


# =====================================================================
# 10. Manifest and provider ID
# =====================================================================

class TestManifest:
    """The Confluence provider manifest carries the right identity."""

    def test_provider_id(self) -> None:
        assert PROVIDER_ID == "confluence"

    def test_manifest_shape(self) -> None:
        adapter = ConfluenceProviderAdapter()
        m = adapter.manifest()
        assert m["provider_id"] == "confluence"
        assert m["transport"] == "connector_pack"
        assert m["capabilities"]["read"] is True
        assert m["capabilities"]["effect"] is False
        assert m["requires_cli"] == "acli"


# =====================================================================
# 11. Space discovery
# =====================================================================

class TestSpaceDiscovery:
    """discover(kind='spaces') returns normalized space items."""

    def test_discover_spaces(self) -> None:
        spaces = [
            {"id": "1", "key": "GOV", "name": "Governance", "type": "global", "status": "current"},
            {"id": "2", "key": "ENG", "name": "Engineering", "type": "global", "status": "current"},
        ]
        runner = _sequenced_runner([
            (_SWITCH_OK, "", 0),
            (_CONNECTED_STATUS, "", 0),
            (json.dumps(spaces), "", 0),
        ])
        adapter = ConfluenceProviderAdapter(runner=runner)
        result = adapter.discover(
            OWNER,
            "alpha.atlassian.net|user@example.com",
            kind="spaces",
        )
        assert result["state"] == DISCOVERY_READY
        assert len(result["items"]) == 2
        assert result["items"][0]["key"] == "GOV"
        assert result["items"][1]["key"] == "ENG"


# =====================================================================
# 12. Validate scope (space key)
# =====================================================================

class TestValidateScope:
    """validate_scope returns the space detail."""

    def test_valid_space_key(self) -> None:
        space = {"id": "1", "key": "GOV", "name": "Governance", "type": "global", "status": "current"}
        runner = _sequenced_runner([
            (_SWITCH_OK, "", 0),
            (_CONNECTED_STATUS, "", 0),
            (json.dumps(space), "", 0),
        ])
        adapter = ConfluenceProviderAdapter(runner=runner)
        result = adapter.validate_scope(
            OWNER,
            "alpha.atlassian.net|user@example.com",
            "GOV",
        )
        assert result["valid"] is True
        assert result["space"]["key"] == "GOV"


# =====================================================================
# 13. Connection ref normalization
# =====================================================================

class TestConnectionRef:
    """connection_ref follows the site|email pattern."""

    def test_bare_slug(self) -> None:
        ref = ConfluenceProviderAdapter.connection_ref("alpha", "user@example.com")
        assert ref == "alpha.atlassian.net|user@example.com"

    def test_full_site(self) -> None:
        ref = ConfluenceProviderAdapter.connection_ref(
            "alpha.atlassian.net", "user@example.com",
        )
        assert ref == "alpha.atlassian.net|user@example.com"

    def test_url_site(self) -> None:
        ref = ConfluenceProviderAdapter.connection_ref(
            "https://alpha.atlassian.net/", "User@Example.com",
        )
        assert ref == "alpha.atlassian.net|user@example.com"
