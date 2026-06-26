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
