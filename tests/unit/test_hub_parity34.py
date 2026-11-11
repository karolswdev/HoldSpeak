"""Owner library removal, credential custody, test send and encrypted restore."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from holdspeak import operations
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from holdspeak.services.errors import ServiceError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import _boot, destination  # noqa: E402

OWNER = Principal(PrincipalKind.OWNER, "parity-owner")
AGENT = Principal(PrincipalKind.AGENT, "parity-agent")


@pytest.fixture
def hub(tmp_path, monkeypatch):
    from holdspeak.db import reset_database
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _engine(hub):
    from test_model_profile_authority import _profile_body, _install_deployment
    from unittest.mock import patch
    service = hub.root.owner_service
    service.create_profile(OWNER, _profile_body(profile_id="parity-engine"))
    deployment, revision = _install_deployment(hub.db)
    with patch.object(service, "_observe_destination_readiness", return_value=("ready", "ready")):
        # The fixture probe names balanced-qwen; supply the actual profile id.
        from test_model_profile_authority import _probe_body
        probe = _probe_body(deployment, revision)
        probe["profile_id"] = "parity-engine"
        observation = service.probe_profile(OWNER, probe)["observation_id"]
    service.bind_profile(OWNER, {
        "binding_id": "parity-binding", "profile_id": "parity-engine", "profile_revision": 1,
        "deployment_head_id": deployment, "expected_binding_revision": 0,
        "expected_deployment_configuration_revision": 1, "expected_deployment_revision_id": revision,
        "enabled": True, "readiness_observation_id": observation,
    })
    return service.get_profile(OWNER, "parity-engine")


def test_remove_engine_releases_its_binding_but_keeps_history_and_assignments(hub):
    profile = _engine(hub)
    before = hub.root.model_library_service.assignment_heads(OWNER)
    response = hub.client.delete("/api/model-profiles/parity-engine", params={
        "expected_revision": profile["revision"],
        "expected_binding_revision": profile["current_binding"]["revision"],
    })
    assert response.status_code == 200, response.text
    assert response.json() == {"profile_id": "parity-engine", "deleted": True}
    assert hub.root.model_library_service.assignment_heads(OWNER) == before
    assert all(row["id"] != "profile:parity-engine" for row in hub.root.model_library_service.get_library(OWNER)["rows"])
    with hub.db._connection() as conn:
        assert conn.execute("SELECT 1 FROM model_profile_binding_revisions WHERE profile_id='parity-engine'").fetchone()
        assert not conn.execute("SELECT 1 FROM model_profile_binding_heads WHERE profile_id='parity-engine'").fetchone()


def test_used_engine_is_refused_without_reordering_assignment(hub):
    profile = _engine(hub)
    hub.root.inference_assignment_service.set_assignment(OWNER, {
        "command_id": "parity-assignment", "expected_revision": 0,
        "scope": {"kind": "global"}, "entries": [{"profile_id": "parity-engine"}],
    })
    before = hub.root.model_library_service.assignment_heads(OWNER)
    response = hub.client.delete("/api/model-profiles/parity-engine", params={
        "expected_revision": profile["revision"], "expected_binding_revision": profile["current_binding"]["revision"],
    })
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "model_profile_referenced"
    assert "assignment" in response.json()["error"].lower()
    assert hub.root.model_library_service.assignment_heads(OWNER) == before
    assert hub.root.owner_service.get_profile(OWNER, "parity-engine")["current_binding"] == profile["current_binding"]


def test_old_assignment_history_does_not_block_removing_unused_engine(hub):
    profile = _engine(hub)
    scope = {"kind": "capability", "capability_id": "ask.answer"}
    hub.root.inference_assignment_service.set_assignment(OWNER, {
        "command_id": "parity-old-assignment", "expected_revision": 0,
        "scope": scope, "entries": [{"profile_id": "parity-engine"}],
    })
    hub.root.inference_assignment_service.clear_assignment(OWNER, {
        "command_id": "parity-clear-assignment", "expected_revision": 1,
        "scope": scope, "capability_id": "ask.answer",
    })
    before = hub.root.model_library_service.assignment_heads(OWNER)
    response = hub.client.delete("/api/model-profiles/parity-engine", params={
        "expected_revision": profile["revision"], "expected_binding_revision": profile["current_binding"]["revision"],
    })
    assert response.status_code == 200, response.text
    assert hub.root.model_library_service.assignment_heads(OWNER) == before
    with hub.db._connection() as conn:
        assert conn.execute("SELECT 1 FROM inference_assignments WHERE profile_id='parity-engine'").fetchone()


@pytest.mark.parametrize("params", [{}, {"expected_revision": 1, "expected_binding_revision": 99}])
def test_engine_remove_requires_current_revisions(hub, params):
    _engine(hub)
    response = hub.client.delete("/api/model-profiles/parity-engine", params=params)
    assert response.status_code in {400, 409}
    assert hub.root.owner_service.get_profile(OWNER, "parity-engine")["current_binding"]


def test_send_test_has_normal_receipt_destination_history_and_replay(hub, tmp_path):
    dest = destination(hub, tmp_path / "sent")
    selected = hub.db.channel_destinations.get(dest)
    body = {"target_digest": selected["target_digest"], "command_id": "parity-test-send"}
    response = hub.client.post(f"/api/channels/destinations/{dest}/test", json=body)
    assert response.status_code == 200, response.text
    answer = response.json()
    assert answer["send"]["state"] == "sent"
    assert answer["send"]["destination_id"] == dest
    assert answer["send"]["destination_name"] == "Team folder"
    assert answer["receipt"]["outcome"] == "succeeded"
    assert "test message from HoldSpeak" in Path(answer["send"]["file_path"]).read_text()
    replay = hub.client.post(f"/api/channels/destinations/{dest}/test", json=body)
    assert replay.status_code == 200, replay.text
    assert replay.json()["send"]["id"] == answer["send"]["id"]
    assert len(list((tmp_path / "sent").iterdir())) == 1
    assert hub.db.channel_sends.get(answer["send"]["id"])["document_ref"] == f"delivery_test:{dest}"


@pytest.mark.parametrize("reap", [False, True])
def test_test_send_recovers_a_lost_receipt_without_dispatching_twice(hub, tmp_path, monkeypatch, reap):
    from _philo10_send import DispatchSpy, reap_past_deadline, ops
    from test_channel_send_recovery import _fail_the_settle_once
    dest = destination(hub, tmp_path / "sent")
    body = {"target_digest": hub.db.channel_destinations.get(dest)["target_digest"], "command_id": "lost-test"}
    spy = DispatchSpy(monkeypatch)
    _fail_the_settle_once(monkeypatch)
    path = f"/api/channels/destinations/{dest}/test"
    assert hub.client.post(path, json=body).status_code == 500
    if reap:
        hub.frames.clear()
        reap_past_deadline(hub)
    response = hub.client.post(path, json=body)
    assert response.status_code == 200, response.text
    assert response.json()["send"]["state"] == ("unknown" if reap else "sent")
    assert response.json()["receipt"]
    assert spy.calls == 1
    assert len(list((tmp_path / "sent").iterdir())) == 1
    assert len(ops(hub, "channel.send_test")) == 1
    if reap:
        assert any(kind == "desk_changed" and data.get("kind") == "channel" for kind, data in hub.frames)


@pytest.mark.parametrize("digest", [None, "stale-target"])
def test_send_test_refuses_missing_or_stale_target_without_dispatch(hub, tmp_path, digest):
    dest = destination(hub, tmp_path / "sent")
    body = {"command_id": "stale-test"}
    if digest is not None:
        body["target_digest"] = digest
    response = hub.client.post(f"/api/channels/destinations/{dest}/test", json=body)
    assert response.status_code in {400, 409}, response.text
    assert not list((tmp_path / "sent").iterdir())


def test_test_send_still_uses_credential_payload_fence(hub, tmp_path, monkeypatch):
    from holdspeak.services import document_sources
    from holdspeak.services.channel_contract import Document
    dest = destination(hub, tmp_path / "sent")
    monkeypatch.setattr(document_sources._DeliveryTestSource, "render", lambda *_: Document(
        ref=f"delivery_test:{dest}", title="Test", body_md="Authorization: Bearer sk-" + "a" * 48))
    response = hub.client.post(f"/api/channels/destinations/{dest}/test", json={
        "target_digest": hub.db.channel_destinations.get(dest)["target_digest"], "command_id": "credential-test",
    })
    assert response.status_code == 409, response.text
    assert not list((tmp_path / "sent").iterdir())


def _github(hub, monkeypatch, *, returncode=0):
    adapter = hub.root.github_provider
    # Persist the same producer used by a successful gh auth status check.
    adapter._persist_connection({"state": "connected", "display": {"account": "parity-owner"}})
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, returncode)
    monkeypatch.setattr(adapter, "_runner", run)
    return adapter, calls, hub.db.automations.get_provider_connection("wpc_github")


def test_remove_github_calls_credential_custodian_and_preserves_projects(hub, monkeypatch):
    _, calls, saved = _github(hub, monkeypatch)
    project = hub.client.post("/api/projects", json={"name": "Keep this Project"}).json()["project"]
    watch = hub.db.automations.create_watch(watch_id="parity-source", connector_id="gh",
        query_kind="pull_requests", name="Saved repository", query={"repository": "team/project"}, enabled=True)
    hub.db.automations.update_watch_spec(watch["id"], project_id=project["id"],
                                         provider_connection_id="wpc_github", state="active")
    body = {"connection_ref": "parity-owner", "expected_checked_at": saved["last_checked_at"], "command_id": "remove-github"}
    response = hub.client.request("DELETE", "/api/providers/github/connection", json=body)
    assert response.status_code == 200, response.text
    assert response.json() == {"removed": True, "provider": "github", "connection_ref": "parity-owner"}
    assert tuple(calls[0][0]) == ("gh", "auth", "logout", "--hostname", "github.com", "--user", "parity-owner")
    assert calls[0][1]["stdout"] == subprocess.DEVNULL
    assert hub.client.get(f"/api/projects/{project['id']}").status_code == 200
    row = hub.db.automations.get_provider_connection("wpc_github")
    assert row["state"] == "owner_action_required"
    assert row["last_error_detail"] == "Sign in again"
    from holdspeak.services.project_room_reads import _read_room_sources
    source = _read_room_sources(hub.db, project["id"])["items"][0]
    assert source["watchIds"] == [watch["id"]]
    assert source["state"] == "cant_check"
    assert source["plainReason"] == "Sign in again"
    from holdspeak.services.watch_service import WatchService
    def no_provider(*_args, **_kwargs):
        pytest.fail("A removed GitHub sign-in must not fetch with another CLI account")
    check = WatchService(hub.db, snapshot_fetcher=no_provider).test_watch(OWNER, watch["id"])
    assert check["test_state"] == "failed"
    assert check["result"]["error"]["message"] == "Sign in again"
    replay = hub.client.request("DELETE", "/api/providers/github/connection", json=body)
    assert replay.status_code == 200, replay.text
    assert len(calls) == 1
    assert not any(t["name"] == "provider.github_remove" for t in __import__("holdspeak.mcp.tools", fromlist=["TOOLS"]).TOOLS)


def test_github_removal_journals_in_its_adapters_database(hub, tmp_path):
    from holdspeak.db import Database
    from holdspeak.services.credential_service import CredentialService
    from holdspeak.services.github_provider import GitHubProviderAdapter
    from holdspeak.services.provider_service import ProviderService
    other = Database(tmp_path / "other-provider.db")
    def run(argv, **_kwargs):
        return subprocess.CompletedProcess(argv, 0)
    adapter = GitHubProviderAdapter(db=other, runner=run, credential_service=CredentialService(other))
    adapter._persist_connection({"state": "connected", "display": {"account": "parity-owner"}})
    registry = operations.bind_available({"provider_service": ProviderService(lambda _name: adapter)})
    saved = other.automations.get_provider_connection("wpc_github")
    registry.invoke(OWNER, "provider.github_remove", {
        "connection_ref": "parity-owner", "expected_checked_at": saved["last_checked_at"], "command_id": "separate-db",
    })
    with other._connection() as conn:
        assert conn.execute("SELECT 1 FROM kernel_operations WHERE name='provider.github_remove'").fetchone()
    with hub.db._connection() as conn:
        assert not conn.execute("SELECT 1 FROM kernel_operations WHERE name='provider.github_remove'").fetchone()
    from holdspeak.kernel.runtime import _configure
    _configure(hub.db)


def test_github_credential_failure_does_not_claim_removal_or_change_connection(hub, monkeypatch):
    _, calls, saved = _github(hub, monkeypatch, returncode=1)
    response = hub.client.request("DELETE", "/api/providers/github/connection", json={
        "connection_ref": "parity-owner", "expected_checked_at": saved["last_checked_at"], "command_id": "failed-remove",
    })
    assert response.status_code == 503, response.text
    assert hub.db.automations.get_provider_connection("wpc_github") == saved


def test_github_missing_or_stale_binding_never_calls_logout(hub, monkeypatch):
    _, calls, saved = _github(hub, monkeypatch)
    for body in ({}, {"connection_ref": "parity-owner", "expected_checked_at": "stale", "command_id": "stale-remove"}):
        response = hub.client.request("DELETE", "/api/providers/github/connection", json=body)
        assert response.status_code in {400, 409}, response.text
    assert not calls


def test_restore_person_retains_encrypted_notes_and_links(hub):
    people = hub.root.people_service
    people.setup(OWNER)
    person = people.create_relationship(OWNER, {"display_name": "Restore Person"})
    note = people.create_note(OWNER, person["id"], {"body": "Private architecture context"})
    people.link_project(OWNER, person["id"], "project-retained")
    people.archive_relationship(OWNER, person["id"])
    response = hub.client.post(f"/api/people/relationships/{person['id']}/restore", json={})
    assert response.status_code == 200, response.text
    restored = people.get_relationship(OWNER, person["id"])
    assert restored["state"] == "active"
    assert restored["project_refs"] == ["project-retained"]
    assert restored["notes"][0]["id"] == note["id"]
    assert restored["notes"][0]["body"] == "Private architecture context"


@pytest.mark.parametrize("name", ["settings.profile.delete", "provider.github_remove", "channel.send_test", "people.relationship.restore"])
def test_agent_cannot_call_owner_mutations_even_before_arguments(hub, name):
    with pytest.raises((operations.OperationRefused, ServiceError)) as refusal:
        hub.root.operations.invoke(AGENT, name, {})
    assert "owner" in refusal.value.code or "principal" in refusal.value.code
