"""PHILO-10-06 fences for the closing-use driver (``scripts/philo10_send_job.py``).

Every input is a real producer's output: the retained FINAL run (the two real
sends: Codex's own event logs and rollouts, the hub's recorded exchanges, the
readbacks through the contract, the independent read-backs), the retained
rehearsal, and the tracked exactly-once ledger. The reds are deliberate
mutations of copies of them. Nothing here sends, boots a hub or reads the
network.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("philo10_send_job", REPO / "scripts/philo10_send_job.py")
assert SPEC and SPEC.loader
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)

STORY = REPO / "pm/roadmap/holdspeak-philo/phase-10-the-channels"
SHOTS = STORY / "assets/story-06-shots"
#: The FINAL run: the two real sends (folder + issue 699), both sessions, the face.
RUN = SHOTS / "final/20260929T184651Z-send-job-real"
LEDGER = STORY / "assets/story-06-real-sends.json"


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _fixture() -> dict[str, Any]:
    return driver.load_fixture()


def _copy_run(tmp_path: Path) -> Path:
    target = tmp_path / RUN.name
    shutil.copytree(RUN, target, ignore=shutil.ignore_patterns("*.sqlite", "rehearsal-transcript.jsonl", "*.png"))
    return target


# ── the driver reuses the Phase 7 fences (one implementation) ────────────


def test_the_driver_uses_the_phase7_fences_unchanged() -> None:
    assert driver.zero_read_findings is driver.p7.zero_read_findings
    assert driver.account_leak_findings is driver.p7.account_leak_findings
    assert driver.redact_run is driver.p7.redact_run


# ── exactly one send per target (the guard, three independent reads) ─────


def test_the_guard_passes_a_target_with_no_send(tmp_path: Path) -> None:
    folder = tmp_path / "HoldSpeak"
    folder.mkdir()
    (folder / "other.md").write_text("another file\n")
    found = driver.exactly_once_findings(_fixture(), ledger=tmp_path / "none.json", folder=folder,
                                         comments=lambda: [{"body": "a comment", "html_url": "u"}])
    assert found == []


def test_the_guard_refuses_a_target_the_ledger_names(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    driver.record_real_press(ledger, {"target": "github", "pressed_at": "2026-09-29T00:00:00+00:00"})
    fixture = _fixture()
    assert driver.exactly_once_findings(fixture, ledger=ledger, folder=tmp_path, targets=("file",)) == []
    found = driver.exactly_once_findings(fixture, ledger=ledger, folder=tmp_path, targets=("github",))
    assert len(found) == 1 and found[0].startswith("github: the ledger records a real send")


def test_the_guard_refuses_a_folder_that_holds_the_bytes(tmp_path: Path) -> None:
    (tmp_path / "2026-09-29-harbor-cutover-r1-abcdef12.md").write_bytes(driver.body_bytes(_fixture()))
    found = driver.exactly_once_findings(_fixture(), ledger=tmp_path / "none.json", folder=tmp_path)
    assert len(found) == 1 and "already holds the fixture's bytes" in found[0]


def test_the_guard_refuses_an_issue_that_carries_the_marker(tmp_path: Path) -> None:
    fixture = _fixture()
    comments = [{"body": "hello", "html_url": "a"}, {"body": f"x\n{fixture['marker']}\n", "html_url": "b"}]
    found = driver.exactly_once_findings(fixture, ledger=tmp_path / "none.json", folder=tmp_path,
                                         comments=lambda: comments)
    assert found == ["github: b already carries the fixture's marker"]


def test_the_tracked_ledger_names_both_real_sends_with_the_final_runs_proofs() -> None:
    ledger = _json(LEDGER)["sends"]
    assert [e["target"] for e in ledger] == ["file", "github"]
    legs = _json(RUN / "legs.json")
    for entry in ledger:
        assert entry["run"] == RUN.name
        assert entry["state"] == "sent"
        assert entry["proof"] == legs["press"][entry["target"]]["send"]["proof"]


def test_a_second_real_run_refuses_before_anything_boots(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The tracked ledger alone refuses: no hub, no gh, no session, no run directory."""
    code = driver.main(["run", "--real", "--out", str(tmp_path)])
    printed = capsys.readouterr().out
    assert code == 4, printed
    assert "REFUSED file: the ledger records a real send" in printed
    assert "REFUSED github: the ledger records a real send" in printed
    assert list(tmp_path.iterdir()) == []
    assert driver.main(["guard"]) == 4


# ── the final run: sessions, receipts, content, read-backs ────────────────


@pytest.mark.parametrize("stage", driver.SESSIONS)
def test_every_retained_session_has_zero_reads_and_used_the_catalogue(stage: str) -> None:
    events = driver.read_events(RUN / "codex" / stage / "events.jsonl")
    assert driver.zero_read_findings(events) == []
    audit = _json(RUN / "codex" / stage / "mcp-audit.json")
    assert audit["chosen_tools"], f"{stage}: no holdspeak tool was called"
    assert audit["unlisted_tools"] == []
    assert audit["initial_context_findings"] == []
    assert audit["leg"] == "agent"


