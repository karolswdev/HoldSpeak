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
    monkeypatch.setattr(
        gen,
        "current_routes",
        lambda root: {
            ("GET", "/api/kept"): {"handler": "renamed_handler", "module": "holdspeak/routes.py"},
            ("POST", "/api/new"): {"handler": "new_handler", "module": "holdspeak/routes.py"},
        },
    )

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
    assert "new: http POST /api/new has no edge (new_handler)" in lines
    assert "removed: http DELETE /api/gone is not in source (edge.route.gone)" in lines
    assert "removed: verb edge edge.verb.desk_retired names nothing declared now" in lines
    assert "changed: mcp tool demo.tool (edge.mcp.demo_tool): holdspeak/gone.py is gone" in lines
    # git cannot read revision aaaa… in a temporary tree, so the renamed handler is "changed".
    assert "changed: http GET /api/kept (edge.route.kept): source registers renamed_handler, not the cited kept_handler" in lines
    assert not any(line.startswith("stale:") for line in lines)
    assert not any("desk.kept" in line for line in lines)


# ---------------------------------------------------------------------------
# Counsel round (Astra's check of the built story, findings 1-3).
# ---------------------------------------------------------------------------

def _openapi_digest() -> str:
    import hashlib

    return hashlib.sha256((ROOT / "docs/generated/openapi.json").read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def route_surface():
    """The route owner the Philo scripts share (scripts/gen_api_surface.py)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import gen_api_surface
    finally:
        sys.path.remove(str(ROOT / "scripts"))
    return gen_api_surface


def test_census_sees_source_route_changes_while_openapi_is_unchanged(route_surface, monkeypatch):
    """Finding 1: add, remove and rename a route decorator in the assembled app
    and leave docs/generated/openapi.json alone.  The census must name all three."""
    before = _openapi_digest()
    app = route_surface.build_reference_app()

    @app.post("/api/philo-census-probe")
    def philo_census_probe():  # added in source, absent from OpenAPI and the join
        return {}

    def _drop(method: str, path: str):
        (route,) = [r for r in app.router.routes if getattr(r, "path", "") == path and method in getattr(r, "methods", set())]
        app.router.routes.remove(route)
        return route

    _drop("DELETE", "/api/activity/domains/{domain}")  # removed from source
    _drop("DELETE", "/api/activity/records")

    @app.delete("/api/activity/records")
    def delete_records_renamed():  # same method and path, new handler name
        return {}

    monkeypatch.setattr(route_surface, "build_reference_app", lambda: app)
    graph = json.loads((ROOT / gen.OUTPUT).read_text(encoding="utf-8"))
    lines = gen.census(graph, ROOT)

    assert _openapi_digest() == before
    assert "new: http POST /api/philo-census-probe has no edge (philo_census_probe)" in lines
    assert any(line.startswith("removed: http DELETE /api/activity/domains/{domain} ") for line in lines)
    assert any(
        line.startswith("changed: http DELETE /api/activity/records (")
        and "delete_records_renamed" in line
        for line in lines
    )


def _typed(node_id: str, subtype: str) -> dict:
    return {**_node(node_id, "edge", node_id), "subtype": subtype}


def test_subtype_conflict_keeps_both_positions_and_is_not_decided():
    """Finding 2: http versus ui is a conflict; the join names both and picks neither."""
    inputs = _inputs(
        {
            "static-muaddib": _pass(nodes=[_typed("edge.route.demo", "http")]),
            "static-astra": _pass(nodes=[_typed("edge.route.demo", "ui")]),
        }
    )
    graph, notes = gen.join(inputs)
    (node,) = graph["nodes"]
    assert "subtype" not in node
    assert node["label"].endswith("[subtype conflict: astra=ui; muaddib=http]")
    assert "subtype-conflict: edge.route.demo: astra=ui; muaddib=http" in notes


def test_subtype_refinement_is_normalized_by_the_table_and_keeps_both():
    inputs = _inputs(
        {
            "static-muaddib": _pass(nodes=[_typed("edge.route.demo", "http")]),
            "static-astra": _pass(nodes=[_typed("edge.route.demo", "http.POST")]),
        }
    )
    graph, notes = gen.join(inputs)
    (node,) = graph["nodes"]
    assert node["subtype"] == "http.POST"
    assert "astra=http.POST; muaddib=http" in node["label"]
    assert any(note.startswith("subtype-normalized: edge.route.demo: astra=http.POST; muaddib=http") for note in notes)


def test_committed_join_names_every_subtype_disagreement(joined):
    graph, notes = joined
    labels = {node["id"]: node["label"] for node in graph["nodes"]}
    disagreeing = set()
    by_id: dict[str, set[str]] = {}
    for name in gen.PASSES:
        sealed = json.loads((ROOT / gen.GRAPH_DIR / f"{name}.json").read_text(encoding="utf-8"))
        for node in sealed["nodes"]:
            if node.get("subtype"):
                by_id.setdefault(node["id"], set()).add(node["subtype"])
    disagreeing = {node_id for node_id, values in by_id.items() if len(values) > 1}
    assert disagreeing
    for node_id in disagreeing:
        assert "[subtype " in labels[node_id], node_id
        assert all(value in labels[node_id] for value in by_id[node_id]), node_id
    listed = {note.split(": ")[1] for note in notes if note.startswith(("subtype-conflict:", "subtype-normalized:"))}
    assert listed == disagreeing


def test_council_revision_holds_the_resolutions_the_join_read(joined):
    """Finding 3: the cited revision's council-resolutions.json is the file the join used."""
    import hashlib
    import subprocess

    graph, _ = joined
    shown = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{gen.COUNCIL_REVISION}:{gen.RESOLUTIONS}"],
        capture_output=True, check=True,
    ).stdout
    used = {item["path"]: item["sha256"] for item in graph["inputs"]}[gen.RESOLUTIONS]
    assert hashlib.sha256(shown).hexdigest() == used
    assert {row["evidence"][0]["revision"] for row in graph["resolutions"]} == {gen.COUNCIL_REVISION}
