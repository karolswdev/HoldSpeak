"""PG-LANG LANG14: ``holdspeak.sdk.programs`` (create/start/get/decide/text).

Through the real Programs routes over the rig's one ``ProgramService`` (the
opener hands each request to a TestClient, as ``test_program_cli.py``): the
client's requests and the service's answers, unchanged; a refusal is
``ProgramsRefused`` with the hub's code and words.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.sdk.programs import Programs, ProgramsRefused
from holdspeak.services import program_service as program_module
from holdspeak.web.routes.programs import build_programs_router
from tests.integration.program_rig import FAKE_CHECK, Rig
from tests.unit.test_program_cli import _opener


def test_the_sdk_creates_starts_reads_decides_and_changes_by_text(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    app = FastAPI()
    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    seen: list = []
    programs = Programs(url="http://127.0.0.1:8765", token="t", opener=_opener(TestClient(app), seen))

    made = programs.create("Overnight", repository=str(rig.repo), template="fast-cycle", control="normal",
                           check_command=f"sh {FAKE_CHECK}")
    assert made["state"] == "drafting" and seen[-1][:2] == ("POST", "/api/programs")
    pid = made["id"]
    text = programs.text(pid)
    assert text["text"].startswith("# program text") and text["revision"] == made["revision"]
    added = text["text"] + "\nstep +  Owned\n  owns src/a.py\n  brief\n  > Store it.\n"
    dry = programs.text(pid, added, base=text["text"])
    assert dry["changes"] and not dry.get("applied"), dry
    assert rig.service.store.list_steps(pid) == []  # a dry run writes nothing
    applied = programs.text(pid, added, base=text["text"], apply=True)
    assert [step["title"] for step in applied["program"]["steps"]] == ["Owned"], applied
    assert programs.start(pid)["state"] == "running"
    rig.tick()
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
    rig.tick()
    [item] = programs.get(pid)["your_turn_items"]
    assert item["kind"] == "core"
    programs.decide(pid, item["step_id"], kind="core", choice="park")
    assert rig.step(pid, 1)["state"] == "parked"
    with pytest.raises(ProgramsRefused) as refused:
        programs.decide(pid, item["step_id"], kind="core", choice="go_on")
    assert refused.value.status >= 400 and refused.value.code and refused.value.detail

