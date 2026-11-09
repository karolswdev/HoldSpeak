"""PARKED 20261108 (Lane S2, the item queue parked): queue-run cases from
``tests/integration/test_desk_workbenches.py``.

Since 2026-11-08 an automation's run is a Program of one prompt step
(``automation_runs.run_as_program``), and Run now refuses an old queue
(``set_up_as_program``: it is set up as a program). These cases ran the
item queue (a refused item of three, an item's Re-run, the per-item time
limit, an old TODO queue's run before Make one). Not collected; they import
helpers of the live file. Restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations

# ruff: noqa
from tests.integration.test_desk_workbenches import *  # noqa: F401,F403


def _refusing_engine_rig(tmp_path: Path, monkeypatch) -> tuple[Database, TestClient, str, list[str], dict[str, Any]]:
    """Three items on the real routes and the real runner; only the provider
    constructor is a stub. The stub refuses "Item 2" with its own words and
    reports provider token counts the way MeetingIntel.last_usage does."""
    from holdspeak.intel.engine import MeetingIntelError
    from holdspeak.kernel.runtime import _configure

    state: dict[str, Any] = {"calls": 0, "refuse": True}

    class RefusingStub:
        active_provider = "stub-provider"
        active_model = "stub-model-7b"
        last_usage: dict[str, int] = {}

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            state["calls"] += 1
            if "[TASK]\nItem 2" in user_prompt and state["refuse"]:
                self.last_usage = {}
                raise MeetingIntelError("the stub refuses Item 2: no source is attached")
            memory = user_prompt.startswith("Task: ")
            self.last_usage = {"prompt_tokens": 3 if memory else 30, "completion_tokens": 2 if memory else 10,
                               "total_tokens": 5 if memory else 40}
            return f"result {state['calls']}"

    stub = RefusingStub()
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: stub)
    db = Database(tmp_path / "workbench.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    profile = db.profiles.upsert(profile_id="stub-profile", name="Stub", kind="openAICompatible",
                                 base_url="http://stub", model="stub-model-7b")
    recipe = db.recipes.upsert(recipe_id="stub-recipe", name="Stub agent", system_prompt="SYS", user_template="{input}")
    wb = db.workbenches.upsert(workbench_id="wb-truth", name="Truth bench", recipe_id=recipe.id, profile_id=profile.id)
    items = [db.workbench_items.upsert(item_id=f"item-{n}", workbench_id=wb.id, title=f"Item {n}", body=f"input {n}").id
             for n in (1, 2, 3)]
    _configure(db)
    return db, _client(db), wb.id, items, state


def test_a_run_with_one_refused_item_records_two_of_three_the_model_and_the_tokens(tmp_path: Path, monkeypatch) -> None:
    """Recon steps 14–16: the record said `0/0 done · NO MODEL`, tokens 0, a
    run with a failure was green, and the failed item said `Error: failed`."""
    db, client, wb, items, _ = _refusing_engine_rig(tmp_path, monkeypatch)

    ran = client.post(f"/api/workbenches/{wb}/run", json={})
    assert ran.status_code == 200, ran.text

    runs = client.get(f"/api/workbenches/{wb}/runs").json()["runs"]
    assert len(runs) == 1
    run = runs[0]
    assert (run["items_completed"], run["items_attempted"], run["items_failed"]) == (2, 3, 1), run
    assert run["status"] == "completed_with_failures", run
    assert run["model"] == "stub-model-7b", run
    assert run["egress_boundary"] == "cloud", run  # http://stub is not a private address
    # Two items (40 each) and their two memory notes (5 each): the provider's own counts.
    assert run["total_tokens"] == 90, run
    assert client.get(f"/api/workbenches/{wb}").json()["workbench"]["last_run"]["status"] == "completed_with_failures"

    failed = db.workbench_items.get(items[1])
    assert failed.status == "failed"
    assert failed.result == "Error: the stub refuses Item 2: no source is attached"
    assert db.workbench_items.get(items[0]).tokens_consumed == 40


def test_item_rerun_runs_only_that_item_and_gives_a_new_result(tmp_path: Path, monkeypatch) -> None:
    """Recon step 17: Re-run only queued the item; nothing ran until the top Run.
    The face's Re-run is now the PUT it always sent, then POST /run with the
    item's id (WorkbenchWindow.tsx rerunItem → triggerRun([item.id]))."""
    db, client, wb, items, state = _refusing_engine_rig(tmp_path, monkeypatch)
    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    assert db.workbench_items.get(items[1]).status == "failed"

    state["refuse"] = False
    queued = client.put(f"/api/workbenches/{wb}/items/{items[1]}", json={
        "status": "pending", "result": None, "result_egress": None, "tokens_consumed": 0, "completed_at": None})
    assert queued.status_code == 200, queued.text
    db.workbench_items.upsert(item_id="item-4", workbench_id=wb, title="Item 4", body="input 4")
    rerun = client.post(f"/api/workbenches/{wb}/run", json={"item_ids": [items[1]]})
    assert rerun.status_code == 200, rerun.text

    again = db.workbench_items.get(items[1])
    assert again.status == "done" and again.result.startswith("result "), again
    # Only that item ran: the other pending item still waits.
    assert db.workbench_items.get("item-4").status == "pending"
    newest = client.get(f"/api/workbenches/{wb}/runs").json()["runs"][0]
    assert (newest["items_completed"], newest["items_attempted"], newest["status"]) == (1, 1, "completed"), newest




