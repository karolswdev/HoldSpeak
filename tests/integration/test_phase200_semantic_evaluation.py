"""HS-200-08: the evaluation runner, end to end, over the real product paths.

The model is substituted and nothing else is.  ``--engine canned`` points the
product's own endpoint profile at a local OpenAI-compatible stub that answers
with recorded text, so the route plan, the admission, the adapters, the
Interview thread, the meeting plugin chain and the Project update drafter are
all the product's own code on the way to a report.

These tests drive the driver the way the owner does -- through the command
line, in a subprocess with an isolated HOME -- so what they prove is the
invocation the SCORING protocol names, not a private entry point.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.phase200 import checks

REPO = Path(__file__).resolve().parents[2]
DRIVER = REPO / "scripts" / "phase200_eval.py"
CANNED = REPO / "tests" / "fixtures" / "phase200" / "canned" / "harness.json"

pytestmark = pytest.mark.integration


def _run(tmp_path: Path, *args: str, canned: Path = CANNED) -> tuple[subprocess.CompletedProcess, dict]:
    """Run the driver in a subprocess with an isolated HOME; return its report."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    report_path = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable, str(DRIVER), "run",
            "--engine", "canned", "--canned", str(canned),
            "--report", str(report_path),
            "--raw", str(tmp_path / "raw.json"),
            *args,
        ],
        cwd=REPO,
        env={**os.environ, "HOME": str(home)},
        capture_output=True,
        text=True,
        timeout=600,
    )
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    return result, report


@pytest.fixture(scope="module")
def three_categories(tmp_path_factory) -> tuple[subprocess.CompletedProcess, dict, dict]:
    """One episode from each category, through its real product path."""
    tmp_path = tmp_path_factory.mktemp("phase200-eval")
    result, report = _run(tmp_path, "--episode", "IV-01", "--episode", "MX-01", "--episode", "UP-01")
    raw = json.loads((tmp_path / "raw.json").read_text())
    assert report, result.stdout + result.stderr
    return result, report, raw


class TestRunnerEndToEnd:
    def test_the_run_completes_over_every_category(self, three_categories):
        result, report, _ = three_categories
        assert result.returncode == 0, result.stdout + result.stderr
        assert report["totals"]["episodes"] == 3
        assert {row["category"] for row in report["episodes"]} == set(checks.CATEGORIES)
        assert all(not row["error"] for row in report["episodes"]), report["episodes"]

    def test_the_report_names_model_route_build_and_context(self, three_categories):
        _, report, _ = three_categories
        assert report["engine"] == "canned"
        route = report["route"]
        assert route["state"] == "READY", route
        assert route["plan_id"].startswith("irp_")
        assert route["boundary"], route
        assert route["host"], route
        assert route["endpoint"].startswith("http://127.0.0.1:")
        assert report["build"], "the report must name the build it ran"
        for row in report["episodes"]:
            assert len(row["material_sha256"]) == 64

    def test_the_report_names_failures_support_latency_and_review_effort(self, three_categories):
        _, report, _ = three_categories
        assert report["totals"]["critical_failures"] == 0
        assert report["failures_by_kind"] == {}
        assert report["support_judgments"], "the update leg must produce claim support"
        assert report["latency_ms"]["count"] == 3
        assert report["latency_ms"]["max"] > 0
        assert set(report["review_effort"]) == {
            "critical_failures", "held_out_episodes", "items_to_inspect", "total"
        }

    def test_the_llm_judge_is_off_and_never_gating(self, three_categories):
        _, report, _ = three_categories
        assert report["judge"] == {"enabled": False, "note": "supplementary only; never gating"}

    def test_the_interview_leg_ran_the_real_thread(self, three_categories):
        _, _, raw = three_categories
        interview = raw["IV-01"]
        assert len(interview["turns"]) == 3, "every prior owner turn is replayed as a real turn"
        assert "2026-04-14" in interview["text"]
        assert not interview["error"]

    def test_the_meeting_leg_ran_the_real_plugin_chain(self, three_categories):
        _, _, raw = three_categories
        meeting = raw["MX-01"]
        assert meeting["plugin_statuses"]["decision_capture"] == "success"
        assert meeting["plugin_statuses"]["action_owner_enforcer"] == "success"
        assert meeting["artifacts_saved"] >= 1
        # An unstated due date comes back as a typed unknown, not a guess.
        assert meeting["fields"]["due_date"] is None
        assert meeting["fields"]["action_owner"] == "Priya"

    def test_the_update_leg_ran_the_model_drafter_not_the_fallback(self, three_categories):
        _, _, raw = three_categories
        update = raw["UP-01"]
        assert update["generator"].startswith("model:"), (
            f"the update leg fell back to {update['generator']!r}; the run measured no model"
        )
        assert update["claims"], "a drafted update must carry claims"
        assert {claim["support"] for claim in update["claims"]} <= set(checks.UNSUPPORTED_STATES) | {"supported"}
        assert update["ref_map"], "the run must record how episode refs map to product refs"


