"""Shared notice and short-form geometry, using the executable gallery."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pytest
from .test_desk_sweep import TOKEN, T, _Case, _hub_open, _page, desk, pw_browser
from .glass_infra import _normal_chair, clear_hub_windows_http

@pytest.mark.parametrize("width", [900, 393])
def test_shared_notice_and_form_seats(desk: dict[str, Any], pw_browser: Any, width: int) -> None:
    base = desk["base"]
    clear_hub_windows_http(base, TOKEN)
    _hub_open(base, "surface-components", None, window=width == 900)
    ctx, page, errors, requests = _page(pw_browser, width, base)
    out = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/kit11"
    out.mkdir(parents=True, exist_ok=True)
    try:
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        sweep = _Case(page, base, "surface-components", errors, requests)
        sweep.settle()
        win = page.locator("#surface-components")
        win.get_by_test_id("reference-group-live").click()
        popup = win.get_by_role("combobox", name="Live piece", exact=True)
        popup.select_option("Notice")
        sweep.settle()
        notice = win.get_by_role("alert")
        assert notice.count() == 1
        assert notice.inner_text().count("No answer from the engine") == 1
        assert win.get_by_role("status").filter(has_text="Failed").count() == 1
        bar = win.get_by_role("status").filter(has_text="Failed")
        assert "No answer from the engine" not in bar.inner_text()
        facts = bar.evaluate("""el => {
          const parts = [...el.children].filter(e => e.getClientRects().length);
          return {tops:parts.map(e=>e.getBoundingClientRect().top),
            wraps:parts.map(e=>getComputedStyle(e).whiteSpace),
            font:getComputedStyle(document.querySelector('.surface-action-notice')).fontFamily};
        }""")
        assert len(set(facts["tops"])) == 1, facts
        assert all(value == "nowrap" for value in facts["wraps"]), facts
        assert "mono" not in facts["font"].lower(), facts
        page.screenshot(path=str(out / f"1-3-gallery-notice-{width}-after.png"))
        popup.select_option("Form fit")
        sweep.settle()
        form = win.get_by_role("region", name="New person", exact=True).last
        fields = form.locator(".surface-inspector-fields")
        last = form.locator(".gadget-row").last.bounding_box()
        actions = form.locator(".surface-inspector-actions").bounding_box()
        assert last and actions
        assert 0 <= actions["y"] - last["y"] - last["height"] <= 20, (last, actions)
        first = form.locator(".gadget-row").first.bounding_box()
        well = fields.bounding_box()
        assert first and well
        assert first["y"] >= well["y"] - 1
        assert first["y"] + first["height"] <= well["y"] + well["height"] + 1
        page.screenshot(path=str(out / f"6-gallery-form-{width}-after.png"))
        (out / f"gallery-{width}.json").write_text(json.dumps(facts, indent=2) + "\n")
        assert not errors, errors
    finally:
        ctx.close()
