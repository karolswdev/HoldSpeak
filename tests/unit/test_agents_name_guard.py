"""Betterment AG1: the user sees "Agents" and "agent", never "Conductor" or "coder".

DECISIONS #3 (adopted 2026-10-17): "Agent" means only a coding agent session;
its home is Agents (the Conductor window). Code names, routes, window ids, the
stored kind (`coder`) and the MCP tools (`coder.*`) stay; only what the user
sees changes (docs/internal/betterment/agents/RECIPE.md, slice AG1).

This guard reuses the Automations guard's scanner (string literals, template
text and JSX text in `web/src`, outside tests and parked faces) and fails on:

* a visible "Conductor" word anywhere on the desk;
* a visible "coder" or "coders" word anywhere on the desk;
* the old machine words on the agent faces (the Agents window, the agent's
  window, Hand to agent): Re-brief, Install hooks, ASKS YOU, WANTS APPROVAL,
  Raw as a verb, rider, NODE, TARGET, INCOMPATIBLE.

`pages/cores/CompanionCore.tsx` is the old Agents application: AG1 unmapped
it (no manifest row, `/companion` opens Agents), so no face reaches it.
"""
from __future__ import annotations

import re
from pathlib import Path

from tests.unit.test_automation_name_guard import ROOT, _ui_files, split

#: JSX text between tags. Looser than the Automations guard's pattern: text
#: with brackets ("Stop · sure? (ends the agent's session)") is read too.
JSX_TEXT = re.compile(r">([^<>{}]*)<")

#: Unreachable since AG1 (no route and no manifest row reach it).
UNREACHABLE = {"web/src/pages/cores/CompanionCore.tsx"}

_EDGE_L = r"(?<![\w\-./:#@])"
_EDGE_R = r"(?![\w\-/:@])"
#: "Conductor" in any visible text (a lower-case literal with no space is a key).
CONDUCTOR = re.compile(_EDGE_L + r"Conductor" + _EDGE_R)
#: "coder" / "coders" in any case, in text (a space or a capital in the literal).
CODER = re.compile(_EDGE_L + r"coders?" + _EDGE_R, re.IGNORECASE)

#: The agent faces and the words they no longer say.
AGENT_FACES = (
    "web/src/desk/conductor/ConductorWindow.tsx",
    "web/src/desk/conductor/members.ts",
    "web/src/desk/lane/LaneWindow.tsx",
    "web/src/desk/components/HandSheet.tsx",
)
FACE_WORDS = re.compile(
    _EDGE_L
    + r"(?:Re-brief|RE-BRIEF|Install hooks|ASKS YOU|WANTS APPROVAL|[Ww]ants approval"
    r"|Raw|rider|NODE|TARGET|INCOMPATIBLE)"
    + _EDGE_R
)


def _is_text(text: str) -> bool:
    """A literal is text when it has a space or a capital; else it is a key."""
    stripped = text.strip()
    return bool(re.search(r"\s", stripped)) or bool(re.search(r"[A-Z]", stripped))


def _visible(path: Path) -> list[tuple[int, str]]:
    literals, code = split(path.read_text(encoding="utf-8"))
    shown = [(line, text) for line, text in literals if _is_text(text)]
    for match in JSX_TEXT.finditer(code):
        shown.append((code.count("\n", 0, match.start()) + 1, f"JSX {match.group(1)}"))
    return shown


def offenders() -> list[str]:
    found: list[str] = []
    for path in _ui_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in UNREACHABLE:
            continue
        face = rel in AGENT_FACES
        for line, text in _visible(path):
            # A className list ("lw-ask lw-raw-held") is not text.
            if re.fullmatch(r"(?:JSX )?[\w\- ]+", text.strip()) and "-" in text and not re.search(r"[A-Z]", text):
                continue
            if CONDUCTOR.search(text) or CODER.search(text) or (face and FACE_WORDS.search(text)):
                found.append(f"{rel}:{line}: {text.strip()[:120]!r}")
    return found


def test_the_guard_reads_conductor_coder_and_the_face_words() -> None:
    assert CONDUCTOR.search("Conductor") and not CONDUCTOR.search("open-conductor")
    assert not CONDUCTOR.search("ConductorWindow") and not CONDUCTOR.search("/conductor")
    assert CODER.search("Hand to coder") and CODER.search("CODERS")
    assert not CODER.search("coder:claude:1") and not CODER.search("desk-coder-draft")
    assert FACE_WORDS.search("Re-brief") and FACE_WORDS.search("WANTS APPROVAL")
    assert FACE_WORDS.search("Raw") and not FACE_WORDS.search("Rawness")
    assert not _is_text("coder") and _is_text("CODER") and _is_text("the coder")


def test_no_visible_string_says_conductor_or_coder() -> None:
    found = offenders()
    assert not found, (
        'The user sees "Agents" and "agent" (betterment AG1, DECISIONS #3). '
        "Rename these visible strings; code names, routes and the stored kind "
        "stay `conductor` and `coder`:\n" + "\n".join(found)
    )


def test_the_desk_names_the_conductor_agents() -> None:
    manifest = (ROOT / "web/src/desk/applications.ts").read_text(encoding="utf-8")
    row = manifest[manifest.index('action: "open-conductor"'):]
    row = row[: row.index("\n  },")]
    assert 'label: "Agents"' in row and 'toolLabel: "Agents"' in row
    assert 'shortcut: "⌃3"' in row
    # The old Agents application is unmapped (parked, never deleted).
    assert "inspect-personas-and-coders" not in manifest
    assert (ROOT / "web/src/desk/_parked/agents/companionApplication.ts").exists()
    routes = (ROOT / "web/src/routes.tsx").read_text(encoding="utf-8")
    assert '{ path: "/companion", surface: "open-conductor" }' in routes


def test_new_agent_left_the_desk_menu() -> None:
    registry = (ROOT / "web/src/desk/verbRegistry.ts").read_text(encoding="utf-8")
    assert 'id: "desk.new-agent"' not in registry
    assert (ROOT / "web/src/desk/_parked/agents/newAgentVerb.ts").exists()
