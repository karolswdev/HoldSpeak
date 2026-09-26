"""PHILO-8-03 -- the closing rehearsal of the Floor jobs, through the real hub.

One real hub (the rig's ``Hub``: its own process, a fresh isolated HOME), one
Chromium page per width (1440x900 and 393x852). The owner's jobs, in order:

1. two New Zone presses with no rename between (the list);
2. the rename where he is (the list's in-row field, Enter);
3. a list delete without Undo (the row menu), after the window;
4. a list delete with Undo, read again after the window;
5. two deletes in one window (A, then B, on the list);
6. a delete, then a face change (to the Chair) inside the window.

After each job the hub is read back (``GET /api/directories`` or
``GET /api/decisions/{id}``) and the answer goes into ``rehearsal.json``
beside the shots. A rehearsal, never a sitting: nothing here is the owner's
own use. ``--engine none``: no job calls a model.

Usage: ``uv run python scripts/philo8_rehearsal.py --out <dir>`` (the web
bundle must be built).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts import graph_walk as gw

WINDOW_WAIT_MS = 12_000  # the 8 s undo window plus the hub's round trip
T = 20_000


def _palette(page: Any, query: str) -> None:
    field = page.locator("[aria-controls=desk-palette-listbox]")
    if not field.is_visible():
        page.locator("[aria-controls=desk-tool-shelf]").click()
    field.fill(query)


def _run(page: Any, query: str, option: str) -> None:
    _palette(page, query)
    page.locator(f"[id='desk-palette-option-{option}']").click()


def _to_list(page: Any, width: int) -> None:
    page.locator("[data-testid=chair-floor-toggle]").click()
    if width > 720:
        _run(page, "List view", "desk.toggle-view")
    page.locator(".desk-listmode").wait_for(timeout=T)


def _row(page: Any, title: str) -> Any:
    return page.locator(f".desk-listmode .desk-list-name-cell[aria-label='{title}']")


def _receipt(page: Any, want: str, timeout: int = T) -> str:
    page.wait_for_function(
        "(w) => (document.querySelector('.undo-receipt')?.innerText || '').includes(w)",
        arg=want, timeout=timeout)
    page.wait_for_timeout(400)  # the entrance settles, as the owner reads it
    return page.evaluate("() => document.querySelector('.undo-receipt')?.innerText || ''")


def _select(page: Any, title: str) -> None:
    _row(page, title).wait_for(timeout=T)
    page.evaluate(
        "(t) => document.querySelector(`.desk-listmode .desk-list-name-cell[aria-label='${t}']`).focus()",
        title)
    page.keyboard.press(" ")


def _menu_delete(page: Any, title: str) -> None:
    _row(page, title).click(button="right")
    item = page.locator(".desk-world-menu [role=menuitem]", has_text="Delete").last
    item.wait_for(timeout=T)
    item.click()


def rehearse(width: int, hub: Any, out: Path, log: list[dict[str, Any]]) -> None:
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    def status(decision_id: str) -> int:
        return hub.api("GET", f"/api/decisions/{decision_id}")[0]

    def zones() -> list[str]:
        return sorted(d["name"] for d in hub.api("GET", "/api/directories")[1]["directories"])

    def shot(name: str, page: Any) -> str:
        path = out / f"{width}-{name}.png"
        page.screenshot(path=str(path))
        return path.name

    def record(job: str, face: str, hub_read: dict[str, Any], shots: list[str]) -> None:
        entry = {"width": width, "job": job, "face": face, "hub": hub_read, "shots": shots,
                 "at_utc": datetime.now(timezone.utc).isoformat()}
        log.append(entry)
        print(json.dumps(entry))

    titles = {k: f"Rehearsal {k} {width}" for k in ("keep", "undo", "A", "B", "leave")}
    ids = {k: hub.api("POST", "/api/decisions", {"title": t, "status": "accepted"})[1]["decision"]["id"]
           for k, t in titles.items()}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 900 if width > 720 else 852},
                                device_scale_factor=2)
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(f"{hub.url}/?token={hub.token}", wait_until="load")
        try:
            page.get_by_role("button", name="Continue later").click(timeout=5_000)
        except Exception:  # noqa: BLE001 -- the gate was crossed by the other width
            pass
        page.locator("[data-testid=chair-floor-toggle]").wait_for(timeout=T)
        _to_list(page, width)

        # 1. two unnamed zones
        before = zones()
        _run(page, "New Zone", "desk.new-zone")
        page.locator(".desk-listmode input.desk-zone-rename").wait_for(timeout=T)
        page.keyboard.press("Escape")
        page.locator(".desk-listmode input.desk-zone-rename").wait_for(state="detached", timeout=T)
        _run(page, "New Zone", "desk.new-zone")
        page.locator(".desk-listmode input.desk-zone-rename").wait_for(timeout=T)
        page.wait_for_timeout(300)
        field = page.locator(".desk-listmode input.desk-zone-rename").input_value()
        s1 = shot("1-second-zone-field", page)
        made = [z for z in zones() if z not in before]
        record("two unnamed zones", f"list; the second field reads {field!r}", {"new zones": made}, [s1])

        # 2. the rename where he is (the field is open on 'New zone 2')
        page.keyboard.type(f"Platform {width}")
        page.keyboard.press("Enter")
        page.locator(".desk-listmode input.desk-zone-rename").wait_for(state="detached", timeout=T)
        page.locator(f".desk-listmode .desk-sortable-table-open[aria-label^='Platform {width}']").wait_for(timeout=T)
        s2 = shot("2-renamed-in-row", page)
        record("rename where he is", "list; Enter in the row", {"zones now": [z for z in zones() if z not in before]}, [s2])

        # 3. a list delete, no Undo
        _menu_delete(page, titles["keep"])
        pending = _receipt(page, "Removed")
        s3a = shot("3a-list-delete-pending", page)
        committed = _receipt(page, "Removal committed", 20_000)
        s3b = shot("3b-list-delete-committed", page)
        record("list delete, no Undo", f"{pending!r} then {committed!r}",
               {titles["keep"]: status(ids["keep"])}, [s3a, s3b])

        # 4. a list delete with Undo, read again after the window
        page.wait_for_timeout(6_500)  # the committed receipt lingers; let it clear
        _menu_delete(page, titles["undo"])
        _receipt(page, "Removed")
        page.locator("button.undo-receipt-btn").click()
        restored = _receipt(page, "Restored")
        s4a = shot("4a-list-undo-restored", page)
        page.wait_for_timeout(WINDOW_WAIT_MS)
        s4b = shot("4b-list-undo-after-window", page)
        record("list delete with Undo", f"{restored!r}; the row still listed after the window: "
               f"{_row(page, titles['undo']).is_visible()}",
               {titles["undo"] + " (after the window)": status(ids["undo"])}, [s4a, s4b])

        # 5. two deletes in one window (A then B, the list)
        page.wait_for_timeout(6_500)
        _select(page, titles["A"])
        page.keyboard.press("Delete")
        _receipt(page, f"Removed {titles['A']}")
        _select(page, titles["B"])
        page.keyboard.press("Delete")
        second = _receipt(page, f"Removed {titles['B']}")
        s5a = shot("5a-two-deletes-b-pending", page)
        _receipt(page, "Removal committed", 20_000)
        page.wait_for_timeout(1_000)
        s5b = shot("5b-two-deletes-committed", page)
        record("two deletes in one window", f"after B: {second!r}",
               {titles["A"]: status(ids["A"]), titles["B"]: status(ids["B"])}, [s5a, s5b])

        # 6. a delete, then a face change inside the window
        page.wait_for_timeout(6_500)
        _select(page, titles["leave"])
        page.keyboard.press("Delete")
        _receipt(page, "Removed")
        s6a = shot("6a-delete-pending-before-leaving", page)
        page.locator("[data-testid=chair-floor-toggle]").click()
        page.locator(".chair").wait_for(timeout=T)
        page.wait_for_timeout(1_500)
        s6b = shot("6b-on-the-chair", page)
        record("delete, then a face change", "list -> Chair inside the window",
               {titles["leave"]: status(ids["leave"])}, [s6a, s6b])

        real = [e for e in errors if "ResizeObserver" not in e]
        log.append({"width": width, "page_errors": real})
        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    home = Path(tempfile.mkdtemp(prefix="philo8-rehearsal-home-"))
    hub = gw.Hub(home, token="philo8-rehearsal").start()
    log: list[dict[str, Any]] = []
    started = time.monotonic()
    try:
        for width in (1440, 393):
            rehearse(width, hub, out, log)
    finally:
        hub.stop()
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              cwd=gw.REPO).stdout.strip() or None
    (out / "rehearsal.json").write_text(json.dumps({
        "label": args.label, "revision": revision, "rig_hub": "scripts/graph_walk.py Hub",
        "engine": "none", "home": "isolated (mkdtemp), removed after the run",
        "loadavg": os.getloadavg(), "duration_s": round(time.monotonic() - started, 1),
        "jobs": log,
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
