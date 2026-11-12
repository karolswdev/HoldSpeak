"""Declared owner facts over real public reads, and the target that is written."""
from __future__ import annotations

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from holdspeak import operations
from holdspeak.held_arguments import NOT_YET_DESCRIBED
from holdspeak.mcp import tools
from holdspeak.mcp.palettes import CALL_HELD, resolve_palette
from holdspeak.principals import Principal, PrincipalKind, agent_credentials
from holdspeak.services.held_tool_details import HELD_FACT_VALUE_LIMIT, _facts, held_call_details
from holdspeak.services.thread_tools import ThreadToolExecutor, ToolCallHandle
from tests.integration.test_held_tool_fact_declarations import held_capable_tools
from tests.unit.test_desk_ask_ai import hub  # noqa: F401

OWNER = Principal(PrincipalKind.OWNER, 'facts-round3-owner')
PRIVATE = 'PRIVATE_BODY_CREDENTIAL_7d6a'
FAMILIES = ('phone.', 'nudge.', 'people.', 'decision.', 'project.')


def held(name, args):
    return ToolCallHandle('facts-call', 'facts-thread', 'facts-turn', name, deepcopy(args),
                          'effect_proposal', False, 'awaiting_decision', principal=OWNER)


def perform(db, handle):
    executor = ThreadToolExecutor(db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: 'safe')
    executor.decide(handle, 'approve')
    result = executor.execute(handle)
    assert result.kind != 'tool_execution_failed', result.payload
    return result.payload


def first_tools():
    return {name: tool for name, tool in held_capable_tools().items()
            if name.startswith(FAMILIES) or name in CALL_HELD | resolve_palette('ASK')}


@pytest.mark.parametrize('tool', first_tools().values(), ids=lambda t: t['name'])
def test_every_owner_first_write_has_a_declaration(tool):
    assert 'x-held-arguments' in tool['inputSchema'], tool['name']
    assert tool['name'] not in NOT_YET_DESCRIBED


def set_path(args, path, value):
    seat = args
    parts = path.split('.')
    for part in parts[:-1]:
        seat = seat.setdefault(part, {})
    seat[parts[-1]] = value


@pytest.mark.parametrize('tool', first_tools().values(), ids=lambda t: t['name'])
def test_each_declaration_hides_its_private_kinds_and_bounds_values(hub, tool):
    schema = tool['inputSchema']
    assert 'x-held-arguments' in schema
    args, private_rows, body_rows = {}, [], []
    for row in schema['x-held-arguments']:
        keys = row['key'] if isinstance(row['key'], list) else [row['key']]
        for key in keys:
            set_path(args, key, (PRIVATE if row['kind'] != 'text' or row.get('format') == 'word_count' else 'Matching') + ' word ' * 300)
        if row['kind'] != 'text':
            private_rows.append(row)
        if row.get('format') == 'word_count':
            body_rows.append(row)
    facts = _facts(schema, args, OWNER)
    wire = json.dumps(facts)
    assert PRIVATE not in wire
    assert all(len(f['value']) <= HELD_FACT_VALUE_LIMIT for f in facts)
    for row in private_rows:
        # A hidden child can be suppressed by its own hidden parent.
        keys = row['key'] if isinstance(row['key'], list) else [row['key']]
        parents = [r['key'] for r in private_rows if isinstance(r['key'], str)]
        if all(any(k.startswith(p + '.') for p in parents) for k in keys):
            continue
        assert {'label': row['label'], 'value': 'hidden (' + row['kind'] + ')'} in facts
    for row in body_rows:
        assert any(f['label'] == row['label'] and f['value'].endswith(' words') for f in facts)
    # Hidden inheritance is a property of every declaration, not only notes.
    nested = {**schema, 'x-held-arguments': [*schema['x-held-arguments'],
        {'key': 'private', 'label': 'Private', 'kind': 'credential'},
        {'key': 'private.title', 'label': 'Child', 'kind': 'text'}]}
    assert not any(f['label'] == 'Child' for f in _facts(nested, {'private': {'title': PRIVATE}}, OWNER))


