"""The conductor: HoldSpeak held at arm's length.

A small FastAPI app that boots HoldSpeak with a chosen configuration
(good or deliberately bad), watches its health, captures its logs, kills
it, and boots it again differently — all while an independent website
stays up to guide the human sitting.

**The subprocess boundary is the whole point.** Nothing in this package
imports the ``holdspeak`` package — the conductor drives the product only
as a managed subprocess (``holdspeak web``) and over HTTP. A test
(``tests/uat/test_no_holdspeak_import.py``) enforces this so the harness
can never live inside the process it must be able to boot broken.
"""

from __future__ import annotations

from .app import create_app

__all__ = ["create_app"]
