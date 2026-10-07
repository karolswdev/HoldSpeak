"""The test suite never runs the owner's real ``gh`` or ``acli``.

``tests/conftest.py`` sets ``HOLDSPEAK_TEST_NO_REAL_CLI=1`` (a hub the
tests start inherits it). With the flag set, a production default runner
that would start ``gh`` or ``acli`` refuses by name
(``real_cli_refused_in_tests``) unless the program it resolves to lives
under the temp directory: a test's own stub on ``PATH`` still runs. A test
that injects a runner never reaches this guard. Outside the test suite the
flag is not set and nothing changes.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Sequence

TEST_FLAG = "HOLDSPEAK_TEST_NO_REAL_CLI"
GUARDED = frozenset({"gh", "acli"})


class RealCliRefusedInTests(PermissionError):
    """A test reached the real ``gh``/``acli`` through a default runner."""

    code = "real_cli_refused_in_tests"


def _temp_roots() -> list[str]:
    roots = {os.path.realpath(tempfile.gettempdir()), os.path.realpath("/tmp")}
    if Path("/var/folders").exists():
        roots.add(os.path.realpath("/var/folders"))
    return sorted(roots)


def refuse_real_cli_in_tests(argv: Sequence[str]) -> None:
    if os.environ.get(TEST_FLAG) != "1" or not argv:
        return
    program = str(argv[0])
    if Path(program).name not in GUARDED:
        return
    exe = program if os.sep in program else shutil.which(program)
    if exe is None:
        return  # not installed: the caller's own "missing" path answers
    real = os.path.realpath(exe)
    if any(real.startswith(root + os.sep) for root in _temp_roots()):
        return  # a test's own stub
    raise RealCliRefusedInTests(
        f"real_cli_refused_in_tests: {Path(program).name} at {real}; inject a runner"
    )
