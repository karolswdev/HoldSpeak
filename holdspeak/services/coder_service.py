"""Transport-neutral coder-session operations (HS-122-05)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

from datetime import datetime, timezone
from typing import Any, Callable

from ..db.core import Database
from ..logging_config import get_logger
from ..principals import Principal
from holdspeak.services.errors import NotFound, ServiceError, ValidationError

log = get_logger("services.coder")

#: The companion board (``GET /api/coders/status``): the reply target's age
#: limit and the overview's.
COMPANION_TARGET_MAX_AGE_SECONDS = 120
COMPANION_OVERVIEW_MAX_AGE_SECONDS = 30 * 60


class CoderRefused(ServiceError):
    """A refusal the coder surface answers by name: ``body`` is the answer,
    ``http`` its status (the bodies the hand-written routes answered with:
    ``{"status": "stale_session", "detail": ...}`` at 409, ...)."""

    def __init__(self, body: dict[str, Any], http: int, *, code: str | None = None) -> None:
        name = code or str(body.get("status") or body.get("error") or "refused")
        super().__init__(name, str(body.get("detail") or body.get("error") or name),
                         context={"http": http, "body": dict(body)})


def _flag(value: Any, default: bool) -> bool:
    """A query flag (``?include_ended=false``) or a JSON boolean."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"} if isinstance(value, str) else bool(value)


def _integer(value: Any, name: str, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} must be an integer") from exc


