"""PHILO-9-06 fences for the closing-use driver (``scripts/philo9_room_job.py``).

Every input is a real producer's output: the Phase 5 rehearsal's retained
Codex logs (the zero-read fence's red), and this story's retained rehearsal
(Codex's own event logs and rollouts, the hub's recorded exchanges, the
readbacks through the contract). The reds are those records themselves and
deliberate mutations of copies of them.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("philo9_room_job", REPO / "scripts/philo9_room_job.py")
assert SPEC and SPEC.loader
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)

PHASE5_RUN = REPO / (
    "pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/"
    "final/20260925T001407Z-his-words-real"
)
STORY = REPO / "pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract"
SHOTS = STORY / "assets/story-06-shots"
#: Rehearsal one: its own audit refused the agent sessions' pairing (the
#: Codex ``status: failed`` defect) and it found the two catalogue gaps.
FIRST = SHOTS / "attempts/20260928T164015Z-room-job"
#: Rehearsal two, after the gaps were paid: completed, no blocker.
SECOND = SHOTS / "attempts/20260928T165409Z-room-job"
#: The FINAL closing run on merged main (PHILO-9-03's face): four sessions and the face.
RUN = SHOTS / "final/20260928T172621Z-room-job"


def _events(stage_dir: Path) -> list[dict[str, Any]]:
    return driver.read_events(stage_dir / "events.jsonl")


def _copy_run(tmp_path: Path) -> Path:
    target = tmp_path / RUN.name
    shutil.copytree(RUN, target, ignore=shutil.ignore_patterns("*.sqlite", "rehearsal-transcript.jsonl"))
    return target


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


# ── the zero-read fence (the Phase 7 implementation, one copy) ───────────


def test_the_driver_uses_the_phase7_fences_unchanged() -> None:
    assert driver.zero_read_findings is driver.p7.zero_read_findings
    assert driver.account_leak_findings is driver.p7.account_leak_findings


@pytest.mark.parametrize(("stage", "count"), [("decision_thought", 25), ("import", 3)])
def test_the_zero_read_fence_fails_on_the_phase5_logs(stage: str, count: int) -> None:
    findings = driver.zero_read_findings(_events(PHASE5_RUN / "codex" / stage))
    assert len(findings) == count
    assert {f["type"] for f in findings} == {"command_execution"}


@pytest.mark.parametrize("stage", driver.SESSIONS)
def test_every_retained_session_has_zero_reads_and_used_the_catalogue(stage: str) -> None:
    events = _events(RUN / "codex" / stage)
    assert driver.zero_read_findings(events) == []
    audit = _json(RUN / "codex" / stage / "mcp-audit.json")
    assert audit["chosen_tools"], f"{stage}: no holdspeak tool was called"
    assert audit["unlisted_tools"] == []
    assert audit["initial_context_findings"] == []


def test_every_client_call_pairs_with_one_hub_exchange_from_the_retained_records() -> None:
    """Re-paired from the retained events and transcript: the rehearsal's own
    audit refused the two agent sessions before the Codex ``status: failed``
    repair (``scripts/philo5_his_words.py`` ``_codex_mcp_calls``)."""
    repaired = driver.repair_findings(RUN)
    for stage in driver.SESSIONS:
        assert repaired[f"pairing {stage}"] == [], stage
    assert driver.repair_findings(FIRST)["pairing agent_ungranted"] == []
    retained = _json(FIRST / "codex" / "agent_ungranted" / "mcp-audit.json")
    assert "project.run_steward" in str(retained["reconciliation_error"])
    assert _json(RUN / "codex" / "agent_ungranted" / "mcp-audit.json")["reconciliation_error"] is None


def test_a_refused_call_without_the_failed_status_does_not_pair(tmp_path: Path) -> None:
    """Codex records a server ``isError: true`` answer as ``status: failed``;
    read as a success, the refused call pairs with no server row."""
    run = _copy_run(tmp_path)
    shutil.copy2(RUN / "rehearsal-transcript.jsonl", run / "rehearsal-transcript.jsonl")
    events = run / "codex" / "agent_ungranted" / "events.jsonl"
    rows = driver.read_events(events)
    for row in rows:
        if (row.get("item") or {}).get("status") == "failed":
            row["item"]["status"] = "completed"
    events.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert driver.repair_findings(run)["pairing agent_ungranted"]


def test_a_shell_command_in_a_retained_session_turns_the_fence_red() -> None:
    events = copy.deepcopy(_events(RUN / "codex" / "owner_job"))
    call = next(e for e in events if e.get("type") == "item.completed"
                and (e.get("item") or {}).get("type") == "mcp_tool_call")
    call["item"] = {"id": "x", "type": "command_execution", "command": "cat README.md"}
    assert len(driver.zero_read_findings(events)) == 1


# ── the redaction and the leak fence (law XXX-12) ────────────────────────


def test_no_retained_story06_record_holds_an_email_or_a_token() -> None:
    assert driver.account_leak_findings(SHOTS) == []


@pytest.mark.parametrize("planted", [
    "someone.real@example.org",
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV",
    "Authorization: Bearer abcdefghijklmnopqrstuvwx",
])
def test_the_leak_fence_turns_red_on_a_planted_value(tmp_path: Path, planted: str) -> None:
    target = tmp_path / "run" / "rollout.jsonl"
    target.parent.mkdir()
    target.write_text((RUN / "codex" / "owner_job" / "rollout.jsonl").read_text()
                      + json.dumps({"planted": planted}) + "\n")
    assert driver.account_leak_findings(tmp_path / "run")


def test_the_redaction_at_capture_removes_a_planted_address(tmp_path: Path) -> None:
    run = _copy_run(tmp_path)
    path = run / "codex" / "owner_job" / "last.md"
    path.write_text(path.read_text() + "\nsent by someone.real@example.org\n")
    assert driver.account_leak_findings(run)
    driver.redact_run(run)
    assert driver.account_leak_findings(run) == []


# ── the fixture was fixed before the run ─────────────────────────────────


def test_the_fixture_was_in_the_run_before_the_first_session() -> None:
    assert driver.fixture_before_run_findings(RUN) == []
    record = _json(RUN / "fixture.json")
    assert record["fixture"]["project"] == "Payments ledger cutover"
    assert record["fixture"]["delivery"]["delivered_to"] == ["Priya", "Tomas"]


def test_a_fixture_written_after_the_first_session_is_red(tmp_path: Path) -> None:
    run = _copy_run(tmp_path)
    record = _json(run / "fixture.json")
    record["written_at"] = _json(run / "codex" / "owner_job" / "timing.json")["finished_at"]
    (run / "fixture.json").write_text(json.dumps(record))
    assert any("not before the first session" in f for f in driver.fixture_before_run_findings(run))


def test_a_changed_fixture_value_or_changed_words_are_red(tmp_path: Path) -> None:
    run = _copy_run(tmp_path)
    record = _json(run / "fixture.json")
    record["fixture"]["delivery"]["delivered_to"] = ["Tomas", "Priya"]
    (run / "fixture.json").write_text(json.dumps(record))
    (run / "codex" / "owner_find" / "owner-prompt.txt").write_text("Find project proj-1234abcd.\n")
    findings = driver.fixture_before_run_findings(run)
    assert any("values differ" in f for f in findings)
    assert any("owner_find: the words sent" in f for f in findings)


def test_the_story_fixture_words_are_ordinary() -> None:
    for stage, words in driver.load_fixture()["prompts"].items():
        assert driver.prompt_findings(words) == [], stage


# ── the sessions are isolated: fresh roots, distinct ids, no resume ──────


def test_the_retained_sessions_are_isolated() -> None:
    assert driver.session_isolation_findings(RUN) == []
    ids = [_json(RUN / "codex" / s / "mcp-audit.json")["session_id"] for s in driver.SESSIONS]
    assert len(set(ids)) == len(driver.SESSIONS)


@pytest.mark.parametrize("mutation", ["same_session", "resumed", "shared_home", "user_config"])
def test_each_isolation_mutation_is_red(tmp_path: Path, mutation: str) -> None:
    run = _copy_run(tmp_path)
    stage = run / "codex" / "owner_find"
    if mutation == "same_session":
        audit = _json(stage / "mcp-audit.json")
        audit["session_id"] = _json(run / "codex" / "owner_job" / "mcp-audit.json")["session_id"]
        (stage / "mcp-audit.json").write_text(json.dumps(audit))
    elif mutation == "resumed":
        (stage / "command.txt").write_text((stage / "command.txt").read_text().replace(
            "codex exec ", "codex exec resume 0199 "))
    elif mutation == "shared_home":
        env = _json(stage / "environment.json")
        env["env"]["HOME"] = _json(run / "codex" / "owner_job" / "environment.json")["env"]["HOME"]
        (stage / "environment.json").write_text(json.dumps(env))
    else:
        (stage / "command.txt").write_text((stage / "command.txt").read_text().replace(
            " --ignore-user-config", ""))
    assert driver.session_isolation_findings(run)


# ── the content checks compare the fixture's values ──────────────────────


def _owner_back() -> dict[str, Any]:
    return _json(RUN / "owner_job" / "readbacks.json")


def test_the_owner_job_reads_back_every_fixture_value() -> None:
    fixture = _json(RUN / "fixture.json")["fixture"]
    back = _owner_back()
    assert driver.owner_job_findings(fixture, back["readbacks"]) == []
    assert driver.owner_receipt_findings(back["receipts"]) == []


@pytest.mark.parametrize("mutation", ["order", "due", "body", "impact", "second_run_effect"])
def test_each_content_mutation_is_red(mutation: str) -> None:
    fixture = _json(RUN / "fixture.json")["fixture"]
    back = copy.deepcopy(_owner_back()["readbacks"])
    update = next(u for u in back["updates"] if u["lifecycle"] == "published")
    if mutation == "order":
        update["deliveries"].reverse()
    elif mutation == "due":
        fixture["milestone"]["due_at"] = fixture["run_date"]
    elif mutation == "body":
        update["body_md"] = update["body_md"].replace("Old ledger freeze slips", "a risk")
    elif mutation == "impact":
        risk = next(i for i in back["items"] if i["item_type"] == "risk")
        risk["details_json"] = risk["details_json"].replace('"high"', '"low"')
    else:
        effects = back["steward_run"]["run"]["summary"]["phase_results"]["act"]["effect_receipts"]
        effects.append({"effect_kind": "create_door_item", "outcome": "applied"})
    assert driver.owner_job_findings(fixture, back)


def test_a_missing_or_extra_owner_write_is_red() -> None:
    receipts = _owner_back()["receipts"]
    marks = [r for r in receipts if r["operation"]["name"] == "project.mark_update_delivered"]
    assert len(marks) == 2
    assert driver.owner_receipt_findings([r for r in receipts if r is not marks[0]])
    assert driver.owner_receipt_findings(receipts + [marks[0]])


def test_the_agent_leg_refused_then_ran_inside_the_bound() -> None:
    fixture = _json(RUN / "fixture.json")["fixture"]
    grant = _json(RUN / "agent" / "grant.json")
    identity = fixture["agent"]["identity"]
    ungranted = _json(RUN / "agent_ungranted" / "readbacks.json")["receipts"]
    granted = _json(RUN / "agent_granted" / "readbacks.json")["receipts"]
    assert driver.agent_findings("ungranted", ungranted, identity=identity, fixture=fixture, grant_id=None) == []
    assert driver.agent_findings("granted", granted, identity=identity, fixture=fixture,
                                 grant_id=grant["response"]["grant_id"]) == []
    # The same receipts against the wrong phase or grant are red.
    assert driver.agent_findings("granted", ungranted, identity=identity, fixture=fixture,
                                 grant_id=grant["response"]["grant_id"])
    assert driver.agent_findings("granted", granted, identity=identity, fixture=fixture, grant_id="pdg_other")


def test_find_it_cold_took_project_list_after_the_discovery_repair() -> None:
    """Rehearsal one took memory.search (it never returns a project); after
    project.list named "find a project by its name", rehearsal two took it."""
    assert _json(FIRST / "codex" / "owner_find" / "mcp-audit.json")["chosen_tools"][0] == "memory.search"
    assert _json(RUN / "codex" / "owner_find" / "mcp-audit.json")["chosen_tools"][0] == "project.list"


def test_the_agent_heard_owner_only_for_mark_delivered_after_the_repair() -> None:
    fixture = _json(RUN / "fixture.json")["fixture"]
    for label in ("ungranted", "granted"):
        receipts = _json(RUN / f"agent_{label}" / "readbacks.json")["receipts"]
        marks = [r["receipt"]["outcome"] for r in receipts if r["operation"]["name"] == "project.mark_update_delivered"]
        assert marks == [fixture["agent"]["owner_only_code"]] == ["owner_principal_required"], label
    first = _json(FIRST / "agent_granted" / "readbacks.json")["receipts"]
    assert [r["receipt"]["outcome"] for r in first
            if r["operation"]["name"] == "project.mark_update_delivered"] == ["project_delegation_required"]


def test_the_final_run_is_complete_and_labelled_for_the_owners_review() -> None:
    status = _json(RUN / "run-status.json")
    assert status["outcome"] == "completed" and status["blocked"] == []
    assert status["label"] == "REHEARSED; OWNER REVIEW PENDING"
    assert status["face"]["room_shots"] and status["face"]["grant_shots"]
    assert "FACE LEG PENDING" in str(_json(SECOND / "run-status.json")["face"])


# ── the face: the Room and the grant row after the job, as rendered ──────


def _room_face() -> dict[str, Any]:
    return _json(RUN / "observations" / "room.json")


@pytest.mark.parametrize("width", ["1440", "393"])
def test_the_room_face_shows_every_fixture_value_at_both_widths(width: str) -> None:
    fixture = _json(RUN / "fixture.json")["fixture"]
    face = _room_face()["widths"][width]
    # ITEMS: the recapture with the seen-in-the-unobscured-viewport collector
    # (Codex Astra r1 on #687); the first capture's 393 items shot was the head.
    reshoot = _json(RUN / "observations" / "room-items-reshoot.json")["widths"][width]
    assert reshoot["findings"] == [] and reshoot["items"]["rows_total"] == len(reshoot["items"]["seen_on"]) == 2
    facts = {**face["facts"], "items": reshoot["items"]}
    assert driver.face_findings(fixture, facts, {"receipts": face["hub_room_receipts"]}) == []
    receipts = face["facts"]["receipts"]["receipts"]
    assert any("STEWARD RUN" in r and "REFUSED NO GRANT" in r for r in receipts), receipts
    assert any("MARK DELIVERED" in r and "REFUSED OWNER ONLY" in r for r in receipts), receipts
    assert [p for run in face["facts"]["steward_runs"] for p in run["plan"] if "Act" in p] == ["✓ Act 1 effect"] * 2


@pytest.mark.parametrize("mutation", ["late_words", "one_delivery", "no_refusal", "risk_impact", "small_text",
                                      "risk_row_unseen"])
def test_each_face_mutation_is_red(mutation: str) -> None:
    fixture = _json(RUN / "fixture.json")["fixture"]
    face = copy.deepcopy(_room_face()["widths"]["393"])
    facts = face["facts"]
    facts["items"] = _json(RUN / "observations" / "room-items-reshoot.json")["widths"]["393"]["items"]
    if mutation == "late_words":
        facts["room"]["needs_you_why"] = ["OVERDUE · 3 DAYS"]
    elif mutation == "one_delivery":
        facts["update"]["delivery_rows"] = facts["update"]["delivery_rows"][:1]
    elif mutation == "no_refusal":
        facts["receipts"]["receipts"] = [r for r in facts["receipts"]["receipts"] if "REFUSED" not in r]
    elif mutation == "risk_impact":
        facts["items"]["item_rows"] = [r.replace("IMPACT HIGH", "IMPACT LOW") for r in facts["items"]["item_rows"]]
    elif mutation == "risk_row_unseen":
        facts["items"]["seen_on"] = {"0": facts["items"]["seen_on"]["0"]}
        facts["items"]["item_rows"] = facts["items"]["item_rows"][:1]
    else:
        facts["room"]["small_text"] = ["10 px"]
    assert driver.face_findings(fixture, facts, {"receipts": face["hub_room_receipts"]})


def test_the_grant_row_keeps_stop_on_the_archived_project_and_its_receipt() -> None:
    grant = _json(RUN / "observations" / "grant.json")
    assert grant["findings"] == [] and grant["archive"]["status"] == 200
    for width in ("1440", "393"):
        archived = grant["widths"][width]["archived"]
        assert archived["archived_token"] == "ARCHIVED" and "ALLOWED" in archived["chip"]
        assert archived["verb"] == "Stop run and publish"
    assert "SUCCEEDED" in grant["widths"]["1440"]["stopped"]["well"]
    assert grant["widths"]["393"]["stopped"]["line_present"] is False
    receipt = grant["stop_receipt"]["objects"][0]
    assert (receipt["operation"]["name"], receipt["receipt"]["state"]) == ("project.delegation.revoke", "succeeded")


def test_every_face_shot_is_retained() -> None:
    names = {p.name for p in (RUN / "shots").glob("*.png")}
    for stem in ("room-head", "room-items-1", "room-receipts-1", "updates-list", "update-delivered", "steward-run-1",
                 "steward-run-2", "grant-archived-live"):
        for width in (1440, 393):
            assert f"{stem}-{width}.png" in names, (stem, width)
    assert {"grant-stopped-receipt-1440.png", "grant-stopped-after-393.png"} <= names


def test_the_superseded_393_items_shot_was_the_head_shot() -> None:
    """Codex Astra r1 on #687: the first capture's 393 ITEMS shot is byte-identical
    to the head shot (parked under shots/superseded/); the recapture is not."""
    shots = RUN / "shots"
    assert (shots / "superseded" / "room-items-393.png").read_bytes() == (shots / "room-head-393.png").read_bytes()
    assert (shots / "room-items-1-393.png").read_bytes() != (shots / "room-head-393.png").read_bytes()
