"""The Settings > Engines receipt and Undo never overlap, at either width.

The retired drag switchboard is kept in _parked/test_runs_on_glass.py.
Assignment state and refusals use the app and hub tests named there.
"""
from __future__ import annotations

import pytest

from .glass_infra import _api, _settle
from .fit_rig import BOX_JS, T, WIDTHS, FitRig, TOKEN as FIT_TOKEN
from .type_floor_rig import HIT_PROBE_JS, OWNERSHIP_JS

pytest.importorskip("playwright.sync_api", reason="Settings Engines geometry needs Playwright")
pytestmark = [pytest.mark.e2e, pytest.mark.timeout(240, method="thread")]


class TestTheRunsOnFooter(FitRig):
    """replaces: tests/e2e/test_philo15_12_ugly_glass.py::TestPhilo15Lane12Ugly::test_the_runs_on_receipt_never_runs_into_undo (moved whole)."""

    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_runs_on_receipt_never_runs_into_undo(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from .glass_infra import _normal_chair, engine_profile

        # A real chain edit produces both the receipt and Undo.
        engine_profile()
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        from tests.unit.test_phase143_inference_assignments import _profile

        # Removing the first of two engines changes the chain at either width.
        _profile(get_database(), "lane12-second-engine")
        InferenceAssignmentService(get_database()).set_assignment(
            Principal(PrincipalKind.OWNER, "lane12-owner"),
            {"command_id": f"lane12-default-{width}", "expected_revision": 0, "scope": {"kind": "global"},
             "entries": [{"profile_id": "hs201-meeting-engine", "profile_revision": 1},
                         {"profile_id": "lane12-second-engine", "profile_revision": 1}]},
        )
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                _normal_chair(page)
                self._stage(page, "configure-settings", "engines")
                engines = page.locator("#surface-settings")
                engines.get_by_role("button", name="Edit Everything else", exact=True).click()
                editor = engines.get_by_test_id("settings-engines-editor")
                editor.get_by_role("button", name="Remove Hs201 Meeting Engine", exact=True).click()
                receipt = page.get_by_test_id("settings-engines-receipt")
                # The current pane draws receipt and Undo in flow. Their
                # rendered ink must remain separate when the receipt wraps.
                undo = engines.get_by_role("button", name="Undo", exact=True)
                undo.wait_for(timeout=T)
                receipt.filter(has_text="Set at").wait_for(timeout=T)
                undo.scroll_into_view_if_needed()
                _settle(page)
                rb, cb = receipt.evaluate(BOX_JS), undo.evaluate(BOX_JS)
                text = receipt.inner_text()
                # The text's own box (the span may be wider than its glyphs when it wraps).
                ink = receipt.evaluate("(e) => { const r = document.createRange(); r.selectNodeContents(e);"
                                       " const clip = e.closest('.kit-statusbar-items'); const cs = clip && getComputedStyle(clip).overflow === 'hidden' ? clip.getBoundingClientRect() : null;"
                                       " const rs = [...r.getClientRects()]; return rs.map((b) => ({x: b.left, r: cs ? Math.min(b.right, cs.right) : b.right, y: b.top, btm: b.bottom})); }")
                rb = receipt.evaluate("(e) => { const b = e.getBoundingClientRect(); const clip = e.closest('.kit-statusbar-items');"
                                      " const cs = clip && getComputedStyle(clip).overflow === 'hidden' ? clip.getBoundingClientRect() : null;"
                                      " return {x: b.left, y: b.top, r: cs ? Math.min(b.right, cs.right) : b.right, btm: b.bottom, w: b.width, h: b.height}; }")
                self.facts["B27"] = {"receipt": rb, "undo": cb, "text": text, "ink": ink}
                same_row = lambda b: not (b["btm"] <= cb["y"] or b["y"] >= cb["btm"])  # noqa: E731
                assert rb["r"] <= cb["x"] + 0.5 or not same_row(rb), self.facts["B27"]
                for line in ink:
                    if same_row(line):
                        assert line["r"] <= cb["x"] + 0.5, self.facts["B27"]
                assert text.startswith("Set at "), text
                self._shot(page, "B27-runson", width)
                if width == 393:
                    before_undo = _api(page, "GET", "/api/inference/assignments", token=FIT_TOKEN)
                    default = next(row for row in before_undo["rows"] if row["id"] == "global")
                    assert default["assignment"]["entries"][0]["profile_id"] == "lane12-second-engine", default
                    observed = undo.evaluate("(el) => {" + OWNERSHIP_JS + HIT_PROBE_JS + "return hs202Probe(el, 44, 'Engines'); }")
                    assert not observed["occluded"] and not observed["covered"] and not observed["bad"], observed
                    assert observed["w"] >= 44 and observed["h"] >= 44, observed
                    undo.click()
                    page.wait_for_function(
                        "() => /^Undone at /.test(document.querySelector('[data-testid=settings-engines-receipt]')?.textContent || '')"
                    )
                    after_undo = _api(page, "GET", "/api/inference/assignments", token=FIT_TOKEN)
                    restored = next(row for row in after_undo["rows"] if row["id"] == "global")
                    assert [entry["profile_id"] for entry in restored["assignment"]["entries"]] == [
                        "hs201-meeting-engine", "lane12-second-engine"], restored
                self._write("runson", width)
                assert not errors, errors
            finally:
                browser.close()
