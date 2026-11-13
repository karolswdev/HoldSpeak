"""Whole-family facts, actual default operands and private write data."""
from __future__ import annotations

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from holdspeak import operations
from holdspeak.held_arguments import NOT_YET_DESCRIBED, resolve_target, strongest_effect
from holdspeak.mcp import tools
from holdspeak.principals import Principal, PrincipalKind, agent_credentials
from holdspeak.services.errors import ServiceError
from holdspeak.services.held_tool_details import _facts, held_call_details
from holdspeak.services.thread_tools import ThreadToolExecutor
from tests.integration.test_held_tool_facts_round3 import OWNER, PRIVATE, held, perform
from tests.unit.test_desk_ask_ai import hub  # noqa: F401

FAMILIES = ('desk.', 'desk_window.', 'workbench.', 'calls.', 'settings.', 'inference.', 'model_library.',
            'recordings.', 'scheduled_recording.', 'memory.', 'repository.', 'provider.', 'agent.')


def family_tools():
    return [t for t in tools.TOOLS if t['name'].startswith(FAMILIES) and strongest_effect(t) == 'write']


@pytest.mark.parametrize('tool', family_tools(), ids=lambda t: t['name'])
def test_every_write_in_the_completed_families_declares_facts(tool):
    schema = tool['inputSchema']
    assert 'x-held-arguments' in schema, tool['name']
    assert tool['name'] not in NOT_YET_DESCRIBED
    fields = {schema['x-held-delegate']['arguments']} if schema.get('x-held-delegate') else set()
    for row in schema['x-held-arguments']:
        assert row['label']
        fields.update(key.split('.')[0] for key in ([row['key']] if isinstance(row['key'], str) else row['key']))
    assert fields == set(schema.get('properties', {}))


def put(args, path, value):
    seat = args
    keys = path.split('.')
    for key in keys[:-1]:
        seat = seat.setdefault(key, {})
    seat[keys[-1]] = value


@pytest.mark.parametrize('tool', family_tools(), ids=lambda t: t['name'])
def test_every_family_fact_hides_private_kinds_and_shortens_values(tool):
    schema, args = tool['inputSchema'], {}
    assert 'x-held-arguments' in schema
    for row in schema['x-held-arguments']:
        for path in ([row['key']] if isinstance(row['key'], str) else row['key']):
            put(args, path, (PRIVATE if row['kind'] != 'text' else 'Matching') + ' word' * 400)
    facts = _facts(schema, args, OWNER)
    assert PRIVATE not in json.dumps(facts)
    assert all(len(f['value']) <= 160 for f in facts)
    private = {**schema, 'x-held-arguments': [*schema['x-held-arguments'],
        {'key': 'private', 'label': 'Private', 'kind': 'credential'},
        {'key': 'private.title', 'label': 'Child', 'kind': 'text'}]}
    assert not any(f['label'] == 'Child' for f in _facts(private, {'private': {'title': PRIVATE}}, OWNER))


def example(prop, key=''):
    if prop.get('enum'):
        return next(v for v in prop['enum'] if v is not None)
    kind = prop.get('type')
    if isinstance(kind, list):
        kind = next(t for t in kind if t != 'null')
    if kind == 'object':
        return {k: example(v, k) for k, v in prop.get('properties', {}).items() if k in prop.get('required', [])}
    if kind == 'array':
        return [example(prop.get('items', {}))]
    if kind in {'integer', 'number'}:
        return prop.get('minimum', 1)
    if kind == 'boolean':
        return False
    if key == 'profile_id':
        return 'sample-model'
    if key == 'endpoint':
        return 'http://127.0.0.1:9000/v1'
    if key == 'model':
        return 'sample-model'
    return 'Matching B'


