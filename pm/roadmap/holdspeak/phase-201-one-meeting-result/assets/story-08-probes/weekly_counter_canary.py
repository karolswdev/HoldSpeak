"""HS-201-08 negative canary for the scoped weekly counter assertion."""
from __future__ import annotations

import re

from playwright.sync_api import sync_playwright


# Execute the actual loop from the glass test, not a second copy of its rule.
import ast
from pathlib import Path

source_path = Path("tests/e2e/test_hs175_rhythm_brief_glass.py")
tree = ast.parse(source_path.read_text())
method = next(node for node in ast.walk(tree)
              if isinstance(node, ast.FunctionDef)
              and node.name == "test_brief_this_week_section")
loop = next(node for node in method.body
            if isinstance(node, ast.For) and isinstance(node.target, ast.Name)
            and node.target.id == "testid")
assertion_code = compile(ast.Module(body=[loop], type_ignores=[]), str(source_path), "exec")


def assert_scoped_counters(page) -> None:
    brief = page.locator(".intelligence-brief")
    brief.wait_for(state="visible", timeout=1000)
    exec(assertion_code, {"brief_el": brief, "re": re})


CASES = {
    "00:33 timestamp": """
      <div class="intelligence-brief">
        <div class="intelligence-brief-generated">GENERATED SEP 20 00:33</div>
        <div data-testid="brief-tw-meetings"><span class="intelligence-brief-tw-primary">2 MEETINGS</span></div>
      </div>
    """,
    "08:00 timestamp": """
      <div class="intelligence-brief">
        <div class="intelligence-brief-generated">GENERATED SEP 20 08:00</div>
        <div data-testid="brief-tw-meetings"><span class="intelligence-brief-tw-primary">2 MEETINGS</span></div>
      </div>
    """,
    "0 MEETINGS counter": """
      <div class="intelligence-brief">
        <div class="intelligence-brief-generated">GENERATED SEP 20 00:33</div>
        <div data-testid="brief-tw-meetings"><span class="intelligence-brief-tw-primary">0 MEETINGS</span></div>
      </div>
    """,
    "00 ARMED counter": """
      <div class="intelligence-brief">
        <div class="intelligence-brief-generated">GENERATED SEP 20 08:00</div>
        <div data-testid="brief-tw-armed"><span class="intelligence-brief-tw-primary">00 ARMED</span></div>
      </div>
    """,
}


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    for label, html in CASES.items():
        page.set_content(html)
        if "timestamp" in label:
            assert_scoped_counters(page)
            print(f"PASS {label}: timestamp accepted")
        else:
            try:
                assert_scoped_counters(page)
            except AssertionError as exc:
                print(f"PASS {label}: rejected ({exc})")
            else:
                raise AssertionError(f"CANARY FAILED: {label} was accepted")
    browser.close()
