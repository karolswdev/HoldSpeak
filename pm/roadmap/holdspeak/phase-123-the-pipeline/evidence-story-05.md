# Evidence - HS-123-05

- **Story:** HS-123-05 - Projects and projections
- **Status:** done
- **Date:** 2026-08-06

## Proof

### Captured run — 2026-08-07T02:02:20Z

- **Command:** `sh -c rg -n "class (ProjectService|ProjectionService)|def (list_projects|create_project|get_project|update_project|archive_project|list_briefings|list_resources|associate_meeting|since_last_meeting|set_presentation)" holdspeak/services && ! rg -n "get_database\(|ctx\.get_database" holdspeak/web/routes/projects.py holdspeak/web/routes/projections.py && ! rg -n "holdspeak\.web\.routes|WebContext|fastapi" holdspeak/services/project_service.py holdspeak/services/projection_service.py && uv run pytest -q tests/unit/test_project_projection_services.py tests/unit/test_web_routes_projections.py tests/integration/test_one_place_relationships.py tests/integration/test_web_activity_api.py -k "project or projection or axes"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5031425ff6622cef5c93be348b9a5ad86491d9a0

```text
holdspeak/services/projection_service.py:11:class ProjectionService:
holdspeak/services/projection_service.py:30:    def set_presentation(self, principal: Principal, projection_id: str, state: dict[str, Any]) -> dict[str, Any]:
holdspeak/services/project_service.py:14:class ProjectService:
holdspeak/services/project_service.py:20:    def list_projects(self, principal: Principal, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
holdspeak/services/project_service.py:26:    def create_project(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
holdspeak/services/project_service.py:41:    def get_project(self, principal: Principal, project_id: str) -> dict[str, Any]:
holdspeak/services/project_service.py:44:    def update_project(self, principal: Principal, project_id: str, patch: dict[str, Any]) -> dict[str, Any]:
holdspeak/services/project_service.py:66:    def archive_project(self, principal: Principal, project_id: str) -> bool:
holdspeak/services/project_service.py:71:    def list_briefings(self, principal: Principal, project_id: str, limit: int = 50) -> dict[str, Any]:
holdspeak/services/project_service.py:87:    def list_resources(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
holdspeak/services/project_service.py:114:    def associate_meeting(self, principal: Principal, project_id: str, meeting_id: str) -> bool:
holdspeak/services/project_service.py:130:    def since_last_meeting(self, principal: Principal, project_id: str) -> dict[str, Any]:
.............                                                            [100%]
13 passed, 36 deselected in 3.26s
```
