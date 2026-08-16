"""Phase-91 React meeting archive locks.

HS-132-12: HS-117-09 decomposed ``HistoryCore.tsx`` into ``cores/history/*``.
The wing/door/receipt-section roster is now declared in ``history/helpers.ts``
(which names itself "part of the phase-91 archive lock"), and the proposal
governance moved into ``history/useMeetingData.tsx``.
"""
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_HISTORY = _REPO / "web/src/pages/cores/history"


def test_history_uses_bounded_archive_and_detail_sections() -> None:
    shell = (_REPO / "web/src/pages/cores/HistoryCore.tsx").read_text()
    helpers = (_HISTORY / "helpers.ts").read_text()
    # The catalog + door roster is a BOUNDED, declared set — never an
    # open-ended tab wall. HS-102/111 renamed the old "meetings" tab to
    # the "outcomes" wing; the roster itself is unchanged in kind.
    assert "export const WINGS" in helpers
    for wing in ("outcomes", "record", "artifacts"):
        assert f'id: "{wing}"' in helpers, wing
    assert "export const DOOR_SECTIONS" in helpers
    for door in ("actions", "speakers", "projects", "queues"):
        assert f'"{door}"' in helpers, door
    # Receipt sections inside one open meeting: HS-117-09 turned each id
    # into its own component, so the roster is pinned at the composition.
    detail = (_HISTORY / "MeetingDetail.tsx").read_text()
    for section in (
        "<TranscriptWell",    # transcript
        "<ArtifactsLibrary",  # artifacts
        "<AftercareGadgets",  # aftercare
        "RAW · ROUTING",      # routing
        "<NeedsYouTable",     # proposals + open actions
    ):
        assert section in detail, section
    assert "proposalRows" in (_HISTORY / "useMeetingData.tsx").read_text()
    assert "MeetingDetail" in shell and "ImportSection" in shell


def test_history_keeps_approval_and_export_governance() -> None:
    shell = (_REPO / "web/src/pages/cores/HistoryCore.tsx").read_text()
    data = (_HISTORY / "useMeetingData.tsx").read_text()
    assert '"approved"' in data and '"rejected"' in data
    assert 'row.status === "proposed" && !refused' in data
    assert 'policy.outcome === "refused"' in data
    assert "row.policy_snapshot" in data and "row.operation" in data
    assert "commitment" in data and "authority_basis" in data
    # Export still goes through the blob verb on the shell's footer.
    assert "apiBlob" in shell
    assert "ConfirmVerb" in shell
