"""PHILO-2-07: the graph join generator (brief section 8).

The committed join must be current and must validate; a contradiction without
a council resolution must stop the generator and name both sides; saved
observations keep their original revision; the census names new, removed and
changed entry points.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REV_A = "a" * 40
REV_B = "b" * 40


def _module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve their module through sys.modules.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gen = _module("philo_graph_reference")


def _source(path: str = "holdspeak/main.py") -> dict:
    return {"revision": REV_A, "path": path, "line": 1, "symbol": "main", "claim": "c"}


def _pass(nodes=(), reviews=(), findings=(), observations=(), cases=()) -> dict:
    return {
        "schema_version": 1,
        "generator": "test",
        "source_commit": REV_A,
        "phase1_baseline": REV_B,
        "inputs": [],
        "nodes": list(nodes),
        "links": [],
        "cases": list(cases),
        "observations": list(observations),
        "claim_reviews": list(reviews),
        "findings": list(findings),
        "resolutions": [],
    }


def _finding(fid: str, claim_ids=(), bin_="product-defect") -> dict:
    return {
        "id": fid,
        "bin": bin_,
        "owner_cost": "c",
        "expected": "e",
        "actual": "a",
        "evidence": [_source()],
        "case_ids": [],
        "claim_ids": list(claim_ids),
        "positions": {"muaddib": "m", "astra": "a"},
    }


def _review(rid: str, verdict: str) -> dict:
    return {
        "id": rid,
        "claim_ref": {"inventory_path": "docs/x.json", "record_id": "rec.one", "field": "exposure"},
        "revision": REV_A,
        "verdict": verdict,
        "evidence": [_source()],
        "limits": "l",
    }


def _inputs(passes: dict, resolutions=()) -> "gen.Inputs":
    full = {name: _pass() for name in gen.PASSES}
    full.update(passes)
    return gen.Inputs(
        passes=full,
        atlas={"cases": []},
        resolutions={"resolutions": list(resolutions), "council_round": 2},
        hashes={"docs/x.json": "0" * 64},
    )


def _node(node_id: str, kind: str, label: str) -> dict:
    return {"id": node_id, "kind": kind, "label": label, "phase1_refs": [], "sources": [_source()]}


# ---------------------------------------------------------------------------
# The committed join.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def joined() -> tuple[dict, list[str]]:
    return gen.join(gen.load_inputs(ROOT))


def test_committed_join_is_current(joined):
    """--check's own comparison: the file on disk is the join of the inputs."""
    graph, _ = joined
    assert (ROOT / gen.OUTPUT).read_text(encoding="utf-8") == gen.render(graph)


def test_committed_join_validates(joined):
    graph, _ = joined
    validator = _module("philo_graph_validate")
    schema = json.loads((ROOT / "docs/internal/philo/graph/graph.schema.json").read_text(encoding="utf-8"))
    assert validator.validate(graph, schema, ROOT) == []


def test_every_finding_carries_exactly_one_council_resolution(joined):
    graph, _ = joined
    finding_ids = sorted(finding["id"] for finding in graph["findings"])
    resolved = sorted(row["finding_id"] for row in graph["resolutions"])
    assert resolved == finding_ids


def test_saved_observations_keep_their_original_revision(joined):
    """A regeneration never restamps old execution evidence."""
    graph, _ = joined
    joined_by_id = {obs["id"]: obs for obs in graph["observations"]}
    for name in ("live-muaddib", "live-astra"):
        sealed = json.loads((ROOT / gen.GRAPH_DIR / f"{name}.json").read_text(encoding="utf-8"))
        for observation in sealed["observations"]:
            assert joined_by_id[observation["id"]] == observation
            assert joined_by_id[observation["id"]]["provenance"]["revision"] == sealed["source_commit"]


# ---------------------------------------------------------------------------
# Contradictions.
# ---------------------------------------------------------------------------

def test_node_kind_contradiction_is_refused_naming_both():
    inputs = _inputs(
        {
            "static-muaddib": _pass(nodes=[_node("edge.demo", "edge", "Demo")]),
            "static-astra": _pass(nodes=[_node("edge.demo", "action", "Demo")]),
        }
    )
    with pytest.raises(gen.JoinError) as error:
        gen.join(inputs)
    message = "\n".join(error.value.problems)
    assert "edge.demo" in message
    assert "static-muaddib: kind=edge" in message and "static-astra: kind=action" in message


def test_claim_verdict_contradiction_is_refused_without_a_resolution():
    inputs = _inputs(
        {
            "static-muaddib": _pass(reviews=[_review("cr.one", "verified")]),
            "static-astra": _pass(reviews=[_review("cr.two", "contradicted")]),
        }
    )
    with pytest.raises(gen.JoinError) as error:
        gen.join(inputs)
    message = "\n".join(error.value.problems)
    assert "cr.one (static-muaddib) says verified" in message
    assert "cr.two (static-astra) says contradicted" in message


