"""The kinds PR #786 made findable are in the chunk index too: the meeting
summary and topics, sends, published updates.  Each row is made by its real
producer on a real hub (the rig of test_memory_findable_kinds)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, destination, room, send, send_body  # noqa: E402

from holdspeak.memory.retain import rebuild, sweep  # noqa: E402
from holdspeak.runtime import composition  # noqa: E402
from test_memory_findable_kinds import _meeting  # noqa: E402
from test_memory_review_795 import TextEngine  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _chunks(hub: Hub) -> dict[str, str]:
    """Every chunk of each source, joined (a summary and each topic are
    chunks of their own)."""
    joined: dict[str, list[str]] = {}
    with hub.db._connection() as conn:
        for row in conn.execute("SELECT source_ref,text FROM memory_chunks ORDER BY source_ref,ordinal"):
            joined.setdefault(str(row["source_ref"]), []).append(str(row["text"]))
    return {ref: "\n".join(texts) for ref, texts in joined.items()}


def test_the_summary_sends_and_updates_are_chunked_embedded_and_recalled(hub: Hub, tmp_path: Path) -> None:
    _meeting(hub)
    pid, update = room(hub, name="Atlas", body="The quillon cutover is on track.")
    dest = destination(hub, tmp_path / "out", name="Dana")
    sent = send(hub, send_body(hub, "inline", update, dest, "pcmd_send_dana"))
    assert sent.status_code == 200, sent.text
    send_ref = f"send:{sent.json()['send']['id']}"

    engine = TextEngine(near=("quillon", "zephyrine", "To Dana"))
    rebuild(hub.db, engine)
    hub.db.memory.set_embedder(engine)
    chunks = _chunks(hub)

    # The meeting: transcript, summary and topics.
    assert "zephyrine" in chunks["meeting:m-kestrel"] and "Obsidianware" in chunks["meeting:m-kestrel"]
    # The published update and the send he pressed.
    update_ref = next(ref for ref in chunks if ref.startswith("project_update:"))
    assert "quillon" in chunks[update_ref]
    assert "To Dana" in chunks[send_ref] and "quillon" not in chunks[send_ref]

    def vector_refs(**scope) -> list[str]:
        answer = hub.db.memory.search("a question with other words", limit=50, **scope)
        return [hit.source_ref for hit in answer.hits if hit.retrieval_origin == "vector"]

    assert vector_refs(kinds="project_update", project_id=pid) == [update_ref]
    assert vector_refs(kinds="send", project_id=pid) == [send_ref]
    assert vector_refs(kinds="meeting") == ["meeting:m-kestrel"]
    hit = hub.db.memory.search("a question with other words", kinds="send").hits[0]
    assert hit.project_id == pid and hit.title.startswith("Atlas")

    # A parked meeting leaves at once (read time), then from the index.
    hub.db.meetings.delete_meeting("m-kestrel")
    assert vector_refs(kinds="meeting") == []
    assert sweep(hub.db)["gone"] == 1
    assert "meeting:m-kestrel" not in _chunks(hub)
