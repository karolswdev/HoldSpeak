"""Real producers for the shared name fitter's five consumer seats."""
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote
from . import open_rig
from .glass_infra import _api, _normal_chair, _settle, clear_hub_windows_http
from .test_lists_wave14_glass import LONG_NAME, IDENTIFIER
from .test_people_os_grammar_glass import TOKEN


def seed_names(tmp_path, base, monkeypatch):
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.agent_context import event_log, ingest_agent_hook_event
    import holdspeak.agent_context as context
    db=get_database()
    open_rig._seed(tmp_path/'home',base)
    owner=Principal(PrincipalKind.OWNER,'name-fit-rig')
    db.projects.create_project(project_id='name-fit-room',name='Architecture review',description='Review the filed sources.',keywords=[])
    primitives,projects=PrimitiveService(db),ProjectService(db)
    people=[]
    now=datetime.now(timezone.utc)
    for i in range(50):
        name=IDENTIFIER if i==0 else LONG_NAME if i==1 else f'Platform reviewer {i:02d} — {LONG_NAME}'
        people.append(open_rig._http(base,'POST','/api/people/relationships',{'display_name':name,'relationship_kind':'peer'})['relationship'])
        db.workbenches.upsert(workbench_id=f'name-fit-{i}',name=name,instruction='Prepare the architecture review.')
        db.meetings.save_meeting(MeetingState(id=f'name-fit-{i}',title=name,started_at=now-timedelta(hours=i),ended_at=now-timedelta(hours=i)+timedelta(minutes=30),intel=IntelSnapshot(timestamp=1,summary='Read the saved review.'),intel_status='completed'))
        db.proposals.create_proposal(meeting_id='name-fit-0',project_id=None,kind='action',text=name,source_plugin='summary')
        primitives.create_note(owner,note_id=f'name-fit-{i}',title=name,body_markdown='Keep the source with the review.',tags=[])
        projects.add_resource(owner,'name-fit-room',f'note:name-fit-{i}')
        for event,data in [('SessionStart',{'source':'startup'}),('UserPromptSubmit',{'prompt':'Read the saved review.'}),('Notification',{'notification_type':'idle_prompt','message':f'Who owns {name}?'})]:
            ingest_agent_hook_event(agent='claude',payload={'session_id':f'name-fit-{i}','cwd':str(tmp_path/'home'),'hook_event_name':event,**data},state_path=context.AGENT_CONTEXT_FILE,events_spool_dir=event_log.default_spool_dir())
    return people


def open_window(page, base, wid, width, object_ref=None, payload=None):
    clear_hub_windows_http(base,TOKEN)
    _api(page,'POST',f'/api/desk/windows/{wid}/open',payload or ({'object_ref':object_ref} if object_ref else {}),token=TOKEN)
    if width==1440:
        _api(page,'POST',f'/api/desk/windows/{wid}/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'900px','h':'600px'}},token=TOKEN)
    page.reload(wait_until='load');_normal_chair(page)
    win=page.locator(f'[id="{unquote(wid)}"]');win.wait_for();return win


def scenes(page, base, width, people):
    win=open_window(page,base,'surface-people',width)
    row=win.locator(f'[data-object-id="{people[0]["id"]}"]');row.click()
    row.evaluate("row=>{const well=row.closest('.object-list-rows');well.scrollTop+=row.getBoundingClientRect().top-well.getBoundingClientRect().top;}");_settle(page)
    yield 'people',win,win.get_by_role('grid',name='People',exact=True)
    win=open_window(page,base,'surface-workbenches',width)
    win.locator('[data-object-id="name-fit-0"]').click();_settle(page)
    yield 'automations',win,win.get_by_role('grid',name='Automations',exact=True)
    win=open_window(page,base,'surface-meetings',width)
    win.get_by_test_id('meeting-row-name-fit-0').click()
    win.get_by_role('button',name='Meeting contents',exact=True).click()
    page.get_by_role('menuitemradio',name='Tasks to confirm',exact=True).click()
    grid=win.get_by_role('grid',name='Tasks to confirm',exact=True);grid.wait_for();_settle(page)
    yield 'meetings-preview',win,grid
    win=open_window(page,base,'chair%3Aneeds',width,payload={'kind':'chair','ref':'needs'})
    grid=page.get_by_test_id('needs-drawer').get_by_role('grid',name='Needs you',exact=True);grid.locator('[data-object-id]').first.wait_for();_settle(page)
    yield 'needs-you',win,grid
    win=open_window(page,base,'surface-project-memory',width,object_ref='project:name-fit-room')
    win.get_by_test_id('room-body').wait_for()
    from .test_native_project_source_return_glass import _files
    grid=_files(win).get_by_role('grid');grid.locator('[data-object-id]').first.wait_for();_settle(page)
    yield 'room-files',win,grid
