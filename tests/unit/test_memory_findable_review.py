"""Astra's findings on PR #786, each fenced through the real producers.

1. A parked meeting came back through its action items: recall still drew
   the meeting and both actions. Parked sources stay out of search, recall
   and the relationship walk.
3. A CC recipient of a send was forgotten: `quartzcc` found nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_memory_findable_kinds import _meeting_with_actions, _recall, _refs, _search  # noqa: E402
from test_philo10_email_channel import hub, press, ready, send, store, wire  # noqa: E402,F401

from holdspeak.grounding import hydrate_refs_detailed  # noqa: E402


def test_a_parked_meeting_and_its_actions_stay_out_of_memory(hub: Any) -> None:
    _meeting_with_actions(hub)
    before = _recall(hub, "quillfeather rollout")
    assert [row["action_item_id"] for row in before["owed"]] == ["act-open"]
    assert [row["source_ref"] for row in before["meetings"]] == ["meeting:m-rollout"]

    # The real park: the owner's Delete on the meeting.
    parked = hub.client.delete("/api/meetings/m-rollout")
    assert parked.status_code == 200, parked.text
    with hub.db._connection() as conn:
        assert conn.execute("SELECT parked FROM meetings WHERE id='m-rollout'").fetchone()[0] == 1

    for query in ("quillfeather", "rollout", "quillfeather rollout planning"):
        assert _refs(hub, query) == [], query
        after = _recall(hub, query)
        assert after["owed"] == [] and after["meetings"] == [] and after["also"] == [], query
        assert after["remembered"] == 0
    assert _recall(hub, "quillfeather", filter="commitments")["owed"] == []
    recent = hub.client.get("/api/memory/recall", params={"recent": "true"}).json()
    assert recent["meetings"] == [] and recent["also"] == [] and recent["owed"] == []
    # The relevance pass Ask runs: nothing from the parked meeting.
    asked = hydrate_refs_detailed(hub.db, [], [], "summary", query="quillfeather rollout", include_memory=True)
    assert asked.blocks == [] and asked.unknown == []

    restored = hub.client.post("/api/meetings/m-rollout/restore")
    assert restored.status_code == 200, restored.text
    assert [row["action_item_id"] for row in _recall(hub, "quillfeather")["owed"]] == ["act-open"]


def test_a_cc_recipient_finds_the_send(hub: Any, wire: Any) -> None:
    update, dest = ready(hub, cc=["quartzcc@example.com"])
    answer = send(hub, press(hub, "inline", update, dest, "pcmd_cc"))
    assert answer.status_code == 200, answer.text
    send_id = answer.json()["send"]["id"]
    assert answer.json()["send"]["state"] == "sent" and len(wire.requests) == 1

    hits = _search(hub, "quartzcc", kind="send")
    assert [hit["source_ref"] for hit in hits] == [f"send:{send_id}"]
    assert "quartzcc@example.com" in hits[0]["snippet"]
    assert _refs(hub, "priya", kind="send") == [f"send:{send_id}"]  # To, as before

    asked = hydrate_refs_detailed(hub.db, [], [], "summary", query="quartzcc", include_memory=True)
    block = next(b for b in asked.blocks if b.kind == "send")
    assert "Cc: " in block.text and "quartzcc@example.com" in block.text
    assert asked.unknown == []