@pytest.fixture
def fact_rig(hub, tmp_path, monkeypatch):
    from holdspeak.delivery import DeliveryRegistry
    from holdspeak.services.repository_drawer_service import RepositoryDrawerService
    from holdspeak.services.workbench_service import WorkbenchService
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService
    from holdspeak.services.agent_hand_service import AgentHandService
    from holdspeak.services.scheduled_recording_service import ScheduledRecordingService
    from holdspeak.services.provider_service import ProviderService
    from holdspeak.services.jira_provider import JiraProviderAdapter
    from holdspeak.services.confluence_provider import ConfluenceProviderAdapter
    from holdspeak.calls import service as call_module
    from holdspeak.mcp.families import model_library, agent
    from tests.integration.program_rig import make_repo
    from tests.unit.test_repository_routes import _git
    repo_a, repo_b = make_repo(tmp_path / 'repo-a'), make_repo(tmp_path / 'repo-b')
    registry = DeliveryRegistry(tmp_path / 'registry.json', map_path=tmp_path / 'absent-map')
    source_a, _ = registry.register(str(repo_a), label='Matching repository A')
    source_b, _ = registry.register(str(repo_b), label='Matching repository B')
    (repo_b / 'held.txt').write_text(PRIVATE)
    _git(repo_b, 'add', 'held.txt')
    repo = RepositoryDrawerService(hub.db, registry=registry)
    work = WorkbenchService(hub.db)
    a, b = [work.create_workbench(OWNER, name='Matching automation ' + suffix) for suffix in ('A', 'B')]
    items = [work.add_item(OWNER, row['id'], title='Matching item ' + suffix) for row, suffix in ((a, 'A'), (b, 'B'))]
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
    from holdspeak.config import Config
    setup = InferenceSetupApplicationService(hub.db, config_provider=Config, home_provider=lambda: tmp_path / 'home')
    acquisition = InferenceAcquisitionApplicationService(hub.db, setup_service=setup, model_root=tmp_path / 'custody', home_provider=lambda: tmp_path / 'home')
    library = ModelLibraryApplicationService(hub.db, setup_service=setup, acquisition_service=acquisition)
    hand = AgentHandService(hub.db, launch_service=lambda: None)
    calls = call_module.CallsService()
    monkeypatch.setattr(call_module, '_settings', lambda: SimpleNamespace(allowed_numbers=['+441234567890']))
    monkeypatch.setattr(model_library, '_service', lambda: library)
    monkeypatch.setattr(agent, '_hand_service', lambda: hand)
    monkeypatch.setenv('HOLDSPEAK_CLI_ENGINES', 'on')  # parser only; no CLI is ever started by this fixture
    jira, confluence = JiraProviderAdapter(hub.db), ConfluenceProviderAdapter(hub.db)
    for adapter in (jira, confluence):
        for suffix in ('a', 'b'):
            adapter.add_connection(OWNER, 'team-' + suffix, f'{suffix}@example.test')
    providers = ProviderService(lambda name: {'jira': jira, 'confluence': confluence}.get(name))
    services = {'repository_drawer_service': repo, 'workbench_service': work, 'primitive_service': PrimitiveService(hub.db),
        'model_library_service': library, 'agent_hand_service': hand, 'calls_service': calls,
        'provider_service': providers, 'scheduled_recording_service': ScheduledRecordingService(hub.db)}
    bound = operations.bind_available(services)
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: bound)
    original = tools.runtime_service
    monkeypatch.setattr(tools, 'runtime_service', lambda name, fallback: services.get(name) if name in services else original(name, fallback))
    return SimpleNamespace(db=hub.db, repo=repo, registry=registry, repo_a=repo_a, repo_b=repo_b,
        source_a=source_a, source_b=source_b, work=work, a=a, b=b, items=items, library=library, hand=hand,
        calls=calls, jira=jira, confluence=confluence, bound=bound, services=services)


