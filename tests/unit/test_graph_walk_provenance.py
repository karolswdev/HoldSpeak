"""The graph-walk rig (scripts/graph_walk.py): source provenance, the engine
replay, the CLI meeting-intelligence queue, and integer facts.

Moved from tests/unit/test_philo11_walk_harness.py by the fast diet
(2026-10-12); its tests of the Phase 11 proof programs (rig_run.py, retain.py,
red_main.sh under pm/roadmap) are parked in tests/_parked/unit/.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest



REPO = Path(__file__).resolve().parents[2]


def test_graph_walk_can_be_told_the_revision_of_an_extracted_archive(monkeypatch) -> None:
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import graph_walk

    monkeypatch.setenv("HOLDSPEAK_SOURCE_REVISION", "332d91586bdbd7fe40e3c2c00851a46adc4650e4")
    monkeypatch.setenv("HOLDSPEAK_SOURCE_DIRTY", "true")
    provenance = graph_walk.base_provenance(engine_mode="none")
    assert provenance["revision"].startswith("332d9158")
    assert provenance["revision_source"] == "environment"
    assert provenance["dirty"] is True


def test_graph_walk_provenance_names_git_when_no_revision_override(monkeypatch) -> None:
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import graph_walk

    monkeypatch.delenv("HOLDSPEAK_SOURCE_REVISION", raising=False)
    monkeypatch.delenv("HOLDSPEAK_SOURCE_DIRTY", raising=False)
    provenance = graph_walk.base_provenance(engine_mode="none")
    assert provenance["revision_source"] == "git"
    assert provenance["revision"]


def test_engine_replay_serves_model_discovery_on_loopback(tmp_path: Path) -> None:
    import sys
    import urllib.request

    sys.path.insert(0, str(REPO / "scripts"))
    import graph_walk
    import holdspeak.intel.engine as engine_module
    import holdspeak.intel.providers as providers_module
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.services.model_library_service import ModelLibraryApplicationService

    reply_path = tmp_path / "engine-reply.json"
    reply_path.write_text(json.dumps({"provider": "recorded", "model": "p11-model", "raw_text": "recorded decision",
                                     "capabilities": ["meeting.plugin.decision_capture"]}))
    old_engine = engine_module.MeetingIntel
    old_configured = providers_module._configured_engine
    old_profile_body = ModelLibraryApplicationService._profile_body
    draft = {"provider_family": "openai_compatible", "profile_id": "recorded", "expected_profile_revision": 0,
             "label": "Recorded", "model": "p11-model"}
    claim = "result_schema:" + process_inference_capability_registry().require(
        "meeting.plugin.decision_capture").output_schema_sha256
    # PHILO-15 10 (Astra r1, finding 5): the production profile claims the
    # plugin schemas itself now (the plugin result is checked by the closed
    # semantic adapter); the harness patch must still leave the claim in.
    assert claim in old_profile_body(draft)["capability_manifest"]["claims"]
    try:
        digest, provider_url = graph_walk._install_engine_replay(reply_path)
        with urllib.request.urlopen(f"{provider_url}/models", timeout=2) as response:
            payload = json.loads(response.read())
        assert digest
        assert provider_url.startswith("http://127.0.0.1:")
        assert payload["data"] == [{"id": "p11-model", "owned_by": "graph-walk-replay"}]
        from holdspeak.services.agent_turn_service import AgentTurnService
        recorded_engine = providers_module._configured_engine()
        assert AgentTurnService.dispatch_plugin(SimpleNamespace(_engine=recorded_engine),
            [{"role": "user", "content": "Extract the decision"}], temperature=0.2,
            max_tokens=800, plugin_id="decision_capture") == "recorded decision"
        assert recorded_engine.calls == ["_chat_completion_text"]
        assert claim in ModelLibraryApplicationService._profile_body(draft)["capability_manifest"]["claims"]
    finally:
        engine_module.MeetingIntel = old_engine
        providers_module._configured_engine = old_configured
        ModelLibraryApplicationService._profile_body = staticmethod(old_profile_body)


def test_cli_queue_meeting_intelligence_uses_the_real_db_producer(tmp_path: Path) -> None:
    """The rig queues a real imported meeting through IntelRepository."""
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import graph_walk
    from holdspeak.db import Database
    from holdspeak.db.intel import _durable_transcript_hash
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    home = tmp_path / "hub-home"
    db_path = home / ".holdspeak" / "holdspeak.db"
    db_path.parent.mkdir(parents=True)
    database = Database(db_path)
    database.meetings.save_meeting(
        MeetingState(
            id="imported-meeting",
            started_at=datetime.now(),
            segments=[TranscriptSegment("durable imported words", "Me", 0.0, 2.0)],
            provenance="import",
        )
    )
    with database._connection() as conn:
        durable_hash = _durable_transcript_hash(conn, "imported-meeting")
    database.close()

    provenance = {"fixture_hashes": {}}
    record = graph_walk.run_step(
        {
            "kind": "cli",
            "action": "queue_meeting_intelligence",
            "meeting_id": "imported-meeting",
            "adapter": "db-producer",
        },
        page=None,
        hub=SimpleNamespace(home=home, db_path=str(db_path)),
        provenance=provenance,
        variables={},
    )

    assert record["producer"] == "holdspeak.db.intel.IntelRepository.enqueue_intel_job"
    assert record["db_path"] == str(db_path.resolve())
    assert record["transcript_hash"] == durable_hash
    assert record["planned_route"] is None
    assert record["job_id"]
    assert provenance["meeting_intelligence"] == [record]

    database = Database(db_path)
    with database._connection() as conn:
        row = conn.execute(
            "SELECT meeting_id,status,transcript_hash FROM intel_jobs WHERE job_id=?",
            (record["job_id"],),
        ).fetchone()
    database.close()
    assert row is not None
    assert tuple(row) == ("imported-meeting", "queued", durable_hash)


def test_cli_queue_meeting_intelligence_refuses_owner_or_missing_meeting(tmp_path: Path) -> None:
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import graph_walk

    home = tmp_path / "hub-home"
    db_path = home / ".holdspeak" / "holdspeak.db"
    db_path.parent.mkdir(parents=True)
    owner_db = tmp_path / "owner.sqlite"

    with pytest.raises(graph_walk.Blocked, match="no imported meeting"):
        graph_walk.run_step(
            {"kind": "cli", "action": "queue_meeting_intelligence", "meeting_id": "absent"},
            page=None,
            hub=SimpleNamespace(home=home, db_path=str(db_path)),
            provenance={"fixture_hashes": {}},
            variables={},
        )

    with pytest.raises(graph_walk.Blocked, match="outside the isolated hub HOME"):
        graph_walk.run_step(
            {"kind": "cli", "action": "queue_meeting_intelligence", "meeting_id": "absent"},
            page=None,
            hub=SimpleNamespace(home=home, db_path=str(owner_db)),
            provenance={"fixture_hashes": {}},
            variables={},
        )


@pytest.mark.parametrize("value,want,expected", [
    (39000, 39000, True), (39000.0, 39000, False),
    ("39000", 39000, False), (True, 1, False), (False, 0, False),
])
def test_integer_facts_check_the_json_type_not_only_equality(value, want, expected) -> None:
    """The same numeric value as a float or boolean is not an integer field."""
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import graph_walk

    predicate = {"kind": "op_facts", "facts": [
        {"source": "trigger", "path": "limit", "value": want, "integer": True},
    ]}
    after = {"operation_trigger": {"response": {"limit": value}}}
    assert graph_walk.check_predicate(predicate, {}, after)[0] is expected
