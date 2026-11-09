"""PARKED 20261109 (ops/settings): tests of routes no client called, parked with them.

POST /api/inference-targets (web/routes/primitives/_parked/profiles_20261109.py); POST
/api/providers/github/validate-repo, /jira/search, /jira/validate-scope, /confluence/validate
(web/routes/_parked/providers_unreached_20261109.py).
Not collected. Kept for history.
"""
from __future__ import annotations


# From tests/unit/test_inference_targets.py:
def test_target_api_rejects_secret_fields(rig) -> None:
    _, client = rig
    response = client.post(
        "/api/inference-targets",
        json={
            "name": "Nope",
            "kind": "external_service",
            "api_key": "sk-secret",
        },
    )
    assert response.status_code == 400
    assert "sk-secret" not in response.text




# From tests/integration/test_provider_routes.py:
# ── POST /api/providers/github/validate-repo ─────────────────────────


class TestGitHubValidateRepo:
    def test_valid_repo(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post(
            "/api/providers/github/validate-repo",
            json={"owner_repo": "acme/platform"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_missing_owner_repo_400(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post(
            "/api/providers/github/validate-repo",
            json={},
        )
        assert resp.status_code == 400
        assert "owner_repo" in resp.json()["message"]

    def test_invalid_format(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post(
            "/api/providers/github/validate-repo",
            json={"owner_repo": "no-slash"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False




    def test_search_roundtrip(self, jira_discovery_rig) -> None:
        _, client, _, _ = jira_discovery_rig
        ref = "alpha.atlassian.net|user@example.com"
        resp = client.post(
            "/api/providers/jira/search",
            json={"connection_ref": ref, "jql": "project = KAN"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "ready"
        assert len(body["items"]) >= 1
        item = body["items"][0]
        assert "key" in item
        assert "summary" in item
        assert "url" in item


    def test_search_missing_fields_400(self, jira_discovery_rig) -> None:
        _, client, _, _ = jira_discovery_rig
        resp = client.post(
            "/api/providers/jira/search",
            json={"connection_ref": "alpha.atlassian.net|user@example.com"},
        )
        assert resp.status_code == 400


    def test_validate_scope_valid(self, jira_discovery_rig) -> None:
        _, client, _, _ = jira_discovery_rig
        ref = "alpha.atlassian.net|user@example.com"
        resp = client.post(
            "/api/providers/jira/validate-scope",
            json={"connection_ref": ref, "project_key": "KAN"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["project"]["key"] == "KAN"
        assert len(body["issue_types"]) >= 1


    def test_validate_scope_missing_fields_400(self, jira_discovery_rig) -> None:
        _, client, _, _ = jira_discovery_rig
        resp = client.post(
            "/api/providers/jira/validate-scope",
            json={"connection_ref": "alpha.atlassian.net|user@example.com"},
        )
        assert resp.status_code == 400



    def test_search_parity(self, jira_discovery_rig) -> None:
        """HTTP search == adapter.search."""
        _, client, _, jira_adapter = jira_discovery_rig
        ref = "alpha.atlassian.net|user@example.com"

        http_resp = client.post(
            "/api/providers/jira/search",
            json={"connection_ref": ref, "jql": "project = KAN"},
        )
        http_body = http_resp.json()

        mcp_body = jira_adapter.search(OWNER, ref, jql="project = KAN")

        assert http_body["state"] == mcp_body["state"]
        assert http_body["connection_ref"] == mcp_body["connection_ref"]
        assert len(http_body["items"]) == len(mcp_body["items"])


    def test_validate_scope_parity(self, jira_discovery_rig) -> None:
        """HTTP validate-scope == adapter.validate_scope."""
        _, client, _, jira_adapter = jira_discovery_rig
        ref = "alpha.atlassian.net|user@example.com"

        http_resp = client.post(
            "/api/providers/jira/validate-scope",
            json={"connection_ref": ref, "project_key": "KAN"},
        )
        http_body = http_resp.json()

        mcp_body = jira_adapter.validate_scope(OWNER, ref, "KAN")

        assert http_body["valid"] == mcp_body["valid"]
        assert http_body["connection_ref"] == mcp_body["connection_ref"]
        if http_body["valid"]:
            assert http_body["project"]["key"] == mcp_body["project"]["key"]

