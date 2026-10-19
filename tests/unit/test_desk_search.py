"""Betterment Q3 (Search asks): the hub half of ⌘K's MEMORY rows.

`/api/memory/search` answers plain text: no markdown marks, no empty `[]`,
the server's `<mark>` grammar kept; and a thread that holds only a question
(an Ask with no answer) is not a hit. The answer for the freeze question is
recorded for the palette's face test (`memory-search.freeze-question`)."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402
from holdspeak.services.memory_faces import plain_snippet  # noqa: E402
from tests.integration import test_desk_agents_wire as wire  # noqa: E402

pytestmark = pytest.mark.timeout(240)

WIRE_DIR = REPO / "web" / "src" / "test" / "wire"
QUESTION = "what did we decide about the freeze?"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database

    monkeypatch.setattr(wire, "WIRE_DIR", WIRE_DIR)
    yield seeds._boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _thread(hub: Any, question: str, answer: str | None) -> str:
    threads = hub.db.threads
    thread = threads.create_thread(title=question)
    asked = threads.append_message(thread.id, role="user")
    threads.append_part(asked.id, kind="text", text=question)
    threads.complete_message(asked.id)
    if answer is not None:
        said = threads.append_message(thread.id, role="assistant", parent_id=asked.id)
        threads.append_part(said.id, kind="text", text=answer)
        threads.complete_message(said.id)
    return thread.id


def _seed(hub: Any) -> dict[str, str]:
    seeds._seed_honest_faces(hub)
    note = hub.client.post("/api/notes", json={
        "title": "Freeze plan",
        "body_markdown": "## Freeze\n- **Freeze** the old ledger on Nov 5 []\n- see [the runbook](https://example.invalid/rb)",
    })
    assert note.status_code in (200, 201), note.text
    return {
        "unanswered": _thread(hub, "When is the freeze?", None),
        "answered": _thread(hub, "Why the freeze?", "We **freeze** the old ledger on Nov 5 to stop dual-write drift."),
    }


def test_snippets_are_plain_words() -> None:
    assert plain_snippet("you <mark>owe</mark> Mira: - **Feedback on her doc** — due Friday []") == (
        "you <mark>owe</mark> Mira: Feedback on her doc — due Friday")
    assert plain_snippet("a [runbook](https://x.invalid) and `code`") == "a runbook and code"
    assert plain_snippet("kept [redacted] words") == "kept [redacted] words"
    assert plain_snippet("Dual-write is stable - cutover") == "Dual-write is stable - cutover"


def test_search_answers_plain_text_and_no_unanswered_thread(hub: Any, tmp_path: Path) -> None:
    ids = _seed(hub)
    for query in ("freeze", QUESTION):
        response = hub.client.get("/api/memory/search", params={"query": query, "limit": "12"})
        assert response.status_code == 200, response.text
        hits = response.json()["hits"]
        refs = [str(hit.get("source_ref") or "") for hit in hits]
        assert hits, (query, hits)
        assert not any(ref.split("#", 1)[0] == f"thread:{ids['unanswered']}" for ref in refs), (query, refs)
        for hit in hits:
            for field in ("snippet", "title"):
                text = str(hit.get(field) or "")
                assert "**" not in text and "[]" not in text and "](" not in text, (query, field, text)
    # The question itself finds the answered thread and the note (the face's recording).
    answer = hub.client.get("/api/memory/search", params={"query": QUESTION, "limit": "12"}).json()
    refs = [str(hit.get("source_ref") or "").split("#", 1)[0] for hit in answer["hits"]]
    assert f"thread:{ids['answered']}" in refs, refs
    wire._fence("memory-search.freeze-question", answer, tmp_path, str(hub.client.base_url),
                by="tests/unit/test_desk_search.py")
