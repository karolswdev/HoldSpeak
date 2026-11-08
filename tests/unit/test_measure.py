"""scripts/measure.py prints every section of rule 7 on a stub checkout.

git is a fake on PATH; --no-gh and --no-hub skip GitHub and the hub.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "measure.py"
SEAMS = REPO / "scripts" / "measure_seams.json"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _stub_checkout(root: Path) -> None:
    _write(root / "holdspeak" / "big.py", "x = 1\n" * 40)
    _write(root / "holdspeak" / "services" / "clean_service.py", "import os\n")
    _write(root / "holdspeak" / "services" / "bad_service.py", "from holdspeak.web.routes import x\n")
    _write(root / "holdspeak" / "web" / "routes.py", "x = 1\n")
    _write(root / "holdspeak" / "web_server.py", "def _create_app():\n    pass\n_create_app()\n")
    _write(root / "holdspeak" / "keystore.py", "keyring.get_password('a', 'b')\n")
    _write(root / "holdspeak" / "other.py", "keyring.get_password('a', 'b')\n")
    _write(root / "web" / "src" / "App.tsx", "export const a = 1;\n" * 5)
    _write(root / "web" / "src" / "walk.css", ".walk-dot {}\n.pg-wiz-dot {}\n")
    built = root / "holdspeak" / "static" / "_built"
    _write(built / "build-id.json", json.dumps({"build_id": "stub123"}))
    _write(built / "assets" / "desk-abc.js", "console.log(1);\n" * 200)
    _write(built / "assets" / "small-def.js", "1;\n")


def _fake_git(bin_dir: Path) -> None:
    today = dt.date.today().isoformat()
    log = (
        f"{today}\tThe walk link is the tailnet name (#1840)\n"
        f"{today}\tA plain commit without a number\n"
        f"{today}\tMerge pull request #12 from x/y\n"
    )
    _write(bin_dir / "git", f"#!/bin/sh\ncat <<'EOF'\n{log}EOF\n")
    (bin_dir / "git").chmod((bin_dir / "git").stat().st_mode | stat.S_IEXEC)


def test_measure_prints_every_section_on_a_stub(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _stub_checkout(root)
    bin_dir = tmp_path / "bin"
    _fake_git(bin_dir)
    out_dir = tmp_path / "out"
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(root), "--out", str(out_dir), "--no-hub", "--no-gh"],
        capture_output=True, text=True, env=env, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stderr
    text = result.stdout
    for section in ("Merges per day", "Hours, PR open to merge", "Web bundle", "Hub cold start",
                    "Largest Python files", "Largest TS files", "Python files per package",
                    "Fence", "Seams to remove (lines)"):
        assert f"| {section} |" in text, section
    today = dt.date.today().isoformat()
    assert f"| Merges per day | {today} | 2 |" in text
    assert "| Merges per day | Total, 7 days | 2 |" in text
    assert "| Web bundle | Build id | stub123 |" in text
    assert "| Web bundle | JS files | 2 |" in text
    assert "Large chunk: desk-abc.js" in text
    assert "| Hub cold start | Skipped | --no-hub |" in text
    assert "| Hours, PR open to merge | Skipped | --no-gh |" in text
    assert "| Largest Python files | holdspeak/big.py | 40 lines |" in text
    assert "must be 0) | 1 |" in text
    assert "| Two step-dot implementations (wizard and walk) | 2 |" in text
    assert "| _create_app lines in web_server.py | 2 |" in text
    assert "| Keystore readers outside keystore.py | 1 |" in text
    written = (out_dir / f"{today}.md").read_text()
    assert "| Merges per day |" in written and written.startswith(f"# Measure {today}")


def test_seams_json_parses_and_every_pattern_compiles() -> None:
    data = json.loads(SEAMS.read_text())
    assert data["seams"], "the seam list is empty"
    for seam in data["seams"]:
        assert seam["name"] and seam["paths"]
        re.compile(seam["pattern"])
        for rel in seam["paths"]:
            assert (REPO / rel).exists(), f"{seam['name']}: {rel} is missing"
