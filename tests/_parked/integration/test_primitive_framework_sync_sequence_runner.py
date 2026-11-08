"""Parked 2026-11-08 from tests/integration/test_primitive_framework_sync.py: the tests of the parked Sequence/Workflow runner
(holdspeak/services/_parked/sequence_workflow_service.py). Kept, not collected.
"""
"""The Primitive Framework — the LIVE cross-surface sync loop, end-to-end.

Wave 2 proved sync with per-router unit fakes. This proves the loop against the
REAL ASGI app (`MeetingWebServer._create_app`, the same factory production runs):
the CRUD primitives router and the sync router are wired together over ONE real
tmp-path Database, and the exact wire shapes the two authoring surfaces emit
round-trip and reconcile in that single store.

The two surfaces, on the same hub:

- **Web** authors with the CRUD verbs (`POST /api/notes`, `POST /api/recipes`,
  `POST /api/kbs`, ...). The hub stamps `last_modified`/`created_at`.
- **iPad** authors by pushing a `ChangeSet` (`POST /api/sync/push`) — per kind a
  list of ``{meta:{id, kind, last_modified, deleted}, value}`` records with
  snake_case `value` payloads (the Phase-0 contract coder's wire shape).

Both must show up in `GET /api/sync/pull` AND through the CRUD `GET` routes, and
the LWW + tombstone rules must hold across the surfaces. The `value` field sets on
the wire are asserted byte-for-byte against THE_PRIMITIVE_FRAMEWORK.md — that
exact-key agreement IS the cross-surface contract.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.requires_meeting]

from holdspeak.db import Database, get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


# ── The canonical snake_case `value` field sets (THE_PRIMITIVE_FRAMEWORK.md) ──
# These are the cross-surface agreement: every surface's `value` payload on the
# wire MUST carry exactly these keys. (The hub `to_dict` adds `updated_at` to the
# note value as a device-local stamp; it is not part of the agreement, so we
# compare the contract keys as a subset where the hub is the emitter and assert
# the contract keys exactly where the test controls the payload.)
NOTE_KEYS = {"id", "title", "body_markdown", "tags",
             "created_at", "updated_at", "last_modified", "deleted"}
AGENT_KEYS = {"id", "name", "avatar", "role", "system_prompt", "user_template",
              "tools", "kb_id", "profile_id", "kind", "created_at", "last_modified", "deleted",
    "manual_context", "use_zone_context",  # v7 (Phase 77): the pinned context rides the wire
    "kind",  # Phase 153: ordinary recipes and thread modes share this record.
}
KB_KEYS = {"id", "name", "member_ids", "created_at", "last_modified", "deleted"}
META_KEYS = {"id", "kind", "last_modified", "deleted"}


@pytest.fixture


def test_ipad_synced_graph_workflow_runs_on_the_hub(env, monkeypatch) -> None:
    """The whole Phase-22 loop over the real app: the SWIFT-ENCODED golden
    fixture (`blueprint-linear-sample.json`, the iPad Blueprint encoder's exact
    bytes) rides `/api/sync/push` as a workflow's `graph_json`, then
    `/api/workflows/{id}/run` executes the synced graph — threaded node order,
    the per-node provenance surfaced in the steps, the run-born artifact minted.
    Authored on one surface, synced, run on the hub: the graph travels."""
    db, client = env

    fixtures = (Path(__file__).resolve().parents[2]
                / "pm" / "roadmap" / "holdspeak-mobile" / "contracts" / "fixtures")
    graph = json.loads((fixtures / "blueprint-linear-sample.json").read_text(encoding="utf-8"))

    lm = "2030-06-26T12:00:00Z"
    push = client.post("/api/sync/push", json={"workflows": [{
        "meta": {"id": "wf-golden", "kind": "workflow", "last_modified": lm, "deleted": False},
        "value": {"name": graph["name"], "prompt": "fallback: {input}", "graph_json": graph},
    }]})
    assert push.status_code == 200
    assert push.json()["received"]["workflows"] == 1

    created = client.post("/api/inference-targets", json={
        "id": "sync-ready", "name": "Sync ready", "kind": "openAICompatible",
        "base_url": "http://127.0.0.1:9999/v1", "model": "sync-test", "requires_key": False,
    })
    assert created.status_code == 201, created.text
    deployment_revision = __import__("holdspeak.deployment_revisions", fromlist=["capture_deployment_revision"]).capture_deployment_revision(
        db, __import__("holdspeak.inference_targets", fromlist=["resolve_inference_target"]).resolve_inference_target(db, "sync-ready")
    )
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    InferenceAssignmentService(db).set_assignment(
        Principal(PrincipalKind.OWNER, "owner-session"),
        {
            "command_id": "sync-workflow-route", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "workflow.node"},
            "entries": [{"profile_id": "legacy-sync-ready"}],
        },
    )
    calls = []

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            calls.append(user_prompt)
            return f"risk: finding {len(calls)}\nnoise line"

    constructed = []
    def _build_fake(**kwargs):
        constructed.append(kwargs)
        return _FakeIntel()
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", _build_fake)

    resp = client.post("/api/workflows/wf-golden/run", json={"input": "the standup"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # The graph ran (never the prompt fallback): llm → extract → keep_if in the
    # fixture's exec order, with the iPad-authored provenance on the steps.
    assert "warning" not in body
    assert [s["node_id"] for s in body["steps"]] == ["ask", "dec", "keep"]
    assert [s["kind"] for s in body["steps"]] == ["llm", "extract", "keep_if"]
    by_id = {s["node_id"]: s for s in body["steps"]}
    assert by_id["ask"]["failure_policy"] == "carry"
    assert by_id["ask"]["status"] == "ok"
    assert by_id["ask"]["runs_on"] == "endpoint"
    assert by_id["dec"]["failure_policy"] == "skip"
    assert by_id["dec"]["runs_on"] == "onDevice"

    # Two model ops fired; keep_if (pure) kept only the risk line of the last output.
    assert len(calls) == 2
    assert body["output"] == "risk: finding 2"

    # The run persisted as a run-born artifact with the workflow as its lineage.
    assert body["artifact_id"]
    assert [row["source_type"] for row in body["sources"]] == ["workflow"]
    assert body["operation"] == "workflow.run"
    assert body["result_ref"] == f"artifact:{body['artifact_id']}"
    assert len(body["children"]) == 2
    assert all(child["outcome"] == "succeeded" for child in body["children"])
    assert constructed and constructed[0]["profile_id"] == "sync-ready"
    assert deployment_revision.id in [row.id for row in db.deployment_revisions.list()]
