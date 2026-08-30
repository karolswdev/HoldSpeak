"""Phase-91 React Dictation cockpit locks.

HS-132-12: the Phase-117 decomposition (HS-117-08) emptied
``DictationCore.tsx`` into ``cores/dictation/*`` — the shell now holds
only the wing roster, the door stack and the footer. These locks are
re-pointed at the deck (shell + sub-components) so the invariants they
guard are enforced against the code that actually ships.
"""
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_DECK_DIR = _REPO / "web/src/pages/cores/dictation"


def _page() -> str:
    """The Dictation shell alone (wings, door stack, footer)."""
    return (_REPO / "web/src/pages/cores/DictationCore.tsx").read_text()


def _deck() -> str:
    """The whole Dictation program: the shell plus every sub-component."""
    parts = [_page()]
    for source in sorted(_DECK_DIR.glob("*.ts*")):
        if source.name.endswith(".test.tsx"):
            continue
        parts.append(source.read_text())
    return "\n".join(parts)


def test_dictation_is_one_typed_section_graph() -> None:
    # HS-100-07: the cockpit became Speak — the loop is the front face,
    # Journal/Blocks are wings in the WINDOW HEAD, and every former
    # config tab stacks behind the one gear door. No tab wall.
    page = _page()
    applications = (_REPO / "web/src/desk/applications.ts").read_text()
    assert 'action: "dictate"' in applications
    assert 'label: "Speak"' in applications
    for wing in ("speak", "journal", "blocks"):
        assert f'id: "{wing}"' in page
    for door_section in ("<Readiness />", "<Memory />", "<Knowledge />",
                         "<Runtime />", "<Hooks />", "<Nudges />"):
        assert door_section in page, f"door must stack {door_section}"
    # HS-117-07 folded the WINGS + useState + useWindowWings triple into
    # useCoreWings; the wings still ride the WINDOW HEAD, never a tab wall.
    assert "useCoreWings" in page
    hooks = (_REPO / "web/src/pages/cores/core-hooks.tsx").read_text()
    assert "useWindowWings" in hooks
    assert "<Tabs" not in _deck()


def test_dictation_preserves_primary_api_verbs() -> None:
    deck = _deck()
    for endpoint in (
        "/api/dictation/readiness", "/api/dictation/dry-run",
        "/api/dictation/blocks", "/api/dictation/corrections",
        "/api/dictation/learning-digest", "/api/dictation/project-kb",
        "/api/dictation/project-hs", "/api/dictation/journal",
        "/api/dictation/agent-hooks", "/api/activity/nudges",
    ):
        assert endpoint in deck, endpoint


def test_dictation_keeps_device_local_project_scope() -> None:
    deck = _deck()
    assert "holdspeak.projectRootOverride" in deck
    assert "project_root" in deck
    assert "Project scope" in deck


def test_dictation_lists_are_react_owned_and_focus_safe() -> None:
    deck = _deck()
    assert ".innerHTML" not in deck
    assert "document.querySelector" not in deck
    assert "ConfirmVerb" in deck
    assert "SurfaceState" in deck
