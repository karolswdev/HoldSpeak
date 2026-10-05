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
"""
from __future__ import annotations

import ipaddress
import os
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
        connected = self._connected_refs(principal)
        gh_path = gh_hosts_path(self._environ, self._home())
        gh_installed = self._which("gh") is not None
        for row in read_gh_accounts(gh_path):
            candidates.append({
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

    def _connected_refs(self, principal: Principal) -> set[tuple[str, str]]:
        """(provider, ref) pairs the connectors already hold as connected (stored rows only)."""
        refs: set[tuple[str, str]] = set()
        if self._connections is None:
            return refs
        try:
            tools = self._connections.list_tools(principal).get("tools", [])
        except Exception as exc:
            log.debug("connections read failed: %s", exc)
            return refs
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
