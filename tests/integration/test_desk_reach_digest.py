"""PG-DIRECTION DIR9 (one page, several items) and DIR10 (held items outside Programs).

On the Programs rig: a Program's core question, a Desk decision to review and
a call an agent asks to place go on ONE briefing page (``POST
/api/reach/packages`` with ``kind: digest``), in order. The page reads them
many times; each is decided alone through its own verb (the Program's
``program.decide``; the decision's Confirm; the call's Let it wait) and
settles to its line while the others stay open; the page's count follows.
A single decision or call is a page of its own (DIR10).

The face half replays the answers recorded here
(``web/src/briefing/__fixtures__/reach.digest.json``,
``reach.digest.answered.json`` and ``reach.decision.json``;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites them, else this test fences their shape).
"""
from __future__ import annotations

from tests.integration.program_rig import OWNER
from tests.integration.test_desk_reach import PAGE_FIXTURES, Clock, _fixture, _rig


def _decision(rig, ident: str = "dec-1") -> str:
    rig.db.desk_decisions.upsert(decision_id=ident, title="Keep the event log for 14 days", status="proposed",
                                 decision_markdown="Read receipts older than 14 days are pruned.")
    return f"decision:{ident}"


def _held_call(rig, ident: str = "pcall-held-1") -> str:
    from holdspeak.phone.service import default_phone_service

    default_phone_service(rig.db).store.save_call({
        "id": ident, "seq": 0, "direction": "to_phone", "reason": "The schema step needs your word",
        "context_digest": "sha256:0", "urgent": False, "state": "held", "created_at": "2026-11-01T12:00:00+00:00",
        "transport": "none", "decision": None})
    return f"phone-call:{ident}"


def test_one_page_carries_three_held_items_in_order_and_settles_each(tmp_path, monkeypatch) -> None:
    clock = Clock()
    rig, pid, client = _rig(tmp_path, monkeypatch, clock)
    core = next(row for row in client.get(f"/api/programs/{pid}").json()["your_turn_items"] if row["kind"] == "core")
    refs = [f"program:{pid}:{core['id']}", _decision(rig), _held_call(rig), "decision:gone"]
    made = client.post("/api/reach/packages", json={"refs": refs, "kind": "digest"})
    assert made.status_code == 201, made.text
    token = made.json()["token"]
    assert made.json()["refs"] == refs[:3]  # an item that does not wait is left out
    page = client.get(f"/api/b/{token}").json()
    _fixture(PAGE_FIXTURES / "reach.digest.json", page, tmp_path, token)
    assert page["package"]["kind"] == "digest" and page["package"]["head"] == "3 wait on you"
    assert page["package"]["open_words"] == "3 wait on you." and page["package"]["expires_words"] == "Expires in 12 h"
    assert [item["ref"] for item in page["items"]] == refs[:3]
    assert [item["state"] for item in page["items"]] == ["open"] * 3
    decision, call = page["items"][1], page["items"][2]
    assert (decision["kind_words"], decision["question"]) == ("Decision to review", "Confirm this decision?")
    assert decision["note"] == ["The decision: Keep the event log for 14 days.",
                                "Read receipts older than 14 days are pruned."]
    assert [(c["id"], c["label"]) for c in decision["choices"]] == [("confirm", "Confirm")]
    assert call["question"] == "Call you about the schema step needs your word?"
    assert [c["id"] for c in call["choices"]] == ["call_now", "let_wait"]

    # Each is decided alone, through its own verb; the others stay open.
    answered = client.post(f"/api/b/{token}/answer", json={"ref": refs[1], "choice": "confirm"})
    assert answered.status_code == 200, answered.text
    assert rig.db.desk_decisions.get("dec-1").status == "accepted"
    client.post(f"/api/b/{token}/answer", json={"ref": refs[2], "choice": "let_wait"})
    from holdspeak.phone.service import default_phone_service

    assert default_phone_service(rig.db).store.get_call("pcall-held-1")["state"] == "ended"
    page = client.get(f"/api/b/{token}").json()
    _fixture(PAGE_FIXTURES / "reach.digest.answered.json", page, tmp_path, token)
    assert [item["state"] for item in page["items"]] == ["open", "decided", "decided"]
    assert page["items"][1]["outcome"]["label"] == "Confirm" and page["package"]["open_words"] == "1 waits on you."
    again = client.post(f"/api/b/{token}/answer", json={"ref": refs[1], "choice": "confirm"})
    assert again.status_code == 409 and again.json()["code"] == "answered_already"
    # The Program's item is decided through program.decide with via=page.
    client.post(f"/api/b/{token}/answer", json={"ref": refs[0], "choice": "go_on"})
    lines = [row["line"] for row in client.get(f"/api/programs/{pid}").json()["checkpoints"]]
    assert any(line.startswith("Go on:") and "decided from the briefing page" in line for line in lines), lines
    assert client.get(f"/api/b/{token}").json()["package"]["open_words"] == "Nothing on this page waits on you."


def test_a_decision_and_a_held_call_are_each_a_page_of_their_own(tmp_path, monkeypatch) -> None:
    clock = Clock()
    rig, _pid, client = _rig(tmp_path, monkeypatch, clock)
    ref = _decision(rig, "dec-2")
    made = client.post("/api/reach/packages", json={"refs": [ref]})
    assert made.status_code == 201, made.text
    token = made.json()["token"]
    page = client.get(f"/api/b/{token}").json()
    _fixture(PAGE_FIXTURES / "reach.decision.json", page, tmp_path, token)
    assert page["package"]["kind"] == "item" and page["items"][0]["head"] == "A decision to review"
    # Answered on the desk first: the page says so and decides nothing.
    rig.db.desk_decisions.upsert(decision_id="dec-2", title="Keep the event log for 14 days", status="accepted")
    item = client.get(f"/api/b/{token}").json()["items"][0]
    assert item["state"] == "gone" and item["outcome"]["words"] == "Answered already on your desk."
    call = _held_call(rig, "pcall-held-2")
    made = client.post("/api/reach/packages", json={"refs": [call]})
    assert made.status_code == 201
    answer = client.post(f"/api/b/{made.json()['token']}/answer", json={"ref": call, "choice": "let_wait"})
    assert answer.status_code == 200 and answer.json()["item"]["state"] == "decided"


def test_a_digest_names_its_items_and_refuses_a_send(tmp_path, monkeypatch) -> None:
    clock = Clock()
    rig, pid, client = _rig(tmp_path, monkeypatch, clock)
    refused = client.post("/api/reach/packages", json={"refs": ["decision:none"], "kind": "digest"})
    assert refused.status_code == 409 and refused.json()["code"] == "not_waiting"
    sent = client.post("/api/reach/packages", json={"refs": [_decision(rig)], "kind": "digest", "send": "telegram"})
    assert sent.status_code == 400 and sent.json()["code"] == "send_unavailable"
    assert OWNER  # the owner made every page here (the rig's edge)
