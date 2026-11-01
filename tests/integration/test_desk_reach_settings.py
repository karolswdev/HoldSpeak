"""PG-DIRECTION DIR4 to DIR6 on the Programs rig: Later and Settings ▸ Reach, through the routes.

``GET /api/reach`` (the channels, the ladder, quiet hours, the digest, Later
means), ``PUT /api/reach``, ``PUT /api/reach/telegram/token`` (the keystore
file inside HOME), ``POST`` and ``DELETE /api/reach/telegram/pair``, ``POST
/api/reach/later`` (the Needs you row goes to the Later group), and ``POST
/api/reach/packages`` with ``send: telegram`` (the row's line says it was
sent). The Telegram Bot API is the fake bot of ``tests/unit/test_reach_telegram.py``
over the fixture's shapes; nothing leaves the machine.

The faces replay the answers recorded here (``web/src/desk/reach/__fixtures__/``;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites them, else this test fences their shape).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.services import briefing_service as briefing_module
from holdspeak.services import program_service as program_module
from holdspeak.services import reach_service as reach_module
from holdspeak.services import telegram_reach as telegram_module
from holdspeak.services.briefing_service import BriefingService
from holdspeak.services.needs_you_membership import compute_needs_you
from holdspeak.services.reach_service import ReachService
from holdspeak.services.telegram_reach import TelegramReach
from holdspeak.web.routes.briefing import build_briefing_router
from holdspeak.web.routes.programs import build_programs_router
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig
from tests.integration.test_desk_reach import ROOT, _fixture
from tests.unit.test_reach_telegram import TOKEN, FakeBot, update

FIXTURES = ROOT / "web" / "src" / "desk" / "reach" / "__fixtures__"


@pytest.fixture
def desk(tmp_path, monkeypatch):
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "home" / "channel-keys.json"))
    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "on")
    monkeypatch.setenv("HOLDSPEAK_PHONE", "off")
    monkeypatch.setenv("HOLDSPEAK_RECORDINGS", "off")
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Overnight on the home box", goal="Stop the stalls.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Store the stall reason", "brief": "Store it.", "owns": ["src/a.py"]}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"src/a.py": "a\n", "holdspeak/db/schema.py": "b\n"})
    rig.tick()
    bot = FakeBot()
    briefing = BriefingService(rig.db, programs=lambda: rig.service)
    holder: dict = {}
    reach = ReachService(rig.db, programs=lambda: rig.service, briefing=briefing, telegram=lambda: holder["tg"])
    telegram = TelegramReach(rig.db, caller=bot, briefing=briefing, reach=reach, programs=lambda: rig.service,
                             link=lambda path: f"https://hub.tail.ts.net{path}")
    holder["tg"] = telegram
    briefing._reach, briefing.settle, briefing._telegram = reach, telegram.settle, lambda: telegram
    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    monkeypatch.setattr(briefing_module, "default_briefing_service", lambda db=None: briefing)
    monkeypatch.setattr(reach_module, "default_reach_service", lambda db=None: reach)
    monkeypatch.setattr(telegram_module, "default_telegram_reach", lambda db=None: telegram)
    app = FastAPI()

    @app.middleware("http")
    async def _edge(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    app.include_router(build_briefing_router(None))  # type: ignore[arg-type]
    item = next(row for row in rig.service.needs_you_items() if row["kind"] == "core")
    return {"rig": rig, "pid": pid, "client": TestClient(app), "bot": bot, "telegram": telegram,
            "ref": f"program:{pid}:{item['id']}", "tmp": tmp_path}


def _record(name: str, answer, desk) -> None:
    _fixture(FIXTURES / name, answer, desk["tmp"], "no-page-token-in-this-answer")


def test_settings_reach_reads_and_saves_its_rows(desk) -> None:
    client = desk["client"]
    unpaired = client.get("/api/reach")
    assert unpaired.status_code == 200, unpaired.text
    body = unpaired.json()
    assert body["channels"]["telegram"]["paired"] is None and body["channels"]["telegram"]["token"] == "missing"
    assert body["ladder"]["telegram"] == "at_once" and body["later_means"] == "in_2h"
    assert body["quiet_hours"]["start"] == 22 and body["digest"]["at"] == "end_of_quiet"
    assert set(body["ladder"]["kinds"]) >= {"level", "core_question", "program_done"}
    _record("reach.unpaired.json", body, desk)

    refused = client.post("/api/reach/telegram/pair")
    assert refused.status_code == 409 and refused.json()["code"] == "token_missing"
    bad = client.put("/api/reach/telegram/token", json={"token": "not a token"})
    assert bad.status_code == 400 and bad.json()["code"] == "token_invalid"
    stored = client.put("/api/reach/telegram/token", json={"token": TOKEN})
    assert stored.json() == {"token": "keystore"} and TOKEN not in client.get("/api/reach").text

    pairing = client.post("/api/reach/telegram/pair")
    assert pairing.status_code == 201
    code = pairing.json()["code"]
    pairing_body = {**pairing.json(), "code": "482913", "words": "482 913", "say": "Send /pair 482 913 to your bot"}
    _record("reach.pairing.json", pairing_body, desk)
    _record("reach.pairing_open.json", client.get("/api/reach").json(), desk)
    assert desk["telegram"].handle_update(update("pair", code=code))["ok"] is True
    paired = client.get("/api/reach").json()
    assert paired["channels"]["telegram"]["paired"]["name"] == "Karol"
    assert paired["channels"]["telegram"]["token"] == "keystore"
    _record("reach.paired.json", paired, desk)

    saved = client.put("/api/reach", json={"telegram": "after_10", "later_means": "end_of_quiet", "digest": 7})
    assert saved.status_code == 200, saved.text
    assert saved.json()["ladder"]["telegram"] == "after_10" and saved.json()["digest"] == {"at": 7, "hour": 7}
    _record("reach.saved.json", saved.json(), desk)
    assert client.put("/api/reach", json={"telegram": "loud"}).json()["code"] == "telegram_invalid"
    # DIR7: the ladder's Phone rung (the Phone app channel) as its own picker.
    phone_off = client.put("/api/reach", json={"phone_app": "off"})
    assert phone_off.status_code == 200 and phone_off.json()["channels"]["phone_app"]["on"] is False
    assert phone_off.json()["ladder"]["order"] == ["desk", "phone_app", "telegram", "call"]
    _record("reach.phone_off.json", phone_off.json(), desk)

    unpaired_again = client.delete("/api/reach/telegram/pair")
    assert unpaired_again.json() == {"paired": None}
    assert client.get("/api/reach").json()["channels"]["telegram"]["paired"] is None


def test_later_and_sent_to_telegram_reach_the_needs_you_row(desk) -> None:
    client, rig, ref = desk["client"], desk["rig"], desk["ref"]
    client.put("/api/reach/telegram/token", json={"token": TOKEN})
    code = client.post("/api/reach/telegram/pair").json()["code"]
    desk["telegram"].handle_update(update("pair", code=code))

    made = client.post("/api/reach/packages", json={"refs": [ref], "send": ["telegram"]})
    assert made.status_code == 201, made.text
    assert made.json()["telegram"]["message_id"] and "text" not in made.json()["telegram"]
    needs = compute_needs_you(programs=rig.service.needs_you_items())
    row = next(item for item in needs["unmutedItems"] if item["ref"] == ref)
    assert row["program"]["page"]["sent"]["via"] == "telegram" and row["counted"] is True
    _record("needs_you.sent.json", {"items": [row]}, desk)

    later = client.post("/api/reach/later", json={"ref": ref, "later": "later 2h"})
    assert later.status_code == 200, later.text
    assert later.json()["words"].startswith("Later · back at ") and later.json()["via"] == "desk"
    needs = compute_needs_you(programs=rig.service.needs_you_items())
    row = next(item for item in needs["unmutedItems"] if item["ref"] == ref)
    assert row["later"]["via"] == "desk" and row["counted"] is False
    assert ref not in [member["ref"] for member in needs["members"]]
    _record("needs_you.later.json", {"items": [row]}, desk)
    bad = client.post("/api/reach/later", json={"ref": ref, "later": "after the standup"})
    assert bad.status_code == 400 and bad.json()["detail"] == "Say a time, for example 14:30."
    nothing = client.post("/api/reach/digest")
    assert nothing.status_code == 409 and nothing.json()["code"] == "nothing_waits"
