"""HS-169-02: The Streamlined Door — one-screen project creation.

Composes existing services (no new tables).  Two routes:
  POST /api/projects/door/count  — live snapshot counts
  POST /api/projects/door/preview — validate pasted sources and find local material
  POST /api/projects/door         — one-call project + watches

The count path builds the SAME stored query shape and runs the SAME
WatchSource.snapshot the evaluation path uses.  Parity is tested in
tests/unit/test_hs169_door.py.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from holdspeak.principals import Principal
from holdspeak.redaction import redact_error
from holdspeak.services.errors import ServiceError, ValidationError

DOOR_DEFAULTS: dict[str, list[dict[str, Any]]] = {
    "github": [
        {"key": "open_prs", "label": "OPEN PRS", "template_id": "watch.github.review_queue", "on": True},
        {"key": "ci", "label": "CI", "template_id": "watch.github.branch_ci", "on": True},
    ],
    "jira": [
        {"key": "overdue", "label": "OVERDUE", "template_id": "watch.jira.due_risk", "on": True},
        {"key": "due_7_days", "label": "DUE 7 DAYS", "template_id": "watch.jira.delivery_flow", "on": True},
        {"key": "blocked", "label": "BLOCKED", "template_id": "watch.jira.blockers", "on": False},
    ],
    "confluence": [
        {"key": "recent_blogs", "label": "RECENT BLOGS", "template_id": "watch.confluence.recent_blogs", "on": True},
        {"key": "pages_by_id", "label": "PAGES BY ID", "template_id": "watch.confluence.pages_by_id", "on": False},
    ],
}

_DEFAULTS_BY_KEY: dict[str, dict[str, Any]] = {}
for _provider_rows in DOOR_DEFAULTS.values():
    for _row in _provider_rows:
        _DEFAULTS_BY_KEY[_row["key"]] = _row


_GITHUB_SOURCE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*)(?:[/?#].*)?$",
    re.IGNORECASE,
)
_JIRA_SOURCE_RE = re.compile(
    r"(?:https?://)?(?P<site>[^/\s]+)/(?:browse|projects|plugins/servlet/project-config)/([A-Z][A-Z0-9]+)(?:-\d+)?(?:[/?#].*)?$",
    re.IGNORECASE,
)
_JIRA_KEY_RE = re.compile(r"^([A-Z][A-Z0-9]+)(?:-\d+)?$", re.IGNORECASE)
_CONFLUENCE_SOURCE_RE = re.compile(
    r"(?:https?://)?(?P<site>[^/\s]+)/(?:wiki/)?spaces/([A-Za-z0-9_-]+)(?:[/?#].*)?$",
    re.IGNORECASE,
)


def _normalise_source_site(value: str) -> str:
    """Return the URL host used to bind a pasted Atlassian source."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    return (parsed.hostname or "").strip().rstrip(".").lower()


def parse_source_text(text: str) -> list[dict[str, Any]]:
    """Parse the links and keys a person pastes into the project Door.

    Parsing is deliberately local and side-effect free.  Provider adapters
    validate the returned rows separately, so an unconfigured provider can be
    shown as ``not checked`` without claiming that the source is valid.
    """
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for token in re.split(r"[\s,;]+", str(text or "").strip()):
        token = token.strip().strip("<>()[]{}")
        if not token:
            continue
        provider = ""
        scope: Any = None
        site = ""
        label = token
        match = _GITHUB_SOURCE_RE.match(token)
        if match:
            provider, scope = "github", match.group(1)
            label = scope
        else:
            match = _CONFLUENCE_SOURCE_RE.match(token)
            if match:
                provider, scope = "confluence", match.group(2)
                site = _normalise_source_site(match.group("site"))
                label = f"Confluence {site} · {scope}" if site else f"Confluence {scope}"
            else:
                match = _JIRA_SOURCE_RE.match(token)
                if match and ("/" in token or token.lower().startswith(("http://", "https://"))):
                    provider, scope = "jira", match.group(2).upper()
                    site = _normalise_source_site(match.group("site"))
                    label = f"Jira {site} · {scope}" if site else f"Jira {scope}"
                else:
                    match = _JIRA_KEY_RE.match(token)
                    if match:
                        provider, scope = "jira", match.group(1).upper()
                        label = f"Jira {scope}"
        if not provider or scope is None or (provider, site, str(scope).lower()) in seen:
            continue
        seen.add((provider, site, str(scope).lower()))
        rows.append({
            "provider": provider,
            "scope": scope,
            "site": site or None,
            "label": label,
            "state": "not_checked",
            "reason": None,
        })
    return rows


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _egress_host(provider: str, scope: Any) -> str:
    if provider == "github":
        return "GITHUB.COM"
    if provider in ("jira", "confluence") and isinstance(scope, dict):
        ref = str(scope.get("connection_ref") or "")
        site = ref.split("|")[0].strip() if "|" in ref else ref
        if site:
            return site.upper()
    return ""