@pytest.fixture
def people_rig(hub, tmp_path, monkeypatch):
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from holdspeak.services.people_service import PeopleService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.workbench_service import WorkbenchService
    from holdspeak.mcp.families import people as family
    from holdspeak import people_operations
    store = EncryptedPeopleStore(tmp_path / 'people.sqlite3', MemoryKeyStore())
    store.initialize()
    people, projects, work = PeopleService(store), ProjectService(hub.db), WorkbenchService(hub.db)
    monkeypatch.setattr(family, 'build_people_service', lambda: people)
    monkeypatch.setattr(people_operations, '_projects', lambda: projects)
    monkeypatch.setattr(people_operations, 'workbenches', lambda: work)
    registry = operations.bind_available({'people_service': people, 'project_service': projects, 'workbench_service': work})
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    monkeypatch.setenv(family.ACCESS_ENV, 'write')
    return SimpleNamespace(db=hub.db, people=people, projects=projects, work=work)


@pytest.mark.parametrize('name', [n for n in first_tools() if n.startswith('people.')])
def test_people_write_uses_the_second_person_or_item_without_a_body_fact(people_rig, name):
    rig = people_rig
    a, b = [rig.people.create_relationship(OWNER, {'display_name': 'Matching ' + suffix})
            for suffix in ('First', 'Second')]
    sessions = [rig.people.create_one_on_one(OWNER, r['id'], {'agenda': PRIVATE, 'visibility': 'shared_intent'}) for r in (a, b)]
    requests = [rig.people.create_request(OWNER, r['id'], {'body': PRIVATE, 'visibility': 'shared_intent'}) for r in (a, b)]
    commitments = [rig.people.accept_request(OWNER, r['id']) for r in requests]
    agenda = [rig.people.add_agenda_item(OWNER, s['id'], {'body': PRIVATE, 'visibility': 'shared_intent'}) for s in sessions]
    project = rig.projects.create_project(OWNER, {'name': 'Matching project'})
    work = rig.work.create_workbench(OWNER, name='Matching automation')
    args = {'relationship_id': b['id']}
    verb = name.removeprefix('people.')
    if verb == 'relationship.create':
        args = {'display_name': 'Matching Third', 'role_context': PRIVATE}
    elif verb == 'one_on_one.create': args['agenda'] = PRIVATE
    elif verb == 'agenda.add': args = {'session_id': sessions[1]['id'], 'body': PRIVATE}
    elif verb in {'note.create', 'request.create', 'owed.create'}: args['body'] = PRIVATE
    elif verb == 'request.accept':
        requests[1] = rig.people.create_request(OWNER, b['id'], {'body': PRIVATE, 'visibility': 'shared_intent'})
        args = {'request_id': requests[1]['id'], 'body': PRIVATE}
    elif verb == 'commitment.transition': args = {'commitment_id': commitments[1]['id'], 'verb': 'done'}
    elif verb == 'agenda.transition': args = {'item_id': agenda[1]['id'], 'to': 'done'}
    elif verb == 'commitment.satisfy': args = {'commitment_id': commitments[1]['id'], 'rationale': PRIVATE}
    elif verb == 'commitment.send_to_workbench': args = {'commitment_id': commitments[1]['id'], 'workbench_id': work['id']}
    elif verb in {'project.link', 'project.unlink'}:
        args['project_id'] = project['id']
        if verb == 'project.unlink': rig.people.link_project(OWNER, b['id'], project['id'])
    elif verb in {'calendar.link', 'calendar.unlink'}:
        args.update(uid='series-second', source_id='calendar-source')
        rig.people.link_calendar_series(OWNER, a['id'], 'series-first', 'calendar-source', '')
        if verb == 'calendar.unlink': rig.people.link_calendar_series(OWNER, b['id'], args['uid'], args['source_id'], '')
    elif verb.startswith('suggestion.'):
        events = [SimpleNamespace(id='event-' + n, uid='series-' + n, title='1:1 with Mira ' + n,
            starts_at='2099-01-01T10:00:00+00:00', ends_at='2099-01-01T11:00:00+00:00',
            location=None, meeting_url=None, attendees=[]) for n in ('First', 'Second')]
        rig.db.calendar_events.replace_projection('round3', events, seen_at=1, source_id='round3')
        suggestions = rig.people.suggestions(OWNER, db=rig.db)
        picked = next(s for s in suggestions if s['name'] == 'Mira Second')
        args = {'key': picked['key']}
    else: raise AssertionError('Add the real domain case for ' + name)
    before_a = rig.people.get_relationship(OWNER, a['id'])
    call = held(name, args)
    details = held_call_details(call, OWNER)
    assert PRIVATE not in json.dumps(details)
    if 'relationship_id' in args:
        assert {'label': 'Person', 'value': 'Matching Second'} in details['facts']
    if verb.startswith('suggestion.'):
        assert {'label': 'Person', 'value': 'Mira Second'} in details['facts']
    result = perform(rig.db, call)
    assert rig.people.get_relationship(OWNER, a['id']) == before_a
    after_b = rig.people.get_relationship(OWNER, b['id'])
    if verb == 'relationship.create': assert result['display_name'] == 'Matching Third'
    elif verb == 'one_on_one.create': assert result['relationship_id'] == b['id']
    elif verb == 'agenda.add': assert result['session_id'] == sessions[1]['id']
    elif verb in {'note.create', 'request.create'}: assert result['relationship_id'] == b['id']
    elif verb == 'owed.create': assert result['commitment']['relationship_id'] == b['id']
    elif verb == 'request.accept': assert result['request_id'] == requests[1]['id']
    elif verb == 'commitment.transition': assert rig.people.get_commitment(OWNER, commitments[1]['id'])['state'] == 'done'
    elif verb == 'agenda.transition': assert next(s for s in after_b['sessions'] if s['id'] == sessions[1]['id'])['agenda'][0]['state'] == 'done'
    elif verb == 'commitment.satisfy': assert result['commitment']['state'] == 'done'
    elif verb == 'commitment.send_to_workbench': assert result['commitment']['id'] == commitments[1]['id'] and result['item']['workbench_id'] == work['id']
    elif verb == 'project.link': assert project['id'] in after_b['project_refs']
    elif verb == 'project.unlink': assert project['id'] not in after_b['project_refs']
    elif verb == 'calendar.link': assert any(s['uid'] == 'series-second' for s in after_b['calendar_links'])
    elif verb == 'calendar.unlink': assert not after_b['calendar_links']
    elif verb.startswith('suggestion.'):
        remaining = rig.people.suggestions(OWNER, db=rig.db)
        assert any(s['name'] == 'Mira First' for s in remaining)
        assert not any(s['name'] == 'Mira Second' for s in remaining)


