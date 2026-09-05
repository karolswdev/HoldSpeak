"""CadenceMixin (CAD-1-04) — the in-runtime cadence tick.

Mirrors PluginQueueMixin: a daemon thread on `runtime_stop_event`, started by
WebRuntime.run() ONLY when `config.cadence.enabled` is True. When disabled the
thread never starts and the runtime is byte-identical to a build without cadence.
The loop performs no external side effect — it projects + scores loops and computes
which are due (delivery is Phase 2+).
"""
from __future__ import annotations

from typing import Optional

from ..logging_config import get_logger

log = get_logger("runtime.cadence")


class CadenceMixin:
    def _cadence_enabled(self) -> bool:
        configured = bool(getattr(getattr(self.config, "cadence", None), "enabled", False))
        if not configured:
            return False
        from ..operation_policy import describe_operation, resolve_policy

        operation = describe_operation(
            operation_id="cadence:background-loop",
            family="sync_cadence",
            effect_class="cadence/tick",
            actor="runtime",
            destination="local_cadence_store",
            data_classes=("loop_metadata",),
            consequence="queue_executor",
        )
        return resolve_policy(
            operation,
            mode=getattr(self.config, "control_mode", "neutral"),
            source="config",
        ).outcome == "allowed"

    def _cadence_service(self):
        """Lazily build a CadenceService bound to the shared DB + config."""
        if getattr(self, "_cadence_service_obj", None) is None:
            from ..cadence.service import CadenceService
            from ..db import get_database

            self._cadence_service_obj = CadenceService(get_database(), self.config.cadence)
        return self._cadence_service_obj

    def _cadence_tick_once(self) -> None:
        try:
            result = self._cadence_service().tick()
            if result.due:
                log.info(
                    "cadence tick: %d projected, %d open, %d due",
                    result.projected, result.open_loops, result.due_count,
                )
                self._push_due_to_telegram(result.due)
            self._maybe_push_daily_brief()
            self._maybe_regenerate_brief()
            self._invalidate_needs_you_cache()
        except Exception as exc:  # never let the tick crash the runtime
            log.error("cadence tick failed: %s", exc)

    def _maybe_push_daily_brief(self) -> None:
        """First-activity morning push (CAD-5): once per day, after quiet hours, send the
        brief to paired Telegram chats. Off unless the Telegram surface is active."""
        tg = getattr(self.config, "cadence_telegram", None)
        if tg is None or not tg.is_active or not tg.allowed_chat_ids:
            return
        try:
            from datetime import datetime

            from ..cadence.brief import should_send_daily_brief
            from ..cadence.models import CadencePolicy
            from ..cadence_telegram import TelegramSurface
            from ..db import get_database

            db = get_database()
            policy = db.cadence.get_policy("daily_brief")
            last_sent = (policy.config.get("last_sent_date") if policy else None)
            earliest = int(getattr(self.config.cadence, "quiet_hours_end", 8))
            now = datetime.now()
            if not should_send_daily_brief(now, last_sent_date=last_sent, earliest_hour=earliest):
                return
            surface = TelegramSurface(db, tg)
            for chat_id in tg.allowed_chat_ids:
                surface.send_brief(chat_id)
            db.cadence.upsert_policy(CadencePolicy(
                name="daily_brief", config={"last_sent_date": now.strftime("%Y-%m-%d")}))
            log.info("cadence: pushed the daily brief to %d chat(s)", len(tg.allowed_chat_ids))
        except Exception as exc:
            log.error("cadence daily brief failed: %s", exc)

    def _maybe_regenerate_brief(self) -> None:
        """HS-171-06: regenerate the Monday brief on its own cadence.

        Once per day, after quiet hours close, call MondayBriefService.generate()
        so the brief is fresh before any push or shade read.  The regeneration is
        receipted via pipeline_events.
        """
        try:
            from datetime import datetime

            from ..cadence.brief import should_send_daily_brief
            from ..cadence.models import CadencePolicy
            from ..db import get_database
            from ..principals import Principal, PrincipalKind

            db = get_database()
            policy = db.cadence.get_policy("brief_regeneration")
            last_regen = (policy.config.get("last_regen_date") if policy else None)
            earliest = int(getattr(self.config.cadence, "quiet_hours_end", 8))
            now = datetime.now()
            if not should_send_daily_brief(now, last_sent_date=last_regen, earliest_hour=earliest):
                return

            from ..services.monday_brief_service import MondayBriefService

            brief_svc = MondayBriefService(db)
            system_principal = Principal(PrincipalKind.SERVICE, "heartbeat")
            brief = brief_svc.generate(system_principal, now=now)

            db.cadence.upsert_policy(CadencePolicy(
                name="brief_regeneration",
                config={"last_regen_date": now.strftime("%Y-%m-%d")},
            ))

            # Receipt via pipeline_events.
            from ..services.observer import PipelineEvent
            from ..services.sqlite_observer import SQLiteObserver
            import time as _time
            import uuid as _uuid

            observer = SQLiteObserver(db._connection)
            item_count = getattr(brief, "item_count", 0) or len(getattr(brief, "items", []))
            observer.on_event(PipelineEvent(
                event_id=str(_uuid.uuid4()),
                timestamp=_time.time(),
                service="heartbeat",
                method="brief.regenerated",
                principal_kind="service",
                principal_identity="heartbeat",
                args_summary="{}",
                result_summary=f"items={item_count}",
                error=None,
                error_code=None,
                duration_ms=0,
                correlation_id="",
                is_async=False,
            ))
            log.info("heartbeat: regenerated the Monday brief (%d items)", item_count)
        except Exception as exc:
            log.error("heartbeat brief regeneration failed: %s", exc)

    def _invalidate_needs_you_cache(self) -> None:
        """HS-171-03: invalidate the needs-you aggregate cache after a tick."""
        try:
            cache = getattr(self, "_needs_you_cache", None)
            if cache is None:
                # Try the web context's cache (set by the route builder).
                ctx = getattr(self, "_web_context", None)
                if ctx is not None:
                    cache = getattr(ctx, "_needs_you_cache", None)
            if cache is not None:
                import uuid as _uuid
                cache.invalidate(sweep_id=str(_uuid.uuid4()))
                log.debug("heartbeat: invalidated needs-you cache")
        except Exception as exc:
            log.error("heartbeat: failed to invalidate needs-you cache: %s", exc)

    def _push_due_to_telegram(self, due_loops) -> None:
        """Deliver due nudges to paired Telegram chats (CAD-4-05) — off unless the
        Telegram surface is enabled + has a token + a paired chat."""
        tg = getattr(self.config, "cadence_telegram", None)
        if tg is None or not tg.is_active or not tg.allowed_chat_ids:
            return
        try:
            from ..cadence_telegram import TelegramSurface
            from ..db import get_database

            sent = TelegramSurface(get_database(), tg).push_due_nudges(due_loops)
            if sent:
                log.info("cadence: pushed %d nudge(s) to Telegram", sent)
        except Exception as exc:
            log.error("cadence telegram push failed: %s", exc)

    def _cadence_loop(self) -> None:
        interval = max(30, int(getattr(self.config.cadence, "tick_interval_seconds", 300)))
        # An initial settle so startup isn't contended; then tick on the interval.
        while not self.runtime_stop_event.wait(interval):
            self._cadence_tick_once()
