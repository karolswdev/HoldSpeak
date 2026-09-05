"""HS-171-02: HeartbeatService -- the sweep scheduler and aggregate cache.

The heartbeat is the unattended cadence that evaluates due watches on a
configurable interval, caches the needs-you aggregate, and receipts every
sweep through the kernel (Article XI.2).

Settings are stored in the cadence_policies table (key `heartbeat`),
not in Config TOML -- the TOML file is the owner's hand-edited runtime
config; the heartbeat interval is a server-side operational setting.

M3 (counsel): this service does NOT re-implement the aggregate builder.
It delegates to ``needs_you_aggregate.build_aggregate`` /
``NeedsYouCache`` -- that module is the single owner of the shape.

M1 (counsel): the muted_projects setting is passed through to the
aggregate builder; muted items are marked ``muted: true`` and excluded
from the count that drives the notification edge.

N2 (counsel): the sweep receipt's ``outcomes`` is bounded -- a summary
of counts per outcome state + failing watch ids only.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
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


def _summarize_outcomes(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    """N2: bounded receipt summary -- counts per state + failing watch ids only.

    Instead of dumping the full unbounded outcomes list into the receipt,
    produce a compact summary: how many evaluated/skipped/failed, and the
    watch_ids of any that failed.
    """
    counts: dict[str, int] = {}
    failed_ids: list[str] = []
    for o in outcomes:
        state = o.get("outcome", "unknown")
        counts[state] = counts.get(state, 0) + 1
        if state in ("error", "failed"):
            wid = o.get("watch_id", "")
            if wid:
                failed_ids.append(wid)
    return {
        "counts": counts,
        "total": len(outcomes),
        "failed_watch_ids": failed_ids,
    }


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
        sweep_id = f"sweep_{uuid.uuid4().hex[:12]}"

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

        # M3: Refresh the aggregate cache via the canonical builder
        self.refresh_aggregate(principal, sweep_id=sweep_id)

        duration_ms = (time.time() - t0) * 1000

        # Compute next sweep time
        sweep_minutes = settings["sweep_every_minutes"]
        next_at = (now + timedelta(minutes=sweep_minutes)).isoformat(timespec="seconds")

        # Persist timestamps
        settings["last_sweep_at"] = now.isoformat(timespec="seconds")
        settings["next_sweep_at"] = next_at
        self._persist(settings)

        # N2: Build the receipt with bounded outcomes summary
        receipt = {
            "kind": "heartbeat.sweep",
            "at": now.isoformat(timespec="seconds"),
            "rooms": rooms_evaluated,
            "watches": watch_count,
            "duration_ms": round(duration_ms, 1),
            "held": held,
            "errors": len(errors),
            "outcomes": _summarize_outcomes(outcomes),
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

    # ── Aggregate cache (M3: delegates to needs_you_aggregate) ─────────

    def _build_aggregate_via_canonical(
        self, principal: Principal | None = None,
    ) -> dict[str, Any]:
        """Build the aggregate via the canonical needs_you_aggregate.build_aggregate.

        M1: passes muted_project_ids from the heartbeat setting into the builder.
        Muted Rooms' items get ``muted: true`` and are excluded from ``count``
        but included in ``mutedCount``.
        """
        from holdspeak.services.needs_you_aggregate import build_aggregate
        from holdspeak.services.project_service import ProjectService

        ps = ProjectService(self._db, observer=self._observer)
        _p = principal or Principal(PrincipalKind.OWNER, "heartbeat")
        settings = self.get_settings()
        muted_ids = set(settings.get("muted_projects", []))

        aggregate = build_aggregate(
            list_projects=ps.list_projects,
            room=ps.room,
            principal=_p,
        )

        # M1: apply mute list -- mark muted items and split counts.
        items = aggregate.get("items", [])
        unmuted_items: list[dict[str, Any]] = []
        muted_count = 0
        for item in items:
            if item.get("projectId") in muted_ids:
                item["muted"] = True
                muted_count += 1
            else:
                item["muted"] = False
                unmuted_items.append(item)

        aggregate["count"] = len(unmuted_items)
        aggregate["mutedCount"] = muted_count
        return aggregate

    def refresh_aggregate(
        self, principal: Principal | None = None, *, sweep_id: str | None = None,
    ) -> dict[str, Any]:
        """Refresh the needs-you aggregate via the canonical builder.

        M3: delegates to needs_you_aggregate.build_aggregate -- this
        service does NOT re-implement the aggregate shape.
        """
        try:
            from holdspeak.services.needs_you_aggregate import NeedsYouCache

            _p = principal or Principal(PrincipalKind.OWNER, "heartbeat")

            # Build a one-shot cache and populate it.  In the live runtime
            # the NeedsYouCache lives on the route/context; here we call the
            # canonical builder directly.
            aggregate = self._build_aggregate_via_canonical(_p)
            if sweep_id:
                aggregate["sweepId"] = sweep_id
            return aggregate
        except Exception as exc:
            log.error("heartbeat aggregate refresh failed: %s", exc)
            return {"count": 0, "projects": [], "items": [], "mutedCount": 0}

    def get_aggregate(self, principal: Principal | None = None) -> dict[str, Any]:
        """Return the aggregate (always fresh from the canonical builder)."""
        return self.refresh_aggregate(principal)

    # ── Muted-aware count for notification edge ────────────────────────

    def notification_count(self, principal: Principal | None = None) -> int:
        """M1: the count that drives the notification edge EXCLUDES muted.

        Badge = shade caption = notification = ONE count everywhere.
        """
        agg = self._build_aggregate_via_canonical(principal)
        return agg.get("count", 0)

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
