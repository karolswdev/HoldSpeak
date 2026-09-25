"""Capture and fence the PHILO-6-03 placement proposal.

The page imports the production Chair, Surface species, Button, MicButton and
MeetingSummarySlab. This script proves the proposed card misses the readable
Arrival sections, summary text and capture bar at both required widths.
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
            capture = page.locator("[data-testid=arrival-capture-bar]").bounding_box()
            if not card or not capture:
                raise AssertionError(f"missing geometry at {board}/{width}: {card=} {capture=}")
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
            capture_rect = {**capture, "right": capture["x"] + capture["width"], "bottom": capture["y"] + capture["height"]}
            active_sections = {}
            for label in ("NO CALENDAR", "BRIEF", "MEETINGS · 1"):
                heading = page.get_by_role("heading", name=label)
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
            facts[f"{board}-{width}"] = {
                "board": board,
            "query": query,
            "viewport": {"width": width, "height": height},
            "card": card_rect,
            "summary_well": summary_well_rect,
            "summary_text": summary_rect,
            "capture_bar": capture_rect,
            "active_sections": active_sections,
            "card_text": card_text,
            "card_overlaps_summary_text": overlap(card_rect, summary_rect) if summary_rect else False,
            "card_overlaps_summary_well": overlap(card_rect, summary_well_rect) if summary_well_rect else False,
            "card_overlaps_capture_bar": overlap(card_rect, capture_rect),
            "chair_scroll_top": page.locator("[data-testid=chair]").evaluate("(el) => el.scrollTop"),
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
    assert not fact["card_overlaps_summary_text"], f"toast covers summary text at {key}"
    assert not fact["card_overlaps_summary_well"], f"toast covers summary well at {key}"
    assert not fact["card_overlaps_capture_bar"], f"toast covers capture bar at {key}"
    assert all(
        not overlap(fact["card"], section)
        for section in fact["active_sections"].values()
    ), f"toast covers an active Arrival section at {key}"
    assert fact["scroll_width"] <= fact["viewport"]["width"], f"horizontal overflow at {key}"
    assert fact["button_count"] == 2, f"toast verbs drifted at {key}"
    if fact["board"] == "capture":
        assert fact["capture_state"] == "pressed-mic", f"capture board state drifted at {key}"
    else:
        assert fact["capture_state"] == "idle-mic", f"non-capture board state drifted at {key}"
