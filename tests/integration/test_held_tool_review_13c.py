"""The reviewed filings, commitment fallback and message direction use the write's resolver."""
from __future__ import annotations

import json
from copy import deepcopy

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.held_tool_details import held_call_details
from holdspeak.services.errors import ServiceError
from holdspeak.services.thread_tools import ThreadToolExecutor
from holdspeak.mcp import tools
from tests.integration.test_held_tool_facts_round3 import OWNER, held, perform, people_rig, project_rig  # noqa: F401
from tests.unit.test_desk_ask_ai import hub  # noqa: F401


def decisions(rig):
    from holdspeak.services.primitive_service import PrimitiveService
    from tests.unit.test_project_setup_service import _seed_decision
    PrimitiveService(rig.db).create_decision(OWNER, decision_id='shared', title='Desk architecture')
    _seed_decision(rig.db, decision_id='shared', text='Meeting architecture')


def test_high_remove_changes_only_the_named_desk_filing(project_rig):
    rig = project_rig
    decisions(rig)
    for ref in ('desk_decision:shared', 'decision:shared'):
        rig.projects.add_resource(OWNER, rig.b['id'], ref)
    call = held('project.resource.remove', {'project_id': rig.b['id'], 'resource_ref': 'desk_decision:shared'})
    assert {'label': 'Source', 'value': 'Desk architecture'} in held_call_details(call, OWNER)['facts']
    perform(rig.db, call)
    assert [r['resource_ref'] for r in rig.projects.list_resources(OWNER, rig.b['id'])] == ['decision:shared']


def test_high_relationship_read_does_not_expand_into_the_other_store(project_rig):
    rig = project_rig
    decisions(rig)
    rig.projects.add_resource(OWNER, rig.a['id'], 'decision:shared')
    rig.projects.add_resource(OWNER, rig.b['id'], 'desk_decision:shared')
    rows = rig.projects.list_resource_relationships(OWNER, 'desk_decision:shared')['projects']
    assert [r['project_id'] for r in rows] == [rig.b['id']]


@pytest.mark.parametrize('body', [None, '', ' \t\n '], ids=['absent', 'blank', 'whitespace'])
def test_medium_accept_counts_the_effective_request_body(people_rig, body):
    rig = people_rig
    person = rig.people.create_relationship(OWNER, {'display_name': 'Mira'})
    request = rig.people.create_request(OWNER, person['id'], {'body': 'Review the architecture', 'visibility': 'shared_intent'})
    args = {'request_id': request['id'], **({'body': body} if body is not None else {})}
    call = held('people.request.accept', args)
    facts = held_call_details(call, OWNER)
    assert {'label': 'Commitment', 'value': '3 words'} in facts['facts']
    assert {'label': 'From', 'value': 'Request'} in facts['facts']
    assert 'Review the architecture' not in json.dumps(facts)
    result = perform(rig.db, call)
    assert result['body'] == 'Review the architecture'


def test_request_body_is_frozen_and_its_count_is_not_disclosed_to_an_agent(people_rig):
    rig = people_rig
    person = rig.people.create_relationship(OWNER, {'display_name': 'Mira'})
    request = rig.people.create_request(OWNER, person['id'], {'body': 'Private request words', 'visibility': 'shared_intent'})
    call = held('people.request.accept', {'request_id': request['id'], 'body': ''})
    call.principal = Principal(PrincipalKind.AGENT, 'request-caller')
    owner = held_call_details(call, OWNER)
    caller = held_call_details(call, call.principal)
    assert {'label': 'Commitment', 'value': 'Hidden'} in caller['facts']
    assert {'label': 'From', 'value': 'Hidden'} in caller['facts']
    assert owner['binding'] == caller['binding']
    assert 'Private request words' not in json.dumps(caller)


@pytest.fixture
def phone(hub, monkeypatch):
    from holdspeak.phone.service import PhoneService
    from holdspeak.phone import service
    import holdspeak.phone
    phone = PhoneService(hub.db)
    monkeypatch.setattr(service, 'default_phone_service', lambda: phone)
    monkeypatch.setattr(holdspeak.phone, 'phone_on', lambda: True)
    monkeypatch.setattr(phone, '_push_event', lambda *a, **kw: False)
    return phone


def test_medium_an_owner_reply_names_the_desk_and_writes_a_reply(hub, phone):
    parent = phone.send_message(OWNER, 'A question')
    call = held('phone.send_message', {'text': 'Approved', 'reply_to': parent['id']})
    facts = held_call_details(call, OWNER)
    assert {'label': 'To', 'value': 'Desk'} in facts['facts']
    result = perform(hub.db, call)
    assert result['direction'] == 'from_phone'
    assert result['reply_to'] == parent['id']


