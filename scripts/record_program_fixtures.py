#!/usr/bin/env python3
"""Record the hub's own Programs answers for the faces lane (the test diet's
SCAR LAW: nothing typed by hand, every field the face reads is the hub's).

It drives the Programs rig (``tests/integration/program_rig.py``: real git,
a real database, the real ``ProgramService`` and ``ProgramRunner``, fakes at
the process edge only) into each state the faces draw, then reads every
answer through the REAL routes (``web/routes/programs.py`` on a FastAPI
``TestClient``) and the real Needs you, Room and person readers.

    HOME=$(mktemp -d) uv run python scripts/record_program_fixtures.py

It writes ``web/src/desk/programs/__fixtures__/``:
programs.list.json, program.running.json, program.your_turn.json,
program.done.json, program.parked.json, program.drafting.json,
program.limited.json (PG19), program.race.json (a race of 2: Codex wins in
34 min, Claude Code parks), needs_you.program.json, room.programs.json,
person.programs.json; PG-REQ (2026-10-31): program.requirements.json (one
requirement of each kind and state, an every-step parent with six copies, a
waived one), program.requirement_word.json (a step at its merge waits for
his word), program.adjust.json (a Planned step moved, one inserted, a
started step amended), programs.filtered.list.json (``q``, project,
person); the faces lane's answers to his presses on the same records
(program.requirement_word.met.json, program.requirements.send_back.json,
.waive_refused.json, .waived.json, .added.json; needs_you.requirements.json; program.requirements.evidence.json; program.adjust.moved.json,
.inserted.json, .amended.json, .titled.json, .refused.json) and an
orchestrator's proposals (program.proposals.json, .added.json).
``--only program.race.json`` writes one file.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from holdspeak.delivery.pi_launch import LibraryEngine, PiEngine  # noqa: E402
from holdspeak.services import program_service as program_module  # noqa: E402
from holdspeak.services.needs_you_membership import compute_needs_you  # noqa: E402
from holdspeak.web.routes.programs import build_programs_router  # noqa: E402
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig  # noqa: E402

OUT = REPO / "web" / "src" / "desk" / "programs" / "__fixtures__"
QWEN = LibraryEngine("engine-tailscale-karol-8080", "qwen3.8-27b on karol", PiEngine(
    endpoint="http://karol:8080/v1", model="qwen3.8-27b", context_window=32768, key_slot="",
    host="karol:8080", boundary="private"))


class People:
    def display_names(self) -> dict[str, str]:
        return {"p-alice": "Alice"}

    def get_relationship(self, principal: Any, person_id: str) -> dict[str, Any]:
        return {"display_name": "Alice", "owner_aliases": ["alice-gh"]}


def _client(rig: Rig) -> TestClient:
    program_module.default_program_service = lambda db=None: rig.service  # the hub's one instance
    app = FastAPI()
    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    return TestClient(app)


def _get(client: TestClient, path: str) -> Any:
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def _create(rig: Rig, title: str, **kw: Any) -> str:
    return rig.service.create(OWNER, title=title, goal=kw.pop("goal", f"{title}."), repository=str(rig.repo),
                              check_command=kw.pop("check", f"sh {FAKE_CHECK}"), **kw)["id"]


def _review(rig: Rig, words: str) -> None:
    rig.tick()
    for record in rig.ledger.list():
        if record.get("helper_of") and rig.states.get(record["launch_id"], {}).get("state") != "done":
            rig.words.setdefault(record["launch_id"], words)
            rig.states[record["launch_id"]] = {"state": "done", "turn_id": f"r-{record['launch_id']}"}
    rig.tick(2)


def _at_limit(rig: Rig, launch_id: str, turn: str) -> None:
    """The flight of a Claude Code launch that stopped at its usage limit
    (the screen's notice, as ``agent_flights`` reads it)."""
    from datetime import datetime, timedelta, timezone

    until = (datetime.now(timezone.utc) + timedelta(minutes=90)).replace(second=0, microsecond=0)
    rig.states[launch_id] = {"state": "done", "turn_id": turn, "limit": {
        "rule": "claude.usage_limit", "line": "You've hit your limit · resets 2pm", "share": None,
        "until": until.isoformat().replace("+00:00", "Z"), "words": until.astimezone().strftime("%H:%M")}}


def record_limited(root: Path) -> Any:
    """PG19, in a rig of its own (the list, Room and Needs you fixtures stay
    as they were): a step handed off at its limit by his press, and a step
    limited now with its Your turn row (Normal)."""
    rig = Rig(root / "rig-limited", people=lambda: People())
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    client = _client(rig)
    limited = _create(rig, "People routes overnight", template="fast-cycle", control="normal",
                      project_id="proj-holdspeak", runs_on=["claude", "codex"])
    rig.service.plan(OWNER, limited, steps=[
        {"title": "People routes", "brief": "31 handlers through run_in_threadpool.", "owns": ["holdspeak/web/routes/people.py"]},
        {"title": "Projects routes", "brief": "20 handlers through run_in_threadpool.", "owns": ["holdspeak/web/routes/projects.py"]},
    ])
    rig.service.start(OWNER, limited)
    l1, l2 = rig.step(limited, 1), rig.step(limited, 2)
    tree = Path(rig.ledger.get(l1["launch_id"])["worktree_path"])
    (tree / "CLAUDE.md").write_text("Run one test at a time.\napi_key=sk-demo0123456789abcdefghij\n"
                                    "token=ghp_demo0123456789abcdefghijkl\n", encoding="utf-8")
    (tree / "holdspeak" / "web" / "routes").mkdir(parents=True, exist_ok=True)
    (tree / "holdspeak" / "web" / "routes" / "people.py").write_text("# 20 of 31 handlers\n", encoding="utf-8")
    rig.service.checkpoint(OWNER, limited, l1["id"], "Keep the 14-day rule")
    rig.agent.end_turn(l1["launch_id"])
    rig.tick()  # a turn with no commit: asked to commit (one earlier turn)
    _at_limit(rig, l1["launch_id"], "t-limit-1")
    rig.tick()
    rig.service.decide(OWNER, limited, l1["id"], kind="limited", choice="continue")
    rig.states[rig.step(limited, 1)["launch_id"]] = {"state": "working", "turn_id": None}
    _at_limit(rig, l2["launch_id"], "t-limit-2")
    rig.tick()

    return _get(client, f"/api/programs/{limited}")


def record_race(root: Path) -> Any:
    """A race of 2 at Normal, in a rig of its own: Claude Code and Codex get
    one brief each; Codex is green 34 minutes in and wins; Claude Code parks
    as "Lost the race to Codex". The rig's clock is the service's seam (the
    34 minutes are its clock, never a typed field)."""
    from datetime import datetime, timedelta, timezone

    moment = {"at": datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=34)}
    rig = Rig(root / "rig-race", clock=lambda: moment["at"].isoformat())
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    client = _client(rig)
    race = _create(rig, "The fast path", template="race", control="normal", project_id="proj-holdspeak")
    rig.service.plan(OWNER, race, steps=[
        {"title": "Fast read path", "brief": "Make the read path fast.", "owns": ["holdspeak/web/routes/read.py"]},
    ])
    rig.service.start(OWNER, race)
    lead = rig.step(race, 1)
    codex = lead["contenders"][0]
    moment["at"] += timedelta(minutes=34)
    rig.agent.finish(codex["launch_id"], {"holdspeak/web/routes/read.py": "# fast\n"})
    rig.tick(3)  # checked, PR, merged (Normal); Claude Code loses
    return _get(client, f"/api/programs/{race}")