@pytest.fixture
def project_rig(hub, monkeypatch):
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_update_service import ProjectUpdateService
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.meeting_service import MeetingService
    from holdspeak.mcp.families import project as family
    projects = ProjectService(hub.db)
    updates = ProjectUpdateService(hub.db, project_service=projects)
    delta = ProjectDeltaService(hub.db, collector=ProjectEvidenceCollector(hub.db), project_service=projects)
    registry = operations.bind_available({'project_service': projects, 'project_update_service': updates,
        'project_delta_service': delta, 'primitive_service': PrimitiveService(hub.db),
        'meeting_service': MeetingService(hub.db)})
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    monkeypatch.setattr(family, '_ops', lambda: registry)
    a, b = [projects.create_project(OWNER, {'name': 'Matching project ' + suffix}) for suffix in ('First', 'Second')]
    return SimpleNamespace(db=hub.db, projects=projects, updates=updates, delta=delta, a=a, b=b, registry=registry)


@pytest.mark.parametrize('name', ['project.update', 'project.archive', 'project.restore', 'project.link',
    'project.unlink', 'project.mark_room_read', 'project.draft_update', 'project.open_review',
    'project.item.update', 'project.item.transition', 'project.resource.add', 'project.resource.remove'])
def test_project_writes_name_and_change_only_the_selected_second_object(project_rig, name):
    from tests.integration.test_held_tool_review_13b import meeting
    rig = project_rig
    args = {'project_id': rig.b['id']}
    if name == 'project.update': args['patch'] = {'name': 'Changed Second', 'description': PRIVATE}
    elif name == 'project.restore': rig.projects.archive_project(OWNER, rig.b['id'])
    elif name in {'project.link', 'project.unlink'}:
        meeting(rig.db, 'meeting-first', 'Matching meeting First')
        meeting(rig.db, 'meeting-second', 'Matching meeting Second')
        args['meeting_id'] = 'meeting-second'
        if name.endswith('unlink'): rig.projects.associate_meeting(OWNER, rig.b['id'], 'meeting-second')
    elif name.startswith('project.item.'):
        items = [rig.projects.create_item(OWNER, project['id'], {'item_type': 'risk', 'title': 'Matching item ' + suffix, 'details': {'likelihood': 'medium', 'impact': 'medium'}})
                 for project, suffix in ((rig.a, 'First'), (rig.b, 'Second'))]
        args['item_id'] = items[1]['id']
        args['patch' if name.endswith('update') else 'verb'] = {'title': 'Changed Second', 'summary': PRIVATE} if name.endswith('update') else 'closed'
    elif name.startswith('project.resource.'):
        from holdspeak.services.primitive_service import PrimitiveService
        for identity, suffix in (('first', 'First'), ('second', 'Second')):
            PrimitiveService(rig.db).create_note(OWNER, note_id=identity, title='Matching source ' + suffix, body_markdown=PRIVATE)
        args['resource_ref'] = 'note:second'
        if name.endswith('remove'): rig.projects.add_resource(OWNER, rig.b['id'], 'note:second')
    before_a = rig.projects.get_project(OWNER, rig.a['id'])
    call = held(name, args)
    details = held_call_details(call, OWNER)
    assert {'label': 'Project', 'value': 'Matching project Second'} in details['facts']
    assert PRIVATE not in json.dumps(details)
    if 'item_id' in args: assert {'label': 'Item', 'value': 'Matching item Second'} in details['facts']
    if 'meeting_id' in args: assert {'label': 'Meeting', 'value': 'Matching meeting Second'} in details['facts']
    if 'resource_ref' in args: assert {'label': 'Source', 'value': 'Matching source Second'} in details['facts']
    result = perform(rig.db, call)
    assert rig.projects.get_project(OWNER, rig.a['id']) == before_a
    if name == 'project.update': assert rig.projects.get_project(OWNER, rig.b['id'])['name'] == 'Changed Second'
    elif name == 'project.archive': assert rig.projects.get_project(OWNER, rig.b['id'])['is_archived']
    elif name == 'project.restore': assert not rig.projects.get_project(OWNER, rig.b['id'])['is_archived']
    elif name == 'project.draft_update': assert result['update']['project_id'] == rig.b['id']
    elif name == 'project.open_review': assert result['project_id'] == rig.b['id']
    elif name == 'project.item.update': assert result['item']['id'] == args['item_id'] and result['item']['title'] == 'Changed Second'
    elif name == 'project.item.transition': assert result['item']['id'] == args['item_id'] and result['item']['lifecycle'] == 'closed'
    elif name == 'project.link': assert [m['id'] for m in rig.projects.list_meetings(OWNER, rig.b['id'])] == ['meeting-second']
    elif name == 'project.unlink': assert not rig.projects.list_meetings(OWNER, rig.b['id'])
    elif name == 'project.resource.add': assert any(r['resource_ref'] == 'note:second' for r in rig.projects.list_resources(OWNER, rig.b['id']))
    elif name == 'project.resource.remove': assert not rig.projects.list_resources(OWNER, rig.b['id'])
    elif name == 'project.mark_room_read': assert result['readAt']


