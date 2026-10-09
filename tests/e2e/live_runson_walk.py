"""PHILO-16 (C): a read-only walk of Runs on (the Models window) on a real desk.

The port of the parked `tests/_parked/philo16-concierge/live170_walk.py`
(its Concierge part). It opens Runs on at 1440x900 and 393x852, shoots the
window, and records what the board says: the AppHead fact and strip, each
job (state, the engine it runs on, its token line), each engine plate (emblem,
tokens, lamp), the FOUND rows, and the wires. It writes runson-facts.json and
runson-facts.md.

THE LIVE LAWS (Article IV: the walk arms nothing):
1. READ-ONLY. It never presses a verb: no Try it, Use it, Download, Add, Undo,
   no drag, no Enter on a plate. It never selects a job (a selection is not a
   write, but the walk does not need one).
2. NO TOKEN IN A FILE. The --hub URL (with its token) comes from the command
   line; the token never appears in what the walk writes.
3. FACE-DRIVEN. It opens Runs on through the staged-surface seam (the same
   seam as tests/e2e/runs_on.py) and reads the DOM.
4. STANDALONE. Not collected by pytest (no test_* names); run it directly:

  uv run python tests/e2e/live_runson_walk.py --hub "http://127.0.0.1:PORT/?token=TOKEN" [--out DIR]

Exit 0: both widths read, no raw button, no horizontal overflow, no page
error. Exit 1 otherwise, with the reason.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests._evidence import evidence_dir  # noqa: E402

DEFAULT_OUT = evidence_dir("docs/internal/philo/phase-16/live-runson")
VIEWPORTS = ((1440, 900), (393, 852))

_READ_BOARD = r"""() => {
  const root = document.querySelector("[data-testid='runson-root']");
  const board = document.querySelector("[data-testid='switchboard']");
  const text = (el) => (el?.innerText || el?.textContent || "").replace(/\s+/g, " ").trim();
  const jobs = [...document.querySelectorAll("[data-testid^='switchboard-job-']")].map((el) => ({
    id: el.getAttribute("data-job-id"),
    state: el.getAttribute("data-state"),
    name: text(el.querySelector(".switchboard-job-name")),
    tasks: text(el.querySelector(".switchboard-job-tasks")),
    result: text(el.querySelector(".switchboard-job-result")),
  }));
  const plates = [...document.querySelectorAll("[data-testid^='switchboard-engine-']")].map((el) => ({
    id: (el.getAttribute("data-testid") || "").replace("switchboard-engine-", ""),
    name: el.getAttribute("aria-label") || "",
    text: text(el),
    lamp: (document.querySelector(`[data-testid='switchboard-lamp-${(el.getAttribute("data-testid") || "").replace("switchboard-engine-", "")}']`)?.className || ""),
    // A FOUND row sits after the Found caption in document order.
    found: (() => {
      const cap = document.querySelector("[data-testid='switchboard-found-cap']");
      return Boolean(cap && (cap.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING));
    })(),
  }));
  const wires = [...document.querySelectorAll("[data-testid='switchboard-wire']")].map((el) => ({
    job: el.getAttribute("data-job"), engine: el.getAttribute("data-engine"),
    order: Number(el.getAttribute("data-order")), cls: el.getAttribute("class"),
  }));
  const raw = [...document.querySelectorAll("[data-testid='runson-root'] button, .runson-foot button")]
    .filter((b) => {
      const c = b.className.split(" ");
      return !c.includes("btn") && !c.includes("desk-mic") && !c.includes("gadget-chip-egress");
    })
    .map((b) => (b.textContent || b.className).slice(0, 40));
  return {
    open: Boolean(root),
    layout: board?.getAttribute("data-layout") || null,
    fact: text(document.querySelector("[data-testid='runson-fact']")),
    strip: [...document.querySelectorAll("[data-testid='runson-strip'] li")].map(text),
    found_cap: text(document.querySelector("[data-testid='switchboard-found-cap']")),
    receipt: text(document.querySelector("[data-testid='runson-receipt']")),
    jobs, plates, wires, raw_buttons: raw,
    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
  };
}"""


def _settle(page: Any) -> None:
    page.evaluate("""() => Promise.race([
        Promise.all(document.getAnimations().map((a) => a.finished.catch(() => null))),
        new Promise((r) => setTimeout(r, 2000)),
    ])""")
    page.wait_for_timeout(200)


def _open_runs_on(page: Any) -> None:
    """The staged-surface seam (tests/e2e/runs_on.py open_runs_on); read-only."""
    page.evaluate(
        """() => sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key: "open-concierge"}))"""
    )
    page.reload(wait_until="load")
    later = page.get_by_role("button", name="Continue later", exact=True)
    try:
        later.wait_for(timeout=3000)
        later.click()  # the first-value gate only; not a write to the desk
    except Exception:  # noqa: BLE001 - the gate is already past
        pass
    page.get_by_test_id("runson-root").wait_for(timeout=30_000)
    page.get_by_test_id("switchboard").wait_for(timeout=30_000)
    # The detection (LAN probes) fills the engines in after the roster paints.
    try:
        page.wait_for_function(
            "() => /Checked/.test(document.querySelector(\"[data-testid='runson-strip']\")?.textContent || '')",
            timeout=30_000,
        )
    except Exception:  # noqa: BLE001 - recorded below as a strip without Checked
        pass
    _settle(page)


def _md(report: dict[str, Any]) -> str:
    lines = [f"# Runs on, live walk ({report['generated_at']})", "", f"Hub: `{report['hub_host']}`", ""]
    for width, facts in report["widths"].items():
        lines += [f"## {width}", "", f"- Layout: {facts.get('layout')}", f"- Fact: {facts.get('fact')}",
                  f"- Strip: {' · '.join(facts.get('strip') or [])}", f"- Found: {facts.get('found_cap') or 'none'}",
                  f"- Shot: `{facts.get('shot')}`", "", "| Job | State | Line |", "| --- | --- | --- |"]
        for job in facts.get("jobs", []):
            lines.append(f"| {job['name']} | {job['state']} | {job['result'] or job['tasks']} |")
        lines += ["", "| Engine | Lamp | Tokens |", "| --- | --- | --- |"]
        for plate in facts.get("plates", []):
            lamp = next((c for c in plate["lamp"].split() if c.startswith("is-")), plate["lamp"])
            lines.append(f"| {plate['name']} | {lamp} | {plate['text']} |")
        lines += ["", "| Wire | Order |", "| --- | --- |"]
        for wire in facts.get("wires", []):
            lines.append(f"| {wire['job']} → {wire['engine']} | {wire['order']} |")
        lines.append("")
    if report["problems"]:
        lines += ["## Problems", ""] + [f"- {p}" for p in report["problems"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="PHILO-16 (C) read-only Runs on walk")
    parser.add_argument("--hub", required=True, help="hub URL with ?token=...")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    parsed = urlparse(args.hub)
    token = parse_qs(parsed.query).get("token", [""])[0]
    if not token:
        print("ERROR: --hub must carry ?token=...")
        return 1
    base = f"{parsed.scheme}://{parsed.netloc}"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    report: dict[str, Any] = {"generated_at": datetime.now().isoformat(timespec="seconds"),
                              "hub_host": parsed.netloc, "widths": {}, "problems": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.emulate_media(reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
                writes: list[str] = []
                reading = {"on": False}

                def _write(r: Any, writes: list[str] = writes, reading: dict = reading) -> None:
                    if r.method in ("GET", "HEAD", "OPTIONS") or urlparse(r.url).netloc != parsed.netloc:
                        return
                    # The desk's own load (its seed, the first-value gate) is
                    # the product's, recorded apart; only a write sent while
                    # the walk reads the board fails law 1.
                    writes.append(("READING " if reading["on"] else "LOAD ") + f"{r.method} {urlparse(r.url).path}")

                page.on("request", _write)
                page.goto(f"{base}/?token={token}", wait_until="load")
                try:
                    _open_runs_on(page)
                    reading["on"] = True
                    facts = page.evaluate(_READ_BOARD)
                    win = page.locator(".desk-surface-window").filter(has=page.get_by_test_id("runson-root")).first
                    shot = out / f"runson-{width}.png"
                    win.screenshot(path=str(shot))
                    facts["shot"] = str(shot)
                except Exception as exc:  # noqa: BLE001
                    facts = {"error": f"{type(exc).__name__}: {str(exc)[:300]}"}
                    report["problems"].append(f"{width}: Runs on did not read: {facts['error']}")
                report["widths"][str(width)] = facts
                if facts.get("raw_buttons"):
                    report["problems"].append(f"{width}: raw buttons {facts['raw_buttons']}")
                if facts.get("overflow"):
                    report["problems"].append(f"{width}: horizontal overflow")
                want = "list" if width < 720 else "board"
                if facts.get("layout") and facts["layout"] != want:
                    report["problems"].append(f"{width}: layout {facts['layout']}, wanted {want}")
                for e in errors:
                    if "ResizeObserver" not in e:
                        report["problems"].append(f"{width}: page error {e[:200]}")
                facts["load_writes"] = [w[5:] for w in writes if w.startswith("LOAD ")]
                for w in writes:
                    if w.startswith("READING "):
                        report["problems"].append(f"{width}: a write while reading: {w[8:]}")
                page.close()
        finally:
            browser.close()

    (out / "runson-facts.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    (out / "runson-facts.md").write_text(_md(report))
    print(f"Runs on walk: {out / 'runson-facts.md'}")
    for width, facts in report["widths"].items():
        print(f"  {width}: {facts.get('layout')} · {facts.get('fact')} · "
              f"{len(facts.get('jobs') or [])} jobs · {len(facts.get('plates') or [])} plates · "
              f"{len(facts.get('wires') or [])} wires")
    for p in report["problems"]:
        print(f"  PROBLEM: {p}")
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
