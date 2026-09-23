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


def test_phase1_record_id_must_exist_in_that_inventory(schema, example):
    """Astra's counsel on built: a made-up record id used to pass. The graph
    does not own Phase 1 semantics, so a reference must land on a real record."""

    def mutate(graph: dict) -> None:
        graph["nodes"][0]["phase1_refs"][0] = {
            "inventory_path": "docs/internal/philo/data/desk.json",
            "record_id": "desk.does_not_exist",
        }

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "phase1-record-unresolved: nodes[0].phase1_refs[0]: record_id "
        "'desk.does_not_exist' is not a record in "
        "'docs/internal/philo/data/desk.json'"
    ]


def test_phase1_api_reference_must_exist_as_that_method_and_path(schema, example):
    def mutate(graph: dict) -> None:
        graph["nodes"][2]["phase1_refs"][0] = {
            "inventory_path": "docs/generated/openapi.json",
            "method": "GET",
            "path": "/api/desk/does-not-exist",
        }

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "phase1-api-unresolved: nodes[2].phase1_refs[0]: GET "
        "/api/desk/does-not-exist is not declared in 'docs/generated/openapi.json'"
    ]


def test_phase1_api_reference_must_match_the_declared_method(schema, example):
    """A real path under a method the API does not declare is still a miss."""

    def mutate(graph: dict) -> None:
        graph["nodes"][2]["phase1_refs"][0] = {
            "inventory_path": "docs/generated/openapi.json",
            "method": "DELETE",
            "path": "/api/desk/projections",
        }

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "phase1-api-unresolved: nodes[2].phase1_refs[0]: DELETE "
        "/api/desk/projections is not declared in 'docs/generated/openapi.json'"
    ]


def test_phase1_inventory_must_be_a_file_in_the_tree(schema, example):
    def mutate(graph: dict) -> None:
        graph["nodes"][0]["phase1_refs"][0] = {
            "inventory_path": "docs/internal/philo/data/nope.json",
            "record_id": "desk.execute",
        }

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "phase1-inventory-unreadable: nodes[0].phase1_refs[0]: inventory "
        "'docs/internal/philo/data/nope.json' does not exist in the tree"
    ]


def test_claim_review_record_reference_must_exist(schema, example):
    """A claim_ref that names a record and field carries the same Phase 1
    shape, and owes the same proof."""

    def mutate(graph: dict) -> None:
        graph["claim_reviews"][0]["claim_ref"]["record_id"] = "desk.not_a_record"

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "phase1-record-unresolved: claim_reviews[0].claim_ref: record_id "
        "'desk.not_a_record' is not a record in 'docs/generated/domain-model.yaml'"
    ]


def test_source_path_must_exist_in_the_tree(schema, example):
    def mutate(graph: dict) -> None:
        graph["nodes"][0]["sources"][0]["path"] = "web/src/desk/components/NoSuchFile.tsx"

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "source-path-missing: nodes[0].sources[0].path: "
        "'web/src/desk/components/NoSuchFile.tsx' does not exist in the tree"
    ]


def test_evidence_path_must_exist_in_the_tree(schema, example):
    """Evidence carries the same source-reference shape as sources."""

    def mutate(graph: dict) -> None:
        graph["findings"][0]["evidence"][0]["path"] = "holdspeak/db/gone.py"

    violations = validator_module.validate(_mutated(example, mutate), schema)
    assert violations == [
        "source-path-missing: findings[0].evidence[0].path: "
        "'holdspeak/db/gone.py' does not exist in the tree"
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
