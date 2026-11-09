# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_blueprint_graph_conformance.py to restore.

# ruff: noqa


# --- test_fixture_nodes_omit_unset_provenance_keys: P2: asserts the shape of the test's own fixture file
def test_fixture_nodes_omit_unset_provenance_keys() -> None:
    """The inherit-the-default contract is the ABSENCE of the key (never null):
    Swift's nil runsOn/failurePolicy must not reach the wire at all."""
    graph = _load("blueprint-linear-sample.json")
    by_id = {n["id"]: n for n in graph["nodes"]}
    assert "runs_on" not in by_id["keep"]
    assert "failure_policy" not in by_id["keep"]
    assert by_id["ask"]["runs_on"] == "endpoint"
