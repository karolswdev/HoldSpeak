"""scripts/measure.py prints every section of rule 7 on a stub checkout.

git (and gh) are fakes on PATH; --no-gh and --no-hub skip GitHub and the hub.
HOME is a temp folder in every run, so the walks read are the fake ones.
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
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "HOME": str(tmp_path / "home")}
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
    assert "| Desk open (1440 wide, new desk, cold cache) | Skipped | --no-hub |" in text
    assert "| Hours, PR open to merge | Skipped | --no-gh |" in text
    assert "| Hours, first commit to merge (proxy for finding to main) | Skipped | --no-gh |" in text
    assert "| Presses by him, last 24 h | Walks | 0 |" in text
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


def _iso(moment: dt.datetime) -> str:
    return moment.isoformat()


def _run_measure(tmp_path: Path, extra_env: dict[str, str], *args: str) -> str:
    root = tmp_path / "repo"
    _stub_checkout(root)
    bin_dir = tmp_path / "bin"
    _fake_git(bin_dir)
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
           "HOME": str(tmp_path / "home"), **extra_env}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(root), "--no-hub", *args],
        capture_output=True, text=True, env=env, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_presses_reads_two_walks_and_the_bundles(tmp_path: Path) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    feedback = tmp_path / "home" / ".local" / "share" / "holdspeak" / "feedback"
    t0 = now - dt.timedelta(hours=2)
    # Walk one: three presses (one replaced), first to last 120 s.
    _write(feedback / "walks" / ("a" * 32) / "walk.json", json.dumps({
        "created_at": _iso(t0),
        "answers": {
            "one": {"at": _iso(t0 + dt.timedelta(seconds=60)), "choice": "Keep",
                    "earlier": [{"at": _iso(t0), "choice": "skip"}]},
            "two": {"at": _iso(t0 + dt.timedelta(seconds=120)), "choice": "words", "words": "No."},
        },
    }))
    # Walk two: two presses 40 s apart, plus a press from two days ago.
    t1 = now - dt.timedelta(hours=1)
    _write(feedback / "walks" / ("b" * 32) / "walk.json", json.dumps({
        "created_at": _iso(t1),
        "answers": {
            "one": {"at": _iso(t1), "choice": "Redo"},
            "two": {"at": _iso(t1 + dt.timedelta(seconds=40)), "choice": "Keep"},
            "old": {"at": _iso(now - dt.timedelta(days=2)), "choice": "Keep"},
        },
    }))
    # An old walk with no answers does not count.
    _write(feedback / "walks" / ("c" * 32) / "walk.json", json.dumps({
        "created_at": _iso(now - dt.timedelta(days=3)), "answers": {},
    }))
    _write(feedback / "f1" / "report.json", json.dumps({"captured_at": _iso(now - dt.timedelta(hours=3))}))
    _write(feedback / "f2" / "report.json", json.dumps({"captured_at": _iso(now - dt.timedelta(days=2))}))
    text = _run_measure(tmp_path, {}, "--no-gh", "--no-write")
    label = "| Presses by him, last 24 h |"
    assert f"{label} Walks | 2 |" in text
    assert f"{label} Walks with an answer | 2 |" in text
    assert f"{label} Answers: Keep | 2 |" in text
    assert f"{label} Answers: Redo | 1 |" in text
    assert f"{label} Answers: words | 1 |" in text
    assert f"{label} Answers: skip | 1 |" in text
    assert f"{label} Answers, total | 5 |" in text
    assert f"{label} Median s, first to last answer of a walk | 80 s |" in text
    assert f"{label} Feedback bundles | 1 |" in text


def _fake_gh(bin_dir: Path, payload: list[dict]) -> None:
    """`gh pr list` answers the PRs without commits; `gh pr view <n>` answers
    one PR's commits, as the real gh does."""
    data = bin_dir / "gh-data"
    _write(data / "list.json", json.dumps([{k: v for k, v in pr.items() if k != "commits"} for pr in payload]))
    for pr in payload:
        _write(data / f"view-{pr['number']}.json", json.dumps({"commits": pr["commits"]}))
    _write(bin_dir / "gh", f"#!/bin/sh\nif [ \"$2\" = list ]; then cat '{data}/list.json'; "
                          f"else cat '{data}'/view-$3.json; fi\n")
    (bin_dir / "gh").chmod((bin_dir / "gh").stat().st_mode | stat.S_IEXEC)