def valid_arguments(tool, rig):
    schema, name = tool['inputSchema'], tool['name']
    args = {k: example(v, k) for k, v in schema.get('properties', {}).items() if k in schema.get('required', [])}
    if name.startswith('repository.'):
        args.update(repository_id=rig.source_b.source_id)
        if name == 'repository.register':
            args = {'source_id': rig.source_b.source_id}
        elif name == 'repository.write_file':
            args.update(path='output.txt', content=PRIVATE + ' €')
        elif name == 'repository.stage':
            args['paths'] = ['held.txt']
        elif name == 'repository.commit':
            args['message'] = ' Record the result '
        elif name == 'repository.checkout':
            args['branch'] = 'main'
    if name.startswith('workbench.'):
        args['workbench_id'] = rig.b['id']
        if 'item_id' in args:
            args['item_id'] = rig.items[1]['id']
    if name.startswith('provider.') and 'site' in args:
        args.update(site='team-b', email='b@example.test')
    if 'connection_ref' in args:
        args['connection_ref'] = 'team-b.atlassian.net|b@example.test'
    if name == 'desk.verb':
        args = {'verb_id': 'desk.create', 'arguments': {'kind': 'notes', 'data': {'title': 'Matching note', 'body_markdown': PRIVATE}}}
    if name == 'scheduled_recording.create':
        args['cron_expr'] = '0 9 * * *'
    if name == 'agent.hand':
        args.update(kind='note', id='missing-note')
    return args


def optional_paths(schema, prefix=''):
    paths = []
    for key, prop in schema.get('properties', {}).items():
        path = prefix + key
        if key not in schema.get('required', []):
            paths.append(path)
        paths.extend(optional_paths(prop, path + '.'))
    return paths


@pytest.mark.parametrize('tool', [t for t in family_tools() if optional_paths(t['inputSchema'])], ids=lambda t: t['name'])
def test_optional_family_arguments_use_the_dispatchers_effective_payload(fact_rig, tool, monkeypatch):
    """Actual canonical preparation, then the real dispatcher with its effect port captured."""
    schema, name = tool['inputSchema'], tool['name']
    base = valid_arguments(tool, fact_rig)
    for key in optional_paths(schema):
        for value in (None, '', ' \t\n '):
            args = deepcopy(base)
            if value is None:
                seat = args
                for part in key.split('.')[:-1]:
                    seat = seat.setdefault(part, {})
                seat.pop(key.split('.')[-1], None)
            else:
                put(args, key, value)
            call = held(name, args)
            try:
                shown = held_call_details(call, OWNER)
            except (ServiceError, ValueError, TypeError, tools.ToolError) as error:
                with pytest.raises(type(error)):
                    resolve_target(schema, args, OWNER, caller=OWNER)
                continue
            captured = []
            def effect_port(_name, payload, principal):
                captured.append(resolve_target(schema, payload, principal, caller=principal))
                return {'captured': True}
            with monkeypatch.context() as context:
                context.setattr(tools, 'FAMILIES', [SimpleNamespace(TOOLS=[tool], dispatch=effect_port)])
                executor = ThreadToolExecutor(fact_rig.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: 'safe')
                executor.decide(call, 'approve')
                result = executor.execute(call)
            assert result.kind != 'tool_execution_failed', (name, key, value, result.payload)
            assert len(captured) == 1
            assert captured[0] == call.execution_args, (name, key, value)
            assert shown['facts'] == _facts(schema, captured[0], OWNER), (name, key, value)


def test_desk_alias_uses_the_canonical_declaration_and_real_write(fact_rig):
    rig = fact_rig
    call = held('desk.verb', {'verb_id': 'desk.create', 'arguments': {'kind': 'notes', 'data': {'title': 'Platform plan', 'body_markdown': PRIVATE}}})
    details = held_call_details(call, OWNER)
    assert {'label': 'Title', 'value': 'Platform plan'} in details['facts']
    assert {'label': 'Text', 'value': '1 words'} in details['facts']
    assert PRIVATE not in json.dumps(details)
    result = perform(rig.db, call)
    assert rig.db.notes.get(result['id']).body_markdown == PRIVATE
    name, args = tools.held_desk_verb({'verb_id': 'workbench.run', 'arguments': {'workbench_id': rig.b['id']}})
    assert name == 'automation.run'
    schema = tools._tool_schema(name)
    assert 'x-held-arguments' in schema
    assert {'label': 'Automation', 'value': 'Matching automation B'} in _facts(schema, args, OWNER)


