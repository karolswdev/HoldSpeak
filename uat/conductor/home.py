"""Assemble an isolated HOME for a run — the dogfood ``_home`` recipe, in code.

The conductor boots the product with ``HOME`` pointed here so its config
and DB never touch the real ``~/.config/holdspeak`` or
``~/.local/share/holdspeak``. Model caches (``~/.cache/huggingface``,
``~/Models``) are symlinked in from the real HOME so Whisper/GGUF weights
are reused, not re-downloaded — the Phase-67 dogfood ``setup.sh`` logic,
ported (not shelled out to) because the conductor owns this code now.

A **deck** is a sparse config overlay: the product's ``Config.load``
merges any missing field over its own defaults (unknown keys are
dropped), so the conductor only writes the delta. It never imports
``Config`` — it writes JSON and lets the product read it.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

# Subdirs a HoldSpeak HOME needs to exist before boot (config + data + cache).
_HOME_SUBDIRS = (
    ".config/holdspeak",
    ".local/share/holdspeak",
    ".cache",
    "Documents",
)

# Caches worth linking from the real HOME so nothing re-downloads.
_LINKED_CACHES = (
    ".cache/huggingface",
    "Models",
)


def _real_home() -> Path:
    return Path(os.environ.get("UAT_REAL_HOME", os.path.expanduser("~")))


def _link_cache(rel: str, real_home: Path, home: Path) -> bool:
    src = real_home / rel
    dst = home / rel
    if src.exists() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            dst.symlink_to(src)
            return True
        except OSError:
            # A best-effort convenience; a missing cache link only means a
            # re-download, never a broken run.
            return False
    return False


def assemble_home(home: Path, *, link_caches: bool = True) -> Path:
    """Create the isolated HOME's skeleton and link model caches in.

    Idempotent: safe to call twice on the same HOME.
    """
    home = Path(home)
    for sub in _HOME_SUBDIRS:
        (home / sub).mkdir(parents=True, exist_ok=True)
    if link_caches:
        real_home = _real_home()
        for rel in _LINKED_CACHES:
            _link_cache(rel, real_home, home)
    return home


def config_file(home: Path) -> Path:
    return Path(home) / ".config" / "holdspeak" / "config.json"


def write_config(home: Path, overlay: dict | None) -> Path:
    """Write a run's config overlay as the HOME's ``config.json``.

    The overlay is a sparse dict; ``config_version`` is defaulted to 1 if
    the overlay omits it so the product never falls back to a rewritten
    default file. Returns the written path.
    """
    overlay = copy.deepcopy(overlay) if overlay else {}
    overlay.setdefault("config_version", 1)
    path = config_file(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(overlay, indent=2, sort_keys=True))
    return path


def read_config(home: Path) -> dict:
    """Read back the raw config JSON a run booted with (for reporting)."""
    path = config_file(home)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return {}
