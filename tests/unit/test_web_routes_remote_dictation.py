"""HSM-13-01 — the remote-dictation inject route (``POST /api/dictation/remote``).

A companion client (iPhone/iPad) posts a dictated answer; the route runs it through
the rich dictation pipeline and delivers the *processed* text into the desktop's
dictation target via the injected ``on_remote_dictation`` hook. Auth is the runtime's
existing web-auth middleware (Bearer token, off-loopback) — not re-tested here.

The pipeline call is monkeypatched so these tests isolate the route's wiring (delegate
→ deliver → return); the pipeline's own transforms are covered by the dry-run tests
that share the same ``_run_dictation_dry_run_text`` helper.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.web.context import WebContext
from holdspeak.web.routes.dictation.pipeline import build_pipeline_router

PIPELINE = "holdspeak.web.routes.dictation.pipeline._run_dictation_dry_run_text"


@pytest.fixture(autouse=True)
def _stub_pipeline(monkeypatch):
    # The rich pipeline returns the corrected/blocked/plugin-applied text as
    # ``final_text``; stub it to a deterministic transform so we can assert the route
    # delivers the PROCESSED text, not the raw input.
    monkeypatch.setattr(PIPELINE, lambda text, *a, **k: {"final_text": f"[corrected] {text}"})


@pytest.fixture(autouse=True)
def _default_macros_off(monkeypatch):
    # HSM-18-02: the remote route now consults ``Config.load()`` to fire voice-command
    # macros. Default macros OFF for hermetic, byte-identical plain-dictation tests; the
    # macro test below overrides this with an enabled config.
    from holdspeak.config import Config

    monkeypatch.setattr(Config, "load", classmethod(lambda cls: Config()))


def _ctx(**kw) -> WebContext:
    return WebContext(get_state=lambda: {}, **kw)


def _client(ctx: WebContext) -> TestClient:
    app = FastAPI()
    app.include_router(build_pipeline_router(ctx, project_doc_suggestions={}))
    return TestClient(app)


def test_processes_through_pipeline_and_delivers():
    delivered: list[str] = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))
    r = _client(ctx).post("/api/dictation/remote", json={"text": "ship it friday"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["delivered"] is True
    # The pipeline transform was applied (not raw transcript) ...
    assert body["final_text"] == "[corrected] ship it friday"
    # ... and that PROCESSED text is what got delivered into the coder.
    assert delivered == ["[corrected] ship it friday"]


def test_delivery_identity_returns_cached_receipt_without_typing_twice(tmp_path):
    from holdspeak.db import Database

    database = Database(tmp_path / "delivery.db")
    delivered: list[str] = []
    ctx = _ctx(
        on_remote_dictation=lambda text: delivered.append(text),
        dictation_deliveries=database.dictation_deliveries,
    )
    client = _client(ctx)
    payload = {"text": "ship it friday", "delivery_id": "device:attempt-1"}

    first = client.post("/api/dictation/remote", json=payload)
    reconnect = client.post("/api/dictation/remote", json=payload)

    assert first.status_code == reconnect.status_code == 200
    assert first.json()["deduplicated"] is False
    assert reconnect.json()["deduplicated"] is True
    assert reconnect.json()["delivery_id"] == "device:attempt-1"
    assert reconnect.json()["final_text"] == "[corrected] ship it friday"
    assert delivered == ["[corrected] ship it friday"]


def test_delivery_identity_refuses_silent_retargeting(tmp_path):
    from holdspeak.db import Database

    database = Database(tmp_path / "delivery.db")
    delivered: list[str] = []
    client = _client(
        _ctx(
            on_remote_dictation=lambda text: delivered.append(text),
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    assert client.post(
        "/api/dictation/remote",
        json={"text": "first words", "delivery_id": "same-id"},
    ).status_code == 200

    conflict = client.post(
        "/api/dictation/remote",
        json={"text": "different words", "delivery_id": "same-id"},
    )

    assert conflict.status_code == 409
    assert conflict.json()["failure_category"] == "delivery_conflict"
    assert delivered == ["[corrected] first words"]


def test_failed_delivery_identity_never_replays_implicitly(tmp_path):
    from holdspeak.db import Database

    database = Database(tmp_path / "delivery.db")
    calls = 0

    def fail_after_one_call(_text: str) -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("target stopped")

    client = _client(
        _ctx(
            on_remote_dictation=fail_after_one_call,
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    payload = {"text": "keep this", "delivery_id": "failed-id"}
    first = client.post("/api/dictation/remote", json=payload)
    replay = client.post("/api/dictation/remote", json=payload)

    assert first.status_code == replay.status_code == 425
    assert first.json()["error_code"] == "delivery_pending"
    assert replay.json()["error_code"] == "delivery_pending"
    assert calls == 1


def test_without_delivery_hook_processes_only():
    r = _client(_ctx()).post("/api/dictation/remote", json={"text": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["delivered"] is False                 # nothing to deliver into
    assert body["final_text"] == "[corrected] hello"  # still pipeline-processed


def test_rejects_empty_text():
    r = _client(_ctx()).post("/api/dictation/remote", json={"text": "   "})
    assert r.status_code == 400


def test_rejects_non_object_target():
    r = _client(_ctx()).post("/api/dictation/remote", json={"text": "hi", "target": "nope"})
    assert r.status_code == 400


def test_delivery_failure_surfaces_502_not_autonomous_retry():
    def boom(_text: str):
        raise RuntimeError("no dictation target focused")

    ctx = _ctx(on_remote_dictation=boom)
    r = _client(ctx).post("/api/dictation/remote", json={"text": "hi"})
    assert r.status_code == 502
    assert r.json()["delivered"] is False


# ── HSM-15-01a: the explicit target_mode field ────────────────────────────────


def test_default_target_mode_calls_hook_positionally_byte_identical():
    """An unset target_mode delivers exactly as before: the hook is called with the
    processed text positionally and NO `target` keyword (a plain str hook works)."""
    calls: list = []

    def hook(text):  # NOTE: accepts only the positional text — the legacy signature
        calls.append(text)

    ctx = _ctx(on_remote_dictation=hook)
    r = _client(ctx).post("/api/dictation/remote", json={"text": "ship it"})
    assert r.status_code == 200
    assert r.json()["delivered"] is True
    assert calls == ["[corrected] ship it"]


def test_target_mode_focused_threads_through_to_hook():
    """target_mode="focused" threads `target="focused"` to the delivery hook."""
    seen: list = []

    def hook(text, *, target="agent"):
        seen.append((text, target))

    ctx = _ctx(on_remote_dictation=hook)
    r = _client(ctx).post(
        "/api/dictation/remote", json={"text": "freeform note", "target_mode": "focused"}
    )
    assert r.status_code == 200
    assert r.json()["delivered"] is True
    assert seen == [("[corrected] freeform note", "focused")]


def test_explicit_agent_target_mode_does_not_thread_keyword():
    """target_mode="agent" is the default path: hook called positionally only."""
    calls: list = []

    def hook(text):  # legacy positional-only hook would break if a kwarg were passed
        calls.append(text)

    ctx = _ctx(on_remote_dictation=hook)
    r = _client(ctx).post(
        "/api/dictation/remote", json={"text": "answer", "target_mode": "agent"}
    )
    assert r.status_code == 200
    assert calls == ["[corrected] answer"]


def test_rejects_unknown_target_mode():
    r = _client(_ctx()).post(
        "/api/dictation/remote", json={"text": "hi", "target_mode": "nonsense"}
    )
    assert r.status_code == 400


# ── HSM-18-02: voice command macros fire on the remote relay (not just the local path) ──


def test_voice_macro_fires_on_relay_and_is_not_dictated(monkeypatch):
    """A configured, enabled macro keyword posted over the relay FIRES (it is not
    dictated as prose). This is the exact seam that shipped broken: the local path
    dispatched macros, the remote path went straight to the dry-run. A ``type_text``
    macro free-types into the focused Mac app via the relay; the response carries the
    ``fired`` object the companion renders as the macro-object chip."""
    from holdspeak.config import Config, MacrosConfig, VoiceMacro, VoiceMacroAction

    cfg = Config()
    cfg.dictation.macros = MacrosConfig(
        enabled=True, items=[VoiceMacro("standup", VoiceMacroAction("type_text", "## Standup"))]
    )
    monkeypatch.setattr(Config, "load", classmethod(lambda cls: cfg))

    typed: list = []
    ctx = _ctx(on_remote_dictation=lambda t, *, target="agent": typed.append((t, target)))
    r = _client(ctx).post("/api/dictation/remote", json={"text": "standup"})

    assert r.status_code == 200
    body = r.json()
    assert body["fired"]["kind"] == "type_text"
    assert body["fired"]["keyword"] == "standup"
    assert body["fired"]["ok"] is True
    assert body["final_text"] == ""  # NOT run through the dictation pipeline
    # the macro typed into the focused app via the relay, not delivered as a dictation answer
    assert typed == [("## Standup", "focused")]


def test_no_macro_match_falls_through_to_dictation():
    """With macros off (the autouse default), a normal utterance is dictated exactly as
    before this fix: no ``fired`` key, pipeline-processed, delivered into the coder."""
    delivered: list = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))
    r = _client(ctx).post("/api/dictation/remote", json={"text": "ship it friday"})

    assert r.status_code == 200
    body = r.json()
    assert "fired" not in body
    assert body["final_text"] == "[corrected] ship it friday"
    assert delivered == ["[corrected] ship it friday"]


def test_raw_delivers_verbatim_no_pipeline():
    """HSM-18-01 — ``raw: true`` types EXACTLY the given text. A client holding a
    dry-run receipt sends the previewed ``final_text``; re-running the pipeline would
    make the receipt a lie (the rewrite is not idempotent)."""
    delivered: list = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))
    r = _client(ctx).post(
        "/api/dictation/remote", json={"text": "[corrected] ship it", "raw": True}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["delivered"] is True
    assert body["final_text"] == "[corrected] ship it"   # verbatim, NOT re-corrected
    assert delivered == ["[corrected] ship it"]


def test_raw_skips_macro_dispatch(monkeypatch):
    """A raw send never fires a macro — the receipt's words type as words even if one
    of them is a configured keyword."""
    from holdspeak.config import Config, MacrosConfig, VoiceMacro, VoiceMacroAction

    cfg = Config()
    cfg.dictation.macros = MacrosConfig(
        enabled=True, items=[VoiceMacro("standup", VoiceMacroAction("type_text", "## Standup"))]
    )
    monkeypatch.setattr(Config, "load", classmethod(lambda cls: cfg))

    delivered: list = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))
    r = _client(ctx).post("/api/dictation/remote", json={"text": "standup", "raw": True})
    assert r.status_code == 200
    body = r.json()
    assert "fired" not in body
    assert body["final_text"] == "standup"
    assert delivered == ["standup"]


def test_raw_threads_focused_target_mode():
    """raw + target_mode="focused" free-types the verbatim text into the focused app."""
    typed: list = []
    ctx = _ctx(on_remote_dictation=lambda t, *, target="agent": typed.append((t, target)))
    r = _client(ctx).post(
        "/api/dictation/remote",
        json={"text": "exact words", "raw": True, "target_mode": "focused"},
    )
    assert r.status_code == 200
    assert typed == [("exact words", "focused")]


def test_raw_absent_stays_byte_identical():
    """No ``raw`` key -> the pre-18-01 pipeline path, unchanged."""
    delivered: list = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))
    r = _client(ctx).post("/api/dictation/remote", json={"text": "ship it"})
    assert r.status_code == 200
    assert r.json()["final_text"] == "[corrected] ship it"
    assert delivered == ["[corrected] ship it"]


def test_selection_pin_grounds_the_remote_dictation(monkeypatch):
    """HSM-18-05 — the pre-briefing loop closes on the remote lane. A pending
    "Dictate with this" pin is consumed (one-shot) and its activity context is
    threaded into the pipeline call, exactly as the local runner does (HS-53-07)."""
    from holdspeak.dictation_selection import clear_selected_record, set_selected_record

    seen: dict = {}

    def capture(text, *a, **k):
        seen["activity_context"] = k.get("activity_context")
        return {"final_text": f"[corrected] {text}"}

    monkeypatch.setattr(PIPELINE, capture)

    class _Ctx:
        records = [{"id": 42, "title": "the PR"}]
        selected_record_id = 42

        def to_dict(self):
            return {"records": self.records, "selected_record_id": 42}

    captured_build: dict = {}

    def fake_build(*, limit, refresh, selected_record_id):
        captured_build["selected_record_id"] = selected_record_id
        return _Ctx()

    import holdspeak.activity_context as activity_mod

    monkeypatch.setattr(activity_mod, "build_activity_context", fake_build)

    set_selected_record(42)
    try:
        r = _client(_ctx()).post("/api/dictation/remote", json={"text": "reply to that"})
        assert r.status_code == 200
        assert captured_build["selected_record_id"] == 42
        assert seen["activity_context"] == {"records": [{"id": 42, "title": "the PR"}],
                                            "selected_record_id": 42}

        # The pin is one-shot: a second remote dictation gets no grounding.
        seen.clear()
        r = _client(_ctx()).post("/api/dictation/remote", json={"text": "and again"})
        assert r.status_code == 200
        assert seen["activity_context"] is None
    finally:
        clear_selected_record()


def test_no_pin_keeps_remote_dictation_byte_identical():
    """No pending pin -> activity_context is None -> the pre-18-05 call, unchanged."""
    from holdspeak.dictation_selection import clear_selected_record

    clear_selected_record()
    delivered: list = []
    ctx = _ctx(on_remote_dictation=lambda t: delivered.append(t))
    r = _client(ctx).post("/api/dictation/remote", json={"text": "plain words"})
    assert r.status_code == 200
    assert r.json()["final_text"] == "[corrected] plain words"
    assert delivered == ["[corrected] plain words"]
