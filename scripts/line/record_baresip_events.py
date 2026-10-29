#!/usr/bin/env python3
"""Record a real baresip's ctrl_tcp answers and events for the fake baresip.

Two baresips on 127.0.0.1 (the Line and a caller), each with aupipe, driven
through ctrl_tcp: an incoming call accepted, a DTMF key, a hang-up by the
caller; a call the Line rejects busy (486); a call the Line places. Every
message both ends got is written, in order, to
``tests/fixtures/baresip_events.json``. The fake baresip
(``tests/fixtures/fake_baresip.py``) replays these shapes.

    uv run python scripts/line/record_baresip_events.py [out.json]
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from holdspeak.line.audio import HeardPort, SayPort  # noqa: E402
from holdspeak.line.control import Control  # noqa: E402
from holdspeak.line.supervisor import (  # noqa: E402
    Account, LineConfig, Supervisor, baresip_version, build_aupipe, find_baresip,
)

OUT = ROOT / "tests" / "fixtures" / "baresip_events.json"


async def wait_type(ctrl: Control, typ: str, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while True:
        event = await asyncio.wait_for(ctrl.events.get(), max(0.01, deadline - time.monotonic()))
        ctrl._seen.append(event.raw)  # type: ignore[attr-defined]
        if event.type == typ:
            return event


async def main(out: Path) -> int:
    binary = find_baresip()
    if not binary:
        print("baresip is not installed")
        return 1
    root = Path(tempfile.mkdtemp(prefix="hsl", dir="/tmp"))
    aupipe = build_aupipe(root / "build", binary=binary)
    ends = {}
    for name, sip, ctrl in (("line", 5070, 4444), ("far", 5080, 4445)):
        cfg = LineConfig(home=root / name, sip_port=sip, ctrl_port=ctrl,
                         say_sock=root / f"{name}.say", heard_sock=root / f"{name}.heard",
                         account=Account(kind="sip", user=name, codecs=("PCMU", "PCMA")))
        ports = (SayPort(cfg.say_sock), HeardPort(cfg.heard_sock))
        sup = Supervisor(cfg, binary=binary)
        sup.prepare(aupipe=aupipe)
        await sup.start()
        ends[name] = (cfg, sup, ports)
    await asyncio.sleep(0.5)
    line, far = Control(port=4444), Control(port=4445)
    await line.connect()
    await far.connect()
    for c in (line, far):
        c._seen = []  # type: ignore[attr-defined]
    record: dict = {"baresip": baresip_version(binary), "recorded": time.strftime("%Y-%m-%d"), "steps": []}

    async def step(name: str, coro):
        reply = await coro
        record["steps"].append({"step": name, "response": reply})
        return reply

    def drain(tag: str) -> None:
        for who, c in (("line", line), ("far", far)):
            while not c.events.empty():
                c._seen.append(c.events.get_nowait().raw)  # type: ignore[attr-defined]
            record["steps"].append({"step": f"{tag}: events at {who}", "events": c._seen})  # type: ignore[attr-defined]
            c._seen = []  # type: ignore[attr-defined]

    try:
        # 1. an incoming call: accepted, a DTMF key, the caller hangs up.
        await step("far dial", far.command("dial", "sip:line@127.0.0.1:5070"))
        incoming = await wait_type(line, "CALL_INCOMING")
        await step("line accept", line.command("accept", incoming.call_id))
        await wait_type(line, "CALL_ESTABLISHED")
        await wait_type(far, "CALL_ESTABLISHED")
        await asyncio.sleep(0.5)
        await step("far sndcode 5", far.command("sndcode", "5"))
        await asyncio.sleep(0.8)
        await step("line listcalls", line.command("listcalls"))
        await step("far hangup", far.command("hangup"))
        await wait_type(line, "CALL_CLOSED")
        await wait_type(far, "CALL_CLOSED")
        await asyncio.sleep(0.3)
        drain("incoming call")
        # 2. the Line rejects a call busy.
        await step("far dial", far.command("dial", "sip:line@127.0.0.1:5070"))
        incoming = await wait_type(line, "CALL_INCOMING")
        await step("line hangup busy", line.command("hangup", f"{incoming.call_id} scode=486"))
        await wait_type(far, "CALL_CLOSED")
        await asyncio.sleep(0.3)
        drain("rejected call")
        # 3. the Line places a call; the far end answers; the Line hangs up.
        await step("line dial", line.command("dial", "sip:far@127.0.0.1:5080"))
        incoming = await wait_type(far, "CALL_INCOMING")
        await step("far accept", far.command("accept", incoming.call_id))
        await wait_type(line, "CALL_ESTABLISHED")
        await asyncio.sleep(0.5)
        await step("line hangup", line.command("hangup"))
        await wait_type(line, "CALL_CLOSED")
        await asyncio.sleep(0.3)
        drain("placed call")
        # 4. a command with no call.
        await step("line hangup no call", line.command("hangup"))
        drain("no call")
    finally:
        await line.close()
        await far.close()
        for cfg, sup, ports in ends.values():
            await sup.stop()
            for port in ports:
                port.close()
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({sum(len(s.get('events', [])) for s in record['steps'])} events)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)))
