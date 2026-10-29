"""The Line (2026-10-29): the whole node (baresip supervised, ctrl_tcp, the two
sockets, the end-of-speech rule, the manners, the link) on the fake baresip,
a real separate process (``tests/fixtures/fake_baresip.py``) that replays a
real baresip 4.12.0's recorded answers and events."""
from __future__ import annotations

import asyncio
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.calls import aiphone
from holdspeak.calls.aiphone import AiPhone
from holdspeak.line.adapter import Line
from holdspeak.line.supervisor import Account, LineConfig, account_line, link_modules, write_config
from holdspeak.line.turns import Timing
from tests.fixtures.line_rig import running_node

pytestmark = pytest.mark.timeout(120, method="thread")

FAKE_AI_PHONE = Path(__file__).resolve().parents[1] / "fixtures" / "fake_ai_phone.py"
SIP = {"account": {"kind": "sip", "user": "holdspeak"}, "daily_limit": 20, "owner": "Karol"}
REMOTE = "sip:+12125550142@sip.telnyx.com"


def _shape(reply: Any) -> tuple:
    return (reply.code, reply.ok, reply.kind, reply.data.get("result"), reply.data.get("ended_by"))


async def _walk(phone: Any, *, call_id_from: Any = None) -> list[tuple]:
    incoming = await phone.listen(timeout=10)
    call_id = incoming.data["call_id"]
    heard = await phone.listen(call_id=call_id, timeout=10)
    said = await phone.say("Hello. What can I do?", call_id=call_id)
    quiet = await phone.listen(call_id=call_id, timeout=1)
    ended = await phone.hangup(say="Goodbye.", call_id=call_id)
    gone = await phone.say("Anyone there?", call_id=call_id)
    assert heard.data["text"] == "Blue heron."
    return [_shape(r) for r in (incoming, heard, said, quiet, ended, gone)]


def test_the_line_answers_the_relay_walk_exactly_as_ai_phone_does(tmp_path, monkeypatch) -> None:
    """The second parameter: the same walk on the fake ai-phone and on the
    Line; the same codes, kinds and results, step by step."""
    script = tmp_path / "scenario.json"
    script.write_text(json.dumps({"listen": [{"kind": "incoming", "remote": REMOTE},
                                            {"kind": "heard", "text": "Blue heron."}, {"exit": 10}]}))
    monkeypatch.setenv("FAKE_AI_PHONE_SCRIPT", str(script))
    monkeypatch.setenv("FAKE_AI_PHONE_STATE", str(tmp_path / "fake-state.json"))
    phone = AiPhone([sys.executable, str(FAKE_AI_PHONE)], home=tmp_path / "aph")
    expected = asyncio.run(_walk(phone))

    async def line_walk() -> list[tuple]:
        scenario = {"incoming": {"remote": REMOTE}, "caller": [{"say": "Blue heron.", "wait": 0.3}]}
        async with running_node(scenario, config=SIP) as rig:
            line = Line(rig.node.name, hub=rig.hub, count_path=rig.root / "c.json")
            return await _walk(line)

    assert asyncio.run(line_walk()) == expected


def test_a_placed_call_says_the_ai_disclosure_first_then_answers() -> None:
    async def walk() -> tuple:
        async with running_node({"dial": "answer"}, config=SIP) as rig:
            line = Line(rig.node.name, hub=rig.hub, count_path=rig.root / "c.json")
            reply = await line.call("sip:karol@127.0.0.1:5090", ring_seconds=5)
            await asyncio.sleep(0.3)
            return reply, rig.commands(), rig.voice(), rig.node.voice

    reply, commands, voice, node_voice = asyncio.run(walk())
    assert reply.ok and reply.data["outcome"] == "answered", reply
    assert commands[0] == {**commands[0], "command": "dial", "params": "sip:karol@127.0.0.1:5090"}
    words = "This is HoldSpeak, an AI assistant, calling for Karol."
    assert words in node_voice.kept
    # The first sound on the call is the disclosure (this voice: 40 ms a character).
    assert voice and abs(voice[0]["seconds"] - 0.04 * len(words)) < 0.25, voice


@pytest.mark.parametrize("dial, code", [("busy", aiphone.BUSY), ("decline", aiphone.REJECTED), ("none", aiphone.NO_ANSWER)])
def test_a_placed_call_that_is_not_answered_is_its_code(dial: str, code: int) -> None:
    async def walk() -> tuple:
        async with running_node({"dial": dial}, config=SIP) as rig:
            reply = await Line(rig.node.name, hub=rig.hub, count_path=rig.root / "c.json").call(
                "sip:karol@127.0.0.1:5090", ring_seconds=1.0)
            return reply, [c.get("command") for c in rig.commands()]

    reply, commands = asyncio.run(walk())
    assert reply.code == code and not reply.ok, reply
    if dial == "none":
        assert commands == ["dial", "hangup"]  # the Line stops the ringing itself


def test_the_line_never_dials_an_emergency_number_and_a_number_needs_a_carrier() -> None:
    async def walk() -> tuple:
        async with running_node({}, config=SIP) as rig:
            # Past the hub's own guard: the node refuses too (two locks, one rule).
            cmd = rig.hub.queue(rig.node.name, "call", to="tel:112", ring_seconds=1)
            refused = await rig.hub.wait(rig.node.name, f"result:{cmd}", 5)
            number = await Line(rig.node.name, hub=rig.hub, count_path=rig.root / "c.json").call("+12125550142")
            return refused, number, rig.commands()

    refused, number, commands = asyncio.run(walk())
    assert refused["outcome"] == "emergency"
    assert number.code == aiphone.REJECTED and "no line" in number.error  # the service's no_line reason
    assert not any(c.get("command") == "dial" for c in commands)


