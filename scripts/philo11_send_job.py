#!/usr/bin/env python3
"""PHILO-11-07: the closing use (more documents on the channels).

Two legs, kept apart (story 07 Scope):

* ``rehearse`` (leg A): a cold-context Codex session (the Phase 9 R3 setup:
  scratch root, HOME and CODEX_HOME with the auth file alone, the isolated hub
  its only MCP server), connected as an AGENT with a Settings-issued DESK
  credential, gets the owner's ordinary words and nothing else. From the MCP
  catalogue alone it finds today's brief and one decision record and PREPARES
  a send of each to the saved folder destination (a scratch folder: nothing
  leaves the machine). Its own Send is refused ``owner_principal_required``
  with a receipt. The face shows PREPARED BY the agent at 1440 and 393; the
  owner's Send is pressed on the face (the Chair's brief well and
  Intelligence -> DECISIONS) by the driver AS THE OWNER; the face shows SAVED
  with the path at both widths; the hub's rows, the kernel receipts and the
  file bytes are read back.
* ``real`` (leg B): the owner's authorized targets (charter D3, the Phase 10
  Q6 ruling carries): the folder ``/Users/karol/Documents/HoldSpeak`` and the
  PUBLIC scratch issue ``karolswdev/HoldSpeak#699``. Fixture text only. On an
  isolated hub, the driver AS THE OWNER previews each document and presses
  the inline Send (``POST /api/channels/send``, the SEND well's own route)
  with the digest it read: each of the eight Phase 11 kinds once to the
  folder, and the three families (the brief, the decision record, the meeting
  summary) once to the issue. Each is read back from the far side (the file's
  bytes and sha256; ``gh api`` on the comment), checked for the transcript
  sentinel and for internal ids (the #711 law), and each brief's Slack text
  length is recorded against the 39,000 limit.

EXACTLY ONCE. The ledger (``assets/story-07-real-sends.json``, tracked) gets
an entry BEFORE each real press. Before anything boots, and again before each
press, :func:`exactly_once_findings` refuses a (kind, target) the ledger
names, that the folder already holds (a file with the fixture's marker and the
kind's own heading) or that the issue already carries. A second ``real`` run
refuses before its hub boots.

Machinery reused, not forked: Phase 9 story 06's driver
(``scripts/philo9_room_job.py``) and through it Phase 7's (the cold root, the
Codex turn, the zero-read fence, the receipt read, the redaction at capture);
the Phase 11 glass rig (``tests/e2e/_doc_send_glass.Boards``).
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Iterable, Iterator


REPO = Path(__file__).resolve().parents[1]
STORY_DIR = REPO / "pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels"
FIXTURE_PATH = STORY_DIR / "story-07-fixture.json"
#: The exactly-once ledger of the REAL sends (tracked; an entry is written BEFORE each real press).
LEDGER_PATH = STORY_DIR / "assets/story-07-real-sends.json"
SHOTS_REL = "pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-07-shots"
TOKEN = "philo11-07-send-job"
REVIEW_LABEL = "REHEARSED; OWNER REVIEW PENDING"
SESSIONS = ("agent_prepare",)
PRESS_LABEL = ("the owner's press, made by the driver AS THE OWNER by the owner's word (charter D3, "
               "2026-09-29) for exactly these targets; Codex never sends")
GH_HOSTS = Path.home() / ".config" / "gh" / "hosts.yml"
GH_TOKEN_RE = re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}")
KINDS = ("project_update", "monday_brief", "desk_decision", "meeting_decision", "decision_record",
         "meeting_summary", "meeting_digest", "meeting_followup")
#: The #711 law (Muad'Dib, 2026-09-30), the same patterns as
#: tests/unit/test_philo11_document_sources.py::test_no_rendered_document_carries_an_internal_id.
INTERNAL_RE = re.compile(r"prop-|record-|meeting:|#segment|decision_[0-9a-f]|brief-|pupd_|chs_")
HEX_ID_RE = re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{8,}\b")
SLACK_LIMIT = 39_000


def _load(name: str, path: Path) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


p9 = _load("philo9_room_job", REPO / "scripts/philo9_room_job.py")
p7 = p9.p7
p5 = p9.p5


# ── the fixture (fixed before the run) ───────────────────────────────────


def load_fixture(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    fixture = json.loads(path.read_text())
    # PHILO-15-09 (B04, ruling 2): the sent Brief is titled with its own day
    # (`# Brief · Wednesday 7 Oct 2026`), never "Monday Brief". The tracked
    # fixture is history (pm/roadmap); its signature is read as the product
    # writes it now.
    signatures = fixture.get("signatures") or {}
    if signatures.get("monday_brief") == ["# Monday Brief", "Period:"]:
        signatures["monday_brief"] = ["# Brief · ", "Period:"]
    return fixture


def write_run_fixture(run_dir: Path, source: Path) -> dict[str, Any]:
    raw = source.read_bytes()
    record = {"source": str(source.relative_to(REPO)) if source.is_relative_to(REPO) else str(source),
              "source_sha256": hashlib.sha256(raw).hexdigest(),
              "written_at": datetime.now(timezone.utc).isoformat(), "fixture": json.loads(raw)}
    p7._json_dump(run_dir / "fixture.json", record)
    return record


def fixture_before_run_findings(run_dir: Path, source: Path = FIXTURE_PATH) -> list[str]:
    """The fixture was in the run, unchanged, before the hub was seeded and before any session."""
    path = run_dir / "fixture.json"
    if not path.exists():
        return ["the run holds no fixture.json"]
    record = json.loads(path.read_text())
    findings: list[str] = []
    if record.get("source_sha256") != hashlib.sha256(source.read_bytes()).hexdigest():
        findings.append("the run's fixture hash differs from the story's fixture file")
    written = datetime.fromisoformat(str(record.get("written_at")))
    seed = run_dir / "seed.json"
    if not seed.exists():
        findings.append("the run holds no seed.json")
    elif written >= datetime.fromisoformat(json.loads(seed.read_text())["seeded_at"]):
        findings.append("the fixture was written after the hub was seeded")
    for stage in SESSIONS:
        timing = run_dir / "codex" / stage / "timing.json"
        if timing.exists() and written >= datetime.fromisoformat(json.loads(timing.read_text())["started_at"]):
            findings.append(f"{stage}: the fixture was written after the session began")
        sent = run_dir / "codex" / stage / "owner-prompt.txt"
        want = str((record.get("fixture") or {}).get("prompts", {}).get(stage, "")).strip()
        if sent.exists() and sent.read_text().strip() != want:
            findings.append(f"{stage}: the words sent are not the fixture's words")
    return findings


def session_isolation_findings(run_dir: Path) -> list[str]:
    return p9.session_isolation_findings(run_dir, SESSIONS)


# ── the seed: every document through its real producer, fixture text only ──


@contextmanager
def _home(home: Path, keystore: Path) -> Iterator[None]:
    """HOME and the People key file for the producers that resolve them (restored after)."""
    saved = {k: os.environ.get(k) for k in ("HOME", "HOLDSPEAK_PEOPLE_KEYSTORE_FILE")}
    os.environ["HOME"] = str(home)
    os.environ["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] = str(keystore)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def mint(db: Any, fixture: dict[str, Any], *, now: datetime, keystore: Path) -> dict[str, Any]:
    """The eight Phase 11 documents, minted through their real producers (the
    tests/unit/_philo11_documents.py pattern, with the fixture's own text).
    Writes the durable source stores only; never renders, prepares or sends."""
    from holdspeak.db.decisions import backfill_decisions
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.people import production_people_store
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.decision_record_service import DecisionRecordService
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.services.people_service import PeopleService
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_update_service import ProjectUpdateService

    owner = Principal(PrincipalKind.OWNER, fixture["owner_identity"])
    project = fixture["project"]
    db.projects.create_project(project_id="philo11-07-project", name=project["name"])
    db.project_updates.insert_update(update_id="philo11-07-update", project_id="philo11-07-project",
                                     project_revision=1, body_md="")
    updates = ProjectUpdateService(db, project_service=ProjectService(db))
    # PHILO-15 B64: the owner's text, saved through the editor's path, is his
    # reviewed words (an update with no verified claim is refused).
    updates.save_update(owner, "philo11-07-update", body_md=project["update_body"])
    updates.publish_update(owner, "philo11-07-update")

    primitives = PrimitiveService(db)
    dd = fixture["desk_decision"]
    desk = primitives.create_decision(owner, decision_id="philo11-07-desk", title=dd["title"], status=dd["status"],
                                      deciders=dd["deciders"], context_markdown=dd["context_markdown"],
                                      decision_markdown=dd["decision_markdown"], alternatives=dd["alternatives"],
                                      consequences_markdown=dd["consequences_markdown"])
    pd = fixture["proposed_decision"]
    primitives.create_decision(owner, decision_id="philo11-07-proposed", title=pd["title"], status="proposed",
                               decision_markdown=pd["decision_markdown"])

    m = fixture["meeting"]
    start = (now - timedelta(hours=m["hours_ago"])).replace(microsecond=0)
    meeting = MeetingState(
        id="philo11-07-meeting", started_at=start, ended_at=start + timedelta(minutes=m["minutes"]),
        title=m["title"],
        segments=[TranscriptSegment(text=fixture["transcript_sentinel"], speaker="Avery", start_time=1.0, end_time=2.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=list(m["topics"]), summary=m["summary"], action_items=[{
            "id": "philo11-07-action", "task": m["action_item"], "owner": None, "due": None, "status": "pending",
            "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}]),
        intel_status="completed")
    db.meetings.save_meeting(meeting)
    db.plugins.record_artifact(artifact_id="philo11-07-decisions", meeting_id=meeting.id, artifact_type="decisions",
                               title="Meeting decisions", structured_json={"decisions": list(m["decisions"])},
                               plugin_id="philo11-07-fixture")
    with db._connection() as conn:
        backfill_decisions(conn)
    lifecycle = db.decisions.list(meeting_id=meeting.id)[0]
    records = DecisionRecordService(db)
    record = records.create_from_meeting(owner, lifecycle.id)
    dr = fixture["decision_record"]
    records.update_record(owner, record["id"], {
        "owner": dr["owner"], "review_date": (now.date() + timedelta(days=dr["review_days"])).isoformat()})

    with _home(Path(os.environ.get("HOME", str(Path.home()))), keystore):
        store = production_people_store()
        store.initialize()
        people = PeopleService(store)
        person = fixture["person"]
        rel = people.create_relationship(owner, {"display_name": person["display_name"]})
        req = people.create_request(owner, rel["id"], {"body": person["request"]})
        people.accept_request(owner, req["id"])

    brief = MondayBriefService(db).generate(owner, now=now)
    return {
        "project_update": "project_update:philo11-07-update",
        "monday_brief": f"monday_brief:{brief.id}",
        "desk_decision": f"desk_decision:{desk['id']}",
        "meeting_decision": f"meeting_decision:{lifecycle.id}",
        "decision_record": f"decision_record:{record['id']}",
        "meeting_summary": f"meeting_summary:{meeting.id}",
        "meeting_digest": f"meeting_digest:{meeting.id}",
        "meeting_followup": f"meeting_followup:{meeting.id}",
    }


def seed_db(home: Path, fixture: dict[str, Any], now: datetime) -> dict[str, Any]:
    """Mint the documents into the hub's database (under its HOME) BEFORE the hub boots."""
    from holdspeak.db.core import Database

    keystore = home / "people.key"
    path = home / ".local/share/holdspeak/holdspeak.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    with _home(home, keystore):
        db = Database(path)
        try:
            refs = mint(db, fixture, now=now, keystore=keystore)
        finally:
            db.close()
    return {"seeded_at": datetime.now(timezone.utc).isoformat(), "db": str(path), "people_keystore": str(keystore),
            "documents": refs}


# ── the sent text: no transcript, no internal id (the #711 law) ──────────


def source_ids(db_path: Path, refs: dict[str, str]) -> set[str]:
    import sqlite3
    from contextlib import closing

    ids = {ref.split(":", 1)[1] for ref in refs.values()}
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        ids |= {str(r[0]) for r in conn.execute("SELECT source_ref FROM decision_record_sources")}
        ids |= {str(r[0]) for r in conn.execute("SELECT id FROM decision_records")}
        ids |= {str(r[0]) for r in conn.execute("SELECT id FROM monday_briefs")}
        ids |= {str(r[0]) for r in conn.execute("SELECT id FROM monday_brief_items")}
    return {i for i in ids if i}


def sent_text_findings(kind: str, text: str, *, sentinel: str, ids: Iterable[str]) -> list[str]:
    """What the far side holds carries no transcript and no internal id."""
    found = []
    if sentinel in text:
        found.append(f"{kind}: the transcript sentinel is in the sent text")
    for pattern in (INTERNAL_RE, HEX_ID_RE):
        found += [f"{kind}: internal ref {m.group(0)!r}" for m in pattern.finditer(text)]
    found += [f"{kind}: source id {i!r}" for i in ids if i in text]
    return found


def slack_length(text: str) -> dict[str, Any]:
    """The brief's Slack serialization (the channel's own converter) against the 39,000 limit."""
    from holdspeak.services.channel_slack import MAX_TEXT_CHARACTERS, markdown_to_slack

    slack = markdown_to_slack(text)
    return {"slack_text_characters": len(slack), "limit": MAX_TEXT_CHARACTERS,
            "within_limit": len(slack) <= MAX_TEXT_CHARACTERS,
            "slack_text_sha256": hashlib.sha256(slack.encode("utf-8")).hexdigest()}


# ── exactly once per (kind, target) ──────────────────────────────────────


def _gh_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GH_", "GITHUB_"))}
    env["HOME"] = str(home)
    return env


def gh_json(args: list[str], home: Path) -> Any:
    """One ``gh api`` read under the scratch HOME (its gh login file only)."""
    done = subprocess.run(["gh", "api", *args], env=_gh_env(home), capture_output=True, text=True, timeout=60)
    if done.returncode != 0:
        raise RuntimeError(f"gh api {args[0]} exit {done.returncode}: {done.stderr.strip()[:200]}")
    return json.loads(done.stdout)


def issue_comments(fixture: dict[str, Any], home: Path) -> list[dict[str, Any]]:
    gh = fixture["destinations"]["github"]
    pages = gh_json(["--paginate", "--slurp", f"repos/{gh['repo']}/issues/{gh['number']}/comments"], home)
    return [c for page in pages for c in page]


def carries(fixture: dict[str, Any], kind: str, text: str) -> bool:
    """The text is this fixture's document of this kind (its marker and the kind's own signature)."""
    return fixture["marker"] in text and all(s in text for s in fixture["signatures"][kind])


def exactly_once_findings(fixture: dict[str, Any], sends: Iterable[tuple[str, str]], *, ledger: Path | None = None,
                          folder: Path | None = None,
                          comments: Callable[[], list[dict[str, Any]]] | None = None) -> list[str]:
    """Why a REAL send of (kind, target) would be a second one (empty: none sent yet).

    Three independent reads, any one refuses: the ledger names it; the folder
    already holds a file that carries it; the issue already carries a comment
    that carries it."""
    wanted = list(sends)
    found: list[str] = []
    ledger = ledger or LEDGER_PATH
    if ledger.exists():
        for entry in json.loads(ledger.read_text()).get("sends") or []:
            if (entry.get("kind"), entry.get("target")) in wanted:
                found.append(f"{entry['kind']} -> {entry['target']}: the ledger records a real press at "
                             f"{entry.get('pressed_at')}")
    files = [k for k, t in wanted if t == "file"]
    if files:
        where = folder or Path(fixture["destinations"]["file"]["real_folder"])
        if where.is_dir():
            for path in sorted(where.iterdir()):
                if not path.is_file() or path.suffix != ".md":
                    continue
                text = path.read_bytes().decode("utf-8", errors="replace")
                found += [f"{k} -> file: {path} already carries it" for k in files if carries(fixture, k, text)]
    hub = [k for k, t in wanted if t == "github"]
    if hub and comments is not None:
        for comment in comments():
            body = str(comment.get("body") or "")
            found += [f"{k} -> github: {comment.get('html_url')} already carries it" for k in hub
                      if carries(fixture, k, body)]
    return found


def ledger_append(ledger: Path, entry: dict[str, Any]) -> None:
    """One real press, named BEFORE it happens (a real send is never made twice)."""
    data = json.loads(ledger.read_text()) if ledger.exists() else {
        "about": "PHILO-11-07: the real sends, one per (kind, target), by the owner's word (charter D3, "
                 "2026-09-29). scripts/philo11_send_job.py real refuses any pair named here.",
        "sends": []}
    data["sends"].append(entry)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def ledger_settle(ledger: Path, kind: str, target: str, **fields: Any) -> None:
    data = json.loads(ledger.read_text())
    for entry in reversed(data["sends"]):
        if (entry.get("kind"), entry.get("target")) == (kind, target):
            entry.update(fields)
            break
    ledger.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


# ── the gh login file (the one file taken from the real HOME) ────────────


def copy_gh_login(hub_home: Path, source: Path = GH_HOSTS) -> dict[str, Any]:
    target = hub_home / ".config" / "gh" / "hosts.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(target.parent, 0o700)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(source.read_bytes())
    return {"copied_to": "<hub HOME>/.config/gh/hosts.yml", "mode": oct(target.stat().st_mode & 0o777),
            "source": "~/.config/gh/hosts.yml"}


def delete_gh_login(hub_home: Path) -> dict[str, Any]:
    target = hub_home / ".config" / "gh"
    shutil.rmtree(target, ignore_errors=True)
    return {"deleted": "<hub HOME>/.config/gh", "exists_after": target.exists()}


def gh_credential_findings(root: Path, source: Path = GH_HOSTS) -> list[dict[str, Any]]:
    """Every retained file holding a gh token (by shape, or the login file's own token values)."""
    values: set[str] = set()
    if source.exists():
        values = {m.group(1) for m in re.finditer(r"oauth_token:\s*(\S+)", source.read_text())}
    findings = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="replace")
        hits = len(GH_TOKEN_RE.findall(text)) + sum(text.count(v) for v in values if len(v) >= 8)
        if hits or path.name == "hosts.yml":
            findings.append({"file": str(path.relative_to(root)), "gh_credential": hits or "login file"})
    return findings


