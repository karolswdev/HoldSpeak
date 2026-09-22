"""PHILO-2-01: the graph schema of brief section 8 and its validator.

The worked example must validate, and four shapes the brief forbids must be
refused by name: a link endpoint that resolves to nothing, an observation
without runtime provenance, a finding without a bin, and a case with no
expected-result predicate.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs" / "internal" / "philo" / "graph" / "graph.schema.json"
EXAMPLE_PATH = ROOT / "docs" / "internal" / "philo" / "graph" / "examples" / "graph.example.json"


def _module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator_module = _module("philo_graph_validate")


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def example() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def test_schema_is_a_valid_draft_2020_12_schema(schema):
    from jsonschema import Draft202012Validator

    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_worked_example_passes_schema_and_integrity(schema, example):
    assert validator_module.validate(example, schema) == []


def test_worked_example_joins_phase1_records_and_api_pairs(example):
    """Section 8: Phase 1 references are inventory path plus record id, and
    API references are method and path.  The example must actually carry both
    shapes, or it does not demonstrate the join it exists to demonstrate."""
    refs = [ref for node in example["nodes"] for ref in node["phase1_refs"]]
    assert {"inventory_path": "docs/internal/philo/data/desk.json", "record_id": "desk.receipt"} in refs
    assert {
        "inventory_path": "docs/generated/openapi.json",
        "method": "GET",
        "path": "/api/desk/projections",
    } in refs


def test_observations_are_stored_one_per_brain_pass_viewport(example):
    """Section 8: never overwrite one brain, viewport or attempt with another."""
    keys = [
        (row["brain"], row["pass"], row.get("viewport"))
        for row in example["observations"]
    ]
    assert len(keys) == len(set(keys))
    assert len(keys) == len(example["observations"])


def _mutated(example: dict, mutate) -> dict:
    graph = copy.deepcopy(example)
    mutate(graph)
    return graph


def test_unresolved_link_endpoint_is_refused(schema, example):
    def mutate(graph: dict) -> None:
        graph["links"][0]["to"] = "iface.shade.does_not_exist"

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "link-endpoint-unresolved: links[0].to: 'iface.shade.does_not_exist' "
        "does not resolve to a node"
    ]


def test_observation_without_provenance_is_refused(schema, example):
    def mutate(graph: dict) -> None:
        graph["observations"][0].pop("provenance")

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert len(violations) == 1
    assert violations[0].startswith("schema: observations.0: ")
    assert "'provenance' is a required property" in violations[0]


def test_finding_without_a_bin_is_refused(schema, example):
    def mutate(graph: dict) -> None:
        graph["findings"][0].pop("bin")

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert len(violations) == 1
    assert violations[0].startswith("schema: findings.0: ")
    assert "'bin' is a required property" in violations[0]


def test_case_without_an_expected_predicate_is_refused(schema, example):
    def mutate(graph: dict) -> None:
        graph["cases"][0]["expected"].pop("predicate")

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert len(violations) == 1
    assert violations[0].startswith("schema: cases.0.expected: ")
    assert "'predicate' is a required property" in violations[0]


def test_duplicate_ids_are_refused(schema, example):
    def mutate(graph: dict) -> None:
        graph["nodes"].append(copy.deepcopy(graph["nodes"][0]))

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "duplicate-id: nodes[10]: id 'edge.shade.desk_memory' is already used by nodes[0]"
    ]


def test_cli_exits_zero_on_the_example_and_one_on_a_broken_graph(tmp_path, capsys, example):
    clean = validator_module.main([str(EXAMPLE_PATH)])
    first = capsys.readouterr().out
    assert clean == 0

    again = validator_module.main([str(EXAMPLE_PATH)])
    assert capsys.readouterr().out == first, "validator output must be deterministic"
    assert again == 0

    broken = copy.deepcopy(example)
    broken["resolutions"][0]["finding_id"] = "fnd.nothing_here"
    broken_path = tmp_path / "graph.json"
    broken_path.write_text(json.dumps(broken), encoding="utf-8")

    assert validator_module.main([str(broken_path)]) == 1
    out = capsys.readouterr().out
    assert "resolution-finding-unresolved: resolutions[0].finding_id" in out
