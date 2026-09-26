"""PHILO-7-01 DISCOVERY: the catalogue names his jobs.

The fence reads ONLY the real ``tools/list`` answer of a real hub (the
``MeetingWebServer`` app, over ``/api/mcp``): no source file, no repository
file, no import of the tool module. From that answer alone it maps each job
phrase to its tool and its argument path, and it checks that every id argument
of the slice's tools says where its value comes from, naming a tool that the
same answer lists.

What this proves: the words are present in the catalogue a client receives.
What it does NOT prove: that a model finds them (story 04's cold-context run
is that proof; the phase status names the risk).

"put a decision on my review list" is named here for the words only; story 02
pays the decision operation behind it.

This file imports no symbol the story adds, so it runs unchanged on a copy of
main (red: the catalogue has none of the job words).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

TOKEN = "philo7-01-discovery"

#: job phrase -> (tool, argument path: (argument, value or None)).
JOBS: dict[str, tuple[str, tuple[tuple[str, str | None], ...]]] = {
    "file a note into a zone": ("zone.file", (("directory_id", None), ("primitive_id", "note:"))),
    "find a note": ("desk.list", (("kind", "notes"),)),
    "read a note": ("desk.get", (("kind", "notes"), ("id", None))),
    "make a zone": ("desk.create", (("kind", "directories"), ("data", "name"))),
    "put a decision on my review list": ("desk.create", (("kind", "decisions"), ("data", "status=proposed"))),
    "list the notes in a zone": ("zone.list_members", (("directory_id", None),)),
    # PHILO-7-04 (the owner's review: "the decision is thin"): the reason
    # goes in the decision's context, not in its title.
    "the reason for a decision": ("desk.create", (("kind", "decisions"), ("data", "context_markdown"))),
}

#: The slice's tools whose id arguments must say where the value comes from.
SLICE_TOOLS = (
    "desk.list", "desk.get", "desk.create", "desk.update", "desk.delete", "desk.verb",
    "zone.file", "zone.unfile", "zone.list_members",
    "kb.add_member", "kb.remove_member", "kb.list_members",
)
_ID_ARGUMENT = re.compile(r"(^id$|_id$|^ref$)")
_FROM_TOOL = re.compile(r"\bfrom ([a-z_]+\.[a-z_.]+)")


@pytest.fixture(scope="module")
def catalogue(tmp_path_factory: pytest.TempPathFactory) -> list[dict[str, Any]]:
    """The real hub's ``tools/list`` answer, and nothing else."""
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    mp = pytest.MonkeyPatch()
    mp.setattr(db_core, "DEFAULT_DB_PATH", Path(tmp_path_factory.mktemp("discovery")) / "hub.db")
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
    # The job's sentence: from the phrase to the end of its sentence.
    sentence = description[description.index(phrase):].split(". ")[0]
    for argument, value in path:
        assert argument in properties, f"{tool_name} has no argument {argument!r}"
        if value is None:
            continue
        if argument == "kind":
            assert value in properties["kind"]["enum"], (tool_name, value)
            assert f"kind={value}" in sentence, f"{phrase!r}: the sentence does not name kind={value}: {sentence!r}"
        else:
            words = (sentence + " " + properties[argument].get("description", "").lower())
            assert value in words, f"{phrase!r}: {argument} does not name {value!r}: {words!r}"


@pytest.mark.parametrize("tool_name", SLICE_TOOLS)
def test_every_id_argument_names_where_its_value_comes_from(catalogue, tool_name) -> None:
    tools = _by_name(catalogue)
    properties = tools[tool_name]["inputSchema"]["properties"]
    id_arguments = [name for name in properties if _ID_ARGUMENT.search(name)]
    assert id_arguments or tool_name in {"desk.list", "desk.create"}, tool_name
    for argument in id_arguments:
        description = properties[argument].get("description", "")
        sources = _FROM_TOOL.findall(description)
        listed = "one of:" in description.lower()
        assert sources or listed, f"{tool_name}.{argument} does not say where its value comes from: {description!r}"
        for source in sources:
            assert source in tools, f"{tool_name}.{argument} names {source!r}, which tools/list does not list"
