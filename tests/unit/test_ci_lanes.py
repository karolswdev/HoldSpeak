"""The CI lanes stay as ruled: metal is opt-in, the live-bus proof is mandatory."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_real_hardware_lane_is_named_and_explicitly_opt_in() -> None:
    config = (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "DICTATION_PIPELINE_GUIDE.md").read_text(
        encoding="utf-8"
    )
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(
        encoding="utf-8"
    )
    web_package = (ROOT / "web" / "package.json").read_text(encoding="utf-8")

    assert '"--run-metal"' in config
    assert '"metal" in item.keywords' in config
    assert "-m metal --run-metal" in guide
    assert 'e2e and not metal' in workflow
    assert 'vitest run --maxWorkers=2' in web_package


def test_e2e_job_builds_bundle_installs_browser_and_requires_live_bus() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(
        encoding="utf-8"
    )
    e2e = workflow.split("  e2e-tests:", 1)[1].split("  linux-smoke:", 1)[0]

    for required in (
        "actions/setup-node@v4",
        "npm ci",
        "npm run build",
        "playwright install chromium",
        'HOLDSPEAK_REQUIRE_LIVE_BUS: "1"',
        "tests/e2e/test_live_bus.py",
    ):
        assert required in e2e
