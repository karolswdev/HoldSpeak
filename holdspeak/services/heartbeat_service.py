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
        notifier: Any | None = None,
        calendar_conductor: Any | None = None,
        clock: Any | None = None,
        local_zone: Any | None = None,
    ) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        self._watch_service = watch_service
        self._notifier = notifier  # injectable for tests; None = OS default
        # HS-175-02: the calendar refresh rides the heartbeat sweep.
        self._calendar_conductor = calendar_conductor
        # HS-200-03: the sweep read the clock TWICE — once as aware UTC for the
        # receipt and once as naive local for the quiet-hours test — so the two
        # could straddle a second, and neither could be injected. A sweep held
        # by quiet hours writes no `calendar` sub-receipt, which is why
        # tests/unit/test_hs175_calendar_wire.py passed by day and failed on any
        # machine running it between 22:00 and 08:00 local, the CI runner
        # included. One injectable instant now serves both readings.
        self._clock = clock
        # Quiet hours are LOCAL hours, so the zone is as much an input as the
        # instant. Injecting the instant alone is not enough: a fixed UTC noon
        # is midnight in Auckland and still lands inside the default window.
        # None keeps production behaviour -- this machine's own zone.
        self._local_zone = local_zone

    def _now_utc(self) -> datetime:
        """The current instant, aware and in UTC, from the injected clock."""
        if self._clock is None:
            return datetime.now(timezone.utc)
        now = self._clock()
        return now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)

    def _now_local(self) -> datetime:
        """The one sweep instant expressed in the quiet-hours zone."""
        return self._now_utc().astimezone(self._local_zone)

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
            "last_notified_count": int(config.get("last_notified_count", 0)),
            # HS-174-08: remote runner settings.
            "runs_on": str(config.get("runs_on", "local")),
            "remote_hosts": self._compute_remote_hosts(),
            "last_remote_run_at": self._last_remote_run_at(),
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
        # HS-174-08: runs_on setting.
        if "runs_on" in patch:
            val = str(patch["runs_on"]).strip()
            current["runs_on"] = val if val else "local"
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
            "last_notified_count": 0,
            # HS-174-08: remote runner defaults (computed values added in
            # get_settings; not stored).
            "runs_on": "local",
            "remote_hosts": self._compute_remote_hosts(),
            "last_remote_run_at": self._last_remote_run_at(),
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
            "last_notified_count": settings.get("last_notified_count", 0),
            # HS-174-08
            "runs_on": settings.get("runs_on", "local"),
        }
        self._db.cadence.upsert_policy(CadencePolicy(
            id=_HEARTBEAT_POLICY_ID,
            name=_HEARTBEAT_POLICY_ID,
            enabled=True,
            config=config,
        ))

    # ── HS-174-08: remote runner helpers ─────────────────────────────────

    def _compute_remote_hosts(self) -> list[str]:
        """Remote hosts that have called POST /api/mcp in the last 30 days.

        Derived from pipeline_events callers with origin='remote'.
        """
        thirty_days_ago = time.time() - 30 * 86400
        try:
            with self._db._connection() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT caller FROM pipeline_events "
                    "WHERE origin = 'remote' AND caller != '' "
                    "AND timestamp > ? "
                    "ORDER BY caller",
                    (thirty_days_ago,),
                ).fetchall()
            return [str(row["caller"]) for row in rows]
        except Exception:
            return []

    def _last_remote_run_at(self) -> str | None:
        """Newest heartbeat.sweep receipt with origin=remote (ISO string)."""
        try:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT timestamp FROM pipeline_events "
                    "WHERE service = 'HeartbeatService' AND method = 'run_sweep' "
                    "AND origin = 'remote' "
                    "ORDER BY timestamp DESC LIMIT 1",
                ).fetchone()
            if row:
                from datetime import datetime as _dt, timezone as _tz
                return _dt.fromtimestamp(
                    float(row["timestamp"]), _tz.utc,
                ).isoformat(timespec="seconds")
        except Exception:
            pass
        return None

    def record_held_remote(self, host: str) -> None:
        """Record that the local loop held because runs_on is a remote host.

        Writes a quiet pipeline_events row (no notification, no kernel receipt).
        """
        from holdspeak.services.observer import PipelineEvent

        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            service="HeartbeatService",
            method="run_sweep",
            principal_kind="owner",
            principal_identity="heartbeat-conductor",
            args_summary=json.dumps({"held": True, "runs_on": host}),
            result_summary=json.dumps({"outcome": "held_remote_runs_on", "host": host}),
            error=None,
            error_code=None,
            duration_ms=0.0,
            correlation_id=str(uuid.uuid4()),
            is_async=False,
            origin="local",
            caller="",
            caller_identity="",
        )
        try:
            self._observer.on_event(event)
        except Exception:
            pass

    # ── In quiet hours? ────────────────────────────────────────────────

    def in_quiet_hours(self, now: datetime | None = None) -> bool:
        """Check whether the current time falls within quiet hours."""
        settings = self.get_settings()
        if now is None:
            # HS-200-03: default through the injected clock, in local hours,
            # so no caller can reach an un-injectable wall clock from here.
            now = self._now_local()
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
        now = self._now_utc()
        settings = self.get_settings()
        sweep_id = f"sweep_{uuid.uuid4().hex[:12]}"

        # Quiet hours check. Quiet hours are the owner's LOCAL hours, so the one
        # sweep instant is converted to this machine's zone rather than read
        # from the clock a second time.
        held = self.in_quiet_hours(self._now_local())

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

        # HS-175-02: calendar refresh rides the heartbeat sweep.
        # Own failure boundary: a conductor crash never breaks the loop.
        calendar_refresh_receipt: dict[str, Any] | None = None
        if not held and self._calendar_conductor is not None:
            try:
                applied = self._calendar_conductor.refresh()
                calendar_refresh_receipt = {
                    "kind": "calendar.refresh",
                    "applied": applied,
                }
                # Per-source outcomes with host for HTTPS sources.
                try:
                    config = self._calendar_conductor._config_loader()
                    source_outcomes: list[dict[str, str]] = []
                    for src in config.calendar.sources:
                        if src.enabled:
                            url = str(src.url or "")
                            entry: dict[str, str] = {"source_id": src.id}
                            if url.lower().startswith("https://"):
                                try:
                                    from urllib.parse import urlparse
                                    entry["host"] = urlparse(url).hostname or ""
                                except Exception:
                                    entry["host"] = ""
                            source_outcomes.append(entry)
                    if source_outcomes:
                        calendar_refresh_receipt["sources"] = source_outcomes
                except Exception:
                    pass
            except Exception as exc:
                log.error("heartbeat sweep calendar refresh failed: %s", exc)
                calendar_refresh_receipt = {
                    "kind": "calendar.refresh",
                    "applied": False,
                    "error": str(exc),
                }

        # HS-175-04: backfill meeting Watches for Rooms that have linked
        # meetings but no meeting Watch yet.  Idempotent (ensure_meeting_watch
        # checks before creating).  Own failure boundary.
        # HS-175 counsel C7(a): a Room with a meeting Watch in ANY state
        # (retired included) is never backfilled -- Retire is the owner's
        # word and the sweep does not take it back.
        meeting_watch_backfill: dict[str, Any] | None = None
        if not held:
            try:
                from holdspeak.services.watch_service import ensure_meeting_watch
                with self._db._connection() as conn:
                    rows = conn.execute(
                        """SELECT DISTINCT mp.project_id
                           FROM meeting_projects mp
                           WHERE NOT EXISTS (
                               SELECT 1 FROM connector_watches cw
                               WHERE cw.project_id = mp.project_id
                                 AND cw.connector_id = 'meeting'
                           )""",
                    ).fetchall()
                created = 0
                for row in rows:
                    result = ensure_meeting_watch(
                        self._db, str(row["project_id"]), why="backfill",
                    )
                    if result is not None:
                        created += 1
                if created > 0:
                    meeting_watch_backfill = {
                        "kind": "meeting_watch.backfill",
                        "created": created,
                    }
            except Exception as exc:
                log.error("heartbeat meeting watch backfill failed: %s", exc)
                meeting_watch_backfill = {
                    "kind": "meeting_watch.backfill",
                    "created": 0,
                    "error": str(exc),
                }

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
        # HS-175-02: calendar refresh receipt rides along.
        if calendar_refresh_receipt is not None:
            receipt["calendar"] = calendar_refresh_receipt
        # HS-175-04: meeting watch backfill receipt rides along.
        if meeting_watch_backfill is not None:
            receipt["meeting_watch_backfill"] = meeting_watch_backfill

        # Write kernel receipt (Article XI.2)
        self._write_receipt(receipt)

        # Write pipeline_events
        self._write_pipeline_event(receipt, duration_ms)

        # D3 notifier: run the notification decision after every sweep.
        # Own failure boundary -- a notifier crash never breaks the loop.
        try:
            notify_receipt = self._run_notification_decision(principal, settings)
            receipt["notify"] = notify_receipt
        except Exception as exc:
            log.error("heartbeat notification decision failed: %s", exc)
            receipt["notify"] = {
                "kind": "heartbeat.notify",
                "outcome": "error",
                "error": str(exc),
            }

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
        """Write a pipeline_events row for the sweep.

        HS-174-04: propagates origin/caller/caller_identity from the
        context vars so a remote-triggered sweep carries origin=remote.
        """
        from holdspeak.services.observer import PipelineEvent, _origin, _caller, _caller_identity

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
            # HS-174-04: inherit origin from the calling context.
            origin=_origin.get("local"),
            caller=_caller.get(""),
            caller_identity=_caller_identity.get(""),
        )
        try:
            self._observer.on_event(event)
        except Exception:
            pass

    # ── D3 notification decision (wired from run_sweep) ────────────────

    def _run_notification_decision(
        self, principal: Principal, settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate the notification edge after a sweep and fire if appropriate.

        Persists ``last_notified_count`` in the heartbeat policy config so a
        restart does not re-notify the same count.  Returns a receipt dict
        with outcome vocabulary: ``sent``, ``held_quiet_hours``,
        ``held_no_edge``, ``off``, ``error``.
        """
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        notify_mode = settings.get("notify", _DEFAULT_NOTIFY)

        # Fast path: notifications disabled.
        if notify_mode == "off":
            receipt = {"kind": "heartbeat.notify", "outcome": "off"}
            self._write_notify_receipt(receipt)
            return receipt

        # Build the aggregate count (muted-aware).
        count = self.notification_count(principal)

        # Recover persisted edge state.
        persisted_edge = int(settings.get("last_notified_count", 0))
        edge = EdgeDetector(initial_count=persisted_edge)

        quiet_start = settings["quiet_hours"]["start"]
        quiet_end = settings["quiet_hours"]["end"]

        # Build aggregate for project_count.
        agg = self._build_aggregate_via_canonical(principal)
        project_count = len(agg.get("projects", []))
        content_items = agg.get("items", [])

        # The notification decision.
        result = heartbeat_notify(
            count,
            project_count,
            edge=edge,
            quiet_hours_start=quiet_start,
            quiet_hours_end=quiet_end,
            content_items=content_items,
            notify_content=False,
            receipt_writer=None,
            _notifier=self._notifier,
        )

        # For mode "edge", rely on the edge detector (heartbeat_notify
        # already checked it).  For "every_sweep", skip the edge and fire
        # on any non-zero count not held by quiet hours.
        if notify_mode == "every_sweep" and not result["fired"] and result["reason"] == "no_edge":
            # Override edge: fire if count > 0 and not quiet.
            if count > 0:
                from holdspeak.desktop_notify import notify as _do_notify

                if project_count > 1:
                    body = f"{count} need you across {project_count} projects"
                else:
                    body = f"{count} need you"
                _notifier = self._notifier or _do_notify
                fired = _notifier("HoldSpeak", body, click_url=None)
                if fired:
                    edge.mark_fired(count)
                result["fired"] = fired
                result["reason"] = "fired" if fired else "dispatch_failed"

        # Map to receipt vocabulary.
        if result["fired"]:
            outcome = "sent"
        elif result.get("held") and result["reason"] == "quiet_hours":
            outcome = "held_quiet_hours"
        elif result["reason"] == "no_edge":
            outcome = "held_no_edge"
        elif result["reason"] == "dispatch_failed":
            outcome = "error"
        else:
            outcome = "held_no_edge"

        receipt = {
            "kind": "heartbeat.notify",
            "outcome": outcome,
            "count": count,
            "projectCount": project_count,
            "fired": result["fired"],
            "lastNotifiedCount": persisted_edge,
        }

        # Persist edge state for restart survival.
        if result["fired"]:
            self._persist_edge(count)
        self._write_notify_receipt(receipt)
        return receipt

    def _persist_edge(self, count: int) -> None:
        """Persist the last-notified count in the heartbeat policy config."""
        settings = self.get_settings()
        settings["last_notified_count"] = count
        self._persist(settings)

    def _write_notify_receipt(self, receipt: dict[str, Any]) -> None:
        """Write a kernel receipt for the notification decision."""
        receipt_id = f"hbn_rcpt_{uuid.uuid4().hex[:12]}"
        operation_id = f"hbn_op_{uuid.uuid4().hex[:12]}"
        idem_key = f"heartbeat.notify:{_now_iso()}:{uuid.uuid4().hex[:8]}"
        now = _now_epoch()
        state = "succeeded" if receipt.get("outcome") != "error" else "failed"
        outcome_json = json.dumps(receipt, default=str, separators=(",", ":"))

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
                        "heartbeat.notify",
                        1,
                        "owner",
                        "heartbeat-service",
                        "heartbeat:notify",
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
                    (receipt_id, operation_id, state, outcome_json, "", now),
                )
        except Exception as exc:
            log.error("heartbeat notify receipt write failed: %s", exc)

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
