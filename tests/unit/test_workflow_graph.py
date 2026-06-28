"""The linear Blueprint graph runner's parse/linearize boundary (pure, no engine).

Covers exactly what `holdspeak.web.routes.workflow_graph` will and won't run:
a single unambiguous chain of LLM/prompt/pass-through nodes linearizes; anything
with control flow, fan-out, fan-in, cycles, or dangling edges is refused.
"""
from __future__ import annotations

from holdspeak.web.routes.workflow_graph import (
    apply_pure_transform,
    build_node_prompt,
    linearize,
    on_node_error,
    parse_graph,
    resolved_failure_policy,
    GraphNode,
)


def _node(nid: str, kind: dict | str) -> dict:
    return {"id": nid, "kind": kind, "failure_policy": None}


def _exec(frm: str, to: str, name: str = "then") -> dict:
    return {"from": {"node": frm, "name": name}, "to": to}


# ── parse_graph ──────────────────────────────────────────────────────────────
def test_parse_graph_decodes_tagged_union_kinds() -> None:
    g = {"nodes": [
        _node("e", {"entry": {}}),
        _node("l", {"llm": {"name": "X", "prompt": "Do {input}"}}),
        _node("x", {"extract": "decisions"}),
    ]}
    nodes = parse_graph(g)
    assert nodes is not None
    assert [(n.id, n.kind) for n in nodes] == [("e", "entry"), ("l", "llm"), ("x", "extract")]
    assert nodes[1].payload == {"name": "X", "prompt": "Do {input}"}
    assert nodes[2].payload == "decisions"


def test_parse_graph_rejects_non_graphs_and_dupes() -> None:
    assert parse_graph(None) is None
    assert parse_graph({"nodes": []}) is None
    assert parse_graph({"nodes": [1, 2]}) is None          # int nodes (legacy stub)
    assert parse_graph({"nodes": [_node("a", {"entry": {}}),
                                  _node("a", {"output": {}})]}) is None  # dup id


# ── linearize: the SUPPORTED chain ──────────────────────────────────────────
def test_linearize_orders_a_single_chain() -> None:
    # Edges given out of order; entry declared. Must order entry->b->c->out.
    g = {
        "entry": "e",
        "nodes": [
            _node("e", {"entry": {}}),
            _node("out", {"output": {}}),
            _node("c", {"rewrite": {"tone": "calm"}}),
            _node("b", {"summarize": {}}),
        ],
        "exec_edges": [
            _exec("c", "out"),
            _exec("e", "b"),
            _exec("b", "c"),
        ],
    }
    plan = linearize(g)
    assert plan.linearizable
    assert [n.id for n in plan.ordered] == ["e", "b", "c", "out"]


def test_linearize_chain_without_declared_entry() -> None:
    g = {
        "nodes": [_node("a", {"summarize": {}}), _node("b", {"summarize": {}})],
        "exec_edges": [_exec("a", "b")],
    }
    plan = linearize(g)
    assert plan.linearizable and [n.id for n in plan.ordered] == ["a", "b"]


# ── linearize: the REFUSED graphs (no guessed order) ────────────────────────
def test_linearize_refuses_branch() -> None:
    g = {
        "nodes": [
            _node("e", {"entry": {}}),
            _node("br", {"branch": {"condition": {"is_empty": {}}}}),
            _node("a", {"summarize": {}}),
            _node("b", {"summarize": {}}),
        ],
        "exec_edges": [_exec("e", "br"), _exec("br", "a", "true"), _exec("br", "b", "false")],
    }
    plan = linearize(g)
    assert not plan.linearizable and "control-flow" in plan.reason


def test_linearize_refuses_for_each_and_while_and_sequence() -> None:
    for kind in ({"for_each": {}}, {"while_loop": {"condition": {"is_empty": {}}, "max_iterations": 3}},
                 {"sequence": {"count": 2}}):
        g = {"nodes": [_node("e", {"entry": {}}), _node("c", kind)],
             "exec_edges": [_exec("e", "c")]}
        plan = linearize(g)
        assert not plan.linearizable, kind


def test_linearize_refuses_fan_out_even_with_linear_kinds() -> None:
    # Two "then" edges off one node = a fork the validator must reject.
    g = {
        "nodes": [_node("e", {"entry": {}}), _node("a", {"summarize": {}}),
                  _node("b", {"summarize": {}})],
        "exec_edges": [_exec("e", "a"), _exec("e", "b")],
    }
    plan = linearize(g)
    assert not plan.linearizable and "fans out" in plan.reason


def test_linearize_refuses_fan_in_join() -> None:
    g = {
        "nodes": [_node("a", {"summarize": {}}), _node("b", {"summarize": {}}),
                  _node("m", {"merge": {}})],
        "exec_edges": [_exec("a", "m"), _exec("b", "m")],
    }
    plan = linearize(g)
    assert not plan.linearizable and "join" in plan.reason


def test_linearize_refuses_dangling_edge_and_disconnected() -> None:
    dangling = {"nodes": [_node("a", {"summarize": {}})],
                "exec_edges": [_exec("a", "ghost")]}
    assert not linearize(dangling).linearizable

    disconnected = {"nodes": [_node("a", {"summarize": {}}), _node("b", {"summarize": {}}),
                              _node("c", {"summarize": {}})],
                    "exec_edges": [_exec("a", "b")]}  # c is orphaned -> two heads
    assert not linearize(disconnected).linearizable


