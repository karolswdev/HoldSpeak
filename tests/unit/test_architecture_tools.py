"""The architecture tools: the census and the architecture validator.

Grouped by service (the fast diet, 2026-10-12). Moved verbatim from:
- test_philo_census.py
- test_philo_architecture.py
"""
from __future__ import annotations

# ── moved from tests/unit/test_philo_census.py ──
# Census evidence must retain limits and actual handler declarations.

import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]


def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def test_raw_request_is_not_fabricated_schema(tmp_path):
    mod=module('philo_api_reference');source=tmp_path/'route.py'
    source.write_text('''@router.post("/api/demo")
async def demo(request: Request) -> Any:
    body = await request.json()
    return service.preview(body.get("name"))
''')
    row=mod.inspect_module(source)[0]
    assert row['raw_request'] is True
    assert row['declared_response_model'] is None
    assert row['body_access_keys']==['name']
    assert 'service.preview' in row['calls']
    assert row['literal_error_statuses']==[]


def test_declared_method_and_errors_retained(tmp_path):
    mod=module('philo_api_reference');source=tmp_path/'route.py'
    source.write_text('''@router.api_route("/api/demo", methods=["PATCH"], response_model=Reply)
async def demo(body: Payload) -> Reply:
    raise HTTPException(status_code=409)
''')
    row=mod.inspect_module(source)[0]
    assert row['methods']==['PATCH']
    assert row['declared_response_model']=='Reply'
    assert row['literal_error_statuses']==[409]
    assert row['parameters']==[{'name':'body','annotation':'Payload'}]
    assert row['raw_request'] is False


def test_websocket_has_explicit_transport(tmp_path):
    mod=module('philo_api_reference');source=tmp_path/'route.py'
    source.write_text('''@router.websocket("/ws")
async def socket(websocket: WebSocket):
    await websocket.accept()
''')
    assert mod.inspect_module(source)[0]['methods']==['WS']


def test_import_only_file_does_not_invent_handler(tmp_path):
    mod=module('philo_api_reference');source=tmp_path/'route.py'
    source.write_text('from somewhere import router\n')
    assert mod.inspect_module(source)==[]


def test_doctor_census_records_repair_and_condition(tmp_path,monkeypatch):
    mod=module('philo_doctor_reference');monkeypatch.setattr(mod,'ROOT',tmp_path)
    source=tmp_path/'doctor.py'
    source.write_text('''def _check_audio():
    if missing:
        return DoctorCheck(name="Audio", status="FAIL", detail="Missing", fix="Select input")
    return DoctorCheck(name="Audio", status="PASS", detail="Ready")
''')
    rows=mod.extract(source)
    assert len(rows)==1
    assert len(rows[0]['outcomes'])==2
    assert rows[0]['outcomes'][0]['fields']['status']=="'PASS'" or rows[0]['outcomes'][1]['fields']['status']=="'PASS'"
    assert any(r['fields'].get('fix')=="'Select input'" for r in rows[0]['outcomes'])
    assert 'if missing:' in rows[0]['condition_source']


def test_candidate_patterns_do_not_claim_proof():
    mod=module('philo_boundary_census')
    import re
    assert re.search(mod.PATTERNS['http_client'],'import httpx')
    assert re.search(mod.PATTERNS['process_or_shell'],'subprocess.run(args)')
    assert not re.search(mod.PATTERNS['credential_store'],'normal_settings = {}')


def test_repository_categories_separate_runtime_and_evidence():
    mod=module('philo_repository_census')
    assert mod.category('holdspeak/kernel/broker.py')=='python-kernel'
    assert mod.category('pm/roadmap/holdspeak/evidence.png')=='roadmap-and-evidence'
    assert mod.category('apple/Sources/Client.swift')=='apple-clients-and-native-runtime'


def test_workspace_reference_rejects_invalid_rect_and_version():
    import copy
    import json
    from jsonschema import Draft202012Validator
    schema=json.loads((ROOT/'architecture/desk-workspace.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    validate=Draft202012Validator(schema)
    good={'version':1,'windowsById':{},'panel':{'rects':{'surface:a':{'x':0,'y':0,'w':600,'h':400}},'order':[],'max':[]},'zoneWindows':[],'zoneViewPrefs':{}}
    assert not list(validate.iter_errors(good))
    negative=copy.deepcopy(good);negative['panel']['rects']['surface:a']['w']=-1
    assert list(validate.iter_errors(negative))
    future=copy.deepcopy(good);future['version']=999
    assert list(validate.iter_errors(future))
    # A proposed preference is not silently accepted as today's saved workspace.
    proposed=copy.deepcopy(good);proposed['theme']={'mode':'light'}
    assert list(validate.iter_errors(proposed))


def test_config_census_keeps_default_expression_without_executing_it(tmp_path):
    mod = module('philo_config_reference')
    mod.ROOT = tmp_path
    source = tmp_path / 'config.py'
    source.write_text('''@dataclass
class Config:
    names: list[str] = field(default_factory=network_lookup)
    limit: int = 5

class Service:
    not_config: str = "ignored"
''')
    rows = mod.extract(source)
    assert [(row['field'], row['default_expression']) for row in rows] == [
        ('names', 'field(default_factory=network_lookup)'), ('limit', '5')
    ]


def test_api_candidates_are_independent_of_directory_enumeration(tmp_path, monkeypatch):
    import json
    mod = module('philo_api_reference')
    (tmp_path / 'docs/internal/philo').mkdir(parents=True)
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'docs/api-surface.json').write_text(json.dumps({'routes': [
        {'module': 'demo', 'path': '/api/example', 'methods': ['GET']}
    ]}))
    (tmp_path / 'docs/internal/philo/snapshot.json').write_text(json.dumps({'commit': 'fixture'}))
    first = tmp_path / 'tests/test_a.py'
    last = tmp_path / 'tests/test_z.py'
    first.write_text('# /api/example')
    last.write_text('# /api/example')
    monkeypatch.setattr(Path, 'rglob', lambda self, pattern: iter([last, first]))
    reverse = mod.generate(tmp_path)
    monkeypatch.setattr(Path, 'rglob', lambda self, pattern: iter([first, last]))
    forward = mod.generate(tmp_path)
    assert reverse == forward
    row = json.loads(forward['docs/generated/api-reference.json'])['routes'][0]
    assert row['test_candidates'] == ['tests/test_a.py', 'tests/test_z.py']


# ── moved from tests/unit/test_philo_architecture.py ──

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


def test_existing_build_copy_is_not_source_evidence(tmp_path: Path) -> None:
    root = _root(tmp_path)
    built = root / 'holdspeak/static/_built/qlippy/README.md'
    built.parent.mkdir(parents=True)
    built.write_text('# Build copy\n')
    path = root / 'docs/internal/philo/data/runtime.json'
    shard = json.loads(path.read_text())
    shard['capabilities'][0]['sources'][0] = {
        'path': str(built.relative_to(root)), 'line': 1, 'symbol': 'module',
        'claim': 'A generated file must not masquerade as maintained source.'
    }
    path.write_text(json.dumps(shard))
    result = validate(root, expected_shards=('runtime',))
    assert any('build or environment artifact' in str(error) for error in result.errors)
