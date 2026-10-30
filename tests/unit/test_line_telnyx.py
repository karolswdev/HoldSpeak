"""The Line's Telnyx setup (LINE-3b): with his key the hub connects the SIP
account, lists numbers with their cost, buys one ONLY on his press (the quote
his confirm sends, the kernel operation ``calls.line.buy_number``), assigns
it, and the written accounts file registers. The fake Telnyx
(``tests/fixtures/fake_telnyx.py``) is the only Telnyx reached."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.principals import Principal, PrincipalKind
from tests.fixtures.fake_telnyx import running_fake_telnyx

OWNER = Principal(PrincipalKind.OWNER, "line-owner")
AGENT = Principal(PrincipalKind.AGENT, "agent-codex")
KEY = "KEY0123456789abcdefTELNYX"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database

    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(fake / "keys.json"))
    for name in ("TELNYX_API_KEY", "HOLDSPEAK_LINE_SIP_PASSWORD", "HOLDSPEAK_AI_PHONE", "HOLDSPEAK_LINE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(config_module, "CONFIG_FILE", fake / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", fake / "holdspeak.db")
    reset_database()
    yield fake
    reset_database()


@pytest.fixture
def telnyx(home, monkeypatch):
    from holdspeak.line import setup as line_setup

    monkeypatch.setattr(line_setup, "TELNYX_SETUP", line_setup.TelnyxSetup())
    with running_fake_telnyx(key=KEY) as fake:
        monkeypatch.setenv("HOLDSPEAK_TELNYX_API", fake.url)
        yield fake


def _client() -> tuple[TestClient, dict[str, Any]]:
    import holdspeak.web.routes.calls as calls_routes
    from holdspeak.web.context import WebContext

    who = {"principal": OWNER}
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        request.state.principal = who["principal"]
        return await call_next(request)

    app.include_router(calls_routes.build_calls_router(WebContext(get_state=lambda: {}, broadcast=lambda k, d: None)))
    return TestClient(app), who


def _key() -> None:
    from holdspeak.line import secrets

    secrets.write(secrets.TELNYX_API_KEY, KEY)


def _operations() -> list[dict[str, Any]]:
    from holdspeak.db import get_database

    with get_database()._connection() as conn:
        rows = conn.execute(
            "SELECT o.name, o.principal_kind, o.target_ref, o.state, r.outcome, r.result_ref FROM kernel_operations o "
            "LEFT JOIN kernel_receipts r ON r.operation_id = o.operation_id WHERE o.name = 'calls.line.buy_number'"
        ).fetchall()
    return [dict(zip(("name", "principal_kind", "target_ref", "state", "outcome", "result_ref"), row)) for row in rows]


def test_without_a_key_the_status_says_missing_and_connect_says_the_next_step(telnyx) -> None:
    client, _ = _client()
    status = client.get("/api/calls/line/telnyx/status")
    assert status.status_code == 200
    assert status.json() == {"key": "missing", "password": "missing", "connection": None, "number": "",
                             "balance": None, "error": ""}
    refused = client.post("/api/calls/line/telnyx/connect")
    assert refused.status_code == 409
    assert refused.json()["reason"] == "no_key" and refused.json()["next"] == "Save your Telnyx API key in step 1."
    assert telnyx.requests == []  # no key: nothing went to Telnyx


def test_connect_makes_the_sip_account_once_and_keeps_the_password_in_the_keystore(telnyx, home, caplog) -> None:
    from holdspeak.config import Config
    from holdspeak.line import secrets

    _key()
    client, _ = _client()
    with caplog.at_level(logging.DEBUG):
        first = client.post("/api/calls/line/telnyx/connect")
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["connected"] and body["created"] and body["domain"] == "sip.telnyx.com"
    assert body["user"].startswith("hs") and len(body["user"]) == 12 and body["user"].isalnum()
    made = telnyx.connections[0]
    assert made["connection_name"] == "HoldSpeak Line" and made["user_name"] == body["user"]
    assert made["outbound"] == {"outbound_voice_profile_id": telnyx.profiles[0]["id"]}
    password = secrets.read(secrets.SIP_PASSWORD)
    assert password == made["password"] and len(password) == 32 and ";" not in password
    account = Config.load().calls.line["account"]
    assert account == {"kind": "telnyx", "user": body["user"], "domain": "sip.telnyx.com",
                       "outbound": "sip:sip.telnyx.com;transport=tcp", "password_ref": "calls.line.sip_password",
                       "connection_id": made["id"], "number": "", "codecs": ["opus", "PCMU", "PCMA"]}
    on_disk = (home / ".holdspeak" / "config.json").read_text() + first.text + caplog.text
    assert password not in on_disk and KEY not in on_disk  # never in the file, the answer or a log line
    # Idempotent: the second press reuses the connection and its password.
    again = client.post("/api/calls/line/telnyx/connect").json()
    assert again["created"] is False and again["connection_id"] == made["id"]
    assert len(telnyx.connections) == 1 and len(telnyx.profiles) == 1
    assert secrets.read(secrets.SIP_PASSWORD) == password
    # The keystore lost the password: the same connection gets a new one.
    secrets.write(secrets.SIP_PASSWORD, None)
    third = client.post("/api/calls/line/telnyx/connect").json()
    assert third["created"] is False and len(telnyx.connections) == 1
    assert secrets.read(secrets.SIP_PASSWORD) == telnyx.connections[0]["password"] != password


def test_a_refused_key_says_what_failed_what_is_kept_and_the_next_action(telnyx) -> None:
    from holdspeak.line import secrets

    secrets.write(secrets.TELNYX_API_KEY, "KEY-wrong")
    client, _ = _client()
    refused = client.post("/api/calls/line/telnyx/connect")
    assert refused.status_code == 502
    assert refused.json() == {
        "error": "Telnyx did not take the key while it made the SIP connection.", "reason": "key_refused",
        "kept": "Your key is kept. Nothing was made at Telnyx.",
        "next": "Check the key in the Telnyx portal, then save it again."}
    assert "KEY-wrong" not in refused.text
    assert client.get("/api/calls/line/telnyx/status").json()["error"] == "Telnyx did not take the key."


def test_find_numbers_lists_ten_with_their_cost_and_a_quote_each(telnyx) -> None:
    _key()
    client, _ = _client()
    found = client.get("/api/calls/line/telnyx/numbers", params={"area": "212"})
    assert found.status_code == 200, found.text
    rows = found.json()["numbers"]
    assert len(rows) == 10 and rows[0]["phone_number"] == "+12125550100"
    assert {k: rows[0][k] for k in ("monthly_cost", "upfront_cost", "currency")} == {
        "monthly_cost": "1.00", "upfront_cost": "1.00", "currency": "USD"}
    assert len({row["quote"] for row in rows}) == 10
    method, path, query, _ = telnyx.requests[-1]
    assert (method, path) == ("GET", "/available_phone_numbers")
    assert query == {"filter[country_code]": "US", "filter[features]": "voice", "filter[limit]": "10",
                     "filter[national_destination_code]": "212"}
    bad = client.get("/api/calls/line/telnyx/numbers", params={"area": "21"})
    assert bad.status_code == 400 and bad.json()["reason"] == "area"


def test_a_number_is_bought_only_on_his_press_and_is_one_kernel_operation(telnyx) -> None:
    from holdspeak.config import Config

    _key()
    client, who = _client()
    assert client.post("/api/calls/line/telnyx/connect").status_code == 200
    row = client.get("/api/calls/line/telnyx/numbers", params={"area": "212"}).json()["numbers"][0]
    # No press, no quote: refused before Telnyx is asked.
    bare = client.post("/api/calls/line/telnyx/buy", json={"phone_number": row["phone_number"]})
    assert bare.status_code == 403 and bare.json()["reason"] == "press_required"
    assert bare.json()["kept"] == "Nothing was bought."
    # A quote for another number is not his press for this one.
    other = client.post("/api/calls/line/telnyx/buy", json={"phone_number": "+12125550199", "quote": row["quote"]})
    assert other.status_code == 409 and other.json()["reason"] == "quote_old"
    # An agent's credential is refused by the kernel, with a receipt.
    who["principal"] = AGENT
    agent = client.post("/api/calls/line/telnyx/buy", json={"phone_number": row["phone_number"], "quote": row["quote"]})
    assert agent.status_code == 403, agent.text
    assert telnyx.orders == []
    # His press: the order, and the receipt names the number and the cost.
    who["principal"] = OWNER
    bought = client.post("/api/calls/line/telnyx/buy", json={"phone_number": row["phone_number"], "quote": row["quote"]})
    assert bought.status_code == 200, bought.text
    body = bought.json()
    assert body["phone_number"] == "+12125550100" and body["order_status"] == "success"
    assert body["monthly_cost"] == "1.00" and body["receipt"]["outcome"] == "succeeded"
    connection_id = Config.load().calls.line["account"]["connection_id"]
    assert telnyx.orders[0]["phone_numbers"][0]["phone_number"] == "+12125550100"
    assert telnyx.orders[0]["connection_id"] == connection_id
    ops = _operations()
    ref = "phone_number:12125550100/monthly-1.00-USD/upfront-1.00-USD"
    assert {"principal_kind": "agent", "state": "refused"}.items() <= ops[0].items()
    assert ops[1] == {"name": "calls.line.buy_number", "principal_kind": "owner", "target_ref": ref,
                      "state": "succeeded", "outcome": "succeeded", "result_ref": ref}
    # The quote is spent: a second press does not buy again.
    twice = client.post("/api/calls/line/telnyx/buy", json={"phone_number": row["phone_number"], "quote": row["quote"]})
    assert twice.status_code == 409 and len(telnyx.orders) == 1


def test_assign_points_the_number_at_the_line_and_the_status_reads_it_back(telnyx) -> None:
    from holdspeak.config import Config

    _key()
    client, _ = _client()
    client.post("/api/calls/line/telnyx/connect")
    row = client.get("/api/calls/line/telnyx/numbers", params={"area": "212"}).json()["numbers"][3]
    # The order is pending: the number is not there yet.
    telnyx.order_status = "pending"
    client.post("/api/calls/line/telnyx/buy", json={"phone_number": row["phone_number"], "quote": row["quote"]})
    pending = client.post("/api/calls/line/telnyx/assign", json={"phone_number": row["phone_number"]})
    assert pending.status_code == 409 and pending.json()["next"] == "Press Assign again in a minute."
    # It lands, pointed elsewhere: assign points it at the line.
    telnyx.numbers.append({"id": "1293384261075739999", "record_type": "phone_number", "phone_number": row["phone_number"],
                           "status": "active", "connection_id": ""})
    assigned = client.post("/api/calls/line/telnyx/assign", json={"phone_number": row["phone_number"]})
    assert assigned.status_code == 200, assigned.text
    account = Config.load().calls.line["account"]
    assert telnyx.numbers[-1]["connection_id"] == account["connection_id"] and account["number"] == "+12125550103"
    assert ("PATCH", "/phone_numbers/1293384261075739999") in [(m, p) for m, p, _q, _b in telnyx.requests]
    status = client.get("/api/calls/line/telnyx/status").json()
    assert status == {"key": "keystore", "password": "keystore",
                      "connection": {"id": account["connection_id"], "user": account["user"], "domain": "sip.telnyx.com"},
                      "number": "+12125550103",
                      "balance": {"balance": "20.00", "available": "20.00", "currency": "USD"}, "error": ""}


def test_the_line_off_switch_covers_the_telnyx_routes(telnyx, monkeypatch) -> None:
    _key()
    monkeypatch.setenv("HOLDSPEAK_LINE", "off")
    client, _ = _client()
    for method, path in (("get", "/api/calls/line/telnyx/status"), ("post", "/api/calls/line/telnyx/connect"),
                         ("get", "/api/calls/line/telnyx/numbers"), ("post", "/api/calls/line/telnyx/buy"),
                         ("post", "/api/calls/line/telnyx/assign")):
        answer = getattr(client, method)(path)
        assert answer.status_code == 409 and answer.json()["reason"] == "off", path
    assert telnyx.requests == []


def test_the_connected_account_is_written_for_baresip_and_registers(telnyx) -> None:
    from holdspeak.calls.service import line_config
    from tests.fixtures.line_rig import read_jsonl, running_node

    _key()
    client, _ = _client()
    connected = client.post("/api/calls/line/telnyx/connect").json()
    config = line_config("this-mac")
    assert "connection_id" not in config["account"] and config["password"] == telnyx.connections[0]["password"]

    async def run() -> tuple[str, str, list[dict[str, Any]]]:
        async with running_node({"dial": "answer"}, config=config) as rig:
            for _ in range(200):
                if rig.node.line_state == "registered":
                    break
                await asyncio.sleep(0.02)
            accounts = (rig.node.supervisor.cfg.home / "accounts").read_text()
            return rig.node.line_state, accounts, rig.commands()

    state, accounts, commands = asyncio.run(run())
    user, password = connected["user"], telnyx.connections[0]["password"]
    assert accounts == (f"<sip:{user}@sip.telnyx.com;transport=tcp>;auth_pass={password};"
                        "outbound=\"sip:sip.telnyx.com;transport=tcp\";regint=600;answermode=manual;"
                        "audio_codecs=PCMU,PCMA\n")
    assert state == "registered"
    assert {"register": f"sip:{user}@sip.telnyx.com;transport=tcp", "answer": 200} in [
        {k: v for k, v in c.items() if k != "at"} for c in commands]
    assert json.dumps(config).count(KEY) == 0  # the node never gets the provisioning key
