"""Transport-neutral composition for the delivery domain.

2026-11-09 (one contract): the route bodies of ``/api/delivery/*`` are verbs
here, each ``(principal, ...)``; ``holdspeak/delivery_operations.py`` declares
them and the routes and MCP tools are produced from the rows. The
collaborators (the collector, the dossiers, the PR cache, the attempts, the
node link, the terminal targets, the commands, the launcher) build lazily on
first use, so composing the hub has no side effects. ``configure`` takes the
hub's shared instances (``runtime/web_mount.py``) and the test seams the
routers took before.
"""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import base64
from threading import Lock, RLock
from typing import Any, Callable, Optional

from ..db.core import Database
from ..logging_config import get_logger
from .errors import NotFound, ServiceError

log = get_logger("services.delivery")

#: The collaborators a caller can hand in ready-made (the hub's shared ones, a test's fakes).
_COLLABORATORS = frozenset({
    "collector", "dossiers", "prs", "attempts", "sweep", "profiles", "targets",
    "commands", "launcher", "stream", "live", "workspace", "link", "pr_actuators",
})
#: The settings the lazy builds read, with their production defaults.
_SETTINGS: dict[str, Any] = {
    "registry_path": None, "map_path": None, "runner": None, "dw_argv_factory": None,
    "max_age_seconds": 15.0, "claims_state_path": None, "launches_path": None,
    "ledger_path": None, "profiles_path": None, "local_node_id": "local", "mode_loader": None,
    "sync_on_read": True, "token_store_path": None, "web_token": None, "legacy_env": None,
}
#: Typed subscription absences and their HTTP status (PLATFORM-CONTRACT §7.1).
TERMINAL_ABSENCE_HTTP = {"target_gone": 404, "generation_mismatch": 409, "stream_unavailable": 503,
                         "unauthorized": 401}


def _refusal(code: str, detail: str, http: int, body: dict[str, Any]) -> ServiceError:
    """A domain refusal that keeps the wire body and status the route answered with."""
    return ServiceError(code, detail, context={"http": http, "body": body})


def _flag(value: Any) -> bool:
    """A query flag (``?active_only=true``) or a JSON boolean."""
    return value.strip().lower() in {"1", "true", "yes", "on"} if isinstance(value, str) else bool(value)


