"""HoldSpeak UAT harness (dev-only).

This package is the User Acceptance Testing rig for HoldSpeak: the
**conductor** (a standalone process that hosts HoldSpeak as an isolated
managed subprocess), the induction engine (decks, seeds, state recipes),
the scenario contract + feature ledger, the guided site, and the debrief.

It is a development harness and is **never** part of the published
``holdspeak`` package. Critically, the conductor stands *outside* the
product under test: it must be able to boot HoldSpeak broken, kill it,
and boot it again differently — so it never imports the ``holdspeak``
package into its own process (subprocess boundary only). See
``pm/roadmap/holdspeak-uat/``.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
