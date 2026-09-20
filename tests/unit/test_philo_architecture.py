from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_capability_docs import generate
from scripts.validate_architecture import validate


def _capability() -> dict:
    return {
        "id": "demo.run",
        "name": "Run demo",
        "purpose": "Run the bounded demo operation.",
        "domain": "demo",
        "status": "experimental",
        "status_reason": "Source is present and execution is not yet recorded.",
        "exposure": "developer",
        "surfaces": ["demo"],
        "entry_points": ["src.py::run"],
        "platforms": {"macos": "unknown", "linux_x11": "unknown", "linux_wayland": "unknown", "ipad": "not_applicable", "aipi": "not_applicable"},
        "inputs": [], "outputs": [], "persistence": [], "apis": [], "configuration": [],
        "dependencies": ["free text dependency"], "model_requirements": [], "network_requirements": [],
        "trust_boundary": "The demo stays in the test repository.",
        "egress_possible": False, "egress": "No data leaves the repository.",
        "side_effect": "none", "authority": "The test caller owns the local operation.", "kernel_operations": [],
        "sources": [{"path": "src.py", "symbol": "run", "line": 1, "claim": "The demo entry point exists."}],
        "tests": [{"path": "test_src.py", "node": "test_run", "assertion": "The operation returns its input.", "execution": "not_run"}],
        "docs": ["docs/demo.md"], "limitations": [], "failure_states": [], "replacement": None,
        "evidence_level": "source_and_assertions_inspected", "release_availability": "unverified", "owner_observed": False,
    }


def _root(tmp_path: Path, *, second_shard: bool = False) -> Path:
    data = tmp_path / "docs/internal/philo/data"
    data.mkdir(parents=True)
    (tmp_path / "docs/internal/philo/snapshot.json").write_text(json.dumps({"commit": "snap"}))
    (tmp_path / "src.py").write_text("def run():\n    return 1\n")
    (tmp_path / "test_src.py").write_text("def test_run():\n    assert 1 == 1\n")
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs/demo.md").write_text("# Demo\n")
    shard = {"schema_version": 1, "snapshot": "snap", "capabilities": [_capability()], "components": [], "integrations": [], "domain_model": [], "trust_boundaries": []}
    (data / "runtime.json").write_text(json.dumps(shard))
    if second_shard:
        (data / "voice.json").write_text(json.dumps(shard))
    return tmp_path


def test_valid_metadata_resolves_python_symbols_and_test_nodes(tmp_path: Path) -> None:
    result = validate(_root(tmp_path), expected_shards=("runtime",))
    assert result.ok, [str(item) for item in result.errors]


def test_invalid_metadata_reports_path_node_enum_and_egress(tmp_path: Path) -> None:
    root = _root(tmp_path)
    path = root / "docs/internal/philo/data/runtime.json"
    shard = json.loads(path.read_text())
    cap = shard["capabilities"][0]
    cap["status"] = "made_up"
    cap["egress_possible"] = True
    cap["egress"] = ""
    cap["sources"][0]["path"] = "missing.py"
    cap["sources"][0]["line"] = 99
    cap["sources"].append({"path": "src.py", "symbol": "run", "line": 99, "claim": "The line is deliberately outside the file."})
    cap["tests"][0]["node"] = "test_missing"
    path.write_text(json.dumps(shard))
    result = validate(root, expected_shards=("runtime",))
    messages = "\n".join(str(item) for item in result.errors)
    assert "not one of" in messages
    assert "source path does not exist" in messages
    assert "outside src.py" in messages
    assert "test node 'test_missing' not found" in messages
    assert "egress_possible requires" in messages


def test_duplicate_ids_and_snapshot_drift_are_errors(tmp_path: Path) -> None:
    root = _root(tmp_path, second_shard=True)
    voice = root / "docs/internal/philo/data/voice.json"
    shard = json.loads(voice.read_text())
    shard["snapshot"] = "different"
    voice.write_text(json.dumps(shard))
    result = validate(root, expected_shards=("runtime", "voice"))
    messages = "\n".join(str(item) for item in result.errors)
    assert "duplicate capabilities ID 'demo.run'" in messages
    assert "snapshot drift" in messages


