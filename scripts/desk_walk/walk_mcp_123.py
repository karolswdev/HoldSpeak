"""HS-123-13 service-layer MCP catalog walk.

Run with:
    uv run python -m scripts.desk_walk.walk_mcp_123

The walk uses a fresh database and the services which back the MCP transport.
It deliberately avoids a hub: the goal is a fast, deterministic proof that the
expanded catalog remains wired to real persistence.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable

from holdspeak.db.core import Database
from holdspeak.mcp.resources import list_resources
from holdspeak.mcp.tools import TOOLS
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.desk_service import DeskService
from holdspeak.services.dictation_service import DictationService
from holdspeak.services.primitive_service import NotFound, PrimitiveService
from holdspeak.services.profile_service import ProfileService
from holdspeak.services.workbench_service import WorkbenchService


Check = Callable[[], None]


def _check(label: str, action: Check) -> str | None:
    """Run one visible walk leg and return its failure, if any."""
    try:
        action()
    except Exception as exc:  # Report every independent check before failing.
        print(f"FAIL {label}: {type(exc).__name__}: {exc}")
        return label
    print(f"PASS {label}")
    return None


def main() -> None:
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="holdspeak-mcp-123-") as tempdir:
        db = Database(Path(tempdir) / "walk.db")
        principal = Principal(PrincipalKind.OWNER, "walk")
        primitives = PrimitiveService(db)
        workbenches = WorkbenchService(db)
        profiles = ProfileService(db)
        dictation = DictationService(db)
        desk = DeskService(db)

        def primitive_lifecycle() -> None:
            created = primitives.create_note(
                principal,
                title="MCP 123 walk note",
                body_markdown="Real service-backed lifecycle proof.",
                tags=["walk"],
            )
            note_id = created["id"]
            assert primitives.get_note(principal, note_id)["title"] == "MCP 123 walk note"
            assert any(note["id"] == note_id for note in primitives.list_notes(principal))
            updated = primitives.update_note(principal, note_id, title="MCP 123 updated note")
            assert updated["title"] == "MCP 123 updated note"
            assert primitives.delete_note(principal, note_id) is True
            try:
                primitives.get_note(principal, note_id)
            except NotFound:
                return
            raise AssertionError("deleted note remained readable")

        def workbench_lifecycle() -> None:
            workbench = workbenches.create_workbench(principal, name="MCP 123 walk")
            assert workbenches.get_workbench(principal, workbench["id"])["id"] == workbench["id"]
            item = workbenches.add_item(
                principal, workbench["id"], title="Exercise add-item", body="walk"
            )
            assert item["workbench_id"] == workbench["id"]
            assert workbenches.delete_item(principal, workbench["id"], item["id"]) is True
            assert workbenches.delete_workbench(principal, workbench["id"]) is True

        def profile_listing() -> None:
            listed = profiles.list_profiles(principal)
            assert isinstance(listed["profiles"], list)
            assert "mesh_liveness" in listed

        def journal_listing() -> None:
            journal = dictation.list_journal(principal)
            assert journal["count"] == 0
            assert journal["items"] == []

        def desk_reads() -> None:
            snapshot = desk.snapshot(principal)
            assert snapshot["notes"] == []
            assert snapshot["workbenches"] == []
            assert desk.health() == {"status": "ok"}

        def tool_catalog() -> None:
            assert len(TOOLS) >= 40, f"expected >= 40 tools, got {len(TOOLS)}"

        def resource_catalog() -> None:
            catalog = list_resources()
            static_count = len(catalog["resources"])
            template_count = len(catalog["resourceTemplates"])
            assert static_count >= 9, f"expected >= 9 static resources, got {static_count}"
            assert template_count >= 7, f"expected >= 7 resource templates, got {template_count}"

        for label, action in (
            ("PrimitiveService CRUD lifecycle", primitive_lifecycle),
            ("WorkbenchService create and add item", workbench_lifecycle),
            ("ProfileService list profiles", profile_listing),
            ("DictationService list journal", journal_listing),
            ("DeskService snapshot and health", desk_reads),
            ("MCP tool catalog has at least 40 tools", tool_catalog),
            ("MCP resources have at least 9 static and 7 templates", resource_catalog),
        ):
            if failure := _check(label, action):
                failures.append(failure)

    if failures:
        raise SystemExit(f"MCP 123 walk failed: {', '.join(failures)}")
    print("MCP 123 service walk passed.")


if __name__ == "__main__":
    main()
