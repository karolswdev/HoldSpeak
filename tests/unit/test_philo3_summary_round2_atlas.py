"""The actual failure recipes must distinguish state and the displayed cause."""

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("case_id", "state"),
    [
        ("case.j6.run_summary.intel_failed", "FAILED"),
        ("case.j6.run_summary.retrying", "RETRYING"),
    ],
)
def test_actual_j6_recipe_requires_plain_provider_cause(case_id, state):
    atlas = json.loads((ROOT / "docs/internal/philo/graph/atlas.json").read_text())
    case = next(case for case in atlas["cases"] if case["id"] == case_id)
    replay = next(step for step in case["setup"] if step.get("substitute") == "engine_reply")
    reply = json.loads((ROOT / replay["reply"]).read_text())
    assert reply["error"]
    expected = case["expected"]
    assert expected["observe_at"] == "[data-testid=arrival-summary-status]"
    assert expected["predicate"] == {
        "kind": "text_equals",
        "value": f"{state}\nLAST ATTEMPT · 192.168.1.43 · LAN\nLAST ERROR · PROVIDER FAILED",
    }
    assert {"method": "GET", "path": "/api/intel/summary"} in expected["reads"]
