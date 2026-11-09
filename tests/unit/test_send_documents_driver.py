"""PHILO-11-07: the closing-use driver's own fences (no hub boots, nothing is sent).

The exactly-once guard (the ledger, the folder, the issue), the refusal of a
second real run before anything boots, the far-side byte law, the #711 law on
the sent text (no transcript, no internal id), each kind's signature naming
its own document only, and the brief's Slack length against the 39,000 limit.
Documents are minted through the real producers into a tmp_path database.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import philo11_send_job as job  # noqa: E402


@pytest.fixture
def fixture() -> dict:
    return job.load_fixture()


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> dict:
    """The eight documents of the story's fixture, minted and rendered in a tmp HOME."""
    home = tmp_path_factory.mktemp("philo11-07-mint")
    fx = job.load_fixture()
    saved = {k: os.environ.get(k) for k in ("HOME", "HOLDSPEAK_PEOPLE_KEYSTORE_FILE")}
    seeded = job.seed_db(home, fx, datetime(2026, 10, 1, 9, 0, 0))
    from holdspeak.db.core import Database
    from holdspeak.services.document_sources import render_document

    with job._home(home, Path(seeded["people_keystore"])):
        db = Database(Path(seeded["db"]))
        try:
            docs = {k: render_document(db, ref) for k, ref in seeded["documents"].items()}
        finally:
            db.close()
    assert {k: os.environ.get(k) for k in saved} == saved   # the driver's HOME is restored
    return {"docs": docs, "ids": job.source_ids(Path(seeded["db"]), seeded["documents"]), "fixture": fx}


def test_the_fixture_plans_every_kind_on_the_file_and_three_families_on_github(fixture) -> None:
    plan = [(s["kind"], s["target"]) for s in fixture["real_sends"]]
    assert len(plan) == len(set(plan))
    assert {k for k, t in plan if t == "file"} == set(job.KINDS)
    assert {k for k, t in plan if t == "github"} == {"monday_brief", "decision_record", "meeting_summary"}
    assert set(fixture["signatures"]) == set(job.KINDS)
    assert set(fixture["named_limits"]) >= {"email", "slack", "jira", "confluence"}


def test_each_document_carries_only_its_own_signature(rendered) -> None:
    fx = rendered["fixture"]
    for kind, doc in rendered["docs"].items():
        owners = [k for k in job.KINDS if job.carries(fx, k, doc.body_md)]
        assert owners == [kind], (kind, owners)


def test_no_sent_text_carries_the_transcript_or_an_internal_id(rendered) -> None:
    fx = rendered["fixture"]
    for kind, doc in rendered["docs"].items():
        text = "\n".join((doc.body_md, doc.title, doc.label))
        assert job.sent_text_findings(kind, text, sentinel=fx["transcript_sentinel"], ids=rendered["ids"]) == []
    # Red: the transcript sentinel, a record ref and a source id are each named.
    body = rendered["docs"]["meeting_summary"].body_md
    leaked = body + f"\n{fx['transcript_sentinel']}\nrecord-4dd89b268c8344f5\n" + next(iter(rendered["ids"]))
    found = job.sent_text_findings("meeting_summary", leaked, sentinel=fx["transcript_sentinel"], ids=rendered["ids"])
    assert any("transcript" in f for f in found) and any("record-" in f for f in found)
    assert any("source id" in f for f in found)


def test_the_brief_goes_out_whole_and_its_slack_length_is_measured(rendered) -> None:
    brief = rendered["docs"]["monday_brief"].body_md
    # The sent Brief carries no People data (#767): no section, no name.
    assert "## People" not in brief and rendered["fixture"]["person"]["display_name"] not in brief
    # PHILO-15-09 (B04): the Brief's own weekday and date, one range.
    assert brief.startswith("# Brief · Thursday 1 Oct 2026\nPeriod: SEP 30 - OCT 01\n")
    measured = job.slack_length(brief)
    assert measured["limit"] == 39_000 and measured["within_limit"]
    assert 0 < measured["slack_text_characters"] <= len(brief)
    assert not job.slack_length("x" * 39_001)["within_limit"]


