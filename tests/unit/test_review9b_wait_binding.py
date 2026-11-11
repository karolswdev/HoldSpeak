"""Owner answers cross the real hook registry, HTTP route and terminal executor.
Only the tmux identity/transport and clock-independent process edge are injected.
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import holdspeak.agent_context as context
from holdspeak import coder_steering, tmux_transport
from holdspeak.agent_context import screen_watch, screen_rules
from holdspeak.config import Config
from holdspeak.db import core as dbcore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system.coders import build_coders_router
from holdspeak.web.routes.system.coder_steering_routes import build_coder_steering_router

COMPLETE_SCREEN = (Path(__file__).parents[1]/"fixtures/agent_screens/claude-rig-permission.txt").read_text()

FIELDS = ("wait_id", "wait_revision", "wait_kind", "expected_pane_id", "expected_pane_fingerprint")

@pytest.fixture
def rig(tmp_path, monkeypatch):
    dbcore.reset_database()
    db = dbcore.Database(tmp_path / "hub.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr(context, "AGENT_CONTEXT_FILE", tmp_path / "sessions.json")
    monkeypatch.setenv("HOLDSPEAK_WAIT_PANE_PROBE", "on")
    monkeypatch.setattr("holdspeak.agent_context.hooks._read_tmux_display", lambda *a, **k: {})
    state = SimpleNamespace(fingerprint="original-process", pane="%3", sent=[], db=db, screen=None, principal=Principal(PrincipalKind.OWNER,"review9b-owner"))
    def identity(target, runner=None):
        pane = target if str(target).startswith("%") else state.pane
        return {"status":"ok", "pane_id":pane, "fingerprint":state.fingerprint}
    monkeypatch.setattr(coder_steering, "resolve_pane_identity", identity)
    monkeypatch.setattr(screen_watch, "capture", lambda *a, **k: (state.screen or "", ""))
    monkeypatch.setattr(Config, "load", classmethod(lambda cls: SimpleNamespace(control_mode="safe")))
    monkeypatch.setattr(tmux_transport, "send_text_to_pane", lambda **kw: state.sent.append(kw))
    monkeypatch.setattr(tmux_transport, "send_keys_to_pane", lambda **kw: state.sent.append(kw))
    screen_watch.STORE.clear(); coder_steering.clear_grants()
    app=FastAPI()
    @app.middleware("http")
    async def owner(req, next):
        req.state.principal=state.principal
        return await next(req)
    ctx=WebContext(get_state=lambda:{},broadcast=lambda *_:None)
    app.include_router(build_coders_router(ctx)); app.include_router(build_coder_steering_router(ctx))
    state.client=TestClient(app)
    def event(message="Who owns the runbook?", *, permission=False, pane="%3"):
        return context.ingest_agent_hook_event(agent="claude", payload={"session_id":"review9b", "cwd":str(tmp_path),
            "tmux_pane":pane,"hook_event_name":"Notification","notification_type":"permission_prompt" if permission else "idle_prompt",
            "message":message}, state_path=tmp_path/"sessions.json", events_spool_dir=tmp_path/"events")
    state.event=event
    def shown():
        answer=state.client.get("/api/coders/sessions?include_ended=false")
        assert answer.status_code == 200, answer.text
        session=answer.json()["sessions"][0]["session"]
        return {key:session.get(key) for key in FIELDS}
    state.shown=shown
    yield state
    coder_steering.clear_grants(); screen_watch.STORE.clear(); dbcore.reset_database()


def post(rig, binding, *, keys=None):
    body={"kind":"answer", **binding, **({"keys":keys} if keys else {"text":"Jordan", "submit":True})}
    return rig.client.post(f"/api/coders/claude:review9b/{'keys' if keys else 'steer'}", json=body)

@pytest.mark.parametrize("keys", [None, ["Escape"], ["Enter"]])
def test_same_wait_id_with_a_changed_prompt_refuses_the_displayed_answer(rig, keys):
    rig.event(); shown=rig.shown()
    rig.event("Run the new command?", permission=True)
    assert rig.shown()["wait_id"] == shown["wait_id"]
    answer=post(rig,shown,keys=keys)
    assert answer.status_code == 409 and answer.json()["status"] == "wait_not_current", answer.text
    assert rig.sent == []


def test_prompt_revision_is_checked_again_at_the_terminal_boundary(rig, monkeypatch):
    rig.event(); shown=rig.shown()
    original=coder_steering.current_wait_episode
    def changed(key):
        rig.event("Who signs the release?")
        return original(key)
    monkeypatch.setattr(coder_steering,"current_wait_episode",changed)
    answer=post(rig,shown)
    assert answer.status_code == 409 and answer.json()["status"] == "wait_not_current", answer.text
    assert rig.sent == []


def test_a_changed_prompt_between_text_and_return_gets_no_return(rig, monkeypatch):
    rig.event(); shown=rig.shown()
    def type_text(**kw):
        rig.sent.append(kw)
        if not kw["submit"]: rig.event("Who signs the release?")
    monkeypatch.setattr(tmux_transport,"send_text_to_pane",type_text)
    answer=post(rig,shown)
    assert answer.status_code == 409, answer.text
    assert rig.sent and not any(row.get("submit") for row in rig.sent)

@pytest.mark.parametrize("change", ["respawn", "retarget"])
def test_wait_keeps_its_original_process_proof_and_a_replacement_gets_no_keys(rig, change):
    rig.event(); shown=rig.shown()
    if change == "respawn": rig.fingerprint="replacement-process"
    else:
        rig.pane="%9"; rig.event(pane="%9")
    current=rig.shown()
    assert current["expected_pane_id"] == shown["expected_pane_id"] == "%3"
    assert current["expected_pane_fingerprint"] == shown["expected_pane_fingerprint"] == "original-process"
    answer=post(rig,shown,keys=["Escape"])
    assert answer.status_code == 409, answer.text
    assert rig.sent == []


def permission(rig, screen):
    rig.screen=screen
    rig.event("Claude needs permission to use Bash", permission=True)
    verdict=screen_rules.read_screen("claude",screen)
    assert verdict is not None
    screen_watch.STORE.observe("claude:review9b",agent="claude",target="%3",verdict=verdict,screen=screen,title="",
                               now=datetime.now(timezone.utc), identity={"pane_id":"%3", "fingerprint":rig.fingerprint})
    return rig.shown()


def test_a_permission_suffix_has_no_producer_certificate_and_cannot_be_allowed(rig):
    screen="\n".join(["Bash command", *[f"echo part-{n}" for n in range(20)], "Do you want to proceed?", "1. Yes", "2. No"])
    reading=screen_rules.prompt_reading(screen)
    assert reading.get("command") and reading.get("command_complete") is False
    shown=permission(rig,screen)
    answer=post(rig,shown,keys=["Enter"])
    assert answer.status_code == 409 and answer.json()["status"] == "command_incomplete", answer.text
    assert rig.sent == []
    denied=post(rig,shown,keys=["Escape"])
    assert denied.status_code == 200, denied.text


def test_a_certified_permission_and_an_unchanged_question_keep_the_working_paths(rig):
    rig.event(); answer=post(rig,rig.shown())
    assert answer.status_code == 200, answer.text
    rig.sent.clear()
    shown=permission(rig,COMPLETE_SCREEN)
    answer=post(rig,shown,keys=["Enter"])
    assert answer.status_code == 200, answer.text
    assert rig.sent == [{"pane":"%3", "keys":[("named","Enter")]}]


def test_an_earlier_prompt_does_not_become_current_again_when_its_words_return(rig):
    rig.event(); earlier=rig.shown()
    rig.event("Who signs the release?"); rig.event()
    assert rig.shown()["wait_id"] == earlier["wait_id"]
    answer=post(rig,earlier)
    assert answer.status_code == 409 and answer.json()["status"] == "wait_not_current", answer.text
    assert rig.sent == []


def test_a_command_changed_after_the_watcher_read_is_refused_before_permission_keys(rig):
    shown=permission(rig,COMPLETE_SCREEN)
    rig.screen=COMPLETE_SCREEN.replace("rm -rf build/ && make release", "echo another-command")
    answer=post(rig,shown,keys=["Enter"])
    assert answer.status_code == 409 and answer.json()["status"] == "wait_not_current", answer.text
    assert rig.sent == []


def test_a_permission_screen_that_arrived_before_its_hook_gets_no_typed_answer(rig):
    rig.event(); shown=rig.shown()
    rig.screen="Bash command\necho hello\nDo you want to proceed?\n1. Yes\n2. No"
    answer=post(rig,shown)
    assert answer.status_code == 409 and answer.json()["status"] == "wait_not_current", answer.text
    assert rig.sent == []


def test_a_header_looking_line_inside_a_command_is_not_an_opening_boundary():
    reading=screen_rules.prompt_reading("   hidden prefix\n   Bash command\n   echo suffix\n Do you want to proceed?")
    assert reading["command"] and reading["command_complete"] is False


def test_an_agent_gets_no_owner_wait_proof_and_cannot_answer_with_a_copied_proof(rig):
    rig.event(); binding=rig.shown()
    rig.principal=Principal(PrincipalKind.AGENT,"untrusted-agent")
    row=rig.client.get("/api/coders/sessions").json()["sessions"][0]["session"]
    assert not {"wait_revision","wait_pane_id","wait_pane_fingerprint","expected_pane_fingerprint"}.intersection(row)
    answer=post(rig,binding)
    assert answer.status_code == 403, answer.text
    assert rig.sent == []


def test_a_prompt_changed_during_the_final_screen_read_gets_no_keys(rig, monkeypatch):
    rig.event(); shown=rig.shown()
    def read_then_change(*args, **kwargs):
        rig.event("Who signs the release?")
        return "", ""
    monkeypatch.setattr(screen_watch,"capture",read_then_change)
    answer=post(rig,shown,keys=["Escape"])
    assert answer.status_code == 409 and answer.json()["status"] == "wait_not_current", answer.text
    assert rig.sent == []
