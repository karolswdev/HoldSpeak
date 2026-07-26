"""HS-104-01 — the capability ledger: matrix pins, enforcement, doctor census."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.agent_capabilities import (
    ADAPTERS,
    LEDGER,
    Capability,
    CapabilityUnavailableError,
    LedgerConsumer,
    Standing,
    UnknownAdapterError,
    capabilities_payload,
    consumer_violations,
    require_capability,
    standing_for,
)

# The whole declaration table, pinned cell by cell. A standing change is a
# reviewed edit that lands here in the same commit as the code it describes.
EXPECTED = {
    "tmux-pane": {
        Capability.TOOL_HOOKS: Standing.UNAVAILABLE,
        Capability.SESSION_IDENTITY: Standing.INFERRED,
        Capability.USAGE_TOKENS: Standing.UNAVAILABLE,
        Capability.REPO_HEAD: Standing.INFERRED,
        Capability.BLOCKING: Standing.UNAVAILABLE,
    },
    "delivery-node": {
        Capability.TOOL_HOOKS: Standing.UNAVAILABLE,
        Capability.SESSION_IDENTITY: Standing.AUTHORITATIVE,
        Capability.USAGE_TOKENS: Standing.UNAVAILABLE,
        Capability.REPO_HEAD: Standing.AUTHORITATIVE,
        Capability.BLOCKING: Standing.UNAVAILABLE,
    },
    "mesh-node": {
        Capability.TOOL_HOOKS: Standing.UNAVAILABLE,
        Capability.SESSION_IDENTITY: Standing.INFERRED,
        Capability.USAGE_TOKENS: Standing.UNAVAILABLE,
        Capability.REPO_HEAD: Standing.UNAVAILABLE,
        Capability.BLOCKING: Standing.UNAVAILABLE,
    },
    # HS-104-02 flipped tool_hooks + blocking (PreToolUse intercepts and
    # the hook blocks on the decision) and session_identity to inferred
    # (the session_id is self-reported by the agent process).
    "claude-code-hooks": {
        Capability.TOOL_HOOKS: Standing.AUTHORITATIVE,
        Capability.SESSION_IDENTITY: Standing.INFERRED,
        # HS-104-05: the Stop hook reports transcript usage totals.
        Capability.USAGE_TOKENS: Standing.AUTHORITATIVE,
        Capability.REPO_HEAD: Standing.UNAVAILABLE,
        Capability.BLOCKING: Standing.AUTHORITATIVE,
    },
}


def test_ledger_matches_the_pinned_matrix_exactly() -> None:
    assert set(LEDGER) == set(EXPECTED) == set(ADAPTERS)
    for adapter, row in EXPECTED.items():
        assert dict(LEDGER[adapter]) == row, adapter
        assert set(LEDGER[adapter]) == set(Capability), adapter


@pytest.mark.parametrize("adapter", ADAPTERS)
@pytest.mark.parametrize("capability", list(Capability))
def test_every_cell_answers(adapter: str, capability: Capability) -> None:
    assert standing_for(adapter, capability) is EXPECTED[adapter][capability]


def test_require_capability_returns_standing_when_vouched() -> None:
    assert (
        require_capability("delivery-node", Capability.SESSION_IDENTITY)
        is Standing.AUTHORITATIVE
    )
    assert (
        require_capability("tmux-pane", Capability.SESSION_IDENTITY)
        is Standing.INFERRED
    )


def test_require_capability_refuses_unavailable_by_name() -> None:
    with pytest.raises(CapabilityUnavailableError) as exc:
        require_capability("tmux-pane", Capability.BLOCKING)
    assert exc.value.adapter == "tmux-pane"
    assert exc.value.capability is Capability.BLOCKING
    assert "unavailable" in str(exc.value)
    assert "tmux-pane" in str(exc.value)


def test_unknown_adapter_refused_by_name() -> None:
    with pytest.raises(UnknownAdapterError, match="not-an-adapter"):
        require_capability("not-an-adapter", Capability.BLOCKING)


def test_consumer_census_flags_unavailable_and_unknown() -> None:
    bad = (
        LedgerConsumer("gate.decide", "tmux-pane", Capability.BLOCKING),
        LedgerConsumer("card.tokens", "ghost-adapter", Capability.USAGE_TOKENS),
        LedgerConsumer("ok.attempts", "delivery-node", Capability.SESSION_IDENTITY),
    )
    violations = consumer_violations(bad)
    assert len(violations) == 2
    assert any("gate.decide" in v and "unavailable" in v for v in violations)
    assert any("card.tokens" in v and "not in the ledger" in v for v in violations)


def test_registered_consumers_are_all_backed() -> None:
    assert consumer_violations() == []


def test_doctor_check_goes_red_on_a_bad_consumer(monkeypatch) -> None:
    import holdspeak.agent_capabilities as mod
    from holdspeak.commands.doctor import _check_agent_capabilities

    assert _check_agent_capabilities().status == "PASS"
    monkeypatch.setattr(
        mod,
        "LEDGER_CONSUMERS",
        (LedgerConsumer("bad.consumer", "tmux-pane", Capability.BLOCKING),),
    )
    check = _check_agent_capabilities()
    assert check.status == "FAIL"
    assert check.fix is not None and "bad.consumer" in check.fix


def _schema() -> dict:
    path = (
        Path(__file__).resolve().parents[2]
        / "pm/roadmap/holdspeak-mobile/contracts/schemas/agent-capabilities.schema.json"
    )
    return json.loads(path.read_text())


def test_route_serves_the_table_and_the_contract_validates_it() -> None:
    from jsonschema import Draft202012Validator

    from holdspeak.web.routes.system.agent_capabilities import (
        build_agent_capabilities_router,
    )

    app = FastAPI()
    app.include_router(build_agent_capabilities_router())
    body = TestClient(app).get("/api/agents/capabilities").json()

    validator = Draft202012Validator(_schema())
    assert list(validator.iter_errors(body)) == []
    assert body == capabilities_payload()
    assert {row["adapter"] for row in body["adapters"]} == set(ADAPTERS)


def test_contract_rejects_a_lying_payload() -> None:
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(_schema())
    payload = capabilities_payload()
    payload["adapters"][0]["capabilities"]["blocking"] = "probably"
    assert list(validator.iter_errors(payload)) != []
