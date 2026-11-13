"""A held permission commits to the words and authority the owner read."""
from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak import operations
from holdspeak.mcp import tools
from holdspeak.principals import Principal, PrincipalKind, agent_credentials
from holdspeak.services.held_tool_details import held_call_details
from holdspeak.services.errors import ServiceError
from tests.integration.test_held_tool_facts_round3 import OWNER, held, perform, PRIVATE
from tests.integration.test_held_tool_facts_round5 import fact_rig  # noqa: F401
from tests.unit.test_desk_ask_ai import hub  # noqa: F401


@pytest.fixture
def prompt_rig(hub, monkeypatch):
    from holdspeak.agent_context import screen_watch as watch
    from tests.unit.test_screen_rules import _observe, _screen, T0
    from holdspeak.services.agent_hand_service import AgentHandService
    store = watch.ScreenStore()
    _observe(store, 'claude-rig-permission', T0)
    content = {'screen': _screen('claude-rig-permission')}
    ledger = SimpleNamespace(get=lambda _: {'state': 'launched', 'session': 'hs-l1'})
    monkeypatch.setattr(watch, 'STORE', store)
    monkeypatch.setattr(watch, 'first_pane', lambda *a: '%7')
    monkeypatch.setattr(watch, 'capture', lambda *a: content['screen'])
    port = '_answer_prompt' if hasattr(watch, '_answer_prompt') else 'answer_launch'
    original = getattr(watch, port)
    monkeypatch.setattr(watch, port, lambda *a, **kw: original(*a, **{**kw, 'ledger': ledger, 'store': store, 'now': T0}))
    sent = []
    monkeypatch.setattr('holdspeak.delivery.direct_gesture_input.submit_process_input_from_owner_gesture', lambda **kw: sent.append(kw) or {})
    service = AgentHandService(hub.db, launch_service=lambda: None)
    registry = operations.bind_available({'agent_hand_service': service})
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    return SimpleNamespace(db=hub.db, service=service, store=store, content=content, sent=sent,
                           since=watch.screen_wire(store.get('launch:l1'), T0)['since'])


def test_high_permission_names_the_command_action_and_lifetime(prompt_rig):
    rig = prompt_rig
    call = held('agent.launch.answer', {'launch_id': 'l1', 'since': rig.since, 'keys': ['Enter']})
    facts = held_call_details(call, OWNER)['facts']
    assert any(f['label'] == 'Permission' and f['value'] == 'Allow this command once' for f in facts)
    assert any(f['label'] == 'Until' and f['value'] == 'This command only' for f in facts)
    assert any(f['label'].startswith('Prompt') and 'rm -rf build/' in f['value'] and f['redact'] for f in facts)
    perform(rig.db, call)
    assert rig.sent and rig.sent[0]['keys'] == ['Enter']


def test_high_a_changed_command_with_the_same_since_sends_no_key(prompt_rig):
    rig = prompt_rig
    call = held('agent.launch.answer', {'launch_id': 'l1', 'since': rig.since, 'keys': ['Enter']})
    held_call_details(call, OWNER)
    screen, title = rig.content['screen']
    rig.content['screen'] = (screen.replace('rm -rf build/', 'rm -rf private/'), title)
    with pytest.raises(ServiceError) as stale:
        rig.service.launch_answer(OWNER, **call.args)
    assert stale.value.code == 'answer_stale'
    assert rig.sent == []


def test_high_commit_facts_keep_the_subject_and_count_the_body(fact_rig):
    rig = fact_rig
    call = held('repository.commit', {'repository_id': rig.source_b.source_id,
        'message': 'Fix the build\n\nPrivate incident details\n'+ PRIVATE})
    before = held_call_details(call, OWNER)
    wire = json.dumps(before)
    assert {'label': 'Subject', 'value': 'Fix the build'} in before['facts']
    assert {'label': 'Body', 'value': '4 words'} in before['facts']
    assert PRIVATE not in wire and 'Private incident details' not in wire
    call.args['message'] = call.args['message'].replace('Private incident', 'Other incident')
    assert held_call_details(call, OWNER)['binding'] != before['binding']


