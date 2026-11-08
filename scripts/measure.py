#!/usr/bin/env python3
"""Print the numbers of rule 7 as one table, and keep a copy for each night.

    uv run python scripts/measure.py              # every section, writes the file
    uv run python scripts/measure.py --no-hub     # skip the hub cold start
    uv run python scripts/measure.py --no-gh      # skip the GitHub read
    uv run python scripts/measure.py --no-write   # print only

CLAUDE.md, "How we work now", rule 7: "Measure. Merges per day, presses per
night, hours from finding to main." The direction: "not an overcomplicated
architecture with multiple implementations of the same thing." This script
reads these numbers:

1. Merges per day on origin/main for the last 7 days (subjects with "(#n)").
2. Hours from PR open to merge for the PRs merged in the last 24 hours.
3. The size of the built web bundle (holdspeak/static/_built/assets/*.js).
4. The hub cold start: process start to the first GET / with status 200.
5. The shape of the code: the largest files, files per package, the fence.
6. The seams in scripts/measure_seams.json: each count must go to zero.

It writes the same table to docs/internal/measure/<YYYY-MM-DD>.md, so each
night compares with the night before.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import os
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SEAMS_FILE = SCRIPT_DIR / "measure_seams.json"
HUB_PORT = 8798
HUB_SWITCHES = {
    "HOLDSPEAK_AGENT_STATE": "off",
    "HOLDSPEAK_ACTIVE_TARGET": "off",
    "HOLDSPEAK_DESKTOP_NOTIFY": "0",
    "HOLDSPEAK_MACOS_CALENDAR": "0",
    "HOLDSPEAK_CLI_ENGINES": "off",
    "HOLDSPEAK_RESTART_CHECK": "off",
    "HOLDSPEAK_SCREEN_RULES": "off",
    "HOLDSPEAK_CALLS": "off",
    "HOLDSPEAK_LINE": "off",
    "HOLDSPEAK_RECORDINGS": "off",
    "HOLDSPEAK_MIC_CHECK": "off",
    "HOLDSPEAK_PROGRAMS": "off",
    "HOLDSPEAK_PHONE": "off",
    "HOLDSPEAK_TELEGRAM": "off",
}
PR_REF = re.compile(r"\(#(\d+)\)|Merge pull request #(\d+)")
# An import of the web layer package (holdspeak/web) from a service module.
WEB_IMPORT = re.compile(r"^\s*(from|import)\s+(holdspeak\.web|\.\.web)(\.|\s|$)", re.M)
SKIP_DIRS = {"node_modules", "__pycache__", "_built", "dist", ".venv", "_parked"}

Row = tuple[str, str, str]


def _run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {result.stderr.strip()[:200]}")
    return result.stdout


def _files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix in suffixes else []
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(suffixes):
                found.append(Path(dirpath) / name)
    return found


def _lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


# 1. Merges per day -----------------------------------------------------------

def merges_per_day(repo: Path, today: dt.date) -> list[Row]:
    first = today - dt.timedelta(days=6)
    out = _run(
        ["git", "log", "origin/main", "--first-parent",
         f"--since={first.isoformat()} 00:00", "--date=short-local", "--format=%cd%x09%s"],
        repo,
    )
    counts: Counter[str] = Counter()
    for line in out.splitlines():
        day, _, subject = line.partition("\t")
        if PR_REF.search(subject):
            counts[day] += 1
    rows: list[Row] = []
    for offset in range(7):
        day = (first + dt.timedelta(days=offset)).isoformat()
        rows.append(("Merges per day", day, str(counts.get(day, 0))))
    rows.append(("Merges per day", "Total, 7 days", str(sum(counts.values()))))
    return rows


# 2. Hours from finding to main -----------------------------------------------

def _stamp(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def finding_to_main(repo: Path, now: dt.datetime) -> list[Row]:
    out = _run(
        ["gh", "pr", "list", "--state", "merged", "--limit", "60",
         "--json", "number,createdAt,mergedAt,title"],
        repo,
    )
    hours = []
    for pr in json.loads(out or "[]"):
        if not pr.get("mergedAt") or not pr.get("createdAt"):
            continue
        merged = _stamp(pr["mergedAt"])
        if now - merged > dt.timedelta(hours=24):
            continue
        hours.append((merged - _stamp(pr["createdAt"])).total_seconds() / 3600)
    label = "Hours, PR open to merge"
    if not hours:
        return [(label, "PRs merged, last 24 h", "0")]
    return [
        (label, "PRs merged, last 24 h", str(len(hours))),
        (label, "Median", f"{statistics.median(hours):.2f} h"),
        (label, "Maximum", f"{max(hours):.2f} h"),
    ]


# 3. Bundle size --------------------------------------------------------------

def _kib(size: int) -> str:
    return f"{size / 1024:,.0f} KiB"


def bundle(repo: Path) -> list[Row]:
    built = repo / "holdspeak" / "static" / "_built"
    label = "Web bundle"
    build_id = "not built"
    id_file = built / "build-id.json"
    if id_file.is_file():
        build_id = str(json.loads(id_file.read_text()).get("build_id", "unknown"))
    chunks = sorted((built / "assets").glob("*.js")) if (built / "assets").is_dir() else []
    if not chunks:
        return [(label, "Build id", build_id), (label, "JS files", "0 (run npm run build in web/)")]
    sizes = {p.name: p.stat().st_size for p in chunks}
    gz = sum(len(gzip.compress(p.read_bytes(), compresslevel=6)) for p in chunks)
    rows: list[Row] = [
        (label, "Build id", build_id),
        (label, "JS files", str(len(chunks))),
        (label, "JS, raw", _kib(sum(sizes.values()))),
        (label, "JS, gzip", _kib(gz)),
    ]
    for name, size in sorted(sizes.items(), key=lambda kv: -kv[1])[:3]:
        rows.append((label, f"Large chunk: {name}", _kib(size)))
    return rows


# 4. Hub cold start -----------------------------------------------------------

def _one_cold_start(repo: Path, timeout: float) -> float | None:
    home = tempfile.mkdtemp(prefix="measure-hub-")
    env = {**os.environ, **HUB_SWITCHES, "HOME": home, "HOLDSPEAK_WEB_PORT": str(HUB_PORT)}
    url = f"http://127.0.0.1:{HUB_PORT}/"
    start = time.monotonic()
    proc = subprocess.Popen(
        ["uv", "run", "python", "-m", "holdspeak.cli_entry", "web", "--no-open"],
        cwd=repo, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        while time.monotonic() - start < timeout:
            if proc.poll() is not None:
                return None
            try:
                with urllib.request.urlopen(url, timeout=1) as resp:
                    if resp.status == 200:
                        return time.monotonic() - start
            except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
                pass
            time.sleep(0.1)
        return None
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=10)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
        shutil.rmtree(home, ignore_errors=True)


def _port_answers() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{HUB_PORT}/", timeout=1):
            return True
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
        return False


def hub_cold_start(repo: Path, runs: int = 3, timeout: float = 30.0) -> list[Row]:
    label = "Hub cold start"
    if _port_answers():
        return [(label, f"Port {HUB_PORT}", "in use by another process; not measured")]
    times = [t for t in (_one_cold_start(repo, timeout) for _ in range(runs)) if t is not None]
    if not times:
        return [(label, f"GET / 200, port {HUB_PORT}", f"no 200 in {timeout:.0f} s")]
    rows: list[Row] = [(label, f"Median of {len(times)}, start to GET / 200", f"{statistics.median(times):.2f} s")]
    if len(times) < runs:
        rows.append((label, "Runs with no 200", str(runs - len(times))))
    return rows


# 5. Shape of the code --------------------------------------------------------

def shape(repo: Path) -> list[Row]:
    rows: list[Row] = []
    pkg = repo / "holdspeak"
    py = _files(pkg, (".py",))
    for path in sorted(py, key=_lines, reverse=True)[:10]:
        rows.append(("Largest Python files", str(path.relative_to(repo)), f"{_lines(path):,} lines"))
    ts = _files(repo / "web" / "src", (".ts", ".tsx"))
    for path in sorted(ts, key=_lines, reverse=True)[:10]:
        rows.append(("Largest TS files", str(path.relative_to(repo)), f"{_lines(path):,} lines"))
    per_pkg: Counter[str] = Counter()
    for path in py:
        parts = path.relative_to(pkg).parts
        per_pkg["holdspeak (top level)" if len(parts) == 1 else f"holdspeak/{parts[0]}"] += 1
    for name, count in sorted(per_pkg.items(), key=lambda kv: (-kv[1], kv[0])):
        rows.append(("Python files per package", name, str(count)))
    services = sorted((pkg / "services").glob("*.py")) if (pkg / "services").is_dir() else []
    crossing = [p.name for p in services if WEB_IMPORT.search(p.read_text(errors="replace"))]
    rows.append(("Fence", "holdspeak/services modules that import holdspeak/web (must be 0)", str(len(crossing))))
    return rows


# 6. Seams --------------------------------------------------------------------

SEAM_SUFFIXES = (".py", ".ts", ".tsx", ".css", ".js", ".json", ".md", ".html")


def load_seams(path: Path = SEAMS_FILE) -> list[dict]:
    data = json.loads(path.read_text())
    seams = data["seams"]
    for seam in seams:
        re.compile(seam["pattern"])
    return seams


def seam_count(repo: Path, seam: dict) -> int:
    pattern = re.compile(seam["pattern"])
    exclude = set(seam.get("exclude", []))
    total = 0
    for rel in seam["paths"]:
        for path in _files(repo / rel, SEAM_SUFFIXES):
            if path.name in exclude:
                continue
            total += sum(1 for line in path.read_text(errors="replace").splitlines() if pattern.search(line))
    return total


def seams(repo: Path) -> list[Row]:
    return [("Seams to remove (lines)", s["name"], str(seam_count(repo, s))) for s in load_seams()]


# Output ----------------------------------------------------------------------

def table(rows: list[Row]) -> str:
    out = ["| Measure | Item | Value |", "| --- | --- | --- |"]
    out += [f"| {a} | {b.replace('|', '/')} | {c} |" for a, b, c in rows]
    return "\n".join(out)


def _section(rows: list[Row], label: str, fn, *args) -> None:
    try:
        rows.extend(fn(*args))
    except Exception as exc:  # one broken source must not hide the others
        rows.append((label, "Could not read", str(exc).splitlines()[0][:120] if str(exc) else type(exc).__name__))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=SCRIPT_DIR.parent)
    parser.add_argument("--out", type=Path, default=None, help="folder for <date>.md (default docs/internal/measure)")
    parser.add_argument("--no-hub", action="store_true", help="skip the hub cold start")
    parser.add_argument("--no-gh", action="store_true", help="skip the GitHub read")
    parser.add_argument("--no-write", action="store_true", help="print only")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    started = time.monotonic()
    now = dt.datetime.now(dt.timezone.utc)
    today = dt.date.today()

    rows: list[Row] = []
    _section(rows, "Merges per day", merges_per_day, repo, today)
    if args.no_gh:
        rows.append(("Hours, PR open to merge", "Skipped", "--no-gh"))
    else:
        _section(rows, "Hours, PR open to merge", finding_to_main, repo, now)
    _section(rows, "Web bundle", bundle, repo)
    if args.no_hub:
        rows.append(("Hub cold start", "Skipped", "--no-hub"))
    else:
        _section(rows, "Hub cold start", hub_cold_start, repo)
    _section(rows, "Shape", shape, repo)
    _section(rows, "Seams to remove (lines)", seams, repo)

    head = f"Measure {today.isoformat()}, origin/main, {time.monotonic() - started:.0f} s to read."
    text = f"{head}\n\n{table(rows)}\n"
    print(text, end="")
    if not args.no_write:
        out_dir = args.out or repo / "docs" / "internal" / "measure"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"{today.isoformat()}.md"
        target.write_text(f"# Measure {today.isoformat()}\n\n"
                          "Written by `scripts/measure.py` (CLAUDE.md, rule 7). "
                          "Compare with the file of the night before.\n\n"
                          f"{text}")
        print(f"\nWrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
