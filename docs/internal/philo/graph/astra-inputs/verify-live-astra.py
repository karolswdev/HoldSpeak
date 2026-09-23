"""Read-only consistency checks for the sealed Astra audit artifacts."""
import hashlib
import json
import subprocess
from pathlib import Path
from collections import Counter

base = Path('docs/internal/philo/graph')
graph = json.loads((base / 'live-astra.json').read_text())
atlas = json.loads((base / 'atlas.json').read_text())
run_case_ids = {o['case_id'] for o in graph['observations']}
assert graph['cases'] == [c for c in atlas['cases'] if c['id'] in run_case_ids], 'Live cases differ from the original atlas run cases'
for path in ['scripts/graph_walk.py', 'docs/internal/philo/graph/atlas.json']:
    committed = subprocess.check_output(['git', 'show', 'f575a582:' + path])
    assert Path(path).read_bytes() == committed, f'Shared input changed: {path}'

for entry in graph['inputs']:
    assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest() == entry['sha256'], entry['path']

raws = {r['run_id']: (p, r) for p in sorted((base / 'observations/astra').glob('*/observation.json'))
        for r in [json.loads(p.read_text())]}
incidents = json.loads((base/'astra-inputs/execution-incidents.json').read_text())['incidents']
excluded_runs = {run for incident in incidents for run in incident['affected_runs']}
assert len(raws) == len(graph['observations']), 'Raw/graph run count mismatch'
for obs in graph['observations']:
    path, raw = raws[obs['run_id']]
    assert raw.get('complete') is True or raw['run_id'] in excluded_runs, f'Unexplained incomplete raw record: {path}'
    assert raw['provenance']['revision'] == graph['source_commit']
    assert obs['id'] == raw['id'].lower()
    assert obs['verdict'] == raw['verdict']
    assert obs['brain'] == raw['brain'] == 'astra'
    assert obs['case_id'] == raw['case_id']
    assert obs['viewport'] == raw['viewport']
    for key in ('before', 'after', 'initial_feedback', 'terminal_outcome'):
        field = json.loads(obs[key])
        assert field['raw_record'] == str(path)
        assert field['value'] == raw.get(key)
    for key in ('frontend_build', 'hub', 'clock'):
        assert json.loads(obs['provenance'][key]) == raw['provenance'][key]
    if raw['job'] == 'j6':
        assert raw['provenance']['engine_mode'] == 'real'
    else:
        assert raw['provenance']['engine_mode'] != 'real'
    if raw['provenance'].get('db_path'):
        resolved = Path(raw['provenance']['db_path'])
        assert str(resolved).startswith(('/private/var/folders/', '/var/folders/', '/tmp/'))
        assert '/Users/karol/.local/' not in str(resolved)

runtime = json.loads((base / 'astra-inputs/j6-runtime-atlas.json').read_text())
changes = json.loads((base / 'astra-inputs/j6-address-resolution.json').read_text())
expected = json.loads(json.dumps(atlas))
for change in changes:
    case = next(c for c in expected['cases'] if c['id'] == change['case_id'])
    index = int(change['field'].split('[')[1].split(']')[0])
    assert case['job'] == 'j6' and case['setup'][index]['value'] == change['from']
    assert change['to'] == 'http://192.168.1.43:8080/v1'
    case['setup'][index]['value'] = change['to']
assert runtime == expected, 'Runtime atlas contains more than the authorized address resolution'

preflight = {x['case_id']: x for x in json.loads((base/'astra-inputs/preflight.json').read_text())['entries']}
observed_slots = {(r['case_id'],r['viewport']) for _,r in raws.values() if r['run_id'] not in excluded_runs and r.get('complete') is True}
for case in atlas['cases']:
    if case['applicability'] != 'applicable':
        assert case['reason']
        continue
    for viewport in case['viewports'] or [1440]:
        if (case['id'],viewport) in observed_slots:
            continue
        assert case['id'] in preflight, f'Unaccounted viewport {case["id"]} {viewport}'
        block = preflight[case['id']]
        assert block['invoked'] is False and block['verdict'] == 'blocked' and block['reason']
        assert viewport in (block['viewports'] or [1440])
order = []
for _,raw in sorted(raws.values(),key=lambda item:item[1]['provenance']['clock']['started_utc']):
    order.append(12 if raw['job']=='beyond' else int(raw['job'][1:]))
assert order == sorted(order), 'The J1–J11 then beyond ordering was not preserved'
for incident in incidents:
    assert incident['replacement_runs'], f'No serial replacement evidence for {incident["id"]}'
    affected_slots = {(raws[r][1]['case_id'],raws[r][1]['viewport']) for r in incident['affected_runs']}
    replacement_slots = {(raws[r][1]['case_id'],raws[r][1]['viewport']) for r in incident['replacement_runs']}
    assert affected_slots == replacement_slots
    assert all(raws[r][1]['complete'] is True for r in incident['replacement_runs'])
report = (base/'live-astra.md').read_text()
assert all(c['id'] in report for c in atlas['cases'])
assert all(f'**J{i} —' in report for i in range(1,12))
assert 'TECHNICAL:' in report and 'OWNER USEFULNESS:' in report
print(f'OK {len(raws)} raw runs match graph rows and provenance; input hashes match; original atlas and rig unchanged; runtime atlas has only {len(changes)} authorized address resolutions.')
print(f'OK all 73 cases and applicable viewport slots accounted for; J1–J11 precede beyond; J6 real and other runs non-real; {len(excluded_runs)} incident runs retained and excluded, with complete serial replacements. Raw verdicts: {dict(Counter(r["verdict"] for _,r in raws.values()))}')
