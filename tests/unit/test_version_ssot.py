"""The version has one source of truth and cannot drift.

`pyproject.toml` is the single source of truth. `holdspeak.__version__`
resolves from the installed package metadata (which is written from
`pyproject.toml`), so the two must agree. This test is the guard that the
`0.1.0` / `0.2.1` split that prompted Phase 50 cannot come back.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import holdspeak


def _pyproject_version() -> str:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    return data["project"]["version"]


def test_code_version_matches_pyproject() -> None:
    assert holdspeak.__version__ == _pyproject_version()


def test_version_is_not_the_unknown_fallback() -> None:
    # Running the test suite means the package is importable; the fallback
    # placeholder should never be what we resolve to.
    assert holdspeak.__version__ != "0.0.0+unknown"


def test_doctor_runtime_check_reports_version() -> None:
    from holdspeak.commands.doctor import _check_runtime

    check = _check_runtime()
    assert holdspeak.__version__ in check.detail


def test_setup_status_reports_version() -> None:
    from holdspeak.setup_status import build_setup_status

    status = build_setup_status(skip_network=True)
    assert status["version"] == holdspeak.__version__
