"""Phase-91 React meeting archive locks."""
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def test_history_uses_bounded_archive_and_detail_sections() -> None:
    page = (_REPO / "web/src/pages/HistoryPage.tsx").read_text()
    for tab in ("meetings", "actions", "speakers", "projects", "queues"):
        assert f'"{tab}"' in page
    for tab in ("transcript", "artifacts", "aftercare", "routing", "proposals"):
        assert f'"{tab}"' in page
    assert "MeetingDetail" in page and "ImportDialog" in page


def test_history_keeps_approval_and_export_governance() -> None:
    page = (_REPO / "web/src/pages/HistoryPage.tsx").read_text()
    assert '"approved"' in page and '"rejected"' in page
    assert 'row.status === "proposed" && !refused' in page
    assert 'policy.outcome === "refused"' in page
    assert "row.policy_snapshot" in page and "row.operation" in page
    assert "apiBlob" in page
    assert "commitment" in page and "authority_basis" in page
    assert "ConfirmAction" in page