def test_medium_no_configured_egress_is_frozen_and_a_new_host_refuses(fact_rig, monkeypatch):
    from holdspeak.intel import cli_engine
    host = {'value': ''}
    monkeypatch.setattr(cli_engine, 'pi_config_host', lambda _: host['value'])
    args = {'draft': {'request_id': 'egress', 'profile_id': 'engine', 'expected_profile_revision': 0,
                      'preset': 'pi', 'model': 'team/model'}}
    call = held('model_library.connect_cli_engine', args)
    details = held_call_details(call, OWNER)
    assert any(f['label'] == 'Egress' and f['value'] == 'none' for f in details['facts'])
    assert 'egress_binding' in call.args['draft']
    host['value'] = 'new-host.example.test'
    with pytest.raises(ServiceError) as stale:
        fact_rig.library.connect_cli_engine(OWNER, call.args['draft'])
    assert stale.value.code == 'answer_stale'

from tests.unit.test_agent_hand import db  # noqa: F401,E402


@pytest.fixture
def authority_rig(tmp_path, db, monkeypatch):
    from tests.unit.test_agent_hand import _rig
    from tests.unit.test_agent_hand_preview import _reads
    from holdspeak.mcp.families import agent
    rig = _rig(tmp_path, db, monkeypatch, agent='codex')
    mode = {'value': 'safe'}
    rig.hand._control_mode = lambda: mode['value']
    rig.service._control_mode = lambda: mode['value']
    rig.hand.bind_reads(_reads(rig))
    monkeypatch.setattr(agent, '_hand_service', lambda: rig.hand)
    registry = operations.bind_available({'agent_hand_service': rig.hand})
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    yield rig, mode
    rig.service.first_message.close()


def test_high_hand_shows_its_effective_authority_and_the_actual_spawn_agrees(authority_rig):
    rig, mode = authority_rig
    call = held('agent.hand', {'kind': 'action', 'id': 'ai_1', 'profile': 'codex-default'})
    facts = held_call_details(call, OWNER)['facts']
    for label, value in [('Control', 'Secure'), ('Network', 'No'), ('For', 'Codex CLI')]:
        assert any(f['label'] == label and f['value'] == value for f in facts)
    assert any(f['label'] == 'Folder' and f['value'] == str(rig.worktree) for f in facts)
    result = perform(rig.db, call)
    assert result['control_mode'] == 'safe'
    assert any(argv[:2] == ['tmux', 'new-session'] for argv in rig.tmux.calls)


def test_high_hand_control_changed_before_launch_refuses_without_a_process(authority_rig):
    from holdspeak.services.thread_tools import ThreadToolExecutor
    rig, mode = authority_rig
    call = held('agent.hand', {'kind': 'action', 'id': 'ai_1', 'profile': 'codex-default'})
    before = held_call_details(call, OWNER)
    mode['value'] = 'yolo'
    executor = ThreadToolExecutor(rig.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: 'safe')
    executor.decide(call, 'approve')
    result = executor.execute(call)
    assert result.payload['code'] == 'answer_stale', result.payload
    assert not any(argv[:2] == ['tmux', 'new-session'] for argv in rig.tmux.calls)


def test_pending_authority_read_changes_the_binding_when_control_changes(authority_rig):
    rig, mode = authority_rig
    call = held('agent.hand', {'kind': 'action', 'id': 'ai_1', 'profile': 'codex-default'})
    before = held_call_details(call, OWNER)
    mode['value'] = 'yolo'
    after = held_call_details(call, OWNER)
    assert after['binding'] != before['binding']
    assert any(f['label'] == 'Control' and f['value'] == 'YOLO' for f in after['facts'])


def authority_tools():
    """The declaration supplies the domain; later authority tools join this proof."""
    return [t for t in tools.TOOLS if t['inputSchema'].get('x-held-authority')]


def _bind(monkeypatch, **services):
    registry = operations.bind_available(services)
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    return registry


