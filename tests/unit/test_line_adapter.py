"""The Line (2026-10-29): the adapter answers with ai-phone's result codes for
every case of the fake ai-phone's table (``tests/fixtures/fake_ai_phone.py``),
so ``REASONS`` and the 409 reasons of POST /api/calls/place do not change.

The node here is scripted on the hub's own wire (``LineHub``): it answers each
command as a node does. The real node on the fake baresip is
``test_line_node.py``."""
from __future__ import annotations

import asyncio
from typing import Any

from holdspeak.calls import aiphone
from holdspeak.line.adapter import Line
from holdspeak.line.hub import LineHub

NODE = "this-mac"


async def _node(hub: LineHub, answers: dict[str, dict[str, Any]], stop: asyncio.Event) -> None:
    """A scripted node: its hello, then each command answered by ``answers[op]``."""
    hub.hello(NODE, lines=[{"id": "main", "kind": "sip", "state": "listening"}])
    after = 0
    while not stop.is_set():
        for command in await hub.next(NODE, after=after, wait=0.2):
            after = command["id"]
            reply = dict(answers.get(command["op"]) or {})
            hub.post_events(NODE, [{"seq": 1000 + after, "kind": "result", "cmd": command["id"],
                                    "call_id": command.get("call_id", ""), **reply}])


def _line(hub: LineHub, tmp_path, limit: int = 20) -> Line:
    return Line(NODE, hub=hub, daily_limit=lambda: limit, count_path=tmp_path / "placed.json")


def test_listen_says_incoming_heard_ended_and_timeout_with_ai_phones_codes(tmp_path) -> None:
    async def walk() -> list:
        hub = LineHub()
        line = _line(hub, tmp_path)
        hub.hello(NODE, lines=[])
        hub.post_events(NODE, [{"seq": 1, "kind": "incoming", "call_id": "c1", "remote": "sip:+12125550142@sip.telnyx.com"},
                               {"seq": 2, "kind": "heard", "call_id": "c1", "text": "Blue heron."},
                               {"seq": 2, "kind": "heard", "call_id": "c1", "text": "a repeat is taken once"}])
        incoming = await line.listen(timeout=2)
        heard = await line.listen(call_id="c1", timeout=2)
        quiet = await line.listen(call_id="c1", timeout=1)
        hub.post_events(NODE, [{"seq": 3, "kind": "ended", "call_id": "c1", "outcome": "completed", "ended_by": "them"}])
        ended = await line.listen(call_id="c1", timeout=2)
        gone = await line.say("Anyone there?", call_id="c1")
        unknown = await line.listen(call_id="nope", timeout=1)
        return [incoming, heard, quiet, ended, gone, unknown]

    incoming, heard, quiet, ended, gone, unknown = asyncio.run(walk())
    assert incoming.ok and incoming.kind == "incoming" and incoming.data["remote"].startswith("sip:+1212")
    assert incoming.data["line"] == "main" and incoming.data["call_id"] == "c1"
    assert heard.ok and heard.kind == "heard" and heard.data["text"] == "Blue heron."
    assert quiet.code == aiphone.LISTEN_TIMEOUT and quiet.kind == "timeout" and quiet.reason == "timeout"
    assert ended.ok and ended.kind == "ended" and ended.data["ended_by"] == "them" and ended.data["outcome"] == "completed"
    assert gone.code == aiphone.NO_CALL and "has ended" in gone.error and gone.reason == "no_call"
    assert unknown.code == aiphone.NO_CALL


def test_say_hangup_and_call_answer_like_ai_phone(tmp_path) -> None:
    async def walk(answers: dict) -> list:
        hub, stop = LineHub(), asyncio.Event()
        task = asyncio.ensure_future(_node(hub, answers, stop))
        await asyncio.sleep(0.05)
        hub.post_events(NODE, [{"seq": 1, "kind": "incoming", "call_id": "c1", "remote": "sip:x@y"}])
        line = _line(hub, tmp_path)
        out = [await line.say("Hello.", call_id="c1"), await line.hangup(say="Goodbye.", call_id="c1"),
               await line.call("+12125550142", ring_seconds=2)]
        stop.set()
        await task
        return out

    said, hung, placed = asyncio.run(walk({"say": {"result": "said"}, "hangup": {"result": "hung_up"},
                                           "call": {"outcome": "answered", "call_id": "c2"}}))
    assert said.ok and said.data["result"] == "said"
    assert hung.ok and hung.data["ended_by"] == "hangup_command" and hung.data["outcome"] == "completed"
    assert placed.ok and placed.data["outcome"] == "answered" and placed.data["mode"] == "relay"
    assert placed.events == [{"event": "created", "call_id": "c2"}]
    interrupted = asyncio.run(walk({"say": {"result": "interrupted"}, "hangup": {"result": "no_call"},
                                    "call": {"outcome": "busy"}}))
    assert interrupted[0].ok and interrupted[0].data["result"] == "interrupted"
    assert interrupted[1].code == aiphone.NO_CALL
    assert interrupted[2].code == aiphone.BUSY and interrupted[2].reason == "busy"


