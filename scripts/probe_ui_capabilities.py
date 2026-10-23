#!/usr/bin/env python3
"""Report browser feature availability on isolated about:blank pages.

Run under scripts/test_lock.py with an isolated HOME and the real
PLAYWRIGHT_BROWSERS_PATH. This does not open HoldSpeak, contact a hub,
benchmark performance, or establish accessible application behavior.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import platform


FEATURES = """() => {
  const supports = value => typeof globalThis.CSS?.supports === 'function'
    && globalThis.CSS.supports(value);
  const entries = globalThis.PerformanceObserver?.supportedEntryTypes ?? [];
  return {
    popover: 'popover' in (globalThis.HTMLElement?.prototype ?? {}),
    anchorName: supports('anchor-name: --desk-anchor'),
    positionAnchor: supports('position-anchor: --desk-anchor'),
    viewTransitions: 'startViewTransition' in (globalThis.document ?? {}),
    contentVisibility: supports('content-visibility: auto'),
    subgrid: supports('grid-template-columns: subgrid'),
    containers: supports('container-type: inline-size'),
    pointerCapture: 'setPointerCapture' in (globalThis.Element?.prototype ?? {}),
    eventTiming: entries.includes('event'),
    longAnimationFrames: entries.includes('long-animation-frame')
  };
}"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--browser", choices=("chromium", "firefox", "webkit"),
        action="append", help="Repeat to select engines; defaults to all three.",
    )
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright

    results: list[dict[str, object]] = []
    with sync_playwright() as playwright:
        for name in args.browser or ["chromium", "firefox", "webkit"]:
            browser = None
            try:
                browser = getattr(playwright, name).launch(headless=True, timeout=15_000)
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                results.append({
                    "name": name, "version": browser.version,
                    "capabilities": page.evaluate(FEATURES),
                })
            except Exception as exc:
                results.append({"name": name, "error": str(exc)[:600]})
            finally:
                if browser is not None:
                    browser.close()
    print(json.dumps({
        "date": datetime.now(timezone.utc).isoformat(),
        "os": platform.platform(),
        "scope": "Isolated about:blank probes; no HoldSpeak task, performance or accessibility benchmark",
        "engines": results,
    }, indent=2))
    return int(any("error" in result for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