def recording_runner(fixture: dict[str, Any], path: Path) -> Path:
    """The dry run's gh: answers as a signed-in gh would; nothing leaves the machine."""
    gh = fixture["destinations"]["github"]
    path.write_text(json.dumps({
        "about": "PHILO-11-07 dry run: gh answers as a signed-in gh would; nothing leaves the machine.",
        "answers": [
            {"argv_prefix": ["gh", "api", "user"], "code": 0, "stdout": json.dumps({"login": gh["login"], "id": 1}),
             "stderr": ""},
            {"argv_prefix": ["gh", gh["kind"], "comment"], "code": 0,
             "stdout": f"https://{gh['host']}/{gh['repo']}/issues/{gh['number']}#issuecomment-1\n", "stderr": ""},
        ]}, indent=2))
    return path


# ── the hub (seeded before boot; the owner's contract) ───────────────────


def _owner(hub: Any, name: str, args: dict[str, Any]) -> Any:
    refused, body = p9._owner_call(hub, name, args)
    if refused:
        raise RuntimeError(f"{name} refused: {body}")
    return body


def save_destinations(hub: Any, fixture: dict[str, Any], folder: Path, *, github: bool) -> dict[str, Any]:
    d = fixture["destinations"]
    saved = {"file": _owner(hub, "channel.save_destination",
                            {"name": d["file"]["name"], "channel": "file", "folder": str(folder)})["destination"]}
    if github:
        g = d["github"]
        saved["github"] = _owner(hub, "channel.save_destination",
                                 {"name": g["name"], "channel": "github", "host": g["host"], "repo": g["repo"],
                                  "kind": g["kind"], "number": g["number"]})["destination"]
    return saved


