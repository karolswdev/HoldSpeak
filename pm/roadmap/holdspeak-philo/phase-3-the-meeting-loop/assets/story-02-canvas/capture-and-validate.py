#!/usr/bin/env python3
"""Capture and validate the PHILO-3-02 corrected static canvas.

This script opens local .dc.html boards only. It never starts the product,
connects to a hub/model, reads a desk database, or uses a microphone.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
BOARDS = [
    ("summary-imported.dc.html", 1440, 900, "imported"),
    ("summary-imported-phone.dc.html", 393, 852, "imported"),
    ("summary-ready.dc.html", 1440, 900, "ready"),
    ("summary-ready-phone.dc.html", 393, 852, "ready"),
    ("summary-retrying.dc.html", 1440, 900, "retrying"),
    ("summary-retrying-phone.dc.html", 393, 852, "retrying"),
    ("summary-failed.dc.html", 1440, 900, "failed"),
    ("summary-failed-phone.dc.html", 393, 852, "failed"),
]
TITLE = "Architecture boundary review"
PHONE_WIDTH = 393


def fail(message: str) -> None:
    raise AssertionError(message)


def element_from_point(page: Any, selector: str, x: float, y: float) -> dict[str, Any]:
    return page.evaluate(
        """({selector, x, y}) => {
          const target = document.querySelector(selector);
          const hit = document.elementFromPoint(x, y);
          const ok = Boolean(target && hit && (hit === target || target.contains(hit)));
          return {ok, hit: hit ? `${hit.tagName.toLowerCase()}.${hit.className || ''}` : null};
        }""",
        {"selector": selector, "x": x, "y": y},
    )


def pointer_proof(page: Any, locator: Any, selector: str, filename: str, label: str) -> dict[str, Any]:
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    if not box:
        fail(f"{filename}: {label} has no box")
    if box["height"] < 44:
        fail(f"{filename}: {label} is {box['height']}px high")
    dock_top = page.locator(".dock").bounding_box()["y"]
    box["right"] = box["x"] + box["width"]
    box["bottom"] = box["y"] + box["height"]
    if box["bottom"] > dock_top + 0.5:
        fail(f"{filename}: {label} falls behind dock")
    points = {
        "center": (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2),
        "top": (box["x"] + box["width"] / 2, box["y"] + 2),
        "right": (box["right"] - 2, box["y"] + box["height"] / 2),
        "bottom": (box["x"] + box["width"] / 2, box["bottom"] - 2),
        "left": (box["x"] + 2, box["y"] + box["height"] / 2),
        "top_left": (box["x"] + 2, box["y"] + 2),
        "top_right": (box["right"] - 2, box["y"] + 2),
        "bottom_left": (box["x"] + 2, box["bottom"] - 2),
        "bottom_right": (box["right"] - 2, box["bottom"] - 2),
    }
    hits: dict[str, Any] = {}
    for name, (x, y) in points.items():
        page.mouse.move(x, y)
        hit = element_from_point(page, selector, x, y)
        if not hit["ok"]:
            fail(f"{filename}: elementFromPoint {label} {name} hit {hit['hit']}")
        hits[name] = {"x": round(x, 2), "y": round(y, 2), **hit}
    return {"box": box, "dock_top": dock_top, "points": hits}


def main() -> int:
    results: list[dict[str, Any]] = []
    log_lines = [
        "PHILO-3-02 corrected canvas validation",
        f"scope: local static boards only; HOME={os.environ.get('HOME', '')}",
        f"playwright browser path: {os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '')}",
    ]
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for filename, width, height, state in BOARDS:
                path = ROOT / filename
                if not path.exists():
                    fail(f"missing board: {filename}")
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                page.goto(path.as_uri(), wait_until="load")
                page.wait_for_load_state("domcontentloaded")
                page.evaluate("document.fonts.ready")
                loaded_fonts = page.evaluate(
                    """() => Object.fromEntries(
                      ['Inter', 'Space Grotesk', 'JetBrains Mono'].map(family => [
                        family,
                        [...document.fonts].some(face => face.family === family && face.status === 'loaded')
                      ])
                    )"""
                )
                if not all(loaded_fonts.values()):
                    fail(f"{filename}: bundled font did not load: {loaded_fonts}")

                if page.locator(".desk").get_attribute("data-state") != state:
                    fail(f"{filename}: state mismatch")
                title = page.locator(".meeting-title")
                if title.count() != 1 or title.inner_text() != TITLE:
                    fail(f"{filename}: full meeting title is missing")
                title_metrics = title.evaluate(
                    "el => ({scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, fontSize: getComputedStyle(el).fontSize})"
                )
                if title_metrics["scrollWidth"] > title_metrics["clientWidth"] + 1:
                    fail(f"{filename}: title is clipped")
                if title_metrics["fontSize"] != "15px":
                    fail(f"{filename}: title font is {title_metrics['fontSize']}, expected 15px")

                role_fonts = {
                    ".arrival-display": "26px",
                    ".meeting-title": "15px",
                    ".summary-text": "13px",
                    ".transcript-text": "13px",
                }
                for selector, expected in role_fonts.items():
                    if page.locator(selector).count():
                        actual = page.locator(selector).first.evaluate("el => getComputedStyle(el).fontSize")
                        if actual != expected:
                            fail(f"{filename}: {selector} font is {actual}, expected {expected}")

                readable = page.locator("body *").evaluate_all(
                    "els => els.filter(el => (el.innerText || '').trim()).map(el => ({tag: el.tagName, cls: el.className, size: parseFloat(getComputedStyle(el).fontSize)}))"
                )
                small = [item for item in readable if item["size"] < 12]
                if small:
                    fail(f"{filename}: readable text below 12px: {small[:3]}")
                css = (ROOT / "canvas.css").read_text()
                if "--text-faint: #8b93a3" not in css:
                    fail("canvas.css: current faint token is absent")
                forbidden = re.compile(r"\b(?:Retry|2/3|3/3)\b|The cause stays with this meeting", re.I)
                visible_text = page.locator("body").inner_text()
                if forbidden.search(visible_text):
                    fail(f"{filename}: invented retry control, limit, or prose remains")

                verb = page.locator("[data-role='primary-verb']")
                expected_verbs = {"imported": "Run summary", "ready": "Open", "retrying": None, "failed": None}
                expected_verb = expected_verbs[state]
                if expected_verb is None and verb.count() != 0:
                    fail(f"{filename}: retry/failure has a new row verb")
                if expected_verb is not None and (verb.count() != 1 or verb.inner_text() != expected_verb):
                    fail(f"{filename}: expected existing {expected_verb!r} verb")

                work = page.locator(".chair")
                scroll_metrics = work.evaluate(
                    "el => ({scrollHeight: el.scrollHeight, clientHeight: el.clientHeight, overflowY: getComputedStyle(el).overflowY})"
                )
                if scroll_metrics["overflowY"] not in {"auto", "scroll"}:
                    fail(f"{filename}: Chair is not the scroll owner")
                scroll_metrics["scrollable"] = scroll_metrics["scrollHeight"] > scroll_metrics["clientHeight"]

                shot = ROOT / filename.replace(".html", ".png")
                # Retain the arrival position before hit checks scroll to the
                # footer. The owner's main board must still show its row.
                page.mouse.move(0, 0)
                page.screenshot(path=str(shot), full_page=False)
                result: dict[str, Any] = {
                    "file": filename,
                    "state": state,
                    "viewport": {"width": width, "height": height},
                    "screenshot": shot.name,
                    "title": {"text": TITLE, **title_metrics},
                    "fonts_loaded": loaded_fonts,
                    "fonts": role_fonts,
                    "readable_text_min_px": min(item["size"] for item in readable),
                    "scroll": scroll_metrics,
                    "forbidden_copy": False,
                }

                if width == PHONE_WIDTH:
                    if expected_verb is not None:
                        result["phone_hit_ownership"] = {
                            "verb": expected_verb,
                            **pointer_proof(page, verb, "[data-role='primary-verb']", filename, expected_verb),
                        }
                    footer_hits = []
                    footer = page.locator(".capture-bar .button")
                    for index in range(footer.count()):
                        footer_button = footer.nth(index)
                        footer_hits.append(
                            {
                                "verb": footer_button.inner_text(),
                                **pointer_proof(
                                    page,
                                    footer_button,
                                    f".capture-bar button:nth-of-type({index + 1})",
                                    filename,
                                    f"footer {footer_button.inner_text()}",
                                ),
                            }
                        )
                    result["phone_footer_hit_ownership"] = footer_hits
                    footer_shot = ROOT / filename.replace(".html", "-footer.png")
                    page.mouse.move(0, 0)
                    page.screenshot(path=str(footer_shot), full_page=False)
                    result["footer_screenshot"] = footer_shot.name
                results.append(result)
                log_lines.append(
                    f"PASS {filename} viewport={width}x{height} state={state} fonts=Inter,Space Grotesk,JetBrains Mono scroll={scroll_metrics['scrollHeight']}px/{scroll_metrics['clientHeight']}px scrollable={scroll_metrics['scrollable']}"
                )
                if "phone_hit_ownership" in result:
                    log_lines.append(f"  elementFromPoint: {json.dumps(result['phone_hit_ownership']['points'], sort_keys=True)}")
                if "phone_footer_hit_ownership" in result:
                    log_lines.append(
                        "  footer elementFromPoint: "
                        + json.dumps(
                            {item["verb"]: item["points"] for item in result["phone_footer_hit_ownership"]},
                            sort_keys=True,
                        )
                    )
                page.close()
            browser.close()
    except Exception as exc:
        log_lines.append(f"FAIL {type(exc).__name__}: {exc}")
        (ROOT / "validation.log").write_text("\n".join(log_lines) + "\n")
        (ROOT / "validation.json").write_text(json.dumps({"status": "FAIL", "error": str(exc), "boards": results}, indent=2) + "\n")
        raise

    payload = {
        "status": "PASS",
        "scope": "static canvas only; no product server, hub, model, keychain, desk database or microphone",
        "boards": results,
    }
    (ROOT / "validation.json").write_text(json.dumps(payload, indent=2) + "\n")
    log_lines.append(f"PASS total={len(results)} boards screenshots={len(list(ROOT.glob('summary-*.png')))}")
    (ROOT / "validation.log").write_text("\n".join(log_lines) + "\n")
    print("\n".join(log_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
