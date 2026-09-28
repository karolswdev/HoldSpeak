"""PHILO-9-01 DISCOVERY: the catalogue names his project jobs (F12).

The fence reads ONLY the real ``tools/list`` answer of a real hub (the
``MeetingWebServer`` app, over ``/api/mcp``): no source file, no repository
file, no import of the tool module. From that answer alone it maps each of the
owner's job phrases to one tool and its argument path, checks that every id
argument of the Room's tools says where its value comes from (naming a tool
the same answer lists), and checks that no project tool says or implies that
the product sends, emails or posts the update (the Q0 ruling: delivery is his
act, by copy and confirm).

What this proves: the words are in the catalogue a client receives. What it
does not prove: that a model finds them (story 06's cold-context Codex run).

"mark it delivered" is story 02's criterion (Muad'Dib's ruling on PR #680,
2026-09-27, R4-2); it is pinned here as a strict expected failure, so
PHILO-9-02 turns it red-to-green when it lands
``project.mark_update_delivered`` and removes the mark.

This file imports no symbol the story adds, so it runs unchanged on an export
of main (red there: the catalogue has none of the job words, and no item tool).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

TOKEN = "philo9-01-discovery"

#: job phrase -> (tool, argument path: (argument, a word the path must name, or None)).
JOBS: dict[str, tuple[str, tuple[tuple[str, str | None], ...]]] = {
    "make a project": ("project.create", (("name", None),)),
    "add a milestone or a risk to a project": (
        "project.item.create", (("project_id", None), ("item_type", "milestone"), ("title", None), ("due_at", None)),
    ),
    "what needs me": ("desk.needs_you", ()),
    "draft my update": ("project.draft_update", (("project_id", None),)),
    "publish my update in the room": ("project.publish_update", (("update_id", None),)),
    "copy my update for delivery": ("project.list_updates", (("project_id", "body_md"),)),
}

#: The Room's tools whose id arguments must say where the value comes from.
ROOM_TOOLS = (
    "project.get", "project.get_room", "project.update", "project.archive", "project.restore",
    "project.link", "project.unlink", "project.open_review", "project.get_delta",
    "project.decide_proposal", "project.accept_review", "project.list_updates",
    "project.draft_update", "project.update_draft", "project.publish_update",
    "project.item.list", "project.item.create", "project.item.update", "project.item.transition",
    "project.resource.list", "project.resource.add", "project.resource.remove",
)
_ID_ARGUMENT = re.compile(r"(^id$|_id$)")
_FROM_TOOL = re.compile(r"\b(?:from|of an? [a-z ]+ from) ([a-z_]+\.[a-z_.]+)")
_SEND_WORDS = re.compile(r"\b(send|sends|sending|sent|email|emails|emailed|mail|mails|mailed|post|posts|posted|posting)\b")


@pytest.fixture(scope="module")
def catalogue(tmp_path_factory: pytest.TempPathFactory) -> list[dict[str, Any]]:
    """The real hub's ``tools/list`` answer, and nothing else."""
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    mp = pytest.MonkeyPatch()
    mp.setattr(db_core, "DEFAULT_DB_PATH", Path(tmp_path_factory.mktemp("discovery9")) / "hub.db")
    reset_database()
    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                                get_state=MagicMock(return_value={})),
            auth_token=TOKEN,
        )
        client = TestClient(server.app, client=("127.0.0.1", 50000))
        client.headers.update({"Authorization": f"Bearer {TOKEN}"})
        resp = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        assert resp.status_code == 200, resp.text
        return resp.json()["result"]["tools"]
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))
        mp.undo()


def _by_name(catalogue: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {tool["name"]: tool for tool in catalogue}


@pytest.mark.parametrize("phrase", sorted(JOBS))
def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
    tool_name, path = JOBS[phrase]
    naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
    assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
    tool = _by_name(catalogue)[tool_name]
    description = tool["description"].lower()
    properties = tool["inputSchema"]["properties"]
    for argument, value in path:
        assert argument in properties, f"{tool_name} has no argument {argument!r}"
        if value is None:
            continue
        words = description + " " + properties[argument].get("description", "").lower()
        assert value in words or value in (properties[argument].get("enum") or []), (phrase, argument, value)


@pytest.mark.xfail(strict=True, reason="PHILO-9-02 lands project.mark_update_delivered (R4-2)")
def test_mark_it_delivered_maps_to_its_tool(catalogue) -> None:
    naming = [t["name"] for t in catalogue if "mark it delivered" in t.get("description", "").lower()]
    assert naming == ["project.mark_update_delivered"]


@pytest.mark.parametrize("tool_name", ROOM_TOOLS)
def test_every_id_argument_names_where_its_value_comes_from(catalogue, tool_name) -> None:
    tools = _by_name(catalogue)
    properties = tools[tool_name]["inputSchema"]["properties"]
    id_arguments = [name for name in properties if _ID_ARGUMENT.search(name) and name != "command_id"]
    assert id_arguments, tool_name
    for argument in id_arguments:
        description = properties[argument].get("description", "")
        sources = [s.rstrip(".") for s in _FROM_TOOL.findall(description)]
        assert sources, f"{tool_name}.{argument} does not say where its value comes from: {description!r}"
        assert all(source in tools for source in sources), (tool_name, argument, sources)


def test_no_project_tool_says_the_product_sends_the_update(catalogue) -> None:
    offenders = []
    for tool in catalogue:
        if not (tool["name"].startswith("project.") or tool["name"] == "desk.needs_you"):
            continue
        texts = [tool.get("description", "")] + [
            spec.get("description", "") for spec in tool["inputSchema"].get("properties", {}).values()]
        for text in texts:
            lowered = text.lower()
            if "update" in lowered and _SEND_WORDS.search(lowered):
                offenders.append((tool["name"], text))
    assert offenders == [], offenders
