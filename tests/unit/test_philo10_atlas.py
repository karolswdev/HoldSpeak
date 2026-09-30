"""PHILO-10-05: the atlas cases for Send (docs/internal/philo/graph/atlas-phase10.json).

The general fences of ``tests/unit/test_philo_graph_atlas.py`` read
``atlas.json`` by default (the Phase 8 law), so this file applies them to the
Phase 10 file itself, and fences what story 05 owns: one face case per Send
state at 1440 and 393, each reading its durable hub outcome in the SAME
observation (all_of: a face half and a hub half; no face-only proof), an
``.op`` sibling reading the kernel receipt where the outcome is durable, the
named transitions, the exclusions, the recording runner, the counts and the
evidence copier (every claimed run kept, keyed by case x width x run, reuse
refused). The verdicts are the rig's (``scripts/graph_walk.py run``), recorded
in the story's evidence.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.unit import test_philo_graph_atlas as general

REPO = Path(__file__).resolve().parents[2]
GRAPH = REPO / "docs/internal/philo/graph"
PHASE10 = GRAPH / "atlas-phase10.json"
PROOF = REPO / "pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof"
SHOTS = REPO / "pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-shots"

COUNTS = {
    "atlas.json": 85,
    "atlas-phase3.json": 36,
    "atlas-phase7.json": 27,
    "atlas-phase8.json": 19,
    "atlas-phase9.json": 13,
    "atlas-phase9-steward.json": 4,
    "atlas-phase10.json": 32,  # PHILO-10-07: five Resend face cases
    "atlas-phase11-slack.json": 4,  # PHILO-11-02/06: real hub, recorded Slack edge
    "atlas-phase11.json": 7,  # PHILO-11-06: seven durable document sources
}

# The charter's state/width matrix -> its face case (Manual is Phase 9's).
MATRIX = {
    "No destination saved": "case.p10.send.no_destination",
    "Destinations listed": "case.p10.send.destinations_listed",
    "Destination picked": "case.p10.send.destination_picked",
    "Sending": "case.p10.send.sending",
    "SENT": "case.p10.send.sent",
    "REFUSED": "case.p10.send.refused",
    "FAILED": "case.p10.send.failed",
    "UNKNOWN": "case.p10.send.unknown",
    "UNKNOWN after a restart": "case.p10.send.unknown_after_restart",
    "DESTINATION CHANGED": "case.p10.send.destination_changed",
    "PREPARED": "case.p10.send.prepared",
    "Several sends": "case.p10.send.several",
}

# The transitions the charter's exit 7 and the story name.
TRANSITIONS = {
    "restart during dispatching": "case.p10.send.unknown_after_restart",
    "replay of the same key": "case.p10.send.replay_same_key.op",
    "destination changed after prepare": "case.p10.send.destination_changed",
    "Send and Discard together": "case.p10.send.discard_after_send",
    "Send and Discard, the other order": "case.p10.send.send_after_discard.op",
    "receipts across away and back": "case.p10.send.receipt_after_return",
}

GENERAL = [
    general.test_every_case_state_id_resolves,
    general.test_every_case_reference_inside_the_atlas_resolves,
    general.test_every_clock_a_case_uses_is_declared,
    general.test_every_applicable_case_carries_one_trigger,
    general.test_face_cases_carry_both_ruled_viewports,
    general.test_every_applicable_predicate_is_a_kind_the_rig_implements,
    general.test_every_predicate_observes_a_selector_or_a_route,
    general.test_every_case_keeps_its_human_sentence,
    general.test_every_ui_action_is_one_the_rig_implements,
    general.test_every_boundary_names_its_substitution,
    general.test_no_precondition_check_compares_two_snapshots,
    general.test_every_precondition_check_observes_a_selector_or_a_route,
    general.test_no_check_asserts_the_result_the_trigger_must_produce,
    general.test_no_step_acts_on_a_root_placeholder,
    general.test_navigation_steps_carry_no_selector,
    general.test_every_desk_face_case_crosses_the_gate_first,
    general.test_every_captured_id_names_the_field_it_reads,
    general.test_ids_are_unique,
]


def _atlas() -> dict:
    return json.loads(PHASE10.read_text())


def _cases() -> dict[str, dict]:
    return {case["id"]: case for case in _atlas()["cases"]}


def _face(case: dict) -> bool:
    return case["trigger"]["kind"] == "ui"


def _parts(case: dict) -> list[dict]:
    predicate = case["expected"]["predicate"]
    return predicate["predicates"] if predicate["kind"] == "all_of" else [predicate]


@pytest.mark.parametrize("fence", GENERAL, ids=lambda f: f.__name__)
def test_the_general_fences_hold_for_the_phase10_file(fence) -> None:
    fence(_atlas())


def test_the_phase10_file_validates_against_the_schema() -> None:
    general.test_atlas_validates_against_its_schema(_atlas(), json.loads(general.SCHEMA_PATH.read_text()))


def test_every_api_step_exists_in_the_generated_openapi() -> None:
    general.test_every_api_setup_step_exists_in_the_generated_openapi(
        _atlas(), json.loads(general.OPENAPI_PATH.read_text()))


def test_the_counts_over_every_atlas_file() -> None:
    have = {path.name: len(json.loads(path.read_text())["cases"]) for path in general.ATLAS_FILES}
    assert have == COUNTS


def test_every_matrix_state_and_transition_has_its_case() -> None:
    cases = _cases()
    for label, cid in {**MATRIX, **TRANSITIONS}.items():
        assert cid in cases, (label, cid)
    for cid in MATRIX.values():
        assert _face(cases[cid]) and cases[cid]["viewports"] == [1440, 393], cid


def test_face_cases_run_at_both_widths_and_the_rest_headless() -> None:
    for cid, case in _cases().items():
        assert case["viewports"] == ([1440, 393] if _face(case) else []), cid
        assert cid.endswith(".op") != _face(case), cid


def test_every_face_case_reads_its_hub_outcome_in_the_same_observation() -> None:
    """No face-only proof: each face case is all_of a readable face half and a
    hub half (the hub's rows, the trigger's own answer, or the runner's count)."""
    for cid, case in _cases().items():
        if not _face(case):
            continue
        kinds = [p["kind"] for p in _parts(case)]
        assert case["expected"]["predicate"]["kind"] == "all_of", cid
        assert "readable_text" in kinds, cid
        assert "protocol_reads" in kinds, cid


def test_every_admitted_write_twin_reads_its_kernel_receipt_with_its_actor() -> None:
    for cid, case in _cases().items():
        if _face(case):
            continue
        text = json.dumps(case["expected"])
        assert "kernel.receipt.read" in text, cid
        assert '"objects.0.receipt.actor_kind", "value": "owner"' in text, cid
        assert '"objects.0.receipt.state"' in text, cid


def test_every_face_case_without_a_twin_is_excluded_with_a_reason() -> None:
    atlas = _atlas()
    excluded = " ".join(entry["combination"] for entry in atlas["excluded"])
    ids = set(_cases())
    for cid, case in _cases().items():
        if _face(case) and f"{cid}.op" not in ids:
            assert cid in excluded, cid


def test_the_pairs_read_the_same_values() -> None:
    """Each face case and its .op twin name the same outcome: the same state,
    reason or code, and the same destination kind."""
    cases = _cases()
    for cid, case in cases.items():
        twin = cases.get(f"{cid}.op")
        if not _face(case) or twin is None:
            continue
        face_text, twin_text = json.dumps(case["expected"]["predicate"]), json.dumps(twin)
        for token in ("sent", "failed", "unknown", "prepared", "refused", "destination_parked",
                      "send_already_settled", "github_target_not_found", "indeterminate"):
            if f'"{token}"' in face_text:
                assert f'"{token}"' in twin_text, (cid, token)
        uses_runner = any(s.get("substitute") == "cli_runner" for s in case["setup"])
        assert uses_runner == any(s.get("substitute") == "cli_runner" for s in twin["setup"]), cid
        if uses_runner:
            face_script = next(s["reply"] for s in case["setup"] if s.get("kind") == "boundary")
            assert face_script == next(s["reply"] for s in twin["setup"] if s.get("kind") == "boundary"), cid


def test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send() -> None:
    """Every case whose send reaches the recording runner counts its gh creates."""
    for cid, case in _cases().items():
        steps = case["setup"] + [case["trigger"]]
        runner = next((s for s in steps if s.get("substitute") == "cli_runner"), None)
        sends = any(s.get("name") == "channel.send" or "send-verb" in str(s.get("selector", "")) for s in steps)
        if runner and sends:
            counts = [p for p in _parts(case) if p["kind"] == "cli_calls"]
            https = json.loads((REPO / runner["reply"]).read_text()).get("https")
            prefix = ["https", "POST", "api.resend.com", "/emails"] if https else ["gh", "issue", "comment"]
            assert counts == [{"kind": "cli_calls", "argv_prefix": prefix, "count": 1}], cid


def test_every_email_case_boots_the_memory_key_store_before_a_key_is_saved() -> None:
    """PHILO-10-07: a case that saves an email key (face or route) declares the email edge,
    whose install replaces the key store with a memory one: the rig never reaches the OS keychain."""
    for cid, case in _cases().items():
        steps = case["setup"] + [case["trigger"]]
        saves_key = any("email-keys" in str(s.get("path", "")) or "dest-key-row" in str(s.get("selector", ""))
                        for s in steps)
        if saves_key:
            runner = next((s for s in steps if s.get("substitute") == "cli_runner"), None)
            assert runner and json.loads((REPO / runner["reply"]).read_text()).get("https"), cid


def test_the_email_edge_records_before_it_answers_and_never_the_key(tmp_path, monkeypatch) -> None:
    rig = _rig()
    import urllib.request

    from holdspeak.services import channel_email

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(channel_email, "HTTPS_HANDLER", channel_email.HTTPS_HANDLER)
    monkeypatch.setattr(channel_email, "KEY_STORE", channel_email.KEY_STORE)
    rig._install_cli_runner(REPO / "tests/fixtures/philo10_atlas/resend-accepted.json")
    assert isinstance(channel_email.KEY_STORE(), channel_email.MemoryEmailKeyStore)
    opener = urllib.request.OpenerDirector()
    opener.add_handler(channel_email.HTTPS_HANDLER())
    req = urllib.request.Request("https://api.resend.com/emails", data=b"{}", method="POST",
                                 headers={"Authorization": "Bearer re_secret_never_logged", "User-Agent": "HoldSpeak"})
    with opener.open(req) as answer:
        assert answer.status == 200 and json.loads(answer.read()) == {"id": "re-atlas-4ef9-0001"}
    text = (tmp_path / rig.CLI_CALLS_FILE).read_text()
    [entry] = [json.loads(line) for line in text.splitlines()]
    assert entry["argv"] == ["https", "POST", "api.resend.com", "/emails"]
    assert (entry["auth"], entry["user_agent"]) == ("Bearer", "HoldSpeak")
    assert "re_secret_never_logged" not in text


def test_every_runner_script_is_retained_and_answers_by_argv_prefix() -> None:
    scripts = {s["reply"] for c in _cases().values() for s in c["setup"] if s.get("substitute") == "cli_runner"}
    assert scripts == {f"tests/fixtures/philo10_atlas/{n}" for n in
                       ("gh-posted.json", "gh-held.json", "gh-not-found.json", "gh-unpinned.json",
                        "resend-accepted.json", "resend-unknown.json")}
    for script in scripts:
        data = json.loads((REPO / script).read_text())
        answers, https = data["answers"], data.get("https") or []
        assert answers or https, script
        assert all(a["argv_prefix"][0] == "gh" for a in answers), script
        # PHILO-10-07: the email edge answers only Resend's one send route, by host + path.
        assert all((a["host"], a["path"]) == ("api.resend.com", "/emails") for a in https), script


def test_no_trigger_is_optional_and_no_optional_step_is_the_outcome() -> None:
    """Law: an optional step is never the outcome. The only optional step is the gate's Continue later."""
    for cid, case in _cases().items():
        assert not case["trigger"].get("optional"), cid
        optional = [s for s in general._acts(case) if s.get("optional")]
        assert all(s.get("name") == "Continue later" for s in optional), cid


def test_a_timed_window_is_one_gesture() -> None:
    """Law: Discard's confirm window (ConfirmVerb, 3 s) is armed and confirmed
    in ONE trigger (its `then`), never across the before-capture."""
    case = _cases()["case.p10.send.discard_after_send"]
    trigger = case["trigger"]
    assert "prepared-discard" in trigger["selector"]
    assert [s["selector"] for s in trigger["then"]] == [trigger["selector"]]
    assert not any("prepared-discard" in str(s.get("selector", "")) and s.get("action") == "click" for s in case["setup"])


def test_every_new_face_case_says_what_main_showed() -> None:
    for cid, case in _cases().items():
        if _face(case):
            assert "New (no red claimed)" in case["expected"]["words"] or "Red on main" in case["expected"]["words"], cid


# ── the rig's recording runner and predicates (unit, no hub) ──────────────

def _rig():
    spec = importlib.util.spec_from_file_location("_graph_walk_p10", REPO / "scripts/graph_walk.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_calls_counts_by_prefix_across_processes() -> None:
    rig = _rig()
    calls = [{"argv": ["gh", "api", "user"], "pid": 1}, {"argv": ["gh", "issue", "comment", "42"], "pid": 1}]
    one = {"kind": "cli_calls", "argv_prefix": ["gh", "issue", "comment"], "count": 1}
    assert rig.check_predicate(one, {}, {"cli_calls": calls})[0]
    assert not rig.check_predicate(one, {}, {"cli_calls": calls + [{"argv": ["gh", "issue", "comment", "42"], "pid": 2}]})[0]
    assert not rig.check_predicate(one, {}, {})[0]  # no runner: never a pass
    assert rig.check_predicate(one, {}, {"cli_calls": calls, "headless": True})[0]


def test_protocol_reads_count_names_an_exact_number_of_rows() -> None:
    rig = _rig()
    after = {"api_reads": [{"method": "GET", "path": "/x", "status": 200, "payload": {"sends": [{"state": "sent"}, {"state": "sent"}]}}]}
    want = lambda n: {"kind": "protocol_reads", "expect": [{"status": 200, "row": {"path": "sends", "match": {"state": "sent"}, "count": n}}]}
    assert rig.check_predicate(want(2), {}, after)[0]
    assert not rig.check_predicate(want(1), {}, after)[0]
    assert not rig.check_predicate(want(0), {}, after)[0]
    assert rig.check_predicate(want(0), {}, {"api_reads": [{"method": "GET", "path": "/x", "status": 200, "payload": {"sends": []}}]})[0]


def test_the_recording_runner_records_before_it_answers(tmp_path, monkeypatch) -> None:
    rig = _rig()
    from holdspeak.services import channel_cli

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(channel_cli, "CLI_RUNNER", channel_cli.CLI_RUNNER)
    script = REPO / "tests/fixtures/philo10_atlas/gh-posted.json"
    digest = rig._install_cli_runner(script)
    assert digest == hashlib.sha256(script.read_bytes()).hexdigest()
    body = tmp_path / "body.md"
    body.write_text("the update")
    done = channel_cli.CLI_RUNNER(["gh", "issue", "comment", "42", "--repo", "acme/payments", "--body-file", str(body)])
    assert done.returncode == 0 and "issuecomment-99001" in done.stdout
    missing = channel_cli.CLI_RUNNER(["acli", "jira", "auth", "status"])
    assert missing.returncode == 1
    log = [json.loads(line) for line in (tmp_path / rig.CLI_CALLS_FILE).read_text().splitlines()]
    assert [entry["argv"][:3] for entry in log] == [["gh", "issue", "comment"], ["acli", "jira", "auth"]]
    assert log[0]["body_sha256"] == hashlib.sha256(b"the update").hexdigest() and log[1]["answer"] is None


# ── the evidence copier: every claimed run kept, reuse refused ─────────────

sys.path.insert(0, str(PROOF))
import retain  # noqa: E402

HEADER = "file\tcase\twidth\tverdict\tseconds\tload1\treading\trun_dir\n"


def _batch(root: Path, rows: list[tuple[str, str, str, str]]) -> Path:
    src = root / "src"
    src.mkdir()
    lines = [HEADER]
    for case, width, verdict, run_dir in rows:
        (src / run_dir).mkdir(parents=True, exist_ok=True)
        obs = {"case_id": case, "verdict": verdict, **({} if width == "op" else {"viewport": int(width)})}
        (src / run_dir / "observation.json").write_text(json.dumps(obs))
        (src / run_dir / "after.png").write_bytes(b"png")
        lines.append(f"atlas-phase10.json\t{case}\t{width}\t{verdict}\t1\t1.0\tr\t{run_dir}\n")
    (src / "runs.tsv").write_text("".join(lines))
    return src


GOOD = [("case.a", "1440", "pass", "case.a--1440/r1"), ("case.a", "393", "pass", "case.a--393/r1"),
        ("case.a.op", "op", "pass", "case.a.op--op/r1")]


def test_the_copier_keeps_each_run_in_its_own_directory(tmp_path) -> None:
    src = _batch(tmp_path, GOOD)
    assert retain.retain(src, tmp_path / "dest") == 3
    assert (tmp_path / "dest/case.a--393/r1/after.png").exists()


def test_the_copier_refuses_to_reuse_a_label(tmp_path) -> None:
    src = _batch(tmp_path, GOOD)
    retain.retain(src, tmp_path / "dest")
    with pytest.raises(retain.Refused, match="written once"):
        retain.retain(src, tmp_path / "dest")


@pytest.mark.parametrize("rows, why", [
    (GOOD + [("case.a", "1440", "pass", "case.a--1440/r1")], "two rows name one run directory"),
    ([("case.a", "1440", "pass", "batch/r1")], "is not <case>--<width>/<run id>"),
    ([("case.a", "1440", "pass", "case.b--1440/r1")], "is not <case>--<width>/<run id>"),
], ids=["shared-run-dir", "batch-keyed", "wrong-case"])
def test_the_copier_refuses_a_run_that_is_not_its_own(tmp_path, rows, why) -> None:
    src = _batch(tmp_path, rows)
    with pytest.raises(retain.Refused, match=why):
        retain.retain(src, tmp_path / "dest")


def test_the_copier_refuses_an_observation_of_another_case_or_width(tmp_path) -> None:
    src = _batch(tmp_path, GOOD)
    (src / "case.a--393/r1/observation.json").write_text(json.dumps({"case_id": "case.a", "verdict": "pass", "viewport": 1440}))
    with pytest.raises(retain.Refused, match="viewport"):
        retain.retain(src, tmp_path / "dest")
    assert not (tmp_path / "dest").exists()  # a refusal leaves no partial label


SHOTS07 = REPO / "pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-07-shots"
RETAINED = sorted(p.name for p in SHOTS.iterdir()) if SHOTS.exists() else []
RETAINED += sorted(f"../story-07-shots/{p.name}" for p in SHOTS07.iterdir()) if SHOTS07.exists() else []


@pytest.mark.parametrize("label", RETAINED)
def test_every_claimed_run_keeps_its_own_observation(label) -> None:
    """One runs.tsv row = one directory = one observation of THAT case at THAT width with THAT verdict."""
    rows = [line.split("\t") for line in (SHOTS / label / "runs.tsv").read_text().splitlines()[1:]]
    assert rows
    dirs = [row[7] for row in rows]
    assert len(set(dirs)) == len(dirs)
    obs_only = not any((SHOTS / label).glob("*/*/*.png"))
    for _f, cid, width, verdict, *_rest, run_dir in rows:
        assert run_dir.startswith(f"{cid}--{width}/"), run_dir
        obs = json.loads((SHOTS / label / run_dir / "observation.json").read_text())
        assert obs["case_id"] == cid and (obs["verdict"] == verdict or (verdict, obs["verdict"]) == ("error", "not_run")), run_dir
        if width != "op":
            assert obs["viewport"] == int(width), run_dir
            if not obs_only and obs["verdict"] != "not_run":  # a hub that died at boot opened no page
                assert any(p.suffix == ".png" for p in (SHOTS / label / run_dir).iterdir()), run_dir
    on_disk = {f"{p.parent.name}/{p.name}" for p in (SHOTS / label).glob("*/*") if p.is_dir()}
    assert on_disk == set(dirs)
