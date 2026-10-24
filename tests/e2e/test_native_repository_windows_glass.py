"""P01/P02/P10 first resource wave on a real, isolated Desk and git source.

This rig checks browser ownership: a pointer opens another view, each view
keeps its own location and inspection, a refusal stays at its target, and
closing one frame returns to the exact surviving frame. The Components case
uses its local specimen only; it is not another production repository.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="repository glass needs Playwright")
pytestmark = [pytest.mark.e2e]

TOKEN = "native-repository-glass"
SHOTS = evidence_dir("native-desktop-wave1")
SIZES = {1440: 900, 393: 852}


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _isolated_boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    # DeliveryRegistry's default path is frozen at module import, before
    # glass_infra._boot changes HOME. Pin it per test so a later sweep worker
    # never reads a registry pointing at this test's removed temp git root.
    import holdspeak.delivery.registry as registry_module

    monkeypatch.setattr(registry_module, "DEFAULT_REGISTRY_PATH", tmp_path / "home" / ".holdspeak" / "delivery_sources.json")
    return _boot(tmp_path, monkeypatch, token=TOKEN)


def _source(tmp_path: Path, *, folder: str = "native-glass-repo", alpha: str = "Alpha source on this desk.\n") -> Path:
    root = tmp_path / folder
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "src" / "alpha.txt").write_text(alpha, encoding="utf-8")
    (root / "docs" / "guide.md").write_text("# Guide for the second view\n", encoding="utf-8")
    (root / "README.md").write_text("Native glass source\n", encoding="utf-8")
    _git(root, "init")
    _git(root, "config", "user.email", "glass@example.test")
    _git(root, "config", "user.name", "Glass")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture")
    return root


def _start(page: Any, base: str, root: Path) -> str:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    registered = _api(page, "POST", "/api/repositories", {"path": str(root), "label": "Native glass"}, token=TOKEN)
    resource_id = registered["repository"]["id"]
    # The one-shot opener is the public Desk route; it crosses the same
    # openPullout registry path as the object opener, after collection refresh.
    page.goto(f"{base}/?token={TOKEN}&open=repository:{resource_id}", wait_until="load")
    _normal_chair(page)
    page.locator(f'[id="repository:{resource_id}"] .repo-browser').wait_for()
    return resource_id


def _open_row(view: Any, path: str) -> None:
    row = view.locator(f'.repo-browser tr.desk-sortable-table-row[aria-label="{path}"]')
    row.wait_for(state="visible")
    row.click()


def _phone_swipe_right(page: Any) -> None:
    """One real touch drag in the window body, using the desk's phone ring."""
    cdp = page.context.new_cdp_session(page)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 60, "y": 430, "id": 1}]})
    for step in range(1, 7):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove",
                                              "touchPoints": [{"x": 60 + 270 * step / 6, "y": 430 + step, "id": 1}]})
        page.wait_for_timeout(16)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    cdp.detach()


def _assert_narrow_targets(page: Any, view: Any, frame_id: str) -> None:
    """Run the desk sweep's canonical nine-point hit probe on this frame."""
    from .test_desk_sweep import TARGET_JS

    draft = view.get_by_role("textbox", name="Commit message")
    draft.fill("Probe only")
    try:
        assert view.get_by_role("button", name="Commit", exact=True).is_enabled()
        faults = page.evaluate(TARGET_JS, f'[id="{frame_id}"]')
        assert not faults, faults
    finally:
        draft.fill("")