def test_a_hidden_delegate_parent_stays_hidden(fact_rig):
    schema = tools._tool_schema('desk.verb')
    private = {**schema, 'x-held-arguments': [*schema['x-held-arguments'], {'key': 'arguments', 'label': 'Inputs', 'kind': 'credential'}]}
    facts = _facts(private, {'verb_id': 'desk.create', 'arguments': {'kind': 'notes', 'data': {'title': PRIVATE}}}, OWNER)
    assert PRIVATE not in json.dumps(facts)
    assert {'label': 'Inputs', 'value': 'hidden (credential)'} in facts


def test_repository_file_facts_show_size_and_path_never_content(fact_rig):
    rig = fact_rig
    args = {'repository_id': rig.source_b.source_id, 'path': 'output.txt', 'content': PRIVATE + ' €'}
    call = held('repository.write_file', args)
    details = held_call_details(call, OWNER)
    assert {'label': 'Repository', 'value': 'Matching repository B'} in details['facts']
    assert {'label': 'Path', 'value': 'output.txt'} in details['facts']
    assert {'label': 'Kind', 'value': 'Text file'} in details['facts']
    assert {'label': 'Size', 'value': f"{len(args['content'].encode())} bytes"} in details['facts']
    assert PRIVATE not in json.dumps(details)
    perform(rig.db, call)
    assert (rig.repo_b / 'output.txt').read_text() == args['content']
    assert not (rig.repo_a / 'output.txt').exists()


def test_repository_commit_names_its_message_and_exact_staged_count(fact_rig):
    rig = fact_rig
    call = held('repository.commit', {'repository_id': rig.source_b.source_id, 'message': ' Record the result '})
    facts = held_call_details(call, OWNER)['facts']
    assert {'label': 'Message', 'value': 'Record the result'} in facts
    assert {'label': 'Files', 'value': '1'} in facts
    assert PRIVATE not in json.dumps(facts)
    perform(rig.db, call)
    from tests.unit.test_repository_routes import _git_output
    assert _git_output(rig.repo_b, 'log', '-1', '--format=%s') == 'Record the result'
    assert _git_output(rig.repo_a, 'log', '-1', '--format=%s') != 'Record the result'


def test_a_changed_index_refuses_the_approved_commit(fact_rig):
    rig = fact_rig
    call = held('repository.commit', {'repository_id': rig.source_b.source_id, 'message': 'Record the result'})
    held_call_details(call, OWNER)
    from tests.unit.test_repository_routes import _git
    (rig.repo_b / 'later.txt').write_text('Second file')
    _git(rig.repo_b, 'add', 'later.txt')
    with pytest.raises(ServiceError, match='staged files changed'):
        rig.repo.commit(OWNER, rig.source_b.source_id, message='Record the result', worktree_id=call.args['worktree_id'], expected_index=call.args['expected_index'])


@pytest.mark.parametrize('family', ['jira', 'confluence'])
def test_provider_removal_names_the_selected_host_and_account(fact_rig, family):
    rig = fact_rig
    call = held('provider.' + family + '_remove_connection', {'connection_ref': 'https://team-b.atlassian.net/|B@EXAMPLE.TEST'})
    details = held_call_details(call, OWNER)
    assert {'label': 'Host', 'value': 'team-b.atlassian.net'} in details['facts']
    assert {'label': 'Account', 'value': 'b@example.test'} in details['facts']
    perform(rig.db, call)
    remaining = getattr(rig, family).list_connections(OWNER)
    assert len(remaining) == 1 and 'team-a' in remaining[0]['external_connection_ref']