@pytest.mark.parametrize('name', ['project.update_draft', 'project.publish_update', 'project.update.regenerate'])
def test_update_facts_follow_the_selected_update_to_its_project(project_rig, name):
    rig = project_rig
    updates = [rig.updates.draft_update(OWNER, p['id']) for p in (rig.a, rig.b)]
    args = {'update_id': updates[1]['id']}
    if name == 'project.update_draft': args['body_md'] = PRIVATE
    before_a = rig.updates.get_update(OWNER, updates[0]['id'])
    call = held(name, args)
    details = held_call_details(call, OWNER)
    assert {'label': 'Project', 'value': 'Matching project Second'} in details['facts']
    assert PRIVATE not in json.dumps(details)
    result = perform(rig.db, call)
    assert result['update']['project_id'] == rig.b['id']
    assert rig.updates.get_update(OWNER, updates[0]['id']) == before_a
    if name == 'project.update_draft': assert result['update']['body_md'] == PRIVATE
    if name == 'project.publish_update': assert result['update']['lifecycle'] == 'published'


def test_chained_names_use_each_readers_scoped_path_and_one_owner_revision(project_rig, monkeypatch):
    from holdspeak.mcp import server
    rig = project_rig
    update = rig.updates.draft_update(OWNER, rig.b['id'])
    credential = agent_credentials.issue('round3-scoped', palette=frozenset({'project.update.get', 'project.get'}))
    try:
        call = held('project.publish_update', {'update_id': update['id']})
        call.principal = credential.principal
        owner = held_call_details(call, OWNER)
        assert {'label': 'Project', 'value': 'Matching project Second'} in owner['facts']
        ordinary = server.read_for_principal
        visited = []
        def scoped(tool, args, reader):
            visited.append((tool, reader))
            # This is the filtered first answer, not the raw dispatch answer.
            if reader == credential.principal and tool == 'project.update.get': return {'withheld': True}
            return ordinary(tool, args, reader)
        monkeypatch.setattr(server, 'read_for_principal', scoped)
        caller = held_call_details(call, credential.principal)
        assert {'label': 'Project', 'value': 'hidden (secret)'} in caller['facts']
        assert 'Matching project Second' not in json.dumps(caller)
        assert not any(t == 'project.get' and p == credential.principal for t, p in visited)
        assert caller['binding'] == owner['binding']
        rig.projects.update_project(OWNER, rig.b['id'], {'name': 'Renamed Second'})
        assert held_call_details(call, OWNER)['binding'] != owner['binding']
    finally: agent_credentials.revoke(credential.principal.identity)


