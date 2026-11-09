"""The Workbench window's Park, on the hub side (the test diet, 2026-10-11).

Successors of the hub halves of tests/e2e/test_philo13_02_park_glass.py: the
real Workbench routes on an isolated database, with the browser test's own
seed (four items, two done, one artifact linked to an item) and the runner's
own claim statement. The face halves (receipts, the PARKED token, Restore)
are vitest: web/src/desk/components/__tests__/workbenchPark.test.tsx.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.primitives.workbenches import build_workbenches_router

OWNER = Principal(PrincipalKind.OWNER, "desk-workbenches")
TITLES = ["Draft rollback runbook", "Old sampling spike", "Rerun shard benchmark", "Close the audit ticket"]


def _client(db: Database) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_workbenches_router(
        WebContext(get_state=lambda: {}, workbench_service=WorkbenchService(db))))
    return TestClient(app)


def _seed(db: Database, client: TestClient) -> tuple[str, dict[str, str]]:
    """The glass seed, through the same routes (POST, POST items, PUT done)."""
    made = client.post("/api/workbenches", json={"name": "Ledger cutover bench"})
    assert made.status_code == 201, made.text
    wb = made.json()["workbench"]["id"]
    ids: dict[str, str] = {}
    for title in TITLES:
        added = client.post(f"/api/workbenches/{wb}/items", json={"title": title})
        assert added.status_code == 201, added.text
        ids[title] = added.json()["item"]["id"]
    for title in TITLES[2:]:
        done = client.put(f"/api/workbenches/{wb}/items/{ids[title]}", json={"status": "done"})
        assert done.status_code == 200, done.text
    db.plugins.record_artifact(
        artifact_id="p13-wb-artifact", meeting_id="", artifact_type="workbench_output",
        title="Spike result", body_markdown="Sampling at 1 in 10.",
        sources=[{"source_type": "input", "source_ref": f"workbench_item:{ids['Old sampling spike']}"}])
    return wb, ids


def _item_row(db: Database, item_id: str) -> dict[str, Any]:
    """The glass's own DB read: the row is kept; parked, status, links."""
    with db._connection() as conn:
        row = conn.execute("SELECT parked, status FROM workbench_items WHERE id = ?", (item_id,)).fetchone()
        links = conn.execute(
            "SELECT COUNT(*) FROM artifact_sources WHERE source_ref = ?", (f"workbench_item:{item_id}",)
        ).fetchone()[0]
    return {"present": row is not None, "parked": None if row is None else int(row[0]),
            "status": None if row is None else row[1], "links": links}


def _listed(client: TestClient, wb: str, *, parked: bool = False) -> list[str]:
    path = f"/api/workbenches/{wb}" + ("?parked=true" if parked else "")
    return [item["id"] for item in client.get(path).json()["workbench"]["items"]]


def test_park_one_and_clear_done_keep_the_rows_parked_across_a_reload(tmp_path: Path) -> None:
    """replaces: tests/e2e/test_philo13_02_park_glass.py::test_workbench_item_park_single_bulk_restore_and_reload
    (the hub half: the row is kept and parked in the DB, and a reload reads it parked)."""
    path = tmp_path / "workbench.db"
    db = Database(path)
    client = _client(db)
    wb, ids = _seed(db, client)
    spike = ids["Old sampling spike"]
    before = _item_row(db, spike)
    assert before == {"present": True, "parked": 0, "status": "pending", "links": 1}, before

    # Park (the face's one press is DELETE): kept, parked, its link kept.
    parked = client.delete(f"/api/workbenches/{wb}/items/{spike}")
    assert parked.status_code == 200, parked.text
    assert parked.json()["parked"] == spike
    assert _item_row(db, spike) == {**before, "parked": 1}
    assert spike not in _listed(client, wb)
    assert _listed(client, wb, parked=True) == [spike]

    # A reload is a new read of the same database: still parked.
    db.close()
    db = Database(path)
    client = _client(db)
    assert _item_row(db, spike) == {**before, "parked": 1}
    assert _listed(client, wb, parked=True) == [spike]

    # Restore brings it back with its link.
    restored = client.post(f"/api/workbenches/{wb}/items/restore", json={"item_ids": [spike]})
    assert restored.status_code == 200, restored.text
    assert restored.json()["restored"] == [spike]
    assert _item_row(db, spike) == before
    assert spike in _listed(client, wb)

    # Clear done parks both done items at once; a reload reads both parked.
    done = [ids[t] for t in TITLES[2:]]
    bulk = client.post(f"/api/workbenches/{wb}/items/park", json={"item_ids": done})
    assert bulk.status_code == 200, bulk.text
    assert bulk.json()["parked"] == done
    db.close()
    db = Database(path)
    client = _client(db)
    assert [_item_row(db, i)["parked"] for i in done] == [1, 1]
    assert sorted(_listed(client, wb, parked=True)) == sorted(done)

    # Restore each, one at a time (the face restores from the Parked filter).
    for item_id in done:
        one = client.post(f"/api/workbenches/{wb}/items/{item_id}/restore")
        assert one.status_code == 200, one.text
        assert one.json()["item"]["parked"] is False
    assert [_item_row(db, i) for i in done] == [
        {"present": True, "parked": 0, "status": "done", "links": 0}
    ] * 2
    assert _listed(client, wb, parked=True) == []


def test_a_claimed_item_is_refused_in_place(tmp_path: Path) -> None:
    """replaces: tests/e2e/test_philo13_02_park_glass.py::test_a_claimed_item_is_refused_in_place
    A run claims the item between the face's read and his press: Park is
    refused (409, the status the face reads to say `Could not park · A run holds
    it`, WorkbenchWindow.tsx), and the row stays claimed and not parked."""
    db = Database(tmp_path / "workbench.db")
    client = _client(db)
    wb, ids = _seed(db, client)
    item = ids["Draft rollback runbook"]
    assert item in _listed(client, wb)  # the face's read: pending, not parked

    # The runner's own claim statement (holdspeak/services/workbench_runner.py:257),
    # as the glass ran it, after the read and before the press.
    with db._connection() as conn:
        claimed = conn.execute(
            "UPDATE workbench_items SET status='claimed', claimed_at=? WHERE id=? AND status='pending' AND parked=0",
            (datetime.now().isoformat(), item),
        )
        assert claimed.rowcount == 1

    refused = client.delete(f"/api/workbenches/{wb}/items/{item}")
    assert refused.status_code == 409, refused.text
    row = _item_row(db, item)
    assert row["parked"] == 0 and row["status"] == "claimed", row
    assert item in _listed(client, wb)
    assert _listed(client, wb, parked=True) == []


# ── A0 "Tell the truth" (betterment/workbench/RECIPE.md, recon steps 14–17) ──

# ── A2 "One automation = one instruction + sources; each run = one result" ──
# (betterment/workbench/RECIPE.md, slice A2). The real routes, the real runner,
# the real conductor tick and the real WatchService; only the provider
# constructor is a stub, and it replies from tests/fixtures/automations.

import json as _json  # noqa: E402

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "automations"
INBOX = "hs-seed-inbox"
DO = "Write my weekly update from these notes."
#: The system prompt of each engine call the rig's stub answered (not the memory note).
_SYSTEMS: list[str] = []


