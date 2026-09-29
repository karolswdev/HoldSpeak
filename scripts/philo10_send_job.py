#!/usr/bin/env python3
"""PHILO-10-06: prepare it cold, send it yourself (Codex, cold context; two real sends).

The closing use of Phase 10. A cold-context Codex session, connected as an
AGENT with a Settings-issued PROJECT credential, gets the owner's ordinary
words and nothing else. From the MCP catalogue of an isolated rig hub alone it
finds the published update and the two saved destinations and PREPARES a send
to each; its own attempt to send is refused ``owner_principal_required`` with a
receipt. Then the OWNER presses Send on the face (the Room's real Send route,
``POST /api/channels/send``): in this run the driver presses AS THE OWNER, by
the owner's word of 2026-09-29, for exactly these two targets. Codex never
sends. A second fresh session reads where the update went and its proofs.

The sessions (each its own scratch root, HOME and CODEX_HOME with the auth file
alone; distinct session ids; no resume; the isolated hub the only MCP server):

1. ``agent_prepare``: prepare both sends; try to send them (refused);
2. ``agent_check``: after the owner's press, where did it go, with what proof.

Two modes:

* the REHEARSAL (default): the file destination is a folder in the run's
  scratch root, and ``gh`` is the rig's RECORDING runner (``graph_walk.py``
  boundary ``cli_runner``, PHILO-10-05): nothing leaves the machine;
* ``--real``: the owner's two authorized targets, the folder
  ``/Users/karol/Documents/HoldSpeak`` and a comment on
  ``karolswdev/HoldSpeak#699``. The hub's scratch HOME gets ONE file from the
  real HOME, a 0600 copy of the ``gh`` login file, deleted when the run ends.
  Nothing else crosses: never the owner's DB or Keychain.

EXACTLY ONE SEND PER TARGET. Before anything boots, and again just before each
press, :func:`exactly_once_findings` refuses a target that the ledger
(``assets/story-06-real-sends.json``, written right after each real press,
whatever its outcome) names, that the folder already holds (the fixture's
exact bytes), or that issue 699 already carries (a comment with the fixture's
marker). A second ``--real`` run refuses before its hub boots.

The machinery is Phase 9 story 06's driver (``scripts/philo9_room_job.py``) and,
through it, Phase 7's: the cold root, the Codex turn and its retained rollout,
the zero-read fence, the pairing, the receipt read, the redaction at capture.
The face reads the Send face's own facts (``tests/e2e/_send_face_glass.FACTS``).
Jira, Confluence and email are NAMED LIMITS (the owner has no account yet,
2026-09-29); their contracts are proven by stories 02 and 03's fences.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
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
from typing import Any, Callable, Iterable


REPO = Path(__file__).resolve().parents[1]
STORY_DIR = REPO / "pm/roadmap/holdspeak-philo/phase-10-the-channels"
FIXTURE_PATH = STORY_DIR / "story-06-fixture.json"
#: The exactly-once ledger of the REAL sends (tracked; written after each real press).
LEDGER_PATH = STORY_DIR / "assets/story-06-real-sends.json"
SHOTS_REL = "pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-06-shots"
TOKEN = "philo10-06-send-job"
REVIEW_LABEL = "REHEARSED; OWNER REVIEW PENDING"
SESSIONS = ("agent_prepare", "agent_check")
PRESS_LABEL = ("the owner's press, made by the driver AS THE OWNER through the Room's Send "
               "(POST /api/channels/send from the face), by the owner's word of 2026-09-29 for "
               "exactly these two targets; Codex never sends")
GH_HOSTS = Path.home() / ".config" / "gh" / "hosts.yml"
#: A gh credential in any retained file (the token shapes gh writes).
GH_TOKEN_RE = re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}")


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

# The fences are the Phase 7 ones, unchanged (one implementation).
read_events = p7.read_events
zero_read_findings = p7.zero_read_findings
account_leak_findings = p7.account_leak_findings
redact_run = p7.redact_run


# ── the fixture (fixed before the run) ───────────────────────────────────


def load_fixture(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text())


def body_bytes(fixture: dict[str, Any]) -> bytes:
    """The exact bytes every channel of this run carries (file and GitHub serialize body_md as UTF-8)."""
    return str(fixture["update_body"]).encode("utf-8")


def write_run_fixture(run_dir: Path, source: Path) -> dict[str, Any]:
    raw = source.read_bytes()
    record = {
        "source": str(source.relative_to(REPO)) if source.is_relative_to(REPO) else str(source),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "fixture": json.loads(raw),
        "body_sha256": hashlib.sha256(body_bytes(json.loads(raw))).hexdigest(),
    }
    p7._json_dump(run_dir / "fixture.json", record)
    return record


def fixture_before_run_findings(run_dir: Path, source: Path = FIXTURE_PATH) -> list[str]:
    """The fixture was in the run, unchanged, before the first session began; the words sent are its words."""
    path = run_dir / "fixture.json"
    if not path.exists():
        return ["the run holds no fixture.json"]
    record = json.loads(path.read_text())
    findings: list[str] = []
    if record.get("source_sha256") != hashlib.sha256(source.read_bytes()).hexdigest():
        findings.append("the run's fixture hash differs from the story's fixture file")
    if record.get("fixture") != load_fixture(source):
        findings.append("the run's fixture values differ from the story's fixture file")
    written = datetime.fromisoformat(str(record.get("written_at")))
    starts = [datetime.fromisoformat(json.loads(t.read_text())["started_at"])
              for t in (run_dir / "codex" / s / "timing.json" for s in SESSIONS) if t.exists()]
    if not starts:
        findings.append("no session timing in the run")
    elif written >= min(starts):
        findings.append(f"the fixture was written at {written.isoformat()}, not before the first session")
    seed = run_dir / "seed.json"
    if seed.exists():
        seeded = datetime.fromisoformat(json.loads(seed.read_text())["seeded_at"])
        if written >= seeded:
            findings.append("the fixture was written after the hub was seeded")
    prompts = (record.get("fixture") or {}).get("prompts") or {}
    for stage in SESSIONS:
        sent = run_dir / "codex" / stage / "owner-prompt.txt"
        if sent.exists() and sent.read_text().strip() != str(prompts.get(stage, "")).strip():
            findings.append(f"{stage}: the words sent are not the fixture's words")
    return findings


def session_isolation_findings(run_dir: Path) -> list[str]:
    return p9.session_isolation_findings(run_dir, SESSIONS)


# ── exactly one send per target ──────────────────────────────────────────


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


def exactly_once_findings(fixture: dict[str, Any], *, ledger: Path = LEDGER_PATH, folder: Path | None = None,
                          comments: Callable[[], list[dict[str, Any]]] | None = None,
                          targets: Iterable[str] = ("file", "github")) -> list[str]:
    """Why a REAL send to a target would be a second one (empty: none sent yet).

    Three independent reads, any one refuses: the ledger names the target; the
    folder already holds a file with the fixture's exact bytes; the issue
    already carries a comment with the fixture's marker.
    """
    found: list[str] = []
    wanted = set(targets)
    body, marker = body_bytes(fixture), str(fixture["marker"])
    if ledger.exists():
        for entry in json.loads(ledger.read_text()).get("sends") or []:
            if entry.get("target") in wanted:
                found.append(f"{entry['target']}: the ledger records a real send at {entry.get('pressed_at')}")
    if "file" in wanted:
        where = folder or Path(fixture["destinations"]["file"]["real_folder"])
        if where.is_dir():
            for path in sorted(where.iterdir()):
                if path.is_file() and path.read_bytes() == body:
                    found.append(f"file: {path} already holds the fixture's bytes")
    if "github" in wanted and comments is not None:
        for comment in comments():
            if marker in str(comment.get("body") or ""):
                found.append(f"github: {comment.get('html_url')} already carries the fixture's marker")
    return found


def record_real_press(ledger: Path, entry: dict[str, Any]) -> None:
    """Append one real press to the ledger (written after the press, whatever its outcome)."""
    data = json.loads(ledger.read_text()) if ledger.exists() else {
        "about": "PHILO-10-06: the real sends, one per target, by the owner's word of 2026-09-29. "
                 "scripts/philo10_send_job.py run --real refuses a target named here.",
        "sends": []}
    data["sends"].append(entry)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


# ── the gh login file (the one file taken from the real HOME) ────────────


def copy_gh_login(hub_home: Path, source: Path = GH_HOSTS) -> dict[str, Any]:
    target = hub_home / ".config" / "gh" / "hosts.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(target.parent, 0o700)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(source.read_bytes())
    return {"copied_to": str(target), "mode": oct(target.stat().st_mode & 0o777), "source": "~/.config/gh/hosts.yml"}


def delete_gh_login(hub_home: Path) -> dict[str, Any]:
    target = hub_home / ".config" / "gh"
    shutil.rmtree(target, ignore_errors=True)
    return {"deleted": str(target), "exists_after": target.exists()}


def gh_credential_findings(root: Path, source: Path = GH_HOSTS) -> list[dict[str, Any]]:
    """Every retained file holding a gh token (by shape, or the login file's own token values)."""
    values: set[str] = set()
    if source.exists():
        for match in re.finditer(r"oauth_token:\s*(\S+)", source.read_text()):
            values.add(match.group(1))
    findings = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="replace")
        hits = len(GH_TOKEN_RE.findall(text)) + sum(text.count(v) for v in values if len(v) >= 8)
        if hits or path.name == "hosts.yml":
            findings.append({"file": str(path.relative_to(root)), "gh_credential": hits or "login file"})
    return findings