def test_he_speaks_over_the_line_and_the_say_is_interrupted() -> None:
    async def walk() -> Any:
        scenario = {"incoming": {"remote": REMOTE}, "caller": [{"say": "Wait, stop.", "barge_ms": 300}]}
        async with running_node(scenario, config=SIP) as rig:
            line = Line(rig.node.name, hub=rig.hub, count_path=rig.root / "c.json")
            incoming = await line.listen(timeout=10)
            long = "Here is the whole runbook, read out step by step, so that you can follow every part of it."
            said = await line.say(long, call_id=incoming.data["call_id"])
            heard = await line.listen(call_id=incoming.data["call_id"], timeout=10)
            return said, heard, rig.voice()

    said, heard, voice = asyncio.run(walk())
    assert said.ok and said.data["result"] == "interrupted", said
    assert voice[0]["seconds"] < 1.5  # 3.6 s of voice, stopped by his words
    assert heard.data["text"] == "Wait, stop."


def test_with_no_answer_the_line_fills_and_then_hangs_up_itself() -> None:
    async def walk() -> tuple:
        scenario = {"incoming": {"remote": REMOTE}, "caller": [{"say": "Hello?", "wait": 0.3}]}
        async with running_node(scenario, config=SIP, timing=Timing(0.3, 1.2, 2.2)) as rig:
            line = Line(rig.node.name, hub=rig.hub, count_path=rig.root / "c.json")
            incoming = await line.listen(timeout=10)
            call_id = incoming.data["call_id"]
            heard = await line.listen(call_id=call_id, timeout=10)
            ended = await line.listen(call_id=call_id, timeout=10)  # nobody answers him
            return heard, ended, rig.node.call, [c.get("command") for c in rig.commands()]

    heard, ended, call, commands = asyncio.run(walk())
    assert heard.data["text"] == "Hello?"
    assert ended.kind == "ended" and ended.data["ended_by"] == "holdspeak", ended
    assert call is None and commands[-1] == "hangup"


def test_baresip_that_exits_ends_the_call_failed_and_is_started_again() -> None:
    async def walk() -> tuple:
        scenario = {"incoming": {"remote": REMOTE}, "exit_after": 1.5}
        async with running_node(scenario, config=SIP) as rig:
            line = Line(rig.node.name, hub=rig.hub, count_path=rig.root / "c.json")
            incoming = await line.listen(timeout=10)
            ended = await line.listen(call_id=incoming.data["call_id"], timeout=10)
            await asyncio.sleep(1.6)  # the backoff's first second
            return ended, rig.node.supervisor.restarts, rig.node.supervisor.running(), rig.node.control is not None

    ended, restarts, running, connected = asyncio.run(walk())
    assert ended.kind == "ended" and ended.data["outcome"] == "failed" and ended.data["ended_by"] == "holdspeak"
    assert restarts >= 1 and running and connected


def test_the_config_binds_one_address_keeps_the_password_private_and_loads_only_the_list(tmp_path) -> None:
    with pytest.raises(ValueError, match="never to every address"):
        LineConfig(home=tmp_path / "x", bind="0.0.0.0")
    telnyx = Account.of({"kind": "telnyx", "user": "hsline"}, password="s3cret")
    line = account_line(telnyx, bind="127.0.0.1", sip_port=5060, codecs=["PCMU", "PCMA"])
    assert line.startswith("<sip:hsline@sip.telnyx.com;transport=tcp>;auth_pass=s3cret;")
    assert ";regint=600;answermode=manual;audio_codecs=PCMU,PCMA" in line and "opus" not in line
    sip = account_line(Account(), bind="100.118.33.80", sip_port=5060, codecs=["opus", "PCMU", "PCMA"])
    assert sip == "<sip:holdspeak@100.118.33.80:5060>;regint=0;answermode=manual;audio_codecs=opus,PCMU,PCMA"
    stock = tmp_path / "stock"
    stock.mkdir()
    for name in ("g711", "auresamp", "account", "menu", "ctrl_tcp", "gzrtp", "x11", "opus"):
        (stock / f"{name}.so").write_text("")
    aupipe = tmp_path / "aupipe.so"
    aupipe.write_text("")
    have = link_modules(tmp_path / "mods", stock, aupipe)
    assert set(have) == {"g711", "auresamp", "account", "menu", "ctrl_tcp", "opus", "aupipe"}
    assert sorted(p.name for p in (tmp_path / "mods").iterdir()) == sorted(f"{n}.so" for n in have)
    cfg = LineConfig(home=tmp_path / "home", account=telnyx, sip_port=5061, ctrl_port=4499)
    write_config(cfg, modules=have, module_dir=tmp_path / "mods")
    config = (tmp_path / "home" / "config").read_text()
    assert "sip_listen\t\t127.0.0.1:5061" in config and "ctrl_tcp_listen\t\t127.0.0.1:4499" in config
    assert "gzrtp" not in config and "s3cret" not in config
    assert "s3cret" in (tmp_path / "home" / "accounts").read_text()
    for name in ("config", "accounts", "contacts"):
        assert stat.S_IMODE(os.stat(tmp_path / "home" / name).st_mode) == 0o600
