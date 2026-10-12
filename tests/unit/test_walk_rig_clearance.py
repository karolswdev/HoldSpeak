"""H-rig-clearof: the real placement probe selects the viewport's contract."""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from playwright.sync_api import sync_playwright

from scripts import graph_walk as gw

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def page():
    with sync_playwright() as play:
        browser = play.chromium.launch()
        yield browser.new_page()
        browser.close()


@pytest.mark.parametrize("width, target", [(1440, "#capture"), (393, "#dock")])
def test_viewport_clearance_is_armed_and_rejects_real_overlap(page, width, target):
    page.set_viewport_size({"width": width, "height": 852})
    page.set_content(f"""<div id="slot"><div id="card"
      style="width:200px;height:80px">MEETING READY</div></div>
      <div id="{target[1:]}" style="position:absolute;top:200px;width:200px;height:50px">control</div>""")
    predicate = {
        "kind": "readable_text", "value": "MEETING READY",
        "clear_of_by_viewport": {
            "1440": [{"selector": "#capture", "required": True}],
            "393": [{"selector": "#dock", "required": True}],
        },
    }
    case = {"expected": {"observe_at": "#card", "predicate": predicate}}
    gw.arm_placement_probe(page, case)
    observed = gw.snapshot(page, case)
    assert observed.get("placement"), "per-width clearance must arm the probe"
    assert [item["selector"] for item in observed["placement"]["clear"]] == [target]
    assert gw.check_predicate(predicate, {}, observed)[0]
    # Use real DOM geometry. A card over a required control must still fail.
    page.locator(target).evaluate("el => { el.style.top = '20px'; el.style.zIndex = '-1'; }")
    observed = gw.snapshot(page, case)
    assert not gw.check_predicate(predicate, {}, observed)[0]
    page.locator(target).evaluate("el => el.remove()")
    observed = gw.snapshot(page, case)
    assert not gw.check_predicate(predicate, {}, observed)[0]


def test_clearance_does_not_silently_skip_an_undeclared_width(page):
    page.set_viewport_size({"width": 393, "height": 852})
    case = {"expected": {"observe_at": "#card", "predicate": {
        "kind": "readable_text", "value": "ready",
        "clear_of_by_viewport": {"1440": []},
    }}}
    with pytest.raises(gw.Blocked, match="393"):
        gw.arm_placement_probe(page, case)


def test_restart_trigger_accepts_ui_followups_in_the_actual_atlas_schema():
    atlas = json.loads((ROOT / "docs/internal/philo/graph/atlas-phase3.json").read_text())
    schema = json.loads((ROOT / "docs/internal/philo/graph/atlas.schema.json").read_text())
    case = next(c for c in atlas["cases"] if c["id"] == "case.closure.chain.s3_same_summary_after_restart.replayed")
    case["trigger"]["then"] = [{"kind": "ui", "action": "wait_for", "selector": "#summary", "at_width": 393}]
    Draft202012Validator(schema).validate(atlas)
    case["trigger"]["then"][0]["kind"] = "api"
    assert list(Draft202012Validator(schema).iter_errors(atlas))


def test_per_width_clearance_schema_rejects_a_misspelled_width():
    atlas = json.loads((ROOT / "docs/internal/philo/graph/atlas.json").read_text())
    schema = json.loads((ROOT / "docs/internal/philo/graph/atlas.schema.json").read_text())
    case = next(c for c in atlas["cases"] if c["id"] == "case.philo603.toast.arrival")
    case["expected"]["predicate"]["clear_of_by_viewport"] = {"393px": []}
    assert list(Draft202012Validator(schema).iter_errors(atlas))
