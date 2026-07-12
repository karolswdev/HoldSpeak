"""HSM-14 — the iPad desk's GitHub-issue connector, grounded in the host actuators.

A companion proposes filing a desk card as a GitHub issue; the host refuses
honestly when no repo is configured/empty text; the payload is {repo, title,
body}; nothing is filed before approval; approving runs the Phase-38
`gh issue create` connector (the subprocess faked via the route's runner seam)
and returns the issue URL; the github decision route is target-scoped; and the
companion status reports `github_configured`. Auth is the host's local `gh` —
no token is stored or crosses (there is no credential to leak here).
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

import holdspeak.config as config_module  # noqa: E402
import holdspeak.web.routes.actuator_shared as actuator_shared  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import get_database, reset_database  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402

REPO = "acme/app"
ISSUE_URL = "https://github.com/acme/app/issues/42"
PROPOSE = "/api/desk/actuators/github/propose"


class _FakeGh:
    """A stand-in for subprocess.run that records argv and returns a CompletedProcess."""

    def __init__(self, *, returncode=0, stdout=ISSUE_URL, stderr=""):
        self.calls: list[list[str]] = []
        self._rc, self._out, self._err = returncode, stdout, stderr

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(argv, returncode=self._rc, stdout=self._out, stderr=self._err)


@pytest.fixture
def temp_db_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_dir):
    reset_database()
    return get_database(temp_db_dir / "test.db")


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    Config().save(path=target)
    return target


def _configure(settings_path, repo=REPO):
    config = Config.load()
    config.meeting.companion_github_repo = repo
    config.save(path=settings_path)


def _set_control_mode(settings_path, mode):
    config = Config.load()
    config.control_mode = mode
    config.save(path=settings_path)


@pytest.fixture
def server():
    return MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_a, **_k: None, on_stop=lambda *_a, **_k: None, get_state=lambda: None),
        host="127.0.0.1",
    )


@pytest.fixture
def client(server, settings_path) -> TestClient:
    return TestClient(server.app)


@pytest.fixture
def gh(monkeypatch):
    """Inject the fake `gh` runner the route's GitHub connector uses."""
    fake = _FakeGh()
    monkeypatch.setattr(actuator_shared, "_GITHUB_RUNNER", fake)
    return fake


def _decide(client, pid, decision, by="karol"):
    return client.post(f"/api/desk/actuators/github/{pid}/decision", json={"decision": decision, "decided_by": by})


@pytest.mark.integration
def test_no_repo_refuses_with_400(client, db):
    res = client.post(PROPOSE, json={"text": "ship it"})
    assert res.status_code == 400
    assert "repo" in res.json()["error"].lower()


@pytest.mark.integration
def test_empty_text_refuses_with_400(client, db, settings_path):
    _configure(settings_path)
    assert client.post(PROPOSE, json={"text": "  "}).status_code == 400


@pytest.mark.integration
def test_propose_carries_repo_title_body(client, db, settings_path):
    _configure(settings_path)
    proposal = client.post(PROPOSE, json={"text": "the body", "title": "Wire onboarding"}).json()["proposal"]
    assert proposal["status"] == "proposed"
    assert proposal["target"] == "github"
    assert proposal["action"] == "create_issue"
    assert proposal["payload"] == {"repo": REPO, "title": "Wire onboarding", "body": "the body"}
    assert REPO in proposal["preview"]


@pytest.mark.integration
def test_request_repo_overrides_host_and_names_it_in_the_preview(client, db, settings_path):
    # The iPad can target a repo per send; a request `repo` wins over the host's
    # and is the one threaded into the payload + preview.
    _configure(settings_path, repo="host/default")
    proposal = client.post(
        PROPOSE, json={"text": "the body", "title": "Ship", "repo": "other/repo"}
    ).json()["proposal"]
    assert proposal["payload"]["repo"] == "other/repo"
    assert "other/repo" in proposal["preview"]
    assert "host/default" not in proposal["preview"]