def _shot_repo(rig: Rig) -> None:
    """The rig repository names a shot command (a real process that writes
    the image the verifier looks for)."""
    from tests.integration.program_rig import git

    (rig.repo / ".holdspeak").mkdir(exist_ok=True)
    (rig.repo / ".holdspeak" / "program.json").write_text(json.dumps({
        "shot": "mkdir -p .tmp/shots && printf png > .tmp/shots/{case}-{width}.png && echo '1 passed'",
        "shot_image": ".tmp/shots/*{case}-{width}*.png"}) + "\n", encoding="utf-8")
    git(rig.repo, "add", "-A")
    git(rig.repo, "commit", "-m", "shot command")
    git(rig.repo, "push", "origin", "main")


def record_requirements(root: Path) -> dict[str, Any]:
    """PG-REQ, in a rig of its own: six steps at Normal with an every-step
    Check (six copies), one requirement of each kind on its own step, each
    state (Met, Unmet, Not yet, Waived, Waits for you), and the Program's
    own (a word and an end check). Also the word fixture and the filtered
    list."""
    rig = Rig(root / "rig-requirements", people=lambda: People())
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    _shot_repo(rig)
    client = _client(rig)
    flag = root / "requirements-red"
    flag.write_text("1")
    pid = _create(rig, "The hub stops stalling", template="fast-cycle", control="normal", project_id="proj-holdspeak",
                  for_person_id="p-alice", reviewer_profile="codex-default")
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Indexes", "brief": "Add the three indexes.", "owns": ["holdspeak/db/schema.py"]},
        {"title": "Retention", "brief": "Prune read receipts after 14 days.", "owns": ["holdspeak/db/retention.py"]},
        {"title": "Projections off the loop", "brief": "Move the slow reads off the event loop."},
        {"title": "People routes", "brief": "31 handlers through run_in_threadpool."},
        {"title": "Projects routes", "brief": "20 handlers through run_in_threadpool."},
        {"title": "The fan-out", "brief": "Fan out the reads.", "after": [3, 4]},
    ])
    s = {n: rig.step(pid, n) for n in range(1, 7)}

    def add(**kw: Any) -> str:
        answer = client.post(f"/api/programs/{pid}/requirements", json=kw)
        assert answer.status_code == 201, answer.text
        return answer.json()["requirement_id"]

    add(text="`echo 12 passed` is green", each_step=True)
    add(text="The People window at 393 has no clipped text", step_id=s[1]["id"])
    add(text="No new route skips the residual set", step_id=s[2]["id"])
    add(text="I tried it on my desk", kind="word", step_id=s[3]["id"])
    add(text="The routes stay green", kind="check", step_id=s[4]["id"],
        spec={"command": f"if [ -f {flag} ]; then echo '1 failed, 30 passed'; exit 1; fi; echo '31 passed'"})
    waived = add(text="The old ledger is gone", step_id=s[5]["id"])
    add(text="The desk feels fast after the program", kind="word")
    add(text="`echo ok` on main", kind="check")
    client.post(f"/api/programs/{pid}/requirements/{waived}/decide",
                json={"choice": "waive", "line": "The ledger lane owns it"})
    rig.service.start(OWNER, pid)
    s = {n: rig.step(pid, n) for n in range(1, 7)}
    rig.agent.finish(s[1]["launch_id"], {"holdspeak/db/schema.py": "-- indexes\n"})
    rig.tick(3)  # check, shot and every-step check Met; PR; merged (Normal)
    rig.agent.finish(s[2]["launch_id"], {"holdspeak/db/retention.py": "# prune\n"})
    rig.tick(2)  # the Review requirement brings the reviewer
    for record in [r for r in rig.ledger.list() if r.get("helper_of") == s[2]["launch_id"]]:
        rig.words[record["launch_id"]] = ("MUST: none\nREQ R1: MET · 12 passed\n"
                                          "REQ R3: UNMET · projects.py adds /api/projects/{id}/fold with no entry")
        rig.states[record["launch_id"]] = {"state": "done", "turn_id": "r1"}
    rig.tick(2)
    rig.agent.finish(s[3]["launch_id"], {"holdspeak/web/routes/read.py": "x\n"})
    rig.tick(3)  # PR open; his word holds it
    rig.agent.finish(s[4]["launch_id"], {"holdspeak/web/routes/people.py": "x\n"})
    rig.tick()  # R5 red, round 1: back to the builder
    rig.tick()
    wire = _get(client, f"/api/programs/{pid}")

    # His word at the merge, alone (the Your turn row of §9).
    word = _create(rig, "The dock lamp", template="fast-cycle", control="normal", project_id="proj-holdspeak")
    rig.service.plan(OWNER, word, steps=[{"title": "Dock lamp", "brief": "Light the lamp when a step waits."}])
    w1 = rig.step(word, 1)
    client.post(f"/api/programs/{word}/requirements", json={"text": "I tried it on my desk", "kind": "word",
                                                             "step_id": w1["id"]})
    client.post(f"/api/programs/{word}/requirements", json={"text": "The Dock window at 393 has no clipped text",
                                                             "step_id": w1["id"]})
    rig.service.start(OWNER, word)
    rig.agent.finish(rig.step(word, 1)["launch_id"], {"web/src/desk/dock/lamp.ts": "export {};\n"})
    rig.tick(3)
    filtered = _get(client, "/api/programs?q=stalling&project_id=proj-holdspeak&person_id=p-alice")
    word_wire = _get(client, f"/api/programs/{word}")
    out = {"program.requirements.json": wire, "programs.filtered.list.json": filtered,
           "program.requirement_word.json": word_wire}
    # His word as a Needs you row (the Program's title as its group).
    needs = compute_needs_you(programs=rig.service.needs_you_items())
    out["needs_you.requirements.json"] = {
        "items": [item for item in needs["unmutedItems"] if item.get("source") == "program"]}
    # PG-REQ faces (REQ10): the hub's answers to his presses, on the same
    # records, so a face test drives each press to the rendered outcome.
    label = {row["label"]: row["id"] for row in wire["requirements"]}
    label.update({row["label"]: row["id"] for step in wire["steps"] for row in step["requirements"]})
    # The evidence route: R5's log text, and R2's shot (its media type).
    log = client.get(f"/api/programs/{pid}/requirements/{label['R5']}/evidence")
    shot = client.get(f"/api/programs/{pid}/requirements/{label['R2']}/evidence")
    out["program.requirements.evidence.json"] = {
        "log": {"status": log.status_code, "type": log.headers.get("content-type"), "text": log.text},
        "shot": {"status": shot.status_code, "type": shot.headers.get("content-type"), "bytes": len(shot.content)}}
    turn = word_wire["your_turn_items"][0]
    out["program.requirement_word.met.json"] = _press(
        client, f"/api/programs/{word}/requirements/{turn['requirement_id']}/decide", {"choice": "met"})
    out["program.requirements.send_back.json"] = _press(
        client, f"/api/programs/{pid}/requirements/{label['R3']}/decide", {"choice": "send_back", "line": "Add the entry"})
    refused = client.post(f"/api/programs/{pid}/requirements/{label['R5']}/decide", json={"choice": "waive"})
    out["program.requirements.waive_refused.json"] = {"status": refused.status_code, "body": refused.json()}
    out["program.requirements.waived.json"] = _press(
        client, f"/api/programs/{pid}/requirements/{label['R5']}/decide", {"choice": "waive", "line": "The rig has no routes"})
    out["program.requirements.added.json"] = _press(
        client, f"/api/programs/{pid}/requirements", {"text": "The Programs window at 393 has no clipped text",
                                                      "step_id": s[5]["id"]})
    return out


