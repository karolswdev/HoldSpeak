"""The Line: HoldSpeak's own phone line (docs/internal/betterment/line/LINE-DESIGN-2026-10-29.md).

baresip (BSD-3) as a supervised child, our ``aupipe`` module for the call's
audio, our own speech (Parakeet in, Pocket out), driven by the hub through the
``Line`` adapter (the surface of ``AiPhone``; ``calls/runner.py`` runs
unchanged). Nothing AGPL or GPL is in the tree or the Line's process.

``HOLDSPEAK_LINE=off`` (every rig hub): no baresip is looked for, the
adapter is never the Line, and the node does not run.
"""
from __future__ import annotations

import os

LINE_ENV = "HOLDSPEAK_LINE"


def line_on() -> bool:
    """``HOLDSPEAK_LINE=off``: no baresip probe, no Line adapter, no node."""
    return os.environ.get(LINE_ENV, "on").strip().lower() not in {"off", "0", "false", "no"}


__all__ = ["LINE_ENV", "line_on"]
