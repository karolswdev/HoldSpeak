"""The formerly skipped live-bus proof stays mandatory in hosted CI."""
from pathlib import Path


def test_e2e_job_builds_bundle_installs_browser_and_requires_live_bus() -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github" / "workflows" / "test.yml").read_text(
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
