"""The owner ruling of 2026-10-25 (UX-CANON A.9 amended): no egress labels on
working windows.

Owner: "I'm also pissed off at the ever-present 'labels' (the LAN, the
192.168.1.36, the jira label as visible on that screen) ... It feels like an
ancient relic now."

Two fences over the live web/src tree:

1. The working windows (Today, Needs you, the Room, Meetings, Ask, Speak,
   Agents, the drawers, Activity, Automations) draw no egress chip, no route
   lamp and no scope word in their rows, toolbars and status bars. A row
   with a host chip fails here; nothing here requires one.
2. The places where the choice or the act is made keep their disclosure:
   the Send preview, the Hand confirm, Settings (Engines, Connections,
   Destinations), Setup and the New Project Door still name the
   destination.

The rendered check is the desk sweep's `labels` fence
(tests/e2e/test_desk_sweep.py).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[2] / "web" / "src"

# The working windows' face files. A new working face joins this list.
WORKING_FACES = (
    "desk/pullouts/views/TodayView.tsx",
    "desk/needs/TodayNeeds.tsx",
    "desk/components/AskPanel.tsx",
    "desk/surface/EngineLine.tsx",
    "desk/surface/RunLine.tsx",
    "pages/cores/DictationCore.tsx",
    "pages/cores/dictation/SpeakFace.tsx",
    "desk/conductor/ConductorWindow.tsx",
    "desk/lane/LaneWindow.tsx",
    "desk/components/AgentFlight.tsx",
    "pages/cores/HistoryCore.tsx",
    "pages/cores/history/MeetingRecord.tsx",
    "pages/cores/history/MeetingHeader.tsx",
    "pages/cores/history/CatalogRail.tsx",
    "pages/cores/history/NeedsYouTable.tsx",
    "meetings/RouteDisclosure.tsx",
    "meetings/MeetingIntelRecovery.tsx",
    "features/project-room/ProjectRoomCore.tsx",
    "features/project-room/prepare/PreparePosture.tsx",
    "features/project-room/update/UpdatePosture.tsx",
    "desk/drawer/DrawerWindow.tsx",
    "desk/drawer/InfoWindow.tsx",
    "pages/cores/ActivityCore.tsx",
    "pages/cores/ActivityFinishedReceipts.tsx",
    "desk/components/automation/AutomationWindow.tsx",
    "desk/components/automation/ResultCard.tsx",
)

# The chip species, the route lamp, and a scope word or LAN suffix built into
# a face string.
_LABELS = (
    (re.compile(r"<EgressChip\b"), "an EgressChip"),
    (re.compile(r"<RouteEgressChip\b"), "a route egress chip"),
    (re.compile(r"<TurnLamp\b"), "a route lamp"),
    (re.compile(r"""["'`][^"'`\n]*·\s*(?:LAN|CLOUD|LOCAL|REMOTE|MIXED)\b"""), "a '· <scope word>' label"),
    (re.compile(r"""\bREMOTE ·"""), "a 'REMOTE ·' label"),
)


def _code(text: str) -> str:
    """The file without its comments: a comment may name the old rule."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(^|[^:])//[^\n]*", r"\1", text)


@pytest.mark.parametrize("face", WORKING_FACES)
def test_a_working_window_draws_no_egress_label(face: str) -> None:
    path = WEB / face
    assert path.is_file(), f"{face} moved: update WORKING_FACES"
    code = _code(path.read_text(encoding="utf-8"))
    found = [what for pattern, what in _LABELS if pattern.search(code)]
    assert not found, (
        f"{face} draws {', '.join(found)} on a working window. Owner ruling 2026-10-25 "
        "(UX-CANON A.9 amended): name an engine by name only; put the address in the "
        "verb's hover title, or in the confirm or preview before the press."
    )


# Where the choice or the act is made, the destination is still named.
KEPT_DISCLOSURE = (
    "desk/surface/send/SendWell.tsx",
    "pages/cores/connections/Destinations.tsx",
    "desk/hand/HandConfirm.tsx",
    "desk/components/HandSheet.tsx",
    "features/runson/RunsOnCore.tsx",
    "pages/cores/connections/ConnectionsPane.tsx",
    "features/project-room/door/DoorCore.tsx",
    "features/project-room/NudgeCard.tsx",
)


@pytest.mark.parametrize("face", KEPT_DISCLOSURE)
def test_the_choice_or_the_act_still_names_the_destination(face: str) -> None:
    code = _code((WEB / face).read_text(encoding="utf-8"))
    assert "<EgressChip" in code, (
        f"{face} is where the choice or the act is made: it must still name the "
        "destination before the press (owner ruling 2026-10-25)."
    )
