"""Reproduce PHILO-5-03 rig reds and greens in an isolated HOME.

Calibration uses its labelled fixture server. Snapshot and resource checks
use real product hubs; restart mutations consume a retained real atlas run.
No product source is modified. Every unexpected result exits nonzero.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'holdspeak/operations.py').exists())
sys.path.insert(0, str(ROOT))
from scripts import graph_walk as gw
from tests.unit import test_philo5_graph_op as checks

OUT = Path(__file__).resolve().parent


def calibrations() -> None:
    original = gw.STEP_KINDS
    try:
        gw.STEP_KINDS = frozenset(original - {'op'})
        record = gw.calibrate(OUT / 'op-removed', brain='astra', headless=True,
                              cases=[gw.CALIBRATION_OP_CASES[0]])[0]
        assert record['verdict'] == 'blocked', record
        assert 'not in the rig' in ' '.join(record['notes']), record
        print('RED op removed: calibration CAL-op-success BLOCKED; trigger not dispatched')
    finally:
        gw.STEP_KINDS = original
    for record in gw.calibrate(OUT / 'op-calibration', brain='astra', headless=True):
        actual = (record['verdict'], (record.get('terminal_outcome') or {}).get('state', '-'))
        expected = gw.CALIBRATION_OP_EXPECTED[record['case_id']]
        assert actual == expected, (record['case_id'], actual, expected)
        print('GREEN calibration', record['case_id'], actual)


def snapshot_baseline() -> None:
    source = subprocess.check_output(['git', '-C', str(ROOT), 'show',
        'c4d464985c25b296906608f0b256960d229c786c:scripts/graph_walk.py'], text=True)
    legacy = types.ModuleType('philo5_graph_walk_baseline')
    legacy.__file__ = str(ROOT / 'scripts/graph_walk.py')
    sys.modules[legacy.__name__] = legacy
    exec(compile(source, legacy.__file__, 'exec'), legacy.__dict__)
    with tempfile.TemporaryDirectory(prefix='philo5-fence-') as directory:
        hub = gw.Hub(Path(directory), token='philo5-fence-owner').start()
        try:
            status, made = hub.api('POST', '/api/decisions', {'title': 'Snapshot real producer'})
            assert status == 201, (status, made)
            decision = made.get('decision', made)
            case = {'expected': {'observe_at': f"protocol: GET /api/decisions/{decision['id']}"}}
            try:
                legacy.snapshot(None, case, hub)
            except AttributeError as error:
                assert 'evaluate' in str(error), error
                print('RED base snapshot:', type(error).__name__, str(error))
            else:
                raise AssertionError('base snapshot unexpectedly passed without a page')
            observed = gw.snapshot(None, case, hub)
            assert observed['protocol']['payload']['decision']['id'] == decision['id']
            print('GREEN headless snapshot: real producer decision ID read back without a page')
        finally:
            hub.stop()


def other_mutations() -> None:
    original = gw.OP_MCP_PROJECTIONS['decision.create']['name']
    try:
        gw.OP_MCP_PROJECTIONS['decision.create']['name'] = 'desk.renamed'
        try:
            checks.test_canonical_map_matches_live_operation_exposure_projection()
        except AssertionError as error:
            print('RED canonical projection rename:', str(error))
        else:
            raise AssertionError('renamed projection escaped the exposure fence')
    finally:
        gw.OP_MCP_PROJECTIONS['decision.create']['name'] = original
    checks.test_canonical_map_matches_live_operation_exposure_projection()
    print('GREEN canonical projections match live descriptors')

    decoder = gw._decode_mcp_envelope
    def content_only(envelope):
        wire = copy.deepcopy(envelope)
        if isinstance(wire.get('result'), dict):
            wire['result'].pop('contents', None)
        return decoder(wire)
    try:
        gw._decode_mcp_envelope = content_only
        with tempfile.TemporaryDirectory(prefix='philo5-resource-red-') as directory:
            try:
                checks.test_real_hub_thought_capture_preserves_revisions_and_workspace_cursor(Path(directory))
            except gw.Blocked as error:
                assert 'thought.aggregate_revision' in str(error), error
                print('RED real Thought resource decoder:', str(error))
            else:
                raise AssertionError('contents decoder mutation escaped the real-resource fence')
    finally:
        gw._decode_mcp_envelope = decoder
    with tempfile.TemporaryDirectory(prefix='philo5-resource-green-') as directory:
        checks.test_real_hub_thought_capture_preserves_revisions_and_workspace_cursor(Path(directory))
    print('GREEN real Thought resource: typed revisions, cursor, save and readback')

    path = next((OUT.parent / 'real/op').glob('*s3_same_summary_after_restart.op*/observation.json'))
    record = json.loads(path.read_text())
    predicate = {'kind': 'op_field', 'path': 'intel.summary', 'nonempty': True, 'restart_required': True}
    assert record['verdict'] == 'pass' and gw.check_predicate(predicate, record['before'], record['after'])[0]
    for flag in ('summary_retained', 'receipt_retained', 'meeting_identity_retained'):
        after = copy.deepcopy(record['after'])
        after['restart'].pop(flag)
        ok, why = gw.check_predicate(predicate, record['before'], after)
        assert not ok, flag
        print('RED actual atlas restart flag omitted:', flag, why)
    print('GREEN actual atlas restart retains all three relationships:', record['run_id'])


if __name__ == '__main__':
    calibrations()
    snapshot_baseline()
    other_mutations()
    print('ALL REQUIRED RIG FENCE RESULTS VERIFIED')
