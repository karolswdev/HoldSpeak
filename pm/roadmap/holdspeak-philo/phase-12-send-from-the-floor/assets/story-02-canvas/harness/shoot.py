"""PHILO-12-02 canvases F-J: Send from the Floor.

Everything is live except the stated shim (harness/p12.ts): a REAL hub
(scripts/graph_walk.py serve) on an isolated HOME (tempfile.mkdtemp, removed
when the run ends), seeded through its real HTTP routes (rig.py) and, for the
records no route makes, through the product's DB layer (seed_db.py); and the
PRODUCT app served by vite with the proposal seats (harness/vite.config.mjs).
Nothing leaves the machine: the stand-in destinations' Send is answered by the
shim; the real folder destination writes into the run's temp folder.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python pm/roadmap/holdspeak-philo/phase-12-send-from-the-floor/assets/story-02-canvas/harness/shoot.py

Shots: ../shots/<board>-<width>.png at 1440x900 and 393x852 (device scale 2);
facts.json beside them. Each width runs on its own hub and HOME.
ONLY_WIDTH=393 limits the run to one width. Exit 2 on a failed fence.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig  # noqa: E402

CANVAS = HERE.parent
SHOTS = CANVAS / "shots"
REPO = HERE.parents[6]
WEB = REPO / "web"
PY = os.environ.get("CANVAS_PYTHON") or str(REPO / ".venv/bin/python")
ALL_WIDTHS = [(1440, 900), (393, 852)]
WIDTHS = [w for w in ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
TOKEN = rig.TOKEN


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, headers: dict[str, str] | None = None, timeout: float = 120) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=2) as r:
                if r.status < 500:
                    return
        except Exception:
            time.sleep(0.4)
    raise RuntimeError(f"not up: {url}")


# ── the rendered facts of one board ─────────────────────────────────────────
FACTS = r"""() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const menus = [...document.querySelectorAll('[role=menu]')].filter(vis);
  const rows = menus.flatMap((m) => [...m.querySelectorAll(':scope > [role^=menuitem], :scope > .btn')]).filter(vis);
  const tag = document.querySelector('.desk-drop-verb');
  const wells = [...document.querySelectorAll('[data-testid=send-well]')].filter(vis);
  const picked = [...document.querySelectorAll('[data-testid=send-open]')].filter(vis).map((e) => e.dataset.destination);
  // The proposal's own text: menu rows, the tag, the artifact window's well and verbs.
  const prop = [...menus, ...(tag ? [tag] : []), ...document.querySelectorAll('[data-p12]')];
  const small = [];
  for (const root of prop) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const t = n.textContent.trim(); if (!t || /^[●○◆▸▾»◂▷✓✗·\s]+$/.test(t)) continue;
      const el = n.parentElement; if (!vis(el)) continue;
      const fs = parseFloat(getComputedStyle(el).fontSize); if (fs < 12) small.push({ text: t.slice(0, 30), fs });
    }
  }
  const raw = prop.flatMap((r) => [...(r.matches('button') ? [r] : []), ...r.querySelectorAll('button')])
    .filter((b) => vis(b) && !String(b.className).includes('btn')).map((b) => (b.innerText || '').trim().slice(0, 30));
  const propText = prop.map((e) => e.innerText || '').join('\n');
  return {
    menus: menus.map((m) => m.getAttribute('aria-label')),
    menu_rows: rows.map((r) => ({ text: r.innerText.replace(/\s+/g, ' ').trim(), h: Math.round(r.getBoundingClientRect().height), ghost: r.getAttribute('aria-disabled') === 'true' })),
    tag: tag ? tag.innerText.trim() : null,
    tag_has_egress_chip: !!(tag && tag.querySelector('.gadget-chip-egress')),
    windows: [...document.querySelectorAll('.desk-window')].filter(vis).map((w) => w.getAttribute('aria-label') || ''),
    wells: wells.map((w) => w.dataset.doc),
    picked,
    well_egress: [...document.querySelectorAll('[data-testid=send-open] .gadget-chip-egress')].filter(vis).map((e) => e.innerText.trim()),
    outcomes: [...document.querySelectorAll('[data-testid=send-sent], [data-testid=preview-refused], [data-testid=send-refused]')].filter(vis).map((e) => e.innerText.replace(/\s+/g, ' ').trim()),
    small_text: small,
    raw_buttons: raw,
    zero_counter: /(^|\s)0 [A-Z]{2,}/.test(propText),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
  };
}"""

VISIBLE = r"""(sels) => sels.map((sel) => {
  const els = [...document.querySelectorAll(sel)].filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.height; });
  if (!els.length) return {sel, ok: false, why: 'absent'};
  const e = els[0]; const r = e.getBoundingClientRect();
  let top = 0, left = 0, bottom = innerHeight, right = innerWidth;
  for (let a = e.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowY + ' ' + cs.overflowX)) {
      const ar = a.getBoundingClientRect();
      top = Math.max(top, ar.top); bottom = Math.min(bottom, ar.bottom); left = Math.max(left, ar.left); right = Math.min(right, ar.right);
    }
  }
  const band = Math.min(r.height, 40);
  const inside = r.top >= top - 1 && r.top + band <= bottom + 1 && r.left >= left - 1 && r.right <= right + 1;
  const pts = [[r.left + r.width / 2, r.top + band / 2], [r.left + 2, r.top + 2], [r.right - 2, r.top + band - 2]];
  // A layer that takes no pointer (the drop tag) is checked by its box only.
  const hit = getComputedStyle(e).pointerEvents === 'none' || pts.every(([x, y]) => { const h = document.elementFromPoint(x, y); return !!h && (e.contains(h) || h.contains(e)); });
  return {sel, ok: inside && hit, why: inside ? (hit ? '' : 'covered') : 'clipped', text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60)};
})"""

# Every menu row at 393 owns its strip: nine points inside the row are the row (UX-CANON C,
# the chrome strip rule: each row at least 44 px high, measured, no halo).
ROW_POINTS = r"""() => {
  const rows = [...document.querySelectorAll('[role=menu] > [role^=menuitem]')].filter((r) => r.getBoundingClientRect().height);
  return rows.map((r) => { const b = r.getBoundingClientRect();
    const xs = [b.left + 2, b.left + b.width / 2, b.right - 2], ys = [b.top + 1, b.top + b.height / 2, b.bottom - 1];
    let own = 0; for (const x of xs) for (const y of ys) { const h = document.elementFromPoint(x, y); if (h && r.contains(h)) own++; }
    return { text: r.innerText.replace(/\s+/g, ' ').trim().slice(0, 30), h: Math.round(b.height), own }; });
}"""


def run(width: int, height: int) -> tuple[list[str], dict]:
    home = tempfile.mkdtemp(prefix="philo12-02-canvas-")
    outdir = tempfile.mkdtemp(prefix="p12-", dir="/tmp")
    folder = f"{outdir}/Reports"
    Path(folder).mkdir()
    hub_port, canvas_port = free_port(), free_port()
    hub = f"http://127.0.0.1:{hub_port}"
    env = {**os.environ, "HOME": home, "PYTHONPATH": str(REPO), "HOLDSPEAK_PEOPLE_KEYSTORE_FILE": f"{home}/people.key"}
    facts: dict = {}
    fails: list[str] = []
    errors: list[str] = []
    procs: list[subprocess.Popen] = []
    phone = width <= 420
    try:
        seeded = subprocess.run([PY, str(HERE / "seed_db.py")], cwd=REPO, env=env, capture_output=True, text=True, timeout=180)
        if seeded.returncode:
            raise RuntimeError(f"seed_db failed: {seeded.stderr[-2000:]}")
        procs.append(subprocess.Popen([PY, "scripts/graph_walk.py", "serve", "--port", str(hub_port), "--token", TOKEN],
                                      cwd=REPO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        procs.append(subprocess.Popen([str(WEB / "node_modules/.bin/vite"), "--config", str(HERE / "vite.config.mjs")], cwd=WEB,
                                      env={**os.environ, "HUB": hub, "CANVAS_PORT": str(canvas_port), "CANVAS_MODE": "proposal"},
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        wait_http(f"{hub}/api/projects", {"Authorization": f"Bearer {TOKEN}"})
        wait_http(f"http://127.0.0.1:{canvas_port}/")
        seed = rig.seed_hub(hub, folder, brief=False)   # I4 first: no brief yet
        facts["_seed"] = seed
        print(width, "seed", json.dumps(seed), flush=True)
        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, has_touch=phone)
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.on("console", lambda m: errors.append(f"console: {m.text[:200]}")
                    if m.type == "error" and "status of 4" not in m.text and "Failed to fetch" not in m.text else None)
            try:
                boards(page, width, hub, canvas_port, seed, facts, fails)
            except Exception as exc:
                import traceback
                traceback.print_exc()
                fails.append(f"CRASH at width {width}: {str(exc).splitlines()[0][:300]}")
                try:
                    page.screenshot(path=str(SHOTS / f"_crash-{width}.png"))
                except Exception:
                    pass
            browser.close()
    finally:
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except Exception:
                p.kill()
        shutil.rmtree(outdir, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)   # law: a run removes its own scratch HOME
        facts[f"_browser_errors_{width}"] = errors
    return fails, facts


def boards(page, width: int, hub: str, port: int, seed: dict, facts: dict, fails: list[str]) -> None:
    phone = width <= 420
    height = page.viewport_size["height"]

    def boot():
        page.locator(".chair").wait_for(timeout=120_000)
        for _ in range(80):
            cl = page.get_by_role("button", name="Continue later", exact=True)
            if not cl.count():
                break
            try:
                cl.first.click(timeout=2000)
            except Exception:
                pass
            page.wait_for_timeout(700)
        page.wait_for_timeout(1200)

    def ev(js: str, arg=None):
        return page.evaluate(js, arg)

    def close_menu():
        """An outside pointer-down closes every desk menu (the species' dismissal rule)."""
        for i in range(4):
            if not page.locator("[role=menu]").count():
                return
            if i < 2:
                ev("() => document.body.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}))")
            else:
                page.keyboard.press("Escape")
            page.wait_for_timeout(400)
        raise RuntimeError("a menu did not close")

    def floor():
        """The Floor: at 1440 the spatial world; at 393 the list (the phone's default past 16 objects)."""
        close_all()
        # The Dock's one toggle reads `Floor` while the Chair is up (and `Chair` on the Floor).
        for _ in range(3):
            door = page.locator("button.desk-dock-launch[aria-label=Floor]")
            if not door.count() or not page.locator(".chair").count():
                break
            door.first.click()
            page.wait_for_timeout(2000)
        if page.locator(".chair").count():
            raise RuntimeError("the Floor did not open")
        page.locator(".desk-world-canvas, .desk-listmode").first.wait_for(timeout=30_000)
        page.wait_for_timeout(2500)

    def close_all():
        ev("() => window.__p12Open.closeAll()")
        close_menu()
        page.wait_for_timeout(500)

    def probe(ref: str) -> dict:
        for _ in range(40):
            hit = next((o for o in ev("() => window.__hsWorldProbe ? window.__hsWorldProbe() : []") if o["ref"] == ref or o["id"] == ref), None)
            if hit:
                return hit
            page.wait_for_timeout(250)
        raise RuntimeError(f"not on the Floor: {ref}")

    def shoot(board: str, named: list[str] | None = None, checks: dict | None = None, extra: dict | None = None,
              rows44: bool = False):
        page.wait_for_timeout(500)
        key = f"{board}-{width}"
        css = []
        for i, sel in enumerate(named or []):
            if sel == ".desk-world-canvas":
                continue   # the GL world is behind its own a11y layer; its icons are checked by the probe
            loc = page.locator(sel)
            if not loc.count():
                css.append(f"[data-absent-{i}]")
                continue
            loc.first.evaluate("(e, n) => { e.dataset.mark = n; }", f"m{i}")
            css.append(f"[data-mark='m{i}']")
        vis = ev(VISIBLE, css)
        ev("() => document.querySelectorAll('[data-mark]').forEach((e) => e.removeAttribute('data-mark'))") if False else None
        page.screenshot(path=str(SHOTS / f"{key}.png"))
        ev("() => document.querySelectorAll('[data-mark]').forEach((e) => e.removeAttribute('data-mark'))")
        f = ev(FACTS)
        f["named"] = vis
        if phone and rows44:
            f["row_points"] = ev(ROW_POINTS)
        if extra:
            f.update(extra)
        facts[key] = f
        for v, sel in zip(vis, [n for n in (named or []) if n != ".desk-world-canvas"]):
            v["sel"] = sel
            if not v["ok"]:
                fails.append(f"{key}: off screen {v}")
        law = {
            "no tag says Send": not (f["tag"] and "send" in f["tag"].lower().replace("preview for", "")),
            "no egress chip on the tag": not f["tag_has_egress_chip"],
            "no raw button in the proposal": not f["raw_buttons"],
            "no text under 12px in the proposal": not f["small_text"],
            "no counter of zero": not f["zero_counter"],
            "no modal": not f["modal"],
            "no horizontal overflow": not f["h_overflow"],
        }
        if phone and rows44:
            law["menu rows 44 px at 393, nine points owned"] = all(r["h"] >= 44 and r["own"] == 9 for r in f["row_points"])
        for name, ok in {**law, **(checks or {})}.items():
            if not ok:
                fails.append(f"{key}: {name}")
        print(key, "menus", f["menus"], "tag", f["tag"], "wells", f["wells"], "picked", f["picked"],
              "hidden", [v["sel"][-40:] for v in vis if not v["ok"]], flush=True)
        return f

    # ── menus: the spatial right-click (1440) or the touch long-press on a list row (393) ──
    def touch_long_press(x: float, y: float):
        cdp = page.context.new_cdp_session(page)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
        page.wait_for_timeout(750)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(400)

    def row_of(title: str) -> str:
        return f".desk-listmode .desk-sortable-table-row:has(.desk-list-name-cell:text-is('{title}')), .desk-listmode .desk-sortable-table-row:has(.desk-sortable-table-open:has-text('{title}'))"

    def object_menu(ref: str, title: str):
        """Open the object's menu on its own entry point: right-click at 1440, a touch long-press at 393."""
        if phone:
            row = page.locator(row_of(title)).first
            # The rig's mouse cursor rests where the last click was; a panel that opens under it
            # would take its hover intent. A phone has no cursor: park it off the panel first.
            page.mouse.move(2, 2)
            row.evaluate("(e) => e.scrollIntoView({block: 'center'})")
            page.wait_for_timeout(300)
            b = row.bounding_box()
            touch_long_press(b["x"] + 60, b["y"] + b["height"] / 2)
        else:
            o = probe(ref)
            page.mouse.click(o["x"], o["y"] - 10, button="right")
        page.locator("[role=menu]").first.wait_for(timeout=10_000)
        page.wait_for_timeout(300)

    def list_menu(title: str):
        """The list's row menu at 1440 (the mouse right-click; the list at 1440 is a desktop list)."""
        row = page.locator(row_of(title)).first
        row.scroll_into_view_if_needed()
        b = row.bounding_box()
        page.mouse.click(b["x"] + 120, b["y"] + b["height"] / 2, button="right")
        page.locator("[role=menu]").first.wait_for(timeout=10_000)
        page.wait_for_timeout(300)

    def open_sub():
        sub = page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Send to')").first
        sub.click()
        page.wait_for_timeout(500)

    def menu_pick(name: str):
        page.locator(f"[role=menu] [role=menuitem]:has-text('{name}')").last.click()
        page.wait_for_timeout(300)

    def send_to(ref: str, title: str, dest: str):
        object_menu(ref, title)
        open_sub()
        menu_pick(dest)

    def bar_send(ref: str, dest: str):
        """The menu bar (Object at 1440, the compact Go at 393), the object selected: the entry point
        that stays reachable while a window covers the Floor or the list."""
        ev("(r) => window.__p12Open.select(r)", ref)
        page.wait_for_timeout(300)
        page.locator(f".desk-verbbar [data-menu-id={'go' if phone else 'object'}] button").first.click()
        page.wait_for_timeout(600)
        sub = page.locator("[role=menu] [aria-haspopup=menu]:has-text('Send to')").first
        sub.scroll_into_view_if_needed()
        sub.click()
        page.wait_for_timeout(500)
        menu_pick(dest)
        ev("() => window.__p12Open.clearSelection()")

    def drag(ref: str, target_ref: str, release: bool = True):
        a, t = probe(ref), probe(target_ref)
        page.mouse.move(a["x"], a["y"] - 10)
        page.mouse.down()
        steps = 14
        for i in range(1, steps + 1):
            page.mouse.move(a["x"] + (t["x"] - a["x"]) * i / steps, a["y"] - 10 + (t["y"] - a["y"]) * i / steps)
            page.wait_for_timeout(40)
        page.wait_for_timeout(400)
        page.mouse.move(t["x"] + 2, t["y"] + 50)   # low in the target's cell: its lit art stays in view; the rule re-reads a landed fact
        page.wait_for_timeout(400)
        if release:
            page.mouse.up()
            page.wait_for_timeout(300)

    def well(dest: str) -> str:
        return f"[data-testid=send-open][data-destination='{dest}']"

    def wait_preview(dest: str):
        page.locator(f"{well(dest)} [data-testid=send-preview], {well(dest)} [data-testid=preview-refused]").first.wait_for(timeout=20_000)
        page.wait_for_timeout(600)

    def seat(sel: str, block: str = "center"):
        loc = page.locator(sel)
        if loc.count():
            loc.first.evaluate("(e, b) => e.scrollIntoView({block: b})", block)
        page.wait_for_timeout(300)

    def seat_row(dest: str):
        """The picked row's head at the top of its window: the pick, its preview and Send in view."""
        seat(f"[data-testid=destination-row]:has([data-destination='{dest}'])", "start")

    def place(item_id: str, x: float, y: float):
        """Where he would drag it (a Floor position, saved per browser): the rig sets it through the store."""
        ev("([i, x, y]) => { const s = window.__p12Store(); s.setPosition(i, {x, y}); s.persistPositions(); }", [item_id, x, y])

    dec, pid, bare, art = seed["decision"], seed["project"], seed["bare_project"], "art-cutover-reqs"
    DEC_T, PROJ_T, BARE_T = "Freeze the old ledger on Nov 3", rig.PROJECT, rig.BARE_PROJECT

    page.goto(f"http://127.0.0.1:{port}/?token={TOKEN}", wait_until="load")
    boot()
    ev("() => window.__p12Fixture.standins(['slack', 'github'])")
    floor()
    if not phone:
        # Clear lines of sight for the drags (inherited: the default grid puts Vendor call under a drawer).
        place("m-bare", 0.86, 0.80)
        place(dec, 0.13, 0.62)
        page.wait_for_timeout(800)

    # ── I4: no brief yet -> no icon, no row ──────────────────────────────────
    shoot("I4-no-brief", [".desk-world-canvas"],
          checks={"no brief icon or row": not ev("() => !!document.querySelector('[data-obj-id=\"intelligence:brief\"]') || [...document.querySelectorAll('.desk-sortable-table-row')].some((r) => r.innerText.includes('BRIEF'))")})
    s, b = rig.hub_api(hub, "POST", "/api/brief/generate", {})
    seed["brief"] = b.get("id") if isinstance(b, dict) else None
    ev("() => window.__p12Fixture.refresh()")
    page.wait_for_timeout(1500)

    # ── F1: three destinations at the right edge; the brief icon above them (393: the list) ──
    if phone:
        seat(".desk-listmode .desk-sortable-table-row:has(.desk-sortable-table-open:has-text('BRIEF'))", "center")
        shoot("F1-destinations-column", [row_of(ev("() => window.__p12Brief()"))],
              checks={"no destination row in the list": not ev("() => [...document.querySelectorAll('.desk-sortable-table-row')].some((r) => /Team folder|Slack #leads/.test(r.innerText))")})
    else:
        icons = [probe(f"destination:{seed['folder_destination']}"), probe("destination:chd_p12_slack"), probe("destination:chd_p12_github")]
        shoot("F1-destinations-column", [".desk-world-canvas"],
              extra={"icons": icons}, checks={"one column at the right edge": all(i["x"] > width - 80 for i in icons)})

    # ── F2: a destination icon selected, its menu `Open` only; Open lands on its row in Settings ──
    if not phone:
        o = probe("destination:chd_p12_slack")
        page.mouse.click(o["x"], o["y"] - 10)
        page.mouse.click(o["x"], o["y"] - 10, button="right")
        page.locator("[role=menu]").first.wait_for(timeout=10_000)
        f = shoot("F2-destination-menu", ["[role=menu]"])
        if [r["text"] for r in f["menu_rows"]] != ["▷ Open"] and [r["text"] for r in f["menu_rows"]] != ["Open"]:
            fails.append(f"F2-{width}: the destination menu is not Open only: {f['menu_rows']}")
        menu_pick("Open")
    else:
        ev("() => window.__p12OpenIcon({kind: 'destination', id: 'destination:chd_p12_slack'})")
        page.locator("[data-testid=destinations]").wait_for(timeout=20_000)
        page.wait_for_timeout(1500)
        seat("[data-testid=dest-row]:has([data-destination='Slack #leads'])", "start")
        shoot("F2-destination-menu", ["[data-testid=dest-row]:has([data-destination='Slack #leads'])"])   # the phone has no icon: Settings is its door
    page.locator("[data-testid=dest-row]:has([data-destination='Slack #leads'])").wait_for(timeout=20_000)
    page.wait_for_timeout(1200)
    seat("[data-testid=dest-row]:has([data-destination='Slack #leads'])", "start")
    shoot("F2b-open-lands-on-row", ["[data-testid=dest-row]:has([data-destination='Slack #leads'])"],
          checks={"the Slack row is open, not the add form": ev("() => !document.querySelector('[data-testid=dest-form]') && !!document.querySelector('[data-testid=dest-open], [data-testid=dest-row][aria-expanded=true]')")})
    close_all()
    floor()

    # ── F4: the decision's own sprite beside a note; F5: the six channels ─────
    if not phone:
        page.mouse.click(*[probe(f"decision:{dec}")[k] for k in ("x", "y")])
        shoot("F4-decision-sprite", [".desk-world-canvas"],
              extra={"decision_sprite": ev("(r) => window.__p12SpriteOf(r)", f"decision:{dec}")},
              checks={"the decision wears its own sprite": "p12/decision" in ev("(r) => window.__p12SpriteOf(r)", f"decision:{dec}")})
        page.mouse.click(5, height // 2)
    else:
        page.locator(row_of(DEC_T)).first.scroll_into_view_if_needed()
        shoot("F4-decision-sprite", [row_of(DEC_T)])
    ev("() => window.__p12Fixture.standins(['slack', 'github', 'jira', 'confluence', 'email'])")
    page.wait_for_timeout(1500)
    if not phone:
        shoot("F5-six-channels", [".desk-world-canvas"])
    else:
        object_menu(f"decision:{dec}", DEC_T)
        open_sub()
        shoot("F5-six-channels", ["[role=menu] .desk-menu-back"], rows44=True)
        close_menu()
    ev("() => window.__p12Fixture.standins(['slack', 'github'])")
    page.wait_for_timeout(1200)

    # ── H: `Send to ▸` ───────────────────────────────────────────────────────
    object_menu(f"decision:{dec}", DEC_T)
    shoot("H1-decision-menu", ["[role=menu] [aria-haspopup=menu]:has-text('Send to')"], rows44=True)
    open_sub()
    f = shoot("H2-send-to-open", ["[role=menu] [role=menuitem]:has-text('Slack #leads')"], rows44=True)
    if phone and not ev("() => !!document.querySelector('[role=menu] .desk-menu-back')"):
        fails.append(f"H2-{width}: the submenu does not replace the panel with a back row")
    close_menu()
    page.wait_for_timeout(300)
    if not phone:
        # H2 at 1440: the same row menu in the LIST (the list view at desktop width).
        ev("() => window.__p12Open.view('list')")
        page.locator(".desk-listmode").wait_for(timeout=10_000)
        page.wait_for_timeout(1200)
        list_menu(DEC_T)
        open_sub()
        shoot("H2b-list-send-to", ["[role=menu] [role=menuitem]:has-text('Slack #leads')"])
        close_menu()
        # H6 at 1440: the brief row in the list carries Send to.
        list_menu(ev("() => window.__p12Brief()"))
        open_sub()
        shoot("H6-brief-row-send-to", ["[role=menu] [role=menuitem]:has-text('Slack #leads')"])
        close_menu()
        ev("() => window.__p12Open.view('icons')")
        page.wait_for_timeout(1500)
        floor()
    else:
        object_menu("intelligence:brief", ev("() => window.__p12Brief()"))
        open_sub()
        shoot("H6-brief-row-send-to", ["[role=menu] [role=menuitem]:has-text('Slack #leads')"], rows44=True)
        close_menu()
    # H4: a note: no Send to (withheld).
    object_menu("note:hs-seed-prompt-weekly-update", "Weekly update")
    f = shoot("H4-note-withheld", ["[role=menu]"], rows44=True)
    if any("Send to" in r["text"] for r in f["menu_rows"]):
        fails.append(f"H4-{width}: Send to on a note")
    close_menu()
    # H5: the menu bar Object menu (1440) / the compact Go menu (393), the decision selected.
    ev("(r) => window.__p12Open.select(r)", f"decision:{dec}")
    page.wait_for_timeout(400)
    page.locator(f".desk-verbbar [data-menu-id={'go' if phone else 'object'}] button").first.click()
    page.wait_for_timeout(600)
    sub = page.locator("[role=menu] [aria-haspopup=menu]:has-text('Send to')").first
    sub.scroll_into_view_if_needed()
    sub.click()
    page.wait_for_timeout(500)
    shoot("H5-menu-bar-send-to", ["[role=menu] [role=menuitem]:has-text('Slack #leads')"], rows44=True)
    close_menu()
    ev("() => window.__p12Open.clearSelection()")
    page.wait_for_timeout(300)

    # H7: a meeting whose summary read is loading (CHECKING), then failed (CAN'T CHECK); a pick on failed opens its window.
    ev("() => window.__p12Fixture.hold('meeting:m-sync', 'loading')")
    object_menu("meeting:m-sync", "Ledger cutover sync")
    if not phone:
        open_sub()
    shoot("H7a-read-loading", ["[role=menu] [role=menuitem]:has-text('CHECKING')"], rows44=True)
    close_menu()
    ev("() => window.__p12Fixture.hold('meeting:m-sync', 'failed')")
    object_menu("meeting:m-sync", "Ledger cutover sync")
    open_sub()
    shoot("H7b-read-failed", ["[role=menu] [role=menuitem]:has-text(\"CAN'T CHECK\")"], rows44=True)
    menu_pick("Team folder")
    page.locator(".desk-window [data-testid=send-well]").first.wait_for(timeout=20_000)
    page.wait_for_timeout(1500)
    shoot("H7c-failed-pick-opens-window", [well("Team folder")] if page.locator(well("Team folder")).count() else [".desk-window"])
    ev("() => window.__p12Fixture.hold('meeting:m-sync', null)")
    close_all()
    floor()

    # ── G: the drop (1440) and its 393 end state by the menu ──────────────────
    slack, fold = "destination:chd_p12_slack", f"destination:{seed['folder_destination']}"
    if not phone:
        drag(f"decision:{dec}", slack, release=False)
        shoot("G1-decision-held-over-slack", [".desk-drop-verb"],
              checks={"tag reads Preview for Slack #leads": ev("() => document.querySelector('.desk-drop-verb')?.innerText") == "Preview for Slack #leads"})
        page.mouse.up()
    else:
        object_menu(f"decision:{dec}", DEC_T)
        open_sub()
        shoot("G1-decision-held-over-slack", ["[role=menu] [role=menuitem]:has-text('Slack #leads')"], rows44=True)
        menu_pick("Slack #leads")
    wait_preview("Slack #leads")
    seat_row("Slack #leads")
    shoot("G2-released-preview-open", [f"{well('Slack #leads')} [data-testid=send-verb]", f"{well('Slack #leads')} .gadget-chip-egress"],
          checks={"Slack picked": True}, extra={"sends_before_press": rig.hub_api(hub, "GET", "/api/channels/sends")[1]})
    # G7: a second pick on the already-open window: the pick changes in place.
    nwin = len(ev(FACTS)["windows"])
    if not phone:
        drag(f"decision:{dec}", fold)
    else:
        bar_send(f"decision:{dec}", "Team folder")   # the window covers the list at 393
    wait_preview("Team folder")
    seat_row("Team folder")
    f = shoot("G7-second-pick-in-place", [f"{well('Team folder')} [data-testid=send-verb]"],
              checks={"the pick changed in place": True})
    if len(f["windows"]) != nwin or f["picked"] != ["Team folder"]:
        fails.append(f"G7-{width}: windows {nwin}->{len(f['windows'])}, picked {f['picked']}")
    # back to Slack for G3 (the pick, pushed again)
    if not phone:
        drag(f"decision:{dec}", slack)
    else:
        bar_send(f"decision:{dec}", "Slack #leads")
    wait_preview("Slack #leads")
    page.locator(f"{well('Slack #leads')} [data-testid=send-verb]").click()
    page.locator(f"{well('Slack #leads')} [data-testid=send-sent]").wait_for(timeout=20_000)
    seat_row("Slack #leads")
    shoot("G3-sent", [f"{well('Slack #leads')} [data-testid=send-sent]"],
          extra={"shim_sends": ev("() => window.__p12Fixture.sends().map((s) => [s.document_ref, s.destination_name, s.state])")},
          checks={"the send names the decision": any(s[0] == f"desk_decision:{dec}" for s in ev("() => window.__p12Fixture.sends().map((s) => [s.document_ref, s.destination_name])"))})
    close_all()
    floor()

    # G4: refusals on the tag (1440); at 393 the menu withholds Send to.
    if not phone:
        drag("meeting:m-bare", slack, release=False)
        n0 = len(ev(FACTS)["windows"])
        shoot("G4-no-summary-tag", [".desk-drop-verb"], checks={"tag NO SUMMARY": ev("() => document.querySelector('.desk-drop-verb')?.innerText") == "NO SUMMARY"})
        page.mouse.up()
        page.wait_for_timeout(1200)
        if len(ev(FACTS)["windows"]) != n0:
            fails.append(f"G4-{width}: release on a refusal opened a window")
        drag(f"project:{bare}", slack, release=False)
        shoot("G4b-no-published-update-tag", [".desk-drop-verb"],
              checks={"tag NO PUBLISHED UPDATE": ev("() => document.querySelector('.desk-drop-verb')?.innerText") == "NO PUBLISHED UPDATE"})
        page.mouse.up()
        ev("() => window.__p12Fixture.parkQuietly('github')")
        drag(f"decision:{dec}", "destination:chd_p12_github", release=False)
        shoot("G4c-parked-tag", [".desk-drop-verb"], checks={"tag PARKED": ev("() => document.querySelector('.desk-drop-verb')?.innerText") == "PARKED"})
        page.mouse.up()
    else:
        # The first open starts the read (CHECKING); the menu opened again after it landed withholds Send to (N2).
        object_menu("meeting:m-bare", "Vendor call")
        close_menu()
        page.wait_for_timeout(1200)
        object_menu("meeting:m-bare", "Vendor call")
        f = shoot("G4-no-summary-tag", ["[role=menu]"], rows44=True)
        if any("Send to" in r["text"] for r in f["menu_rows"]):
            fails.append(f"G4-{width}: Send to on a meeting with no summary")
        close_menu()
        object_menu(f"project:{bare}", BARE_T)
        close_menu()
        page.wait_for_timeout(1200)
        object_menu(f"project:{bare}", BARE_T)
        f = shoot("G4b-no-published-update-tag", ["[role=menu]"], rows44=True)
        if any("Send to" in r["text"] for r in f["menu_rows"]):
            fails.append(f"G4b-{width}: Send to on a project with no published update")
        close_menu()
        ev("() => window.__p12Fixture.parkQuietly('github')")
        ev("() => window.__p12Fixture.refresh()")
        page.wait_for_timeout(800)
        object_menu(f"decision:{dec}", DEC_T)
        open_sub()
        f = shoot("G4c-parked-tag", ["[role=menu] .desk-menu-back"], rows44=True)
        if any("Ledger cutover issue" in r["text"] for r in f["menu_rows"]):
            fails.append(f"G4c-{width}: a parked destination in Send to")
        close_menu()
    ev("() => window.__p12Fixture.refresh()")
    page.wait_for_timeout(800)

    # G5: a meeting with a summary: the meeting window, form Summary, the destination picked. G8: Digest keeps it.
    if not phone:
        drag("meeting:m-sync", slack)
    else:
        send_to("meeting:m-sync", "Ledger cutover sync", "Slack #leads")
    wait_preview("Slack #leads")
    seat("[data-testid=doc-forms]", "start")
    shoot("G5-meeting-summary-picked", ["[data-testid=doc-forms]", f"{well('Slack #leads')} [data-testid=send-verb]"],
          checks={"the well is the summary": any(w.startswith("meeting_summary:") for w in ev(FACTS)["wells"])})
    page.locator("[data-testid=doc-forms] select").select_option("meeting_digest")
    wait_preview("Slack #leads")
    seat("[data-testid=doc-forms]", "start")
    f = shoot("G8-digest-keeps-destination", ["[data-testid=doc-forms]", f"{well('Slack #leads')} [data-testid=send-verb]"])
    if f["picked"] != ["Slack #leads"] or not any(w.startswith("meeting_digest:") for w in f["wells"]):
        fails.append(f"G8-{width}: digest wells {f['wells']} picked {f['picked']}")
    page.locator("[data-testid=doc-forms] select").select_option("meeting_summary")
    close_all()
    floor()

    # G6: a project: the Room at the Update posture on its latest published update, the destination picked.
    latest = seed["updates"][-1]
    if not phone:
        drag(f"project:{pid}", fold)
    else:
        send_to(f"project:{pid}", PROJ_T, "Team folder")
    page.locator(f"[data-testid=send-well][data-doc='project_update:{latest}'] {well('Team folder')}").wait_for(timeout=30_000)
    wait_preview("Team folder")
    seat_row("Team folder")
    shoot("G6-project-latest-update", [f"{well('Team folder')} [data-testid=send-verb]"],
          checks={"the latest published update": f"project_update:{latest}" in ev(FACTS)["wells"]})
    # G9: the Room already open on the OLDER update; a pick switches it to the linked (latest) update.
    older = seed["updates"][0]
    ev("([p, u]) => window.__p12OpenRoomUpdate(p, u)", [pid, older])   # he opened the older update in the Room
    page.locator(f"[data-testid=send-well][data-doc='project_update:{older}']").wait_for(timeout=20_000)
    page.wait_for_timeout(800)
    seat(f"[data-testid=send-well][data-doc='project_update:{older}']", "start")
    shoot("G9a-room-on-older-update", [f"[data-testid=send-well][data-doc='project_update:{older}'] [data-testid=destination-row]"])
    # The open Room covers the project's icon (1440) and the list (393): the menu bar, the project selected.
    bar_send(f"project:{pid}", "Slack #leads")
    page.locator(f"[data-testid=send-well][data-doc='project_update:{latest}'] {well('Slack #leads')}").wait_for(timeout=30_000)
    wait_preview("Slack #leads")
    seat_row("Slack #leads")
    shoot("G9b-room-switched-to-linked-update", [f"{well('Slack #leads')} [data-testid=send-verb]"],
          checks={"switched to the linked update": f"project_update:{latest}" in ev(FACTS)["wells"]})
    close_all()
    floor()

    # ── I: the brief ─────────────────────────────────────────────────────────
    btitle = ev("() => window.__p12Brief()")
    if not phone:
        page.mouse.click(*[probe("intelligence:brief")[k] for k in ("x", "y")])
        shoot("I1-brief-icon", [".desk-world-canvas"], extra={"brief_label": btitle},
              checks={"BRIEF <day>": btitle.startswith("BRIEF ")})
        o = probe("intelligence:brief")
        page.mouse.dblclick(o["x"], o["y"] - 10)
    else:
        seat(row_of(btitle), "center")
        shoot("I1-brief-icon", [row_of(btitle)], extra={"brief_label": btitle}, checks={"BRIEF <day>": btitle.startswith("BRIEF ")})
        page.locator(row_of(btitle)).first.locator(".desk-sortable-table-open").click()
    page.locator("[data-testid=send-well][data-doc^='monday_brief:']").first.wait_for(timeout=30_000)
    page.wait_for_timeout(1200)
    shoot("I2-brief-opened", [".desk-window [data-testid=send-well]"] if not phone else [".desk-window"],
          checks={"the handed brief id": f"monday_brief:{seed['brief']}" in ev(FACTS)["wells"]})
    close_all()
    floor()
    if not phone:
        drag("intelligence:brief", slack)
    else:
        send_to("intelligence:brief", btitle, "Slack #leads")
    wait_preview("Slack #leads")
    seat_row("Slack #leads")
    shoot("I3-brief-dropped", [f"{well('Slack #leads')} [data-testid=send-verb]"],
          checks={"the brief's exact id": f"monday_brief:{seed['brief']}" in ev(FACTS)["wells"]})
    close_all()
    floor()

    # ── J: the artifact ──────────────────────────────────────────────────────
    ev("(r) => window.__p12Open.open('artifact', r)", art)
    page.locator("[data-seat=artifact] [data-testid=send-well]").wait_for(timeout=20_000)
    page.wait_for_timeout(1000)
    seat("[data-seat=artifact]", "start")
    raw_art = ev("() => [...[...document.querySelectorAll('.desk-window')].pop().querySelectorAll('button')].filter((b) => !/(^|\\s)btn/.test(b.className)).map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim())")
    shoot("J1-artifact-window-well", ["[data-seat=artifact] [data-testid=destination-row]"], extra={"raw_buttons_in_artifact_window": raw_art},
          checks={"no raw button in the artifact window": not raw_art})
    close_all()
    floor()
    if not phone:
        drag(f"artifact:{art}", fold)
    else:
        send_to(f"artifact:{art}", "Cutover requirements", "Team folder")
    wait_preview("Team folder")
    body = page.locator(f"{well('Team folder')} [data-testid=send-preview-body]").inner_text()
    seat_row("Team folder")
    shoot("J2-artifact-dropped-on-folder", [f"{well('Team folder')} [data-testid=send-verb]"],
          extra={"preview_body": body[:400]},
          checks={"no synthesis footer in the preview": "Source windows" not in body and "win-7f3a2c" not in body})
    page.locator(f"{well('Team folder')} [data-testid=send-verb]").click()
    page.locator(f"{well('Team folder')} [data-testid=send-sent]").wait_for(timeout=20_000)
    seat_row("Team folder")
    shoot("J2b-artifact-saved", [f"{well('Team folder')} [data-testid=send-sent]"])
    close_all()

    # ── F3 / H3: no destinations (the folder parked through the real route; no stand-ins) ──
    rig.hub_api(hub, "DELETE", f"/api/channels/destinations/{seed['folder_destination']}", {"command_id": "canvas-park-1"})
    ev("() => window.__p12Fixture.standins([])")
    page.wait_for_timeout(1500)
    floor()
    shoot("F3-no-destinations", [".desk-world-canvas"],
          checks={"no destination icon": not any(o["id"].startswith("destination:") for o in ev("() => window.__hsWorldProbe ? window.__hsWorldProbe() : []"))})
    object_menu(f"decision:{dec}", DEC_T)
    open_sub()
    f = shoot("H3-add-destination", ["[role=menu] [role=menuitem]:has-text('Add destination')"], rows44=True)
    menu_pick("Add destination")
    page.locator("[data-testid=dest-form]").wait_for(timeout=20_000)
    page.wait_for_timeout(1000)
    shoot("H3b-add-destination-opens-form", ["[data-testid=dest-form]"])


def main() -> None:
    import signal
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    all_fails: list[str] = []
    path = SHOTS / "facts.json"
    for w, h in WIDTHS:
        fails, facts = run(w, h)
        all_fails += fails
        prior = json.loads(path.read_text()) if path.exists() else {}
        SHOTS.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**prior, **facts, f"_fails_{w}": fails}, indent=1, ensure_ascii=False) + "\n")
    if all_fails:
        print("FENCE FAILURES:", *all_fails, sep="\n  ", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
