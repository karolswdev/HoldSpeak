"""HS-171-02: HeartbeatService -- the sweep scheduler and aggregate cache.

The heartbeat is the unattended cadence that evaluates due watches on a
configurable interval, caches the needs-you aggregate, and receipts every
sweep through the kernel (Article XI.2).

Settings are stored in the cadence_policies table (key `heartbeat`),
not in Config TOML -- the TOML file is the owner's hand-edited runtime
config; the heartbeat interval is a server-side operational setting.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.observer import NullObserver, PipelineObserver

log = logging.getLogger(__name__)

# Defaults
_DEFAULT_SWEEP_EVERY = 15       # minutes
_DEFAULT_QUIET_START = 22       # hour
_DEFAULT_QUIET_END = 8          # hour
_DEFAULT_NOTIFY = "edge"        # off | edge | every_sweep
_HEARTBEAT_POLICY_ID = "heartbeat"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _now_epoch() -> float:
    return time.time()


class HeartbeatService:
    """Owns the heartbeat sweep settings, the sweep loop, and the aggregate cache."""

    def __init__(
        self,
        db: Database,
        *,
        observer: PipelineObserver | None = None,
        watch_service: Any | None = None,
    ) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        self._watch_service = watch_service
        # In-memory aggregate cache, invalidated by each sweep.
        self._aggregate_cache: dict[str, Any] | None = None
        self._cache_at: float = 0.0

    # ── Settings ───────────────────────────────────────────────────────

    def get_settings(self) -> dict[str, Any]:
        """Read heartbeat settings from cadence_policies."""
        policy = self._db.cadence.get_policy(_HEARTBEAT_POLICY_ID)
        if policy is None:
            return self._defaults()
        config = policy.config if hasattr(policy, "config") else (policy.get("config") if isinstance(policy, dict) else {})
        return {
            "sweep_every_minutes": int(config.get("sweep_every_minutes", _DEFAULT_SWEEP_EVERY)),
            "quiet_hours": {
                "start": int(config.get("quiet_start", _DEFAULT_QUIET_START)),
                "end": int(config.get("quiet_end", _DEFAULT_QUIET_END)),
            },
            "notify": str(config.get("notify", _DEFAULT_NOTIFY)),
            "muted_projects": list(config.get("muted_projects", [])),
            "last_sweep_at": config.get("last_sweep_at"),
            "next_sweep_at": config.get("next_sweep_at"),
        }

    def update_settings(self, patch: dict[str, Any]) -> dict[str, Any]:
        """Update heartbeat settings. Returns the new state."""
        current = self.get_settings()
        if "sweep_every_minutes" in patch:
            val = int(patch["sweep_every_minutes"])
            if val < 1:
                val = 1
            if val > 1440:
                val = 1440
            current["sweep_every_minutes"] = val
        if "quiet_hours" in patch:
            qh = patch["quiet_hours"]
            if isinstance(qh, dict):
                if "start" in qh:
                    current["quiet_hours"]["start"] = int(qh["start"]) % 24
                if "end" in qh:
                    current["quiet_hours"]["end"] = int(qh["end"]) % 24
        if "notify" in patch:
            n = str(patch["notify"])
            if n in ("off", "edge", "every_sweep"):
                current["notify"] = n
        if "muted_projects" in patch:
            current["muted_projects"] = list(patch["muted_projects"])
        self._persist(current)
        return current

    def _defaults(self) -> dict[str, Any]:
        return {
            "sweep_every_minutes": _DEFAULT_SWEEP_EVERY,
            "quiet_hours": {"start": _DEFAULT_QUIET_START, "end": _DEFAULT_QUIET_END},
            "notify": _DEFAULT_NOTIFY,
            "muted_projects": [],
            "last_sweep_at": None,
            "next_sweep_at": None,
        }

    def _persist(self, settings: dict[str, Any]) -> None:
        from holdspeak.cadence.models import CadencePolicy

        config = {
            "sweep_every_minutes": settings["sweep_every_minutes"],
            "quiet_start": settings["quiet_hours"]["start"],
            "quiet_end": settings["quiet_hours"]["end"],
            "notify": settings["notify"],
            "muted_projects": settings["muted_projects"],
            "last_sweep_at": settings.get("last_sweep_at"),
            "next_sweep_at": settings.get("next_sweep_at"),
        }
        self._db.cadence.upsert_policy(CadencePolicy(
            id=_HEARTBEAT_POLICY_ID,
            name=_HEARTBEAT_POLICY_ID,
            enabled=True,
            config=config,
        ))

    # ── In quiet hours? ────────────────────────────────────────────────

    def in_quiet_hours(self, now: datetime | None = None) -> bool:
        """Check whether the current time falls within quiet hours."""
        settings = self.get_settings()
        if now is None:
            now = datetime.now()
        hour = now.hour
        start = settings["quiet_hours"]["start"]
        end = settings["quiet_hours"]["end"]
        if start == end:
            return False
        if start < end:
            return start <= hour < end
        # Wraps midnight (e.g. 22..8)
        return hour >= start or hour < end

    # ── The sweep ──────────────────────────────────────────────────────

    def run_sweep(self, principal: Principal) -> dict[str, Any]:
        """Run one heartbeat sweep: evaluate due watches, refresh aggregate, receipt.

        Returns the sweep receipt payload.
        """
        t0 = time.time()
        now = datetime.now(timezone.utc)
        settings = self.get_settings()

        # Quiet hours check
        held = self.in_quiet_hours(datetime.now())

        outcomes: list[dict[str, Any]] = []
        rooms_evaluated = 0
        watch_count = 0
        errors: list[dict[str, Any]] = []

        if not held:
            # Call WatchService.evaluate_due to evaluate all due watches
            if self._watch_service is not None:
                try:
                    results = self._watch_service.evaluate_due(principal)
                    if isinstance(results, list):
                        outcomes = results
                        watch_count = len(results)
                        # Count unique projects from evaluated watches
                        project_ids = set()
                        for o in results:
                            wid = o.get("watch_id", "")
                            # Try to look up the project for this watch
                            try:
                                with self._db._connection() as conn:
                                    row = conn.execute(
                                        "SELECT project_id FROM connector_watches WHERE id=?",
                                        (wid,),
                                    ).fetchone()
                                    if row and row["project_id"]:
                                        project_ids.add(row["project_id"])
                            except Exception:
                                pass
                            if o.get("outcome") in ("error", "failed"):
                                errors.append(o)
                        rooms_evaluated = len(project_ids)
                except Exception as exc:
                    log.error("heartbeat sweep evaluate_due failed: %s", exc)
                    errors.append({"error": str(exc)})

        # Refresh the aggregate cache
        self.refresh_aggregate(principal)

        duration_ms = (time.time() - t0) * 1000

        # Compute next sweep time
        sweep_minutes = settings["sweep_every_minutes"]
        next_at = (now + __import__("datetime").timedelta(minutes=sweep_minutes)).isoformat(timespec="seconds")

        # Persist timestamps
        settings["last_sweep_at"] = now.isoformat(timespec="seconds")
        settings["next_sweep_at"] = next_at
        self._persist(settings)

        # Build the receipt
        receipt = {
            "kind": "heartbeat.sweep",
            "at": now.isoformat(timespec="seconds"),
            "rooms": rooms_evaluated,
            "watches": watch_count,
            "duration_ms": round(duration_ms, 1),
            "held": held,
            "errors": len(errors),
            "outcomes": outcomes,
        }

        # Write kernel receipt (Article XI.2)
        self._write_receipt(receipt)

        # Write pipeline_events
        self._write_pipeline_event(receipt, duration_ms)

        return receipt

    def _write_receipt(self, receipt: dict[str, Any]) -> None:
        """Write a kernel receipt for the sweep."""
        receipt_id = f"hb_rcpt_{uuid.uuid4().hex[:12]}"
        operation_id = f"hb_op_{uuid.uuid4().hex[:12]}"
        idem_key = f"heartbeat:{receipt['at']}:{uuid.uuid4().hex[:8]}"
        now = _now_epoch()
        state = "succeeded" if not receipt.get("errors") else "failed"
        outcome = json.dumps(receipt, default=str, separators=(",", ":"))

        try:
            with self._db._connection() as conn:
                conn.execute(
                    """INSERT INTO kernel_operations
                       (operation_id, request_id, idempotency_key, name, version,
                        principal_kind, principal_identity, target_ref, placement,
                        envelope_sha256, policy_version, authority_basis,
                        state, revision, native_id, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                    (
                        operation_id,
                        idem_key,
                        idem_key,
                        "heartbeat.sweep",
                        1,
                        "owner",
                        "heartbeat-service",
                        "heartbeat:sweep",
                        "local",
                        "",
                        "",
                        "heartbeat-conductor",
                        state,
                        operation_id,
                        now,
                        now,
                    ),
                )
                conn.execute(
                    """INSERT INTO kernel_receipts
                       (receipt_id, operation_id, state, outcome, result_ref, created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (receipt_id, operation_id, state, outcome, "", now),
                )
        except Exception as exc:
            log.error("heartbeat receipt write failed: %s", exc)

    def _write_pipeline_event(self, receipt: dict[str, Any], duration_ms: float) -> None:
        """Write a pipeline_events row for the sweep."""
        from holdspeak.services.observer import PipelineEvent

        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            service="HeartbeatService",
            method="run_sweep",
            principal_kind="owner",
            principal_identity="heartbeat-conductor",
            args_summary="{}",
            result_summary=json.dumps(
                {"watches": receipt["watches"], "rooms": receipt["rooms"],
                 "held": receipt["held"]},
                default=str, separators=(",", ":")),
            error=None if not receipt.get("errors") else f"{receipt['errors']} errors",
            error_code=None,
            duration_ms=duration_ms,
            correlation_id=str(uuid.uuid4()),
            is_async=False,
        )
        try:
            self._observer.on_event(event)
        except Exception:
            pass

    # ── Aggregate cache ────────────────────────────────────────────────

    def refresh_aggregate(self, principal: Principal | None = None) -> dict[str, Any]:
        """Refresh the needs-you aggregate cache.

        Calls the same builder that projects.py uses -- ProjectService's
        room section builder -- to build the aggregate.
        """
        from holdspeak.services.project_service import ProjectService

        try:
            ps = ProjectService(self._db, observer=self._observer)
            _p = principal or Principal(PrincipalKind.OWNER, "heartbeat")
            projects = ps.list_projects(_p, {"include_archived": False})
            _SEVERITY_ORDER = {"danger": 0, "warning": 1, "info": 2}
            items: list[dict] = []
            project_ids: set[str] = set()

            for proj in projects:
                pid = proj.get("id") or ""
                if not pid:
                    continue
                try:
                    room = ps.room(_p, pid)
                except Exception:
                    continue
                needs = room.get("needsYou", {})
                if needs.get("state") != "ok":
                    continue
                for item in (needs.get("items") or []):
                    items.append({
                        "projectId": pid,
                        "projectName": proj.get("name") or proj.get("title") or "",
                        "ref": item.get("title", ""),
                        "title": item.get("title", ""),
                        "why": item.get("why", ""),
                        "severity": item.get("severity", "info"),
                    })
                    project_ids.add(pid)

            items.sort(key=lambda r: (
                _SEVERITY_ORDER.get(r.get("severity", "info"), 2),
                r.get("why") or "",
            ))

            self._aggregate_cache = {
                "count": len(items),
                "projects": sorted(project_ids),
                "items": items,
            }
            self._cache_at = time.time()
        except Exception as exc:
            log.error("heartbeat aggregate refresh failed: %s", exc)
            self._aggregate_cache = {"count": 0, "projects": [], "items": []}
            self._cache_at = time.time()

        return self._aggregate_cache

    def get_aggregate(self, principal: Principal | None = None) -> dict[str, Any]:
        """Return the cached aggregate, refreshing if stale."""
        settings = self.get_settings()
        ttl = settings["sweep_every_minutes"] * 60
        if self._aggregate_cache is None or (time.time() - self._cache_at) > ttl:
            return self.refresh_aggregate(principal)
        return self._aggregate_cache

    # ── Hub mirror ─────────────────────────────────────────────────────

    def hub_rhythm(self) -> dict[str, Any]:
        """Build the rhythm sub-object for GET /api/settings/hub."""
        settings = self.get_settings()
        # Count cadence loops
        loops = 0
        try:
            loops = len(self._db.cadence.list_loops())
        except Exception:
            pass
        return {
            "loops": loops,
            "sweepEveryMinutes": settings["sweep_every_minutes"],
            "nextSweepAt": settings.get("next_sweep_at"),
            "lastSweepAt": settings.get("last_sweep_at"),
            "quiet": {
                "start": settings["quiet_hours"]["start"],
                "end": settings["quiet_hours"]["end"],
                "held": self.in_quiet_hours(),
            },
        }
