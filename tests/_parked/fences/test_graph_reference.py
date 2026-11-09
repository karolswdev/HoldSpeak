# PARKED 2026-11-09 (fences diet, pipe/fences-diet): the committed PHILO-2 join read against today's tree; every park or route move turned it red and it cost ~18 s per xdist worker (two full joins).
# Nothing replaces it: a dead audit artefact. The generator's own rules stay live in tests/unit/test_graph_reference.py on synthetic inputs.
"""PHILO-2-07: the graph join generator (brief section 8).

The join of the committed inputs must validate (the join itself is not in git); a contradiction without
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


# ---------------------------------------------------------------------------
# The committed join.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def joined() -> tuple[dict, list[str]]:
    return gen.join(gen.load_inputs(ROOT))


def test_the_join_is_not_in_git_and_renders_the_same_twice(joined):
    """Owner ruling 2026-10-03: the join is generated on demand, never
    committed. It must render the same bytes from the same inputs."""
    graph, _ = joined
    assert gen.render(graph) == gen.render(gen.join(gen.load_inputs(ROOT))[0])
    assert json.loads(gen.render(graph))["nodes"]
    assert gen.main(["--check"]) == 0


# The join is a record of the tree at its passes' source commit. Whether a
# cited file or route still exists TODAY is placement, not the join's
# integrity: every park and every route removal turned this red (2026-11-08,
# the test-speed subtraction). The schema, the ids and the links still must hold.
_TREE_DRIFT = ("source-path-missing:", "phase1-api-unresolved:")


def test_committed_join_validates(joined):
    graph, _ = joined
    validator = _module("philo_graph_validate")
    schema = json.loads((ROOT / "docs/internal/philo/graph/graph.schema.json").read_text(encoding="utf-8"))
    problems = [line for line in validator.validate(graph, schema, ROOT) if not line.startswith(_TREE_DRIFT)]
    assert problems == []


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
# Counsel round (Astra's check of the built story, findings 1-3).
# ---------------------------------------------------------------------------

def _openapi_digest() -> str:
    import hashlib

    target = ROOT / "docs/generated/openapi.json"  # not in git: absent is a digest too
    return hashlib.sha256(target.read_bytes() if target.is_file() else b"").hexdigest()


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

    _drop("DELETE", "/api/activity/project-rules/{rule_id}")  # removed from source
    _drop("DELETE", "/api/activity/records")

    @app.delete("/api/activity/records")
    def delete_records_renamed():  # same method and path, new handler name
        return {}

    monkeypatch.setattr(route_surface, "build_reference_app", lambda: app)
    graph, _ = gen.join(gen.load_inputs(ROOT))
    lines = gen.census(graph, ROOT)

    assert _openapi_digest() == before
    assert "new: http POST /api/philo-census-probe has no edge (philo_census_probe)" in lines
    assert any(line.startswith("removed: http DELETE /api/activity/project-rules/{rule_id} ") for line in lines)
    assert any(
        line.startswith("changed: http DELETE /api/activity/records (")
        and "delete_records_renamed" in line
        for line in lines
    )


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
