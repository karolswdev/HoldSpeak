#!/usr/bin/env python3
"""PHILO-9-06: work in a project room without the repo (Codex, cold context).

The closing use of Phase 9. A cold-context Codex session gets the owner's
ordinary words and nothing else, and does his project job from the MCP
catalogue of an isolated rig hub. The launch is the charter's "The closing
contract" (``current-phase-status.md``): ``--client codex``, legs OWNER and
AGENT, every session in its own fresh scratch root, HOME and CODEX_HOME (the
auth file alone), a distinct session id, no resume.

The sessions, in order:

1. ``owner_job``: the OWNER makes the project, the milestone and the risk,
   asks what needs him, sets the steward to draft only, runs it, publishes
   the draft, reads the text for delivery and marks it delivered twice;
2. ``owner_find``: a fresh OWNER session finds the project from its name
   alone and reads its published, delivered update ("find it cold");
3. ``agent_ungranted`` and ``agent_granted``: the AGENT leg, a real
   Settings-issued PROJECT credential over ``/api/mcp``; refused before the
   owner's project grant, inside the bound after it; marking delivered stays
   refused. The owner then marks the agent's update delivered.

The machinery is the Phase 7 driver's (``scripts/philo7_file_and_find.py``):
the cold root, the launch-setup check, the Codex turn with its retained
rollout, the zero-read fence, the pairing of client events with hub
exchanges, the receipt read and the redaction at capture. This file adds the
fixture, the job's content checks and the three-session isolation check.

The fixture is ``story-06-fixture.json`` beside the story; the run copies it,
with the due date resolved, into the run BEFORE the first session and records
its hash. Every check compares the fixture's values, never a success flag.
The hub runs under a fresh temporary HOME; the owner's desk is never used.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
STORY_DIR = REPO / "pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract"
FIXTURE_PATH = STORY_DIR / "story-06-fixture.json"
TOKEN = "philo9-06-room-job"
REVIEW_LABEL = "REHEARSED; OWNER REVIEW PENDING"
FACE_PENDING = (
    "FACE LEG PENDING: the Room's face at 1440 and 393 is shot after PHILO-9-03 "
    "(the Room's face) merges; rerun with --face."
)
#: The sessions, in run order; each is its own cold root and Codex session.
SESSIONS = ("owner_job", "owner_find", "agent_ungranted", "agent_granted")
TERMINAL_RUN = {"completed", "failed", "interrupted"}


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


p7 = _load("philo7_file_and_find", REPO / "scripts/philo7_file_and_find.py")
p5 = p7.p5

# The fences are the Phase 7 ones, unchanged (one implementation).
read_events = p7.read_events
zero_read_findings = p7.zero_read_findings
account_leak_findings = p7.account_leak_findings
redact_run = p7.redact_run
prompt_findings = p7.prompt_findings


# ── the fixture (fixed before the run) ───────────────────────────────────


def load_fixture(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text())


def resolve_fixture(fixture: dict[str, Any], run_date: date) -> dict[str, Any]:
    """The fixture with the milestone's due date made concrete for this run."""
    resolved = json.loads(json.dumps(fixture))
    days = int(fixture["milestone"]["due_days_before_run"])
    resolved["run_date"] = run_date.isoformat()
    resolved["milestone"]["due_at"] = (run_date - timedelta(days=days)).isoformat()
    return resolved


def write_run_fixture(run_dir: Path, source: Path, run_date: date) -> dict[str, Any]:
    """Copy the fixture into the run before any session; record its hash."""
    raw = source.read_bytes()
    resolved = resolve_fixture(json.loads(raw), run_date)
    record = {
        "source": str(source.relative_to(REPO)) if source.is_relative_to(REPO) else str(source),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "fixture": resolved,
    }
    p7._json_dump(run_dir / "fixture.json", record)
    return record


def fixture_before_run_findings(run_dir: Path, source: Path = FIXTURE_PATH) -> list[str]:
    """The fixture was in the run, unchanged, before the first session began."""
    findings: list[str] = []
    path = run_dir / "fixture.json"
    if not path.exists():
        return ["the run holds no fixture.json"]
    record = json.loads(path.read_text())
    if record.get("source_sha256") != hashlib.sha256(source.read_bytes()).hexdigest():
        findings.append("the run's fixture hash differs from the story's fixture file")
    stripped = {k: v for k, v in (record.get("fixture") or {}).items() if k != "run_date"}
    stripped_milestone = dict(stripped.get("milestone") or {})
    stripped_milestone.pop("due_at", None)
    stripped["milestone"] = stripped_milestone
    if stripped != load_fixture(source):
        findings.append("the run's fixture values differ from the story's fixture file")
    written = datetime.fromisoformat(str(record.get("written_at")))
    starts: list[datetime] = []
    for stage in SESSIONS:
        timing = run_dir / "codex" / stage / "timing.json"
        if timing.exists():
            starts.append(datetime.fromisoformat(json.loads(timing.read_text())["started_at"]))
    if not starts:
        findings.append("no session timing in the run")
    elif written >= min(starts):
        findings.append(f"the fixture was written at {written.isoformat()}, not before the first session")
    prompts = (record.get("fixture") or {}).get("prompts") or {}
    for stage in SESSIONS:
        sent = run_dir / "codex" / stage / "owner-prompt.txt"
        if sent.exists() and sent.read_text().strip() != str(prompts.get(stage, "")).strip():
            findings.append(f"{stage}: the words sent are not the fixture's words")
    return findings


# ── the three-session isolation (fresh roots, distinct ids, no resume) ───


def session_isolation_findings(run_dir: Path) -> list[str]:
    """Every session: its own work root, HOME and CODEX_HOME, a lawful launch,
    a distinct session id, never resumed."""
    findings: list[str] = []
    seen: dict[str, dict[str, str]] = {"session_id": {}, "work": {}, "home": {}, "codex_home": {}}
    for stage in SESSIONS:
        stage_dir = run_dir / "codex" / stage
        setup_path = run_dir / stage / "launch-setup.json"
        if not stage_dir.exists() or not setup_path.exists():
            findings.append(f"{stage}: no retained session")
            continue
        audit = json.loads((stage_dir / "mcp-audit.json").read_text())
        setup = json.loads(setup_path.read_text())
        env = json.loads((stage_dir / "environment.json").read_text())["env"]
        command = (stage_dir / "command.txt").read_text()
        if setup.get("findings"):
            findings.append(f"{stage}: launch setup {setup['findings']}")
        if audit.get("resumed") or " resume " in command:
            findings.append(f"{stage}: the session was resumed")
        for flag in ("--ignore-user-config", "--ignore-rules", "--disable apps", "--disable plugins"):
            if flag not in command:
                findings.append(f"{stage}: the launch lacks {flag}")
        values = {"session_id": str(audit.get("session_id") or ""), "work": str(setup.get("work") or ""),
                  "home": str(env.get("HOME") or ""), "codex_home": str(env.get("CODEX_HOME") or "")}
        for key, value in values.items():
            if not value or value == "None":
                findings.append(f"{stage}: no {key}")
            elif value in seen[key]:
                findings.append(f"{stage}: {key} shared with {seen[key][value]}")
            else:
                seen[key][value] = stage
    return findings


# ── the contract readbacks (owner token, the rig's read adapter) ─────────


def _read(gw: Any, hub: Any, name: str, args: dict[str, Any], provenance: dict[str, Any]) -> Any:
    record = p5._read_op(gw, hub, name, args, provenance)
    return record, p5._response(record)


def _owner_call(hub: Any, name: str, args: dict[str, Any]) -> tuple[bool, Any]:
    """One owner tools/call over the hub's own /api/mcp (the owner's contract)."""
    hub._mcp_request_id += 1
    answer = hub.mcp({"jsonrpc": "2.0", "id": f"driver-{hub._mcp_request_id}", "method": "tools/call",
                      "params": {"name": name, "arguments": args}})
    if "error" in answer:
        return True, answer["error"]
    result = answer.get("result") or {}
    text = "".join(str(part.get("text", "")) for part in result.get("content") or [] if isinstance(part, dict))
    try:
        body: Any = json.loads(text)
    except ValueError:
        body = text
    return bool(result.get("isError")), body