def test_model_credentials_and_secret_parent_children_never_become_facts(fact_rig):
    from tests.unit.test_model_library_providers import _draft
    args = {'draft': _draft(request_id='private', profile_id='private', provider_family='private_endpoint'), 'secret': {'value': PRIVATE}}
    details = held_call_details(held('model_library.define_endpoint', args), OWNER)
    assert PRIVATE not in json.dumps(details)
    assert {'label': 'Credential', 'value': 'hidden (credential)'} in details['facts']
    assert {'label': 'Endpoint', 'value': 'hidden (credential)'} in details['facts']
    assert {'label': 'Engine', 'value': 'Provider model'} in details['facts']


def test_spend_limit_shows_the_amount_and_null_means_no_limit(fact_rig):
    for amount, words in [(12.34, '12.34'), (None, 'No limit')]:
        details = held_call_details(held('model_library.set_spend_limit', {'request_id': 'limit', 'profile_id': 'sample', 'spend_limit_usd': amount}), OWNER)
        assert {'label': 'US dollars per run', 'value': words} in details['facts']


def test_calls_freeze_and_hide_the_effective_default_number(fact_rig):
    for name in ('calls.place', 'calls.test_line'):
        call = held(name, {'to': ' '})
        wire = held_call_details(call, OWNER)
        assert call.args['to'] == '+441234567890'
        assert '+441234567890' not in json.dumps(wire)
        assert {'label': 'To', 'value': 'hidden (secret)'} in wire['facts']


def test_credential_locators_are_hidden_even_in_refusals(fact_rig):
    secret = 'https://user:PRIVATE_PASSWORD@team.atlassian.net/?token=PRIVATE_TOKEN'
    schema = tools._tool_schema('provider.jira_add_connection')
    wire = json.dumps(_facts(schema, {'site': secret, 'email': 'user:PRIVATE_PASSWORD@example.test'}, OWNER))
    assert 'PRIVATE_PASSWORD' not in wire and 'PRIVATE_TOKEN' not in wire
    from holdspeak.provider_operations import provider_arguments
    with pytest.raises(ServiceError) as refused:
        provider_arguments({'site': secret, 'email': 'owner@example.test'}, provider='jira', verb='add_connection')
    assert 'PRIVATE_PASSWORD' not in str(refused.value) and 'PRIVATE_TOKEN' not in str(refused.value)


def test_schedules_name_the_selected_row_and_update_only_that_row(fact_rig):
    service = fact_rig.services['scheduled_recording_service']
    a, b = [service.create_schedule(OWNER, title='Matching schedule ' + suffix, cron_expr='0 9 * * *') for suffix in ('A', 'B')]
    call = held('scheduled_recording.update', {'schedule_id': b['id'], 'title': 'Changed schedule'})
    assert {'label': 'Schedule', 'value': 'Matching schedule B'} in held_call_details(call, OWNER)['facts']
    perform(fact_rig.db, call)
    rows = {row['id']: row for row in service.list_schedules(OWNER)}
    assert rows[a['id']]['title'] == 'Matching schedule A'
    assert rows[b['id']]['title'] == 'Changed schedule'


def test_event_linked_schedule_describes_the_event_not_ignored_manual_inputs(fact_rig):
    from datetime import datetime, timedelta, timezone
    from holdspeak.db.calendar_events import CalendarEvent
    now = datetime.now(timezone.utc)
    events = [CalendarEvent(id='event-' + suffix, uid=suffix, title='Matching event ' + suffix,
        starts_at=(now + timedelta(hours=1)).isoformat(), ends_at=(now + timedelta(hours=2)).isoformat(),
        last_seen_at=now.timestamp(), subscription_revision='source', location=None, meeting_url=None) for suffix in ('A', 'B')]
    fact_rig.db.calendar_events.replace_projection('source', events, seen_at=now.timestamp(), source_id='calendar', source_label='Work')
    call = held('scheduled_recording.create', {'calendar_event_id': 'event-B', 'title': 'Ignored title', 'cron_expr': 'invalid', 'duration_minutes': 999})
    wire = held_call_details(call, OWNER)
    assert {'label': 'Event', 'value': 'Matching event B'} in wire['facts']
    assert 'Ignored title' not in json.dumps(wire)
    assert set(call.args) == {'calendar_event_id'}
    result = perform(fact_rig.db, call)
    assert result['title'] == 'Matching event B' and result['calendar_event_id'] == 'event-B'