def test_a_reviewing_owner_does_not_turn_an_agents_message_into_an_owner_reply(hub, phone):
    parent = phone.send_message(OWNER, 'A question')
    agent = Principal(PrincipalKind.AGENT, 'phone-caller')
    call = held('phone.send_message', {'text': 'Approved', 'reply_to': parent['id']})
    call.principal = agent
    assert {'label': 'To', 'value': "Owner's phone"} in held_call_details(call, OWNER)['facts']
    executor = ThreadToolExecutor(hub.db, principal=agent, dispatch_fn=tools.dispatch, control_mode_fn=lambda: 'safe')
    executor.decide(call, 'approve')
    assert executor.execute(call).payload['direction'] == 'to_phone'


def test_the_approved_direction_is_checked_before_message_effects(hub, phone):
    parent = phone.send_message(OWNER, 'A question')
    call = held('phone.send_message', {'text': 'Approved', 'reply_to': parent['id']})
    held_call_details(call, OWNER)
    executor = ThreadToolExecutor(hub.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: 'safe')
    executor.decide(call, 'approve')
    changed = deepcopy(phone.store.get_message(parent['id']))
    changed['direction'] = 'from_phone'
    phone.store.save_message(changed)
    result = executor.execute(call)
    assert result.kind == 'tool_execution_failed'
    assert 'message_target_changed' in json.dumps(result.payload)
    assert len(phone.store.list_messages()) == 1


def optional_paths(schema, prefix=''):
    """All named optional fields, including nested provider/credential DTOs."""
    paths = []
    for key, prop in schema.get('properties', {}).items():
        path = prefix + key
        if key not in schema.get('required', []):
            paths.append(path)
        paths.extend(optional_paths(prop, path + '.'))
    return paths


def optional_declarations():
    """The catalogue, including later declarations; no tool-name inventory."""
    return [t for t in tools.TOOLS if 'x-held-arguments' in t['inputSchema']
            and optional_paths(t['inputSchema'])]


@pytest.fixture
def effective_rig(people_rig, phone, tmp_path, monkeypatch):
    from holdspeak import operations
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.meeting_service import MeetingService
    from holdspeak.services.note_outcomes_service import NoteOutcomesService
    from holdspeak.services.program_service import default_program_service
    from holdspeak.services.reach_service import ReachService
    from tests.integration.program_rig import make_repo, FAKE_CHECK
    from holdspeak.services import reach_service
    rig = people_rig
    person = rig.people.create_relationship(OWNER, {'display_name': 'Matching person'})
    request = rig.people.create_request(OWNER, person['id'], {'body': 'Saved request words', 'visibility': 'shared_intent'})
    project = rig.projects.create_project(OWNER, {'name': 'Matching project'})
    note = PrimitiveService(rig.db).create_note(OWNER, title='Matching note')
    outcomes = NoteOutcomesService(rig.db)
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO note_outcomes (id,note_id,ordinal,kind,text,state,found_at) VALUES ('row',?,0,'task','Saved row','proposed','2026-11-12T00:00:00Z')", (note['id'],))
    programs = default_program_service(rig.db)
    program = programs.create(OWNER, title='Matching program', repository=str(make_repo(tmp_path / 'repo')),
                              check_command=f'sh {FAKE_CHECK}')
    capture = MeetingService(rig.db)
    capture.bind_lifecycle(get_state=lambda: {'id': 'capture', 'title': 'Active capture', 'meeting_active': True})
    registry = operations.bind_available({'project_service': rig.projects, 'people_service': rig.people,
        'note_outcomes_service': outcomes, 'program_service': programs, 'meeting_service': capture})
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    reach = ReachService(rig.db)
    monkeypatch.setattr(reach_service, 'default_reach_service', lambda: reach)
    return {**vars(rig), 'request_id': request['id'], 'project_id': project['id'], 'note_id': note['id'],
            'row_id': 'row', 'program_id': program['id'], 'name': 'Matching program', 'meeting_id': 'capture'}


def schema_example(prop):
    if prop.get('enum'):
        return next(v for v in prop['enum'] if v is not None)
    kind = prop.get('type')
    if isinstance(kind, list):
        kind = next(t for t in kind if t != 'null')
    if kind == 'object':
        return {k: schema_example(v) for k, v in prop.get('properties', {}).items() if k in prop.get('required', [])}
    if kind == 'array':
        return [schema_example(prop.get('items', {}))]
    if kind in {'integer', 'number'}:
        return prop.get('minimum', 1)
    if kind == 'boolean':
        return False
    return 'Matching value'