def _ops_since(hub: Any, rowid: int) -> list[dict[str, Any]]:
    """Kernel operations made after ``rowid``, with their parent (read-only;
    provenance only -- each receipt is then read back through the contract)."""
    import sqlite3
    from contextlib import closing

    uri = Path(str(hub.db_path)).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(
            "SELECT rowid AS rid, operation_id, name, state, principal_kind, principal_identity,"
            " authority_basis, delegator_kind, parent_operation_id FROM kernel_operations"
            " WHERE rowid > ? ORDER BY rowid", (rowid,))]


def _receipts(gw: Any, hub: Any, ops: list[dict[str, Any]], provenance: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for op in ops:
        read = p7._receipt(gw, hub, str(op["operation_id"]), provenance)
        out.append({"operation": op, "receipt": read["receipt"]})
    return out


def _wait_run(gw: Any, hub: Any, run_id: str, provenance: dict[str, Any], timeout_s: float = 120) -> Any:
    deadline = time.monotonic() + timeout_s
    while True:
        record, run = _read(gw, hub, "project.get_steward_run", {"run_id": run_id}, provenance)
        state = ((run or {}).get("run") or {}).get("state")
        if state in TERMINAL_RUN or time.monotonic() > deadline:
            return record, run
        time.sleep(0.5)


def owner_readbacks(gw: Any, hub: Any, fixture: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    """Everything the owner job's checks compare, read back through the contract."""
    reads: dict[str, Any] = {}
    record, listed = _read(gw, hub, "project.list", {}, provenance)
    reads["project_list"] = record
    named = [p for p in (listed or {}).get("projects") or [] if p.get("name") == fixture["project"]]
    out: dict[str, Any] = {"reads": reads, "projects_named": named}
    if len(named) != 1:
        return out
    pid = str(named[0]["id"])
    out["project_id"] = pid
    reads["items"], items = _read(gw, hub, "project.item.list", {"project_id": pid}, provenance)
    out["items"] = (items or {}).get("items") or []
    reads["needs_you"], needs = _read(gw, hub, "desk.needs_you", {}, provenance)
    out["needs_you"] = needs or {}
    reads["room"], room = _read(gw, hub, "project.get_room", {"project_id": pid}, provenance)
    out["room"] = {key: (room or {}).get(key) for key in ("health", "review", "steward", "updates", "needsYou")}
    run_id = (((room or {}).get("steward") or {}).get("latest_run") or {}).get("id")
    if run_id:
        reads["steward_run"], run = _wait_run(gw, hub, str(run_id), provenance)
        out["steward_run"] = run or {}
    reads["updates"], updates = _read(gw, hub, "project.list_updates", {"project_id": pid}, provenance)
    out["updates"] = (updates or {}).get("updates") or []
    return out


def _details(item: dict[str, Any]) -> dict[str, Any]:
    raw = item.get("details") if isinstance(item.get("details"), dict) else item.get("details_json")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except ValueError:
            return {}
    return dict(raw or {})


def _effects(run: dict[str, Any]) -> list[dict[str, Any]]:
    summary = ((run.get("run") or {}).get("summary") or {})
    act = (summary.get("phase_results") or {}).get("act") or {}
    return [e for e in act.get("effect_receipts") or [] if isinstance(e, dict)]


def owner_job_findings(fixture: dict[str, Any], back: dict[str, Any]) -> list[str]:
    """The OWNER session's result against the fixture: content, not flags."""
    f: list[str] = []
    if len(back.get("projects_named") or []) != 1:
        return [f"{len(back.get('projects_named') or [])} projects named {fixture['project']!r}, not one"]
    pid = back["project_id"]
    for spec in (fixture["milestone"], fixture["risk"]):
        rows = [i for i in back.get("items") or [] if i.get("item_type") == spec["item_type"]
                and i.get("title") == spec["title"]]
        if len(rows) != 1:
            f.append(f"{len(rows)} {spec['item_type']} items titled {spec['title']!r}, not one")
            continue
        item = rows[0]
        if item.get("lifecycle") != spec["lifecycle"]:
            f.append(f"{spec['title']!r} lifecycle is {item.get('lifecycle')!r}, not {spec['lifecycle']!r}")
        if spec["item_type"] == "milestone" and str(item.get("due_at") or "")[:10] != spec["due_at"]:
            f.append(f"{spec['title']!r} is due {item.get('due_at')!r}, not {spec['due_at']!r}")
        if spec["item_type"] == "risk":
            details = _details(item)
            for key in ("likelihood", "impact", "mitigation"):
                if details.get(key) != spec[key]:
                    f.append(f"{spec['title']!r} {key} is {details.get(key)!r}, not {spec[key]!r}")
    extra = [i.get("title") for i in back.get("items") or []
             if i.get("title") not in (fixture["milestone"]["title"], fixture["risk"]["title"])]
    if extra:
        f.append(f"items the fixture does not name: {extra}")
    attention = fixture["attention"]
    needs = [i for i in (back.get("needs_you") or {}).get("items") or []
             if i.get("projectId") == pid and i.get("title") == attention["needs_you_title"]]
    if len(needs) != 1 or needs[0].get("rankClass") != attention["needs_you_rank_class"]:
        f.append(f"NEEDS YOU does not list {attention['needs_you_title']!r} as overdue: {needs}")
    health = ((back.get("room") or {}).get("health") or {}).get("assessment")
    if not health or health == attention["health_is_not"]:
        f.append(f"the room's health is {health!r}")
    steward = fixture["steward"]
    run = back.get("steward_run") or {}
    row = run.get("run") or {}
    if row.get("state") != steward["run_state"]:
        f.append(f"the steward run is {row.get('state')!r}, not {steward['run_state']!r}")
    compare = (((row.get("summary") or {}).get("phase_results") or {}).get("compare") or {})
    open_review = ((back.get("room") or {}).get("review") or {}).get("open_review_id")
    if not compare.get("review_id") or compare.get("review_id") != open_review:
        f.append(f"the run's review {compare.get('review_id')!r} is not the open review {open_review!r}")
    drafted = [e for e in _effects(run) if e.get("effect_kind") == "draft_update" and e.get("outcome") == "applied"]
    others = [e for e in _effects(run) if e.get("effect_kind") not in steward["eligible_effect_kinds"]]
    if len(drafted) != steward["drafted_updates"] or others:
        f.append(f"the run drafted {len(drafted)} updates and took {others}")
    drafted_id = ((drafted[0].get("result") or {}).get("update_id")) if drafted else None
    publication = fixture["publication"]
    published = [u for u in back.get("updates") or [] if u.get("lifecycle") == publication["lifecycle"]]
    if len(published) != 1:
        f.append(f"{len(published)} published updates, not one")
        return f
    update = published[0]
    if drafted_id and update.get("id") != drafted_id:
        f.append(f"the published update {update.get('id')} is not the one the run drafted {drafted_id}")
    for title in publication["body_names"]:
        if title not in str(update.get("body_md") or ""):
            f.append(f"the published body does not name {title!r}")
    deliveries = update.get("deliveries") or []
    names = [d.get("delivered_to") for d in deliveries]
    if names != fixture["delivery"]["delivered_to"]:
        f.append(f"the deliveries are {names}, not {fixture['delivery']['delivered_to']}")
    ops = [d.get("operation_id") for d in deliveries]
    if len(set(ops)) != len(ops) or not all(ops) or not all(d.get("delivered_at") for d in deliveries):
        f.append(f"a delivery lacks its own time or operation: {deliveries}")
    return f


#: The OWNER session's admitted writes, by name (the steward's children are
#: reported apart; they carry the run as their parent). ``project.create`` and
#: ``project.item.create`` are exempt by the charter's admission table
#: (current-phase-status.md, "exempt" rows): they add no operation; their
#: result is checked by content in :func:`owner_job_findings`.
OWNER_JOB_WRITES = {
    "project.configure_steward": 1, "project.run_steward": 1, "project.publish_update": 1,
    "project.mark_update_delivered": 2,
}


def owner_receipt_findings(receipts: list[dict[str, Any]], expected: dict[str, int] | None = None) -> list[str]:
    """Each admitted OWNER write: its count, a terminal succeeded receipt, the owner the actor."""
    expected = OWNER_JOB_WRITES if expected is None else expected
    f: list[str] = []
    top = [r for r in receipts if not r["operation"].get("parent_operation_id")]
    names = [r["operation"]["name"] for r in top]
    for name, count in expected.items():
        if names.count(name) != count:
            f.append(f"{names.count(name)} {name} operations, not {count}")
    for extra in sorted(set(names) - set(expected)):
        f.append(f"an operation the job does not name: {extra} x{names.count(extra)}")
    for r in receipts:
        receipt, op = r["receipt"], r["operation"]
        if receipt.get("state") != "succeeded":
            f.append(f"{op['name']} {op['operation_id']} receipt state {receipt.get('state')!r} ({receipt.get('outcome')!r})")
        if receipt.get("actor_kind") != "owner" or op.get("principal_kind") != "owner":
            f.append(f"{op['name']} {op['operation_id']} actor is not the owner")
    return f


def _window(hub: Any, run_dir: Path, stage: str) -> list[dict[str, Any]]:
    rows = p5._http_exchange_records(hub)
    start = json.loads((run_dir / "codex" / stage / "transcript-window.json").read_text())["exchange_start"]
    end = json.loads((run_dir / "codex" / stage / "mcp-audit.json").read_text()).get("exchange_end")
    return rows[start:end]


def _tool_calls(rows: Iterable[dict[str, Any]]) -> list[tuple[str, dict[str, Any], str]]:
    """(tool name, arguments, answer text) of every tools/call row, in order."""
    out = []
    for row in rows:
        request = row.get("request_body")
        if row.get("path") != "/api/mcp" or not isinstance(request, dict) or request.get("method") != "tools/call":
            continue
        params = request.get("params") or {}
        result = ((row.get("response_body") or {}).get("result") or {}) if isinstance(row.get("response_body"), dict) else {}
        text = "".join(str(p.get("text", "")) for p in result.get("content") or [] if isinstance(p, dict))
        out.append((str(params.get("name")), dict(params.get("arguments") or {}), text))
    return out


def read_for_delivery_findings(calls: list[tuple[str, dict[str, Any], str]], body_md: str) -> list[str]:
    """After the publish, the client read the published text (body_md) back."""
    publish = [i for i, (name, _a, _t) in enumerate(calls) if name == "project.publish_update"]
    if not publish:
        return ["the client never called project.publish_update"]
    after = calls[publish[-1] + 1:]
    reads = [name for name, _a, text in after if name == "project.list_updates" and json.dumps(body_md)[1:-1] in text]
    if not reads:
        return ["after the publish, no project.list_updates answer carried the published body_md"]
    return []


def find_cold_findings(calls: list[tuple[str, dict[str, Any], str]], pid: str, update: dict[str, Any],
                       fixture: dict[str, Any], ops: list[dict[str, Any]]) -> list[str]:
    """The fresh session found the project from its name and read its
    published, delivered update; it wrote nothing."""
    f: list[str] = []
    if not any(pid in text for name, _a, text in calls if name in {"project.list", "project.get"}):
        f.append("no project.list or project.get answer named the project")
    body = json.dumps(str(update.get("body_md") or ""))[1:-1]
    read = [text for name, _a, text in calls if update.get("id", "\0") in text and body in text]
    if not read:
        f.append("no answer carried the published update's body")
    elif not any(all(to in text for to in fixture["delivery"]["delivered_to"]) for text in read):
        f.append("no answer carrying the update also carried both deliveries")
    if ops:
        f.append(f"the find session wrote: {[op['name'] for op in ops]}")
    return f


def agent_findings(label: str, receipts: list[dict[str, Any]], *, identity: str, fixture: dict[str, Any],
                   grant_id: str | None) -> list[str]:
    """The AGENT session's receipts: refused before the grant, inside the bound
    naming the delegation after it; marking delivered refused throughout."""
    f: list[str] = []
    agent = fixture["agent"]
    by_name: dict[str, list[dict[str, Any]]] = {}
    for r in receipts:
        if r["operation"].get("parent_operation_id"):
            continue
        by_name.setdefault(r["operation"]["name"], []).append(r)
    for r in receipts:
        op = r["operation"]
        if op.get("principal_kind") != "agent" or op.get("principal_identity") != identity:
            f.append(f"{op['name']} {op['operation_id']} actor is {op.get('principal_kind')}:{op.get('principal_identity')}")
    marks = by_name.get(agent["owner_only_refused"]) or []
    if not marks:
        f.append(f"the agent never tried {agent['owner_only_refused']}")
    owner_code = agent.get("owner_only_code", agent["refusal_code"])
    for r in marks:
        if r["receipt"].get("state") != "refused" or r["receipt"].get("outcome") != owner_code:
            f.append(f"{agent['owner_only_refused']} was not refused {owner_code}: {r['receipt'].get('outcome')!r}")
    for name in agent["refused_before_grant"]:
        rows = by_name.get(name) or []
        if not rows:
            f.append(f"the agent never tried {name}")
            continue
        for r in rows:
            receipt = r["receipt"]
            if label == "ungranted":
                if receipt.get("state") != "refused" or receipt.get("outcome") != agent["refusal_code"]:
                    f.append(f"{name} before the grant: {receipt.get('state')!r} {receipt.get('outcome')!r}")
            else:
                basis = str(r["operation"].get("authority_basis") or "")
                if receipt.get("state") != "succeeded":
                    f.append(f"{name} with the grant: {receipt.get('state')!r} {receipt.get('outcome')!r}")
                if not grant_id or not basis.startswith(f"project-delegation:{grant_id}:"):
                    f.append(f"{name} with the grant does not name the delegation: {basis!r}")
                if r["operation"].get("delegator_kind") != "owner":
                    f.append(f"{name} delegator is {r['operation'].get('delegator_kind')!r}")
    outside = sorted(n for n in by_name if n not in (*agent["bound"], agent["owner_only_refused"])
                     and any(r["receipt"].get("state") == "succeeded" for r in by_name[n]))
    if outside:
        f.append(f"writes outside the bound succeeded: {outside}")
    return f


# ── the run ──────────────────────────────────────────────────────────────


def _session(run_dir: Path, temp_root: Path, hub: Any, stage: str, leg: str, prompt: str,
             bearer: str | None, timeout_s: float) -> tuple[dict[str, Any], list[str]]:
    """One fresh cold session: its own root, homes and Codex session."""
    cold, setup = p7._leg_setup(run_dir, temp_root, hub, leg, bearer, stage)
    if setup["findings"]:
        return {"launch_setup": setup}, [f"{stage}: launch setup {setup['findings']}"]
    audit = p7.codex_turn(run_dir=run_dir, stage=stage, prompt=prompt, cold=cold, leg=leg, hub=hub,
                          session_id=None, bearer=bearer, timeout_s=timeout_s)
    audit["exchange_end"] = len(p5._http_exchange_records(hub))
    p7._json_dump(run_dir / "codex" / stage / "mcp-audit.json", audit)
    return {"launch_setup": setup, "audit": p7._slim(audit)}, [f"{stage}: {b}" for b in p7.turn_blockers(audit)]


def _run(args: argparse.Namespace) -> int:
    p7.CLIENT[0] = "codex"
    p7.CODEX_AUTH[0] = Path(args.codex_auth).expanduser().resolve()
    run_dir = Path(args.out).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_dir = run_dir / f"{stamp}-room-job"
    run_dir.mkdir()
    started_at = datetime.now(timezone.utc)
    fixture_record = write_run_fixture(run_dir, Path(args.fixture).resolve(), date.today())
    fixture = fixture_record["fixture"]
    temp_root = Path(tempfile.mkdtemp(prefix="philo9-06-"))
    hub_home = temp_root / "hub-home"
    hub_home.mkdir()
    gw = p7._gw()
    provenance = gw.base_provenance(engine_mode="none")
    provenance["engine_mode_reason"] = (
        "the job calls no model: the steward drafts with the deterministic generator "
        "(holdspeak/services/project_update_service.py draft_update, generator deterministic)")
    p7._json_dump(run_dir / "run.json", {
        "claim": p7.CLAIM_CODEX, "client": "codex", "model": p7.MODEL, "reasoning_effort": p7.EFFORT,
        "label": REVIEW_LABEL, "observed_sitting": False, "engine_mode": "none",
        "legs": ["owner", "agent"], "sessions": list(SESSIONS), "temp_root": str(temp_root),
        "hub_home": str(hub_home), "fixture_sha256": fixture_record["source_sha256"],
        "face": "requested" if args.face else FACE_PENDING,
    })
    blocked: list[str] = []
    out: dict[str, Any] = {"sessions": {}, "checks": {}}
    hub = None
    try:
        hub = gw.Hub(hub_home, token=TOKEN, record_rehearsal=True,
                     transcript_path=hub_home / "rehearsal-transcript.jsonl").start()
        p7._json_dump(run_dir / "hub-proof.json", p5._hub_proof(hub, hub_home))
        prompts = fixture["prompts"]

        # 1. OWNER: the job.
        rowid = p7._max_op_rowid(hub)
        out["sessions"]["owner_job"], stops = _session(run_dir, temp_root, hub, "owner_job", "owner",
                                                       prompts["owner_job"], None, args.codex_timeout)
        blocked += stops
        ops = _ops_since(hub, rowid)
        back = owner_readbacks(gw, hub, fixture, provenance)
        receipts = _receipts(gw, hub, ops, provenance)
        checks = {"content": owner_job_findings(fixture, back), "receipts": owner_receipt_findings(receipts)}
        pid = back.get("project_id")
        published = [u for u in back.get("updates") or [] if u.get("lifecycle") == "published"]
        if (run_dir / "codex" / "owner_job" / "mcp-audit.json").exists():
            calls = _tool_calls(_window(hub, run_dir, "owner_job"))
            checks["read_for_delivery"] = (read_for_delivery_findings(calls, str(published[0].get("body_md") or ""))
                                           if published else ["no published update to read"])
        if published:
            edit_rowid = p7._max_op_rowid(hub)
            refused, body = _owner_call(hub, "project.update_draft",
                                        {"update_id": published[0]["id"], "body_md": "An edit after publication."})
            code = body.get("code") if isinstance(body, dict) else None
            back["edit_after_publish"] = {"refused": refused, "answer": body,
                                          "operations": _ops_since(hub, edit_rowid)}
            if not refused or code != fixture["publication"]["edit_after_publish_refused"]:
                checks["content"].append(f"an edit after publication was not refused published_update: {body}")
        p7._json_dump(run_dir / "owner_job" / "readbacks.json", {"readbacks": back, "operations": ops,
                                                                  "receipts": receipts})
        out["checks"]["owner_job"] = checks
        blocked += [f"owner_job {kind}: {x}" for kind, rows in checks.items() for x in rows]
        if not pid or not published:
            raise RuntimeError("the OWNER job left no project with a published update; the later sessions need it")
        update = published[0]

        # 2. OWNER: find it cold.
        rowid = p7._max_op_rowid(hub)
        out["sessions"]["owner_find"], stops = _session(run_dir, temp_root, hub, "owner_find", "owner",
                                                        prompts["owner_find"], None, args.codex_timeout)
        blocked += stops
        ops = _ops_since(hub, rowid)
        calls = _tool_calls(_window(hub, run_dir, "owner_find"))
        out["owner_find_tools"] = [name for name, _a, _t in calls]
        out["checks"]["owner_find"] = find_cold_findings(calls, pid, update, fixture, ops)
        blocked += [f"owner_find: {x}" for x in out["checks"]["owner_find"]]

        # 3. AGENT: a real Settings-issued PROJECT credential; a waiting draft.
        identity = fixture["agent"]["identity"]
        status_e, _enabled = hub.api("PUT", "/api/settings/remote", {"enabled": True})
        status_c, issued = hub.api("POST", "/api/settings/remote/credentials",
                                   {"identity": identity, "palette": fixture["agent"]["palette"]})
        if status_e >= 400 or status_c >= 400 or not isinstance(issued, dict) or not issued.get("token"):
            raise RuntimeError(f"credential issue failed ({status_e}, {status_c}): {issued!r}")
        bearer = str(issued["token"])
        credential = {k: v for k, v in issued.items() if k != "token"}
        credential["token_sha256_12"] = hashlib.sha256(bearer.encode()).hexdigest()[:12]
        credential["route"] = "POST /api/settings/remote/credentials"
        status_d, seeded = hub.api("POST", f"/api/projects/{pid}/updates/draft", {})
        seed = {"route": f"POST /api/projects/{pid}/updates/draft (owner token)", "status": status_d,
                "update_id": ((seeded or {}).get("update") or {}).get("id") if isinstance(seeded, dict) else None}
        p7._json_dump(run_dir / "agent" / "setup.json", {"credential": credential, "waiting_draft": seed})

        rowid = p7._max_op_rowid(hub)
        out["sessions"]["agent_ungranted"], stops = _session(
            run_dir, temp_root, hub, "agent_ungranted", "agent", prompts["agent_ungranted"], bearer, args.codex_timeout)
        blocked += stops
        receipts = _receipts(gw, hub, _ops_since(hub, rowid), provenance)
        _rec, room = _read(gw, hub, "project.get_room", {"project_id": pid}, provenance)
        _rec, drafts = _read(gw, hub, "project.list_updates", {"project_id": pid, "lifecycle": "draft"}, provenance)
        ungranted = agent_findings("ungranted", receipts, identity=identity, fixture=fixture, grant_id=None)
        latest = (((room or {}).get("steward") or {}).get("latest_run") or {}).get("id")
        if latest != (back.get("steward_run") or {}).get("run", {}).get("id"):
            ungranted.append(f"a steward run started without the grant: {latest}")
        if [u.get("id") for u in (drafts or {}).get("updates") or []] != [seed["update_id"]]:
            ungranted.append(f"the waiting draft changed without the grant: {drafts}")
        p7._json_dump(run_dir / "agent_ungranted" / "readbacks.json",
                      {"receipts": receipts, "latest_run": latest, "drafts": drafts})
        out["checks"]["agent_ungranted"] = ungranted
        blocked += [f"agent_ungranted: {x}" for x in ungranted]

        status_g, granted = hub.api("PUT", f"/api/settings/remote/delegations/{identity}/projects/{pid}", {})
        grant_id = granted.get("grant_id") if isinstance(granted, dict) else None
        grant = {"route": f"PUT /api/settings/remote/delegations/{identity}/projects/{pid}", "status": status_g,
                 "response": granted}
        if isinstance(granted, dict) and granted.get("operation_id"):
            grant["receipt"] = p7._receipt(gw, hub, str(granted["operation_id"]), provenance)["receipt"]
        p7._json_dump(run_dir / "agent" / "grant.json", grant)

        rowid = p7._max_op_rowid(hub)
        out["sessions"]["agent_granted"], stops = _session(
            run_dir, temp_root, hub, "agent_granted", "agent", prompts["agent_granted"], bearer, args.codex_timeout)
        blocked += stops
        _rec, room = _read(gw, hub, "project.get_room", {"project_id": pid}, provenance)
        run_id = (((room or {}).get("steward") or {}).get("latest_run") or {}).get("id")
        _rec, run = _wait_run(gw, hub, str(run_id), provenance) if run_id else (None, {})
        receipts = _receipts(gw, hub, _ops_since(hub, rowid), provenance)
        granted_f = agent_findings("granted", receipts, identity=identity, fixture=fixture, grant_id=grant_id)
        row = (run or {}).get("run") or {}
        drafted = [e for e in _effects(run or {}) if e.get("effect_kind") == "draft_update" and e.get("outcome") == "applied"]
        agent_update = ((drafted[0].get("result") or {}).get("update_id")) if len(drafted) == 1 else None
        if row.get("requested_by") != f"principal:{identity}" or row.get("state") != "completed":
            granted_f.append(f"the latest run is not the agent's completed run: {row.get('requested_by')} {row.get('state')}")
        if len(drafted) != 1:
            granted_f.append(f"the agent's run drafted {len(drafted)} updates, not one")
        _rec, ups = _read(gw, hub, "project.list_updates", {"project_id": pid}, provenance)
        mine = [u for u in (ups or {}).get("updates") or [] if u.get("id") == agent_update]
        if not mine or mine[0].get("lifecycle") != "published":
            granted_f.append(f"the agent's drafted update {agent_update} is not published")
        elif mine[0].get("deliveries"):
            granted_f.append("the agent's update carries a delivery before the owner marked it")
        # The owner marks the agent's update delivered (owner-only).
        owner_mark: dict[str, Any] = {}
        if agent_update:
            refused, body = _owner_call(hub, "project.mark_update_delivered",
                                        {"update_id": agent_update,
                                         "delivered_to": fixture["agent"]["owner_marks_delivered_to"]})
            owner_mark = {"refused": refused, "answer": body}
            _rec, ups = _read(gw, hub, "project.list_updates", {"project_id": pid}, provenance)
            mine = [u for u in (ups or {}).get("updates") or [] if u.get("id") == agent_update]
            marks = [d.get("delivered_to") for d in (mine[0].get("deliveries") if mine else []) or []]
            owner_mark["deliveries"] = marks
            if refused or marks != [fixture["agent"]["owner_marks_delivered_to"]]:
                granted_f.append(f"the owner's mark on the agent's update did not read back: {marks} {body}")
            elif isinstance(body, dict) and body.get("operation_id"):
                owner_mark["receipt"] = p7._receipt(gw, hub, str(body["operation_id"]), provenance)["receipt"]
        p7._json_dump(run_dir / "agent_granted" / "readbacks.json",
                      {"receipts": receipts, "run": run, "updates": ups, "owner_mark": owner_mark})
        out["checks"]["agent_granted"] = granted_f
        blocked += [f"agent_granted: {x}" for x in granted_f]

        # 4. The face: after PHILO-9-03 merges.
        if args.face:
            room_face = _shoot_room(run_dir, hub, pid, fixture, update)
            grant_face = _shoot_grant(run_dir, hub, pid, fixture)
            out["face"] = {"room_shots": room_face["shots"], "grant_shots": grant_face["shots"]}
            face_f = [f"room {w}: {x}" for w, v in room_face["widths"].items() for x in v["findings"]]
            face_f += [f"grant: {x}" for x in grant_face["findings"]]
            face_f += [f"page error: {e}" for e in room_face.get("page_errors", []) + grant_face.get("page_errors", [])]
            out["checks"]["face"] = face_f
            blocked += [f"face: {x}" for x in face_f]
        else:
            p7._write_text(run_dir / "face-pending.txt", FACE_PENDING + "\n")
            out["face"] = FACE_PENDING
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
        # The scratch homes hold a copy of the owner's Codex auth file; it
        # never outlives the run.
        for auth in temp_root.glob("*/home/.codex/auth.json"):
            auth.unlink(missing_ok=True)
        p7._json_dump(run_dir / "provenance.json", provenance)
        p7._json_dump(run_dir / "legs.json", out)
    redaction = redact_run(run_dir)
    fences = {
        "fixture_before_run": fixture_before_run_findings(run_dir, Path(args.fixture).resolve()),
        "session_isolation": session_isolation_findings(run_dir),
        "zero_read": {stage: len(zero_read_findings(read_events(run_dir / "codex" / stage / "events.jsonl")))
                      for stage in SESSIONS if (run_dir / "codex" / stage / "events.jsonl").exists()},
        "account_leaks": account_leak_findings(run_dir),
    }
    for kind in ("fixture_before_run", "session_isolation", "account_leaks"):
        blocked += [f"fence {kind}: {x}" for x in fences[kind]]
    blocked += [f"fence zero_read: {stage} {n}" for stage, n in fences["zero_read"].items() if n]
    p7._json_dump(run_dir / "redaction.json", {"rule": "e-mail addresses and account ids redacted (Phase 7 rule)",
                                               **redaction})
    p7._json_dump(run_dir / "fences.json", fences)
    p7._json_dump(run_dir / "run-status.json", {
        "started_at": started_at.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
        "outcome": "blocked" if blocked else "completed", "blocked": blocked, "label": REVIEW_LABEL,
        "claim": p7.CLAIM_CODEX, "face": out.get("face"),
    })
    print(f"RUN_DIR {run_dir}")
    print(f"PROOF {REVIEW_LABEL}")
    print(f"OUTCOME {'BLOCKED' if blocked else 'COMPLETED'}")
    for line in blocked:
        print(f"BLOCKED {line}")
    if not args.face:
        print(FACE_PENDING)
    return 0 if not blocked else 3


# ── the face (PHILO-9-03's merged Room and PHILO-9-07's grant row) ──────

SIZES = {1440: 900, 393: 852}

#: Rendered facts of the Room window (the story 03 glass's own selectors).
ROOM_FACTS = r"""() => {
  const anchor = document.querySelector('[data-testid=room-body], [data-testid=update-posture], [data-testid=steward-posture]');
  const win = anchor ? anchor.closest('.desk-window') : null;
  if (!win) return {window: false};
  const text = (sel) => [...win.querySelectorAll(sel)].filter((e) => e.getBoundingClientRect().height > 0)
    .map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  const small = [];
  const GLYPH = /^[●○✓✗⚠—↻ℹ«»·▤›×\s>]+$/;
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || GLYPH.test(t)) continue;
    const el = n.parentElement; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none' || el.closest('.sr-only')) continue;
    if (parseFloat(cs.fontSize) < 12) small.push(t.slice(0, 40));
  }
  return {
    window: true,
    headline: text('[data-testid=room-headline]')[0] ?? null,
    head_tokens: text('[data-testid=room-head-chips] .surface-state-chip, [data-testid=room-head-chips] .surface-token'),
    needs_you: text('[data-testid=needs-you-row]'),
    needs_you_why: text('[data-testid=needs-you-why]'),
    item_rows: text('[data-testid=item-row]'),
    update_rows: text('[data-testid=update-list-item]'),
    delivered_chips: text('[data-testid=update-delivered-chip]'),
    delivery_rows: text('[data-testid=delivery-row]'),
    receipts: text('[data-testid=receipt-row]'),
    plan: text('[data-testid=steward-run-plan] .surface-plan-step'),
    steward_outcome: text('[data-testid=steward-run-outcome]')[0] ?? null,
    steward_state: text('[data-testid=steward-run-state]')[0] ?? null,
    small_text: small.slice(0, 12),
    raw_buttons: [...win.querySelectorAll('button')].filter((b) => !String(b.className).includes('btn') && b.getBoundingClientRect().width)
      .map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30)),
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
  };
}"""


def _glass() -> Any:
    """The e2e glass helpers (the bundle build, the settle, the browser fetch): reused, not forked."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from tests.e2e import glass_infra

    return glass_infra


def _pages(play: Any, hub: Any) -> tuple[Any, dict[int, Any], list[str]]:
    glass = _glass()
    browser = play.chromium.launch(headless=True)
    pages: dict[int, Any] = {}
    errors: list[str] = []
    for width, height in SIZES.items():
        page = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1).new_page()
        page.set_default_timeout(45_000)
        page.emulate_media(reduced_motion="reduce")
        page.on("pageerror", lambda e, w=width: errors.append(f"{w}: {str(e)[:200]}"))
        page.goto(f"{hub.url}/?token={hub.token}", wait_until="load")
        glass._api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=hub.token)
        pages[width] = page
    return browser, pages, errors


def _stage(page: Any, hub: Any, key: str, scope: str | None = None) -> None:
    """Open one surface the way the desk's own callers stage it (the story 03 glass)."""
    page.evaluate("""([key, scope]) => sessionStorage.setItem('hs.desk.staged-surface-open',
        JSON.stringify(scope ? {key, scope} : {key}))""", [key, scope])
    page.goto(f"{hub.url}/?token={hub.token}", wait_until="networkidle")


def _snap(run_dir: Path, page: Any, name: str, width: int) -> str:
    glass = _glass()
    page.mouse.move(1, 1)
    glass._settle(page)
    shots = run_dir / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    path = shots / f"{name}-{width}.png"
    page.screenshot(path=str(path))
    return str(path.relative_to(run_dir))


def _scroll_to(page: Any, selector: str) -> None:
    loc = page.locator(selector).first
    loc.wait_for(timeout=20_000)
    loc.scroll_into_view_if_needed()
    page.wait_for_timeout(300)


def face_findings(fixture: dict[str, Any], facts: dict[str, Any], hub_room: dict[str, Any]) -> list[str]:
    """The Room's face against the fixture and the hub's own read, per width."""
    f: list[str] = []
    title = fixture["milestone"]["title"]
    days = int(fixture["milestone"]["due_days_before_run"])
    room = facts.get("room") or {}
    if "1 MILESTONE LATE" not in room.get("head_tokens", []):
        f.append(f"the head does not say 1 MILESTONE LATE: {room.get('head_tokens')}")
    if f"MILESTONE · {days} DAYS LATE" not in room.get("needs_you_why", []):
        f.append(f"NEEDS YOU does not say MILESTONE · {days} DAYS LATE: {room.get('needs_you_why')}")
    if not any(title in r for r in room.get("needs_you", [])):
        f.append(f"NEEDS YOU does not list {title!r}")
    items = (facts.get("items") or {}).get("item_rows", [])
    if not any(title in r and f"{days} DAYS LATE" in r for r in items):
        f.append(f"ITEMS does not show {title!r} {days} DAYS LATE: {items}")
    risk = fixture["risk"]
    if not any(risk["title"] in r and f"LIKELIHOOD {risk['likelihood'].upper()}" in r
               and f"IMPACT {risk['impact'].upper()}" in r for r in items):
        f.append(f"ITEMS does not show the risk with its likelihood and impact: {items}")
    delivered = (facts.get("updates") or {}).get("delivered_chips", [])
    if not any("DELIVERED ×2" in chip for chip in delivered):
        f.append(f"the update list does not show DELIVERED ×2: {delivered}")
    rows = (facts.get("update") or {}).get("delivery_rows", [])
    names = fixture["delivery"]["delivered_to"]
    if len(rows) < 2 or not all(any(n in r for r in rows) for n in names):
        f.append(f"the delivery rows do not show {names}: {rows}")
    receipts = (facts.get("receipts") or {}).get("receipts", [])
    joined = " | ".join(receipts)
    for word in ("STEWARD RUN", "PUBLISH UPDATE", "MARKED DELIVERED", "REFUSED"):
        if word not in joined:
            f.append(f"RECEIPTS do not show {word}: {receipts}")
    hub_receipts = ((hub_room.get("receipts") or {}).get("items") or [])
    refused_hub = [i for i in hub_receipts if i.get("outcome") == "refused"]
    refused_face = [r for r in receipts if "REFUSED" in r]
    if refused_hub and not refused_face:
        f.append("the hub holds refused receipts the face does not show")
    for part in ("room", "items", "updates", "update", "receipts", "steward"):
        data = facts.get(part) or {}
        if data.get("small_text"):
            f.append(f"{part}: text under 12 px {data['small_text']}")
        if data.get("raw_buttons"):
            f.append(f"{part}: raw buttons {data['raw_buttons']}")
        if data.get("h_overflow"):
            f.append(f"{part}: horizontal overflow")
        if data.get("modal"):
            f.append(f"{part}: a modal")
    return f


def _shoot_room(run_dir: Path, hub: Any, pid: str, fixture: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """The Room after the job at 1440x900 and 393x852, through the merged face:
    NEEDS YOU and the late milestone, ITEMS, the update list and the delivered
    update, RECEIPTS (the agent's refusals included), the steward's run."""
    from playwright.sync_api import sync_playwright

    glass = _glass()
    glass._ensure_build()
    out: dict[str, Any] = {"shots": [], "widths": {}}
    with sync_playwright() as play:
        browser, pages, errors = _pages(play, hub)
        try:
            for width, page in pages.items():
                facts: dict[str, Any] = {}
                hub_room = glass._api(page, "GET", f"/api/projects/{pid}/room", token=hub.token)
                _stage(page, hub, "open-project-memory", f"project:{pid}")
                glass._normal_chair(page)
                page.locator("[data-testid=room-body]").wait_for(timeout=20_000)
                page.locator("[data-testid=needs-you-why]").first.wait_for(timeout=20_000)
                page.wait_for_timeout(900)
                facts["room"] = page.evaluate(ROOM_FACTS)
                out["shots"].append(_snap(run_dir, page, "room-head", width))
                _scroll_to(page, "[data-testid=item-row]")
                facts["items"] = page.evaluate(ROOM_FACTS)
                out["shots"].append(_snap(run_dir, page, "room-items", width))
                _scroll_to(page, "[data-testid=receipt-row]")
                facts["receipts"] = page.evaluate(ROOM_FACTS)
                # Every receipt row on a shot: page the rows from the top (the
                # Ask well floats over the window's foot).
                count = page.locator("[data-testid=receipt-row]").count()
                step = 3 if width < 1000 else 4
                for shot_index, first in enumerate(range(0, count, step)):
                    page.evaluate("""(i) => { const rows = document.querySelectorAll('[data-testid=receipt-row]');
                        rows[i].scrollIntoView({block: 'start'}); }""", first)
                    page.wait_for_timeout(250)
                    out["shots"].append(_snap(run_dir, page, f"room-receipts-{shot_index + 1}", width))
                page.locator("[data-testid=updates-verb]").click()
                page.locator("[data-testid=update-list]").wait_for(timeout=20_000)
                page.wait_for_timeout(400)
                facts["updates"] = page.evaluate(ROOM_FACTS)
                out["shots"].append(_snap(run_dir, page, "updates-list", width))
                page.locator(f"[data-testid=update-list-item]:has([data-update-id='{update['id']}'])").first.click()
                page.locator("[data-testid=update-editor]").wait_for(timeout=20_000)
                page.wait_for_timeout(400)
                if page.locator("[data-testid=delivery-row]").count():
                    _scroll_to(page, "[data-testid=delivery-row]")
                facts["update"] = page.evaluate(ROOM_FACTS)
                out["shots"].append(_snap(run_dir, page, "update-delivered", width))
                _stage(page, hub, "open-project-memory", f"project:{pid}")
                glass._normal_chair(page)
                page.locator("[data-testid=room-body]").wait_for(timeout=20_000)
                page.locator("[data-testid=steward-verb]").click()
                page.locator("[data-testid=steward-list-item]").first.wait_for(timeout=20_000)
                facts["steward_list"] = page.evaluate(ROOM_FACTS)
                steward_items = page.locator("[data-testid=steward-list-item]")
                facts["steward_runs"] = []
                for index in range(steward_items.count()):
                    if index:
                        _stage(page, hub, "open-project-memory", f"project:{pid}")
                        glass._normal_chair(page)
                        page.locator("[data-testid=steward-verb]").click()
                        steward_items.first.wait_for(timeout=20_000)
                    steward_items.nth(index).click()
                    page.locator("[data-testid=steward-run-state]").wait_for(timeout=20_000)
                    page.wait_for_timeout(500)
                    facts["steward_runs"].append(page.evaluate(ROOM_FACTS))
                    out["shots"].append(_snap(run_dir, page, f"steward-run-{index + 1}", width))
                facts["steward"] = facts["steward_runs"][0] if facts["steward_runs"] else {}
                findings = face_findings(fixture, facts, hub_room)
                out["widths"][width] = {"facts": facts, "hub_room_receipts": (hub_room.get("receipts") or {}),
                                        "findings": findings}
            out["page_errors"] = errors
        finally:
            browser.close()
    p7._json_dump(run_dir / "observations" / "room.json", out)
    return out


def _shoot_grant(run_dir: Path, hub: Any, pid: str, fixture: dict[str, Any]) -> dict[str, Any]:
    """The Settings grant row after the job (canvas board 12): the owner
    archives the project; the LIVE grant stays, ARCHIVED, with its Stop, at
    both widths; Stop is pressed once; the line goes, the receipt stays."""
    from playwright.sync_api import sync_playwright

    glass = _glass()
    identity = fixture["agent"]["identity"]
    out: dict[str, Any] = {"shots": [], "widths": {}}
    status, archived = hub.api("DELETE", f"/api/projects/{pid}")
    out["archive"] = {"route": f"DELETE /api/projects/{pid} (owner token)", "status": status, "answer": archived}

    def remote(page: Any) -> Any:
        return page.locator(".gadget-group", has=page.locator(".gadget-group-label", has_text="Remote access")).last

    def row(page: Any) -> Any:
        return remote(page).locator(".surface-ledger-row",
                                    has=page.locator(".surface-ledger-primary", has_text=identity)).first

    def line(page: Any) -> Any:
        return row(page).locator(f'[data-testid="project-line-{pid}"]')

    def settings(page: Any) -> None:
        _stage(page, hub, "configure-settings")
        page.locator(".prefs-hub-headline").wait_for(timeout=20_000)
        system = page.locator(".surface-ledger-row", has=page.locator(".surface-ledger-primary", has_text="System"))
        system.locator(".btn", has_text="Open").click()
        page.locator(".gadget-group-label", has_text="Remote access").wait_for(timeout=20_000)
        glass._settle(page)
        trigger = row(page).locator("button", has_text="Projects")
        if trigger.count() and trigger.get_attribute("aria-expanded") != "true":
            trigger.click()
        page.wait_for_timeout(400)

    def text(loc: Any) -> str:
        return (loc.first.inner_text() if loc.count() else "").replace("\n", " ").strip()

    def reveal(page: Any, selector: str) -> None:
        page.evaluate("""(sel) => { const e = document.querySelector(sel); if (e) e.scrollIntoView({block: 'center'}); }""",
                      selector)
        page.wait_for_timeout(200)

    with sync_playwright() as play:
        browser, pages, errors = _pages(play, hub)
        try:
            for width, page in pages.items():
                settings(page)
                reveal(page, f'[data-testid="project-line-{pid}"]')
                out["widths"][width] = {"archived": {
                    "line": text(line(page)),
                    "archived_token": text(line(page).locator('[data-testid="project-archived"]')),
                    "chip": text(line(page).locator('[data-testid="project-grant-chip"]')),
                    "verb": text(line(page).locator('[data-testid="project-grant-verb"]')),
                }}
                out["shots"].append(_snap(run_dir, page, "grant-archived-live", width))
            # Stop, pressed once (at 1440); the 393 page is reloaded after it.
            page = pages[1440]
            line(page).locator('[data-testid="project-grant-verb"]').click()
            page.wait_for_function(f"() => !document.querySelector('[data-testid=\"project-line-{pid}\"]')",
                                   timeout=20_000)
            foot = page.locator('[data-testid="foot-receipt"]')
            foot.wait_for(timeout=20_000)
            stopped = {"foot": text(foot)}
            foot.click()
            well = page.locator('[data-testid="grant-receipt"]')
            well.wait_for(timeout=20_000)
            stopped["well"] = text(well)
            stopped["operation_id"] = well.get_attribute("data-operation-id")
            reveal(page, '[data-testid="grant-receipt"]')
            out["widths"][1440]["stopped"] = stopped
            out["shots"].append(_snap(run_dir, page, "grant-stopped-receipt", 1440))
            page = pages[393]
            settings(page)
            out["widths"][393]["stopped"] = {"line_present": line(page).count() > 0, "row": text(row(page))}
            out["shots"].append(_snap(run_dir, page, "grant-stopped-after", 393))
            if stopped.get("operation_id"):
                out["stop_receipt"] = glass._api(
                    pages[1440], "GET", f"/api/kernel/read?refs=operation:{stopped['operation_id']}&view=receipt",
                    token=hub.token)
            out["page_errors"] = errors
        finally:
            browser.close()
    findings: list[str] = []
    for width in SIZES:
        a = out["widths"][width]["archived"]
        if "ARCHIVED" not in a["archived_token"] or "Stop" not in a["verb"] or "ALLOWED" not in a["chip"]:
            findings.append(f"{width}: the archived LIVE grant line is not ARCHIVED + ALLOWED + Stop: {a}")
    stopped = out["widths"][1440].get("stopped") or {}
    if "STOPPED" not in stopped.get("foot", "") or "SUCCEEDED" not in stopped.get("well", ""):
        findings.append(f"1440: Stop left no STOPPED receipt: {stopped}")
    if out["widths"][393].get("stopped", {}).get("line_present"):
        findings.append("393: the stopped grant's line is still on the row")
    receipt = ((out.get("stop_receipt") or {}).get("objects") or [{}])[0]
    if ((receipt.get("operation") or {}).get("name"), (receipt.get("receipt") or {}).get("state")) != (
            "project.delegation.revoke", "succeeded"):
        findings.append(f"the Stop's kernel receipt does not read back: {receipt}")
    out["findings"] = findings
    p7._json_dump(run_dir / "observations" / "grant.json", out)
    return out


class _Transcript:
    """A retained run's hub transcript, read as the hub's (for the pairing)."""

    def __init__(self, run_dir: Path) -> None:
        self.transcript_path = run_dir / "rehearsal-transcript.jsonl"


def repair_findings(run_dir: Path) -> dict[str, list[str]]:
    """Every session's client events paired again with the hub's retained
    exchanges, and the job's receipts and content checked again, from the
    retained records alone (no new session)."""
    out: dict[str, list[str]] = {}
    for stage in SESSIONS:
        start = json.loads((run_dir / "codex" / stage / "transcript-window.json").read_text())["exchange_start"]
        try:
            rec = p5._reconcile_mcp_calls(run_dir / "codex" / stage, _Transcript(run_dir), start)
            out[f"pairing {stage}"] = [] if len(rec["matches"]) == rec["codex_calls"] else ["unpaired calls"]
        except RuntimeError as exc:
            out[f"pairing {stage}"] = [str(exc)]
    fixture = json.loads((run_dir / "fixture.json").read_text())["fixture"]
    owner = json.loads((run_dir / "owner_job" / "readbacks.json").read_text())
    out["owner content"] = owner_job_findings(fixture, owner["readbacks"])
    out["owner receipts"] = owner_receipt_findings(owner["receipts"])
    grant = json.loads((run_dir / "agent" / "grant.json").read_text())
    identity = fixture["agent"]["identity"]
    for label in ("ungranted", "granted"):
        receipts = json.loads((run_dir / f"agent_{label}" / "readbacks.json").read_text())["receipts"]
        out[f"agent {label}"] = agent_findings(label, receipts, identity=identity, fixture=fixture,
                                               grant_id=grant["response"].get("grant_id") if label == "granted" else None)
    return out


def fence_run(run_dir: Path) -> int:
    """The fences over a retained run: fixture before the run, the session
    isolation, zero reads, no account leak; the pairing, receipts and content
    checked again from the retained records."""
    problems = 0
    for name, rows in (("fixture_before_run", fixture_before_run_findings(run_dir)),
                       ("session_isolation", session_isolation_findings(run_dir)),
                       ("account_leaks", account_leak_findings(run_dir)),
                       *repair_findings(run_dir).items()):
        problems += len(rows)
        print(f"{name}={rows}")
    for stage in SESSIONS:
        events = read_events(run_dir / "codex" / stage / "events.jsonl")
        zero = zero_read_findings(events)
        problems += len(zero)
        print(f"{stage} zero_read={len(zero)}")
    print("FENCES GREEN" if not problems else f"FENCES RED: {problems}")
    return 0 if not problems else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help="one fresh cold-context rehearsal: four sessions, both legs")
    run.add_argument("--out", required=True, help="parent directory for the unique run")
    run.add_argument("--client", choices=("codex",), default="codex")
    run.add_argument("--legs", choices=("owner,agent",), default="owner,agent")
    run.add_argument("--codex-timeout", type=float, default=1200)
    run.add_argument("--codex-auth", type=Path, default=Path.home() / ".codex" / "auth.json",
                     help="the Codex auth file copied (alone) into each scratch CODEX_HOME")
    run.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    run.add_argument("--face", action="store_true", help="shoot the Room at 1440 and 393 (after PHILO-9-03)")
    pr = sub.add_parser("probe", help="confirm every expectation reachable on a rig hub, no client")
    pr.add_argument("--out", required=True)
    pr.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    pr.add_argument("--face", action="store_true")
    fence = sub.add_parser("fence", help="run the fences over a retained run (no new session)")
    fence.add_argument("run_dir", type=Path)
    return parser


def _agent_call(hub: Any, bearer: str, name: str, args: dict[str, Any]) -> tuple[bool, Any]:
    """One agent tools/call over /api/mcp with the PROJECT bearer (the probe only)."""
    import urllib.request

    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": args}}).encode()
    req = urllib.request.Request(f"{hub.url}/api/mcp", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        answer = json.loads(resp.read().decode())
    if "error" in answer:
        return True, answer["error"]
    result = answer.get("result") or {}
    text = "".join(str(p.get("text", "")) for p in result.get("content") or [] if isinstance(p, dict))
    try:
        return bool(result.get("isError")), json.loads(text)
    except ValueError:
        return bool(result.get("isError")), text


def probe(args: argparse.Namespace) -> int:
    """Each fixture expectation confirmed reachable on a rig hub BEFORE the
    Codex run, through the same contract, with no client (the charter:
    "confirmed reachable on the rig before the run"); ``--face`` also shoots
    the Room and the grant row, to prove the face leg's wiring."""
    run_dir = Path(args.out).resolve() / (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-probe")
    run_dir.mkdir(parents=True)
    fixture = write_run_fixture(run_dir, Path(args.fixture).resolve(), date.today())["fixture"]
    temp_root = Path(tempfile.mkdtemp(prefix="philo9-06-probe-"))
    (temp_root / "hub-home").mkdir()
    gw = p7._gw()
    hub = gw.Hub(temp_root / "hub-home", token=TOKEN).start()
    steps: list[dict[str, Any]] = []

    def step(label: str, value: tuple[bool, Any]) -> Any:
        steps.append({"step": label, "is_error": value[0], "answer": value[1]})
        return value[1]

    try:
        m, r = fixture["milestone"], fixture["risk"]
        pid = step("create", _owner_call(hub, "project.create", {"name": fixture["project"]}))["project"]["id"]
        step("milestone", _owner_call(hub, "project.item.create", {"project_id": pid, "item_type": "milestone",
                                                                    "title": m["title"], "due_at": m["due_at"]}))
        step("risk", _owner_call(hub, "project.item.create", {"project_id": pid, "item_type": "risk", "title": r["title"],
                                                               "details": {k: r[k] for k in ("likelihood", "impact", "mitigation")}}))
        step("policy", _owner_call(hub, "project.configure_steward",
                                   {"project_id": pid, "eligible_effect_kinds": fixture["steward"]["eligible_effect_kinds"]}))
        run = step("run", _owner_call(hub, "project.run_steward", {"project_id": pid}))
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            _e, read = _owner_call(hub, "project.get_steward_run", {"run_id": run["run_id"]})
            if ((read or {}).get("run") or {}).get("state") in TERMINAL_RUN:
                break
            time.sleep(0.5)
        uid = step("drafts", _owner_call(hub, "project.list_updates", {"project_id": pid}))["updates"][0]["id"]
        step("publish", _owner_call(hub, "project.publish_update", {"update_id": uid}))
        for to in fixture["delivery"]["delivered_to"]:
            step(f"deliver {to}", _owner_call(hub, "project.mark_update_delivered", {"update_id": uid, "delivered_to": to}))
        identity = fixture["agent"]["identity"]
        hub.api("PUT", "/api/settings/remote", {"enabled": True})
        _s, issued = hub.api("POST", "/api/settings/remote/credentials",
                             {"identity": identity, "palette": fixture["agent"]["palette"]})
        bearer = str(issued["token"])
        _s, seeded = hub.api("POST", f"/api/projects/{pid}/updates/draft", {})
        waiting = seeded["update"]["id"]
        step("agent run (no grant)", _agent_call(hub, bearer, "project.run_steward", {"project_id": pid}))
        step("agent publish (no grant)", _agent_call(hub, bearer, "project.publish_update", {"update_id": waiting}))
        step("agent mark (no grant)", _agent_call(hub, bearer, "project.mark_update_delivered", {"update_id": waiting}))
        steps.append({"step": "grant", "answer": hub.api("PUT", f"/api/settings/remote/delegations/{identity}/projects/{pid}", {})})
        arun = step("agent run (grant)", _agent_call(hub, bearer, "project.run_steward", {"project_id": pid}))
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            _e, read = _owner_call(hub, "project.get_steward_run", {"run_id": arun["run_id"]})
            if ((read or {}).get("run") or {}).get("state") in TERMINAL_RUN:
                break
            time.sleep(0.5)
        drafted = [e for e in _effects(read) if e.get("effect_kind") == "draft_update"][0]["result"]["update_id"]
        step("agent publish (grant)", _agent_call(hub, bearer, "project.publish_update", {"update_id": drafted}))
        step("agent mark (grant)", _agent_call(hub, bearer, "project.mark_update_delivered", {"update_id": drafted}))
        step("owner marks the agent's update", _owner_call(hub, "project.mark_update_delivered",
                                                            {"update_id": drafted, "delivered_to": fixture["agent"]["owner_marks_delivered_to"]}))
        result: dict[str, Any] = {"steps": steps}
        if args.face:
            room = _shoot_room(run_dir, hub, pid, fixture, {"id": uid})
            grant = _shoot_grant(run_dir, hub, pid, fixture)
            result["face_findings"] = {**{f"room {w}": v["findings"] for w, v in room["widths"].items()},
                                       "grant": grant["findings"],
                                       "page_errors": room.get("page_errors", []) + grant.get("page_errors", [])}
        p7._json_dump(run_dir / "probe.json", result)
    finally:
        hub.stop()
    print(f"RUN_DIR {run_dir}")
    print(json.dumps(result.get("face_findings"), indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "fence":
        return fence_run(args.run_dir.resolve())
    if args.mode == "probe":
        return probe(args)
    try:
        return _run(args)
    except Exception as exc:  # noqa: BLE001
        print(f"PHILO9_ROOM_JOB_BLOCKED {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
