"""Calls: call HoldSpeak, and HoldSpeak calls (2026-10-28).

HoldSpeak does not build telephony. The owner's own ai-phone install
(github.com/oxnw/ai-phone, AGPL-3.0) is the phone half: the line, speech in
and speech out, on this Mac. HoldSpeak runs it as a separate program and owns
each turn of a call in relay mode (``listen`` → the agent turn → ``say``).
No ai-phone code is imported, vendored or shipped.

- :mod:`.aiphone`: the adapter that runs the ai-phone CLI and reads its JSON.
- :mod:`.runner`: one call: the gate, the turns, the held questions, the read
  back, the note.
- :mod:`.service`: the hub's calls: status, the listener, place, hang up,
  decide, the ``call_state`` frame.

Design: ``docs/internal/betterment/calls/CALLS-DESIGN-2026-10-28.md``.
"""
