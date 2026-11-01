"""PG-LANG JRN9 to JRN11 on the briefing page: an audit's File the findings
(Secure), its Make a fix program, and a lesson are held items the page reads
and decides, like any other.

The hub half: ``POST /api/reach/packages`` makes the page; ``GET /api/b/<token>``
reads the item in his terms (``brief_words``: the question, each choice with
its consequence); ``POST /api/b/<token>/answer`` decides it through the step's
decide route and the page settles to one line. The answers are stored for the
page's T2 (``web/src/briefing/__fixtures__/reach.audit.json`` and
``reach.lesson.json``; ``HOLDSPEAK_WIRE_WRITE=1`` rewrites them).
"""
from __future__ import annotations

from tests.integration.program_rig import OWNER, Rig
from tests.integration.test_desk_program_audit import REPORT_1, _audit, _report, _tasks
from tests.integration.test_desk_program_lessons import _go_red, _lessons, _program, _red_check
from tests.integration.test_desk_reach import PAGE_FIXTURES, Clock, _fixture, _rig_of


def test_file_and_make_are_held_items_the_page_decides(tmp_path, monkeypatch) -> None:
    clock = Clock()
    rig = Rig(tmp_path)
    pid = _audit(rig, "secure", steps=1)
    _report(rig, monkeypatch, pid, 1, REPORT_1)
    rig, pid, client = _rig_of(rig, pid, tmp_path, monkeypatch, clock)
    items = {row["kind"]: row for row in client.get(f"/api/programs/{pid}").json()["your_turn_items"]}
    refs = [f"program:{pid}:{items[kind]['id']}" for kind in ("audit_file", "fix_program")]
    made = client.post("/api/reach/packages", json={"refs": [refs[0]]})
    assert made.status_code == 201, made.text
    token = made.json()["token"]
    made_two = client.post("/api/reach/packages", json={"refs": [refs[1]]})
    assert made_two.status_code == 201, made_two.text
    token_two = made_two.json()["token"]
    opened = client.get(f"/api/b/{token}").json()
    [first] = opened["items"]
    [second] = client.get(f"/api/b/{token_two}").json()["items"]
    assert first["question"] == "File the findings as Door tasks?" and first["kind_words"] == "Audit findings"
    assert first["head"] == "Desk audit" and first["place"].startswith("The program")
    assert first["doing"].startswith("The program: ") and "Step" not in first["doing"]
    assert [(row["id"], row["label"]) for row in first["choices"]] == [("file", "File"), ("skip", "Skip")]
    assert second["question"] == "Make a fix program from the MUST findings?"
    assert [(row["id"], row["label"]) for row in second["choices"]] == [("make", "Make"), ("skip", "Skip")]
    filed = client.post(f"/api/b/{token}/answer", json={"ref": refs[0], "choice": "file"})
    assert filed.status_code == 200, filed.text
    assert filed.json()["item"]["state"] == "decided" and len(_tasks(rig)) == 3
    assert filed.json()["item"]["outcome"]["words"].startswith("File · ")
    fixed = client.post(f"/api/b/{token_two}/answer", json={"ref": refs[1], "choice": "make"})
    assert fixed.status_code == 200, fixed.text
    assert rig.program(pid)["fix_program_id"]
    again = client.post(f"/api/b/{token_two}/answer", json={"ref": refs[1], "choice": "skip"})
    assert again.status_code == 409 and again.json()["code"] == "answered_already"
    after = client.get(f"/api/b/{token}").json()
    assert [row["state"] for row in after["items"]] == ["decided"]
    _fixture(PAGE_FIXTURES / "reach.audit.json", {
        "made": made.json(), "open": opened, "filed": filed.json(), "made_fix": fixed.json(), "after": after,
    }, tmp_path, token)


def test_a_lesson_is_a_held_item_the_page_decides(tmp_path, monkeypatch) -> None:
    clock = Clock()
    rig = Rig(tmp_path)
    pid = _program(rig, _red_check(tmp_path))
    _go_red(rig, pid, 1)
    _go_red(rig, pid, 2)
    [row] = _lessons(rig, pid)
    rig, pid, client = _rig_of(rig, pid, tmp_path, monkeypatch, clock)
    ref = f"program:{pid}:{row['id']}"
    made = client.post("/api/reach/packages", json={"refs": [ref]})
    assert made.status_code == 201, made.text
    token = made.json()["token"]
    opened = client.get(f"/api/b/{token}").json()
    shown = opened["items"][0]
    assert shown["question"] == "Keep this lesson, and where?" and shown["kind_words"] == "Lesson"
    assert shown["head"] == "The words wave"
    assert shown["doing"].startswith("The program: Running · ") and "Step" not in shown["doing"]
    assert [choice["label"] for choice in shown["choices"]] == ["Keep for this program", "Keep for HoldSpeak", "Skip"]
    kept = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "keep_program"})
    assert kept.status_code == 200, kept.text
    assert kept.json()["item"]["state"] == "decided" and _lessons(rig, pid) == []
    assert any(req["text"] == row["requirement"] for req in rig.service.requirements(pid))
    _fixture(PAGE_FIXTURES / "reach.lesson.json", {"made": made.json(), "open": opened, "kept": kept.json()},
             tmp_path, token)