def _flatten_github_query(spec: dict[str, Any]) -> dict[str, Any]:
    """Flatten a compiled GitHub WatchSpec into the stored query shape
    that create_from_setup uses (project_service.py ~L630)."""
    subject = spec.get("subject", {})
    query = dict(subject.get("query", {}))
    repos = subject.get("scope", {}).get("repositories", [])
    if repos:
        query["repository"] = repos[0]
    return query


def _flatten_jira_query(spec: dict[str, Any]) -> dict[str, Any]:
    """Flatten a compiled Jira WatchSpec into the stored query shape
    that create_from_setup uses (project_service.py ~L636)."""
    subject = spec.get("subject", {})
    query = dict(subject.get("query", {}))
    scope = subject.get("scope", {})
    conn_ref = scope.get("connection_ref") or spec.get("provider", {}).get("connection_ref")
    if conn_ref:
        query["connection_ref"] = conn_ref
    projects = scope.get("projects", [])
    if projects:
        query["projects"] = list(projects)
    issue_types = scope.get("issue_types", [])
    if issue_types:
        query["issue_types"] = list(issue_types)
    return query


def _ci_label(entities: list[dict[str, Any]]) -> str:
    """Derive a CI label from branch_ci snapshot entities."""
    if not entities:
        return "CI —"
    conclusion = entities[0].get("conclusion")
    if conclusion == "success":
        return "CI green"
    if conclusion in ("failure", "timed_out", "cancelled"):
        return "CI red"
    status = entities[0].get("status")
    if status == "in_progress":
        return "CI running"
    return "CI —"


def _count_label(key: str, count: int, entities: list[dict[str, Any]]) -> str:
    if key == "ci":
        return _ci_label(entities)
    labels: dict[str, str] = {
        "open_prs": "open PRs",
        "overdue": "overdue",
        "due_7_days": "due this week",
        "blocked": "blocked",
    }
    suffix = labels.get(key, key)
    return f"{count} {suffix}"


