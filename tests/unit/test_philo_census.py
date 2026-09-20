"""Census evidence must retain limits and actual handler declarations."""
from __future__ import annotations
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