def _instruction_rig(tmp_path: Path, monkeypatch, *benches: str, template: bool = False,
                     cli_bench: str = "", engine_name: str = "Stub",
                     lessons: list[str] | None = None,
                     inbox: bool = True) -> tuple[Database, TestClient, list[str], dict[str, Any]]:
    """The A0 rig's shape: the engine (a legacy profile on each automation)
    is bound before the kernel starts, so the owner's first write seeds the
    subject assignment. ``benches`` are plain automations; ``template`` adds
    the TODO template as it was instantiated before A2."""
    from holdspeak.kernel.runtime import _configure

    replies = _json.loads((_FIXTURES / "engine_replies.json").read_text())
    prompts: list[str] = []
    _SYSTEMS.clear()

    class RecordingStub:
        active_provider = "stub-provider"
        active_model = "stub-model-7b"
        last_usage: dict[str, int] = {}

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            if user_prompt.startswith("Task: "):  # the memory note after an item
                self.last_usage = {"total_tokens": 5}
                return lessons.pop(0) if lessons else replies["memory"]
            prompts.append(user_prompt)
            _SYSTEMS.append(str(system_prompt or ""))
            if "Refuse this one." in user_prompt:
                from holdspeak.intel.engine import MeetingIntelError

                self.last_usage = {}
                raise MeetingIntelError("the stub refuses: no source is attached")
            self.last_usage = {"total_tokens": 40}
            return replies["pr_summary"] if "[EVENT]" in user_prompt else replies["weekly_update"]

    stub = RecordingStub()
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: stub)
    db = Database(tmp_path / "automation.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    db.profiles.upsert(profile_id="stub-profile", name=engine_name, kind="openAICompatible",
                       base_url="http://stub", model="stub-model-7b")
    for bench in benches:
        db.workbenches.upsert(workbench_id=bench, name="Weekly update", profile_id="stub-profile")
    if cli_bench:
        db.profiles.upsert(profile_id="cli-profile", name="Claude Code", kind="cliCommand",
                           base_url="cli:claude", model="default")
        db.workbenches.upsert(workbench_id=cli_bench, name="Agent update", profile_id="cli-profile")
    made: dict[str, Any] = {}
    if template:
        made = WorkbenchService(db).instantiate_template(OWNER, "todo-agent", profile_id="stub-profile")
    if inbox:  # a seeded desk; a fresh desk has no Inbox until a result needs one (A6)
        db.directories.upsert(directory_id=INBOX, name="Inbox")
    db.notes.upsert(note_id="note-sync", title="Platform sync", body_markdown="The cutover moves to Thursday.")
    db.notes.upsert(note_id="note-hiring", title="Hiring", body_markdown="Two loops are booked for next week.")
    _configure(db)
    return db, _client(db), prompts, made


def _make_automation(client: TestClient, wb: str, **fields: Any) -> str:
    """Give an automation its instruction and two note sources (the PUT a
    face sends); it has no agent: the instruction is the job."""
    made = client.put(f"/api/workbenches/{wb}", json={
        "instruction": DO, "sources": ["note:note-sync", "note:note-hiring"], **fields,
    })
    assert made.status_code == 200, made.text
    body = made.json()["workbench"]
    assert (body["instruction"], body["sources"], body["output_target"]) == (
        DO, ["note:note-sync", "note:note-hiring"], fields.get("output_target", "inbox"))
    assert body["recipe_id"] is None and body["instruction_from"] == "automation"
    return wb


def _inbox_notes(db: Database) -> list[Any]:
    with db._connection() as conn:
        ids = [row[0].removeprefix("note:") for row in conn.execute(
            "SELECT primitive_id FROM directory_memberships WHERE directory_id=? AND deleted=0 ORDER BY created_at",
            (INBOX,)).fetchall()]
    return [db.notes.get(note_id) for note_id in ids if note_id.startswith("note_result_")]


def test_a_scheduled_instruction_makes_one_inbox_note_per_tick_that_reads_both_notes(tmp_path: Path, monkeypatch) -> None:
    """Done when (A2): an instruction, two note sources and the Every-minute
    schedule give one Inbox note per tick, and the note reads both notes."""
    from types import SimpleNamespace

    from holdspeak.workbench_conductor import WorkbenchConductor

    db, client, prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-weekly")
    wb = _make_automation(client, "wb-weekly")
    enabled = client.put(f"/api/workbenches/{wb}", json={"schedule": "* * * * *", "schedule_enabled": True})
    assert enabled.status_code == 200, enabled.text
    assert enabled.json()["workbench"]["schedule_enabled"] is True

    # A controlled clock: two ticks, one minute apart.
    clock = {"now": 1_800_000_000.0}
    monkeypatch.setattr("holdspeak.workbench_conductor.time", SimpleNamespace(time=lambda: clock["now"]))
    conductor = WorkbenchConductor()
    conductor._tick_body()
    conductor._tick_body()  # the same minute: no second run
    clock["now"] += 60
    conductor._tick_body()

    notes = _inbox_notes(db)
    assert len(notes) == 2, [n.title for n in notes]
    assert len(prompts) == 2
    for prompt in prompts:
        assert "The cutover moves to Thursday." in prompt and "Two loops are booked for next week." in prompt
        assert DO in prompt
    for note in notes:
        assert note.title.startswith("Weekly update, ")
        assert "the cutover moves to Thursday" in note.body_markdown
        assert f"(/?open=workbench:{wb})" in note.body_markdown

    detail = client.get(f"/api/workbenches/{wb}").json()["workbench"]
    results = detail["results"]
    assert len(results) == 2 and all(r["status"] == "done" and r["new"] for r in results), results
    runs = client.get(f"/api/workbenches/{wb}/runs").json()["runs"]
    assert [(r["items_completed"], r["items_attempted"], r["status"]) for r in runs] == [(1, 1, "completed")] * 2

    # A result is NEW until it is opened (decision 5), never "pending-review".
    # 2026-11-08: each run is a Program of one prompt step; its result id is the step's.
    artifact_id = results[0]["artifact_id"]
    assert all(r["program"]["state"] == "done" for r in results)
    opened = client.post(f"/api/workbenches/{wb}/results/{artifact_id}/open")
    assert opened.status_code == 200, opened.text
    assert opened.json()["result"]["status"] == "read"
    after = client.get(f"/api/workbenches/{wb}").json()["workbench"]["results"]
    assert [r["new"] for r in after] == [False, True]