def _case(request, tool, monkeypatch, tmp_path):
    """Real owning resolvers/writers; only terminal and provider effects are rigged."""
    name, domain = tool['name'], tool['inputSchema']['x-held-authority']
    if domain in ('launch', 'helper'):
        rig, mode = request.getfixturevalue('authority_rig')
        args = {'kind': 'action', 'id': 'ai_1', 'profile': 'codex-default'}
        caller = OWNER
        if name != 'agent.hand':
            result = rig.hand.hand(OWNER, 'action', 'ai_1', profile='codex-default')
            launch_id = result['launch_id']
            rig.service.first_message.close()
            args = {'launch_id': launch_id}
            if name == 'agent.launch.resume':
                from holdspeak.services.agent_flights import STOPPED_BY_RESTART
                rig.launches.update(launch_id, state=STOPPED_BY_RESTART, session_key='codex:smoke-session')
            elif name == 'agent.start_helper':
                caller = Principal(PrincipalKind.AGENT, 'agent:launch:' + launch_id)
                args = {'instruction': 'Check the change', 'profile': 'codex-default'}
            elif name == 'agent.helper.allow':
                from holdspeak.services import agent_helpers
                pending = agent_helpers.start_helper(launch_id, instruction='Check the change', profile='codex-default',
                    hand_service=rig.hand, control_mode=lambda: 'safe', ledger=rig.launches)
                args['request_id'] = pending['owner_action']['request_id']
        call = held(name, args)
        call.principal = caller
        # Both MCP paths use the same runtime-composed service.
        monkeypatch.setattr('holdspeak.runtime.composition.service', lambda key, fallback: rig.hand if key == 'agent_hand_service' else fallback())
        return rig.db, call, lambda: mode.update(value='yolo')
    if domain == 'prompt':
        if name == 'agent.launch.answer':
            rig = request.getfixturevalue('prompt_rig')
            call = held(name, {'launch_id': 'l1', 'since': rig.since, 'keys': ['Enter']})
            def mutate():
                screen, title = rig.content['screen']
                rig.content['screen'] = (screen.replace('rm -rf build/', 'rm -rf private/'), title)
            return rig.db, call, mutate
        from holdspeak.agent_context import own_agents
        from holdspeak.agent_context.screen_watch import ScreenStore
        from holdspeak.services.coder_service import CoderService
        from tests.unit.test_own_agents import TmuxRig, PERMISSION
        from datetime import datetime, timezone
        hub = request.getfixturevalue('hub')
        tmux, store, now = TmuxRig(), ScreenStore(), datetime(2026, 10, 19, tzinfo=timezone.utc)
        tmux.screen = PERMISSION
        monkeypatch.setenv('HOLDSPEAK_OWN_AGENTS', 'on')
        original = own_agents._answer_prompt
        monkeypatch.setattr(own_agents, '_answer_prompt', lambda *a, **kw: original(*a, **{**kw, 'records': [], 'runner': tmux, 'store': store, 'now': now}))
        first = own_agents.list_own_agents(records=[], runner=tmux, store=store, now=now)[0]
        _bind(monkeypatch, coder_service=CoderService(hub.db))
        call = held(name, {'pane_id': '%1', 'since': first['screen']['since'], 'keys': ['Enter']})
        # Own-agent since already contains a content hash; change the selected
        # authority binding without changing that supported public read token.
        def mutate():
            tmux.screen = PERMISSION.replace('rm -rf build/', 'rm -rf private/')
            monkeypatch.setattr(own_agents, '_prompt_token', lambda *a: first['screen']['since'])
        return hub.db, call, mutate
    if domain in ('program', 'automation'):
        from tests.integration.program_rig import Rig, FAKE_CHECK
        from holdspeak.services.workbench_service import WorkbenchService
        from holdspeak.services import program_service
        rig = Rig(tmp_path)
        programs = rig.service
        if domain == 'program':
            pid = programs.create(OWNER, title='Planned job', repository=str(rig.repo), control='secure', check_command=f'sh {FAKE_CHECK}')['id']
            programs.plan(OWNER, pid, steps=[{'title': 'Change the file', 'brief': 'Do it.'}])
            if name == 'program.resume':
                programs.store.save_program({**programs.store.get_program(pid), 'state': 'parked'})
            _bind(monkeypatch, program_service=programs)
            call = held(name, {'program_id': pid})
            def mutate():
                programs.store.save_program({**programs.store.get_program(pid), 'control': 'yolo'})
        else:
            work = WorkbenchService(rig.db)
            monkeypatch.setattr(program_service, 'default_program_service', lambda *a, **kw: programs)
            made = work.create_workbench(OWNER, name='Planned automation', do_kind='run_program',
                program_control='secure', program_template='fast-cycle', work_folder=str(rig.repo))
            wid = made['id']
            _bind(monkeypatch, workbench_service=work)
            monkeypatch.setattr(tools, "runtime_service", lambda key, fallback: work if key == "workbench_service" else fallback())
            call = held(name, {'workbench_id': wid})
            def mutate():
                work.update_workbench(OWNER, wid, program_control='yolo')
        return rig.db, call, mutate
    if domain in ('steering', 'steering-revoke'):
        from holdspeak import coder_steering, agent_context
        from holdspeak.config import Config
        from holdspeak.services.coder_service import CoderService
        from tests.unit.test_web_routes_coders_steer import _session
        hub = request.getfixturevalue('hub')
        coder_steering.clear_grants()
        request.addfinalizer(coder_steering.clear_grants)
        monkeypatch.setattr(agent_context, 'list_agent_sessions', lambda **kw: [_session()])
        pane = {'value': '%3'}
        monkeypatch.setattr(coder_steering, 'resolve_pane_identity', lambda *a, **kw: {'status': 'ok', 'pane_id': pane['value']})
        monkeypatch.setattr(Config, 'load', classmethod(lambda cls: SimpleNamespace(control_mode='safe')))
        service = CoderService(hub.db)
        _bind(monkeypatch, coder_service=service)
        if domain == 'steering-revoke':
            coder_steering.arm('claude:abc', '%3')
        call = held(name, {'key': 'claude:abc'})
        def mutate():
            pane['value'] = '%8'
            if domain == 'steering-revoke':
                coder_steering.arm('claude:abc', '%8')
        return hub.db, call, mutate
    if domain in ('revoke', 'self-revoke'):
        from holdspeak.services.gate_service import GateService
        hub = request.getfixturevalue('hub')
        credential = agent_credentials.issue('Build agent')
        _bind(monkeypatch, gate_service=GateService(hub.db))
        call = held(name, {'agent_identity': 'Build agent'} if domain == 'revoke' else {})
        if domain == 'self-revoke':
            call.principal = credential.principal
        return hub.db, call, lambda: agent_credentials.issue('Build agent')
    if domain in ('gate', 'kernel'):
        from holdspeak.services.gate_service import GateService
        from holdspeak.gate_operations import LIVE_KERNEL_SERVICE
        from holdspeak.kernel.runtime import _configure
        from holdspeak.coder_gate import redact_args
        hub = request.getfixturevalue('hub')
        _configure(hub.db)
        gate = GateService(hub.db)
        agent = Principal(PrincipalKind.AGENT, 'Build agent')
        sha, head = redact_args({'command': 'rm -rf build/'})
        proposal = gate.propose(agent, {'id': 'review-command', 'tool': 'Bash', 'args_sha256': sha,
            'args_head': head, 'cwd': '/work', 'ttl_seconds': 300})
        assert proposal['state'] == 'held'
        _bind(monkeypatch, gate_service=gate, kernel_service=LIVE_KERNEL_SERVICE)
        if domain == 'gate':
            call = held(name, {'proposal_id': proposal['id'], 'decision': 'approved'})
        else:
            oid = proposal['operation']['kernel_operation_id']
            operation = LIVE_KERNEL_SERVICE.read(OWNER, ['operation:' + oid])['objects'][0]['operation']
            call = held(name, {'operation_id': oid, 'decision': 'approve', 'expected_revision': operation['revision']})
        def mutate():
            gate.decide(OWNER, proposal['id'], {'decision': 'denied'})
        return hub.db, call, mutate
    if domain == 'egress':
        from holdspeak.intel import cli_engine
        rig = request.getfixturevalue('fact_rig')
        host = {'value': ''}
        monkeypatch.setattr(cli_engine, 'pi_config_host', lambda _: host['value'])
        call = held(name, {'draft': {'request_id': 'authority-egress', 'profile_id': 'engine', 'expected_profile_revision': 0,
                                     'preset': 'pi', 'model': 'team/model'}})
        return rig.db, call, lambda: host.update(value='changed.example.test')
    pytest.fail('Add a real authority-change rig for ' + name)


