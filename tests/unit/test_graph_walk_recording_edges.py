"""The graph-walk rig (scripts/graph_walk.py): the recording CLI runner, the
email edge, and the cli_calls / protocol_reads counts.

Moved from tests/unit/test_philo10_atlas.py by the fast diet (2026-10-12); the
Phase 10 atlas-case pins and the Phase 10 evidence-copier tests (retain.py, a
closed phase's proof script under pm/roadmap) are parked in
tests/_parked/unit/test_philo10_atlas.py.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def test_the_email_edge_records_before_it_answers_and_never_the_key(tmp_path, monkeypatch) -> None:
    rig = _rig()
    import urllib.request

    from holdspeak.services import channel_email

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(channel_email, "HTTPS_HANDLER", channel_email.HTTPS_HANDLER)
    monkeypatch.setattr(channel_email, "KEY_STORE", channel_email.KEY_STORE)
    # The edge install also replaces the Slack seams (graph_walk._install_email_edge):
    # restore them too, or a memory key store leaks into the next test in this worker.
    from holdspeak.services import channel_slack

    monkeypatch.setattr(channel_slack, "HTTPS_HANDLER", channel_slack.HTTPS_HANDLER)
    monkeypatch.setattr(channel_slack, "KEY_STORE", channel_slack.KEY_STORE)
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
