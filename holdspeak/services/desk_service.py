"""Transport-neutral desk bootstrap and aggregate reads (HS-122-05)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

from typing import Any

from ..db.core import Database
from ..db.seed import apply_seed, reset_desk
from ..principals import Principal


@observe_service
class DeskService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def seed(self, principal: Principal) -> dict[str, Any]:
        report = apply_seed(self._db)
        return {"success": True, **report.to_dict()}

    def reset(self, principal: Principal) -> dict[str, Any]:
        report = reset_desk(self._db)
        seed = report.seed
        return {
            "success": True,
            "tombstoned": dict(report.tombstoned),
            "tombstoned_total": report.tombstoned_total,
            "seeded": dict(seed.applied) if seed else {},
            "seeded_total": seed.total if seed else 0,
            "profiles_seeded": seed.profiles_seeded if seed else 0,
            "profiles_adopted": dict(seed.profiles_adopted) if seed else {},
            "filed": seed.filed if seed else 0,
            "manifest": seed.manifest if seed else None,
        }

    def snapshot(self, principal: Principal) -> dict[str, Any]:
        """Return the durable desk primitives as one transport-neutral snapshot."""
        return {
            "notes": [item.to_dict() for item in self._db.notes.list()],
            "decisions": [item.to_dict() for item in self._db.desk_decisions.list()],
            "directories": [item.to_dict() for item in self._db.directories.list()],
            "workflows": [item.to_dict() for item in self._db.workflows.list()],
            "chains": [item.to_dict() for item in self._db.chains.list()],
            "profiles": [item.to_dict() for item in self._db.profiles.list()],
            "workbenches": [item.to_dict() for item in self._db.workbenches.list()],
        }

    def health(self) -> dict[str, Any]:
        from ..kernel.runtime import _service
        faults = list(getattr(_service(), "projection_stager", None).health_faults)
        if not faults:
            return {"status": "ok"}
        return {"status": "unhealthy", "projection_reconciliation_faults": faults}
