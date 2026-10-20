"""The Project Door's real HTTP partial link failure and Retry face."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="the Door Retry proof needs Playwright")

from tests._evidence import evidence_dir

from .door_rig import (
    _GH_AUTH_CONNECTED,
    _GH_PR_SNAPSHOT,
    _GH_REPO_LIST,
    _GH_RUN_LIST,
    _make_gh_runner,
    _open_door,
    _write_gh_fixture,
)
from .glass_infra import _boot, _ensure_build


TOKEN = "project-door-retry"
SIZES = ((1440, 900), (393, 852))
SHOTS = evidence_dir("project-door-retry")


def _found_shot(page: Any, path: Path) -> None:
    door = page.locator("[data-testid=door-root]")
    door.screenshot(path=str(path.with_name(path.stem + "-door.png")))
    page.get_by_test_id("door-found").scroll_into_view_if_needed()
    page.get_by_test_id("door-found").screenshot(path=str(path))
    assert path.exists() and path.stat().st_size > 2_000, f"missing or tiny Door shot: {path}"


@pytest.mark.e2e
@pytest.mark.parametrize(("width", "height"), SIZES)
def test_project_door_real_http_partial_failure_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    """A failed note leaf stays selected, then Retry links it once in the Room."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.runtime import composition
    from holdspeak.services import project_door_service as door_module
    from holdspeak.services.primitive_service import PrimitiveService
    from tests.e2e.glass_infra import _api

    fixture = tmp_path / "gh-fixture.json"
    _write_gh_fixture(
        fixture,
        auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT, "returncode": 0},
        run_list={"stdout": _GH_RUN_LIST, "returncode": 0},
    )

    server, base = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_make_gh_runner(fixture))
    try:
        from holdspeak.db import get_database

        db = get_database()
        owner = Principal(PrincipalKind.OWNER, TOKEN)
        started = datetime.now().replace(microsecond=0) - timedelta(hours=2)
        db.meetings.save_meeting(MeetingState(
            id="m-browser-retry",
            started_at=started,
            ended_at=started + timedelta(minutes=30),
            title="Payments migration review",
            segments=[TranscriptSegment(
                text="Payments migration is ready for the next cutover.",
                speaker="Mira Okafor",
                start_time=1.0,
                end_time=4.0,
            )],
            intel=IntelSnapshot(timestamp=1.0, topics=["payments"], summary="Cutover review."),
            intel_status="completed",
        ))
        note = PrimitiveService(db).create_note(
            owner, title="Payments migration risks", body_markdown="Review payments cutover risk.",
        )
        note_ref = f"note:{note['id']}"
        door = composition.current().project_door_service
        project_service = door._project_service
        real_add_resource = project_service.add_resource
        failed_once = False

        def fail_note_once(principal: Any, project_id: str, resource_ref: str, *args: Any, **kwargs: Any) -> Any:
            nonlocal failed_once
            if resource_ref == note_ref and not failed_once:
                failed_once = True
                raise door_module.ServiceError("note_store_unavailable", "Notes store is read-only")
            return real_add_resource(principal, project_id, resource_ref, *args, **kwargs)

        monkeypatch.setattr(project_service, "add_resource", fail_note_once)

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(
                viewport={"width": width, "height": height},
                reduced_motion="reduce",
                has_touch=width < 720,
            )
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _open_door(page, base)
            page.get_by_test_id("door-root").wait_for(timeout=30_000)

            page.get_by_test_id("door-outcome-input").fill("Payments migration")
            page.get_by_test_id("door-source-paste-input").fill("github.com/acme/app")
            page.get_by_test_id("door-source-check").click()
            page.get_by_test_id("door-found").wait_for(timeout=30_000)
            assert "Payments migration review" in page.get_by_test_id("door-found").inner_text()
            assert "Payments migration risks" in page.get_by_test_id("door-found").inner_text()

            with page.expect_response(
                lambda response: response.url.endswith("/api/projects/door")
                and response.request.method == "POST",
                timeout=30_000,
            ) as create_response:
                page.get_by_test_id("door-create").click()
            created = create_response.value.json()
            project_id = created["projectId"]
            error = page.get_by_test_id(f"door-found-error-{note['id']}")
            error.wait_for(timeout=30_000)
            assert error.inner_text() == "Notes store is read-only"
            retry = page.get_by_test_id(f"door-found-retry-{note['id']}")
            assert retry.is_visible()
            SHOTS.mkdir(parents=True, exist_ok=True)
            _found_shot(page, SHOTS / f"failed-retry-{width}.png")

            with page.expect_response(
                lambda response: response.url.endswith("/api/projects/door")
                and response.request.method == "POST",
                timeout=30_000,
            ) as retry_response:
                retry.click()
            assert retry_response.value.json()["found_links"] == [
                {"kind": "note", "id": note["id"], "state": "linked", "error": None},
            ]
            page.locator("#surface-project-memory").wait_for(timeout=30_000)
            resources = _api(page, "GET", f"/api/projects/{project_id}/resources", token=TOKEN)
            refs = [str(row["resource_ref"]) for row in resources["resources"]]
            assert refs.count("meeting:m-browser-retry") == 1, refs
            assert refs.count(note_ref) == 1, refs
            assert failed_once is True
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
