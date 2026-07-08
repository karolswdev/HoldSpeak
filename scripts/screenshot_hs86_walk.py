"""HS-86-05 — the walk: this story crosses its own belt, live.

One hub, one page session (never reloaded), real acts between shots:
the story was flipped in-progress via the CLI before launch; evidence
is captured mid-walk; a REAL gate refusal is staged (a commit attempt
with no contract); the phase's real PR opens. Every belt change the
page shows arrived frame- or poll-driven — `page.reload` is never
called. The hub's mission-control access log is recorded in-process
and dumped; the walk's exit assertion is that it holds only GETs.
"""
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

from playwright.sync_api import sync_playwright

from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak/phase-86-delivery-belt/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
ACCESS_LOG = Path("pm/roadmap/holdspeak/phase-86-delivery-belt/screenshots/walk-access-log.json")
REPO = Path(__file__).resolve().parent.parent


def run(argv: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("  $", " ".join(argv))
    return subprocess.run(argv, cwd=REPO, capture_output=True, text=True, check=check)


def main() -> None:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    hits: list[dict] = []

    @server.app.middleware("http")
    async def _record(request, call_next):  # the walk's read-only proof
        if request.url.path.startswith("/api/missioncontrol"):
            hits.append({"method": request.method, "path": request.url.path})
        return await call_next(request)

    url = server.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            pg = browser.new_page(viewport={"width": 1440, "height": 1000})
            pg.goto(f"{url}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-mc-repo-head", timeout=30_000)
            pg.wait_for_timeout(1_000)
            conveyor = pg.locator(".desk-mc")
            chip = pg.locator(".desk-mc-story", has_text="HS-86-05")

            # W1 — the story rides in-progress (flipped via the CLI
            # before launch; the belt read it from receipts).
            assert "st-in-progress" in (chip.first.get_attribute("class") or "")
            conveyor.screenshot(path=str(OUT / "walk-1-story-in-progress.png"))
            print("W1: in-progress on the belt")

            # W2 — evidence captured mid-walk; the tick appears with
            # no reload (poll heartbeat + belt frame).
            run([
                ".githooks/dw", "evidence", "capture", "holdspeak", "86", "5", "--",
                "uv", "run", "pytest", "-q",
                "tests/unit/test_web_routes_missioncontrol.py",
            ])
            chip.first.locator(".desk-mc-evidence-open").wait_for(timeout=40_000)
            conveyor.screenshot(path=str(OUT / "walk-2-evidence-station.png"))
            print("W2: evidence tick, no reload")

            # W3 — a REAL refusal: a commit attempted with no
            # contract. The gate blocks; the refusal event reaches
            # the belt's gate light.
            run(["git", "add", "pm/roadmap/holdspeak/phase-86-delivery-belt"])
            probe = run(["git", "commit", "-m", "walk probe (must not land)"], check=False)
            assert probe.returncode != 0, "the gate must refuse"
            pg.locator(".desk-mc-light.gate-refusal").wait_for(timeout=40_000)
            conveyor.screenshot(path=str(OUT / "walk-3-gate-refusal.png"))
            print("W3: the gate refused; the belt wears it")

            # W4 — the phase's real PR opens; the PR + CI lights come on.
            run(["git", "push", "-u", "origin", "phase-86-delivery-belt"], check=False)
            pr = run([
                "gh", "pr", "create",
                "--title", "Phase 86: the Delivery Belt (read-only) — the AI-Headquarters floor",
                "--body", "The conveyor completes: gh receipts as station lights, "
                "scope:belt frames on the one bus, evidence opening in place, the tree "
                "clean and the rails current. Closed by this walk.\n\n"
                "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
                "https://claude.ai/code/session_01CWNwHDFD8prLGXtToBoSZQ",
            ], check=False)
            print("  pr:", (pr.stdout or pr.stderr).strip().splitlines()[-1])
            pg.locator(".desk-mc-light.pr", has_text="1").first.wait_for(timeout=60_000)
            conveyor.screenshot(path=str(OUT / "walk-4-pr-and-ci-lights.png"))
            print("W4: PR + CI lights lit")

            browser.close()
    finally:
        server.stop()

    ACCESS_LOG.write_text(json.dumps(hits, indent=1))
    methods = {h["method"] for h in hits}
    assert methods == {"GET"}, f"belt-side writes observed: {methods}"
    print(f"access log: {len(hits)} mission-control requests, all GET")


if __name__ == "__main__":
    main()