def test_finding_to_main_proxy_reads_the_first_commit(tmp_path: Path) -> None:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    merged = now - dt.timedelta(hours=1)
    z = lambda moment: moment.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    payload = [
        {"number": 1, "createdAt": z(merged - dt.timedelta(hours=1)), "mergedAt": z(merged),
         "commits": [{"authoredDate": z(merged - dt.timedelta(hours=2))},
                     {"authoredDate": z(merged - dt.timedelta(hours=6))}]},
        {"number": 2, "createdAt": z(merged - dt.timedelta(hours=3)), "mergedAt": z(merged),
         "commits": [{"authoredDate": z(merged - dt.timedelta(hours=4))}]},
        {"number": 3, "createdAt": z(merged - dt.timedelta(hours=1)), "mergedAt": z(merged),
         "commits": [{"authoredDate": z(merged - dt.timedelta(hours=8))}]},
        {"number": 4, "createdAt": z(now - dt.timedelta(days=3)), "mergedAt": z(now - dt.timedelta(days=2)),
         "commits": [{"authoredDate": z(now - dt.timedelta(days=4))}]},
    ]
    _fake_gh(tmp_path / "bin", payload)
    text = _run_measure(tmp_path, {}, "--no-write")
    proxy = "| Hours, first commit to merge (proxy for finding to main) |"
    assert f"{proxy} PRs merged, last 24 h | 3 |" in text
    assert f"{proxy} Median | 6.00 h |" in text
    assert f"{proxy} Maximum | 8.00 h |" in text
    opened = "| Hours, PR open to merge |"
    assert f"{opened} PRs merged, last 24 h | 3 |" in text
    assert f"{opened} Median | 1.00 h |" in text
    assert f"{opened} Maximum | 3.00 h |" in text


def test_new_seams_count_with_path_and_folder_excludes(tmp_path: Path) -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import measure
    finally:
        sys.path.pop(0)
    root = tmp_path / "repo"
    _write(root / "holdspeak" / "services" / "program_definitions.py", "class ProgramRefused(ServiceError):\n")
    _write(root / "holdspeak" / "services" / "walk_service.py", "class WalkRefused(ServiceError):\n")
    _write(root / "web" / "src" / "desk" / "needs" / "face.ts", "a.toUpperCase();\n")
    _write(root / "web" / "src" / "desk" / "needs" / "__tests__" / "face.test.ts", "a.toUpperCase();\n")
    _write(root / "web" / "src" / "styles" / "global.css", "@media (max-width: 720px) {}\n")
    _write(root / "web" / "src" / "desk" / "x" / "global.css", "@media (max-width: 720px) {}\n")
    _write(root / "web" / "src" / "desk" / "useCompact.ts", "// mirrors @media (max-width: 720px)\n")
    _write(root / "web" / "src" / "desk" / "Menu.tsx", '<Button label="Hand to agent" />\n')
    _write(root / "docs" / "internal" / "old.md", '"Hand to agent"\n')
    by_name = {seam["name"]: seam for seam in measure.load_seams()}
    count = lambda name: measure.seam_count(root, by_name[name])  # noqa: E731
    assert count("Refusal classes outside the definitions homes") == 1
    assert count("toUpperCase( in web/src/desk/needs") == 1
    # The allowlist names web/src/styles/global.css by path: a file of the
    # same name elsewhere counts, and a .ts comment does not (CSS only).
    assert count("Viewport max-width media outside the container-query allowlist") == 1
    assert count('"Hand to agent" face strings') == 1
    for seam in by_name.values():
        assert seam.get("why"), f"{seam['name']} has no why"


def test_rewrite_keeps_the_first_run_as_the_baseline(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    today = dt.date.today().isoformat()
    _write(out_dir / f"{today}.md", f"# Measure {today}\n\nWritten by x.\n\nMeasure {today}, origin/main, 7 s to read.\n\n| first table |\n")
    os.utime(out_dir / f"{today}.md", (dt.datetime(2026, 11, 8, 0, 40).timestamp(),) * 2)
    _run_measure(tmp_path, {}, "--no-gh", "--out", str(out_dir))
    once = (out_dir / f"{today}.md").read_text()
    assert once.startswith(f"# Measure {today}")
    assert "\n## Baseline (00:40)\n" in once and "| first table |" in once
    assert once.index("| Presses by him, last 24 h |") < once.index("## Baseline")
    _run_measure(tmp_path, {}, "--no-gh", "--out", str(out_dir))
    twice = (out_dir / f"{today}.md").read_text()
    assert twice.count("## Baseline (") == 1 and "| first table |" in twice
