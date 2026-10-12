"""scripts/quick_check_affected.py: the test files a change affects (the fast
cycle's quick check; Astra's post-merge review of its first version)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts" / "quick_check_affected.py"


def _affected(changed: list[str], quick_tests: str = "") -> tuple[int, list[str], str]:
    env = {**os.environ, "QUICK_TESTS": quick_tests}
    run = subprocess.run([sys.executable, str(HELPER)], input="\n".join(changed), text=True,
                         capture_output=True, env=env, cwd=ROOT, timeout=120)
    return run.returncode, [line for line in run.stdout.splitlines() if line], run.stderr


def test_a_from_package_import_module_is_matched() -> None:
    """`from holdspeak.memory import pages` names the module by its package
    plus its name; the first version only matched `holdspeak.memory.pages`."""
    rc, tests, _ = _affected(["holdspeak/memory/pages.py"])
    assert rc == 0
    assert "tests/unit/test_memory_slice5_pages.py" in tests  # from holdspeak.memory.pages import ...
    # `from holdspeak.memory import pages as pages_module`: the first version missed it.
    assert "tests/unit/test_memory_slice6_reflect.py" in tests


def test_a_package_init_matches_its_package() -> None:
    rc, tests, _ = _affected(["holdspeak/people/__init__.py"])
    assert rc == 0
    assert "tests/unit/test_people_service.py" in tests  # from holdspeak.people import ...


def test_a_changed_script_maps_to_its_tests() -> None:
    rc, tests, _ = _affected(["scripts/quick_check_affected.py"])
    assert rc == 0
    assert "tests/unit/test_quick_check_affected.py" in tests  # names scripts/quick_check_affected.py


def test_changed_uat_and_e2e_test_files_are_included_directly() -> None:
    uat = next(p for p in sorted((ROOT / "tests" / "uat").rglob("test_*.py")) if "_parked" not in p.as_posix())
    rel = uat.relative_to(ROOT).as_posix()
    rc, tests, _ = _affected([rel, "tests/e2e/test_philo17_today_glass.py"])
    assert rc == 0
    assert rel in tests and "tests/e2e/test_philo17_today_glass.py" in tests


def test_quick_tests_adds_files_and_a_missing_one_is_an_error() -> None:
    rc, tests, _ = _affected(["README.md"], "tests/unit/test_people_service.py")
    assert rc == 0 and tests == ["tests/unit/test_people_service.py"]
    rc, _, err = _affected(["README.md"], "tests/unit/test_no_such_file.py")
    assert rc == 2 and "missing" in err
