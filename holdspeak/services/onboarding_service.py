"""Onboarding backends: find what the owner already has, and one "Use it".

Owner, 2026-10-05: "strong defaults, batteries included" and an interactive
onboarding.  The faces show candidates; each has one verb, "Use it".  A
detect call finds candidates with zero setup; "Use it" is the owner's press
(CONFIG / AUTHORITY consent) and writes through the existing services.

What each call touches:

Calendar
  * ``calendar_detect`` reads the macOS Calendars permission (no prompt) and,
    with full access, the calendar list through EventKit.  No network.
  * ``calendar_request_access`` shows the macOS Calendars prompt.  Only this
    explicit call does that; boot and detect never do.
  * ``calendar_check`` validates one ICS URL and fetches it once (the owner's
    press; HTTPS, no redirect, no proxy, size-bounded: the same reader the
    ingest uses).  That fetch is egress to the URL's host, named in the
    answer.  ``webcal://`` reads as ``https://``.
  * ``calendar_use`` adds the source to ``calendar.sources`` through
    ``SettingsService.update_settings`` and asks the ingest for one refresh.

Connections
  * ``connections_detect`` runs no process and makes no network request:
    GitHub from ``gh``'s ``hosts.yml`` (host names and logins only; the token
    is never read out), Jira and Confluence from ``acli``'s
    ``jira_config.yaml`` / ``confluence_config.yaml`` (site and email).
  * ``connections_use`` adds the connector and runs its existing status probe:
    GitHub ``gh auth status --hostname <host>`` (gh checks its token against
    that host only; the answer names the host and login);
    Jira / Confluence ``acli <product> auth switch`` + ``auth status`` under
    the acli lock (the switch-and-verify law).  Those probes reach the
    provider; the answer names the host.
  * A Send destination names one target (an issue number, a Jira key, a
    Confluence space), so "Use it" on an account connects the connector; the
    destination is saved where the owner names the target.

Agents (the Conductor, step 1 "Ready")
  * ``agents_detect`` runs no process and makes no network request: ``claude``,
    ``codex``, ``tmux`` and ``holdspeak`` on PATH; our hook entries in the
    settings file each agent reads (``CLAUDE_CONFIG_DIR`` / ``CODEX_HOME``, else
    ``~/.claude/settings.json`` / ``~/.codex/hooks.json``), and whether their
    command can run; sign-in from stored credentials only.  Inconclusive
    evidence reads ``unknown`` (the macOS Keychain, the Codex keyring), never
    ``no``.  No credential value is read out.
  * ``agents_use`` is the admitted, owner-only kernel operation
    ``agent_hooks.install``: one receipt for success, refusal or failure.  It
    merges the HoldSpeak hooks into the file the operation bound at admission
    (the same idempotent merge as ``holdspeak agent-hook install``; foreign
    hooks are kept).  A local file write; no network.
"""
from __future__ import annotations

import ipaddress
import os
import re
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlsplit

from ..logging_config import get_logger
from ..principals import Principal
from .errors import ConflictError, NotFound, ServiceError, ValidationError

log = get_logger("onboarding")

VERB = "Use it"


def _lamp_for_host(host: str) -> str:
    """The lamp of a host the owner's press reaches: local, lan or cloud."""
    text = str(host or "").strip().lower()
    if text in {"localhost", ""}:
        return "local"
    try:
        address = ipaddress.ip_address(text)
    except ValueError:
        return "lan" if text.endswith(".local") else "cloud"
    if address.is_loopback:
        return "local"
    if address.is_private or address.is_link_local:
        return "lan"
    return "cloud"


def gh_hosts_path(environ: Optional[dict[str, str]] = None, home: Optional[Path] = None) -> Path:
    """Where ``gh`` keeps ``hosts.yml``: GH_CONFIG_DIR, XDG_CONFIG_HOME/gh, ~/.config/gh."""
    env = os.environ if environ is None else environ
    if env.get("GH_CONFIG_DIR"):
        return Path(env["GH_CONFIG_DIR"]) / "hosts.yml"
    if env.get("XDG_CONFIG_HOME"):
        return Path(env["XDG_CONFIG_HOME"]) / "gh" / "hosts.yml"
    return (home or Path.home()) / ".config" / "gh" / "hosts.yml"