def test_the_time_limit_is_per_item_and_comes_from_the_engine(tmp_path: Path, monkeypatch) -> None:
    """60 s for an HTTP engine; a CLI engine gets its preset's timeout."""
    from holdspeak.intel.cli_engine import PRESETS
    from holdspeak.services import automation_runs

    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-http", cli_bench="wb-cli")
    wb = _make_automation(client, "wb-http")
    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    with db._connection() as conn:
        row = conn.execute(
            """SELECT p.deadline_at, o.created_at FROM kernel_parent_runs p
               JOIN kernel_operations o ON o.operation_id = p.operation_id
               JOIN workbench_runs r ON r.parent_operation_id = p.operation_id WHERE r.workbench_id=?""",
            (wb,)).fetchone()
        revision = conn.execute("SELECT id FROM deployment_revisions LIMIT 1").fetchone()["id"]
        conn.execute(
            """INSERT INTO deployment_revisions (id, destination_id, kind, engine, model, boundary, endpoint)
               VALUES ('dep-cli', 'cli-claude', 'cli_engine', 'cli_v1', 'default', 'cloud', 'cli:claude')""")
    assert automation_runs.item_seconds(db, {"entries": [{"deployment_revision_id": revision}]}) == 60.0
    assert automation_runs.item_seconds(db, {"entries": [{"deployment_revision_id": revision},
                                                         {"deployment_revision_id": "dep-cli"}]}) \
        == PRESETS["claude"].timeout_seconds
    # A press reads the assigned engine before the run is admitted.
    assert automation_runs.assigned_item_seconds(db, wb) == 60.0
    agent = _make_automation(client, "wb-cli")
    assert automation_runs.assigned_item_seconds(db, agent) == PRESETS["claude"].timeout_seconds
    # The HTTP run was admitted for one 60 s item.
    started = datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00")).timestamp() \
        if isinstance(row["created_at"], str) else float(row["created_at"])
    assert 0 < float(row["deadline_at"]) - started <= 61, (row["deadline_at"], row["created_at"])