class TestCriticalFailureIsCaught:
    def test_an_invented_value_fails_the_run_and_its_exit_code(self, tmp_path):
        """A model that restates a corrected fact fails, whatever else passed."""
        canned = tmp_path / "bad.json"
        canned.write_text(json.dumps({
            "default": "unknown",
            "episodes": {
                "MX-02": [
                    {
                        "match": "open_questions",
                        "text": "```json\n{\"decisions\": [{\"decision\": "
                                "\"The cutover is on 2026-05-06\", \"rationale\": null}], "
                                "\"open_questions\": []}\n```",
                    },
                    {
                        "match": "action_items",
                        "text": "```json\n{\"action_items\": []}\n```",
                    },
                ]
            },
        }))
        result, report = _run(tmp_path, "--episode", "MX-02", "--episode", "MX-01", canned=canned)

        assert report["totals"]["critical_failures"] == 1, report["episodes"]
        assert report["critical_verdict"] == "fail"
        assert result.returncode == 1, "a critical failure must fail the command"
        assert checks.FAILURE_SUPERSEDED_RESTATED in report["failures_by_kind"]
        assert "MX-02" in report["review_effort"]["critical_failures"]

    def test_a_failed_trial_is_retained_not_dropped(self, tmp_path):
        """An episode that raises is recorded with its error, not silently skipped."""
        canned = tmp_path / "empty.json"
        canned.write_text(json.dumps({"default": "unknown", "episodes": {}}))
        _, report = _run(tmp_path, "--episode", "UP-02", "--repeat", "2", canned=canned)
        assert report["totals"]["episodes"] == 2, "a repeated trial keeps both runs"
        assert report["repeat"] == 2


class TestSupplementaryJudge:
    def test_the_judge_is_a_column_and_never_a_verdict(self, tmp_path):
        """--judge adds a scored column. It cannot lift or lower a verdict."""
        result, report = _run(tmp_path, "--episode", "MX-01", "--judge")
        judge = report["judge"]
        assert judge["enabled"] is True
        assert judge["note"] == "supplementary only; never gating"
        assert set(judge["scores"]) == {"MX-01"}
        # The verdict is the deterministic one, whatever the judge answered.
        assert report["critical_verdict"] == "pass"
        assert result.returncode == 0
        assert "judge" not in json.dumps(report["totals"])


class TestSelection:
    def test_the_held_out_split_can_be_run_alone(self, tmp_path):
        _, report = _run(tmp_path, "--split", "held_out", "--category", "update", "--limit", "1")
        assert report["totals"]["episodes"] == 1
        assert report["episodes"][0]["split"] == checks.SPLIT_HELD_OUT
        assert report["review_effort"]["total"] == 1, "every held-out episode needs a reviewer"
