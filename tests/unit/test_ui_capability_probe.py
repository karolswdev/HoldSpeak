"""Optional APIs must not erase the rest of a browser capability report."""
from __future__ import annotations

import json
import subprocess

import pytest

from scripts.probe_ui_capabilities import FEATURES


@pytest.mark.parametrize("missing", ["CSS", "PerformanceObserver", "both"])
def test_absent_optional_api_keeps_independent_results(missing: str) -> None:
    setup = """globalThis.HTMLElement = {prototype: {popover: null}};
globalThis.Element = {prototype: {setPointerCapture() {}}};
globalThis.document = {startViewTransition() {}};
globalThis.CSS = {supports() { return true; }};
globalThis.PerformanceObserver = {supportedEntryTypes: ['event', 'long-animation-frame']};
"""
    if missing in {"CSS", "both"}:
        setup += "delete globalThis.CSS;\n"
    if missing in {"PerformanceObserver", "both"}:
        setup += "delete globalThis.PerformanceObserver;\n"
    run = subprocess.run(
        ["node", "-e", setup + f"console.log(JSON.stringify(({FEATURES})()));"],
        check=True, capture_output=True, text=True,
    )
    report = json.loads(run.stdout)
    assert len(report) == 10 and all(isinstance(value, bool) for value in report.values())
    assert report["popover"] and report["pointerCapture"] and report["viewTransitions"]
    assert report["anchorName"] is (missing not in {"CSS", "both"})
    assert report["eventTiming"] is (missing not in {"PerformanceObserver", "both"})