def _press(client: TestClient, path: str, body: dict[str, Any], method: str = "post") -> Any:
    """One press through the real route; the hub's answer as it is sent."""
    answer = getattr(client, method)(path, json=body)
    assert answer.status_code < 300, answer.text
    return answer.json()


def record_adjust(root: Path) -> Any:
    """PG-REQ §8, in a rig of its own: a step inserted before a Planned one,
    a Planned step moved, a started step amended (one line typed at its turn
    boundary, one waiting)."""
    rig = Rig(root / "rig-adjust", people=lambda: People())
    client = _client(rig)
    pid = _create(rig, "Calls on the home box", template="fast-cycle", control="normal")
    rig.service.plan(OWNER, pid, steps=[
        {"title": "The call runner", "brief": "Run a call turn on qwen."},
        {"title": "The calls window", "brief": "Draw the call.", "after": [1]},
        {"title": "The ring timer", "brief": "Ring after 10 minutes.", "after": [1]},
        {"title": "The phone route", "brief": "Mount the phone route.", "after": [1]},
    ])
    rig.service.start(OWNER, pid)
    first, ring, route = rig.step(pid, 1), rig.step(pid, 3), rig.step(pid, 4)
    answer = client.post(f"/api/programs/{pid}/plan", json={"steps": [{"title": "The loop watch",
                                                                       "brief": "Log a held loop."}], "before": ring["id"]})
    assert answer.status_code == 200, answer.text
    answer = client.patch(f"/api/programs/{pid}/steps/{route['id']}", json={"before": rig.step(pid, 2)["id"]})
    assert answer.status_code == 200, answer.text
    client.post(f"/api/programs/{pid}/steps/{first['id']}/amend", json={"line": "Keep the 14-day rule"})
    rig.agent.end_turn(first["launch_id"])
    rig.tick()  # typed at the turn boundary
    client.post(f"/api/programs/{pid}/steps/{first['id']}/amend", json={"line": "Use the new index"})
    wire = _get(client, f"/api/programs/{pid}")
    out = {"program.adjust.json": wire}
    # PG-REQ faces (REQ11): the answers to his adjust presses, in order, on
    # the same records: Move up (step 3 before step 2), Insert before step 4,
    # Amend brief on step 1, a title edit on step 5, and the refusal of a
    # move of the started step 1.
    steps = {step["ordinal"]: step["id"] for step in wire["steps"]}
    out["program.adjust.moved.json"] = _press(client, f"/api/programs/{pid}/steps/{steps[3]}", {"before": steps[2]}, "patch")
    out["program.adjust.inserted.json"] = _press(client, f"/api/programs/{pid}/plan", {
        "steps": [{"title": "The retry"}], "before": steps[4], "waits": True})
    out["program.adjust.amended.json"] = _press(client, f"/api/programs/{pid}/steps/{steps[1]}/amend",
                                                {"line": "Log each turn"})
    out["program.adjust.titled.json"] = _press(client, f"/api/programs/{pid}/steps/{steps[5]}",
                                               {"title": "The ring timer, ten minutes"}, "patch")
    refused = client.patch(f"/api/programs/{pid}/steps/{steps[1]}", json={"before": steps[2]})
    out["program.adjust.refused.json"] = {"status": refused.status_code, "body": refused.json()}
    return out