@pytest.mark.integration
def test_request_repo_with_no_host_configured(client, db):
    # No host repo at all, but the iPad passes a valid one: it proposes.
    proposal = client.post(
        PROPOSE, json={"text": "ship it", "repo": "acme/app"}
    ).json()["proposal"]
    assert proposal["payload"]["repo"] == "acme/app"
    assert "acme/app" in proposal["preview"]


@pytest.mark.integration
@pytest.mark.parametrize("bad", ["not-a-repo", "owner/", "/name", "a/b/c", "bad repo/x", "owner/na me"])
def test_malformed_request_repo_refuses_with_400(client, db, bad):
    res = client.post(PROPOSE, json={"text": "ship it", "repo": bad})
    assert res.status_code == 400, bad
    assert "owner/name" in res.json()["error"].lower()


@pytest.mark.integration
def test_a_proposed_issue_files_nothing(client, db, settings_path, gh):
    _configure(settings_path)
    client.post(PROPOSE, json={"text": "ship it"})
    assert gh.calls == []                          # proposing never shells out


@pytest.mark.integration
def test_approval_files_the_issue_and_returns_the_url(client, db, settings_path, gh):
    _configure(settings_path)
    proposal = client.post(PROPOSE, json={"text": "the body", "title": "Wire onboarding"}).json()["proposal"]
    final = _decide(client, proposal["id"], "approved").json()["proposal"]
    assert final["status"] == "executed"
    assert final["result"]["url"] == ISSUE_URL
    # exactly one `gh issue create`, argv carries repo/title/body, no shell
    assert len(gh.calls) == 1
    argv = gh.calls[0]
    assert argv[:3] == ["gh", "issue", "create"]
    assert REPO in argv and "Wire onboarding" in argv and "the body" in argv


@pytest.mark.integration
def test_yolo_files_to_the_registered_repo_without_a_decision(
    client, db, settings_path, gh
):
    _configure(settings_path)
    _set_control_mode(settings_path, "yolo")
    proposal = client.post(
        PROPOSE,
        json={"text": "the body", "title": "Wire onboarding"},
    ).json()["proposal"]
    assert proposal["status"] == "executed"
    assert proposal["policy_snapshot"]["authority_basis"] == "control_posture"
    assert len(gh.calls) == 1


@pytest.mark.integration
def test_yolo_refuses_an_unregistered_repo_without_filing_or_prompting(
    client, db, settings_path, gh
):
    _configure(settings_path, repo="host/default")
    _set_control_mode(settings_path, "yolo")
    proposal = client.post(
        PROPOSE,
        json={"text": "the body", "title": "Ship", "repo": "other/repo"},
    ).json()["proposal"]
    assert proposal["status"] == "proposed"
    assert proposal["policy_snapshot"]["outcome"] == "refused"
    assert proposal["policy_snapshot"]["reason_code"] == "registered_destination_required"
    assert gh.calls == []
    assert client.get("/api/mesh/inbox").json()["counts"]["pending_approvals"] == 0
    decision = _decide(client, proposal["id"], "approved")
    assert decision.status_code == 400
    assert "refuses" in decision.json()["error"]


@pytest.mark.integration
def test_rejection_files_nothing(client, db, settings_path, gh):
    _configure(settings_path)
    pid = client.post(PROPOSE, json={"text": "ship it"}).json()["proposal"]["id"]
    assert _decide(client, pid, "rejected").json()["proposal"]["status"] == "rejected"
    assert gh.calls == []


@pytest.mark.integration
def test_github_decision_is_target_scoped(client, db, settings_path, gh):
    _configure(settings_path)
    pid = client.post(PROPOSE, json={"text": "ship it"}).json()["proposal"]["id"]
    # a github proposal cannot be decided on the slack or webhook routes
    assert client.post(f"/api/desk/actuators/slack/{pid}/decision", json={"decision": "approved"}).status_code == 404
    assert client.post(f"/api/desk/actuators/webhook/{pid}/decision", json={"decision": "approved"}).status_code == 404


@pytest.mark.integration
def test_companion_status_reports_github_configured(client, db, settings_path):
    assert client.get("/api/desk/actuators/status").json()["github_configured"] is False
    _configure(settings_path)
    assert client.get("/api/desk/actuators/status").json()["github_configured"] is True