@pytest.mark.parametrize('tool', optional_declarations(), ids=lambda t: t['name'])
def test_optional_arguments_match_the_dispatchers_effective_payload(effective_rig, tool, monkeypatch):
    """Property over the live declaration tree: absent, blank, and whitespace.

    The real dispatcher prepares scalar fields. Its effect port is captured,
    not executed repeatedly (sends, engines and deletes must not run here).
    Stateful tools use their owning write resolver at that port, as their
    writer does. Facts come only from the one projector. The domain tests
    above and below also inspect actual writes and refusals.
    """
    from types import SimpleNamespace
    from holdspeak.held_arguments import resolve_target
    from holdspeak.services.held_tool_details import _facts
    schema, name = tool['inputSchema'], tool['name']
    props = schema.get('properties', {})
    args = {key: effective_rig.get(key, schema_example(prop)) for key, prop in props.items()
            if key in schema.get('required', [])}
    if name.startswith('program.'):
        args.update(program_id=effective_rig['program_id'], name=effective_rig['name'])
    if name == 'channel.send':
        args = {'send_id': 'prepared'}
    if name.startswith('project.resource.'):
        args['resource_ref'] = 'note:' + effective_rig['note_id']
    if name == 'project.item.create':
        args['item_type'] = 'risk'
    if name == 'note.outcome.edit':
        args.update(note_id=effective_rig['note_id'], row_id='row')
    if name == 'desk.create':
        args['kind'] = 'notes'
    for key in optional_paths(schema):
        for value in (None, '', ' \t\n '):
            raw = deepcopy(args)
            seat = raw
            for part in key.split('.')[:-1]:
                seat = seat.setdefault(part, {})
            if value is None:
                seat.pop(key.split('.')[-1], None)
            else:
                seat[key.split('.')[-1]] = value
            call = held(name, raw)
            try:
                details = held_call_details(call, OWNER)
            except (ValueError, TypeError, tools.ToolError, ServiceError) as error:
                # A bad blank precondition or enum must fail through the same
                # owning preparation function, before a write can be reached.
                with pytest.raises(type(error)):
                    resolve_target(schema, raw, OWNER, caller=OWNER)
                continue
            captured = []
            def effect_port(tool_name, payload, principal):
                effective = resolve_target(schema, payload, principal, caller=principal)
                captured.append(deepcopy(effective))
                return {'captured': True}
            # Execute the frozen approved call through the real MCP entry;
            # replace only the final effect port, with the live schema intact.
            with monkeypatch.context() as port:
                port.setattr(tools, 'FAMILIES', [SimpleNamespace(TOOLS=[tool], dispatch=effect_port)])
                executor = ThreadToolExecutor(effective_rig['db'], principal=OWNER,
                    dispatch_fn=tools.dispatch, control_mode_fn=lambda: 'safe')
                executor.decide(call, 'approve')
                result = executor.execute(call)
            assert result.kind != 'tool_execution_failed', (name, key, value, result.payload)
            if call.resolution_error:
                assert captured == [] and result.payload == call.resolution_error
                continue
            assert len(captured) == 1, (name, key, value)
            assert details['facts'] == _facts(schema, captured[0], OWNER), (name, key, value)
            assert captured[0] == call.execution_args, (name, key, value)


@pytest.mark.parametrize('blank', ['', ' \t\n '])
def test_a_note_owner_fact_uses_the_written_people_match(hub, monkeypatch, blank):
    from holdspeak import operations
    from holdspeak.services.note_outcomes_service import NoteOutcomesService
    from holdspeak.services.primitive_service import PrimitiveService
    note = PrimitiveService(hub.db).create_note(OWNER, title='Work note')
    service = NoteOutcomesService(hub.db)
    with hub.db._connection() as conn:
        conn.execute("INSERT INTO note_outcomes (id,note_id,ordinal,kind,text,owner,found_at) VALUES ('row',?,0,'task','Review','Mira','2026-11-12T00:00:00Z')", (note['id'],))
    registry = operations.bind_available({'note_outcomes_service': service})
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    call = held('note.outcome.edit', {'note_id': note['id'], 'row_id': 'row', 'owner_name': blank})
    assert {'label': 'Owner', 'value': 'Me'} in held_call_details(call, OWNER)['facts']
    perform(hub.db, call)
    assert service.read(OWNER, note['id'])['rows'][0]['owner'] == 'Me'


def test_a_changed_request_fallback_is_refused_before_minting(people_rig, monkeypatch):
    rig = people_rig
    person = rig.people.create_relationship(OWNER, {'display_name': 'Mira'})
    request = rig.people.create_request(OWNER, person['id'], {'body': 'Old request', 'visibility': 'shared_intent'})
    call = held('people.request.accept', {'request_id': request['id']})
    held_call_details(call, OWNER)
    frozen = deepcopy(call.args)
    original = rig.people.get_request
    monkeypatch.setattr(rig.people, 'get_request', lambda *a: {**original(*a), 'body': 'Changed request'})
    with pytest.raises(ValueError, match='people_request_changed'):
        rig.people.accept_request(OWNER, request['id'], frozen)
    assert not rig.people._list('commitment', relationship_id=person['id'])