class ProjectDoorService:
    def __init__(
        self,
        *,
        project_service: Any = None,
        watch_service: Any = None,
        gh_runner: Any = None,
        github_adapter: Any = None,
        jira_adapter: Any = None,
        confluence_adapter: Any = None,
        db: Any = None,
        meeting_service: Any = None,
        primitive_service: Any = None,
    ) -> None:
        self._project_service = project_service
        self._watch_service = watch_service
        self._gh_runner = gh_runner
        self._github_adapter = github_adapter
        self._jira_adapter = jira_adapter
        self._confluence_adapter = confluence_adapter
        self._db = db
        self._meeting_service = meeting_service
        self._primitive_service = primitive_service

    def preview(self, principal: Principal, outcome: str = "", pasted: str = "") -> dict[str, Any]:
        """Return parsed sources and local material for the Door.

        The read is bounded and truthful: provider rows say ``not checked``
        until their existing validator can answer, while meetings and notes
        come from the hub's actual stores.
        """
        sources = parse_source_text(pasted)
        for row in sources:
            row.update(self._validate_source(principal, row))
        words = [w.lower() for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}", str(outcome or ""))]
        meetings: list[dict[str, Any]] = []
        if self._meeting_service is not None:
            try:
                for query in (str(outcome or "").strip(), *words):
                    if not query:
                        continue
                    answer = self._meeting_service.list_meetings(principal, query=query, limit=50)
                    for meeting in answer.get("meetings", []):
                        if meeting.get("id") not in {m.get("id") for m in meetings}:
                            meetings.append({
                                "kind": "meeting", "id": str(meeting.get("id", "")),
                                "title": str(meeting.get("title", "")),
                                "detail": str(meeting.get("started_at", ""))[:10],
                                "attendees": list(meeting.get("attendees") or []),
                                "selected": True,
                            })
            except Exception:
                meetings = []
        notes: list[dict[str, Any]] = []
        if self._primitive_service is not None or self._db is not None:
            try:
                note_rows = (
                    self._primitive_service.list_notes(principal)
                    if self._primitive_service is not None
                    else [note.to_dict() for note in self._db.notes.list()]
                )
                for note in note_rows:
                    haystack = f"{note.get('title', '')} {note.get('body_markdown', '')}".lower()
                    if words and any(word in haystack for word in words):
                        notes.append({
                            "kind": "note", "id": str(note.get("id", "")),
                            "title": str(note.get("title", "") or "Untitled note"),
                            "detail": "Note", "selected": True,
                        })
            except Exception:
                notes = []
        people_set = {
            str(name).strip()
            for meeting in meetings
            for name in meeting.get("attendees", [])
            if str(name).strip()
        }
        # Meeting list summaries carry calendar attendees, while the Room's
        # People line is grounded in the speakers of the matched meetings.
        # Read the existing meeting store for those speakers when the hub has
        # one; a provider or partial composition still keeps its truthful
        # attendee projection above.
        if self._db is not None:
            for meeting in meetings:
                try:
                    stored = self._db.meetings.get_meeting(str(meeting.get("id", "")))
                    people_set.update(
                        str(segment.speaker).strip()
                        for segment in (stored.segments if stored is not None else [])
                        if str(segment.speaker).strip()
                    )
                except Exception:
                    continue
        people = sorted(people_set)
        return {"sources": sources, "found": [*meetings, *notes], "people": people}

    def _validate_source(self, principal: Principal, row: dict[str, Any]) -> dict[str, Any]:
        provider, scope = row.get("provider"), row.get("scope")
        ref = ""
        try:
            if provider == "github" and self._github_adapter is not None:
                result = self._github_adapter.validate_repo(principal, str(scope))
            elif provider == "jira" and self._jira_adapter is not None:
                ref, reason = self._resolve_connection("jira", row.get("site"))
                if not ref:
                    return {"state": "not_checked", "reason": reason}
                result = self._jira_adapter.validate_scope(principal, ref, str(scope))
            elif provider == "confluence" and self._confluence_adapter is not None:
                ref, reason = self._resolve_connection("confluence", row.get("site"))
                if not ref:
                    return {"state": "not_checked", "reason": reason}
                result = self._confluence_adapter.validate_scope(principal, ref, str(scope))
            else:
                return {"state": "not_checked", "reason": None}
            valid = bool(result.get("valid")) if isinstance(result, dict) else False
            answer = {
                "state": "checked" if valid else "cant_check",
                "reason": None if valid else str((result or {}).get("error_detail") or (result or {}).get("message") or "Could not check"),
            }
            if provider in {"jira", "confluence"} and ref:
                answer["connection_ref"] = ref
            if isinstance(result, dict):
                if result.get("connection_ref") and "connection_ref" not in answer:
                    answer["connection_ref"] = str(result["connection_ref"])
                space = result.get("space")
                if isinstance(space, dict) and space.get("id"):
                    answer["space_id"] = str(space["id"])
            return answer
        except Exception as exc:
            return {"state": "cant_check", "reason": str(exc)[:300]}

    def _resolve_connection(self, provider: str, site: Any) -> tuple[str, str]:
        """Choose the one connected account bound to a pasted site.

        A bare key is safe only when one connected account exists.  A URL is
        safe only when its host matches exactly; account order never decides
        which site receives provider validation.
        """
        connections = self._db.automations.list_provider_connections(provider_id=provider) if self._db else []
        refs = [
            str(c.get("external_connection_ref") or c.get("connection_ref") or "").strip()
            for c in connections
            if c.get("state") == "connected"
        ]
        refs = [ref for ref in refs if ref]
        requested_site = _normalise_source_site(str(site or ""))

        def ref_site(ref: str) -> str:
            return _normalise_source_site(ref.split("|", 1)[0])

        if requested_site:
            matches = [ref for ref in refs if ref_site(ref) == requested_site]
            if len(matches) == 1:
                return matches[0], ""
            if len(matches) > 1:
                return "", f"Ambiguous account for {requested_site}: Check one account"
            return "", f"Not signed in on {requested_site}: Connect or Check this account"
        if len(refs) == 1:
            return refs[0], ""
        if not refs:
            return "", "Not signed in on this Mac"
        return "", "Ambiguous account: paste a site URL or Check one account"

    def count(
        self,
        principal: Principal,
        provider: str,
        scope: Any,
        watches: list[str],
        adjust: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        host = _egress_host(provider, scope)
        now = _iso_now()
        adjust = adjust or {}

        try:
            tokens: list[dict[str, Any]] = []
            for key in watches:
                default = _DEFAULTS_BY_KEY.get(key)
                if not default:
                    continue
                entities = self._snapshot_for_key(
                    principal, provider, scope, key, default["template_id"], adjust,
                )
                count = len(entities)
                label = _count_label(key, count, entities)
                tokens.append({"key": key, "label": label, "count": count})

            # No counter of zero (UX-CANON; Astra on #1000): a zero count is
            # left out of the line ("0 open PRs" was said); its token stays.
            plain = " · ".join(t["label"] for t in tokens if t["key"] == "ci" or t["count"])
            return {
                "tokens": tokens,
                "plain": plain,
                "checkedAt": now,
                "host": host,
                "state": "live",
                "reason": None,
            }
        except ServiceError as exc:
            return {
                "tokens": [],
                "plain": "",
                "checkedAt": now,
                "host": host,
                "state": "cant_check",
                "reason": str(exc.detail)[:500],
            }
        except Exception as exc:
            return {
                "tokens": [],
                "plain": "",
                "checkedAt": now,
                "host": host,
                "state": "cant_check",
                "reason": str(exc)[:500],
            }

    def _snapshot_for_key(
        self,
        principal: Principal,
        provider: str,
        scope: Any,
        key: str,
        template_id: str,
        adjust: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Run the snapshot for one door default using the SAME path
        that evaluation uses."""
        from holdspeak.services.watch_sources import (
            GitHubWatchSource,
            JiraWatchSource,
        )

        if provider == "github":
            repo = str(scope) if isinstance(scope, str) else ""
            if key == "ci":
                spec = self._compile_ci_watch(repo, adjust)
                stored_query = _flatten_github_query(spec)
                return GitHubWatchSource(runner=self._gh_runner).snapshot(
                    principal, query_kind="branch_ci", query=stored_query,
                )
            spec = self._compile_github(template_id, repo, adjust)
            stored_query = _flatten_github_query(spec)
            return GitHubWatchSource(runner=self._gh_runner).snapshot(
                principal, query_kind="pull_requests", query=stored_query,
            )

        if provider == "jira":
            jira_scope = scope if isinstance(scope, dict) else {}
            spec = self._compile_jira(template_id, jira_scope, adjust)
            stored_query = _flatten_jira_query(spec)
            return JiraWatchSource(adapter=self._jira_adapter).snapshot(
                principal, query_kind="issues", query=stored_query,
            )

        if provider == "confluence":
            from holdspeak.services.watch_sources import ConfluenceWatchSource

            scope_dict = scope if isinstance(scope, dict) else {"space_key": str(scope)}
            spec = self._compile_confluence(template_id, scope_dict, adjust)
            stored_query = dict(spec.get("subject", {}).get("query", {}))
            return ConfluenceWatchSource(adapter=self._confluence_adapter).snapshot(
                principal, query_kind=str(spec.get("subject", {}).get("kind") or "recent_blogs"), query=stored_query,
            )

        raise ServiceError("unknown_provider", f"Unknown provider: {provider}")

    def _compile_github(
        self,
        template_id: str,
        repo: str,
        adjust: dict[str, Any],
    ) -> dict[str, Any]:
        from holdspeak import github_templates
        options: dict[str, Any] = {}
        if "base" in adjust:
            options["base"] = adjust["base"]
        if "labels" in adjust:
            options["labels"] = adjust["labels"]
        return github_templates.compile(template_id, repo, options)

    def _compile_jira(
        self,
        template_id: str,
        scope: dict[str, Any],
        adjust: dict[str, Any],
    ) -> dict[str, Any]:
        from holdspeak import jira_templates
        connection_ref = str(scope.get("connection_ref") or "").strip()
        if not connection_ref:
            raise ValidationError("Check the Jira account for this source before creating it")
        site_scope = {
            "connection_ref": connection_ref,
            "projects": scope.get("projects", []),
            "issue_types": adjust.get("issueTypes", []),
        }
        spec = jira_templates.compile(template_id, site_scope)
        if adjust.get("jql"):
            spec["subject"]["query"]["jql"] = adjust["jql"]
        return spec

    def _compile_confluence(
        self,
        template_id: str,
        scope: dict[str, Any],
        adjust: dict[str, Any],
    ) -> dict[str, Any]:
        from holdspeak import confluence_templates

        connection_ref = str(scope.get("connection_ref") or "").strip()
        if not connection_ref:
            raise ValidationError("Check the Confluence account for this source before creating it")

        site_scope = {
            "connection_ref": connection_ref,
            "space_key": scope.get("space_key") or scope.get("key") or "",
            "space_id": scope.get("space_id") or scope.get("space_key") or scope.get("key") or "",
            "page_ids": scope.get("page_ids") or [],
        }
        return confluence_templates.compile(template_id, site_scope, adjust)

    def create(
        self,
        principal: Principal,
        outcome: str = "",
        sources: list[dict[str, Any]] | None = None,
        project_id: str | None = None,
        found: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sources = sources or []
        if project_id:
            return self.add_sources(principal, project_id, sources, found=found)
        if not str(outcome or "").strip():
            raise ValidationError("outcome is required")
        if self._project_service is None:
            raise ServiceError(
                "project_service_missing",
                "ProjectDoorService requires a composed ProjectService",
            )

        name = (outcome[:80]).strip() or "New Project"

        proposals = []
        for spec, test_state in self._specs_with_state(sources):
            # The setup service receives only the spec. Carry the validation
            # result inside it so an unchecked paste cannot become a passed
            # watch when the project is created.
            spec = {**spec, "test_state": test_state}
            proposals.append({
                "id": f"door_{uuid.uuid4().hex[:12]}",
                "spec": spec,
                "state": "selected",
                "test_state": test_state,
            })

        setup_payload = {
            "name": name,
            "purpose": outcome,
            "outcome_text": outcome,
            "lifecycle": "active",
            "proposals": proposals,
            "session_id": None,
        }

        cmd_id = f"pcmd_{uuid.uuid4().hex[:12]}"
        result = self._project_service.create_from_setup(
            principal, setup_payload, command_id=cmd_id,
        )

        self._baseline(principal, result.get("activated_watches", []))
        found_links = self._link_found(principal, str(result.get("project_id", "")), found or {})
        return {"projectId": result.get("project_id", ""), "found_links": found_links}

    @staticmethod
    def _found_rows(found: dict[str, Any] | None) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for kind, field in (("meeting", "meeting_ids"), ("note", "note_ids")):
            values = found.get(field, []) if isinstance(found, dict) else []
            if not isinstance(values, list):
                continue
            for value in values:
                item_id = str(value or "").strip()
                if item_id:
                    rows.append((kind, item_id))
        return rows

    def _found_link_readback(self, project_id: str, kind: str, item_id: str) -> None:
        """Confirm the leaf wrote its durable project relationship."""
        if self._db is None:
            return
        resource_ref = f"{kind}:{item_id}"
        try:
            with self._db._connection() as conn:
                row = conn.execute(
                    "SELECT 1 FROM project_resources WHERE project_id=? AND resource_ref=? AND deleted=0",
                    (project_id, resource_ref),
                ).fetchone()
        except Exception as exc:
            raise ServiceError("link_readback_failed", redact_error(str(exc), limit=500)) from exc
        if row is None:
            raise ServiceError("link_not_persisted", f"{kind.title()} link was not persisted")

    def _link_found(self, principal: Principal, project_id: str, found: dict[str, Any]) -> list[dict[str, Any]]:
        """Link each selected meeting/note and report every leaf outcome."""
        results: list[dict[str, Any]] = []
        rows = self._found_rows(found)
        if not rows:
            return results
        if not project_id or self._project_service is None:
            return [
                {"kind": kind, "id": item_id, "state": "failed", "error": "Project link service unavailable"}
                for kind, item_id in rows
            ]
        for kind, item_id in rows:
            error: str | None = None
            try:
                if kind == "meeting":
                    linked = self._project_service.associate_meeting(principal, project_id, item_id)
                else:
                    linked = self._project_service.add_resource(
                        principal, project_id, f"note:{item_id}", relationship="member",
                    )
                if linked is False:
                    raise ServiceError("link_failed", f"Could not add {kind} {item_id}")
                self._found_link_readback(project_id, kind, item_id)
            except ServiceError as exc:
                error = redact_error(exc.detail or str(exc), limit=500) or f"Could not add {kind}"
            except Exception as exc:
                error = redact_error(str(exc), limit=500) or f"Could not add {kind}"
            results.append({
                "kind": kind,
                "id": item_id,
                "state": "failed" if error else "linked",
                "error": error,
            })
        return results

    def add_sources(
        self,
        principal: Principal,
        project_id: str,
        sources: list[dict[str, Any]],
        found: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """PHILO-17 U10: the Door's source rows, added to a project that exists.

        The same specs ``create`` arms, through ``ProjectService.add_source_watches``.
        """
        if self._project_service is None:
            raise ServiceError(
                "project_service_missing",
                "ProjectDoorService requires a composed ProjectService",
            )
        specs = self._specs(sources)
        found_rows = self._found_rows(found)
        if not specs and not found_rows:
            raise ValidationError("Choose a source to add")
        activated: list[Any] = []
        if specs:
            result = self._project_service.add_source_watches(principal, project_id, specs)
            activated = result.get("activated_watches", [])
            self._baseline(principal, activated)
        return {
            "projectId": project_id,
            "watches": len(activated),
            "found_links": self._link_found(principal, project_id, found or {}),
        }

    def _specs(self, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Each GitHub or Jira source row compiled to its watch specs."""
        return [spec for spec, _ in self._specs_with_state(sources)]

    def _specs_with_state(self, sources: list[dict[str, Any]]) -> list[tuple[dict[str, Any], str]]:
        specs: list[tuple[dict[str, Any], str]] = []
        for source in sources or []:
            provider = source.get("provider", "")
            scope = source.get("scope")
            adjust = source.get("adjust") or {}
            test_state = "passed" if source.get("test_state") == "passed" else "not_checked"
            for key in source.get("watches", []):
                default = _DEFAULTS_BY_KEY.get(key)
                if not default:
                    continue
                template_id = default["template_id"]
                if provider == "github":
                    repo = str(scope) if isinstance(scope, str) else ""
                    if key == "ci":
                        specs.append((self._compile_ci_watch(repo, adjust), test_state))
                    else:
                        specs.append((self._compile_github(template_id, repo, adjust), test_state))
                    if key == "open_prs":
                        # Conductor R4: the open issues ride with the PR queue
                        # (no toggle of their own), so a Room's GitHub issue
                        # rows work out of the box.
                        specs.append((self._compile_github("watch.github.open_issues", repo, {}), test_state))
                elif provider == "jira":
                    jira_scope = scope if isinstance(scope, dict) else {}
                    specs.append((self._compile_jira(template_id, jira_scope, adjust), test_state))
                elif provider == "confluence":
                    confluence_scope = scope if isinstance(scope, dict) else {"space_key": str(scope)}
                    specs.append((self._compile_confluence(template_id, confluence_scope, adjust), test_state))
        return specs

    def _baseline(self, principal: Principal, activated: list[dict[str, Any]]) -> None:
        """Each armed watch takes its baseline read now (or is marked pending)."""
        if self._watch_service is None:
            return
        for aw in activated:
            wid = aw.get("watch_id", "")
            if not wid:
                continue
            try:
                self._watch_service.baseline_watch(principal, wid)
            except Exception:
                try:
                    self._watch_service._repo.update_watch_spec(
                        wid, baseline_state="pending",
                    )
                except Exception:
                    pass

    def _compile_ci_watch(
        self,
        repo: str,
        adjust: dict[str, Any],
    ) -> dict[str, Any]:
        """Compile the CI Watch spec using branch_ci query kind.

        Uses the branch_ci template from github_templates but overrides
        subject.kind to "branch_ci" (the generic compile hard-codes
        "pull_request"; branch_ci needs its own kind for query routing).
        """
        from holdspeak import github_templates
        options: dict[str, Any] = {}
        if "base" in adjust:
            options["base"] = adjust["base"]
        spec = github_templates.compile("watch.github.branch_ci", repo, options)
        spec["subject"]["kind"] = "branch_ci"
        return spec
