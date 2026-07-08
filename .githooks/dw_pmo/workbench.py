"""The local workbench server: JSON API + static explorer shell.

Read-only in this slice (WLA-5-03): every response is derived live from
the Markdown roadmap through the same ``dw_pmo`` functions the CLI
uses — no second parser, no cache, no database, and no writes. The
server binds 127.0.0.1 only and serves exactly the repo root it was
started against. Non-GET methods are rejected; the file endpoint is
contained to the roadmap tree; static assets are contained to the
workbench directory.

Route logic lives in :func:`handle_api` (pure: path + query in,
status + envelope out) so view models are unit-testable without
sockets. Mutation endpoints arrive with WLA-5-06/07.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .api import build_context_payload, handoff_summary, next_story, phase_events, project_context, story_timeline
from .model import DwError, OPEN_STATUSES, normalize_status
from .parse import discover_phases, discover_projects, get_phase, get_project, parse_story_rows
from .paths import read_text, rel, roadmap_dir, work_log_root
from .mutations import (
    apply_plan,
    plan_fingerprint,
    plan_phase_close,
    plan_phase_create,
    plan_story_create,
    plan_story_evidence,
    plan_story_status,
    preview_plan,
    projected_issues,
)
from .validate import check_project, health_report, project_warnings

SCHEMA_KIND = "delivery-workbench-workbench-response"
SCHEMA_VERSION = 1

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
}


def workbench_dir() -> Path | None:
    """The static UI directory.

    Source layout: pmo-roadmap/lib/dw_pmo -> pmo-roadmap/workbench.
    Installed layout: .githooks/dw_pmo -> .githooks/workbench.
    """
    here = Path(__file__).resolve()
    for candidate in (here.parents[1] / "workbench", here.parents[2] / "workbench"):
        if (candidate / "index.html").is_file():
            return candidate
    return None


def host_allowed(host_header: str) -> bool:
    """Default-deny for non-local Host headers (DNS-rebinding guard).

    A ``*.ts.net`` host (Tailscale's MagicDNS suffix) is also allowed:
    unlike an arbitrary attacker-chosen domain, a ``.ts.net`` name can
    only resolve and route to this process through the requester's
    own authenticated tailnet (WireGuard-encrypted, node-identified)
    via ``tailscale serve`` proxying to this same loopback port — the
    DNS-rebinding threat this guard exists to stop (a hostile page
    tricking a browser into sending a forged Host header at a
    public IP) has no way to reach this branch at all. Owner
    decision: the workbench is "localhost or your own tailnet,"
    not "localhost only."
    """
    raw = (host_header or "").strip().lower()
    if raw.startswith("["):  # bracketed IPv6, e.g. [::1]:8377
        host = raw.split("]")[0].lstrip("[")
    else:
        host = raw.split(":")[0]
    return host in {"127.0.0.1", "localhost", "::1", ""} or host.endswith(".ts.net")


def envelope(data: object, ok: bool = True, issues: list[str] | None = None, warnings: list[str] | None = None) -> dict[str, object]:
    return {
        "kind": SCHEMA_KIND,
        "schema_version": SCHEMA_VERSION,
        "ok": ok,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": data,
        "issues": issues or [],
        "warnings": warnings or [],
    }


def _error(status: int, message: str) -> tuple[int, dict[str, object]]:
    return status, envelope({"error": message}, ok=False, issues=[message])


def _project_summary(project, root: Path) -> dict[str, object]:
    phases = discover_phases(project)
    active = 0
    status_counts: dict[str, int] = {}
    for phase in phases:
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        if any(normalize_status(row.status) in OPEN_STATUSES for row in rows):
            active += 1
        for row in rows:
            token = normalize_status(row.status)
            status_counts[token] = status_counts.get(token, 0) + 1
    issues = check_project(project, root)
    warnings = project_warnings(project, root)
    return {
        "slug": project.slug,
        "prefix": project.prefix,
        "path": rel(project.path, root),
        "phase_count": len(phases),
        "active_phase_count": active,
        "story_status_counts": status_counts,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "next_story": next_story(project, root),
    }


def _contained_read(root: Path, raw_path: str) -> tuple[int, dict[str, object]]:
    """Read a file strictly inside the roadmap tree (traversal-proof)."""
    if not raw_path:
        return _error(400, "missing path parameter")
    allowed = roadmap_dir(root).resolve()
    target = (root / raw_path).resolve()
    if target != allowed and allowed not in target.parents:
        return _error(403, f"path is outside the roadmap tree: {raw_path}")
    if not target.is_file():
        return _error(404, f"no such file: {raw_path}")
    return 200, envelope({"path": rel(target, root), "content": read_text(target)})



def _worklog_read(root: Path, raw_path: str) -> tuple[int, dict[str, object]]:
    """Read a work-log artifact strictly inside the resolved log root.

    Only the capture/digest naming patterns are served; the log content
    is returned verbatim — omitted paths stay omitted because capture
    never wrote their content in the first place."""
    if not raw_path:
        return _error(400, "missing path parameter")
    log_root = work_log_root(root).resolve()
    if not log_root.is_dir():
        return _error(404, "no work-log root exists (work logs are optional evidence)")
    # Hash routers drop the leading slash of absolute paths; accept the
    # path as given, rooted at /, or relative to the log root — but only
    # ever serve from inside the log root.
    candidates = [Path(raw_path)] if Path(raw_path).is_absolute() else [
        Path("/" + raw_path),
        log_root / raw_path,
    ]
    target = None
    for candidate in candidates:
        resolved = candidate.resolve()
        if log_root in resolved.parents:
            target = resolved
            if resolved.is_file():
                break
    if target is None:
        return _error(403, f"path is outside the work-log root: {raw_path}")
    if not (target.name.endswith("-work-summary.log") or target.name.endswith("-deferred-summary.md")):
        return _error(403, f"not a work-log artifact: {target.name}")
    if not target.is_file():
        return _error(404, f"no such work-log entry: {raw_path}")
    return 200, envelope({"path": str(target), "content": read_text(target)})

def mission_control_live_layer(sessions_doc: dict) -> tuple[dict, list]:
    """The belt's live-layer decision kernel (WLA-15-02), server-side
    so it is testable here: `on_story` sessions pin to their story
    ids; every other correlation outcome stays off the belt in its
    honest bucket — ambiguous never guesses a pin (unknown beats
    guessed, the §2 rule). Returns (pins: story_id -> [session],
    off_belt: [session])."""
    pins: dict[str, list] = {}
    off_belt: list = []
    for session in sessions_doc.get("sessions") or []:
        stories = session.get("stories") or []
        if session.get("correlation") == "on_story" and stories:
            for story in stories:
                pins.setdefault(str(story.get("story_id")), []).append(session)
        else:
            off_belt.append(session)
    return pins, off_belt


def handle_api(root: Path, path: str, query: dict[str, list[str]]) -> tuple[int, dict[str, object]]:
    parts = [part for part in path.strip("/").split("/") if part]
    try:
        if parts == ["api", "context"]:
            include_trace = query.get("trace", ["0"])[0] in {"1", "true"}
            payload = build_context_payload(root, discover_projects(root), include_trace=include_trace)
            return 200, envelope(payload)

        if parts == ["api", "projects"]:
            summaries = [_project_summary(p, root) for p in discover_projects(root)]
            return 200, envelope({"projects": summaries})

        if len(parts) == 3 and parts[:2] == ["api", "projects"]:
            project = get_project(root, parts[2])
            return 200, envelope(project_context(project, root))

        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "phases":
            project = get_project(root, parts[2])
            context = project_context(project, root, phase_selector=parts[4])
            phase = context["phases"][0]  # type: ignore[index]
            summary_path = root / str(phase["final_summary"])  # type: ignore[index]
            detail = dict(phase)
            detail["final_summary_content"] = (
                read_text(summary_path) if summary_path.is_file() else ""
            )
            return 200, envelope(detail)

        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "stories":
            project = get_project(root, parts[2])
            context = project_context(project, root)
            for phase in context["phases"]:  # type: ignore[union-attr]
                for story in phase["stories"]:
                    if story["story_id"] == parts[4]:
                        detail = dict(story)
                        story_path = root / str(story["story_path"])
                        detail["story_markdown"] = read_text(story_path) if story_path.is_file() else ""
                        evidence_rel = str(story["evidence_path"])
                        evidence_path = root / evidence_rel if evidence_rel else None
                        detail["evidence_markdown"] = (
                            read_text(evidence_path) if evidence_path and evidence_path.is_file() else ""
                        )
                        detail["phase_number"] = phase["number"]
                        return 200, envelope(detail)
            return _error(404, f"story not found: {parts[4]}")

        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "trace":
            project = get_project(root, parts[2])
            for phase in discover_phases(project):
                for row in parse_story_rows(phase.path / "current-phase-status.md"):
                    if row.story_id == parts[4]:
                        return 200, envelope(story_timeline(row, phase, project, root))
            return _error(404, f"story not found: {parts[4]}")

        if len(parts) == 6 and parts[:2] == ["api", "projects"] and parts[3] == "phases" and parts[5] == "events":
            project = get_project(root, parts[2])
            phase = get_phase(project, parts[4])
            return 200, envelope({"phase": phase.number, "events": phase_events(phase, root)})

        if parts == ["api", "worklog"]:
            return _worklog_read(root, query.get("path", [""])[0])

        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "handoff":
            project = get_project(root, parts[2])
            for phase in discover_phases(project):
                for row in parse_story_rows(phase.path / "current-phase-status.md"):
                    if row.story_id == parts[4]:
                        return 200, envelope(handoff_summary(row, phase, project, root))
            return _error(404, f"story not found: {parts[4]}")

        if parts == ["api", "health"]:
            return 200, envelope(health_report(root, discover_projects(root)))

        if parts == ["api", "missioncontrol"]:
            # WLA-15-01: the read-only belt — the workbench is the
            # fourth consumer of the mission-control substrate, via
            # the in-process API (never re-parsing pm/roadmap here).
            # GET-only by construction; the web view never mutates.
            from .events import read_events
            from .sessions import correlate_sessions
            from .statefeed import build_state_feed

            try:
                tail = max(1, min(int(query.get("tail", ["20"])[0]), 100))
            except ValueError:
                tail = 20
            sessions_doc = correlate_sessions()
            pins, off_belt = mission_control_live_layer(sessions_doc)
            return 200, envelope(
                {
                    "feed": build_state_feed(root),
                    "sessions": sessions_doc,
                    "pins": pins,
                    "off_belt": off_belt,
                    "events": read_events(root, tail=tail),
                }
            )

        if parts == ["api", "file"]:
            return _contained_read(root, query.get("path", [""])[0])

        return _error(404, f"unknown API route: {path}")
    except DwError as err:
        return _error(400, err.message)



# ── mutation intent (WLA-5-06) ───────────────────────────────────────
#
# The editor constructs structured intent; this dispatcher maps each
# request kind one-to-one onto a core plan builder. Preview is pure:
# plan builders only read, so the read-only tree guarantee holds across
# any number of previews. Apply arrives with WLA-5-07.

MUTATION_KINDS = (
    "create_phase",
    "create_story",
    "update_story_status",
    "attach_evidence",
    "close_phase",
)


def _require(body: dict[str, object], *names: str) -> list[str]:
    values = []
    for name in names:
        value = str(body.get(name, "") or "").strip()
        if not value:
            raise DwError(f"missing required field: {name}")
        values.append(value)
    return values


def build_mutation_plan(root: Path, body: dict[str, object]):
    kind = str(body.get("kind", "") or "")
    if kind not in MUTATION_KINDS:
        allowed = ", ".join(MUTATION_KINDS)
        raise DwError(f"unknown mutation kind {kind!r}; allowed: {allowed}")
    (project_slug,) = _require(body, "project")
    project = get_project(root, project_slug)
    force = bool(body.get("force", False))

    if kind == "create_phase":
        number_raw, title = _require(body, "number", "title")
        try:
            number = int(number_raw)
        except ValueError:
            raise DwError(f"phase number must be an integer, got {number_raw!r}")
        if number < 0:
            raise DwError("phase number must not be negative")
        return plan_phase_create(
            root, project, number, title,
            slug=str(body.get("slug", "") or "") or None,
            goal=str(body.get("goal", "") or "") or None,
        )
    if kind == "create_story":
        phase_sel, title = _require(body, "phase", "title")
        phase = get_phase(project, phase_sel)
        return plan_story_create(
            root, project, phase, title,
            slug=str(body.get("slug", "") or "") or None,
            status=str(body.get("status", "") or "backlog"),
        )
    if kind == "update_story_status":
        phase_sel, story, status = _require(body, "phase", "story", "status")
        phase = get_phase(project, phase_sel)
        return plan_story_status(
            root, project, phase, story, status,
            evidence_body=str(body.get("evidence_body", "") or ""),
            force=force,
        )
    if kind == "attach_evidence":
        phase_sel, story = _require(body, "phase", "story")
        phase = get_phase(project, phase_sel)
        return plan_story_evidence(
            root, project, phase, story,
            body=str(body.get("body", "") or ""),
            force=force,
        )
    # close_phase
    (phase_sel,) = _require(body, "phase")
    phase = get_phase(project, phase_sel)
    return plan_phase_close(
        root, project, phase,
        summary_body=str(body.get("summary_body", "") or ""),
        status=str(body.get("status", "") or "done"),
        force=force,
    )


def _issues_guard(root: Path, body: dict[str, object], plan) -> tuple[int, dict[str, object]] | None:
    """Refuse mutations while the project has validation issues — unless
    the plan remediates (its projected issue set is a strict subset of
    the current one; a fix is never ambiguous) or the request
    explicitly acknowledges the issues."""
    project_slug = str(body.get("project", "") or "")
    if not project_slug:
        return None
    project = get_project(root, project_slug)
    issues = check_project(project, root)
    if not issues or bool(body.get("acknowledge_issues", False)):
        return None
    projected = projected_issues(plan)
    if projected is not None and set(projected) < set(issues):
        return None  # this mutation strictly reduces drift; let the fix through
    return 409, envelope(
        {
            "error": "project has validation issues; mutations are guarded",
            "issues": issues,
            "hint": "resolve them in the source Markdown (see /api/health), apply a mutation that fixes them, or resend with acknowledge_issues: true",
        },
        ok=False,
        issues=issues,
    )


def handle_mutation(root: Path, path: str, body: dict[str, object]) -> tuple[int, dict[str, object]]:
    """POST routes: /api/mutations/preview and /api/mutations/apply."""
    route = path.rstrip("/")
    if route == "/api/mutations/preview":
        try:
            plan = build_mutation_plan(root, body)
            guarded = _issues_guard(root, body, plan)
            if guarded:
                return guarded
            payload = preview_plan(plan, include_content=True, include_diff=True)
            project = get_project(root, str(body["project"]))
            payload["issues_before"] = check_project(project, root)
            payload["issues_after"] = projected_issues(plan)
            return 200, envelope(payload)
        except DwError as err:
            return _error(400, err.message)

    if route == "/api/mutations/apply":
        try:
            supplied = str(body.get("fingerprint", "") or "")
            if not supplied:
                return _error(400, "apply requires the fingerprint from a preview response")
            plan = build_mutation_plan(root, body)
            guarded = _issues_guard(root, body, plan)
            if guarded:
                return guarded
            current = plan_fingerprint(plan)
            if current != supplied:
                return 409, envelope(
                    {
                        "error": "stale preview: source files changed after the preview was taken",
                        "supplied_fingerprint": supplied,
                        "current_fingerprint": current,
                        "hint": "re-run the preview and apply with the fresh fingerprint",
                    },
                    ok=False,
                    issues=["stale preview refused; nothing was written"],
                )
            result = apply_plan(plan, validate_after=True)
            result["applied"] = True
            return 200, envelope(result)
        except DwError as err:
            return _error(400, err.message)
        except Exception as err:  # core writes roll back before raising
            return 500, envelope(
                {
                    "error": f"apply failed and was rolled back: {err}",
                    "rolled_back": True,
                },
                ok=False,
                issues=[f"apply failed and was rolled back: {err}"],
            )

    return _error(405, "unsupported method or route; mutations go through /api/mutations/preview and /api/mutations/apply")

def create_handler(root: Path, static_dir: Path | None):
    class WorkbenchHandler(BaseHTTPRequestHandler):
        server_version = "dw-workbench"
        quiet = False

        def log_message(self, fmt: str, *args: object) -> None:
            # Concise access log on stderr; --quiet silences it.
            if not self.quiet:
                import sys

                print(f"dw-workbench: {self.address_string()} {fmt % args}", file=sys.stderr)

        def _send_json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _host_guard(self) -> bool:
            if host_allowed(self.headers.get("Host", "")):
                return True
            self._send_json(403, envelope(
                {"error": "non-local Host header refused (localhost or a .ts.net tailnet host only)"}, ok=False))
            return False

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            if not self._host_guard():
                return
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api"):
                status, payload = handle_api(root, parsed.path, parse_qs(parsed.query))
                self._send_json(status, payload)
                return
            self._send_static(parsed.path)

        def _send_static(self, raw_path: str) -> None:
            if static_dir is None:
                self._send_json(503, envelope({"error": "workbench UI not available; API only"}, ok=False))
                return
            name = raw_path.lstrip("/") or "index.html"
            target = (static_dir / name).resolve()
            allowed = static_dir.resolve()
            if allowed not in target.parents or not target.is_file():
                self._send_json(404, envelope({"error": f"no such asset: {raw_path}"}, ok=False))
                return
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", _CONTENT_TYPES.get(target.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _reject(self) -> None:
            self._send_json(405, envelope({"error": "the workbench explorer is read-only (GET only)"}, ok=False))

        def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib naming)
            # No CORS headers are ever emitted; preflights fail closed.
            self._reject()

        def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
            if not self._host_guard():
                return
            parsed = urlparse(self.path)
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length) if length else b"{}"
                body = json.loads(raw.decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError("body must be a JSON object")
            except (ValueError, UnicodeDecodeError) as err:
                self._send_json(400, envelope({"error": f"invalid JSON body: {err}"}, ok=False))
                return
            status, payload = handle_mutation(root, parsed.path, body)
            self._send_json(status, payload)

        do_PUT = _reject  # noqa: N815
        do_DELETE = _reject  # noqa: N815
        do_PATCH = _reject  # noqa: N815

    return WorkbenchHandler


def serve(root: Path, port: int = 8377, quiet: bool = False) -> None:
    """Run the workbench bound to localhost until interrupted.

    Fails closed: refuses roots without a pm/roadmap tree, refuses
    ports already in use (with remediation), and shuts down cleanly on
    SIGINT/SIGTERM. Never binds beyond 127.0.0.1.
    """
    import signal
    import sys

    if not root.is_dir():
        raise DwError(f"repo root does not exist: {root}")
    try:
        has_roadmap = roadmap_dir(root).is_dir()
    except DwError:
        has_roadmap = False
    if not has_roadmap:
        raise DwError(
            f"no pm/roadmap tree under {root} — the workbench serves exactly one "
            "roadmap-bearing repo root; pass --root or run dw adopt / new-project first"
        )
    handler = create_handler(root, workbench_dir())
    handler.quiet = quiet
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as err:
        raise DwError(
            f"cannot bind 127.0.0.1:{port} ({err.strerror or err}); "
            "the port is likely in use — stop the other process or pass --port <n>"
        )
    print(f"dw-workbench: serving {root}")
    print(f"dw-workbench: http://127.0.0.1:{port}/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)")
    print("dw-workbench: writes happen only via /api/mutations preview→apply inside pm/roadmap; never commits")

    def _term(_sig, _frame):  # graceful SIGTERM
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _term)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("dw-workbench: shutting down", file=sys.stderr)
    finally:
        httpd.server_close()