@pytest.mark.parametrize('tool', authority_tools(), ids=lambda t: t['name'])
def test_every_declared_authority_refuses_a_changed_control_screen_or_grant(request, tool, monkeypatch, tmp_path):
    from holdspeak.services.thread_tools import ThreadToolExecutor
    db, call, mutate = _case(request, tool, monkeypatch, tmp_path)
    details = held_call_details(call, OWNER)
    assert details['facts'] and all(len(f['value']) <= 160 for f in details['facts'])
    domain = tool['inputSchema']['x-held-authority']
    labels = ({'Permission', 'Agent', 'Until', 'Prompt'} if domain == 'prompt' else {'Egress'} if domain == 'egress'
              else {'Control', 'Network', 'Folder', 'For', 'Until'} if domain in ('launch', 'helper', 'program', 'automation')
              else {'Allowed', 'For', 'Scope', 'Until'})
    assert labels <= {re.sub(r' \d+$', '', f['label']) for f in details['facts']}, details
    executor = ThreadToolExecutor(db, principal=call.principal, dispatch_fn=tools.dispatch, control_mode_fn=lambda: 'safe')
    executor.decide(call, 'approve')
    mutate()
    result = executor.execute(call)
    assert result.kind == 'tool_execution_failed', result.payload
    assert result.payload['code'] == 'answer_stale', result.payload


