"""The roadmaps read on a desk refresh is fast, and it follows the disk.

The desk read `GET /api/roadmaps` ran `dw check` and `dw next` for every project
and parsed every story on every refresh (1.2-2.8 s on this repository). The read
is now kept until a file of the project changes. This fence runs the real `dw`
on a seeded roadmap tree: a warm read stays inside the budget, and a change on
disk shows in the next read.
"""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.web.routes.roadmaps as roadmaps
from holdspeak.web.context import WebContext

REPO = Path(__file__).resolve().parents[2]
BUDGET_MS = 200.0
PROJECTS = ("alpha", "beta", "gamma", "delta")
PHASES = 12
STORIES = 6


def _story(path: Path, story_id: str, status: str) -> None:
    path.write_text(
        f"# {story_id} — Story\n\n- **Project:** x\n- **Status:** {status}\n", encoding="utf-8"
    )


def _seed(root: Path) -> None:
    shutil.copytree(REPO / ".githooks", root / ".githooks", ignore=shutil.ignore_patterns("_parked"))
    for slug in PROJECTS:
        project = root / "pm" / "roadmap" / slug
        project.mkdir(parents=True)
        (project / "README.md").write_text(
            f"# {slug.title()}\n\n**Current phase:** [phase-{PHASES}-last]"
            f"(phase-{PHASES}-last/current-phase-status.md)\n",
            encoding="utf-8",
        )
        for number in range(1, PHASES + 1):
            name = f"phase-{number}-last" if number == PHASES else f"phase-{number}-p{number}"
            phase = project / name
            phase.mkdir()
            (phase / "current-phase-status.md").write_text(f"# Phase {number}\n", encoding="utf-8")
            for story in range(1, STORIES + 1):
                status = "ready" if number == PHASES else "done"
                _story(phase / f"story-{story:02d}-s.md", f"XX-{number}-{story:02d}", status)


def _client(root: Path) -> TestClient:
    app = FastAPI()
    app.include_router(roadmaps.build_roadmaps_router(WebContext(get_state=lambda: {}), repo_root=root))
    return TestClient(app)


def _list(client: TestClient) -> tuple[float, dict[str, dict]]:
    started = time.perf_counter()
    response = client.get("/api/roadmaps")
    elapsed = (time.perf_counter() - started) * 1000
    assert response.status_code == 200, response.text
    return elapsed, {item["slug"]: item for item in response.json()["roadmaps"]}


def test_a_warm_roadmaps_read_is_inside_the_budget(tmp_path: Path) -> None:
    _seed(tmp_path)
    client = _client(tmp_path)
    cold, first = _list(client)
    assert sorted(first) == sorted(PROJECTS)
    warm = min(_list(client)[0] for _ in range(3))
    assert warm < BUDGET_MS, f"warm roadmaps read {warm:.0f} ms (cold {cold:.0f} ms); budget {BUDGET_MS:.0f} ms"


def test_a_change_on_disk_shows_in_the_next_read(tmp_path: Path) -> None:
    _seed(tmp_path)
    client = _client(tmp_path)
    _, before = _list(client)
    assert before["alpha"]["storiesDone"] == 0
    assert before["alpha"]["storiesTotal"] == STORIES

    phase = tmp_path / "pm" / "roadmap" / "alpha" / f"phase-{PHASES}-last"
    story = phase / "story-01-s.md"
    _story(story, f"XX-{PHASES}-01", "done")
    # Same size, so only the mtime tells the change: make it a later one.
    later = story.stat().st_mtime_ns + 2_000_000_000
    os.utime(story, ns=(later, later))
    _, after_edit = _list(client)
    assert after_edit["alpha"]["storiesDone"] == 1

    _story(phase / f"story-{STORIES + 1:02d}-new.md", f"XX-{PHASES}-{STORIES + 1:02d}", "ready")
    _, after_add = _list(client)
    assert after_add["alpha"]["storiesTotal"] == STORIES + 1

    detail = client.get("/api/roadmaps/alpha").json()
    last = next(p for p in detail["phases"] if p["number"] == PHASES)
    assert [s["status"] for s in last["stories"]].count("done") == 1
    assert len(last["stories"]) == STORIES + 1

    # A `dw check` finding: evidence for a story that is not done. Health
    # follows the edit.
    assert after_add["alpha"]["health"] == "green", after_add["alpha"]
    (phase / "evidence-story-02.md").write_text("# Evidence\n", encoding="utf-8")
    _, after_check = _list(client)
    assert after_check["alpha"]["health"] != "green"
    assert any("not done" in issue for issue in after_check["alpha"]["issues"]), after_check["alpha"]
    assert after_check["beta"]["health"] == "green"
