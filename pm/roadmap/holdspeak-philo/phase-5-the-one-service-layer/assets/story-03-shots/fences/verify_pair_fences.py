"""Mutation fences over retained real atlas output; originals are never edited."""
import copy
import json
import sys
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'holdspeak/operations.py').exists())
sys.path.insert(0, str(ROOT))
from scripts import philo5_pairs as pairs
ASSETS = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ASSETS / 'pairs-input.json').read_text())['pairs']

def entry(needle):
    return copy.deepcopy(next(p for p in SOURCE if p['pair_id'] == needle))

def read(path):
    return json.loads((ROOT / path).read_text())

def observation(prefix):
    paths = [p for p in ASSETS.glob('*/*/*/observation.json') if p.parent.name.startswith(prefix)]
    assert len(paths) == 1, paths
    return json.loads(paths[0].read_text())

def inline(pair, side, obs):
    pair[side] = {'observation': obs}
    return pair

def check_result(label, pair, expected):
    result = pairs.compare_pair(pair)
    assert result['verdict'] == expected, (result['verdict'], [(c['name'],c['status']) for c in result['checks']])
    failures = [(c['name'], c['status'], c['detail']) for c in result['checks'] if c['status'] != 'pass']
    print(label, expected.upper(), json.dumps(failures))
    return result

def last_op_read(obs, name):
    record = next(r for r in reversed(obs['after']['op_reads']) if r['name'] == name)
    # Match the comparator's real producer field, not its response alias.
    return record.get('domain_response', record.get('response'))

# One changed field in a real producer's final decision.read must fail.
p = entry('case.closure.chain.s4_decision_recorded')
o = read(p['op']['path'])
last_op_read(o, 'decision.read')['title'] = 'MUTATION: wrong saved title'
check_result('RED actual decision.read one-field title skew:', inline(p, 'op', o), 'fail')
check_result('GREEN actual decision pair:', entry('case.closure.chain.s4_decision_recorded'), 'pass')

# A previously retained predicate PASS is not chain proof when restart flags fail.
p = entry('case.closure.chain.s4_decision_recorded')
r = check_result('RED actual S4 old false restart flags:', inline(p, 'op', observation('20260924T214818Z')), 'blocked')
assert all(next(c for c in r['checks'] if c['name'] == 'restart.op.' + key)['status'] == 'fail' for key in ('summary_retained', 'receipt_retained', 'meeting_identity_retained'))

# The old unwrapped case really ran before the next-day lookback window.
o = observation('20260924T221450Z')
c = pairs._breakage_clock_check(o, 'browser')
assert c['status'] == 'blocked', c
print('RED actual breakage before-close clock:', c['status'].upper(), c['detail'])
new = observation('20260924T222649Z')
c = pairs._breakage_clock_check(new, 'browser')
assert c['status'] == 'pass', c
print('GREEN actual wrapped breakage clock:', c['status'].upper(), c['detail'])

# Old op stopped at setup. Compare the actual day-one cause payload explicitly;
# it cannot be promoted into a final next-day read or a completed pair.
p = entry('case.closure.chain.s5_next_day_brief_with_breakage')
old = observation('20260924T223016Z')
check_result('RED actual old incomplete breakage pair:', inline(p, 'op', old), 'blocked')
old_brief = next(r['response'] for r in old['setup'] if r.get('name') == 'brief.generate')
new_brief = next(r['payload'] for r in new['after']['api_reads'] if r['path'] == '/api/brief/latest')
c = pairs._compare_exact('next_day.breakage_causes', pairs._breakage_text_detail_projection(old_brief), pairs._breakage_text_detail_projection(new_brief))
assert c['status'] == 'fail', c
print('RED next_day.breakage_causes (retained day-one op setup vs browser final; diagnostic only):', c['status'].upper(), json.dumps(c))
r = check_result('GREEN actual normalized breakage pair:', entry('case.closure.chain.s5_next_day_brief_with_breakage'), 'pass')
assert next(c for c in r['checks'] if c['name'] == 'next_day.breakage_causes')['status'] == 'pass'

# Newly checked seams: empty shelf is data; a changed brief still fails.
p = entry('case.j10.brief_item_shelf.refused');o = read(p['op']['path'])
last_op_read(o, 'brief.latest')['headline'] = 'MUTATION: changed despite refusal'
check_result('RED actual shelf refusal changed brief:', inline(p, 'op', o), 'fail')
check_result('GREEN actual refused empty shelf with unchanged brief:', entry('case.j10.brief_item_shelf.refused'), 'pass')
p = entry('case.j10.brief_item_shelf.refused');o = read(p['op']['path']);o['after']['op_reads'] = [];o['after'].pop('op', None)
check_result('RED missing named durable refusal reads:', inline(p, 'op', o), 'blocked')

p = entry('case.closure.chain.s2_summary_with_host');o = read(p['op']['path'])
last_op_read(o, 'meeting.read')['run_receipt']['selection_hash'] = 'MUTATION: wrong route hash'
check_result('RED actual summary receipt route identity:', inline(p, 'op', o), 'fail')
check_result('GREEN actual summary receipt route identity:', entry('case.closure.chain.s2_summary_with_host'), 'pass')

p = entry('case.j11.thought_keep.receipt_time')
check_result('RED actual first Thought run did not change body:', inline(p, 'op', observation('20260924T221903Z')), 'fail')
check_result('GREEN actual Thought saved-body transition:', entry('case.j11.thought_keep.receipt_time'), 'pass')

for p in SOURCE:
    assert pairs.compare_pair(p)['verdict'] == 'pass', p['pair_id']
print('GREEN all 18 named pairs plus 2 replay pairs: 20 PASS; original observations unchanged')