def test_every_lookup_step_is_a_declared_pure_read_with_valid_inputs():
    from holdspeak.held_arguments import strongest_effect
    all_tools = {t['name']: t for t in tools.TOOLS}
    for tool in tools.TOOLS:
        for fact in tool['inputSchema'].get('x-held-arguments', []):
            read = fact.get('read')
            while read:
                source = all_tools[read['tool']]
                assert strongest_effect(source) == 'read', (tool['name'], read['tool'])
                assert set(read['arguments']) <= set(source['inputSchema'].get('properties', {})), (tool['name'], read)
                read = read.get('through')


@pytest.mark.parametrize('name', ['desk_window.open', 'desk_window.close', 'desk_window.raise', 'desk_window.arrange'])
def test_window_verbs_use_the_selected_second_window(hub, monkeypatch, name):
    from holdspeak.services.desk_window_service import DeskWindowService
    service = DeskWindowService(hub.db)
    a, b = 'surface-projects', 'surface-people'
    service.open(a)
    if name != 'desk_window.open': service.open(b)
    before = service.get(a)
    args = {'rects': {b: {'x': 0, 'y': 0, 'w': 400, 'h': 400}}} if name.endswith('arrange') else {'window_id': b}
    registry = operations.bind_available({'desk_window_service': service})
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    call = held(name, args)
    details = held_call_details(call, OWNER)
    assert b not in json.dumps(details)
    perform(hub.db, call)
    after = service.get(a)
    assert after['revision'] == before['revision']
    assert (after['x'], after['y'], after['w'], after['h']) == (before['x'], before['y'], before['w'], before['h'])
    windows = service.list()['windows']
    if name.endswith('close'): assert not any(w['id'] == b for w in windows)
    else: assert any(w['id'] == b for w in windows)


def test_filing_names_the_second_folder_and_files_only_the_second_object(hub):
    from holdspeak.services.primitive_service import PrimitiveService
    primitives = PrimitiveService(hub.db)
    a, b = [primitives.create_directory(OWNER, name='Matching folder ' + suffix) for suffix in ('First', 'Second')]
    notes = [primitives.create_note(OWNER, title='Matching note ' + suffix) for suffix in ('First', 'Second')]
    call = held('zone.file', {'directory_id': b['id'], 'primitive_id': 'note:' + notes[1]['id']})
    details = held_call_details(call, OWNER)
    assert {'label': 'Folder', 'value': 'Matching folder Second'} in details['facts']
    assert {'label': 'Object', 'value': 'Matching note Second'} in details['facts']
    perform(hub.db, call)
    assert not primitives.list_directory_members(OWNER, a['id'])
    assert [m['primitive_id'] for m in primitives.list_directory_members(OWNER, b['id'])] == ['note:' + notes[1]['id']]


