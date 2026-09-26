"""PHILO-8-01 canvas: shoot the list's in-row zone name field at 1440 and 393.

Everything is live: a REAL hub (scripts/graph_walk.py serve, isolated HOME,
isolated DB) and the PRODUCT app served by vite with ONE module swapped
(harness/vite.config.mjs: DeskListView -> ProposedDeskListView.tsx). Board 0
and board 7 are the product as built on this branch, served by the hub itself.

Usage (from the repo root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
    uv run python pm/roadmap/holdspeak-philo/phase-8-the-honest-floor/assets/story-01-canvas/harness/shoot.py

Per board and width, shots/facts.json records the focused element, the zone
rows as rendered, the refusal chip and its code, every text node under 12 px
in the list, every raw <button>, the page's horizontal overflow, and each
hub write (method, path, status) the board made.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
REPO = CANVAS.parents[5]
WEB = REPO / "web"
SHOTS = CANVAS / "shots"
TOKEN = "philo8-canvas"
WIDTHS = [(1440, 900), (393, 852)]
LONG_NAME = "Quarterly architecture review and platform roadmap"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, headers: dict[str, str] | None = None, timeout: float = 60) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=2) as r:
                if r.status < 500:
                    return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError(f"not up: {url}")


FACTS = """() => {
  const list = document.querySelector('.desk-listmode');
  const small = [];
  if (list) {
    const walker = document.createTreeWalker(list, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const t = n.textContent.trim();
      if (!t || /^[●○✓✗⚠—↻ℹ«»·\\[\\]x ]+$/.test(t)) continue;
      const el = n.parentElement;
      const r = el.getBoundingClientRect();
      if (!r.width || getComputedStyle(el).visibility === 'hidden') continue;
      const fs = parseFloat(getComputedStyle(el).fontSize);
      if (fs < 12) small.push({text: t.slice(0, 40), fs, cls: String(el.className)});
    }
  }
  const zoneRows = [...document.querySelectorAll('.desk-sortable-table-row')]
    .filter(r => (r.innerText || '').includes('ZONE') || r.querySelector('.desk-zone-rename'))
    .map(r => ({
      text: r.innerText.replace(/\\s+/g, ' ').trim().slice(0, 80),
      field: r.querySelector('input.desk-zone-rename')?.value ?? null,
      refused: r.querySelector('[data-code]')?.dataset.code ?? null,
      chip: r.querySelector('.surface-state-chip')?.innerText.replace(/\\s+/g, ' ').trim() ?? null,
    }));
  const input = document.querySelector('input.desk-zone-rename');
  const ir = input?.getBoundingClientRect();
  return {
    active: document.activeElement ? `${document.activeElement.tagName}.${document.activeElement.className}` : null,
    field_focused: !!input && document.activeElement === input,
    field_rect: ir ? {x: ir.left, y: ir.top, w: ir.width, h: ir.height} : null,
    field_font_px: input ? parseFloat(getComputedStyle(input).fontSize) : null,
    field_selection: input ? {start: input.selectionStart, end: input.selectionEnd, length: input.value.length} : null,
    kind_header_x: (() => { const th = [...document.querySelectorAll('.desk-listmode th')].find(t => /^KIND/.test((t.innerText || '').trim())); return th ? Math.round(th.getBoundingClientRect().left) : null; })(),
    row_heights: [...document.querySelectorAll('.desk-sortable-table-row')].slice(0, 12).map(r => Math.round(r.getBoundingClientRect().height)),
    zone_rows: zoneRows,
    small_text: small,
    raw_buttons: list ? [...list.querySelectorAll('button')].filter(b => !String(b.className).includes('btn')).length : null,
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
    palette_new_zone: !!document.querySelector("[id='desk-palette-option-desk.new-zone']"),
  };
}"""


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    home = tempfile.mkdtemp(prefix="philo8-canvas-")
    hub_port, canvas_port = free_port(), free_port()
    hub_url = f"http://127.0.0.1:{hub_port}"
    env = {**os.environ, "HOME": home}
    hub = subprocess.Popen(
        ["uv", "run", "python", "scripts/graph_walk.py", "serve", "--port", str(hub_port), "--token", TOKEN],
        cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    vite = subprocess.Popen(
        [str(WEB / "node_modules/.bin/vite"), "--config", str(HERE / "vite.config.mjs")],
        cwd=WEB, env={**os.environ, "HUB": hub_url, "CANVAS_PORT": str(canvas_port)},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    auth = {"Authorization": f"Bearer {TOKEN}"}
    facts: dict[str, dict] = {}
    try:
        wait_http(f"{hub_url}/api/setup/status", auth)
        wait_http(f"http://127.0.0.1:{canvas_port}/")
        canvas_url = f"http://127.0.0.1:{canvas_port}"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for width, height in WIDTHS:
                writes: list[dict] = []

                def api(page, method, path, body=None):
                    return page.evaluate(
                        """async ([m, p, b, t]) => { const r = await fetch(p, {method: m,
                           headers: {authorization: `Bearer ${t}`, ...(b ? {'content-type': 'application/json'} : {})},
                           body: b ? JSON.stringify(b) : undefined}); return {status: r.status, body: await r.json().catch(() => null)}; }""",
                        [method, path, body, TOKEN],
                    )

                def open_page(origin: str):
                    ctx = browser.new_context(viewport={"width": width, "height": height})
                    page = ctx.new_page()
                    page.on("response", lambda r: writes.append(
                        {"method": r.request.method, "path": r.url.split(origin)[-1].split("?")[0], "status": r.status})
                        if r.request.method in ("POST", "PUT", "DELETE", "PATCH") and "/api/directories" in r.url else None)
                    page.goto(f"{origin}/?token={TOKEN}", wait_until="load")
                    chair = page.locator(".chair")
                    chair.wait_for(timeout=30_000)
                    if chair.evaluate("e => e.classList.contains('chair-first-value')"):
                        page.get_by_role("button", name="Continue later", exact=True).click()
                    page.locator(".chair:not(.chair-first-value)").wait_for()
                    return ctx, page

                def palette(page, query):
                    page.locator("[aria-controls=desk-tool-shelf]").click()
                    page.locator("[aria-controls=desk-palette-listbox]").fill(query)

                def to_list(page):
                    page.locator("[data-testid=chair-floor-toggle]").click()
                    if not page.locator(".desk-listmode").count():
                        palette(page, "view")
                        page.locator("[id='desk-palette-option-desk.toggle-view']").click()
                    page.locator(".desk-listmode").wait_for(timeout=10_000)

                def new_zone(page):
                    palette(page, "New Zone")
                    page.locator("[id='desk-palette-option-desk.new-zone']").click()
                    page.locator("input.desk-zone-rename").wait_for(timeout=20_000)
                    page.wait_for_timeout(300)

                def shoot(page, board):
                    key = f"{board}-{width}"
                    writes_before = len(writes)
                    page.screenshot(path=str(SHOTS / f"{key}.png"))
                    facts[key] = {**page.evaluate(FACTS), "writes": writes[:]}
                    print(key, json.dumps(facts[key]["zone_rows"][:3])[:200], "focused", facts[key]["field_focused"])
                    del writes_before

                # Seed: one "New zone" already on the desk, so New Zone names "New zone 2".
                ctx, page = open_page(hub_url)
                existing = [d["name"] for d in api(page, "GET", "/api/directories")["body"]["directories"]]
                if "New zone" not in existing:
                    api(page, "POST", "/api/directories", {"name": "New zone"})

                # Board 0 — today, the product as built on this branch (half A): New Zone on
                # the list makes "New zone 2" and nothing opens.
                to_list(page)
                palette(page, "New Zone")
                page.locator("[id='desk-palette-option-desk.new-zone']").click()
                page.wait_for_timeout(6000)
                shoot(page, "0-today-list-after-new-zone")
                # Put the desk back for the proposal boards: remove "New zone 2".
                for d in api(page, "GET", "/api/directories")["body"]["directories"]:
                    if d["name"] == "New zone 2":
                        api(page, "DELETE", f"/api/directories/{d['id']}")
                # Board 7 — the Chair offers no New Zone (half A, built). Reload first so
                # the store holds the hub's zones after the API delete above (C3).
                page.reload(wait_until="load")
                page.locator(".chair:not(.chair-first-value)").wait_for(timeout=30_000)
                if page.locator(".desk-listmode").count():
                    page.locator("[data-testid=chair-floor-toggle]").click()
                page.locator(".chair").wait_for()
                palette(page, "New Zone")
                page.wait_for_timeout(400)
                shoot(page, "7-chair-no-new-zone")
                ctx.close()

                # The proposal boards: the product with the proposed list.
                writes.clear()
                ctx, page = open_page(canvas_url)
                to_list(page)
                new_zone(page)
                shoot(page, "1-new-zone-field-open")
                page.keyboard.type("Platform team")
                shoot(page, "2-typing")
                page.keyboard.press("Enter")
                page.locator("input.desk-zone-rename").wait_for(state="detached", timeout=10_000)
                page.wait_for_timeout(500)
                shoot(page, "3-enter-committed")
                facts[f"3-enter-committed-{width}"]["hub_names"] = sorted(
                    d["name"] for d in api(page, "GET", "/api/directories")["body"]["directories"])

                new_zone(page)
                page.keyboard.press("End")
                page.keyboard.type(" draft")
                page.keyboard.press("Escape")
                page.locator("input.desk-zone-rename").wait_for(state="detached", timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, "4-escape-kept-default")

                # Refused: name the open field "Inbox" (a seeded zone) -> the hub's 409.
                new_zone(page)
                page.keyboard.type("Inbox")
                page.keyboard.press("Enter")
                page.locator("[data-testid=zone-name-refused]").wait_for(timeout=10_000)
                page.wait_for_timeout(300)
                shoot(page, "5-refused-name-taken")
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)

                # F2 on an existing zone row (focus its name, press F2).
                page.get_by_role("button", name="Platform team zone").first.focus()
                page.keyboard.press("F2")
                page.locator("input.desk-zone-rename").wait_for(timeout=15_000)
                page.wait_for_timeout(300)
                shoot(page, "6-f2-rename-existing")
                page.keyboard.press("Escape")
                page.locator("input.desk-zone-rename").wait_for(state="detached", timeout=15_000)

                # Board 8 (MISSED) — a long name, committed: how the row shows it.
                new_zone(page)
                page.keyboard.type(LONG_NAME)
                shoot(page, "8a-long-name-typing")
                page.keyboard.press("Enter")
                page.locator("input.desk-zone-rename").wait_for(state="detached", timeout=15_000)
                page.wait_for_timeout(500)
                shoot(page, "8b-long-name-committed")

                # Board 9 (MISSED) — a name of spaces only, then Enter.
                new_zone(page)
                puts_before = sum(1 for w in writes if w["method"] == "PUT")
                page.keyboard.type("   ")
                page.keyboard.press("Enter")
                page.wait_for_timeout(800)
                shoot(page, "9-spaces-only")
                facts[f"9-spaces-only-{width}"]["puts_added"] = sum(1 for w in writes if w["method"] == "PUT") - puts_before

                # Board 10 (MISSED) — two fast New Zone presses on the list.
                palette(page, "New Zone")
                page.locator("[id='desk-palette-option-desk.new-zone']").click()
                palette(page, "New Zone")
                page.locator("[id='desk-palette-option-desk.new-zone']").click()
                page.locator("input.desk-zone-rename").wait_for(timeout=30_000)
                page.wait_for_timeout(6000)
                shoot(page, "10-two-fast-presses")
                page.keyboard.press("Escape")
                ctx.close()

                # Clean the desk for the next width.
                ctx, page = open_page(hub_url)
                for d in api(page, "GET", "/api/directories")["body"]["directories"]:
                    if d["name"].startswith("New zone") and d["name"] != "New zone" or d["name"] in ("Platform team", LONG_NAME):
                        api(page, "DELETE", f"/api/directories/{d['id']}")
                ctx.close()
            browser.close()
    finally:
        vite.terminate()
        hub.terminate()
        try:
            hub.wait(timeout=10)
        except Exception:
            hub.kill()
    (SHOTS / "facts.json").write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n")
    print("facts:", SHOTS / "facts.json")


if __name__ == "__main__":
    main()
