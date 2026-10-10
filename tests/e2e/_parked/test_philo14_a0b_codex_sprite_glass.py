"""PHILO-14 A0b round 2 -- a Codex session wears the Codex sprite at rest,
lit (hover) and selected on the real Floor.

Astra's counsel on PR #934: ``engine.ts`` lit the hovered object with a
sprite URL built without the agent name, so a Codex coder turned into the
Claude Code robot under the pointer. The scene object now carries its own
lit URL (``SceneObject.spriteSel``) built with the agent.

The producer is real: the ``holdspeak agent-hook ingest --agent codex`` CLI
records a session from the Codex transcript fixture into the isolated
HOME's agent registry; the hub reads it through ``/api/coders/status``. The fence sweeps the
pointer over the Floor, presses the object that lit, then moves away, and
asserts every agent sprite the page asked for is ``agent-codex*``.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the Codex sprite glass needs Playwright")

TOKEN = "philo14-a0b-codex-sprite"
REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "agent_transcripts" / "codex_question.jsonl"


def _ingest_codex(home: Path, registry: Path) -> dict[str, Any]:
    transcript = home / "codex_question.jsonl"
    shutil.copyfile(FIXTURE, transcript)
    payload = {"session_id": "philo14-a0b-codex", "cwd": str(home),
               "hook_event_name": "Stop", "transcript_path": str(transcript)}
    env = {**os.environ, "HOME": str(home),
           "PYTHONPATH": str(REPO) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    done = subprocess.run(
        [sys.executable, "-m", "holdspeak.main", "agent-hook", "ingest",
         "--agent", "codex", "--state-path", str(registry),
         "--capture-messages", "--print-summary"],
        cwd=str(home), env=env, input=json.dumps(payload),
        capture_output=True, text=True, check=False, timeout=120)
    assert done.returncode == 0, done.stderr[-800:]
    return json.loads(done.stdout)


class TestCodexSpriteKeepsItsFace:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        import holdspeak.agent_context as agent_context
        import holdspeak.agent_context.models as agent_models

        self.registry = tmp_path / "home" / ".holdspeak" / "agent_sessions.json"
        monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", self.registry)
        monkeypatch.setattr(agent_models, "AGENT_CONTEXT_FILE", self.registry)
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        self.home = tmp_path / "home"
        try:
            yield
        finally:
            server.stop()

    def test_codex_stays_codex_at_rest_hover_and_selected(self) -> None:
        from playwright.sync_api import sync_playwright

        session = _ingest_codex(self.home, self.registry)
        assert session["agent"] == "codex"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
            page.set_default_timeout(30_000)
            asked: list[str] = []
            page.on("request", lambda r: asked.append(r.url.split("?")[0].rsplit("/", 1)[-1])
                    if "/desk/sprites/agent-" in r.url else None)
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                coders = _api(page, "GET", "/api/coders/status", token=TOKEN)
                assert "codex" in json.dumps(coders), ("the producer response has no Codex", coders)
                page.reload(wait_until="load")
                _normal_chair(page)
                _settle(page)
                page.locator("[data-testid=chair-floor-toggle]").click()
                page.wait_for_timeout(2500)
                assert "agent-codex.png" in asked, ("the Floor never drew the Codex at rest", asked)

                # Sweep the pointer until the Codex lights (its _sel image).
                lit_at = None
                for y in range(80, 860, 40):
                    for x in range(20, 1440, 40):
                        page.mouse.move(x, y)
                        page.wait_for_timeout(15)
                        if "agent-codex_sel.png" in asked:
                            lit_at = (x, y)
                            break
                    if lit_at:
                        break
                assert lit_at, ("hover never lit the Codex", asked)
                page.mouse.click(*lit_at)  # selected
                page.wait_for_timeout(800)
                page.mouse.move(1430, 70)  # away
                page.wait_for_timeout(800)
                page.mouse.move(*lit_at)  # hover again
                page.wait_for_timeout(800)
                wrong = [a for a in asked if not a.startswith("agent-codex")]
                assert not wrong, ("a Codex wore another agent's sprite", asked)
            finally:
                browser.close()