def test_generation_and_coverage_are_deterministic_and_do_not_promote_paths(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = generate(root, allow_missing_shards=True)
    second = generate(root, allow_missing_shards=True)
    assert first == second
    assert "docs/generated/capabilities.yaml" in first
    coverage = json.loads(first["docs/generated/doc-coverage.json"])
    assert coverage["totals"]["source_paths"] == [1, 1]
    assert coverage["totals"]["assertions_inspected"] == 1
    assert coverage["totals"]["tests_executed"] == 0
    assert coverage["totals"]["semantics_unresolved"] == 1


def test_typescript_token_and_test_title_fallback_is_static(tmp_path: Path) -> None:
    root = _root(tmp_path)
    (root / "src.py").unlink()
    (root / "test_src.py").unlink()
    (root / "src.ts").write_text("export const run = () => 1;\n")
    (root / "test_src.ts").write_text('it("runs the demo", () => { expect(true).toBe(true); });\n')
    data = root / "docs/internal/philo/data/runtime.json"
    shard = json.loads(data.read_text())
    cap = shard["capabilities"][0]
    cap["entry_points"] = ["src.ts::run"]
    cap["sources"][0] = {"path": "src.ts", "symbol": "run", "line": 1, "claim": "The token exists."}
    cap["tests"][0] = {"path": "test_src.ts", "node": "runs the demo", "assertion": "The test title is present.", "execution": "not_run"}
    data.write_text(json.dumps(shard))
    result = validate(root, expected_shards=("runtime",))
    assert result.ok, [str(item) for item in result.errors]


def test_coverage_requires_assertion_and_execution_on_same_test(tmp_path: Path) -> None:
    from scripts.check_doc_coverage import _record_coverage

    record = _capability()
    record["tests"] = [
        {"path": "test_src.py", "node": "test_run", "assertion": "Result is checked.", "execution": "not_run"},
        {"path": "test_src.py", "node": "test_other", "assertion": "", "execution": "passed"},
    ]
    assert _record_coverage(tmp_path, "capabilities", record)["semantic_status"] == "unresolved"
    record["tests"][0]["execution"] = "passed"
    assert _record_coverage(tmp_path, "capabilities", record)["semantic_status"] == "partially_evidenced"


def test_explicit_api_reference_checks_method_and_route(tmp_path: Path) -> None:
    root = _root(tmp_path)
    (root / "docs/api-surface.json").write_text(json.dumps({"routes": [
        {"path": "/api/items/{item_id}", "methods": ["GET"]}
    ]}))
    path = root / "docs/internal/philo/data/runtime.json"
    shard = json.loads(path.read_text())
    shard["capabilities"][0]["apis"] = ["GET /api/items/{id}"]
    path.write_text(json.dumps(shard))
    assert validate(root, expected_shards=("runtime",)).ok
    shard["capabilities"][0]["apis"] = ["POST /api/items/{id}", "/api/deleted"]
    path.write_text(json.dumps(shard))
    errors = validate(root, expected_shards=("runtime",)).errors
    assert sum("API reference absent" in str(error) for error in errors) == 2


def test_requirement_catalogue_checks_its_own_source_references(tmp_path: Path) -> None:
    root = _root(tmp_path)
    row = {"id": "FR-DEMO-001", "status": "IMPLEMENTED", "sources": [
        {"path": "src.py", "symbol": "invented", "line": 1, "claim": "Incorrect anchor"}
    ], **{field: "declared" for field in ("statement", "rationale", "owner", "acceptance", "test", "gap")}}
    (root / "docs/internal/philo/data/requirements.json").write_text(json.dumps({"requirements": [row, row]}))
    messages = '\n'.join(str(error) for error in validate(root, expected_shards=("runtime",)).errors)
    assert "symbol 'invented' not found" in messages
    assert "missing or duplicate identity" in messages
