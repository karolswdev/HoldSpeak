"""Calls (2026-10-28): the ai-phone adapter against a fake ai-phone CLI.

The fake (``tests/fixtures/fake_ai_phone.py``) is a real separate process
that prints ai-phone's own shapes and exit codes (its command reference and
``cli_call.py`` at 436f9f1b); the adapter runs it the way it runs the real one.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

from holdspeak.calls import aiphone
from holdspeak.calls.aiphone import AiPhone, resolve_command
from holdspeak.calls.runner import is_goodbye, number_allowed, passphrase_heard, read_back, speakable, yes_or_no

FAKE = Path(__file__).resolve().parents[1] / "fixtures" / "fake_ai_phone.py"


def fake_phone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scenario: dict) -> AiPhone:
    script = tmp_path / "scenario.json"
    script.write_text(json.dumps(scenario))
    monkeypatch.setenv("FAKE_AI_PHONE_SCRIPT", str(script))
    monkeypatch.setenv("FAKE_AI_PHONE_STATE", str(tmp_path / "fake-state.json"))
    monkeypatch.setenv(aiphone.COMMAND_ENV, f"{sys.executable} {FAKE}")
    monkeypatch.setenv(aiphone.HOME_ENV, str(tmp_path / "ai-phone-home"))
    phone = AiPhone.from_settings("")
    assert phone is not None
    return phone


def fake_log(tmp_path: Path) -> list[list[str]]:
    return json.loads((tmp_path / "fake-state.json").read_text())["log"]


def test_the_relay_commands_read_ai_phones_json_and_exit_codes(tmp_path, monkeypatch) -> None:
    phone = fake_phone(tmp_path, monkeypatch, {"listen": [
        {"kind": "incoming", "remote": "sip:+12125550142@sip.telnyx.com"},
        {"kind": "heard", "text": "Blue heron."},
        {"exit": 10},
    ]})

    async def walk() -> list:
        incoming = await phone.listen(timeout=5)
        heard = await phone.listen(call_id=incoming.data["call_id"], timeout=5)
        said = await phone.say("Hello. What can I do?", call_id=incoming.data["call_id"])
        quiet = await phone.listen(call_id=incoming.data["call_id"], timeout=5)
        ended = await phone.hangup(say="Goodbye.", call_id=incoming.data["call_id"])
        gone = await phone.say("Anyone there?", call_id=incoming.data["call_id"])
        return [incoming, heard, said, quiet, ended, gone]

    incoming, heard, said, quiet, ended, gone = asyncio.run(walk())
    assert incoming.ok and incoming.kind == "incoming", incoming
    assert incoming.data["remote"] == "sip:+12125550142@sip.telnyx.com" and incoming.data["line"] == "main"
    assert heard.ok and heard.kind == "heard" and heard.data["text"] == "Blue heron."
    assert said.ok and said.data["result"] == "said"
    assert quiet.code == aiphone.LISTEN_TIMEOUT and quiet.kind == "timeout" and quiet.reason == "timeout"
    assert ended.ok and ended.data["ended_by"] == "hangup_command" and ended.data["outcome"] == "completed"
    assert [line["who"] for line in ended.data["transcript"]] == ["them", "agent", "agent"]
    assert gone.code == aiphone.NO_CALL and not gone.ok and "has ended" in gone.error
    # Each command ran as its own process with --json (the documented form).
    assert all(entry[-1] == "--json" for entry in fake_log(tmp_path))
    assert fake_log(tmp_path)[2][:2] == ["say", "Hello. What can I do?"]


def test_a_placed_call_answers_with_its_call_id_and_its_created_event(tmp_path, monkeypatch) -> None:
    phone = fake_phone(tmp_path, monkeypatch, {"listen": []})
    reply = asyncio.run(phone.call("+12125550142", ring_seconds=5))
    assert reply.ok and reply.data["outcome"] == "answered" and reply.data["mode"] == "relay"
    assert reply.events == [{"event": "created", "call_id": reply.data["call_id"]}]
    assert fake_log(tmp_path)[0][:3] == ["call", "+12125550142", "--relay"]


def test_no_answer_and_a_daemon_that_is_down_are_reasons(tmp_path, monkeypatch) -> None:
    phone = fake_phone(tmp_path, monkeypatch, {"listen": [], "call": {"exit": 6, "outcome": "no_answer"}})
    reply = asyncio.run(phone.call("+12125550142", ring_seconds=5))
    assert reply.code == aiphone.NO_ANSWER and reply.reason == "no_answer" and not reply.ok
    monkeypatch.setenv("FAKE_AI_PHONE_DOWN", "1")
    down = asyncio.run(phone.listen(timeout=5))
    assert down.code == aiphone.NOT_RUNNING and down.reason == "not_running" and "not running" in down.error


def test_the_command_is_named_whole_or_found_in_the_checkout_or_on_path(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(aiphone.COMMAND_ENV, raising=False)
    checkout = tmp_path / "ai-phone"
    (checkout / ".venv" / "bin").mkdir(parents=True)
    binary = checkout / ".venv" / "bin" / "ai-phone"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    assert resolve_command(str(checkout)) == [str(binary)]
    binary.unlink()
    (checkout / "pyproject.toml").write_text("[project]\nname='ai-phone'\n")
    monkeypatch.setattr(aiphone.shutil, "which", lambda name: f"/opt/bin/{name}")
    assert resolve_command(str(checkout)) == ["/opt/bin/uv", "run", "--project", str(checkout), "ai-phone"]
    assert resolve_command("") == ["/opt/bin/ai-phone"]
    monkeypatch.setattr(aiphone.shutil, "which", lambda name: None)
    assert resolve_command("") is None
    assert resolve_command(str(tmp_path / "nowhere")) is None
    monkeypatch.setenv(aiphone.COMMAND_ENV, "python3 /x/fake.py")
    assert resolve_command(str(checkout)) == ["python3", "/x/fake.py"]


def test_the_state_file_and_the_socket_are_ai_phones_status(tmp_path, monkeypatch) -> None:
    import shutil
    import socket
    import tempfile

    # A short folder: a Unix socket path has a 104-byte limit on macOS
    # (ai-phone's own is ~/.ai-phone/control.sock).
    home = Path(tempfile.mkdtemp(prefix="aph", dir="/tmp"))
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        phone = AiPhone(["ai-phone"], home=home)
        assert phone.state() == {} and phone.running() is False
        (home / "state.json").write_text(json.dumps({
            "written_at": 1.0, "lines": {"agent": {"id": "agent", "kind": "sip", "address": "sip:agent@mac",
                                                   "state": "unregistered"}},
            "active_call": None, "brain": {"kind": "openai_compatible", "model": "qwen3.8-27b"}}))
        assert phone.state()["lines"]["agent"]["kind"] == "sip"
        (home / "control.sock").write_text("")  # a stale file is not a running daemon
        assert phone.running() is False
        (home / "control.sock").unlink()
        server.bind(str(home / "control.sock"))
        server.listen(1)
        assert phone.running() is True
    finally:
        server.close()
        shutil.rmtree(home, ignore_errors=True)


def test_the_words_of_a_call() -> None:
    assert speakable("**Done** — added [the task](note:x) (action_item:ai_1).\n\n- one\n- two") == "Done — added the task . one two"
    long = "One sentence here. " * 60
    assert len(speakable(long)) <= 600 and speakable(long).endswith(".")
    assert yes_or_no("Yes, send it.") == "approve" and yes_or_no("No, don't.") == "deny" and yes_or_no("Hmm.") == ""
    assert yes_or_no("Yes. No.") == ""
    assert is_goodbye("That's all, thanks.") and is_goodbye("Okay, bye") and not is_goodbye("Bye the way, add a note about the goodbye party for Tomás")
    assert passphrase_heard("Uh, blue heron.", "Blue Heron") and not passphrase_heard("blue", "blue heron")
    assert not passphrase_heard("anything", "")
    assert number_allowed("sip:+12125550142@sip.telnyx.com", ["+1 212 555 0142"])
    assert number_allowed("sip:agent@100.64.0.9", ["sip:agent@100.64.0.9"])
    assert not number_allowed("sip:+12125550199@sip.telnyx.com", ["+1 212 555 0142"])
    assert number_allowed("anything", [])
    words, rows = read_back({"wrote": [{"kind": "action_item", "label": "Nudge Tomás", "ref": "action_item:ai_1"}],
                             "prepared": [{"kind": "send", "label": "Runbook to HoldSpeak folder", "ref": "send:s1"}]})
    assert words == "Done: Added a task: Nudge Tomás. Prepared Runbook to HoldSpeak folder."
    assert [row["effect"] for row in rows] == ["wrote", "prepared"]