def record_proposals(root: Path) -> dict[str, Any]:
    """PG-REQ §6, §9: an orchestrating agent at Normal proposes a requirement
    on a step, a change to a planned step and an amendment to a running
    step; each waits in Your turn for his Add, Apply or Send."""
    from holdspeak.mcp import palettes
    from holdspeak.mcp.families import program as family
    import holdspeak.principals as principals
    from holdspeak.principals import AgentCredentialStore

    rig = Rig(root / "rig-proposals", people=lambda: People())
    client = _client(rig)
    store = AgentCredentialStore()
    agent = store.issue("agent:orchestrator", palette=palettes.resolve_palette("CONDUCTOR"), palette_name="CONDUCTOR",
                        launch_id="L-orch").principal
    saved = (principals.agent_credentials, program_module.default_program_service)
    principals.agent_credentials = store
    program_module.default_program_service = lambda db=None: rig.service
    try:
        made = family.dispatch("program.create", {"title": "The phone line", "repository": str(rig.repo),
                                                  "control": "normal", "check_command": f"sh {FAKE_CHECK}"}, agent)
        pid = made["id"]
        family.dispatch("program.plan", {"program_id": pid, "steps": [
            {"title": "The SIP runner", "brief": "Run baresip under the hub."},
            {"title": "The line window", "brief": "Draw the line."}]}, agent)
        family.dispatch("program.start", {"program_id": pid}, agent)
        one, two = rig.step(pid, 1), rig.step(pid, 2)
        family.dispatch("program.require", {"program_id": pid, "text": "The line answers in two rings",
                                            "step_id": one["id"]}, agent)
        family.dispatch("program.step_update", {"program_id": pid, "step_id": two["id"], "title": "The Line window"}, agent)
        family.dispatch("program.amend", {"program_id": pid, "step_id": one["id"], "line": "Keep the port at 5060"}, agent)
    finally:
        principals.agent_credentials, program_module.default_program_service = saved
    wire = _get(client, f"/api/programs/{pid}")
    item = next(i for i in wire["your_turn_items"] if i["kind"] == "requirement_proposed")
    return {"program.proposals.json": wire,
            "program.proposals.added.json": _press(client, f"/api/programs/{pid}/proposals/{item['proposal_id']}/decide",
                                                   {"choice": "add"})}