def test_every_failed_call_is_ai_phones_code_and_reason(tmp_path) -> None:
    cases = {"no_answer": (aiphone.NO_ANSWER, "no_answer"), "rejected": (aiphone.REJECTED, "rejected"),
             "busy": (aiphone.BUSY, "busy"), "not_running": (aiphone.NOT_RUNNING, "not_running"),
             "emergency": (aiphone.EMERGENCY, "emergency"), "daily_limit": (aiphone.DAILY_LIMIT, "daily_limit")}

    async def place(outcome: str) -> Any:
        hub, stop = LineHub(), asyncio.Event()
        task = asyncio.ensure_future(_node(hub, {"call": {"outcome": outcome}}, stop))
        await asyncio.sleep(0.05)
        reply = await _line(hub, tmp_path).call("+12125550142", ring_seconds=2)
        stop.set()
        await task
        return reply

    for outcome, (code, reason) in cases.items():
        reply = asyncio.run(place(outcome))
        assert (reply.code, reply.reason, reply.ok) == (code, reason, False), outcome


def test_the_hub_guards_the_number_the_limit_and_a_line_that_is_not_running(tmp_path) -> None:
    async def walk() -> list:
        hub = LineHub()
        line = _line(hub, tmp_path, limit=1)
        never = [await line.listen(timeout=1), await line.say("Hi.", call_id="c1"), await line.call("+12125550142")]
        emergency = await line.call("911")  # refused on the hub before any node is asked
        line._count.add()
        limited = await line.call("+12125550142")
        hub.hello(NODE, lines=[])
        waiting = asyncio.ensure_future(line.listen(timeout=2))
        await asyncio.sleep(0.1)
        busy = await line.listen(timeout=1)
        waiting.cancel()
        return never + [emergency, limited, busy]

    listen, say, call, emergency, limited, busy = asyncio.run(walk())
    assert {listen.code, say.code, call.code} == {aiphone.NOT_RUNNING}
    assert listen.reason == "not_running" and "not running" in listen.error
    assert emergency.code == aiphone.EMERGENCY and emergency.reason == "emergency"
    assert limited.code == aiphone.DAILY_LIMIT and limited.reason == "daily_limit"
    assert busy.code == aiphone.LISTENER_BUSY and busy.reason == "listener_busy"


def test_a_cancelled_listen_leaves_its_event_for_the_next_one(tmp_path) -> None:
    async def walk() -> Any:
        hub = LineHub()
        line = _line(hub, tmp_path)
        hub.hello(NODE, lines=[])
        hub.post_events(NODE, [{"seq": 1, "kind": "incoming", "call_id": "c1", "remote": "r"}])
        first = asyncio.ensure_future(line.listen(call_id="c1", timeout=5))
        await asyncio.sleep(0.05)
        first.cancel()
        hub.post_events(NODE, [{"seq": 2, "kind": "heard", "call_id": "c1", "text": "Hello?"}])
        return await line.listen(call_id="c1", timeout=2)

    reply = asyncio.run(walk())
    assert reply.kind == "heard" and reply.data["text"] == "Hello?"


def test_the_state_is_ai_phones_state_json_shape(tmp_path) -> None:
    from holdspeak.calls.service import _lines

    hub = LineHub()
    line = _line(hub, tmp_path)
    assert line.state() == {} and line.running() is False
    hub.hello(NODE, lines=[{"id": "main", "kind": "sip", "address": "sip:holdspeak@127.0.0.1:5060", "state": "listening"}],
              version="line-2")
    assert line.running() is True
    assert _lines(line.state()) == [{"id": "main", "kind": "sip", "state": "listening", "words": "Ready"}]
