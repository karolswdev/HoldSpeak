"""HSM-22-01 — the graph_json language-boundary pin.

The fixtures under ``pm/roadmap/holdspeak-mobile/contracts/fixtures/`` are ENCODED BY
SWIFT (``BlueprintWireTests``, the canonical `HoldSpeakContracts` coder — regenerate
with ``HS_REGEN_BLUEPRINT_FIXTURES=1 swift test --filter BlueprintWireTests``). This
test feeds those exact bytes into ``workflow_graph.linearize()``: the real encoder
output against the real parser, so the two ends of the wire can never drift silently.

Before this pin the hub's conformance ran a hand-written Python dict in the Swift
*shape*; the shape was right, but nothing proved the Swift encoder actually produces
it (the survey's "language boundary unproven" finding).
"""
from __future__ import annotations

import json
from pathlib import Path

from holdspeak.web.routes.workflow_graph import linearize

_FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "pm" / "roadmap" / "holdspeak-mobile" / "contracts" / "fixtures"
)


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_swift_encoded_linear_blueprint_linearizes() -> None:
    plan = linearize(_load("blueprint-linear-sample.json"))
    assert plan.linearizable, plan.reason

    # The whole chain, in exec-edge order (entry/output ride as passthroughs).
    assert [n.id for n in plan.ordered] == ["e1", "ask", "dec", "keep", "out"]
    assert [n.kind for n in plan.ordered] == ["entry", "llm", "extract", "keep_if", "output"]

    by_id = {n.id: n for n in plan.ordered}
    # Per-node provenance reaches the plan exactly as the Swift inspector set it.
    assert by_id["ask"].failure_policy == "fallbackOnDevice"
    assert by_id["ask"].runs_on == "endpoint"
    assert by_id["dec"].failure_policy == "skip"
    assert by_id["dec"].runs_on == "onDevice"
    # Unset on the wire (key absent) inherits: None policy, "auto" target.
    assert by_id["keep"].failure_policy is None
    assert by_id["keep"].runs_on == "auto"

    # The tagged-union payloads parse: the llm prompt and extract's `_0` artifact type.
    assert "list the risks" in str(by_id["ask"].payload)
    assert by_id["dec"].payload == {"_0": "decisions"}


def test_swift_encoded_branching_blueprint_is_refused_honestly() -> None:
    plan = linearize(_load("blueprint-branching-sample.json"))
    assert not plan.linearizable
    assert "branch" in (plan.reason or "")


def test_fixture_nodes_omit_unset_provenance_keys() -> None:
    """The inherit-the-default contract is the ABSENCE of the key (never null):
    Swift's nil runsOn/failurePolicy must not reach the wire at all."""
    graph = _load("blueprint-linear-sample.json")
    by_id = {n["id"]: n for n in graph["nodes"]}
    assert "runs_on" not in by_id["keep"]
    assert "failure_policy" not in by_id["keep"]
    assert by_id["ask"]["runs_on"] == "endpoint"