@observe_service
class CoderService:
    def __init__(
        self,
        db: Database | None = None,
        *,
        reply_sender: Callable[[str, str], Any] | None = None,
        observer: PipelineObserver | None = None,
        on_changed: Callable[[str, str, str], None] | None = None,
        broadcast: Callable[[str, Any], None] | None = None,
        launch_reads: Any = None,
    ) -> None:
        # HS-200-45 R4: the note a coder reply materializes is written below
        # PrimitiveService, so this service announces it itself.
        from holdspeak.runtime.composition import notify_desk_changed
        self._on_changed = on_changed or notify_desk_changed
        if db is None:
            from ..db import get_database

            db = get_database()
        self._db = db
        self._reply_sender = reply_sender
        self._observer = observer or NullObserver()
        # The bus the coder frames go on (``intel_status``, scope coder); None:
        # the installed hub's bus, read at each frame.
        self._broadcast = broadcast
        # The launch driver's reads (``LaunchReads``); None: the defaults.
        self._launch_reads = launch_reads

    def explain(self, principal: Principal, target: str) -> dict[str, Any]:
        from .agent_flights import explain_agent

        answer = explain_agent(self._db, target)
        if answer is None:
            raise NotFound("agent", target)
        return answer

    def relay(self, principal: Principal, verb: str, args: dict[str, Any]) -> dict[str, Any]:
        """Relay through the configured node's existing token and authority checks."""
        from .. import coder_steering_relay
        from ..principals import PrincipalKind
        from ..operations import OperationOwnerRequired
        from urllib.parse import urlencode

        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise OperationOwnerRequired(f"coder.relay.{verb}")
        key = str(args.get("key") or "").strip()
        if not key:
            raise CoderRefused({"error": "key is required"}, 400)
        body = {k: v for k, v in args.items() if k not in ("key", "node")}
        if verb == "peek":
            query = {"lines": _integer(args.get("lines"), "lines", 200)}
            if args.get("last_hash"):
                query["last_hash"] = args["last_hash"]
            if _integer(args.get("raw"), "raw", 0):
                query["raw"] = 1
            path, body = "peek?" + urlencode(query), None
        else:
            path = verb
            if verb == "arm":
                body = {"ttl_seconds": body["ttl_seconds"]} if "ttl_seconds" in body else {}
            elif verb == "disarm":
                body = {}
        result = coder_steering_relay.relay(args.get("node"), path, key,
            method="GET" if verb == "peek" else "POST", body=body)
        status = coder_steering_relay.relay_http_code(result)
        if status != 200:
            raise CoderRefused(result, status)
        return result

    def list_sessions(
        self,
        principal: Principal,
        *,
        agent: str | None = None,
        include_ended: bool = True,
    ) -> list[dict[str, Any]]:
        from ..agent_context import DEFAULT_LIFECYCLE_DEAD_SECONDS, LIFECYCLE_ENDED, effective_state, list_agent_sessions
        from ..agent_device import build_agent_identity_payload

        now = datetime.now(timezone.utc)
        items: list[dict[str, Any]] = []
        for session in list_agent_sessions(agent=agent):
            age = self._age_seconds(session.updated_at, now)
            if age is not None and age > DEFAULT_LIFECYCLE_DEAD_SECONDS:
                continue
            state = effective_state(session, now=now)
            if state == LIFECYCLE_ENDED and not include_ended:
                continue
            payload = session.to_dict()
            payload["state"] = state
            items.append({"session": payload, "age_seconds": age, "identity": build_agent_identity_payload(session)})
        return items

    def get_session(self, principal: Principal, session_id: str) -> dict[str, Any]:
        agent, raw_session_id = self._split_session_id(session_id)
        from ..agent_context import list_agent_sessions

        session = next(
            (
                item for item in list_agent_sessions(agent=agent)
                if item.session_id == raw_session_id
            ),
            None,
        )
        if session is None:
            raise NotFound("coder session", session_id)
        return session.to_dict()

    # ── the coder board (``/api/coders``) ─────────────────────────────────

    def board(self, principal: Principal, *, agent: Any = None, include_ended: Any = None) -> dict[str, Any]:
        """The live coder set (HSM-17-02) with the flights, the launch history
        and the launch count (``GET /api/coders/sessions``; MCP ``coder.list``).

        Every session the hooks reported, newest first, each with its raw
        ``lifecycle``, its pending ``question`` and its effective ``state``.
        ``flights``: each item an agent was handed (Conductor F2); a session
        that works on one carries it as ``flight``. Each row's ``screen`` is
        its pane as the watcher last read it (AG7). Reading the board drains
        the hook's event spool into the event log (PHILO-14 C0).
        """
        items = self.list_sessions(
            principal, agent=agent or None, include_ended=_flag(include_ended, True)
        )
        flights: list[dict[str, Any]] = []
        try:
            from .agent_flights import agent_flights, annotate_sessions

            # The whole registry: lifecycle and freshness resolve before the
            # presentation filter above (include_ended, the dead window).
            flights = agent_flights(self._db)
            annotate_sessions(items, flights)
        except Exception as exc:
            log.warning(f"agent flights unread: {exc}")
        try:
            from ..agent_context.screen_watch import STORE, screen_wire

            now = datetime.now(timezone.utc)
            for row in items:
                session = row.get("session") or {}
                row["screen"] = screen_wire(STORE.get(f"{session.get('agent')}:{session.get('session_id')}"), now)
        except Exception as exc:
            log.warning(f"agent screens unread: {exc}")
        extra: dict[str, Any] = {}
        try:
            from .agent_flights import launch_history

            extra["history"] = launch_history(self._db)
        except Exception as exc:
            log.warning(f"agent launch history unread: {exc}")
        try:
            from .agent_hand_queue import queued_flights

            # Betterment AG5: a hand that waits for a free agent is a flight
            # in the ``queued`` state.
            flights = [*flights, *queued_flights(self._db)]
        except Exception as exc:
            log.warning(f"queued hands unread: {exc}")
        try:
            from .agent_hand_preview import LaunchReads
            from .agent_hand_service import working_at_once, working_launches

            reads = self._launch_reads or LaunchReads()
            # Betterment AG5: the agents that work or need him, against the
            # setting ``agents.working_at_once``.
            extra["launches"] = {"live": len(working_launches(reads.launcher(), self._db)), "cap": working_at_once()}
        except Exception as exc:
            log.warning(f"agent launch count unread: {exc}")
        try:
            from ..agent_context import event_log

            event_log.drain_spool(self._db._connection)
        except Exception as exc:
            log.warning(f"agent event spool not drained: {exc}")
        return {"sessions": items, "count": len(items), "flights": flights, **extra}

    def companion_status(
        self, principal: Principal, *, runtime: dict[str, Any], runtime_error: str | None,
        devices: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """One snapshot of the AI PI companion loop (``GET /api/coders/status``).

        The transport holds ``runtime`` (the hub's normalized runtime status),
        ``runtime_error`` and ``devices`` (the active device descriptors)."""
        from ..agent_context import (
            DEFAULT_STALE_AGENT_SESSION_SECONDS,
            get_recent_awaiting_agent_session,
            list_recent_awaiting_agent_sessions,
        )
        from ..agent_device import AGENT_QUERY_NAMES, build_agent_identity_payload
        from ..config import Config

        device_connected = bool(devices)
        agent_error: str | None = None
        try:
            session = get_recent_awaiting_agent_session(max_age_seconds=COMPANION_TARGET_MAX_AGE_SECONDS)
            agent_sessions = list_recent_awaiting_agent_sessions(
                max_age_seconds=COMPANION_OVERVIEW_MAX_AGE_SECONDS, limit=8,
            )
        except Exception as exc:
            log.error(f"agent companion status failed: {exc}")
            agent_error = str(exc)
            session = None
            agent_sessions = []
        agent_waiting = bool(session and session.awaiting_response)
        tmux_reply_available = bool(
            session and session.awaiting_response and getattr(session, "tmux_pane", None)
        )

        dictation_error: str | None = None
        try:
            dictation_cfg = Config.load().dictation
            pipeline_enabled = bool(dictation_cfg.pipeline.enabled)
            pipeline_stages = list(dictation_cfg.pipeline.stages)
            target_profile_override = dictation_cfg.pipeline.target_profile_override
            runtime_backend = dictation_cfg.runtime.backend
        except Exception as exc:
            log.error(f"dictation config load failed: {exc}")
            dictation_error = str(exc)
            pipeline_enabled = False
            pipeline_stages = []
            target_profile_override = None
            runtime_backend = None

        text_injection_known = "text_injection_enabled" in runtime
        text_injection_enabled = bool(runtime.get("text_injection_enabled")) if text_injection_known else None
        agent_identity = build_agent_identity_payload(session, text_injection_enabled=text_injection_enabled)
        if session is not None and not any(
            item.agent == session.agent and item.session_id == session.session_id for item in agent_sessions
        ):
            agent_sessions.insert(0, session)
        selected_agent_key = (session.agent, session.session_id) if session is not None else None
        agent_session_items = []
        selected_index: int | None = None
        now = datetime.now(timezone.utc)
        for index, item in enumerate(agent_sessions):
            selected = (item.agent, item.session_id) == selected_agent_key
            if selected:
                selected_index = index
            age_seconds = self._age_seconds(item.updated_at, now)
            # Pinned sessions are intentionally kept; never badge them stale.
            stale = (
                not item.pinned and age_seconds is not None and age_seconds > DEFAULT_STALE_AGENT_SESSION_SECONDS
            )
            agent_session_items.append({
                "index": index, "selected": selected, "pinned": item.pinned, "stale": stale,
                "age_seconds": age_seconds, "session": item.to_dict(),
                "identity": build_agent_identity_payload(item, text_injection_enabled=text_injection_enabled),
            })

        blockers: list[str] = []
        if not device_connected:
            blockers.append("no_device_connected")
        if not agent_waiting:
            blockers.append("no_agent_waiting")
        if not pipeline_enabled:
            blockers.append("dictation_pipeline_disabled")
        if text_injection_enabled is False and not tmux_reply_available:
            blockers.append("text_injection_unavailable")
        elif text_injection_enabled is None and not tmux_reply_available:
            blockers.append("text_injection_status_unknown")
        if agent_error:
            blockers.append("agent_status_unavailable")
        if dictation_error:
            blockers.append("dictation_config_unavailable")
        if runtime_error:
            blockers.append("runtime_status_unavailable")

        return {
            "status": "ok",
            "ready_for_agent_reply": not blockers,
            "blockers": blockers,
            "checks": {
                "device_connected": device_connected,
                "agent_waiting": agent_waiting,
                "dictation_pipeline_enabled": pipeline_enabled,
                "text_injection_enabled": text_injection_enabled,
                "tmux_reply_available": tmux_reply_available,
                "target_confidence": agent_identity["target_confidence"] if agent_identity else None,
            },
            "devices": {
                "connected": device_connected,
                "count": len(devices),
                "items": devices,
                "query_names": sorted(AGENT_QUERY_NAMES),
            },
            "agent": {
                "awaiting_response": agent_waiting,
                "session": session.to_dict() if session else None,
                "identity": agent_identity,
                "sessions": {
                    "count": len(agent_session_items),
                    "selected_index": selected_index,
                    "items": agent_session_items,
                },
                "max_age_seconds": COMPANION_TARGET_MAX_AGE_SECONDS,
                "overview_max_age_seconds": COMPANION_OVERVIEW_MAX_AGE_SECONDS,
                "stale_threshold_seconds": DEFAULT_STALE_AGENT_SESSION_SECONDS,
                "error": agent_error,
            },
            "dictation": {
                "pipeline_enabled": pipeline_enabled,
                "stages": pipeline_stages,
                "target_profile_override": target_profile_override,
                "runtime_backend": runtime_backend,
                "error": dictation_error,
            },
            "runtime": {
                "status": runtime.get("status"),
                "mode": runtime.get("mode"),
                "meeting_active": runtime.get("meeting_active"),
                "meeting_id": runtime.get("meeting_id"),
                "voice_state": runtime.get("voice_state"),
                "text_injection_enabled": text_injection_enabled,
                "text_injection_error": runtime.get("text_injection_error"),
                "tmux_reply_available": tmux_reply_available,
                "target_transport": agent_identity["target_transport"] if agent_identity else None,
                "error": runtime_error,
            },
            "companion": {
                "query_names": sorted(AGENT_QUERY_NAMES),
                "voice_reply_max_age_seconds": COMPANION_TARGET_MAX_AGE_SECONDS,
                "stale_threshold_seconds": DEFAULT_STALE_AGENT_SESSION_SECONDS,
            },
        }

    @staticmethod
    def _target(agent: Any, session_id: Any) -> tuple[str, str]:
        """The required ``(agent, session_id)`` pair of a board press."""
        if not isinstance(agent, str) or not agent.strip():
            raise CoderRefused({"error": "agent is required"}, 400, code="agent_required")
        if not isinstance(session_id, str) or not session_id.strip():
            raise CoderRefused({"error": "session_id is required"}, 400, code="session_id_required")
        return agent, session_id

    def select(self, principal: Principal, agent: Any, session_id: Any) -> dict[str, Any]:
        """Make one waiting session the AI PI's active reply target."""
        from ..agent_context import select_awaiting_agent_session

        session = select_awaiting_agent_session(*self._target(agent, session_id))
        if session is None:
            raise CoderRefused({"success": False, "error": "unknown_session", "session": None}, 404)
        return {"success": True, "session": session.to_dict()}

    def dismiss(self, principal: Principal, agent: Any, session_id: Any) -> dict[str, Any]:
        """Clear a waiting session's captured question (the session stays)."""
        from ..agent_context import clear_agent_session_response

        agent, session_id = self._target(agent, session_id)
        session = clear_agent_session_response(agent=agent, session_id=session_id)
        return {"success": session is not None, "session": session.to_dict() if session else None}

    def pin(self, principal: Principal, agent: Any, session_id: Any, pinned: Any = True) -> dict[str, Any]:
        """Pin or unpin a waiting session as the sticky reply target."""
        from ..agent_context import pin_agent_session

        agent, session_id = self._target(agent, session_id)
        session = pin_agent_session(agent, session_id, bool(True if pinned is None else pinned))
        if session is None:
            raise CoderRefused({"success": False, "error": "unknown_session", "session": None}, 404)
        return {"success": True, "session": session.to_dict()}

    def own_agents(self, principal: Principal) -> dict[str, Any]:
        """The Claude Code and Codex processes the owner started by hand.

        Read only; a registered HoldSpeak launch is not in the list."""
        from ..agent_context.own_agents import list_own_agents

        agents = list_own_agents()
        return {"agents": agents, "count": len(agents)}

    def answer_own_agent(
        self, principal: Principal, pane_id: Any, since: Any, keys: Any = None, text: Any = None
    ) -> dict[str, Any]:
        """Answer one owner-started pane after a fresh read of its prompt."""
        from ..agent_context.own_agents import ScreenAnswerRefused, answer_own_agent
        from ..delivery.direct_gesture_input import ProcessInputRefused

        pane, mark = str(pane_id or ""), str(since or "")
        if not pane or not mark:
            raise CoderRefused({"error": "pane_id_and_since_required", "code": "pane_id_and_since_required"}, 400)
        try:
            result = answer_own_agent(
                pane, since=mark,
                keys=[str(item) for item in keys] if isinstance(keys, list) else None,
                text=str(text or "") if keys is None else None,
            )
        except ScreenAnswerRefused as exc:
            raise CoderRefused({"error": exc.code, "code": exc.code, "status": exc.code, "detail": exc.detail}, 409,
                               code=exc.code) from exc
        except ProcessInputRefused as exc:
            raise CoderRefused({"error": exc.reason, "code": exc.reason, "status": "transport_error"}, 409,
                               code=exc.reason) from exc
        self._frame(f"own:{pane}")
        return result

    # ── the factory ───────────────────────────────────────────────────────

    def spawn(self, principal: Principal, name: Any, command: Any = None, cwd: Any = None) -> dict[str, Any]:
        """Start a detached tmux session (audited)."""
        from .. import coder_factory

        result = coder_factory.spawn(
            str(name or "").strip(), command=str(command) if command else None, cwd=str(cwd) if cwd else None,
        )
        if result["status"] != "spawned":
            raise CoderRefused(result, 400 if result["status"] == "cwd_invalid" else 409)
        return result

    def rename(self, principal: Principal, target: Any, name: Any) -> dict[str, Any]:
        """Rename a tmux session (audited)."""
        from .. import coder_factory

        clean_target = str(target or "").strip()
        if not clean_target:
            raise CoderRefused({"error": "target is required"}, 400, code="target_required")
        result = coder_factory.rename(clean_target, str(name or "").strip())
        if result["status"] != "renamed":
            raise CoderRefused(result, 409)
        return result

    # ── steering (HS-87) ──────────────────────────────────────────────────

    def _frame(self, key: str) -> None:
        """One ``scope: "coder"`` frame on the one bus: arming moved, a grant
        expired, an awaiting flag flipped (the HS-86-03 frame shape)."""
        send = self._broadcast
        if send is None:
            from holdspeak.runtime.composition import installed

            root = installed()
            send = root.broadcast if root is not None else None
        if send is None:
            return
        try:
            send("intel_status", {
                "state": "ready", "scope": "coder",
                "capability": {"kind": "coder", "id": key, "name": key.split(":", 1)[0]},
            })
        except Exception as exc:
            log.debug(f"coder frame dropped: {exc}")

    def _sweep(self) -> None:
        """Lazy expiry on read: an expired grant frames when a read sees it."""
        from .. import coder_steering

        for expired_key in coder_steering.sweep_expired():
            self._frame(expired_key)

    @staticmethod
    def _steering_session(key: Any) -> Any:
        """A steering key's session. ``pane:%N`` names a raw tmux pane
        (HS-89-02; any pane, a hand-started one too); every other key is an
        ``agent:session_id`` in the registry."""
        from types import SimpleNamespace

        from .coder_steering_support import canonical_pane_id

        key = str(key or "")
        if key.startswith("pane:"):
            pane_id = canonical_pane_id(key[len("pane:"):])
            if pane_id is None:
                raise CoderRefused({"error": "key must be pane:%N"}, 400, code="invalid_key")
            # A raw pane is never stale the way a registry record can be.
            return SimpleNamespace(
                agent="pane", session_id=pane_id, awaiting_response=False, question=None,
                updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                tmux_pane=pane_id, last_assistant_text=None,
            )
        from ..agent_context import list_agent_sessions

        agent, _, session_id = key.partition(":")
        if not agent.strip() or not session_id.strip():
            raise CoderRefused({"error": "key must be agent:session_id"}, 400, code="invalid_key")
        session = next((s for s in list_agent_sessions(agent=agent) if s.session_id == session_id), None)
        if session is None:
            raise CoderRefused({"status": "unknown_session", "key": key}, 404)
        return session

    def _stale(self, session: Any) -> tuple[bool, int | None]:
        from ..agent_context import DEFAULT_RECENT_MAX_AGE_SECONDS

        age = self._age_seconds(session.updated_at, datetime.now(timezone.utc))
        return bool(age is not None and age > DEFAULT_RECENT_MAX_AGE_SECONDS), age

    @staticmethod
    def _registered_pane(target: str | None) -> str | None:
        """The ``%N`` the registry's target names now (None when it cannot prove itself)."""
        from .. import coder_steering
        from .coder_steering_support import canonical_pane_id

        if not target:
            return None
        direct = canonical_pane_id(target)
        if direct:
            return direct
        identity = coder_steering.resolve_pane_identity(target)
        return canonical_pane_id(identity.get("pane_id")) if identity.get("status") == "ok" else None

    def peek(self, principal: Principal, key: Any, lines: Any = None, last_hash: Any = None,
             raw: Any = None) -> dict[str, Any]:
        """A read-only window into a session's tmux pane (HS-87-01).

        Free: no grant, no keystroke. Absences are typed peek statuses
        (``no_pane``, ``pane_gone``, ``tmux_absent``); a registry record past
        the recent window is ``stale``. The answer carries the grant
        (HS-87-02) and the policy; ``raw=1`` keeps the ANSI (HS-111-11)."""
        from .. import coder_steering
        from ..agent_context.models import is_blocked
        from ..config import Config
        from ..operation_policy import steering_ttl_for_mode
        from .coder_steering_support import (
            active_policy_grant, canonical_pane_id, steering_commitment, steering_policy,
        )

        count, raw_flag = _integer(lines, "lines", 200), _integer(raw, "raw", 0)
        session = self._steering_session(key)
        key = str(key)
        stale, _age = self._stale(session)
        self._sweep()
        grant = active_policy_grant(key)
        envelope: dict[str, Any] = {
            "key": key, "agent": session.agent, "stale": stale,
            "awaiting_response": session.awaiting_response, "question": session.question,
            # Conductor F2 (K5b): the one blocked predicate.
            "blocked": is_blocked(session), "updated_at": session.updated_at,
            "grant": {"armed": grant is not None, "expires_in_seconds": grant["expires_in_seconds"] if grant else None},
        }
        target = coder_steering.resolve_pane_target(session)
        if target is None:
            operation, policy = steering_policy(
                key, None, operation_kind="type_text_and_keys", data_classes=("typed_text", "key_events"),
                registered=False, grant=grant,
            )
            envelope.update(operation=operation, policy=policy, commitment=steering_commitment(operation, policy))
            envelope["peek"] = {"status": "no_pane"}
            return envelope
        pane_id = canonical_pane_id(target)
        if pane_id is None:
            identity = coder_steering.resolve_pane_identity(target)
            pane_id = canonical_pane_id(identity.get("pane_id")) if identity.get("status") == "ok" else None
        operation, policy = steering_policy(
            key, pane_id, operation_kind="type_text_and_keys", data_classes=("typed_text", "key_events"),
            registered=not stale, grant=grant,
        )
        envelope.update(pane_id=pane_id, operation=operation, policy=policy,
                        commitment=steering_commitment(operation, policy))
        preset_ttl = steering_ttl_for_mode(Config.load().control_mode)
        envelope["arm_commitment"] = f"Arm pane {pane_id or target} for {preset_ttl // 60} minutes"
        envelope["peek"] = coder_steering.peek_pane(
            target, lines=count, last_hash=last_hash or None, **({"raw": True} if raw_flag else {}))
        return envelope

    def arm(self, principal: Principal, key: Any, ttl_seconds: Any = None) -> dict[str, Any]:
        """Arm a session for steering (HS-87-02): the owner's explicit act.

        Pins the pane's ``%N`` at grant time. A stale registry record and a
        pane that cannot prove itself are refused with a typed 409."""
        from .. import coder_steering
        from ..config import Config
        from ..operation_policy import POLICY_VERSION, steering_ttl_for_mode

        session = self._steering_session(key)
        key = str(key)
        stale, age = self._stale(session)
        if stale:
            raise CoderRefused({
                "status": "stale_session",
                "detail": f"registry record is {age}s old — a stale session cannot be armed",
            }, 409)
        target = coder_steering.resolve_pane_target(session)
        if target is None:
            raise CoderRefused({"status": "no_pane", "detail": "this session never saw tmux"}, 409)
        control_mode = Config.load().control_mode
        ttl = coder_steering.clamp_ttl(steering_ttl_for_mode(control_mode, ttl_seconds))
        result = coder_steering.arm(key, target, ttl_seconds=ttl, control_mode=control_mode)
        if result["status"] != "armed":
            raise CoderRefused(result, 409)
        result["control_mode"] = control_mode
        result["commitment"] = f"Arm pane {result['pane_id']} for {ttl // 60} minutes"
        result["policy_version"] = POLICY_VERSION
        self._frame(key)
        return result

    def disarm(self, principal: Principal, key: Any) -> dict[str, Any]:
        """Disarm a session: one press, at once, idempotent (HS-87-02)."""
        from .. import coder_steering

        key = str(key or "")
        was_armed = coder_steering.disarm(key)
        if was_armed:
            self._frame(key)
        return {"status": "disarmed", "key": key, "was_armed": was_armed}

    def grants(self, principal: Principal) -> dict[str, Any]:
        """Every live steering grant (HS-87-02). Expired grants sweep (and frame) here."""
        from .. import coder_steering

        self._sweep()
        return {"grants": coder_steering.active_grants()}

    def nodes(self, principal: Principal) -> dict[str, Any]:
        """The configured steering nodes, names only (HS-90-02): never a URL or a token."""
        from .. import coder_steering_relay

        return {"nodes": sorted(coder_steering_relay.load_nodes().keys())}

    def panes(self, principal: Principal) -> dict[str, Any]:
        """Every tmux pane on this Mac (HS-89-02): read only; no tmux server is an empty list."""
        from .. import coder_steering

        return coder_steering.list_panes()

    @staticmethod
    def _owner_answer(body: dict[str, Any]) -> bool:
        """Betterment AG2: the owner's press on the agent's current wait
        (``kind: "answer"`` with its ``wait_id``)."""
        return str(body.get("kind") or "") == "answer" and bool(str(body.get("wait_id") or ""))

    def steer(self, principal: Principal, key: Any, body: dict[str, Any], *, process_input: Any) -> dict[str, Any]:
        """Deliver one steer through THE chokepoint (HS-87-03/04).

        ``grounding`` refs are hydrated, fenced and capped (over the cap
        refuses at compose time); ``preview: true`` answers the exact text and
        sends nothing. Delivered or refused, the attempt is audited.
        ``process_input``: the transport's ``ProcessInputServices``."""
        from .. import coder_steering
        from .coder_steering_support import (
            active_policy_grant, compose_from_body, deliver_process_input, expected_pane_id,
            steering_commitment, steering_policy, wait_not_current,
        )

        session = self._steering_session(key)
        key = str(key)
        wait_not_current(session, body)  # PHILO-14 C2
        composed = compose_from_body(body, principal=principal, service=self)
        if composed["status"] == "over_cap":
            raise CoderRefused({
                "status": "grounding_over_cap",
                "detail": f"grounded context is {composed['context_bytes']} bytes, "
                          f"over the {composed['cap_bytes']} byte cap",
                "context_bytes": composed["context_bytes"], "cap_bytes": composed["cap_bytes"],
            }, 409)
        target = coder_steering.resolve_pane_target(session)
        stale, _age = self._stale(session)
        grant = active_policy_grant(key)
        answer = self._owner_answer(body)
        pane_id = expected_pane_id(key, body, grant) or (self._registered_pane(target) if answer else None)
        operation, policy = steering_policy(
            key, pane_id, operation_kind="type_text", data_classes=("typed_text",),
            registered=not stale, grant=grant, owner_answer=answer,
        )
        if bool(body.get("preview")):
            # Executed == previewed: the SAME composed text the send uses.
            return {
                "status": "preview", "text": composed["text"], "context_bytes": composed["context_bytes"],
                "cap_bytes": composed["cap_bytes"], "refs": composed["refs"], "operation": operation,
                "policy": policy, "commitment": steering_commitment(operation, policy),
            }
        result = deliver_process_input(
            process_input, key=key, target=target, agent=session.agent, pane_id=pane_id, verb="terminal.text",
            payload={
                "text": str(composed["text"]),
                "submit": bool(body.get("submit", True)),
                "grounding_refs": list(composed["refs"]),
                # Betterment AG2: an answer is checked against the wait it
                # names again just before the keystroke.
                **({"expected_wait_id": coder_steering.wait_episode(session)} if answer else {}),
            },
            policy=policy, principal=principal,
        )
        return self._delivered(key, result)

    def send_keys(self, principal: Principal, key: Any, body: dict[str, Any], *, process_input: Any) -> dict[str, Any]:
        """Send allow-listed keys through ``process.input@1``. An unknown key
        and missing authority are refused by name; every attempt is audited."""
        from .. import coder_steering
        from .coder_steering_support import (
            active_policy_grant, deliver_process_input, expected_pane_id, steering_policy, wait_not_current,
        )

        session = self._steering_session(key)
        key = str(key)
        # Betterment AG2: Allow / Deny answer a wait; a stale wait is refused
        # before anything is sent.
        wait_not_current(session, body)
        target = coder_steering.resolve_pane_target(session)
        stale, _age = self._stale(session)
        grant = active_policy_grant(key)
        answer = self._owner_answer(body)
        pane_id = expected_pane_id(key, body, grant) or (self._registered_pane(target) if answer else None)
        operation, policy = steering_policy(
            key, pane_id, operation_kind="send_keys", data_classes=("key_events",),
            registered=not stale, grant=grant, owner_answer=answer,
        )
        result = deliver_process_input(
            process_input, key=key, target=target, agent=session.agent, pane_id=pane_id, verb="terminal.keys",
            payload={
                "keys": body.get("keys") or [],
                **({"expected_wait_id": coder_steering.wait_episode(session)} if answer else {}),
            },
            policy=policy, principal=principal,
        )
        return self._delivered(key, result)

    def _delivered(self, key: str, result: dict[str, Any]) -> dict[str, Any]:
        """A delivery's answer: an audited or revoking attempt frames; a refusal is a 409."""
        if result.get("audit_id") is not None or result.get("revoked"):
            self._frame(key)
        if result["status"] != "delivered":
            raise CoderRefused(result, 409)
        return result

    def kill(self, principal: Principal, key: Any, scope: Any = None) -> dict[str, Any]:
        """End the armed pane (``scope="pane"``) or its tmux session
        (``scope="session"``), gated like a steer (HS-90-01). A recycled pane
        refuses AND revokes; the launch records the owner's stop."""
        from .. import coder_factory, coder_steering
        from .coder_steering_support import record_kill

        session = self._steering_session(key)
        key, clean_scope = str(key), str(scope or "pane")
        result = coder_factory.kill(
            key, current_target=coder_steering.resolve_pane_target(session), scope=clean_scope, agent=session.agent,
        )
        if result.get("revoked"):
            self._frame(key)
        if result["status"] != "killed":
            raise CoderRefused(result, 409)
        record_kill(key, session, result, clean_scope)  # PHILO-14 C2: the launch says so
        self._frame(key)
        return result

    def keep_session_note(self, principal: Principal, key: Any, title: Any = None, body: Any = None) -> dict[str, Any]:
        """Keep the session's current ask as a desk note (HS-87-05): the body
        is the ask (or ``body``) under a lineage line that names the session,
        the agent and the moment; ``title`` overrides the name."""
        session = self._steering_session(key)
        key = str(key)
        ask = str(body or getattr(session, "question", None) or getattr(session, "last_assistant_text", None) or "")
        if not ask.strip():
            raise CoderRefused({"error": "nothing to keep — the session has no current ask"}, 400,
                               code="nothing_to_keep")
        stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        name = str(title or "").strip() or f"From {session.agent} · {key}"
        lineage = f"> kept from session `{key}` ({session.agent}) at {stamp}"
        note = self.keep_note(principal, key, {
            "title": name, "body_markdown": f"{lineage}\n\n{ask}", "tags": ["session", session.agent],
        })
        return {"note": note}

    def reply(self, principal: Principal, session_id: str, text: str) -> dict[str, Any]:
        clean_text = str(text or "").strip()
        if not clean_text:
            raise ValidationError("text must be a non-empty string")
        session = self.get_session(principal, session_id)
        if self._reply_sender is None:
            raise ValidationError("coder reply delivery is unavailable")
        outcome = self._reply_sender(session_id, clean_text)
        return {"success": True, "session": session, "reply": outcome}

    def list_steering_audit(
        self, principal: Principal, session_key: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Return the bounded, content-safe steering audit trail."""
        try:
            clean_limit = int(limit)
        except (TypeError, ValueError) as exc:
            raise ValidationError("limit must be an integer") from exc
        clean_session_key = str(session_key).strip() if session_key is not None else None
        entries = self._db.steering.list(
            session_key=clean_session_key or None,
            limit=clean_limit,
        )
        return [entry.to_dict() for entry in entries]

    def keep_note(
        self, principal: Principal, session_key: str, content: dict[str, Any]
    ) -> dict[str, Any]:
        """Persist a session-derived note after the route resolves its session."""
        if not str(session_key or "").strip():
            raise ValidationError("session_key must be non-empty")
        if not isinstance(content, dict):
            raise ValidationError("note content must be an object")
        title = str(content.get("title") or "").strip()
        body_markdown = str(content.get("body_markdown") or "").strip()
        if not title:
            raise ValidationError("note title must be non-empty")
        if not body_markdown:
            raise ValidationError("note body must be non-empty")
        raw_tags = content.get("tags") or []
        if not isinstance(raw_tags, list) or not all(isinstance(tag, str) for tag in raw_tags):
            raise ValidationError("note tags must be strings")
        from uuid import uuid4

        note = self._db.notes.upsert(
            note_id=f"note-{uuid4().hex}",
            title=title,
            body_markdown=body_markdown,
            tags=[tag.strip() for tag in raw_tags if tag.strip()],
        )
        try:
            self._on_changed("note", note.id, "create")
        except Exception:  # pragma: no cover - a dead socket is not a failed write
            pass
        return note.to_dict()

    def hydrate_refs(
        self,
        principal: Principal,
        meeting_ids: list[str],
        artifact_ids: list[str],
        expand: str,
        *,
        query: str = "",
        qualified_refs: list[str] | None = None,
    ) -> tuple[list[Any], list[str]]:
        """Hydrate steer grounding through the application's database boundary."""
        from ..grounding import hydrate_refs

        return hydrate_refs(
            self._db,
            meeting_ids,
            artifact_ids,
            expand,
            qualified_refs=qualified_refs or None,
            query=query,
            # Conductor R1: only the attached refs (the query still orders a
            # picked container's members); memory never adds its own picks.
            include_memory=False,
        )

    def process_input_commands(self, targets: Any) -> Any:
        """Compose the local process-input command service for coder steering."""
        from ..db.delivery_receipts import NodeReceiptLedger
        from ..delivery.commands import HubCommandService, NodeCommandProcessor

        ledger = self._db.db_path.with_name(f"{self._db.db_path.stem}-coder-node-ledger.db")
        return HubCommandService(
            repo=self._db.delivery_receipts,
            processor=NodeCommandProcessor(
                node_id="local", targets=targets, ledger=NodeReceiptLedger(ledger)
            ),
            local_node_id="local",
        )

    @staticmethod
    def _split_session_id(value: str) -> tuple[str, str]:
        agent, separator, session_id = str(value or "").partition(":")
        if not separator or not agent.strip() or not session_id.strip():
            raise ValidationError("session_id must be agent:session_id")
        return agent.strip(), session_id.strip()

    @staticmethod
    def _age_seconds(stamp: str | None, now: datetime) -> int | None:
        if not isinstance(stamp, str) or not stamp.strip():
            return None
        try:
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(0, int((now - parsed).total_seconds()))
