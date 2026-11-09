"""PHILO-4-02 fences for the readable, unobscured decision row."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
RIG_PATH = REPO / "scripts/graph_walk.py"
SPEC = importlib.util.spec_from_file_location("philo4_02_readable_rows_rig", RIG_PATH)
assert SPEC and SPEC.loader
rig = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rig)

ATLAS = REPO / "docs/internal/philo/graph/atlas-phase3.json"
SCHEMA = REPO / "docs/internal/philo/graph/atlas.schema.json"
GRAPH_SCHEMA = REPO / "docs/internal/philo/graph/graph.schema.json"
CASE_ID = "case.closure.chain.s5_next_day_brief_has_it"


def _snapshot(*, covered: bool) -> dict:
    """Take the same DOM snapshot as the rig, with a real hit-test fence."""
    playwright = pytest.importorskip(
        "playwright.sync_api", reason="readable-row fence needs Playwright"
    )
    html = """
      <style>
        html, body { margin: 0; width: 393px; height: 240px; }
        #decision-row { position: absolute; left: 16px; top: 24px;
          width: 240px; height: 56px; padding: 8px; box-sizing: border-box; }
        #capture-dock { position: absolute; left: 16px; top: 24px;
          width: 240px; height: 56px; z-index: 2; background: #fff; }
      </style>
      <div id="decision-row">Review decision: New</div>
      <div id="capture-dock" hidden></div>
    """
    with playwright.sync_playwright() as browser_type:
        browser = browser_type.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 393, "height": 240})
            page.set_content(html)
            if covered:
                page.locator("#capture-dock").evaluate(
                    "node => node.removeAttribute('hidden')"
                )
            return page.evaluate(rig._SNAPSHOT_JS, ["#decision-row", None, None])
        finally:
            browser.close()


def test_readable_text_uses_element_from_point_and_rejects_a_covering_dock():
    """A visible row is readable only when all sampled hit points are owned."""
    predicate = {"kind": "readable_text", "value": "Review decision: New"}
    uncovered = _snapshot(covered=False)
    covered = _snapshot(covered=True)

    ok, reading = rig.check_predicate(predicate, {}, uncovered)
    assert ok, reading
    ok, reading = rig.check_predicate(predicate, {}, covered)
    assert not ok, reading
    assert covered["hit_test"]["in_viewport"] is True
    assert covered["hit_test"]["all_owned"] is False


@pytest.mark.parametrize(
    "change",
    [
        lambda snap: snap.update(text=""),
        lambda snap: snap["hit_test"]["rect"].update(w=0),
        lambda snap: snap["hit_test"]["rect"].update(h=0),
        lambda snap: snap["hit_test"].update(in_viewport=False),
        lambda snap: snap["hit_test"].update(all_owned=False),
    ],
)
def test_readable_text_rejects_missing_text_or_unreadable_geometry(change):
    observation = _snapshot(covered=False)
    change(observation)
    ok, _reading = rig.check_predicate(
        {"kind": "readable_text", "value": "Review decision: New"},
        {},
        observation,
    )
    assert not ok


def test_atlas_declares_readable_text_for_the_as_written_chain_case():
    atlas = json.loads(ATLAS.read_text())
    case = next(case for case in atlas["cases"] if case["id"] == CASE_ID)
    expected = case["expected"]

    assert expected["observe_at"] == "[data-testid=arrival-brief-row]"
    assert expected["predicate"] == {
        "kind": "readable_text",
        "value": "Review decision: Keep summary retrieval on the local desk",
    }
    setup = case["setup"]
    selectors = [step.get("selector") for step in setup if isinstance(step, dict)]
    assert not any("arrival-brief-row button" in str(selector) for selector in selectors)
    assert not any("arrival-brief-more" in str(selector) for selector in selectors)
    assert any(step.get("kind") == "cli" and step.get("action") == "restart_hub"
               for step in setup)
    assert any(step.get("kind") == "check"
               and step.get("observe_at") == "[data-testid=meeting-summary-text]"
               and step.get("predicate", {}).get("kind") == "text_equals"
               for step in setup)


def test_readable_text_is_in_the_shared_schema_vocabulary():
    for path in (SCHEMA, GRAPH_SCHEMA):
        schema = json.loads(path.read_text())
        predicate = schema["$defs"]["case"]["properties"]["expected"]["properties"]["predicate"]
        assert "readable_text" in predicate["properties"]["kind"]["enum"], path
