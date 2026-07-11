"""Capture every HoldSpeak Web route and audit its interactive-control grammar.

This is a Web-only design/accessibility audit. Compact screenshots are browser
evidence and must never be treated as native Swift acceptance evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROUTES = (
    "/",
    "/welcome",
    "/setup",
    "/live",
    "/activity",
    "/history",
    "/settings",
    "/profiles",
    "/dictation",
    "/commands",
    "/companion",
    "/presence",
    "/studio",
    "/workbench",
    "/cadence",
    "/docs/dictation-runtime",
    "/design/components",
)

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000},
    "compact_web": {"width": 430, "height": 932},
}


def _slug(route: str) -> str:
    return "home" if route == "/" else route.strip("/").replace("/", "-")


def _page_metrics(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const selector = [
            'button', 'input:not([type="hidden"])', 'select', 'textarea',
            'summary', '[role="button"]', '[role="radio"]', '[role="checkbox"]'
          ].join(',');
          const visible = (el) => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
          };
          const nameOf = (el) => {
            const labels = el.labels ? [...el.labels].map(x => x.innerText.trim()).join(' ') : '';
            return (el.getAttribute('aria-label') || labels || el.getAttribute('title') ||
              el.innerText || el.value || '').trim();
          };
          const controls = [...document.querySelectorAll(selector)].filter(visible).map((el) => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            const label = el.matches('input[type="checkbox"], input[type="radio"]')
              ? el.closest('label')
              : null;
            const target = label && visible(label) ? label.getBoundingClientRect() : r;
            return {
              tag: el.tagName.toLowerCase(),
              type: el.getAttribute('type') || el.getAttribute('role') || '',
              name: nameOf(el),
              width: Math.round(r.width * 10) / 10,
              height: Math.round(r.height * 10) / 10,
              target_width: Math.round(target.width * 10) / 10,
              target_height: Math.round(target.height * 10) / 10,
              appearance: s.appearance,
              radius: s.borderRadius,
              font: `${s.fontFamily}|${s.fontSize}|${s.fontWeight}`,
              border: `${s.borderWidth}|${s.borderStyle}|${s.borderColor}`,
              background: s.backgroundColor,
            };
          });
          const fieldControls = controls.filter(x => ['input','select','textarea'].includes(x.tag));
          const buttonControls = controls.filter(x => x.tag === 'button' || x.type === 'button');
          const signature = (x) => [x.height, x.radius, x.font, x.border, x.background].join('::');
          return {
            title: document.title,
            url: location.href,
            viewport_width: document.documentElement.clientWidth,
            document_width: document.documentElement.scrollWidth,
            horizontal_overflow:
              document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
            controls: controls.length,
            fields: fieldControls.length,
            buttons: buttonControls.length,
            under_24px: controls.filter(x => x.target_width < 24 || x.target_height < 24),
            under_44px: controls.filter(x => x.target_width < 44 || x.target_height < 44),
            unnamed: controls.filter(x => !x.name),
            native_selects: controls.filter(x => x.tag === 'select' && x.appearance !== 'none'),
            field_style_signatures: [...new Set(fieldControls.map(signature))],
            button_style_signatures: [...new Set(buttonControls.map(signature))],
          };
        }"""
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8788")
    parser.add_argument("--out", type=Path, default=Path("/tmp/holdspeak-web-ui-audit"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {"base_url": args.base_url, "viewports": {}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for viewport_name, viewport in VIEWPORTS.items():
            context = browser.new_context(viewport=viewport)
            viewport_report: dict[str, Any] = {}
            for route in ROUTES:
                page = context.new_page()
                console_errors: list[str] = []
                page.on(
                    "console",
                    lambda message, errors=console_errors: (
                        errors.append(message.text) if message.type == "error" else None
                    ),
                )
                try:
                    response = page.goto(
                        f"{args.base_url.rstrip('/')}{route}",
                        wait_until="networkidle",
                        timeout=20_000,
                    )
                    page.screenshot(
                        path=args.out / f"{viewport_name}-{_slug(route)}.png",
                        full_page=True,
                    )
                    viewport_report[route] = {
                        "http_status": response.status if response else None,
                        "console_errors": console_errors,
                        **_page_metrics(page),
                    }
                except Exception as exc:  # one broken route must not hide the rest
                    viewport_report[route] = {
                        "error": str(exc),
                        "console_errors": console_errors,
                    }
                finally:
                    page.close()
            report["viewports"][viewport_name] = viewport_report
            context.close()
        browser.close()

    (args.out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(args.out / "report.json")


if __name__ == "__main__":
    main()
