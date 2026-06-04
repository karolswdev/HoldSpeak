"""HS-38-06 demo — screenshot the live "Pending actions" panel.

Serves the built dashboard (`holdspeak/static/_built/index.html`) statically, seeds
two live `actuator_proposed` proposals into the Alpine component (exactly what the
`actuator_proposed` broadcast handler does — no backend needed), and screenshots the
panel to `live_pending_actions.png`.

Requires a built bundle (`cd web && npm run build`) + Playwright/Chromium. Run from
the repo root:

    uv run python3 pm/roadmap/holdspeak/phase-38-actuators-ii/evidence/capture_live_panel.py
"""
from __future__ import annotations

import functools
import http.server
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[5]
WEB_ROOT = REPO / "holdspeak" / "static"
OUT = Path(__file__).with_name("live_pending_actions.png")

SEED_JS = """
() => {
  const el = document.querySelector('[x-data]');
  const data = window.Alpine ? window.Alpine.$data(el) : el._x_dataStack[0];
  // Exactly the read-only descriptors the actuator_proposed broadcast carries.
  data.addProposal({
    id: 'p-gh-1', meeting_id: 'm-live', plugin_id: 'github_issue_actuator',
    status: 'proposed', target: 'github', action: 'create_issue',
    preview: 'Open a GitHub issue in acme/app: “Follow up: Wire the staging smoke test”',
    reversible: false, created_at: '2026-06-04T12:00:00',
  });
  data.addProposal({
    id: 'p-hook-1', meeting_id: 'm-live', plugin_id: 'webhook_post_actuator',
    status: 'proposed', target: 'webhook', action: 'post_message',
    preview: 'POST a meeting update to hooks.example.test: “Release planning wrapped — 1 action item(s) captured.”',
    reversible: false, created_at: '2026-06-04T12:00:01',
  });
}
"""


def main() -> None:
    if not (WEB_ROOT / "_built" / "index.html").exists():
        raise SystemExit("built bundle missing — run `cd web && npm run build` first")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB_ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 460, "height": 900}, device_scale_factor=2)
            page.goto(f"http://127.0.0.1:{port}/_built/index.html", wait_until="networkidle")
            page.wait_for_selector("[x-data]")
            page.wait_for_timeout(400)  # let Alpine mount
            page.evaluate(SEED_JS)
            panel = page.wait_for_selector(".proposals-panel", state="visible", timeout=5000)
            page.wait_for_timeout(200)
            panel.screenshot(path=str(OUT))
            browser.close()
        print(f"wrote {OUT}")
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
