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

import asyncio
import threading
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.principals import Principal, PrincipalKind
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


class _RemoteClient(TestClient):
    """Model the production clients: every committed send owns a stable claim."""

    def post(self, url, *args, **kwargs):
        payload = kwargs.get("json")
        if url == "/api/dictation/remote" and isinstance(payload, dict):
            payload = dict(payload)
            payload.setdefault("delivery_id", f"test:remote-{uuid.uuid4()}")
            kwargs["json"] = payload
        return super().post(url, *args, **kwargs)


def _client(ctx: WebContext, *, with_delivery_ids: bool = True) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def authenticated(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "remote-dictation-test")
        return await call_next(request)

    app.include_router(build_pipeline_router(ctx, project_doc_suggestions={}))
    return (_RemoteClient if with_delivery_ids else TestClient)(app)


def test_committed_remote_delivery_requires_a_client_stable_claim():
    r = _client(_ctx(), with_delivery_ids=False).post(
        "/api/dictation/remote", json={"text": "ship it once"}
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "delivery_id_required"


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


def test_changed_target_mode_under_same_id_is_refused(tmp_path):
    """HS-93-05: the payload binding covers the destination, not just the words.
    The same id with the same text but a different target_mode is a different
    request; it must 409 and never reach the hook a second time."""
    from holdspeak.db import Database

    database = Database(tmp_path / "delivery.db")
    delivered: list = []
    client = _client(
        _ctx(
            on_remote_dictation=lambda t, *, target="agent": delivered.append((t, target)),
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    first = client.post(
        "/api/dictation/remote",
        json={"text": "same words", "target_mode": "agent", "delivery_id": "id-1"},
    )
    conflict = client.post(
        "/api/dictation/remote",
        json={"text": "same words", "target_mode": "focused", "delivery_id": "id-1"},
    )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["failure_category"] == "delivery_conflict"
    assert delivered == [("[corrected] same words", "agent")]


def test_changed_raw_flag_under_same_id_is_refused(tmp_path):
    """raw toggles whether the pipeline runs; the same id must not silently
    switch between verbatim and processed delivery."""
    from holdspeak.db import Database

    database = Database(tmp_path / "delivery.db")
    delivered: list[str] = []
    client = _client(
        _ctx(
            on_remote_dictation=lambda t: delivered.append(t),
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    assert client.post(
        "/api/dictation/remote",
        json={"text": "exact words", "raw": True, "delivery_id": "id-raw"},
    ).status_code == 200

    conflict = client.post(
        "/api/dictation/remote",
        json={"text": "exact words", "delivery_id": "id-raw"},
    )

    assert conflict.status_code == 409
    assert conflict.json()["failure_category"] == "delivery_conflict"
    assert delivered == ["exact words"]


def test_terminal_failure_is_cached_and_an_explicit_new_id_may_retry(tmp_path, monkeypatch):
    """A known pre-effect failure (the pipeline itself) becomes a terminal
    failed Receipt: the same id replays the cached failure without re-running
    anything, and an explicit retry under a NEW id runs the effect exactly once."""
    from holdspeak.db import Database

    database = Database(tmp_path / "delivery.db")
    delivered: list[str] = []
    pipeline_calls = 0

    def exploding_pipeline(text, *a, **k):
        nonlocal pipeline_calls
        pipeline_calls += 1
        if pipeline_calls == 1:
            raise RuntimeError("rewrite backend unavailable")
        return {"final_text": f"[corrected] {text}"}

    monkeypatch.setattr(PIPELINE, exploding_pipeline)
    client = _client(
        _ctx(
            on_remote_dictation=lambda t: delivered.append(t),
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    payload = {"text": "keep these words", "delivery_id": "id-fail-1"}

    first = client.post("/api/dictation/remote", json=payload)
    replay = client.post("/api/dictation/remote", json=payload)
    retry = client.post(
        "/api/dictation/remote",
        json={"text": "keep these words", "delivery_id": "id-fail-2"},
    )

    assert first.status_code == replay.status_code == 500
    assert replay.json()["deduplicated"] is True
    assert pipeline_calls == 2, "the cached failure must not re-run the pipeline"
    assert retry.status_code == 200
    assert retry.json()["deduplicated"] is False
    assert delivered == ["[corrected] keep these words"]


def test_pending_claim_refuses_a_changed_payload_too(tmp_path):
    """An indeterminate delivery stays pending AND keeps its payload binding:
    reusing the pending id for different words is a 409 conflict, not a
    silent replacement of the uncertain effect."""
    from holdspeak.db import Database

    database = Database(tmp_path / "delivery.db")
    calls = 0

    def fail_once(_text: str) -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("target stopped")

    client = _client(
        _ctx(
            on_remote_dictation=fail_once,
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    pending = client.post(
        "/api/dictation/remote",
        json={"text": "original words", "delivery_id": "id-pending"},
    )
    changed = client.post(
        "/api/dictation/remote",
        json={"text": "different words", "delivery_id": "id-pending"},
    )
    same = client.post(
        "/api/dictation/remote",
        json={"text": "original words", "delivery_id": "id-pending"},
    )

    assert pending.status_code == 425
    assert changed.status_code == 409
    assert same.status_code == 425, "indeterminate stays pending; never re-run"
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


def test_delivery_failure_stays_pending_and_never_autonomously_retries():
    def boom(_text: str):
        raise RuntimeError("no dictation target focused")

    ctx = _ctx(on_remote_dictation=boom)
    r = _client(ctx).post("/api/dictation/remote", json={"text": "hi"})
    assert r.status_code == 425
    assert r.json()["error_code"] == "delivery_pending"
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


def test_pre_delivery_fence_refusal_cannot_close_the_speech_parent_succeeded(
    tmp_path, monkeypatch
):
    """A gate loser is a refused parent, not a clean return from `with entry`."""
    from holdspeak.db import Database
    from holdspeak.kernel.runtime import _configure

    database = Database(tmp_path / "pre-delivery-fence.db")
    database.profiles.upsert(
        profile_id="pre-delivery-provider",
        name="pre-delivery-provider",
        kind="openAICompatible",
        base_url="https://pre-delivery.invalid/v1",
        model="pre-delivery-model",
    )
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)
    from holdspeak.config import Config

    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router"]
    config.dictation.runtime.profile_id = "pre-delivery-provider"
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))
    delivered: list[str] = []

    def cancel_before_handoff(text, *args, **kwargs):
        kwargs["fence"].cancel()
        return {"final_text": f"[corrected] {text}"}

    monkeypatch.setattr(PIPELINE, cancel_before_handoff)
    response = _client(
        _ctx(
            on_remote_dictation=lambda text: delivered.append(text),
            dictation_deliveries=database.dictation_deliveries,
        )
    ).post("/api/dictation/remote", json={"text": "cancel before delivery"})

    assert response.status_code == 422
    assert response.json()["refusal"] == "speech_session_not_live"
    assert delivered == []
    with database._connection() as connection:
        parent = connection.execute(
            "SELECT operation_id FROM kernel_operations "
            "WHERE name='dictation.session'"
        ).fetchone()
        receipt = connection.execute(
            "SELECT outcome FROM kernel_receipts WHERE operation_id=?",
            (parent["operation_id"],),
        ).fetchone()
    assert receipt["outcome"] == "refused"


def test_remote_effect_handoff_settles_success_before_cancellation_can_win(
    tmp_path, monkeypatch
):
    """Effect-first owns delivery and the speech parent in one election."""
    from holdspeak.db import Database
    from holdspeak.kernel.runtime import _configure
    import holdspeak.web.routes.dictation.pipeline as pipeline_routes

    database = Database(tmp_path / "remote-handoff-race.db")
    database.profiles.upsert(
        profile_id="remote-handoff-provider",
        name="remote-handoff-provider",
        kind="openAICompatible",
        base_url="https://remote-handoff.invalid/v1",
        model="remote-handoff-model",
    )
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)
    from holdspeak.config import Config

    config = Config()
    config.dictation.pipeline.enabled = True
    config.dictation.pipeline.stages = ["intent-router"]
    config.dictation.runtime.profile_id = "remote-handoff-provider"
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))

    captured: dict[str, object] = {}
    entry_ready = threading.Event()
    delivery_entered = threading.Event()
    release_delivery = threading.Event()
    cancellation_started = threading.Event()
    cancellation_done = threading.Event()
    typed: list[str] = []
    response: list[object] = []
    original_open = pipeline_routes._open_text_entry

    def capture_entry(*args, **kwargs):
        snapshot, entry = original_open(*args, **kwargs)
        captured["entry"] = entry
        entry_ready.set()
        return snapshot, entry

    def blocking_delivery(text: str) -> None:
        delivery_entered.set()
        assert release_delivery.wait(5), "test never released delivery"
        typed.append(text)

    monkeypatch.setattr(pipeline_routes, "_open_text_entry", capture_entry)
    client = _client(
        _ctx(
            on_remote_dictation=blocking_delivery,
            dictation_deliveries=database.dictation_deliveries,
        )
    )
    request_thread = threading.Thread(
        target=lambda: response.append(
            client.post("/api/dictation/remote", json={"text": "one handoff"})
        )
    )
    request_thread.start()
    assert entry_ready.wait(5), "speech entry was never captured"
    assert delivery_entered.wait(5), "delivery never won the election"

    def cancel() -> None:
        cancellation_started.set()
        captured["entry"].cancel()
        cancellation_done.set()

    cancel_thread = threading.Thread(target=cancel)
    cancel_thread.start()
    assert cancellation_started.wait(5)
    assert not cancellation_done.wait(0.05), "cancellation crossed an active handoff"
    release_delivery.set()
    request_thread.join(5)
    cancel_thread.join(5)

    assert response and response[0].status_code == 200
    assert typed == ["[corrected] one handoff"]
    assert cancellation_done.is_set()
    with database._connection() as connection:
        receipt = connection.execute(
            "SELECT r.outcome FROM kernel_receipts r "
            "JOIN kernel_operations o ON o.operation_id=r.operation_id "
            "WHERE o.name='dictation.session' ORDER BY o.created_at DESC LIMIT 1"
        ).fetchone()
    assert receipt["outcome"] == "succeeded"


def test_accepted_delivery_survives_request_cancellation_to_terminal_claim(
    tmp_path, monkeypatch
):
    """Transport cancellation cannot abandon accepted idempotent work as pending."""
    from holdspeak.db import Database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.principals import Principal, PrincipalKind

    database = Database(tmp_path / "committed-disconnect.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda: database)
    _configure(database)
    started = threading.Event()
    release = threading.Event()
    delivered = threading.Event()
    typed: list[str] = []

    def slow_pipeline(text, *args, **kwargs):
        started.set()
        assert release.wait(5), "test never released committed processing"
        return {"final_text": f"[corrected] {text}"}

    def deliver(text: str) -> None:
        typed.append(text)
        delivered.set()

    monkeypatch.setattr(PIPELINE, slow_pipeline)
    router = build_pipeline_router(
        _ctx(
            on_remote_dictation=deliver,
            dictation_deliveries=database.dictation_deliveries,
        ),
        project_doc_suggestions={},
    )
    endpoint = next(
        route.endpoint
        for route in router.routes
        if getattr(route, "path", "") == "/api/dictation/remote"
    )
    request = type(
        "Request",
        (),
        {
            "state": type(
                "State",
                (),
                {
                    "principal": Principal(
                        PrincipalKind.OWNER, "committed-disconnect-test"
                    )
                },
            )()
        },
    )()

    async def scenario() -> None:
        task = asyncio.create_task(
            endpoint(
                request,
                {
                    "text": "finish after disconnect",
                    "delivery_id": "disconnect:accepted-1",
                },
            )
        )
        assert await asyncio.to_thread(started.wait, 5), "processing never started"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        release.set()
        assert await asyncio.to_thread(delivered.wait, 5), "delivery never completed"
        for _ in range(100):
            claim = database.dictation_deliveries.get("disconnect:accepted-1")
            if claim is not None and claim["status"] != "pending":
                break
            await asyncio.sleep(0.01)

    try:
        asyncio.run(scenario())
    finally:
        release.set()

    assert typed == ["[corrected] finish after disconnect"]
    claim = database.dictation_deliveries.get("disconnect:accepted-1")
    assert claim is not None
    assert claim["status"] == "succeeded"
    assert claim["response"]["delivered"] is True
