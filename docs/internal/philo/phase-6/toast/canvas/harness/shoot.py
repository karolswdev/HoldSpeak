"""Capture and fence the PHILO-6-03 placement proposal.

The page imports the production Chair, Meetings window, Floor DeskListView,
Surface species, Button, MicButton and MeetingSummarySlab. The fences prove
the card is in view, has its two real Buttons, displaces the current surface's
content and misses fixed chrome at both required widths.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)


def overlap(a: dict, b: dict) -> bool:
    return not (
        a["right"] <= b["x"]
        or b["right"] <= a["x"]
        or a["bottom"] <= b["y"]
        or b["bottom"] <= a["y"]
    )


CASES = (
    ("today", "?board=today"),
    ("proposed", "?board=proposed"),
    ("summary-open", "?board=summary-open"),
    ("capture", "?board=capture"),
    ("meetings", "?board=meetings"),
    ("floor", "?board=floor"),
    # Placement must also survive a longer readable summary at a different
    # scroll position. These probes are recorded in facts.json, not shown as
    # extra owner boards.
    ("summary-open-long", "?board=summary-open&summary=long"),
)
facts = {}
errors = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    for width, height in ((1440, 900), (393, 852)):
        context = browser.new_context(
            viewport={"width": width, "height": height}, device_scale_factor=2
        )
        page = context.new_page()
        page.on(
            "console",
            lambda message: errors.append(f"console: {message.text}")
            if message.type == "error"
            else None,
        )
        page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
        for board, query in CASES:
            page.goto(f"http://127.0.0.1:4431/{query}")
            page.wait_for_selector("[data-testid=toast-card]")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(200)
            page.screenshot(path=str(OUT / f"{board}-{width}.png"), full_page=True)

            card = page.locator("[data-testid=toast-card]").bounding_box()
            summary_well_locator = page.locator("[data-testid=arrival-summary]")
            summary_locator = page.locator("[data-testid=meeting-summary-text]")
            summary_well = summary_well_locator.bounding_box() if summary_well_locator.count() else None
            summary = summary_locator.bounding_box() if summary_locator.count() else None
            capture_locator = page.locator("[data-testid=arrival-capture-bar]")
            capture = capture_locator.bounding_box() if capture_locator.count() else None
            if not card:
                raise AssertionError(f"missing card geometry at {board}/{width}")
            card_rect = {**card, "right": card["x"] + card["width"], "bottom": card["y"] + card["height"]}
            summary_well_rect = None
            if summary_well:
                summary_well_rect = {
                    **summary_well,
                    "right": summary_well["x"] + summary_well["width"],
                    "bottom": summary_well["y"] + summary_well["height"],
                }
            summary_rect = None
            if summary:
                summary_rect = {**summary, "right": summary["x"] + summary["width"], "bottom": summary["y"] + summary["height"]}
            capture_rect = None
            if capture:
                capture_rect = {**capture, "right": capture["x"] + capture["width"], "bottom": capture["y"] + capture["height"]}
            active_sections = {}
            for label in ("NO CALENDAR", "BRIEF", "MEETINGS · 1"):
                heading = page.get_by_role("heading", name=label)
                if not heading.count():
                    continue
                section = heading.locator("..")
                section_box = section.bounding_box()
                if section_box:
                    active_sections[label] = {
                        **section_box,
                        "right": section_box["x"] + section_box["width"],
                        "bottom": section_box["y"] + section_box["height"],
                    }
            card_text = page.locator("[data-testid=toast-card]").inner_text()
            pressed_mic_count = page.locator("[data-testid=canvas-pressed-mic]").count()
            surface_regions = {}
            if board == "meetings":
                for name, selector in {
                    "titlebar": ".toast-meetings-window .desk-pullout-head",
                    "content": "[data-testid=meetings-window-content]",
                }.items():
                    region = page.locator(selector).bounding_box()
                    if region:
                        surface_regions[name] = {
                            **region,
                            "right": region["x"] + region["width"],
                            "bottom": region["y"] + region["height"],
                        }
            elif board == "floor":
                region = page.locator("[data-testid=floor-work-area]").bounding_box()
                if region:
                    surface_regions["work_area"] = {
                        **region,
                        "right": region["x"] + region["width"],
                        "bottom": region["y"] + region["height"],
                    }
                floor_content = page.locator(
                    "[data-testid=floor-work-area] .desk-list-face"
                ).bounding_box()
                if floor_content:
                    surface_regions["floor_content"] = {
                        **floor_content,
                        "right": floor_content["x"] + floor_content["width"],
                        "bottom": floor_content["y"] + floor_content["height"],
                    }
            chrome_regions = {}
            for name, selector in {
                "menubar": ".desk-menubar",
                "dock": ".desk-dock",
            }.items():
                region = page.locator(selector).bounding_box()
                if region:
                    chrome_regions[name] = {
                        **region,
                        "right": region["x"] + region["width"],
                        "bottom": region["y"] + region["height"],
                    }
            card_in_viewport = (
                card_rect["x"] >= 0
                and card_rect["y"] >= 0
                and card_rect["right"] <= width
                and card_rect["bottom"] <= height
            )
            facts[f"{board}-{width}"] = {
                "board": board,
                "query": query,
                "viewport": {"width": width, "height": height},
                "card": card_rect,
                "card_in_viewport": card_in_viewport,
                "summary_well": summary_well_rect,
                "summary_text": summary_rect,
                "capture_bar": capture_rect,
                "active_sections": active_sections,
                "surface_regions": surface_regions,
                "chrome_regions": chrome_regions,
                "card_text": card_text,
                "card_overlaps_summary_text": overlap(card_rect, summary_rect) if summary_rect else False,
                "card_overlaps_summary_well": overlap(card_rect, summary_well_rect) if summary_well_rect else False,
                "card_overlaps_capture_bar": overlap(card_rect, capture_rect) if capture_rect else False,
                "card_overlaps_surface": {
                    name: overlap(card_rect, region)
                    for name, region in surface_regions.items()
                },
                "card_overlaps_chrome": {
                    name: overlap(card_rect, region)
                    for name, region in chrome_regions.items()
                },
                "floor_content_visible": (
                    (
                        "floor_content" in surface_regions
                        and surface_regions["floor_content"]["y"] < height
                        and surface_regions["floor_content"]["bottom"] > 0
                    )
                    if board == "floor"
                    else None
                ),
                "chair_scroll_top": page.locator("[data-testid=chair]").evaluate("(el) => el.scrollTop") if page.locator("[data-testid=chair]").count() else None,
                "scroll_width": page.evaluate("document.documentElement.scrollWidth"),
                "button_count": page.locator("[data-testid=toast-card] .btn").count(),
                "capture_state": "pressed-mic" if pressed_mic_count else "idle-mic",
            }
        context.close()
    browser.close()

(OUT / "facts.json").write_text(json.dumps(facts, indent=2) + "\n")
(OUT / "browser-errors.json").write_text(json.dumps(errors, indent=2) + "\n")
print(json.dumps(facts, indent=2))
print(json.dumps({"browser_errors": errors}, indent=2))

assert not errors, errors
for key, fact in facts.items():
    if fact["board"] == "today":
        continue
    assert fact["card_in_viewport"], f"toast is not in the viewport at {key}"
    assert not fact["card_overlaps_summary_text"], f"toast covers summary text at {key}"
    assert not fact["card_overlaps_summary_well"], f"toast covers summary well at {key}"
    assert not fact["card_overlaps_capture_bar"], f"toast covers capture bar at {key}"
    assert all(
        not overlap(fact["card"], section)
        for section in fact["active_sections"].values()
    ), f"toast covers an active Arrival section at {key}"
    assert not any(fact["card_overlaps_surface"].values()), f"toast covers current-surface content at {key}"
    assert not any(fact["card_overlaps_chrome"].values()), f"toast covers desk chrome at {key}"
    assert fact["scroll_width"] <= fact["viewport"]["width"], f"horizontal overflow at {key}"
    assert fact["button_count"] == 2, f"toast verbs drifted at {key}"
    assert "3 open" in fact["card_text"], f"fixture count must stay nonzero at {key}"
    if fact["board"] == "floor":
        assert fact["floor_content_visible"], f"Floor list content is below the viewport at {key}"
    if fact["board"] == "capture":
        assert fact["capture_state"] == "pressed-mic", f"capture board state drifted at {key}"
    else:
        assert fact["capture_state"] == "idle-mic", f"non-capture board state drifted at {key}"
