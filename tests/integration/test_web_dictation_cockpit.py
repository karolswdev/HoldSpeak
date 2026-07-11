"""Phase-91 React Dictation cockpit locks."""
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web/src/pages/DictationPage.tsx").read_text()


def test_dictation_is_one_typed_section_graph() -> None:
    page = _page()
    assert "Daily cockpit" in page and "Dictation" in page
    for section in ("ready", "dry", "blocks", "memory", "knowledge", "journal", "runtime", "hooks", "nudges"):
        assert f'["{section}"' in page
    assert "useMemo" in page and "<Tabs" in page


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
    assert "Project grounding" in page


def test_dictation_lists_are_react_owned_and_focus_safe() -> None:
    page = _page()
    assert ".innerHTML" not in page
    assert "document.querySelector" not in page
    assert "ConfirmAction" in page
    assert "ResourceState" in page
