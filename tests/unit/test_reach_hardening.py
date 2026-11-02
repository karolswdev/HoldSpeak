"""Reach hardening (Astra's post-merge check, 2026-11-01; ruling the same day).

- 5 wrong pairing codes and the code is void: a new one is needed.
- Revoke shares the answer's lock: an answer in flight ends before Revoke
  returns; after it, the page is gone.
- A decided item of a page reads as its outcome only and serves no evidence.
- A prepared send's page shows the whole frozen payload, word for word, or
  it offers no Send.
- One redaction (``reach_redact.reach_line``) for every Telegram message and
  every page line: home paths, diff headers, password-shaped pairs.
"""
from __future__ import annotations

import threading
import time

import pytest

from holdspeak.services.reach_redact import reach_line
from tests.unit.test_reach_telegram import OWNER_CHAT, Desk, keystore, update  # noqa: F401  (autouse keystore)
from tests.integration.program_rig import OWNER


# ── pairing ──────────────────────────────────────────────────────────

def test_five_wrong_codes_void_the_pairing_code(tmp_path) -> None:
    from holdspeak.services.telegram_reach import PAIR_WRONG_MAX, paired_chat

    desk = Desk(tmp_path)
    desk.telegram.save_token(OWNER, "6000000001:AAH-fake-token-for-the-rig-only-0123456789")
    code = desk.telegram.start_pairing(OWNER)["code"]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(PAIR_WRONG_MAX):
        assert desk.telegram.handle_update(update("pair", code=wrong))["ok"] is False
    assert desk.telegram.handle_update(update("pair", code=code))["ok"] is False
    assert paired_chat() is None
    fresh = desk.telegram.start_pairing(OWNER)["code"]
    assert desk.telegram.handle_update(update("pair", code=fresh))["ok"] is True


# ── revoke ───────────────────────────────────────────────────────────

def test_revoke_waits_for_an_answer_in_flight_and_ends_the_page(tmp_path) -> None:
    from holdspeak.services import briefing_service

    desk = Desk(tmp_path)
    _pid, item = desk.core()
    ref = f"program:{item['program_id']}:{item['id']}"
    made = desk.briefing.make(OWNER, [ref])
    done = threading.Event()
    with briefing_service._LOCK:  # an answer in flight holds the lock
        thread = threading.Thread(target=lambda: (desk.briefing.revoke(OWNER, made["id"]), done.set()))
        thread.start()
        time.sleep(0.2)
        assert not done.is_set()  # Revoke does not return while the answer runs
    thread.join(5)
    assert done.is_set()
    with pytest.raises(Exception):
        desk.briefing.answer(made["token"], ref, "go_on")


# ── a decided item ───────────────────────────────────────────────────

def test_a_decided_item_reads_as_its_outcome_and_serves_no_evidence(tmp_path) -> None:
    desk = Desk(tmp_path)
    _pid, item = desk.core()
    ref = f"program:{item['program_id']}:{item['id']}"
    made = desk.briefing.make(OWNER, [ref])
    before = desk.briefing.read(made["token"])["items"][0]
    panes = [row["pane"] for row in before.get("evidence") or []]
    assert panes, before
    choice = before["choices"][0]["id"]
    desk.briefing.answer(made["token"], ref, choice)
    after = desk.briefing.read(made["token"])["items"][0]
    assert after["state"] == "decided" and "evidence" not in after and "note" not in after
    with pytest.raises(Exception) as refused:
        desk.briefing.evidence(made["token"], ref, panes[0])
    assert "decided" in str(getattr(refused.value, "detail", refused.value))


# ── the Send preview ─────────────────────────────────────────────────

def _send_body(tmp_path, payload: str) -> dict:
    from holdspeak.db import Database
    from holdspeak.services.briefing_sources import SendSource

    source = SendSource(Database(tmp_path / "hub.db"))
    return source.body("send:chs_1", {"payload": payload, "destination_name": "Team folder",
                                      "document_json": '{"title": "Update"}', "created_at": ""})


def test_the_send_page_shows_the_whole_payload_word_for_word(tmp_path) -> None:
    payload = "\n".join([f"  line {n}: " + "x" * 250 for n in range(30)] + ["", "the sentinel line"])
    body = _send_body(tmp_path, payload)
    assert body["preview"]["lines"] == payload.splitlines() and body["preview"]["whole"] is True
    assert [row["id"] for row in body["choices"]] == ["send", "discard"]


def test_a_payload_a_page_cannot_show_whole_offers_no_send(tmp_path) -> None:
    from holdspeak.services.briefing_sources import SEND_FROM_DESK, SendSource
    from holdspeak.services.errors import ServiceError

    for payload in ("See /Users/someone/private/notes for the numbers.", "x\n" * 500):
        body = _send_body(tmp_path, payload)
        assert [row["id"] for row in body["choices"]] == ["discard"] and body["preview"]["lines"] == []
        assert SEND_FROM_DESK in body["note"]
        with pytest.raises(ServiceError) as refused:
            SendSource(None).decide("send:chs_1", {"payload": payload}, "send", via="page")
        assert refused.value.code == "not_offered"


# ── one redaction ────────────────────────────────────────────────────

@pytest.mark.parametrize("text, kept, gone", [
    ("Program diff --git a/private b/private", "a change", "diff --git"),
    ("notes in /Users/review/private/notes", "~/private/notes", "/Users/review"),
    ("@@ -1,2 +3,4 @@ the change", "a change", "@@"),
    ("db password: hunter2x", "db", "hunter2x"),
    ("api_key sk-12345678", "api_key", "sk-12345678"),
])
def test_one_redaction_for_every_reach_line(text, kept, gone) -> None:
    out = reach_line(text)
    assert kept in out and gone not in out, out


def test_plain_words_are_kept() -> None:
    for text in ("a token of thanks", "the secret plan", "see ~/notes and /tmp/x"):
        assert reach_line(text) == text


def test_the_digest_and_a_page_line_go_through_it(tmp_path) -> None:
    desk = Desk(tmp_path)
    desk.pair()
    desk.bot.calls.clear()
    desk.telegram.digest([{"kind": "core", "program_title": "diff --git a/private b/private",
                           "ordinal": 1}, {"kind": "core", "program_title": "/Users/review/private/notes",
                                            "ordinal": 2}])
    (sent,) = desk.bot.of("sendMessage")
    assert "diff --git" not in sent["text"] and "/Users/review" not in sent["text"]
    _pid, item = desk.core()
    ref = f"program:{item['program_id']}:{item['id']}"
    made = desk.briefing.make(OWNER, [ref], kind="digest", lines=["The db password: hunter2x is in the note."])
    page = desk.briefing.read(made["token"])
    assert all("hunter2x" not in line for line in page["package"]["lines"]), page["package"]["lines"]