@pytest.mark.parametrize('action', ['update', 'delete'])
def test_work_item_selector_acts_on_the_named_item(fact_rig, action):
    rig = fact_rig
    a, b = rig.items
    args = {'workbench_id': rig.b['id'], 'item_id': b['id']}
    if action == 'update':
        args['fields'] = {'title': 'Changed B', 'body': PRIVATE}
    call = held('workbench.' + action + '_item', args)
    facts = held_call_details(call, OWNER)['facts']
    assert {'label': 'Item', 'value': 'Matching item B'} in facts
    assert PRIVATE not in json.dumps(facts)
    perform(rig.db, call)
    assert rig.db.workbench_items.get(a['id']).title == 'Matching item A'
    selected = rig.db.workbench_items.get(b['id'])
    assert (selected is None) if action == 'delete' else selected.title == 'Changed B'


def test_cli_defaults_and_fractional_spend_are_idempotent(fact_rig):
    schema = tools._tool_schema('model_library.connect_cli_engine')
    for spend in (None, 0.001, 12.345):
        args = {'draft': {'request_id': 'cli', 'profile_id': 'engine', 'expected_profile_revision': 0, 'preset': 'claude', 'spend_limit_usd': spend}}
        call = held('model_library.connect_cli_engine', args)
        facts = held_call_details(call, OWNER)['facts']
        assert {'label': 'Engine', 'value': 'Claude Code'} in facts
        assert {'label': 'Model', 'value': 'default'} in facts
        assert resolve_target(schema, call.args, OWNER) == call.args
        assert fact_rig.library._cli_draft(call.args['draft']) == fact_rig.library._cli_draft(args['draft'])


def test_calls_execution_uses_the_number_frozen_before_settings_change(fact_rig, monkeypatch):
    import asyncio
    from holdspeak.calls import service as module
    called = []
    class Phone:
        async def call(self, number, **kwargs):
            called.append(number)
            return SimpleNamespace(ok=True, data={'outcome': 'answered', 'call_id': 'test'}, reason='', error='')
        async def say(self, *args, **kwargs): pass
        async def hangup(self, *args, **kwargs): pass
    call = held('calls.test_line', {})
    held_call_details(call, OWNER)
    monkeypatch.setattr(module, '_settings', lambda: SimpleNamespace(allowed_numbers=['+449999999999']))
    monkeypatch.setattr(module, 'calls_on', lambda: True)
    monkeypatch.setattr(module, '_is_line', lambda _: True)
    fact_rig.calls.configure(phone=lambda: Phone())
    asyncio.run(fact_rig.calls.test_line(call.args['to']))
    assert called == ['+441234567890']


def test_a_hand_cannot_fall_back_to_a_new_project_after_approval(fact_rig):
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.primitive_service import PrimitiveService
    rig = fact_rig
    note = PrimitiveService(rig.db).create_note(OWNER, title='Matching note B')
    PrimitiveService(rig.db).create_note(OWNER, title='Matching note A')
    call = held('agent.hand', {'kind': 'note', 'id': note['id']})
    held_call_details(call, OWNER)
    assert call.args['project_binding'] == ''
    projects = ProjectService(rig.db)
    project = projects.create_project(OWNER, {'name': 'Matching Project B'})
    projects.create_project(OWNER, {'name': 'Matching Project A'})
    projects.add_resource(OWNER, project['id'], 'note:' + note['id'])
    with pytest.raises(ServiceError, match='Project changed'):
        rig.hand.resolve_hand_arguments(OWNER, call.args)