def test_the_guard_reads_the_ledger_the_folder_and_the_issue(fixture, tmp_path: Path, rendered) -> None:
    ledger, folder = tmp_path / "ledger.json", tmp_path / "folder"
    folder.mkdir()
    plan = [(s["kind"], s["target"]) for s in fixture["real_sends"]]
    assert job.exactly_once_findings(fixture, plan, ledger=ledger, folder=folder, comments=lambda: []) == []
    job.ledger_append(ledger, {"kind": "meeting_digest", "target": "file", "pressed_at": "t"})
    assert job.exactly_once_findings(fixture, plan, ledger=ledger, folder=folder) == [
        "meeting_digest -> file: the ledger records a real press at t"]
    ledger.unlink()
    (folder / "x.md").write_text(rendered["docs"]["desk_decision"].body_md)
    (folder / "unrelated.md").write_text("# Monday Brief\n## People\nno marker\n")
    assert [f.split(":")[0] for f in job.exactly_once_findings(fixture, plan, ledger=ledger, folder=folder)] == [
        "desk_decision -> file"]
    found = job.exactly_once_findings(fixture, [("decision_record", "github")], ledger=ledger, folder=folder,
                                      comments=lambda: [{"body": rendered["docs"]["decision_record"].body_md,
                                                         "html_url": "u"}])
    assert found == ["decision_record -> github: u already carries it"]


def test_a_second_real_run_is_refused_before_anything_boots(fixture, tmp_path: Path, monkeypatch) -> None:
    ledger = tmp_path / "ledger.json"
    job.ledger_append(ledger, {"kind": "monday_brief", "target": "github", "pressed_at": "t"})
    monkeypatch.setattr(job, "LEDGER_PATH", ledger)
    fx = dict(fixture, destinations=dict(fixture["destinations"], file=dict(
        fixture["destinations"]["file"], real_folder=str(tmp_path / "folder"))))
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(json.dumps(fx))
    booted: list[bool] = []
    monkeypatch.setattr(job, "boot", lambda *a, **k: booted.append(True))
    out = tmp_path / "out"
    assert job.main(["real", "--out", str(out), "--fixture", str(fixture_path)]) == 4
    assert not booted and not out.exists()
    # The guard mode answers the same, and an empty ledger lets a run through the early guard.
    assert job.main(["guard", "--fixture", str(fixture_path)]) == 4
    ledger.unlink()
    assert job.main(["guard", "--fixture", str(fixture_path)]) == 0


@pytest.mark.parametrize("target", ["file", "github"])
def test_an_extra_newline_on_the_far_side_is_red(target: str) -> None:
    body = b"# Monday Brief\n"
    digest = hashlib.sha256(body).hexdigest()
    good = ({"exists": True, "in_folder": True, "sha256": digest} if target == "file"
            else {"url_equals_proof": True, "login": "karolswdev", "sha256": digest})
    assert job.readback_findings(target, good, digest, real=True) == []
    bad = dict(good, sha256=hashlib.sha256(body + b"\n").hexdigest())
    assert job.readback_findings(target, bad, digest, real=True)


def test_the_ledger_is_written_before_the_press(tmp_path: Path) -> None:
    order: list[str] = []

    class Hub:
        def api(self, method: str, path: str, body: dict) -> tuple[int, dict]:
            order.append(path)
            if path.endswith("/preview"):
                return 200, {"payload_digest": "d", "preview": {"text": "t"}}
            return 200, {"outcome": "sent", "send": {"id": "s"}}

    ledger = tmp_path / "ledger.json"
    job.owner_press(Hub(), "monday_brief:b", "dest", "c",
                    on_press=lambda: (order.append("ledger"), job.ledger_append(ledger, {"kind": "k", "target": "t"})))
    assert order == ["/api/channels/preview", "ledger", "/api/channels/send"]
    assert json.loads(ledger.read_text())["sends"] == [{"kind": "k", "target": "t"}]


def test_the_tracked_ledger_refuses_a_second_real_run(tmp_path: Path, monkeypatch) -> None:
    """The tracked ledger is an operational input, not evidence: it stays in
    the tree (pm/ARCHIVE.md). With it, a real run refuses before anything boots."""
    sends = json.loads(job.LEDGER_PATH.read_text())["sends"]
    assert len(sends) == 11 and {e["state"] for e in sends} == {"sent"}
    booted: list[bool] = []
    monkeypatch.setattr(job, "boot", lambda *a, **k: booted.append(True))
    out = tmp_path / "out"
    assert job.main(["real", "--out", str(out)]) == 4
    assert not booted and not out.exists()
    assert job.main(["guard"]) == 4
