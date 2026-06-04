"""HS-37-01 — ActuatorProposal contract tests.

An actuator's `run()` returns a proposal (a described side effect), never an
action. These tests pin the parse/validate contract: a faithful proposal
round-trips; a malformed one raises `ActuatorProposalError` listing every
problem at once (so the host can surface it as a plain `error`, never a
silent side effect).
"""

from __future__ import annotations

import pytest

from holdspeak.plugins.actuators import (
    ACTUATOR_PROPOSAL_STATUS,
    ActuatorProposal,
    ActuatorProposalError,
)


def _good(**overrides):
    base = {
        "target": "github",
        "action": "create_issue",
        "preview": "Open a follow-up issue for the unowned action item",
        "payload": {"repo": "acme/app", "title": "Follow up"},
    }
    base.update(overrides)
    return base


def test_status_constant() -> None:
    assert ACTUATOR_PROPOSAL_STATUS == "proposed"


# ──────────────────────────── Happy path ──────────────────────────────


def test_from_run_output_minimal() -> None:
    proposal = ActuatorProposal.from_run_output(_good())
    assert proposal.target == "github"
    assert proposal.action == "create_issue"
    assert proposal.preview.startswith("Open a follow-up")
    assert proposal.payload == {"repo": "acme/app", "title": "Follow up"}
    # Optional fields default safely.
    assert proposal.reversible is False
    assert proposal.required_capabilities == ()


def test_from_run_output_full_round_trips() -> None:
    proposal = ActuatorProposal.from_run_output(
        _good(reversible=True, required_capabilities=["actuator", "LLM"])
    )
    payload = proposal.to_payload()
    assert payload["target"] == "github"
    assert payload["reversible"] is True
    # Capabilities are normalized (stripped + lowercased).
    assert payload["required_capabilities"] == ["actuator", "llm"]
    # The machine payload survives verbatim.
    assert payload["payload"] == {"repo": "acme/app", "title": "Follow up"}


def test_strings_are_stripped() -> None:
    proposal = ActuatorProposal.from_run_output(_good(target="  jira  ", action=" comment "))
    assert proposal.target == "jira"
    assert proposal.action == "comment"


def test_empty_payload_is_allowed() -> None:
    proposal = ActuatorProposal.from_run_output(_good(payload={}))
    assert proposal.payload == {}


# ──────────────────────────── Rejections ──────────────────────────────


def test_non_mapping_is_rejected() -> None:
    with pytest.raises(ActuatorProposalError):
        ActuatorProposal.from_run_output(["not", "a", "dict"])


@pytest.mark.parametrize("field_name", ["target", "action", "preview"])
def test_missing_required_string_is_rejected(field_name: str) -> None:
    bad = _good()
    bad.pop(field_name)
    with pytest.raises(ActuatorProposalError) as exc:
        ActuatorProposal.from_run_output(bad)
    assert field_name in str(exc.value)


@pytest.mark.parametrize("field_name", ["target", "action", "preview"])
def test_blank_required_string_is_rejected(field_name: str) -> None:
    with pytest.raises(ActuatorProposalError):
        ActuatorProposal.from_run_output(_good(**{field_name: "   "}))


def test_non_object_payload_is_rejected() -> None:
    with pytest.raises(ActuatorProposalError) as exc:
        ActuatorProposal.from_run_output(_good(payload="ship it"))
    assert "payload" in str(exc.value)


def test_all_problems_surface_at_once() -> None:
    with pytest.raises(ActuatorProposalError) as exc:
        ActuatorProposal.from_run_output({"payload": 5})
    message = str(exc.value)
    # target, action, preview all missing + payload wrong — every one reported.
    for token in ("target", "action", "preview", "payload"):
        assert token in message


def test_non_list_capabilities_is_rejected() -> None:
    with pytest.raises(ActuatorProposalError) as exc:
        ActuatorProposal.from_run_output(_good(required_capabilities="actuator"))
    assert "required_capabilities" in str(exc.value)
