"""Ask consumes one tool-owned disclosure, including long authority facts."""
from pathlib import Path

from holdspeak.services.held_tool_details import held_call_details
from tests.integration.test_held_tool_review_13d import authority_rig  # noqa: F401
from tests.integration.test_held_tool_review_13d import db  # noqa: F401
from tests.integration.test_held_tool_facts_round3 import held, OWNER
from tests.unit.test_desk_speak import _record


def test_a_long_held_authority_is_recorded_for_ask(authority_rig, tmp_path):
    rig, _mode = authority_rig
    call = held('agent.hand', {'kind': 'action', 'id': 'ai_1', 'profile': 'codex-default'})
    details = held_call_details(call, OWNER)
    assert any(f['label'] == 'Authority binding' for f in details['facts'])
    assert not rig.tmux.calls, 'Reading the question must not start an agent'
    _record('ask.held-authority.wire', {'held': details}, tmp_path,
            'tests/integration/test_ask_held_words.py::test_a_long_held_authority_is_recorded_for_ask',
            folder=Path(__file__).resolve().parents[2] / 'web/src/test/wire')


def test_a_declared_source_kind_and_withheld_reference_have_face_words():
    call = held('door.add_item', {'task': 'Review the recovery point', 'due': '2026-10-23',
                                 'source_type': 'meeting', 'source_ref': 'private-source'})
    details = held_call_details(call, OWNER)
    assert {'label': 'Source kind', 'value': 'Meeting'} in details['facts']
    assert {'label': 'Source', 'value': 'Hidden'} in details['facts']
    assert 'private-source' not in str(details)