@pytest.mark.parametrize('name', ['decision.accept', 'decision.meeting_supersede', 'decision.promote', 'decision.promote_draft'])
def test_meeting_decision_facts_name_the_second_meeting_without_the_decision_body(hub, monkeypatch, name):
    from tests.unit.test_decisions import _meeting_visible
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
    from holdspeak.services.meeting_service import MeetingService
    for suffix, day in (('First', 1), ('Second', 2)):
        _meeting_visible(hub.db, 'meeting-' + suffix, 'Matching meeting ' + suffix, day, [PRIVATE])
    a, b = [hub.db.decisions.list(meeting_id='meeting-' + suffix)[0] for suffix in ('First', 'Second')]
    service = DecisionLifecycleService(hub.db)
    registry = operations.bind_available({'decision_lifecycle_service': service, 'meeting_service': MeetingService(hub.db)})
    monkeypatch.setattr(tools, 'runtime_registry', lambda *a: registry)
    args = {'decision_id': b.id}
    if name in {'decision.promote', 'decision.promote_draft'}:
        hub.db.decisions.accept(b.id, actor=OWNER.identity)
        args['artifact_type'] = 'adr'
    if name == 'decision.meeting_supersede':
        hub.db.decisions.accept(a.id, actor=OWNER.identity)
        hub.db.decisions.accept(b.id, actor=OWNER.identity)
        args['superseded_by'] = a.id
    drafted = []
    if name == 'decision.promote_draft':
        # The inference boundary is a test adapter. The real MCP operation
        # must give it B; no engine or provider is contacted.
        async def draft(principal, decision_id, artifact_type, payload):
            drafted.append((decision_id, artifact_type))
            return service.get_decision(principal, decision_id)
        monkeypatch.setattr(service, 'draft_promoted_with_model', draft)
    before_a = hub.db.decisions.get(a.id).to_dict()
    call = held(name, args)
    facts = held_call_details(call, OWNER)
    assert {'label': 'Meeting', 'value': 'Matching meeting Second'} in facts['facts']
    assert PRIVATE not in json.dumps(facts)
    perform(hub.db, call)
    if name == 'decision.accept': assert hub.db.decisions.get(b.id).lifecycle == 'accepted'
    if name == 'decision.meeting_supersede': assert hub.db.decisions.get(b.id).lifecycle == 'superseded'
    if name == 'decision.promote': assert hub.db.decisions.get_with_lineage(b.id)['lineage']['derived_artifacts']
    if name == 'decision.promote_draft': assert drafted == [(b.id, 'adr')]
    # Supersede adds a lineage edge to A, but does not change its decision.
    assert hub.db.decisions.get(a.id).to_dict() == before_a


def test_desk_supersede_names_and_changes_the_second_decision(hub):
    from holdspeak.services.primitive_service import PrimitiveService
    service = PrimitiveService(hub.db)
    a, b = [service.create_decision(OWNER, title='Matching decision ' + suffix, decision_markdown=PRIVATE)
            for suffix in ('First', 'Second')]
    before_a = service.get_decision(OWNER, a['id'])
    call = held('decision.supersede', {'decision_id': b['id']})
    assert {'label': 'Decision', 'value': 'Matching decision Second'} in held_call_details(call, OWNER)['facts']
    perform(hub.db, call)
    assert service.get_decision(OWNER, a['id']) == before_a
    assert service.get_decision(OWNER, b['id'])['status'] == 'superseded'


def test_nudge_dismiss_only_changes_the_second_step(project_rig, monkeypatch):
    from holdspeak.services.project_steward_service import ProjectStewardService
    rig = project_rig
    for suffix, project in (('first', rig.a), ('second', rig.b)):
        rig.db.steward_runs.insert_run(run_id='run-' + suffix, project_id=project['id'])
        rig.db.steward_steps.insert_step(step_id='nudge-' + suffix, run_id='run-' + suffix,
                                        effect_kind='github_comment', state='proposed')
    service = ProjectStewardService(rig.db, collector=None, delta=rig.delta, project_service=rig.projects)
    from holdspeak.mcp.families import project as family
    registry = operations.bind_available({'project_steward_service': service})
    monkeypatch.setattr(family, '_ops', lambda: registry)
    call = held('nudge.dismiss', {'step_id': 'nudge-second'})
    assert held_call_details(call, OWNER)['facts'] == [{'label': 'Review', 'value': 'hidden (secret)'}]
    perform(rig.db, call)
    assert rig.db.steward_steps.get_step('nudge-first')['state'] == 'proposed'
    assert rig.db.steward_steps.get_step('nudge-second')['state'] == 'dismissed'