def boot(fixture: dict[str, Any], temp_root: Path, run_dir: Path, *, record: bool,
         cli_runner: Path | None = None, before: Callable[[Path], None] | None = None) -> tuple[Any, dict[str, Any]]:
    """Seed the hub's DB under its own HOME, then boot the hub on it (the People key file in its env)."""
    hub_home = temp_root / "hub-home"
    hub_home.mkdir()
    seeded = seed_db(hub_home, fixture, datetime.now())
    p7._json_dump(run_dir / "seed.json", seeded)
    if before is not None:
        before(hub_home)
    os.environ["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] = seeded["people_keystore"]
    hub = p7._gw().Hub(hub_home, token=TOKEN, record_rehearsal=record,
                       transcript_path=(hub_home / "rehearsal-transcript.jsonl") if record else None,
                       cli_runner=cli_runner).start()
    if Path(str(hub.db_path)).resolve() != Path(seeded["db"]).resolve():
        hub.stop()
        raise RuntimeError(f"the hub's DB {hub.db_path} is not the seeded DB")
    p7._json_dump(run_dir / "hub-proof.json", p5._hub_proof(hub, hub_home))
    return hub, seeded


def stop(hub: Any, run_dir: Path) -> None:
    p7._json_dump(run_dir / "hub-proof-final.json", p5._hub_proof(hub, Path(hub.home)))
    if hub.db_path and Path(str(hub.db_path)).exists():
        p5._backup_db(Path(str(hub.db_path)), run_dir / "db-proof.sqlite")
    hub.stop()
    p7._write_text(run_dir / "hub.log", "\n".join(hub.lines) + "\n")
    for name, dest in (("rehearsal-transcript.jsonl", "rehearsal-transcript.jsonl"),
                       ("graph-walk-cli-calls.jsonl", "cli-calls.jsonl")):
        src = Path(hub.home) / name
        if src.exists():
            shutil.copy2(src, run_dir / dest)


def _send_row(hub: Any, send_id: str) -> dict[str, Any]:
    return _owner(hub, "channel.sends", {"send_id": send_id})["sends"][0]


# ── the far side, read back apart from the hub ───────────────────────────


def file_readback(send: dict[str, Any], folder: Path) -> dict[str, Any]:
    path = Path(str((send.get("proof") or {}).get("path") or ""))
    data = path.read_bytes() if path.is_file() else b""
    return {"path": str(path), "in_folder": path.parent == Path(os.path.realpath(folder)), "exists": path.is_file(),
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "mode": oct(path.stat().st_mode & 0o777) if path.exists() else None,
            "text": data.decode("utf-8", errors="replace")}


def github_readback(fixture: dict[str, Any], send: dict[str, Any], home: Path) -> dict[str, Any]:
    url = str((send.get("proof") or {}).get("url") or "")
    comment_id = url.rsplit("#issuecomment-", 1)[-1]
    gh = fixture["destinations"]["github"]
    comment = gh_json([f"repos/{gh['repo']}/issues/comments/{comment_id}"], home)
    body = str(comment.get("body") or "")
    return {"api": f"GET repos/{gh['repo']}/issues/comments/{comment_id}", "html_url": comment.get("html_url"),
            "url_equals_proof": comment.get("html_url") == url, "login": (comment.get("user") or {}).get("login"),
            "created_at": comment.get("created_at"), "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "size": len(body.encode("utf-8")), "text": body}


def recorded_readback(fixture: dict[str, Any], hub_home: Path, seen: int) -> dict[str, Any]:
    """The dry run: the recording runner's log (the body the CLI would read) for the newest comment."""
    log = hub_home / "graph-walk-cli-calls.jsonl"
    calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    creates = [c for c in calls if c["argv"][:3] == ["gh", fixture["destinations"]["github"]["kind"], "comment"]]
    return {"recorded": True, "creates": len(creates), "new_creates": len(creates) - seen,
            "sha256": (creates[-1].get("body_sha256") if creates else None), "text": None}


def readback_findings(target: str, back: dict[str, Any], digest: str, *, real: bool) -> list[str]:
    """The far side's bytes are the frozen bytes EXACTLY (the sha256 of the frozen payload)."""
    if target == "file":
        ok = back.get("exists") and back.get("in_folder") and back.get("sha256") == digest
        return [] if ok else [f"file: the read-back is not the frozen bytes ({back.get('path')})"]
    if not real:
        ok = back.get("new_creates") == 1 and back.get("sha256") == digest
        return [] if ok else [f"github (recorded): {back}"]
    ok = back.get("url_equals_proof") is True and back.get("login") and back.get("sha256") == digest
    return [] if ok else [f"github: the read-back is not the frozen bytes ({back.get('html_url')})"]


def receipt_findings(label: str, read: dict[str, Any], *, actor: str, name: str) -> list[str]:
    receipt, op = read.get("receipt") or {}, read.get("operation") or {}
    f = []
    if (receipt.get("state"), receipt.get("actor_kind")) != ("succeeded", actor):
        f.append(f"{label}: the receipt is {receipt.get('state')!r} by {receipt.get('actor_kind')!r}")
    if op.get("name") != name:
        f.append(f"{label}: the operation is {op.get('name')!r}, not {name}")
    return f


# ── leg B: the real sends (the owner's press through the well's own route) ──


def owner_press(hub: Any, ref: str, destination_id: str, command_id: str,
                on_press: Callable[[], None] | None = None) -> dict[str, Any]:
    """The owner reads the preview, then presses Send with the digest he saw:
    ``POST /api/channels/send`` (the SEND well's inline Send), the hub's owner token."""
    status, preview = hub.api("POST", "/api/channels/preview", {"document_ref": ref, "destination_id": destination_id})
    if status >= 400 or not isinstance(preview, dict):
        raise RuntimeError(f"preview {ref}: {status} {str(preview)[:200]}")
    if on_press is not None:
        on_press()
    status, answer = hub.api("POST", "/api/channels/send", {
        "document_ref": ref, "destination_id": destination_id, "preview_digest": preview["payload_digest"],
        "command_id": command_id})
    return {"preview_status": status, "preview_digest": preview["payload_digest"],
            "preview_text": (preview.get("preview") or {}).get("text"), "status": status,
            "answer": answer if isinstance(answer, dict) else {"raw": str(answer)[:500]}}


def run_real(args: argparse.Namespace) -> int:
    fixture_path = Path(args.fixture).resolve()
    fixture = load_fixture(fixture_path)
    dry = bool(args.dry)
    plan = [(s["kind"], s["target"]) for s in fixture["real_sends"]]
    if not dry:
        early = exactly_once_findings(fixture, plan)
        if early:
            for line in early:
                print(f"REFUSED {line}")
            print("PHILO11_SEND_JOB_REFUSED a real send that already happened; nothing booted")
            return 4
        if not GH_HOSTS.exists():
            print("PHILO11_SEND_JOB_REFUSED no gh login file in the real HOME")
            return 4
    run_dir = Path(args.out).resolve() / (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                                          + ("-real-dry" if dry else "-real"))
    run_dir.mkdir(parents=True)
    started = datetime.now(timezone.utc)
    record = write_run_fixture(run_dir, fixture_path)
    temp_root = Path(tempfile.mkdtemp(prefix="philo11-07-"))
    if dry:
        folder = temp_root / "outbox"
        folder.mkdir()
    else:
        folder = Path(fixture["destinations"]["file"]["real_folder"])
        folder.mkdir(parents=True, exist_ok=True)  # he asked to file there
    p7._json_dump(run_dir / "run.json", {
        "story": "PHILO-11-07", "leg": "B (real sends)", "mode": "dry" if dry else "real", "label": REVIEW_LABEL,
        "observed_sitting": False, "engine_mode": "none", "press": PRESS_LABEL + (
            "; through POST /api/channels/send (the SEND well's inline Send route), after the owner's preview"),
        "folder": "<scratch outbox>" if dry else str(folder), "fixture_sha256": record["source_sha256"],
        "plan": plan, "named_limits": fixture["named_limits"]})
    blocked: list[str] = []
    out: dict[str, Any] = {"sends": [], "slack": {}}
    hub = None
    gh_file: dict[str, Any] = {}
    hub_home = temp_root / "hub-home"
    try:
        def gh_login(home: Path) -> None:
            if dry:
                return
            gh_file["copy"] = copy_gh_login(home)
            gh_file["login"] = gh_json(["user"], home).get("login")
            if gh_file["login"] != fixture["destinations"]["github"]["login"]:
                raise RuntimeError(f"gh is signed in as {gh_file['login']!r}, not the fixture's login")
            late = exactly_once_findings(fixture, plan, comments=lambda: issue_comments(fixture, home))
            if late:
                raise RuntimeError(f"exactly once: {late}")

        runner = recording_runner(fixture, temp_root / "gh-recording.json") if dry else None
        hub, seeded = boot(fixture, temp_root, run_dir, record=False, cli_runner=runner, before=gh_login)
        refs = seeded["documents"]
        dests = save_destinations(hub, fixture, folder, github=True)
        p7._json_dump(run_dir / "destinations.json", dests)
        ids = source_ids(Path(seeded["db"]), refs)
        gw = p7._gw()
        provenance = gw.base_provenance(engine_mode="none")
        recorded_seen = 0
        for kind, target in plan:
            ref, dest = refs[kind], dests[target]
            label = f"{kind} -> {target}"
            guard: list[str] = []
            if not dry:
                guard = exactly_once_findings(fixture, [(kind, target)], comments=(
                    (lambda: issue_comments(fixture, hub_home)) if target == "github" else None))
                if target == "github":
                    login = gh_json(["user"], hub_home).get("login")
                    if login != fixture["destinations"]["github"]["login"]:
                        guard.append(f"gh api user answered {login!r}")
                if guard:
                    blocked.append(f"{label}: refused by the guard {guard}")
                    out["sends"].append({"kind": kind, "target": target, "pressed": False, "guard": guard})
                    continue
            pressed_at = datetime.now(timezone.utc).isoformat()
            entry = {"kind": kind, "target": target, "pressed_at": pressed_at, "run": run_dir.name,
                     "document_ref": ref}
            press = owner_press(hub, ref, dest["id"], f"philo11-07-{kind}-{target}",
                                on_press=None if dry else (lambda e=entry: ledger_append(LEDGER_PATH, e)))
            answer = press["answer"]
            send = (answer.get("send") or {}) if isinstance(answer, dict) else {}
            row = _send_row(hub, send["id"]) if send.get("id") else {}
            found: list[str] = []
            if press["status"] != 200 or answer.get("outcome") != "sent" or row.get("state") != "sent":
                found.append(f"{label}: not sent: {press['status']} {answer.get('outcome')!r} "
                             f"{answer.get('error_code') or answer.get('code') or row.get('reason')!r}")
            read = p7._receipt(gw, hub, str(row.get("send_operation_id") or answer.get("operation_id")), provenance) \
                if row else {}
            found += receipt_findings(label, read, actor="owner", name="channel.send")
            if row.get("payload_digest") != press["preview_digest"]:
                found.append(f"{label}: the frozen digest is not the digest of the preview he read")
            if target == "file":
                back = file_readback(row, folder)
            elif dry:
                back = recorded_readback(fixture, hub_home, recorded_seen)
                recorded_seen = back["creates"]
            else:
                back = github_readback(fixture, row, hub_home)
            found += readback_findings(target, back, str(row.get("payload_digest")), real=not dry)
            text = back.get("text") if back.get("text") is not None else (press["preview_text"] or "")
            found += sent_text_findings(label, text, sentinel=fixture["transcript_sentinel"], ids=ids)
            if not carries(fixture, kind, text):
                found.append(f"{label}: the far side does not carry the fixture's {kind}")
            if kind == "monday_brief":
                out["slack"][target] = {"text_from": "the far side's read-back" if back.get("text") is not None
                                        else "the preview (recorded gh)", **slack_length(text)}
                if not out["slack"][target]["within_limit"]:
                    found.append(f"{label}: the Slack text is over the limit: {out['slack'][target]}")
            if not dry:
                ledger_settle(LEDGER_PATH, kind, target, state=row.get("state"), proof=row.get("proof"),
                              send_id=row.get("id"), sha256=back.get("sha256"))
            out["sends"].append({"kind": kind, "target": target, "document_ref": ref, "pressed": True,
                                 "pressed_at": pressed_at, "guard": guard, "preview_digest": press["preview_digest"],
                                 "send": row, "receipt": read.get("receipt"), "operation": read.get("operation"),
                                 "readback": {k: v for k, v in back.items() if k != "text"},
                                 "findings": found})
            blocked += found
        out["sends_listed"] = {kind: _owner(hub, "channel.sends", {"document_ref": ref})["sends"]
                               for kind, ref in refs.items()}
    except Exception as exc:  # noqa: BLE001 - the run records every stop
        blocked.append(f"driver: {type(exc).__name__}: {exc}")
        p7._write_text(run_dir / "run-error.txt", f"{type(exc).__name__}: {exc}\n")
    finally:
        if hub is not None:
            stop(hub, run_dir)
        if not dry:
            gh_file["delete"] = delete_gh_login(hub_home)
        p7._json_dump(run_dir / "gh-login-file.json", gh_file or {"mode": "dry: no file taken from the real HOME"})
        p7._json_dump(run_dir / "legs.json", out)
        shutil.rmtree(temp_root, ignore_errors=True)
    redaction = p7.redact_run(run_dir)
    fences = {"fixture_before_run": fixture_before_run_findings(run_dir, fixture_path),
              "account_leaks": p7.account_leak_findings(run_dir), "gh_credentials": gh_credential_findings(run_dir),
              "gh_login_file_deleted": [] if dry or not gh_file.get("delete", {}).get("exists_after") else ["kept"]}
    for kind, rows in fences.items():
        blocked += [f"fence {kind}: {x}" for x in rows]
    p7._json_dump(run_dir / "redaction.json", {"rule": "e-mail addresses and account ids redacted (Phase 7 rule)",
                                               **redaction})
    p7._json_dump(run_dir / "fences.json", fences)
    p7._json_dump(run_dir / "run-status.json", {
        "started_at": started.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
        "outcome": "blocked" if blocked else "completed", "blocked": blocked, "label": REVIEW_LABEL,
        "mode": "dry" if dry else "real", "named_limits": fixture["named_limits"]})
    print(f"RUN_DIR {run_dir}")
    print(f"MODE {'DRY (scratch folder, recorded gh)' if dry else 'REAL'}")
    for s in out["sends"]:
        rb = s.get("readback") or {}
        proof = (s.get("send") or {}).get("proof") or {}
        print(f"SENT {s['kind']} -> {s['target']} {(s.get('send') or {}).get('state')} "
              f"{proof.get('path') or proof.get('url')} sha256={rb.get('sha256')} far_side_ok={not s.get('findings')}")
    for target, slack in out["slack"].items():
        print(f"SLACK brief -> {target}: {slack['slack_text_characters']} / {slack['limit']} characters")
    print(f"OUTCOME {'BLOCKED' if blocked else 'COMPLETED'}")
    for line in blocked:
        print(f"BLOCKED {line}")
    return 0 if not blocked else 3


# ── leg A: the rehearsal (a cold agent prepares; the owner presses on the face) ──

CH = ".chair [data-seat=brief]"                                   # the Chair's brief seat
DR = ".desk-window .receipt-detail [data-seat=decision-record]"   # Intelligence -> DECISIONS, the record


def _boards(run_dir: Path, width: int) -> Any:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from tests.e2e._doc_send_glass import Boards

    shots = run_dir / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    return Boards(shots, width)


def _chair(page: Any, hub: Any, glass: Any) -> None:
    page.goto(f"{hub.url}/?token={hub.token}", wait_until="load")
    glass._normal_chair(page)
    page.locator(f"{CH} [data-send=well]").first.wait_for(timeout=30_000)
    page.wait_for_timeout(1200)
    glass._settle(page)


def _record(page: Any, hub: Any, glass: Any, text: str) -> None:
    _chair(page, hub, glass)
    page.locator("button.desk-dock-app").first.click()
    page.locator(".desk-window .intelligence-pullout").first.wait_for(timeout=30_000)
    page.locator(".intelligence-segment", has_text="Decisions").first.click()
    page.wait_for_timeout(900)
    page.locator(".desk-window .receipts-results .surface-ledger-line", has_text=text).first.click()
    page.locator(f"{DR} [data-send=well]").first.wait_for(timeout=30_000)
    page.wait_for_timeout(900)
    glass._settle(page)


def _clean(boards: Any) -> list[str]:
    try:
        boards.assert_clean()
    except AssertionError as exc:
        return [str(x) for x in (exc.args[0] if exc.args and isinstance(exc.args[0], list) else exc.args)]
    return []


def _face_press(page: Any, scope: str) -> dict[str, Any]:
    """The owner's Send on the agent's prepared row (the face's own verb; POST /api/channels/send)."""
    verb = page.locator(f"{scope} [data-testid=prepared-send]").first
    verb.wait_for(timeout=30_000)
    verb.scroll_into_view_if_needed()
    with page.expect_response(lambda r: r.url.endswith("/api/channels/send") and r.request.method == "POST",
                              timeout=180_000) as answer:
        verb.click()
    body = answer.value.json()
    page.locator(f"{scope} [data-testid=prepared-result]").first.wait_for(timeout=30_000)
    page.wait_for_timeout(700)
    return {"status": answer.value.status, "outcome": body.get("outcome"),
            "send_id": (body.get("send") or {}).get("id"), "operation_id": body.get("operation_id")}


def face_prepared_findings(fixture: dict[str, Any], facts: dict[str, Any]) -> list[str]:
    by = f"PREPARED BY {fixture['agent']['identity'].upper()}"
    name = fixture["destinations"]["file"]["name"]
    return [f"{key}: no prepared row {by} for {name}: {f.get('prepared')}" for key, f in facts.items()
            if not any(name in r and by in r for r in f.get("prepared") or [])]


def face_saved_findings(fixture: dict[str, Any], facts: dict[str, Any], paths: dict[str, str]) -> list[str]:
    by = f"BY {fixture['agent']['identity'].upper()}"
    out = []
    for key, f in facts.items():
        path = paths["monday_brief" if "brief" in key else "decision_record"]
        if not any(f"✓ SAVED {path}" in r and by in r for r in f.get("prepared") or []):
            out.append(f"{key}: no SAVED {path} {by}: {f.get('prepared')}")
    return out


def agent_receipt_findings(fixture: dict[str, Any], receipts: list[dict[str, Any]]) -> list[str]:
    """The agent's receipts: its prepares succeeded under its own identity; every send refused
    owner_principal_required; no other write succeeded."""
    f: list[str] = []
    agent = fixture["agent"]
    top = [r for r in receipts if not r["operation"].get("parent_operation_id")]
    for r in top:
        op = r["operation"]
        if op.get("principal_kind") != "agent" or op.get("principal_identity") != agent["identity"]:
            f.append(f"{op['name']} actor is {op.get('principal_kind')}:{op.get('principal_identity')}")
    prepares = [r["receipt"].get("state") for r in top if r["operation"]["name"] == agent["prepares"]]
    if prepares.count("succeeded") != len(agent["kinds"]):
        f.append(f"{prepares} prepare receipts, not {len(agent['kinds'])} succeeded")
    sends = [r for r in top if r["operation"]["name"] == agent["send_refused"]]
    if not sends:
        f.append("the agent never tried to send")
    for r in sends:
        if (r["receipt"].get("state"), r["receipt"].get("outcome")) != ("refused", agent["send_refused_code"]):
            f.append(f"the agent's send was not refused {agent['send_refused_code']}: "
                     f"{r['receipt'].get('state')!r} {r['receipt'].get('outcome')!r}")
    others = sorted({r["operation"]["name"] for r in top if r["operation"]["name"] not in
                     (agent["prepares"], agent["send_refused"]) and r["receipt"].get("state") == "succeeded"})
    if others:
        f.append(f"agent writes the job does not name succeeded: {others}")
    return f


def prepared_findings(fixture: dict[str, Any], refs: dict[str, str], dest_id: str, sends: dict[str, list[dict[str, Any]]],
                      previews: dict[str, str]) -> list[str]:
    """Exactly one PREPARED send per wanted document, to the folder, by the agent, the bytes of the owner's preview."""
    f: list[str] = []
    identity = fixture["agent"]["identity"]
    for kind in fixture["agent"]["kinds"]:
        rows = sends.get(kind) or []
        if len(rows) != 1:
            f.append(f"{kind}: {len(rows)} sends, not one prepared send")
            continue
        row = rows[0]
        if (row.get("state"), row.get("destination_id"), row.get("document_ref")) != ("prepared", dest_id, refs[kind]):
            f.append(f"{kind}: {row.get('state')!r} to {row.get('destination_id')!r} of {row.get('document_ref')!r}")
        if row.get("prepared_by") != {"kind": "agent", "identity": identity}:
            f.append(f"{kind}: prepared by {row.get('prepared_by')}, not the agent {identity}")
        if row.get("payload_digest") != previews.get(kind):
            f.append(f"{kind}: the frozen digest is not the owner's preview digest")
    extra = [k for k, rows in sends.items() if k not in fixture["agent"]["kinds"] and rows]
    if extra:
        f.append(f"sends of documents the job does not name: {extra}")
    return f


def run_rehearse(args: argparse.Namespace) -> int:
    from playwright.sync_api import sync_playwright

    fixture_path = Path(args.fixture).resolve()
    fixture = load_fixture(fixture_path)
    p7.CLIENT[0] = "codex"
    p7.CODEX_AUTH[0] = Path(args.codex_auth).expanduser().resolve()
    run_dir = Path(args.out).resolve() / (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-rehearse"
                                          + ("" if args.press_width == 1440 else f"-press{args.press_width}"))
    run_dir.mkdir(parents=True)
    started = datetime.now(timezone.utc)
    record = write_run_fixture(run_dir, fixture_path)
    temp_root = Path(tempfile.mkdtemp(prefix="philo11-07-rh-"))
    folder = temp_root / "outbox"
    folder.mkdir()
    gw = p7._gw()
    provenance = gw.base_provenance(engine_mode="none")
    provenance["engine_mode_reason"] = "the job calls no model: every document is the fixture's stored record"
    p7._json_dump(run_dir / "run.json", {
        "story": "PHILO-11-07", "leg": "A (rehearsal)", "claim": p7.CLAIM_CODEX, "client": "codex",
        "model": p7.MODEL, "reasoning_effort": p7.EFFORT, "label": REVIEW_LABEL, "observed_sitting": False,
        "engine_mode": "none", "sessions": list(SESSIONS), "press": PRESS_LABEL + "; on the face (the Chair's "
        "brief well and Intelligence -> DECISIONS), clicked by the driver at " + str(args.press_width),
        "press_width": args.press_width, "folder": "<scratch outbox>",
        "fixture_sha256": record["source_sha256"]})
    blocked: list[str] = []
    out: dict[str, Any] = {"checks": {}, "press": {}, "readback": {}}
    hub = None
    try:
        hub, seeded = boot(fixture, temp_root, run_dir, record=True)
        refs = seeded["documents"]
        dest = save_destinations(hub, fixture, folder, github=False)["file"]
        p7._json_dump(run_dir / "destinations.json", {"file": dest})
        kinds = fixture["agent"]["kinds"]
        previews = {k: _owner(hub, "channel.preview", {"document_ref": refs[k], "destination_id": dest["id"]})[
            "payload_digest"] for k in kinds}
        identity = fixture["agent"]["identity"]
        status_e, _ = hub.api("PUT", "/api/settings/remote", {"enabled": True})
        status_c, issued = hub.api("POST", "/api/settings/remote/credentials",
                                   {"identity": identity, "palette": fixture["agent"]["palette"]})
        if status_e >= 400 or status_c >= 400 or not isinstance(issued, dict) or not issued.get("token"):
            raise RuntimeError(f"credential issue failed ({status_e}, {status_c})")
        bearer = str(issued["token"])
        credential = {k: v for k, v in issued.items() if k != "token"}
        credential.update({"token_sha256_12": hashlib.sha256(bearer.encode()).hexdigest()[:12],
                           "route": "POST /api/settings/remote/credentials"})
        p7._json_dump(run_dir / "agent" / "credential.json", credential)

        # 1. The cold agent: prepare both, try to send (refused).
        rowid = p7._max_op_rowid(hub)
        out["session"], stops = p9._session(run_dir, temp_root, hub, "agent_prepare", "agent",
                                            fixture["prompts"]["agent_prepare"], bearer, args.codex_timeout)
        blocked += stops
        ops = p9._ops_since(hub, rowid)
        receipts = p9._receipts(gw, hub, ops, provenance)

        def sends_now() -> dict[str, list[dict[str, Any]]]:
            return {k: _owner(hub, "channel.sends", {"document_ref": ref})["sends"] for k, ref in refs.items()}

        sends = sends_now()
        out["agent_send_by_driver"] = None
        if not any(r["operation"]["name"] == "channel.send" for r in receipts):
            prepared = [s for k in kinds for s in sends.get(k) or [] if s.get("state") == "prepared"]
            if prepared:
                refused, body = p9._agent_call(hub, bearer, "channel.send", {"send_id": prepared[0]["id"]})
                out["agent_send_by_driver"] = {"refused": refused, "answer": body,
                                               "label": "the agent's send made by the driver with the agent's credential"}
                more = p9._ops_since(hub, max(o["rid"] for o in ops) if ops else rowid)
                receipts += p9._receipts(gw, hub, more, provenance)
                sends = sends_now()
        calls = p9._tool_calls(p9._window(hub, run_dir, "agent_prepare"))
        out["agent_tools"] = [name for name, _a, _t in calls]
        checks = {"prepared": prepared_findings(fixture, refs, dest["id"], sends, previews),
                  "receipts": agent_receipt_findings(fixture, receipts),
                  "nothing_left": [] if not any(folder.iterdir()) else [f"the folder is not empty: {os.listdir(folder)}"]}
        p7._json_dump(run_dir / "agent_prepare" / "readbacks.json",
                      {"operations": ops, "receipts": receipts, "sends": sends, "previews": previews,
                       "agent_send_by_driver": out["agent_send_by_driver"]})
        out["checks"]["agent_prepare"] = checks
        blocked += [f"agent_prepare {k}: {x}" for k, rows in checks.items() for x in rows]
        by_kind = {k: (sends.get(k) or [{}])[0] for k in kinds}
        if any(not by_kind[k].get("id") or by_kind[k].get("state") != "prepared" for k in kinds):
            raise RuntimeError(f"nothing to press: {[(k, by_kind[k].get('state')) for k in kinds]}")

        # 2. The face: PREPARED at both widths; his press at 1440; SAVED at both widths.
        glass = p9._glass()
        glass._ensure_build()
        record_text = fixture["meeting"]["decisions"][0]["decision"]
        facts: dict[str, Any] = {"prepared": {}, "saved": {}}
        with sync_playwright() as play:
            browser, pages, errors = p9._pages(play, hub)
            try:
                boards = {w: _boards(run_dir, w) for w in pages}
                for width, page in pages.items():
                    b = boards[width]
                    _chair(page, hub, glass)
                    page.locator(f"{CH} [data-testid=prepared-row]").first.wait_for(timeout=30_000)
                    facts["prepared"][f"brief-{width}"] = b.shoot(
                        page, "1-brief-prepared", CH, [f"{CH} [data-testid=prepared-row]",
                                                       f"{CH} [data-testid=prepared-send]"])
                    _record(page, hub, glass, record_text)
                    page.locator(f"{DR} [data-testid=prepared-row]").first.wait_for(timeout=30_000)
                    facts["prepared"][f"record-{width}"] = b.shoot(
                        page, "2-record-prepared", DR, [f"{DR} [data-testid=prepared-row]",
                                                        f"{DR} [data-testid=prepared-send]"])
                page = pages[args.press_width]   # the owner's press, at the width asked for
                _chair(page, hub, glass)
                out["press"]["monday_brief"] = {"face": _face_press(page, CH), "label": PRESS_LABEL}
                _record(page, hub, glass, record_text)
                out["press"]["decision_record"] = {"face": _face_press(page, DR), "label": PRESS_LABEL}
                paths: dict[str, str] = {}
                for kind in kinds:
                    row = _send_row(hub, by_kind[kind]["id"])
                    read = p7._receipt(gw, hub, str(row.get("send_operation_id")), provenance)
                    back = file_readback(row, folder)
                    found = [] if row.get("state") == "sent" else [f"{kind}: the send is {row.get('state')!r}"]
                    found += receipt_findings(kind, read, actor="owner", name="channel.send")
                    found += readback_findings("file", back, str(row.get("payload_digest")), real=True)
                    found += sent_text_findings(kind, back["text"], sentinel=fixture["transcript_sentinel"],
                                                ids=source_ids(Path(seeded["db"]), refs))
                    if (row.get("proof") or {}).get("sha256") != back["sha256"]:
                        found.append(f"{kind}: the hub's proof sha256 is not the file's")
                    paths[kind] = str((row.get("proof") or {}).get("path"))
                    out["press"][kind].update({"send": row, "receipt": read["receipt"], "operation": read["operation"]})
                    out["readback"][kind] = {k: v for k, v in back.items() if k != "text"}
                    if kind == "monday_brief":
                        out["readback"][kind]["slack"] = slack_length(back["text"])
                    out["checks"][f"press_{kind}"] = found
                    blocked += found
                for width, page in pages.items():
                    b = boards[width]
                    _chair(page, hub, glass)
                    page.locator(f"{CH} [data-testid=prepared-result]").first.wait_for(timeout=30_000)
                    facts["saved"][f"brief-{width}"] = b.shoot(
                        page, "3-brief-saved", CH, [f"{CH} [data-testid=prepared-result]"])
                    _record(page, hub, glass, record_text)
                    page.locator(f"{DR} [data-testid=prepared-result]").first.wait_for(timeout=30_000)
                    facts["saved"][f"record-{width}"] = b.shoot(
                        page, "4-record-saved", DR, [f"{DR} [data-testid=prepared-result]"])
                    b.write("face", {"width": width})
                    out["checks"][f"face_clean_{width}"] = _clean(b)
                out["checks"]["face_prepared"] = face_prepared_findings(fixture, facts["prepared"])
                out["checks"]["face_saved"] = face_saved_findings(fixture, facts["saved"], paths)
                out["face"] = {phase: {k: {"prepared": v.get("prepared"), "wells": v.get("wells"),
                                           "named": v.get("named"), "history_head": v.get("history_head")}
                                       for k, v in rows.items()} for phase, rows in facts.items()}
                out["page_errors"] = errors
                for key in ("face_prepared", "face_saved", "face_clean_1440", "face_clean_393"):
                    blocked += [f"{key}: {x}" for x in out["checks"][key]]
                blocked += [f"page error: {e}" for e in errors]
            finally:
                browser.close()
        out["sends_after"] = sends_now()
    except Exception as exc:  # noqa: BLE001 - the run records every stop
        blocked.append(f"driver: {type(exc).__name__}: {exc}")
        p7._write_text(run_dir / "run-error.txt", f"{type(exc).__name__}: {exc}\n")
    finally:
        if hub is not None:
            stop(hub, run_dir)
        for auth in temp_root.glob("**/.codex/auth.json"):
            auth.unlink(missing_ok=True)
        p7._json_dump(run_dir / "provenance.json", provenance)
        p7._json_dump(run_dir / "legs.json", out)
        shutil.rmtree(temp_root, ignore_errors=True)
    redaction = p7.redact_run(run_dir)
    events = run_dir / "codex" / "agent_prepare" / "events.jsonl"
    fences = {"fixture_before_run": fixture_before_run_findings(run_dir, fixture_path),
              "session_isolation": session_isolation_findings(run_dir),
              "zero_read": len(p7.zero_read_findings(p7.read_events(events))) if events.exists() else "no events",
              "account_leaks": p7.account_leak_findings(run_dir)}
    for kind in ("fixture_before_run", "session_isolation", "account_leaks"):
        blocked += [f"fence {kind}: {x}" for x in fences[kind]]
    if fences["zero_read"] != 0:
        blocked.append(f"fence zero_read: {fences['zero_read']}")
    p7._json_dump(run_dir / "redaction.json", {"rule": "e-mail addresses and account ids redacted (Phase 7 rule)",
                                               **redaction})
    p7._json_dump(run_dir / "fences.json", fences)
    p7._json_dump(run_dir / "run-status.json", {
        "started_at": started.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
        "outcome": "blocked" if blocked else "completed", "blocked": blocked, "label": REVIEW_LABEL,
        "claim": p7.CLAIM_CODEX, "press": PRESS_LABEL})
    print(f"RUN_DIR {run_dir}")
    print("MODE REHEARSAL (isolated hub, scratch folder: nothing leaves the machine)")
    print(f"AGENT_TOOLS {out.get('agent_tools')}")
    for kind, press in out["press"].items():
        face, send, receipt = press.get("face") or {}, press.get("send") or {}, press.get("receipt") or {}
        print(f"PRESS {kind} width={args.press_width} http={face.get('status')} outcome={face.get('outcome')} "
              f"send={send.get('state')} op={send.get('send_operation_id')} receipt={receipt.get('state')} "
              f"by={receipt.get('actor_kind')}")
    for kind, back in out["readback"].items():
        print(f"SAVED {kind} {json.dumps(back, sort_keys=True)}")
    print(f"OUTCOME {'BLOCKED' if blocked else 'COMPLETED'}")
    for line in blocked:
        print(f"BLOCKED {line}")
    return 0 if not blocked else 3


# ── the CLI ──────────────────────────────────────────────────────────────


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)
    rh = sub.add_parser("rehearse", help="leg A: a cold Codex session prepares; the owner presses on the face")
    rh.add_argument("--out", default=None)
    rh.add_argument("--codex-timeout", type=float, default=1200)
    rh.add_argument("--codex-auth", type=Path, default=Path.home() / ".codex" / "auth.json")
    rh.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    rh.add_argument("--press-width", type=int, choices=(1440, 393), default=1440,
                    help="the width at which the owner's Send is pressed (Astra r1 on #719: both widths)")
    real = sub.add_parser("real", help="leg B: the real sends, exactly once each (refused when one exists)")
    real.add_argument("--out", default=None)
    real.add_argument("--dry", action="store_true", help="a scratch folder and a recording gh: nothing leaves")
    real.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    guard = sub.add_parser("guard", help="the exactly-once guard alone: would a real run send again?")
    guard.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from tests._evidence import evidence_dir  # noqa: PLC0415 -- the evidence law decides where runs go

    args = _parser().parse_args(argv)
    if args.mode == "guard":
        fixture = load_fixture(args.fixture.resolve())
        found = exactly_once_findings(fixture, [(s["kind"], s["target"]) for s in fixture["real_sends"]])
        for line in found:
            print(f"REFUSED {line}")
        print("GUARD REFUSES A REAL RUN" if found else "GUARD: no real send recorded")
        return 4 if found else 0
    if args.out is None:
        args.out = str(evidence_dir(SHOTS_REL + ("/final" if args.mode == "real" and not args.dry else "/attempts")))
    try:
        return run_rehearse(args) if args.mode == "rehearse" else run_real(args)
    except Exception as exc:  # noqa: BLE001
        print(f"PHILO11_SEND_JOB_BLOCKED {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
