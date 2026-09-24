"""Scoped PHILO-4-04 verification, with an isolated HOME per command."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[5]
PROOF = ROOT / "docs/internal/philo/phase-4/headline"
PYTHON_TESTS = [
    "tests/unit/test_philo4_04_headline_storage.py",
    "tests/unit/test_brief_shelf.py",
    "tests/unit/test_philo_4_01_generate.py",
    "tests/unit/test_philo4_04_atlas_contracts.py",
    "tests/unit/test_philo_graph_atlas.py",
    "tests/unit/test_ux_canon_ratchet.py",
    "tests/unit/test_evidence_scratch_guard.py",
]
WEB_TESTS = [
    "src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx",
    "src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx",
    "src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx",
    "src/desk/chair/__tests__/briefReceiptRendered202.test.tsx",
    "src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx",
    "src/desk/chair/__tests__/decisionRows.philo402.test.tsx",
]


def run(label, command, cwd=ROOT):
    env = os.environ.copy()
    owner_home = Path(env["HOME"])
    node = owner_home / ".nvm/versions/node/v22.21.0/bin"
    if node.is_dir():
        env["PATH"] = str(node) + os.pathsep + env["PATH"]
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(owner_home / "Library/Caches/ms-playwright")
    env["npm_config_cache"] = str(owner_home / ".npm")
    env["NO_COLOR"] = "1"
    print(f"\n{label}: {command!r}", flush=True)
    with tempfile.TemporaryDirectory(prefix="philo404-verify-") as home:
        env["HOME"] = home
        result = subprocess.run(command, cwd=cwd, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = f"command: {command!r}\ncwd: {cwd}\nexit: {result.returncode}\n\n{result.stdout}"
    (PROOF / f"final-{label}.log").write_text(log)
    print(result.stdout, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    run("collect-python", ["uv", "run", "--no-sync", "pytest", "--collect-only", "-q", *PYTHON_TESTS])
    run("green-python", ["uv", "run", "--no-sync", "pytest", "-q", *PYTHON_TESTS])
    run("collect-rendered", ["node_modules/.bin/vitest", "list", *WEB_TESTS], ROOT / "web")
    run("green-rendered", ["node_modules/.bin/vitest", "run", *WEB_TESTS, "--maxWorkers=2"], ROOT / "web")
    for reference in ("philo_graph_reference", "philo_api_reference", "philo_boundary_census"):
        run(reference, ["uv", "run", "--no-sync", "python", f"scripts/{reference}.py", "--check"])
    run("diff-check", ["git", "diff", "--check"])
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    churn = [line for line in status.splitlines()
             if line.startswith(" M") and "pm/roadmap/holdspeak/" in line]
    assert not churn, churn
    print("Evidence churn: no ' M' paths under pm/roadmap/holdspeak/", flush=True)
