"""PARKED 20261108 (evening): tests of routes parked with the unreached-routes census.

From ``tests/integration/test_web_project_kb_api.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""
class TestDeleteProjectKB:
    def test_delete_removes_file_preserves_dir(
        self, test_client: TestClient, project_root_dir: Path, cache_invalidator: MagicMock
    ) -> None:
        path = _seed_kb(project_root_dir, {"stack": "python"})
        response = test_client.delete("/api/dictation/project-kb")
        assert response.status_code == 200
        assert not path.exists()
        assert (project_root_dir / ".holdspeak").is_dir(), (
            ".holdspeak/ must be preserved (it's also the anchor signal)"
        )
        cache_invalidator.assert_called_once()

    def test_delete_no_file_404(
        self, test_client: TestClient, project_root_dir: Path
    ) -> None:
        response = test_client.delete("/api/dictation/project-kb")
        assert response.status_code == 404

    def test_delete_no_project_404(self, test_client: TestClient, no_project: None) -> None:
        response = test_client.delete("/api/dictation/project-kb")
        assert response.status_code == 404