def test_a_review_request_event_makes_one_result_about_that_pr(tmp_path: Path, monkeypatch) -> None:
    """Done when (A2): an event (a GitHub review-request answer) gives one
    result about that PR. The gh answers are replayed through the real
    GitHubWatchSource; no process runs and nothing leaves the machine."""
    import subprocess

    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import GitHubWatchSource

    db, client, prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-review")
    wb = _make_automation(client, "wb-review")
    wire = _json.loads((_FIXTURES / "gh_pr_review_requested.json").read_text())

    def snapshot(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def replay(command, **_kwargs):
            assert command[:3] == ["gh", "pr", "list"]
            return subprocess.CompletedProcess(command, 0, _json.dumps(rows), "")
        return GitHubWatchSource(runner=replay).snapshot(
            OWNER, query_kind="pull_requests", query={"repository": wire["repository"]})

    # The watch fold (2026-11-08): the event start is a watch.
    rows = {"now": wire["before"]}
    watches = WatchService(db, snapshot_fetcher=lambda *_a, **_k: snapshot(rows["now"]))
    watch = watches.start_automation_event(
        OWNER, workbench_id=wb, preset_id="github-review-requested", repository=wire["repository"])
    rows["now"] = wire["after"]
    changed = watches.evaluate_once(OWNER, watch["id"])

    # gh also reports the review decision change; only the review request starts it.
    assert changed["transitions"] >= 1
    assert len(prompts) == 1
    assert "https://github.com/acme/ledger/pull/418" in prompts[0] and DO in prompts[0]
    results = client.get(f"/api/workbenches/{wb}").json()["workbench"]["results"]
    assert len(results) == 1, results
    assert results[0]["title"] == "Move the ledger cutover behind a flag"
    assert results[0]["status"] == "done" and results[0]["new"] is True
    notes = _inbox_notes(db)
    assert [n.title for n in notes] == ["Move the ledger cutover behind a flag"]
    assert "PR 418" in notes[0].body_markdown

    # The same answer again is no new event and no second result.
    again = watches.evaluate_once(OWNER, watch["id"])
    assert again.get("transitions", 0) == 0 and len(_inbox_notes(db)) == 1 and len(prompts) == 1


def test_an_old_template_automation_is_set_up_as_a_program(tmp_path: Path, monkeypatch) -> None:
    """An automation with no instruction shows its agent's prompt as its Do
    text without writing it (A2); since 2026-11-08 Run now does not run its
    queue: Programs run it, so the hub names the refusal (set it up as a
    program) and nothing runs."""
    db, client, prompts, made = _instruction_rig(tmp_path, monkeypatch, template=True)
    wb = made["workbench"]
    starters = len(wb["items"])
    assert starters >= 1

    detail = client.get(f"/api/workbenches/{wb['id']}").json()["workbench"]
    assert detail["instruction"] == "" and detail["instruction_from"] == "agent"
    recipe = db.recipes.get(wb["recipe_id"])
    assert detail["instruction_shown"] == ((recipe.user_template or "").strip() or recipe.system_prompt.strip())

    ran = client.post(f"/api/workbenches/{wb['id']}/run", json={})
    assert ran.status_code == 409, ran.text
    assert ran.json()["code"] == "set_up_as_program"
    assert prompts == []
    items = db.workbench_items.list_for_workbench(wb["id"])
    assert len(items) == starters and all(item.status == "pending" for item in items)
    assert _inbox_notes(db) == []
    assert db.workbenches.get(wb["id"]).instruction == ""  # nothing rewritten on read
    assert client.get(f"/api/workbenches/{wb['id']}").json()["workbench"]["results"] == []


def test_a_result_for_needs_you_or_a_destination_is_a_door_item_or_a_prepared_send(tmp_path: Path, monkeypatch) -> None:
    """``needs_you`` adds one Door item the owner holds (due today); a
    destination only prepares the send: he presses Send."""
    from holdspeak.db.channels import BUILTIN_FOLDER_ID

    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-needs", "wb-send")
    needs = _make_automation(client, "wb-needs", output_target="needs_you")
    ran = client.post(f"/api/workbenches/{needs}/run", json={})
    assert ran.status_code == 200, ran.text
    assert [d["outcome"] for d in ran.json()["run"]["deliveries"]] == ["added"]
    artifact_id = client.get(f"/api/workbenches/{needs}").json()["workbench"]["results"][0]["artifact_id"]
    with db._connection() as conn:
        # 2026-11-08: a run is a Program of one prompt step; the result's id is the step's.
        door = conn.execute("SELECT owner, due, source_type, task FROM action_items WHERE source_ref=?",
                            (f"program_step:{artifact_id}",)).fetchall()
    assert len(door) == 1 and door[0]["owner"] == "me" and door[0]["source_type"] == "automation_result"
    assert door[0]["due"] == datetime.now().astimezone().date().isoformat()
    assert _inbox_notes(db) == []

    refused = client.put(f"/api/workbenches/{needs}", json={"output_target": "destination:nowhere"})
    assert refused.status_code == 400, refused.text
    sent = _make_automation(client, "wb-send", output_target=f"destination:{BUILTIN_FOLDER_ID}")
    ran = client.post(f"/api/workbenches/{sent}/run", json={})
    assert ran.status_code == 200, ran.text
    assert [d["outcome"] for d in ran.json()["run"]["deliveries"]] == ["prepared"]
    note_id = ran.json()["run"]["deliveries"][0]["note_id"]  # the answer is a note; the send is prepared from it
    with db._connection() as conn:
        sends = conn.execute("SELECT state FROM channel_sends WHERE document_ref=?",
                             (f"note:{note_id}",)).fetchall()
    assert [row["state"] for row in sends] == ["prepared"]  # nothing sent


def test_an_older_database_gains_the_three_columns_on_open(tmp_path: Path) -> None:
    """Additive schema: the one schema adds instruction, sources_json and
    output_target to an older workbenches table; old rows read as a queue."""
    import sqlite3

    path = tmp_path / "older.db"
    Database(path)
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """ALTER TABLE workbenches RENAME TO workbenches_new;
           CREATE TABLE workbenches (id TEXT PRIMARY KEY, name TEXT NOT NULL DEFAULT '', recipe_id TEXT,
             profile_id TEXT, resolver_profile_id TEXT, schedule TEXT,
             schedule_enabled INTEGER NOT NULL DEFAULT 0, schedule_revision INTEGER NOT NULL DEFAULT 1,
             item_order_json TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL DEFAULT (datetime('now')),
             last_modified TEXT NOT NULL DEFAULT (datetime('now')), deleted INTEGER NOT NULL DEFAULT 0);
           DROP TABLE workbenches_new;
           INSERT INTO workbenches (id, name) VALUES ('wb-old', 'Old bench');""")
    conn.commit()
    conn.close()
    db = Database(path)
    old = db.workbenches.get("wb-old")
    assert (old.instruction, old.sources_json, old.output_target) == ("", "[]", "inbox")


def test_a_failed_result_keeps_its_reason_its_sources_and_its_place(tmp_path: Path, monkeypatch) -> None:
    """A failed run is a result too: it shows the engine's words, keeps the
    automation's sources, and nothing is delivered."""
    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-fails")
    _make_automation(client, "wb-fails")
    assert client.put("/api/workbenches/wb-fails", json={"instruction": "Refuse this one."}).status_code == 200
    ran = client.post("/api/workbenches/wb-fails/run", json={})
    assert ran.status_code == 200, ran.text
    assert "deliveries" not in ran.json()["run"]
    [result] = client.get("/api/workbenches/wb-fails").json()["workbench"]["results"]
    assert result["status"] == "failed" and result["error"] == "the stub refuses: no source is attached", result
    from holdspeak.db.programs import ProgramStore

    # The run's step keeps the automation's sources (2026-11-08: the run is a Program).
    assert ProgramStore(db).get_step(result["item_id"])["sources"] == ["note:note-sync", "note:note-hiring"]
    assert _inbox_notes(db) == []


# ── A3 "The automation window" (betterment/workbench/RECIPE.md, slice A3) ──
# The hub half of the window: each result carries what the card shows (the
# answer, seconds, model, the Inbox note), the About line names its sources,
# and Forget removes one lesson. The face half replays the answers recorded
# here (web/src/desk/__tests__/fixtures/automation-hub/*.json;
# HOLDSPEAK_WIRE_WRITE=1 rewrites them, else this test fences their shape).

import os as _os  # noqa: E402
import re as _re  # noqa: E402

AUTOMATION_HUB = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "automation-hub"
LESSONS = ["Mira owns the rollback runbook; name her first.", "Keep the update under ten lines."]


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(v) for v in value]
    return "null" if value is None else type(value).__name__


