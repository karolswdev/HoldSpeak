"""HS-112-02 — the Speak room speaks through the ONE delivery contract.

The room named Speak holds TALK, releases, and posts the transcript to
``POST /api/dictation/remote`` — the same route, pipeline, journal, kernel
warrant and idempotency claim the companion has always used. These tests pin
the three things the room added to that contract:

* the aimed AGENT refusal (``require_agent``): nothing awaiting means a NAMED
  terminal refusal, never a silent free-type into whatever is focused;
* a deterministic kernel refusal (``desktop_focus_unresolved``) comes back
  named and terminal, while an ambiguous mid-effect failure still parks
  ``pending`` and never replays;
* a delivery journals as ``dictation``; only an explicit REHEARSE writes
  ``dry_run``.

The rich pipeline is stubbed (as in ``test_web_routes_remote_dictation``) so
these isolate the route's wiring.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.desktop_typing import DesktopTypeRefused
from holdspeak.web.context import WebContext
from holdspeak.web.routes.dictation.pipeline import build_pipeline_router

PIPELINE = "holdspeak.web.routes.dictation.pipeline._run_dictation_dry_run_text"


@pytest.fixture(autouse=True)
def _stub_pipeline(monkeypatch):
    monkeypatch.setattr(
        PIPELINE, lambda text, *a, **k: {"final_text": f"[corrected] {text}"}
    )


@pytest.fixture(autouse=True)
def _default_macros_off(monkeypatch):
    from holdspeak.config import Config

    monkeypatch.setattr(Config, "load", classmethod(lambda cls: Config()))


@pytest.fixture(autouse=True)
def _no_selection_pin():
    from holdspeak.dictation_selection import clear_selected_record

    clear_selected_record()


def _ctx(**kw) -> WebContext:
    return WebContext(get_state=lambda: {}, **kw)


def _client(ctx: WebContext) -> TestClient:
    app = FastAPI()
    app.include_router(build_pipeline_router(ctx, project_doc_suggestions={}))
    return TestClient(app)


def _room_payload(**overrides) -> dict:
    """What the deck posts on TALK release (AIM = FOCUSED APP)."""
    payload = {
        "text": "ship it friday",
        "target_mode": "focused",
        # one id per utterance, exactly as the deck mints it
        "delivery_id": f"speak:{uuid.uuid4()}",
    }
    payload.update(overrides)
    return payload


# ── the room lands through the shared claim ──────────────────────────────────


def test_room_delivery_lands_once_under_a_retried_delivery_id(tmp_path):
    """The web client mints one id per utterance; a retry of it lands ONCE."""
    database = Database(tmp_path / "delivery.db")
    typed: list = []
    client = _client(
        _ctx(
            on_remote_dictation=lambda t, *, target="agent": typed.append((t, target)),
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    payload = _room_payload()

    first = client.post("/api/dictation/remote", json=payload)
    retry = client.post("/api/dictation/remote", json=payload)

    assert first.status_code == retry.status_code == 200
    assert first.json()["deduplicated"] is False
    assert retry.json()["deduplicated"] is True
    assert retry.json()["final_text"] == "[corrected] ship it friday"
    assert typed == [("[corrected] ship it friday", "focused")]


def test_room_delivery_returns_the_kernel_receipt_for_the_deck():
    """The hook's own receipt (method/target/operation_id) rides back so the
    deck can name where the words landed instead of guessing."""
    ctx = _ctx(
        on_remote_dictation=lambda t, *, target="agent": {
            "delivered": True,
            "method": "desktop.type_text",
            "target": "desktop-input:focus-3-abcd",
            "operation_id": "op-7",
        }
    )
    r = _client(ctx).post("/api/dictation/remote", json=_room_payload())

    assert r.status_code == 200
    assert r.json()["delivery"]["method"] == "desktop.type_text"
    assert r.json()["delivery"]["operation_id"] == "op-7"


# ── AIM = AGENT: the honest no-awaiting-agent refusal ────────────────────────


def test_aimed_agent_refuses_by_name_when_nothing_is_awaiting(monkeypatch):
    import holdspeak.agent_context as agent_context

    monkeypatch.setattr(
        agent_context, "get_recent_awaiting_agent_session", lambda **kw: None
    )
    delivered: list = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))

    r = _client(ctx).post(
        "/api/dictation/remote",
        json=_room_payload(target_mode="agent", require_agent=True),
    )

    assert r.status_code == 422
    body = r.json()
    assert body["refusal"] == "no_awaiting_agent"
    assert body["failure_category"] == "delivery_refused"
    assert body["delivered"] is False
    assert delivered == [], "a refused aim never reaches the delivery hook"


def test_aimed_agent_delivers_when_one_is_awaiting(monkeypatch):
    import holdspeak.agent_context as agent_context

    monkeypatch.setattr(
        agent_context,
        "get_recent_awaiting_agent_session",
        lambda **kw: object(),
    )
    delivered: list = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))

    r = _client(ctx).post(
        "/api/dictation/remote",
        json=_room_payload(target_mode="agent", require_agent=True),
    )

    assert r.status_code == 200
    assert r.json()["delivered"] is True
    assert delivered == ["[corrected] ship it friday"]


def test_unaimed_agent_send_keeps_the_companion_fallback(monkeypatch):
    """No ``require_agent`` -> the companion's byte-identical path: the hook is
    called and decides for itself (tmux pane, else desktop fallback)."""
    import holdspeak.agent_context as agent_context

    monkeypatch.setattr(
        agent_context, "get_recent_awaiting_agent_session", lambda **kw: None
    )
    delivered: list = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))

    r = _client(ctx).post(
        "/api/dictation/remote", json={"text": "ship it friday", "target_mode": "agent"}
    )

    assert r.status_code == 200
    assert delivered == ["[corrected] ship it friday"]


def test_require_agent_is_part_of_the_delivery_binding(tmp_path, monkeypatch):
    """The same id may not silently switch between an aimed and a fallback
    send — the destination is part of what the id promises."""
    import holdspeak.agent_context as agent_context

    monkeypatch.setattr(
        agent_context,
        "get_recent_awaiting_agent_session",
        lambda **kw: object(),
    )
    database = Database(tmp_path / "delivery.db")
    delivered: list = []
    client = _client(
        _ctx(
            on_remote_dictation=lambda t: delivered.append(t),
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    first = client.post(
        "/api/dictation/remote",
        json=_room_payload(target_mode="agent", require_agent=True, delivery_id="id-a-aimed"),
    )
    conflict = client.post(
        "/api/dictation/remote",
        json=_room_payload(target_mode="agent", delivery_id="id-a-aimed"),
    )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["failure_category"] == "delivery_conflict"
    assert delivered == ["[corrected] ship it friday"]


# ── AIM = FOCUSED APP: the kernel's own refusal, named in-flow ───────────────


def test_focus_unresolved_is_a_named_terminal_refusal(tmp_path):
    """`desktop_focus_unresolved` is decided BEFORE a keystroke leaves: the
    room gets the name, the claim closes, a retry replays the cached refusal
    instead of re-entering the kernel."""
    database = Database(tmp_path / "delivery.db")
    calls = 0

    def refuse(_text, *, target="agent"):
        nonlocal calls
        calls += 1
        raise DesktopTypeRefused("desktop_focus_unresolved", operation_id="op-1")

    client = _client(
        _ctx(
            on_remote_dictation=refuse,
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    payload = _room_payload()
    first = client.post("/api/dictation/remote", json=payload)
    retry = client.post("/api/dictation/remote", json=payload)

    assert first.status_code == retry.status_code == 422
    assert first.json()["refusal"] == "desktop_focus_unresolved"
    assert first.json()["delivered"] is False
    assert retry.json()["deduplicated"] is True
    assert calls == 1, "a terminal refusal never re-enters the kernel"


def test_driver_unavailable_is_also_named():
    def refuse(_text, *, target="agent"):
        raise DesktopTypeRefused("desktop_type_driver_unavailable")

    r = _client(_ctx(on_remote_dictation=refuse)).post(
        "/api/dictation/remote", json={"text": "hi", "target_mode": "focused"}
    )

    assert r.status_code == 422
    assert r.json()["refusal"] == "desktop_type_driver_unavailable"


def test_mid_effect_refusal_still_parks_pending_and_never_replays(tmp_path):
    """A driver that raised MID-type is ambiguous: we cannot prove nothing was
    typed, so the claim stays pending and the effect is never repeated."""
    database = Database(tmp_path / "delivery.db")
    calls = 0

    def half_typed(_text, *, target="agent"):
        nonlocal calls
        calls += 1
        raise DesktopTypeRefused("desktop_type_driver_failed")

    client = _client(
        _ctx(
            on_remote_dictation=half_typed,
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    payload = _room_payload()
    first = client.post("/api/dictation/remote", json=payload)
    retry = client.post("/api/dictation/remote", json=payload)

    assert first.status_code == retry.status_code == 425
    assert first.json()["error_code"] == "delivery_pending"
    assert calls == 1


def test_raw_delivery_refusal_is_named_too():
    """A REHEARSE receipt sent verbatim refuses with the same vocabulary."""

    def refuse(_text, *, target="agent"):
        raise DesktopTypeRefused("desktop_focus_unresolved")

    r = _client(_ctx(on_remote_dictation=refuse)).post(
        "/api/dictation/remote",
        json={"text": "exact words", "raw": True, "target_mode": "focused"},
    )

    assert r.status_code == 422
    assert r.json()["refusal"] == "desktop_focus_unresolved"


# ── the journal reads the truth: delivery = dictation, rehearse = dry_run ────


def test_delivery_journals_as_a_dictation_not_a_dry_run(monkeypatch):
    seen: dict = {}

    def capture(text, *a, **k):
        seen["journal_source"] = k.get("journal_source")
        return {"final_text": f"[corrected] {text}"}

    monkeypatch.setattr(PIPELINE, capture)
    _client(_ctx(on_remote_dictation=lambda t, *, target="agent": None)).post(
        "/api/dictation/remote", json=_room_payload()
    )

    assert seen["journal_source"] == "dictation"


def test_rehearsal_still_journals_as_a_dry_run(monkeypatch):
    seen: dict = {}

    def capture(text, *a, **k):
        seen["journal_source"] = k.get("journal_source", "dry_run")
        return {"final_text": text}

    monkeypatch.setattr(PIPELINE, capture)
    r = _client(_ctx()).post(
        "/api/dictation/dry-run", json={"utterance": "rehearse this"}
    )

    assert r.status_code == 200
    assert seen["journal_source"] == "dry_run"


def test_journal_source_reaches_the_recorder(tmp_path):
    """The helper actually threads the lane down to `journal.record`."""
    from holdspeak.web.routes.dictation._helpers import _run_dictation_dry_run_text

    recorded: list = []

    class _Recorder:
        repository = None

        def record(self, run, *, source, **kw):
            recorded.append(source)
            return None

    _run_dictation_dry_run_text(
        "spoken words",
        None,
        None,
        suggestions={},
        journal=_Recorder(),
        journal_source="dictation",
    )

    assert recorded == ["dictation"]
