"""Independent terminal views against real shells on a private tmux socket.

The browser uses the production discovery, grant, command, stream and Desk
window routes. No agent CLI, provider, microphone or owner tmux is involved.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from urllib.parse import quote
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api")
pytestmark = [pytest.mark.e2e, pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux is required")]
TOKEN = "terminal-workspace-glass"
SHOTS = evidence_dir("terminal-flow")


def _tmux(*args: str) -> str:
    result = subprocess.run(["tmux", *args], check=True, capture_output=True, text=True, timeout=8)
    return result.stdout.strip()


def _capture(pane: str) -> str:
    return _tmux("capture-pane", "-p", "-t", pane, "-S", "-100")


def _eventually(predicate: Any, *, seconds: float = 12) -> Any:
    until = time.monotonic() + seconds
    last = None
    while time.monotonic() < until:
        last = predicate()
        if last:
            return last
        time.sleep(0.1)
    raise AssertionError(f"Terminal observation did not arrive: {last!r}")


def _open(page: Any, descriptor: dict[str, Any]) -> Any:
    page.get_by_test_id(f"terminal-open-{descriptor['id']}").click()
    frame = page.locator(f'[id="terminal:{descriptor["id"]}"]')
    frame.wait_for(state="visible")
    return frame


def _inventory(page: Any, base: str) -> Any:
    # Raising is a presentation act through the existing shared OS contract.
    _api(page, "POST", "/api/desk/windows/surface-terminals/open", token=TOKEN)
    frame = page.locator('[id="surface-terminals"]')
    frame.wait_for(state="visible")
    return frame


def _tile(inventory: Any, page: Any) -> None:
    tile = inventory.get_by_test_id("terminal-tile")
    if tile.is_visible():
        tile.click()
    else:
        inventory.get_by_role("button", name="More", exact=True).click()
        page.get_by_role("menuitem", name="Tile terminals", exact=True).click()


def _type(frame: Any, words: str) -> None:
    frame.get_by_test_id("terminal-enable-typing").click()
    # The press requests a grant. Keyboard input is permitted only after the
    # rendered acknowledgement, which can take longer under the broad rig.
    frame.get_by_role("button", name="View only", exact=True).wait_for(state="visible")
    from playwright.sync_api import expect
    helper = frame.locator("textarea.xterm-helper-textarea")
    # Type owns focus at the press, without a second screen click or a test
    # helper doing work the interface should do itself.
    expect(helper).to_be_focused()
    helper.type(words, delay=45)
    helper.press("Enter")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True, timeout=12).stdout.strip()


def _ag8_hand_refused_wire() -> dict[str, Any]:
    """Return the recorded hub refusal envelope used by StartAgent tests."""
    fixture = Path(__file__).resolve().parents[2] / "web/src/desk/__tests__/fixtures/agents-ag8/hand.refused.wire.json"
    return json.loads(fixture.read_text(encoding="utf-8"))["wire"]


def _workspace_face(page: Any, inventory: Any, name: str) -> None:
    # A restored frame mounts before its lazy core publishes the wings.
    # Wait for that actual chrome before choosing its wide or folded form.
    inventory.locator(".desk-wings").wait_for(state="visible")
    tab = inventory.get_by_role("tab", name=name, exact=True)
    if tab.is_visible():
        tab.click()
    else:
        inventory.get_by_role("button", name=re.compile(r"^Window faces:")).click()
        page.get_by_role("menuitemcheckbox", name=name, exact=True).click()


@pytest.mark.parametrize(("width", "height"), [(1440, 900), (393, 852)])
def test_connected_workspace_keeps_exact_worktree_draft_and_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    """Real private Git/tmux/hub: metadata is seeded, no agent is executed."""
    import holdspeak.delivery.registry as registry_module
    import holdspeak.delivery.factory_launch as launch_module
    from holdspeak.db import get_database
    from holdspeak.delivery import DeliveryRegistry
    from holdspeak.delivery.factory_launch import LaunchLedger
    from scripts.record_connected_workspace_fixture import seed_connected_records
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    sockets = Path(tempfile.mkdtemp(prefix="hsconn-", dir="/tmp"))
    monkeypatch.setenv("TMUX_TMPDIR", str(sockets))
    monkeypatch.setenv("BASH_SILENCE_DEPRECATION_WARNING", "1")
    monkeypatch.delenv("TMUX", raising=False)
    registry_path = tmp_path / "home" / ".holdspeak" / "delivery_sources.json"
    launch_path = tmp_path / "home" / ".holdspeak" / "factory_launches.json"
    monkeypatch.setattr(registry_module, "DEFAULT_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(launch_module, "DEFAULT_LAUNCHES_PATH", launch_path)
    server = None
    connected_shots = evidence_dir("connected-workspace")
    connected_shots.mkdir(parents=True, exist_ok=True)
    try:
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        main = sockets / "repository"
        main.mkdir()
        _git(main, "init", "-b", "main")
        _git(main, "config", "user.email", "fixture@example.test")
        _git(main, "config", "user.name", "Connected fixture")
        (main / "app.txt").write_text("main checkout\n", encoding="utf-8")
        (main / "README.md").write_text("# Private connected fixture\n", encoding="utf-8")
        _git(main, "add", "app.txt", "README.md")
        _git(main, "commit", "-m", "Seed private workspace")
        review, scratch = sockets / "review", sockets / "scratch"
        _git(main, "worktree", "add", "-b", "work/review", str(review))
        _git(main, "worktree", "add", "-b", "work/scratch", str(scratch))
        (review / "app.txt").write_text("review worktree\n", encoding="utf-8")
        (scratch / "app.txt").write_text("scratch worktree\n", encoding="utf-8")
        before_main, before_scratch = _git(main, "rev-parse", "HEAD"), _git(scratch, "rev-parse", "HEAD")
        _tmux("-f", "/dev/null", "new-session", "-d", "-s", "connected-review", "-c", str(review), "bash --noprofile --norc")
        _tmux("new-session", "-d", "-s", "connected-scratch", "-c", str(scratch), "bash --noprofile --norc")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height}, has_touch=width == 393,
                                    reduced_motion="reduce")
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            registered = _api(page, "POST", "/api/repositories", {"path": str(main), "label": "Workspace fixture"}, token=TOKEN)
            source_id = registered["repository"]["id"]
            for worktree in (review, scratch):
                _api(page, "POST", "/api/repositories", {"path": str(worktree)}, token=TOKEN)
            rows = _api(page, "GET", "/api/delivery/terminal/sessions", token=TOKEN)["sessions"]
            first = next(row for row in rows if row["session"] == "connected-review")
            second = next(row for row in rows if row["session"] == "connected-scratch")
            registry = DeliveryRegistry.read_only_snapshot(registry_path)
            source = registry.get(source_id)
            worktree = next(row for row in source.worktrees if Path(row.path).resolve() == review.resolve())
            seeded = seed_connected_records(get_database(), registry, LaunchLedger(launch_path), source,
                                             worktree, first["target"], main, session="connected-review")
            page.goto(f"{base}/terminals?token={TOKEN}", wait_until="load")
            inventory = page.locator('[id="surface-terminals"]')
            inventory.wait_for(state="visible")
            terminal = _open(page, first)
            _type(terminal, "git diff -- app.txt")
            _eventually(lambda: "+review worktree" in _capture(first["pane_id"]))
            terminal.get_by_role("button", name="View only", exact=True).click()
            terminal.get_by_test_id("terminal-workspace").click()
            expect(inventory).to_have_class(re.compile(r"\bis-front\b"))
            _workspace_face(page, inventory, "Sessions")
            # Selecting a connected shell presents the job before the owner
            # opens another wing: the real seeded brief, Project and agent
            # state are readable beside the terminal. Opening the workspace
            # must not dispatch or contact a provider by itself.
            overview = inventory.get_by_test_id("terminal-job-overview")
            expect(overview).to_contain_text("Build the connected workspace")
            expect(overview).to_contain_text("Workspace fixture")
            # The real isolated flight may already be expired (there is no
            # provider process in this engine=none walk); the state remains a
            # named fact rather than an optimistic success or blank.
            assert re.search(r"\b(?:Live|Needs you|Done|expired)\b", overview.inner_text())
            expect(overview).to_contain_text("Codex")
            expect(overview.get_by_role("button", name="Open terminal", exact=True)).to_be_visible()
            _eventually(lambda: "Connecting" not in inventory.inner_text(), seconds=15)
            if width == 393:
                # The overview has three actionable doors on phone. Check
                # their real post-layout hit ownership after scrolling each
                # into view; the status bar must not steal a clipped edge.
                for button in (
                    overview.get_by_role("button", name="Workspace fixture", exact=True),
                    overview.get_by_role("button", name="Open terminal", exact=True),
                    overview.get_by_role("button", name="Open agent", exact=True),
                ):
                    button.evaluate("element => element.scrollIntoView({block: 'center', inline: 'nearest'})")
                    box = button.bounding_box()
                    assert box and box["width"] >= 44 and box["height"] >= 44, box
                    assert button.evaluate("""button => {
                        const r = button.getBoundingClientRect();
                        return [
                            [r.x + r.width / 2, r.y + r.height / 2],
                            [r.left + 2, r.top + 2], [r.right - 2, r.top + 2],
                            [r.left + 2, r.bottom - 2], [r.right - 2, r.bottom - 2],
                        ].every(([x, y]) => {
                            const hit = document.elementFromPoint(x, y);
                            return hit === button || button.contains(hit);
                        });
                    }"""), f"Overlapping overview target: {button.inner_text()}"
                inventory.locator(".terminals-list").evaluate("element => element.scrollTo({top: 0, left: 0})")
                page.screenshot(path=str(connected_shots / "workspace-job-overview-393.png"))
            if width == 1440:
                _api(page, "POST", "/api/desk/windows/arrange", {"rects": {
                    # Positions are offsets from the work band's centre.
                    "surface-terminals": {"x": "-50% + 10", "y": "-50% + 50", "w": "720px", "h": "680px"},
                    f"terminal:{first['id']}": {"x": "40px", "y": "-50% + 50", "w": "660px", "h": "680px"},
                }}, token=TOKEN)
                _settle(page)
                page.screenshot(path=str(connected_shots / "workspace-job-overview.png"))
                # The same selected workspace must reflow when its Desk frame
                # is narrow on a wide viewport. This is a geometry check, not
                # a second browser harness.
                _api(page, "POST", "/api/desk/windows/arrange", {"rects": {
                    "surface-terminals": {"x": "-50% + 10", "y": "-50% + 50", "w": "480px", "h": "620px"},
                    f"terminal:{first['id']}": {"x": "40px", "y": "-50% + 50", "w": "520px", "h": "620px"},
                }}, token=TOKEN)
                _settle(page)
                narrow_inventory = inventory.bounding_box()
                assert narrow_inventory and narrow_inventory["width"] <= 520, narrow_inventory
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(connected_shots / "workspace-job-overview-narrow-desktop.png"))
            _workspace_face(page, inventory, "Files")
            files = inventory.get_by_test_id("terminal-workspace-files")
            files.locator('tr[aria-label="app.txt"]').click()
            expect(files.get_by_test_id("repo-file-content")).to_contain_text("review worktree")
            expect(files.get_by_test_id("repo-file-content")).not_to_contain_text("main checkout")
            page.screenshot(path=str(connected_shots / f"files-{width}.png"))
            # A file handoff uses the producer-backed source/worktree and the
            # bytes just read. It prepares a brief but never sends it until
            # the owner presses Start.
            hand_requests: list[Any] = []
            page.on("request", lambda request: hand_requests.append(request)
                    if request.method == "POST" and request.url.endswith("/api/agent/hand") else None)
            files.get_by_test_id("terminal-file-prepare-agent").click()
            prepared = inventory.get_by_test_id("conductor-start-form")
            prepared.wait_for(state="visible")
            expect(prepared.get_by_test_id("conductor-start-context")).to_contain_text("Workspace fixture")
            expect(prepared.get_by_test_id("conductor-start-context")).to_contain_text("app.txt")
            expect(prepared.get_by_test_id("conductor-start-context")).to_contain_text("work/review")
            words = prepared.get_by_test_id("conductor-start-words")
            expect(words).to_have_value("Review app.txt")
            assert not hand_requests, "Preparing context must not dispatch an agent"
            if width == 393:
                # The compact form is a real scroll surface. Scroll the verbs
                # into view before checking all nine hit points so the Desk
                # status bar cannot own an apparently large clipped target.
                for button in (
                    prepared.get_by_role("button", name="Cancel", exact=True),
                    prepared.get_by_role("button", name="Start", exact=True),
                ):
                    button.evaluate("element => element.scrollIntoView({block: 'center', inline: 'nearest'})")
                    box = button.bounding_box()
                    assert box and box["width"] >= 44 and box["height"] >= 44, box
                    assert button.evaluate("""button => {
                        const r = button.getBoundingClientRect();
                        return [
                            [r.x + r.width / 2, r.y + r.height / 2],
                            [r.left + 2, r.top + 2], [r.right - 2, r.top + 2],
                            [r.left + 2, r.bottom - 2], [r.right - 2, r.bottom - 2],
                        ].every(([x, y]) => {
                            const hit = document.elementFromPoint(x, y);
                            return hit === button || button.contains(hit);
                        });
                    }"""), f"Overlapping compact target: {button.inner_text()}"
            page.screenshot(path=str(connected_shots / f"handoff-prepared-{width}.png"))
            words.fill("Review the exact worktree file")
            prepared.get_by_role("button", name="Cancel", exact=True).click()
            expect(inventory.get_by_test_id("conductor-start-form")).to_have_count(0)
            # Reopen through the same selected file's Prepare agent verb. The
            # generic toolbar starts a fresh, unprepared hand by design.
            files.get_by_test_id("terminal-file-prepare-agent").click()
            reopened_start = inventory.get_by_test_id("conductor-start-form")
            expect(reopened_start.get_by_test_id("conductor-start-words")).to_have_value("Review the exact worktree file")
            expect(reopened_start.get_by_test_id("conductor-start-context")).to_contain_text("Workspace fixture")
            # The hub still records the Note and Project as real local
            # producers; only the named hand boundary is intercepted so this
            # walk cannot start an agent or provider.
            page.route("**/api/agent/hand", lambda route: route.fulfill(
                status=409, content_type="application/json",
                # This is the recorded AG8 refusal envelope from the hub
                # producer, not an invented browser-only error shape.
                body=json.dumps(_ag8_hand_refused_wire()),
            ))
            with page.expect_request(lambda request: request.method == "POST" and request.url.endswith("/api/notes")) as note_request:
                with page.expect_request(lambda request: request.method == "POST" and request.url.endswith("/api/agent/hand")) as hand_request:
                    reopened_start.get_by_role("button", name="Start", exact=True).click()
            note_payload = note_request.value.post_data_json
            hand_payload = hand_request.value.post_data_json
            assert len(hand_requests) == 1, "Only explicit Start may cross the hand boundary"
            assert hand_payload["kind"] == "note"
            assert hand_payload["project_id"] == seeded["project_id"]
            assert note_payload["title"] == "Review the exact worktree file"
            assert "Repository source: Workspace fixture" in note_payload["body_markdown"]
            assert "Captured worktree:" in note_payload["body_markdown"]
            assert "work/review" in note_payload["body_markdown"]
            assert "File path: app.txt" in note_payload["body_markdown"]
            assert "review worktree" in note_payload["body_markdown"]
            expect(reopened_start.get_by_role("alert")).to_contain_text("Not started")
            expect(reopened_start.get_by_test_id("conductor-start-words")).to_have_value("Review the exact worktree file")
            page.screenshot(path=str(connected_shots / f"handoff-failed-{width}.png"))
            page.unroute("**/api/agent/hand")
            reopened_start.get_by_role("button", name="Cancel", exact=True).click()
            files.get_by_role("button", name="Edit file", exact=True).click()
            editor = files.locator('[contenteditable="true"][aria-label="Edit app.txt"]')
            editor.fill("owner draft kept\n")
            (review / "app.txt").write_text("agent changed after open\n", encoding="utf-8")
            page.reload(wait_until="load")
            inventory.wait_for(state="visible")
            _workspace_face(page, inventory, "Sessions")
            terminal = _open(page, first)
            terminal.get_by_test_id("terminal-workspace").click()
            files = inventory.get_by_test_id("terminal-workspace-files")
            files.locator('tr[aria-label="app.txt"]').click()
            files.get_by_role("button", name="Edit file", exact=True).click()
            editor = files.locator('[contenteditable="true"][aria-label="Edit app.txt"]')
            expect(editor).to_have_text("owner draft kept\n")
            # Tabs must not replace a draft's base hash with a newer file hash.
            _workspace_face(page, inventory, "Context")
            context = inventory.get_by_test_id("terminal-workspace-context")
            expect(context).to_contain_text("Workspace fixture")
            expect(context).to_contain_text("Connected workspace")
            expect(context).to_contain_text("Configured")
            expect(context).not_to_contain_text("Review complete")
            expect(context).not_to_contain_text("registered")
            expect(context).to_contain_text("Keep one Desk")
            _settle(page)
            page.screenshot(path=str(connected_shots / f"context-summary-{width}.png"))
            context.get_by_role("button", name="Connected workspace · Step 1", exact=True).click()
            program = page.locator(f'[id="pullout:program:{seeded["program_id"]}"]')
            program.wait_for(state="visible")
            expect(program.get_by_role("textbox", name="Step 1 title", exact=True)).to_have_value("Build the workspace")
            program.get_by_role("button", name=re.compile(r"^Back from " if width == 393 else r"^Close ")).click()
            _inventory(page, base)
            context.locator(".surface-row").filter(has=page.get_by_text("Keep one Desk", exact=True)).get_by_role("button", name="Open decision", exact=True).click()
            decision = page.locator('[id="pullout:decision:decision-connected-workspace"]')
            decision.wait_for(state="visible")
            expect(decision).to_contain_text("Keep one Desk")
            decision.get_by_role("button", name=re.compile(r"^Back from " if width == 393 else r"^Close ")).click()
            _inventory(page, base)
            _settle(page)
            if width == 393:
                from .test_desk_sweep import TARGET_JS

                assert not page.evaluate(TARGET_JS, '[id="surface-terminals"]')
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(connected_shots / f"context-{width}.png"))
            _workspace_face(page, inventory, "Files")
            files = inventory.get_by_test_id("terminal-workspace-files")
            files.locator('tr[aria-label="app.txt"]').click()
            files.get_by_role("button", name="Edit file", exact=True).click()
            editor = files.locator('[contenteditable="true"][aria-label="Edit app.txt"]')
            expect(editor).to_have_text("owner draft kept\n")
            with page.expect_response(lambda response: response.request.method == "PUT"
                                      and f"/api/repositories/{source_id}/file/app.txt" in response.url) as refused_save:
                files.get_by_role("button", name="Save file", exact=True).click()
            assert refused_save.value.status == 409
            assert refused_save.value.json()["error"] == "file changed before write"
            expect(files.get_by_role("alert")).to_contain_text("Your edit stays")
            expect(editor).to_have_text("owner draft kept\n")
            assert (review / "app.txt").read_text() == "agent changed after open\n"
            if width == 393:
                assert not page.evaluate(TARGET_JS, '[id="surface-terminals"]')
            page.screenshot(path=str(connected_shots / f"conflict-{width}.png"))
            # Recover without discarding the owner's words. The review uses
            # actual latest disk bytes and still sends an expected revision.
            with page.expect_response(lambda response: response.request.method == "GET"
                                      and f"/api/repositories/{source_id}/file/app.txt" in response.url) as latest_read:
                files.get_by_role("button", name="Read latest", exact=True).click()
            latest = latest_read.value.json()
            assert latest["content"] == "agent changed after open\n"
            assert f"worktree_id={worktree.worktree_id}" in latest_read.value.url
            expect(files).to_contain_text("agent changed after open")
            expect(editor).to_have_text("owner draft kept\n")
            editor.fill("owner reviewed change\n")
            page.screenshot(path=str(connected_shots / f"review-latest-{width}.png"))
            with page.expect_request(lambda request: request.method == "PUT"
                                     and f"/api/repositories/{source_id}/file/app.txt" in request.url) as reviewed_write:
                files.get_by_role("button", name="Save reviewed edit", exact=True).click()
            assert reviewed_write.value.post_data_json["expected_sha256"] == latest["sha256"]
            expect(files).to_contain_text("File saved")
            assert (review / "app.txt").read_text() == "owner reviewed change\n"
            files.get_by_role("button", name="Changes", exact=True).click()
            changes = inventory.get_by_test_id("terminal-workspace-changes")
            expect(changes).to_contain_text("+owner reviewed change")
            changes.get_by_role("checkbox", name="Select app.txt for Git", exact=True).check()
            stage_lock = Path(_git(review, "rev-parse", "--git-path", "index.lock"))
            if not stage_lock.is_absolute():
                stage_lock = review / stage_lock
            stage_lock.touch(exist_ok=False)
            with page.expect_response(lambda response: response.request.method == "POST"
                                      and f"/api/repositories/{source_id}/stage" in response.url) as refused_stage:
                changes.get_by_role("button", name=re.compile(r"^Stage")).click()
            assert refused_stage.value.status == 409
            expect(changes.get_by_role("checkbox", name="Select app.txt for Git", exact=True)).to_be_checked()
            stage_lock.unlink()
            changes.get_by_role("button", name="Retry", exact=True).click()
            expect(changes).to_contain_text("1 file staged")
            expect(changes.locator(".surface-well").filter(has=page.get_by_text("Staged diff", exact=True))).to_contain_text("+owner reviewed change")
            commit_words = " Review connected workspace change "
            changes.get_by_role("textbox", name="Commit message", exact=True).fill(commit_words)
            page.screenshot(path=str(connected_shots / f"changes-{width}.png"))
            hook = main / ".git" / "hooks" / "pre-commit"
            hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            hook.chmod(0o700)
            with page.expect_response(lambda response: response.request.method == "POST"
                                      and f"/api/repositories/{source_id}/commit" in response.url) as refused_commit:
                changes.get_by_role("button", name="Commit", exact=True).click()
            assert refused_commit.value.status == 409
            expect(changes.get_by_role("textbox", name="Commit message", exact=True)).to_have_value(commit_words)
            assert "+owner reviewed change" in _git(review, "diff", "--cached")
            hook.unlink()
            changes.get_by_role("button", name="Retry", exact=True).click()
            expect(changes).to_contain_text("Changes committed")
            expect(changes.get_by_role("textbox", name="Commit message", exact=True)).to_have_value("")
            assert _git(review, "log", "-1", "--format=%s") == "Review connected workspace change"
            assert _git(main, "rev-parse", "HEAD") == before_main
            assert _git(scratch, "rev-parse", "HEAD") == before_scratch
            assert (main / "app.txt").read_text() == "main checkout\n"
            assert (scratch / "app.txt").read_text() == "scratch worktree\n"
            _workspace_face(page, inventory, "Sessions")
            # The second private shell gets its own source/worktree context,
            # never the first shell's launch, MCP or Program association.
            terminal_b = _open(page, second)
            terminal_b.get_by_test_id("terminal-workspace").click()
            files_b = inventory.get_by_test_id("terminal-workspace-files")
            files_b.locator('tr[aria-label="app.txt"]').click()
            expect(files_b.get_by_test_id("repo-file-content")).to_contain_text("scratch worktree")
            _workspace_face(page, inventory, "Context")
            expect(context).not_to_contain_text("Connected workspace")
            expect(context).to_contain_text("Worktree only")
            sibling_context = next(row for row in _api(page, "GET", "/api/delivery/terminal/sessions", token=TOKEN)["sessions"] if row["id"] == second["id"])["context"]
            assert all(sibling_context[key] is None for key in ("launch", "project", "program", "mcp"))
            # Existing local work needs a complete UI setup path too. This
            # independent Git source is deliberately not in the registry.
            local = sockets / "existing-local"
            local.mkdir()
            _git(local, "init", "-b", "main")
            _git(local, "config", "user.email", "fixture@example.test")
            _git(local, "config", "user.name", "Connected fixture")
            (local / "app.txt").write_text("existing local work\n", encoding="utf-8")
            _git(local, "add", "app.txt")
            _git(local, "commit", "-m", "Existing local source")
            _tmux("new-session", "-d", "-s", "connected-existing", "-c", str(local), "bash --noprofile --norc")
            _workspace_face(page, inventory, "Sessions")
            inventory.get_by_role("combobox", name="Project", exact=True).select_option("all")
            refresh = inventory.get_by_test_id("terminal-refresh")
            if refresh.is_visible():
                refresh.click()
            else:
                inventory.get_by_role("button", name="More", exact=True).click()
                page.get_by_role("menuitem", name="Refresh", exact=True).click()
            third = _eventually(lambda: next((row for row in _api(
                page, "GET", "/api/delivery/terminal/sessions", token=TOKEN,
            )["sessions"] if row["session"] == "connected-existing"), None))
            assert third["context"]["status"] == "unbound"
            third_terminal = _open(page, third)
            third_terminal.get_by_test_id("terminal-workspace").click()
            _workspace_face(page, inventory, "Context")
            folder = context.get_by_role("textbox", name="Repository folder", exact=True)
            expect(folder).to_have_value(str(local.resolve()))
            _settle(page)
            page.screenshot(path=str(connected_shots / f"register-{width}.png"))
            context.get_by_role("button", name="Register folder", exact=True).click()
            expect(context).to_contain_text("Worktree only")
            inventory.get_by_role("combobox", name="Project", exact=True).select_option(seeded["registration_project_id"])
            expect(inventory.get_by_role("combobox", name="Session", exact=True).locator("option:checked")).to_have_text(third["label"])
            context.get_by_role("button", name="Use repository in project", exact=True).click()
            expect(context).to_contain_text("Repository added to project")
            final_rows = _api(page, "GET", "/api/delivery/terminal/sessions", token=TOKEN)["sessions"]
            third_bound = next(row for row in final_rows if row["id"] == third["id"])
            assert third_bound["context"]["status"] == "worktree"
            assert third_bound["context"]["launch"] is None and third_bound["context"]["mcp"] is None
            filed = _api(page, "GET", f"/api/projects/{seeded['registration_project_id']}/resources", token=TOKEN)
            assert f"repository:{third_bound['context']['source']['id']}" in {row["resource_ref"] for row in filed["resources"]}
            _workspace_face(page, inventory, "Sessions")
            expect(inventory.get_by_test_id(f"terminal-row-{third['id']}")).to_be_visible()
            assert not errors, errors
            (connected_shots / f"observation-{width}.json").write_text(json.dumps({
                "engine_mode": "none", "agent_metadata": "real producer seed; no agent process",
                "handoff": {
                    "prepared_without_dispatch": True,
                    "explicit_start_boundary": True,
                    "hand_boundary": "intercepted recorded AG8 no_repository refusal",
                    "provider_dispatch": False,
                },
                "git": "private real main + two worktrees", "tmux": "private real socket",
                "health": _api(page, "GET", "/health", token=TOKEN),
                "build": json.loads((Path(__file__).resolve().parents[2] / "holdspeak/static/_built/.builds.json").read_text())[0],
                "db": str(tmp_path / "holdspeak.db"),
                "project_id": seeded["project_id"], "exact_worktree_edit": True,
                "draft_and_hash_retained_across_wings": True, "real_409_keeps_owner_draft": True,
                "draft_and_hash_retained_across_reload": True,
                "conflict_review_keeps_draft": True,
                "local_stage_and_commit": True, "main_and_sibling_unchanged": True,
                "real_git_failures_keep_selection_and_message": True,
                "matching_program_context": True, "page_errors": errors,
                "matching_program_door": True, "filed_decision_door": True,
                "local_folder_registration": True, "explicit_project_repository_binding": True,
            }, indent=2) + "\n", encoding="utf-8")
            browser.close()
    finally:
        if server is not None:
            server.stop()
        try:
            _tmux("kill-server")
        except subprocess.CalledProcessError:
            pass
        shutil.rmtree(sockets, ignore_errors=True)


@pytest.mark.parametrize(("width", "height"), [(1440, 900), (393, 852)])
def test_independent_input_persistent_views_and_close_without_kill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    _ensure_build()
    # HOME alone does not isolate tmux. Its Unix-socket path must be short
    # on macOS and is owned exclusively by this test, including teardown.
    sockets = Path(tempfile.mkdtemp(prefix="hsterm-", dir="/tmp"))
    monkeypatch.setenv("TMUX_TMPDIR", str(sockets))
    monkeypatch.delenv("TMUX", raising=False)
    server = None
    try:
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        name_a, name_b = "terminal-proof-a", "terminal-proof-b"
        _tmux("-f", "/dev/null", "new-session", "-d", "-s", name_a, "-x", "90", "-y", "28", "bash --noprofile --norc")
        _tmux("new-session", "-d", "-s", name_b, "-x", "90", "-y", "28", "bash --noprofile --norc")
        pane_a = _tmux("list-panes", "-t", name_a, "-F", "#{pane_id}")
        pane_b = _tmux("list-panes", "-t", name_b, "-F", "#{pane_id}")
        assert pane_a != pane_b
        socket_path = _tmux("display-message", "-p", "-t", name_a, "#{socket_path}")
        assert Path(socket_path).resolve().is_relative_to(sockets.resolve())

        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": width, "height": height}, has_touch=width == 393)
            page = context.new_page()
            page.emulate_media(reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            response = page.goto(f"{base}/terminals?token={TOKEN}", wait_until="load")
            assert response is not None and response.status == 200, "Terminals deep link must serve the React shell"
            inventory = page.locator('[id="surface-terminals"]')
            try:
                inventory.wait_for(state="visible", timeout=15_000)
            except Exception:
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(SHOTS / f"failed-inventory-{width}.png"))
                print("Terminals startup:", page.locator("body").inner_text()[:5000], "errors:", errors)
                raise
            sessions = _api(page, "GET", "/api/delivery/terminal/sessions", token=TOKEN)
            assert sessions["status"] == "ok", sessions
            a = next(row for row in sessions["sessions"] if row["session"] == name_a)
            b = next(row for row in sessions["sessions"] if row["session"] == name_b)
            assert a["id"] != b["id"] and a["target"]["target_id"] != b["target"]["target_id"]
            # The frame paints before the core's first inventory read lands
            # (Connecting); wait for the rows, never count at once.
            from playwright.sync_api import expect
            expect(inventory.locator(".kit-listrow")).to_have_count(2, timeout=15_000)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / f"inventory-{width}.png"))
            working = tmp_path / "shell-folder"
            working.mkdir()
            inventory.get_by_test_id("terminal-new").click()
            inventory.get_by_role("textbox", name="Shell name", exact=True).fill("terminal-proof-created")
            inventory.get_by_role("textbox", name="Folder (optional)", exact=True).fill(str(working))
            inventory.get_by_role("button", name="Create shell", exact=True).click()
            created = _eventually(lambda: next((row for row in _api(
                page, "GET", "/api/delivery/terminal/sessions", token=TOKEN,
            )["sessions"] if row["session"] == "terminal-proof-created"), None))
            actual_folder = _tmux("display-message", "-p", "-t", "terminal-proof-created", "#{pane_current_path}")
            assert Path(actual_folder).resolve() == working.resolve()
            made_view = page.locator(f'[id="terminal:{created["id"]}"]')
            made_view.wait_for(state="visible")
            made_view.get_by_role("button", name=re.compile(r"^Back from " if width == 393 else r"^Close ")).click()
            made_view.wait_for(state="detached")
            _tmux("has-session", "-t", "terminal-proof-created")
            _inventory(page, base)
            first = _open(page, a)
            marker_a = f"observed-A-{width}"
            _type(first, f"printf '{marker_a}\\n'")
            _eventually(lambda: marker_a in [line.strip() for line in _capture(pane_a).splitlines()])
            # An Escape belongs to the TUI. It must not dismiss the frame.
            first.locator("textarea.xterm-helper-textarea").press("Escape")
            assert first.is_visible()
            # In bash Escape is a real Readline prefix: the later `printf`
            # would become Meta-p (history search). Cancel that shell mode
            # through the same input seam before continuing the workflow.
            first.locator("textarea.xterm-helper-textarea").press("Control+c")
            if width == 1440:
                # Reflow follows this window's width, even on a wide Desk.
                # The physical pane stays wide/tall and must scroll within
                # the smaller well rather than hiding below clipped chrome.
                frame_box = first.bounding_box()
                grip = first.locator(".desk-window-grip").bounding_box()
                assert frame_box and grip
                start_x, start_y = grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2
                page.mouse.move(start_x, start_y)
                page.mouse.down()
                page.mouse.move(start_x + 480 - frame_box["width"], start_y + 360 - frame_box["height"], steps=8)
                page.mouse.up()
                _settle(page)
                small = first.bounding_box()
                assert small and small["width"] <= 520 and small["height"] <= 400, small
                well = first.locator(".terminal-well")
                screen = first.locator(".terminal-well-screen")
                well_box, screen_box = well.bounding_box(), screen.bounding_box()
                assert well_box and screen_box and screen_box["y"] + screen_box["height"] <= well_box["y"] + well_box["height"] + 1
                assert screen.evaluate("element => element.scrollHeight > element.clientHeight")
                screen.evaluate("element => element.scrollTop = element.scrollHeight")
                assert screen.evaluate("element => element.scrollTop > 0")
                screen.evaluate("element => element.scrollTop = 0")
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(SHOTS / "workspace-narrow-desktop.png"))

            _inventory(page, base)
            second = _open(page, b)
            marker_b = f"observed-B-{width}"
            _type(second, f"printf '{marker_b}\\n'")
            try:
                _eventually(lambda: marker_b in [line.strip() for line in _capture(pane_b).splitlines()])
            except AssertionError as error:
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(SHOTS / f"failed-input-{width}.png"))
                raise AssertionError(f"Independent input not observed. A={_capture(pane_a)!r}; B={_capture(pane_b)!r}; view={second.inner_text()!r}") from error
            assert marker_b not in _capture(pane_a)
            assert marker_a not in _capture(pane_b)
            assert page.locator('[id^="terminal:"]').count() == 2
            if width == 1440:
                _inventory(page, base)
                _tile(inventory, page)
                _eventually(lambda: len(_api(page, "GET", "/api/desk/windows", token=TOKEN)["windows"]) >= 3)
            before = _api(page, "GET", "/api/desk/windows", token=TOKEN)
            terminal_rows = {row["id"]: row for row in before["windows"] if row["id"].startswith("terminal:")}
            assert len(terminal_rows) == 2
            if width == 1440:
                assert terminal_rows[f"terminal:{a['id']}"]["x"] != terminal_rows[f"terminal:{b['id']}"]["x"]
            # The inventory is not the owner of a terminal subscription. A
            # reload with only terminal frames must discover and restore them.
            _api(page, "POST", "/api/desk/windows/surface-terminals/close", token=TOKEN)
            page.reload(wait_until="load")
            page.locator(f'[id="terminal:{b["id"]}"] .xterm').wait_for(state="visible")
            restored = _api(page, "GET", "/api/desk/windows", token=TOKEN)
            after_rows = {row["id"]: row for row in restored["windows"] if row["id"].startswith("terminal:")}
            for ident, row in terminal_rows.items():
                assert ident in after_rows
                assert [after_rows[ident][k] for k in ("x", "y", "w", "h")] == [row[k] for k in ("x", "y", "w", "h")]
            # Restore/focus A, close the window through its own frame and prove
            # the actual producer remains alive. Phone Back returns inventory.
            _inventory(page, base)
            first = _open(page, a)
            close = first.get_by_role("button", name=re.compile(r"^Back from " if width == 393 else r"^Close "))
            close.click()
            first.wait_for(state="detached")
            _tmux("has-session", "-t", name_a)
            assert marker_a in _capture(pane_a)
            _inventory(page, base)
            reopened = _open(page, a)
            reopened.locator(".xterm").wait_for(state="visible")
            # The screen owns the default face; the optional voice/message
            # composer does not occupy space until the owner asks for it.
            assert reopened.get_by_test_id("terminal-composer").count() == 0
            from playwright.sync_api import expect
            arm_url = f"**/api/coders/{quote(a['key'], safe='')}/arm"
            pending_arm: list[Any] = []
            page.route(arm_url, lambda route: pending_arm.append(route))
            with page.expect_request(arm_url):
                reopened.get_by_test_id("terminal-enable-typing").click()
            expect(reopened.locator("textarea.xterm-helper-textarea")).to_be_focused()
            assert len(pending_arm) == 1
            reopened.get_by_test_id("terminal-find").click()
            finder = reopened.get_by_role("textbox", name="Find in scrollback", exact=True)
            finder.fill(marker_a)
            # A real hub answer is withheld, then released after the owner has
            # chosen another input. Its arrival must never steal that focus.
            reply = pending_arm[0].fetch()
            pending_arm[0].fulfill(response=reply)
            page.unroute(arm_url)
            reopened.get_by_role("button", name="View only", exact=True).wait_for(state="visible")
            expect(finder).to_be_focused()
            reopened.get_by_test_id("terminal-find").click()
            expect(reopened.locator("textarea.xterm-helper-textarea")).to_be_focused()
            message = reopened.get_by_role("button", name="Message", exact=True)
            message.click()
            composer = reopened.get_by_test_id("terminal-composer")
            field = composer.get_by_role("textbox", name="Message", exact=True)
            field.fill("keep this draft")
            message.click()
            expect(composer).to_have_count(0)
            expect(reopened.locator("textarea.xterm-helper-textarea")).to_be_focused()
            message.click()
            expect(field).to_have_value("keep this draft")
            marker_message = f"observed-message-{width}"
            field.fill(f"printf '{marker_message}\\n'")
            with page.expect_response("**/api/delivery/terminal/commands") as sent_message:
                composer.get_by_role("button", name="Send", exact=True).click()
            message_response = sent_message.value
            message_wire = {
                "request": message_response.request.post_data_json,
                "response": message_response.json(),
            }
            try:
                _eventually(lambda: marker_message in [line.strip() for line in _capture(pane_a).splitlines()])
            except AssertionError as error:
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(SHOTS / f"failed-message-{width}.png"))
                raise AssertionError(f"Message output not observed. A={_capture(pane_a)!r}; B={_capture(pane_b)!r}; wire={message_wire!r}; view={reopened.inner_text()!r}; draft={field.input_value()!r}") from error
            expect(field).to_have_value("")
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / f"message-{width}.png"))
            message.click()
            expect(composer).to_have_count(0)
            # Shared menus/search remain reachable by keyboard without
            # dismissing the terminal itself.
            keys = reopened.get_by_role("button", name="Keys", exact=True)
            keys.click()
            page.get_by_role("menuitem", name="Ctrl-C", exact=True).wait_for(state="visible")
            page.keyboard.press("Escape")
            assert reopened.is_visible()
            reopened.get_by_test_id("terminal-find").click()
            finder = reopened.get_by_role("textbox", name="Find in scrollback", exact=True)
            finder.fill(marker_a)
            finder.press("Enter")
            reopened.get_by_test_id("terminal-find").click()
            finder.wait_for(state="detached")
            expect(reopened.locator("textarea.xterm-helper-textarea")).to_be_focused()
            if width == 393:
                for button in (keys, reopened.get_by_test_id("terminal-enable-typing"), reopened.get_by_test_id("terminal-find"), message):
                    box = button.bounding_box()
                    assert box and box["width"] >= 44 and box["height"] >= 44, box
                    assert button.evaluate("""button => {
                        const r = button.getBoundingClientRect();
                        return [
                            [r.x + r.width / 2, r.y + r.height / 2],
                            [r.left + 2, r.top + 2], [r.right - 2, r.top + 2],
                            [r.left + 2, r.bottom - 2], [r.right - 2, r.bottom - 2],
                        ].every(([x, y]) => {
                            const hit = document.elementFromPoint(x, y);
                            return hit === button || button.contains(hit);
                        });
                    }"""), f"Overlapping compact target: {button.inner_text()}"
                screen = reopened.locator(".terminal-well-screen")
                assert screen.evaluate("element => element.scrollWidth > element.clientWidth")
                screen.evaluate("element => element.scrollLeft = 100")
                assert screen.evaluate("element => element.scrollLeft > 0")
                screen.evaluate("element => element.scrollLeft = 0")
            if width == 1440:
                inventory = _inventory(page, base)
                _tile(inventory, page)
            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / f"workspace-{width}.png"))
            layout = page.evaluate("""() => {
                const rect = (element) => {
                    if (!element) return null;
                    const r = element.getBoundingClientRect();
                    return {x:r.x, y:r.y, width:r.width, height:r.height,
                        right:r.right, bottom:r.bottom};
                };
                const tokens = getComputedStyle(document.documentElement);
                const luminance = (token) => {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = tokens.getPropertyValue(token).trim();
                    ctx.fillRect(0, 0, 1, 1);
                    const rgb = [...ctx.getImageData(0, 0, 1, 1).data].slice(0,3)
                        .map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
                    return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
                };
                const foreground = luminance('--text-on-accent');
                const background = luminance('--desk-terminal-screen');
                return {
                    terminal_text_contrast: (Math.max(foreground, background) + .05)
                        / (Math.min(foreground, background) + .05),
                    dock: rect(document.querySelector('.desk-dock')),
                    terminals: [...document.querySelectorAll('[id^="terminal:"]')]
                        .filter(element => element.getBoundingClientRect().width > 0)
                        .map(element => ({id:element.id, frame:rect(element),
                            composer:rect(element.querySelector('[data-testid="terminal-composer"]')),
                            body:rect(element.querySelector('.terminals-window-body')),
                            toolbar:rect(element.querySelector('[data-testid="terminal-toolbar"]')),
                            screen:rect(element.querySelector('.terminals-screen')),
                            status:rect(element.querySelector('[data-testid="terminal-status"]'))})),
                };
            }""")
            (SHOTS / f"observation-{width}.json").write_text(json.dumps({
                "viewport": width, "source": "production browser + isolated hub + private real tmux",
                "db": str(tmp_path / "holdspeak.db"), "socket": socket_path,
                "targets": [a["id"], b["id"]], "observed": [marker_a, marker_b, marker_message],
                "type_focused_without_second_click": True,
                "late_grant_kept_find_focus": True,
                "message_draft_survived_disclosure": True,
                "close_kept_session": True, "restored_geometry": True, "page_errors": errors,
                "layout": layout,
            }, indent=2))
            assert not errors, errors
            assert layout["terminal_text_contrast"] >= 4.5, layout
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert layout["terminals"], layout
            for terminal in layout["terminals"]:
                frame, body, toolbar, screen, status = (
                    terminal[key] for key in ("frame", "body", "toolbar", "screen", "status")
                )
                assert terminal["composer"] is None, terminal
                assert -1 <= frame["x"] and frame["right"] <= width + 1, terminal
                assert 0 <= frame["y"] and frame["bottom"] <= height + 1, terminal
                # The terminal is the window's working surface, with no pale
                # page inset or empty gap between the shared strips.
                assert abs(screen["x"] - body["x"]) <= 1, terminal
                assert abs(screen["right"] - body["right"]) <= 1, terminal
                assert abs(screen["y"] - toolbar["bottom"]) <= 1, terminal
                assert abs(screen["bottom"] - status["y"]) <= 1, terminal
                assert status["bottom"] <= layout["dock"]["y"] + 1, terminal
            browser.close()
    finally:
        if server is not None:
            server.stop()
        for socket in sockets.glob("tmux-*/default"):
            subprocess.run(["tmux", "-S", str(socket), "kill-server"], capture_output=True, timeout=5, check=False)
        shutil.rmtree(sockets, ignore_errors=True)
