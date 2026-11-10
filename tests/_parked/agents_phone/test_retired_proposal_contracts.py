# PARKED: desk proposals now need an owner decision; repository registration has an owner MCP tool.
from __future__ import annotations
import pytest


# From tests/integration/test_web_companion_github.py
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


# From tests/integration/test_web_companion_webhook.py
@pytest.mark.integration
def test_yolo_executes_the_configured_webhook_without_a_decision(
    client, db, settings_path, posts, broadcasts
):
    _configure(settings_path)
    _set_control_mode(settings_path, "yolo")
    proposal = client.post(PROPOSE, json={"text": "the brief"}).json()["proposal"]
    assert proposal["status"] == "executed"
    assert proposal["policy_snapshot"]["authority_basis"] == "control_posture"
    assert proposal["policy_snapshot"]["mode"] == "yolo"
    assert len(posts) == 1
    assert posts[0][1] == {"text": proposal["preview"]}


# From tests/unit/test_project_repository.py
def test_the_descriptor_is_owner_only_http_only_and_admitted() -> None:
    from holdspeak.agent_operations import PROJECT_REPOSITORY_REGISTER as op
    from holdspeak.kernel.project import OWNER_ONLY_OPERATIONS, REPOSITORY_ADMITTED

    assert op.owner_only and op.owner_press and op.admission.rule == "admitted" and op.admission.enforced
    assert op.exposure == ("http:POST /api/projects/{project_id}/repository",)
    assert REPOSITORY_ADMITTED == {"project.repository.register", "project.repository.clone"}
    assert REPOSITORY_ADMITTED <= OWNER_ONLY_OPERATIONS