def test_the_sessions_are_isolated_and_the_fixture_came_first() -> None:
    assert driver.session_isolation_findings(RUN) == []
    assert driver.fixture_before_run_findings(RUN) == []


def test_the_agent_prepared_both_and_its_send_was_refused_with_a_receipt() -> None:
    prepare = _json(RUN / "agent_prepare" / "readbacks.json")
    seeded = _json(RUN / "seed.json")
    fixture = _fixture()
    assert driver.agent_receipt_findings(fixture, prepare["receipts"]) == []
    assert driver.prepare_findings(fixture, seeded, prepare["sends"], prepare["previews"]) == []
    refused = [r for r in prepare["receipts"] if r["operation"]["name"] == "channel.send"]
    assert refused and all((r["receipt"]["state"], r["receipt"]["outcome"]) == ("refused", "owner_principal_required")
                           for r in refused)


def test_the_owners_press_sent_both_and_the_far_side_reads_back_the_frozen_bytes() -> None:
    legs = _json(RUN / "legs.json")
    fixture = _fixture()
    digest = hashlib.sha256(driver.body_bytes(fixture)).hexdigest()
    assert set(legs["press"]) == {"file", "github"}
    for key, press in legs["press"].items():
        assert driver.owner_press_findings(fixture, key, press["send"], press["receipt"], press["operation"]) == []
        assert driver.readback_findings(key, legs["readback"][key], True) == []
        assert press["send"]["payload_digest"] == digest
    assert legs["readback"]["file"]["sha256"] == digest
    assert legs["readback"]["github"]["login"] == fixture["destinations"]["github"]["login"]
    assert legs["readback"]["github"]["url_equals_proof"] is True


def test_the_retained_run_holds_no_account_data_or_gh_credential() -> None:
    assert driver.account_leak_findings(RUN) == []
    assert driver.gh_credential_findings(RUN) == []
    assert _json(RUN / "gh-login-file.json")["delete"]["exists_after"] is False


def test_the_face_showed_prepared_then_sent_at_both_widths() -> None:
    legs = _json(RUN / "legs.json")
    fixture = _fixture()
    sends = {k: v["send"] for k, v in legs["press"].items()}
    assert driver.prepared_face_findings(fixture, legs["face_prepared"]) == []
    assert driver.sent_face_findings(fixture, legs["face_sent"], sends) == []
    for shot in legs["face_prepared"]["shots"] + legs["face_sent"]["shots"]:
        assert (RUN / shot).is_file(), shot


# ── the reds: mutations of copies of the real records ─────────────────────


def test_an_agent_send_that_succeeded_is_red(tmp_path: Path) -> None:
    prepare = _json(RUN / "agent_prepare" / "readbacks.json")
    receipts = copy.deepcopy(prepare["receipts"])
    for r in receipts:
        if r["operation"]["name"] == "channel.send":
            r["receipt"]["state"], r["receipt"]["outcome"] = "succeeded", "succeeded"
    found = driver.agent_receipt_findings(_fixture(), receipts)
    assert any("was not refused owner_principal_required" in x for x in found), found


def test_a_send_prepared_by_the_owner_is_red() -> None:
    prepare = _json(RUN / "agent_prepare" / "readbacks.json")
    sends = copy.deepcopy(prepare["sends"])
    sends[0]["prepared_by"] = {"kind": "owner", "identity": "local-owner"}
    found = driver.prepare_findings(_fixture(), _json(RUN / "seed.json"), sends, prepare["previews"])
    assert any("not the agent" in x for x in found), found


def test_a_file_that_does_not_read_back_is_red() -> None:
    back = dict(_json(RUN / "legs.json")["readback"]["file"], bytes_equal_frozen=False)
    assert driver.readback_findings("file", back, True)


def test_a_planted_gh_token_is_red(tmp_path: Path) -> None:
    run = _copy_run(tmp_path)
    (run / "hub.log").write_text("token gho_" + "A" * 36 + "\n")
    assert [f["file"] for f in driver.gh_credential_findings(run)] == ["hub.log"]


def test_a_fixture_written_after_the_first_session_is_red(tmp_path: Path) -> None:
    run = _copy_run(tmp_path)
    record = _json(run / "fixture.json")
    record["written_at"] = "2099-01-01T00:00:00+00:00"
    (run / "fixture.json").write_text(json.dumps(record))
    found = driver.fixture_before_run_findings(run)
    assert any("not before the first session" in x for x in found), found


def test_a_resumed_or_shared_session_is_red(tmp_path: Path) -> None:
    run = _copy_run(tmp_path)
    audit = _json(run / "codex" / "agent_check" / "mcp-audit.json")
    first = _json(run / "codex" / "agent_prepare" / "mcp-audit.json")
    audit["session_id"] = first["session_id"]
    (run / "codex" / "agent_check" / "mcp-audit.json").write_text(json.dumps(audit))
    assert any("session_id shared" in x for x in driver.session_isolation_findings(run))
