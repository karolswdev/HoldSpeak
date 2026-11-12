"""Exercise quick-check verdicts and retry files without running its suites."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def check_repo(tmp_path):
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    for name in ("quick_check.sh", "quick_check_memo.py"):
        shutil.copyfile(ROOT / "scripts" / name, scripts / name)
    for args in (("init", "-q"), ("add", "scripts"),
                 ("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "seed")):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
    (scripts / "changed.py").write_text("# An untracked change selects pytest.\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    uv = bin_dir / "uv"
    # Stub the suite boundary only. The actual shell, retry writer, verdict
    # and green memo all run. No nested lock or real pytest process is started.
    uv.write_text(f"#!{sys.executable}\n" + '''
import os
import json
import subprocess
import sys
from pathlib import Path

args = sys.argv[1:]
if args[0] == "run":
    args = args[1:]
if args[:2] == ["--project", ".."]:
    args = args[2:]
if args[:2] == ["python", "scripts/quick_check_affected.py"]:
    print("tests/unit/test_selected.py")
elif args[:2] == ["python", "scripts/vitest_related.py"]:
    print("src/conductor.test.tsx")
elif args[:2] == ["python", "scripts/quick_check_memo.py"]:
    sys.exit(subprocess.call([sys.executable, *args[1:]]))
elif args[0] == "python" and args[1] in ("scripts/test_lock.py", "../scripts/test_lock.py"):
    command = args[args.index("--") + 1:]
    assert command[:3] == ["uv", "run", "pytest"] or command[0] == "./node_modules/.bin/vitest", args
    with open(os.environ["QUICK_STUB_COMMANDS"], "a") as calls:
        calls.write(json.dumps(command) + "\\n")
    print(Path(os.environ["QUICK_STUB_LOG"]).read_text())
    sys.exit(int(os.environ["QUICK_STUB_RC"]))
else:
    raise AssertionError(args)
''')
    uv.chmod(0o755)
    return repo, bin_dir


def _run(check_repo, log: str, rc: int, *, retry: bool = False):
    repo, bin_dir = check_repo
    output = repo / ".tmp" / "stub.log"
    output.parent.mkdir(exist_ok=True)
    output.write_text(log)
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
           "QUICK_STUB_LOG": str(output), "QUICK_STUB_RC": str(rc),
           "QUICK_STUB_COMMANDS": str(repo / ".tmp/commands.jsonl"), "GIT_CONFIG_GLOBAL": "/dev/null"}
    return subprocess.run(["bash", "scripts/quick_check.sh", "--retry" if retry else "HEAD"],
                          cwd=repo, env=env, capture_output=True, text=True, timeout=30)


def test_retry_ids_come_only_from_test_paths_in_the_short_summary(check_repo):
    run = _run(check_repo, """------------------------------ Captured log call ------------------------------
ERROR    holdspeak.program_runner:program_runner.py:394 no such table: programs
ERROR    holdspeak.workbench_conductor:workbench_conductor.py:550 night tick
ERROR tests/unit/test_logged.py::test_not_a_summary captured text
=========================== short test summary info ============================
FAILED tests/unit/test_selected.py::test_write - AssertionError
ERROR tests/unit/test_selected.py::test_setup - RuntimeError
ERROR holdspeak.program_runner:program_runner.py:394 not a test path
1 failed, 1 error in 0.12s
""", 1)
    assert run.returncode == 1, run.stdout + run.stderr
    rows = (check_repo[0] / ".tmp/quick-check/retry.txt").read_text().splitlines()
    assert {row for row in rows if row.startswith("ids ")} == {
        "ids pytest tests/unit/test_selected.py::test_write",
        "ids pytest tests/unit/test_selected.py::test_setup",
    }


@pytest.mark.parametrize("rc", [0, 5])
def test_retry_with_no_test_is_red_and_does_not_write_a_green_memo(check_repo, rc):
    failed = _run(check_repo, """=========================== short test summary info ============================
FAILED tests/unit/test_selected.py::test_write - AssertionError
1 failed in 0.12s
""", 1)
    assert failed.returncode == 1, failed.stdout + failed.stderr
    retry = _run(check_repo, "no tests ran in 0.61s\n", rc, retry=True)
    assert retry.returncode == 1, retry.stdout + retry.stderr
    assert "no test ran: RED" in retry.stdout
    assert "QUICK CHECK GREEN" not in retry.stdout
    memo = check_repo[0] / ".tmp/quick-check/green.json"
    assert not memo.exists() or "pytest" not in json.loads(memo.read_text())
    assert "step pytest" in (check_repo[0] / ".tmp/quick-check/retry.txt").read_text()


def test_retry_that_runs_the_failed_test_records_green(check_repo):
    _run(check_repo, """=========================== short test summary info ============================
FAILED tests/unit/test_selected.py::test_write - AssertionError
1 failed in 0.12s
""", 1)
    run = _run(check_repo, "1 passed in 0.12s\n", 0, retry=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "QUICK CHECK GREEN" in run.stdout
    memo = json.loads((check_repo[0] / ".tmp/quick-check/green.json").read_text())
    assert "pytest" in memo
    assert not (check_repo[0] / ".tmp/quick-check/retry.txt").exists()


@pytest.mark.parametrize("project", [None, "desk"])
def test_vitest_retry_keeps_the_file_and_its_project(check_repo, project):
    repo, _bin = check_repo
    source = repo / "web/src/changed.ts"
    source.parent.mkdir(parents=True)
    source.write_text("export {};\n")
    retry_file = repo / ".tmp/quick-check/retry.txt"
    retry_file.parent.mkdir(parents=True)
    retry_file.write_text("base HEAD\nstep vitest\n")
    prefix = f"|{project}| " if project else ""
    failed = _run(check_repo, f""" FAIL  {prefix}src/conductor.test.tsx > Stop keeps its agent
 FAIL  {prefix}src/conductor.test.tsx > Stop keeps its receipt
 Test Files  1 failed (1)
 Tests  2 failed (2)
""", 1, retry=True)
    assert failed.returncode == 1, failed.stdout + failed.stderr
    project_arg = [f"--project={project}"] if project else []
    assert [row for row in retry_file.read_text().splitlines() if row.startswith("ids ")] == [
        " ".join(["ids", "vitest", "src/conductor.test.tsx", *project_arg])
    ]
    passed = _run(check_repo, " Test Files  1 passed (1)\n Tests  2 passed (2)\n", 0, retry=True)
    assert passed.returncode == 0, passed.stdout + passed.stderr
    commands = [json.loads(line) for line in (repo / ".tmp/commands.jsonl").read_text().splitlines()]
    assert commands[-1] == ["./node_modules/.bin/vitest", "run", "--maxWorkers=4",
                            "src/conductor.test.tsx", *project_arg]
    assert not retry_file.exists()
