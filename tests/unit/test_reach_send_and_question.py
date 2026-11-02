"""PG-DIRECTION DIR10, the last held kinds (DIRECTION-2026-10-31 §3, §10).

Through the REAL hub on an isolated HOME (the PHILO-10 send rig):

- a prepared send (``send:<id>``, made by the real ``channel.prepare`` to a
  FILE destination) is a briefing page whose preview names the destination
  and the lines it sends; **Send** on the page runs the real ``channel.send``
  (the file is written); it is the page only: a Telegram tap is refused and
  its Telegram message carries no Send button;
- a desk agent's question outside a Program (``coder:<agent>:<session>``) is
  a page answered with his words, typed through the responder's delivery path
  (the pane is the process edge, faked here); a permission prompt stays on the
  desk;
- a gate hold stays on the desk (IMP5 supersedes §3's "the page only").
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, destination, files, prepare, room  # noqa: E402
from tests.integration.test_desk_reach import PAGE_FIXTURES, _fixture  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _page(hub: Hub, ref: str) -> tuple[str, dict[str, Any]]:
    made = hub.client.post("/api/reach/packages", json={"refs": [ref]})
    assert made.status_code == 201, made.text
    token = made.json()["token"]
    page = hub.client.get(f"/api/b/{token}")
    assert page.status_code == 200, page.text
    return token, page.json()


def test_a_prepared_send_is_decided_on_its_page_only(hub: Hub, tmp_path: Path) -> None:
    from holdspeak.services.briefing_service import BriefingService
    from holdspeak.services.telegram_reach import choice_buttons

    _pid, update = room(hub)
    folder = tmp_path / "out"
    dest = destination(hub, folder)
    send_id = prepare(hub, update, dest)["send"]["id"]
    ref = f"send:{send_id}"
    token, page = _page(hub, ref)
    _fixture(PAGE_FIXTURES / "reach.send.json", page, tmp_path, token)
    item = page["items"][0]
    assert item["kind_words"] == "Ready to send" and item["page_only"] is True
    assert item["question"] == "Send it to Team folder?"
    assert item["preview"]["destination"] == "Team folder"
    assert any("on track" in line for line in item["preview"]["lines"]), item["preview"]
    assert [c["id"] for c in item["choices"]] == ["send", "discard"]
    # Never a Telegram tap: no Send button there, and a tap is refused by name.
    assert [row["text"] for row in choice_buttons("pkg", item)[0]] == ["Later ▾"]
    briefing = BriefingService(hub.db)
    package = briefing.store.by_hash(__import__("holdspeak.services.briefing_service", fromlist=["token_hash"])
                                     .token_hash(token))
    with pytest.raises(Exception) as refused:
        briefing.answer_package(package["id"], ref, "send", via="telegram")
    assert getattr(refused.value, "code", "") == "page_only"
    assert files(folder) == []
    # On the page: the real channel.send writes the file.
    sent = hub.client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "send"})
    assert sent.status_code == 200, sent.text
    _fixture(PAGE_FIXTURES / "reach.send.sent.json", sent.json(), tmp_path, token)
    assert sent.json()["item"]["state"] == "decided"
    assert len(files(folder)) == 1
    assert hub.db.channel_sends.get(send_id)["state"] == "sent"


class _Responder:
    """The responder's reads and its pane delivery (the process edge)."""

    def __init__(self, approve: bool = False) -> None:
        self.typed: list[tuple[str, str]] = []
        self.session = SimpleNamespace(
            agent="claude", session_id="s-1", question="Which branch should I base the fix on?",
            wait_started_at="2026-11-01T12:00:00+00:00", updated_at="2026-11-01T12:00:00+00:00",
            state="waiting", wait_kind="approve" if approve else "answer", wait_id="w-1")
        self.expected: list = []

    def _sessions(self) -> list[Any]:
        return [self.session]

    @staticmethod
    def _key(session: Any) -> str:
        return f"{session.agent}:{session.session_id}"

    def _launch_for(self, key: str) -> dict[str, Any]:
        return {"launch_id": "L-1", "session_key": key, "title": "Fix the flaky test", "state": "working"}

    def _deliver(self, launch: Any, key: str, agent: str, text: str, *, submit: bool = True,
                 expected_wait_id: Any = None) -> dict[str, Any]:
        # The steering chokepoint reads the wait right before it types
        # (``coder_steering.deliver``): a changed wait types nothing.
        from holdspeak.coder_steering import wait_episode

        self.expected.append(expected_wait_id)
        if expected_wait_id is not None and expected_wait_id != wait_episode(self.session):
            return {"status": "wait_not_current"}
        self.typed.append((key, text))
        return {"status": "delivered"}


