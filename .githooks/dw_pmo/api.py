"""Machine-readable context envelopes shared by the CLI and workbench."""

from __future__ import annotations

from pathlib import Path

from .model import DONE_STATUSES, OPEN_STATUSES, Phase, Project, StoryRow, normalize_status
from .parse import (
    discover_phases,
    get_phase,
    header_status,
    hook_snapshot,
    link_target,
    parse_current_phase_dirname,
    parse_current_phase_target,
    parse_story_rows,
    story_num_from_file,
    supplemental_canon,
)
from .paths import rel, roadmap_dir
from .trace import recent_commits, work_log_entries
from .validate import check_project, project_warnings


def next_story(project: Project, root: Path) -> dict[str, object] | None:
    preferred = ("in-progress", "ready", "backlog")
    # Nothing in a closed phase is actionable (WLA-16-03) — a
    # final-summary is the phase's terminal receipt. Within each status
    # tier, the phase the README pointer names is consulted first.
    phases = [
        phase
        for phase in discover_phases(project)
        if not (phase.path / "final-summary.md").exists()
    ]
    pointer_dir = parse_current_phase_dirname(project)
    if pointer_dir:
        phases.sort(key=lambda phase: phase.path.name != pointer_dir)
    for status in preferred:
        for phase in phases:
            for row in parse_story_rows(phase.path / "current-phase-status.md"):
                if normalize_status(row.status) == status:
                    story_target = link_target(row.story_file)
                    return {
                        "story_id": row.story_id,
                        "title": row.title,
                        "status": row.status,
                        "phase": phase.number,
                        "phase_path": phase.path.name,
                        "story_path": rel((phase.path / story_target).resolve(), root),
                    }
    return None


def story_context(row: StoryRow, phase: Phase, project: Project, root: Path, include_trace: bool = False) -> dict[str, object]:
    story_target = link_target(row.story_file)
    story_path = (phase.path / story_target).resolve()
    story_num = story_num_from_file(row.story_file)
    evidence_target = link_target(row.evidence)
    if row.evidence in {"-", "—", ""} and story_num is not None:
        evidence_path = phase.path / f"evidence-story-{story_num:02d}.md"
        evidence_link = ""
    elif evidence_target and evidence_target not in {"-", "—"}:
        evidence_path = (phase.path / evidence_target).resolve()
        evidence_link = evidence_target
    else:
        evidence_path = None
        evidence_link = ""

    header = header_status(story_path)
    paths = [
        project.path / "README.md",
        phase.path / "current-phase-status.md",
        story_path,
    ]
    if evidence_path:
        paths.append(evidence_path)
    final_summary = phase.path / "final-summary.md"
    if final_summary.exists():
        paths.append(final_summary)

    item = {
        "story_id": row.story_id,
        "title": row.title,
        "status": row.status,
        "header_status": header,
        "story_file": story_target,
        "story_path": rel(story_path, root),
        "story_exists": story_path.exists(),
        "evidence": row.evidence,
        "evidence_file": evidence_link,
        "evidence_path": rel(evidence_path, root) if evidence_path else "",
        "evidence_exists": bool(evidence_path and evidence_path.exists()),
        "trace": {
            "readme": rel(project.path / "README.md", root),
            "phase_status": rel(phase.path / "current-phase-status.md", root),
            "story": rel(story_path, root),
            "evidence": rel(evidence_path, root) if evidence_path else "",
            "final_summary": rel(final_summary, root),
        },
    }
    if include_trace:
        item["recent_commits"] = recent_commits(root, paths)
        item["work_log_entries"] = work_log_entries(root, project, row)
    return item


def project_context(
    project: Project,
    root: Path,
    phase_selector: str | None = None,
    status_filter: str | None = None,
    include_trace: bool = False,
) -> dict[str, object]:
    phases = discover_phases(project)
    if phase_selector:
        phases = [get_phase(project, phase_selector)]

    phase_items: list[dict[str, object]] = []
    for phase in phases:
        all_rows = parse_story_rows(phase.path / "current-phase-status.md")
        rows = []
        for row in all_rows:
            if status_filter and normalize_status(row.status) != normalize_status(status_filter):
                continue
            rows.append(story_context(row, phase, project, root, include_trace))
        phase_items.append(
            {
                "number": phase.number,
                "slug": phase.slug,
                "path": rel(phase.path, root),
                "status_file": rel(phase.path / "current-phase-status.md", root),
                "status_file_exists": (phase.path / "current-phase-status.md").exists(),
                "final_summary": rel(phase.path / "final-summary.md", root),
                "final_summary_exists": (phase.path / "final-summary.md").exists(),
                "active": any(normalize_status(row.status) in OPEN_STATUSES for row in all_rows),
                "stories": rows,
            }
        )

    return {
        "slug": project.slug,
        "prefix": project.prefix,
        "path": rel(project.path, root),
        "readme": rel(project.path / "README.md", root),
        "readme_exists": (project.path / "README.md").exists(),
        "current_phase_target": parse_current_phase_target(project),
        "next_story": next_story(project, root),
        "issues": check_project(project, root),
        "warnings": project_warnings(project, root),
        "supplemental_canon": supplemental_canon(root, project),
        "hook_snapshot": hook_snapshot(root),
        "work_logs": work_log_entries(root, project),
        "phases": phase_items,
    }


def build_context_payload(
    root: Path,
    projects: list[Project],
    phase_selector: str | None = None,
    status_filter: str | None = None,
    include_trace: bool = False,
) -> dict[str, object]:
    return {
        "kind": "delivery-workbench-roadmap-context",
        "schema_version": 1,
        "root": str(root),
        "roadmap_dir": rel(roadmap_dir(root), root),
        "projects": [
            project_context(project, root, phase_selector, status_filter, include_trace)
            for project in projects
        ],
    }