def _record_window(name: str, client: TestClient, wb: str, tmp_path: Path) -> dict[str, Any]:
    """What the automation window reads: the automation and its lessons."""
    answers = {
        f"/api/workbenches/{wb}": client.get(f"/api/workbenches/{wb}").json(),
        f"/api/workbenches/{wb}/memory": client.get(f"/api/workbenches/{wb}/memory").json(),
    }
    text = _re.sub(_re.escape(str(tmp_path)), "/tmp/rig", _json.dumps(answers))
    scrubbed = _json.loads(text)
    path = AUTOMATION_HUB / f"{name}.json"
    if _os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_json.dumps({
            "_source": "The hub's own answers, captured by tests/integration/test_desk_workbenches.py "
                       "(TestClient, isolated database, the A2 rig's recorded engine replies). "
                       "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit it.",
            "workbench_id": wb, "gets": scrubbed}, indent=1, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answers {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    stored = _json.loads(path.read_text())["gets"]
    assert _shape(stored) == _shape(scrubbed), f"{path.name}: the stored answers are not the hub's shape"
    return scrubbed


def test_the_automation_window_reads_its_sentence_results_and_lessons(tmp_path: Path, monkeypatch) -> None:
    """Done when (A3, hub half): an automation's one read gives the sentence
    (Do, About by name, When, With) and its results newest first, each with
    the answer, the seconds, the model and its Inbox note; a failed run gives
    its reason; Forget removes one lesson and keeps the rest."""
    import holdspeak.workbench_memory as memory

    monkeypatch.setattr(memory, "WORKBENCH_DIR", tmp_path / "workbenches")
    db, client, _prompts, _ = _instruction_rig(
        tmp_path, monkeypatch, "wb-friday", engine_name="LAN Qwen", lessons=list(LESSONS))
    wb = _make_automation(client, "wb-friday")
    assert client.put(f"/api/workbenches/{wb}", json={"name": "Friday team update"}).status_code == 200
    db.notes.upsert(note_id="note-gone", title="", body_markdown="An untitled note.")

    empty = _record_window("empty", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert empty["results"] == []
    assert empty["instruction_shown"] == DO and empty["event_starts"] == []
    assert [(s["label"], s["kind"], s["missing"]) for s in empty["sources_shown"]] == [
        ("Platform sync", "note", False), ("Hiring", "note", False)]

    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    one = _record_window("one", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    [first] = one["results"]
    assert first["status"] == "done" and first["new"] is True and first["error"] is None
    assert first["text"].startswith("## Weekly update") and "cutover moves to Thursday" in first["text"]
    assert first["model"] == "stub-model-7b" and first["boundary"] == "cloud"
    assert isinstance(first["seconds"], int) and first["seconds"] >= 0
    assert first["note_id"] and db.notes.get(first["note_id"]) is not None  # the Inbox note exists

    # A failed run: its reason in words, no answer, no note.
    assert client.put(f"/api/workbenches/{wb}", json={"instruction": "Refuse this one."}).status_code == 200
    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    failed = _record_window("failed", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    newest = failed["results"][0]
    assert newest["status"] == "failed" and newest["error"] == "the stub refuses: no source is attached"
    assert newest["text"] is None and newest["note_id"] is None

    # Run again with the real instruction: the newest is a good result again.
    assert client.put(f"/api/workbenches/{wb}", json={"instruction": DO}).status_code == 200
    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    populated = _record_window("populated", client, wb, tmp_path)
    detail = populated[f"/api/workbenches/{wb}"]["workbench"]
    assert [r["status"] for r in detail["results"]] == ["done", "failed", "done"]
    lessons = populated[f"/api/workbenches/{wb}/memory"]["entries"]
    assert [e["content"] for e in lessons] == list(reversed(LESSONS))

    # Forget the newest lesson (index 0, with its timestamp): the other stays.
    stale = client.delete(f"/api/workbenches/{wb}/memory/0", params={"at": "2000-01-01T00:00:00Z"})
    assert stale.status_code == 404, stale.text  # a lesson written meanwhile is never forgotten in its place
    forgot = client.delete(f"/api/workbenches/{wb}/memory/0", params={"at": lessons[0]["timestamp"]})
    assert forgot.status_code == 200, forgot.text
    after = _record_window("forgot", client, wb, tmp_path)[f"/api/workbenches/{wb}/memory"]["entries"]
    assert [e["content"] for e in after] == [LESSONS[0]]

    # Opening the newest result reads it: NEW goes, the others stay NEW.
    artifact = detail["results"][0]["artifact_id"]
    assert client.post(f"/api/workbenches/{wb}/results/{artifact}/open").status_code == 200
    opened = _record_window("opened", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert [r["new"] for r in opened["results"]] == [False, False, True]

    # A source that is gone stays listed as missing, never by its id.
    assert client.put(f"/api/workbenches/{wb}", json={
        "sources": ["note:note-sync", "note:note-gone", "note:note-never"]}).status_code == 200
    shown = client.get(f"/api/workbenches/{wb}").json()["workbench"]["sources_shown"]
    assert [(s["label"], s["missing"]) for s in shown] == [("Platform sync", False), ("Untitled", False), ("", True)]


# ── A4 "When, and With" (betterment/workbench/RECIPE.md, slice A4) ─────────
# The hub half: a When choice is stored (a schedule as cron, never shown),
# turned on, and says when it fires next; With writes the automation's own
# engine and re-freezes a live schedule, so a scheduled run uses the new
# engine; the Spend limit per run is the automation's own; an event start's
# occurrence runs at once.


def _live(db: Database, wb: str) -> dict[str, Any] | None:
    from holdspeak.services.schedule_delegation import ScheduleDelegationService

    return ScheduleDelegationService(db).live(wb)


def test_when_every_friday_at_three_is_stored_as_cron_turned_on_and_says_when_next(tmp_path: Path, monkeypatch) -> None:
    """Done when (A4): "Every Friday at 3 PM" is one choice; the hub turns it
    on (a live delegation) and gives next_run_at, a Friday at 15:00 on the
    hub's clock. Only when I press Run now turns every start off."""
    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-when")
    wb = _make_automation(client, "wb-when")

    chosen = client.put(f"/api/workbenches/{wb}/when", json={"kind": "schedule", "every": "week", "day": 5, "time": "15:00"})
    assert chosen.status_code == 200, chosen.text
    body = chosen.json()["workbench"]
    assert (body["schedule"], body["schedule_enabled"], body["when_kind"]) == ("0 15 * * 5", True, "schedule")
    fires = datetime.fromisoformat(body["next_run_at"].replace("Z", "+00:00")).astimezone()
    assert (fires.weekday(), fires.hour, fires.minute) == (4, 15, 0)  # Friday 15:00 local
    assert _live(db, wb) is not None and _live(db, wb)["cadence"] == "0 15 * * 5"

    for when, cron in [({"every": "day", "time": "08:30"}, "30 8 * * *"),
                       ({"every": "weekday", "time": "07:00"}, "0 7 * * 1-5"),
                       ({"every": "hour"}, "0 * * * *")]:
        again = client.put(f"/api/workbenches/{wb}/when", json={"kind": "schedule", **when})
        assert again.status_code == 200 and again.json()["workbench"]["schedule"] == cron, again.text
    refused = client.put(f"/api/workbenches/{wb}/when", json={"kind": "schedule", "every": "week", "time": "15:00"})
    assert refused.status_code == 400 and refused.json()["error"] == "Choose a day of the week"

    manual = client.put(f"/api/workbenches/{wb}/when", json={"kind": "manual"}).json()["workbench"]
    assert (manual["schedule"], manual["schedule_enabled"], manual["next_run_at"], manual["when_kind"]) == (
        None, False, None, "manual")
    assert _live(db, wb) is None
    # The events the editor offers are the ones the hub can deliver: GitHub,
    # never Jira (its preset carries no connection) or "A meeting ends".
    assert [e["id"] for e in manual["when_events"]] == [
        "github-review-requested", "github-checks-failed", "github-pr-merged"]


def test_the_spend_limit_per_run_is_the_automation_own_and_overrides_the_engine(tmp_path: Path, monkeypatch) -> None:
    """With's Spend limit per run: stored on the automation (null = the
    engine's own), refused outside $0-$1000, and the run hands it to an
    agent CLI that stops at a limit (a copy: the routed engine is shared)."""
    from holdspeak.intel.cli_engine import CliEngine, parse_cli_endpoint
    from holdspeak.services.program_prompt import _MeteredPromptAdapter

    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-spend")
    wb = _make_automation(client, "wb-spend")
    set_ = client.put(f"/api/workbenches/{wb}/engine", json={"spend_limit_usd": 0.5})
    assert set_.status_code == 200 and set_.json()["workbench"]["spend_limit_usd"] == 0.5, set_.text
    for bad in (0, -1, 1001, "1", True):
        assert client.put(f"/api/workbenches/{wb}/engine", json={"spend_limit_usd": bad}).status_code == 400
    cleared = client.put(f"/api/workbenches/{wb}/engine", json={"spend_limit_usd": None})
    assert cleared.json()["workbench"]["spend_limit_usd"] is None
    # An upsert (the Do editor's PUT) never clears it.
    client.put(f"/api/workbenches/{wb}/engine", json={"spend_limit_usd": 0.25})
    client.put(f"/api/workbenches/{wb}", json={"instruction": DO})
    assert db.workbenches.get(wb).spend_limit_usd == 0.25

    claude = CliEngine(parse_cli_endpoint("cli:claude?spend_limit_usd=2")[0], spend_limit_usd=2.0)
    limited = _MeteredPromptAdapter(0.25)._limited(claude)
    assert limited is not claude and (limited.spend_limit_usd, claude.spend_limit_usd) == (0.25, 2.0)
    codex = CliEngine(parse_cli_endpoint("cli:codex")[0])
    assert _MeteredPromptAdapter(0.25)._limited(codex) is codex  # Codex cannot stop at a limit
    assert _MeteredPromptAdapter(None)._limited(claude) is claude


def test_an_event_choice_turns_its_start_on_and_its_occurrence_runs_without_a_press(tmp_path: Path, monkeypatch) -> None:
    """When something happens: the choice installs and turns on the start
    (a quiet baseline first), stops the schedule, and the event's
    occurrence runs at once (A2 follow-up: it used to wait for a press that
    never came). Since 2026-11-08 the start is a watch (WatchService): one
    real event from the recorded gh answer is driven through the watch's
    evaluation to one Program run and its result."""
    import subprocess

    import holdspeak.services.watch_sources as watch_sources
    from holdspeak.services.watch_service import AUTOMATION_INTENT_PREFIX, WatchService
    from holdspeak.services.watch_sources import GitHubWatchSource

    import holdspeak.workbench_memory as memory

    monkeypatch.setattr(memory, "WORKBENCH_DIR", tmp_path / "workbenches")
    db, client, prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-event")
    wb = _make_automation(client, "wb-event")
    wire = _json.loads((_FIXTURES / "gh_pr_review_requested.json").read_text())

    def snapshot(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def replay(command, **_kwargs):
            assert command[:3] == ["gh", "pr", "list"]
            return subprocess.CompletedProcess(command, 0, _json.dumps(rows), "")
        return GitHubWatchSource(runner=replay).snapshot(
            OWNER, query_kind="pull_requests", query={"repository": wire["repository"]})

    monkeypatch.setattr(watch_sources, "fetch_watch_snapshot", lambda *_a, **_k: snapshot(wire["before"]))
    assert client.put(f"/api/workbenches/{wb}/when", json={"kind": "schedule", "every": "day", "time": "09:00"}).status_code == 200
    bad = client.put(f"/api/workbenches/{wb}/when", json={"kind": "event", "event_id": "jira-assigned-to-me",
                                                           "repository": wire["repository"]})
    assert bad.status_code == 400, bad.text
    chosen = client.put(f"/api/workbenches/{wb}/when", json={
        "kind": "event", "event_id": "github-review-requested", "repository": wire["repository"]})
    assert chosen.status_code == 200, chosen.text
    body = chosen.json()["workbench"]
    assert (body["schedule"], body["schedule_enabled"], body["when_kind"]) == (None, False, "event")
    [start] = body["event_starts"]
    assert start["enabled"] is True and start["event_pattern"] == "github.pr.review_requested"
    # A5: the face's About line for an event start (the thing that happened).
    _record_window("about-event", client, wb, tmp_path)
    watch = db.automations.get_watch(start["id"])
    assert (watch["intent"], watch["state"]) == (AUTOMATION_INTENT_PREFIX + wb, "active")
    assert db.automations.list_reactions() == []  # no legacy Watch + Reaction pair

    monkeypatch.setattr(watch_sources, "fetch_watch_snapshot", lambda *_a, **_k: snapshot(wire["after"]))
    WatchService(db).evaluate_once(OWNER, start["id"])
    # The event's run is a Program of one prompt step (2026-11-08); no occurrence item.
    from holdspeak.db.programs import ProgramStore
    from holdspeak.services.automation_runs import program_runs

    [program] = program_runs(db, wb)
    [step] = ProgramStore(db).list_steps(program["id"])
    assert step["facts"]["run_context"]["event_type"] == "github.pr.review_requested"
    assert db.workbench_items.list_for_workbench(wb) == []
    assert len(prompts) == 1 and "https://github.com/acme/ledger/pull/418" in prompts[0]
    # The same evaluation again mints nothing and runs nothing twice.
    WatchService(db).evaluate_once(OWNER, start["id"])
    assert len(prompts) == 1
    results = client.get(f"/api/workbenches/{wb}").json()["workbench"]["results"]
    assert [(r["title"], r["status"]) for r in results] == [("Move the ledger cutover behind a flag", "done")]

    # The same choice again turns the same start back on (no second start);
    # Run now only stops it.
    again = client.put(f"/api/workbenches/{wb}/when", json={
        "kind": "event", "event_id": "github-review-requested", "repository": wire["repository"]})
    assert [s["id"] for s in again.json()["workbench"]["event_starts"]] == [start["id"]]
    manual = client.put(f"/api/workbenches/{wb}/when", json={"kind": "manual"}).json()["workbench"]
    assert manual["event_starts"] == [] and db.automations.get_watch(start["id"])["state"] == "paused"


def test_a_legacy_event_start_needs_setting_again(tmp_path: Path, monkeypatch) -> None:
    """Watch fold 4 (2026-11-08): an event start saved as a legacy Reaction
    runs nothing; there is no migration. The window's When line says it must
    be set again (``when_needs_reset``) until he saves a When choice."""
    import holdspeak.workbench_memory as memory

    monkeypatch.setattr(memory, "WORKBENCH_DIR", tmp_path / "workbenches")
    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-legacy")
    wb = _make_automation(client, "wb-legacy")
    db.automations.create_reaction(
        reaction_id="reaction-old", name="PR review requested", watch_id=None,
        event_pattern="github.pr.review_requested", workbench_id=wb,
        title_template="{entity_title}", auto_run=False, enabled=True,
    )
    db.workbenches.set_when_json(wb, {"kind": "event", "reaction_id": "reaction-old"})
    old = client.get(f"/api/workbenches/{wb}").json()["workbench"]
    assert (old["when_needs_reset"], old["event_starts"]) == (True, [])
    saved = client.put(f"/api/workbenches/{wb}/when", json={"kind": "manual"})
    assert saved.status_code == 200, saved.text
    assert saved.json()["workbench"]["when_needs_reset"] is False


def test_a_schedule_with_no_engine_is_kept_off_and_says_why(tmp_path: Path) -> None:
    """A fresh desk has no engine to freeze: the schedule is saved, off, and
    the refusal says to choose an engine under With."""
    from holdspeak.kernel.runtime import _configure

    db = Database(tmp_path / "bare.db")
    _configure(db)
    client = _client(db)
    wb = client.post("/api/workbenches", json={"name": "Friday team update"}).json()["workbench"]["id"]
    assert client.put(f"/api/workbenches/{wb}", json={"instruction": DO}).status_code == 200
    refused = client.put(f"/api/workbenches/{wb}/when", json={"kind": "schedule", "every": "week", "day": 5, "time": "15:00"})
    assert refused.status_code == 400, refused.text
    assert refused.json()["error"] == "The schedule is saved but off: choose an engine under With, then turn it on."
    kept = client.get(f"/api/workbenches/{wb}").json()["workbench"]
    assert (kept["schedule"], kept["schedule_enabled"], kept["next_run_at"]) == ("0 15 * * 5", False, None)


def test_the_when_and_with_lines_record_their_answers(tmp_path: Path, monkeypatch) -> None:
    """The face half of A4 replays these answers
    (web/src/desk/__tests__/automation.app.test.tsx): Run now only, then
    Every Friday at 15:00; an automation with no engine, then With set to
    Claude Code (an agent CLI engine) and its first Run now."""
    import holdspeak.workbench_memory as memory

    monkeypatch.setattr(memory, "WORKBENCH_DIR", tmp_path / "workbenches")
    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-friday", engine_name="LAN Qwen")
    wb = _make_automation(client, "wb-friday")
    assert client.put(f"/api/workbenches/{wb}", json={"name": "Friday team update"}).status_code == 200
    friday = client.put(f"/api/workbenches/{wb}/when", json={"kind": "schedule", "every": "week", "day": 5, "time": "15:00"})
    assert friday.status_code == 200, friday.text
    shown = _record_window("when-friday", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert shown["schedule"] == "0 15 * * 5" and shown["next_run_at"]

    # No engine: a new automation on a desk whose only engines are other
    # automations' own (no default).
    bare = client.post("/api/workbenches", json={"name": "Meeting follow-ups", "id": "wb-bare"})
    assert bare.status_code == 201, bare.text
    assert client.put("/api/workbenches/wb-bare", json={
        "instruction": DO, "sources": ["note:note-sync", "note:note-hiring"]}).status_code == 200
    none = _record_window("with-none", client, "wb-bare", tmp_path)["/api/workbenches/wb-bare"]["workbench"]
    assert none["assignment_summary"]["chain"] == [] and none["assignment_summary"]["profile_id"] is None

    # Add: the Engines app's own path for a found agent CLI (the face posts
    # connect-cli-engine; its answer is recorded in engines.recorded.json).
    from holdspeak.config import Config
    from holdspeak.intel.cli_engine import CLI_ENGINES_ENV
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService

    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home")
    monkeypatch.setenv(CLI_ENGINES_ENV, "on")  # the engine stays the recorded stub; no CLI runs
    ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition).connect_cli_engine(
        OWNER, {"request_id": "record-add", "profile_id": "agent-claude", "expected_profile_revision": 0,
                "preset": "claude"})
    used = client.put("/api/workbenches/wb-bare/engine", json={"profile_id": "agent-claude"})
    assert used.status_code == 200, used.text
    claude = _record_window("with-claude", client, "wb-bare", tmp_path)["/api/workbenches/wb-bare"]["workbench"]
    assert claude["assignment_summary"]["chain"] == ["Claude Code"]
    assert client.post("/api/workbenches/wb-bare/run", json={}).status_code == 200
    ran = _record_window("with-claude-ran", client, "wb-bare", tmp_path)["/api/workbenches/wb-bare"]["workbench"]
    assert [r["status"] for r in ran["results"]] == ["done"]


# ── A5 "About" (betterment/workbench/RECIPE.md, slice A5) ──────────────────
# The hub half: About takes meetings, notes, drawers, projects and people by
# name, and two relative sets. A set is read when the run starts (Friday's
# run reads the meetings since Monday); a drawer reads as "Notes in <name>";
# a person adds the name only (the People record stays on this device).


def _record_gets(name: str, client: TestClient, paths: list[str], wb: str, tmp_path: Path) -> dict[str, Any]:
    """Other reads a face test replays (the same file rule as _record_window)."""
    answers = {path: client.get(path).json() for path in paths}
    scrubbed = _json.loads(_re.sub(_re.escape(str(tmp_path)), "/tmp/rig", _json.dumps(answers)))
    path = AUTOMATION_HUB / f"{name}.json"
    if _os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(_json.dumps({
            "_source": "The hub's own answers, captured by tests/integration/test_desk_workbenches.py "
                       "(TestClient, isolated database). "
                       "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit it.",
            "workbench_id": wb, "gets": scrubbed}, indent=1, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answers {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    assert _shape(_json.loads(path.read_text())["gets"]) == _shape(scrubbed), f"{path.name}: not the hub's shape"
    return scrubbed


def test_about_reads_sets_drawers_and_people_by_name_and_the_run_reads_them(tmp_path: Path, monkeypatch) -> None:
    """Done when (A5, hub half): About names each pick (This week's meetings,
    Notes in Work, a person); the run reads this week's meeting and not last
    month's, the note, and the person's name; a set or person it does not
    know is refused."""
    import holdspeak.services.automation_runs as automation
    import holdspeak.workbench_memory as memory
    from holdspeak.timestamps import local_now, utc_iso
    from holdspeak.web.routes.primitives.directories import build_directories_router
    from holdspeak.web.routes.primitives.notes import build_notes_router

    monkeypatch.setattr(memory, "WORKBENCH_DIR", tmp_path / "workbenches")
    db, client, prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-about", engine_name="LAN Qwen")
    wb = _make_automation(client, "wb-about")
    assert client.put(f"/api/workbenches/{wb}", json={"name": "Friday team update"}).status_code == 200
    # The People list is the encrypted store's; the rig has none, so its one
    # read (the owner's list of names) answers what a set-up store would.
    monkeypatch.setattr(automation, "_people_names", lambda: {"rel-mira": "Mira Chen"})
    db.directories.upsert(directory_id="dir-work", name="Work")
    db.notes.upsert(note_id="note-roadmap", title="Roadmap review", body_markdown="Q4 scope is frozen.")
    db.directory_memberships.upsert(primitive_id="note:note-roadmap", directory_id="dir-work")
    now = utc_iso(local_now())
    with db._connection() as conn:
        conn.execute("INSERT INTO meetings (id, title, started_at, created_at) VALUES (?,?,?,?)",
                     ("m-week", "Platform sync meeting", now, now))
        conn.execute("INSERT INTO meetings (id, title, started_at, created_at) VALUES (?,?,?,?)",
                     ("m-old", "Old planning", "2020-01-06T10:00:00Z", "2020-01-06T10:00:00Z"))

    for bad in (["meetings:last_year"], ["person:"]):
        refused = client.put(f"/api/workbenches/{wb}", json={"sources": bad})
        assert refused.status_code == 400, (bad, refused.text)
    valid_people_alias = client.put(f"/api/workbenches/{wb}", json={"sources": ["people:rel-mira"]})
    assert valid_people_alias.status_code == 200, valid_people_alias.text
    assert valid_people_alias.json()["workbench"]["sources"] == ["people:rel-mira"]

    # The face's two presses (About, then the "plat" match): no sources, then
    # Platform sync; Run now's result cites it.
    assert client.put(f"/api/workbenches/{wb}", json={"sources": []}).status_code == 200
    none = _record_window("about-none", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert none["sources_shown"] == []
    assert client.put(f"/api/workbenches/{wb}", json={"sources": ["note:note-sync"]}).status_code == 200
    one = _record_window("about-platform", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert [s["label"] for s in one["sources_shown"]] == ["Platform sync"]
    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    assert "The cutover moves to Thursday." in prompts[-1]
    ran = _record_window("about-platform-ran", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert "Platform sync" in ran["results"][0]["text"]

    picked = client.put(f"/api/workbenches/{wb}", json={"sources": [
        "note:note-sync", "meetings:this_week", "zone:dir-work", "person:rel-mira", "person:rel-gone"]})
    assert picked.status_code == 200, picked.text
    shown = _record_window("about-picked", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert [(s["label"], s["kind"], s["missing"]) for s in shown["sources_shown"]] == [
        ("Platform sync", "note", False), ("This week's meetings", "set", False),
        ("Notes in Work", "zone", False), ("Mira Chen", "person", False), ("", "person", True)]
    # An event start's About line reads the thing that happened.
    assert {e["id"]: e["subject"] for e in shown["when_events"]}["github-review-requested"] == (
        "the review request that came in")

    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    prompt = prompts[-1]
    assert "The cutover moves to Thursday." in prompt  # the note
    assert "Platform sync meeting" in prompt and "Old planning" not in prompt  # this week only
    assert "Q4 scope is frozen." in prompt  # the drawer's note
    assert "Person: Mira Chen" in prompt and "rel-gone" not in prompt
    result = client.get(f"/api/workbenches/{wb}").json()["workbench"]["results"][0]
    from holdspeak.db.programs import ProgramStore

    refs = ProgramStore(db).get_step(result["item_id"])["facts"]["prompt"]["refs"]
    assert refs == ["note:note-sync", "meeting:m-week", "zone:dir-work"], refs

    # This week's notes are his notes, never an automation's own results.
    week_notes, _ = automation.expand_sources(db, ["notes:this_week"])
    assert "note:note-sync" in week_notes and not [r for r in week_notes if r.startswith("note:note_result_")]
    assert any(n.id.startswith("note_result_") for n in [db.notes.get(result["note_id"])] if n)

    # A set that holds nothing says so; the engine does not guess.
    assert automation.expand_sources(db, ["notes:this_week"], now=datetime(2001, 1, 3).astimezone())[1] == []
    assert automation.expand_sources(db, ["meetings:this_week"], now=datetime(2030, 1, 9).astimezone()) == (
        [], ["This week's meetings: none yet."])

    # What the picker finds by name: the desk's notes and drawers (the face
    # replays these reads; the palette reads the same lists).
    lists = TestClient(_mount(FastAPI(), db, build_notes_router, build_directories_router))
    _record_gets("about-desk", lists, ["/api/notes", "/api/directories"], wb, tmp_path)


def _mount(app: FastAPI, db: Database, *builders: Any) -> FastAPI:
    from holdspeak.services.primitive_service import PrimitiveService

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, primitive_service=PrimitiveService(db))
    for build in builders:
        app.include_router(build(ctx))
    return app


# ── A7 "Home, New automation, and starters" (betterment/workbench/RECIPE.md) ──
# The hub half: New automation offers the four starters (the old templates
# are hidden, still in code); a press makes one automation with the
# starter's sentence and no agent (nothing is copied); a blank it cannot
# guess is named until he fills it. The DESIGN §6 walk on the hub: Friday
# team update → With Claude Code → Run now → a readable result. The face
# replays these answers (automation.app.test.tsx, "A7").


def test_a_starter_makes_one_automation_and_the_friday_walk_reads_a_result(tmp_path: Path, monkeypatch) -> None:
    import holdspeak.workbench_memory as memory
    from holdspeak.config import Config
    from holdspeak.intel.cli_engine import CLI_ENGINES_ENV
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService
    from holdspeak.workbench_templates import get_template

    import itertools

    monkeypatch.setattr(memory, "WORKBENCH_DIR", tmp_path / "workbenches")
    # Stable ids, so the recorded answers keep their paths from run to run.
    made_ids = itertools.count(1)
    monkeypatch.setattr("holdspeak.services.workbench_service._new_id",
                        lambda prefix: f"{prefix}_a7_{next(made_ids)}")
    db, client, prompts, _ = _instruction_rig(tmp_path, monkeypatch)
    with db._connection() as conn:
        now = datetime.now().astimezone().isoformat()
        conn.execute("INSERT INTO meetings (id, title, started_at, created_at) VALUES (?,?,?,?)",
                     ("m-sync", "Platform sync meeting", now, now))

    start = _record_gets("starters", client, ["/api/workbench-templates", "/api/workbenches"], "", tmp_path)
    starters = start["/api/workbench-templates"]["templates"]
    # PG14: the rig's engine is OpenAI-compatible, so pi can run on it and
    # the Overnight program starter is offered too.
    assert [s["id"] for s in starters] == [
        "friday-team-update", "meeting-follow-ups", "one-on-one-prep", "summarize-a-drawer", "morning-prep",
        "overnight-program"]
    friday = starters[0]
    assert (friday["schedule"], friday["sources"], friday["output_target"], friday["blanks"]) == (
        "0 15 * * 5", ["meetings:this_week", "notes:this_week"], "inbox", {})
    assert start["/api/workbenches"]["workbenches"] == []
    # Retired as starters; still in code.
    assert get_template("todo-agent") is not None and not {"todo-agent", "triage-agent", "morning-brief"} & {
        s["id"] for s in starters}

    recipes_before = len(db.recipes.list())
    made = client.post("/api/workbench-templates/friday-team-update/instantiate", json={})
    assert made.status_code == 201, made.text
    wb = made.json()["workbench"]["id"]
    assert len(db.recipes.list()) == recipes_before  # nothing is copied
    new = _record_window("friday-new", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert (new["name"], new["recipe_id"], new["instruction_from"]) == ("Friday team update", None, "automation")
    assert (new["schedule"], new["schedule_enabled"], new["when_kind"]) == ("0 15 * * 5", False, "schedule")
    assert [s["label"] for s in new["sources_shown"]] == ["This week's meetings", "This week's notes"]
    assert new["blanks"] == {}

    # A blank stays named until he fills it; a second press makes a second one.
    prep = client.post("/api/workbench-templates/one-on-one-prep/instantiate", json={}).json()["workbench"]
    assert prep["blanks"] == {"about": "which people?"} and prep["output_target"] == "inbox"
    filled = client.put(f"/api/workbenches/{prep['id']}", json={"sources": ["note:note-sync"]}).json()["workbench"]
    assert filled["blanks"] == {}
    follow = client.post("/api/workbench-templates/meeting-follow-ups/instantiate", json={}).json()["workbench"]
    assert (follow["output_target"], follow["schedule"], follow["blanks"]) == ("needs_you", None, {"about": "which meeting?"})
    assert len(db.recipes.list()) == recipes_before
    # The old template path still answers for an old caller.
    old = client.post("/api/workbench-templates/todo-agent/instantiate", json={})
    assert old.status_code == 201 and old.json()["workbench"]["recipe_id"]
    for gone in (prep["id"], follow["id"], old.json()["workbench"]["id"]):
        db.workbenches.delete(gone)

    # With: the Engines app's own Add for a found agent CLI, then this one uses it.
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: tmp_path / "home")
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home")
    monkeypatch.setenv(CLI_ENGINES_ENV, "on")  # the engine stays the recorded stub; no CLI runs
    ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition).connect_cli_engine(
        OWNER, {"request_id": "record-add", "profile_id": "agent-claude", "expected_profile_revision": 0,
                "preset": "claude"})
    assert client.put(f"/api/workbenches/{wb}/engine", json={"profile_id": "agent-claude"}).status_code == 200
    claude = _record_window("friday-claude", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    assert claude["assignment_summary"]["chain"] == ["Claude Code"]

    assert client.post(f"/api/workbenches/{wb}/run", json={}).status_code == 200
    assert "Platform sync meeting" in prompts[-1] and "The cutover moves to Thursday." in prompts[-1]
    ran = _record_window("friday-ran", client, wb, tmp_path)[f"/api/workbenches/{wb}"]["workbench"]
    [result] = ran["results"]
    assert result["status"] == "done" and result["text"].startswith("## Weekly update") and result["new"] is True
    rows = _record_gets("home-rows", client, ["/api/workbenches"], wb, tmp_path)["/api/workbenches"]["workbenches"]
    assert [r["name"] for r in rows] == ["Friday team update"]


# ── A9 "Old automations" (betterment/workbench/RECIPE.md, slice A9) ────────
# The hub half: an old TODO automation (the template as instantiated before
# A2) shows its typed tasks and their results; one press (make-one) writes
# its agent's prompt as its Do, and nothing is lost: the tasks, their
# results, the agent and its skills stay. Its next run makes one result.


def test_make_one_refuses_an_automation_with_no_agent_prompt(tmp_path: Path) -> None:
    db = Database(tmp_path / "plain.db")
    client = _client(db)
    db.workbenches.upsert(workbench_id="wb-bare", name="Bare")
    refused = client.post("/api/workbenches/wb-bare/make-one")
    assert refused.status_code == 400 and "no agent prompt" in refused.json()["error"]
    assert client.post("/api/workbenches/wb-missing/make-one").status_code == 404


# ── A6 "Put it in, and where results show up" (betterment/workbench/RECIPE.md,
# slice A6) ───────────────────────────────────────────────────────────────
# The hub half: Put it in takes My Inbox, Needs you or a saved destination; a
# scheduled run on a FRESH desk (no seed, no Inbox) still files its note in an
# Inbox; the "new result" row source names each automation with a NEW result
# until it is opened, and an opened result leaves it everywhere at once.


def _destinations_answer(db: Database) -> dict[str, Any]:
    """The hub's own ``GET /api/channels/destinations`` answer (the route is
    ``channel.destinations`` and nothing else)."""
    from holdspeak import operations
    from holdspeak.services.channel_service import ChannelService
    from holdspeak.web.routes._room_kernel import kernel_fields

    registry = operations.for_runtime(channel_service=lambda: ChannelService(db))
    result, kernel = registry.invoke_receipted(OWNER, "channel.destinations", {})
    return _json.loads(_json.dumps({**result, **kernel_fields(kernel)}, default=str))


def _record_put(name: str, client: TestClient, db: Database, wb: str, tmp_path: Path) -> dict[str, Any]:
    """The window's reads, the destinations list and the new-result rows."""
    answers = {
        f"/api/workbenches/{wb}": client.get(f"/api/workbenches/{wb}").json(),
        f"/api/workbenches/{wb}/memory": client.get(f"/api/workbenches/{wb}/memory").json(),
        "/api/automations/new": client.get("/api/automations/new").json(),
        "/api/channels/destinations": _destinations_answer(db),
    }
    text = _re.sub(_re.escape(str(tmp_path)), "/tmp/rig", _json.dumps(answers))
    # The built-in folder lives in the (isolated) HOME: never a machine path.
    text = _re.sub(_re.escape(_json.dumps(str(Path.home().resolve()))[1:-1]), "/tmp/home", text)
    text = _re.sub(_re.escape(_json.dumps(str(Path.home()))[1:-1]), "/tmp/home", text)
    scrubbed = _json.loads(text)
    path = AUTOMATION_HUB / f"{name}.json"
    if _os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(_json.dumps({
            "_source": "The hub's own answers, captured by tests/integration/test_desk_workbenches.py "
                       "(TestClient, isolated database, the A2 rig's recorded engine replies). "
                       "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit it.",
            "workbench_id": wb, "gets": scrubbed}, indent=1, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answers {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    assert _shape(_json.loads(path.read_text())["gets"]) == _shape(scrubbed), f"{path.name}: not the hub's shape"
    return scrubbed


def test_put_it_in_files_a_fresh_desk_inbox_and_new_results_show_until_opened(tmp_path: Path, monkeypatch) -> None:
    """Done when (A6, hub half): a scheduled run makes the Inbox note (on a
    fresh desk too), the new-result row names the automation, and opening the
    result clears it; Put it in takes Needs you and a saved destination."""
    from types import SimpleNamespace

    import holdspeak.workbench_memory as memory
    from holdspeak.db.channels import BUILTIN_FOLDER_ID
    from holdspeak.workbench_conductor import WorkbenchConductor

    monkeypatch.setattr(memory, "WORKBENCH_DIR", tmp_path / "workbenches")
    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-put", inbox=False)
    assert db.directories.get(INBOX, include_deleted=True) is None  # a fresh desk: no Inbox
    wb = _make_automation(client, "wb-put")
    assert client.put(f"/api/workbenches/{wb}", json={"name": "Friday team update"}).status_code == 200
    assert client.get("/api/automations/new").json() == {"automations": [], "new_count": 0}

    # A scheduled run (the conductor's tick on a controlled clock).
    assert client.put(f"/api/workbenches/{wb}", json={"schedule": "* * * * *", "schedule_enabled": True}).status_code == 200
    clock = {"now": 1_800_000_000.0}
    monkeypatch.setattr("holdspeak.workbench_conductor.time", SimpleNamespace(time=lambda: clock["now"]))
    WorkbenchConductor()._tick_body()
    assert client.put(f"/api/workbenches/{wb}", json={"schedule_enabled": False}).status_code == 200

    inbox = db.directories.get(INBOX)
    assert inbox is not None and inbox.name == "Inbox"  # made for the first result
    [note] = _inbox_notes(db)
    assert note.title.startswith("Friday team update, ")
    new = _record_put("put-new", client, db, wb, tmp_path)
    rows = new["/api/automations/new"]
    assert rows["new_count"] == 1
    assert [(r["workbench_id"], r["name"], r["new_count"]) for r in rows["automations"]] == [
        (wb, "Friday team update", 1)]
    destinations = new["/api/channels/destinations"]["destinations"]
    assert BUILTIN_FOLDER_ID in [d["id"] for d in destinations]

    # Put it in: Needs you, then a saved destination (a folder: he presses Send).
    needs = client.put(f"/api/workbenches/{wb}", json={"output_target": "needs_you"})
    assert needs.status_code == 200 and needs.json()["workbench"]["output_target"] == "needs_you"
    to_folder = client.put(f"/api/workbenches/{wb}", json={"output_target": f"destination:{BUILTIN_FOLDER_ID}"})
    assert to_folder.status_code == 200, to_folder.text
    _record_put("put-folder", client, db, wb, tmp_path)

    # Opening the result reads it: the row goes, and the count with it.
    artifact = new[f"/api/workbenches/{wb}"]["workbench"]["results"][0]["artifact_id"]
    assert client.post(f"/api/workbenches/{wb}/results/{artifact}/open").status_code == 200
    opened = _record_put("put-opened", client, db, wb, tmp_path)
    assert opened["/api/automations/new"] == {"automations": [], "new_count": 0}
    assert [r["new"] for r in opened[f"/api/workbenches/{wb}"]["workbench"]["results"]] == [False]

    # An Inbox he deleted is not brought back: the next note stays on the floor.
    assert client.put(f"/api/workbenches/{wb}", json={"output_target": "inbox"}).status_code == 200
    db.directories.upsert(directory_id=INBOX, name="Inbox", deleted=True)
    ran = client.post(f"/api/workbenches/{wb}/run", json={})
    assert ran.status_code == 200, ran.text
    [delivery] = ran.json()["run"]["deliveries"]
    assert (delivery["outcome"], delivery["filed"]) == ("noted", False)
    assert db.directories.get(INBOX) is None


def test_a_new_result_raises_one_quiet_notice_that_opens_the_automation(tmp_path: Path, monkeypatch) -> None:
    """Betterment daily D8 (decision 2): a run that makes a new result raises
    ONE quiet notice, "<name> has a new result", that opens the automation
    window; Today's NEW line comes from the same result (A6). No notice while
    the automation window is in front, with "Finished work" off, or in quiet
    hours. A rig posts nothing and records why."""
    from datetime import datetime as _dt

    from holdspeak import desk_presence
    from holdspeak.services import heartbeat_service as hb_module
    from holdspeak.services.heartbeat_service import HeartbeatService

    posts: list[tuple[str, str, Any]] = []

    def notifier(title: str, body: str, *, click_url: Any = None) -> bool:
        posts.append((title, body, click_url))
        return True

    monkeypatch.setattr(hb_module, "_notify_default", notifier)
    desk_presence.clear()
    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-told")
    wb = _make_automation(client, "wb-told")
    assert client.put(f"/api/workbenches/{wb}", json={"name": "Friday team update"}).status_code == 200
    heartbeat = HeartbeatService(db)
    hour = _dt.now().hour
    heartbeat.update_settings({"notify": "edge", "quiet_hours": {"start": (hour + 3) % 24, "end": (hour + 5) % 24}})

    def run() -> None:
        ran = client.post(f"/api/workbenches/{wb}/run", json={})
        assert ran.status_code == 200, ran.text

    run()
    assert posts == [("HoldSpeak", "Friday team update has a new result", f"/?open=workbench:{wb}")], posts
    assert client.get("/api/automations/new").json()["new_count"] == 1  # the Today line

    try:  # the automation window in front: he is looking at it
        desk_presence.report(f"pullout:workbench:{wb}", True)
        run()
        assert len(posts) == 1, posts
    finally:
        desk_presence.clear()

    heartbeat.update_settings({"notify_finished": False})
    run()
    assert len(posts) == 1, posts
    heartbeat.update_settings({"notify_finished": True, "quiet_hours": {"start": hour, "end": (hour + 1) % 24}})
    run()
    assert len(posts) == 1, posts  # quiet hours: the line in Today waits for him
    assert client.get("/api/automations/new").json()["new_count"] == 4

    # A rig (HOLDSPEAK_DESKTOP_NOTIFY=0, no notifier) posts nothing and says why.
    monkeypatch.undo()
    monkeypatch.setenv("HOLDSPEAK_DESKTOP_NOTIFY", "0")
    heartbeat.update_settings({"quiet_hours": {"start": (hour + 3) % 24, "end": (hour + 5) % 24}})
    assert HeartbeatService(db).finished_notice(wb, "Friday team update")["outcome"] == "not_posted_in_rig"


def test_a_desk_with_its_own_inbox_drawer_gets_the_note_there(tmp_path: Path, monkeypatch) -> None:
    """A desk whose Inbox is a drawer he made (not the seed's) files there."""
    db, client, _prompts, _ = _instruction_rig(tmp_path, monkeypatch, "wb-own", inbox=False)
    db.directories.upsert(directory_id="dir-mine", name="inbox")
    wb = _make_automation(client, "wb-own")
    ran = client.post(f"/api/workbenches/{wb}/run", json={})
    [delivery] = ran.json()["run"]["deliveries"]
    assert delivery["filed"] is True
    assert db.directories.get(INBOX, include_deleted=True) is None
    with db._connection() as conn:
        filed = conn.execute("SELECT directory_id FROM directory_memberships WHERE primitive_id=?",
                             (f"note:{delivery['note_id']}",)).fetchone()
    assert filed["directory_id"] == "dir-mine"


def test_run_refusals_say_automation_never_workbench(tmp_path: Path) -> None:
    """The A7 follow-up: the words he can see say automation."""
    from holdspeak.web.routes.primitives import workbenches as route

    assert all("workbench" not in words.lower() for words in route._NO_ENGINE_WORDS.values())
    db = Database(tmp_path / "words.db")
    missing = _client(db).get("/api/workbenches/wb-nowhere")
    assert missing.status_code == 404 and missing.json()["error"] == "Unknown automation: wb-nowhere"
