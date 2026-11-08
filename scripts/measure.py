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
2. Hours from finding to main for the PRs merged in the last 24 hours. A
   finding has no timestamp yet, so the PROXY is the PR's first commit (its
   earliest author date) to the merge; PR open to merge stays beside it.
3. The size of the built web bundle (holdspeak/static/_built/assets/*.js).
4. The hub cold start: process start to the first GET / with status 200.
5. The shape of the code: the largest files, files per package, the fence.
6. The seams in scripts/measure_seams.json: each count must go to zero.
7. Presses by him per night: The Walk's answers (walk.json in each folder
   under ~/.local/share/holdspeak/feedback/walks) and the feedback bundles
   (report.json in each folder under ~/.local/share/holdspeak/feedback), for
   the last 24 hours. The folder is fixed under HOME
   (holdspeak/services/ui_feedback.py feedback_root); it is read only.

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
from concurrent.futures import ThreadPoolExecutor
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


def _hours_rows(label: str, hours: list[float]) -> list[Row]:
    if not hours:
        return [(label, "PRs merged, last 24 h", "0")]
    return [
        (label, "PRs merged, last 24 h", str(len(hours))),
        (label, "Median", f"{statistics.median(hours):.2f} h"),
        (label, "Maximum", f"{max(hours):.2f} h"),
    ]


GH_LIMIT = 300
FIRST_COMMIT_LABEL = "Hours, first commit to merge (proxy for finding to main)"


def _first_commit(repo: Path, number: int) -> dt.datetime | None:
    out = _run(["gh", "pr", "view", str(number), "--json", "commits"], repo)
    authored = [_stamp(c["authoredDate"]) for c in json.loads(out or "{}").get("commits") or []
                if c.get("authoredDate")]
    return min(authored) if authored else None


def finding_to_main(repo: Path, now: dt.datetime) -> list[Row]:
    # The commits come from one `gh pr view` per PR: the list call with
    # commits passes GitHub's GraphQL node limit at 100 PRs.
    out = _run(
        ["gh", "pr", "list", "--state", "merged", "--limit", str(GH_LIMIT),
         "--json", "number,createdAt,mergedAt"],
        repo,
    )
    listed = json.loads(out or "[]")
    recent = [pr for pr in listed
              if pr.get("mergedAt") and now - _stamp(pr["mergedAt"]) <= dt.timedelta(hours=24)]
    opened = [(_stamp(pr["mergedAt"]) - _stamp(pr["createdAt"])).total_seconds() / 3600
              for pr in recent if pr.get("createdAt")]
    with ThreadPoolExecutor(max_workers=8) as pool:
        firsts = list(pool.map(lambda pr: _first_commit(repo, int(pr["number"])), recent))
    first_commit = [(_stamp(pr["mergedAt"]) - first).total_seconds() / 3600
                    for pr, first in zip(recent, firsts) if first is not None]
    rows = _hours_rows(FIRST_COMMIT_LABEL, first_commit) + _hours_rows("Hours, PR open to merge", opened)
    if len(listed) >= GH_LIMIT and len(recent) == len(listed):
        rows.append((FIRST_COMMIT_LABEL, "Warning", f"all {GH_LIMIT} PRs listed are in the window; raise GH_LIMIT"))
    return rows


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


def _excluded(repo: Path, path: Path, exclude: list[str]) -> bool:
    """An entry with a slash is a path from the repo root (a file or a
    folder); an entry without one names a file or any folder on the way."""
    rel = path.relative_to(repo).as_posix()
    parts = set(path.relative_to(repo).parts)
    for entry in exclude:
        entry = entry.strip("/")
        if "/" in entry:
            if rel == entry or rel.startswith(entry + "/"):
                return True
        elif entry in parts:
            return True
    return False


def seam_count(repo: Path, seam: dict) -> int:
    pattern = re.compile(seam["pattern"])
    exclude = list(seam.get("exclude", []))
    suffixes = tuple(seam.get("suffixes") or SEAM_SUFFIXES)
    total = 0
    for rel in seam["paths"]:
        for path in _files(repo / rel, suffixes):
            if _excluded(repo, path, exclude):
                continue
            total += sum(1 for line in path.read_text(errors="replace").splitlines() if pattern.search(line))
    return total


def seams(repo: Path) -> list[Row]:
    return [("Seams to remove (lines)", s["name"], str(seam_count(repo, s))) for s in load_seams()]


# 7. Presses by him -------------------------------------------------------------

def feedback_root(home: Path | None = None) -> Path:
    """The hub's feedback folder (ui_feedback.feedback_root): fixed under HOME."""
    return (Path.home() if home is None else home) / ".local" / "share" / "holdspeak" / "feedback"


def _presses(answer: dict) -> list[dict]:
    """One answer and the earlier answers it replaced: each one is a press."""
    found = [answer] + [e for e in answer.get("earlier") or [] if isinstance(e, dict)]
    return [p for p in found if isinstance(p.get("at"), str)]


def presses(now: dt.datetime, home: Path | None = None) -> list[Row]:
    root = feedback_root(home)
    since = now - dt.timedelta(hours=24)
    label = "Presses by him, last 24 h"
    walks = 0
    answered = 0
    choices: Counter[str] = Counter()
    spans: list[float] = []
    walks_dir = root / "walks"
    for walk_file in sorted(walks_dir.glob("*/walk.json")) if walks_dir.is_dir() else []:
        try:
            walk = json.loads(walk_file.read_text())
        except (OSError, ValueError):
            continue
        times: list[dt.datetime] = []
        for answer in (walk.get("answers") or {}).values():
            if not isinstance(answer, dict):
                continue
            for press in _presses(answer):
                at = _stamp(press["at"])
                if at < since:
                    continue
                times.append(at)
                choice = str(press.get("choice") or "")
                choices[choice if choice in ("Keep", "Redo", "words", "skip") else "other"] += 1
        created = walk.get("created_at")
        if (isinstance(created, str) and _stamp(created) >= since) or times:
            walks += 1
        if times:
            answered += 1
        if len(times) >= 2:
            spans.append((max(times) - min(times)).total_seconds())
    bundles = 0
    for report in sorted(root.glob("*/report.json")) if root.is_dir() else []:
        try:
            captured = json.loads(report.read_text()).get("captured_at")
            at = _stamp(captured) if isinstance(captured, str) else None
        except (OSError, ValueError):
            at = None
        if at is None:
            at = dt.datetime.fromtimestamp(report.stat().st_mtime, dt.timezone.utc)
        if at >= since:
            bundles += 1
    rows: list[Row] = [
        (label, "Walks", str(walks)),
        (label, "Walks with an answer", str(answered)),
    ]
    for choice in ("Keep", "Redo", "words", "skip"):
        rows.append((label, f"Answers: {choice}", str(choices.get(choice, 0))))
    if choices.get("other"):
        rows.append((label, "Answers: other", str(choices["other"])))
    rows.append((label, "Answers, total", str(sum(choices.values()))))
    rows.append((label, "Median s, first to last answer of a walk",
                 f"{statistics.median(spans):.0f} s" if spans else "no walk with 2 answers"))
    rows.append((label, "Feedback bundles", str(bundles)))
    return rows


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
        rows.append((FIRST_COMMIT_LABEL, "Skipped", "--no-gh"))
        rows.append(("Hours, PR open to merge", "Skipped", "--no-gh"))
    else:
        _section(rows, FIRST_COMMIT_LABEL, finding_to_main, repo, now)
    _section(rows, "Web bundle", bundle, repo)
    if args.no_hub:
        rows.append(("Hub cold start", "Skipped", "--no-hub"))
    else:
        _section(rows, "Hub cold start", hub_cold_start, repo)
    _section(rows, "Shape", shape, repo)
    _section(rows, "Seams to remove (lines)", seams, repo)
    _section(rows, "Presses by him, last 24 h", presses, now)

    clock = dt.datetime.now().strftime("%H:%M")
    head = f"Measure {today.isoformat()} {clock}, origin/main, {time.monotonic() - started:.0f} s to read."
    why = "\n".join(f"- {s['name']}: {s['why']}" for s in _safe_seams() if s.get("why"))
    text = f"{head}\n\n{table(rows)}\n"
    if why:
        text += f"\nWhy each seam is a seam:\n\n{why}\n"
    print(text, end="")
    if not args.no_write:
        out_dir = args.out or repo / "docs" / "internal" / "measure"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"{today.isoformat()}.md"
        baseline = _baseline(target)
        target.write_text(f"# Measure {today.isoformat()}\n\n"
                          "Written by `scripts/measure.py` (CLAUDE.md, rule 7). "
                          "Compare with the file of the night before. The last run of the day "
                          "is on top; the first run of the day stays below it as the baseline.\n\n"
                          f"{text}{baseline}")
        print(f"\nWrote {target}")
    return 0


HEAD_TIME = re.compile(r"^Measure \d{4}-\d{2}-\d{2} (\d{2}:\d{2})", re.M)
BASELINE = "\n## Baseline ("


def _baseline(target: Path) -> str:
    """The first run of the day, kept when the script writes the day's file
    again. A file that has a Baseline section keeps it; a file without one
    becomes the baseline (its time from its head line, else the file's time)."""
    if not target.is_file():
        return ""
    old = target.read_text()
    at = old.find(BASELINE)
    if at >= 0:
        return old[at:]
    start = old.find("\nMeasure ")
    body = old[start + 1:] if start >= 0 else old
    found = HEAD_TIME.search(body)
    clock = found.group(1) if found else dt.datetime.fromtimestamp(target.stat().st_mtime).strftime("%H:%M")
    return f"\n## Baseline ({clock})\n\n{body.rstrip()}\n"


def _safe_seams() -> list[dict]:
    try:
        return load_seams()
    except Exception:
        return []


if __name__ == "__main__":
    sys.exit(main())