def test_an_old_todo_automation_shows_its_tasks_and_becomes_one_automation_in_one_press(
        tmp_path: Path, monkeypatch) -> None:
    import itertools

    import holdspeak.workbench_memory as memory

    monkeypatch.setattr(memory, "WORKBENCH_DIR", tmp_path / "workbenches")
    made_ids = itertools.count(1)
    monkeypatch.setattr("holdspeak.services.workbench_service._new_id",
                        lambda prefix: f"{prefix}_a9_{next(made_ids)}")
    db, client, prompts, made = _instruction_rig(tmp_path, monkeypatch, template=True)
    wb = made["workbench"]["id"]
    recipe = db.recipes.get(made["workbench"]["recipe_id"])
    agent_prompt = (recipe.user_template or "").strip() or recipe.system_prompt.strip()

    old = _record_window("old-queue", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert (old["instruction"], old["instruction_from"], old["instruction_shown"]) == ("", "agent", agent_prompt)
    titles = [item["title"] for item in old["items"]]
    assert titles and all(item["status"] == "pending" for item in old["items"])
    assert old["results"] == []

    # The queue runs as before: each task gets its own answer.
    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    ran = _record_window("old-queue-ran", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert [i["title"] for i in ran["items"]] == titles
    assert all(i["status"] == "done" and i["result"] and i["result_artifact_id"] for i in ran["items"])
    answers = {i["id"]: (i["result"], i["result_artifact_id"]) for i in ran["items"]}

    # One press: the agent's prompt becomes Do. Nothing else changes.
    pressed = client.post(f"/api/workbenches/{wb}/make-one")
    assert pressed.status_code == 200, pressed.text
    one = _record_window("old-made-one", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert (one["instruction"], one["instruction_from"], one["instruction_shown"]) == (
        agent_prompt, "automation", agent_prompt)
    assert one["recipe_id"] == recipe.id and db.recipes.get(recipe.id) is not None
    assert {i["id"]: (i["result"], i["result_artifact_id"]) for i in one["items"]} == answers
    assert all(db.plugins.get_artifact(a) is not None for _r, a in answers.values())
    # A second press changes nothing.
    again = client.post(f"/api/workbenches/{wb}/make-one").json()["workbench"]
    assert again["instruction"] == agent_prompt

    # Its next run makes one result (one occurrence), the old tasks untouched.
    before = len(prompts)
    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    assert len(prompts) == before + 1 and agent_prompt in prompts[-1]
    # Orchestrator ruling: the agent's prompt goes once (as the task), never
    # again as the system prompt.
    assert agent_prompt not in _SYSTEMS[-1] and prompts[-1].count(agent_prompt) == 1
    assert agent_prompt in _SYSTEMS[0]  # the queue run before the press still used the agent
    after = client.get(f"/api/workbenches/{wb}").json()["workbench"]
    [result] = after["results"]
    assert result["status"] == "done" and result["new"] is True
    kept = {i["id"]: (i["result"], i["result_artifact_id"]) for i in after["items"] if i["id"] in answers}
    assert kept == answers


def test_with_writes_the_automation_engine_and_refreezes_its_live_schedule(tmp_path: Path, monkeypatch) -> None:
    """Done when (A4, T1): With writes
    subject:workbench:<id>:capability:workbench.item; a live schedule is
    re-frozen on the new engine (scheduled runs ignored engine changes
    before); an off schedule stays off."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-with")
    db.profiles.upsert(profile_id="lan-profile", name="LAN Qwen", kind="openAICompatible",
                       base_url="http://192.168.1.43:8080/v1", model="qwen")
    wb = _make_automation(client, "wb-with")
    assert client.put(f"/api/workbenches/{wb}/when", json={"kind": "schedule", "every": "day", "time": "09:00"}).status_code == 200
    before = _live(db, wb)
    runner = WorkbenchRunner(db, _configure(db))
    assert [e["profile_id"] for e in runner._scheduled_route(before)["entries"]] == ["legacy-stub-profile"]

    used = client.put(f"/api/workbenches/{wb}/engine", json={"profile_id": "legacy-lan-profile"})
    assert used.status_code == 200, used.text
    summary = used.json()["workbench"]["assignment_summary"]
    assert (summary["chain"], summary["profile_id"]) == (["LAN Qwen"], "legacy-lan-profile")
    with db._connection() as conn:
        head = conn.execute("SELECT cleared FROM inference_assignment_heads WHERE assignment_key=?",
                            (f"subject:workbench:{wb}:capability:workbench.item",)).fetchone()
        old = conn.execute("SELECT state, revocation_reason FROM kernel_schedule_delegations WHERE id=?",
                           (before["id"],)).fetchone()
    assert head is not None and head["cleared"] == 0
    assert (old["state"], old["revocation_reason"]) == ("REVOKED", "engine_changed")
    after = _live(db, wb)
    assert after["id"] != before["id"]
    assert [e["profile_id"] for e in runner._scheduled_route(after)["entries"]] == ["legacy-lan-profile"]

    # An off schedule has nothing to re-freeze; the engine is still written.
    assert client.put(f"/api/workbenches/{wb}", json={"schedule_enabled": False}).status_code == 200
    back = client.put(f"/api/workbenches/{wb}/engine", json={"profile_id": "legacy-stub-profile"})
    assert back.status_code == 200 and back.json()["workbench"]["assignment_summary"]["profile_id"] == "legacy-stub-profile"
    assert _live(db, wb) is None