def record(root: Path) -> dict[str, Any]:
    idle = {"qwen": False}
    rig = Rig(root / "rig", people=lambda: People(), engines=lambda e: QWEN if e == QWEN.profile_id else None,
              idle=lambda engine_id: (idle["qwen"], "qwen"))
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    red = root / "red"
    client = _client(rig)

    # ── Running, at YOLO: steps in many §4 states and Decided for you ──
    running = _create(rig, "The hub stops stalling", template="fast-cycle", control="yolo",
                      project_id="proj-holdspeak", for_person_id="p-alice",
                      check=f"FAKE_CHECK_RED_FILE={red} sh {FAKE_CHECK}")
    rig.service.plan(OWNER, running, steps=[
        {"title": "Indexes", "brief": "Add the three indexes.", "owns": ["holdspeak/db/schema.py"]},
        {"title": "Retention", "brief": "Prune read receipts after 14 days.", "owns": ["holdspeak/db/retention.py"]},
        {"title": "Projections off the loop", "brief": "Move the slow reads off the event loop."},
        {"title": "People routes", "brief": "31 handlers through run_in_threadpool."},
        {"title": "Overnight sweep on qwen", "brief": "Sweep the copy.", "profile": "pi-default",
         "engine": QWEN.profile_id, "prefer_idle": True},
        {"title": "The fan-out", "brief": "Fan out the reads.", "after": [3, 4]},
    ])
    rig.service.start(OWNER, running)
    step = {n: rig.step(running, n) for n in range(1, 7)}
    rig.agent.finish(step[1]["launch_id"], {"holdspeak/db/schema.py": "-- indexes\n"})
    rig.tick(3)  # checked, PR, merged (YOLO)
    rig.gh.ci = "pending"
    rig.agent.finish(step[2]["launch_id"], {"holdspeak/db/retention.py": "# prune\n"})
    rig.tick(2)  # PR open, CI pending
    rig.gh.ci_by_number[int(rig.step(running, 2)["pr"]["number"])] = "pending"
    red.write_text("1")
    rig.agent.finish(step[3]["launch_id"], {"holdspeak/web/routes/read.py": "x\n"})
    rig.tick()  # check red, round 1: back to the builder
    red.unlink()
    rig.states[step[4]["launch_id"]] = {"state": "waiting", "turn_id": None}
    rig.tick()
    rig.service.checkpoint(OWNER, running, step[4]["id"], "31 handlers, 20 done")
    # A step the plan lacked, named by step 1's agent: YOLO adds it.
    first = rig.service.store.get_step(step[1]["id"])
    rig.service.propose_step(rig.service.store.get_program(running), first,
                             {"title": "Write the docs", "brief": "docs/programs.md"})
    rig.service.changed(running)

    # ── Your turn, at Secure: a merge ask, findings left, a core question ──
    turn = _create(rig, "The words wave", template="build-and-review", control="secure",
                   reviewer_profile="codex-default", project_id="proj-holdspeak")
    rig.service.plan(OWNER, turn, steps=[
        {"title": "Settings words", "brief": "Plain words in Settings.", "owns": ["web/src/desk/settings/words.ts"]},
        {"title": "Dock words", "brief": "Plain words on the Dock.", "owns": ["web/src/desk/dock/words.ts"]},
        {"title": "Door words", "brief": "Plain words on the Door.", "owns": ["web/src/desk/door/words.ts"]},
    ])
    rig.service.start(OWNER, turn)
    t = {n: rig.step(turn, n) for n in (1, 2, 3)}
    rig.gh.ci = "passing"
    rig.agent.finish(t[1]["launch_id"], {"web/src/desk/settings/words.ts": "export {};\n"})
    rig.agent.finish(t[2]["launch_id"], {"web/src/desk/dock/words.ts": "export {};\n"})
    rig.agent.finish(t[3]["launch_id"], {"web/src/desk/door/words.ts": "export {};\n", "other/thing.py": "x\n"})
    rig.tick(2)  # the check, then AG12 starts the reviewers
    for record in [r for r in rig.ledger.list() if r.get("helper_of")]:
        builder = record["helper_of"]
        words = "MUST: none" if builder == t[1]["launch_id"] else "MUST: name the empty state in plain words (dock/words.ts:3)"
        rig.words[record["launch_id"]] = words
    _review(rig, "")
    # Round 2 for step 2: the builder fixes, the reviewer still finds it.
    rig.agent.finish(t[2]["launch_id"], {"web/src/desk/dock/words.ts": "export const x = 1;\n"})
    rig.tick()
    for record in [r for r in rig.ledger.list() if r.get("helper_of") == t[2]["launch_id"]]:
        rig.words.setdefault(record["launch_id"], "MUST: the empty state still says nothing\nSHOULD: sentence case the title")
    _review(rig, "MUST: the empty state still says nothing\nSHOULD: sentence case the title")

    # ── Done, at Normal ──
    done = _create(rig, "Wave 6 of the atlas", template="fast-cycle", control="normal", project_id="proj-holdspeak")
    rig.service.plan(OWNER, done, steps=[{"title": "Atlas anchors", "brief": "Cite each anchor once."}])
    rig.service.start(OWNER, done)
    rig.agent.finish(rig.step(done, 1)["launch_id"], {"docs/atlas.md": "x\n"})
    rig.tick(3)

    # ── Parked by him, with a step the engine parked after its rounds ──
    parked = _create(rig, "Retire the old ledger", template="fast-cycle", control="normal",
                     check=f"FAKE_CHECK_RED=1 sh {FAKE_CHECK}")
    rig.service.plan(OWNER, parked, steps=[{"title": "Drop the ledger", "brief": "x"}, {"title": "Tidy", "brief": "y"}])
    rig.service.start(OWNER, parked)
    p1 = rig.step(parked, 1)
    rig.agent.finish(p1["launch_id"], {"a.txt": "1\n"})
    rig.tick()
    rig.agent.start_turn(p1["launch_id"])
    rig.tick()
    rig.agent.finish(p1["launch_id"], {"a.txt": "2\n"})
    rig.tick()
    rig.service.park(OWNER, parked)

    # ── Drafting ──
    drafting = _create(rig, "Calls on the home box", template="overnight", project_id="proj-holdspeak")
    rig.service.plan(OWNER, drafting, steps=[{"title": "The call runner", "brief": "Run a call turn on qwen."},
                                            {"title": "The calls window", "brief": "Draw the call.", "after": [1]}])

    fixtures = {
        "programs.list.json": _get(client, "/api/programs"),
        "program.running.json": _get(client, f"/api/programs/{running}"),
        "program.your_turn.json": _get(client, f"/api/programs/{turn}"),
        "program.done.json": _get(client, f"/api/programs/{done}"),
        "program.parked.json": _get(client, f"/api/programs/{parked}"),
        "program.drafting.json": _get(client, f"/api/programs/{drafting}"),
    }
    needs = compute_needs_you(programs=rig.service.needs_you_items())
    fixtures["needs_you.program.json"] = {
        "items": [item for item in needs["unmutedItems"] if item.get("source") == "program"],
        "count": needs["count"], "members": needs["members"],
    }
    from holdspeak.services.project_service import ProjectService

    fixtures["room.programs.json"] = ProjectService(rig.db).room(OWNER, "proj-holdspeak")["programs"]
    fixtures["person.programs.json"] = {"programs": rig.service.for_person("p-alice", since="2026-01-01T00:00:00+00:00")}
    fixtures["program.limited.json"] = record_limited(root)
    fixtures["program.race.json"] = record_race(root)
    fixtures.update(record_requirements(root))
    fixtures.update(record_adjust(root))
    fixtures.update(record_proposals(root))
    return fixtures


