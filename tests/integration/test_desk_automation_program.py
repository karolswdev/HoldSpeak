"""Programs PG14 on the automation routes: a run_program automation, run.

The real Workbench routes (TestClient, isolated database) over the Programs
rig (real git, fakes at the process edge). The face half replays the answers
recorded here (web/src/desk/__tests__/fixtures/automation-hub/program-*.json;
HOLDSPEAK_WIRE_WRITE=1 rewrites them, else this test fences their shape).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from holdspeak.services import program_service as programs
from tests.integration.program_rig import Rig
from tests.integration.test_desk_workbenches import AUTOMATION_HUB, _client, _shape


def _record(name: str, client: Any, wb: str, tmp_path: Path, *, ran: Any = None) -> dict[str, Any]:
    """What the automation window reads, and the run answer that led here."""
    answers = {
        f"/api/workbenches/{wb}": client.get(f"/api/workbenches/{wb}").json(),
        f"/api/workbenches/{wb}/memory": client.get(f"/api/workbenches/{wb}/memory").json(),
    }
    body = {"gets": answers, **({"ran": ran} if ran is not None else {})}
    scrubbed = json.loads(re.sub(re.escape(str(tmp_path)), "/tmp/rig", json.dumps(body)))
    path = AUTOMATION_HUB / f"{name}.json"
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(json.dumps({
            "_source": "The hub's own answers, captured by tests/integration/test_desk_automation_program.py "
                       "(TestClient, isolated database, the Programs rig). "
                       "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit it.",
            "workbench_id": wb, **scrubbed}, indent=1, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answers {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    stored = json.loads(path.read_text())
    assert _shape({k: stored[k] for k in scrubbed}) == _shape(scrubbed), f"{path.name}: not the hub's shape"
    return scrubbed


def test_a_run_program_automation_starts_one_program_and_says_so_while_it_runs(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.kernel.runtime import _configure

    rig = Rig(tmp_path)
    monkeypatch.setattr(programs, "default_program_service", lambda db=None: rig.service)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: rig.db)
    rig.service._project_source = lambda _project_id: SimpleNamespace(primary_path=str(rig.repo))
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-app', 'App')")
    rig.db.notes.upsert(note_id="note-timeout", title="Login timeout", body_markdown="It times out.")
    rig.db.notes.upsert(note_id="note-retry", title="Retry the upload", body_markdown="It fails once.")
    _configure(rig.db)
    client = _client(rig.db)

    made = client.post("/api/workbenches", json={"id": "wb-nightly", "name": "Nightly fixes"})
    assert made.status_code == 201, made.text
    wb = made.json()["workbench"]["id"]
    saved = client.put(f"/api/workbenches/{wb}", json={
        "do_kind": "run_program", "instruction": "Fix each bug with a test.",
        "program_template": "fast-cycle", "program_control": "yolo",
        "program_runs_on": [{"profile": "codex-default", "engine": None}],
        "sources": ["project:proj-app", "note:note-timeout", "note:note-retry"],
    })
    assert saved.status_code == 200, saved.text

    new = _record("program-new", client, wb, tmp_path)["gets"][f"/api/workbenches/{wb}"]["workbench"]
    assert new["do_kind"] == "run_program" and new["results"] == []
    assert (new["program"]["template_name"], new["program"]["control_word"], new["program"]["runs_on_words"]) == (
        "Fast cycle", "YOLO", "Codex")

    first = client.post(f"/api/workbenches/{wb}/run", json={})
    assert first.status_code == 200, first.text
    run = first.json()["run"]
    assert run["program_started"] is True
    ran = _record("program-ran", client, wb, tmp_path, ran=run)["gets"][f"/api/workbenches/{wb}"]["workbench"]
    [result] = ran["results"]
    assert result["program"]["window"] == f"pullout:program:{run['program_id']}"
    assert result["program"]["total"] == 2 and result["text"].startswith("Started the program Nightly fixes")
    assert ran["program"]["latest"]["id"] == run["program_id"]
    program = rig.program(run["program_id"])
    assert program["origin_ref"] == f"automation:{wb}" and program["place"]["origin"]["title"] == "Nightly fixes"

    second = client.post(f"/api/workbenches/{wb}/run", json={})
    assert second.status_code == 200, second.text
    again = second.json()["run"]
    assert again["program_started"] is False and again["program_id"] == run["program_id"]
    assert again["reason"].endswith("is still running. Nothing started.")
    still = _record("program-still", client, wb, tmp_path, ran=again)["gets"][f"/api/workbenches/{wb}"]["workbench"]
    assert len(still["results"]) == 1 and len(rig.service.store.list_programs()) == 1
