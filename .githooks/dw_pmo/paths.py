"""Root discovery, path containment, and small filesystem helpers."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .model import die


def run_git_root(cwd: Path) -> Path | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(out) if out else None


def find_root(start: Path) -> Path:
    git_root = run_git_root(start)
    if git_root:
        return git_root
    cur = start.resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "pm" / "roadmap").is_dir():
            return candidate
    return cur


def roadmap_dir(root: Path) -> Path:
    rd = root / "pm" / "roadmap"
    if rd.is_dir():
        return rd
    source_layout = root / "pmo-roadmap" / "pm" / "roadmap"
    if source_layout.is_dir():
        return source_layout
    die(f"roadmap directory not found: {rd}")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "untitled"


def strip_code(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def ensure_under(path: Path, allowed_root: Path) -> None:
    resolved = path.resolve()
    allowed = allowed_root.resolve()
    if resolved != allowed and allowed not in resolved.parents:
        die(f"refusing to write outside PMO roadmap tree: {resolved}")


_WORK_LOG_DIR_ASSIGN_RE = re.compile(
    r"""^\s*(?:export\s+)?PMO_WORK_LOG_DIR=(["']?)(.*?)\1\s*$"""
)


def work_log_root(root: Path | None = None) -> Path:
    """Resolve the work-log root.

    Precedence (identical to the hooks and readers): a simple
    ``PMO_WORK_LOG_DIR=`` assignment in ``.githooks/pre-commit.config``
    beats the environment, which beats ``~/.work/log``. Last assignment
    in the config wins, matching bash sourcing.
    """
    value = os.environ.get("PMO_WORK_LOG_DIR") or ""
    if root is not None:
        cfg = root / ".githooks" / "pre-commit.config"
        if cfg.is_file():
            try:
                for line in cfg.read_text(encoding="utf-8").splitlines():
                    m = _WORK_LOG_DIR_ASSIGN_RE.match(line)
                    if m:
                        value = m.group(2)
            except OSError:
                pass
    if value:
        home = str(Path.home())
        value = value.replace("${HOME}", home).replace("$HOME", home)
        return Path(value).expanduser()
    return Path.home() / ".work" / "log"


def template_dir() -> Path | None:
    # Source layout: <repo>/pmo-roadmap/lib/dw_pmo/paths.py -> parents[2]
    # is pmo-roadmap/, which holds templates/. Installed layout:
    # <target>/.githooks/dw_pmo/paths.py -> parents[2] is the repo root,
    # matching the historical installed-dw behavior (repo-root templates/
    # or the embedded fallback).
    candidate = Path(__file__).resolve().parents[2] / "templates"
    return candidate if candidate.is_dir() else None