def test_a_desk_agents_question_is_answered_with_his_words(hub: Hub, monkeypatch: pytest.MonkeyPatch,
                                                         tmp_path: Path) -> None:
    from holdspeak.services import briefing_sources

    responder = _Responder()
    monkeypatch.setattr(briefing_sources.CoderQuestionSource, "_responder", lambda self: responder)
    monkeypatch.setattr("holdspeak.agent_context.models.is_blocked", lambda session: True)
    monkeypatch.setattr("holdspeak.agent_context.models.wait_kind", lambda session: session.wait_kind)
    ref = "coder:claude:s-1"
    token, page = _page(hub, ref)
    _fixture(PAGE_FIXTURES / "reach.question.json", page, tmp_path, token)
    item = page["items"][0]
    assert item["kind"] == "answer" and item["head"] == "Claude Code · Fix the flaky test"
    assert item["question"] == "Which branch should I base the fix on?"
    assert item["text"]["label"] == "Your answer" and item["choices"] == []
    answered = hub.client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "answer", "reason": "Base it on main."})
    assert answered.status_code == 200, answered.text
    assert answered.json()["item"]["state"] == "decided"
    _fixture(PAGE_FIXTURES / "reach.question.answered.json", answered.json(), tmp_path, token)
    assert responder.typed == [("claude:s-1", "Base it on main.")]


def test_a_permission_prompt_and_a_gate_hold_stay_on_the_desk(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import briefing_sources

    responder = _Responder(approve=True)
    monkeypatch.setattr(briefing_sources.CoderQuestionSource, "_responder", lambda self: responder)
    monkeypatch.setattr("holdspeak.agent_context.models.is_blocked", lambda session: True)
    monkeypatch.setattr("holdspeak.agent_context.models.wait_kind", lambda session: session.wait_kind)
    for ref in ("coder:claude:s-1", "gate:prop-1"):
        made = hub.client.post("/api/reach/packages", json={"refs": [ref]})
        assert made.status_code == 409, (ref, made.text)



def test_a_remote_answer_is_bound_to_the_wait_it_answers(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    """Astra's post-merge check (2026-11-01): the page's answer was typed
    with no wait bound, so a pane that turned into a permission prompt (or
    another question) after the page was made could take it. The answer
    carries the wait the page showed; a changed wait types nothing."""
    from holdspeak.services import briefing_sources
    from holdspeak.services.briefing_service import WAIT_CHANGED

    responder = _Responder()
    monkeypatch.setattr(briefing_sources.CoderQuestionSource, "_responder", lambda self: responder)
    monkeypatch.setattr("holdspeak.agent_context.models.is_blocked", lambda session: True)
    monkeypatch.setattr("holdspeak.agent_context.models.wait_kind", lambda session: session.wait_kind)
    ref = "coder:claude:s-1"
    token, _page_body = _page(hub, ref)
    # Another wait with the same words (the agent asked again): not the
    # wait the page showed.
    responder.session.wait_id = "w-2"
    late = hub.client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "answer", "reason": "Yes."})
    assert late.status_code == 409 and WAIT_CHANGED in late.text
    assert responder.typed == []
    # Another question: the page's item is gone ("Answered already").
    responder.session.question = "Shall I also delete the old branch?"
    gone = hub.client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "answer", "reason": "Yes."})
    assert gone.status_code == 409 and responder.typed == []
    # The wait changes between the check and the typing: the chokepoint refuses.
    responder.session.wait_id = "w-1"
    responder.session.question = "Which branch should I base the fix on?"
    token, _page_body = _page(hub, ref)
    assert responder.typed == []
    real_held = briefing_sources.CoderQuestionSource.held

    calls = {"n": 0}

    def held_then_change(self, ref_):
        found = real_held(self, ref_)
        calls["n"] += 1
        if calls["n"] == 2:  # the answer's own read: right after it, the pane changes
            responder.session.wait_kind = "approve"  # a permission prompt now
        return found

    monkeypatch.setattr(briefing_sources.CoderQuestionSource, "held", held_then_change)
    raced = hub.client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "answer", "reason": "y"})
    assert raced.status_code == 409 and WAIT_CHANGED in raced.text
    assert responder.typed == [] and responder.expected[-1] == "w-1|answer"