def test_a_chained_name_lookup_cannot_run_a_write(hub):
    from holdspeak.held_arguments import held_arguments, named
    from tests.integration.test_held_tool_review_13b import meeting
    meeting(hub.db, 'name-source', 'Private source')
    schema = held_arguments('Read a name', named('id', 'Name', 'meeting.get', {'meeting_id': 'id'}, 'task',
        through={'tool': 'door.add_item', 'arguments': {'task': 'title'}}))
    before = hub.db._connection
    with before() as conn:
        count = conn.execute('SELECT COUNT(*) FROM action_items').fetchone()[0]
    assert _facts(schema, {'id': 'name-source'}, OWNER) == [{'label': 'Name', 'value': 'hidden (secret)'}]
    with before() as conn:
        assert conn.execute('SELECT COUNT(*) FROM action_items').fetchone()[0] == count


@pytest.mark.parametrize('name', ['project.setup.answer', 'project.setup.suggest',
    'project.setup.select_proposal', 'project.setup.deselect_proposal'])
def test_setup_uses_the_second_session_and_its_own_proposal(project_rig, monkeypatch, name):
    from holdspeak.services.project_setup_service import ProjectSetupService, Q_OUTCOME
    from holdspeak.mcp.families import project as family
    rig = project_rig
    service = ProjectSetupService(rig.db, project_service=rig.projects, watch_service=None)
    monkeypatch.setattr(family, '_setup_service', lambda: service)
    sessions = [service.start_setup(OWNER) for _ in range(2)]
    a, b = sessions
    args = {'session_id': b['id']}
    if name.endswith('answer'):
        args.update(question_id=Q_OUTCOME, payload={'text': PRIVATE})
    elif name.endswith('proposal'):
        for i, session in enumerate(sessions):
            service._repo.create_setup_proposal(proposal_id='proposal-' + str(i), session_id=session['id'],
                provider_id='native', spec_schema='WatchSpec@1', spec_json='{}', rationale_json='{}',
                state='selected' if name.endswith('deselect_proposal') else 'proposed')
        args['proposal_id'] = 'proposal-1'
    before_a = service.get_setup(a['id'])
    call = held(name, args)
    details = held_call_details(call, OWNER)
    assert PRIVATE not in json.dumps(details)
    assert b['id'] not in json.dumps(details)
    perform(rig.db, call)
    assert service.get_setup(a['id']) == before_a
    after_b = service.get_setup(b['id'])
    if name.endswith('answer'): assert after_b['answers'][Q_OUTCOME]['answer']['original'] == PRIVATE
    elif name.endswith('suggest'): assert after_b['stage'] == 'proposals'
    elif name.endswith('deselect_proposal'): assert after_b['proposals'][0]['state'] == 'proposed'
    else: assert after_b['proposals'][0]['state'] == 'selected'


def test_a_project_decision_ref_cannot_change_stores_after_its_facts_are_read(project_rig):
    from holdspeak.services.primitive_service import PrimitiveService
    from tests.unit.test_project_setup_service import _seed_decision
    rig = project_rig
    PrimitiveService(rig.db).create_decision(OWNER, decision_id='shared-id', title='Desk target', decision_markdown=PRIVATE)
    call = held('project.resource.add', {'project_id': rig.b['id'], 'resource_ref': 'decision:shared-id'})
    details = held_call_details(call, OWNER)
    assert call.args['expected_resource_ref'] == 'desk_decision:shared-id'
    assert {'label': 'Source', 'value': 'Desk target'} in details['facts']
    executor = ThreadToolExecutor(rig.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: 'safe')
    executor.decide(call, 'approve')
    # Same legacy token can now denote a meeting decision. The approved
    # store is a precondition, never a reason to file the other object.
    _seed_decision(rig.db, decision_id='shared-id', text=PRIVATE)
    outcome = executor.execute(call)
    assert outcome.kind == 'tool_execution_failed'
    assert outcome.payload['code'] == 'source_target_changed'
    assert not rig.projects.list_resources(OWNER, rig.b['id'])
    other = held('project.resource.add', {'project_id': rig.b['id'], 'resource_ref': 'decision:shared-id'})
    facts = held_call_details(other, OWNER)['facts']
    assert {'label': 'Source', 'value': 'hidden (secret)'} in facts
    assert 'Desk target' not in json.dumps(facts)
