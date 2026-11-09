# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_agents_name_guard.py to restore.

# ruff: noqa


# --- test_the_guard_reads_conductor_coder_and_the_face_words: P2: tests the guard's own regexes, not the face
def test_the_guard_reads_conductor_coder_and_the_face_words() -> None:
    assert CONDUCTOR.search("Conductor") and not CONDUCTOR.search("open-conductor")
    assert not CONDUCTOR.search("ConductorWindow") and not CONDUCTOR.search("/conductor")
    assert CODER.search("Hand to coder") and CODER.search("CODERS")
    assert not CODER.search("coder:claude:1") and not CODER.search("desk-coder-draft")
    assert FACE_WORDS.search("Re-brief") and FACE_WORDS.search("WANTS APPROVAL")
    assert FACE_WORDS.search("Raw") and not FACE_WORDS.search("Rawness")
    assert not _is_text("coder") and _is_text("CODER") and _is_text("the coder")


# --- test_the_desk_names_the_conductor_agents: P8: source-text scan that parked files exist and a manifest string is present
def test_the_desk_names_the_conductor_agents() -> None:
    manifest = (ROOT / "web/src/desk/applications.ts").read_text(encoding="utf-8")
    row = manifest[manifest.index('action: "open-conductor"'):]
    row = row[: row.index("\n  },")]
    assert 'label: "Agents"' in row and 'toolLabel: "Agents"' in row
    assert 'shortcut: "⌃4"' in row
    # The old Agents application is unmapped (parked, never deleted).
    assert "inspect-personas-and-coders" not in manifest
    assert (ROOT / "web/src/desk/_parked/agents/companionApplication.ts").exists()
    routes = (ROOT / "web/src/routes.tsx").read_text(encoding="utf-8")
    assert '{ path: "/companion", surface: "open-conductor" }' in routes


# --- test_new_agent_left_the_desk_menu: P8: source-text scan that parked files exist and a manifest string is present
def test_new_agent_left_the_desk_menu() -> None:
    registry = (ROOT / "web/src/desk/verbRegistry.ts").read_text(encoding="utf-8")
    assert 'id: "desk.new-agent"' not in registry
    assert (ROOT / "web/src/desk/_parked/agents/newAgentVerb.ts").exists()
