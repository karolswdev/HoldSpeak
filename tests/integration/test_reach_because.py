"""IMP5 "Knowledge escalates, authority never does" (BROCREW-IMPORT-2026-11-01.md).

Every held item that travels to a page or Telegram records its ``because``:
why it may travel (a question, a choice among offered presses, a to-do),
and the ladder's rule when the ladder sent it; a permission (a gate hold, a
gate approval) never becomes a package. A late or bad answer is refused in
one of four honest ways, each with his words: not pending ("Answered at
21:46 from the desk"), not offered, not usable (the item stays live), not
kept (it still waits).
"""
from __future__ import annotations

import re

import pytest

from holdspeak.services import briefing_service as briefing_module
from holdspeak.services.briefing_service import (
    AUTHORITY_KINDS, BRIEFABLE, NOT_KEPT, NOT_OFFERED, NOT_USABLE, BriefingRefused,
)
from tests.integration.program_rig import OWNER
from tests.integration.test_desk_reach import Clock, _rig


def _core_ref(client, pid: str) -> str:
    item = next(row for row in client.get(f"/api/programs/{pid}").json()["your_turn_items"] if row["kind"] == "core")
    return f"program:{pid}:{item['id']}"


def test_a_page_says_why_the_item_travelled(tmp_path, monkeypatch) -> None:
    rig, pid, client = _rig(tmp_path, monkeypatch, Clock())
    made = client.post("/api/reach/packages", json={"refs": [_core_ref(client, pid)]}).json()
    item = client.get(f"/api/b/{made['token']}").json()["items"][0]
    assert item["because"] == {"rule": "kind", "kind": "core", "words": "a question"}


def test_a_permission_never_becomes_a_package(tmp_path, monkeypatch) -> None:
    assert not (BRIEFABLE & AUTHORITY_KINDS)  # the fence: no permission kind is briefable
    rig, pid, client = _rig(tmp_path, monkeypatch, Clock())
    refused = client.post("/api/reach/packages", json={"refs": ["gate:toolu_1"]})
    assert refused.status_code == 409 and refused.json()["code"] == "authority_stays"
    # A Program item of a permission kind is refused too, whatever lists it.
    turn = rig.service._turn

    def with_a_gate(program, steps, **kw):
        return [*turn(program, steps, **kw), {"id": "s:gate", "kind": "gate_approval", "step_id": "", "choices": ["allow"]}]

    monkeypatch.setattr(rig.service, "_turn", with_a_gate)
    briefing = briefing_module.default_briefing_service()
    with pytest.raises(BriefingRefused) as stays:
        briefing.make(OWNER, [f"program:{pid}:s:gate"])
    assert stays.value.code == "authority_stays"


def test_the_four_honest_refusals_of_a_late_or_bad_answer(tmp_path, monkeypatch) -> None:
    rig, pid, client = _rig(tmp_path, monkeypatch, Clock())
    ref = _core_ref(client, pid)
    token = client.post("/api/reach/packages", json={"refs": [ref]}).json()["token"]

    # Not usable: no choice named; the item stays live.
    blank = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": ""})
    assert blank.status_code == 400 and blank.json()["code"] == "not_usable" and blank.json()["detail"] == NOT_USABLE
    # Not offered: a choice the page did not offer.
    other = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "merge"})
    assert other.status_code == 400 and other.json()["code"] == "not_offered" and other.json()["detail"] == NOT_OFFERED
    # Not kept: Later could not be kept; it still waits.
    reach = briefing_module.default_briefing_service().reach()

    def broken(*_a, **_kw):
        raise RuntimeError("the store is full")

    monkeypatch.setattr(reach, "later", broken)
    later = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "later", "later": "in_1h"})
    assert later.status_code == 409 and later.json()["code"] == "not_kept" and later.json()["detail"] == NOT_KEPT
    assert client.get(f"/api/b/{token}").json()["items"][0]["state"] == "open"
    # Not pending: answered on the desk first; then the page says when and where.
    rig.service.decide(OWNER, pid, rig.step(pid, 1)["id"], kind="core", choice="go_on")
    late = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "go_on"})
    assert late.status_code == 409 and late.json()["code"] == "answered_already"
    assert re.fullmatch(r"Answered at \d\d:\d\d from the desk", late.json()["detail"]), late.json()


def test_a_page_answer_then_another_says_from_the_briefing_page(tmp_path, monkeypatch) -> None:
    rig, pid, client = _rig(tmp_path, monkeypatch, Clock())
    ref = _core_ref(client, pid)
    token = client.post("/api/reach/packages", json={"refs": [ref]}).json()["token"]
    assert client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "go_on"}).status_code == 200
    again = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "park"})
    assert re.fullmatch(r"Answered at \d\d:\d\d from the briefing page", again.json()["detail"]), again.json()
    assert again.json()["refusal"] == "not_pending"
