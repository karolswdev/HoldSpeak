"""Where runs live on disk.

Everything a run owns hangs under ``uat/_runs/<run_id>/`` — its isolated
HOME, its captured logs, its screenshots — and the run DB is a single
sqlite file beside them. ``uat/_runs/`` is gitignored.

``UAT_RUNS_ROOT`` overrides the root (tests point it at a tmp dir so a
suite never touches a real sitting's runs).
"""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """The HoldSpeak repo root (``uat/conductor/paths.py`` → up three)."""
    return Path(__file__).resolve().parents[2]


def runs_root() -> Path:
    """The directory holding every run's on-disk state and the run DB."""
    override = os.environ.get("UAT_RUNS_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return repo_root() / "uat" / "_runs"


def run_dir(run_id: str) -> Path:
    return runs_root() / run_id


def run_home(run_id: str) -> Path:
    """The isolated HOME for a run — the product's ``~`` for its lifetime."""
    return run_dir(run_id) / "home"


def run_logs_dir(run_id: str) -> Path:
    return run_dir(run_id) / "logs"


def run_shots_dir(run_id: str) -> Path:
    return run_dir(run_id) / "shots"


def run_debrief_dir(run_id: str) -> Path:
    return run_dir(run_id) / "debrief"


def db_path() -> Path:
    """The single sqlite run DB, shared across all runs."""
    override = os.environ.get("UAT_DB_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return runs_root() / "uat.db"