def read_gh_accounts(path: Path) -> list[dict[str, Any]]:
    """Host names and logins from ``gh``'s ``hosts.yml``; never a token.

    One row per (host, login).  ``active`` is the login gh uses now
    (``user:``); gh keeps one active login per host.
    """
    import yaml

    try:
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        from .jira_provider import config_read_failure

        # Class and position only: the YAML error text quotes the file, and
        # hosts.yml holds tokens.
        log.debug("could not read gh hosts at %s: %s", path, config_read_failure(exc))
        return []
    if not isinstance(data, dict):
        return []
    rows: list[dict[str, Any]] = []
    for host, entry in data.items():
        if not isinstance(entry, dict):
            continue
        active = str(entry.get("user") or "").strip()
        users = entry.get("users")
        logins = [str(login) for login in users] if isinstance(users, dict) else []
        if active and active not in logins:
            logins.insert(0, active)
        for login in logins:
            rows.append({"host": str(host).strip().lower(), "login": login, "active": login == active})
    return rows


class OnboardingService:
    """Detect -> candidates -> "Use it", for the calendar and the connections."""

    def __init__(
        self,
        *,
        settings_service: Any = None,
        connections_service: Any = None,
        jira_provider: Any = None,
        confluence_provider: Any = None,
        config_loader: Optional[Callable[[], Any]] = None,
        home_provider: Callable[[], Path] = Path.home,
        environ: Optional[dict[str, str]] = None,
        macos: Any = None,
        calendar_reader: Any = None,
        calendar_refresh: Optional[Callable[[], Any]] = None,
        which: Callable[[str], Optional[str]] = shutil.which,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._settings = settings_service
        self._connections = connections_service
        self._jira = jira_provider
        self._confluence = confluence_provider
        if config_loader is None:
            from ..config import Config

            config_loader = Config.load
        self._config = config_loader
        self._home = home_provider
        self._environ = environ
        if macos is None:
            from .. import macos_calendar as macos
        self._macos = macos
        self._reader = calendar_reader
        self._refresh = calendar_refresh if calendar_refresh is not None else _refresh_calendar_ingest
        self._which = which
        self._clock = clock

    # ── calendar ──────────────────────────────────────────────────────

    def _sources(self) -> list[Any]:
        return list(self._config().calendar.sources)

    def _macos_candidates(self, in_use: set[str]) -> list[dict[str, Any]]:
        out = []
        for calendar in self._macos.list_calendars():
            source_id = f"eventkit:{calendar['id']}"
            out.append({
                "id": source_id,
                "kind": "macos",
                "label": calendar["title"],
                "account": calendar["account"],
                "calendar_kind": calendar["kind"],
                "lamp": "local",
                "egress_host": None,
                "in_use": source_id in in_use,
                "verb": VERB,
            })
        return out

    def calendar_detect(self, principal: Principal) -> dict[str, Any]:
        """What the owner already has: the macOS calendars (no prompt, no network)."""
        state = self._macos.access_state()
        in_use = {str(s.url) for s in self._sources()}
        return {
            "macos": {
                "state": state,
                # The face offers the macOS prompt only while it can appear.
                "can_request": state == "not_determined",
            },
            "candidates": self._macos_candidates(in_use) if state == "full_access" else [],
            "sources": len(in_use),
        }

    def calendar_request_access(self, principal: Principal) -> dict[str, Any]:
        """The owner's press: show the macOS Calendars prompt, then detect again."""
        state = self._macos.request_access()
        result = self.calendar_detect(principal)
        result["macos"]["requested"] = state
        return result

    def calendar_open_settings(self, principal: Principal) -> dict[str, Any]:
        """``calendar.open_settings`` (PHILO-15 04): the owner's press opens System
        Settings at Privacy & Security > Calendars, the one way forward when the
        Calendars permission is denied (admitted kernel operation, one receipt)."""
        from . import project_kernel

        if project_kernel.current() is None:
            raise RuntimeError("calendar.open_settings runs only as an admitted kernel operation")
        _require_owner(principal)
        if not self._macos.open_privacy_settings():
            raise ConflictError("System Settings did not open.", code="system_settings_not_opened")
        return {"opened": True, "pane": "privacy_calendars"}

    def calendar_check(self, principal: Principal, url: Any) -> dict[str, Any]:
        """Validate one ICS URL and read it once (egress to its host on this press)."""
        from ..calendar_ingest import HORIZON_DAYS, parse_calendar_bytes
        from ..calendar_ingest_conductor import CalendarSourceError, CalendarSourceReader
        from ..config.integrations import validate_calendar_subscription

        text = str(url or "").strip()
        try:
            source = validate_calendar_subscription(text)
        except ValueError as exc:
            raise ValidationError(str(exc), code="calendar_url_invalid") from exc
        if not source.lower().startswith("https://"):
            raise ValidationError("Give an https:// or webcal:// calendar link.", code="calendar_url_invalid")
        host = str(urlsplit(source).hostname or "").lower()
        base = {"url": source, "host": host, "lamp": _lamp_for_host(host)}
        reader = self._reader or CalendarSourceReader()
        try:
            raw = reader.read(source)
        except CalendarSourceError as exc:
            return {**base, "ok": False, "error_class": exc.error_class,
                    "redirect_target": exc.redirect_target or None}
        parsed = parse_calendar_bytes(raw, now=self._clock(), subscription_revision="onboarding-check")
        if parsed.feed_error:
            return {**base, "ok": False, "error_class": parsed.feed_error, "redirect_target": None}
        label = _calendar_name(raw) or host
        in_use = {str(s.url) for s in self._sources()}
        return {
            **base,
            "ok": True,
            "candidate": {
                "id": source,
                "kind": "ics",
                "label": label,
                "account": host,
                "calendar_kind": "subscription",
                "lamp": base["lamp"],
                "egress_host": host,
                "in_use": source in in_use,
                "verb": VERB,
            },
            "events_next_days": len(parsed.events),
            "horizon_days": HORIZON_DAYS,
        }

    def calendar_use(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        """The owner's "Use it": add the calendar to ``calendar.sources``."""
        from ..config.integrations import validate_calendar_subscription

        if self._settings is None:
            raise ServiceError("onboarding_unavailable", "Settings are not available.", context={"status": 503})
        candidate_id = str((body or {}).get("id") or "").strip()
        try:
            source = validate_calendar_subscription(candidate_id)
        except ValueError as exc:
            raise ValidationError(str(exc), code="calendar_candidate_invalid") from exc
        if not source or not (source.startswith("eventkit:") or source.lower().startswith("https://")):
            raise ValidationError("Use it needs a calendar candidate id.", code="calendar_candidate_invalid")
        label = str((body or {}).get("label") or "").strip()
        if source.startswith("eventkit:"):
            if self._macos.access_state() != "full_access":
                raise ConflictError("HoldSpeak cannot read your calendars yet.", code="calendar_permission_required")
            match = next((c for c in self._macos.list_calendars() if f"eventkit:{c['id']}" == source), None)
            if match is None:
                raise NotFound("calendar", source)
            label = label or match["title"]
        else:
            label = label or str(urlsplit(source).hostname or "")
        existing = self._sources()
        for item in existing:
            if str(item.url) == source:
                return {"added": False, "source": _source_row(item)}
        sources = [
            {"id": s.id, "label": s.label, "url": s.url, "enabled": s.enabled} for s in existing
        ]
        sources.append({"label": label[:200], "url": source, "enabled": True})
        self._settings.update_settings(principal, {"calendar": {"sources": sources}})
        added = next((s for s in self._sources() if str(s.url) == source), None)
        if added is None:  # pragma: no cover - the write above raised instead
            raise ServiceError("calendar_source_not_saved", "The calendar was not saved.", context={"status": 500})
        _in_background(self._refresh)
        return {"added": True, "source": _source_row(added)}

    # ── connections ───────────────────────────────────────────────────

    def connections_detect(self, principal: Principal) -> dict[str, Any]:
        """Signed-in ``gh`` and ``acli`` accounts, from their files (no process, no network)."""
        candidates: list[dict[str, Any]] = []
        tools = self._connection_tools(principal)
        connected = self._connected_refs(principal, tools)
        # PHILO-15 B31: the GitHub row's state and time come from the one
        # Connections entry (a stored probe, else gh's sign-in file), so this
        # card and Settings › Connections never disagree.
        github = next((t for t in tools if t.get("provider_id") == "github"), {})
        github_login = str((github.get("account") or {}).get("login") or "")
        gh_path = gh_hosts_path(self._environ, self._home())
        gh_installed = self._which("gh") is not None
        for row in read_gh_accounts(gh_path):
            mine = row["active"] and github_login == _gh_account_ref(row["host"], row["login"])
            candidates.append({
                "state": str(github.get("state") or "") if mine else "",
                "checked_at": github.get("last_checked_at") if mine else None,
                "checked_by": github.get("checked_by") or ("probe" if github.get("last_checked_at") else None)
                if mine else None,
                "id": f"github:{row['host']}:{row['login']}",
                "provider": "github",
                "label": row["login"],
                "account": row["login"],
                "site": row["host"],
                "active": row["active"],
                # Connected only for the host and login the last probe named.
                "connected": row["active"] and ("github", _gh_account_ref(row["host"], row["login"])) in connected,
                "lamp": _lamp_for_host(row["host"]),
                "egress_host": row["host"],
                "verb": VERB if row["active"] and gh_installed else None,
            })
        acli_installed = self._which("acli") is not None
        acli_dir = self._home() / ".config" / "acli"
        for provider in ("jira", "confluence"):
            from .jira_provider import read_acli_profiles

            for row in read_acli_profiles(acli_dir / f"{provider}_config.yaml"):
                site = row["site"]
                candidates.append({
                    "id": f"{provider}:{row['ref']}",
                    "provider": provider,
                    "label": row["display_name"] or row["email"],
                    "account": row["email"],
                    "site": site,
                    "active": bool(row["current"]),
                    "connected": (provider, row["ref"]) in connected,
                    "lamp": _lamp_for_host(site.split("/")[0]),
                    "egress_host": site,
                    "verb": VERB if acli_installed else None,
                })
        return {
            "candidates": candidates,
            "tools": {
                "gh": {"installed": gh_installed, "detected_from": str(gh_path)},
                "acli": {"installed": acli_installed, "detected_from": str(acli_dir)},
            },
        }

    def _connection_tools(self, principal: Principal) -> list[dict[str, Any]]:
        """The Connections entries (stored reads only), or none when unreadable."""
        if self._connections is None:
            return []
        try:
            return list(self._connections.list_tools(principal).get("tools", []))
        except Exception as exc:
            log.debug("connections read failed: %s", exc)
            return []

    def _connected_refs(
        self, principal: Principal, tools: Optional[list[dict[str, Any]]] = None,
    ) -> set[tuple[str, str]]:
        """(provider, ref) pairs the connectors already hold as connected (stored rows only)."""
        refs: set[tuple[str, str]] = set()
        if tools is None:
            tools = self._connection_tools(principal)
        for tool in tools:
            provider = str(tool.get("provider_id") or "")
            if provider == "github" and tool.get("state") == "connected":
                login = str((tool.get("account") or {}).get("login") or "")
                if login:
                    refs.add(("github", login))
            for row in tool.get("connections") or []:
                if row.get("state") == "connected":
                    refs.add((provider, str(row.get("connection_ref") or "")))
        return refs

    def connections_use(self, principal: Principal, body: dict[str, Any]) -> dict[str, Any]:
        """The owner's "Use it": add the connector, run its status probe, return its entry."""
        if self._connections is None:
            raise ServiceError("onboarding_unavailable", "Connections are not available.", context={"status": 503})
        candidate_id = str((body or {}).get("id") or "").strip()
        match = next(
            (c for c in self.connections_detect(principal)["candidates"] if c["id"] == candidate_id), None,
        )
        if match is None:
            raise NotFound("connection candidate", candidate_id)
        if match["verb"] is None:
            code = "github_account_not_active" if match["provider"] == "github" and not match["active"] \
                else f"{'gh' if match['provider'] == 'github' else 'acli'}_not_installed"
            raise ConflictError("This account cannot be used from here.", code=code)
        provider = match["provider"]
        if provider == "github":
            # One host: `gh auth status --hostname <host>`; egress to that host.
            entry = self._connections.recheck(principal, "github", ref=match["site"])
            expected = _gh_account_ref(match["site"], match["account"])
            if entry.get("state") == "connected" and str((entry.get("account") or {}).get("login") or "") != expected:
                raise ConflictError(
                    "gh is signed in to this host as another account.", code="github_identity_changed",
                )
        else:
            adapter = self._jira if provider == "jira" else self._confluence
            if adapter is None:
                raise ServiceError("onboarding_unavailable", f"{provider} is not available.", context={"status": 503})
            adapter.add_connection(principal, match["site"], match["account"])
            ref = candidate_id.split(":", 1)[1]
            entry = self._connections.recheck(principal, provider, ref=ref)
        return {
            "candidate": match["id"], "provider": provider, "egress_host": match["egress_host"], "entry": entry,
        }


    # ── agents ────────────────────────────────────────────────────────

    def agents_detect(self, principal: Principal) -> dict[str, Any]:
        """Claude Code and Codex: on PATH, hooks installed and runnable, signed in; plus tmux (files only)."""
        return detect_agents(which=self._which, home=self._home(), environ=self._environ)

    def agent_settings_target(self, agent: str) -> Optional[str]:
        """The settings file the install for *agent* writes (``None`` for an unknown agent).

        The route binds it into the admitted operation's arguments BEFORE
        execution; :meth:`agents_use` writes only that file.
        """
        from ..agent_context.hooks import agent_settings_path

        if agent not in AGENTS:
            return None
        return str(agent_settings_path(agent, home=self._home(), env=self._env()))

    def _env(self) -> dict[str, str]:
        return dict(os.environ if self._environ is None else self._environ)

    # ── Conductor R7: the People MCP access (config) ─────────────────

    def people_access(self, principal: Principal, environ: Optional[dict[str, str]] = None) -> dict[str, Any]:
        """The effective People MCP access: ``{mode, source, effective, agents}``.

        ``mode`` is the persisted setting; ``effective`` what applies (the env
        var overrides); ``agents`` what a launched agent gets (read unless off)."""
        from ..config import Config
        from ..mcp.families.people import access_source

        _require_owner(principal)
        config = Config.load()
        from ..mcp.families.people import ACCESS_ENV

        effective, source = access_source(self._env() if environ is None else environ)
        return {
            "mode": str(config.people.mcp_access),
            "effective": effective,
            "source": source,
            # The variable that overrides the setting, named when it does.
            "env_var": ACCESS_ENV if source == "env" else None,
            "agents": "off" if effective == "off" else "read",
        }

    def people_access_set(self, principal: Principal, mode: str) -> dict[str, Any]:
        """``people_access.set``: the owner's press writes ``people.mcp_access``
        (admitted kernel operation, one receipt)."""
        from ..config import Config
        from ..config.people import ACCESS_MODES
        from . import project_kernel

        if project_kernel.current() is None:
            raise RuntimeError("people_access.set runs only as an admitted kernel operation")
        _require_owner(principal)
        value = str(mode or "").strip().lower()
        if value not in ACCESS_MODES:
            raise ValidationError("mode is off, read or write.", code="people_access_mode_unknown")
        from ..mcp.families.people import ACCESS_ENV, access_source

        if access_source(self._env())[1] == "env":
            # Owner ratification 2026-10-07 ("Of course it should, buddy!"): while
            # the variable overrides it, the setting does not change.
            raise ConflictError(f"{ACCESS_ENV} is set and overrides this setting.",
                                code="people_access_env_override", context={"env_var": ACCESS_ENV})
        config = Config.load()
        config.people.mcp_access = value
        config.save()
        return self.people_access(principal)

    def agents_use(self, principal: Principal, agent: str, settings_path: str) -> dict[str, Any]:
        """The owner's "Use it" (``agent_hooks.install``): install the HoldSpeak hooks for one agent.

        Runs only as the admitted kernel operation: the receipt names success,
        the refusal or the failure.  It writes exactly the file the operation
        bound at admission.
        """
        from ..agent_context.hooks import holdspeak_executable, install_agent_hooks
        from . import project_kernel

        if project_kernel.current() is None:
            raise RuntimeError("agent_hooks.install runs only as an admitted kernel operation")
        agent = str(agent or "").strip().lower()
        if agent not in AGENTS:
            raise ValidationError("Use it needs an agent: claude or codex.", code="agent_unknown")
        if self._which(agent) is None:
            raise ConflictError(f"{AGENTS[agent]} is not installed.", code=f"{agent}_not_installed")
        if settings_path != self.agent_settings_target(agent):
            raise ConflictError("The agent's settings file changed. Try again.", code="agent_settings_path_changed")
        if holdspeak_executable() is None:
            raise ConflictError("HoldSpeak cannot find its own command for the hook.", code="holdspeak_not_found")
        path = Path(settings_path)
        try:
            result = install_agent_hooks(path, agent_hook_template(agent))
        except ValueError as exc:
            raise ConflictError(
                f"HoldSpeak cannot read {path}. Fix the JSON and try again.", code="agent_settings_unreadable",
            ) from exc
        log.info("agent hooks installed for %s at %s (%s)", agent, path, ", ".join(result["installed_events"]))
        if agent == "codex":
            result = {**result, "trust": trust_codex_hooks(
                executable=str(self._which("codex")), env={**os.environ, **self._env()}, home=self._home(),
                hooks_json=path,
            )}
        return {**self.agents_detect(principal), "used": {"agent": agent, **result}}


def _require_owner(principal: Any) -> None:
    from ..principals import PrincipalKind

    if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
        raise ServiceError("owner_required", "Only the owner reads or sets People MCP access.",
                           context={"status": 403})


#: The coding agents the Conductor launches, by command name.
AGENTS: dict[str, str] = {"claude": "Claude Code", "codex": "Codex"}

TMUX_INSTALL_HINT = {
    "darwin": "brew install tmux",
    "linux": "sudo apt-get install tmux",
}


def codex_trust_stamp_path(home: Path) -> Path:
    return home / ".holdspeak" / "codex_hook_trust.json"


def trust_codex_hooks(
    *, executable: str, env: dict[str, str], home: Path, hooks_json: Optional[Path] = None,
) -> dict[str, Any]:
    """Codex runs a hook only when its user config trusts the hook's hash
    (``agent_context.codex_trust``). Inside ``agent_hooks.install`` only:
    trust HoldSpeak's installed rider hooks and the hooks every Codex launch
    passes, through Codex's own config writer: exactly those hooks (matched
    by source, position, event, matcher, command and timeout), trusted AND
    enabled, then listed again. A failure is named in the receipt; the hooks
    file stays written."""
    from .. import coder_gate
    from ..agent_context import codex_trust

    flags = coder_gate.codex_hook_flags(coder_gate.spawn_prefix())
    try:
        summary = codex_trust.trust_holdspeak_hooks(
            flags, cwd=str(home) if home.is_dir() else "/", executable=executable,
            env={**env, "HOME": str(home)}, hooks_json=hooks_json,
        )
    except codex_trust.CodexTrustError as exc:
        log.warning("codex hook trust failed: %s", exc)
        return {"state": "failed", "reason": exc.reason}
    if summary["untrusted"]:
        return {"state": "failed", "reason": "codex_hooks_untrusted", **summary}
    codex_trust.write_trust_stamp(flags, codex_trust_stamp_path(home))
    return {"state": "trusted", **summary}


def _codex_launch_hooks_stamped(home: Path) -> bool:
    """The install operation trusted the hooks a Codex launch passes now (no process)."""
    from .. import coder_gate
    from ..agent_context import codex_trust

    try:
        return codex_trust.trust_stamp_matches(
            coder_gate.codex_hook_flags(coder_gate.spawn_prefix()), codex_trust_stamp_path(home),
        )
    except Exception:
        return False


def agent_hook_template(agent: str) -> dict[str, Any]:
    """The hook template ``holdspeak agent-hook install`` writes for one agent (no message capture)."""
    from ..agent_context.hooks import claude_hook_template, codex_hook_template

    return claude_hook_template() if agent == "claude" else codex_hook_template()


def _hooks_state(path: Path, events: list[str], which: Callable[[str], Optional[str]]) -> str:
    """``installed``, ``partial``, ``missing``, ``unreadable``, or ``broken`` (our command cannot run)."""
    import json

    from ..agent_context.hooks import _is_our_hook_entry, hook_command_runs, our_hook_commands

    if not path.is_file():
        return "missing"
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "unreadable"
    if not isinstance(settings, dict):
        return "unreadable"
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return "missing"
    ours = [
        event for event in events
        if isinstance(hooks.get(event), list) and any(_is_our_hook_entry(e) for e in hooks[event])
    ]
    if not ours:
        return "missing"
    if not all(hook_command_runs(command, which=which) for command in our_hook_commands(settings)):
        return "broken"
    return "installed" if len(ours) == len(events) else "partial"


def _json_object(path: Path) -> dict[str, Any]:
    import json

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _filled(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _claude_signed_in(home: Path, env: dict[str, str]) -> tuple[str, Optional[str]]:
    """``yes`` only from a credential (the API key variable or a stored OAuth token); else ``unknown``.

    Claude Code on macOS keeps its token in the Keychain, and account
    metadata alone proves nothing, so the answer is never ``no``.
    """
    if _filled(env.get("ANTHROPIC_API_KEY")):
        return "yes", "ANTHROPIC_API_KEY"
    config_dir = Path(env["CLAUDE_CONFIG_DIR"]).expanduser() if _filled(env.get("CLAUDE_CONFIG_DIR")) \
        else home / ".claude"
    credentials = config_dir / ".credentials.json"
    oauth = _json_object(credentials).get("claudeAiOauth")
    if isinstance(oauth, dict) and (_filled(oauth.get("accessToken")) or _filled(oauth.get("refreshToken"))):
        return "yes", str(credentials)
    return "unknown", None


def _codex_signed_in(home: Path, env: dict[str, str]) -> tuple[str, Optional[str]]:
    """``yes`` only from a stored token or key in ``auth.json``; else ``unknown`` (Codex can use the keyring)."""
    codex_home = Path(env["CODEX_HOME"]).expanduser() if _filled(env.get("CODEX_HOME")) else home / ".codex"
    auth_file = codex_home / "auth.json"
    auth = _json_object(auth_file)
    tokens = auth.get("tokens")
    if _filled(auth.get("OPENAI_API_KEY")) or (
        isinstance(tokens, dict) and any(_filled(tokens.get(k)) for k in ("access_token", "refresh_token", "id_token"))
    ):
        return "yes", str(auth_file)
    return "unknown", None


def detect_agents(
    *,
    which: Callable[[str], Optional[str]] = shutil.which,
    home: Optional[Path] = None,
    environ: Optional[dict[str, str]] = None,
    platform: Optional[str] = None,
) -> dict[str, Any]:
    """Agent readiness, read only: one row per agent, plus tmux and the hook command's ``holdspeak``.

    Shared by ``agents_detect`` and ``holdspeak doctor``.  Runs no process,
    makes no network request, writes nothing, and reads no credential value
    out.  ``ready`` needs the agent on PATH and every event of our hook
    installed with a command that can run.
    """
    import shlex
    import sys

    from ..agent_context.hooks import _agent_hook_command, agent_settings_path, hook_command_runs

    root = home or Path.home()
    env = dict(os.environ if environ is None else environ)
    rows: list[dict[str, Any]] = []
    for agent, label in AGENTS.items():
        executable = which(agent)
        settings_path = agent_settings_path(agent, home=root, env=env)
        events = list(agent_hook_template(agent)["hooks"])
        hooks = _hooks_state(settings_path, events, which)
        if agent == "codex" and hooks == "installed" and not _codex_launch_hooks_stamped(root):
            # Codex runs no hook its config does not trust: the press trusts them.
            hooks = "untrusted"
        signed_in, signed_in_from = (_claude_signed_in if agent == "claude" else _codex_signed_in)(root, env)
        rows.append({
            "id": agent,
            "label": label,
            "installed": executable is not None,
            "path": executable,
            "hooks": hooks,
            "hooks_path": str(settings_path),
            "signed_in": signed_in,
            "signed_in_from": signed_in_from,
            "version": _version_of(executable),
            "ready": executable is not None and hooks == "installed",
            "verb": VERB if executable is not None else None,
        })
    tmux = which("tmux")
    system = platform or sys.platform
    command = _agent_hook_command("claude")
    hook_executable = shlex.split(command)[0]
    return {
        "agents": rows,
        "tmux": {
            "installed": tmux is not None,
            "path": tmux,
            "version": _version_of(tmux),
            "install_hint": None if tmux else TMUX_INSTALL_HINT.get(system, "Install tmux with your package manager"),
        },
        # The executable a hook installed now runs (install and detect resolve it the same way).
        "holdspeak": {
            "path": which("holdspeak"),
            "hook_executable": hook_executable,
            "hook_runs": hook_command_runs(command, which=which),
        },
    }


_VERSION_SEGMENT = re.compile(r"^v?(\d+\.\d+(?:\.\d+)?[a-z]?)(?:[-+_].*)?$")


def _version_of(executable: Optional[str]) -> Optional[str]:
    """The tool's version, read from where it is installed; ``None`` when no file says it.

    Runs no process: a versioned folder on the resolved path (Homebrew
    ``Cellar/tmux/3.5a``, Claude Code ``versions/2.1.4``, Codex
    ``releases/0.46.0-...``), after the ``package.json`` of an npm install."""
    import json

    if not executable:
        return None
    try:
        real = Path(executable).resolve()
    except OSError:
        return None
    # npm first: an nvm path holds the NODE version as a folder (v20.1.0).
    for parent in list(real.parents)[:3]:
        version = _json_object(parent / "package.json").get("version")
        if _filled(version):
            return str(version)
    for part in reversed(real.parts):
        match = _VERSION_SEGMENT.match(part)
        if match:
            return match.group(1)
    return None


def _gh_account_ref(host: str, login: str) -> str:
    """How the GitHub connector stores an account: ``login`` on github.com, else ``host:login``."""
    return login if host == "github.com" else f"{host}:{login}"


def _calendar_name(raw: bytes) -> str:
    try:
        from icalendar import Calendar

        return str(Calendar.from_ical(raw).get("X-WR-CALNAME") or "").strip()
    except Exception:
        return ""


def _source_row(source: Any) -> dict[str, Any]:
    from ..config.integrations import calendar_subscription_summary

    summary = calendar_subscription_summary(source.url)
    return {
        "id": source.id,
        "label": source.label,
        "url": source.url,
        "enabled": source.enabled,
        "kind": summary.get("kind"),
        "egress_host": summary.get("host") or None,
    }


def _in_background(fn: Callable[[], Any]) -> None:
    def _run() -> None:
        try:
            fn()
        except Exception as exc:
            log.info("calendar refresh after Use it failed: %s", exc)

    threading.Thread(target=_run, name="onboarding-calendar-refresh", daemon=True).start()


def _refresh_calendar_ingest() -> Any:
    from ..calendar_ingest_conductor import _conductor

    if _conductor is None:
        return False
    return _conductor.refresh()
