"""HS-104-05 — session receipts: rollup math, tier honesty, the
pricing-table absent-row rule, the sample floor, the Stop-hook usage
leg, and the census over the reported/estimated call sites."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.coder_gate import GateConfig, run_stop_hook, summarize_transcript_usage
from holdspeak.db import Database, reset_database
from holdspeak.session_receipts import (
    PERCENTILE_SAMPLE_FLOOR,
    build_receipt,
    load_pricing,
)

REPO = Path(__file__).resolve().parents[2]


class Clock:
    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "receipts.db")
    clock = Clock()
    db.gate._now = clock
    yield db, clock
    reset_database()


def _hold_and_decide(db, clock, *, key, tool="Bash", wait=2.0, decision="approved"):
    db.gate.propose(
        proposal_id=key,
        session_key="claude:s1",
        agent="claude",
        tool=tool,
        args_sha256="a" * 64,
        args_head="{}",
        cwd="/tmp",
        ttl_seconds=600,
    )
    clock.now += wait
    db.gate.decide(key, decision=decision, decided_by="owner")


PRICING = {
    "pricing_schema": 1,
    "updated": "2026-07-26",
    "models": {"claude-fable-5": {"input_per_mtok": 3.0, "output_per_mtok": 15.0}},
}


def test_always_true_tier_from_hub_records(rig) -> None:
    db, clock = rig
    db.steering.record(session_key="claude:s1", text="do it", outcome="delivered")
    db.steering.record(session_key="claude:s1", text="again", outcome="refused")
    _hold_and_decide(db, clock, key="p1")
    receipt = build_receipt("claude:s1", db=db, pricing={})
    always = receipt["always"]
    assert always["provenance"] == "hub records"
    assert always["steers_delivered"] == 1
    assert always["steers_refused"] == 1
    assert always["holds"]["approved"] == 1
    assert always["elapsed_seconds"] is not None and always["elapsed_seconds"] > 0
    # No usage row: the reported and estimated tiers are ABSENT.
    assert "reported" not in receipt
    assert "estimated" not in receipt


def test_reported_tier_keeps_cache_figures_separate(rig) -> None:
    db, clock = rig
    db.gate.report_usage(
        session_key="claude:s1",
        model="claude-fable-5",
        input_tokens=1000,
        output_tokens=2000,
        cache_read_tokens=500,
        cache_creation_tokens=250,
    )
    receipt = build_receipt("claude:s1", db=db, pricing={})
    reported = receipt["reported"]
    assert reported["provenance"] == "authoritative"
    assert reported["input_tokens"] == 1000
    assert reported["cache_read_tokens"] == 500
    assert reported["cache_creation_tokens"] == 250
    assert "total_tokens" not in reported  # never summed into one number


def test_reported_tier_refused_for_an_unvouched_adapter(rig) -> None:
    db, clock = rig
    db.gate.report_usage(
        session_key="coder:pane1",  # tmux adapter: usage unavailable
        model="m",
        input_tokens=1,
        output_tokens=1,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    receipt = build_receipt("coder:pane1", db=db, pricing=PRICING)
    assert "reported" not in receipt  # the ledger cannot vouch
    assert "estimated" not in receipt


def test_estimate_renders_with_source_and_date_or_not_at_all(rig) -> None:
    db, clock = rig
    db.gate.report_usage(
        session_key="claude:s1",
        model="claude-fable-5",
        input_tokens=1_000_000,
        output_tokens=100_000,
        cache_read_tokens=0,
        cache_creation_tokens=0,
    )
    with_price = build_receipt("claude:s1", db=db, pricing=PRICING)
    estimated = with_price["estimated"]
    assert estimated["cost_usd"] == pytest.approx(3.0 + 1.5)
    assert estimated["source"] == "price table"
    assert estimated["as_of"] == "2026-07-26"

    without = build_receipt("claude:s1", db=db, pricing={"models": {}})
    assert "estimated" not in without  # absent, never $0.00


def test_sample_floor_boundary_19_vs_20(rig) -> None:
    db, clock = rig
    for i in range(PERCENTILE_SAMPLE_FLOOR - 1):
        _hold_and_decide(db, clock, key=f"a{i}", wait=1.0 + i * 0.1)
    below = build_receipt("claude:s1", db=db, pricing={})["tools"][0]
    assert below["samples"] == 19
    assert "p50_seconds" not in below and "max_seconds" in below

    _hold_and_decide(db, clock, key="a19", wait=9.0)
    at_floor = build_receipt("claude:s1", db=db, pricing={})["tools"][0]
    assert at_floor["samples"] == 20
    assert "p50_seconds" in at_floor and "p95_seconds" in at_floor
    assert "max_seconds" not in at_floor


def test_tools_never_blend(rig) -> None:
    db, clock = rig
    _hold_and_decide(db, clock, key="b1", tool="Bash")
    _hold_and_decide(db, clock, key="e1", tool="Edit")
    tools = build_receipt("claude:s1", db=db, pricing={})["tools"]
    assert [t["tool"] for t in tools] == ["Bash", "Edit"]


def test_load_pricing_missing_or_corrupt_is_no_prices(tmp_path) -> None:
    assert load_pricing(tmp_path / "none.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    assert load_pricing(bad) == {}


# ── the Stop-hook usage leg ──────────────────────────────────────────


def _transcript(tmp_path, lines) -> Path:
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(x) for x in lines))
    return path


def test_transcript_usage_sums_numbers_only(tmp_path) -> None:
    path = _transcript(
        tmp_path,
        [
            {"message": {"model": "claude-fable-5", "usage": {
                "input_tokens": 10, "output_tokens": 20,
                "cache_read_input_tokens": 5, "cache_creation_input_tokens": 2}},
             "secret": "NEVER-SENT"},
            {"message": {"model": "claude-fable-5", "usage": {
                "input_tokens": 1, "output_tokens": 2}}},
            {"not": "a message"},
        ],
    )
    usage = summarize_transcript_usage(path)
    assert usage == {
        "model": "claude-fable-5",
        "input_tokens": 11,
        "output_tokens": 22,
        "cache_read_tokens": 5,
        "cache_creation_tokens": 2,
    }


def test_stop_hook_reports_only_for_a_held_repo(tmp_path) -> None:
    path = _transcript(
        tmp_path,
        [{"message": {"model": "m", "usage": {"input_tokens": 1, "output_tokens": 1}}}],
    )
    posted: list[dict] = []

    def post(url, body, timeout):
        posted.append({"url": url, "body": body})
        return 200, {}

    payload = {
        "hook_event_name": "Stop",
        "session_id": "s1",
        "transcript_path": str(path),
        "cwd": str(tmp_path),
    }
    # Unarmed / unheld: silent, nothing leaves.
    assert run_stop_hook(payload, config=GateConfig(), http_post=post) is False
    assert posted == []

    armed = GateConfig(armed=True, repos={str(tmp_path): ["Bash"]})
    assert run_stop_hook(payload, config=armed, http_post=post) is True
    assert posted[0]["url"].endswith("/api/gate/usage")
    body = posted[0]["body"]
    assert set(body) == {
        "model", "input_tokens", "output_tokens",
        "cache_read_tokens", "cache_creation_tokens",
    }  # identity comes from the credential; only numbers + model ride the body


def test_stop_hook_failure_is_silent(tmp_path) -> None:
    path = _transcript(
        tmp_path,
        [{"message": {"model": "m", "usage": {"input_tokens": 1, "output_tokens": 1}}}],
    )

    def post(url, body, timeout):
        raise OSError("down")

    armed = GateConfig(armed=True, repos={str(tmp_path): ["Bash"]})
    payload = {
        "hook_event_name": "Stop",
        "session_id": "s1",
        "transcript_path": str(path),
        "cwd": str(tmp_path),
    }
    assert run_stop_hook(payload, config=armed, http_post=post) is False


# ── the routes ───────────────────────────────────────────────────────


@pytest.fixture
def route_rig(tmp_path, monkeypatch):
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.gate_routes import build_gate_router

    reset_database()
    db = Database(tmp_path / "receipt-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    from holdspeak.principals import Principal, PrincipalKind, agent_credentials

    app = FastAPI()
    app.state.agent_credentials = agent_credentials

    @app.middleware("http")
    async def agent_principal(request, call_next):
        request.state.principal = Principal(PrincipalKind.AGENT, "claude:s1")
        return await call_next(request)

    app.include_router(build_gate_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def test_usage_route_upserts_and_receipt_route_serves_tiers(route_rig, monkeypatch) -> None:
    db, client = route_rig
    response = client.post(
        "/api/gate/usage",
        json={
            "session_key": "claude:s1",
            "model": "claude-fable-5",
            "input_tokens": 100,
            "output_tokens": 200,
            "cache_read_tokens": 50,
            "cache_creation_tokens": 25,
        },
    )
    assert response.status_code == 200
    import holdspeak.session_receipts as sr

    monkeypatch.setattr(sr, "load_pricing", lambda path=None: PRICING)
    receipt = client.get("/api/sessions/claude:s1/receipt").json()
    assert receipt["reported"]["cache_read_tokens"] == 50
    assert receipt["estimated"]["source"] == "price table"
    assert receipt["always"]["steers_delivered"] == 0


def test_census_reported_and_estimated_call_sites() -> None:
    """Every reported/estimated figure's call site goes through
    require_capability — grep-pinned."""
    receipts = (REPO / "holdspeak/session_receipts.py").read_text(encoding="utf-8")
    assert "require_capability" in receipts
    assert receipts.index("require_capability(") < receipts.index('receipt["reported"]')
    routes = (REPO / "holdspeak/web/routes/system/gate_routes.py").read_text(encoding="utf-8")
    assert 'require_capability("claude-code-hooks", Capability.USAGE_TOKENS)' in routes