def _number(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise _refusal("validation_error", f"{name} must be an integer", 422,
                       {"error": "validation_error", "detail": f"{name} must be an integer"}) from None


@observe_service
class DeliveryService:
    """Own delivery persistence, compose the delivery collaborators, answer the delivery verbs."""

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        self._built: dict[str, Any] = {}
        self._given: set[str] = set()
        self._settings: dict[str, Any] = dict(_SETTINGS)
        self._build_lock = RLock()
        self._link_lock = Lock()

    def configure(self, **seams: Any) -> "DeliveryService":
        """Hand in shared collaborators and settings; ``None`` keeps the default."""
        for name, value in seams.items():
            if name in _COLLABORATORS:
                if value is not None:
                    self._built[name] = value
                    self._given.add(name)
            elif name in _SETTINGS:
                if value is not None:
                    self._settings[name] = value
            else:
                raise TypeError(f"DeliveryService.configure: unknown seam {name!r}")
        return self

    def draft_review(self, principal: Any, source_id: str, number: int) -> tuple[int, dict[str, Any]]:
        from ..operations import OperationOwnerRequired
        from ..principals import PrincipalKind, PrincipalRight
        from ..kernel.runtime import _service as kernel_service
        from .delivery_review import draft_review
        if principal.kind is not PrincipalKind.OWNER or not principal.permits(PrincipalRight.OWNER):
            raise OperationOwnerRequired("delivery.pr_draft_review")
        return draft_review(self.pr_receipts(), kernel_service(), principal, source_id, int(number))

    def belt_state(self, principal: Any) -> dict[str, Any]:
        from ..missioncontrol_bridge import load_project_map, state_payload
        try:
            return state_payload(load_project_map(self._settings["map_path"]), self._settings["runner"], principal=principal)
        except Exception as exc:
            log.warning("mission control state failed (%s)", exc)
            return {"repos": [], "error": "mission control state failed"}

    def belt_journal(self, principal: Any, limit: int = 50) -> dict[str, Any]:
        from ..db import get_database
        from ..rails_observer import list_journal
        try:
            entries = list_journal(self._db if self._db is not None else get_database(), limit=limit)
            return {"entries": [{"id": note.id, "title": note.title, "body_markdown": note.body_markdown,
                                  "created_at": getattr(note, "created_at", "")} for note in entries]}
        except Exception as exc:
            log.warning("rails journal read failed (%s)", exc)
            return {"entries": [], "error": "rails journal read failed"}

    # -- the lazy collaborators -------------------------------------------------

    def _get(self, name: str, build: Callable[[], Any]) -> Any:
        if name not in self._built:
            with self._build_lock:
                if name not in self._built:
                    self._built[name] = build()
        return self._built[name]

    def _registry(self) -> Any:
        from ..delivery import DeliveryRegistry

        return DeliveryRegistry(self._settings["registry_path"], map_path=self._settings["map_path"])

    def _dw_kwargs(self) -> dict[str, Any]:
        return {"runner": self._settings["runner"], "dw_argv_factory": self._settings["dw_argv_factory"],
                "max_age_seconds": self._settings["max_age_seconds"]}

    def _collector(self) -> Any:
        from ..delivery import DeliveryCollector

        return self._get("collector", lambda: DeliveryCollector(self._registry(), **self._dw_kwargs()))

    def _dossiers(self) -> Any:
        from ..delivery.dossiers import DossierService

        return self._get("dossiers", lambda: DossierService(self._registry(), **self._dw_kwargs()))

    def pr_receipts(self) -> Any:
        """The PR cache: production reads the one the Heartbeat sweep refreshes."""
        def build() -> Any:
            from ..delivery.pr_receipts import PrReceiptsService, default_pr_receipts

            seams = (self._settings["registry_path"], self._settings["map_path"], self._settings["runner"])
            if all(seam is None for seam in seams):
                return default_pr_receipts()
            return PrReceiptsService(self._registry(), runner=self._settings["runner"])

        return self._get("prs", build)

    def _attempts(self) -> Any:
        def build() -> Any:
            from ..delivery.attempts import WorkAttemptService, resolver_from_registry

            return WorkAttemptService(self._db.work_attempts, resolver=resolver_from_registry(self._registry()))

        return self._get("attempts", build)

    def _attempts_sweep(self) -> Any:
        """The launch sweep the attempts read runs first (HS-111-06), or None.

        Off when a caller handed in the attempts and no sweep (a hermetic test rig)."""
        if "sweep" not in self._built and "attempts" in self._given:
            return None

        def build() -> Any:
            launcher = self._new_launcher(profiles=None, targets=None, commands=None)

            def sweep() -> None:
                launcher.bind_rider_claims(state_path=self._settings["claims_state_path"])
                launcher.expire_unregistered()

            return sweep

        return self._get("sweep", build)

    def _profiles(self) -> Any:
        from ..delivery.factory_launch import AgentProfileStore

        return self._get("profiles", lambda: AgentProfileStore(self._settings["profiles_path"]))

    def _targets(self) -> Any:
        from ..delivery.terminal import TerminalTargetRegistry

        return self._get("targets", TerminalTargetRegistry)

    def _commands(self) -> Any:
        def build() -> Any:
            from ..db.delivery_receipts import NodeReceiptLedger
            from ..delivery.commands import HubCommandService, NodeCommandProcessor

            node_id = self._settings["local_node_id"]
            processor = NodeCommandProcessor(node_id=node_id, targets=self._targets(),
                                             ledger=NodeReceiptLedger(self._settings["ledger_path"]))
            return HubCommandService(repo=self._db.delivery_receipts, processor=processor, local_node_id=node_id,
                                     mode_loader=self._settings["mode_loader"])

        commands = self._get("commands", build)
        # Remote nodes claim their queued commands through the shared node link.
        link = self._built.get("link")
        if link is not None and getattr(link, "command_source", None) is None:
            link.command_source = commands.claim_for_node
        return commands

    def _new_launcher(self, *, profiles: Any, targets: Any, commands: Any) -> Any:
        from ..delivery.factory_launch import LaunchLedger, LaunchService

        return LaunchService(
            profiles=profiles, registry=self._registry(), targets=targets, commands=commands,
            attempts=self._db.work_attempts, ledger=LaunchLedger(self._settings["launches_path"]),
            local_node_id=self._settings["local_node_id"], db=self._db,
        )

    def _launcher(self) -> Any:
        return self._get("launcher", lambda: self._new_launcher(
            profiles=self._profiles(), targets=self._targets(), commands=self._commands()))

    def _stream(self) -> Any:
        from ..delivery.terminal import TerminalStreamService

        return self._get("stream", lambda: TerminalStreamService(self._targets()))

    def _live(self) -> Any:
        return self._get("live", lambda: self.terminal_live_service(targets=self._targets()))

    def _workspace(self) -> Any:
        def build() -> Any:
            from .terminal_workspace import TerminalWorkspaceService
            from .terminal_workspace_context import TerminalWorkspaceContext

            return TerminalWorkspaceService(
                self._targets(), local_node_id=self._settings["local_node_id"],
                context=TerminalWorkspaceContext(self._db, registry_path=self._settings["registry_path"],
                                                 launches_path=self._settings["launches_path"]),
            )

        return self._get("workspace", build)

    def _link(self) -> Any:
        def build() -> Any:
            from ..delivery.node_link import NodeLinkState, NodeTokenStore

            return NodeLinkState(NodeTokenStore(self._settings["token_store_path"]),
                                 web_token=self._settings["web_token"])

        return self._get("link", build)

    def terminal_live_service(self, *, targets: Any, runner: Any = None, popen_factory: Any = None) -> Any:
        """Compose the continuous local terminal stream over shared targets.

        The stream is ephemeral and has no database collaborator; the hub
        composition builds it once (``runtime/delivery_composition.py``).
        """
        from ..delivery.terminal_live import TerminalLiveService

        kwargs: dict[str, Any] = {"targets": targets}
        if runner is not None:
            kwargs["runner"] = runner
        if popen_factory is not None:
            kwargs["popen_factory"] = popen_factory
        return TerminalLiveService(**kwargs)

    # -- the read model (HS-94-02) -------------------------------------------------

    def snapshot(self, principal: Any) -> dict[str, Any]:
        """The coherent cached read model (§4.4); polling never runs a fresh dw or gh."""
        return self._collector().snapshot()

    def sources(self, principal: Any) -> dict[str, Any]:
        """The registry and freshness view: labels, opaque ids, typed statuses."""
        return self._collector().sources_view()

    def register_source(self, principal: Any, path: Any = None, label: Any = None) -> dict[str, Any]:
        """Register a source by path; the server resolves and validates it (§10)."""
        from ..delivery.registry import RegistryError

        if not isinstance(path, str) or not path:
            raise _refusal("invalid_source", "path is required", 400, {"success": False, "error": "path is required"})
        try:
            result = self._collector().register_source(path, label=label if isinstance(label, str) else None)
        except RegistryError as refusal:
            raise _refusal("invalid_source", str(refusal), 400, {"success": False, "error": str(refusal)}) from refusal
        return {"success": True, **result}

    # -- work attempts (HS-94-04) ----------------------------------------------------

    def list_attempts(self, principal: Any, source_id: Any = "", project: Any = "", story_id: Any = "",
                      session_id: Any = "", active_only: Any = False) -> dict[str, Any]:
        """Durable attempts with state and provenance; the read sweeps launches and rider claims first."""
        attempts = self._attempts()
        if self._settings["sync_on_read"]:
            sweep = self._attempts_sweep()
            if sweep is not None:
                try:
                    # Launch attempts first (HS-94-07 ordering): once bound,
                    # the generic sweep below only heartbeats them.
                    sweep()
                except Exception as exc:
                    log.warning(f"launch sweep skipped: {exc}")
            try:
                attempts.sync_rider_claims(state_path=self._settings["claims_state_path"])
            except Exception as exc:  # an honest read beats a lost one
                log.warning(f"rider-claim sync skipped: {exc}")
        return attempts.list_attempts(
            source_id=source_id or None, project=project or None, story_id=story_id or None,
            session_id=session_id or None, active_only=_flag(active_only),
        )

    def create_attempt(self, principal: Any, source_id: Any = None, worktree_id: Any = None, project: Any = None,
                       story_id: Any = None, session_id: Any = None, node_id: Any = None,
                       target_id: Any = None) -> dict[str, Any]:
        """Attach exact work with explicit refs (provenance ``manual``). A session
        already bound to a live attempt is refused (409), never pinned twice."""
        from ..delivery.attempts import AttemptConflict, AttemptError

        refs = {"source_id": source_id, "worktree_id": worktree_id, "project": project, "story_id": story_id}
        missing = sorted(key for key, value in refs.items() if not isinstance(value, str) or not value)
        if missing:
            detail = f"missing {', '.join(missing)}"
            raise _refusal("invalid_attempt", detail, 400, {"success": False, "error": detail})
        try:
            attempt = self._attempts().manual_attach(
                **refs, session_id=session_id, node_id=node_id, target_id=target_id, actor="desk-owner",
            )
        except AttemptConflict as conflict:
            raise _refusal("attempt_conflict", str(conflict), 409, {"success": False, "error": str(conflict)}) from conflict
        except AttemptError as refused:
            raise _refusal("invalid_attempt", str(refused), 400, {"success": False, "error": str(refused)}) from refused
        return {"success": True, "attempt": attempt}

    # -- evidence dossiers (HS-94-05) ---------------------------------------------------

    @staticmethod
    def _dossier_refusal(refusal: Any) -> ServiceError:
        body: dict[str, Any] = {"refusal": refusal.code, "detail": refusal.detail}
        if refusal.manifest is not None:
            body["manifest"] = refusal.manifest
        return _refusal(refusal.code, refusal.detail, refusal.http_status, body)

    def story_dossier(self, principal: Any, project: str, story: str, source: Any = "") -> dict[str, Any]:
        """The story dossier. ``source`` pins one source; else every registered source is tried."""
        from ..delivery.dossiers import DossierRefusal

        try:
            dossiers = self._dossiers()
            if source:
                return dossiers.story_dossier(source, project, story)
            return dossiers.story_dossier_any(project, story)
        except DossierRefusal as refusal:
            raise self._dossier_refusal(refusal) from refusal

    def phase_dossier(self, principal: Any, project: str, phase: Any, source: Any = "") -> dict[str, Any]:
        """The phase dossier: grouped story dossiers and the final summary reference, metadata only."""
        from ..delivery.dossiers import DossierRefusal

        number = _number(phase, "phase")
        try:
            dossiers = self._dossiers()
            if source:
                return dossiers.phase_dossier(source, project, number)
            last: Any = None
            for source_id in dossiers.source_ids():
                try:
                    return dossiers.phase_dossier(source_id, project, number)
                except DossierRefusal as refusal:
                    if refusal.code != "not_found":
                        last = refusal
            raise last or DossierRefusal("not_found", f"phase {number} not found in any source")
        except DossierRefusal as refusal:
            raise self._dossier_refusal(refusal) from refusal

    def evidence_asset(self, principal: Any, bundle_id: str, asset_id: str) -> tuple[bytes, dict[str, Any]]:
        """Manifest-bound bytes and the manifest member, through dw's asset chokepoint."""
        from ..delivery.dossiers import DossierRefusal

        try:
            return self._dossiers().open_asset(bundle_id, asset_id)
        except DossierRefusal as refusal:
            raise self._dossier_refusal(refusal) from refusal

    def evidence_asset_wire(self, principal: Any, bundle_id: str, asset_id: str) -> dict[str, Any]:
        """The asset as one JSON object (the MCP face): its media type, sha256 and base64 bytes."""
        data, member = self.evidence_asset(principal, bundle_id, asset_id)
        return {"bundle_id": bundle_id, "asset_id": asset_id, "size": len(data),
                "media_type": str(member.get("media_type") or "application/octet-stream"),
                "sha256": str(member.get("sha256") or ""), "content_base64": base64.b64encode(data).decode("ascii")}

    # -- PR receipts (HS-104-04) ---------------------------------------------------------

    def _attempt_story_ids(self) -> list[str]:
        """Story ids of the durable Work attempts (the heuristic correlation input).
        Best effort: an empty list means no heuristic labels, never a failure."""
        try:
            ids = []
            for row in self._db.work_attempts.list():
                story_id = getattr(row, "story_id", None) or (row.get("story_id") if isinstance(row, dict) else None)
                if story_id:
                    ids.append(str(story_id))
            return sorted(set(ids))
        except Exception:
            return []

    def pr_rows(self, principal: Any) -> dict[str, Any]:
        """Cached PR rows and freshness. Only an explicitly configured per-source cadence polls."""
        prs = self.pr_receipts()
        prs.maybe_cadence_refresh(self._attempt_story_ids())
        return prs.rows_view()

    def refresh_prs(self, principal: Any, source_id: Any = None) -> dict[str, Any]:
        """Poll GitHub for the PR rows now: one batched ``gh`` per source."""
        return self.pr_receipts().refresh(source_id or None, attempt_story_ids=self._attempt_story_ids())

    def pr_diff(self, principal: Any, source_id: str, number: Any) -> dict[str, Any]:
        """The local diff of one PR, or the honest absence and the offer to fetch it."""
        return self.pr_receipts().diff(source_id, _number(number, "number"))

    def fetch_pr(self, principal: Any, source_id: str, number: Any) -> dict[str, Any]:
        """Fetch one PR's head so its diff is local (the explicit egress act)."""
        return self.pr_receipts().fetch(source_id, _number(number, "number"))

    # -- the node link (HS-94-03) --------------------------------------------------------

    def node_request(self, principal: Any, verb: str, args: dict[str, Any]) -> Any:
        from ..principals import PrincipalKind
        from ..operations import OperationOwnerRequired
        if getattr(principal, "kind", None) is PrincipalKind.AGENT:
            raise OperationOwnerRequired(f"delivery.node.{verb}")
        body = {key: value for key, value in args.items() if key not in ("node_token", "name")}
        return self.node_call(lambda link: getattr(link, verb)(args["name"], args["node_token"], **body))

    def node_call(self, call: Callable[[Any], Any]) -> Any:
        """Run *call* on the shared node link, one call at a time."""
        with self._link_lock:
            return call(self._link())

    def nodes(self, principal: Any) -> dict[str, Any]:
        """Node liveness with last-seen kept; legacy env-table nodes are labelled ``legacy-direct``."""
        from ..delivery.node_link import AUTH_REASONS, NodeLinkError

        try:
            return self.node_call(lambda link: link.nodes_view(legacy_env=self._settings["legacy_env"]))
        except NodeLinkError as exc:
            reason = getattr(exc, "reason", "refused")
            status = 401 if reason in AUTH_REASONS else 400 if reason.startswith("event_") else 409
            raise _refusal(reason, str(exc), status, {"ok": False, "error": reason, "detail": str(exc)}) from exc

    # -- terminals (HS-94-06) --------------------------------------------------------------

    def terminal_sessions(self, principal: Any) -> dict[str, Any]:
        """The current local terminal sessions, from the live tmux panes."""
        return self._workspace().discover()

    def terminal_read(self, principal: Any, target_id: Any = None, target_generation: Any = None,
                      resume_sequence: Any = None, last_hash: Any = None) -> dict[str, Any]:
        """One subscription poll: a snapshot, sequenced deltas, ``not_modified``,
        ``resync_required``, or a typed absence."""
        if not isinstance(target_id, str) or not isinstance(target_generation, str):
            raise _refusal("validation_error", "target_id and target_generation are required", 422,
                           {"error": "validation_error", "detail": "target_id and target_generation are required"})
        sequence = None if resume_sequence is None else _number(resume_sequence, "resume_sequence")
        return self._stream().read(target_id, target_generation, resume_sequence=sequence,
                                   last_hash=last_hash if isinstance(last_hash, str) else None)

    def terminal_subscribe(self, target_id: str, target_generation: str, *, stream_id: Optional[str] = None,
                           resume_sequence: Optional[int] = None) -> Any:
        """Open the continuous local stream of one target (the NDJSON route)."""
        return self._live().subscribe(target_id, target_generation, stream_id=stream_id,
                                      resume_sequence=resume_sequence)

    def terminal_command(self, principal: Any, body: dict[str, Any]) -> dict[str, Any]:
        """Submit one command intent; the hub derives the authority block."""
        from ..operations import OperationOwnerRequired
        from ..principals import PrincipalKind
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise OperationOwnerRequired("delivery.terminal_command")
        from ..delivery.commands import CommandRefused
        try:
            operation = body.get("operation") or {}
            if not isinstance(operation, dict):
                raise CommandRefused("operation_unknown", "operation must be an object")
            commands = self._commands()
            if operation.get("family") == "coder_steering" and operation.get("verb") in {"terminal.text", "terminal.keys"}:
                return commands.submit_process_input(body, principal)
            if operation.get("family") == "coder_steering" and operation.get("verb") == "process.resize@1":
                return commands.submit_process_resize(body, principal)
            return commands.submit(body)
        except CommandRefused as exc:
            raise _refusal(exc.reason, str(exc), 400,
                {"ok": False, "error": exc.reason, "detail": str(exc)}) from exc

    # -- the factory (HS-94-07) --------------------------------------------------------------

    def factory_profiles(self, principal: Any) -> dict[str, Any]:
        """The node's Agent Profiles: fixed executables and allow-listed option slots."""
        return self._profiles().to_wire()

    def factory_launch(self, principal: Any, body: dict[str, Any]) -> dict[str, Any]:
        """One typed agent launch from a profile, a source, a worktree and a story."""
        from ..operations import OperationOwnerRequired
        from ..principals import PrincipalKind
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise OperationOwnerRequired("delivery.factory_launch")
        from ..delivery.factory_launch import LaunchRefused
        from ..delivery.commands import CommandRefused
        try:
            return self._launcher().launch(body)
        except (LaunchRefused, CommandRefused) as exc:
            raise _refusal(exc.reason, str(exc), 400,
                {"ok": False, "error": exc.reason, "detail": str(exc)}) from exc

    def factory_discover(self, principal: Any) -> dict[str, Any]:
        """Panes and sessions as immutable targets; the read first binds rider
        claims and expires overdue registrations."""
        launcher = self._launcher()
        if self._settings["sync_on_read"]:
            try:
                launcher.bind_rider_claims(state_path=self._settings["claims_state_path"])
                launcher.expire_unregistered()
            except Exception as exc:
                log.warning(f"launch-claim sweep skipped: {exc}")
        return launcher.discover()

    def default_launch_service(self) -> Any:
        from ..delivery.factory_launch import default_launch_service
        from ..kernel.runtime import _service as kernel_service

        service = default_launch_service(self._db)
        service.bind_kernel(kernel_service())
        return service

    # HS-131-13 deleted `prepare_pr_review`. It had no caller: the PR review route
    # was migrated to the admitted Delivery parent, frozen revision, staged
    # projection, and terminal receipt in HS-131-07, and this dormant helper still
    # resolved a MUTABLE target and constructed an engine with no admitted child
    # behind it. Dormant is not exempt from Article XI.2.

    def persist_pr_review_artifact(
        self, *, name: str, user_input: str, output: str, sources: list[dict[str, Any]]
    ) -> str | None:
        from .support import _persist_run_artifact

        return _persist_run_artifact(
            db=self._db,
            kind="pr_review",
            name=name,
            user_input=user_input,
            output=output,
            sources=sources,
        )

    @staticmethod
    def _pr_available(context: dict[str, Any], verb: str) -> None:
        if context.get("status") != "ok":
            raise _refusal("unknown_pr", "Unknown PR", 404, {"error": "unknown_pr"})
        available = ((context.get("row") or {}).get("verbs") or {}).get(verb) or {}
        if not available.get("available"):
            raise _refusal("verb_unavailable", "The PR action is unavailable", 409,
                {"error": "verb_unavailable", "verb": verb, "reason": available.get("reason") or "unavailable"})

    def send_pr_agent(self, principal: Any, source_id: str, number: Any, body: dict[str, Any]) -> dict[str, Any]:
        from uuid import uuid4
        from ..operations import OperationOwnerRequired
        from ..principals import PrincipalKind
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise OperationOwnerRequired("delivery.pr_send_agent")
        number = _number(number, "number")
        context = self.pr_receipts().action_context(source_id, number)
        self._pr_available(context, "send_agent")
        material = self.pr_receipts().review_material(source_id, number)
        if material.get("status") != "ok":
            raise _refusal("diff_unavailable", "The PR diff is unavailable", 409,
                {"error": "diff_unavailable", "reason": material.get("detail") or material.get("status")})
        instruction = str(body.get("instruction") or "").strip()
        bounded = (f"PR #{number} {context['row'].get('url')}\n{instruction}\n\nDiff (bounded):\n"
            + str(material.get("diff") or "")[:1600])
        launch = {"agent_profile_id": str(body.get("agent_profile_id") or "claude-default"),
            "source_id": source_id, "worktree": {"mode": "existing", "worktree_id": context["worktree_id"]},
            "story_ref": {"project": "holdspeak", "story_id": str(material.get("story_id") or f"PR-{number}")},
            "session_label": f"hs-pr-{number}-{uuid4().hex[:6]}"}
        try:
            return self.default_launch_service().submit_process_spawn(launch, bounded, principal)
        except Exception as exc:
            reason = getattr(exc, "reason", "process_spawn_failed")
            raise _refusal(reason, str(exc), 409, {"error": reason, "detail": str(exc)}) from exc

    def propose_pr(self, principal: Any, source_id: str, number: Any, body: dict[str, Any]) -> dict[str, Any]:
        from uuid import uuid4
        from ..kernel.runtime import _service as kernel_service
        number = _number(number, "number")
        kind = str(body.get("kind") or "comment")
        context = self.pr_receipts().action_context(source_id, number)
        self._pr_available(context, "post_status" if kind == "status" else "post_comment")
        row = context["row"]
        proposal_id = str(uuid4())
        if kind == "status":
            preview = str(body.get("description") or "").strip()
            payload = {"repo": row.get("repo"), "sha": row.get("head_sha"), "state": str(body.get("state") or "pending"),
                "context": str(body.get("context") or "HoldSpeak"), "description": preview}
            action = "set_commit_status"
        else:
            preview = str(body.get("body") or "").strip()
            payload = {"repo": row.get("repo"), "number": number, "body": preview}
            action = "comment_pr"
        if not preview:
            raise _refusal("proposal_text_required", "Proposal text is required", 400, {"error": "proposal_text_required"})
        handle = kernel_service().submit({"request_schema": 1, "request_id": str(uuid4()),
            "idempotency_key": f"pr-proposal:{proposal_id}", "operation": {"name": "actuator.egress", "version": 1},
            "subject_refs": [f"pr:{source_id}:{number}"], "target": {"ref": f"actuator:{proposal_id}"},
            "arguments": {"proposal_id": proposal_id, "origin": "desk", "window_id": f"pr-{source_id}-{number}",
                "plugin_id": "github_pr_follow", "plugin_version": "1", "target": "github", "action": action,
                "preview": preview, "payload": payload, "reversible": False, "required_capabilities": ["actuator"]},
            "placement": "node:actuator-local"}, principal)
        answer = {**handle, "proposal_id": proposal_id, "preview": preview, "kind": kind}
        if handle.get("state") == "refused":
            raise _refusal("proposal_refused", "The kernel refused the proposal", 409, answer)
        return answer

    def decide_pr(self, principal: Any, proposal_id: str, decision: Any) -> dict[str, Any]:
        from ..operations import OperationOwnerRequired
        from ..principals import PrincipalKind
        from ..kernel.runtime import _service as kernel_service
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise OperationOwnerRequired("delivery.pr_decide")
        if decision not in {"approve", "reject"}:
            raise _refusal("decision_unknown", "Unknown decision", 400, {"error": "decision_unknown"})
        lifecycle = self._built.get("pr_actuators")
        if lifecycle is None:
            raise _refusal("hub_required", "The live hub executes this proposal", 409, {"error": "hub_required"})
        broker = kernel_service()
        objects = broker.read([f"actuator:{proposal_id}"], "state", "committed", principal).get("objects") or []
        if not objects:
            raise _refusal("proposal_unknown", "Unknown proposal", 404, {"error": "proposal_unknown"})
        operation = objects[0]["operation"]
        try:
            handle = broker.decide(operation["operation_id"], decision, operation["revision"], principal)
        except Exception as exc:
            reason = getattr(exc, "reason", "decision_failed")
            raise _refusal(reason, str(exc), 409, {"error": reason}) from exc
        proposal = self.actuator_proposal(proposal_id)
        if decision == "approve":
            proposal = lifecycle.execute(proposal, actor=principal.identity)
        return {**handle, "proposal": lifecycle.serialize(proposal)}

    def actuator_proposal(self, proposal_id: str) -> Any:
        proposal = self._db.actuators.get_proposal(proposal_id)
        if proposal is None:
            raise NotFound("proposal", proposal_id)
        return proposal

    def execute_actuator_proposal(
        self, executor: Any, ctx: Any, proposal: Any, *, actor: str
    ) -> Any:
        return executor(ctx, self._db, proposal, actor=actor)
