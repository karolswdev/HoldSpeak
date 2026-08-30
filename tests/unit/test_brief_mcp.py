"""MCP delivery coverage for the persistent Monday Brief."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import resources, tools
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.monday_brief_service import MondayBriefService


OWNER = Principal(PrincipalKind.OWNER, "brief-mcp-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


@pytest.fixture
def mcp_db(db: Database, monkeypatch: pytest.MonkeyPatch) -> Database:
    monkeypatch.setattr(tools, "get_database", lambda: db)
    monkeypatch.setattr(tools, "get_observer", lambda: None)
    monkeypatch.setattr(resources, "get_database", lambda: db)
    return db


def test_monday_brief_tool_returns_persisted_brief_structure(mcp_db: Database) -> None:
    generated = tools.dispatch("monday_brief.generate", {}, OWNER)

    latest = tools.dispatch("monday_brief.get", {}, OWNER)

    # HS-150-03: the adapter may add person_sections or person_sections_state;
    # strip adapter-composed keys before comparing persisted structure.
    _ADAPTER_KEYS = {"person_sections", "person_sections_state"}
    persisted_keys = set(latest) - _ADAPTER_KEYS
    assert persisted_keys == {
        "id", "period_start", "period_end", "headline", "sections", "generated_at",
        "is_empty", "shelf",
    }
    assert set(latest["sections"]) == {"changed", "broke", "waiting", "decisions"}


def test_monday_brief_resource_returns_latest_brief(mcp_db: Database) -> None:
    generated = MondayBriefService(mcp_db).generate(OWNER)

    result = resources.read_resource("holdspeak://briefs/latest", OWNER)

    contents = result["contents"][0]
    assert contents["mimeType"] == "application/json"
    payload = json.loads(contents["text"])
    assert payload["id"] == generated.id
    assert payload["headline"] == generated.headline
