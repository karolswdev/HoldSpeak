"""Phase-91 React Dictation cockpit locks."""
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web/src/pages/cores/DictationCore.tsx").read_text()


def test_dictation_is_one_typed_section_graph() -> None:
    # HS-100-07: the cockpit became Speak — the loop is the front face,
    # Journal/Blocks are wings in the WINDOW HEAD, and every former
    # config tab stacks behind the one gear door. No tab wall.
    page = _page()
    surfaces = (_REPO / "web/src/desk/components/SurfaceWindows.tsx").read_text()
    assert '"Speak"' in surfaces
    for wing in ("speak", "journal", "blocks"):
        assert f'id: "{wing}"' in page
    for door_section in ("<Readiness />", "<Memory />", "<Knowledge />",
                         "<Runtime />", "<Hooks />", "<Nudges />"):
        assert door_section in page, f"door must stack {door_section}"
    assert "useWindowWings" in page and "<Tabs" not in page


def test_dictation_preserves_primary_api_verbs() -> None:
    page = _page()
    for endpoint in (
        "/api/dictation/readiness", "/api/dictation/dry-run",
        "/api/dictation/blocks", "/api/dictation/corrections",
        "/api/dictation/learning-digest", "/api/dictation/project-kb",
        "/api/dictation/project-hs", "/api/dictation/journal",
        "/api/dictation/agent-hooks", "/api/activity/nudges",
    ):
        assert endpoint in page


def test_dictation_keeps_device_local_project_scope() -> None:
    page = _page()
    assert "holdspeak.projectRootOverride" in page
    assert "project_root" in page
    assert "Project scope" in page


def test_dictation_lists_are_react_owned_and_focus_safe() -> None:
    page = _page()
    assert ".innerHTML" not in page
    assert "document.querySelector" not in page
    assert "ConfirmVerb" in page
    assert "SurfaceState" in page
