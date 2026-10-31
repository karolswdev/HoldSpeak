"""Calls (2026-10-28): the settings keys, the CALL palette, the held egress
gate, the MCP tools and the call's default engine."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "calls-owner")


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database

    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.setattr(config_module, "CONFIG_FILE", fake / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", fake / "holdspeak.db")
    reset_database()
    yield fake
    reset_database()


def test_the_five_calls_keys_round_trip_and_the_passphrase_is_write_only(home) -> None:
    from holdspeak.config import Config
    from holdspeak.db import get_database
    from holdspeak.services.settings_service import SettingsService

    from holdspeak.phone import phone_on

    service = SettingsService(get_database())
    fresh = service.get_settings(OWNER)["calls"]
    # The Line's keys (2026-10-29) are pinned in tests/unit/test_line_settings.py.
    assert fresh.pop("daily_limit") == 20 and fresh.pop("line")["adapter"] == ""
    assert fresh == {"enabled": False, "aiphone_dir": "", "greeting": "Hello. What can I do?",
                     "allowed_numbers": [], "passphrase_set": False,
                     # Phone (2026-10-28): Settings ▸ Calls ▸ Phone; phone_on
                     # is read only (HOLDSPEAK_PHONE), so the faces read no 404.
                     "phone_reach": {}, "phone_urgent_dnd": False, "phone_on": phone_on()}
    service.update_settings(OWNER, {"calls": {
        "enabled": True, "aiphone_dir": " ~/dev/ai-phone ", "greeting": "Hi Karol.",
        "allowed_numbers": "+1 212 555 0142, sip:agent@mac", "passphrase": "blue heron"}})
    read = service.get_settings(OWNER)["calls"]
    read.pop("daily_limit"), read.pop("line")
    assert read == {"enabled": True, "aiphone_dir": "~/dev/ai-phone", "greeting": "Hi Karol.",
                    "allowed_numbers": ["+1 212 555 0142", "sip:agent@mac"], "passphrase_set": True,
                    "phone_reach": {}, "phone_urgent_dnd": False, "phone_on": phone_on()}
    # The face sends its read back: the passphrase stays, passphrase_set and
    # phone_on are no fields.
    service.update_settings(OWNER, {"calls": {**read, "greeting": ""}})
    stored = Config.load().calls
    assert stored.passphrase == "blue heron" and stored.greeting == "Hello. What can I do?"
    assert "blue heron" not in json.dumps(service.get_settings(OWNER))


def test_a_call_offers_the_ask_tools_plus_the_two_sends_and_no_config() -> None:
    from holdspeak.mcp.palettes import ASK, CALL, CALL_HELD, CALL_HELD_AUTHORITY, CALL_HELD_EGRESS, resolve_palette
    from holdspeak.mcp.tool_authority import AUTHORITY, CONFIG, EGRESS, TOOL_AUTHORITY, WORK

    call, ask = resolve_palette(CALL), resolve_palette(ASK)
    assert CALL_HELD_EGRESS == {"channel.send", "nudge.send"}
    # PG15: a Program's read and its start join the call; the start holds.
    # LANG5: program.shape joins too, held for his spoken yes.
    # DIR8 (owner ruling 2026-10-31): program.decide, held, the one AUTHORITY tool on a call.
    assert call - ask == CALL_HELD_EGRESS | {"program.start", "program.get", "program.shape", "program.decide"}
    assert CALL_HELD == CALL_HELD_EGRESS | {"program.start", "program.shape", "program.decide"}
    assert CALL_HELD_AUTHORITY == {"program.decide"} and TOOL_AUTHORITY["program.decide"] == AUTHORITY
    # The fence: no other authority or config tool is on a call, and the one is held.
    assert {name for name in call if TOOL_AUTHORITY[name] in (AUTHORITY, CONFIG)} == CALL_HELD_AUTHORITY
    assert {name for name in call if TOOL_AUTHORITY[name] != WORK} <= CALL_HELD
    assert {TOOL_AUTHORITY[n] for n in ("program.start", "program.get", "program.shape")} == {WORK}
    assert all(TOOL_AUTHORITY[name] == WORK for name in ask)
    assert all(TOOL_AUTHORITY[name] == EGRESS for name in CALL_HELD_EGRESS)
    assert "calls.place" not in call and TOOL_AUTHORITY["calls.place"] == EGRESS
    assert {TOOL_AUTHORITY[n] for n in ("calls.status", "calls.list", "calls.hangup")} == {WORK}


def test_a_held_egress_tool_always_waits_for_his_answer_and_is_refused_elsewhere(home) -> None:
    from holdspeak.db import get_database
    from holdspeak.services.thread_tools import ThreadToolExecutor

    db = get_database()
    thread = db.threads.create_thread(title="Call")
    on_call = ThreadToolExecutor(db, dispatch_fn=lambda *a: {}, principal=OWNER,
                                 control_mode_fn=lambda: "yolo", held_egress=frozenset({"channel.send"}))
    held = on_call.admit("turn-1", thread.id, {"id": "c1", "name": "channel.send", "arguments": {"send_id": "s1"}})
    assert held.state == "awaiting_decision"  # yolo admits every other tool; this one waits
    work = on_call.admit("turn-1", thread.id, {"id": "c2", "name": "door.get", "arguments": {}})
    assert work.state == "admitted"
    plain = ThreadToolExecutor(db, dispatch_fn=lambda *a: {}, principal=OWNER, control_mode_fn=lambda: "yolo")
    with pytest.raises(ValueError, match="owner's press"):
        plain.admit("turn-2", thread.id, {"id": "c3", "name": "channel.send", "arguments": {"send_id": "s1"}})
    with pytest.raises(ValueError, match="owner's press"):
        on_call.admit("turn-1", thread.id, {"id": "c4", "name": "settings.update", "arguments": {}})


def test_the_mcp_tools_read_the_same_service(home, monkeypatch) -> None:
    from holdspeak.calls import service as calls_service
    from holdspeak.calls.runner import CallRecord
    from holdspeak.mcp.tools import TOOLS, dispatch

    names = {tool["name"] for tool in TOOLS}
    assert {"calls.status", "calls.list", "calls.place", "calls.hangup"} <= names
    monkeypatch.setenv("PATH", "/nonexistent")
    monkeypatch.delenv("HOLDSPEAK_AI_PHONE", raising=False)
    status = dispatch("calls.status", {}, OWNER)
    assert status["aiphone"] == {"state": "not_found", "words": "ai-phone not found"}
    assert status["steps"][0] == {"id": "install", "done": False, "words": "Install ai-phone on this Mac"}
    fresh = calls_service.CallsService()
    monkeypatch.setattr(calls_service, "CALLS", fresh)
    record = CallRecord(phone_call_id="c0f001", direction="in", remote="sip:+1212@x")
    record.state = "ended"
    fresh._keep(record)
    assert dispatch("calls.list", {}, OWNER)["calls"][0]["id"] == record.id
    monkeypatch.setenv("HOLDSPEAK_CALLS", "off")
    assert dispatch("calls.status", {}, OWNER)["aiphone"]["state"] == "off"


def test_a_call_runs_on_the_home_engine_unless_he_assigned_calls_turn(home, monkeypatch) -> None:
    from holdspeak.calls.service import HOME_ENGINE_PROFILE, CallsService
    from holdspeak.db import get_database

    db = get_database()
    service = CallsService()
    service.configure(db=lambda: db)
    assert service._override_profile() == ""
    with db._connection() as conn:
        conn.execute("INSERT INTO profiles (id, name) VALUES (?, ?)", (HOME_ENGINE_PROFILE, "Home engine over Tailscale"))
    assert service._override_profile() == HOME_ENGINE_PROFILE
    from tests.unit.test_desk_ask_ai import _assign, _seed_routes

    _seed_routes(db)
    _assign(db, "calls.turn", ["glass-lan"], "calls-own")
    assert service._override_profile() == ""
