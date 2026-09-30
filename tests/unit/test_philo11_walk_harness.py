"""PHILO-11-06 fences for the serial atlas conductor and its retention.

These tests exercise the harness' own evidence law with small observations;
they do not run an atlas batch.  The live runner remains one graph-walk
invocation per case, with the parent orchestrator owning the actual walks.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.unit._philo11_proof_inputs import load_proof_module, read_proof_script


REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def rig():
    return load_proof_module("rig_run.py")


@pytest.fixture(scope="module")
def retain_module():
    return load_proof_module("retain.py")


def _observation(case: str, width: int = 1440, *, revision: str = "332d91586b", dirty: bool = True,
                 home: Path | None = None) -> dict:
    home = home or Path("/tmp/philo11-hub-home")
    return {
        "case_id": case,
        "brain": "astra",
        "viewport": width,
        "verdict": "pass",
        "complete": True,
        "provenance": {
            "revision": revision,
            "dirty": dirty,
            "hub": {"home": str(home)},
            "db_path": str(home / ".holdspeak" / "holdspeak.db"),
        },
    }


def _write_run(src: Path, case: str = "case.p11.doc.sent.op", width: str = "op", *,
               revision: str = "332d91586b", dirty: bool = True) -> str:
    run_id = "20260930T000000Z-case-astra-1440"
    relative = f"{case}--{width}/{run_id}"
    path = src / relative
    path.mkdir(parents=True)
    home = Path("/tmp/philo11-hub-home")
    (path / "observation.json").write_text(
        json.dumps(_observation(case, 1440, revision=revision, dirty=dirty, home=home))
    )
    (path / "rig.log").write_text("VERDICT: pass\n")
    return relative


def _write_table(src: Path, relative: str, *, verdict: str = "pass", revision: str = "332d91586b",
                 dirty: str = "true") -> None:
    row = ["atlas-phase11.json", "case.p11.doc.sent.op", "op", verdict, "0.1", "0.2",
           "terminal settled", relative, "0", revision, dirty]
    header = [
        "file", "case", "width", "verdict", "seconds", "load1", "reading", "run_dir",
        "exit_code", "source_revision", "source_dirty",
    ]
    (src / "runs.tsv").write_text("\n".join("\t".join(line) for line in (header, row)) + "\n")


def test_plan_expands_face_widths_and_headless_operations_in_file_order(rig, tmp_path: Path) -> None:
    atlas = tmp_path / "atlas.json"
    atlas.write_text(json.dumps({"cases": [
        {"id": "face", "viewports": [1440, 393]},
        {"id": "op", "viewports": [], "setup": [{"kind": "boundary", "substitute": "engine_reply"}]},
    ]}))
    rig.ROOT = tmp_path
    runs = rig.plan(["atlas.json"])
    assert [(run.case, run.width_label, run.headless) for run in runs] == [
        ("face", "1440", False), ("face", "393", False), ("op", "op", True)
    ]
    assert [run.replayed for run in runs] == [False, False, True]


def test_reading_is_one_physical_tsv_line(rig) -> None:
    reading = rig._reading({"notes": ["predicate:\nselector\twith\nnewlines"]}, "")
    assert reading == "predicate: selector with newlines"
    assert "\n" not in reading and "\r" not in reading and "\t" not in reading


def test_observation_validation_requires_the_declared_source_provenance(rig, tmp_path: Path) -> None:
    label = tmp_path / "label"
    label.mkdir()
    relative = _write_run(label)
    row = ["atlas-phase11.json", "case.p11.doc.sent.op", "op", "pass", "0.1", "0.2",
           "terminal settled", relative, "0", "332d91586b", "true"]
    with pytest.raises(rig.HarnessError, match="source revision"):
        rig._observation_for(label, row, expected_revision="3552be416c", expected_dirty=True, brain="astra")


def test_observation_validation_rejects_a_db_outside_the_hub_home(rig, tmp_path: Path) -> None:
    label = tmp_path / "label"
    label.mkdir()
    relative = _write_run(label)
    observation_path = label / relative / "observation.json"
    data = json.loads(observation_path.read_text())
    data["provenance"]["db_path"] = "/tmp/owner-db.sqlite"
    observation_path.write_text(json.dumps(data))
    row = ["atlas-phase11.json", "case.p11.doc.sent.op", "op", "pass", "0.1", "0.2",
           "terminal settled", relative, "0", "332d91586b", "true"]
    with pytest.raises(rig.HarnessError, match="escapes hub HOME"):
        rig._observation_for(label, row, expected_revision="332d91586b", expected_dirty=True, brain="astra")


def test_not_applicable_observation_is_valid_before_a_hub_exists(rig, tmp_path: Path) -> None:
    label = tmp_path / "label"
    label.mkdir()
    relative = _write_run(label)
    observation_path = label / relative / "observation.json"
    data = json.loads(observation_path.read_text())
    data["verdict"] = "not_applicable"
    data["provenance"].pop("hub")
    data["provenance"].pop("db_path")
    observation_path.write_text(json.dumps(data))
    row = ["atlas-phase11.json", "case.p11.doc.sent.op", "op", "not_applicable", "0.1", "0.2",
           "not applicable", relative, "0", "332d91586b", "true"]
    observation, run_dir = rig._observation_for(
        label, row, expected_revision="332d91586b", expected_dirty=True, brain="astra"
    )
    assert observation["verdict"] == "not_applicable" and run_dir == relative


def test_retention_keeps_every_serial_run_and_refuses_reuse(retain_module, tmp_path: Path) -> None:
    src = tmp_path / "source"
    src.mkdir()
    relative = _write_run(src)
    _write_table(src, relative)
    dest = tmp_path / "kept"
    assert retain_module.retain(src, dest) == 1
    assert (dest / relative / "observation.json").is_file()
    with pytest.raises(retain_module.Refused, match="already exists"):
        retain_module.retain(src, dest)


def test_retention_refuses_a_table_that_does_not_name_the_observation(retain_module, tmp_path: Path) -> None:
    src = tmp_path / "source"
    src.mkdir()
    relative = _write_run(src)
    _write_table(src, relative.replace("case.p11.doc.sent.op", "case.p11.other"))
    with pytest.raises(retain_module.Refused, match="another case"):
        retain_module.retain(src, tmp_path / "kept")


def test_retention_refuses_a_multiline_tsv_row_instead_of_merging_it(retain_module, tmp_path: Path) -> None:
    src = tmp_path / "source"
    src.mkdir()
    relative = _write_run(src)
    _write_table(src, relative)
    (src / "runs.tsv").write_text((src / "runs.tsv").read_text().replace("terminal settled", "terminal\nsettled"))
    with pytest.raises(retain_module.Refused, match="row has"):
        retain_module.retain(src, tmp_path / "kept")


def test_archive_red_script_uses_archive_revision_and_astra(rig) -> None:
    script = read_proof_script("red_main.sh")
    assert "git archive \"$REV\"" in script
    assert "--source-revision \"$REV\"" in script
    assert "--source-dirty true" in script
    assert "--brain astra" in script


def test_graph_walk_can_be_told_the_revision_of_an_extracted_archive(monkeypatch) -> None:
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import graph_walk

    monkeypatch.setenv("HOLDSPEAK_SOURCE_REVISION", "332d91586bdbd7fe40e3c2c00851a46adc4650e4")
    monkeypatch.setenv("HOLDSPEAK_SOURCE_DIRTY", "true")
    provenance = graph_walk.base_provenance(engine_mode="none")
    assert provenance["revision"].startswith("332d9158")
    assert provenance["dirty"] is True


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
    assert claim not in old_profile_body(draft)["capability_manifest"]["claims"]
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