def test_linearize_refuses_unknown_kind() -> None:
    g = {"nodes": [_node("a", {"teleport": {}})], "exec_edges": []}
    plan = linearize(g)
    assert not plan.linearizable and "unsupported kind" in plan.reason


# ── prompt templates (mirror the Swift interpreter) ─────────────────────────
def test_build_node_prompt_matches_swift_templates() -> None:
    assert build_node_prompt(GraphNode("l", "llm", {"prompt": "Hi {input}!"}), "X") == "Hi X!"
    assert build_node_prompt(GraphNode("s", "summarize", {}), "BODY").startswith(
        "Summarize the following")
    assert "executive tone" in build_node_prompt(
        GraphNode("r", "rewrite", {"tone": "executive"}), "B")
    # `extract(ArtifactType)` is a single UNLABELED associated value, so Swift's
    # synthesized Codable encodes it as {"extract": {"_0": "action_items"}}. The
    # decoded payload is that {"_0": ...} object — the REAL wire shape the hub sees.
    assert "extract the action items" in build_node_prompt(
        GraphNode("x", "extract", {"_0": "action_items"}), "B")
    # The bare-string payload is accepted too (defensive), but it is NOT the wire shape.
    assert "extract the action items" in build_node_prompt(
        GraphNode("x", "extract", "action_items"), "B")


def test_apply_pure_transform() -> None:
    kept = apply_pure_transform(GraphNode("k", "keep_if", {"keyword": "risk"}),
                                "a risk here\nno match\nbig RISK")
    assert kept == "a risk here\nbig RISK"
    split = apply_pure_transform(GraphNode("s", "split_into_items", {}),
                                 " one \n\n two \n")
    assert split == "one\ntwo"


# ── per-node provenance: failure_policy + runs_on are carried, not dropped ────
def test_parse_graph_carries_failure_policy_and_runs_on() -> None:
    g = {"nodes": [
        {"id": "a", "kind": {"summarize": {}},
         "failure_policy": "skip", "runs_on": "endpoint"},
        {"id": "b", "kind": {"summarize": {}},
         "failure_policy": "fallbackOnDevice", "runs_on": "onDevice"},
    ]}
    nodes = parse_graph(g)
    assert nodes is not None
    assert (nodes[0].failure_policy, nodes[0].runs_on) == ("skip", "endpoint")
    assert (nodes[1].failure_policy, nodes[1].runs_on) == ("fallbackOnDevice", "onDevice")


def test_parse_graph_unset_or_unknown_provenance_is_byte_identical_default() -> None:
    # No keys, explicit null, and unknown strings all normalize to the inherit-default:
    # failure_policy None (inherit the run default), runs_on "auto" (follow Settings).
    g = {"nodes": [
        {"id": "a", "kind": {"summarize": {}}},                      # absent
        {"id": "b", "kind": {"summarize": {}}, "failure_policy": None, "runs_on": None},
        {"id": "c", "kind": {"summarize": {}},
         "failure_policy": "teleport", "runs_on": "moon"},           # unrecognised
    ]}
    nodes = parse_graph(g)
    assert nodes is not None
    for n in nodes:
        assert n.failure_policy is None
        assert n.runs_on == "auto"


def test_resolved_failure_policy_falls_back_to_run_default() -> None:
    # An explicit node policy wins; unset inherits the runner's default.
    assert resolved_failure_policy(GraphNode("a", "llm", {}, failure_policy="skip")) == "skip"
    assert resolved_failure_policy(GraphNode("a", "llm", {})) == "retryThenQueue"
    assert resolved_failure_policy(GraphNode("a", "llm", {}), default="skip") == "skip"


def test_on_node_error_honors_skip_and_fallback_but_surfaces_retry() -> None:
    carried = "the resolved input"
    # skip → carry the input straight through (the step is dropped, run survives).
    assert on_node_error(GraphNode("a", "llm", {}, failure_policy="skip"), carried) == carried
    # fallbackOnDevice → no separate hub fallback, so carry through (degrade, don't drop run).
    assert on_node_error(
        GraphNode("a", "llm", {}, failure_policy="fallbackOnDevice"), carried) == carried
    # retryThenQueue and unset → None: the hub surfaces the failure (no silent recovery).
    assert on_node_error(GraphNode("a", "llm", {}, failure_policy="retryThenQueue"), carried) is None
    assert on_node_error(GraphNode("a", "llm", {}), carried) is None


def test_linearize_preserves_provenance_through_ordering() -> None:
    g = {
        "nodes": [
            {"id": "a", "kind": {"summarize": {}},
             "failure_policy": "skip", "runs_on": "endpoint"},
            {"id": "b", "kind": {"rewrite": {"tone": "calm"}},
             "failure_policy": "fallbackOnDevice", "runs_on": "onDevice"},
        ],
        "exec_edges": [_exec("a", "b")],
    }
    plan = linearize(g)
    assert plan.linearizable
    a, b = plan.ordered
    assert (a.id, a.failure_policy, a.runs_on) == ("a", "skip", "endpoint")
    assert (b.id, b.failure_policy, b.runs_on) == ("b", "fallbackOnDevice", "onDevice")
