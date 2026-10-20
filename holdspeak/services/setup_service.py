"""Transport-neutral first-run setup and onboarding operations."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import os
import hashlib
import shutil
import uuid
from pathlib import Path
from typing import Any

from ..db.core import Database
from ..principals import Principal
from .errors import NotFound, ServiceError, ValidationError


def _verb_for_action(action: str) -> str:
    return {
        "speech": "Set up speech",
        "engine": "Use it",
        "agent_engine": "Use it",
        "connection": "Use it",
        "calendar": "Use it",
        "agents": "Let my agents use HoldSpeak",
    }.get(action, "Use")


@observe_service
class SetupService:
    def __init__(
        self,
        db: Database,
        *,
        observer: PipelineObserver | None = None,
        web_bind: str = "127.0.0.1",
        auth_token_set: bool | None = None,
        onboarding_service: Any = None,
        local_ai_setup_service: Any = None,
        inference_default_service: Any = None,
        inference_assignment_service: Any = None,
        model_library_service: Any = None,
        people_service: Any = None,
        lan_scanner: Any = None,
        lan_checked_at: Any = None,
        home_provider: Any = Path.home,
        which: Any = shutil.which,
    ) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        # The runtime's real bind host and token (web_server.py composes them).
        self._web_bind = web_bind
        self._auth_token_set = auth_token_set
        self._onboarding = onboarding_service
        self._local_ai = local_ai_setup_service
        self._defaults = inference_default_service
        self._assignments = inference_assignment_service
        self._model_library = model_library_service
        self._people = people_service
        self._lan_scanner = lan_scanner
        self._lan_checked_at = lan_checked_at
        self._home = home_provider
        self._which = which

    def bind_found_sources(
        self,
        *,
        onboarding_service: Any = None,
        local_ai_setup_service: Any = None,
        inference_default_service: Any = None,
        inference_assignment_service: Any = None,
        model_library_service: Any = None,
        people_service: Any = None,
    ) -> None:
        """Bind the composition-owned producers after the web context exists."""
        self._onboarding = onboarding_service or self._onboarding
        self._local_ai = local_ai_setup_service or self._local_ai
        self._defaults = inference_default_service or self._defaults
        self._assignments = inference_assignment_service or self._assignments
        self._model_library = model_library_service or self._model_library
        self._people = people_service or self._people

    def found(self, principal: Principal) -> dict[str, Any]:
        """Read the one Setup inventory without running a process or network call.

        The rows are projections of the existing onboarding and inference reads.
        A caller can use the row's ``action`` with :meth:`use_found`; no row is
        adopted merely because it was found.
        """
        rows: list[dict[str, Any]] = []

        def row(
            row_id: str,
            kind: str,
            label: str,
            detail: str = "",
            *,
            state: str = "found",
            reason: str = "",
            egress_host: str | None = None,
            action: str | None = None,
            payload: dict[str, Any] | None = None,
            verb: str | None = None,
        ) -> None:
            rows.append({
                "id": row_id,
                "kind": kind,
                "label": label,
                "detail": detail,
                "state": state,
                "reason": reason,
                "egress_host": egress_host,
                "verb": verb or (_verb_for_action(action) if action else None),
                "action": action,
                "payload": payload or {},
            })

        # Speech is a local file/runtime read.  Keep the speech row even on an
        # empty Mac: the owner can fetch the small model with one press.
        speech_status: dict[str, Any] = {}
        if self._local_ai is not None:
            try:
                speech_status = dict(self._local_ai.status(principal) or {})
            except Exception as exc:
                row("speech", "speech", "Speech", state="does_not_work",
                    reason=f"Could not check speech: {type(exc).__name__}", action="speech")
        else:
            row("speech", "speech", "Speech", "Whisper runs on this Mac", action="speech")
        if not speech_status and not rows:
            row("speech", "speech", "Speech", "Whisper runs on this Mac", action="speech")
        elif speech_status:
            speech = speech_status.get("speech") if isinstance(speech_status.get("speech"), dict) else {}
            files = [item for item in speech_status.get("files", []) if isinstance(item, dict) and item.get("key") == "whisper"]
            file_detail = ""
            if files:
                file_detail = str(files[0].get("label") or files[0].get("name") or "Whisper")
                size = sum(int(item.get("size_bytes") or 0) for item in files)
                if size > 0:
                    file_detail += f" · {size // 1_000_000} MB"
            status_state = str(speech_status.get("state") or "").lower()
            ready = bool(speech.get("ready")) or status_state == "ready"
            failed = status_state in {"failed", "incomplete", "needs_runtime", "error"}
            pending = status_state in {"downloading", "pending", "working", "running", "queued", "in_progress"}
            row(
                "speech", "speech", "Speech", file_detail or "Whisper runs on this Mac",
                state="works" if ready else "does_not_work" if failed else "pending" if pending else "found",
                reason=str(speech_status.get("error") or "") if failed else "",
                egress_host=str((speech_status.get("egress") or {}).get("destination") or "huggingface.co") if not ready else None,
                action=None if ready else "speech",
                payload={"only": ["whisper"]},
            )

        # Stored default proposals are the existing owner-press engine read.
        if self._defaults is not None:
            try:
                for proposal in self._defaults.proposals():
                    if not isinstance(proposal, dict):
                        continue
                    pid = str(proposal.get("id") or "")
                    if not pid:
                        continue
                    host = str(proposal.get("host") or "")
                    row(
                        f"engine:{pid}", "engine", str(proposal.get("label") or pid), host,
                        egress_host=host or None, action="engine",
                        verb=str(proposal.get("verb") or "Use it"),
                        payload={"proposal_id": pid},
                    )
            except Exception:
                pass

        # E2 agent-engine detection is PATH and sign-in-file only.  It does not
        # probe an endpoint or run a CLI.
        try:
            from .concierge_service import _found_agent_engines

            db = getattr(self._defaults, "_db", None) or self._db
            for engine in _found_agent_engines(db, self._home()):
                preset = str(engine.get("agentPreset") or "")
                if not preset:
                    continue
                row(
                    f"agent-engine:{preset}", "engine", str(engine.get("name") or preset),
                    "signed in" if engine.get("signedIn") == "yes" else "on this Mac",
                    egress_host=str(engine.get("vendor") or "") or None,
                    action="agent_engine", payload={"preset": preset, "profile_id": f"agent-{preset}"},
                )
        except Exception:
            pass

        onboarding = self._onboarding
        if onboarding is not None:
            connection_candidates: list[dict[str, Any]] = []
            connection_tools: dict[str, Any] = {}
            try:
                detected = onboarding.connections_detect(principal)
                connection_candidates = [
                    candidate for candidate in detected.get("candidates", [])
                    if isinstance(candidate, dict)
                ]
                connection_tools = detected.get("tools", {}) if isinstance(detected, dict) else {}
                for candidate in connection_candidates:
                    cid = str(candidate.get("id") or "")
                    if not cid:
                        continue
                    provider = str(candidate.get("provider") or "Account").title()
                    detail = " · ".join(str(value) for value in (candidate.get("account"), candidate.get("site")) if value)
                    connected = bool(candidate.get("connected"))
                    candidate_verb = str(candidate.get("verb") or "").strip()
                    row(
                        f"connection:{cid}", "account", provider, detail,
                        state="works" if connected else "found" if candidate_verb else "does_not_work",
                        reason="" if connected or candidate_verb else "The account cannot be used here.",
                        egress_host=str(candidate.get("egress_host") or "") or None,
                        action=None if connected or not candidate_verb else "connection",
                        verb=candidate_verb or None, payload={"id": cid},
                    )
                seen_providers = {str(candidate.get("provider") or "").lower() for candidate in connection_candidates}
                missing_accounts = (
                    ("github", "GitHub", "gh"),
                    ("jira", "Jira", "acli"),
                    ("confluence", "Confluence", "acli"),
                )
                for provider, label, tool in missing_accounts:
                    if provider in seen_providers:
                        continue
                    installed = bool((connection_tools.get(tool) or {}).get("installed"))
                    detail = "No account found" if installed else f"{tool} is not installed"
                    reason = (
                        f"No {label} account was found on this Mac"
                        if installed else f"Install {tool} and sign in to use {label}"
                    )
                    row(
                        f"connection:{provider}:not-found", "account", label, detail,
                        state="does_not_work", reason=reason,
                    )
            except Exception:
                row(
                    "connections:not-found", "account", "Accounts", state="does_not_work",
                    reason="Accounts could not be read on this Mac",
                )
            try:
                calendar = onboarding.calendar_detect(principal)
                sources = int(calendar.get("sources") or 0)
                candidates = calendar.get("candidates") or []
                for candidate in candidates:
                    if not isinstance(candidate, dict):
                        continue
                    cid = str(candidate.get("id") or "")
                    if not cid:
                        continue
                    in_use = bool(candidate.get("in_use"))
                    candidate_verb = str(candidate.get("verb") or "").strip()
                    row(
                        f"calendar:{cid}", "calendar", "Calendar", str(candidate.get("label") or ""),
                        state="works" if in_use else "found" if candidate_verb else "does_not_work",
                        reason="" if in_use or candidate_verb else "Calendar access is not available.",
                        egress_host=str(candidate.get("egress_host") or "") or None,
                        action=None if in_use or not candidate_verb else "calendar",
                        verb=candidate_verb or None,
                        payload={"id": cid, "label": candidate.get("label") or ""},
                    )
                if sources and not candidates:
                    row("calendar", "calendar", "Calendar", f"{sources} source{'s' if sources != 1 else ''}", state="works")
                elif not sources and not candidates:
                    macos_state = str((calendar.get("macos") or {}).get("state") or "").lower()
                    detail = {
                        "denied": "Calendar access is denied",
                        "unavailable": "Calendar is not available on this Mac",
                        "not_determined": "Calendar access is not set up",
                    }.get(macos_state, "No calendar found on this Mac")
                    row(
                        "calendar:not-found", "calendar", "Calendar", detail,
                        state="does_not_work", reason="No calendar is ready to use",
                    )
            except Exception:
                row(
                    "calendar:not-found", "calendar", "Calendar", state="does_not_work",
                    reason="Calendar could not be read on this Mac",
                )
            try:
                agents = onboarding.agents_detect(principal).get("agents", [])
                ready_agents: list[str] = []
                pending_agents: list[str] = []
                installed_agents: list[str] = []
                for agent in agents:
                    if not isinstance(agent, dict) or not agent.get("installed"):
                        continue
                    label = str(agent.get("label") or agent.get("id") or "")
                    installed_agents.append(label)
                    if agent.get("ready"):
                        ready_agents.append(label)
                    elif str(agent.get("id") or "") in {"claude", "codex"}:
                        pending_agents.append(str(agent.get("id")))
                if ready_agents or pending_agents:
                    names = ", ".join(ready_agents + [next((str(a.get("label") or a.get("id")) for a in agents if isinstance(a, dict) and str(a.get("id")) == p), p) for p in pending_agents])
                    row(
                        "agents", "agents", "Agents", names,
                        state="works" if not pending_agents else "found",
                        action=None if not pending_agents else "agents",
                        payload={"agents": pending_agents},
                    )
                elif not installed_agents:
                    row(
                        "agents:not-found", "agents", "Agents",
                        "Claude Code, Codex and pi were not found on this Mac",
                        state="does_not_work", reason="Install a coding agent to use it with HoldSpeak",
                    )
            except Exception:
                row(
                    "agents:not-found", "agents", "Agents", state="does_not_work",
                    reason="Coding agents could not be read on this Mac",
                )

        owner_name = ""
        try:
            from ..config import Config

            owner_name = str(Config.load().owner.name or "").strip()
        except Exception:
            pass
        row("owner", "owner", "Your name", owner_name, state="works" if owner_name else "found", action=None)

        suggestions: list[dict[str, Any]] = []
        if self._people is not None:
            try:
                suggestions = list(self._people.suggestions(principal, db=self._db) or [])
            except Exception:
                suggestions = []
        relationships: list[dict[str, Any]] = []
        if self._people is not None:
            try:
                relationships = list(self._people.list_relationships(principal) or [])
            except Exception:
                relationships = []
        first_run = True
        try:
            from ..db import FIRST_DICTATION_SUCCESS

            first_run = not self._db.milestones.is_set(FIRST_DICTATION_SUCCESS)
        except Exception:
            # The inventory remains useful when a partially created database
            # cannot answer the optional first-run milestone read.
            pass
        return {
            "rows": rows,
            "owner_name": owner_name,
            "people": relationships,
            "suggestions": suggestions,
            "first_run": first_run,
        }

    def use_row(self, principal: Principal, id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run one existing Setup owner action selected by its found row."""
        body = payload or {}
        value = str(id or "")
        if value == "speech":
            if self._local_ai is None:
                raise ServiceError("setup_unavailable", "Speech setup is not available.", context={"status": 503})
            return self._local_ai.start(principal, only=("whisper",))
        if value.startswith("engine:"):
            if self._defaults is None:
                raise ServiceError("setup_unavailable", "Engine setup is not available.", context={"status": 503})
            result = self._defaults.use_proposal(principal, value.split(":", 1)[1])
            return {**result, "state": "ready"}
        if value.startswith("connection:") and self._onboarding is not None:
            return self._onboarding.connections_use(principal, {"id": value.split(":", 1)[1]})
        if value.startswith("calendar:") and self._onboarding is not None:
            result = self._onboarding.calendar_use(principal, {"id": value.split(":", 1)[1], "label": body.get("label", "")})
            return {**result, "state": "ready"}
        if value.startswith("agent-engine:") and self._model_library is not None:
            preset = value.split(":", 1)[1]
            self._require_engine_assignment()
            result = self._model_library.connect_cli_engine(principal, {
                "request_id": f"setup-agent-{preset}", "profile_id": f"agent-{preset}",
                "expected_profile_revision": 0, "preset": preset,
            })
            return self._use_engine(principal, result)
        if value.startswith("lan:") and self._model_library is not None:
            endpoint = str(body.get("base_url") or body.get("baseUrl") or "").strip()
            model = str(body.get("model") or body.get("name") or "").strip()
            if not endpoint or not model:
                raise ValidationError("The network engine has no model address.")
            self._require_engine_assignment()
            key = hashlib.sha256(f"{endpoint}\n{model}".encode()).hexdigest()[:20]
            result = self._model_library.define_endpoint(principal, {
                "request_id": f"setup-lan-{key}",
                "profile_id": f"lan-{key}",
                "expected_profile_revision": 0,
                "label": model,
                "model": model,
                "provider_family": "private_endpoint",
                "requires_key": False,
                "endpoint": endpoint,
            })
            return self._use_engine(principal, result)
        raise ValidationError("Setup row cannot be used here.")

    def _require_engine_assignment(self) -> None:
        if self._assignments is None:
            raise ServiceError("setup_unavailable", "Engine selection is not available.", context={"status": 503})

    def _use_engine(self, principal: Principal, result: dict[str, Any]) -> dict[str, Any]:
        """The Setup Use gesture adds the engine and selects Everything else.

        Model Library deliberately leaves assignments unchanged. Setup owns
        this second, explicit part of its gesture; speech never inherits the
        global chat assignment.
        """
        provider = result["provider"]
        scope = {"kind": "global"}
        try:
            current = self._assignments.get_assignment(principal, scope)
            revision = int(current["revision"])
        except NotFound:
            revision = 0
        assignment = self._assignments.set_assignment(principal, {
            "command_id": f"setup-engine-{uuid.uuid4().hex}",
            "expected_revision": revision,
            "scope": scope,
            "entries": [{"profile_id": provider["profile_id"], "profile_revision": provider["profile_revision"]}],
        })
        return {"library": result, "assignment": assignment, "state": "ready"}

    # Kept as a small compatibility seam for the service-level callers that
    # existed before ST3's operation descriptor was added. The web route uses
    # ``setup.use`` and therefore calls ``use_row`` through the registry.
    def use_found(self, principal: Principal, row_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.use_row(principal, row_id, payload)

    def scan_lan(self, principal: Principal) -> dict[str, Any]:
        """Perform the one explicit private-network look when Setup opens."""
        from .lan_engine_discovery import checked_at, scan_lan_engines

        checked = self._lan_checked_at or checked_at
        if os.environ.get("HOLDSPEAK_SETUP_LAN_SCAN", "on").strip().lower() in {
            "0", "off", "false", "no",
        }:
            return {"rows": [], "checkedAt": checked(), "disabled": True}
        scanner = self._lan_scanner or scan_lan_engines
        result = scanner(principal=principal)
        return {"rows": result.get("engines", []), "checkedAt": checked()}

    def add_people(self, principal: Principal, names: Any) -> dict[str, Any]:
        if self._people is None:
            raise ServiceError("people_unavailable", "People are not available on this hub.", context={"status": 503})
        if isinstance(names, str):
            values = [part.strip() for part in names.split(",")]
        elif isinstance(names, list):
            values = [str(part).strip() for part in names]
        else:
            raise ValidationError("Add names separated by commas.")
        values = [name for name in values if name]
        if not values:
            raise ValidationError("Add a name.")
        # People creates its encrypted store on the first write.  Honor the
        # explicit Setup gesture when this composition exposes readiness and
        # still needs it; the existing create path remains the fallback for
        # older PeopleService implementations.
        readiness = getattr(self._people, "readiness_state", None)
        setup = getattr(self._people, "setup", None)
        if callable(readiness) and callable(setup) and readiness() == "unconfigured":
            setup(principal)
        relationships = [
            self._people.create_relationship(principal, {"display_name": name, "relationship_kind": "direct_report"})
            for name in values
        ]
        return {"relationships": relationships}

    def status(self, principal: Principal) -> dict[str, Any]:
        from ..setup_status import build_setup_status

        return build_setup_status(
            database=self._db,
            web_bind=self._web_bind,
            auth_token_set=self._auth_token_set,
        )

    def test_runtime(self, principal: Principal, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        from ..config import Config
        from ..setup_runtime import probe_runtime

        return probe_runtime(Config.load().dictation)

    def set_onboarding_disposition(
        self, principal: Principal, payload: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            from ..db.onboarding import ONBOARDING_DISPOSITIONS
            disposition = str(payload.get("disposition") or "").strip().lower()
            if disposition not in ONBOARDING_DISPOSITIONS:
                raise ValueError(f"invalid onboarding disposition: {payload.get('disposition')!r}")
            # The ordinary seed is the durable gate for leaving first value.
            # Keep it here as defence in depth: any caller that persists an
            # onboarding exit cannot reveal an unfurnished Desk.
            from ..db.seed import apply_seed

            apply_seed(self._db)
            state = self._db.onboarding.set_disposition(disposition)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return {"success": True, "onboarding": state}

    def start_first_value(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
        self._reject_content(payload)
        try:
            attempt = self._db.onboarding.start_attempt(
                destination=str(payload.get("destination") or "this_machine")
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return {"success": True, "attempt": attempt}

    def finish_first_value(
        self, principal: Principal, attempt_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._reject_content(payload)
        try:
            attempt = self._db.onboarding.finish_attempt(
                attempt_id,
                outcome=str(payload.get("outcome") or ""),
                steps=payload.get("steps"),
                decisions=payload.get("decisions"),
                destination=str(payload.get("destination") or "this_machine"),
                failure_category=payload.get("failure_category"),
            )
        except KeyError as exc:
            raise NotFound("first-value attempt", attempt_id) from exc
        except (TypeError, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        # HS-140-02 records transcript-backed local success only. Story 05
        # owns the later seed-before-reveal milestone and onboarding exit.
        return {"success": True, "attempt": attempt}

    def record_event(
        self, principal: Principal, attempt_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._reject_event_payload(payload)
        try:
            event = self._db.onboarding.record_event(
                attempt_id,
                event_id=str(payload.get("event_id") or ""),
                kind=str(payload.get("kind") or ""),
            )
        except KeyError as exc:
            raise NotFound("first-value attempt", attempt_id) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return {"success": True, "event": event}

    @staticmethod
    def _reject_content(payload: dict[str, Any]) -> None:
        if {
            "text", "phrase", "transcript", "content", "audio",
            "clipboard", "clipboard_value", "note_body", "body_markdown",
        }.intersection(payload):
            raise ValidationError("First-value receipts never accept phrase content.")

    @staticmethod
    def _reject_event_payload(payload: dict[str, Any]) -> None:
        allowed = {"event_id", "kind"}
        if set(payload).difference(allowed):
            raise ValidationError("First-value events accept only event_id and kind.")