# ── traceability timeline (WLA-5-05) ─────────────────────────────────

def story_timeline(row: StoryRow, phase: Phase, project: Project, root: Path) -> dict[str, object]:
    """Normalized intent-to-proof chain for one story.

    The chain names every PMO hop with an explicit exists flag (absent
    links render as absent, never disappear); events merge recent
    commits (scoped to the story's PMO files, carrying PMO-Story and
    PMO-Contract-Digest trailers where stamped) with work-log entries
    (honoring PMO_WORK_LOG_DIR resolution; empty when no log root
    exists). ``shipped`` is asserted only when the story status is done
    AND evidence exists — never from either alone.
    """
    context = story_context(row, phase, project, root, include_trace=True)
    chain = []
    for hop in ("readme", "phase_status", "story", "evidence", "final_summary"):
        rel_path = str(context["trace"][hop])  # type: ignore[index]
        chain.append(
            {
                "hop": hop,
                "path": rel_path,
                "exists": bool(rel_path) and (root / rel_path).is_file(),
            }
        )
    events: list[dict[str, object]] = []
    for commit in context.get("recent_commits", []):  # type: ignore[union-attr]
        events.append(
            {
                "type": "commit",
                "sort_key": str(commit.get("date", "")),
                "date": commit.get("date", ""),
                "subject": commit.get("subject", ""),
                "sha": commit.get("sha", ""),
                "pmo_story": commit.get("pmo_story", ""),
                "contract_digest": commit.get("contract_digest", ""),
                "source": commit.get("sha", ""),
            }
        )
    for entry in context.get("work_log_entries", []):  # type: ignore[union-attr]
        events.append(
            {
                "type": "work-log",
                "sort_key": str(entry.get("timestamp") or entry.get("date") or ""),
                "date": entry.get("date", ""),
                "subject": entry.get("subject", ""),
                "commit": entry.get("commit", ""),
                "source": entry.get("path", ""),
            }
        )
    events.sort(key=lambda e: str(e["sort_key"]), reverse=True)
    status = str(context["status"])
    evidence_exists = bool(context["evidence_exists"])
    shipped = normalize_status(status) in DONE_STATUSES and evidence_exists
    reason = ""
    if not shipped:
        if normalize_status(status) not in DONE_STATUSES:
            reason = f"story status is {status!r}, not done"
        elif not evidence_exists:
            reason = "story is marked done but its evidence file does not exist"
    return {
        "story_id": context["story_id"],
        "title": context["title"],
        "status": status,
        "phase_number": phase.number,
        "evidence_exists": evidence_exists,
        "shipped": shipped,
        "not_shipped_reason": reason,
        "chain": chain,
        "events": events,
    }


def phase_events(phase: Phase, root: Path) -> list[dict[str, object]]:
    """Recent commits scoped to the phase directory (phase trace view)."""
    return recent_commits(root, [phase.path], limit=10)

def handoff_summary(row: StoryRow, phase: Phase, project: Project, root: Path) -> dict[str, object]:
    """Concise agent handoff for one story: PMO source paths, captured
    command-output references, PMO-scoped commits, and supplementary
    work-log pointers. Deterministic text, safe to paste into a task or
    commit-contract context. Work logs are labeled supplementary —
    evidence-story-NN.md remains the proof of record."""
    from .evidence import parse_captured_runs
    from .paths import read_text

    timeline = story_timeline(row, phase, project, root)
    lines = [
        f"# Delivery Workbench handoff — {timeline['story_id']}",
        f"Story: {timeline['story_id']} — {timeline['title']} [{timeline['status']}]"
        f" (shipped: {'yes' if timeline['shipped'] else 'no — ' + str(timeline['not_shipped_reason'])})",
        "Sources:",
    ]
    evidence_path = None
    for hop in timeline["chain"]:
        state = hop["path"] if hop["exists"] else f"(absent) {hop['path']}"
        lines.append(f"  {hop['hop']}: {state}")
        if hop["hop"] == "evidence" and hop["exists"]:
            evidence_path = root / str(hop["path"])
    lines.append("Captured runs (command output references in evidence):")
    runs = parse_captured_runs(read_text(evidence_path)) if evidence_path else []
    if runs:
        for run in runs:
            lines.append(f"  - {run['timestamp']} `{run['command']}` exit {run['exit_code']}")
    elif evidence_path:
        lines.append("  - none (narrative-only evidence)")
    else:
        lines.append("  - none (no evidence file exists yet — required before done)")
    lines.append("Recent commits (scoped to this story's PMO files):")
    commits = [e for e in timeline["events"] if e["type"] == "commit"]
    for event in commits or []:
        trailer = f" [PMO-Story: {event['pmo_story']}]" if event["pmo_story"] else ""
        lines.append(f"  - {str(event['sha'])[:9]} {event['date']} {event['subject']}{trailer}")
    if not commits:
        lines.append("  - none found")
    lines.append("Work logs (supplementary; never a substitute for evidence-story-NN.md):")
    logs = [e for e in timeline["events"] if e["type"] == "work-log"]
    for event in logs or []:
        lines.append(f"  - {event['source']} ({event['sort_key']})")
    if not logs:
        lines.append("  - none (optional evidence; absent)")
    return {
        "story_id": timeline["story_id"],
        "shipped": timeline["shipped"],
        "text": "\n".join(lines),
    }

