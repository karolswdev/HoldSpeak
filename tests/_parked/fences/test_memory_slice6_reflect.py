# PARKED 2026-11-09 (fences diet, pipe/fences-diet): a committed byte SNAPSHOT of each palette's schema, re-recorded on every tool change.
# Replaced by the behaviour tests that stay live: a 32k chase turn and a 28,300-byte Plan turn still run (test_memory_slice6_reflect.py).
"""Parked from tests/unit/test_memory_slice6_reflect.py; the 28,850 case of
test_a_plan_turn_main_admits_is_still_admitted ("any growth fails") parked with it."""
import pytest

#: Each thread palette's tool-schema bytes on MAIN (64d1e7126, before this
#: slice), measured with admission's own serializer (``_canonical``: sorted
#: keys, compact, ASCII).  Admission counts one token per byte, so no
#: palette may grow: a turn that fit on main must still fit.
MAIN_PALETTE_BYTES = {"default": 14871, "desk": 27680, "chase": 30959, "plan": 2875}


def test_no_thread_palette_grows_versus_main() -> None:
    from holdspeak.services import thread_modes
    from holdspeak.services.inference_adoption_service import _canonical
    from holdspeak.services.thread_tools import CHAT_PALETTE, tool_schemas_for

    palettes = {"default": CHAT_PALETTE, "desk": thread_modes._DESK_TOOLS,
                "chase": thread_modes._CHASE_TOOLS, "plan": thread_modes._PLAN_TOOLS}
    for name, tools in palettes.items():
        size = len(_canonical(tool_schemas_for(tools)).encode())
        assert size <= MAIN_PALETTE_BYTES[name], (name, size, MAIN_PALETTE_BYTES[name])


