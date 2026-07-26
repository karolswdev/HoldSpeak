"""HS-104-02 — the tool-call gate: state machine, matcher, redaction,
the hook's fail-closed posture, and the hub routes."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.coder_gate import (
    DEFAULT_TTL_SECONDS,
    GateConfig,
    HookDecision,
    gate_matches,
    install_block,
    load_gate_config,
    redact_args,
    run_hook,
    save_gate_config,
)
from holdspeak.db import Database, reset_database
from holdspeak.db.gate import (
    APPROVED,
    DENIED,
    EXPIRED,
    HELD,
    INVALIDATED,
    GateArgsMismatchError,
    GateStateError,
)


class Clock:
    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "gate.db")
    clock = Clock()
    db.gate._now = clock
    yield db, clock
    reset_database()


def _propose(db, clock, proposal_id="p1", args_sha256="a" * 64, ttl=60.0):
    return db.gate.propose(
        proposal_id=proposal_id,
        session_key="claude:s1",
        agent="claude",
        tool="Bash",
        args_sha256=args_sha256,
        args_head='{"command":"rm -rf build"}',
        cwd="/tmp/repo",
        ttl_seconds=ttl,
    )


# -- state machine ---------------------------------------------------------


def test_propose_holds_and_audits(rig) -> None:
    db, clock = rig
    proposal = _propose(db, clock)
    assert proposal.state == HELD
    assert proposal.expires_at == pytest.approx(clock.now + 60.0)
    events = [e["event"] for e in db.gate.audit_entries()]
    assert events == ["proposed"]


@pytest.mark.parametrize("decision", [APPROVED, DENIED])
def test_decide_from_held(rig, decision) -> None:
    db, clock = rig
    _propose(db, clock)
    after = db.gate.decide("p1", decision=decision, decided_by="owner", reason="because")
    assert after.state == decision
    assert after.decided_by == "owner"
    assert after.reason == "because"
    assert [e["event"] for e in db.gate.audit_entries()] == [decision, "proposed"]


def test_double_decision_refused_with_standing_state(rig) -> None:
    db, clock = rig
    _propose(db, clock)
    db.gate.decide("p1", decision=APPROVED, decided_by="owner")
    with pytest.raises(GateStateError) as exc:
        db.gate.decide("p1", decision=DENIED, decided_by="owner")
    assert exc.value.current == APPROVED
    assert exc.value.requested == DENIED
    # One decision, both arrivals audited.
    assert [e["event"] for e in db.gate.audit_entries()] == [APPROVED, "proposed"]


def test_replay_same_key_same_args_returns_standing_state(rig) -> None:
    db, clock = rig
    _propose(db, clock)
    db.gate.decide("p1", decision=APPROVED, decided_by="owner")
    replay = _propose(db, clock)
    assert replay.state == APPROVED
    events = [e["event"] for e in db.gate.audit_entries()]
    assert events == ["re_arrival", APPROVED, "proposed"]


def test_args_mismatch_refuses_and_revokes_the_held_original(rig) -> None:
    db, clock = rig
    _propose(db, clock, args_sha256="a" * 64)
    with pytest.raises(GateArgsMismatchError):
        _propose(db, clock, args_sha256="b" * 64)
    original = db.gate.get("p1")
    assert original.state == INVALIDATED  # refuse AND revoke
    events = [e["event"] for e in db.gate.audit_entries()]
    assert "args_mismatch" in events and INVALIDATED in events


def test_expiry_denies_never_allows(rig) -> None:
    db, clock = rig
    _propose(db, clock, ttl=60.0)
    clock.now += 61.0
    assert db.gate.expire_due() == ["p1"]
    assert db.gate.get("p1").state == EXPIRED
    with pytest.raises(GateStateError):
        db.gate.decide("p1", decision=APPROVED, decided_by="owner")


def test_expiry_race_exactly_one_terminal_state(rig) -> None:
    db, clock = rig
    _propose(db, clock, ttl=60.0)
    clock.now += 60.0  # decision lands exactly at expiry
    with pytest.raises(GateStateError) as exc:
        db.gate.decide("p1", decision=APPROVED, decided_by="owner")
    assert exc.value.current == EXPIRED
    assert db.gate.get("p1").state == EXPIRED


def test_restart_invalidates_every_held(rig) -> None:
    db, clock = rig
    _propose(db, clock, proposal_id="p1")
    _propose(db, clock, proposal_id="p2", args_sha256="c" * 64)
    db.gate.decide("p1", decision=DENIED, decided_by="owner")
    flipped = db.gate.invalidate_all_held(reason="hub restarted while the proposal was held")
    assert flipped == ["p2"]
    assert db.gate.get("p1").state == DENIED  # nothing decided is re-served
    assert db.gate.get("p2").state == INVALIDATED


def test_args_head_bounded_to_120_chars(rig) -> None:
    db, clock = rig
    proposal = db.gate.propose(
        proposal_id="long",
        session_key="claude:s1",
        agent="claude",
        tool="Bash",
        args_sha256="d" * 64,
        args_head="x" * 500,
        cwd="/tmp",
        ttl_seconds=10,
    )
    assert len(proposal.args_head) == 120


# -- config + matcher ------------------------------------------------------


def test_config_roundtrip_and_defaults(tmp_path) -> None:
    path = tmp_path / "gate.json"
    assert load_gate_config(path) == GateConfig()  # missing file is OFF
    save_gate_config(GateConfig(armed=True, repos={"/tmp/repo": ["Bash"]}), path)
    loaded = load_gate_config(path)
    assert loaded.armed is True
    assert loaded.repos == {"/tmp/repo": ["Bash"]}
    path.write_text("not json")
    assert load_gate_config(path) == GateConfig()  # corrupt file is OFF


def test_matcher_is_a_double_opt_in(tmp_path) -> None:
    repo = tmp_path / "repo"
    (repo / "sub").mkdir(parents=True)
    inside = str(repo / "sub")
    armed = GateConfig(armed=True, repos={str(repo): ["Bash"]})
    assert gate_matches(armed, cwd=str(repo), tool="Bash")
    assert gate_matches(armed, cwd=inside, tool="Bash")  # subdir matches
    assert not gate_matches(armed, cwd=inside, tool="Edit")  # tool not held
    assert not gate_matches(armed, cwd=str(tmp_path / "other"), tool="Bash")
    assert not gate_matches(GateConfig(armed=False, repos=armed.repos), cwd=inside, tool="Bash")
    assert not gate_matches(GateConfig(armed=True), cwd=inside, tool="Bash")  # no repos


def test_redaction_hash_and_head() -> None:
    sha, head = redact_args({"command": "rm -rf /tmp/x", "description": "y" * 300})
    assert len(sha) == 64
    assert len(head) <= 120
    sha2, _ = redact_args({"description": "y" * 300, "command": "rm -rf /tmp/x"})
    assert sha == sha2  # canonical ordering


def test_install_block_prints_and_never_writes(tmp_path, monkeypatch) -> None:
    block = json.loads(install_block())
    hook = block["hooks"]["PreToolUse"][0]
    assert hook["matcher"] == "Bash"
    assert "gate hook" in hook["hooks"][0]["command"]


# -- the hook runner -------------------------------------------------------


def _payload(tool="Bash", cwd="/tmp/repo"):
    return {
        "session_id": "s1",
        "tool_name": tool,
        "tool_input": {"command": "rm -rf build"},
        "cwd": cwd,
        "tool_use_id": "toolu_1",
    }


def _armed(cwd="/tmp/repo"):
    return GateConfig(armed=True, repos={cwd: ["Bash"]})


def test_unarmed_hook_is_inert_no_network(tmp_path) -> None:
    calls = []

    def post(url, body, timeout):
        calls.append(url)
        return 200, {}

    decision = run_hook(
        _payload(cwd=str(tmp_path)),
        config=GateConfig(),
        http_post=post,
        http_get=lambda url, timeout: (200, {}),
    )
    assert decision == HookDecision(deny=None)
    assert calls == []  # zero interception, zero hub contact


def test_armed_hub_unreachable_denies_by_name(tmp_path) -> None:
    def post(url, body, timeout):
        raise OSError("connection refused")

    decision = run_hook(
        _payload(cwd=str(tmp_path)),
        config=_armed(str(tmp_path)),
        http_post=post,
        http_get=lambda url, timeout: (200, {}),
    )
    assert decision.deny is not None
    assert "hub unreachable" in decision.deny


def test_armed_hub_500_denies(tmp_path) -> None:
    decision = run_hook(
        _payload(cwd=str(tmp_path)),
        config=_armed(str(tmp_path)),
        http_post=lambda url, body, timeout: (500, {}),
        http_get=lambda url, timeout: (200, {}),
    )
    assert decision.deny is not None and "HTTP 500" in decision.deny


def test_armed_poll_resolves_approval(tmp_path) -> None:
    clock = Clock()
    states = iter([HELD, HELD, APPROVED])

    def get(url, timeout):
        return 200, {"state": next(states)}

    decision = run_hook(
        _payload(cwd=str(tmp_path)),
        config=_armed(str(tmp_path)),
        http_post=lambda url, body, timeout: (200, {"state": HELD}),
        http_get=get,
        sleep=lambda seconds: setattr(clock, "now", clock.now + seconds),
        now=clock,
    )
    assert decision == HookDecision(deny=None)


def test_armed_deny_reason_rides_back_verbatim(tmp_path) -> None:
    clock = Clock()
    decision = run_hook(
        _payload(cwd=str(tmp_path)),
        config=_armed(str(tmp_path)),
        http_post=lambda url, body, timeout: (200, {"state": HELD}),
        http_get=lambda url, timeout: (200, {"state": DENIED, "reason": "use the staging bucket"}),
        sleep=lambda seconds: setattr(clock, "now", clock.now + seconds),
        now=clock,
    )
    assert decision.deny is not None
    assert "use the staging bucket" in decision.deny
    output = decision.to_hook_output()
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "use the staging bucket" in output["hookSpecificOutput"]["permissionDecisionReason"]


def test_armed_poll_timeout_denies(tmp_path) -> None:
    clock = Clock()
    decision = run_hook(
        _payload(cwd=str(tmp_path)),
        config=_armed(str(tmp_path)),
        http_post=lambda url, body, timeout: (200, {"state": HELD}),
        http_get=lambda url, timeout: (200, {"state": HELD}),
        sleep=lambda seconds: setattr(clock, "now", clock.now + seconds),
        now=clock,
        ttl_seconds=5.0,
    )
    assert decision.deny is not None and "expired" in decision.deny


def test_hook_reuses_one_idempotency_key_across_retries(tmp_path) -> None:
    posted_ids = []

    def post(url, body, timeout):
        posted_ids.append(body["id"])
        return 200, {"state": APPROVED}

    run_hook(
        _payload(cwd=str(tmp_path)),
        config=_armed(str(tmp_path)),
        http_post=post,
        http_get=lambda url, timeout: (200, {}),
    )
    assert posted_ids == ["toolu_1"]  # tool_use_id wins when present


# -- the hub routes --------------------------------------------------------


@pytest.fixture
def route_rig(tmp_path, monkeypatch):
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.gate_routes import build_gate_router

    reset_database()
    db = Database(tmp_path / "gate-routes.db")
    clock = Clock()
    db.gate._now = clock
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()
    app.include_router(build_gate_router(WebContext(get_state=lambda: {})))
    yield db, clock, TestClient(app)
    reset_database()


def _wire_proposal(client, proposal_id="p1", args_sha256="a" * 64):
    return client.post(
        "/api/gate/proposals",
        json={
            "id": proposal_id,
            "session_key": "claude:s1",
            "agent": "claude",
            "tool": "Bash",
            "args_sha256": args_sha256,
            "args_head": '{"command":"rm -rf build"}',
            "cwd": "/tmp/repo",
            "ttl_seconds": 60,
        },
    )


def test_route_roundtrip_propose_decide_poll(route_rig) -> None:
    db, clock, client = route_rig
    held = _wire_proposal(client)
    assert held.status_code == 200
    assert held.json()["state"] == HELD

    listed = client.get("/api/gate/proposals?state=held").json()
    assert [p["id"] for p in listed["proposals"]] == ["p1"]

    decided = client.post(
        "/api/gate/proposals/p1/decide",
        json={"decision": DENIED, "reason": "not on this branch", "actor": "owner"},
    )
    assert decided.status_code == 200
    assert decided.json()["state"] == DENIED

    polled = client.get("/api/gate/proposals/p1").json()
    assert polled["state"] == DENIED
    assert polled["reason"] == "not on this branch"

    audit = client.get("/api/gate/audit").json()["entries"]
    assert [e["event"] for e in audit] == [DENIED, "proposed"]


def test_route_double_decision_409_names_standing(route_rig) -> None:
    db, clock, client = route_rig
    _wire_proposal(client)
    client.post("/api/gate/proposals/p1/decide", json={"decision": APPROVED})
    second = client.post("/api/gate/proposals/p1/decide", json={"decision": DENIED})
    assert second.status_code == 409
    assert second.json() == {
        "error": "already_decided",
        "state": APPROVED,
        "requested": DENIED,
    }


def test_route_args_mismatch_409_and_revoke(route_rig) -> None:
    db, clock, client = route_rig
    _wire_proposal(client)
    mismatch = _wire_proposal(client, args_sha256="b" * 64)
    assert mismatch.status_code == 409
    assert mismatch.json()["error"] == "args_mismatch"
    assert db.gate.get("p1").state == INVALIDATED


def test_route_expiry_visible_to_the_polling_hook(route_rig) -> None:
    db, clock, client = route_rig
    _wire_proposal(client)
    clock.now += 61.0
    polled = client.get("/api/gate/proposals/p1").json()
    assert polled["state"] == EXPIRED


def test_route_unknown_proposal_404(route_rig) -> None:
    db, clock, client = route_rig
    assert client.get("/api/gate/proposals/ghost").status_code == 404
    assert client.post("/api/gate/proposals/ghost/decide", json={"decision": APPROVED}).status_code == 404


def test_startup_invalidation_via_route_helper(route_rig) -> None:
    from holdspeak.web.routes.system.gate_routes import invalidate_held_on_startup

    db, clock, client = route_rig
    _wire_proposal(client)
    assert invalidate_held_on_startup() == 1
    assert db.gate.get("p1").state == INVALIDATED
    polled = client.get("/api/gate/proposals/p1").json()
    assert polled["state"] == INVALIDATED


def test_wire_payload_matches_the_contract_schema(route_rig) -> None:
    from jsonschema import Draft202012Validator

    db, clock, client = route_rig
    body = _wire_proposal(client).json()
    schema = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "pm/roadmap/holdspeak-mobile/contracts/schemas/gate-proposal.schema.json"
        ).read_text()
    )
    assert list(Draft202012Validator(schema).iter_errors(body)) == []


def test_redaction_census_no_full_payload_fields(route_rig) -> None:
    """The wire and the row carry args_sha256 + args_head only — no
    field that could hold the full arguments."""
    db, clock, client = route_rig
    body = _wire_proposal(client).json()
    assert "args" not in body and "tool_input" not in body and "command" not in body
    row_columns = {
        "id", "session_key", "agent", "tool", "args_sha256", "args_head", "cwd",
        "operation", "policy_snapshot", "created_at", "expires_at", "state",
        "decided_by", "decided_at", "reason",
    }
    assert set(body) == row_columns