def test_claim_verdict_contradiction_passes_with_a_council_resolution():
    finding = _finding("fnd.one", claim_ids=["cr.one", "cr.two"], bin_="doc-drift")
    inputs = _inputs(
        {
            "static-muaddib": _pass(reviews=[_review("cr.one", "verified")], findings=[finding]),
            "static-astra": _pass(reviews=[_review("cr.two", "contradicted")]),
        },
        resolutions=[
            {
                "id": "res.one",
                "findings": ["fnd.one"],
                "bin": "doc-drift",
                "disposition": "story7",
                "positions": {"muaddib": "agree", "astra": "agree"},
            }
        ],
    )
    graph, _ = gen.join(inputs)
    assert [row["id"] for row in graph["resolutions"]] == ["res.one:fnd.one"]


def test_finding_without_a_resolution_is_refused():
    inputs = _inputs({"live-astra": _pass(findings=[_finding("fnd.lonely")])})
    with pytest.raises(gen.JoinError) as error:
        gen.join(inputs)
    assert any("finding-unresolved: fnd.lonely" in line for line in error.value.problems)


def test_same_id_with_different_content_is_refused():
    one = _finding("fnd.same")
    two = copy.deepcopy(one)
    two["actual"] = "something else"
    inputs = _inputs({"static-muaddib": _pass(findings=[one]), "live-astra": _pass(findings=[two])})
    with pytest.raises(gen.JoinError) as error:
        gen.join(inputs)
    assert any("findings id fnd.same differs between static-muaddib and live-astra" in line for line in error.value.problems)


def test_council_rebin_is_written_beside_the_sealed_bin():
    inputs = _inputs(
        {"live-astra": _pass(findings=[_finding("fnd.recipe", bin_="product-defect")])},
        resolutions=[
            {
                "id": "res.recipe",
                "findings": ["fnd.recipe"],
                "bin": "tooling-debt",
                "disposition": "phase3:1",
                "disposition_final": "proposed:A2",
                "positions": {"muaddib": "agree", "astra": "agree"},
            }
        ],
    )
    graph, _ = gen.join(inputs)
    (row,) = graph["resolutions"]
    assert row["disposition"] == "tooling-debt: proposed:A2 (sealed live-astra bin: product-defect)"


def test_exposure_disagreement_is_named_not_chosen():
    inputs = _inputs(
        {
            "static-muaddib": _pass(nodes=[_node("edge.verb.demo", "edge", "Demo [conditional]")]),
            "static-astra": _pass(nodes=[_node("edge.verb.demo", "edge", "[exposure=active] demo")]),
        }
    )
    graph, notes = gen.join(inputs)
    (node,) = graph["nodes"]
    assert node["label"].endswith("[exposure disagreement: astra=active; muaddib=conditional]")
    assert notes == ["exposure-disagreement: edge.verb.demo: astra=active; muaddib=conditional"]


# ---------------------------------------------------------------------------
# The census.
# ---------------------------------------------------------------------------

def test_census_names_new_removed_and_changed(tmp_path, monkeypatch):
    (tmp_path / "docs/generated").mkdir(parents=True)
    (tmp_path / "docs/generated/openapi.json").write_text(
        json.dumps({"paths": {"/api/kept": {"get": {}}, "/api/new": {"post": {}}}})
    )
    (tmp_path / "web/src/desk").mkdir(parents=True)
    (tmp_path / "web/src/desk/verbRegistry.ts").write_text('export const VERBS = [\n  {\n    id: "desk.kept",\n  },\n];\n')
    (tmp_path / "web/src/desk/applications.ts").write_text("export const DESK_APPLICATIONS = [\n];\n")
    (tmp_path / "holdspeak").mkdir()
    (tmp_path / "holdspeak/routes.py").write_text("async def renamed_handler():\n    pass\n")
    monkeypatch.setattr(gen, "current_mcp_tools", lambda: {"demo.tool"})

    def edge(node_id, source, refs=()):
        return {"id": node_id, "kind": "edge", "label": node_id, "phase1_refs": list(refs), "sources": [source]}

    route_source = {"revision": REV_A, "path": "holdspeak/routes.py", "line": 1, "symbol": "kept_handler", "claim": "c"}
    graph = {
        "source_commit": REV_A,
        "nodes": [
            edge("edge.route.kept", route_source, [{"inventory_path": "docs/generated/openapi.json", "method": "GET", "path": "/api/kept"}]),
            edge("edge.route.gone", route_source, [{"inventory_path": "docs/generated/openapi.json", "method": "DELETE", "path": "/api/gone"}]),
            edge("edge.verb.desk_kept", {**route_source, "path": "web/src/desk/verbRegistry.ts", "symbol": "VERBS"}),
            edge("edge.verb.desk_retired", {**route_source, "path": "web/src/desk/verbRegistry.ts", "symbol": "VERBS"}),
            edge("edge.mcp.demo_tool", {**route_source, "path": "holdspeak/gone.py", "symbol": "TOOLS"}),
        ],
    }
    lines = gen.census(graph, tmp_path)
    assert "new: http POST /api/new has no edge" in lines
    assert "removed: http DELETE /api/gone is gone from the roster (edge.route.gone)" in lines
    assert "removed: verb edge edge.verb.desk_retired names nothing declared now" in lines
    assert "changed: mcp tool demo.tool (edge.mcp.demo_tool): holdspeak/gone.py is gone" in lines
    # git cannot read revision aaaa… in a temporary tree, so the moved handler is "changed".
    assert "changed: http GET /api/kept (edge.route.kept): def kept_handler is no longer in holdspeak/routes.py" in lines
    assert not any("desk.kept" in line for line in lines)
