"""PG-LANG LANG14: ``holdspeak program create|start|get|decide`` (thin over the hub).

The commands go through the real Programs routes (``build_programs_router``
over the rig's one ``ProgramService``): the opener hands each request to a
TestClient, so what is proven is the CLI's request and its words, and the
service's answer, unchanged.
"""
from __future__ import annotations

import argparse
import io
import json
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.commands.program import build_program_subparsers, run_program_command
from holdspeak.services import program_service as program_module
from holdspeak.web.routes.programs import build_programs_router
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


class _Answer:
    def __init__(self, status: int, body: bytes) -> None:
        self.status, self._body = status, body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_Answer":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None


def _opener(client: TestClient, seen: list[tuple[str, str, Any]]) -> Any:
    def open_(req: Any, timeout: float = 0) -> _Answer:
        path = req.full_url.split("://", 1)[1].split("/", 1)[1]
        body = json.loads(req.data.decode("utf-8")) if req.data else None
        seen.append((req.get_method(), "/" + path, body))
        resp = client.request(req.get_method(), "/" + path, json=body)
        return _Answer(resp.status_code, resp.content)

    return open_


def _run(argv: list[str], client: TestClient, seen: list) -> tuple[int, str]:
    parser = argparse.ArgumentParser(prog="holdspeak")
    build_program_subparsers(parser.add_subparsers(dest="command").add_parser("program"))
    out = io.StringIO()
    code = run_program_command(parser.parse_args(argv), out=out, opener=_opener(client, seen))
    return code, out.getvalue()


def test_create_start_get_and_decide_over_the_hub(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    app = FastAPI()
    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    client = TestClient(app)
    seen: list = []
    base = ["program", "--url", "http://127.0.0.1:8765", "--token", "t"]
    code, out = _run([*base, "create", "--title", "Overnight", "--repo", str(rig.repo), "--template", "fast-cycle",
                      "--control", "normal", "--json"], client, seen)
    made = json.loads(out)
    assert code == 0 and made["state"] == "drafting" and made["control"] == "normal"
    assert seen[-1] == ("POST", "/api/programs", {"title": "Overnight", "repository": str(rig.repo),
                                                  "template": "fast-cycle", "control": "normal"})
    pid = made["id"]
    rig.service.update(OWNER, pid, check_command=f"sh {FAKE_CHECK}")
    rig.service.plan(OWNER, pid, steps=[{"title": "Owned", "brief": "Store it.", "owns": ["src/a.py"]}])
    code, out = _run([*base, "start", pid], client, seen)
    assert code == 0 and out.startswith(f"{pid} · Overnight · "), out
    rig.tick()
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
    rig.tick()
    code, out = _run([*base, "get", pid, "--json"], client, seen)
    wire = json.loads(out)
    [item] = wire["your_turn_items"]
    assert item["kind"] == "core" and wire == rig.program(pid) | {"in_state_seconds": wire["in_state_seconds"]}
    code, out = _run([*base, "decide", pid, item["step_id"], "--kind", "core", "--choice", "park"], client, seen)
    assert code == 0 and rig.step(pid, 1)["state"] == "parked"
    # A refusal is the hub's own words and exit 1.
    code, out = _run([*base, "decide", pid, item["step_id"], "--kind", "core", "--choice", "go_on"], client, seen)
    assert code == 1 and out.startswith("Refused: "), out


def test_no_verb_says_which(capsys) -> None:
    parser = argparse.ArgumentParser(prog="holdspeak")
    build_program_subparsers(parser.add_subparsers(dest="command").add_parser("program"))
    assert run_program_command(parser.parse_args(["program"])) == 2
    assert "create, start, get or decide" in capsys.readouterr().err
