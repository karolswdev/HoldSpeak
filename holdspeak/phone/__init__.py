"""Phone: the desk reaches the owner on his phone, and he reaches the desk (2026-10-28).

The design is ``docs/internal/betterment/phone/PHONE-DESIGN-2026-10-28.md``.
The model is absorbed from agentring (github.com/mutonby/agentring at
10b0e55, Apache-2.0): a message channel with replies and one
sequence-numbered event log, a call state machine (ringing, answered, missed,
declined, ended), a paired device with a revocable token, signed pushes, and
the etiquette an agent follows when it decides to reach a person. The ideas
are rewritten in HoldSpeak's own code and words; no agentring code runs here
(``docs/internal/betterment/phone/ABSORBED-FROM-AGENTRING.md``). The hub is
the relay: there is no second server.

- :mod:`.contract`: the wire (pydantic), round-tripped against
  ``tests/fixtures/phone/``.
- :mod:`.store`: the four tables.
- :mod:`.events`: the event log (replay from ``after_seq``, live fan-out).
- :mod:`.calls`: the call state machine and its ring timer.
- :mod:`.devices`: pairing, the device token, the per-hub secret.
- :mod:`.push`: the push providers (APNs, and a null one for rigs).
- :mod:`.transport_number`: a call on the real number through Calls.
- :mod:`.phone_rules`: when the desk may message or call him.
- :mod:`.service`: :class:`PhoneService`, the one service behind REST and MCP.

``HOLDSPEAK_PHONE=off`` (every rig hub) mounts no phone route, starts no
timer and sends no push.
"""
from __future__ import annotations

import os

PHONE_ENV = "HOLDSPEAK_PHONE"


def phone_on() -> bool:
    """``HOLDSPEAK_PHONE=off``: no phone route, no timer, no push."""
    return os.environ.get(PHONE_ENV, "on").strip().lower() not in {"off", "0", "false", "no"}


__all__ = ["PHONE_ENV", "phone_on"]
