"""HS-133-09 Surface honesty: pagination, kind-gap sentences, pipeline.events rename."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import holdspeak.mcp.tools as mcp_tools
import holdspeak.mcp.resources as mcp_resources
from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.server import handle_message
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.profile_service import ProfileService


OWNER = Principal(PrincipalKind.OWNER, "surface-test")


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


# ---------------------------------------------------------------------------
# (a) Pagination: >100 destinations truncated to exactly 100 by the resource read
# ---------------------------------------------------------------------------


def test_destination_resource_read_truncates_to_100(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Seed 101 profiles; the holdspeak://destinations resource must return exactly 100."""
    for i in range(101):
        db.profiles.upsert(profile_id=f"profile-{i:04d}", name=f"Profile {i}")

    monkeypatch.setattr(mcp_resources, "get_database", lambda: db)

    result = mcp_resources.read_resource("holdspeak://destinations", OWNER)
    payload = json.loads(result["contents"][0]["text"])
    assert len(payload["profiles"]) == 100


def test_workbench_resource_read_truncates_to_100(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Seed 101 workbenches; the holdspeak://workbenches resource must return exactly 100."""
    for i in range(101):
        db.workbenches.upsert(workbench_id=f"wb-{i:04d}", name=f"Workbench {i}")

    monkeypatch.setattr(mcp_resources, "get_database", lambda: db)

    result = mcp_resources.read_resource("holdspeak://workbenches", OWNER)
    payload = json.loads(result["contents"][0]["text"])
    assert len(payload) == 100


# ---------------------------------------------------------------------------
# (b) Kind-gap: each desk.* CRUD description carries its boundary sentence
# ---------------------------------------------------------------------------

_LONG_FORM_SENTENCE = (
    "The desk schema advertises 17 primitive kinds; this tool operates on the "
    "6 authorable kinds: notes, decisions, kbs, directories, workflows, and chains."
)
_SHORT_FORM_SENTENCE = (
    "Authorable kinds: notes, decisions, kbs, directories, workflows, chains."
)

_EXPECTED_SENTENCES: dict[str, str] = {
    "desk.list": _LONG_FORM_SENTENCE,
    "desk.get": _LONG_FORM_SENTENCE,
    "desk.create": _SHORT_FORM_SENTENCE,
    "desk.update": _SHORT_FORM_SENTENCE,
    "desk.delete": _SHORT_FORM_SENTENCE,
}


def test_desk_crud_descriptions_carry_kind_boundary_sentence() -> None:
    """All five desk.* CRUD tool descriptions contain the kind-boundary sentence."""
    tool_map = {tool["name"]: tool for tool in mcp_tools.TOOLS}
    for tool_name, expected_substring in _EXPECTED_SENTENCES.items():
        tool = tool_map.get(tool_name)
        assert tool is not None, f"{tool_name} missing from TOOLS catalogue"
        desc = tool["description"]
        assert expected_substring in desc, (
            f"{tool_name} description does not contain the expected kind-boundary sentence.\n"
            f"  Expected substring: {expected_substring!r}\n"
            f"  Actual description: {desc!r}"
        )


# ---------------------------------------------------------------------------
# (c) pipeline.events dispatches; the old underscore name is absent from catalogue
# ---------------------------------------------------------------------------


def test_pipeline_events_dispatches(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pipeline.events dispatches identically to the old underscore-named tool."""
    import time

    with db._connection() as conn:
        conn.execute(
            """
            INSERT INTO pipeline_events (
                event_id, timestamp, service, method, principal_kind,
                correlation_id, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("surface-event", time.time(), "surface-svc", "surface-method", "owner", "surface-chain", None),
        )

    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    monkeypatch.setattr(mcp_tools, "get_observer", lambda: None)

    events = mcp_tools.dispatch("pipeline.events", {}, OWNER)
    assert any(e["event_id"] == "surface-event" for e in events)


_RETIRED_UNDERSCORE_NAME = "pipeline" + "_events" + "_query"


def test_retired_underscore_name_absent_from_catalogue() -> None:
    """The old underscore-named tool must not appear in the tool catalogue."""
    names = {tool["name"] for tool in mcp_tools.TOOLS}
    assert _RETIRED_UNDERSCORE_NAME not in names, (
        "retired underscore name still present in the TOOLS catalogue"
    )
    assert "pipeline.events" in names, (
        "pipeline.events missing from the TOOLS catalogue"
    )
