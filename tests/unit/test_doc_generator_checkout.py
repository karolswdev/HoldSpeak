"""Documentation generators must inspect the checkout that contains them."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("script", ["gen_api_surface.py", "generate_capability_docs.py"])
def test_shared_environment_cannot_select_another_checkout(tmp_path: Path, script: str) -> None:
    stale = tmp_path / "other-checkout"
    for package in ("holdspeak", "scripts"):
        folder = stale / package
        folder.mkdir(parents=True)
        # HoldSpeak is a regular package; scripts is a namespace in the repo.
        marker = "__init__.py" if package == "holdspeak" else "validate_architecture.py"
        (folder / marker).write_text('raise RuntimeError("wrong checkout imported")\n')
    env = os.environ.copy()
    env["PYTHONPATH"] = str(stale)
    probe = """
import runpy, sys
from pathlib import Path
namespace = runpy.run_path(sys.argv[1], run_name="documentation_checkout_probe")
import holdspeak
import scripts.validate_architecture as validator
root = Path(sys.argv[2]).resolve()
assert Path(holdspeak.__file__).resolve().is_relative_to(root)
assert Path(validator.__file__).resolve().is_relative_to(root)
assert namespace.get("REPO", namespace.get("ROOT")).resolve() == root
"""
    result = subprocess.run(
        [sys.executable, "-c", probe, str(ROOT / "scripts" / script), str(ROOT)],
        cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