def _check(fixtures: dict[str, Any]) -> None:
    running = fixtures["program.running.json"]
    assert running["control"] == "yolo", running["control"]
    decided = running["decided_for_you"]
    assert len(decided) >= 3 and any(row["overturnable"] for row in decided), decided
    words = [step["state_word"] for step in running["steps"]]
    assert "Ready · waiting for qwen" in words, words
    assert any((step.get("engine") or {}).get("label") == QWEN.label for step in running["steps"])
    assert fixtures["program.your_turn.json"]["state"] == "waiting"
    assert {item["kind"] for item in fixtures["program.your_turn.json"]["your_turn_items"]} >= {"merge", "finding", "core"}
    assert fixtures["program.done.json"]["state"] == "done"
    assert fixtures["program.parked.json"]["state"] == "parked"
    assert fixtures["program.drafting.json"]["state"] == "drafting"
    assert fixtures["needs_you.program.json"]["items"]
    limited = fixtures["program.limited.json"]
    assert limited["steps"][0]["handoffs"] and limited["steps"][0]["handoffs"][0]["redacted_words"], limited["steps"][0]
    assert limited["steps"][1]["state"] == "limited", limited["steps"][1]["state"]
    assert any(item["kind"] == "limited" for item in limited["your_turn_items"])
    race = fixtures["program.race.json"]["steps"][0]
    assert race["race"] == 2 and len(race["contenders"]) == 1, race
    assert race["state"] == "parked" and race["parked_reason"] == "Lost the race to Codex", race
    assert race["elapsed"] == "34 min", race["elapsed"]
    assert race["contenders"][0]["state"] in ("merged", "done"), race["contenders"][0]["state"]
    # PG-REQ: each kind and each state, an every-step parent with six copies, a waived one.
    wire = fixtures["program.requirements.json"]
    rows = list(wire["requirements"]) + [row for step in wire["steps"] for row in step["requirements"]]
    assert {row["kind"] for row in rows} == {"check", "review", "shot", "word"}, {row["kind"] for row in rows}
    assert {row["state"] for row in rows} >= {"met", "unmet", "not_yet", "waived"}, {row["state"] for row in rows}
    assert "Waits for you" in {row["state_word"] for row in rows}
    parent = next(row for row in wire["requirements"] if row["scope"] == "every_step")
    assert len(parent["steps"]) == 6, parent["steps"]
    assert any(row["evidence"].get("kind") == "shot" and row["state"] == "met" for row in rows)
    assert {"requirement_word"} <= {item["kind"] for item in wire["your_turn_items"]}
    assert wire["requirements_met"]["total"] >= 10, wire["requirements_met"]
    word = fixtures["program.requirement_word.json"]
    assert [item["kind"] for item in word["your_turn_items"]] == ["requirement_word"], word["your_turn_items"]
    filtered = fixtures["programs.filtered.list.json"]
    assert filtered["filter"]["shown"] == 1 and filtered["filter"]["of"] >= 2, filtered["filter"]
    adjust = fixtures["program.adjust.json"]
    assert [step["title"] for step in adjust["steps"]] == [
        "The call runner", "The phone route", "The calls window", "The loop watch", "The ring timer"], adjust["steps"]
    lines = [item["line"] for item in adjust["steps"][0]["amendments"]]
    assert lines == ["Keep the 14-day rule", "Use the new index"], lines
    assert adjust["steps"][0]["amendments"][0]["sent_at"] and not adjust["steps"][0]["amendments"][1]["sent_at"]
    assert adjust["steps"][0]["frozen"]["brief"] == "The agent has read it"
    # PG-REQ faces: the answers to his presses.
    assert fixtures["program.requirements.waive_refused.json"]["status"] == 400
    assert fixtures["program.adjust.refused.json"]["status"] == 409
    moved = fixtures["program.adjust.moved.json"]
    assert [step["title"] for step in moved["steps"]][:3] == ["The call runner", "The calls window", "The phone route"]
    proposals = fixtures["program.proposals.json"]
    assert {item["kind"] for item in proposals["your_turn_items"]} >= {"requirement_proposed", "step_change", "step_amend"}


def main(argv: list[str]) -> int:
    only = argv[argv.index("--only") + 1:] if "--only" in argv else []
    with tempfile.TemporaryDirectory(prefix="program-fixtures-") as tmp:
        fixtures = record(Path(tmp))
    _check(fixtures)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in fixtures.items():
        if only and name not in only:
            continue
        (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {(OUT / name).relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