# ── the rehearsal runner (nothing leaves) ────────────────────────────────


def rehearsal_runner(fixture: dict[str, Any], path: Path) -> Path:
    gh = fixture["destinations"]["github"]
    script = {
        "about": "PHILO-10-06 rehearsal: gh answers as a signed-in gh would; nothing leaves the machine.",
        "answers": [
            {"argv_prefix": ["gh", "api", "user"], "code": 0,
             "stdout": json.dumps({"login": gh["login"], "id": 1}), "stderr": ""},
            {"argv_prefix": ["gh", gh["kind"], "comment"], "code": 0,
             "stdout": f"https://{gh['host']}/{gh['repo']}/issues/{gh['number']}#issuecomment-1\n", "stderr": ""},
        ],
    }
    path.write_text(json.dumps(script, indent=2))
    return path


# ── the seed (the owner's contract; fixed before the sessions) ───────────


def _owner(hub: Any, name: str, args: dict[str, Any]) -> Any:
    refused, body = p9._owner_call(hub, name, args)
    if refused:
        raise RuntimeError(f"{name} refused: {body}")
    return body


def seed(hub: Any, fixture: dict[str, Any], folder: Path) -> dict[str, Any]:
    """The project, its published update (the fixture's exact text) and the two saved destinations."""
    pid = _owner(hub, "project.create", {"name": fixture["project"]})["project"]["id"]
    status, drafted = hub.api("POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})
    if status >= 400:
        raise RuntimeError(f"draft failed: {status} {drafted}")
    uid = drafted["update"]["id"]
    _owner(hub, "project.update_draft", {"update_id": uid, "body_md": fixture["update_body"]})
    published = _owner(hub, "project.publish_update", {"update_id": uid})
    dests = fixture["destinations"]
    saved = {
        "file": _owner(hub, "channel.save_destination",
                       {"name": dests["file"]["name"], "channel": "file", "folder": str(folder)})["destination"],
        "github": _owner(hub, "channel.save_destination",
                         {"name": dests["github"]["name"], "channel": "github", "host": dests["github"]["host"],
                          "repo": dests["github"]["repo"], "kind": dests["github"]["kind"],
                          "number": dests["github"]["number"]})["destination"],
    }
    return {"seeded_at": datetime.now(timezone.utc).isoformat(), "project_id": pid, "update_id": uid,
            "published": {k: published.get(k) for k in ("id", "lifecycle", "published_at")}
            if isinstance(published, dict) else published,
            "destinations": saved}


def seed_findings(fixture: dict[str, Any], seeded: dict[str, Any], folder: Path) -> list[str]:
    f: list[str] = []
    gh = seeded["destinations"]["github"]
    if gh.get("account") != {"host": fixture["destinations"]["github"]["host"],
                             "login": fixture["destinations"]["github"]["login"]}:
        f.append(f"the GitHub destination froze the account {gh.get('account')}, not the fixture's login")
    if seeded["destinations"]["file"].get("target", {}).get("folder") != os.path.realpath(folder):
        f.append(f"the folder destination froze {seeded['destinations']['file'].get('target')}")
    return f


# ── the checks (content, never a success flag) ───────────────────────────


def _sends(hub: Any, uid: str) -> list[dict[str, Any]]:
    return _owner(hub, "channel.sends", {"update_id": uid})["sends"]


def prepare_findings(fixture: dict[str, Any], seeded: dict[str, Any], sends: list[dict[str, Any]],
                     previews: dict[str, str]) -> list[str]:
    """After the agent session: exactly one PREPARED send per destination, by the agent, the frozen bytes
    the owner's own preview names; nothing else moved."""
    f: list[str] = []
    identity = fixture["agent"]["identity"]
    for key, dest in seeded["destinations"].items():
        rows = [s for s in sends if s.get("destination_id") == dest["id"]]
        if len(rows) != 1:
            f.append(f"{key}: {len(rows)} sends, not one prepared send")
            continue
        row = rows[0]
        if row.get("state") != "prepared":
            f.append(f"{key}: the send is {row.get('state')!r}, not prepared")
        if row.get("prepared_by") != {"kind": "agent", "identity": identity}:
            f.append(f"{key}: prepared by {row.get('prepared_by')}, not the agent {identity}")
        if row.get("payload_digest") != previews.get(key):
            f.append(f"{key}: the frozen digest is not the owner's preview digest")
        if row.get("payload_digest") != hashlib.sha256(body_bytes(fixture)).hexdigest():
            f.append(f"{key}: the frozen bytes are not the fixture's text")
    extra = [s for s in sends if s.get("destination_id") not in {d["id"] for d in seeded["destinations"].values()}]
    if extra:
        f.append(f"sends to destinations the fixture does not name: {extra}")
    return f


def agent_receipt_findings(fixture: dict[str, Any], receipts: list[dict[str, Any]]) -> list[str]:
    """The agent's receipts: its prepares succeeded under its own identity; every send refused
    owner_principal_required; no other write succeeded."""
    f: list[str] = []
    agent = fixture["agent"]
    top = [r for r in receipts if not r["operation"].get("parent_operation_id")]
    for r in top:
        op = r["operation"]
        if op.get("principal_kind") != "agent" or op.get("principal_identity") != agent["identity"]:
            f.append(f"{op['name']} {op['operation_id']} actor is {op.get('principal_kind')}:{op.get('principal_identity')}")
    prepares = [r for r in top if r["operation"]["name"] == agent["prepares"]]
    if [r["receipt"].get("state") for r in prepares].count("succeeded") != 2:
        f.append(f"{[r['receipt'].get('state') for r in prepares]} prepare receipts, not two succeeded")
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


def owner_press_findings(fixture: dict[str, Any], key: str, send: dict[str, Any], receipt: dict[str, Any],
                         operation: dict[str, Any] | None) -> list[str]:
    f: list[str] = []
    if send.get("state") != "sent":
        f.append(f"{key}: the send is {send.get('state')!r} ({send.get('reason')!r}), not sent")
    if (receipt.get("state"), receipt.get("actor_kind")) != ("succeeded", "owner"):
        f.append(f"{key}: the press receipt is {receipt.get('state')!r} by {receipt.get('actor_kind')!r}")
    if (operation or {}).get("name") != "channel.send":
        f.append(f"{key}: the press operation is {(operation or {}).get('name')!r}")
    proof = send.get("proof") or {}
    digest = hashlib.sha256(body_bytes(fixture)).hexdigest()
    if key == "file":
        if proof.get("sha256") != digest or proof.get("size") != len(body_bytes(fixture)):
            f.append(f"file: the proof {proof} is not the fixture's bytes")
        if proof.get("path") != send.get("file_path"):
            f.append("file: the proof's path is not the send's file path")
    else:
        gh = fixture["destinations"]["github"]
        want = rf"^https://{re.escape(gh['host'])}/{re.escape(gh['repo'])}/issues/{gh['number']}#issuecomment-\d+$"
        if not re.match(want, str(proof.get("url") or "")):
            f.append(f"github: the proof URL {proof.get('url')!r} is not a comment on the frozen issue")
    return f


def file_readback(fixture: dict[str, Any], send: dict[str, Any], folder: Path) -> dict[str, Any]:
    """The file read back independently of the hub: its bytes are the frozen bytes."""
    path = Path(str((send.get("proof") or {}).get("path") or ""))
    data = path.read_bytes() if path.is_file() else b""
    body = body_bytes(fixture)
    return {"path": str(path), "in_folder": path.parent == Path(os.path.realpath(folder)),
            "exists": path.is_file(), "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "bytes_equal_frozen": data == body, "mode": oct(path.stat().st_mode & 0o777) if path.exists() else None}


def github_readback(fixture: dict[str, Any], send: dict[str, Any], home: Path) -> dict[str, Any]:
    """The comment read back from GitHub itself (``gh api``): its body equals the frozen bytes."""
    url = str((send.get("proof") or {}).get("url") or "")
    comment_id = url.rsplit("#issuecomment-", 1)[-1]
    gh = fixture["destinations"]["github"]
    comment = gh_json([f"repos/{gh['repo']}/issues/comments/{comment_id}"], home)
    body = str(comment.get("body") or "")
    return {"api": f"GET repos/{gh['repo']}/issues/comments/{comment_id}", "html_url": comment.get("html_url"),
            "url_equals_proof": comment.get("html_url") == url, "login": (comment.get("user") or {}).get("login"),
            "created_at": comment.get("created_at"),
            "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "body_equals_frozen": body.encode("utf-8") == body_bytes(fixture),
            "body_equals_frozen_trailing_whitespace_aside": body.rstrip() == fixture["update_body"].rstrip()}


def recorded_readback(fixture: dict[str, Any], hub_home: Path) -> dict[str, Any]:
    """Rehearsal: the recording runner's log (the body file the CLI would read) against the frozen bytes."""
    log = hub_home / "graph-walk-cli-calls.jsonl"
    calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    creates = [c for c in calls if c["argv"][:3] == ["gh", fixture["destinations"]["github"]["kind"], "comment"]]
    return {"creates": len(creates), "body_sha256": [c.get("body_sha256") for c in creates],
            "body_equals_frozen": [c.get("body_sha256") == hashlib.sha256(body_bytes(fixture)).hexdigest()
                                   for c in creates]}


def readback_findings(key: str, back: dict[str, Any], real: bool) -> list[str]:
    if key == "file":
        return [] if back.get("exists") and back.get("bytes_equal_frozen") and back.get("in_folder") else \
            [f"file: the read-back does not match: {back}"]
    if not real:
        return [] if back.get("creates") == 1 and all(back.get("body_equals_frozen") or [False]) else \
            [f"github (recorded): {back}"]
    if not (back.get("url_equals_proof") and back.get("login") and
            (back.get("body_equals_frozen") or back.get("body_equals_frozen_trailing_whitespace_aside"))):
        return [f"github: the read-back does not match: {back}"]
    return []


def check_findings(calls: list[tuple[str, dict[str, Any], str]], proofs: dict[str, str],
                   ops: list[dict[str, Any]]) -> list[str]:
    """The fresh session found where the update went and read each proof; it wrote nothing."""
    f: list[str] = []
    for key, proof in proofs.items():
        if not any(json.dumps(proof)[1:-1] in text for _n, _a, text in calls):
            f.append(f"no answer in the session carried the {key} proof")
    written = [op["name"] for op in ops if op.get("state") == "succeeded"]
    if written:
        f.append(f"the check session wrote: {written}")
    return f


# ── the face (the Send face's own facts) ─────────────────────────────────

UP = "[data-testid=update-posture]"
DS = "[data-testid=destinations]"


def _facts_js() -> str:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from tests.e2e._send_face_glass import FACTS

    return FACTS


CONNECTION_FACTS = r"""() => [...document.querySelectorAll('[data-testid^=connections-]')]
  .filter((e) => e.classList.contains('connections-tool-row') && e.getBoundingClientRect().height > 0)
  .map((e) => ({testid: e.dataset.testid, text: e.innerText.replace(/\s+/g, ' ').trim()}))"""


def _seat(page: Any, selector: str) -> None:
    page.evaluate("(s) => { const e = document.querySelector(s); if (e) e.scrollIntoView({block: 'center'}); }", selector)
    page.wait_for_timeout(350)


def _open_room_update(page: Any, hub: Any, pid: str, uid: str, glass: Any) -> None:
    p9._stage(page, hub, "open-project-memory", f"project:{pid}")
    glass._normal_chair(page)
    page.locator("[data-testid=room-body]").wait_for(timeout=20_000)
    page.locator("[data-testid=updates-verb]").click()
    page.locator("[data-testid=update-list]").wait_for(timeout=20_000)
    page.wait_for_timeout(600)


def _open_update(page: Any, uid: str) -> None:
    page.locator(f"[data-testid=update-list-item]:has([data-update-id='{uid}'])").first.click()
    page.locator("[data-testid=update-editor]").wait_for(timeout=20_000)
    page.locator("[data-testid=send-well]").wait_for(timeout=20_000)
    page.wait_for_timeout(900)


def _prow(name: str) -> str:
    return f"li.surface-ledger-row:has(> [data-testid=prepared-row] [data-destination='{name}'])"


def shoot_prepared(run_dir: Path, pages: dict[int, Any], hub: Any, pid: str, uid: str, glass: Any) -> dict[str, Any]:
    """PREPARED at both widths: the update list's chip and the two prepared rows, BY the agent."""
    facts_js = _facts_js()
    out: dict[str, Any] = {"shots": [], "widths": {}}
    for width, page in pages.items():
        _open_room_update(page, hub, pid, uid, glass)
        listed = page.evaluate(facts_js, UP)
        out["shots"].append(p9._snap(run_dir, page, "1-prepared-list", width))
        _open_update(page, uid)
        page.locator("[data-testid=prepared-row]").first.wait_for(timeout=20_000)
        _seat(page, "[data-testid=prepared-list]")
        well = page.evaluate(facts_js, UP)
        out["shots"].append(p9._snap(run_dir, page, "2-prepared-well", width))
        out["widths"][width] = {"list_chips": listed.get("list_chips"), "prepared": well.get("prepared"),
                                "prepared_open": well.get("prepared_open"), "preview_fields": well.get("preview_fields"),
                                "small_text": well.get("small_text"), "raw_buttons": well.get("raw_buttons"),
                                "h_overflow": well.get("h_overflow"), "modal": well.get("modal")}
    return out


def prepared_face_findings(fixture: dict[str, Any], face: dict[str, Any]) -> list[str]:
    f: list[str] = []
    by = f"BY {fixture['agent']['identity'].upper()}"
    for width, facts in face["widths"].items():
        if not any("PREPARED ×2" in c for c in facts.get("list_chips") or []):
            f.append(f"{width}: the update list does not say PREPARED ×2: {facts.get('list_chips')}")
        rows = facts.get("prepared") or []
        for dest in fixture["destinations"].values():
            if not any(dest["name"] in r and "PREPARED" in r and by in r for r in rows):
                f.append(f"{width}: no PREPARED row {by} for {dest['name']}: {rows}")
        f += _hygiene(width, facts)
    return f


def _hygiene(width: Any, facts: dict[str, Any]) -> list[str]:
    f = []
    small = (facts.get("small_text") or {}).get("touched") if isinstance(facts.get("small_text"), dict) else None
    if small:
        f.append(f"{width}: touched text under 12 px {small}")
    raw = (facts.get("raw_buttons") or {}).get("touched") if isinstance(facts.get("raw_buttons"), dict) else None
    if raw:
        f.append(f"{width}: raw buttons {raw}")
    if facts.get("h_overflow"):
        f.append(f"{width}: horizontal overflow")
    if facts.get("modal"):
        f.append(f"{width}: a modal")
    return f


def press(page: Any, name: str, on_click: Callable[[], None] | None = None) -> dict[str, Any]:
    """The owner's Send on one prepared row (the face's own verb; its route is POST /api/channels/send)."""
    row = _prow(name)
    page.locator(row).first.wait_for(timeout=20_000)
    if not page.locator(f"{row} [data-testid=prepared-open]").count():
        page.locator(f"{row} > .surface-ledger-line").click()
    verb = page.locator(f"{row} [data-testid=prepared-send]")
    verb.wait_for(timeout=20_000)
    _seat(page, f"{row} [data-testid=prepared-send]")
    with page.expect_response(lambda r: r.url.endswith("/api/channels/send") and r.request.method == "POST",
                              timeout=180_000) as answer:
        if on_click is not None:
            on_click()  # the ledger names the press BEFORE it happens (a real send is never made twice)
        verb.click()
    body = answer.value.json()
    page.wait_for_function(
        """(name) => [...document.querySelectorAll('[data-testid=prepared-result] [data-destination]')]
            .some((e) => e.dataset.destination === name && ['sent', 'failed', 'unknown'].includes(e.dataset.state))""",
        arg=name, timeout=60_000)
    page.wait_for_timeout(600)
    return {"status": answer.value.status, "outcome": body.get("outcome"), "send_id": (body.get("send") or {}).get("id"),
            "operation_id": body.get("operation_id"), "receipt": body.get("receipt")}


def shoot_sent(run_dir: Path, pages: dict[int, Any], hub: Any, pid: str, uid: str, glass: Any) -> dict[str, Any]:
    """SENT at both widths: DELIVERY ×2 on the list; the results SAVED + POSTED with proofs, BY the agent;
    the history rows; the Destinations group and the connections (the named limits: not set up)."""
    facts_js = _facts_js()
    out: dict[str, Any] = {"shots": [], "widths": {}}
    for width, page in pages.items():
        _open_room_update(page, hub, pid, uid, glass)
        listed = page.evaluate(facts_js, UP)
        out["shots"].append(p9._snap(run_dir, page, "3-sent-list", width))
        _open_update(page, uid)
        page.locator("[data-testid=prepared-result]").first.wait_for(timeout=20_000)
        _seat(page, "[data-testid=prepared-list]")
        results = page.evaluate(facts_js, UP)
        out["shots"].append(p9._snap(run_dir, page, "4-sent-results", width))
        page.locator("[data-testid=delivery-row]").first.wait_for(timeout=20_000)
        _seat(page, "[data-testid=delivery-history]")
        history = page.evaluate(facts_js, UP)
        out["shots"].append(p9._snap(run_dir, page, "5-sent-history", width))
        p9._stage(page, hub, "configure-settings", "integrations")
        glass._normal_chair(page)
        page.locator(DS).wait_for(timeout=20_000)
        page.wait_for_timeout(900)
        _seat(page, DS)
        dests = page.evaluate(facts_js, DS)
        out["shots"].append(p9._snap(run_dir, page, "6-destinations", width))
        conns = page.evaluate(CONNECTION_FACTS)
        _seat(page, "[data-testid=connections-jira], [data-testid^=connections-jira-conn-]")
        out["shots"].append(p9._snap(run_dir, page, "7-connections-named-limits", width))
        out["widths"][width] = {
            "list_chips": listed.get("list_chips"), "prepared_results": results.get("prepared_results"),
            "history": history.get("history"), "history_outcomes": history.get("history_outcomes"),
            "history_head": history.get("history_head"), "destinations": dests.get("destinations"),
            "connections": conns, "small_text": history.get("small_text"), "raw_buttons": history.get("raw_buttons"),
            "h_overflow": history.get("h_overflow") or results.get("h_overflow"), "modal": history.get("modal")}
    return out


def sent_face_findings(fixture: dict[str, Any], face: dict[str, Any], sends: dict[str, dict[str, Any]]) -> list[str]:
    f: list[str] = []
    by = f"BY {fixture['agent']['identity'].upper()}"
    for width, facts in face["widths"].items():
        if not any("DELIVERY ×2" in c for c in facts.get("list_chips") or []):
            f.append(f"{width}: the update list does not say DELIVERY ×2: {facts.get('list_chips')}")
        results = facts.get("prepared_results") or []
        history = facts.get("history") or []
        for key, dest in fixture["destinations"].items():
            proof = (sends.get(key) or {}).get("proof") or {}
            shown = proof.get("path") if key == "file" else str(proof.get("url") or "").split("#")[-1]
            if not any(dest["name"] in r and dest["outcome_word"] in r and by in r for r in results):
                f.append(f"{width}: no {dest['outcome_word']} result {by} for {dest['name']}: {results}")
            if key == "file" and not any(str(shown) in r for r in results):
                f.append(f"{width}: the SAVED result does not show the path {shown}")
            if not any(dest["name"] in r and dest["outcome_word"] in r for r in history):
                f.append(f"{width}: no history row {dest['outcome_word']} {dest['name']}: {history}")
        if sorted(facts.get("history_outcomes") or []) != ["sent", "sent"]:
            f.append(f"{width}: the history outcomes are {facts.get('history_outcomes')}")
        names = " ".join(facts.get("destinations") or [])
        for dest in fixture["destinations"].values():
            if dest["name"] not in names:
                f.append(f"{width}: the Destinations group does not list {dest['name']}")
        # The named limits (no account yet): Jira and Confluence have no signed-in connection (the face's
        # words on a hub that never saw an account: NEVER CHECKED, or NOT SET UP), and no Jira, Confluence
        # or email destination is saved.
        conns = {c["testid"]: c["text"] for c in facts.get("connections") or []}
        for product in ("jira", "confluence"):
            row = conns.get(f"connections-{product}") or ""
            if not row or "CONNECTED" in row.upper().replace("NOT CONNECTED", "") or not (
                    "NEVER CHECKED" in row.upper() or "NOT SET UP" in row.upper()):
                f.append(f"{width}: the {product} connection row does not show it not set up: {row!r}")
        for word in ("JIRA", "CONFLUENCE", "EMAIL"):
            if any(f" {word} " in f" {d.upper()} " for d in facts.get("destinations") or []):
                f.append(f"{width}: a {word.lower()} destination is saved")
        f += _hygiene(width, facts)
    return f


# ── the run ──────────────────────────────────────────────────────────────


def _run(args: argparse.Namespace) -> int:
    real = bool(args.real)
    fixture_path = Path(args.fixture).resolve()
    fixture = load_fixture(fixture_path)
    # Exactly once, BEFORE anything boots (the ledger and the folder; the issue after the gh copy).
    if real:
        early = exactly_once_findings(fixture, targets=("file", "github"))
        if early:
            for line in early:
                print(f"REFUSED {line}")
            print("PHILO10_SEND_JOB_REFUSED a real send to a target that already has one; nothing booted")
            return 4
        if not GH_HOSTS.exists():
            print("PHILO10_SEND_JOB_REFUSED no gh login file in the real HOME")
            return 4
    p7.CLIENT[0] = "codex"
    p7.CODEX_AUTH[0] = Path(args.codex_auth).expanduser().resolve()
    run_dir = Path(args.out).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    run_dir = run_dir / (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + ("-send-job-real" if real else "-send-job"))
    run_dir.mkdir()
    started_at = datetime.now(timezone.utc)
    fixture_record = write_run_fixture(run_dir, fixture_path)
    temp_root = Path(tempfile.mkdtemp(prefix="philo10-06-"))
    hub_home = temp_root / "hub-home"
    hub_home.mkdir()
    if real:
        folder = Path(fixture["destinations"]["file"]["real_folder"])
        folder.mkdir(parents=True, exist_ok=True)  # he asked to file there
    else:
        folder = temp_root / "outbox"
        folder.mkdir()
    gw = p7._gw()
    provenance = gw.base_provenance(engine_mode="none")
    provenance["engine_mode_reason"] = "the job calls no model: the update's text is the fixture's"
    p7._json_dump(run_dir / "run.json", {
        "claim": p7.CLAIM_CODEX, "client": "codex", "model": p7.MODEL, "reasoning_effort": p7.EFFORT,
        "label": REVIEW_LABEL, "observed_sitting": False, "engine_mode": "none", "mode": "real" if real else "rehearsal",
        "legs": ["agent"], "sessions": list(SESSIONS), "press": PRESS_LABEL, "temp_root": str(temp_root),
        "hub_home": str(hub_home), "folder": str(folder), "fixture_sha256": fixture_record["source_sha256"],
        "named_limits": fixture["named_limits"],
    })
    blocked: list[str] = []
    out: dict[str, Any] = {"sessions": {}, "checks": {}, "press": {}, "readback": {}}
    hub = None
    gh_file: dict[str, Any] = {}
    browser = None
    try:
        if real:
            gh_file["copy"] = copy_gh_login(hub_home)
            gh_file["login"] = gh_json(["user"], hub_home).get("login")
            if gh_file["login"] != fixture["destinations"]["github"]["login"]:
                raise RuntimeError(f"gh is signed in as {gh_file['login']!r}, not the fixture's login")
            late = exactly_once_findings(fixture, targets=("github",), comments=lambda: issue_comments(fixture, hub_home))
            if late:
                raise RuntimeError(f"exactly once: {late}")
        runner = None if real else rehearsal_runner(fixture, temp_root / "gh-rehearsal.json")
        hub = gw.Hub(hub_home, token=TOKEN, record_rehearsal=True, transcript_path=hub_home / "rehearsal-transcript.jsonl",
                     cli_runner=runner).start()
        p7._json_dump(run_dir / "hub-proof.json", p5._hub_proof(hub, hub_home))
        seeded = seed(hub, fixture, folder)
        p7._json_dump(run_dir / "seed.json", seeded)
        out["checks"]["seed"] = seed_findings(fixture, seeded, folder)
        blocked += [f"seed: {x}" for x in out["checks"]["seed"]]
        pid, uid = seeded["project_id"], seeded["update_id"]
        previews = {key: _owner(hub, "channel.preview", {"update_id": uid, "destination_id": d["id"]})["payload_digest"]
                    for key, d in seeded["destinations"].items()}

        # 1. AGENT: prepare cold, and try to send (refused).
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
        rowid = p7._max_op_rowid(hub)
        out["sessions"]["agent_prepare"], stops = p9._session(
            run_dir, temp_root, hub, "agent_prepare", "agent", fixture["prompts"]["agent_prepare"], bearer,
            args.codex_timeout)
        blocked += stops
        ops = p9._ops_since(hub, rowid)
        receipts = p9._receipts(gw, hub, ops, provenance)
        sends = _sends(hub, uid)
        agent_send_by_driver = None
        if not any(r["operation"]["name"] == "channel.send" for r in receipts):
            # Codex did not try to send: the driver makes the agent's one attempt with the same credential,
            # recorded apart as the driver's (never as Codex's).
            prepared = [s for s in sends if s.get("state") == "prepared"]
            if prepared:
                refused, body = p9._agent_call(hub, bearer, "channel.send", {"send_id": prepared[0]["id"]})
                agent_send_by_driver = {"refused": refused, "answer": body,
                                        "label": "the agent's send made by the driver with the agent's credential"}
                more = p9._ops_since(hub, max(o["rid"] for o in ops) if ops else rowid)
                receipts += p9._receipts(gw, hub, more, provenance)
                sends = _sends(hub, uid)
        checks = {"prepared": prepare_findings(fixture, seeded, sends, previews),
                  "receipts": agent_receipt_findings(fixture, receipts),
                  "nothing_left": [] if not any(folder.iterdir()) else [f"the folder is not empty: {os.listdir(folder)}"]}
        if not real:
            checks["nothing_left"] += [] if recorded_readback(fixture, hub_home)["creates"] == 0 else ["gh comment ran"]
        p7._json_dump(run_dir / "agent_prepare" / "readbacks.json",
                      {"operations": ops, "receipts": receipts, "sends": sends, "previews": previews,
                       "agent_send_by_driver": agent_send_by_driver})
        out["checks"]["agent_prepare"] = checks
        out["agent_send_by_driver"] = agent_send_by_driver
        blocked += [f"agent_prepare {kind}: {x}" for kind, rows in checks.items() for x in rows]

        # 2. The face: PREPARED at both widths; the owner's press at 1440; SENT at both widths.
        from playwright.sync_api import sync_playwright

        glass = p9._glass()
        glass._ensure_build()
        by_dest = {key: next(s for s in sends if s["destination_id"] == d["id"])
                   for key, d in seeded["destinations"].items() if any(s["destination_id"] == d["id"] for s in sends)}
        with sync_playwright() as play:
            browser, pages, errors = p9._pages(play, hub)
            try:
                prepared_face = shoot_prepared(run_dir, pages, hub, pid, uid, glass)
                out["face_prepared"] = prepared_face
                out["checks"]["face_prepared"] = prepared_face_findings(fixture, prepared_face)
                blocked += [f"face prepared: {x}" for x in out["checks"]["face_prepared"]]
                page = pages[1440]
                _open_room_update(page, hub, pid, uid, glass)
                _open_update(page, uid)
                for key in fixture["press_order"]:
                    dest = fixture["destinations"][key]
                    if key not in by_dest:
                        blocked.append(f"press {key}: nothing prepared")
                        continue
                    guard: dict[str, Any] = {}
                    if real:
                        guard["exactly_once"] = exactly_once_findings(
                            fixture, targets=(key,),
                            comments=(lambda: issue_comments(fixture, hub_home)) if key == "github" else None)
                        if key == "github":
                            guard["gh_api_user_login"] = gh_json(["user"], hub_home).get("login")
                        if guard["exactly_once"] or (key == "github" and guard["gh_api_user_login"] != dest["login"]):
                            blocked.append(f"press {key}: refused by the guard {guard}")
                            out["press"][key] = {"guard": guard, "pressed": False}
                            continue
                    pressed_at = datetime.now(timezone.utc).isoformat()
                    ledger_entry = {"target": key, "pressed_at": pressed_at, "send_id": by_dest[key]["id"],
                                    "run": run_dir.name}
                    answer = press(page, dest["name"],
                                   on_click=(lambda e=ledger_entry: record_real_press(LEDGER_PATH, e)) if real else None)
                    send = _owner(hub, "channel.sends", {"send_id": by_dest[key]["id"]})["sends"][0]
                    read = p7._receipt(gw, hub, str(send.get("send_operation_id") or answer.get("operation_id")),
                                       provenance)
                    press_f = owner_press_findings(fixture, key, send, read["receipt"], read["operation"])
                    back = (file_readback(fixture, send, folder) if key == "file"
                            else github_readback(fixture, send, hub_home) if real
                            else recorded_readback(fixture, hub_home))
                    press_f += readback_findings(key, back, real)
                    if real:
                        record_real_press_proof(LEDGER_PATH, key, send.get("proof"), send.get("state"))
                    out["press"][key] = {"guard": guard, "pressed": True, "pressed_at": pressed_at, "face_answer": answer,
                                         "send": send, "receipt": read["receipt"], "operation": read["operation"],
                                         "label": PRESS_LABEL}
                    out["readback"][key] = back
                    out["checks"][f"press_{key}"] = press_f
                    blocked += [f"press {key}: {x}" for x in press_f]
                    by_dest[key] = send

                # 3. AGENT, a fresh session: where did it go, with what proof.
                rowid = p7._max_op_rowid(hub)
                out["sessions"]["agent_check"], stops = p9._session(
                    run_dir, temp_root, hub, "agent_check", "agent", fixture["prompts"]["agent_check"], bearer,
                    args.codex_timeout)
                blocked += stops
                calls = p9._tool_calls(p9._window(hub, run_dir, "agent_check"))
                proofs = {k: str((s.get("proof") or {}).get("path" if k == "file" else "url") or "")
                          for k, s in by_dest.items()}
                check_ops = p9._ops_since(hub, rowid)
                out["agent_check_tools"] = [name for name, _a, _t in calls]
                out["checks"]["agent_check"] = check_findings(calls, proofs, check_ops)
                blocked += [f"agent_check: {x}" for x in out["checks"]["agent_check"]]

                sent_face = shoot_sent(run_dir, pages, hub, pid, uid, glass)
                out["face_sent"] = sent_face
                out["checks"]["face_sent"] = sent_face_findings(fixture, sent_face, by_dest)
                blocked += [f"face sent: {x}" for x in out["checks"]["face_sent"]]
                out["page_errors"] = errors
                blocked += [f"page error: {e}" for e in errors]
            finally:
                browser.close()
        _rec, updates = p9._read(gw, hub, "project.list_updates", {"project_id": pid}, provenance)
        mine = [u for u in (updates or {}).get("updates") or [] if u.get("id") == uid]
        out["deliveries"] = (mine[0].get("deliveries") if mine else None) or []
        p7._json_dump(run_dir / "owner_press" / "readbacks.json",
                      {"press": out["press"], "readback": out["readback"], "sends": _sends(hub, uid),
                       "deliveries": out["deliveries"]})
    except Exception as exc:  # noqa: BLE001 - the run records every stop
        blocked.append(f"driver: {type(exc).__name__}: {exc}")
        p7._write_text(run_dir / "run-error.txt", f"{type(exc).__name__}: {exc}\n")
    finally:
        if hub is not None:
            p7._json_dump(run_dir / "hub-proof-final.json", p5._hub_proof(hub, hub_home))
            if hub.db_path and Path(str(hub.db_path)).exists():
                p5._backup_db(Path(str(hub.db_path)), run_dir / "db-proof.sqlite")
            hub.stop()
            p7._write_text(run_dir / "hub.log", "\n".join(hub.lines) + "\n")
            transcript = getattr(hub, "transcript_path", None)
            if transcript and Path(transcript).exists():
                shutil.copy2(transcript, run_dir / "rehearsal-transcript.jsonl")
            calls_log = hub_home / "graph-walk-cli-calls.jsonl"
            if calls_log.exists():
                shutil.copy2(calls_log, run_dir / "cli-calls.jsonl")
        if real:
            gh_file["delete"] = delete_gh_login(hub_home)
        for auth in temp_root.glob("*/home/.codex/auth.json"):
            auth.unlink(missing_ok=True)
        p7._json_dump(run_dir / "gh-login-file.json", gh_file or {"mode": "rehearsal: no file taken from the real HOME"})
        p7._json_dump(run_dir / "provenance.json", provenance)
        p7._json_dump(run_dir / "legs.json", out)
    redaction = redact_run(run_dir)
    fences = {
        "fixture_before_run": fixture_before_run_findings(run_dir, fixture_path),
        "session_isolation": session_isolation_findings(run_dir),
        "zero_read": {stage: len(zero_read_findings(read_events(run_dir / "codex" / stage / "events.jsonl")))
                      for stage in SESSIONS if (run_dir / "codex" / stage / "events.jsonl").exists()},
        "account_leaks": account_leak_findings(run_dir),
        "gh_credentials": gh_credential_findings(run_dir),
        "gh_login_file_deleted": [] if not real or not (hub_home / ".config" / "gh").exists() else ["the copy survives"],
    }
    for kind in ("fixture_before_run", "session_isolation", "account_leaks", "gh_credentials", "gh_login_file_deleted"):
        blocked += [f"fence {kind}: {x}" for x in fences[kind]]
    blocked += [f"fence zero_read: {stage} {n}" for stage, n in fences["zero_read"].items() if n]
    p7._json_dump(run_dir / "redaction.json", {"rule": "e-mail addresses and account ids redacted (Phase 7 rule)",
                                               **redaction})
    p7._json_dump(run_dir / "fences.json", fences)
    p7._json_dump(run_dir / "run-status.json", {
        "started_at": started_at.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
        "outcome": "blocked" if blocked else "completed", "blocked": blocked, "label": REVIEW_LABEL,
        "mode": "real" if real else "rehearsal", "claim": p7.CLAIM_CODEX, "press": PRESS_LABEL,
        "named_limits": fixture["named_limits"],
    })
    print(f"RUN_DIR {run_dir}")
    print(f"MODE {'REAL' if real else 'REHEARSAL'}")
    print(f"PROOF {REVIEW_LABEL}")
    for key, back in out["readback"].items():
        print(f"READBACK {key} {json.dumps(back, sort_keys=True)}")
    print(f"OUTCOME {'BLOCKED' if blocked else 'COMPLETED'}")
    for line in blocked:
        print(f"BLOCKED {line}")
    return 0 if not blocked else 3


def record_real_press_proof(ledger: Path, key: str, proof: Any, state: Any) -> None:
    data = json.loads(ledger.read_text())
    for entry in reversed(data["sends"]):
        if entry.get("target") == key:
            entry["state"], entry["proof"] = state, proof
            break
    ledger.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


# ── the fences over a retained run (no new session, no send) ─────────────


def fence_run(run_dir: Path) -> int:
    fixture = json.loads((run_dir / "fixture.json").read_text())["fixture"]
    legs = json.loads((run_dir / "legs.json").read_text())
    prepare = json.loads((run_dir / "agent_prepare" / "readbacks.json").read_text())
    seeded = json.loads((run_dir / "seed.json").read_text())
    problems = 0
    rows: list[tuple[str, list[Any]]] = [
        ("fixture_before_run", fixture_before_run_findings(run_dir)),
        ("session_isolation", session_isolation_findings(run_dir)),
        ("account_leaks", account_leak_findings(run_dir)),
        ("gh_credentials", gh_credential_findings(run_dir)),
        ("agent receipts", agent_receipt_findings(fixture, prepare["receipts"])),
        ("agent prepared", prepare_findings(fixture, seeded, [
            s for s in prepare["sends"]], prepare["previews"])),
    ]
    for key, press in (legs.get("press") or {}).items():
        rows.append((f"owner press {key}", owner_press_findings(fixture, key, press["send"], press["receipt"],
                                                                press["operation"])))
        rows.append((f"read-back {key}", readback_findings(key, legs["readback"][key],
                                                           json.loads((run_dir / "run.json").read_text())["mode"] == "real")))
    for name, found in rows:
        problems += len(found)
        print(f"{name}={found}")
    for stage in SESSIONS:
        zero = zero_read_findings(read_events(run_dir / "codex" / stage / "events.jsonl"))
        problems += len(zero)
        print(f"{stage} zero_read={len(zero)}")
    print("FENCES GREEN" if not problems else f"FENCES RED: {problems}")
    return 0 if not problems else 1


def _parser() -> argparse.ArgumentParser:
    from tests._evidence import evidence_dir  # noqa: PLC0415 -- the evidence law decides where shots go

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help="one fresh run: two cold sessions, the owner's press, the face")
    run.add_argument("--out", default=None, help="parent directory for the unique run (default: the evidence dir)")
    run.add_argument("--real", action="store_true",
                     help="the owner's two authorized targets (exactly one send each; refused when one exists)")
    run.add_argument("--codex-timeout", type=float, default=1200)
    run.add_argument("--codex-auth", type=Path, default=Path.home() / ".codex" / "auth.json")
    run.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    guard = sub.add_parser("guard", help="the exactly-once guard alone: would a real run send again?")
    guard.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    fence = sub.add_parser("fence", help="the fences over a retained run (no new session, no send)")
    fence.add_argument("run_dir", type=Path)
    parser.set_defaults(evidence_dir=evidence_dir)
    return parser


def main(argv: list[str] | None = None) -> int:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    args = _parser().parse_args(argv)
    if args.mode == "fence":
        return fence_run(args.run_dir.resolve())
    if args.mode == "guard":
        found = exactly_once_findings(load_fixture(args.fixture.resolve()))
        for line in found:
            print(f"REFUSED {line}")
        print("GUARD REFUSES A REAL RUN" if found else "GUARD: no real send recorded")
        return 4 if found else 0
    if args.out is None:
        args.out = str(args.evidence_dir(SHOTS_REL + ("/final" if args.real else "/attempts")))
    try:
        return _run(args)
    except Exception as exc:  # noqa: BLE001
        print(f"PHILO10_SEND_JOB_BLOCKED {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
