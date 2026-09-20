"""HS-201-08 roadmap API coverage for the null next-story envelope."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.web.routes.roadmaps as roadmaps
from holdspeak.web.context import WebContext


def _write_project(
    root: Path,
    slug: str,
    *,
    phase: int,
    phase_slug: str,
    story_id: str,
    status: str,
    closed: bool = False,
) -> None:
    project_root = root / "pm" / "roadmap" / slug
    phase_root = project_root / f"phase-{phase}-{phase_slug}"
    phase_root.mkdir(parents=True)
    (project_root / "README.md").write_text(
        f"# {slug}\n\n**Current phase:** [phase-{phase}-{phase_slug}]"
        f"(phase-{phase}-{phase_slug}/current-phase-status.md)\n",
        encoding="utf-8",
    )
    (phase_root / "current-phase-status.md").write_text("# Status\n", encoding="utf-8")
    (phase_root / "story-01-example.md").write_text(
        f"# {story_id}\n\n**Status:** {status}\n", encoding="utf-8"
    )
    if closed:
        (phase_root / "final-summary.md").write_text("# Closed\n", encoding="utf-8")


def _run_for_payload(
    slug: str,
    payload: str,
    *,
    next_exit: int = 0,
) -> tuple[Callable[..., tuple[int, str]], list[tuple[Path, tuple[str, ...]]]]:
    calls: list[tuple[Path, tuple[str, ...]]] = []

    def fake_run(repo_root: Path, *args: str) -> tuple[int, str]:
        calls.append((repo_root, args))
        if args == ("check", slug):
            return 0, "dw check: ok"
        if args == ("next", slug, "--json"):
            return next_exit, payload
        raise AssertionError(args)

    return fake_run, calls


@pytest.mark.parametrize(
    ("name", "payload", "expected", "next_exit"),
    [
        ("explicit-story-id", '{"story_id": "HS-201-08"}', "HS-201-08", 0),
        ("explicit-id", '{"id": "HS-201-08"}', "HS-201-08", 0),
        ("nested-story-id", '{"next_story": {"story_id": "HS-201-08"}}', "HS-201-08", 0),
        ("absent-next-story", "{}", None, 2),
        ("explicit-null-next-story", '{"next_story": null}', None, 2),
    ],
)
def test_project_reads_dw_next_json_variants_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    payload: str,
    expected: str | None,
    next_exit: int,
) -> None:
    _write_project(
        tmp_path,
        name,
        phase=1,
        phase_slug="active",
        story_id="HS-201-08",
        status="ready",
    )
    fake_run, calls = _run_for_payload(name, payload, next_exit=next_exit)
    monkeypatch.setattr(roadmaps, "_run", fake_run)

    result = roadmaps._project(tmp_path, name, include_phases=False)

    assert result is not None
    assert result["nextStoryId"] == expected
    assert calls == [
        (tmp_path, ("check", name)),
        (tmp_path, ("next", name, "--json")),
    ]


def test_roadmaps_list_keeps_active_project_when_completed_project_has_null_next_story(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_project(
        tmp_path,
        "active",
        phase=1,
        phase_slug="active",
        story_id="HS-201-08",
        status="ready",
    )
    _write_project(
        tmp_path,
        "completed",
        phase=1,
        phase_slug="closed",
        story_id="HP-1-01",
        status="done",
        closed=True,
    )

    calls: list[tuple[Path, tuple[str, ...]]] = []

    def fake_run(repo_root: Path, *args: str) -> tuple[int, str]:
        calls.append((repo_root, args))
        if args[0] == "check":
            return 0, "dw check: ok"
        if args == ("next", "active", "--json"):
            return 0, '{"story_id": "HS-201-08"}'
        if args == ("next", "completed", "--json"):
            return 2, '{"next_story": null}'
        raise AssertionError(args)

    monkeypatch.setattr(roadmaps, "_run", fake_run)
    app = FastAPI()
    app.include_router(
        roadmaps.build_roadmaps_router(
            WebContext(get_state=lambda: {}),
            repo_root=tmp_path,
        )
    )

    response = TestClient(app, raise_server_exceptions=False).get("/api/roadmaps")

    assert response.status_code == 200, response.text
    projects = {project["slug"]: project for project in response.json()["roadmaps"]}
    assert projects["active"]["nextStoryId"] == "HS-201-08"
    assert projects["completed"]["nextStoryId"] is None
    assert calls.count((tmp_path, ("next", "active", "--json"))) == 1
    assert calls.count((tmp_path, ("next", "completed", "--json"))) == 1