def test_only_the_callers_own_launch_prompt_is_in_its_copy(prompt_rig):
    rig = prompt_rig
    own = agent_credentials.issue('agent:launch:l1', launch_id='l1').principal
    call = held('agent.launch.answer', {'launch_id': 'l1', 'since': rig.since, 'keys': ['Enter']})
    call.principal = own
    owner = held_call_details(call, OWNER)
    caller = held_call_details(call, own)
    assert owner['binding'] == caller['binding']
    assert 'rm -rf build/' in json.dumps(caller['facts'])
    stranger = agent_credentials.issue('Other caller').principal
    call.principal = stranger
    owner = held_call_details(call, OWNER)
    caller = held_call_details(call, stranger)
    assert owner['binding'] == caller['binding']
    assert 'rm -rf build/' not in json.dumps(caller['facts'])
    assert any(f['label'] == 'Prompt' and f['value'] == 'hidden (secret)' for f in caller['facts'])


@pytest.mark.parametrize('choice,action,lifetime', [
    ('1. Yes', 'Allow this command once', 'This command only'),
    ('1. Yes, allow this command for this session', 'Allow this command rule for the session', 'Until this agent session ends'),
    ('1. No', 'Deny this command', 'No permission'),
])
def test_the_visible_selected_choice_supplies_the_action_and_lifetime(prompt_rig, choice, action, lifetime):
    rig = prompt_rig
    screen, title = rig.content['screen']
    rig.content['screen'] = (screen.replace('1. Yes', choice), title)
    call = held('agent.launch.answer', {'launch_id': 'l1', 'since': rig.since, 'keys': ['Enter']})
    facts = held_call_details(call, OWNER)['facts']
    assert {'label': 'Permission', 'value': action} in facts
    assert {'label': 'Until', 'value': lifetime} in facts


def test_every_word_of_a_long_prompt_stays_readable_in_short_redacted_facts(prompt_rig):
    rig = prompt_rig
    screen, title = rig.content['screen']
    command = 'printf ' + 'read_this_argument_' * 25 + ' END_OF_VALUE'
    rig.content['screen'] = (screen.replace('rm -rf build/ && make release', command), title)
    call = held('agent.launch.answer', {'launch_id': 'l1', 'since': rig.since, 'keys': ['Escape']})
    facts = held_call_details(call, OWNER)['facts']
    parts = [f for f in facts if f['label'].startswith('Prompt') and f.get('redact')]
    assert ''.join(f['value'] for f in parts) == command + '\nClean the build and release'
    assert all(f['redact'] and len(f['value']) <= 160 for f in parts)


