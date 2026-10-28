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
needs_you.program.json, room.programs.json, person.programs.json.
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


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="program-fixtures-") as tmp:
        fixtures = record(Path(tmp))
    _check(fixtures)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in fixtures.items():
        (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {(OUT / name).relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
