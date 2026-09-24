"""Where a test writes its evidence shots and outputs.

The scar: tests wrote screenshots and JSON straight over the tracked evidence
of closed phases, so every full run dirtied ~388 files that someone had to
restore by hand. The law: a test writes to ``.tmp/evidence-shots/<rel>`` (it is
gitignored) unless ``HOLDSPEAK_EVIDENCE_WRITE=1`` sets capture mode, in which
case it writes to the tracked ``<rel>`` for a story that ships its shots.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def evidence_dir(rel: str) -> Path:
    """Return the directory for evidence at repo-relative ``rel``, created."""
    if os.environ.get("HOLDSPEAK_EVIDENCE_WRITE") == "1":
        path = REPO / rel
    else:
        path = REPO / ".tmp" / "evidence-shots" / rel
    path.mkdir(parents=True, exist_ok=True)
    return path