def test_a_queued_hand_keeps_the_permission_digest_until_it_reaches_the_factory(authority_rig, tmp_path):
    from holdspeak.services.agent_hand_queue import HandQueue, start_queued
    rig, mode = authority_rig
    call = held('agent.hand', {'kind': 'action', 'id': 'ai_1', 'profile': 'codex-default'})
    held_call_details(call, OWNER)
    queue = HandQueue(tmp_path / 'queued.json')
    queued = queue.add('action', 'ai_1', profile=call.args['profile'], project_id=call.args['project_id'],
                       expected_authority=call.args['expected_authority'])
    assert isinstance(queue.list()[0]['expected_authority'], str)
    mode['value'] = 'yolo'
    result = start_queued(rig.hand, queue=queue)
    assert result[0]['code'] == 'answer_stale'
    assert queue.outcome(queued['queue_id'])['outcome'] == 'failed'
    assert not any(argv[:2] == ['tmux', 'new-session'] for argv in rig.tmux.calls)


def test_a_bound_brief_is_checked_again_before_arming_or_typing(authority_rig):
    rig, mode = authority_rig
    result = rig.hand.hand(OWNER, 'action', 'ai_1', profile='codex-default')
    rig.service.first_message.close()
    launch_id = result['launch_id']
    call = held('agent.launch.deliver', {'launch_id': launch_id})
    held_call_details(call, OWNER)
    from holdspeak.services.held_authority import digest
    record = rig.launches.get(launch_id)
    record['delivery_authority'] = digest(call.args['expected_authority'])
    typed_before, keys_before = list(rig.typed), list(rig.keys_sent)
    mode['value'] = 'yolo'
    with pytest.raises(ServiceError) as stale:
        rig.service._send_instruction(record, 'Start now', OWNER, {}, record['operation_id'])
    assert stale.value.code == 'answer_stale'
    assert rig.typed == typed_before and rig.keys_sent == keys_before


def test_a_program_keeps_its_authority_until_a_later_step_starts(authority_rig):
    from holdspeak.services.program_service import ProgramService
    from tests.integration.program_rig import FAKE_CHECK
    rig, _ = authority_rig
    programs = ProgramService(rig.db, kernel=lambda **kw: None, runner=lambda: None)
    pid = programs.create(OWNER, title='Later work', repository=str(rig.repo), control='secure', check_command=f'sh {FAKE_CHECK}')['id']
    step = programs.plan(OWNER, pid, steps=[{'title': 'Later step'}])['steps'][0]
    programs.bind_run_authority(programs.store.get_program(pid))
    request = {'origin_ref': {'kind': 'program_step', 'id': step['id']}}
    rig.service.check_program_authority(request)
    changed = programs.store.get_program(pid)
    changed['control'] = 'yolo'
    programs.store.save_program(changed)
    with pytest.raises(ServiceError) as stale:
        rig.service.check_program_authority(request)
    assert stale.value.code == 'answer_stale'



def test_prompt_credentials_are_masked_but_a_secret_change_still_stales_the_answer(prompt_rig):
    from tests.unit.test_own_agents import SECRET
    rig = prompt_rig
    screen, title = rig.content['screen']
    rig.content['screen'] = (screen.replace('rm -rf build/', 'curl -H "Authorization: Bearer ' + SECRET + '" https://example.test'), title)
    call = held('agent.launch.answer', {'launch_id': 'l1', 'since': rig.since, 'keys': ['Enter']})
    before = held_call_details(call, OWNER)
    assert SECRET not in json.dumps(before)
    assert '[redacted]' in json.dumps(before)
    rig.content['screen'] = (rig.content['screen'][0].replace(SECRET, SECRET + 'changed'), title)
    with pytest.raises(ServiceError) as stale:
        rig.service.launch_answer(OWNER, **call.args)
    assert stale.value.code == 'answer_stale'
    assert rig.sent == []


