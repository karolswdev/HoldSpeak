"""PHILO-14 C2: the agent's lane window on a real hub (ratified board A-4 with
C-4's station track).

A real hub on an isolated HOME. What a Hand to coder launch leaves behind,
written through the product's producers as the Conductor F2 seed does
(`docs/internal/philo/phase-14/canvas/harness/seed_f2.py`): an action item on
a meeting, a real clone with a launch worktree and one commit on its branch
(a Delivery Source), the launch on the ledger with its Work attempt bound to a
Claude Code session, the session's hook events (spooled, drained by the lane
read), a held gate proposal, HoldSpeak's drafted answer, and the PR on the
launch's follow-through. No agent runs; nothing leaves the machine.

The real entry opens the lane (not the session window): Dock -> Conductor ->
Open on the asking agent (PHILO-14 C4; the Arrival's coder Open is parked). The test
reads the lane's sections, toggles Raw, and shoots the window at 1440 and 393
to `.tmp/evidence-shots/p14-c2/`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the lane glass needs Playwright")

from .agents_lane_rig import KEY, PSQL, QUESTION, SESSION_ID, TOKEN, _git, _http, _open_lane, _seed, mint_held_call  # noqa: F401  (the rig: tests/e2e/agents_lane_rig.py)

SHOTS = evidence_dir("p14-c2")


@pytest.mark.timeout(240)
def test_the_agents_lane_window_at_1440_and_393(tmp_path: Path, monkeypatch) -> None:
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    import holdspeak.delivery.registry as delivery_registry
    from holdspeak.agent_context import event_log
    from holdspeak.services import agent_responder

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", state / "delivery_sources.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", state / "agent_answers.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        seed = _seed(tmp_path / "home")
        mint_held_call(url, seed["worktree"])
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width, height in ((1440, 900), (393, 852)):
                page = browser.new_page(viewport={"width": width, "height": height})
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                # PHILO-16 (16b): one hub is one desk; this page starts on an empty desk.
                from .glass_infra import clear_hub_windows

                clear_hub_windows(page, TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                _settle(page)
                window = _open_lane(page)
                # The session window is not the face of a launch's session.
                assert page.locator(".is-session").count() == 0

                assert "Claude Code: Write the rollback runbook" in (window.text_content() or "")
                track = page.locator("[data-testid='lane-track']")
                track_text = track.text_content() or ""
                for word in ("BRIEF", "WORK", "COMMIT", "PR", "HELD", "ASKS", "MERGE"):
                    assert word in track_text, track_text
                assert "#413" in track_text and "1 HELD · 1 WAITING" in track_text and "now" in track_text
                assert page.locator("[data-testid='lane-ask'] .ask-well-question").text_content() == QUESTION
                assert "Jordan owns it. Avery reviews." in (page.locator("[data-testid='lane-ask'] .ask-well-draft").text_content() or "")
                rail = page.locator("[data-testid='lane-rail']").text_content() or ""
                for word in ("BRIEF", "READ", "SAYS", "WRITE", "RUN", "COMMIT", "PR", "HELD", "ASKS", "MERGE"):
                    assert word in rail, rail
                assert "Draft the ledger rollback runbook" in rail
                assert "psql -h staging-ledger" in rail
                assert "Your press in GitHub" in rail
                pr = page.locator("[data-testid='lane-pr']").text_content() or ""
                assert "#413" in pr and "CHECKS 6 OF 7" in pr and "1 RUNNING" in pr
                files = page.locator("[data-testid='lane-files']").text_content() or ""
                assert "docs/ledger-rollback.md" in files and "freeze.py" in files
                assert page.get_by_text("GITHUB.COM").first.is_visible()
                assert page.locator("[data-testid='lane-open-pr']").is_visible()
                assert page.locator("[data-testid='lane-stop']").is_visible()

                page.wait_for_timeout(400)
                page.screenshot(path=str(SHOTS / f"C2-lane-{width}.png"))
                if width == 393:
                    # C2b: every footer verb is whole in the frame, 44 px tall,
                    # and is the element at its own centre; no side scroll.
                    verbs = page.locator(".is-lane .surface-footer-verbs button").evaluate_all(
                        """(els) => els.map((el) => {
                            const r = el.getBoundingClientRect();
                            const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                            return {name: el.textContent.trim(), left: r.left, right: r.right, top: r.top,
                                    bottom: r.bottom, height: r.height, hit: !!hit && el.contains(hit)};
                        })""")
                    names = [v["name"] for v in verbs]
                    assert any("Stop" in n for n in names) and any("Open PR" in n for n in names), names
                    for v in verbs:
                        assert v["left"] >= 0 and v["right"] <= 393 and v["top"] >= 0 and v["bottom"] <= 852, v
                        assert v["height"] >= 44, v
                        assert v["hit"], v
                    assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")

                # Raw: the terminal pane in place of the lane, and back.
                page.locator("[data-testid='lane-raw']").click()
                page.locator("[data-testid='lane-raw-pane']").wait_for(timeout=5000)
                assert page.locator("[data-testid='lane-rail']").count() == 0
                if width == 1440:
                    page.screenshot(path=str(SHOTS / f"C2-lane-raw-{width}.png"))
                page.locator("[data-testid='lane-raw']").click()
                page.locator("[data-testid='lane-rail']").wait_for(timeout=5000)
                if width == 393:
                    # Approve the held call from the rail: the real gate route decides it.
                    held = page.locator(".lane-rail-entry").filter(has_text="psql -h staging-ledger")
                    with page.expect_response(lambda r: "/toolu_psql/decide" in r.url) as got:
                        held.locator("[data-testid='lane-approve']").click()
                    assert got.value.status == 200, got.value.text()
                    status, stored = _http(url, "GET", "/api/gate/proposals/toolu_psql", TOKEN)
                    assert stored["state"] == "approved", stored
                    held.locator("[data-testid='lane-approve']").wait_for(state="detached", timeout=10000)

                    # PHILO-14 A5 (Astra r2): a 198-char call the hook cuts.
                    # The lane shows `<head>… +90 CHARS`, Deny and Raw (the
                    # pane holds the whole command), never Approve.
                    base = "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = "
                    long_cmd = base + "7" * (198 - len(base) - 1) + "'"
                    mint_held_call(url, seed["worktree"], long_cmd, "toolu_cut")
                    page.reload(wait_until="load")
                    _normal_chair(page)
                    _settle(page)
                    # The lane window comes back after the reload (B2): read it again.
                    page.locator(".is-lane [data-testid='lane-rail']").wait_for(timeout=15000)
                    cut = page.locator(".lane-rail-entry").filter(has_text="+90 CHARS").first
                    cut.wait_for(timeout=15000)
                    shown = (cut.text_content() or "")
                    assert long_cmd[:100] in shown and "… +90 CHARS" in shown, shown
                    assert cut.locator("[data-testid='lane-approve']").count() == 0
                    assert cut.locator("[data-testid='lane-deny']").count() == 1
                    assert cut.locator("[data-testid='lane-raw-cut']").count() == 1
                    cut.scroll_into_view_if_needed()
                    page.screenshot(path=str(SHOTS / f"C2-lane-cut-{width}.png"))
                _assert_clean(page, errors)
                page.close()
            browser.close()
    finally:
        server.stop()
