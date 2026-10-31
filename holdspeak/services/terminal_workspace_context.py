"""Connected context for one terminal inventory snapshot.

This module is read-only composition over the existing Delivery registry,
launch ledger and hub database.  A terminal is *bound* only when the launch's
stored immutable target still verifies against the target registry.  Session
names, hook labels and current directories are useful display facts, but they
never grant a launch association.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..delivery import factory_launch, registry as delivery_registry


def _empty(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "project": None,
        "source": None,
        "worktree": None,
        "launch": None,
        "program": None,
        "mcp": None,
    }


@dataclass(frozen=True)
class ContextSnapshot:
    """One read of context producers for one terminal inventory."""

    registry: Any = None
    launches: tuple[Mapping[str, Any], ...] = ()
    unavailable: bool = False


RegistryLoader = Callable[[], Any]
LaunchLoader = Callable[[], list[Mapping[str, Any]]]


class TerminalWorkspaceContext:
    """Read-only source/worktree/launch/project context for terminal rows."""

    def __init__(
        self,
        db: Any = None,
        *,
        registry_path: Optional[Path] = None,
        launches_path: Optional[Path] = None,
        registry_loader: Optional[RegistryLoader] = None,
        launch_loader: Optional[LaunchLoader] = None,
        project_id_loader: Optional[Callable[[Any, str, str], Optional[str]]] = None,
        project_loader: Optional[Callable[[Any, str], Any]] = None,
        program_loader: Optional[Callable[[Any, Mapping[str, Any]], Optional[dict[str, Any]]]] = None,
    ) -> None:
        self.db = db
        # Resolve module defaults when the composed service is constructed.
        # Test rigs and a boot-time HOME change must not inherit aliases frozen
        # when this module was imported.
        self.registry_path = Path(
            registry_path if registry_path is not None else delivery_registry.DEFAULT_REGISTRY_PATH
        )
        self.launches_path = Path(
            launches_path if launches_path is not None else factory_launch.DEFAULT_LAUNCHES_PATH
        )
        self._registry_loader = registry_loader or self._read_registry
        self._launch_loader = launch_loader or self._read_launches
        self._project_id_loader = project_id_loader or self._default_project_id
        self._project_loader = project_loader or self._default_project
        self._program_loader = program_loader or self._default_program

    def _read_registry(self) -> Any:
        return delivery_registry.DeliveryRegistry.read_only_snapshot(self.registry_path)

    def _read_launches(self) -> list[Mapping[str, Any]]:
        # read_all reloads once and preserves the distinction between a missing
        # ledger and an existing ledger that cannot be read.
        return [dict(row) for row in factory_launch.LaunchLedger(self.launches_path).read_all()]

    def snapshot(self) -> ContextSnapshot:
        """Load the composed context producers once, never per pane."""
        try:
            registry = self._registry_loader()
            launches = tuple(self._launch_loader())
        except Exception:
            return ContextSnapshot(unavailable=True)
        return ContextSnapshot(registry=registry, launches=launches)

    @staticmethod
    def _default_project_id(db: Any, kind: str, item_id: str) -> Optional[str]:
        if db is None:
            return None
        from .agent_brief import project_for_item

        # A missing filing is a legitimate ``None`` from the repository.  A
        # database failure must escape so the composed context is marked
        # unavailable rather than silently claiming that no Project exists.
        return project_for_item(db, kind, item_id)

    @staticmethod
    def _default_project(db: Any, project_id: str) -> Any:
        if db is None or not project_id:
            return None
        return db.projects.get_project(project_id)

    @staticmethod
    def _default_program(db: Any, launch: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        if db is None:
            return None
        from ..db.programs import ProgramStore

        store = ProgramStore(db)
        origin = launch.get("origin_ref") or {}
        step = None
        if str(origin.get("kind") or "") == "program_step":
            step = store.get_step(str(origin.get("id") or ""))
        if step is None and launch.get("launch_id"):
            step = store.step_of_launch(str(launch.get("launch_id") or ""))
        program = store.get_program(str(step.get("program_id") or "")) if step else None
        if not step or not program:
            return None
        return {
            "id": program["id"],
            "title": program["title"],
            "step_id": step["id"],
            "step_ordinal": int(step["ordinal"]),
        }

    @staticmethod
    def _resolved(path: Any) -> Optional[Path]:
        text = str(path or "").strip()
        if not text:
            return None
        try:
            return Path(text).expanduser().resolve()
        except (OSError, RuntimeError, ValueError):
            return None

    @classmethod
    def _worktree_for_path(cls, registry: Any, cwd: Any) -> tuple[Any, Any] | tuple[None, None]:
        candidate = cls._resolved(cwd)
        if candidate is None:
            return None, None
        choices: list[tuple[int, Any, Any]] = []
        try:
            sources = registry.sources()
        except Exception:
            return None, None
        for source in sources:
            for worktree in source.worktrees:
                root = cls._resolved(worktree.path)
                if root is None:
                    continue
                try:
                    candidate.relative_to(root)
                except ValueError:
                    continue
                # Prefer the deepest registered worktree when paths nest.
                choices.append((len(root.parts), source, worktree))
        if not choices:
            return None, None
        _depth, source, worktree = max(choices, key=lambda item: item[0])
        return source, worktree

    @staticmethod
    def _worktree_wire(source: Any, worktree: Any) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]]]:
        if source is None or worktree is None:
            return None, None
        return (
            {"id": str(source.source_id), "name": str(source.label)},
            {"id": str(worktree.worktree_id), "branch": str(worktree.branch)},
        )

    @staticmethod
    def _launch_for_target(
        launches: tuple[Mapping[str, Any], ...],
        issued: Mapping[str, Any],
        verify: Callable[[Any, Any], Mapping[str, Any]],
    ) -> Optional[Mapping[str, Any]]:
        target_id = str(issued.get("target_id") or "")
        generation = str(issued.get("target_generation") or "")
        pane_id = str(issued.get("pane_id") or "")
        if not target_id or not generation or not pane_id:
            return None
        candidates = []
        for launch in launches:
            target = launch.get("target")
            if not isinstance(target, Mapping):
                continue
            if (
                str(target.get("target_id") or "") == target_id
                and str(target.get("target_generation") or "") == generation
                and (
                    not target.get("pane_id")
                    or str(target.get("pane_id")) == pane_id
                )
            ):
                candidates.append(launch)
        if len(candidates) != 1:
            return None
        try:
            verified = dict(verify(target_id, generation) or {})
        except Exception:
            return None
        if (
            verified.get("status") != "ok"
            or str(verified.get("target_id") or "") != target_id
            or str(verified.get("target_generation") or "") != generation
            or str(verified.get("pane_id") or "") != pane_id
        ):
            return None
        return candidates[0]

    def _bound_details(
        self,
        launch: Mapping[str, Any],
        registry: Any,
    ) -> dict[str, Any]:
        origin = launch.get("origin_ref") if isinstance(launch.get("origin_ref"), Mapping) else None
        kind = str((origin or {}).get("kind") or "")
        item_id = str((origin or {}).get("id") or "")
        safe_origin = {"kind": kind, "id": item_id} if kind and item_id else None
        project = None
        project_id = self._project_id_loader(self.db, kind, item_id) if kind and item_id else None
        if not project_id:
            story = launch.get("story_ref")
            story_project = str(story.get("project") or "") if isinstance(story, Mapping) else ""
            if story_project and story_project != "desk":
                project_id = story_project
        if project_id:
            record = self._project_loader(self.db, str(project_id))
            if record is not None:
                project = {"id": str(getattr(record, "id", project_id)), "name": str(getattr(record, "name", ""))}
        program = self._program_loader(self.db, launch)
        source = worktree = None
        source_id = str(launch.get("source_id") or "")
        worktree_id = str(launch.get("worktree_id") or "")
        try:
            source_record = registry.get(source_id) if source_id else None
            if source_record is not None:
                worktree_record = next(
                    (item for item in source_record.worktrees if str(item.worktree_id) == worktree_id), None
                )
                source, worktree = self._worktree_wire(source_record, worktree_record)
        except Exception:
            source = worktree = None
        raw_mcp = launch.get("mcp")
        mcp = None
        if isinstance(raw_mcp, Mapping) and raw_mcp.get("server") and raw_mcp.get("palette"):
            mcp = {
                "status": "configured",
                "server": str(raw_mcp.get("server")),
                "palette": str(raw_mcp.get("palette")),
                "pre_approved": bool(raw_mcp.get("pre_approved")),
                "read_only": bool(launch.get("read_only")),
            }
        elif isinstance(launch, Mapping):
            mcp = {"status": "unknown", "server": None, "palette": None, "pre_approved": None, "read_only": None}
        return {
            "status": "bound",
            "project": project,
            "source": source,
            "worktree": worktree,
            "launch": {
                "id": str(launch.get("launch_id") or ""),
                "profile_id": str(launch.get("profile_id") or ""),
                "state": str(launch.get("state") or ""),
                "role": str(launch.get("role") or "builder"),
                "origin_ref": safe_origin,
                "attempt_id": str(launch.get("attempt_id") or "") or None,
            },
            "program": program,
            "mcp": mcp,
        }

    def for_terminal(
        self,
        *,
        snapshot: ContextSnapshot,
        issued: Mapping[str, Any],
        current_path: Any,
        verify: Callable[[Any, Any], Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Build one exact wire DTO; all inputs come from this snapshot."""
        if snapshot.unavailable or snapshot.registry is None:
            return _empty("unavailable")
        launch = self._launch_for_target(snapshot.launches, issued, verify)
        if launch is not None:
            try:
                return self._bound_details(launch, snapshot.registry)
            except Exception:
                # A producer failure is not evidence of an unfiled Project or
                # missing Program.  Keep the live terminal visible while
                # honestly marking only its connected context unavailable.
                return _empty("unavailable")
        source, worktree = self._worktree_for_path(snapshot.registry, current_path)
        if source is not None and worktree is not None:
            source_wire, worktree_wire = self._worktree_wire(source, worktree)
            return {
                **_empty("worktree"),
                "source": source_wire,
                "worktree": worktree_wire,
            }
        return _empty("unbound")


__all__ = ["ContextSnapshot", "TerminalWorkspaceContext"]