def test_authority_snapshots_are_not_a_second_projection_through_pipeline_events():
    from holdspeak.services.observer import WITHHELD, _summarize_result, _summarize_args
    from holdspeak.services.coder_service import CoderService
    snapshot = {'expected_authority': {'prompt': PRIVATE, 'material': {'body': PRIVATE}}}
    for payload in (snapshot, {'payload': [snapshot]}):
        result = _summarize_result('AnyService', 'write', payload)
        assert PRIVATE not in result and WITHHELD in result
    # Owner authority reads also withhold reflected argument roots and scalars.
    result = _summarize_result('CoderService', 'resolve_own_answer_authority', {'text': PRIVATE})
    assert PRIVATE not in result and WITHHELD in result
    args = _summarize_args(CoderService.resolve_own_answer_authority,
        (object(), OWNER, {'text': PRIVATE}), {})
    assert PRIVATE not in args and WITHHELD in args


def test_orphaned_grant_names_never_fall_back_to_an_opaque_project_id(hub, monkeypatch):
    from holdspeak.services.gate_service import GateService
    from holdspeak.services import project_delegation
    opaque = 'missing-project-opaque-id'
    monkeypatch.setattr(project_delegation, 'views', lambda *a, **kw: {'by_identity': {'Build agent': [
        {'project_id': opaque, 'project_name': opaque, 'state': 'LIVE'}]}})
    service = GateService(hub.db)
    _bind(monkeypatch, gate_service=service)
    call = held('principals.agent.revoke', {'agent_identity': 'Build agent'})
    details = held_call_details(call, OWNER)
    assert opaque not in json.dumps(details)
    assert 'hidden (secret)' in json.dumps(details)


@pytest.mark.parametrize('bound', [True, False])
def test_a_kernel_spawn_answer_uses_the_admitted_launch_authority(authority_rig, monkeypatch, bound):
    from holdspeak import coder_gate
    from holdspeak.gate_operations import LIVE_KERNEL_SERVICE
    from holdspeak.kernel import runtime
    from holdspeak.services.held_authority import digest
    rig, mode = authority_rig
    request = {'agent_profile_id': 'codex-default', 'source_id': rig.source.source_id,
        'worktree': {'mode': 'new', 'name': 'hs-action-ai_1', 'branch': 'hs/fix-login'},
        'story_ref': {'project': 'desk', 'story_id': 'action-ai_1'}}
    if bound:
        request['authority_commitment'] = digest(rig.service.authority_for(request))
    coder_gate.save_gate_config(coder_gate.GateConfig(armed=True, repos={str(rig.worktree): ["Bash"]}), rig.gate_path)
    admitted = rig.broker.submit({'request_schema': 1, 'request_id': 'review-kernel-spawn',
        'idempotency_key': 'review-kernel-spawn', 'operation': {'name': 'process.spawn', 'version': 1},
        'subject_refs': [], 'target': {'ref': 'launch:launch_review'},
        'arguments': {'launch_id': 'launch_review', **request}, 'placement': 'node:local'}, OWNER)
    assert admitted['state'] == 'awaiting_decision', json.dumps(admitted)
    monkeypatch.setattr(runtime, '_service', lambda: rig.broker)
    monkeypatch.setattr('holdspeak.runtime.composition.service', lambda key, fallback:
        SimpleNamespace(default_launch_service=lambda: rig.service) if key == 'delivery_service' else fallback())
    _bind(monkeypatch, kernel_service=LIVE_KERNEL_SERVICE)
    call = held('kernel.decide', {'operation_id': admitted['operation_id'], 'decision': 'approve',
                                  'expected_revision': admitted['revision']})
    if not bound:
        with pytest.raises(ServiceError) as unreadable:
            held_call_details(call, OWNER)
        assert unreadable.value.code == 'authority_unavailable'
    else:
        details = held_call_details(call, OWNER)
        assert any(f['label'] == 'Control' and f['value'] == 'Secure' for f in details['facts'])
        mode['value'] = 'yolo'
        with pytest.raises(ServiceError) as stale:
            tools.dispatch('kernel.decide', call.args, OWNER)
        assert stale.value.code == 'answer_stale'
    assert rig.broker.read(['operation:' + admitted['operation_id']], 'state', 'committed', OWNER)['objects'][0]['operation']['state'] == 'awaiting_decision'
    assert not any(argv[:2] == ['tmux', 'new-session'] for argv in rig.tmux.calls)