@pytest.mark.parametrize("width", [1440, 393])
def test_two_views_keep_location_inspection_and_refusal_when_one_closes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import expect, sync_playwright

    root = _source(tmp_path)
    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": SIZES[width]},
                                    has_touch=width == 393, reduced_motion="reduce")
            page.set_default_timeout(25_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            try:
                resource_id = _start(page, base, root)
                default = page.locator(f'[id="repository:{resource_id}"]')
                if width == 393:
                    row_height = default.locator('tr[aria-label="src"]').evaluate(
                        "row => row.getBoundingClientRect().height")
                    assert row_height >= 43.5, row_height
                _open_row(default, "src")
                expect(default.get_by_role("button", name="src", exact=True)).to_be_disabled()
                _open_row(default, "src/alpha.txt")
                expect(default.get_by_test_id("repo-file-content")).to_contain_text("Alpha source")

                # The explicit verb creates a second physical frame of the
                # same registered source. It starts at this captured location.
                default.get_by_role("button", name="New window", exact=True).click()
                sibling = page.locator('[id^="repository:view:"]')
                expect(sibling).to_have_count(1)
                sibling_id = sibling.get_attribute("id")
                assert sibling_id and sibling_id != f"repository:{resource_id}"
                if width == 1440:
                    first_box, second_box = default.bounding_box(), sibling.bounding_box()
                    assert first_box and second_box
                    assert (abs(first_box["x"] - second_box["x"]) >= 24
                            or abs(first_box["y"] - second_box["y"]) >= 24), (first_box, second_box)
                assert sibling.get_by_role("button", name="src", exact=True).is_disabled()
                sibling.locator('.repo-breadcrumb-path button').first.click()
                _open_row(sibling, "docs")
                expect(sibling.get_by_role("button", name="docs", exact=True)).to_be_disabled()
                if width == 393:
                    _assert_narrow_targets(page, sibling, sibling_id)
                assert default.get_by_role("button", name="src", exact=True).is_disabled()
                expect(default.get_by_test_id("repo-file-content")).to_contain_text("Alpha source")

                # One named browser-boundary refusal. It never calls a real
                # provider writer and never changes the other view's work.
                def refuse_file(route: Any) -> None:
                    route.fulfill(status=409, content_type="application/json",
                                  body=json.dumps({"error": "file is not readable text"}))

                pattern = f"**/api/repositories/{resource_id}/file/docs/guide.md"
                page.route(pattern, refuse_file, times=1)
                _open_row(sibling, "docs/guide.md")
                expect(sibling).to_contain_text("READ REFUSED · docs/guide.md")
                assert sibling.get_by_role("button", name="docs", exact=True).is_disabled()
                assert default.get_by_role("button", name="src", exact=True).is_disabled()
                sibling.get_by_role("button", name="Retry", exact=True).click()
                expect(sibling.get_by_test_id("repo-file-content")).to_contain_text("Guide for the second view")

                # Back/Forward are local to the instance and restore its
                # inspected file without resetting the first view.
                sibling.get_by_role("button", name="Back", exact=True).click()
                expect(sibling.get_by_role("button", name="root", exact=True)).to_be_disabled()
                sibling.get_by_role("button", name="Forward", exact=True).click()
                expect(sibling.get_by_test_id("repo-file-content")).to_contain_text("Guide for the second view")

                if width == 393:
                    # Real rendered hit bands in the active narrow frame.
                    # Include file navigation, retry/return and row targets.
                    undersized = sibling.evaluate("""win => [...win.querySelectorAll('.repo-browser button, .repo-browser tr[aria-label]')]
                      .filter(el => { const r=el.getBoundingClientRect(), s=getComputedStyle(el);
                        return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; })
                      .filter(el => el.getBoundingClientRect().height < 43.5)
                      .map(el => ({name: el.getAttribute('aria-label') || el.textContent.trim(),
                                   height: Math.round(el.getBoundingClientRect().height)}))""")
                    assert not undersized, undersized
                    _assert_narrow_targets(page, sibling, sibling_id)

                    # The existing touch ring brings the covered frame back
                    # with one swipe; the public window menu returns to docs.
                    _phone_swipe_right(page)
                    expect(default).to_have_class(re.compile(r"\bis-front\b"))
                    expect(default.get_by_test_id("repo-file-content")).to_contain_text("Alpha source")
                    _settle(page)
                    page.screenshot(path=str(SHOTS / "two-views-393-return.png"))
                    default.locator('.desk-pullout-head').click(button="right")
                    menu = page.locator('.desk-head-menu')
                    menu.wait_for(state="visible")
                    assert "Native glass · /src" in (menu.get_attribute("aria-label") or "")
                    menu.get_by_role("menuitem", name=re.compile(r"^To back")).click()
                    expect(sibling).to_have_class(re.compile(r"\bis-front\b"))
                    expect(sibling.get_by_test_id("repo-file-content")).to_contain_text("Guide for the second view")
                    sibling.locator('.desk-pullout-head').click(button="right")
                    menu = page.locator('.desk-head-menu')
                    menu.wait_for(state="visible")
                    assert "Native glass · /docs" in (menu.get_attribute("aria-label") or "")
                    page.keyboard.press("Escape")

                _settle(page)
                page.screenshot(path=str(SHOTS / f"two-views-{width}.png"))
                sibling.locator('.desk-gadget-close').click()
                expect(page.locator(f'[id="{sibling_id}"]')).to_have_count(0)
                expect(default).to_have_count(1)
                expect(default.get_by_test_id("repo-file-content")).to_contain_text("Alpha source")
                assert default.get_by_role("button", name="src", exact=True).is_disabled()
                # Ordinary Open raises the default instance. It cannot clone
                # the explicit sibling or reset the retained inspection.
                page.locator("[aria-controls=desk-tool-shelf]").click()
                page.locator("[aria-controls=desk-palette-listbox]").fill("Native glass")
                page.locator(f'[id="desk-palette-option-repository:{resource_id}"]').click()
                expect(page.locator('.desk-repo-window')).to_have_count(1)
                expect(default.get_by_test_id("repo-file-content")).to_contain_text("Alpha source")
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.stop()


def test_hub_retargets_one_view_without_carrying_old_resource_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from urllib.parse import quote
    from playwright.sync_api import expect, sync_playwright

    first_root = _source(tmp_path)
    second_root = _source(tmp_path, folder="second-glass-repo", alpha="Second source only.\n")
    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            page.set_default_timeout(25_000)
            try:
                first_id = _start(page, base, first_root)
                second_id = _api(page, "POST", "/api/repositories",
                                 {"path": str(second_root), "label": "Second glass"}, token=TOKEN)["repository"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                default = page.locator(f'[id="repository:{first_id}"]')
                default.locator(".repo-browser").wait_for()
                _open_row(default, "src")
                _open_row(default, "src/alpha.txt")
                expect(default.get_by_test_id("repo-file-content")).to_contain_text("Alpha source")
                default.get_by_role("button", name="New window", exact=True).click()
                sibling = page.locator('[id^="repository:view:"]')
                expect(sibling).to_have_count(1)
                sibling_id = sibling.get_attribute("id")
                assert sibling_id
                _open_row(sibling, "src/alpha.txt")
                expect(sibling.get_by_test_id("repo-file-content")).to_contain_text("Alpha source")

                # The hub may reopen this one existing instance on another
                # resource. Its object_ref is the actual registered source ID.
                _api(page, "POST", f"/api/desk/windows/{quote(sibling_id, safe='')}/open",
                     {"object_ref": second_id}, token=TOKEN)
                expect(sibling.locator('tr[aria-label="src/alpha.txt"]')).to_be_visible()
                sibling.locator('tr[aria-label="src/alpha.txt"]').click()
                expect(sibling.get_by_test_id("repo-file-content")).to_contain_text("Second source only")
                assert "Alpha source" not in sibling.inner_text()
                expect(default.get_by_test_id("repo-file-content")).to_contain_text("Alpha source")
            finally:
                browser.close()
    finally:
        server.stop()


def test_late_folder_read_cannot_replace_newer_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from playwright.sync_api import expect, sync_playwright

    root = _source(tmp_path)
    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            page.set_default_timeout(25_000)
            try:
                resource_id = _start(page, base, root)
                view = page.locator(f'[id="repository:{resource_id}"]')

                def late_docs(route: Any) -> None:
                    # The browser timer activates src while this one named
                    # docs read is held. A late response must lose ownership.
                    time.sleep(0.45)
                    route.fulfill(status=200, content_type="application/json",
                                  body=json.dumps({"files": [{"name": "stale.md", "path": "docs/stale.md", "type": "file"}]}))

                page.route(f"**/api/repositories/{resource_id}/tree?path=docs", late_docs, times=1)
                with page.expect_response(lambda response: response.url.endswith("/tree?path=docs")):
                    scheduled = page.evaluate("""() => {
                      const rows = document.querySelector('[id^="repository:"] .repo-browser');
                      const docs = rows?.querySelector('tr[aria-label="docs"]');
                      const src = rows?.querySelector('tr[aria-label="src"]');
                      if (!docs || !src) return false;
                      docs.click();
                      setTimeout(() => src.click(), 75);
                      return true;
                    }""")
                assert scheduled
                expect(view.get_by_role("button", name="src", exact=True)).to_be_disabled()
                expect(view.locator('tr[aria-label="src/alpha.txt"]')).to_have_count(1)
                expect(view.locator('tr[aria-label="docs/stale.md"]')).to_have_count(0)
            finally:
                browser.close()
    finally:
        server.stop()


def test_deleted_folder_is_not_empty_and_has_a_return_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from playwright.sync_api import expect, sync_playwright

    root = _source(tmp_path)
    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            page.set_default_timeout(25_000)
            try:
                resource_id = _start(page, base, root)
                view = page.locator(f'[id="repository:{resource_id}"]')
                expect(view.locator('tr[aria-label="docs"]')).to_be_visible()
                # A real registered-root read sees this folder disappear
                # between listing and navigation; no browser route is mocked.
                (root / "docs" / "guide.md").unlink()
                (root / "docs").rmdir()
                _open_row(view, "docs")
                expect(view).to_contain_text("NOT FOUND · docs")
                assert "Folder empty" not in view.inner_text()
                expect(view.get_by_role("button", name="Retry", exact=True)).to_be_visible()
                back = view.get_by_role("button", name="Back", exact=True)
                expect(back).to_be_enabled()
                back.click()
                expect(view.locator('tr[aria-label="src"]')).to_be_visible()
                expect(view).not_to_contain_text("NOT FOUND · docs")
            finally:
                browser.close()
    finally:
        server.stop()


@pytest.mark.parametrize("width", [1440, 393])
def test_components_resource_specimen_uses_local_browser_seam(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": SIZES[width]}, reduced_motion="reduce")
            page.set_default_timeout(25_000)
            repository_requests: list[str] = []
            page.on("request", lambda request: repository_requests.append(request.url)
                    if "/api/repositories" in request.url else None)
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _normal_chair(page)
                page.goto(f"{base}/design/components?token={TOKEN}", wait_until="load")
                page.get_by_test_id("design-reference").wait_for(state="visible")
                direct = page.get_by_role("button", name="Resources", exact=True)
                if direct.count():
                    direct.click()
                else:
                    page.get_by_role("button", name=re.compile(r"^Patterns:")).click()
                    page.locator("[role^='menuitem']").filter(has_text="Resources").first.click()
                specimen = page.get_by_test_id("reference-resource")
                expect(specimen.locator(".repo-browser")).to_be_visible()
                expect(page.locator('[aria-label="LOCAL SPECIMEN"]')).to_be_visible()
                expect(specimen.locator('tr[aria-label="README.md"]')).to_be_visible()
                specimen.locator('tr[aria-label="README.md"]').click()
                expect(specimen.get_by_test_id("repo-file-content")).to_contain_text("registered repository")

                state = page.get_by_role("combobox", name="Example state")
                state.select_option("failed")
                expect(specimen).to_contain_text("READ REFUSED · src")
                expect(specimen.get_by_role("button", name="Retry", exact=True)).to_be_visible()
                state.select_option("empty")
                expect(specimen).to_contain_text("Folder empty")
                state.select_option("resumed")
                expect(specimen.get_by_test_id("repo-file-content")).to_contain_text("registered repository")
                _settle(page)
                page.screenshot(path=str(SHOTS / f"components-resources-{width}.png"))
                # The fixture exercises the production composition/controller,
                # with local data. It must not become another repository app.
                assert page.locator(".desk-repo-window").count() == 0
                assert not [url for url in repository_requests if "/tree" in url or "/file/" in url], repository_requests
            finally:
                browser.close()
    finally:
        server.stop()