def test_default_lifecycle_and_relationship_facts_match_the_stored_values(project_rig):
    rig = project_rig
    call = held('project.item.create', {'project_id': rig.b['id'], 'item_type': 'risk', 'title': 'Risk', 'lifecycle': '', 'details': {'likelihood': 'low', 'impact': 'low'}})
    assert {'label': 'State', 'value': 'open'} in held_call_details(call, OWNER)['facts']
    result = perform(rig.db, call)
    assert result['item']['lifecycle'] == 'open'
    call = held('project.resource.add', {'project_id': rig.b['id'], 'resource_ref': 'project:' + rig.a['id'], 'relationship': ''})
    assert {'label': 'Relationship', 'value': 'member'} in held_call_details(call, OWNER)['facts']
    perform(rig.db, call)
    assert rig.projects.list_resources(OWNER, rig.b['id'])[0]['relationship'] == 'member'


def test_follow_through_describes_only_the_effective_verb_data(hub):
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService
    service = FollowThroughService(hub.db)
    door = DoorService(service, RefinementThoughtService(hub.db), hub.db.scheduled_recordings, hub.db.calendar_events, db=hub.db)
    task = door.add_item(OWNER, 'Review architecture')
    args = {'card_id': task['id'], 'verb': 'due', 'payload': {'due_at': '', 'due': '20261120', 'to': 'Ignored person'}}
    details = held_call_details(held('follow_through.complete', args), OWNER)
    assert {'label': 'Due', 'value': '2026-11-20'} in details['facts']
    assert not any(f['label'] == 'Owner' for f in details['facts'])
    service.complete(OWNER, **args)
    with hub.db._connection() as conn:
        assert conn.execute('SELECT due FROM action_items WHERE id=?', (task['id'],)).fetchone()['due'] == '2026-11-20'


def test_later_facts_freeze_the_configured_return_time(tmp_path, monkeypatch):
    from holdspeak.services import reach_service
    from tests.unit.test_reach_later import _core, _local
    rig, pid, item = _core(tmp_path, 'normal')
    reach = reach_service.ReachService(rig.db, programs=lambda: rig.service, clock=lambda: _local(12).isoformat())
    monkeypatch.setattr(reach_service, 'default_reach_service', lambda: reach)
    reach.save_settings(OWNER, {'later_means': 'tomorrow'})
    ref = f"program:{pid}:{item['id']}"
    call = held('phone.later', {'ref': ref, 'later': ' '})
    details = held_call_details(call, OWNER)
    expected = call.args['return_at']
    assert {'label': 'Return', 'value': expected} in details['facts']
    result = perform(rig.db, call)
    assert result['until'] == expected
    reach.save_settings(OWNER, {'later_means': 'in_2h'})
    with pytest.raises(ServiceError, match='return time changed'):
        reach.resolve_later_arguments(OWNER, call.args)


def test_a_retired_meeting_decision_keeps_its_reference_identity(project_rig):
    rig = project_rig
    decisions(rig)
    rig.projects.add_resource(OWNER, rig.b['id'], 'decision:shared')
    with rig.db._connection() as conn:
        conn.execute("UPDATE decisions SET deleted=1 WHERE id='shared'")
    assert rig.projects.resolve_resource_target(OWNER, {'resource_ref': 'decision:shared'})['expected_resource_ref'] == 'decision:shared'
    assert rig.projects._project_resource_ref_names('desk_decision:shared') == ('desk_decision:shared',)


@pytest.mark.parametrize('owner_only', [True, False], ids=['owner-only', 'unspecified-kind'])
def test_every_declarations_hidden_parent_hides_children_from_the_caller(owner_only):
    from holdspeak.services.held_tool_details import _facts
    caller = Principal(PrincipalKind.AGENT, 'private-fact-caller')
    for tool in tools.TOOLS:
        schema = tool['inputSchema']
        if 'x-held-arguments' not in schema:
            continue
        schema = {**schema, 'x-held-arguments': [*schema['x-held-arguments'],
            {'key': 'private', 'label': 'Private', 'kind': 'text' if owner_only else None, 'owner_only': owner_only},
            {'key': 'private.title', 'label': 'Private title', 'kind': 'text'}]}
        args = {'private': {'title': 'Private object title'}}
        assert ({'label': 'Private title', 'value': 'Private object title'} in _facts(schema, args, OWNER)) is owner_only
        facts = _facts(schema, args, caller)
        assert {'label': 'Private', 'value': 'Hidden'} in facts
        assert not any(row['label'] == 'Private title' for row in facts), tool['name']
        assert 'Private object title' not in json.dumps(facts), tool['name']
