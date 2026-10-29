"""The Line (2026-10-29): baresip's ctrl_tcp codec and client, on the RECORDED
answers and events of a real baresip 4.12.0 (tests/fixtures/baresip_events.json)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from holdspeak.line import control as ctl
from holdspeak.line.node import close_outcome, dial_id

RECORDED = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "baresip_events.json").read_text())


def _events() -> list[dict]:
    return [event for step in RECORDED["steps"] for event in step.get("events") or []]


def test_a_netstring_round_trips_whole_split_and_back_to_back() -> None:
    messages = [{"command": "dial", "params": "sip:line@127.0.0.1:5070", "token": "hs1"},
                {"event": True, "type": "CALL_INCOMING", "peeruri": "sip:Tomás@x"}]
    wire = b"".join(ctl.encode(m) for m in messages)
    assert ctl.Decoder().feed(wire) == messages
    decoder, out = ctl.Decoder(), []
    for i in range(len(wire)):  # one byte at a time: a partial message waits
        out += decoder.feed(wire[i:i + 1])
    assert out == messages


@pytest.mark.parametrize("bad", [b"x:{},", b"5:{}}}}X", b"2:[],extra", b"99999999999:"])
def test_a_broken_netstring_is_an_error_not_a_guess(bad: bytes) -> None:
    with pytest.raises(ctl.NetstringError):
        decoder = ctl.Decoder()
        decoder.feed(bad)
        decoder.feed(b"3:{},")


def test_the_recorded_events_read_as_the_line_reads_them() -> None:
    assert RECORDED["baresip"] == "4.12.0"
    events = [ctl.Event.of(e) for e in _events()]
    incoming = next(e for e in events if e.type == ctl.INCOMING)
    assert incoming.call_id and incoming.peer.startswith("sip:far@") and incoming.direction == "incoming"
    assert incoming.account == "sip:line@127.0.0.1:5070"
    dtmf = next(e for e in events if e.type == ctl.DTMF_START)
    assert dtmf.param == "5" and dtmf.call_id == incoming.call_id
    closed = [e.param for e in events if e.type == ctl.CLOSED]
    assert "486 Busy Here" in closed and "Rejected by user" in closed


def test_a_placed_calls_end_is_its_outcome_and_dial_names_the_call() -> None:
    dials = [s["response"] for s in RECORDED["steps"] if s["step"].endswith("dial")]
    assert dial_id(dials[0]["data"]) == "39c5fc8289003b75"
    assert close_outcome("486 Busy Here") == "busy"
    assert close_outcome("603 Decline") == "rejected" and close_outcome("404 Not Found") == "rejected"
    assert close_outcome("480 Temporarily Unavailable") == "no_answer"
    assert close_outcome("Rejected by user", rang_out=True) == "no_answer"
    assert close_outcome("Connection reset by peer [54]") == "failed"


def test_the_client_matches_each_answer_to_its_command_and_queues_the_events() -> None:
    """A server that answers like baresip: the recorded answers, an event
    between them, and a command with no call (ok false)."""
    no_call = next(s["response"] for s in RECORDED["steps"] if s["step"] == "line hangup no call")
    incoming = next(e for e in _events() if e["type"] == "CALL_INCOMING")

    async def walk() -> tuple:
        seen = []

        async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            decoder = ctl.Decoder()
            while True:
                data = await reader.read(4096)
                if not data:
                    return
                for message in decoder.feed(data):
                    seen.append(message["command"])
                    writer.write(ctl.encode(incoming))
                    answer = dict(no_call) if message["command"] == "hangup" else {"response": True, "ok": True, "data": ""}
                    answer["token"] = message["token"]
                    writer.write(ctl.encode(answer))
                    await writer.drain()

        server = await asyncio.start_server(serve, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        client = ctl.Control(port=port)
        await client.connect(wait=2)
        accepted = await client.command("accept", "39c5fc8289003b75")
        hung = await client.command("hangup")
        event = await asyncio.wait_for(client.events.get(), 2)
        await client.close()
        server.close()
        return seen, accepted, hung, event

    seen, accepted, hung, event = asyncio.run(walk())
    assert seen == ["accept", "hangup"]
    assert accepted["ok"] is True and hung["ok"] is False and hung["data"] == "no active call\n"
    assert event.type == ctl.INCOMING


def test_a_client_with_no_baresip_says_so() -> None:
    from tests.fixtures.line_rig import free_port

    async def walk() -> None:
        await ctl.Control(port=free_port()).connect(wait=0.2)

    with pytest.raises(ctl.ControlError, match="did not answer"):
        asyncio.run(walk())
